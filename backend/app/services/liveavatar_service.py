import requests
from typing import Any, Dict

from backend.app.core.config import settings


def create_avatar_session() -> Dict[str, Any]:
    """
    Create a LiveAvatar Sandbox session token.
    """

    url = "https://api.liveavatar.com/v1/sessions/token"

    payload = {
        "mode": "FULL",

        # Sandbox mode
        "is_sandbox": True,

        # Sandbox avatar (Wayne)
        "avatar_id": "dd73ea75-1218-4ef3-92ce-606d5f7fbc0a",

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

        print("\n" + "=" * 60)
        print("LIVEAVATAR SANDBOX")
        print("=" * 60)
        print("URL:", url)
        print("Payload:", payload)
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        print("=" * 60 + "\n")

        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:
        raise Exception(
            f"LiveAvatar request failed: {str(e)}"
        )