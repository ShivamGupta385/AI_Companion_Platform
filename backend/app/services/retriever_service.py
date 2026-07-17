# backend/app/services/retriever_service.py

from typing import Optional

from backend.app.services.vector_store import vector_store


retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 5
    }
)


async def retrieve_context(
    query: str,
    user_id: Optional[str] = None,
    document_id: Optional[str] = None,
    file_name: Optional[str] = None,
) -> str:
    """
    Retrieve relevant document chunks for a query.

    Args:
        query: The search query
        user_id: REQUIRED — only search this user's documents
        document_id: If provided, ONLY search within this document
        file_name: If provided (and no document_id), filter by filename

    Returns:
        Joined page content from retrieved chunks
    """

    # --------------------------------------------------
    # Build metadata filter
    # ALWAYS include user_id to prevent cross-user leaks
    # --------------------------------------------------
    search_filter = {}

    if user_id:
        search_filter["user_id"] = str(user_id)

    if document_id:
        search_filter["document_id"] = str(document_id)
        print(f"[RETRIEVER] Filtering by document_id: {document_id}")

    elif file_name:
        search_filter["source"] = file_name
        print(f"[RETRIEVER] Filtering by file_name: {file_name}")

    print(f"[RETRIEVER] User ID filter: {user_id}")
    print(f"[RETRIEVER] Full filter: {search_filter}")

    # --------------------------------------------------
    # Invoke retriever with filter
    # --------------------------------------------------
    if search_filter:
        documents = await retriever.ainvoke(
            query,
            filter=search_filter
        )
    else:
        documents = await retriever.ainvoke(query)

    # --------------------------------------------------
    # Join results
    # --------------------------------------------------
    if not documents:
        print("[RETRIEVER] No documents retrieved")
        return ""

    print(f"[RETRIEVER] Retrieved {len(documents)} chunks")

    for i, doc in enumerate(documents):
        source = doc.metadata.get("source", "unknown")
        doc_id = doc.metadata.get("document_id", "unknown")
        preview = doc.page_content[:100].replace("\n", " ")
        print(f"  Chunk {i+1}: source={source} | doc_id={doc_id} | {preview}...")

    return "\n\n".join(
        doc.page_content
        for doc in documents
    )