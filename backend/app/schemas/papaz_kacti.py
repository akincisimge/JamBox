import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class PapazKactiCardResponse(BaseModel):
    id: str
    suit: str
    rank: str


class PapazKactiDrawRequest(BaseModel):
    card_index: int = Field(ge=0)


class PapazKactiGameResponse(BaseModel):
    id: uuid.UUID
    creator_id: uuid.UUID
    
    player_one_user_id: uuid.UUID
    player_two_user_id: uuid.UUID | None
    player_three_user_id: uuid.UUID | None
    player_four_user_id: uuid.UUID | None
    
    status: Literal["waiting", "active", "finished"]
    turn_user_id: uuid.UUID | None
    loser_user_id: uuid.UUID | None
    
    # Only contains the hand of the requesting user
    hand: list[PapazKactiCardResponse] = Field(default_factory=list)
    
    # Counts of cards for all players
    hand_counts: dict[str, int] = Field(default_factory=dict)
    
    player_one_user: UserResponse
    player_two_user: UserResponse | None
    player_three_user: UserResponse | None
    player_four_user: UserResponse | None
