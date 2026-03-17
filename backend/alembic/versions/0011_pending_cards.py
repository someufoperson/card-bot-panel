"""Add pending_cards table

Revision ID: 0011
Revises: 0010
Create Date: 2026-03-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pending_cards",
        sa.Column("message_id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_pending_cards_user_id", "pending_cards", ["user_id"])
    op.create_index("ix_pending_cards_created_at", "pending_cards", ["created_at"])


def downgrade() -> None:
    op.drop_table("pending_cards")
