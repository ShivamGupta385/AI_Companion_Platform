from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from backend.app.db.session import get_db

from backend.app.models.user import User
from backend.app.models.companion import Companion
from backend.app.models.onboarding_history import OnboardingHistory

from backend.app.schemas.onboarding_schema import (
    OnboardingCreate,
    OnboardingResponse
)

from backend.app.core.security import (
    get_current_user
)

router = APIRouter()


@router.post(
    "/",
    response_model=OnboardingResponse,
    status_code=status.HTTP_201_CREATED
)
def create_onboarding(
    onboarding_data: OnboardingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create onboarding profile for a companion.
    """

    companion = (
        db.query(Companion)
        .filter(
            Companion.id == onboarding_data.companion_id,
            Companion.is_active == True
        )
        .first()
    )

    if not companion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Companion not found"
        )

    existing_onboarding = (
        db.query(OnboardingHistory)
        .filter(
            OnboardingHistory.user_id == current_user.id,
            OnboardingHistory.companion_id == onboarding_data.companion_id
        )
        .first()
    )

    if existing_onboarding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Onboarding already completed for this companion"
        )

    onboarding = OnboardingHistory(
        user_id=current_user.id,
        companion_id=onboarding_data.companion_id,
        baseline_data=onboarding_data.baseline_data
    )

    db.add(onboarding)
    db.commit()
    db.refresh(onboarding)

    return onboarding


@router.get(
    "/{companion_id}",
    response_model=OnboardingResponse,
    status_code=status.HTTP_200_OK
)
def get_onboarding(
    companion_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get onboarding profile for a companion.
    """

    onboarding = (
        db.query(OnboardingHistory)
        .filter(
            OnboardingHistory.user_id == current_user.id,
            OnboardingHistory.companion_id == companion_id
        )
        .first()
    )

    if not onboarding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onboarding not found"
        )

    return onboarding


@router.put(
    "/{companion_id}",
    response_model=OnboardingResponse,
    status_code=status.HTTP_200_OK
)
def update_onboarding(
    companion_id: UUID,
    onboarding_data: OnboardingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update onboarding profile.
    """

    onboarding = (
        db.query(OnboardingHistory)
        .filter(
            OnboardingHistory.user_id == current_user.id,
            OnboardingHistory.companion_id == companion_id
        )
        .first()
    )

    if not onboarding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onboarding not found"
        )

    onboarding.baseline_data = onboarding_data.baseline_data

    db.commit()
    db.refresh(onboarding)

    return onboarding