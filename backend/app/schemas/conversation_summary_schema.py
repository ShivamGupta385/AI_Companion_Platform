import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConversationSummaryBase(BaseModel):
    conversation_id: uuid.UUID
    user_id: uuid.UUID
    companion_id: uuid.UUID
    summary_text: str


class ConversationSummaryCreate(ConversationSummaryBase):
    pass


class ConversationSummaryResponse(ConversationSummaryBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )