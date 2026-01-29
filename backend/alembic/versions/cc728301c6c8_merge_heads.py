"""merge heads

Revision ID: cc728301c6c8
Revises: add_admin_approval_system, add_json_context_to_hcd
Create Date: 2026-01-25 23:33:59.174439

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc728301c6c8'
down_revision: Union[str, None] = ('add_admin_approval_system', 'add_json_context_to_hcd')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
