# backend/app/graph/state.py

from typing import TypedDict, List, Tuple, Optional, Any


class CompanionState(TypedDict, total=False):
    # --------------------------------------------------
    # Identity / request context
    # --------------------------------------------------
    conversation_id: str
    companion_id: str
    companion_name: str
    user_id: str
    user_message: str
    user_profile: dict

    # --------------------------------------------------
    # Companion prompting
    # --------------------------------------------------
    system_prompt: str

    # --------------------------------------------------
    # Short-term thread memory
    # --------------------------------------------------
    memory: List[Tuple[str, str]]
    history: List[Tuple[str, str]]

    # --------------------------------------------------
    # Document context
    # --------------------------------------------------
    document_names: List[str]
    latest_document_name: Optional[str]
    latest_document_id: Optional[str]

    # --------------------------------------------------
    # Vector RAG
    # --------------------------------------------------
    retrieved_context: str

    # --------------------------------------------------
    # Graph RAG
    # --------------------------------------------------
    graph_context: str
    graph_nodes: List[Any]
    graph_edges: List[Any]

    # --------------------------------------------------
    # Final merged context
    # --------------------------------------------------
    hybrid_context: str

    # --------------------------------------------------
    # Long-term memory
    # --------------------------------------------------
    long_term_memories: List[str]
    conversation_summaries: List[str]

    # --------------------------------------------------
    # CROSS-AGENT MEMORY (NEW)
    # --------------------------------------------------
    # Memories written by OTHER companions about this user
    cross_agent_memories: List[dict]
    # Example structure per item:
    # {
    #     "source_companion": "Noor",
    #     "memory_type": "Sleep Patterns",
    #     "content": "User averages 4-5 hours of sleep on weeknights",
    #     "timestamp": "2025-01-15T08:00:00Z",
    #     "confidence": 0.9
    # }

    # Structured cross-agent context string
    # (built from cross_agent_memories, injected into prompt)
    cross_agent_context: str

    # --------------------------------------------------
    # Output
    # --------------------------------------------------
    response: str