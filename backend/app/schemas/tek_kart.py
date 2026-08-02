import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse

TekKartColor = Literal["red", "yellow", "green", "blue"]
TekKartCardKind = Literal[
    "number",
    "skip",
    "reverse",
    "draw_two",
    "wild",
    "wild_draw_four",
]


class TekKartCardResponse(BaseModel):
    id: str
    kind: TekKartCardKind
    color: TekKartColor | None
    number: int | None


class TekKartPlayRequest(BaseModel):
    card_id: str = Field(min_length=1)
    chosen_color: TekKartColor | None = None


class TekKartPlayerResponse(BaseModel):
    user_id: uuid.UUID
    player_order: int
    hand_count: int
    is_current_turn: bool
    is_creator: bool
    user: UserResponse


class TekKartGameResponse(BaseModel):
    id: uuid.UUID
    creator_id: uuid.UUID
    status: Literal["waiting", "active", "finished"]
    version: int
    turn_user_id: uuid.UUID | None
    winner_user_id: uuid.UUID | None
    active_color: TekKartColor | None
    direction: Literal[-1, 1]
    draw_pile_count: int
    top_card: TekKartCardResponse | None
    hand: list[TekKartCardResponse] = Field(default_factory=list)
    playable_card_ids: list[str] = Field(default_factory=list)
    can_draw: bool
    can_call_tek_kart: bool
    called_tek_kart: bool
    players: list[TekKartPlayerResponse] = Field(default_factory=list)
