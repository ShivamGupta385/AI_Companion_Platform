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

    # ---------------------------------------------------------
    # Text sanitization helpers
    # ---------------------------------------------------------
    @staticmethod
    def clean_text(value: str | None) -> str:
        """
        Remove null bytes and unsafe control characters from text
        before sending to LLM, saving in DB, or storing in checkpoints.

        Keeps:
        - normal printable characters
        - newline
        - tab
        - carriage return
        """
        if not value:
            return ""

        cleaned_chars = []
        for ch in str(value):
            code = ord(ch)

            # Remove NULL byte explicitly
            if code == 0:
                continue

            # Keep newline / tab / carriage return
            if ch in ("\n", "\t", "\r"):
                cleaned_chars.append(ch)
                continue

            # Remove other ASCII control chars
            if code < 32:
                continue

            cleaned_chars.append(ch)

        cleaned = "".join(cleaned_chars)

        # UTF-8 roundtrip to strip weird invalid sequences
        cleaned = (
            cleaned.encode("utf-8", errors="ignore")
            .decode("utf-8", errors="ignore")
            .strip()
        )

        return cleaned

    @staticmethod
    def normalize_memory_text(value: str | None) -> str:
        """
        Normalize memory text for dedupe checks.
        """
        text = LongTermMemoryService.clean_text(value)
        return " ".join(text.split()).strip().lower()

    # ---------------------------------------------------------
    # Read APIs
    # ---------------------------------------------------------
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

        # If companion-specific memory is requested, return:
        # - memories tied to that companion
        # - global memories (companion_id is null)
        if companion_id:
            query = query.filter(
                (UserMemory.companion_id == companion_id) |
                (UserMemory.companion_id.is_(None))
            )

        return query.limit(limit).all()

    @staticmethod
    def get_recent_conversation_summaries(
        db: Session,
        user_id: UUID,
        companion_id: Optional[UUID] = None,
        limit: int = 5
    ) -> List[ConversationSummary]:
        query = (
            db.query(ConversationSummary)
            .filter(ConversationSummary.user_id == user_id)
        )

        if companion_id:
            query = query.filter(
                ConversationSummary.companion_id == companion_id
            )

        query = query.order_by(desc(ConversationSummary.updated_at))

        return query.limit(limit).all()

    # ---------------------------------------------------------
    # Write APIs
    # ---------------------------------------------------------
    @staticmethod
    def save_user_memory(
        db: Session,
        user_id: UUID,
        memory_type: str,
        memory_text: str,
        companion_id: Optional[UUID] = None,
        source_conversation_id: Optional[UUID] = None
    ) -> UserMemory:
        memory_text = LongTermMemoryService.clean_text(memory_text)

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

    # ---------------------------------------------------------
    # Transcript builder
    # ---------------------------------------------------------
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

        lines: List[str] = []

        for msg in messages:
            speaker = "User" if msg.sender_type == "user" else "Assistant"
            cleaned_text = LongTermMemoryService.clean_text(msg.message_text)

            if not cleaned_text:
                continue

            lines.append(f"{speaker}: {cleaned_text}")

        transcript = "\n".join(lines)
        transcript = LongTermMemoryService.clean_text(transcript)

        return transcript

    # ---------------------------------------------------------
    # Conversation summary generation
    # ---------------------------------------------------------
    @staticmethod
    async def upsert_conversation_summary(
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

        conversation_text = LongTermMemoryService.clean_text(conversation_text)

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

        response = await llm.ainvoke(summary_prompt)

        raw_summary = getattr(response, "content", "") or ""
        summary_text = LongTermMemoryService.clean_text(raw_summary)

        if not summary_text:
            return None

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

    # ---------------------------------------------------------
    # Durable memory extraction
    # ---------------------------------------------------------
    @staticmethod
    async def extract_and_store_memories(
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

        conversation_text = LongTermMemoryService.clean_text(conversation_text)

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
Do NOT include greetings.
Do NOT include one-time irrelevant facts.

Return each memory as a short bullet point.
Keep each memory concise and factual.

Conversation:
{conversation_text}
"""

        response = await llm.ainvoke(extraction_prompt)
        raw_output = getattr(response, "content", "") or ""
        raw_output = LongTermMemoryService.clean_text(raw_output)

        if not raw_output:
            return []

        stored_memories: List[UserMemory] = []

        # Load existing normalized memories for this user
        existing_memories = (
            db.query(UserMemory)
            .filter(UserMemory.user_id == user_id)
            .all()
        )

        existing_normalized = {
            LongTermMemoryService.normalize_memory_text(m.memory_text)
            for m in existing_memories
            if m.memory_text
        }

        candidate_lines = raw_output.split("\n")

        for line in candidate_lines:
            memory_text = LongTermMemoryService.clean_text(line)

            if memory_text.startswith("-"):
                memory_text = memory_text[1:].strip()

            memory_text = LongTermMemoryService.clean_text(memory_text)

            if not memory_text:
                continue

            # Skip very short / junk memories
            if len(memory_text) < 4:
                continue

            normalized = LongTermMemoryService.normalize_memory_text(memory_text)

            if not normalized:
                continue

            # Deduplicate
            if normalized in existing_normalized:
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
            existing_normalized.add(normalized)

        db.flush()

        return stored_memories