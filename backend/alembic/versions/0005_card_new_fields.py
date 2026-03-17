"""Add new fields to cards and create card_blocks table

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cards", sa.Column("balance", sa.NUMERIC(12, 2), nullable=True))
    op.add_column("cards", sa.Column("monthly_turnover", sa.NUMERIC(12, 2), nullable=True))
    op.add_column("cards", sa.Column("responsible_user", sa.VARCHAR(200), nullable=True))
    op.add_column("cards", sa.Column("folder_link", sa.VARCHAR(500), nullable=True))
    op.add_column("cards", sa.Column("comment", sa.TEXT(), nullable=True))

    op.create_table(
        "card_blocks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("card_id", sa.UUID(), nullable=False),
        sa.Column("blocked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("unblocked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("card_blocks")
    op.drop_column("cards", "comment")
    op.drop_column("cards", "folder_link")
    op.drop_column("cards", "responsible_user")
    op.drop_column("cards", "monthly_turnover")
    op.drop_column("cards", "balance")
