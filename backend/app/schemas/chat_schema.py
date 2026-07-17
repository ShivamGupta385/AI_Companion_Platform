import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ChatRequest(BaseModel):
    conversation_id: uuid.UUID
    message: str


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID

    response: str

    tavus_conversation_id: Optional[str] = None

    conversation_url: Optional[str] = None

    success: bool = True

    model_config = ConfigDict(
        from_attributes=True
    )