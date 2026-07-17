# backend/app/graph/nodes/graph_rag_node.py

from uuid import UUID

from backend.app.db.session import SessionLocal
from backend.app.services.graph_retriever_service import (
    GraphRetrieverService
)
from backend.app.utils.text_cleaner import clean_text


MEMORY_QUERY_KEYWORDS = [
    "remember",
    "last conversation",
    "previous conversation",
    "previous chat",
    "earlier conversation",
    "what did we discuss",
    "what did i say",
    "what did we do",
    "continue from last time",
    "continue from previous",
    "do you remember",
    "our last chat",
    "earlier in this chat",
    "what project am i working on",
    "what am i learning",
]


def is_memory_query(query: str) -> bool:
    query_lower = query.lower().strip()
    return any(
        keyword in query_lower
        for keyword in MEMORY_QUERY_KEYWORDS
    )


def _serialize_nodes(nodes) -> list:
    """
    Convert SQLAlchemy KnowledgeNode objects to plain dicts
    so LangGraph's msgpack checkpointer can serialize them.
    """
    serialized = []
    for node in nodes:
        serialized.append({
            "id": str(node.id) if node.id else None,
            "node_name": node.node_name,
            "node_type": node.node_type,
            "description": node.description,
        })
    return serialized


def _serialize_edges(edges) -> list:
    """
    Convert SQLAlchemy KnowledgeEdge objects to plain dicts
    so LangGraph's msgpack checkpointer can serialize them.
    """
    serialized = []
    for edge in edges:
        serialized.append({
            "id": str(edge.id) if edge.id else None,
            "source_node_id": str(edge.source_node_id) if edge.source_node_id else None,
            "target_node_id": str(edge.target_node_id) if edge.target_node_id else None,
            "relation_type": edge.relation_type,
            "evidence_text": edge.evidence_text,
        })
    return serialized


def graph_rag_node(state):
    """
    LangGraph node for Graph RAG retrieval.

    Responsibilities:
    1. Read user_id and current user_message from state
    2. Query knowledge_nodes + knowledge_edges through GraphRetrieverService
    3. Build graph context text
    4. Merge vector RAG context + graph RAG context into hybrid_context
    5. Store graph fields back into graph state

    IMPORTANT: All SQLAlchemy objects MUST be converted to plain
    dicts before returning in state, because LangGraph's PostgreSQL
    checkpointer uses msgpack which cannot serialize ORM objects.
    """

    db = SessionLocal()

    try:
        user_id = state.get("user_id")
        query = clean_text(state.get("user_message", ""))
        retrieved_context = clean_text(
            state.get("retrieved_context", "")
        )

        if not user_id or not query:
            print("[GRAPH RAG NODE] Missing user_id or query")

            return {
                **state,
                "graph_context": "",
                "graph_nodes": [],
                "graph_edges": [],
                "hybrid_context": retrieved_context or ""
            }

        # ---------------------------------------------------------
        # Skip graph retrieval for memory-style questions
        # ---------------------------------------------------------
        if is_memory_query(query):
            print("=" * 60)
            print("[GRAPH RAG NODE] Memory-style query detected")
            print("QUERY:", query)
            print("Skipping graph retrieval for this query.")
            print("=" * 60)

            return {
                **state,
                "graph_context": "",
                "graph_nodes": [],
                "graph_edges": [],
                "hybrid_context": retrieved_context or ""
            }

        # ---------------------------------------------------------
        # Retrieve graph data
        # ---------------------------------------------------------
        graph_result = GraphRetrieverService.retrieve_graph_context(
            db=db,
            user_id=UUID(user_id),
            query=query,
            node_limit=10,
            edge_limit=20
        )

        raw_graph_context = graph_result.get("graph_context", "")
        raw_graph_nodes = graph_result.get("graph_nodes", []) or []
        raw_graph_edges = graph_result.get("graph_edges", []) or []

        graph_context = clean_text(raw_graph_context)

        # ---------------------------------------------------------
        # CRITICAL: Serialize SQLAlchemy objects to plain dicts
        # LangGraph's msgpack checkpointer cannot serialize ORM objects
        # ---------------------------------------------------------
        graph_nodes = _serialize_nodes(raw_graph_nodes)
        graph_edges = _serialize_edges(raw_graph_edges)

        # ---------------------------------------------------------
        # Build hybrid context
        # ---------------------------------------------------------
        hybrid_parts = []

        if retrieved_context:
            hybrid_parts.append(
                f"DOCUMENT / VECTOR RAG CONTEXT:\n{retrieved_context}"
            )

        if graph_context:
            hybrid_parts.append(
                f"GRAPH RAG CONTEXT:\n{graph_context}"
            )

        hybrid_context = clean_text(
            "\n\n".join(hybrid_parts).strip()
        )

        print("=" * 60)
        print("[GRAPH RAG NODE]")
        print("USER ID:", user_id)
        print("QUERY:", query)
        print("GRAPH NODES:", len(graph_nodes))
        print("GRAPH EDGES:", len(graph_edges))
        print("GRAPH CONTEXT LENGTH:", len(graph_context))
        print("HYBRID CONTEXT LENGTH:", len(hybrid_context))
        print("=" * 60)

        if graph_context:
            print("[GRAPH CONTEXT PREVIEW]")
            print(graph_context[:1500])

        return {
            **state,
            "graph_context": graph_context,
            "graph_nodes": graph_nodes,
            "graph_edges": graph_edges,
            "hybrid_context": hybrid_context
        }

    except Exception as e:
        print(f"[GRAPH RAG NODE ERROR] {e}")

        return {
            **state,
            "graph_context": "",
            "graph_nodes": [],
            "graph_edges": [],
            "hybrid_context": clean_text(
                state.get("retrieved_context", "")
            )
        }

    finally:
        db.close()