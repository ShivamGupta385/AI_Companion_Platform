from langchain_community.document_loaders import (
    PyPDFLoader
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from backend.app.services.vector_store import (
    vector_store
)


def ingest_document(
    file_path: str,
    document_id: str,
    user_id: str,
    file_name: str
):
    """
    Load document,
    split into chunks,
    generate embeddings,
    store in PGVector.
    """

    loader = PyPDFLoader(
        file_path
    )

    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.split_documents(
        documents
    )

    for chunk in chunks:

        chunk.metadata.update(
            {
                "document_id": document_id,
                "user_id": user_id,
                "source": file_name
            }
        )

    clean_chunks = []

    for chunk in chunks:

        try:

            text = (
                chunk.page_content
                .encode(
                    "utf-8",
                    errors="ignore"
                )
                .decode("utf-8")
            )

            chunk.page_content = text

            clean_chunks.append(
                chunk
            )

        except Exception as e:

            print(
                f"Skipping bad chunk: {e}"
            )

    vector_store.add_documents(
        clean_chunks
    )

    print(
        f"Successfully indexed "
        f"{len(clean_chunks)} chunks "
        f"for {file_name}"
    )

    return len(clean_chunks)