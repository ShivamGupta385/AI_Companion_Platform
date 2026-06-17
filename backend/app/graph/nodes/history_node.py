from backend.app.db.session import SessionLocal
from uuid import UUID

from backend.app.models.message import Message


def history_node(state):

    db = SessionLocal()

    try:

        history = (
            db.query(Message)
            .filter(
                Message.conversation_id
                ==UUID(state["conversation_id"])
            )
            .order_by(
                Message.created_at.asc()
            )
            .all()
        )

        messages = []

        for msg in history:

            if msg.sender_type == "user":

                messages.append(
                    (
                        "human",
                        msg.message_text
                    )
                )

            else:

                messages.append(
                    (
                        "assistant",
                        msg.message_text
                    )
                )

        return {
            **state,
            "history": messages
        }

    finally:

        db.close()