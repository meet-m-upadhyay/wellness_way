"""merge heads

Revision ID: 3580d1e342b7
Revises: cc728301c6c8, 8f3d3b3a2e1f
Create Date: 2026-02-23 18:13:19.256139

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3580d1e342b7'
down_revision: Union[str, None] = ('cc728301c6c8', '8f3d3b3a2e1f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
