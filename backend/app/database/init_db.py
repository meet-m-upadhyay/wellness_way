"""
Database initialization script for WellnessWay Diet Planner
"""

import logging
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import get_engine, Base, get_session_local
from app.core.config import get_settings

# Import all models to ensure they are registered
from app.models import User, HealthGoals, DietPreferences, HealthContextDocument, DietPlan

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Initialize the database with tables"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=get_engine())
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def check_db_connection() -> bool:
    """Check if database connection is working"""
    try:
        db = get_session_local()()
        # Simple query to test connection
        db.execute("SELECT 1")
        db.close()
        logger.info("Database connection successful")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        return False


def create_sample_data() -> None:
    """Create sample data for development (optional)"""
    try:
        db = get_session_local()()
        
        # Check if sample user already exists
        existing_user = db.query(User).first()
        if existing_user:
            logger.info("Sample data already exists, skipping creation")
            db.close()
            return
        
        # Create sample user
        sample_user = User(
            name="John Doe",
            age=30,
            gender="male",
            height_cm=175.0,
            weight_kg=75.0,
            body_fat_percentage=15.0,
            muscle_mass_kg=35.0,
            activity_level="moderately_active"
        )
        
        db.add(sample_user)
        db.commit()
        db.refresh(sample_user)
        
        # Create sample health goals
        sample_goals = HealthGoals(
            user_id=sample_user.id,
            primary_goal="muscle_gain",
            target_weight_kg=80.0,
            timeline_weeks=12
        )
        
        db.add(sample_goals)
        
        # Create sample diet preferences
        sample_preferences = DietPreferences(
            user_id=sample_user.id,
            diet_type="non_vegetarian",
            allergies=["nuts", "shellfish"],
            foods_to_avoid=["spicy food"],
            meals_per_day=4,
            budget_constraints="moderate",
            lifestyle_constraints="busy schedule"
        )
        
        db.add(sample_preferences)
        db.commit()
        
        logger.info("Sample data created successfully")
        db.close()
        
    except SQLAlchemyError as e:
        logger.error(f"Error creating sample data: {e}")
        db.rollback()
        db.close()
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Initializing database...")
    
    # Check connection
    if not check_db_connection():
        print("Failed to connect to database. Please ensure PostgreSQL is running.")
        exit(1)
    
    # Initialize database
    init_db()
    
    # Create sample data if in debug mode
    # Create sample data if in debug mode
    if get_settings().debug:
        create_sample_data()
    
    print("Database initialization completed successfully!")