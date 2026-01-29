"""Initial database schema

Revision ID: 7d87899f7073
Revises: 
Create Date: 2026-01-18 21:17:09.513173

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7d87899f7073'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('gender', sa.String(length=20), nullable=False),
        sa.Column('height_cm', sa.Float(), nullable=False),
        sa.Column('weight_kg', sa.Float(), nullable=False),
        sa.Column('body_fat_percentage', sa.Float(), nullable=True),
        sa.Column('muscle_mass_kg', sa.Float(), nullable=True),
        sa.Column('activity_level', sa.String(length=30), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint('age > 0 AND age < 150', name='check_age_range'),
        sa.CheckConstraint('height_cm > 50 AND height_cm < 300', name='check_height_range'),
        sa.CheckConstraint('weight_kg > 20 AND weight_kg < 500', name='check_weight_range'),
        sa.CheckConstraint('body_fat_percentage IS NULL OR (body_fat_percentage >= 0 AND body_fat_percentage <= 100)', name='check_body_fat_range'),
        sa.CheckConstraint('muscle_mass_kg IS NULL OR muscle_mass_kg >= 0', name='check_muscle_mass_range'),
        sa.CheckConstraint("gender IN ('male', 'female', 'other')", name='check_gender_values'),
        sa.CheckConstraint("activity_level IN ('sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active')", name='check_activity_level_values'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create health_goals table
    op.create_table('health_goals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('primary_goal', sa.String(length=20), nullable=False),
        sa.Column('target_weight_kg', sa.Float(), nullable=True),
        sa.Column('timeline_weeks', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint("primary_goal IN ('fat_loss', 'muscle_gain', 'maintenance')", name='check_primary_goal_values'),
        sa.CheckConstraint('target_weight_kg IS NULL OR (target_weight_kg > 20 AND target_weight_kg < 500)', name='check_target_weight_range'),
        sa.CheckConstraint('timeline_weeks IS NULL OR (timeline_weeks > 0 AND timeline_weeks <= 104)', name='check_timeline_range'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create diet_preferences table
    op.create_table('diet_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('diet_type', sa.String(length=20), nullable=False),
        sa.Column('allergies', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('foods_to_avoid', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('meals_per_day', sa.Integer(), nullable=False),
        sa.Column('budget_constraints', sa.Text(), nullable=True),
        sa.Column('lifestyle_constraints', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint("diet_type IN ('vegetarian', 'non_vegetarian', 'vegan')", name='check_diet_type_values'),
        sa.CheckConstraint('meals_per_day >= 1 AND meals_per_day <= 8', name='check_meals_per_day_range'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create health_context_documents table
    op.create_table('health_context_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('bmr_calories', sa.Float(), nullable=False),
        sa.Column('tdee_calories', sa.Float(), nullable=False),
        sa.Column('min_daily_calories', sa.Float(), nullable=False),
        sa.Column('max_calorie_deficit', sa.Float(), nullable=False),
        sa.Column('min_protein_grams', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.CheckConstraint('bmr_calories > 0', name='check_bmr_positive'),
        sa.CheckConstraint('tdee_calories > bmr_calories', name='check_tdee_greater_than_bmr'),
        sa.CheckConstraint('min_daily_calories >= bmr_calories', name='check_min_calories_above_bmr'),
        sa.CheckConstraint('max_calorie_deficit > 0', name='check_max_deficit_positive'),
        sa.CheckConstraint('min_protein_grams > 0', name='check_min_protein_positive'),
        sa.CheckConstraint('version > 0', name='check_version_positive'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'version', name='uq_user_version')
    )
    
    # Create diet_plans table
    op.create_table('diet_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hcd_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan_type', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('content', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint("plan_type IN ('weekly', 'daily')", name='check_plan_type_values'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    op.create_index('ix_health_goals_user_id', 'health_goals', ['user_id'])
    op.create_index('ix_diet_preferences_user_id', 'diet_preferences', ['user_id'])
    op.create_index('ix_health_context_documents_user_id', 'health_context_documents', ['user_id'])
    op.create_index('ix_health_context_documents_is_active', 'health_context_documents', ['is_active'])
    op.create_index('ix_diet_plans_user_id', 'diet_plans', ['user_id'])
    op.create_index('ix_diet_plans_hcd_id', 'diet_plans', ['hcd_id'])
    op.create_index('ix_diet_plans_created_at', 'diet_plans', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_diet_plans_created_at', table_name='diet_plans')
    op.drop_index('ix_diet_plans_hcd_id', table_name='diet_plans')
    op.drop_index('ix_diet_plans_user_id', table_name='diet_plans')
    op.drop_index('ix_health_context_documents_is_active', table_name='health_context_documents')
    op.drop_index('ix_health_context_documents_user_id', table_name='health_context_documents')
    op.drop_index('ix_diet_preferences_user_id', table_name='diet_preferences')
    op.drop_index('ix_health_goals_user_id', table_name='health_goals')
    op.drop_index('ix_users_created_at', table_name='users')
    
    # Drop tables
    op.drop_table('diet_plans')
    op.drop_table('health_context_documents')
    op.drop_table('diet_preferences')
    op.drop_table('health_goals')
    op.drop_table('users')
