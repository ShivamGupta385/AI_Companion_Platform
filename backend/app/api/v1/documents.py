import os
import uuid
from sqlalchemy import or_

from backend.app.models.knowledge_node import KnowledgeNode
from backend.app.models.knowledge_edge import KnowledgeEdge

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    status,
    Form
)
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.models.companion import Companion
from backend.app.schemas.document_schema import DocumentResponse
from backend.app.services.ingestion_service import ingest_document
from backend.app.services.graph_extraction_service import (
    GraphExtractionService
)
from backend.app.core.security import get_current_user

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_document(
    file: UploadFile = File(...),
    companion_id: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document, save metadata in PostgreSQL,
    ingest it into vector RAG, and extract Graph RAG knowledge.
    """

    allowed_extensions = [".pdf", ".txt", ".docx"]

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file name"
        )

    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, TXT and DOCX files are allowed"
        )

    # --------------------------------------------------
    # Validate companion_id if provided
    # --------------------------------------------------
    companion = None

    if companion_id:
        companion = (
            db.query(Companion)
            .filter(Companion.id == companion_id)
            .first()
        )

        if not companion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Companion not found"
            )

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        # --------------------------------------------------
        # 1) Save physical file
        # --------------------------------------------------
        content = await file.read()

        with open(file_path, "wb") as buffer:
            buffer.write(content)

        # --------------------------------------------------
        # 2) Create document row (DO NOT COMMIT YET)
        # --------------------------------------------------
        document = Document(
            user_id=current_user.id,
            companion_id=companion.id if companion else None,
            file_name=file.filename,
            file_path=file_path
        )

        db.add(document)
        db.flush()
        db.refresh(document)

        print("=" * 60)
        print("[DOCUMENT UPLOAD]")
        print("DOCUMENT ID:", document.id)
        print("FILE NAME:", document.file_name)
        print("USER ID:", current_user.id)
        print("COMPANION ID:", document.companion_id)
        print("FILE PATH:", file_path)
        print("=" * 60)

        # --------------------------------------------------
        # 3) Vector ingestion
        # --------------------------------------------------
        ingestion_result = await ingest_document(
            file_path=file_path,
            document_id=str(document.id),
            user_id=str(current_user.id),
            file_name=document.file_name
        )

        chunk_count = ingestion_result.get("chunk_count", 0)
        full_text = ingestion_result.get("full_text", "")

        print("=" * 60)
        print("[VECTOR INGESTION RESULT]")
        print("CHUNK COUNT:", chunk_count)
        print("FULL TEXT LENGTH:", len(full_text))
        print("=" * 60)

        # --------------------------------------------------
        # 4) Graph extraction
        # --------------------------------------------------
        if full_text and full_text.strip():
            try:
                graph_text = full_text[:12000]

                graph_payload = GraphExtractionService.extract_and_store_graph(
                    db=db,
                    user_id=current_user.id,
                    text=graph_text,
                    source_document_id=document.id
                )

                print("=" * 60)
                print("[GRAPH EXTRACTION COMPLETE]")
                print("NODES EXTRACTED:", len(graph_payload.nodes))
                print("EDGES EXTRACTED:", len(graph_payload.edges))
                print("=" * 60)

            except Exception as graph_error:
                print("=" * 60)
                print("[GRAPH EXTRACTION ERROR]")
                print(str(graph_error))
                print("Document upload + vector ingestion succeeded.")
                print("Skipping graph extraction failure.")
                print("=" * 60)
        else:
            print("[GRAPH EXTRACTION] Skipped because full_text is empty")

        # --------------------------------------------------
        # 5) Commit final transaction once
        # --------------------------------------------------
        db.commit()
        db.refresh(document)

        return DocumentResponse(
            id=document.id,
            user_id=document.user_id,
            companion_id=document.companion_id,
            companion_name=companion.name if companion else None,
            file_name=document.file_name,
            file_path=document.file_path,
            uploaded_at=document.uploaded_at
        )

    except Exception as e:
        db.rollback()

        print("=" * 60)
        print("[DOCUMENT UPLOAD ERROR]")
        print(str(e))
        print("=" * 60)

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload/ingestion failed: {str(e)}"
        )


@router.get(
    "/",
    response_model=list[DocumentResponse]
)
async def get_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    documents = (
        db.query(Document, Companion.name.label("companion_name"))
        .outerjoin(
            Companion,
            Document.companion_id == Companion.id
        )
        .filter(Document.user_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )

    result = []

    for document, companion_name in documents:
        result.append(
            DocumentResponse(
                id=document.id,
                user_id=document.user_id,
                companion_id=document.companion_id,
                companion_name=companion_name,
                file_name=document.file_name,
                file_path=document.file_path,
                uploaded_at=document.uploaded_at
            )
        )

    return result


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    try:

        # ----------------------------------------
        # Get all graph nodes for this document
        # ----------------------------------------

        nodes = (
            db.query(KnowledgeNode)
            .filter(
                KnowledgeNode.source_document_id == document.id
            )
            .all()
        )

        node_ids = [node.id for node in nodes]

        # ----------------------------------------
        # Delete graph edges first
        # ----------------------------------------

        if node_ids:
            (
                db.query(KnowledgeEdge)
                .filter(
                    or_(
                        KnowledgeEdge.source_node_id.in_(node_ids),
                        KnowledgeEdge.target_node_id.in_(node_ids)
                    )
                )
                .delete(synchronize_session=False)
            )

        # ----------------------------------------
        # Delete graph nodes
        # ----------------------------------------

        (
            db.query(KnowledgeNode)
            .filter(
                KnowledgeNode.source_document_id == document.id
            )
            .delete(synchronize_session=False)
        )

        # ----------------------------------------
        # Delete document row
        # ----------------------------------------

        db.delete(document)

        db.commit()

        # ----------------------------------------
        # Delete physical file AFTER commit
        # ----------------------------------------

        if (
            document.file_path
            and os.path.exists(document.file_path)
        ):
            try:
                os.remove(document.file_path)
            except Exception:
                pass

        return

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )