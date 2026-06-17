import uuid

from pydantic import BaseModel,ConfigDict


class CompanionResponse(BaseModel):
    id: uuid.UUID
    name: str
    persona: str
    voice_id: str
    is_active: bool
    model_config = ConfigDict(
        from_attributes=True
    )