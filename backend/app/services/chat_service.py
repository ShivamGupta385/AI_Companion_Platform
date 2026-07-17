from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from backend.app.models.user import User
from backend.app.models.message import Message
from backend.app.models.companion import Companion
from backend.app.models.conversation import Conversation
from backend.app.models.user_onboarding import UserOnboarding


from backend.app.services.long_term_memory_service import (
    LongTermMemoryService,
)

from backend.app.utils.text_cleaner import clean_text


class ChatService:
    """
    Shared chat service used by:

    1. Web Chat API
       POST /api/v1/chat

    2. Tavus Custom LLM Endpoint
       POST /api/v1/openai/chat/completions

    All LangGraph execution should happen here so that
    both endpoints reuse the exact same business logic.
    """

    @staticmethod
    def build_memory_buffer(
        db: Session,
        conversation_id: int,
        limit: int = 12,
    ):
        """
        Build short-term thread memory from the latest
        messages stored in PostgreSQL.
        """
        recent_messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )

        recent_messages.reverse()
        buffer = []

        for msg in recent_messages:
            if msg.sender_type == "user":
                role = "human"
            elif msg.sender_type == "assistant":
                role = "assistant"
            else:
                role = "system"

            buffer.append(
                (
                    role,
                    clean_text(msg.message_text),
                )
            )

        return buffer

    @staticmethod
    def get_conversation(
        db: Session,
        conversation_id: int,
        user_id: int,
    ) -> Conversation | None:
        """Fetch user conversation."""
        return (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
            .first()
        )

    @staticmethod
    def get_companion(
        db: Session,
        companion_id: int,
    ) -> Companion | None:
        """Fetch companion."""
        return (
            db.query(Companion)
            .filter(Companion.id == companion_id)
            .first()
        )

    @staticmethod
    def get_onboarding(
        db: Session,
        user_id: int,
    ) -> UserOnboarding | None:
        """Fetch onboarding profile."""
        return (
            db.query(UserOnboarding)
            .filter(UserOnboarding.user_id == user_id)
            .first()
        )

    @staticmethod
    def save_user_message(
        db: Session,
        conversation_id: int,
        message: str,
    ) -> Message:
        """Persist user message."""
        user_message = Message(
            conversation_id=conversation_id,
            sender_type="user",
            message_text=message,
        )
        db.add(user_message)
        db.flush()
        return user_message

    @staticmethod
    def save_assistant_message(
        db: Session,
        conversation_id: int,
        message: str,
    ) -> Message:
        """Persist assistant response."""
        assistant_message = Message(
            conversation_id=conversation_id,
            sender_type="assistant",
            message_text=message,
        )
        db.add(assistant_message)
        db.flush()
        return assistant_message

    @staticmethod
    async def process_chat(
    graph,
    db: Session,
    current_user: User,
    conversation_id: int,
    message: str,
) -> str:
        """
        Process a complete chat request using LangGraph.

        Returns:
            str: Assistant response
        """
        try:
            # 1) Load Conversation
            conversation = ChatService.get_conversation(
                db=db,
                conversation_id=conversation_id,
                user_id=current_user.id,
            )
            if not conversation:
                raise ValueError("Conversation not found")

            # 2) Load Companion
            companion = ChatService.get_companion(
                db=db,
                companion_id=conversation.companion_id,
            )
            if not companion:
                raise ValueError("Companion not found")

            # 3) Load User Onboarding
            onboarding = ChatService.get_onboarding(
                db=db,
                user_id=current_user.id,
            )

            # 4) Clean User Message
            cleaned_user_message = clean_text(message)
            if not cleaned_user_message.strip():
                raise ValueError("Message cannot be empty")

            # 5) Save User Message
            ChatService.save_user_message(
                db=db,
                conversation_id=conversation.id,
                message=cleaned_user_message,
            )

            # 6) Build Thread Memory
            memory_buffer = ChatService.build_memory_buffer(
                db=db,
                conversation_id=conversation.id,
                limit=12,
            )

            # 7) Debug Logs
            print("=" * 80)
            print("[CHAT SERVICE]")
            print("Conversation :", conversation.id)
            print("Companion    :", companion.name)
            print("User         :", current_user.email)
            print("Memory Count :", len(memory_buffer))
            print("Message      :", cleaned_user_message)
            print("=" * 80)

            # 8) Prepare LangGraph State
            graph_input = {
                "conversation_id": str(conversation.id),
                "companion_id": str(companion.id),
                "companion_name": clean_text(companion.name),
                "user_id": str(current_user.id),
                "user_message": cleaned_user_message,
                "user_profile": (
                    onboarding.baseline_data
                    if onboarding and onboarding.baseline_data
                    else {}
                ),
                "memory": memory_buffer,
            }

            # 9) Invoke LangGraph
            result = await graph.ainvoke(
            graph_input,
            config={
                "configurable": {
                    "thread_id": str(conversation.id)
                }
            },
        )

            print("=" * 80)
            print("[GRAPH RESULT]")
            print(result)
            print("=" * 80)

            ai_response = result.get("response", "").strip()
            if not ai_response.strip():
                raise RuntimeError("LangGraph returned an empty response.")

            # 10) Save Assistant Message
            ChatService.save_assistant_message(
                db=db,
                conversation_id=conversation.id,
                message=ai_response,
            )

            # 11) Update Conversation Timestamp
            conversation.updated_at = func.now()

            # 12) Check Message Count
            message_count = (
                db.query(Message)
                .filter(Message.conversation_id == conversation.id)
                .count()
            )

            print("=" * 80)
            print("[CHAT SERVICE]")
            print("Message Count :", message_count)
            print("=" * 80)

            # 13) Update Long-Term Memory
            if message_count >= 8:
                print("=" * 80)
                print("[CHAT SERVICE]")
                print("Updating Long-Term Memory...")
                print("=" * 80)

                await LongTermMemoryService.upsert_conversation_summary(
                db=db,
                conversation_id=conversation.id,
                user_id=current_user.id,
                companion_id=companion.id,
            )

            await LongTermMemoryService.extract_and_store_memories(
                db=db,
                conversation_id=conversation.id,
                user_id=current_user.id,
                companion_id=companion.id,
            )

            # 14) Commit Transaction
            db.commit()

            print("=" * 80)
            print("[CHAT SERVICE SUCCESS]")
            print("Conversation    :", conversation.id)
            print("Response Length :", len(ai_response))
            print("=" * 80)

            # 15) Return Response
            return ai_response

        except Exception:
            db.rollback()
            raise
