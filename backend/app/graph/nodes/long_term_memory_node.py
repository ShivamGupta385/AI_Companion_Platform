from uuid import UUID

from backend.app.db.session import SessionLocal
from backend.app.services.long_term_memory_service import LongTermMemoryService


def long_term_memory_node(state):
    """
    Load cross-conversation long-term memory for the current user.

    This node fetches:
    1. durable user memories from user_memories
    2. summaries of previous conversations from conversation_summaries
    """
    db = SessionLocal()

    try:
        user_id = state.get("user_id")
        companion_id = state.get("companion_id")

        if not user_id:
            print("[LONG TERM MEMORY NODE] No user_id found in state")

            return {
                **state,
                "long_term_memories": [],
                "conversation_summaries": []
            }

        user_uuid = UUID(user_id)

        companion_uuid = None
        if companion_id:
            companion_uuid = UUID(companion_id)

        memories = LongTermMemoryService.get_user_memories(
            db=db,
            user_id=user_uuid,
            companion_id=companion_uuid,
            limit=10
        )

        summaries = LongTermMemoryService.get_recent_conversation_summaries(
            db=db,
            user_id=user_uuid,
            companion_id=companion_uuid,
            limit=5
        )

        memory_texts = [
            memory.memory_text
            for memory in memories
        ]

        summary_texts = [
            summary.summary_text
            for summary in summaries
        ]

        print("=" * 60)
        print("[LONG TERM MEMORY NODE]")
        print("USER ID:", user_id)
        print("COMPANION ID:", companion_id)
        print("LONG TERM MEMORIES:", len(memory_texts))
        print("CONVERSATION SUMMARIES:", len(summary_texts))
        print("=" * 60)

        return {
            **state,
            "long_term_memories": memory_texts,
            "conversation_summaries": summary_texts
        }

    except Exception as e:
        print(f"[LONG TERM MEMORY NODE ERROR] {e}")

        return {
            **state,
            "long_term_memories": [],
            "conversation_summaries": []
        }

    finally:
        db.close()