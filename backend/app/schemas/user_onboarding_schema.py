# backend/app/schemas/user_onboarding_schema.py

from uuid import UUID
from datetime import datetime
from typing import Dict, Any

from pydantic import BaseModel


class UserOnboardingCreate(BaseModel):
    baseline_data: Dict[str, Any]


class UserOnboardingResponse(BaseModel):
    id: UUID
    user_id: UUID
    baseline_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True