import httpx
from typing import Any, Dict, Optional

from backend.app.core.config import settings


class TavusService:
    """
    Tavus API Service.

    Handles:

    - Create Conversation
    - Get Conversation
    - Send Message
    """

    BASE_URL = settings.TAVUS_BASE_URL.rstrip("/")
    API_KEY = settings.TAVUS_API_KEY

    @classmethod
    async def _request(
        cls,
        method: str,
        endpoint: str,
        json: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """
        Generic Tavus API request helper.
        """
        headers = {
            "x-api-key": cls.API_KEY,
            "Content-Type": "application/json",
        }

        url = f"{cls.BASE_URL}{endpoint}"

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(60.0)
        ) as client:

            response = await client.request(
                method=method,
                url=url,
                json=json,
                headers=headers,
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:

            print("=" * 80)
            print("[TAVUS API ERROR]")
            print("URL:", url)
            print("STATUS:", response.status_code)
            print("BODY:", response.text)
            print("=" * 80)

            raise e

        return response.json()

    # ----------------------------------------------------------
    # Create Conversation
    # ----------------------------------------------------------

    @classmethod
    async def create_conversation(
        cls,
        replica_id: str,
        persona_id: Optional[str] = None,
        conversation_name: Optional[str] = None,
    ) -> Dict[str, Any]:

        payload = {
            "replica_id": replica_id,
        }

        if persona_id:
            payload["persona_id"] = persona_id

        if conversation_name:
            payload["conversation_name"] = conversation_name

        response = await cls._request(
            method="POST",
            endpoint="/v2/conversations",
            json=payload,
        )

        return response

    # ----------------------------------------------------------
    # Get Conversation
    # ----------------------------------------------------------

    @classmethod
    async def get_conversation(
        cls,
        conversation_id: str,
    ) -> Dict[str, Any]:

        return await cls._request(
            method="GET",
            endpoint=f"/v2/conversations/{conversation_id}",
        )

    # ----------------------------------------------------------
    # Send Message
    # ----------------------------------------------------------

    @classmethod
    async def send_message(
        cls,
        conversation_id: str,
        text: str,
    ) -> Dict[str, Any]:

        payload = {
            "script": text,
        }

        return await cls._request(
            method="POST",
            endpoint=f"/v2/conversations/{conversation_id}/messages",
            json=payload,
        )