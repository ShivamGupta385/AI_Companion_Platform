import os
from typing import Dict, Any

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.app.services.vector_store import vector_store
from backend.app.utils.text_cleaner import clean_text


def ingest_document(
    file_path: str,
    document_id: str,
    user_id: str,
    file_name: str
) -> Dict[str, Any]:
    """
    Load document, split into chunks, attach metadata,
    generate embeddings, store in vector DB,
    and return full extracted text for Graph RAG.

    Returns:
    {
        "chunk_count": int,
        "full_text": str
    }
    """

    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == ".pdf":
        loader = PyPDFLoader(file_path)
    elif file_extension == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
    elif file_extension == ".docx":
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError(
            f"Unsupported file type for ingestion: {file_extension}"
        )

    print("=" * 60)
    print("[INGESTION START]")
    print("FILE PATH:", file_path)
    print("FILE NAME:", file_name)
    print("DOCUMENT ID:", document_id)
    print("USER ID:", user_id)
    print("EXTENSION:", file_extension)
    print("=" * 60)

    documents = loader.load()

    print("[INGESTION] Loaded raw documents:", len(documents))

    cleaned_documents = []

    # --------------------------------------------------
    # Clean raw document pages
    # --------------------------------------------------
    for doc in documents:
        if not doc.page_content:
            continue

        text = clean_text(doc.page_content)

        if not text.strip():
            continue

        doc.page_content = text
        cleaned_documents.append(doc)

    print("[INGESTION] Cleaned documents:", len(cleaned_documents))

    if not cleaned_documents:
        return {
            "chunk_count": 0,
            "full_text": ""
        }

    # --------------------------------------------------
    # Build cleaned full text for Graph RAG
    # --------------------------------------------------
    full_text = clean_text(
        "\n\n".join(
            doc.page_content for doc in cleaned_documents
        ).strip()
    )

    print("[INGESTION] Full text length:", len(full_text))

    # --------------------------------------------------
    # Split documents into chunks for Vector RAG
    # --------------------------------------------------
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.split_documents(cleaned_documents)

    clean_chunks = []

    for chunk in chunks:
        try:
            text = clean_text(chunk.page_content)

            if not text.strip():
                continue

            chunk.page_content = text

            chunk.metadata.update(
                {
                    "document_id": str(document_id),
                    "user_id": str(user_id),
                    "source": clean_text(str(file_name))
                }
            )

            clean_chunks.append(chunk)

        except Exception as e:
            print(f"[INGESTION] Skipping bad chunk: {e}")

    print("[INGESTION] Final clean chunks:", len(clean_chunks))

    if clean_chunks:
        vector_store.add_documents(clean_chunks)

    print("=" * 60)
    print(
        f"[INGESTION COMPLETE] Indexed "
        f"{len(clean_chunks)} chunks for {file_name}"
    )
    print("=" * 60)

    return {
        "chunk_count": len(clean_chunks),
        "full_text": full_text
    }