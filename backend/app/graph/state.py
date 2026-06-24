from typing import TypedDict, List, Tuple


class CompanionState(TypedDict, total=False):
    conversation_id: str
    companion_id: str
    companion_name: str
    user_message: str
    user_id: str
    user_profile: dict

    system_prompt: str

    memory: List[Tuple[str, str]]
    history: List[Tuple[str, str]]

    retrieved_context: str
    document_names: list[str]

    latest_document_name: str | None
    latest_document_id: str | None

    graph_context: str
    graph_nodes: list
    graph_edges: list
    hybrid_context: str

    long_term_memories: list[str]
    conversation_summaries: list[str]

    response: str