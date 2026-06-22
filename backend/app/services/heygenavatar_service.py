import requests

from backend.app.core.config import settings


def create_avatar_video(
    script: str,
    avatar_id: str,
):

    url = "https://api.heygen.com/v3/videos"

    headers = {
        "x-api-key": settings.HEYGEN_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "type": "avatar",
        "avatar_id": avatar_id,
        "script": script,
        "output_format": "mp4",
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


def get_video(
    video_id: str,
):

    url = (
        f"https://api.heygen.com/v3/videos/{video_id}"
    )

    headers = {
        "x-api-key": settings.HEYGEN_API_KEY,
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )
    print("STATUS:", response.status_code)
    print("RESPONSE:", response.text)
    print("URL:", response.url)

    response.raise_for_status()
    

    return response.json()

