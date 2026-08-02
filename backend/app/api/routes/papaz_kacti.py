from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.realtime.rooms import room_connections
from app.schemas.papaz_kacti import PapazKactiDrawRequest, PapazKactiGameResponse
from app.schemas.room import MessageResponse
from app.services.papaz_kacti import (
    create_papaz_kacti_game,
    draw_papaz_kacti_card,
    get_papaz_kacti_game,
    join_papaz_kacti_game,
    restart_papaz_kacti_game,
    start_papaz_kacti_game,
)
from app.services.rooms import get_room

router = APIRouter(prefix="/rooms")


@router.post(
    "/{code}/papaz-kacti",
    response_model=PapazKactiGameResponse,
    status_code=status.HTTP_201_CREATED,
)
async def open_papaz_kacti_table(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> PapazKactiGameResponse:
    room = await get_room(session, code)
    game, invite = await create_papaz_kacti_game(session, room, current_user)
    invite_response = MessageResponse.model_validate(invite)
    await room_connections.broadcast(
        room.code,
        {"type": "message_created", "message": invite_response.model_dump(mode="json")},
    )
    await room_connections.broadcast(room.code, {"type": "papaz_kacti_updated"})
    return game


@router.get("/{code}/papaz-kacti", response_model=PapazKactiGameResponse)
async def read_papaz_kacti_table(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> PapazKactiGameResponse:
    room = await get_room(session, code)
    return await get_papaz_kacti_game(session, room, current_user)


@router.post("/{code}/papaz-kacti/join", response_model=PapazKactiGameResponse)
async def accept_papaz_kacti_invite(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> PapazKactiGameResponse:
    room = await get_room(session, code)
    game = await join_papaz_kacti_game(session, room, current_user)
    await room_connections.broadcast(room.code, {"type": "papaz_kacti_updated"})
    return game


@router.post("/{code}/papaz-kacti/start", response_model=PapazKactiGameResponse)
async def start_papaz_kacti_table(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> PapazKactiGameResponse:
    room = await get_room(session, code)
    game = await start_papaz_kacti_game(session, room, current_user)
    await room_connections.broadcast(room.code, {"type": "papaz_kacti_updated"})
    return game


@router.post("/{code}/papaz-kacti/draw", response_model=PapazKactiGameResponse)
async def draw_papaz_kacti_card_route(
    code: str,
    payload: PapazKactiDrawRequest,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> PapazKactiGameResponse:
    room = await get_room(session, code)
    game = await draw_papaz_kacti_card(session, room, current_user, payload.card_index)
    await room_connections.broadcast(room.code, {"type": "papaz_kacti_updated"})
    return game


@router.post("/{code}/papaz-kacti/restart", response_model=PapazKactiGameResponse)
async def restart_papaz_kacti_table(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> PapazKactiGameResponse:
    room = await get_room(session, code)
    game = await restart_papaz_kacti_game(session, room, current_user)
    await room_connections.broadcast(room.code, {"type": "papaz_kacti_updated"})
    return game
