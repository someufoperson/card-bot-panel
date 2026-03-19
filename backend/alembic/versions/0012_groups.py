"""Create groups table

Revision ID: 0012
Revises: 0011
Create Date: 2026-03-19

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.VARCHAR(200), nullable=False),
        sa.Column("type", sa.VARCHAR(20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_groups_type", "groups", ["type"])


def downgrade() -> None:
    op.drop_index("ix_groups_type", table_name="groups")
    op.drop_table("groups")
