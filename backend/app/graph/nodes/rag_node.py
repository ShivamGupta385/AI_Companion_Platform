from backend.app.services.retriever_service import retrieve_context


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
]


def is_memory_query(query: str) -> bool:
    query_lower = query.lower().strip()

    return any(keyword in query_lower for keyword in MEMORY_QUERY_KEYWORDS)


def rag_node(state):
    query = state["user_message"]

    # If user is asking about previous conversation / memory,
    # do NOT use document retrieval as the primary source.
    if is_memory_query(query):
        print("=" * 50)
        print("[RAG NODE] Memory-style query detected")
        print("QUERY:", query)
        print("Skipping document retrieval for this query.")
        print("=" * 50)

        return {
            **state,
            "retrieved_context": ""
        }

    # Otherwise, run normal RAG retrieval
    context = retrieve_context(query)

    print("=" * 50)
    print("[RAG NODE] Document / knowledge query")
    print("QUERY:", query)
    print("CONTEXT LENGTH:", len(context))
    print("CONTEXT:")
    print(context[:500])
    print("=" * 50)

    return {
        **state,
        "retrieved_context": context
    }