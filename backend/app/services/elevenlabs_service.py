import requests
from typing import Dict, Any

from backend.app.core.config import settings


LIVEAVATAR_SECRET_URL = "https://api.liveavatar.com/v1/secrets"


class ElevenLabsService:
    @staticmethod
    def register_api_key() -> Dict[str, Any]:
        """
        Register the ElevenLabs API key with LiveAvatar.

        Returns:
            {
                "data": {
                    "secret_id": "...",
                    ...
                }
            }
        """

        payload = {
            "secret_type": "ELEVENLABS_API_KEY",
            "secret_value": settings.ELEVENLABS_API_KEY,
            "secret_name": "AGIX ElevenLabs Agent"
        }

        headers = {
            "X-API-KEY": settings.LIVEAVATAR_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:

            response = requests.post(
                LIVEAVATAR_SECRET_URL,
                json=payload,
                headers=headers,
                timeout=30
            )

            print("=" * 70)
            print("[ELEVENLABS SECRET REGISTRATION]")
            print("URL:", LIVEAVATAR_SECRET_URL)
            print("Status:", response.status_code)
            print("Response:", response.text)
            print("=" * 70)

            response.raise_for_status()

            return response.json()

        except requests.HTTPError as e:
            raise Exception(
                f"Failed to register ElevenLabs API Key: "
                f"{response.status_code} - {response.text}"
            ) from e

        except requests.RequestException as e:
            raise Exception(
                f"LiveAvatar request failed: {str(e)}"
            ) from e