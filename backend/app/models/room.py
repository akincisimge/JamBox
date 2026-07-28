from __future__ import annotations

import uuid
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

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    members: Mapped[list[RoomMember]] = relationship(
        back_populates="room",
        cascade="all, delete-orphan",
    )
    playback: Mapped[RoomPlayback | None] = relationship(
        back_populates="room",
        cascade="all, delete-orphan",
        uselist=False,
    )


class RoomMember(TimestampMixin, Base):
    __tablename__ = "room_members"

    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    is_owner: Mapped[bool] = mapped_column(Boolean, default=False)
    can_control_music: Mapped[bool] = mapped_column(Boolean, default=False)

    room: Mapped[Room] = relationship(back_populates="members")
    user: Mapped[User] = relationship()


class RoomPlayback(Base):
    __tablename__ = "room_playback"

    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"),
        primary_key=True,
    )
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
