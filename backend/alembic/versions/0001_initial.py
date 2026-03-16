"""Initial: cards and settings tables

Revision ID: 0001
Revises:
Create Date: 2026-03-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cards",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("full_name", sa.VARCHAR(255), nullable=False),
        sa.Column("bank", sa.VARCHAR(100), nullable=True),
        sa.Column("card_number", sa.VARCHAR(20), nullable=False),
        sa.Column("card_last4", sa.VARCHAR(4), nullable=False),
        sa.Column("phone_number", sa.VARCHAR(20), nullable=True),
        sa.Column("purchase_date", sa.DATE(), nullable=True),
        sa.Column("group_name", sa.VARCHAR(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "settings",
        sa.Column("key", sa.VARCHAR(100), nullable=False),
        sa.Column("value", sa.TEXT(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("key"),
    )

    op.execute(
        sa.text("""
        INSERT INTO settings (key, value) VALUES
            ('inactivity_timeout', '10'),
            ('device_domain', 'http://localhost'),
            ('bot_token', ''),
            ('allowed_user_id', '')
        ON CONFLICT (key) DO NOTHING
        """)
    )


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_table("cards")
