from elevenlabs.client import ElevenLabs

from backend.app.core.config import settings


if not settings.ELEVENLABS_API_KEY:
    raise ValueError(
        "ELEVENLABS_API_KEY is missing in .env file"
    )


client = ElevenLabs(
    api_key=settings.ELEVENLABS_API_KEY
)