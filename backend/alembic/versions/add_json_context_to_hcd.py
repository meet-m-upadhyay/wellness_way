"""Add json_context field to health_context_documents

Revision ID: add_json_context_to_hcd
Revises: 4323ba1e246b
Create Date: 2026-01-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_json_context_to_hcd'
down_revision = '4323ba1e246b'
branch_labels = None
depends_on = None


def upgrade():
    """Add json_context column to health_context_documents table"""
    op.add_column('health_context_documents', 
                  sa.Column('json_context', postgresql.JSONB, nullable=True))


def downgrade():
    """Remove json_context column from health_context_documents table"""
    op.drop_column('health_context_documents', 'json_context')