import uuid

from fastapi import APIRouter, Response, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.room import MusicPermissionUpdate, RoomCreate, RoomResponse
from app.services.rooms import (
    close_room,
    create_room,
    get_room,
    join_room,
    leave_room,
    update_music_permission,
)

router = APIRouter(prefix="/rooms")


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_new_room(
    payload: RoomCreate,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> RoomResponse:
    room = await create_room(session, current_user, payload.name)
    return RoomResponse.model_validate(room)


@router.get("/{code}", response_model=RoomResponse)
async def read_room(code: str, session: DatabaseSession) -> RoomResponse:
    room = await get_room(session, code)
    return RoomResponse.model_validate(room)


@router.post("/{code}/join", response_model=RoomResponse)
async def join_existing_room(
    code: str,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> RoomResponse:
    room = await get_room(session, code)
    updated_room = await join_room(session, room, current_user)
    return RoomResponse.model_validate(updated_room)


@router.post("/{code}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_existing_room(
    code: str,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> Response:
    room = await get_room(session, code)
    await leave_room(session, room, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{code}/members/{user_id}/music-permission", response_model=RoomResponse)
async def change_music_permission(
    code: str,
    user_id: uuid.UUID,
    payload: MusicPermissionUpdate,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> RoomResponse:
    room = await get_room(session, code)
    updated_room = await update_music_permission(
        session,
        room,
        current_user,
        user_id,
        payload.can_control_music,
    )
    return RoomResponse.model_validate(updated_room)


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    code: str,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> Response:
    room = await get_room(session, code)
    await close_room(session, room, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
