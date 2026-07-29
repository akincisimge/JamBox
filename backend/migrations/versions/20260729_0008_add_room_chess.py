"""Add persistent room chess games and structured messages.

Revision ID: 20260729_0008
Revises: 20260729_0007
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260729_0008"
down_revision: str | None = "20260729_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "room_messages",
        sa.Column("message_type", sa.String(length=32), nullable=False, server_default="text"),
    )
    op.add_column(
        "room_messages",
        sa.Column(
            "payload",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
    )
    op.create_table(
        "chess_games",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("white_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("black_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="waiting"),
        sa.Column("fen", sa.String(length=128), nullable=False),
        sa.Column("turn", sa.String(length=8), nullable=False, server_default="white"),
        sa.Column("move_history", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("winner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["white_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["black_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["winner_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("room_id"),
    )
    op.create_index(op.f("ix_chess_games_room_id"), "chess_games", ["room_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_chess_games_room_id"), table_name="chess_games")
    op.drop_table("chess_games")
    op.drop_column("room_messages", "payload")
    op.drop_column("room_messages", "message_type")
