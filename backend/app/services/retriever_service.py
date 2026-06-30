from backend.app.services.vector_store import (
    vector_store
)


retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 5
    }
)


async def retrieve_context(
    query: str
):

    documents = await retriever.ainvoke(
        query
    )

    return "\n\n".join(
        doc.page_content
        for doc in documents
    )