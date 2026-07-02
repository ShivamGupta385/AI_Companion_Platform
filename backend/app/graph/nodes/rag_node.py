import traceback
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
    "what project am i working on",
    "what am i learning",
]


def is_memory_query(query: str) -> bool:
    query_lower = query.lower().strip()
    return any(
        keyword in query_lower
        for keyword in MEMORY_QUERY_KEYWORDS
    )


def rag_node(state):
    try:
        query = state.get("user_message", "")

        if not query or not query.strip():
            print("=" * 60)
            print("[RAG NODE] Empty query")
            print("=" * 60)
            return {
                **state,
                "retrieved_context": ""
            }

        query = query.strip()

        if is_memory_query(query):
            print("=" * 60)
            print("[RAG NODE] Memory query detected")
            print("QUERY:", query)
            print("Skipping vector retrieval")
            print("=" * 60)

            return {
                **state,
                "retrieved_context": ""
            }

        print("=" * 60)
        print("[RAG NODE] Running retrieval")
        print("QUERY:", query)

        context = retrieve_context(query)

        if context is None:
            context = ""

        print("[RAG NODE] CONTEXT LENGTH:", len(context))
        print("[RAG NODE] CONTEXT PREVIEW:")
        # Encode safely for Windows terminals that may not support all Unicode chars
        preview = (context[:500] if context else "No retrieved context")
        safe_preview = preview.encode("ascii", errors="replace").decode("ascii")
        print(safe_preview)
        print("=" * 60)

        return {
            **state,
            "retrieved_context": context
        }

    except Exception as e:
        print("=" * 60)
        print("[RAG NODE ERROR]")
        print("ERROR:", str(e).encode("ascii", errors="replace").decode("ascii"))
        traceback.print_exc()
        print("=" * 60)
        # Return empty context so the graph can continue rather than crashing
        return {
            **state,
            "retrieved_context": ""
        }