"""Add password hash to users table

Revision ID: add_password_hash_to_users
Revises: 4323ba1e246b
Create Date: 2026-02-23 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_password_hash_to_users'
down_revision: Union[str, None] = '4323ba1e246b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("users")}
    if "password_hash" not in columns:
        op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'password_hash')
