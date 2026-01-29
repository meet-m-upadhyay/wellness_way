"""Add admin approval system

Revision ID: add_admin_approval_system
Revises: 4323ba1e246b_merge_admin_and_auth_fields
Create Date: 2026-01-25 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_admin_approval_system'
down_revision = '4323ba1e246b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add approval_status column to users table
    op.add_column('users', sa.Column('approval_status', sa.String(20), nullable=False, server_default='approved'))
    
    # Add check constraint for approval_status
    op.create_check_constraint(
        'check_approval_status_values',
        'users',
        "approval_status IN ('pending', 'approved', 'declined')"
    )
    
    # Create registration_requests table
    op.create_table('registration_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('google_id', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('email', name='uq_registration_requests_email'),
        sa.CheckConstraint("status IN ('pending', 'approved', 'declined')", name='check_registration_status_values')
    )
    
    # Create indexes for better performance
    op.create_index('ix_registration_requests_email', 'registration_requests', ['email'])
    op.create_index('ix_registration_requests_status', 'registration_requests', ['status'])


def downgrade() -> None:
    # Drop registration_requests table
    op.drop_index('ix_registration_requests_status', table_name='registration_requests')
    op.drop_index('ix_registration_requests_email', table_name='registration_requests')
    op.drop_table('registration_requests')
    
    # Remove approval_status column from users table
    op.drop_constraint('check_approval_status_values', 'users', type_='check')
    op.drop_column('users', 'approval_status')