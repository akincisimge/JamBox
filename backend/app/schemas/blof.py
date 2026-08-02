import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse

BlofRank = Literal["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]


class BlofCardResponse(BaseModel):
    id: str
    suit: Literal["clubs", "diamonds", "hearts", "spades"]
    rank: BlofRank


class BlofPlayRequest(BaseModel):
    card_ids: list[str] = Field(min_length=1, max_length=4)
    declared_rank: BlofRank


class BlofPlayerResponse(BaseModel):
    user_id: uuid.UUID
    player_order: int
    hand_count: int
    is_current_turn: bool
    is_creator: bool
    user: UserResponse


class BlofChallengeResultResponse(BaseModel):
    truthful: bool
    challenger_user_id: uuid.UUID
    challenged_user_id: uuid.UUID
    pile_receiver_user_id: uuid.UUID
    next_turn_user_id: uuid.UUID | None
    revealed_cards: list[BlofCardResponse] = Field(default_factory=list)


class BlofGameResponse(BaseModel):
    id: uuid.UUID
    creator_id: uuid.UUID
    status: Literal["waiting", "active", "finished"]
    version: int
    turn_user_id: uuid.UUID | None
    pending_winner_user_id: uuid.UUID | None
    winner_user_id: uuid.UUID | None
    pile_count: int
    last_play_count: int
    last_declared_rank: BlofRank | None
    last_player_user_id: uuid.UUID | None
    hand: list[BlofCardResponse] = Field(default_factory=list)
    players: list[BlofPlayerResponse] = Field(default_factory=list)
    last_result: BlofChallengeResultResponse | None = None
