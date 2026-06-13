import uuid

from sqlalchemy import String, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base

class UserInsight(Base):
    __tablename__ = "user_insights"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id")
    )

    analyzing_companion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companions.id")
    )

    insight_type: Mapped[str] = mapped_column(
        String(50)
    )

    summary_text: Mapped[str] = mapped_column(
        Text
    )

    confidence_score: Mapped[float] = mapped_column(
        Float
    )