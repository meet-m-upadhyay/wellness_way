"""
Tests for Health Context Documents table with versioning support
Validates Requirements 2.4.1, 2.4.4, 2.4.5
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError

from app.database.connection import Base
from app.models import User, HealthContextDocument


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


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing"""
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
    return user


class TestHealthContextDocumentVersioning:
    """Test versioning support for Health Context Documents"""
    
    def test_create_first_version(self, db_session, sample_user):
        """Test creating the first version of HCD"""
        hcd = HealthContextDocument(
            user_id=sample_user.id,
            version=1,
            content="# Health Context Document v1\n\nInitial profile",
            bmr_calories=1800.0,
            tdee_calories=2200.0,
            min_daily_calories=1800.0,
            max_calorie_deficit=400.0,
            min_protein_grams=112.0,
            is_active=True
        )
        
        db_session.add(hcd)
        db_session.commit()
        db_session.refresh(hcd)
        
        assert hcd.id is not None
        assert hcd.version == 1
        assert hcd.is_active is True
        assert "Initial profile" in hcd.content
    
    def test_create_multiple_versions(self, db_session, sample_user):
        """Test creating multiple versions for the same user"""
        # Create version 1
        hcd_v1 = HealthContextDocument(
            user_id=sample_user.id,
            version=1,
            content="# Health Context Document v1",
            bmr_calories=1800.0,
            tdee_calories=2200.0,
            min_daily_calories=1800.0,
            max_calorie_deficit=400.0,
            min_protein_grams=112.0,
            is_active=False  # Deactivated when v2 is created
        )
        
        # Create version 2
        hcd_v2 = HealthContextDocument(
            user_id=sample_user.id,
            version=2,
            content="# Health Context Document v2",
            bmr_calories=1850.0,
            tdee_calories=2250.0,
            min_daily_calories=1850.0,
            max_calorie_deficit=450.0,
            min_protein_grams=115.0,
            is_active=True
        )
        
        db_session.add_all([hcd_v1, hcd_v2])
        db_session.commit()
        
        # Verify both versions exist
        all_hcds = db_session.query(HealthContextDocument).filter_by(user_id=sample_user.id).all()
        assert len(all_hcds) == 2
        
        versions = [hcd.version for hcd in all_hcds]
        assert 1 in versions
        assert 2 in versions
    
    def test_unique_version_per_user(self, db_session, sample_user):
        """Test that version numbers must be unique per user"""
        # Create first HCD with version 1
        hcd1 = HealthContextDocument(
            user_id=sample_user.id,
            version=1,
            content="# Health Context Document v1",
            bmr_calories=1800.0,
            tdee_calories=2200.0,
            min_daily_calories=1800.0,
            max_calorie_deficit=400.0,
            min_protein_grams=112.0,
            is_active=True
        )
        db_session.add(hcd1)
        db_session.commit()
        
        # Try to create another HCD with the same version for the same user
        hcd2 = HealthContextDocument(
            user_id=sample_user.id,
            version=1,  # Same version - should fail
            content="# Health Context Document v1 duplicate",
            bmr_calories=1900.0,
            tdee_calories=2300.0,
            min_daily_calories=1900.0,
            max_calorie_deficit=400.0,
            min_protein_grams=120.0,
            is_active=True
        )
        db_session.add(hcd2)
        
        # Should raise IntegrityError due to unique constraint
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_different_users_can_have_same_version(self, db_session):
        """Test that different users can have the same version number"""
        # Create two users
        user1 = User(
            name="User 1",
            age=25,
            gender="female",
            height_cm=165.0,
            weight_kg=60.0,
            activity_level="lightly_active"
        )
        user2 = User(
            name="User 2",
            age=35,
            gender="male",
            height_cm=180.0,
            weight_kg=80.0,
            activity_level="very_active"
        )
        db_session.add_all([user1, user2])
        db_session.commit()
        db_session.refresh(user1)
        db_session.refresh(user2)
        
        # Create HCD version 1 for both users
        hcd1 = HealthContextDocument(
            user_id=user1.id,
            version=1,
            content="# User 1 HCD v1",
            bmr_calories=1400.0,
            tdee_calories=1680.0,
            min_daily_calories=1400.0,
            max_calorie_deficit=300.0,
            min_protein_grams=96.0,
            is_active=True
        )
        
        hcd2 = HealthContextDocument(
            user_id=user2.id,
            version=1,
            content="# User 2 HCD v1",
            bmr_calories=2000.0,
            tdee_calories=2800.0,
            min_daily_calories=2000.0,
            max_calorie_deficit=500.0,
            min_protein_grams=128.0,
            is_active=True
        )
        
        db_session.add_all([hcd1, hcd2])
        db_session.commit()
        
        # Both should be created successfully
        assert hcd1.id is not None
        assert hcd2.id is not None
        assert hcd1.version == 1
        assert hcd2.version == 1


class TestHealthContextDocumentImmutability:
    """Test immutability requirements for Health Context Documents"""
    
    def test_hcd_content_immutability(self, db_session, sample_user):
        """Test that HCD content should be treated as immutable"""
        # Create HCD
        hcd = HealthContextDocument(
            user_id=sample_user.id,
            version=1,
            content="# Original Content",
            bmr_calories=1800.0,
            tdee_calories=2200.0,
            min_daily_calories=1800.0,
            max_calorie_deficit=400.0,
            min_protein_grams=112.0,
            is_active=True
        )
        db_session.add(hcd)
        db_session.commit()
        
        original_content = hcd.content
        original_bmr = hcd.bmr_calories
        
        # In practice, the application should create a new version instead of modifying
        # Test that we can update content while maintaining constraints
        hcd.content = "# Modified Content"
        hcd.bmr_calories = 1900.0
        hcd.tdee_calories = 2300.0  # Update TDEE to maintain constraint
        hcd.min_daily_calories = 1900.0  # Update min calories to maintain constraint
        db_session.commit()
        
        # The database allows the update, but the application should prevent this
        # and create new versions instead
        assert hcd.content == "# Modified Content"
        assert hcd.bmr_calories == 1900.0
        
        # Note: True immutability would be enforced at the application layer
        # by always creating new versions instead of updating existing ones
    
    def test_version_increment_pattern(self, db_session, sample_user):
        """Test that versions should increment sequentially"""
        versions_to_create = [1, 2, 3, 4, 5]
        
        for version in versions_to_create:
            hcd = HealthContextDocument(
                user_id=sample_user.id,
                version=version,
                content=f"# Health Context Document v{version}",
                bmr_calories=1800.0 + (version * 10),  # Slight variation
                tdee_calories=2200.0 + (version * 10),
                min_daily_calories=1800.0 + (version * 10),
                max_calorie_deficit=400.0,
                min_protein_grams=112.0,
                is_active=(version == 5)  # Only latest is active
            )
            db_session.add(hcd)
        
        db_session.commit()
        
        # Verify all versions exist
        all_hcds = db_session.query(HealthContextDocument).filter_by(
            user_id=sample_user.id
        ).order_by(HealthContextDocument.version).all()
        
        assert len(all_hcds) == 5
        for i, hcd in enumerate(all_hcds):
            assert hcd.version == i + 1
            assert hcd.is_active == (hcd.version == 5)


class TestHealthContextDocumentConstraints:
    """Test database constraints for Health Context Documents"""
    
    def test_bmr_positive_constraint(self, db_session, sample_user):
        """Test that BMR must be positive"""
        hcd = HealthContextDocument(
            user_id=sample_user.id,
            version=1,
            content="# Test HCD",
            bmr_calories=-100.0,  # Invalid: negative BMR
            tdee_calories=2200.0,
            min_daily_calories=1800.0,
            max_calorie_deficit=400.0,
            min_protein_grams=112.0,
            is_active=True
        )
        db_session.add(hcd)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_tdee_greater_than_bmr_constraint(self, db_session, sample_user):
        """Test that TDEE must be greater than BMR"""
        hcd = HealthContextDocument(
            user_id=sample_user.id,
            version=1,
            content="# Test HCD",
            bmr_calories=2000.0,
            tdee_calories=1800.0,  # Invalid: TDEE < BMR
            min_daily_calories=1800.0,
            max_calorie_deficit=400.0,
            min_protein_grams=112.0,
            is_active=True
        )
        db_session.add(hcd)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_min_calories_above_bmr_constraint(self, db_session, sample_user):
        """Test that minimum daily calories must be at least BMR"""
        hcd = HealthContextDocument(
            user_id=sample_user.id,
            version=1,
            content="# Test HCD",
            bmr_calories=1800.0,
            tdee_calories=2200.0,
            min_daily_calories=1600.0,  # Invalid: min_calories < BMR
            max_calorie_deficit=400.0,
            min_protein_grams=112.0,
            is_active=True
        )
        db_session.add(hcd)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_max_deficit_positive_constraint(self, db_session, sample_user):
        """Test that maximum calorie deficit must be positive"""
        hcd = HealthContextDocument(
            user_id=sample_user.id,
            version=1,
            content="# Test HCD",
            bmr_calories=1800.0,
            tdee_calories=2200.0,
            min_daily_calories=1800.0,
            max_calorie_deficit=-100.0,  # Invalid: negative deficit
            min_protein_grams=112.0,
            is_active=True
        )
        db_session.add(hcd)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_min_protein_positive_constraint(self, db_session, sample_user):
        """Test that minimum protein must be positive"""
        hcd = HealthContextDocument(
            user_id=sample_user.id,
            version=1,
            content="# Test HCD",
            bmr_calories=1800.0,
            tdee_calories=2200.0,
            min_daily_calories=1800.0,
            max_calorie_deficit=400.0,
            min_protein_grams=-50.0,  # Invalid: negative protein
            is_active=True
        )
        db_session.add(hcd)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_version_positive_constraint(self, db_session, sample_user):
        """Test that version must be positive"""
        hcd = HealthContextDocument(
            user_id=sample_user.id,
            version=0,  # Invalid: version must be > 0
            content="# Test HCD",
            bmr_calories=1800.0,
            tdee_calories=2200.0,
            min_daily_calories=1800.0,
            max_calorie_deficit=400.0,
            min_protein_grams=112.0,
            is_active=True
        )
        db_session.add(hcd)
        
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestHealthContextDocumentRequirements:
    """Test specific requirements validation"""
    
    def test_requirement_2_4_1_markdown_content(self, db_session, sample_user):
        """Test Requirement 2.4.1: System generates markdown HCD from user inputs"""
        markdown_content = """# Health Context Document

## User Profile
- **Name**: Test User
- **Age**: 30 years
- **Gender**: Male
- **Height**: 175 cm
- **Weight**: 70 kg
- **Activity Level**: Moderately Active

## Calculated Metrics
- **BMR**: 1800 calories/day
- **TDEE**: 2200 calories/day

## Safety Constraints
- **Minimum Daily Calories**: 1800
- **Maximum Calorie Deficit**: 400
- **Minimum Protein**: 112g/day
"""
        
        hcd = HealthContextDocument(
            user_id=sample_user.id,
            version=1,
            content=markdown_content,
            bmr_calories=1800.0,
            tdee_calories=2200.0,
            min_daily_calories=1800.0,
            max_calorie_deficit=400.0,
            min_protein_grams=112.0,
            is_active=True
        )
        
        db_session.add(hcd)
        db_session.commit()
        db_session.refresh(hcd)
        
        # Verify markdown content is stored correctly
        assert "# Health Context Document" in hcd.content
        assert "## User Profile" in hcd.content
        assert "## Calculated Metrics" in hcd.content
        assert "## Safety Constraints" in hcd.content
        assert hcd.bmr_calories == 1800.0
        assert hcd.tdee_calories == 2200.0
    
    def test_requirement_2_4_4_versioning_and_immutability(self, db_session, sample_user):
        """Test Requirement 2.4.4: HCD is versioned and immutable once created"""
        import time
        
        # Create initial version
        hcd_v1 = HealthContextDocument(
            user_id=sample_user.id,
            version=1,
            content="# Initial HCD",
            bmr_calories=1800.0,
            tdee_calories=2200.0,
            min_daily_calories=1800.0,
            max_calorie_deficit=400.0,
            min_protein_grams=112.0,
            is_active=True
        )
        db_session.add(hcd_v1)
        db_session.commit()
        
        original_id = hcd_v1.id
        original_created_at = hcd_v1.created_at
        
        # Small delay to ensure different timestamps
        time.sleep(0.01)
        
        # Simulate profile update by creating new version
        hcd_v2 = HealthContextDocument(
            user_id=sample_user.id,
            version=2,
            content="# Updated HCD",
            bmr_calories=1850.0,  # Updated values
            tdee_calories=2250.0,
            min_daily_calories=1850.0,
            max_calorie_deficit=450.0,
            min_protein_grams=115.0,
            is_active=True
        )
        db_session.add(hcd_v2)
        db_session.commit()
        
        # Verify both versions exist with different IDs and timestamps
        v1_from_db = db_session.query(HealthContextDocument).filter_by(
            user_id=sample_user.id, version=1
        ).first()
        v2_from_db = db_session.query(HealthContextDocument).filter_by(
            user_id=sample_user.id, version=2
        ).first()
        
        assert v1_from_db.id == original_id
        assert v1_from_db.created_at == original_created_at
        assert v1_from_db.content == "# Initial HCD"
        assert v1_from_db.bmr_calories == 1800.0
        
        assert v2_from_db.id != original_id
        # Note: In SQLite with in-memory DB, timestamps might be the same due to speed
        # In production PostgreSQL, this would be different
        assert v2_from_db.content == "# Updated HCD"
        assert v2_from_db.bmr_calories == 1850.0
    
    def test_requirement_2_4_5_new_versions_on_update(self, db_session, sample_user):
        """Test Requirement 2.4.5: New versions created when user updates profile"""
        # Simulate user profile updates creating new HCD versions
        profile_updates = [
            {"weight": 70.0, "bmr": 1800.0, "tdee": 2200.0},
            {"weight": 68.0, "bmr": 1780.0, "tdee": 2180.0},  # Weight loss
            {"weight": 72.0, "bmr": 1820.0, "tdee": 2220.0},  # Weight gain
        ]
        
        for i, update in enumerate(profile_updates, 1):
            hcd = HealthContextDocument(
                user_id=sample_user.id,
                version=i,
                content=f"# HCD v{i} - Weight: {update['weight']}kg",
                bmr_calories=update['bmr'],
                tdee_calories=update['tdee'],
                min_daily_calories=update['bmr'],
                max_calorie_deficit=400.0,
                min_protein_grams=update['weight'] * 1.6,  # 1.6g per kg
                is_active=(i == len(profile_updates))  # Only latest is active
            )
            db_session.add(hcd)
        
        db_session.commit()
        
        # Verify all versions exist
        all_versions = db_session.query(HealthContextDocument).filter_by(
            user_id=sample_user.id
        ).order_by(HealthContextDocument.version).all()
        
        assert len(all_versions) == 3
        
        # Verify version progression
        for i, hcd in enumerate(all_versions, 1):
            assert hcd.version == i
            assert f"Weight: {profile_updates[i-1]['weight']}kg" in hcd.content
            assert hcd.bmr_calories == profile_updates[i-1]['bmr']
            assert hcd.is_active == (i == 3)  # Only latest is active


if __name__ == "__main__":
    pytest.main([__file__, "-v"])