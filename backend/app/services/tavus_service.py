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
        conversation_name: Optional[str] = None,
        document_ids: Optional[list[str]] = None,
        custom_greeting: Optional[str] = None,
        conversational_context: Optional[str] = None,
        memory_stores: Optional[list[str]] = None
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

        if document_ids:
            payload["document_ids"] = document_ids
            
        if custom_greeting:
            payload["custom_greeting"] = custom_greeting
            
        if conversational_context:
            payload["conversational_context"] = conversational_context
            
        if memory_stores:
            payload["memory_stores"] = memory_stores

        # Removed timeouts per user request

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

        if response.status_code >= 400:
            raise Exception(
                f"Tavus get conversation failed: "
                f"{response.status_code} - {response.text}"
            )

        return response.json()

    @staticmethod
    def end_conversation(
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        End a Tavus conversation/session.
        """

        url = (
            f"{settings.TAVUS_BASE_URL}"
            f"/v2/conversations/{conversation_id}/end"
        )

        headers = {
            "x-api-key": settings.TAVUS_API_KEY
        }

        print("=" * 60)
        print("[TAVUS END] URL:", url)
        print("[TAVUS END] conversation_id:", conversation_id)
        print("=" * 60)

        response = requests.post(
            url,
            headers=headers,
            timeout=30
        )

        print("=" * 60)
        print("[TAVUS END] STATUS:", response.status_code)
        print("[TAVUS END] RESPONSE:", response.text)
        print("=" * 60)

        if response.status_code >= 400:
            raise Exception(
                f"Tavus end conversation failed: "
                f"{response.status_code} - {response.text}"
            )

        try:
            return response.json()
        except Exception:
            return {"status": "success"}

    @staticmethod
    def create_persona(
        persona_name: str,
        system_prompt: str,
        replica_id: str,
        document_ids: Optional[list[str]] = None
    ) -> str:
        """
        Create a dynamic Persona (PAL) for this session.
        """
        url = f"{settings.TAVUS_BASE_URL}/v2/personas"

        payload = {
            "persona_name": persona_name,
            "system_prompt": system_prompt,
            "pipeline_mode": "full",
            "default_replica_id": replica_id,
            "layers": {
                "llm": {
                    "model": "gpt-4o"
                }
            }
        }

        if document_ids:
            payload["document_ids"] = document_ids

        headers = {
            "x-api-key": settings.TAVUS_API_KEY,
            "Content-Type": "application/json"
        }

        print("=" * 60)
        print("[TAVUS CREATE PERSONA] URL:", url)
        print("[TAVUS CREATE PERSONA] PAYLOAD:", payload)
        print("=" * 60)

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30
        )

        print("=" * 60)
        print("[TAVUS CREATE PERSONA] STATUS:", response.status_code)
        print("[TAVUS CREATE PERSONA] RESPONSE:", response.text)
        print("=" * 60)

        if response.status_code >= 400:
            raise Exception(
                f"Tavus create persona failed: "
                f"{response.status_code} - {response.text}"
            )

        data = response.json()
        return data.get("persona_id") or data.get("id") or ""

    @staticmethod
    def delete_persona(persona_id: str) -> None:
        """
        Delete a dynamic Persona (PAL).
        """
        url = f"{settings.TAVUS_BASE_URL}/v2/personas/{persona_id}"

        headers = {
            "x-api-key": settings.TAVUS_API_KEY
        }

        print("=" * 60)
        print("[TAVUS DELETE PERSONA] URL:", url)
        print("[TAVUS DELETE PERSONA] ID:", persona_id)
        print("=" * 60)

        response = requests.delete(
            url,
            headers=headers,
            timeout=30
        )

        print("=" * 60)
        print("[TAVUS DELETE PERSONA] STATUS:", response.status_code)
        print("[TAVUS DELETE PERSONA] RESPONSE:", response.text)
        print("=" * 60)