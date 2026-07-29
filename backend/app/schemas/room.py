import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserResponse


class RoomCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class MusicPermissionUpdate(BaseModel):
    can_control_music: bool


class PlaybackUpdate(BaseModel):
    spotify_uri: str = Field(min_length=1, max_length=255)
    spotify_track_id: str = Field(min_length=1, max_length=128)
    queue_uris: list[str] = Field(min_length=1)
    title: str = Field(min_length=1, max_length=255)
    artist: str = Field(min_length=1, max_length=255)
    album_image_url: str | None = Field(default=None, max_length=2048)
    duration_ms: int = Field(gt=0)
    position_ms: int = Field(default=0, ge=0)
    is_playing: bool


class PlaybackResponse(PlaybackUpdate):
    model_config = ConfigDict(from_attributes=True)

    version: int
    changed_at: datetime


class MessageCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    text: str = Field(min_length=1, max_length=500)


class MessageReactionToggle(BaseModel):
    emoji: str = Field(min_length=1, max_length=8)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    text: str
    reactions: dict[str, list[str]] = Field(default_factory=dict)
    message_type: str = "text"
    payload: dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    user: UserResponse


class ChessMoveCreate(BaseModel):
    from_square: str = Field(pattern=r"^[a-h][1-8]$")
    to_square: str = Field(pattern=r"^[a-h][1-8]$")
    promotion: str | None = Field(default=None, pattern=r"^[qrbn]$")


class ChessGameResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    creator_id: uuid.UUID
    white_user_id: uuid.UUID
    black_user_id: uuid.UUID | None
    status: str
    fen: str
    turn: str
    move_history: list[str] = Field(default_factory=list)
    winner_user_id: uuid.UUID | None
    result: str | None
    created_at: datetime
    updated_at: datetime
    white_user: UserResponse
    black_user: UserResponse | None


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
    playback: PlaybackResponse | None
    messages: list[MessageResponse]
    chess_game: ChessGameResponse | None
