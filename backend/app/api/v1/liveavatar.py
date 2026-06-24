from fastapi import APIRouter, HTTPException, status

from backend.app.services.liveavatar_service import (
    create_avatar_session
)

router = APIRouter()


@router.post(
    "/session",
    status_code=status.HTTP_200_OK
)
async def create_session():
    try:
        response = create_avatar_session()

        return {
            "sessionToken": response["data"]["session_token"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )