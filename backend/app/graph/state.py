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
    # Output
    # --------------------------------------------------
    response: str