from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.realtime.rooms import room_connections
from app.schemas.kelime_kapismasi import (
    KelimeKapismasiGameResponse,
    KelimeKapismasiSubmitRequest,
)
from app.schemas.room import MessageResponse
from app.services.kelime_kapismasi import (
    create_kelime_kapismasi_game,
    get_kelime_kapismasi_game,
    join_kelime_kapismasi_game,
    restart_kelime_kapismasi_game,
    start_kelime_kapismasi_game,
    submit_kelime_kapismasi_word,
)
from app.services.rooms import get_room

router = APIRouter(prefix="/rooms")


async def _broadcast(code: str, game: KelimeKapismasiGameResponse) -> None:
    await room_connections.broadcast(
        code,
        {
            "type": "kelime_kapismasi_updated",
            "room_code": code,
            "game_id": str(game.id),
            "version": game.version,
        },
    )


@router.post(
    "/{code}/kelime-kapismasi",
    response_model=KelimeKapismasiGameResponse,
    status_code=status.HTTP_201_CREATED,
)
async def open_kelime_kapismasi(
    code: str,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> KelimeKapismasiGameResponse:
    room = await get_room(session, code)
    game, invite = await create_kelime_kapismasi_game(session, room, current_user)
    invite_response = MessageResponse.model_validate(invite)
    await room_connections.broadcast(
        room.code,
        {
            "type": "message_created",
            "message": invite_response.model_dump(mode="json"),
        },
    )
    await _broadcast(room.code, game)
    return game


@router.get(
    "/{code}/kelime-kapismasi",
    response_model=KelimeKapismasiGameResponse,
)
async def read_kelime_kapismasi(
    code: str,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> KelimeKapismasiGameResponse:
    room = await get_room(session, code)
    return await get_kelime_kapismasi_game(session, room, current_user)


@router.post(
    "/{code}/kelime-kapismasi/join",
    response_model=KelimeKapismasiGameResponse,
)
async def join_kelime_kapismasi(
    code: str,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> KelimeKapismasiGameResponse:
    room = await get_room(session, code)
    game = await join_kelime_kapismasi_game(session, room, current_user)
    await _broadcast(room.code, game)
    return game


@router.post(
    "/{code}/kelime-kapismasi/start",
    response_model=KelimeKapismasiGameResponse,
)
async def start_kelime_kapismasi(
    code: str,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> KelimeKapismasiGameResponse:
    room = await get_room(session, code)
    game = await start_kelime_kapismasi_game(session, room, current_user)
    await _broadcast(room.code, game)
    return game


@router.post(
    "/{code}/kelime-kapismasi/words",
    response_model=KelimeKapismasiGameResponse,
)
async def submit_kelime_kapismasi_word_route(
    code: str,
    payload: KelimeKapismasiSubmitRequest,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> KelimeKapismasiGameResponse:
    room = await get_room(session, code)
    game = await submit_kelime_kapismasi_word(
        session,
        room,
        current_user,
        payload.word,
    )
    await _broadcast(room.code, game)
    return game


@router.post(
    "/{code}/kelime-kapismasi/restart",
    response_model=KelimeKapismasiGameResponse,
)
async def restart_kelime_kapismasi(
    code: str,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> KelimeKapismasiGameResponse:
    room = await get_room(session, code)
    game = await restart_kelime_kapismasi_game(session, room, current_user)
    await _broadcast(room.code, game)
    return game
