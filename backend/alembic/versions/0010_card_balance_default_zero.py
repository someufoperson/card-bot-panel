"""Set default 0 for balance and monthly_turnover

Revision ID: 0010
Revises: 0009
Create Date: 2026-03-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE cards SET balance = 0 WHERE balance IS NULL")
    op.execute("UPDATE cards SET monthly_turnover = 0 WHERE monthly_turnover IS NULL")
    op.alter_column("cards", "balance",
                    existing_type=sa.NUMERIC(12, 2),
                    nullable=False,
                    server_default="0")
    op.alter_column("cards", "monthly_turnover",
                    existing_type=sa.NUMERIC(12, 2),
                    nullable=False,
                    server_default="0")


def downgrade() -> None:
    op.alter_column("cards", "balance",
                    existing_type=sa.NUMERIC(12, 2),
                    nullable=True,
                    server_default=None)
    op.alter_column("cards", "monthly_turnover",
                    existing_type=sa.NUMERIC(12, 2),
                    nullable=True,
                    server_default=None)
