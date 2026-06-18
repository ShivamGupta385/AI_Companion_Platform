from backend.app.services.retriever_service import (
    retrieve_context
)


def rag_node(state):

    query = state["user_message"]

    context = retrieve_context(query)

    print("=" * 50)
    print("QUERY:", query)
    print("CONTEXT LENGTH:", len(context))
    print("CONTEXT:")
    print(context[:500])
    print("=" * 50)

    state["retrieved_context"] = context

    return state