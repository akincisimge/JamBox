from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.realtime.rooms import room_connections
from app.schemas.room import MessageResponse
from app.schemas.tek_kart import TekKartGameResponse, TekKartPlayRequest
from app.services.rooms import get_room
from app.services.tek_kart import (
    call_tek_kart_for_player,
    create_tek_kart_game,
    draw_tek_kart_card,
    get_tek_kart_game,
    join_tek_kart_game,
    play_tek_kart_card,
    restart_tek_kart_game,
    start_tek_kart_game,
)

router = APIRouter(prefix="/rooms")


async def _broadcast(code: str, game: TekKartGameResponse) -> None:
    await room_connections.broadcast(
        code,
        {
            "type": "tek_kart_updated",
            "room_code": code,
            "game_id": str(game.id),
            "version": game.version,
        },
    )


@router.post(
    "/{code}/tek-kart",
    response_model=TekKartGameResponse,
    status_code=status.HTTP_201_CREATED,
)
async def open_tek_kart_table(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> TekKartGameResponse:
    room = await get_room(session, code)
    game, invite = await create_tek_kart_game(session, room, current_user)
    invite_response = MessageResponse.model_validate(invite)
    await room_connections.broadcast(
        room.code,
        {"type": "message_created", "message": invite_response.model_dump(mode="json")},
    )
    await _broadcast(room.code, game)
    return game


@router.get("/{code}/tek-kart", response_model=TekKartGameResponse)
async def read_tek_kart_table(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> TekKartGameResponse:
    room = await get_room(session, code)
    return await get_tek_kart_game(session, room, current_user)


@router.post("/{code}/tek-kart/join", response_model=TekKartGameResponse)
async def join_tek_kart_table(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> TekKartGameResponse:
    room = await get_room(session, code)
    game = await join_tek_kart_game(session, room, current_user)
    await _broadcast(room.code, game)
    return game


@router.post("/{code}/tek-kart/start", response_model=TekKartGameResponse)
async def start_tek_kart_table(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> TekKartGameResponse:
    room = await get_room(session, code)
    game = await start_tek_kart_game(session, room, current_user)
    await _broadcast(room.code, game)
    return game


@router.post("/{code}/tek-kart/play", response_model=TekKartGameResponse)
async def play_tek_kart_card_route(
    code: str,
    payload: TekKartPlayRequest,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> TekKartGameResponse:
    room = await get_room(session, code)
    game = await play_tek_kart_card(
        session,
        room,
        current_user,
        payload.card_id,
        payload.chosen_color,
    )
    await _broadcast(room.code, game)
    return game


@router.post("/{code}/tek-kart/draw", response_model=TekKartGameResponse)
async def draw_tek_kart_card_route(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> TekKartGameResponse:
    room = await get_room(session, code)
    game = await draw_tek_kart_card(session, room, current_user)
    await _broadcast(room.code, game)
    return game


@router.post("/{code}/tek-kart/call", response_model=TekKartGameResponse)
async def call_tek_kart_route(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> TekKartGameResponse:
    room = await get_room(session, code)
    game = await call_tek_kart_for_player(session, room, current_user)
    await _broadcast(room.code, game)
    return game


@router.post("/{code}/tek-kart/restart", response_model=TekKartGameResponse)
async def restart_tek_kart_table(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> TekKartGameResponse:
    room = await get_room(session, code)
    game = await restart_tek_kart_game(session, room, current_user)
    await _broadcast(room.code, game)
    return game
