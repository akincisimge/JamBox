from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.room import Room
    from app.models.user import User


class KelimeKapismasiGame(TimestampMixin, Base):
    __tablename__ = "kelime_kapismasi_games"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"), unique=True, index=True
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    player_one_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    player_two_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="waiting")
    state: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    winner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1)

    room: Mapped[Room] = relationship()
    creator: Mapped[User] = relationship(foreign_keys=[creator_id])
    player_one_user: Mapped[User] = relationship(foreign_keys=[player_one_user_id])
    player_two_user: Mapped[User | None] = relationship(foreign_keys=[player_two_user_id])
    winner_user: Mapped[User | None] = relationship(foreign_keys=[winner_user_id])
