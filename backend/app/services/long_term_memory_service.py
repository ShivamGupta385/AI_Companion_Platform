from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.user_memory import UserMemory
from backend.app.models.conversation_summary import ConversationSummary
from backend.app.models.message import Message
from backend.app.services.llm_provider import llm


class LongTermMemoryService:
    """
    Service layer for AGIX cross-conversation long-term memory.

    Responsibilities:
    1. Load durable user memories from user_memories
    2. Load recent conversation summaries from conversation_summaries
    3. Save new durable memories
    4. Build conversation transcript text for summarization
    5. Generate / update conversation summaries
    6. Extract and store useful long-term memories
    """

    @staticmethod
    def get_user_memories(
        db: Session,
        user_id: UUID,
        companion_id: Optional[UUID] = None,
        limit: int = 10
    ) -> List[UserMemory]:
        query = (
            db.query(UserMemory)
            .filter(UserMemory.user_id == user_id)
            .order_by(desc(UserMemory.updated_at))
        )

        return query.limit(limit).all()

    @staticmethod
    def get_recent_conversation_summaries(
        db: Session,
        user_id: UUID,
        companion_id: Optional[UUID] = None,
        limit: int = 5
    ) -> List[ConversationSummary]:
        query = db.query(ConversationSummary).filter(
            ConversationSummary.user_id == user_id
        )

        if companion_id:
            query = query.filter(
                ConversationSummary.companion_id == companion_id
            )

        query = query.order_by(desc(ConversationSummary.updated_at))

        return query.limit(limit).all()

    @staticmethod
    def save_user_memory(
        db: Session,
        user_id: UUID,
        memory_type: str,
        memory_text: str,
        companion_id: Optional[UUID] = None,
        source_conversation_id: Optional[UUID] = None
    ) -> UserMemory:
        memory = UserMemory(
            user_id=user_id,
            companion_id=companion_id,
            memory_type=memory_type,
            memory_text=memory_text,
            source_conversation_id=source_conversation_id
        )

        db.add(memory)
        db.flush()

        return memory

    @staticmethod
    def build_conversation_text(
        db: Session,
        conversation_id: UUID,
        limit: int = 30
    ) -> str:
        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .all()
        )

        lines = []

        for msg in messages:
            speaker = "User" if msg.sender_type == "user" else "Assistant"
            lines.append(f"{speaker}: {msg.message_text}")

        return "\n".join(lines)

    @staticmethod
    def upsert_conversation_summary(
        db: Session,
        conversation_id: UUID,
        user_id: UUID,
        companion_id: UUID
    ) -> Optional[ConversationSummary]:
        """
        Create or update a summary for a conversation thread.
        """
        conversation_text = LongTermMemoryService.build_conversation_text(
            db=db,
            conversation_id=conversation_id,
            limit=40
        )

        if not conversation_text.strip():
            return None

        summary_prompt = f"""
You are generating a reusable long-term summary for an AI companion system.

Summarize the following conversation into a concise memory summary for future chats.

Focus on:
- the user's project context
- what the user is learning or building
- important decisions made
- preferences or goals mentioned
- follow-up tasks or pending work
- anything that would be useful if the user starts a new conversation later

Write a compact summary paragraph.

Conversation:
{conversation_text}
"""

        response = llm.invoke(summary_prompt)
        summary_text = response.content.strip()

        existing_summary = (
            db.query(ConversationSummary)
            .filter(
                ConversationSummary.conversation_id == conversation_id
            )
            .first()
        )

        if existing_summary:
            existing_summary.summary_text = summary_text
            db.flush()
            return existing_summary

        new_summary = ConversationSummary(
            conversation_id=conversation_id,
            user_id=user_id,
            companion_id=companion_id,
            summary_text=summary_text
        )

        db.add(new_summary)
        db.flush()

        return new_summary

    @staticmethod
    def extract_and_store_memories(
        db: Session,
        conversation_id: UUID,
        user_id: UUID,
        companion_id: UUID
    ) -> List[UserMemory]:
        """
        Extract durable long-term memories from a conversation and store them.
        """
        conversation_text = LongTermMemoryService.build_conversation_text(
            db=db,
            conversation_id=conversation_id,
            limit=40
        )

        if not conversation_text.strip():
            return []

        extraction_prompt = f"""
You are extracting durable long-term user memories for an AI companion.

From the conversation below, extract ONLY information that is useful in future conversations.

Keep memories only if they are stable or important, such as:
- user project context
- ongoing work
- learning goals
- important preferences
- repeated interests
- future tasks or commitments

Do NOT include temporary small talk.

Return each memory as a short bullet point.
Keep each memory concise and factual.

Conversation:
{conversation_text}
"""

        response = llm.invoke(extraction_prompt)
        raw_output = response.content.strip()

        stored_memories: List[UserMemory] = []

        for line in raw_output.split("\n"):
            memory_text = line.strip()

            if memory_text.startswith("-"):
                memory_text = memory_text[1:].strip()

            if not memory_text:
                continue

            # Avoid exact duplicate memory for same user
            existing = (
                db.query(UserMemory)
                .filter(
                    UserMemory.user_id == user_id,
                    UserMemory.memory_text == memory_text
                )
                .first()
            )

            if existing:
                continue

            memory = UserMemory(
                user_id=user_id,
                companion_id=companion_id,
                memory_type="conversation_insight",
                memory_text=memory_text,
                source_conversation_id=conversation_id
            )

            db.add(memory)
            stored_memories.append(memory)

        db.flush()

        return stored_memories