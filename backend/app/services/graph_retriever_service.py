# backend/app/services/graph_retriever_service.py

from uuid import UUID
from typing import List, Dict, Set

from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.models.knowledge_node import KnowledgeNode
from backend.app.models.knowledge_edge import KnowledgeEdge


class GraphRetrieverService:
    """
    Graph retrieval service for AGIX Graph RAG.

    Responsibilities:
    1. Search graph nodes relevant to a user query
    2. Fetch connected edges
    3. Build graph context text for LLM consumption
    """

    @staticmethod
    def _build_query_terms(query: str) -> List[str]:
        """
        Convert user query into simple searchable terms.
        """
        terms = []

        for word in query.lower().split():
            clean_word = word.strip(".,!?():;[]{}\"'").strip()
            if clean_word and len(clean_word) > 2:
                terms.append(clean_word)

        # remove duplicates while preserving order
        unique_terms = []
        seen = set()

        for term in terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)

        return unique_terms

    @staticmethod
    def retrieve_relevant_nodes(
        db: Session,
        user_id: UUID,
        query: str,
        limit: int = 10
    ) -> List[KnowledgeNode]:
        """
        Find graph nodes relevant to the user's query.
        Matching is done using node_name and description.
        """

        query_terms = GraphRetrieverService._build_query_terms(query)

        if not query_terms:
            return []

        conditions = []

        for term in query_terms:
            conditions.append(
                KnowledgeNode.node_name.ilike(f"%{term}%")
            )
            conditions.append(
                KnowledgeNode.description.ilike(f"%{term}%")
            )

        nodes = (
            db.query(KnowledgeNode)
            .filter(
                KnowledgeNode.user_id == user_id,
                or_(*conditions)
            )
            .limit(limit)
            .all()
        )

        return nodes

    @staticmethod
    def retrieve_connected_edges(
        db: Session,
        user_id: UUID,
        node_ids: List[UUID],
        limit: int = 20
    ) -> List[KnowledgeEdge]:
        """
        Fetch edges connected to the matched nodes.
        """

        if not node_ids:
            return []

        edges = (
            db.query(KnowledgeEdge)
            .filter(
                KnowledgeEdge.user_id == user_id,
                or_(
                    KnowledgeEdge.source_node_id.in_(node_ids),
                    KnowledgeEdge.target_node_id.in_(node_ids)
                )
            )
            .limit(limit)
            .all()
        )

        return edges

    @staticmethod
    def retrieve_nodes_by_ids(
        db: Session,
        node_ids: List[UUID]
    ) -> List[KnowledgeNode]:
        """
        Fetch nodes by list of ids.
        """

        if not node_ids:
            return []

        return (
            db.query(KnowledgeNode)
            .filter(KnowledgeNode.id.in_(node_ids))
            .all()
        )

    @staticmethod
    def build_graph_context(
        db: Session,
        user_id: UUID,
        query: str,
        node_limit: int = 10,
        edge_limit: int = 20
    ) -> str:
        """
        Main Graph RAG retrieval method.

        Flow:
        1. Retrieve relevant nodes
        2. Retrieve connected edges
        3. Retrieve all nodes participating in those edges
        4. Build a graph context string for LLM
        """

        matched_nodes = GraphRetrieverService.retrieve_relevant_nodes(
            db=db,
            user_id=user_id,
            query=query,
            limit=node_limit
        )

        if not matched_nodes:
            return ""

        matched_node_ids = [node.id for node in matched_nodes]

        edges = GraphRetrieverService.retrieve_connected_edges(
            db=db,
            user_id=user_id,
            node_ids=matched_node_ids,
            limit=edge_limit
        )

        # collect all node ids involved in edges
        all_node_ids: Set[UUID] = set(matched_node_ids)

        for edge in edges:
            all_node_ids.add(edge.source_node_id)
            all_node_ids.add(edge.target_node_id)

        all_nodes = GraphRetrieverService.retrieve_nodes_by_ids(
            db=db,
            node_ids=list(all_node_ids)
        )

        node_map: Dict[UUID, KnowledgeNode] = {
            node.id: node for node in all_nodes
        }

        lines = []
        lines.append("GRAPH KNOWLEDGE CONTEXT")
        lines.append("")

        # Section 1: matched nodes
        lines.append("Relevant Entities:")
        for node in matched_nodes:
            description = node.description or "No description"
            lines.append(
                f"- {node.node_name} ({node.node_type}): {description}"
            )

        # Section 2: relationships
        if edges:
            lines.append("")
            lines.append("Relationships:")

            for edge in edges:
                source_node = node_map.get(edge.source_node_id)
                target_node = node_map.get(edge.target_node_id)

                source_name = (
                    source_node.node_name
                    if source_node else str(edge.source_node_id)
                )
                target_name = (
                    target_node.node_name
                    if target_node else str(edge.target_node_id)
                )

                relation_line = (
                    f"- {source_name} --{edge.relation_type}--> {target_name}"
                )

                if edge.evidence_text:
                    relation_line += f" | Evidence: {edge.evidence_text}"

                lines.append(relation_line)

        return "\n".join(lines)

    @staticmethod
    def retrieve_graph_payload(
        db: Session,
        user_id: UUID,
        query: str,
        node_limit: int = 10,
        edge_limit: int = 20
    ) -> dict:
        """
        Optional structured retrieval method if you want
        to inspect graph retrieval results in API / debugging.
        """

        matched_nodes = GraphRetrieverService.retrieve_relevant_nodes(
            db=db,
            user_id=user_id,
            query=query,
            limit=node_limit
        )

        matched_node_ids = [node.id for node in matched_nodes]

        edges = GraphRetrieverService.retrieve_connected_edges(
            db=db,
            user_id=user_id,
            node_ids=matched_node_ids,
            limit=edge_limit
        )

        return {
            "nodes": matched_nodes,
            "edges": edges,
            "graph_context": GraphRetrieverService.build_graph_context(
                db=db,
                user_id=user_id,
                query=query,
                node_limit=node_limit,
                edge_limit=edge_limit
            )
        }

    @staticmethod
    def retrieve_graph_context(
        db: Session,
        user_id: UUID,
        query: str,
        node_limit: int = 10,
        edge_limit: int = 20
    ) -> dict:
        """
        Graph RAG retrieval method that returns the exact structure
        expected by graph_rag_node.py.

        Returns:
            {
                "graph_context": str,   # formatted text for LLM
                "graph_nodes": list,    # matched KnowledgeNode objects
                "graph_edges": list     # connected KnowledgeEdge objects
            }
        """
        payload = GraphRetrieverService.retrieve_graph_payload(
            db=db,
            user_id=user_id,
            query=query,
            node_limit=node_limit,
            edge_limit=edge_limit
        )

        return {
            "graph_context": payload.get("graph_context", ""),
            "graph_nodes": payload.get("nodes", []),
            "graph_edges": payload.get("edges", []),
        }