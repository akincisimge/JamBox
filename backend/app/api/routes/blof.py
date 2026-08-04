from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.realtime.rooms import room_connections
from app.schemas.blof import BlofGameResponse, BlofPlayRequest
from app.schemas.room import MessageResponse
from app.services.blof import (
    accept_blof_play,
    call_blof,
    create_blof_game,
    get_blof_game,
    join_blof_game,
    play_blof_cards,
    restart_blof_game,
    start_blof_game,
)
from app.services.rooms import get_room

router = APIRouter(prefix="/rooms")


async def _broadcast(code: str, game: BlofGameResponse) -> None:
    await room_connections.broadcast(
        code,
        {
            "type": "blof_updated",
            "room_code": code,
            "game_id": str(game.id),
            "version": game.version,
        },
    )


@router.post(
    "/{code}/blof",
    response_model=BlofGameResponse,
    status_code=status.HTTP_201_CREATED,
)
async def open_blof_table(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> BlofGameResponse:
    room = await get_room(session, code)
    game, invite = await create_blof_game(session, room, current_user)
    invite_response = MessageResponse.model_validate(invite)
    await room_connections.broadcast(
        room.code,
        {"type": "message_created", "message": invite_response.model_dump(mode="json")},
    )
    await _broadcast(room.code, game)
    return game


@router.get("/{code}/blof", response_model=BlofGameResponse)
async def read_blof_table(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> BlofGameResponse:
    room = await get_room(session, code)
    return await get_blof_game(session, room, current_user)


@router.post("/{code}/blof/join", response_model=BlofGameResponse)
async def join_blof_table(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> BlofGameResponse:
    room = await get_room(session, code)
    game = await join_blof_game(session, room, current_user)
    await _broadcast(room.code, game)
    return game


@router.post("/{code}/blof/start", response_model=BlofGameResponse)
async def start_blof_table(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> BlofGameResponse:
    room = await get_room(session, code)
    game = await start_blof_game(session, room, current_user)
    await _broadcast(room.code, game)
    return game


@router.post("/{code}/blof/play", response_model=BlofGameResponse)
async def play_blof_cards_route(
    code: str,
    payload: BlofPlayRequest,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> BlofGameResponse:
    room = await get_room(session, code)
    game = await play_blof_cards(
        session, room, current_user, payload.card_ids, payload.declared_rank
    )
    await _broadcast(room.code, game)
    return game


@router.post("/{code}/blof/call", response_model=BlofGameResponse)
async def call_blof_route(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> BlofGameResponse:
    room = await get_room(session, code)
    game = await call_blof(session, room, current_user)
    await _broadcast(room.code, game)
    return game


@router.post("/{code}/blof/accept", response_model=BlofGameResponse)
async def accept_blof_route(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> BlofGameResponse:
    room = await get_room(session, code)
    game = await accept_blof_play(session, room, current_user)
    await _broadcast(room.code, game)
    return game


@router.post("/{code}/blof/restart", response_model=BlofGameResponse)
async def restart_blof_table(
    code: str, session: DatabaseSession, current_user: CurrentUser
) -> BlofGameResponse:
    room = await get_room(session, code)
    game = await restart_blof_game(session, room, current_user)
    await _broadcast(room.code, game)
    return game
