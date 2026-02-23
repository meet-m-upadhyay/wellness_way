"""Make registration requests compatible with email signup

Revision ID: 8f3d3b3a2e1f
Revises: add_password_hash_to_users
Create Date: 2026-02-23 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f3d3b3a2e1f'
down_revision: Union[str, None] = 'add_password_hash_to_users'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('registration_requests', 'google_id', nullable=True)
    op.add_column('registration_requests', sa.Column('password_hash', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('registration_requests', 'password_hash')
    op.alter_column('registration_requests', 'google_id', nullable=False)
