import httpx
from typing import Any, Dict

from backend.app.core.config import settings


LIVEAVATAR_SESSION_URL = (
    "https://api.liveavatar.com/v1/sessions/token"
)


async def create_avatar_session() -> Dict[str, Any]:
    """
    Create a plain LiveAvatar LITE session.

    Conversation flow:

        User
            ↓
        FastAPI
            ↓
        LangGraph
            ↓
        OpenAI
            ↓
        ElevenLabs TTS
            ↓
        LiveAvatar

    LiveAvatar is used only for rendering the avatar.
    """

    payload = {
        "mode": "LITE",
        "avatar_id": settings.LIVEAVATAR_AVATAR_ID,
        "is_sandbox": False,
    }

    headers = {
        "X-API-KEY": settings.LIVEAVATAR_API_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:

        async with httpx.AsyncClient(timeout=30.0) as client:

            response = await client.post(
                LIVEAVATAR_SESSION_URL,
                headers=headers,
                json=payload,
            )

        print("=" * 80)
        print("[LIVEAVATAR SESSION]")
        print("URL:", LIVEAVATAR_SESSION_URL)
        print("Payload:", payload)
        print("Status:", response.status_code)
        print("Response:", response.text)
        print("=" * 80)

        response.raise_for_status()

        return response.json()

    except httpx.HTTPStatusError as e:

        raise Exception(
            "LiveAvatar session creation failed.\n"
            f"Status Code: {response.status_code}\n"
            f"Response: {response.text}"
        ) from e

    except httpx.RequestError as e:

        raise Exception(
            f"LiveAvatar request failed: {str(e)}"
        ) from e