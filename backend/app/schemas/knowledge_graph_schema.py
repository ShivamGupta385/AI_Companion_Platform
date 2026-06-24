import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


# =========================================================
# KNOWLEDGE NODE SCHEMAS
# =========================================================

class KnowledgeNodeBase(BaseModel):
    node_type: str
    node_name: str
    description: Optional[str] = None


class KnowledgeNodeCreate(KnowledgeNodeBase):
    user_id: Optional[uuid.UUID] = None
    source_document_id: Optional[uuid.UUID] = None
    source_conversation_id: Optional[uuid.UUID] = None


class KnowledgeNodeResponse(KnowledgeNodeBase):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    source_document_id: Optional[uuid.UUID] = None
    source_conversation_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# KNOWLEDGE EDGE SCHEMAS
# =========================================================

class KnowledgeEdgeBase(BaseModel):
    source_node_id: uuid.UUID
    target_node_id: uuid.UUID
    relation_type: str
    evidence_text: Optional[str] = None


class KnowledgeEdgeCreate(KnowledgeEdgeBase):
    user_id: Optional[uuid.UUID] = None


class KnowledgeEdgeResponse(KnowledgeEdgeBase):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# GRAPH EXTRACTION PAYLOAD SCHEMAS
# Used for LLM output parsing before saving to DB
# =========================================================

class ExtractedGraphNode(BaseModel):
    name: str
    type: str
    description: Optional[str] = None


class ExtractedGraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    evidence: Optional[str] = None


class ExtractedGraphPayload(BaseModel):
    nodes: List[ExtractedGraphNode] = []
    edges: List[ExtractedGraphEdge] = []


# =========================================================
# GRAPH CONTEXT RESPONSE SCHEMA
# Optional schema if you want to expose graph retrieval output
# through an API later
# =========================================================

class GraphContextResponse(BaseModel):
    graph_context: str
    nodes: List[KnowledgeNodeResponse] = []
    edges: List[KnowledgeEdgeResponse] = []


# =========================================================
# OPTIONAL: DETAILED GRAPH VIEW RESPONSE
# Useful if later you want /graph/user or /graph/document APIs
# =========================================================

class KnowledgeGraphResponse(BaseModel):
    nodes: List[KnowledgeNodeResponse]
    edges: List[KnowledgeEdgeResponse]