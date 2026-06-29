import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ChatRequest(BaseModel):
    conversation_id: uuid.UUID
    message: str


class ChatResponse(BaseModel):
    response: str
    tavus_video_url: Optional[str] = None   # new field for Tavus avatar video

    model_config = ConfigDict(
        from_attributes=True
    )
