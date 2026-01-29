"""
Comprehensive tests for User model constraints and validation
Validates Requirements 2.1.1, 2.1.2, 2.1.4, 2.1.5
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError

from app.database.connection import Base
from app.models.user import User


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


def create_valid_user(**overrides):
    """Helper function to create a valid user with optional field overrides"""
    defaults = {
        "name": "Test User",
        "age": 25,
        "gender": "male",
        "height_cm": 180.0,
        "weight_kg": 70.0,
        "activity_level": "moderately_active"
    }
    defaults.update(overrides)
    return User(**defaults)


class TestUserBasicFields:
    """Test basic user profile fields - Requirements 2.1.1"""
    
    def test_create_user_with_all_required_fields(self, db_session):
        """Test creating user with all required basic fields"""
        user = create_valid_user()
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.name == "Test User"
        assert user.age == 25
        assert user.gender == "male"
        assert user.height_cm == 180.0
        assert user.weight_kg == 70.0
        assert user.activity_level == "moderately_active"
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_create_user_with_female_gender(self, db_session):
        """Test creating user with female gender"""
        user = create_valid_user(gender="female")
        
        db_session.add(user)
        db_session.commit()
        
        assert user.gender == "female"
    
    def test_create_user_with_other_gender(self, db_session):
        """Test creating user with other gender"""
        user = create_valid_user(gender="other")
        
        db_session.add(user)
        db_session.commit()
        
        assert user.gender == "other"
    
    def test_name_cannot_be_null(self, db_session):
        """Test that name field is required"""
        user = User(
            age=25,
            gender="male",
            height_cm=180.0,
            weight_kg=70.0,
            activity_level="moderately_active"
        )
        
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestUserBodyComposition:
    """Test body composition fields - Requirements 2.1.2"""
    
    def test_create_user_with_body_fat_percentage(self, db_session):
        """Test creating user with body fat percentage"""
        user = create_valid_user(body_fat_percentage=15.5)
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.body_fat_percentage == 15.5
    
    def test_create_user_with_muscle_mass(self, db_session):
        """Test creating user with muscle mass"""
        user = create_valid_user(muscle_mass_kg=45.2)
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.muscle_mass_kg == 45.2
    
    def test_create_user_with_both_body_composition_fields(self, db_session):
        """Test creating user with both body composition fields"""
        user = create_valid_user(
            body_fat_percentage=18.0,
            muscle_mass_kg=50.0
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.body_fat_percentage == 18.0
        assert user.muscle_mass_kg == 50.0
    
    def test_body_composition_fields_can_be_null(self, db_session):
        """Test that body composition fields are optional"""
        user = create_valid_user()  # No body composition data
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.body_fat_percentage is None
        assert user.muscle_mass_kg is None


class TestActivityLevelValidation:
    """Test activity level validation - Requirements 2.1.4"""
    
    @pytest.mark.parametrize("activity_level", [
        "sedentary",
        "lightly_active", 
        "moderately_active",
        "very_active",
        "extremely_active"
    ])
    def test_valid_activity_levels(self, db_session, activity_level):
        """Test all valid activity levels"""
        user = create_valid_user(activity_level=activity_level)
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.activity_level == activity_level
    
    def test_invalid_activity_level_rejected(self, db_session):
        """Test that invalid activity levels are rejected"""
        user = create_valid_user(activity_level="invalid_level")
        
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestAgeConstraints:
    """Test age validation constraints - Requirements 2.1.5"""
    
    def test_valid_age_ranges(self, db_session):
        """Test valid age ranges"""
        # Test minimum valid age
        user_young = create_valid_user(age=1)
        db_session.add(user_young)
        db_session.commit()
        assert user_young.age == 1
        
        db_session.rollback()
        
        # Test maximum valid age
        user_old = create_valid_user(age=149)
        db_session.add(user_old)
        db_session.commit()
        assert user_old.age == 149
        
        db_session.rollback()
        
        # Test typical age
        user_typical = create_valid_user(age=30)
        db_session.add(user_typical)
        db_session.commit()
        assert user_typical.age == 30
    
    def test_age_zero_rejected(self, db_session):
        """Test that age 0 is rejected"""
        user = create_valid_user(age=0)
        
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_negative_age_rejected(self, db_session):
        """Test that negative ages are rejected"""
        user = create_valid_user(age=-5)
        
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_age_too_high_rejected(self, db_session):
        """Test that ages >= 150 are rejected"""
        user = create_valid_user(age=150)
        
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestHeightConstraints:
    """Test height validation constraints - Requirements 2.1.5"""
    
    def test_valid_height_ranges(self, db_session):
        """Test valid height ranges"""
        # Test minimum valid height (just above 50cm)
        user_short = create_valid_user(height_cm=51.0)
        db_session.add(user_short)
        db_session.commit()
        assert user_short.height_cm == 51.0
        
        db_session.rollback()
        
        # Test maximum valid height (just below 300cm)
        user_tall = create_valid_user(height_cm=299.0)
        db_session.add(user_tall)
        db_session.commit()
        assert user_tall.height_cm == 299.0
        
        db_session.rollback()
        
        # Test typical height
        user_typical = create_valid_user(height_cm=175.5)
        db_session.add(user_typical)
        db_session.commit()
        assert user_typical.height_cm == 175.5
    
    def test_height_too_low_rejected(self, db_session):
        """Test that heights <= 50cm are rejected"""
        user = create_valid_user(height_cm=50.0)
        
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_height_too_high_rejected(self, db_session):
        """Test that heights >= 300cm are rejected"""
        user = create_valid_user(height_cm=300.0)
        
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_negative_height_rejected(self, db_session):
        """Test that negative heights are rejected"""
        user = create_valid_user(height_cm=-10.0)
        
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestWeightConstraints:
    """Test weight validation constraints - Requirements 2.1.5"""
    
    def test_valid_weight_ranges(self, db_session):
        """Test valid weight ranges"""
        # Test minimum valid weight (just above 20kg)
        user_light = create_valid_user(weight_kg=21.0)
        db_session.add(user_light)
        db_session.commit()
        assert user_light.weight_kg == 21.0
        
        db_session.rollback()
        
        # Test maximum valid weight (just below 500kg)
        user_heavy = create_valid_user(weight_kg=499.0)
        db_session.add(user_heavy)
        db_session.commit()
        assert user_heavy.weight_kg == 499.0
        
        db_session.rollback()
        
        # Test typical weight
        user_typical = create_valid_user(weight_kg=75.5)
        db_session.add(user_typical)
        db_session.commit()
        assert user_typical.weight_kg == 75.5
    
    def test_weight_too_low_rejected(self, db_session):
        """Test that weights <= 20kg are rejected"""
        user = create_valid_user(weight_kg=20.0)
        
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_weight_too_high_rejected(self, db_session):
        """Test that weights >= 500kg are rejected"""
        user = create_valid_user(weight_kg=500.0)
        
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_negative_weight_rejected(self, db_session):
        """Test that negative weights are rejected"""
        user = create_valid_user(weight_kg=-5.0)
        
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestBodyFatPercentageConstraints:
    """Test body fat percentage validation constraints - Requirements 2.1.5"""
    
    def test_valid_body_fat_ranges(self, db_session):
        """Test valid body fat percentage ranges"""
        # Test minimum valid body fat (0%)
        user_min = create_valid_user(body_fat_percentage=0.0)
        db_session.add(user_min)
        db_session.commit()
        assert user_min.body_fat_percentage == 0.0
        
        db_session.rollback()
        
        # Test maximum valid body fat (100%)
        user_max = create_valid_user(body_fat_percentage=100.0)
        db_session.add(user_max)
        db_session.commit()
        assert user_max.body_fat_percentage == 100.0
        
        db_session.rollback()
        
        # Test typical body fat
        user_typical = create_valid_user(body_fat_percentage=15.5)
        db_session.add(user_typical)
        db_session.commit()
        assert user_typical.body_fat_percentage == 15.5
    
    def test_negative_body_fat_rejected(self, db_session):
        """Test that negative body fat percentages are rejected"""
        user = create_valid_user(body_fat_percentage=-1.0)
        
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_body_fat_over_100_rejected(self, db_session):
        """Test that body fat percentages > 100% are rejected"""
        user = create_valid_user(body_fat_percentage=101.0)
        
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestMuscleMassConstraints:
    """Test muscle mass validation constraints - Requirements 2.1.5"""
    
    def test_valid_muscle_mass_ranges(self, db_session):
        """Test valid muscle mass ranges"""
        # Test minimum valid muscle mass (0kg)
        user_min = create_valid_user(muscle_mass_kg=0.0)
        db_session.add(user_min)
        db_session.commit()
        assert user_min.muscle_mass_kg == 0.0
        
        db_session.rollback()
        
        # Test typical muscle mass
        user_typical = create_valid_user(muscle_mass_kg=45.5)
        db_session.add(user_typical)
        db_session.commit()
        assert user_typical.muscle_mass_kg == 45.5
        
        db_session.rollback()
        
        # Test high muscle mass
        user_high = create_valid_user(muscle_mass_kg=80.0)
        db_session.add(user_high)
        db_session.commit()
        assert user_high.muscle_mass_kg == 80.0
    
    def test_negative_muscle_mass_rejected(self, db_session):
        """Test that negative muscle mass is rejected"""
        user = create_valid_user(muscle_mass_kg=-1.0)
        
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestGenderConstraints:
    """Test gender validation constraints - Requirements 2.1.5"""
    
    @pytest.mark.parametrize("gender", ["male", "female", "other"])
    def test_valid_genders(self, db_session, gender):
        """Test all valid gender values"""
        user = create_valid_user(gender=gender)
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.gender == gender
    
    def test_invalid_gender_rejected(self, db_session):
        """Test that invalid gender values are rejected"""
        user = create_valid_user(gender="invalid_gender")
        
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestUserModelIntegration:
    """Integration tests for complete user model functionality"""
    
    def test_create_complete_user_profile(self, db_session):
        """Test creating a user with all fields populated"""
        user = User(
            name="Complete User Profile",
            age=28,
            gender="female",
            height_cm=165.0,
            weight_kg=60.0,
            body_fat_percentage=22.0,
            muscle_mass_kg=35.0,
            activity_level="very_active"
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Verify all fields are correctly stored
        assert user.name == "Complete User Profile"
        assert user.age == 28
        assert user.gender == "female"
        assert user.height_cm == 165.0
        assert user.weight_kg == 60.0
        assert user.body_fat_percentage == 22.0
        assert user.muscle_mass_kg == 35.0
        assert user.activity_level == "very_active"
        assert user.id is not None
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_timestamps_auto_generated(self, db_session):
        """Test that created_at and updated_at are automatically generated"""
        user = create_valid_user()
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.created_at is not None
        assert user.updated_at is not None
        # Both timestamps should be very close (within a few seconds)
        time_diff = abs((user.updated_at - user.created_at).total_seconds())
        assert time_diff < 5  # Should be created within 5 seconds of each other
    
    def test_multiple_users_can_be_created(self, db_session):
        """Test that multiple users can be created without conflicts"""
        user1 = create_valid_user(name="User One", age=25)
        user2 = create_valid_user(name="User Two", age=30)
        user3 = create_valid_user(name="User Three", age=35)
        
        db_session.add_all([user1, user2, user3])
        db_session.commit()
        
        # Verify all users were created with unique IDs
        assert user1.id != user2.id != user3.id
        assert user1.name == "User One"
        assert user2.name == "User Two"
        assert user3.name == "User Three"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])