import secrets
import string
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.room import Room, RoomMember, RoomMessage, RoomPlayback
from app.models.user import User
from app.schemas.room import PlaybackUpdate
from app.services.errors import ConflictError, ForbiddenError, NotFoundError

ROOM_CODE_ALPHABET = string.ascii_uppercase + string.digits
ROOM_CODE_LENGTH = 6


def generate_room_code() -> str:
    suffix = "".join(secrets.choice(ROOM_CODE_ALPHABET) for _ in range(ROOM_CODE_LENGTH))
    return f"JAM-{suffix}"


async def _unique_room_code(session: AsyncSession) -> str:
    for _ in range(10):
        code = generate_room_code()
        existing = await session.scalar(select(Room.id).where(Room.code == code))
        if existing is None:
            return code
    raise ConflictError("Benzersiz oda kodu üretilemedi. Lütfen tekrar deneyin.")


async def get_user(session: AsyncSession, user_id: uuid.UUID) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise NotFoundError("Kullanıcı bulunamadı.")
    return user


async def get_room(session: AsyncSession, code: str) -> Room:
    room = await session.scalar(
        select(Room)
        .where(Room.code == code.upper(), Room.is_active.is_(True))
        .options(
            selectinload(Room.members).selectinload(RoomMember.user),
            selectinload(Room.playback),
            selectinload(Room.messages).selectinload(RoomMessage.user),
        )
        .execution_options(populate_existing=True)
    )
    if room is None:
        raise NotFoundError("Aktif oda bulunamadı.")
    return room


async def create_room(session: AsyncSession, owner: User, name: str) -> Room:
    room = Room(
        code=await _unique_room_code(session),
        name=name.strip(),
        owner_id=owner.id,
    )
    room.members.append(
        RoomMember(
            user_id=owner.id,
            is_owner=True,
            can_control_music=True,
        )
    )
    session.add(room)
    await session.commit()
    return await get_room(session, room.code)


async def join_room(session: AsyncSession, room: Room, user: User) -> Room:
    membership = await session.get(
        RoomMember,
        {"room_id": room.id, "user_id": user.id},
    )
    if membership is None:
        session.add(RoomMember(room_id=room.id, user_id=user.id))
        await session.commit()
    return await get_room(session, room.code)


async def leave_room(session: AsyncSession, room: Room, user: User) -> None:
    membership = await session.get(
        RoomMember,
        {"room_id": room.id, "user_id": user.id},
    )
    if membership is None:
        raise NotFoundError("Kullanıcı bu odada değil.")
    if membership.is_owner:
        raise ConflictError("Oda sahibi odadan ayrılamaz; odayı kapatmalıdır.")

    await session.delete(membership)
    await session.commit()


async def update_music_permission(
    session: AsyncSession,
    room: Room,
    actor: User,
    member_user_id: uuid.UUID,
    can_control_music: bool,
) -> Room:
    if room.owner_id != actor.id:
        raise ForbiddenError("Müzik yetkisini yalnızca oda sahibi değiştirebilir.")
    if member_user_id == room.owner_id and not can_control_music:
        raise ConflictError("Oda sahibinin müzik kontrol yetkisi kaldırılamaz.")

    membership = await session.get(
        RoomMember,
        {"room_id": room.id, "user_id": member_user_id},
    )
    if membership is None:
        raise NotFoundError("Kullanıcı bu odada değil.")

    membership.can_control_music = can_control_music
    await session.commit()
    return await get_room(session, room.code)


async def update_playback(
    session: AsyncSession,
    room: Room,
    actor: User,
    payload: PlaybackUpdate,
) -> Room:
    membership = await session.get(
        RoomMember,
        {"room_id": room.id, "user_id": actor.id},
    )
    if membership is None:
        raise NotFoundError("Kullanıcı bu odada değil.")
    if not membership.can_control_music:
        raise ForbiddenError("Bu kullanıcının müzik kontrol yetkisi yok.")

    position_ms = min(payload.position_ms, payload.duration_ms)
    playback = await session.get(RoomPlayback, room.id)
    if playback is None:
        playback = RoomPlayback(
            room_id=room.id,
            spotify_uri=payload.spotify_uri,
            spotify_track_id=payload.spotify_track_id,
            queue_uris=payload.queue_uris,
            title=payload.title,
            artist=payload.artist,
            album_image_url=payload.album_image_url,
            duration_ms=payload.duration_ms,
            position_ms=position_ms,
            is_playing=payload.is_playing,
            version=1,
            changed_at=datetime.now(UTC),
        )
        session.add(playback)
    else:
        playback.spotify_uri = payload.spotify_uri
        playback.spotify_track_id = payload.spotify_track_id
        playback.queue_uris = payload.queue_uris
        playback.title = payload.title
        playback.artist = payload.artist
        playback.album_image_url = payload.album_image_url
        playback.duration_ms = payload.duration_ms
        playback.position_ms = position_ms
        playback.is_playing = payload.is_playing
        playback.version += 1
        playback.changed_at = datetime.now(UTC)

    await session.commit()
    return await get_room(session, room.code)


async def create_message(
    session: AsyncSession,
    room: Room,
    actor: User,
    text: str,
) -> RoomMessage:
    membership = await session.get(
        RoomMember,
        {"room_id": room.id, "user_id": actor.id},
    )
    if membership is None:
        raise NotFoundError("Kullanıcı bu odada değil.")

    message = RoomMessage(room_id=room.id, user_id=actor.id, text=text.strip())
    message.user = actor
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message


async def toggle_message_reaction(
    session: AsyncSession,
    room: Room,
    actor: User,
    message_id: uuid.UUID,
    emoji: str,
) -> RoomMessage:
    membership = await session.get(
        RoomMember,
        {"room_id": room.id, "user_id": actor.id},
    )
    if membership is None:
        raise NotFoundError("Kullanıcı bu odada değil.")

    message = await session.scalar(
        select(RoomMessage)
        .where(RoomMessage.id == message_id, RoomMessage.room_id == room.id)
        .options(selectinload(RoomMessage.user))
    )
    if message is None:
        raise NotFoundError("Mesaj bulunamadı.")

    reactions = {key: list(value) for key, value in (message.reactions or {}).items()}
    user_id = str(actor.id)
    users = reactions.get(emoji, [])
    if user_id in users:
        users.remove(user_id)
    else:
        users.append(user_id)

    if users:
        reactions[emoji] = users
    else:
        reactions.pop(emoji, None)

    message.reactions = reactions
    await session.commit()
    await session.refresh(message)
    return message


async def close_room(session: AsyncSession, room: Room, actor: User) -> None:
    if room.owner_id != actor.id:
        raise ForbiddenError("Odayı yalnızca oda sahibi kapatabilir.")

    room.is_active = False
    await session.commit()
