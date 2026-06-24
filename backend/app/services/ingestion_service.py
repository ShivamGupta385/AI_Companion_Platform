import os

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader
)
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from backend.app.services.vector_store import vector_store


def ingest_document(
    file_path: str,
    document_id: str,
    user_id: str,
    file_name: str
) -> int:
    """
    Load document, split into chunks, attach metadata,
    generate embeddings, and store in PGVector.

    Supported:
    - PDF
    - TXT
    - DOCX
    """

    file_extension = os.path.splitext(file_path)[1].lower()

    # --------------------------------------------------
    # Choose correct loader
    # --------------------------------------------------
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

    # --------------------------------------------------
    # Load raw documents
    # --------------------------------------------------
    documents = loader.load()

    print("[INGESTION] Loaded raw documents:", len(documents))

    if documents:
        for idx, doc in enumerate(documents[:3], start=1):
            preview = doc.page_content[:500] if doc.page_content else ""
            print(f"[RAW DOC {idx}] preview:")
            print(preview)
            print("-" * 50)

    # --------------------------------------------------
    # Clean empty docs before splitting
    # --------------------------------------------------
    cleaned_documents = []

    for doc in documents:
        if not doc.page_content:
            continue

        text = doc.page_content.strip()
        if not text:
            continue

        doc.page_content = text
        cleaned_documents.append(doc)

    print("[INGESTION] Cleaned documents:", len(cleaned_documents))

    if not cleaned_documents:
        print(f"[INGESTION] No usable text found in {file_name}")
        return 0

    # --------------------------------------------------
    # Split into chunks
    # --------------------------------------------------
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.split_documents(cleaned_documents)

    print("[INGESTION] Chunks after split:", len(chunks))

    # --------------------------------------------------
    # Attach metadata + clean chunk text
    # --------------------------------------------------
    clean_chunks = []

    for chunk in chunks:
        try:
            text = (
                chunk.page_content
                .encode("utf-8", errors="ignore")
                .decode("utf-8")
                .strip()
            )

            if not text:
                continue

            chunk.page_content = text

            chunk.metadata.update(
                {
                    "document_id": str(document_id),
                    "user_id": str(user_id),
                    "source": str(file_name)
                }
            )

            clean_chunks.append(chunk)

        except Exception as e:
            print(f"[INGESTION] Skipping bad chunk: {e}")

    print("[INGESTION] Final clean chunks:", len(clean_chunks))

    if clean_chunks:
        for idx, chunk in enumerate(clean_chunks[:3], start=1):
            print(f"[CHUNK {idx}] metadata:", chunk.metadata)
            print(f"[CHUNK {idx}] preview:", chunk.page_content[:400])
            print("-" * 50)

    # --------------------------------------------------
    # Store in vector DB
    # --------------------------------------------------
    if clean_chunks:
        vector_store.add_documents(clean_chunks)

    print("=" * 60)
    print(
        f"Successfully indexed {len(clean_chunks)} chunks for {file_name}"
    )
    print("=" * 60)

    return len(clean_chunks)