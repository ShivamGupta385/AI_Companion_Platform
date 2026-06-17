# backend/app/schemas/onboarding_schema.py

from uuid import UUID
from datetime import datetime
from typing import Dict, Any

from pydantic import BaseModel


class OnboardingCreate(BaseModel):
    companion_id: UUID
    baseline_data: Dict[str, Any]


class OnboardingResponse(BaseModel):
    id: UUID
    user_id: UUID
    companion_id: UUID
    baseline_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True