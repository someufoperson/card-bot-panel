"""Add pickup_date to cards

Revision ID: 0008
Revises: 0007
Create Date: 2026-03-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cards", sa.Column("pickup_date", sa.DATE(), nullable=True))


def downgrade() -> None:
    op.drop_column("cards", "pickup_date")
