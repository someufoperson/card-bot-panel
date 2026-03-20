"""Add unique constraint on card_number

Revision ID: 0013
Revises: 0012
Create Date: 2026-03-19

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Delete duplicate cards keeping the one with the highest id (most recent)
    op.execute("""
        DELETE FROM cards
        WHERE id NOT IN (
            SELECT MAX(id)
            FROM cards
            GROUP BY card_number
        )
    """)
    op.create_unique_constraint("uq_cards_card_number", "cards", ["card_number"])


def downgrade() -> None:
    op.drop_constraint("uq_cards_card_number", "cards", type_="unique")
