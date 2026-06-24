import requests
from typing import Any, Dict

from backend.app.core.config import settings


def create_avatar_session() -> Dict[str, Any]:
    """
    Create a LiveAvatar session token for frontend SDK usage.
    """

    url = "https://api.liveavatar.com/v1/sessions/token"

    payload = {
        "avatar_id": settings.LIVEAVATAR_AVATAR_ID,
        "mode": "FULL",
        "is_sandbox": False,
        "avatar_persona": {
            "language": "en"
        }
    }

    headers = {
        "X-API-KEY": settings.LIVEAVATAR_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        print("=" * 60)
        print("[LIVEAVATAR TOKEN] URL:", url)
        print("[LIVEAVATAR TOKEN] AVATAR ID:", settings.LIVEAVATAR_AVATAR_ID)
        print("[LIVEAVATAR TOKEN] PAYLOAD:", payload)
        print("[LIVEAVATAR TOKEN] STATUS:", response.status_code)
        print("[LIVEAVATAR TOKEN] RESPONSE:", response.text)
        print("=" * 60)

        if response.status_code >= 400:
            raise Exception(
                f"LiveAvatar session creation failed: "
                f"{response.status_code} - {response.text}"
            )

        return response.json()

    except requests.RequestException as e:
        raise Exception(
            f"LiveAvatar request failed: {str(e)}"
        )