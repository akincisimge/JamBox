import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse

Difficulty = Literal["easy", "medium", "hard"]
KelimeKapismasiStatus = Literal[
    "waiting",
    "countdown",
    "playing",
    "round_result",
    "finished",
]


class KelimeKapismasiSubmitRequest(BaseModel):
    word: str = Field(min_length=1, max_length=40)


class KelimeKapismasiPlayerResponse(BaseModel):
    user_id: uuid.UUID
    player_order: int
    current_word_count: int
    stage_points: float
    total_words: int
    total_letters: int
    is_creator: bool
    user: UserResponse


class KelimeKapismasiRoundPlayerResultResponse(BaseModel):
    user_id: uuid.UUID
    words: list[str] = Field(default_factory=list)
    word_count: int
    total_letters: int
    longest_word: str | None
    stage_points: float


class KelimeKapismasiRoundResultResponse(BaseModel):
    stage_number: int
    difficulty: Difficulty
    winner_user_id: uuid.UUID | None
    players: list[KelimeKapismasiRoundPlayerResultResponse] = Field(
        default_factory=list
    )


class KelimeKapismasiGameResponse(BaseModel):
    id: uuid.UUID
    creator_id: uuid.UUID
    status: KelimeKapismasiStatus
    version: int
    stage_number: int
    stage_count: int = 6
    difficulty: Difficulty | None
    letters: list[str] = Field(default_factory=list)
    min_length: int
    duration_seconds: int
    phase_started_at: datetime | None
    phase_ends_at: datetime | None
    remaining_seconds: int
    own_words: list[str] = Field(default_factory=list)
    own_word_count: int
    players: list[KelimeKapismasiPlayerResponse] = Field(default_factory=list)
    latest_result: KelimeKapismasiRoundResultResponse | None
    winner_user_id: uuid.UUID | None
