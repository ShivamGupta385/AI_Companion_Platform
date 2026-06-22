import uuid

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.db.base import Base


class UserMemory(Base):
    __tablename__ = "user_memories"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id")
    )

    companion_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("companions.id"),
        nullable=True
    )

    memory_type: Mapped[str] = mapped_column(
        String(50)
    )
    # examples:
    # preference
    # project_context
    # learning_goal
    # personal_fact
    # conversation_insight

    memory_text: Mapped[str] = mapped_column(
        Text
    )

    source_conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversations.id"),
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )