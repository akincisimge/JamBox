import secrets
import string
import uuid
from datetime import UTC, datetime

import chess
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.room import ChessGame, Room, RoomMember, RoomMessage, RoomPlayback
from app.models.user import User
from app.schemas.room import ChessMoveCreate, PlaybackUpdate
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
            selectinload(Room.chess_game).selectinload(ChessGame.white_user),
            selectinload(Room.chess_game).selectinload(ChessGame.black_user),
        )
        .execution_options(populate_existing=True)
    )
    if room is None:
        raise NotFoundError("Aktif oda bulunamadı.")
    return room


async def _require_member(session: AsyncSession, room: Room, user: User) -> RoomMember:
    membership = await session.get(RoomMember, {"room_id": room.id, "user_id": user.id})
    if membership is None:
        raise NotFoundError("Kullanıcı bu odada değil.")
    return membership


async def create_room(session: AsyncSession, owner: User, name: str) -> Room:
    room = Room(code=await _unique_room_code(session), name=name.strip(), owner_id=owner.id)
    room.members.append(RoomMember(user_id=owner.id, is_owner=True, can_control_music=True))
    session.add(room)
    await session.commit()
    return await get_room(session, room.code)


async def join_room(session: AsyncSession, room: Room, user: User) -> Room:
    membership = await session.get(RoomMember, {"room_id": room.id, "user_id": user.id})
    if membership is None:
        session.add(RoomMember(room_id=room.id, user_id=user.id))
        await session.commit()
    return await get_room(session, room.code)


async def leave_room(session: AsyncSession, room: Room, user: User) -> None:
    membership = await _require_member(session, room, user)
    if membership.is_owner:
        raise ConflictError("Oda sahibi odadan ayrılamaz; odayı kapatmalıdır.")
    await session.delete(membership)
    await session.commit()


async def update_music_permission(session: AsyncSession, room: Room, actor: User, member_user_id: uuid.UUID, can_control_music: bool) -> Room:
    if room.owner_id != actor.id:
        raise ForbiddenError("Müzik yetkisini yalnızca oda sahibi değiştirebilir.")
    if member_user_id == room.owner_id and not can_control_music:
        raise ConflictError("Oda sahibinin müzik kontrol yetkisi kaldırılamaz.")
    membership = await session.get(RoomMember, {"room_id": room.id, "user_id": member_user_id})
    if membership is None:
        raise NotFoundError("Kullanıcı bu odada değil.")
    membership.can_control_music = can_control_music
    await session.commit()
    return await get_room(session, room.code)


async def update_playback(session: AsyncSession, room: Room, actor: User, payload: PlaybackUpdate) -> Room:
    membership = await _require_member(session, room, actor)
    if not membership.can_control_music:
        raise ForbiddenError("Bu kullanıcının müzik kontrol yetkisi yok.")
    position_ms = min(payload.position_ms, payload.duration_ms)
    playback = await session.get(RoomPlayback, room.id)
    values = dict(
        spotify_uri=payload.spotify_uri, spotify_track_id=payload.spotify_track_id,
        queue_uris=payload.queue_uris, title=payload.title, artist=payload.artist,
        album_image_url=payload.album_image_url, duration_ms=payload.duration_ms,
        position_ms=position_ms, is_playing=payload.is_playing,
    )
    if playback is None:
        playback = RoomPlayback(room_id=room.id, version=1, changed_at=datetime.now(UTC), **values)
        session.add(playback)
    else:
        for key, value in values.items():
            setattr(playback, key, value)
        playback.version += 1
        playback.changed_at = datetime.now(UTC)
    await session.commit()
    return await get_room(session, room.code)


async def create_message(session: AsyncSession, room: Room, actor: User, text: str) -> RoomMessage:
    await _require_member(session, room, actor)
    message = RoomMessage(room_id=room.id, user_id=actor.id, text=text.strip())
    message.user = actor
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message


async def toggle_message_reaction(session: AsyncSession, room: Room, actor: User, message_id: uuid.UUID, emoji: str) -> RoomMessage:
    await _require_member(session, room, actor)
    message = await session.scalar(select(RoomMessage).where(RoomMessage.id == message_id, RoomMessage.room_id == room.id).options(selectinload(RoomMessage.user)))
    if message is None:
        raise NotFoundError("Mesaj bulunamadı.")
    reactions = {key: list(value) for key, value in (message.reactions or {}).items()}
    user_id = str(actor.id)
    users = reactions.get(emoji, [])
    users.remove(user_id) if user_id in users else users.append(user_id)
    if users:
        reactions[emoji] = users
    else:
        reactions.pop(emoji, None)
    message.reactions = reactions
    await session.commit()
    await session.refresh(message)
    return message


async def create_chess_game(session: AsyncSession, room: Room, actor: User) -> tuple[Room, RoomMessage]:
    await _require_member(session, room, actor)
    existing = await session.scalar(select(ChessGame).where(ChessGame.room_id == room.id))
    if existing is not None and existing.status in {"waiting", "active"}:
        raise ConflictError("Bu odada zaten açık bir satranç masası var.")
    if existing is not None:
        await session.delete(existing)
        await session.flush()
    game = ChessGame(
        room_id=room.id, creator_id=actor.id, white_user_id=actor.id,
        status="waiting", fen=chess.STARTING_FEN, turn="white", move_history=[],
    )
    session.add(game)
    await session.flush()
    message = RoomMessage(
        room_id=room.id, user_id=actor.id,
        text=f"♟️ {actor.display_name} satranç masası açtı.",
        message_type="chess_invite", payload={"game_id": str(game.id)},
    )
    message.user = actor
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return await get_room(session, room.code), message


async def add_chess_test_opponent(session: AsyncSession, room: Room, actor: User) -> Room:
    await _require_member(session, room, actor)
    game = await session.scalar(select(ChessGame).where(ChessGame.room_id == room.id))
    if game is None or game.status != "waiting" or game.creator_id != actor.id:
        raise ConflictError("Test rakibi yalnızca bekleyen kendi masanıza ekleyebilirsiniz.")
    spotify_id = f"jambox-test-opponent-{room.id}"
    test_user = await session.scalar(select(User).where(User.spotify_id == spotify_id))
    if test_user is None:
        test_user = User(
            spotify_id=spotify_id,
            display_name="JamBot",
            email=None,
            avatar_url=None,
        )
        session.add(test_user)
        await session.flush()
    membership = await session.get(
        RoomMember,
        {"room_id": room.id, "user_id": test_user.id},
    )
    if membership is None:
        session.add(RoomMember(room_id=room.id, user_id=test_user.id))
    game.black_user_id = test_user.id
    game.status = "active"
    await session.commit()
    return await get_room(session, room.code)


async def join_chess_game(session: AsyncSession, room: Room, actor: User) -> Room:
    await _require_member(session, room, actor)
    game = await session.scalar(select(ChessGame).where(ChessGame.room_id == room.id))
    if game is None or game.status != "waiting":
        raise ConflictError("Katılabileceğiniz açık bir satranç daveti yok.")
    if game.white_user_id == actor.id:
        raise ConflictError("Kendi satranç davetinize katılamazsınız.")
    game.black_user_id = actor.id
    game.status = "active"
    await session.commit()
    return await get_room(session, room.code)


async def make_chess_move(session: AsyncSession, room: Room, actor: User, payload: ChessMoveCreate) -> Room:
    await _require_member(session, room, actor)
    game = await session.scalar(select(ChessGame).where(ChessGame.room_id == room.id))
    if game is None or game.status != "active":
        raise ConflictError("Aktif satranç oyunu bulunamadı.")
    actor_color = chess.WHITE if game.white_user_id == actor.id else chess.BLACK if game.black_user_id == actor.id else None
    if actor_color is None:
        raise ForbiddenError("Bu satranç masasındaki oyunculardan biri değilsiniz.")
    board = chess.Board(game.fen)
    if board.turn != actor_color:
        raise ConflictError("Hamle sırası sizde değil.")
    move = chess.Move.from_uci(f"{payload.from_square}{payload.to_square}{payload.promotion or ''}")
    if move not in board.legal_moves:
        raise ConflictError("Bu hamle geçerli değil.")
    board.push(move)
    history = [*(game.move_history or []), move.uci()]

    test_opponent = (
        await session.get(User, game.black_user_id)
        if game.black_user_id is not None
        else None
    )
    if (
        not board.is_game_over()
        and board.turn == chess.BLACK
        and test_opponent is not None
        and test_opponent.spotify_id.startswith("jambox-test-opponent-")
    ):
        bot_move = secrets.choice(list(board.legal_moves))
        board.push(bot_move)
        history.append(bot_move.uci())

    game.fen = board.fen()
    game.turn = "white" if board.turn == chess.WHITE else "black"
    game.move_history = history
    if board.is_game_over():
        game.status = "finished"
        game.result = board.result()
        if board.is_checkmate():
            game.winner_user_id = actor.id if board.turn == chess.BLACK else game.black_user_id
    await session.commit()
    return await get_room(session, room.code)


async def close_room(session: AsyncSession, room: Room, actor: User) -> None:
    if room.owner_id != actor.id:
        raise ForbiddenError("Odayı yalnızca oda sahibi kapatabilir.")
    room.is_active = False
    await session.commit()
