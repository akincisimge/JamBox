"""Add chess draw offers.

Revision ID: 20260729_0009
Revises: 20260729_0008
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260729_0009"
down_revision: str | None = "20260729_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "chess_games", sa.Column("draw_offer_user_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        "fk_chess_games_draw_offer_user_id_users",
        "chess_games",
        "users",
        ["draw_offer_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_chess_games_draw_offer_user_id_users", "chess_games", type_="foreignkey")
    op.drop_column("chess_games", "draw_offer_user_id")
