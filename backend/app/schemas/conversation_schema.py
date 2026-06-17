import uuid

from pydantic import BaseModel,ConfigDict


class ConversationCreate(BaseModel):
    companion_id: uuid.UUID
    conversation_type: str


class ConversationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    companion_id: uuid.UUID
    conversation_type: str
    model_config = ConfigDict(
        from_attributes=True
    )