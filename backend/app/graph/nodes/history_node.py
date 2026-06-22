from backend.app.db.session import SessionLocal
from uuid import UUID

from backend.app.models.message import Message


def history_node(state):
    """
    Placeholder for longer-term historical memory / summary memory.

    Right now, recent conversation memory is already loaded by memory_node
    from the messages table, so we avoid duplicate DB reads here.

    In future, this node can be used for:
    - summarized older conversation history
    - user preference history
    - archived long-term memory
    """

    return {
        **state,
        "history": state.get("history", [])
    }