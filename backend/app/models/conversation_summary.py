import uuid

from sqlalchemy import (
    Text,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
from sqlalchemy.sql import func

from backend.app.db.base import Base


class ConversationSummary(Base):
    """
    Stores one reusable summary per conversation thread.

    Purpose:
    - summarize older conversation context
    - support cross-conversation memory recall
    - reduce need to pass full message history into the LLM
    """

    __tablename__ = "conversation_summaries"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    # One summary row per conversation
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id"),
        unique=True,
        nullable=False
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    companion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companions.id"),
        nullable=False
    )

    summary_text: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )