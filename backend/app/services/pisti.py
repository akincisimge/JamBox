from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.games.pisti import Card, PistiState, PlayerState, play_card, scores, start_game
from app.models.pisti import PistiGame
from app.models.room import Room, RoomMember, RoomMessage
from app.models.user import User
from app.schemas.pisti import PistiCardResponse, PistiGameResponse
from app.schemas.user import UserResponse
from app.services.errors import ConflictError, ForbiddenError, NotFoundError


async def _require_member(session: AsyncSession, room: Room, user: User) -> RoomMember:
    membership = await session.get(RoomMember, {"room_id": room.id, "user_id": user.id})
    if membership is None:
        raise NotFoundError("Kullanıcı bu odada değil.")
    return membership


async def _load_game(session: AsyncSession, room: Room) -> PistiGame:
    game = await session.scalar(
        select(PistiGame)
        .where(PistiGame.room_id == room.id)
        .options(
            selectinload(PistiGame.player_one_user),
            selectinload(PistiGame.player_two_user),
        )
        .execution_options(populate_existing=True)
    )
    if game is None:
        raise NotFoundError("Bu odada Pişti masası bulunamadı.")
    return game


def _card_to_dict(card: Card) -> dict[str, str]:
    return {"suit": card.suit, "rank": card.rank}


def _card_from_dict(value: dict[str, str]) -> Card:
    return Card(suit=value["suit"], rank=value["rank"])


def _state_to_dict(state: PistiState) -> dict[str, Any]:
    return {
        "players": [
            {
                "user_id": player.user_id,
                "hand": [_card_to_dict(card) for card in player.hand],
                "captured": [_card_to_dict(card) for card in player.captured],
                "pisti_count": player.pisti_count,
            }
            for player in state.players
        ],
        "deck": [_card_to_dict(card) for card in state.deck],
        "table": [_card_to_dict(card) for card in state.table],
        "turn_index": state.turn_index,
        "last_capturer_index": state.last_capturer_index,
        "status": state.status,
    }


def _state_from_dict(value: dict[str, Any]) -> PistiState:
    return PistiState(
        players=[
            PlayerState(
                user_id=player["user_id"],
                hand=[_card_from_dict(card) for card in player.get("hand", [])],
                captured=[_card_from_dict(card) for card in player.get("captured", [])],
                pisti_count=player.get("pisti_count", 0),
            )
            for player in value.get("players", [])
        ],
        deck=[_card_from_dict(card) for card in value.get("deck", [])],
        table=[_card_from_dict(card) for card in value.get("table", [])],
        turn_index=value.get("turn_index", 0),
        last_capturer_index=value.get("last_capturer_index"),
        status=value.get("status", "active"),
    )


def _card_response(card: Card) -> PistiCardResponse:
    return PistiCardResponse(id=card.id, suit=card.suit, rank=card.rank)


def _winner_id(score_values: dict[str, int]) -> uuid.UUID | None:
    if not score_values:
        return None
    best_score = max(score_values.values())
    winners = [user_id for user_id, score in score_values.items() if score == best_score]
    return uuid.UUID(winners[0]) if len(winners) == 1 else None


def _game_response(game: PistiGame, viewer_id: uuid.UUID) -> PistiGameResponse:
    state = _state_from_dict(game.state) if game.state else None
    viewer_hand: list[PistiCardResponse] = []
    turn_user_id: uuid.UUID | None = None
    hand_counts: dict[str, int] = {}
    captured_counts: dict[str, int] = {}
    pisti_counts: dict[str, int] = {}
    table: list[PistiCardResponse] = []
    deck_count = 0

    if state is not None:
        for player in state.players:
            hand_counts[player.user_id] = len(player.hand)
            captured_counts[player.user_id] = len(player.captured)
            pisti_counts[player.user_id] = player.pisti_count
            if player.user_id == str(viewer_id):
                viewer_hand = [_card_response(card) for card in player.hand]
        if state.status == "active" and state.players:
            turn_user_id = uuid.UUID(state.players[state.turn_index].user_id)
        table = [_card_response(card) for card in state.table]
        deck_count = len(state.deck)

    return PistiGameResponse(
        id=game.id,
        creator_id=game.creator_id,
        player_one_user_id=game.player_one_user_id,
        player_two_user_id=game.player_two_user_id,
        status=game.status,
        turn_user_id=turn_user_id,
        hand=viewer_hand,
        hand_counts=hand_counts,
        captured_counts=captured_counts,
        pisti_counts=pisti_counts,
        table=table,
        deck_count=deck_count,
        scores=game.scores or {},
        winner_user_id=game.winner_user_id,
        player_one_user=UserResponse.model_validate(game.player_one_user),
        player_two_user=(
            UserResponse.model_validate(game.player_two_user)
            if game.player_two_user is not None
            else None
        ),
    )


async def create_pisti_game(
    session: AsyncSession, room: Room, actor: User
) -> tuple[PistiGameResponse, RoomMessage]:
    await _require_member(session, room, actor)
    existing = await session.scalar(select(PistiGame).where(PistiGame.room_id == room.id))
    if existing is not None and existing.status in {"waiting", "active"}:
        raise ConflictError("Bu odada zaten açık bir Pişti masası var.")
    if existing is not None:
        await session.delete(existing)
        await session.flush()

    game = PistiGame(
        room_id=room.id,
        creator_id=actor.id,
        player_one_user_id=actor.id,
        status="waiting",
        state={},
        scores={},
    )
    session.add(game)
    await session.flush()

    message = RoomMessage(
        room_id=room.id,
        user_id=actor.id,
        text=f"🃏 {actor.display_name} Pişti masası açtı.",
        message_type="pisti_invite",
        payload={"game_id": str(game.id)},
    )
    message.user = actor
    session.add(message)
    await session.commit()
    await session.refresh(message)
    game = await _load_game(session, room)
    return _game_response(game, actor.id), message


async def join_pisti_game(
    session: AsyncSession, room: Room, actor: User
) -> PistiGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room)
    if game.status != "waiting":
        raise ConflictError("Katılabileceğiniz açık bir Pişti daveti yok.")
    if game.player_one_user_id == actor.id:
        raise ConflictError("Kendi Pişti davetinize katılamazsınız.")

    game.player_two_user_id = actor.id
    state = start_game([str(game.player_one_user_id), str(actor.id)])
    game.state = _state_to_dict(state)
    game.status = "active"
    game.scores = {}
    game.winner_user_id = None
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def get_pisti_game(
    session: AsyncSession, room: Room, actor: User
) -> PistiGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def make_pisti_move(
    session: AsyncSession, room: Room, actor: User, card_id: str
) -> PistiGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room)
    if game.status != "active" or not game.state:
        raise ConflictError("Aktif Pişti oyunu bulunamadı.")
    if actor.id not in {game.player_one_user_id, game.player_two_user_id}:
        raise ForbiddenError("Bu Pişti masasındaki oyunculardan biri değilsiniz.")

    state = _state_from_dict(game.state)
    try:
        play_card(state, str(actor.id), card_id)
    except ValueError as error:
        raise ConflictError(str(error)) from error

    game.state = _state_to_dict(state)
    game.status = state.status
    if state.status == "finished":
        game.scores = scores(state)
        game.winner_user_id = _winner_id(game.scores)
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)


async def restart_pisti_game(
    session: AsyncSession, room: Room, actor: User
) -> PistiGameResponse:
    await _require_member(session, room, actor)
    game = await _load_game(session, room)
    if actor.id not in {game.player_one_user_id, game.player_two_user_id}:
        raise ForbiddenError("Bu Pişti masasını yalnızca oyuncular yenileyebilir.")
    if game.player_two_user_id is None:
        raise ConflictError("Yeni oyun için ikinci oyuncu bekleniyor.")

    state = start_game([str(game.player_one_user_id), str(game.player_two_user_id)])
    game.state = _state_to_dict(state)
    game.status = "active"
    game.scores = {}
    game.winner_user_id = None
    await session.commit()
    game = await _load_game(session, room)
    return _game_response(game, actor.id)
