"""Add persistent room messages.

Revision ID: 20260729_0004
Revises: 20260729_0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260729_0004"
down_revision: str | None = "20260729_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "room_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("text", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_room_messages_room_id", "room_messages", ["room_id"])
    op.create_index("ix_room_messages_user_id", "room_messages", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_room_messages_user_id", table_name="room_messages")
    op.drop_index("ix_room_messages_room_id", table_name="room_messages")
    op.drop_table("room_messages")
