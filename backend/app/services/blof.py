from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.games.blof import (
    BlofChallengeResult,
    BlofPlayerState,
    BlofState,
    accept_last_play,
    call_bluff,
    play_cards,
    start_game,
)
from app.games.cards import Card
from app.models.blof import BlofGame
from app.models.room import Room, RoomMember, RoomMessage
from app.models.user import User
from app.schemas.blof import (
    BlofCardResponse,
    BlofChallengeResultResponse,
    BlofGameResponse,
    BlofPlayerResponse,
)
from app.schemas.user import UserResponse
from app.services.errors import ConflictError, ForbiddenError, NotFoundError


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
) -> BlofGame:
    query = (
        select(BlofGame)
        .where(BlofGame.room_id == room.id)
        .options(
            selectinload(BlofGame.player_one_user),
            selectinload(BlofGame.player_two_user),
            selectinload(BlofGame.player_three_user),
            selectinload(BlofGame.player_four_user),
        )
        .execution_options(populate_existing=True)
    )
    if for_update:
        query = query.with_for_update()
    game = await session.scalar(query)
    if game is None:
        raise NotFoundError("Bu odada Blöf masası bulunamadı.")
    return game


def _card_to_dict(card: Card) -> dict[str, str]:
    return {"suit": card.suit, "rank": card.rank}


def _card_from_dict(value: dict[str, str]) -> Card:
    return Card(suit=value["suit"], rank=value["rank"])


def _result_to_dict(result: BlofChallengeResult | None) -> dict[str, Any] | None:
    if result is None:
        return None
    return {
        "truthful": result.truthful,
        "challenger_user_id": result.challenger_user_id,
        "challenged_user_id": result.challenged_user_id,
        "pile_receiver_user_id": result.pile_receiver_user_id,
        "next_turn_user_id": result.next_turn_user_id,
        "revealed_cards": [_card_to_dict(card) for card in result.revealed_cards],
    }


def _result_from_dict(value: dict[str, Any] | None) -> BlofChallengeResult | None:
    if value is None:
        return None
    return BlofChallengeResult(
        truthful=bool(value["truthful"]),
        challenger_user_id=value["challenger_user_id"],
        challenged_user_id=value["challenged_user_id"],
        pile_receiver_user_id=value["pile_receiver_user_id"],
        next_turn_user_id=value.get("next_turn_user_id"),
        revealed_cards=[_card_from_dict(card) for card in value.get("revealed_cards", [])],
    )


def _state_to_dict(state: BlofState) -> dict[str, Any]:
    return {
        "players": [
            {
                "user_id": player.user_id,
                "hand": [_card_to_dict(card) for card in player.hand],
            }
            for player in state.players
        ],
        "turn_index": state.turn_index,
        "status": state.status,
        "pile": [_card_to_dict(card) for card in state.pile],
        "last_played_cards": [_card_to_dict(card) for card in state.last_played_cards],
        "last_declared_rank": state.last_declared_rank,
        "last_player_user_id": state.last_player_user_id,
        "pending_winner_user_id": state.pending_winner_user_id,
        "winner_user_id": state.winner_user_id,
        "last_result": _result_to_dict(state.last_result),
    }


def _state_from_dict(value: dict[str, Any]) -> BlofState:
    return BlofState(
        players=[
            BlofPlayerState(
                user_id=player["user_id"],
                hand=[_card_from_dict(card) for card in player.get("hand", [])],
            )
            for player in value.get("players", [])
        ],
        turn_index=value.get("turn_index", 0),
        status=value.get("status", "active"),
        pile=[_card_from_dict(card) for card in value.get("pile", [])],
        last_played_cards=[
            _card_from_dict(card) for card in value.get("last_played_cards", [])
        ],
        last_declared_rank=value.get("last_declared_rank"),
        last_player_user_id=value.get("last_player_user_id"),
        pending_winner_user_id=value.get("pending_winner_user_id"),
        winner_user_id=value.get("winner_user_id"),
        last_result=_result_from_dict(value.get("last_result")),
    )


def _card_response(card: Card) -> BlofCardResponse:
    return BlofCardResponse(id=card.id, suit=card.suit, rank=card.rank)


def _player_entries(game: BlofGame) -> list[tuple[uuid.UUID, User]]:
    entries: list[tuple[uuid.UUID, User]] = [(game.player_one_user_id, game.player_one_user)]
    optional = [
        (game.player_two_user_id, game.player_two_user),
        (game.player_three_user_id, game.player_three_user),
        (game.player_four_user_id, game.player_four_user),
    ]
    entries.extend((user_id, user) for user_id, user in optional if user_id and user)
    return entries


def _game_response(game: BlofGame, viewer_id: uuid.UUID) -> BlofGameResponse:
    state = _state_from_dict(game.state) if game.state else None
    hand: list[BlofCardResponse] = []
    turn_user_id: uuid.UUID | None = None
    pending_winner_user_id: uuid.UUID | None = None
    winner_user_id = game.winner_user_id
    hand_counts: dict[str, int] = {}

    if state is not None:
        for player in state.players:
            hand_counts[player.user_id] = len(player.hand)
            if player.user_id == str(viewer_id):
                hand = [_card_response(card) for card in player.hand]
        if state.status == "active" and state.players:
            turn_user_id = uuid.UUID(state.players[state.turn_index].user_id)
        if state.pending_winner_user_id:
            pending_winner_user_id = uuid.UUID(state.pending_winner_user_id)
        if state.winner_user_id:
            winner_user_id = uuid.UUID(state.winner_user_id)

    players = [
        BlofPlayerResponse(
            user_id=user_id,
            player_order=index,
            hand_count=hand_counts.get(str(user_id), 0),
            is_current_turn=turn_user_id == user_id,
            is_creator=game.creator_id == user_id,
            user=UserResponse.model_validate(user),
        )
        for index, (user_id, user) in enumerate(_player_entries(game))
    ]

    last_result = None
    if state is not None and state.last_result is not None:
        result = state.last_result
        last_result = BlofChallengeResultResponse(
            truthful=result.truthful,
            challenger_user_id=uuid.UUID(result.challenger_user_id),
            challenged_user_id=uuid.UUID(result.challenged_user_id),
            pile_receiver_user_id=uuid.UUID(result.pile_receiver_user_id),
            next_turn_user_id=(
                uuid.UUID(result.next_turn_user_id) if result.next_turn_user_id else None
            ),
            revealed_cards=[_card_response(card) for card in result.revealed_cards],
        )

    return BlofGameResponse(
        id=game.id,
        creator_id=game.creator_id,
        status=game.status,
        version=game.version,
        turn_user_id=turn_user_id,
        pending_winner_user_id=pending_winner_user_id,
        winner_user_id=winner_user_id,
        pile_count=len(state.pile) if state else 0,
        last_play_count=len(state.last_played_cards) if state else 0,
        last_declared_rank=state.last_declared_rank if state else None,
        last_player_user_id=(
            uuid.UUID(state.last_player_user_id)
            if state and state.last_player_user_id
            else None
        ),
        hand=hand,
        players=players,
        last_result=last_result,
    )


async def create_blof_game(
    session: AsyncSession, room: Room, actor: User
) -> tuple[BlofGameResponse, RoomMessage]:
    await _require_member(session, room, actor)
    existing = await session.scalar(select(BlofGame).where(BlofGame.room_id == room.id))
    if existing is not None and existing.status in {"waiting", "active"}:
        raise ConflictError("Bu odada zaten açık bir Blöf masası var.")
    if existing is not None:
        await session.delete(existing)
        await session.flush()

    game = BlofGame(
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
        text=f"🎭 {actor.display_name} Blöf masası açtı.",
        message_type="blof_invite",
        payload={"game_id": str(game.id)},
    )
    message.user = actor
    session.add(message)
    await session.commit()
    await session.refresh(message)
    game = await _load_game(session, room)
    return _game_response(game, actor.id), message


async def get_blof_game(
    session: AsyncSession, room: Room, actor: User
) -> BlofGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def join_blof_game(
    session: AsyncSession, room: Room, actor: User
) -> BlofGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    if game.status != "waiting":
        raise ConflictError("Katılabileceğiniz açık bir Blöf daveti yok.")

    player_ids = [user_id for user_id, _ in _player_entries(game)]
    if actor.id in player_ids:
        raise ConflictError("Bu oyuna zaten katıldınız.")
    if len(player_ids) >= 4:
        raise ConflictError("Blöf masası dolu.")

    if game.player_two_user_id is None:
        game.player_two_user_id = actor.id
    elif game.player_three_user_id is None:
        game.player_three_user_id = actor.id
    else:
        game.player_four_user_id = actor.id
    game.version += 1
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def start_blof_game(
    session: AsyncSession, room: Room, actor: User
) -> BlofGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    if game.status != "waiting":
        raise ConflictError("Oyun zaten başlatılmış veya bitmiş.")
    if actor.id != game.creator_id:
        raise ForbiddenError("Oyunu yalnızca masayı açan başlatabilir.")

    player_ids = [str(user_id) for user_id, _ in _player_entries(game)]
    if len(player_ids) < 2:
        raise ConflictError("Oyunu başlatmak için en az 2 oyuncu gerekir.")

    state = start_game(player_ids)
    game.state = _state_to_dict(state)
    game.status = state.status
    game.winner_user_id = None
    game.version += 1
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def play_blof_cards(
    session: AsyncSession,
    room: Room,
    actor: User,
    card_ids: list[str],
    declared_rank: str,
) -> BlofGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    if game.status != "active" or not game.state:
        raise ConflictError("Aktif Blöf oyunu bulunamadı.")

    player_ids = [user_id for user_id, _ in _player_entries(game)]
    if actor.id not in player_ids:
        raise ForbiddenError("Bu oyundaki oyunculardan biri değilsiniz.")

    state = _state_from_dict(game.state)
    try:
        play_cards(state, str(actor.id), card_ids, declared_rank)
    except ValueError as error:
        raise ConflictError(str(error)) from error

    game.state = _state_to_dict(state)
    game.status = state.status
    game.winner_user_id = uuid.UUID(state.winner_user_id) if state.winner_user_id else None
    game.version += 1
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def call_blof(
    session: AsyncSession, room: Room, actor: User
) -> BlofGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    if game.status != "active" or not game.state:
        raise ConflictError("Aktif Blöf oyunu bulunamadı.")

    state = _state_from_dict(game.state)
    try:
        call_bluff(state, str(actor.id))
    except ValueError as error:
        raise ConflictError(str(error)) from error

    game.state = _state_to_dict(state)
    game.status = state.status
    game.winner_user_id = uuid.UUID(state.winner_user_id) if state.winner_user_id else None
    game.version += 1
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def accept_blof_play(
    session: AsyncSession, room: Room, actor: User
) -> BlofGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    if game.status != "active" or not game.state:
        raise ConflictError("Aktif Blöf oyunu bulunamadı.")

    state = _state_from_dict(game.state)
    try:
        accept_last_play(state, str(actor.id))
    except ValueError as error:
        raise ConflictError(str(error)) from error

    game.state = _state_to_dict(state)
    game.status = state.status
    game.winner_user_id = uuid.UUID(state.winner_user_id) if state.winner_user_id else None
    game.version += 1
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def restart_blof_game(
    session: AsyncSession, room: Room, actor: User
) -> BlofGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    if game.status != "finished":
        raise ConflictError("Oyun henüz bitmedi.")
    if actor.id != game.creator_id:
        raise ForbiddenError("Oyunu yalnızca masa sahibi yeniden başlatabilir.")

    player_ids = [str(user_id) for user_id, _ in _player_entries(game)]
    state = start_game(player_ids)
    game.state = _state_to_dict(state)
    game.status = state.status
    game.winner_user_id = None
    game.version += 1
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)
