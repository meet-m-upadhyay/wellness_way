"""Add food_embeddings table

Revision ID: add_food_embeddings_table
Revises: add_food_audit_log_table
Create Date: 2026-02-23 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_food_embeddings_table'
down_revision: Union[str, None] = 'add_food_audit_log_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'food_embeddings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('food_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('embedding_vector', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('normalized_text_used_for_embedding', sa.String(length=255), nullable=False),
        sa.Column('preprocessing_version', sa.String(length=50), nullable=False),
        sa.Column('embedding_model_name', sa.String(length=100), nullable=False),
        sa.Column('embedding_model_version', sa.String(length=50), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'food_id',
            'embedding_model_name',
            'embedding_model_version',
            'preprocessing_version',
            name='uq_food_embeddings_versioning',
        ),
        sa.CheckConstraint('length(normalized_text_used_for_embedding) > 0', name='check_embedding_text_nonempty'),
    )


def downgrade() -> None:
    op.drop_table('food_embeddings')
