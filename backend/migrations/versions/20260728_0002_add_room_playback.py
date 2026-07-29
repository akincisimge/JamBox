"""Add synchronized room playback state.

Revision ID: 20260728_0002
Revises: 20260728_0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260728_0002"
down_revision: str | None = "20260728_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "room_playback",
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("spotify_uri", sa.String(length=255), nullable=False),
        sa.Column("spotify_track_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("artist", sa.String(length=255), nullable=False),
        sa.Column("album_image_url", sa.String(length=2048), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("position_ms", sa.Integer(), nullable=False),
        sa.Column("is_playing", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("room_id"),
    )


def downgrade() -> None:
    op.drop_table("room_playback")
