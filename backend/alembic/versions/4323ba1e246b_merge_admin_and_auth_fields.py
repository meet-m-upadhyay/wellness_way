"""merge admin and auth fields

Revision ID: 4323ba1e246b
Revises: add_admin_field, add_auth_fields
Create Date: 2026-01-23 20:36:52.677309

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4323ba1e246b'
down_revision: Union[str, None] = ('add_admin_field', 'add_auth_fields')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
