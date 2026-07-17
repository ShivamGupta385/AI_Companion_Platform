from fastapi import (
    APIRouter,
    Depends,
    status
)

from backend.app.models.user import User
from backend.app.core.security import get_current_user

router = APIRouter()


@router.get(
    "/me",
    status_code=status.HTTP_200_OK
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Return the currently authenticated user's profile.
    """

    return {
        "id": str(current_user.id),
        "full_name": current_user.full_name,
        "username": current_user.username,
        "email": current_user.email,
        "profile_image_url": current_user.profile_image_url,
        "subscription_plan": current_user.subscription_plan,
        "is_active": current_user.is_active,
    }