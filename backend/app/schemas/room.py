import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserResponse


class RoomCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class MusicPermissionUpdate(BaseModel):
    can_control_music: bool


class RoomMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    is_owner: bool
    can_control_music: bool
    created_at: datetime
    user: UserResponse


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    owner_id: uuid.UUID
    is_active: bool
    created_at: datetime
    members: list[RoomMemberResponse]
