import json
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.knowledge_node import KnowledgeNode
from backend.app.models.knowledge_edge import KnowledgeEdge
from backend.app.schemas.knowledge_graph_schema import (
    ExtractedGraphPayload
)
from backend.app.services.llm_provider import llm


class GraphExtractionService:
    """
    Service for extracting graph entities + relationships
    from document text or conversation text using LLM
    and storing them in PostgreSQL.
    """

    @staticmethod
    def extract_graph_from_text(
        text: str
    ) -> ExtractedGraphPayload:
        """
        Use LLM to extract graph nodes and edges
        from raw text.

        Returns:
            ExtractedGraphPayload
        """

        prompt = f"""
You are an information extraction engine.

Your task is to read the text below and extract a small knowledge graph.

Return ONLY valid JSON in this format:

{{
  "nodes": [
    {{
      "name": "FastAPI",
      "type": "technology",
      "description": "Python web framework"
    }}
  ],
  "edges": [
    {{
      "source": "AGIX",
      "target": "FastAPI",
      "relation": "USES",
      "evidence": "AGIX backend uses FastAPI"
    }}
  ]
}}

RULES:
1. Return ONLY JSON. No markdown. No explanation.
2. "nodes" should contain unique entities/concepts/projects/people/tools/topics.
3. "type" examples:
   - person
   - project
   - technology
   - document
   - topic
   - skill
   - company
   - goal
4. "edges" should represent meaningful relationships.
5. "relation" examples:
   - USES
   - BUILDS
   - LEARNS
   - WORKS_ON
   - RELATED_TO
   - STUDIES
   - CREATED
   - DEPENDS_ON
6. Keep graph compact and useful.
7. If nothing meaningful is found, return:
   {{
     "nodes": [],
     "edges": []
   }}

TEXT:
{text}
"""

        response = llm.invoke(
            [("human", prompt)]
        )

        raw_output = response.content.strip()

        # Clean accidental markdown fences if LLM adds them
        raw_output = raw_output.replace("```json", "")
        raw_output = raw_output.replace("```", "").strip()

        try:
            data = json.loads(raw_output)
            return ExtractedGraphPayload.model_validate(data)

        except Exception as e:
            print("[GRAPH EXTRACTION ERROR]")
            print("Raw LLM Output:")
            print(raw_output)
            raise ValueError(
                f"Failed to parse graph extraction output: {str(e)}"
            )

    @staticmethod
    def get_or_create_node(
        db: Session,
        user_id: UUID,
        node_name: str,
        node_type: str,
        description: Optional[str] = None,
        source_document_id: Optional[UUID] = None,
        source_conversation_id: Optional[UUID] = None
    ) -> KnowledgeNode:
        """
        Find existing node for the same user by name,
        otherwise create a new one.
        """

        existing_node = (
            db.query(KnowledgeNode)
            .filter(
                KnowledgeNode.user_id == user_id,
                KnowledgeNode.node_name == node_name
            )
            .first()
        )

        if existing_node:
            return existing_node

        node = KnowledgeNode(
            user_id=user_id,
            source_document_id=source_document_id,
            source_conversation_id=source_conversation_id,
            node_type=node_type,
            node_name=node_name,
            description=description
        )

        db.add(node)
        db.flush()

        return node

    @staticmethod
    def create_edge_if_not_exists(
        db: Session,
        user_id: UUID,
        source_node_id: UUID,
        target_node_id: UUID,
        relation_type: str,
        evidence_text: Optional[str] = None
    ) -> Optional[KnowledgeEdge]:
        """
        Create graph edge if it does not already exist.
        """

        existing_edge = (
            db.query(KnowledgeEdge)
            .filter(
                KnowledgeEdge.user_id == user_id,
                KnowledgeEdge.source_node_id == source_node_id,
                KnowledgeEdge.target_node_id == target_node_id,
                KnowledgeEdge.relation_type == relation_type
            )
            .first()
        )

        if existing_edge:
            return existing_edge

        edge = KnowledgeEdge(
            user_id=user_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relation_type=relation_type,
            evidence_text=evidence_text
        )

        db.add(edge)
        db.flush()

        return edge

    @staticmethod
    def extract_and_store_graph(
        db: Session,
        user_id: UUID,
        text: str,
        source_document_id: Optional[UUID] = None,
        source_conversation_id: Optional[UUID] = None
    ) -> ExtractedGraphPayload:
        """
        Full pipeline:
        1. Extract graph from text using LLM
        2. Save nodes
        3. Save edges
        4. Return extracted payload
        """

        graph_payload = GraphExtractionService.extract_graph_from_text(
            text=text
        )

        node_map = {}

        # 1) Save nodes
        for node_data in graph_payload.nodes:
            node = GraphExtractionService.get_or_create_node(
                db=db,
                user_id=user_id,
                node_name=node_data.name,
                node_type=node_data.type,
                description=node_data.description,
                source_document_id=source_document_id,
                source_conversation_id=source_conversation_id
            )

            node_map[node_data.name] = node

        # 2) Save edges
        for edge_data in graph_payload.edges:
            source_node = node_map.get(edge_data.source)
            target_node = node_map.get(edge_data.target)

            if not source_node or not target_node:
                continue

            GraphExtractionService.create_edge_if_not_exists(
                db=db,
                user_id=user_id,
                source_node_id=source_node.id,
                target_node_id=target_node.id,
                relation_type=edge_data.relation,
                evidence_text=edge_data.evidence
            )

        db.flush()

        return graph_payload