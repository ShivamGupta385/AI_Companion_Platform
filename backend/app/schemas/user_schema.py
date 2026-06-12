import uuid

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: str

    model_config = {
        "from_attributes": True
    }