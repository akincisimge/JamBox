from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.realtime.rooms import room_connections
from app.schemas.pisti import PistiGameResponse, PistiMoveCreate
from app.schemas.room import MessageResponse
from app.services.pisti import (
    create_pisti_game,
    get_pisti_game,
    join_pisti_game,
    make_pisti_move,
    restart_pisti_game,
)
from app.services.rooms import get_room

router = APIRouter(prefix="/rooms")


@router.post(
    "/{code}/pisti",
    response_model=PistiGameResponse,
    status_code=status.HTTP_201_CREATED,
)
async def open_pisti_table(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> PistiGameResponse:
    room = await get_room(session, code)
    game, invite = await create_pisti_game(session, room, current_user)
    invite_response = MessageResponse.model_validate(invite)
    await room_connections.broadcast(
        room.code,
        {"type": "message_created", "message": invite_response.model_dump(mode="json")},
    )
    await room_connections.broadcast(room.code, {"type": "pisti_updated"})
    return game


@router.get("/{code}/pisti", response_model=PistiGameResponse)
async def read_pisti_table(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> PistiGameResponse:
    room = await get_room(session, code)
    return await get_pisti_game(session, room, current_user)


@router.post("/{code}/pisti/join", response_model=PistiGameResponse)
async def accept_pisti_invite(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> PistiGameResponse:
    room = await get_room(session, code)
    game = await join_pisti_game(session, room, current_user)
    await room_connections.broadcast(room.code, {"type": "pisti_updated"})
    return game


@router.post("/{code}/pisti/cards", response_model=PistiGameResponse)
async def play_pisti_card(
    code: str,
    payload: PistiMoveCreate,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> PistiGameResponse:
    room = await get_room(session, code)
    game = await make_pisti_move(session, room, current_user, payload.card_id)
    await room_connections.broadcast(room.code, {"type": "pisti_updated"})
    return game


@router.post("/{code}/pisti/restart", response_model=PistiGameResponse)
async def restart_pisti_table(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> PistiGameResponse:
    room = await get_room(session, code)
    game = await restart_pisti_game(session, room, current_user)
    await room_connections.broadcast(room.code, {"type": "pisti_updated"})
    return game
