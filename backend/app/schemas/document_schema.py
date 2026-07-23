from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):

    id: UUID

    user_id: UUID

    file_name: str

    file_path: str

    uploaded_at: datetime

    class Config:
        from_attributes = True