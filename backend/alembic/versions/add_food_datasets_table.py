"""Add food_datasets table

Revision ID: add_food_datasets_table
Revises: add_food_items_table
Create Date: 2026-02-23 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_food_datasets_table'
down_revision: Union[str, None] = 'add_food_items_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'food_datasets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('dataset_name', sa.String(length=50), nullable=False),
        sa.Column('dataset_version', sa.String(length=50), nullable=False),
        sa.Column('import_batch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dataset_name', 'dataset_version', name='uq_food_datasets_name_version'),
        sa.CheckConstraint('length(dataset_name) > 0', name='check_food_datasets_name'),
        sa.CheckConstraint('length(dataset_version) > 0', name='check_food_datasets_version'),
    )


def downgrade() -> None:
    op.drop_table('food_datasets')
