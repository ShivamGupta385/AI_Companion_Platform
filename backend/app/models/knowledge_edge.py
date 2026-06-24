# backend/app/models/knowledge_edge.py
import uuid
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.db.base import Base


class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    source_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_nodes.id")
    )

    target_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_nodes.id")
    )

    relation_type: Mapped[str] = mapped_column(
        String(100)
    )
    # examples:
    # USES, WORKS_ON, HAS_FEATURE, MENTIONS, RELATED_TO, UPLOADED

    evidence_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )