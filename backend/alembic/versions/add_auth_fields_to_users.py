"""Add authentication fields to users table

Revision ID: add_auth_fields
Revises: 7d87899f7073
Create Date: 2024-01-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_auth_fields'
down_revision = '7d87899f7073'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add authentication fields to users table
    op.add_column('users', sa.Column('email', sa.String(length=255), nullable=False))
    op.add_column('users', sa.Column('google_id', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('profile_completed', sa.Boolean(), nullable=False, server_default='false'))
    
    # Create indexes
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=True)
    
    # Make existing profile fields nullable for new users
    op.alter_column('users', 'age', nullable=True)
    op.alter_column('users', 'gender', nullable=True)
    op.alter_column('users', 'height_cm', nullable=True)
    op.alter_column('users', 'weight_kg', nullable=True)
    op.alter_column('users', 'activity_level', nullable=True)
    
    # Update constraints to handle nullable fields
    op.drop_constraint('check_age_range', 'users', type_='check')
    op.drop_constraint('check_height_range', 'users', type_='check')
    op.drop_constraint('check_weight_range', 'users', type_='check')
    op.drop_constraint('check_gender_values', 'users', type_='check')
    op.drop_constraint('check_activity_level_values', 'users', type_='check')
    
    # Add updated constraints that handle nullable values
    op.create_check_constraint(
        'check_age_range', 
        'users', 
        'age IS NULL OR (age > 0 AND age < 150)'
    )
    op.create_check_constraint(
        'check_height_range', 
        'users', 
        'height_cm IS NULL OR (height_cm > 50 AND height_cm < 300)'
    )
    op.create_check_constraint(
        'check_weight_range', 
        'users', 
        'weight_kg IS NULL OR (weight_kg > 20 AND weight_kg < 500)'
    )
    op.create_check_constraint(
        'check_gender_values', 
        'users', 
        "gender IS NULL OR gender IN ('male', 'female', 'other')"
    )
    op.create_check_constraint(
        'check_activity_level_values', 
        'users', 
        "activity_level IS NULL OR activity_level IN ('sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active')"
    )


def downgrade() -> None:
    # Remove authentication fields
    op.drop_index(op.f('ix_users_google_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_column('users', 'profile_completed')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'google_id')
    op.drop_column('users', 'email')
    
    # Revert profile fields to non-nullable
    op.alter_column('users', 'activity_level', nullable=False)
    op.alter_column('users', 'weight_kg', nullable=False)
    op.alter_column('users', 'height_cm', nullable=False)
    op.alter_column('users', 'gender', nullable=False)
    op.alter_column('users', 'age', nullable=False)
    
    # Restore original constraints
    op.drop_constraint('check_activity_level_values', 'users', type_='check')
    op.drop_constraint('check_gender_values', 'users', type_='check')
    op.drop_constraint('check_weight_range', 'users', type_='check')
    op.drop_constraint('check_height_range', 'users', type_='check')
    op.drop_constraint('check_age_range', 'users', type_='check')
    
    op.create_check_constraint(
        'check_age_range', 
        'users', 
        'age > 0 AND age < 150'
    )
    op.create_check_constraint(
        'check_height_range', 
        'users', 
        'height_cm > 50 AND height_cm < 300'
    )
    op.create_check_constraint(
        'check_weight_range', 
        'users', 
        'weight_kg > 20 AND weight_kg < 500'
    )
    op.create_check_constraint(
        'check_gender_values', 
        'users', 
        "gender IN ('male', 'female', 'other')"
    )
    op.create_check_constraint(
        'check_activity_level_values', 
        'users', 
        "activity_level IN ('sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active')"
    )