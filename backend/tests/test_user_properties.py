"""
Property-based tests for User model validation
Tests correctness properties for user profile constraints and validation
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError
from contextlib import contextmanager

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


@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# Strategy generators for valid user data
valid_names = st.text(min_size=1, max_size=255).filter(lambda x: x.strip())
valid_ages = st.integers(min_value=1, max_value=149)
valid_genders = st.sampled_from(["male", "female", "other"])
valid_heights = st.floats(min_value=50.1, max_value=299.9, allow_nan=False, allow_infinity=False)
valid_weights = st.floats(min_value=20.1, max_value=499.9, allow_nan=False, allow_infinity=False)
valid_body_fat = st.one_of(
    st.none(),
    st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
)
valid_muscle_mass = st.one_of(
    st.none(),
    st.floats(min_value=0.0, max_value=200.0, allow_nan=False, allow_infinity=False)
)
valid_activity_levels = st.sampled_from([
    "sedentary", "lightly_active", "moderately_active", "very_active", "extremely_active"
])

# Strategy for generating valid users
valid_user_data = st.fixed_dictionaries({
    "name": valid_names,
    "age": valid_ages,
    "gender": valid_genders,
    "height_cm": valid_heights,
    "weight_kg": valid_weights,
    "body_fat_percentage": valid_body_fat,
    "muscle_mass_kg": valid_muscle_mass,
    "activity_level": valid_activity_levels
})


class TestUserValidationProperties:
    """Property-based tests for user validation constraints"""
    
    @given(valid_user_data)
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_valid_users_always_save_successfully(self, user_data):
        """
        **Validates: Requirements 2.1.1, 2.1.2, 2.1.4, 2.1.5**
        Property: All users with valid data should save successfully
        """
        with get_db_session() as db_session:
            user = User(**user_data)
            
            # Should not raise any exceptions
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
            
            # Verify the user was saved with all fields intact
            assert user.id is not None
            assert user.name == user_data["name"]
            assert user.age == user_data["age"]
            assert user.gender == user_data["gender"]
            assert user.height_cm == user_data["height_cm"]
            assert user.weight_kg == user_data["weight_kg"]
            assert user.body_fat_percentage == user_data["body_fat_percentage"]
            assert user.muscle_mass_kg == user_data["muscle_mass_kg"]
            assert user.activity_level == user_data["activity_level"]
            assert user.created_at is not None
            assert user.updated_at is not None
    
    @given(st.integers(min_value=-1000, max_value=0))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_invalid_ages_always_rejected(self, invalid_age):
        """
        **Validates: Requirements 2.1.5**
        Property: Ages <= 0 should always be rejected
        """
        with get_db_session() as db_session:
            user = User(
                name="Test User",
                age=invalid_age,
                gender="male",
                height_cm=180.0,
                weight_kg=70.0,
                activity_level="moderately_active"
            )
            
            db_session.add(user)
            with pytest.raises(IntegrityError):
                db_session.commit()
    
    @given(st.integers(min_value=150, max_value=1000))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_excessive_ages_always_rejected(self, excessive_age):
        """
        **Validates: Requirements 2.1.5**
        Property: Ages >= 150 should always be rejected
        """
        with get_db_session() as db_session:
            user = User(
                name="Test User",
                age=excessive_age,
                gender="male",
                height_cm=180.0,
                weight_kg=70.0,
                activity_level="moderately_active"
            )
            
            db_session.add(user)
            with pytest.raises(IntegrityError):
                db_session.commit()
    
    @given(st.floats(max_value=50.0, allow_nan=False, allow_infinity=False))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_invalid_heights_always_rejected(self, invalid_height):
        """
        **Validates: Requirements 2.1.5**
        Property: Heights <= 50cm should always be rejected
        """
        with get_db_session() as db_session:
            user = User(
                name="Test User",
                age=25,
                gender="male",
                height_cm=invalid_height,
                weight_kg=70.0,
                activity_level="moderately_active"
            )
            
            db_session.add(user)
            with pytest.raises(IntegrityError):
                db_session.commit()
    
    @given(st.floats(min_value=300.0, allow_nan=False, allow_infinity=False))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_excessive_heights_always_rejected(self, excessive_height):
        """
        **Validates: Requirements 2.1.5**
        Property: Heights >= 300cm should always be rejected
        """
        with get_db_session() as db_session:
            user = User(
                name="Test User",
                age=25,
                gender="male",
                height_cm=excessive_height,
                weight_kg=70.0,
                activity_level="moderately_active"
            )
            
            db_session.add(user)
            with pytest.raises(IntegrityError):
                db_session.commit()
    
    @given(st.floats(max_value=20.0, allow_nan=False, allow_infinity=False))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_invalid_weights_always_rejected(self, invalid_weight):
        """
        **Validates: Requirements 2.1.5**
        Property: Weights <= 20kg should always be rejected
        """
        with get_db_session() as db_session:
            user = User(
                name="Test User",
                age=25,
                gender="male",
                height_cm=180.0,
                weight_kg=invalid_weight,
                activity_level="moderately_active"
            )
            
            db_session.add(user)
            with pytest.raises(IntegrityError):
                db_session.commit()
    
    @given(st.floats(min_value=500.0, allow_nan=False, allow_infinity=False))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_excessive_weights_always_rejected(self, excessive_weight):
        """
        **Validates: Requirements 2.1.5**
        Property: Weights >= 500kg should always be rejected
        """
        with get_db_session() as db_session:
            user = User(
                name="Test User",
                age=25,
                gender="male",
                height_cm=180.0,
                weight_kg=excessive_weight,
                activity_level="moderately_active"
            )
            
            db_session.add(user)
            with pytest.raises(IntegrityError):
                db_session.commit()
    
    @given(st.floats().filter(lambda x: x < 0 or x > 100))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_invalid_body_fat_percentages_always_rejected(self, invalid_body_fat):
        """
        **Validates: Requirements 2.1.5**
        Property: Body fat percentages outside [0, 100] should always be rejected
        """
        assume(not (invalid_body_fat != invalid_body_fat))  # Filter out NaN
        assume(invalid_body_fat != float('inf') and invalid_body_fat != float('-inf'))  # Filter out infinity
        
        with get_db_session() as db_session:
            user = User(
                name="Test User",
                age=25,
                gender="male",
                height_cm=180.0,
                weight_kg=70.0,
                body_fat_percentage=invalid_body_fat,
                activity_level="moderately_active"
            )
            
            db_session.add(user)
            with pytest.raises(IntegrityError):
                db_session.commit()
    
    @given(st.floats(max_value=-0.1, allow_nan=False, allow_infinity=False))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_negative_muscle_mass_always_rejected(self, negative_muscle_mass):
        """
        **Validates: Requirements 2.1.5**
        Property: Negative muscle mass should always be rejected
        """
        with get_db_session() as db_session:
            user = User(
                name="Test User",
                age=25,
                gender="male",
                height_cm=180.0,
                weight_kg=70.0,
                muscle_mass_kg=negative_muscle_mass,
                activity_level="moderately_active"
            )
            
            db_session.add(user)
            with pytest.raises(IntegrityError):
                db_session.commit()
    
    @given(st.text().filter(lambda x: x not in ["male", "female", "other"]))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_invalid_genders_always_rejected(self, invalid_gender):
        """
        **Validates: Requirements 2.1.5**
        Property: Invalid gender values should always be rejected
        """
        with get_db_session() as db_session:
            user = User(
                name="Test User",
                age=25,
                gender=invalid_gender,
                height_cm=180.0,
                weight_kg=70.0,
                activity_level="moderately_active"
            )
            
            db_session.add(user)
            with pytest.raises(IntegrityError):
                db_session.commit()
    
    @given(st.text().filter(lambda x: x not in [
        "sedentary", "lightly_active", "moderately_active", "very_active", "extremely_active"
    ]))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_invalid_activity_levels_always_rejected(self, invalid_activity):
        """
        **Validates: Requirements 2.1.4, 2.1.5**
        Property: Invalid activity levels should always be rejected
        """
        with get_db_session() as db_session:
            user = User(
                name="Test User",
                age=25,
                gender="male",
                height_cm=180.0,
                weight_kg=70.0,
                activity_level=invalid_activity
            )
            
            db_session.add(user)
            with pytest.raises(IntegrityError):
                db_session.commit()


class TestUserDataIntegrityProperties:
    """Property-based tests for user data integrity"""
    
    @given(valid_user_data, valid_user_data)
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_multiple_users_have_unique_ids(self, user_data1, user_data2):
        """
        **Validates: Requirements 2.1.1**
        Property: Multiple users should always have unique IDs
        """
        with get_db_session() as db_session:
            user1 = User(**user_data1)
            user2 = User(**user_data2)
            
            db_session.add_all([user1, user2])
            db_session.commit()
            db_session.refresh(user1)
            db_session.refresh(user2)
            
            assert user1.id != user2.id
            assert user1.id is not None
            assert user2.id is not None
    
    @given(valid_user_data)
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_user_timestamps_are_consistent(self, user_data):
        """
        **Validates: Requirements 2.1.1**
        Property: User timestamps should be automatically generated and consistent
        """
        with get_db_session() as db_session:
            user = User(**user_data)
            
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
            
            assert user.created_at is not None
            assert user.updated_at is not None
            # updated_at should be >= created_at
            assert user.updated_at >= user.created_at
    
    @given(valid_user_data)
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_optional_fields_can_be_none(self, user_data):
        """
        **Validates: Requirements 2.1.2**
        Property: Body composition fields should be optional and can be None
        """
        # Force optional fields to None
        user_data_with_nulls = user_data.copy()
        user_data_with_nulls["body_fat_percentage"] = None
        user_data_with_nulls["muscle_mass_kg"] = None
        
        with get_db_session() as db_session:
            user = User(**user_data_with_nulls)
            
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
            
            assert user.body_fat_percentage is None
            assert user.muscle_mass_kg is None
            # Other fields should still be present
            assert user.name is not None
            assert user.age is not None
            assert user.gender is not None
            assert user.height_cm is not None
            assert user.weight_kg is not None
            assert user.activity_level is not None


class TestUserBoundaryProperties:
    """Property-based tests for boundary conditions"""
    
    @given(st.integers(min_value=1, max_value=149))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_all_valid_ages_accepted(self, valid_age):
        """
        **Validates: Requirements 2.1.5**
        Property: All ages in valid range [1, 149] should be accepted
        """
        with get_db_session() as db_session:
            user = User(
                name="Test User",
                age=valid_age,
                gender="male",
                height_cm=180.0,
                weight_kg=70.0,
                activity_level="moderately_active"
            )
            
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
            
            assert user.age == valid_age
    
    @given(st.floats(min_value=50.1, max_value=299.9, allow_nan=False, allow_infinity=False))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_all_valid_heights_accepted(self, valid_height):
        """
        **Validates: Requirements 2.1.5**
        Property: All heights in valid range (50, 300) should be accepted
        """
        with get_db_session() as db_session:
            user = User(
                name="Test User",
                age=25,
                gender="male",
                height_cm=valid_height,
                weight_kg=70.0,
                activity_level="moderately_active"
            )
            
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
            
            assert user.height_cm == valid_height
    
    @given(st.floats(min_value=20.1, max_value=499.9, allow_nan=False, allow_infinity=False))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_all_valid_weights_accepted(self, valid_weight):
        """
        **Validates: Requirements 2.1.5**
        Property: All weights in valid range (20, 500) should be accepted
        """
        with get_db_session() as db_session:
            user = User(
                name="Test User",
                age=25,
                gender="male",
                height_cm=180.0,
                weight_kg=valid_weight,
                activity_level="moderately_active"
            )
            
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
            
            assert user.weight_kg == valid_weight
    
    @given(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_all_valid_body_fat_percentages_accepted(self, valid_body_fat):
        """
        **Validates: Requirements 2.1.5**
        Property: All body fat percentages in valid range [0, 100] should be accepted
        """
        with get_db_session() as db_session:
            user = User(
                name="Test User",
                age=25,
                gender="male",
                height_cm=180.0,
                weight_kg=70.0,
                body_fat_percentage=valid_body_fat,
                activity_level="moderately_active"
            )
            
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
            
            assert user.body_fat_percentage == valid_body_fat
    
    @given(st.floats(min_value=0.0, max_value=200.0, allow_nan=False, allow_infinity=False))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_all_valid_muscle_mass_accepted(self, valid_muscle_mass):
        """
        **Validates: Requirements 2.1.5**
        Property: All muscle mass values >= 0 should be accepted
        """
        with get_db_session() as db_session:
            user = User(
                name="Test User",
                age=25,
                gender="male",
                height_cm=180.0,
                weight_kg=70.0,
                muscle_mass_kg=valid_muscle_mass,
                activity_level="moderately_active"
            )
            
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
            
            assert user.muscle_mass_kg == valid_muscle_mass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])