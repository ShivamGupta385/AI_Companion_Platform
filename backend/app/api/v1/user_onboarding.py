# backend/app/api/v1/user_onboarding.py

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from backend.app.db.session import get_db

from backend.app.models.user import User
from backend.app.models.user_onboarding import UserOnboarding

from backend.app.schemas.user_onboarding_schema import (
    UserOnboardingCreate,
    UserOnboardingResponse
)

from backend.app.core.security import (
    get_current_user
)

router = APIRouter()

@router.post(
    "/",
    response_model=UserOnboardingResponse,
    status_code=status.HTTP_201_CREATED
)
async def save_onboarding(
    onboarding_data: UserOnboardingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    onboarding = (
        db.query(UserOnboarding)
        .filter(
            UserOnboarding.user_id == current_user.id
        )
        .first()
    )

    if onboarding:

        onboarding.baseline_data = (
            onboarding_data.baseline_data
        )

        db.commit()
        db.refresh(onboarding)

        return onboarding

    onboarding = UserOnboarding(
        user_id=current_user.id,
        baseline_data=onboarding_data.baseline_data
    )

    db.add(onboarding)

    db.commit()
    db.refresh(onboarding)

    return onboarding


@router.get(
    "/me",
    response_model=UserOnboardingResponse
)
async def get_onboarding(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    onboarding = (
        db.query(UserOnboarding)
        .filter(
            UserOnboarding.user_id == current_user.id
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
    "/me",
    response_model=UserOnboardingResponse,
    status_code=status.HTTP_200_OK
)
async def update_onboarding(
    onboarding_data: UserOnboardingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's onboarding profile.
    """

    onboarding = (
        db.query(UserOnboarding)
        .filter(
            UserOnboarding.user_id == current_user.id
        )
        .first()
    )

    if not onboarding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onboarding not found"
        )

    # Create a completely new dictionary
    onboarding.baseline_data = {
        **(onboarding.baseline_data or {}),
        **onboarding_data.baseline_data
    }

    db.add(onboarding)

    db.commit()

    db.refresh(onboarding)

    return onboarding