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

from backend.app.schemas.document_schema import (
    DocumentResponse
)

from backend.app.services.ingestion_service import (
    ingest_document
)

from backend.app.core.security import (
    get_current_user
)

router = APIRouter()

UPLOAD_DIR = "uploads"

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    allowed_extensions = [
        ".pdf",
        ".txt",
        ".docx"
    ]

    file_extension = os.path.splitext(
        file.filename
    )[1].lower()

    if file_extension not in allowed_extensions:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, TXT and DOCX files are allowed"
        )

    unique_filename = (
        f"{uuid.uuid4()}_{file.filename}"
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        unique_filename
    )

    with open(
        file_path,
        "wb"
    ) as buffer:

        content = await file.read()

        buffer.write(content)

    document = Document(
        user_id=current_user.id,
        file_name=file.filename,
        file_path=file_path
    )

    db.add(document)

    db.commit()

    db.refresh(document)

    try:

        ingest_document(
        file_path=file_path,
        document_id=str(document.id),
        user_id=str(current_user.id),
        file_name=document.file_name
    )

    except Exception as e:

        raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Ingestion failed: {str(e)}"
    )
    return document


@router.get(
    "/",
    response_model=list[DocumentResponse]
)
def get_documents(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    documents = (
        db.query(Document)
        .filter(
            Document.user_id ==
            current_user.id
        )
        .order_by(
            Document.uploaded_at.desc()
        )
        .all()
    )

    return documents




@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_document(
    document_id: str,
    current_user: User = Depends(
        get_current_user
    ),
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
            status_code=404,
            detail="Document not found"
        )

    db.delete(document)

    db.commit()

    return