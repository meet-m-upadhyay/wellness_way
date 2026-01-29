"""
Test Health Context Document relationships and foreign key constraints
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base
from app.models import User, HealthContextDocument, DietPlan
from datetime import date


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


def test_hcd_user_relationship(db_session):
    """Test that HCD can be queried by user_id"""
    # Create user
    user = User(
        name="Test User",
        age=30,
        gender="male",
        height_cm=175.0,
        weight_kg=70.0,
        activity_level="moderately_active"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create multiple HCD versions for the user
    hcd1 = HealthContextDocument(
        user_id=user.id,
        version=1,
        content="# HCD v1",
        bmr_calories=1800.0,
        tdee_calories=2200.0,
        min_daily_calories=1800.0,
        max_calorie_deficit=400.0,
        min_protein_grams=112.0,
        is_active=False
    )
    
    hcd2 = HealthContextDocument(
        user_id=user.id,
        version=2,
        content="# HCD v2",
        bmr_calories=1850.0,
        tdee_calories=2250.0,
        min_daily_calories=1850.0,
        max_calorie_deficit=450.0,
        min_protein_grams=115.0,
        is_active=True
    )
    
    db_session.add_all([hcd1, hcd2])
    db_session.commit()
    
    # Query HCDs by user
    user_hcds = db_session.query(HealthContextDocument).filter_by(user_id=user.id).all()
    assert len(user_hcds) == 2
    
    # Query active HCD
    active_hcd = db_session.query(HealthContextDocument).filter_by(
        user_id=user.id, is_active=True
    ).first()
    assert active_hcd is not None
    assert active_hcd.version == 2
    assert active_hcd.bmr_calories == 1850.0


def test_diet_plan_hcd_relationship(db_session):
    """Test that DietPlan references HCD correctly"""
    # Create user
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
    
    # Create HCD
    hcd = HealthContextDocument(
        user_id=user.id,
        version=1,
        content="# Test HCD",
        bmr_calories=1400.0,
        tdee_calories=1680.0,
        min_daily_calories=1400.0,
        max_calorie_deficit=300.0,
        min_protein_grams=96.0,
        is_active=True
    )
    db_session.add(hcd)
    db_session.commit()
    db_session.refresh(hcd)
    
    # Create diet plan referencing the HCD
    diet_plan = DietPlan(
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
                            "name": "Oatmeal with berries",
                            "calories": 300,
                            "protein": 10
                        }
                    ]
                }
            ]
        }
    )
    db_session.add(diet_plan)
    db_session.commit()
    db_session.refresh(diet_plan)
    
    # Verify the relationship
    assert diet_plan.hcd_id == hcd.id
    assert diet_plan.user_id == user.id
    
    # Query diet plans by HCD
    hcd_plans = db_session.query(DietPlan).filter_by(hcd_id=hcd.id).all()
    assert len(hcd_plans) == 1
    assert hcd_plans[0].id == diet_plan.id


def test_multiple_users_hcd_isolation(db_session):
    """Test that HCDs are properly isolated between users"""
    # Create two users
    user1 = User(
        name="User 1",
        age=25,
        gender="male",
        height_cm=180.0,
        weight_kg=75.0,
        activity_level="very_active"
    )
    
    user2 = User(
        name="User 2",
        age=35,
        gender="female",
        height_cm=160.0,
        weight_kg=55.0,
        activity_level="sedentary"
    )
    
    db_session.add_all([user1, user2])
    db_session.commit()
    db_session.refresh(user1)
    db_session.refresh(user2)
    
    # Create HCDs for both users
    hcd1 = HealthContextDocument(
        user_id=user1.id,
        version=1,
        content="# User 1 HCD",
        bmr_calories=2000.0,
        tdee_calories=2800.0,
        min_daily_calories=2000.0,
        max_calorie_deficit=500.0,
        min_protein_grams=120.0,
        is_active=True
    )
    
    hcd2 = HealthContextDocument(
        user_id=user2.id,
        version=1,
        content="# User 2 HCD",
        bmr_calories=1300.0,
        tdee_calories=1560.0,
        min_daily_calories=1300.0,
        max_calorie_deficit=260.0,
        min_protein_grams=88.0,
        is_active=True
    )
    
    db_session.add_all([hcd1, hcd2])
    db_session.commit()
    
    # Verify isolation - each user should only see their own HCDs
    user1_hcds = db_session.query(HealthContextDocument).filter_by(user_id=user1.id).all()
    user2_hcds = db_session.query(HealthContextDocument).filter_by(user_id=user2.id).all()
    
    assert len(user1_hcds) == 1
    assert len(user2_hcds) == 1
    
    assert user1_hcds[0].content == "# User 1 HCD"
    assert user2_hcds[0].content == "# User 2 HCD"
    
    assert user1_hcds[0].bmr_calories == 2000.0
    assert user2_hcds[0].bmr_calories == 1300.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])