from fastapi import (
    APIRouter,
    Depends
)

from fastapi.responses import (
    StreamingResponse
)

from backend.app.schemas.tts_schema import (
    SpeakRequest
)

from backend.app.services.tts_service import (
    stream_audio
)

from backend.app.models.user import User

from backend.app.core.security import (
    get_current_user
)


router = APIRouter()


@router.post(
    "/speak"
)
async def speak(
    request: SpeakRequest,
    current_user: User = Depends(
        get_current_user
    )
):

    return StreamingResponse(
        stream_audio(
            request.text
        ),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition":
            "attachment; filename=speech.mp3"
        }
    )