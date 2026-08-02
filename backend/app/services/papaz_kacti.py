from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.games.cards import Card
from app.games.papaz_kacti import (
    PapazKactiState,
    PapazKactiPlayerState,
    draw_card,
    start_game,
)
from app.models.papaz_kacti import PapazKactiGame
from app.models.room import Room, RoomMember, RoomMessage
from app.models.user import User
from app.schemas.papaz_kacti import PapazKactiCardResponse, PapazKactiGameResponse
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
) -> PapazKactiGame:
    query = (
        select(PapazKactiGame)
        .where(PapazKactiGame.room_id == room.id)
        .options(
            selectinload(PapazKactiGame.player_one_user),
            selectinload(PapazKactiGame.player_two_user),
            selectinload(PapazKactiGame.player_three_user),
            selectinload(PapazKactiGame.player_four_user),
        )
        .execution_options(populate_existing=True)
    )
    if for_update:
        query = query.with_for_update()

    game = await session.scalar(query)
    if game is None:
        raise NotFoundError("Bu odada Papaz Kaçtı masası bulunamadı.")
    return game


def _card_to_dict(card: Card) -> dict[str, str]:
    return {"suit": card.suit, "rank": card.rank}


def _card_from_dict(value: dict[str, str]) -> Card:
    return Card(suit=value["suit"], rank=value["rank"])


def _state_to_dict(state: PapazKactiState) -> dict[str, Any]:
    return {
        "players": [
            {
                "user_id": player.user_id,
                "hand": [_card_to_dict(card) for card in player.hand],
                "is_finished": player.is_finished,
            }
            for player in state.players
        ],
        "turn_index": state.turn_index,
        "status": state.status,
        "loser_user_id": state.loser_user_id,
        "log": state.log,
    }


def _state_from_dict(value: dict[str, Any]) -> PapazKactiState:
    return PapazKactiState(
        players=[
            PapazKactiPlayerState(
                user_id=player["user_id"],
                hand=[_card_from_dict(card) for card in player.get("hand", [])],
                is_finished=player.get("is_finished", False),
            )
            for player in value.get("players", [])
        ],
        turn_index=value.get("turn_index", 0),
        status=value.get("status", "active"),
        loser_user_id=value.get("loser_user_id"),
        log=value.get("log", []),
    )


def _card_response(card: Card) -> PapazKactiCardResponse:
    return PapazKactiCardResponse(id=card.id, suit=card.suit, rank=card.rank)


def _game_response(game: PapazKactiGame, viewer_id: uuid.UUID) -> PapazKactiGameResponse:
    state = _state_from_dict(game.state) if game.state else None
    viewer_hand: list[PapazKactiCardResponse] = []
    turn_user_id: uuid.UUID | None = None
    hand_counts: dict[str, int] = {}
    
    if state is not None:
        for player in state.players:
            hand_counts[player.user_id] = len(player.hand)
            if player.user_id == str(viewer_id):
                viewer_hand = [_card_response(card) for card in player.hand]
        if state.status == "active" and state.players:
            turn_user_id = uuid.UUID(state.players[state.turn_index].user_id)

    return PapazKactiGameResponse(
        id=game.id,
        creator_id=game.creator_id,
        player_one_user_id=game.player_one_user_id,
        player_two_user_id=game.player_two_user_id,
        player_three_user_id=game.player_three_user_id,
        player_four_user_id=game.player_four_user_id,
        status=game.status,
        turn_user_id=turn_user_id,
        loser_user_id=game.loser_user_id,
        hand=viewer_hand,
        hand_counts=hand_counts,
        player_one_user=UserResponse.model_validate(game.player_one_user),
        player_two_user=(
            UserResponse.model_validate(game.player_two_user)
            if game.player_two_user is not None
            else None
        ),
        player_three_user=(
            UserResponse.model_validate(game.player_three_user)
            if game.player_three_user is not None
            else None
        ),
        player_four_user=(
            UserResponse.model_validate(game.player_four_user)
            if game.player_four_user is not None
            else None
        ),
    )


async def create_papaz_kacti_game(
    session: AsyncSession, room: Room, actor: User
) -> tuple[PapazKactiGameResponse, RoomMessage]:
    await _require_member(session, room, actor)
    existing = await session.scalar(select(PapazKactiGame).where(PapazKactiGame.room_id == room.id))
    if existing is not None and existing.status in {"waiting", "active"}:
        raise ConflictError("Bu odada zaten açık bir Papaz Kaçtı masası var.")
    if existing is not None:
        await session.delete(existing)
        await session.flush()

    game = PapazKactiGame(
        room_id=room.id,
        creator_id=actor.id,
        player_one_user_id=actor.id,
        status="waiting",
        state={},
    )
    session.add(game)
    await session.flush()

    message = RoomMessage(
        room_id=room.id,
        user_id=actor.id,
        text=f"🃏 {actor.display_name} Papaz Kaçtı masası açtı.",
        message_type="papaz_kacti_invite",
        payload={"game_id": str(game.id)},
    )
    message.user = actor
    session.add(message)
    await session.commit()
    await session.refresh(message)
    game = await _load_game(session, room)
    return _game_response(game, actor.id), message


async def join_papaz_kacti_game(
    session: AsyncSession, room: Room, actor: User
) -> PapazKactiGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    if game.status != "waiting":
        raise ConflictError("Katılabileceğiniz açık bir Papaz Kaçtı daveti yok.")
        
    player_ids = [game.player_one_user_id]
    if game.player_two_user_id: player_ids.append(game.player_two_user_id)
    if game.player_three_user_id: player_ids.append(game.player_three_user_id)
    if game.player_four_user_id: player_ids.append(game.player_four_user_id)

    if actor.id in player_ids:
        raise ConflictError("Bu oyuna zaten katıldınız.")
        
    if len(player_ids) >= 4:
        raise ConflictError("Oyun dolu (Maks 4 kişi).")
        
    if game.player_two_user_id is None:
        game.player_two_user_id = actor.id
    elif game.player_three_user_id is None:
        game.player_three_user_id = actor.id
    elif game.player_four_user_id is None:
        game.player_four_user_id = actor.id

    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def start_papaz_kacti_game(
    session: AsyncSession, room: Room, actor: User
) -> PapazKactiGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    if game.status != "waiting":
        raise ConflictError("Oyun zaten başlatılmış veya bitmiş.")
    if actor.id != game.creator_id:
        raise ForbiddenError("Oyunu sadece masayı açan başlatabilir.")
        
    player_ids = [str(game.player_one_user_id)]
    if game.player_two_user_id: player_ids.append(str(game.player_two_user_id))
    if game.player_three_user_id: player_ids.append(str(game.player_three_user_id))
    if game.player_four_user_id: player_ids.append(str(game.player_four_user_id))
    
    if len(player_ids) < 2:
        raise ConflictError("Oyunu başlatmak için en az 2 oyuncu gerekiyor.")

    state = start_game(player_ids)
    game.state = _state_to_dict(state)
    game.status = state.status
    game.loser_user_id = uuid.UUID(state.loser_user_id) if state.loser_user_id else None
    await session.commit()
    
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def get_papaz_kacti_game(
    session: AsyncSession, room: Room, actor: User
) -> PapazKactiGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def draw_papaz_kacti_card(
    session: AsyncSession, room: Room, actor: User, card_index: int
) -> PapazKactiGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    if game.status != "active" or not game.state:
        raise ConflictError("Aktif Papaz Kaçtı oyunu bulunamadı.")
        
    player_ids = [game.player_one_user_id]
    if game.player_two_user_id: player_ids.append(game.player_two_user_id)
    if game.player_three_user_id: player_ids.append(game.player_three_user_id)
    if game.player_four_user_id: player_ids.append(game.player_four_user_id)
        
    if actor.id not in player_ids:
        raise ForbiddenError("Bu oyundaki oyunculardan biri değilsiniz.")

    state = _state_from_dict(game.state)
    try:
        draw_card(state, str(actor.id), card_index)
    except ValueError as error:
        raise ConflictError(str(error)) from error

    game.state = _state_to_dict(state)
    game.status = state.status
    if state.loser_user_id:
        game.loser_user_id = uuid.UUID(state.loser_user_id)
        
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def restart_papaz_kacti_game(
    session: AsyncSession, room: Room, actor: User
) -> PapazKactiGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room, for_update=True)
    
    if game.status != "finished":
        raise ConflictError("Oyun henüz bitmedi.")
        
    if actor.id != game.creator_id:
        raise ForbiddenError("Oyunu yalnızca masa sahibi yeniden başlatabilir.")
    
    player_ids = [game.player_one_user_id]
    if game.player_two_user_id: player_ids.append(game.player_two_user_id)
    if game.player_three_user_id: player_ids.append(game.player_three_user_id)
    if game.player_four_user_id: player_ids.append(game.player_four_user_id)
        
    if len(player_ids) < 2:
        raise ConflictError("Yeni oyun için en az iki oyuncu bekleniyor.")

    state = start_game([str(pid) for pid in player_ids])
    game.state = _state_to_dict(state)
    game.status = state.status
    game.loser_user_id = None
    
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)
