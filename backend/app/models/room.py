from __future__ import annotations

import uuid

import chess
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Room(TimestampMixin, Base):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    members: Mapped[list[RoomMember]] = relationship(back_populates="room", cascade="all, delete-orphan")
    playback: Mapped[RoomPlayback | None] = relationship(back_populates="room", cascade="all, delete-orphan", uselist=False)
    messages: Mapped[list[RoomMessage]] = relationship(back_populates="room", cascade="all, delete-orphan", order_by="RoomMessage.created_at")
    chess_game: Mapped[ChessGame | None] = relationship(back_populates="room", cascade="all, delete-orphan", uselist=False)


class RoomMember(TimestampMixin, Base):
    __tablename__ = "room_members"

    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    is_owner: Mapped[bool] = mapped_column(Boolean, default=False)
    can_control_music: Mapped[bool] = mapped_column(Boolean, default=False)

    room: Mapped[Room] = relationship(back_populates="members")
    user: Mapped[User] = relationship()


class RoomPlayback(Base):
    __tablename__ = "room_playback"

    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True)
    spotify_uri: Mapped[str] = mapped_column(String(255))
    spotify_track_id: Mapped[str] = mapped_column(String(128))
    queue_uris: Mapped[list[str]] = mapped_column(JSON, default=list)
    title: Mapped[str] = mapped_column(String(255))
    artist: Mapped[str] = mapped_column(String(255))
    album_image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer)
    position_ms: Mapped[int] = mapped_column(Integer, default=0)
    is_playing: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    room: Mapped[Room] = relationship(back_populates="playback")


class RoomMessage(TimestampMixin, Base):
    __tablename__ = "room_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(String(500))
    reactions: Mapped[dict[str, list[str]]] = mapped_column(JSON, default=dict)
    message_type: Mapped[str] = mapped_column(String(32), default="text")
    payload: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)

    room: Mapped[Room] = relationship(back_populates="messages")
    user: Mapped[User] = relationship()


class ChessGame(TimestampMixin, Base):
    __tablename__ = "chess_games"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), unique=True, index=True)
    creator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    white_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    black_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="waiting")
    fen: Mapped[str] = mapped_column(String(128), default="start")
    turn: Mapped[str] = mapped_column(String(8), default="white")
    move_history: Mapped[list[str]] = mapped_column(JSON, default=list)
    winner_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    result: Mapped[str | None] = mapped_column(String(32), nullable=True)
    draw_offer_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    @property
    def legal_moves(self) -> list[str]:
        if self.status != "active":
            return []
        return [move.uci() for move in chess.Board(self.fen).legal_moves]

    @property
    def move_labels(self) -> list[str]:
        board = chess.Board()
        labels: list[str] = []
        for uci in self.move_history or []:
            move = chess.Move.from_uci(uci)
            labels.append(board.san(move))
            board.push(move)
        return labels

    room: Mapped[Room] = relationship(back_populates="chess_game")
    creator: Mapped[User] = relationship(foreign_keys=[creator_id])
    white_user: Mapped[User] = relationship(foreign_keys=[white_user_id])
    black_user: Mapped[User | None] = relationship(foreign_keys=[black_user_id])
