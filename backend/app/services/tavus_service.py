import requests
from typing import Any, Dict, Optional

from backend.app.core.config import settings


class TavusService:
    """
    Service layer for Tavus avatar session management.
    AGIX remains the source of truth for users/conversations/messages.
    Tavus is used as the avatar/video layer.
    """

    @staticmethod
    def create_conversation(
        replica_id: str,
        persona_id: Optional[str] = None,
        conversation_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Tavus conversation/session.
        """

        url = f"{settings.TAVUS_BASE_URL}/v2/conversations"

        payload: Dict[str, Any] = {
            "replica_id": replica_id
        }

        if persona_id:
            payload["persona_id"] = persona_id

        if conversation_name:
            payload["conversation_name"] = conversation_name

        headers = {
            "x-api-key": settings.TAVUS_API_KEY,
            "Content-Type": "application/json"
        }

        print("=" * 60)
        print("[TAVUS CREATE] URL:", url)
        print("[TAVUS CREATE] PAYLOAD:", payload)
        print("=" * 60)

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30
        )

        print("=" * 60)
        print("[TAVUS CREATE] STATUS:", response.status_code)
        print("[TAVUS CREATE] RESPONSE:", response.text)
        print("=" * 60)

        if response.status_code >= 400:
            raise Exception(
                f"Tavus create conversation failed: "
                f"{response.status_code} - {response.text}"
            )

        return response.json()

    @staticmethod
    def get_conversation(
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Fetch Tavus conversation/session details.
        """

        url = (
            f"{settings.TAVUS_BASE_URL}"
            f"/v2/conversations/{conversation_id}"
        )

        headers = {
            "x-api-key": settings.TAVUS_API_KEY
        }

        print("=" * 60)
        print("[TAVUS GET] URL:", url)
        print("[TAVUS GET] conversation_id:", conversation_id)
        print("=" * 60)

        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        print("=" * 60)
        print("[TAVUS GET] STATUS:", response.status_code)
        print("[TAVUS GET] RESPONSE:", response.text)
        print("=" * 60)

        if response.status_code >= 400:
            raise Exception(
                f"Tavus get conversation failed: "
                f"{response.status_code} - {response.text}"
            )

        return response.json()