import uuid

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.db.base import Base


class TaskHistory(Base):
    __tablename__ = "task_history"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id")
    )

    companion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companions.id")
    )

    task_type: Mapped[str] = mapped_column(
        String(50)
    )

    status: Mapped[str] = mapped_column(
        String(50)
    )

    metrics: Mapped[dict] = mapped_column(
        JSONB
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )