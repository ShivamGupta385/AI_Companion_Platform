import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserMemoryBase(BaseModel):
    user_id: uuid.UUID
    companion_id: Optional[uuid.UUID] = None
    memory_type: str
    memory_text: str
    source_conversation_id: Optional[uuid.UUID] = None


class UserMemoryCreate(UserMemoryBase):
    pass


class UserMemoryResponse(UserMemoryBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )