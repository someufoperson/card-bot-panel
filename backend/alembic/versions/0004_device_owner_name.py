"""Replace card_id FK with owner_name on devices

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "devices",
        sa.Column("owner_name", sa.VARCHAR(200), nullable=True),
    )
    op.drop_constraint("devices_card_id_fkey", "devices", type_="foreignkey")
    op.drop_column("devices", "card_id")


def downgrade() -> None:
    op.add_column(
        "devices",
        sa.Column("card_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "devices_card_id_fkey", "devices", "cards", ["card_id"], ["id"],
        ondelete="SET NULL",
    )
    op.drop_column("devices", "owner_name")
