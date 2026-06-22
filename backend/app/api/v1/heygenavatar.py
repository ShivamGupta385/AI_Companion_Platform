from fastapi import APIRouter

from backend.app.core.config import settings

from backend.app.services.heygenavatar_service import (
    create_avatar_video,
    get_video,
)

router = APIRouter()


@router.post("/heygen/video")
def create_video():

    return create_avatar_video(
        script="Hello from AI Companion",
        avatar_id=settings.HEYGEN_AVATAR_ID,
    )


@router.get("/heygen/video/{video_id}")
def video_status(
    video_id: str
):

    return get_video(video_id)