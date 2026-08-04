from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.games.kelime_kapismasi import (
    WordBattleState,
    WordPlayerState,
    WordRound,
    WordRoundPlayerResult,
    WordRoundResult,
    WordSubmission,
    current_round,
    make_round,
    remaining_seconds,
    start_game,
    submit_word,
    sync_state,
)
from app.models.kelime_kapismasi import KelimeKapismasiGame
from app.models.room import Room, RoomMember, RoomMessage
from app.models.user import User
from app.schemas.kelime_kapismasi import (
    KelimeKapismasiGameResponse,
    KelimeKapismasiPlayerResponse,
    KelimeKapismasiRoundPlayerResultResponse,
    KelimeKapismasiRoundResultResponse,
)
from app.schemas.user import UserResponse
from app.services.errors import ConflictError, ForbiddenError, NotFoundError

ROUND_DEFINITIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "aaeklmrt",
        (
            "ara", "ata", "ale", "alt", "tam", "mal", "kal", "kel",
            "ter", "tel", "tek", "ret", "kar", "kat", "tar", "mat",
            "ela", "alet", "kale", "kare", "kart", "tema", "kama",
            "lama", "tela", "alma", "elma", "alem", "kalem", "maket",
            "metal", "merak", "katmer", "karamel", "makale", "marka",
            "emlak", "raket", "tarak",
        ),
    ),
    (
        "aadeeilnnr",
        (
            "ada", "ana", "ara", "dal", "dar", "din", "dil", "nar",
            "nal", "alan", "dana", "dara", "deri", "deli", "ideal",
            "idare", "ilan", "lira", "nadir", "lider", "dinar", "arena",
            "derin", "daire", "narin", "nane", "anne", "neden", "denir",
        ),
    ),
    (
        "aaeiiklmrt",
        (
            "aile", "ikram", "iklim", "imla", "imal", "emir", "kira",
            "kral", "krem", "kale", "kare", "kart", "tema", "maket",
            "metal", "merak", "kalem", "emlak", "raket", "tarak",
            "makale", "karamel", "katmer", "tamir", "terim", "milat",
            "limit", "ritim", "alarm",
        ),
    ),
    (
        "aaeeiiilmnnorrsssttuy",
        (
            "aile", "nota", "otel", "salon", "online", "siren", "serin",
            "sinir", "tesis", "insan", "narin", "arena", "liste", "tane",
            "saat", "sene", "soru", "sorun", "oran", "oral", "real",
            "sinema", "senaryo", "tesisat", "internet",
        ),
    ),
    (
        "aaeeiiklmmnnrst",
        (
            "kalem", "kiremit", "makine", "resim", "sinema", "seramik",
            "merasim", "tesir", "temkin", "misket", "market", "merak",
            "keman", "metin", "resmi", "insan", "nesil", "selam", "metal",
            "emlak", "ikram", "kamera", "matris", "renkli", "terminal",
        ),
    ),
    (
        "aaaeeeiiikkllmmnnrrsstt",
        (
            "karakter", "makineler", "kelimeler", "matematik", "teknik",
            "mimar", "mimari", "mimarlar", "terminal", "seramik", "kiremit",
            "makine", "sinema", "merasim", "misket", "market", "kamera",
            "matris", "metin", "nesil", "selam", "kelime", "kalem",
            "internet", "insan", "narin", "siren", "serin", "sinir", "tesisat",
        ),
    ),
)


async def _require_member(session: AsyncSession, room: Room, user: User) -> RoomMember:
    membership = await session.get(RoomMember, {"room_id": room.id, "user_id": user.id})
    if membership is None:
        raise NotFoundError("Kullanıcı bu odada değil.")
    return membership


async def _load_game(
    session: AsyncSession,
    room: Room,
    *,
    for_update: bool = False,
) -> KelimeKapismasiGame:
    query = (
        select(KelimeKapismasiGame)
        .where(KelimeKapismasiGame.room_id == room.id)
        .options(
            selectinload(KelimeKapismasiGame.player_one_user),
            selectinload(KelimeKapismasiGame.player_two_user),
        )
        .execution_options(populate_existing=True)
    )
    if for_update:
        query = query.with_for_update()

    game = await session.scalar(query)
    if game is None:
        raise NotFoundError("Bu odada Kelime Kapışması bulunamadı.")
    return game


def _build_rounds() -> list[WordRound]:
    return [
        make_round(
            index,
            round_id=f"stage-{index + 1}",
            letters=letters,
            valid_words=set(words),
        )
        for index, (letters, words) in enumerate(ROUND_DEFINITIONS)
    ]


def _round_to_dict(round_spec: WordRound) -> dict[str, Any]:
    return {
        "id": round_spec.id,
        "difficulty": round_spec.difficulty,
        "letters": list(round_spec.letters),
        "valid_words": sorted(round_spec.valid_words),
        "duration_seconds": round_spec.duration_seconds,
        "min_length": round_spec.min_length,
        "points": round_spec.points,
    }


def _round_from_dict(value: dict[str, Any]) -> WordRound:
    return WordRound(
        id=value["id"],
        difficulty=value["difficulty"],
        letters=tuple(value["letters"]),
        valid_words=frozenset(value["valid_words"]),
        duration_seconds=value["duration_seconds"],
        min_length=value["min_length"],
        points=float(value["points"]),
    )


def _submission_to_dict(item: WordSubmission) -> dict[str, Any]:
    return {"word": item.word, "submitted_at": item.submitted_at.isoformat()}


def _submission_from_dict(value: dict[str, Any]) -> WordSubmission:
    return WordSubmission(
        word=value["word"],
        submitted_at=datetime.fromisoformat(value["submitted_at"]),
    )


def _result_to_dict(result: WordRoundResult) -> dict[str, Any]:
    return {
        "stage_number": result.stage_number,
        "difficulty": result.difficulty,
        "winner_user_id": result.winner_user_id,
        "players": [
            {
                "user_id": player.user_id,
                "words": player.words,
                "word_count": player.word_count,
                "total_letters": player.total_letters,
                "longest_word": player.longest_word,
                "stage_points": player.stage_points,
            }
            for player in result.players
        ],
    }


def _result_from_dict(value: dict[str, Any]) -> WordRoundResult:
    return WordRoundResult(
        stage_number=value["stage_number"],
        difficulty=value["difficulty"],
        winner_user_id=value.get("winner_user_id"),
        players=[
            WordRoundPlayerResult(
                user_id=player["user_id"],
                words=list(player.get("words", [])),
                word_count=player["word_count"],
                total_letters=player["total_letters"],
                longest_word=player.get("longest_word"),
                stage_points=float(player["stage_points"]),
            )
            for player in value.get("players", [])
        ],
    )


def _state_to_dict(state: WordBattleState) -> dict[str, Any]:
    return {
        "players": [
            {
                "user_id": player.user_id,
                "submissions": [
                    _submission_to_dict(item) for item in player.submissions
                ],
                "stage_points": player.stage_points,
                "total_words": player.total_words,
                "total_letters": player.total_letters,
            }
            for player in state.players
        ],
        "rounds": [_round_to_dict(round_spec) for round_spec in state.rounds],
        "stage_index": state.stage_index,
        "status": state.status,
        "phase_started_at": state.phase_started_at.isoformat(),
        "phase_ends_at": state.phase_ends_at.isoformat(),
        "results": [_result_to_dict(result) for result in state.results],
        "winner_user_id": state.winner_user_id,
    }


def _state_from_dict(value: dict[str, Any]) -> WordBattleState:
    return WordBattleState(
        players=[
            WordPlayerState(
                user_id=player["user_id"],
                submissions=[
                    _submission_from_dict(item)
                    for item in player.get("submissions", [])
                ],
                stage_points=float(player.get("stage_points", 0)),
                total_words=player.get("total_words", 0),
                total_letters=player.get("total_letters", 0),
            )
            for player in value.get("players", [])
        ],
        rounds=[_round_from_dict(item) for item in value.get("rounds", [])],
        stage_index=value.get("stage_index", 0),
        status=value.get("status", "countdown"),
        phase_started_at=datetime.fromisoformat(value["phase_started_at"]),
        phase_ends_at=datetime.fromisoformat(value["phase_ends_at"]),
        results=[_result_from_dict(item) for item in value.get("results", [])],
        winner_user_id=value.get("winner_user_id"),
    )


def _player_entries(game: KelimeKapismasiGame) -> list[tuple[uuid.UUID, User]]:
    entries: list[tuple[uuid.UUID, User]] = [
        (game.player_one_user_id, game.player_one_user)
    ]
    if game.player_two_user_id and game.player_two_user:
        entries.append((game.player_two_user_id, game.player_two_user))
    return entries


def _player_ids(game: KelimeKapismasiGame) -> list[uuid.UUID]:
    return [
        user_id
        for user_id in (game.player_one_user_id, game.player_two_user_id)
        if user_id is not None
    ]


def _require_player(game: KelimeKapismasiGame, actor: User) -> None:
    if actor.id not in _player_ids(game):
        raise ForbiddenError("Bu oyundaki oyunculardan biri değilsiniz.")


def _latest_result_response(
    state: WordBattleState,
) -> KelimeKapismasiRoundResultResponse | None:
    if not state.results:
        return None
    result = state.results[-1]
    return KelimeKapismasiRoundResultResponse(
        stage_number=result.stage_number,
        difficulty=result.difficulty,
        winner_user_id=(
            uuid.UUID(result.winner_user_id) if result.winner_user_id else None
        ),
        players=[
            KelimeKapismasiRoundPlayerResultResponse(
                user_id=uuid.UUID(player.user_id),
                words=player.words,
                word_count=player.word_count,
                total_letters=player.total_letters,
                longest_word=player.longest_word,
                stage_points=player.stage_points,
            )
            for player in result.players
        ],
    )


def _game_response(
    game: KelimeKapismasiGame,
    viewer_id: uuid.UUID,
    *,
    now: datetime | None = None,
) -> KelimeKapismasiGameResponse:
    state = _state_from_dict(game.state) if game.state else None
    own_words: list[str] = []
    player_states: dict[str, WordPlayerState] = {}

    if state:
        player_states = {player.user_id: player for player in state.players}
        viewer = player_states.get(str(viewer_id))
        if viewer:
            own_words = [item.word for item in viewer.submissions]

    players = [
        KelimeKapismasiPlayerResponse(
            user_id=user_id,
            player_order=index,
            current_word_count=len(
                player_states.get(str(user_id), WordPlayerState(str(user_id))).submissions
            ),
            stage_points=player_states.get(
                str(user_id), WordPlayerState(str(user_id))
            ).stage_points,
            total_words=player_states.get(
                str(user_id), WordPlayerState(str(user_id))
            ).total_words,
            total_letters=player_states.get(
                str(user_id), WordPlayerState(str(user_id))
            ).total_letters,
            is_creator=game.creator_id == user_id,
            user=UserResponse.model_validate(user),
        )
        for index, (user_id, user) in enumerate(_player_entries(game))
    ]

    round_spec = current_round(state) if state else None
    return KelimeKapismasiGameResponse(
        id=game.id,
        creator_id=game.creator_id,
        status=game.status,
        version=game.version,
        stage_number=state.stage_index + 1 if state else 0,
        difficulty=round_spec.difficulty if round_spec else None,
        letters=list(round_spec.letters) if round_spec else [],
        min_length=round_spec.min_length if round_spec else 0,
        duration_seconds=round_spec.duration_seconds if round_spec else 0,
        phase_started_at=state.phase_started_at if state else None,
        phase_ends_at=state.phase_ends_at if state else None,
        remaining_seconds=remaining_seconds(state, now=now) if state else 0,
        own_words=own_words,
        own_word_count=len(own_words),
        players=players,
        latest_result=_latest_result_response(state) if state else None,
        winner_user_id=game.winner_user_id,
    )


def _apply_synced_state(
    game: KelimeKapismasiGame,
    state: WordBattleState,
) -> None:
    game.state = _state_to_dict(state)
    game.status = state.status
    game.winner_user_id = (
        uuid.UUID(state.winner_user_id) if state.winner_user_id else None
    )
    game.version += 1


async def create_kelime_kapismasi_game(
    session: AsyncSession,
    room: Room,
    actor: User,
) -> tuple[KelimeKapismasiGameResponse, RoomMessage]:
    await _require_member(session, room, actor)
    existing = await session.scalar(
        select(KelimeKapismasiGame).where(KelimeKapismasiGame.room_id == room.id)
    )
    if existing is not None and existing.status != "finished":
        raise ConflictError("Bu odada zaten açık bir Kelime Kapışması var.")
    if existing is not None:
        await session.delete(existing)
        await session.flush()

    game = KelimeKapismasiGame(
        room_id=room.id,
        creator_id=actor.id,
        player_one_user_id=actor.id,
        status="waiting",
        state={},
        version=1,
    )
    session.add(game)
    await session.flush()

    message = RoomMessage(
        room_id=room.id,
        user_id=actor.id,
        text=f"🔤 {actor.display_name} Kelime Kapışması başlattı.",
        message_type="kelime_kapismasi_invite",
        payload={"game_id": str(game.id)},
    )
    message.user = actor
    session.add(message)
    await session.commit()
    await session.refresh(message)
    game = await _load_game(session, room)
    return _game_response(game, actor.id), message


async def get_kelime_kapismasi_game(
    session: AsyncSession,
    room: Room,
    actor: User,
) -> KelimeKapismasiGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    if game.state:
        state = _state_from_dict(game.state)
        if sync_state(state):
            _apply_synced_state(game, state)
            await session.commit()
            game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def join_kelime_kapismasi_game(
    session: AsyncSession,
    room: Room,
    actor: User,
) -> KelimeKapismasiGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    if game.status != "waiting":
        raise ConflictError("Katılabileceğiniz açık bir Kelime Kapışması yok.")
    if actor.id in _player_ids(game):
        raise ConflictError("Bu oyuna zaten katıldınız.")
    if game.player_two_user_id is not None:
        raise ConflictError("Kelime Kapışması iki kişiliktir ve masa dolu.")

    game.player_two_user_id = actor.id
    game.version += 1
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def start_kelime_kapismasi_game(
    session: AsyncSession,
    room: Room,
    actor: User,
) -> KelimeKapismasiGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    if game.status != "waiting":
        raise ConflictError("Oyun zaten başlatılmış veya bitmiş.")
    if actor.id != game.creator_id:
        raise ForbiddenError("Oyunu yalnızca masayı açan başlatabilir.")
    if game.player_two_user_id is None:
        raise ConflictError("Oyunu başlatmak için ikinci oyuncu gerekir.")

    state = start_game(
        [str(game.player_one_user_id), str(game.player_two_user_id)],
        _build_rounds(),
    )
    game.state = _state_to_dict(state)
    game.status = state.status
    game.winner_user_id = None
    game.version += 1
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def submit_kelime_kapismasi_word(
    session: AsyncSession,
    room: Room,
    actor: User,
    word: str,
) -> KelimeKapismasiGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    _require_player(game, actor)
    if not game.state or game.status == "waiting":
        raise ConflictError("Aktif Kelime Kapışması bulunamadı.")

    state = _state_from_dict(game.state)
    try:
        submit_word(state, str(actor.id), word)
    except ValueError as error:
        _apply_synced_state(game, state)
        await session.commit()
        raise ConflictError(str(error)) from error

    _apply_synced_state(game, state)
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def restart_kelime_kapismasi_game(
    session: AsyncSession,
    room: Room,
    actor: User,
) -> KelimeKapismasiGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    if game.status != "finished":
        raise ConflictError("Oyun henüz bitmedi.")
    if actor.id != game.creator_id:
        raise ForbiddenError("Oyunu yalnızca masa sahibi yeniden başlatabilir.")
    if game.player_two_user_id is None:
        raise ConflictError("Rövanş için ikinci oyuncu bulunamadı.")

    state = start_game(
        [str(game.player_one_user_id), str(game.player_two_user_id)],
        _build_rounds(),
    )
    game.state = _state_to_dict(state)
    game.status = state.status
    game.winner_user_id = None
    game.version += 1
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id, now=datetime.now(UTC))
