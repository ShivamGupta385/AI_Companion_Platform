from fastapi import APIRouter

from backend.app.services.liveavatar_service import (
    create_avatar_session
)

router = APIRouter()


@router.post("/session")
async def create_session():

    response = create_avatar_session()

    return {
        "sessionToken":
        response["data"]["session_token"]
    }
