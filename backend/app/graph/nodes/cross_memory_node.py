# backend/app/graph/nodes/cross_memory_node.py

from uuid import UUID

from backend.app.db.session import SessionLocal
from backend.app.graph.state import CompanionState
from backend.app.services.cross_memory_service import CrossMemoryService


async def cross_memory_node(state: CompanionState) -> CompanionState:
    """
    Fetches memories written by OTHER companions about this user.

    Runs FIRST in the pipeline, before any other memory loading.
    Populates:
    - cross_agent_memories: raw list of memory dicts
    - cross_agent_context: formatted string for prompt injection
    """
    user_id_str = state.get("user_id")
    companion_name = state.get("companion_name", "")
    companion_id_str = state.get("companion_id")
    user_message = state.get("user_message", "")

    # --------------------------------------------------
    # Validate required fields
    # --------------------------------------------------
    if not user_id_str or not companion_name or not companion_id_str:
        print("[CROSS MEMORY NODE] Missing user_id, companion_name, or companion_id")
        return {
            "cross_agent_memories": [],
            "cross_agent_context": "",
        }

    try:
        user_uuid = UUID(str(user_id_str))
        companion_uuid = UUID(str(companion_id_str))
    except Exception as e:
        print(f"[CROSS MEMORY NODE] Invalid UUID: {e}")
        return {
            "cross_agent_memories": [],
            "cross_agent_context": "",
        }

    db = SessionLocal()

    try:
        service = CrossMemoryService()

        # --------------------------------------------------
        # 1. Fetch memories from all OTHER companions
        # --------------------------------------------------
        cross_memories = await service.get_cross_agent_memories(
            db=db,
            user_id=user_uuid,
            current_companion_name=companion_name,
            current_companion_id=companion_uuid,
            query=user_message,
            limit_per_source=5,
        )

        # --------------------------------------------------
        # 2. Build readable context string
        # --------------------------------------------------
        cross_context = service.build_cross_context_string(
            memories=cross_memories,
            current_companion=companion_name,
        )

        # --------------------------------------------------
        # Debug logs
        # --------------------------------------------------
        print("=" * 60)
        print("[CROSS MEMORY NODE]")
        print("COMPANION:", companion_name)
        print("CROSS AGENT MEMORIES FOUND:", len(cross_memories))

        if cross_memories:
            print("[CROSS MEMORY SAMPLE]")
            for mem in cross_memories[:3]:
                print(
                    f"  {mem['source_companion']} "
                    f"[{mem['memory_type']}]: "
                    f"{mem['content'][:100]}"
                )
        else:
            print("[CROSS MEMORY] No cross-agent memories found yet.")

        print("=" * 60)

        return {
            "cross_agent_memories": cross_memories,
            "cross_agent_context": cross_context,
        }

    except Exception as e:
        print(f"[CROSS MEMORY NODE ERROR] {e}")
        return {
            "cross_agent_memories": [],
            "cross_agent_context": "",
        }

    finally:
        db.close()