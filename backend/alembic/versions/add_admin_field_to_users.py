"""Add admin field to users table

Revision ID: add_admin_field
Revises: 7d87899f7073
Create Date: 2026-01-23 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_admin_field'
down_revision = '7d87899f7073'
branch_labels = None
depends_on = None


def upgrade():
    """Add is_admin field to users table"""
    # Add is_admin column with default False
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))
    
    # Set admin status for the specific email
    op.execute("UPDATE users SET is_admin = true WHERE email = 'meetupadhyaykgp@gmail.com'")


def downgrade():
    """Remove is_admin field from users table"""
    op.drop_column('users', 'is_admin')