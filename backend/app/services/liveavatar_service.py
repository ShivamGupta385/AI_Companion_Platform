import requests

from backend.app.core.config import settings


def create_avatar_session():

    url = (
        "https://api.liveavatar.com/v1/sessions/token"
    )

    headers = {
        "X-API-KEY":
        settings.LIVEAVATAR_API_KEY,

        "Content-Type":
        "application/json"
    }

    payload = {
        "avatar_id":
        "3f291b22-0267-4fb6-a25b-847fb63604b0",

        "mode":
        "FULL",

        "is_sandbox":
        False,

        "avatar_persona": {
            "language": "en"
        }
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload
    )

    print(
        "STATUS:",
        response.status_code
    )

    print(
        "RESPONSE:",
        response.text
    )

    return response.json()

