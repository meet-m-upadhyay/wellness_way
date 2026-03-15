"""add_admin_note_to_registration_requests

Revision ID: e0d8388f688a
Revises: 18839adc0a64
Create Date: 2026-03-15 16:58:32.686560

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e0d8388f688a'
down_revision: Union[str, None] = '18839adc0a64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add admin_note column to registration_requests
    op.add_column('registration_requests', sa.Column('admin_note', sa.String(length=500), nullable=True))
    # Add cuisine and reuse_ingredients to diet_preferences (were added manually before, now tracked by alembic)
    op.add_column('diet_preferences', sa.Column('cuisine', sa.String(length=50), nullable=False, server_default='indian'))
    op.add_column('diet_preferences', sa.Column('reuse_ingredients', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('registration_requests', 'admin_note')
    op.drop_column('diet_preferences', 'reuse_ingredients')
    op.drop_column('diet_preferences', 'cuisine')
