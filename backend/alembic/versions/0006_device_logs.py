"""Create device_logs table

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "device_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("serial", sa.VARCHAR(100), nullable=False),
        sa.Column("event_type", sa.VARCHAR(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_device_logs_serial", "device_logs", ["serial"])


def downgrade() -> None:
    op.drop_index("ix_device_logs_serial", "device_logs")
    op.drop_table("device_logs")
