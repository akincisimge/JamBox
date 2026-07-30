from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.room import Room
    from app.models.user import User


class PistiGame(TimestampMixin, Base):
    __tablename__ = "pisti_games"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"), unique=True, index=True
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    player_one_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    player_two_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(16), default="waiting")
    state: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    scores: Mapped[dict[str, int]] = mapped_column(JSON, default=dict)
    winner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    room: Mapped[Room] = relationship()
    creator: Mapped[User] = relationship(foreign_keys=[creator_id])
    player_one_user: Mapped[User] = relationship(foreign_keys=[player_one_user_id])
    player_two_user: Mapped[User | None] = relationship(foreign_keys=[player_two_user_id])
