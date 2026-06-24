import os
import uuid

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    status
)
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.schemas.document_schema import DocumentResponse
from backend.app.services.ingestion_service import ingest_document
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document, save metadata in PostgreSQL,
    and ingest it into the RAG/vector pipeline.
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
        # 2) Save document metadata in PostgreSQL
        # --------------------------------------------------
        document = Document(
            user_id=current_user.id,
            file_name=file.filename,
            file_path=file_path
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        # --------------------------------------------------
        # 3) Ingest into vector / RAG system
        # --------------------------------------------------
        ingest_document(
            file_path=file_path,
            document_id=str(document.id),
            user_id=str(current_user.id),
            file_name=document.file_name
        )

        return document

    except Exception as e:
        db.rollback()

        # If document row was partially saved, clean it up
        try:
            existing_document = (
                db.query(Document)
                .filter(
                    Document.file_path == file_path,
                    Document.user_id == current_user.id
                )
                .first()
            )
            if existing_document:
                db.delete(existing_document)
                db.commit()
        except Exception:
            db.rollback()

        # Remove uploaded file if something failed
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
def get_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all uploaded documents for the current user.
    """

    documents = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )

    return documents


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a document metadata record.
    """

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

    # Delete file from disk if present
    if document.file_path and os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except Exception:
            pass

    db.delete(document)
    db.commit()

    return