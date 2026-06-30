import traceback

from backend.app.services.retriever_service import retrieve_context
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


async def rag_node(state):
    try:
        query = clean_text(state.get("user_message", ""))

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

        context = await retrieve_context(query)

        if context is None:
            context = ""

        context = clean_text(context)

        print("[RAG NODE] CONTEXT LENGTH:", len(context))
        print("[RAG NODE] CONTEXT PREVIEW:")
        print(context[:500] if context else "No retrieved context")
        print("=" * 60)

        return {
            **state,
            "retrieved_context": context
        }

    except Exception as e:
        print("=" * 60)
        print("[RAG NODE ERROR]")
        print("ERROR:", str(e))
        traceback.print_exc()
        print("=" * 60)
        raise