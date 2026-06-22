import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    companion_id: uuid.UUID
    conversation_type: str


class ConversationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    companion_id: uuid.UUID
    conversation_type: str
    started_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class ConversationDetailResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    companion_id: uuid.UUID
    companion_name: str
    conversation_type: str
    started_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class ConversationListItem(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    companion_id: uuid.UUID
    companion_name: str
    conversation_type: str
    started_at: datetime
    updated_at: datetime
    last_message: Optional[str] = None
    message_count: int = 0

    model_config = ConfigDict(
        from_attributes=True
    )