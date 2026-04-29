"""Add food_audit_log table

Revision ID: add_food_audit_log_table
Revises: add_registry_versions_table
Create Date: 2026-02-23 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_food_audit_log_table'
down_revision: Union[str, None] = 'add_registry_versions_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'food_audit_log',
        sa.Column('audit_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('food_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('field_changed', sa.String(length=100), nullable=False),
        sa.Column('old_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('changed_by', sa.String(length=255), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('audit_id'),
    )


def downgrade() -> None:
    op.drop_table('food_audit_log')
