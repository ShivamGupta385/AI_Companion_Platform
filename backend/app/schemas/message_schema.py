import uuid

from pydantic import BaseModel,ConfigDict

class MessageCreate(BaseModel):
    message_text: str


class MessageResponse(BaseModel):
    id: uuid.UUID
    sender_type: str
    message_text: str
    model_config = ConfigDict(
        from_attributes=True
    )