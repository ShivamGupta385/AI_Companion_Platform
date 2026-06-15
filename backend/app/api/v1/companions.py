from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.companion import Companion
from backend.app.models.user import User

from backend.app.schemas.companion_schema import (
    CompanionResponse
)

from backend.app.core.security import (
    get_current_user
)

router = APIRouter()


@router.get(
    "/",
    response_model=list[CompanionResponse],
    status_code=status.HTTP_200_OK
)
def get_companions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all active companions.
    """

    companions = (
        db.query(Companion)
        .filter(Companion.is_active == True)
        .all()
    )

    return companions


@router.get(
    "/{companion_id}",
    response_model=CompanionResponse,
    status_code=status.HTTP_200_OK
)
def get_companion(
    companion_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get companion details by ID.
    """

    companion = (
        db.query(Companion)
        .filter(
            Companion.id == companion_id,
            Companion.is_active == True
        )
        .first()
    )

    if not companion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Companion not found"
        )

    return companion