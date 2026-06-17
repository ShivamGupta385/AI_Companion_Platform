import uuid

from pydantic import BaseModel,ConfigDict


class ChatRequest(BaseModel):
    conversation_id: uuid.UUID
    message: str


class ChatResponse(BaseModel):
    response: str
    model_config = ConfigDict(
        from_attributes=True
    )