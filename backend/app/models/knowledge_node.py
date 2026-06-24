# backend/app/models/knowledge_node.py
import uuid
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.db.base import Base


class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id"),
        nullable=True
    )

    source_conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversations.id"),
        nullable=True
    )

    node_type: Mapped[str] = mapped_column(
        String(100)
    )
    # examples: person, technology, project, topic, company, skill, feature

    node_name: Mapped[str] = mapped_column(
        String(255),
        index=True
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )