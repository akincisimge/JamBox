import uuid

from fastapi import APIRouter, Response, WebSocket, WebSocketDisconnect, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.models.room import RoomMember
from app.realtime.rooms import room_connections
from app.schemas.room import (
    MessageCreate,
    MessageResponse,
    MusicPermissionUpdate,
    PlaybackUpdate,
    RoomCreate,
    RoomResponse,
)
from app.services.errors import NotFoundError
from app.services.rooms import (
    close_room,
    create_message,
    create_room,
    get_room,
    get_user,
    join_room,
    leave_room,
    update_music_permission,
    update_playback,
)

router = APIRouter(prefix="/rooms")


@router.websocket("/{code}/ws")
async def room_updates(
    websocket: WebSocket,
    code: str,
    user_id: uuid.UUID,
    session: DatabaseSession,
) -> None:
    try:
        room = await get_room(session, code)
        await get_user(session, user_id)
    except NotFoundError:
        await websocket.close(code=4404, reason="Oda veya kullanıcı bulunamadı.")
        return

    membership = await session.get(
        RoomMember,
        {"room_id": room.id, "user_id": user_id},
    )
    if membership is None:
        await websocket.close(code=4403, reason="Kullanıcı bu odada değil.")
        return

    await room_connections.connect(room.code, websocket)
    await websocket.send_json({"type": "connected"})

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        room_connections.disconnect(room.code, websocket)


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
    await room_connections.broadcast(room.code, {"type": "room_updated"})
    return RoomResponse.model_validate(updated_room)


@router.post("/{code}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_existing_room(
    code: str,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> Response:
    room = await get_room(session, code)
    await leave_room(session, room, current_user)
    await room_connections.broadcast(room.code, {"type": "room_updated"})
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
    await room_connections.broadcast(room.code, {"type": "room_updated"})
    return RoomResponse.model_validate(updated_room)


@router.put("/{code}/playback", response_model=RoomResponse)
async def change_playback(
    code: str,
    payload: PlaybackUpdate,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> RoomResponse:
    room = await get_room(session, code)
    updated_room = await update_playback(session, room, current_user, payload)
    await room_connections.broadcast(room.code, {"type": "playback_updated"})
    return RoomResponse.model_validate(updated_room)


@router.post(
    "/{code}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_room_message(
    code: str,
    payload: MessageCreate,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> MessageResponse:
    room = await get_room(session, code)
    message = await create_message(session, room, current_user, payload.text)
    response = MessageResponse.model_validate(message)
    await room_connections.broadcast(
        room.code,
        {"type": "message_created", "message": response.model_dump(mode="json")},
    )
    return response


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    code: str,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> Response:
    room = await get_room(session, code)
    await close_room(session, room, current_user)
    await room_connections.broadcast(room.code, {"type": "room_closed"})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
