"""Add users table

Revision ID: 0014
Revises: 0013
Create Date: 2026-03-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.VARCHAR(100), nullable=False),
        sa.Column("password_hash", sa.TEXT, nullable=True),
        sa.Column("role", sa.VARCHAR(20), nullable=False, server_default="user"),
        sa.Column("must_set_password", sa.BOOLEAN, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )


def downgrade() -> None:
    op.drop_table("users")
