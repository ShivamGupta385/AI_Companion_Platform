from uuid import UUID

from backend.app.db.session import SessionLocal
from backend.app.services.long_term_memory_service import (
    LongTermMemoryService
)


def long_term_memory_node(state):
    """
    Load cross-conversation long-term memory for the current user.

    This node fetches:
    1. durable user memories from user_memories
    2. summaries of previous conversations from conversation_summaries

    Output keys added to state:
    - long_term_memories: list[str]
    - conversation_summaries: list[str]
    """

    db = SessionLocal()

    try:
        user_id = state.get("user_id")
        companion_id = state.get("companion_id")

        # --------------------------------------------------
        # Validate required user_id
        # --------------------------------------------------
        if not user_id:
            print("[LONG TERM MEMORY NODE] No user_id found in state")

            return {
                **state,
                "long_term_memories": [],
                "conversation_summaries": []
            }

        try:
            user_uuid = UUID(str(user_id))
        except Exception:
            print(
                f"[LONG TERM MEMORY NODE] Invalid user_id: {user_id}"
            )
            return {
                **state,
                "long_term_memories": [],
                "conversation_summaries": []
            }

        companion_uuid = None
        if companion_id:
            try:
                companion_uuid = UUID(str(companion_id))
            except Exception:
                print(
                    f"[LONG TERM MEMORY NODE] Invalid companion_id: {companion_id}"
                )
                companion_uuid = None

        # --------------------------------------------------
        # Fetch long-term memories + summaries
        # --------------------------------------------------
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

        # --------------------------------------------------
        # Extract text payloads for LLM state
        # --------------------------------------------------
        memory_texts = [
            memory.memory_text.strip()
            for memory in memories
            if memory.memory_text
        ]

        summary_texts = [
            summary.summary_text.strip()
            for summary in summaries
            if summary.summary_text
        ]

        print("=" * 60)
        print("[LONG TERM MEMORY NODE]")
        print("USER ID:", user_id)
        print("COMPANION ID:", companion_id)
        print("LONG TERM MEMORIES:", len(memory_texts))
        print("CONVERSATION SUMMARIES:", len(summary_texts))

        if memory_texts:
            print("[LONG TERM MEMORY SAMPLE]")
            for item in memory_texts[:3]:
                print("-", item[:200])

        if summary_texts:
            print("[SUMMARY SAMPLE]")
            for item in summary_texts[:2]:
                print("-", item[:200])

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