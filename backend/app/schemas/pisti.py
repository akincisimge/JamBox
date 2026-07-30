import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class PistiCardResponse(BaseModel):
    id: str
    suit: str
    rank: str


class PistiMoveCreate(BaseModel):
    card_id: str = Field(min_length=3, max_length=32)


class PistiGameResponse(BaseModel):
    id: uuid.UUID
    creator_id: uuid.UUID
    player_one_user_id: uuid.UUID
    player_two_user_id: uuid.UUID | None
    status: Literal["waiting", "active", "finished"]
    turn_user_id: uuid.UUID | None
    hand: list[PistiCardResponse] = Field(default_factory=list)
    hand_counts: dict[str, int] = Field(default_factory=dict)
    captured_counts: dict[str, int] = Field(default_factory=dict)
    pisti_counts: dict[str, int] = Field(default_factory=dict)
    table: list[PistiCardResponse] = Field(default_factory=list)
    deck_count: int = 0
    scores: dict[str, int] = Field(default_factory=dict)
    winner_user_id: uuid.UUID | None
    player_one_user: UserResponse
    player_two_user: UserResponse | None
