from backend.app.services.vector_store import (
    vector_store
)


retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 5
    }
)


def retrieve_context(
    query: str,
    user_id: str
):
    try:
        documents = vector_store.similarity_search(
            query,
            k=5,
            filter={"user_id": user_id}
        )
        return "\n\n".join(
            doc.page_content
            for doc in documents
        )
    except Exception as e:
        print(f"[RETRIEVER ERROR] {e}")
        return ""