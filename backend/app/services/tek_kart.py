from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.games.tek_kart import (
    TekKartCard,
    TekKartPlayerState,
    TekKartState,
    call_tek_kart,
    draw_card,
    play_card,
    playable_cards,
    start_game,
)
from app.models.room import Room, RoomMember, RoomMessage
from app.models.tek_kart import TekKartGame
from app.models.user import User
from app.schemas.tek_kart import (
    TekKartCardResponse,
    TekKartColor,
    TekKartGameResponse,
    TekKartPlayerResponse,
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
) -> TekKartGame:
    query = (
        select(TekKartGame)
        .where(TekKartGame.room_id == room.id)
        .options(
            selectinload(TekKartGame.player_one_user),
            selectinload(TekKartGame.player_two_user),
            selectinload(TekKartGame.player_three_user),
            selectinload(TekKartGame.player_four_user),
        )
        .execution_options(populate_existing=True)
    )
    if for_update:
        query = query.with_for_update()

    game = await session.scalar(query)
    if game is None:
        raise NotFoundError("Bu odada Tek Kart masası bulunamadı.")
    return game


def _card_to_dict(card: TekKartCard) -> dict[str, Any]:
    return {
        "id": card.id,
        "kind": card.kind,
        "color": card.color,
        "number": card.number,
    }


def _card_from_dict(value: dict[str, Any]) -> TekKartCard:
    return TekKartCard(
        id=value["id"],
        kind=value["kind"],
        color=value.get("color"),
        number=value.get("number"),
    )


def _state_to_dict(state: TekKartState) -> dict[str, Any]:
    return {
        "players": [
            {
                "user_id": player.user_id,
                "hand": [_card_to_dict(card) for card in player.hand],
                "called_tek_kart": player.called_tek_kart,
            }
            for player in state.players
        ],
        "draw_pile": [_card_to_dict(card) for card in state.draw_pile],
        "discard_pile": [_card_to_dict(card) for card in state.discard_pile],
        "active_color": state.active_color,
        "turn_index": state.turn_index,
        "direction": state.direction,
        "status": state.status,
        "winner_user_id": state.winner_user_id,
        "log": state.log,
    }


def _state_from_dict(value: dict[str, Any]) -> TekKartState:
    return TekKartState(
        players=[
            TekKartPlayerState(
                user_id=player["user_id"],
                hand=[_card_from_dict(card) for card in player.get("hand", [])],
                called_tek_kart=player.get("called_tek_kart", False),
            )
            for player in value.get("players", [])
        ],
        draw_pile=[_card_from_dict(card) for card in value.get("draw_pile", [])],
        discard_pile=[_card_from_dict(card) for card in value.get("discard_pile", [])],
        active_color=value["active_color"],
        turn_index=value.get("turn_index", 0),
        direction=value.get("direction", 1),
        status=value.get("status", "active"),
        winner_user_id=value.get("winner_user_id"),
        log=value.get("log", []),
    )


def _card_response(card: TekKartCard) -> TekKartCardResponse:
    return TekKartCardResponse(
        id=card.id,
        kind=card.kind,
        color=card.color,
        number=card.number,
    )


def _player_entries(game: TekKartGame) -> list[tuple[uuid.UUID, User]]:
    entries: list[tuple[uuid.UUID, User]] = [(game.player_one_user_id, game.player_one_user)]
    optional = [
        (game.player_two_user_id, game.player_two_user),
        (game.player_three_user_id, game.player_three_user),
        (game.player_four_user_id, game.player_four_user),
    ]
    entries.extend((user_id, user) for user_id, user in optional if user_id and user)
    return entries


def _player_ids(game: TekKartGame) -> list[uuid.UUID]:
    return [
        user_id
        for user_id in (
            game.player_one_user_id,
            game.player_two_user_id,
            game.player_three_user_id,
            game.player_four_user_id,
        )
        if user_id is not None
    ]


def _require_player(game: TekKartGame, actor: User) -> None:
    if actor.id not in _player_ids(game):
        raise ForbiddenError("Bu oyundaki oyunculardan biri değilsiniz.")


def _game_response(game: TekKartGame, viewer_id: uuid.UUID) -> TekKartGameResponse:
    state = _state_from_dict(game.state) if game.state else None
    hand: list[TekKartCardResponse] = []
    playable_card_ids: list[str] = []
    hand_counts: dict[str, int] = {}
    turn_user_id: uuid.UUID | None = None
    winner_user_id = game.winner_user_id
    called = False
    can_draw = False
    can_call = False

    if state is not None:
        viewer_player = None
        for player in state.players:
            hand_counts[player.user_id] = len(player.hand)
            if player.user_id == str(viewer_id):
                viewer_player = player
                hand = [_card_response(card) for card in player.hand]
                called = player.called_tek_kart

        if state.status == "active" and state.players:
            turn_user_id = uuid.UUID(state.players[state.turn_index].user_id)
        if state.winner_user_id:
            winner_user_id = uuid.UUID(state.winner_user_id)

        if viewer_player is not None and turn_user_id == viewer_id:
            playable = playable_cards(state, str(viewer_id))
            playable_card_ids = [card.id for card in playable]
            can_draw = not playable and bool(
                state.draw_pile or len(state.discard_pile) > 1
            )
            can_call = len(viewer_player.hand) == 2 and not called

    players = [
        TekKartPlayerResponse(
            user_id=user_id,
            player_order=index,
            hand_count=hand_counts.get(str(user_id), 0),
            is_current_turn=turn_user_id == user_id,
            is_creator=game.creator_id == user_id,
            user=UserResponse.model_validate(user),
        )
        for index, (user_id, user) in enumerate(_player_entries(game))
    ]

    return TekKartGameResponse(
        id=game.id,
        creator_id=game.creator_id,
        status=game.status,
        version=game.version,
        turn_user_id=turn_user_id,
        winner_user_id=winner_user_id,
        active_color=state.active_color if state else None,
        direction=state.direction if state else 1,
        draw_pile_count=len(state.draw_pile) if state else 0,
        top_card=_card_response(state.discard_pile[-1]) if state and state.discard_pile else None,
        hand=hand,
        playable_card_ids=playable_card_ids,
        can_draw=can_draw,
        can_call_tek_kart=can_call,
        called_tek_kart=called,
        players=players,
    )


async def create_tek_kart_game(
    session: AsyncSession, room: Room, actor: User
) -> tuple[TekKartGameResponse, RoomMessage]:
    await _require_member(session, room, actor)
    existing = await session.scalar(select(TekKartGame).where(TekKartGame.room_id == room.id))
    if existing is not None and existing.status in {"waiting", "active"}:
        raise ConflictError("Bu odada zaten açık bir Tek Kart masası var.")
    if existing is not None:
        await session.delete(existing)
        await session.flush()

    game = TekKartGame(
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
        text=f"🎨 {actor.display_name} Tek Kart masası açtı.",
        message_type="tek_kart_invite",
        payload={"game_id": str(game.id)},
    )
    message.user = actor
    session.add(message)
    await session.commit()
    await session.refresh(message)
    game = await _load_game(session, room)
    return _game_response(game, actor.id), message


async def get_tek_kart_game(
    session: AsyncSession, room: Room, actor: User
) -> TekKartGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def join_tek_kart_game(
    session: AsyncSession, room: Room, actor: User
) -> TekKartGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    if game.status != "waiting":
        raise ConflictError("Katılabileceğiniz açık bir Tek Kart daveti yok.")

    player_ids = _player_ids(game)
    if actor.id in player_ids:
        raise ConflictError("Bu oyuna zaten katıldınız.")
    if len(player_ids) >= 4:
        raise ConflictError("Tek Kart masası dolu.")

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


async def start_tek_kart_game(
    session: AsyncSession, room: Room, actor: User
) -> TekKartGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    if game.status != "waiting":
        raise ConflictError("Oyun zaten başlatılmış veya bitmiş.")
    if actor.id != game.creator_id:
        raise ForbiddenError("Oyunu yalnızca masayı açan başlatabilir.")

    player_ids = _player_ids(game)
    if len(player_ids) < 2:
        raise ConflictError("Oyunu başlatmak için en az 2 oyuncu gerekir.")

    state = start_game([str(user_id) for user_id in player_ids])
    game.state = _state_to_dict(state)
    game.status = state.status
    game.winner_user_id = None
    game.version += 1
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def play_tek_kart_card(
    session: AsyncSession,
    room: Room,
    actor: User,
    card_id: str,
    chosen_color: TekKartColor | None,
) -> TekKartGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    if game.status != "active" or not game.state:
        raise ConflictError("Aktif Tek Kart oyunu bulunamadı.")
    _require_player(game, actor)

    state = _state_from_dict(game.state)
    try:
        play_card(state, str(actor.id), card_id, chosen_color=chosen_color)
    except ValueError as error:
        raise ConflictError(str(error)) from error

    game.state = _state_to_dict(state)
    game.status = state.status
    game.winner_user_id = uuid.UUID(state.winner_user_id) if state.winner_user_id else None
    game.version += 1
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def draw_tek_kart_card(
    session: AsyncSession, room: Room, actor: User
) -> TekKartGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    if game.status != "active" or not game.state:
        raise ConflictError("Aktif Tek Kart oyunu bulunamadı.")
    _require_player(game, actor)

    state = _state_from_dict(game.state)
    try:
        draw_card(state, str(actor.id))
    except ValueError as error:
        raise ConflictError(str(error)) from error

    game.state = _state_to_dict(state)
    game.version += 1
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def call_tek_kart_for_player(
    session: AsyncSession, room: Room, actor: User
) -> TekKartGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    if game.status != "active" or not game.state:
        raise ConflictError("Aktif Tek Kart oyunu bulunamadı.")
    _require_player(game, actor)

    state = _state_from_dict(game.state)
    try:
        call_tek_kart(state, str(actor.id))
    except ValueError as error:
        raise ConflictError(str(error)) from error

    game.state = _state_to_dict(state)
    game.version += 1
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def restart_tek_kart_game(
    session: AsyncSession, room: Room, actor: User
) -> TekKartGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    if game.status != "finished":
        raise ConflictError("Oyun henüz bitmedi.")
    if actor.id != game.creator_id:
        raise ForbiddenError("Oyunu yalnızca masa sahibi yeniden başlatabilir.")

    state = start_game([str(user_id) for user_id in _player_ids(game)])
    game.state = _state_to_dict(state)
    game.status = state.status
    game.winner_user_id = None
    game.version += 1
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)
