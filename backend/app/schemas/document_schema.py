from uuid import UUID
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    id: UUID
    user_id: UUID
    companion_id: Optional[UUID] = None
    companion_name: Optional[str] = None
    file_name: str
    file_path: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)