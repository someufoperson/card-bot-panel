"""Add devices table

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("serial", sa.VARCHAR(100), nullable=False),
        sa.Column("label", sa.VARCHAR(255), nullable=True),
        sa.Column(
            "card_id",
            sa.UUID(),
            sa.ForeignKey("cards.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.VARCHAR(10), nullable=False, server_default="offline"),
        sa.Column("session_status", sa.VARCHAR(10), nullable=False, server_default="inactive"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("serial"),
    )


def downgrade() -> None:
    op.drop_table("devices")
