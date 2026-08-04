from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Literal

Difficulty = Literal["easy", "medium", "hard"]
GameStatus = Literal["countdown", "playing", "round_result", "finished"]

COUNTDOWN_SECONDS = 3
RESULT_SECONDS = 6
STAGE_PLAN: tuple[tuple[Difficulty, int, int, float], ...] = (
    ("easy", 45, 3, 1.0),
    ("easy", 45, 3, 1.0),
    ("medium", 50, 4, 2.0),
    ("medium", 50, 4, 2.0),
    ("hard", 60, 5, 3.0),
    ("hard", 60, 5, 3.0),
)


@dataclass(frozen=True, slots=True)
class WordRound:
    id: str
    difficulty: Difficulty
    letters: tuple[str, ...]
    valid_words: frozenset[str]
    duration_seconds: int
    min_length: int
    points: float


@dataclass(slots=True)
class WordSubmission:
    word: str
    submitted_at: datetime


@dataclass(slots=True)
class WordPlayerState:
    user_id: str
    submissions: list[WordSubmission] = field(default_factory=list)
    stage_points: float = 0.0
    total_words: int = 0
    total_letters: int = 0


@dataclass(slots=True)
class WordRoundPlayerResult:
    user_id: str
    words: list[str]
    word_count: int
    total_letters: int
    longest_word: str | None
    stage_points: float


@dataclass(slots=True)
class WordRoundResult:
    stage_number: int
    difficulty: Difficulty
    winner_user_id: str | None
    players: list[WordRoundPlayerResult]


@dataclass(slots=True)
class WordBattleState:
    players: list[WordPlayerState]
    rounds: list[WordRound]
    stage_index: int = 0
    status: GameStatus = "countdown"
    phase_started_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    phase_ends_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    results: list[WordRoundResult] = field(default_factory=list)
    winner_user_id: str | None = None


def normalize_word(value: str) -> str:
    translated = value.strip().translate(str.maketrans({"I": "ı", "İ": "i"}))
    return translated.lower()


def make_round(
    stage_index: int,
    *,
    round_id: str,
    letters: str,
    valid_words: set[str] | frozenset[str],
) -> WordRound:
    if not 0 <= stage_index < len(STAGE_PLAN):
        raise ValueError("Geçersiz etap numarası.")

    difficulty, duration_seconds, min_length, points = STAGE_PLAN[stage_index]
    normalized_letters = tuple(
        normalize_word(letter)
        for letter in letters
        if normalize_word(letter).isalpha()
    )
    if not normalized_letters:
        raise ValueError("Etapta en az bir harf bulunmalıdır.")

    normalized_words = frozenset(
        normalize_word(word) for word in valid_words if normalize_word(word)
    )
    invalid_words = [
        word
        for word in normalized_words
        if len(word) < min_length
        or not word.isalpha()
        or not _can_build_word(word, normalized_letters)
    ]
    if invalid_words:
        raise ValueError(
            f"Etap kelime havuzunda geçersiz kelime var: {invalid_words[0]}"
        )

    return WordRound(
        id=round_id,
        difficulty=difficulty,
        letters=normalized_letters,
        valid_words=normalized_words,
        duration_seconds=duration_seconds,
        min_length=min_length,
        points=points,
    )


def start_game(
    user_ids: list[str],
    rounds: list[WordRound],
    *,
    now: datetime | None = None,
) -> WordBattleState:
    if len(user_ids) != 2:
        raise ValueError("Kelime Kapışması tam olarak 2 oyuncu gerektirir.")
    if len(set(user_ids)) != 2:
        raise ValueError("Oyuncular benzersiz olmalıdır.")
    if len(rounds) != len(STAGE_PLAN):
        raise ValueError("Kelime Kapışması 6 etap gerektirir.")

    for index, round_spec in enumerate(rounds):
        expected_difficulty = STAGE_PLAN[index][0]
        if round_spec.difficulty != expected_difficulty:
            raise ValueError("Etap zorluk sırası kolay, orta ve zor olmalıdır.")

    current_time = _utc(now)
    return WordBattleState(
        players=[WordPlayerState(user_id=user_id) for user_id in user_ids],
        rounds=list(rounds),
        phase_started_at=current_time,
        phase_ends_at=current_time + timedelta(seconds=COUNTDOWN_SECONDS),
    )


def sync_state(
    state: WordBattleState,
    *,
    now: datetime | None = None,
) -> bool:
    current_time = _utc(now)
    changed = False

    while state.status != "finished" and current_time >= state.phase_ends_at:
        boundary = state.phase_ends_at

        if state.status == "countdown":
            state.status = "playing"
            state.phase_started_at = boundary
            state.phase_ends_at = boundary + timedelta(
                seconds=current_round(state).duration_seconds
            )
            changed = True
            continue

        if state.status == "playing":
            _finish_round(state)
            state.status = "round_result"
            state.phase_started_at = boundary
            state.phase_ends_at = boundary + timedelta(seconds=RESULT_SECONDS)
            changed = True
            continue

        if state.status == "round_result":
            if state.stage_index == len(state.rounds) - 1:
                _finish_game(state)
                state.phase_started_at = boundary
                state.phase_ends_at = boundary
            else:
                state.stage_index += 1
                for player in state.players:
                    player.submissions.clear()
                state.status = "countdown"
                state.phase_started_at = boundary
                state.phase_ends_at = boundary + timedelta(
                    seconds=COUNTDOWN_SECONDS
                )
            changed = True

    return changed


def submit_word(
    state: WordBattleState,
    user_id: str,
    value: str,
    *,
    now: datetime | None = None,
) -> str:
    current_time = _utc(now)
    sync_state(state, now=current_time)

    if state.status != "playing":
        raise ValueError("Şu anda kelime gönderilemez.")

    player = _player_by_id(state, user_id)
    word = normalize_word(value)
    round_spec = current_round(state)

    if len(word) < round_spec.min_length:
        raise ValueError(
            f"Bu etapta kelimeler en az {round_spec.min_length} harfli olmalıdır."
        )
    if not word.isalpha():
        raise ValueError("Kelime yalnızca harflerden oluşmalıdır.")
    if not _can_build_word(word, round_spec.letters):
        raise ValueError("Bu kelime verilen harflerle oluşturulamaz.")
    if word not in round_spec.valid_words:
        raise ValueError("Bu kelime sözlükte bulunamadı.")
    if any(item.word == word for item in player.submissions):
        raise ValueError("Bu kelimeyi daha önce kullandın.")

    player.submissions.append(WordSubmission(word=word, submitted_at=current_time))
    return word


def current_round(state: WordBattleState) -> WordRound:
    return state.rounds[state.stage_index]


def remaining_seconds(
    state: WordBattleState,
    *,
    now: datetime | None = None,
) -> int:
    current_time = _utc(now)
    return max(0, int((state.phase_ends_at - current_time).total_seconds() + 0.999))


def _finish_round(state: WordBattleState) -> None:
    round_spec = current_round(state)
    ranking = sorted(state.players, key=_round_ranking_key, reverse=True)
    winner_user_id = (
        ranking[0].user_id
        if _round_ranking_key(ranking[0]) != _round_ranking_key(ranking[1])
        else None
    )
    awarded_points = {
        player.user_id: round_spec.points if winner_user_id == player.user_id else 0.0
        for player in state.players
    }
    if winner_user_id is None:
        awarded_points = {
            player.user_id: round_spec.points / 2 for player in state.players
        }

    player_results: list[WordRoundPlayerResult] = []
    for player in state.players:
        words = [item.word for item in player.submissions]
        stage_points = awarded_points[player.user_id]
        player.stage_points += stage_points
        player.total_words += len(words)
        player.total_letters += sum(len(word) for word in words)
        player_results.append(
            WordRoundPlayerResult(
                user_id=player.user_id,
                words=words,
                word_count=len(words),
                total_letters=sum(len(word) for word in words),
                longest_word=max(words, key=len) if words else None,
                stage_points=stage_points,
            )
        )

    state.results.append(
        WordRoundResult(
            stage_number=state.stage_index + 1,
            difficulty=round_spec.difficulty,
            winner_user_id=winner_user_id,
            players=player_results,
        )
    )


def _finish_game(state: WordBattleState) -> None:
    ranking = sorted(state.players, key=_match_ranking_key, reverse=True)
    state.winner_user_id = (
        ranking[0].user_id
        if _match_ranking_key(ranking[0]) != _match_ranking_key(ranking[1])
        else None
    )
    state.status = "finished"


def _round_ranking_key(player: WordPlayerState) -> tuple[int, int, int, float]:
    words = [item.word for item in player.submissions]
    first_time = (
        -player.submissions[0].submitted_at.timestamp()
        if player.submissions
        else float("-inf")
    )
    return (
        len(words),
        max((len(word) for word in words), default=0),
        sum(len(word) for word in words),
        first_time,
    )


def _match_ranking_key(player: WordPlayerState) -> tuple[float, int, int]:
    return player.stage_points, player.total_words, player.total_letters


def _can_build_word(word: str, letters: tuple[str, ...]) -> bool:
    available = Counter(letters)
    needed = Counter(word)
    return all(needed[letter] <= available[letter] for letter in needed)


def _player_by_id(state: WordBattleState, user_id: str) -> WordPlayerState:
    for player in state.players:
        if player.user_id == user_id:
            return player
    raise ValueError("Bu oyundaki oyunculardan biri değilsiniz.")


def _utc(value: datetime | None) -> datetime:
    current = value or datetime.now(UTC)
    if current.tzinfo is None:
        return current.replace(tzinfo=UTC)
    return current.astimezone(UTC)
