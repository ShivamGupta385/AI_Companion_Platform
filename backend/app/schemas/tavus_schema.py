from pydantic import BaseModel, ConfigDict
from typing import Optional


class TavusSessionCreateResponse(BaseModel):
    conversation_id: str
    conversation_url: Optional[str] = None
    replica_id: Optional[str] = None
    persona_id: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )


class TavusConversationResponse(BaseModel):
    data: dict

    model_config = ConfigDict(
        from_attributes=True
    )