import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    spotify_id: str = Field(min_length=1, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)
    email: EmailStr | None = None
    avatar_url: str | None = Field(default=None, max_length=2048)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    spotify_id: str
    display_name: str
    email: str | None
    avatar_url: str | None
    created_at: datetime
