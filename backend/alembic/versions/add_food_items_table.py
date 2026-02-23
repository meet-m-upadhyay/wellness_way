"""Add food_items table

Revision ID: add_food_items_table
Revises: 3580d1e342b7
Create Date: 2026-02-23 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_food_items_table'
down_revision: Union[str, None] = '3580d1e342b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'food_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('canonical_name', sa.String(length=255), nullable=False),
        sa.Column('dataset_source', sa.String(length=50), nullable=False),
        sa.Column('dataset_food_id', sa.String(length=100), nullable=False),
        sa.Column('registry_version', sa.Integer(), nullable=False),
        sa.Column('macros', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('diet_flags', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('allergen_flags', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('cuisine_tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_deprecated', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint('registry_version > 0', name='check_food_items_registry_version'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dataset_source', 'dataset_food_id', name='uq_food_items_dataset_source_id'),
    )


def downgrade() -> None:
    op.drop_table('food_items')
