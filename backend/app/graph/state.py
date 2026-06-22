from typing import TypedDict, List, Tuple


class CompanionState(TypedDict, total=False):
    # Core conversation context
    conversation_id: str
    companion_id: str
    companion_name: str
    user_message: str
    user_id: str

    # User onboarding / profile context
    user_profile: dict

    # Prompt created by companion node
    system_prompt: str

    # Short-term thread memory from current conversation
    memory: List[Tuple[str, str]]

    # Optional thread history / reserved future use
    history: List[Tuple[str, str]]

    # Long-term cross-conversation memory
    long_term_memories: List[str]
    conversation_summaries: List[str]

    # RAG / documents
    retrieved_context: str
    document_names: list

    # Final response
    response: str