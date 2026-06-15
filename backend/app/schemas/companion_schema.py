import uuid

from pydantic import BaseModel


class CompanionResponse(BaseModel):
    id: uuid.UUID
    name: str
    persona: str
    voice_id: str
    is_active: bool

    model_config = {
        "from_attributes": True
    }