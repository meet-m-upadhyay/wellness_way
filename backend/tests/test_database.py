"""
Tests for database configuration and models
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base
from app.models import User, HealthGoals, DietPreferences, HealthContextDocument, DietPlan


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_user_model_creation(db_session):
    """Test creating a user model"""
    user = User(
        name="Test User",
        age=25,
        gender="male",
        height_cm=180.0,
        weight_kg=70.0,
        activity_level="moderately_active"
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    assert user.id is not None
    assert user.name == "Test User"
    assert user.age == 25
    assert user.created_at is not None


def test_health_goals_model_creation(db_session):
    """Test creating a health goals model"""
    # First create a user
    user = User(
        name="Test User",
        age=25,
        gender="female",
        height_cm=165.0,
        weight_kg=60.0,
        activity_level="lightly_active"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create health goals
    goals = HealthGoals(
        user_id=user.id,
        primary_goal="fat_loss",
        target_weight_kg=55.0,
        timeline_weeks=8
    )
    
    db_session.add(goals)
    db_session.commit()
    db_session.refresh(goals)
    
    assert goals.id is not None
    assert goals.user_id == user.id
    assert goals.primary_goal == "fat_loss"


def test_diet_preferences_model_creation(db_session):
    """Test creating a diet preferences model"""
    # First create a user
    user = User(
        name="Test User",
        age=30,
        gender="other",
        height_cm=170.0,
        weight_kg=65.0,
        activity_level="very_active"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create diet preferences
    preferences = DietPreferences(
        user_id=user.id,
        diet_type="vegetarian",
        allergies=["nuts", "dairy"],
        foods_to_avoid=["spicy"],
        meals_per_day=3
    )
    
    db_session.add(preferences)
    db_session.commit()
    db_session.refresh(preferences)
    
    assert preferences.id is not None
    assert preferences.user_id == user.id
    assert preferences.diet_type == "vegetarian"
    assert preferences.allergies == ["nuts", "dairy"]


def test_health_context_document_model_creation(db_session):
    """Test creating a health context document model"""
    # First create a user
    user = User(
        name="Test User",
        age=28,
        gender="male",
        height_cm=175.0,
        weight_kg=75.0,
        activity_level="moderately_active"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create health context document
    hcd = HealthContextDocument(
        user_id=user.id,
        version=1,
        content="# Health Context Document\n\nTest content",
        bmr_calories=1800.0,
        tdee_calories=2200.0,
        min_daily_calories=1800.0,
        max_calorie_deficit=400.0,
        min_protein_grams=120.0,
        is_active=True
    )
    
    db_session.add(hcd)
    db_session.commit()
    db_session.refresh(hcd)
    
    assert hcd.id is not None
    assert hcd.user_id == user.id
    assert hcd.version == 1
    assert hcd.bmr_calories == 1800.0


def test_diet_plan_model_creation(db_session):
    """Test creating a diet plan model"""
    from datetime import date
    
    # First create a user
    user = User(
        name="Test User",
        age=35,
        gender="female",
        height_cm=160.0,
        weight_kg=55.0,
        activity_level="sedentary"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create HCD
    hcd = HealthContextDocument(
        user_id=user.id,
        version=1,
        content="Test HCD",
        bmr_calories=1400.0,
        tdee_calories=1680.0,
        min_daily_calories=1400.0,
        max_calorie_deficit=300.0,
        min_protein_grams=88.0,
        is_active=True
    )
    db_session.add(hcd)
    db_session.commit()
    db_session.refresh(hcd)
    
    # Create diet plan
    plan = DietPlan(
        user_id=user.id,
        hcd_id=hcd.id,
        plan_type="weekly",
        start_date=date.today(),
        content={
            "days": [
                {
                    "date": "2024-01-01",
                    "meals": [
                        {
                            "type": "breakfast",
                            "name": "Oatmeal",
                            "calories": 300
                        }
                    ]
                }
            ]
        }
    )
    
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    
    assert plan.id is not None
    assert plan.user_id == user.id
    assert plan.hcd_id == hcd.id
    assert plan.plan_type == "weekly"
    assert "days" in plan.content


if __name__ == "__main__":
    pytest.main([__file__])