"""expand v2_ingredients form enum and add llm_confidence

Revision ID: 07f0d3c8039d
Revises: 55cdac51ef9f
Create Date: 2026-04-18 21:53:46.741893

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07f0d3c8039d'
down_revision: Union[str, None] = '55cdac51ef9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('v2_ingredients', sa.Column('llm_confidence', sa.Float(), nullable=True))

    # Expand form CHECK constraint to include LLM-classified values
    op.drop_constraint('check_v2_ingredients_form', 'v2_ingredients', type_='check')
    op.create_check_constraint(
        'check_v2_ingredients_form',
        'v2_ingredients',
        "form IN ('raw', 'cooked', 'dry_ingredient', 'fresh', 'prepared', 'not_applicable', 'unspecified')",
    )


def downgrade() -> None:
    op.drop_constraint('check_v2_ingredients_form', 'v2_ingredients', type_='check')
    op.create_check_constraint(
        'check_v2_ingredients_form',
        'v2_ingredients',
        "form IN ('raw', 'cooked', 'unspecified')",
    )
    op.drop_column('v2_ingredients', 'llm_confidence')
