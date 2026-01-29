"""
Comprehensive tests for diet_plans table implementation
Validates Requirements 2.5.1, 2.6.1 and design specifications
"""

import pytest
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError
from hypothesis import given, strategies as st, assume, HealthCheck, settings
import json

from app.database.connection import Base
from app.models.user import User
from app.models.health_context import HealthContextDocument
from app.models.diet_plan import DietPlan


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


class TestDietPlansTableStructure:
    """Test the diet_plans table structure and constraints"""
    
    def test_diet_plan_table_exists(self, db_session):
        """Test that diet_plans table exists and is accessible"""
        # This test passes if we can create a DietPlan instance
        assert DietPlan.__tablename__ == "diet_plans"
        
        # Check that all required columns exist
        columns = [col.name for col in DietPlan.__table__.columns]
        required_columns = [
            'id', 'user_id', 'hcd_id', 'plan_type', 
            'start_date', 'content', 'created_at'
        ]
        
        for col in required_columns:
            assert col in columns, f"Required column '{col}' missing from diet_plans table"
    
    def test_diet_plan_primary_key(self, db_session):
        """Test that diet_plans table has proper UUID primary key"""
        user = self._create_test_user(db_session)
        hcd = self._create_test_hcd(db_session, user.id)
        
        plan = DietPlan(
            user_id=user.id,
            hcd_id=hcd.id,
            plan_type="daily",
            start_date=date.today(),
            content={"test": "data"}
        )
        
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)
        
        # UUID should be automatically generated
        assert plan.id is not None
        assert isinstance(plan.id, type(user.id))  # Same UUID type
    
    def test_diet_plan_foreign_key_constraints(self, db_session):
        """Test that foreign key relationships work correctly"""
        user = self._create_test_user(db_session)
        hcd = self._create_test_hcd(db_session, user.id)
        
        # Valid foreign keys should work
        plan = DietPlan(
            user_id=user.id,
            hcd_id=hcd.id,
            plan_type="weekly",
            start_date=date.today(),
            content={"days": []}
        )
        
        db_session.add(plan)
        db_session.commit()
        
        assert plan.user_id == user.id
        assert plan.hcd_id == hcd.id
    
    def test_diet_plan_type_constraint(self, db_session):
        """Test that plan_type constraint allows only 'weekly' or 'daily'"""
        user = self._create_test_user(db_session)
        hcd = self._create_test_hcd(db_session, user.id)
        
        # Valid plan types should work
        for plan_type in ['weekly', 'daily']:
            plan = DietPlan(
                user_id=user.id,
                hcd_id=hcd.id,
                plan_type=plan_type,
                start_date=date.today(),
                content={"test": "data"}
            )
            
            db_session.add(plan)
            db_session.commit()
            db_session.refresh(plan)
            
            assert plan.plan_type == plan_type
            
            # Clean up for next iteration
            db_session.delete(plan)
            db_session.commit()
        
        # Invalid plan type should fail
        with pytest.raises(IntegrityError):
            invalid_plan = DietPlan(
                user_id=user.id,
                hcd_id=hcd.id,
                plan_type="invalid_type",
                start_date=date.today(),
                content={"test": "data"}
            )
            
            db_session.add(invalid_plan)
            db_session.commit()
    
    def test_diet_plan_jsonb_content_storage(self, db_session):
        """Test that content field properly stores JSONB data"""
        user = self._create_test_user(db_session)
        hcd = self._create_test_hcd(db_session, user.id)
        
        # Test complex JSON structure as per design requirements
        complex_content = {
            "plan_type": "weekly",
            "days": [
                {
                    "date": "2024-01-01",
                    "meals": [
                        {
                            "type": "breakfast",
                            "name": "Oatmeal with Berries",
                            "ingredients": [
                                {"name": "Rolled oats", "quantity": 50, "unit": "g"},
                                {"name": "Blueberries", "quantity": 100, "unit": "g"},
                                {"name": "Milk", "quantity": 200, "unit": "ml"}
                            ],
                            "instructions": "Cook oats with milk, top with berries",
                            "nutrition": {
                                "calories": 320,
                                "protein": 12.5,
                                "carbohydrates": 45.2,
                                "fat": 8.1,
                                "fiber": 6.3,
                                "sodium": 150
                            }
                        },
                        {
                            "type": "lunch",
                            "name": "Grilled Chicken Salad",
                            "ingredients": [
                                {"name": "Chicken breast", "quantity": 150, "unit": "g"},
                                {"name": "Mixed greens", "quantity": 100, "unit": "g"},
                                {"name": "Olive oil", "quantity": 15, "unit": "ml"}
                            ],
                            "instructions": "Grill chicken, serve over greens with oil",
                            "nutrition": {
                                "calories": 380,
                                "protein": 35.2,
                                "carbohydrates": 8.1,
                                "fat": 22.4,
                                "fiber": 3.2,
                                "sodium": 280
                            }
                        }
                    ],
                    "daily_totals": {
                        "calories": 700,
                        "protein": 47.7,
                        "carbohydrates": 53.3,
                        "fat": 30.5,
                        "fiber": 9.5,
                        "sodium": 430
                    }
                }
            ],
            "weekly_totals": {
                "calories": 4900,
                "protein": 334,
                "carbohydrates": 373,
                "fat": 214,
                "fiber": 67,
                "sodium": 3010
            }
        }
        
        plan = DietPlan(
            user_id=user.id,
            hcd_id=hcd.id,
            plan_type="weekly",
            start_date=date.today(),
            content=complex_content
        )
        
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)
        
        # Verify the JSON structure is preserved
        assert plan.content == complex_content
        assert plan.content["plan_type"] == "weekly"
        assert len(plan.content["days"]) == 1
        assert len(plan.content["days"][0]["meals"]) == 2
        assert plan.content["days"][0]["meals"][0]["nutrition"]["calories"] == 320
        assert plan.content["weekly_totals"]["protein"] == 334
    
    def test_diet_plan_required_fields(self, db_session):
        """Test that all required fields are enforced"""
        user = self._create_test_user(db_session)
        hcd = self._create_test_hcd(db_session, user.id)
        
        # Test missing user_id
        with pytest.raises(IntegrityError):
            plan = DietPlan(
                hcd_id=hcd.id,
                plan_type="daily",
                start_date=date.today(),
                content={"test": "data"}
            )
            db_session.add(plan)
            db_session.commit()
        
        db_session.rollback()
        
        # Test missing hcd_id
        with pytest.raises(IntegrityError):
            plan = DietPlan(
                user_id=user.id,
                plan_type="daily",
                start_date=date.today(),
                content={"test": "data"}
            )
            db_session.add(plan)
            db_session.commit()
        
        db_session.rollback()
        
        # Test missing plan_type
        with pytest.raises(IntegrityError):
            plan = DietPlan(
                user_id=user.id,
                hcd_id=hcd.id,
                start_date=date.today(),
                content={"test": "data"}
            )
            db_session.add(plan)
            db_session.commit()
        
        db_session.rollback()
        
        # Test missing start_date
        with pytest.raises(IntegrityError):
            plan = DietPlan(
                user_id=user.id,
                hcd_id=hcd.id,
                plan_type="daily",
                content={"test": "data"}
            )
            db_session.add(plan)
            db_session.commit()
        
        db_session.rollback()
        
        # Test missing content
        with pytest.raises(IntegrityError):
            plan = DietPlan(
                user_id=user.id,
                hcd_id=hcd.id,
                plan_type="daily",
                start_date=date.today()
            )
            db_session.add(plan)
            db_session.commit()
    
    def test_diet_plan_timestamps(self, db_session):
        """Test that created_at timestamp is automatically set"""
        user = self._create_test_user(db_session)
        hcd = self._create_test_hcd(db_session, user.id)
        
        plan = DietPlan(
            user_id=user.id,
            hcd_id=hcd.id,
            plan_type="daily",
            start_date=date.today(),
            content={"test": "data"}
        )
        
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)
        
        # created_at should be automatically set
        assert plan.created_at is not None
        # Just verify it's a datetime object, don't check exact timing due to SQLite differences
        assert isinstance(plan.created_at, datetime)
    
    def _create_test_user(self, db_session):
        """Helper method to create a test user"""
        user = User(
            name="Test User",
            age=30,
            gender="female",
            height_cm=165.0,
            weight_kg=60.0,
            activity_level="moderately_active"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    def _create_test_hcd(self, db_session, user_id):
        """Helper method to create a test health context document"""
        hcd = HealthContextDocument(
            user_id=user_id,
            version=1,
            content="Test HCD content",
            bmr_calories=1500.0,
            tdee_calories=1800.0,
            min_daily_calories=1500.0,
            max_calorie_deficit=300.0,
            min_protein_grams=90.0,
            is_active=True
        )
        db_session.add(hcd)
        db_session.commit()
        db_session.refresh(hcd)
        return hcd


class TestDietPlansPropertyBasedTests:
    """Property-based tests for diet_plans table"""
    
    @given(
        plan_type=st.sampled_from(['weekly', 'daily']),
        days_ahead=st.integers(min_value=0, max_value=365)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_diet_plan_creation_property(self, db_session, plan_type, days_ahead):
        """Property test: Diet plans can be created with valid data"""
        user = self._create_test_user(db_session)
        hcd = self._create_test_hcd(db_session, user.id)
        
        start_date = date.today()
        if days_ahead > 0:
            from datetime import timedelta
            start_date = date.today() + timedelta(days=days_ahead)
        
        content = self._generate_valid_content(plan_type)
        
        plan = DietPlan(
            user_id=user.id,
            hcd_id=hcd.id,
            plan_type=plan_type,
            start_date=start_date,
            content=content
        )
        
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)
        
        # Verify properties
        assert plan.id is not None
        assert plan.user_id == user.id
        assert plan.hcd_id == hcd.id
        assert plan.plan_type == plan_type
        assert plan.start_date == start_date
        assert plan.content == content
        assert plan.created_at is not None
        
        # Clean up
        db_session.delete(plan)
        db_session.commit()
    
    @given(
        content_structure=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(
                st.text(max_size=100),
                st.integers(min_value=0, max_value=10000),
                st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
                st.lists(st.text(max_size=50), max_size=10)
            ),
            min_size=1,
            max_size=10
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_jsonb_content_storage_property(self, db_session, content_structure):
        """Property test: JSONB content can store various data structures"""
        user = self._create_test_user(db_session)
        hcd = self._create_test_hcd(db_session, user.id)
        
        plan = DietPlan(
            user_id=user.id,
            hcd_id=hcd.id,
            plan_type="daily",
            start_date=date.today(),
            content=content_structure
        )
        
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)
        
        # Verify the content is stored and retrieved correctly
        assert plan.content == content_structure
        
        # Verify JSON serialization works
        json_str = json.dumps(plan.content)
        assert json.loads(json_str) == content_structure
        
        # Clean up
        db_session.delete(plan)
        db_session.commit()
    
    def _create_test_user(self, db_session):
        """Helper method to create a test user"""
        user = User(
            name="Test User",
            age=30,
            gender="female",
            height_cm=165.0,
            weight_kg=60.0,
            activity_level="moderately_active"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    def _create_test_hcd(self, db_session, user_id):
        """Helper method to create a test health context document"""
        hcd = HealthContextDocument(
            user_id=user_id,
            version=1,
            content="Test HCD content",
            bmr_calories=1500.0,
            tdee_calories=1800.0,
            min_daily_calories=1500.0,
            max_calorie_deficit=300.0,
            min_protein_grams=90.0,
            is_active=True
        )
        db_session.add(hcd)
        db_session.commit()
        db_session.refresh(hcd)
        return hcd
    
    def _generate_valid_content(self, plan_type):
        """Generate valid content structure for testing"""
        if plan_type == "daily":
            return {
                "date": "2024-01-01",
                "meals": [
                    {
                        "type": "breakfast",
                        "name": "Test Meal",
                        "calories": 300
                    }
                ],
                "daily_totals": {
                    "calories": 300,
                    "protein": 15
                }
            }
        else:  # weekly
            return {
                "days": [
                    {
                        "date": f"2024-01-0{i}",
                        "meals": [
                            {
                                "type": "breakfast",
                                "name": f"Test Meal {i}",
                                "calories": 300
                            }
                        ]
                    } for i in range(1, 8)
                ],
                "weekly_totals": {
                    "calories": 2100,
                    "protein": 105
                }
            }


class TestDietPlansRequirementsValidation:
    """Test that diet_plans table meets specific requirements"""
    
    def test_requirement_2_5_1_weekly_plan_storage(self, db_session):
        """
        Validates: Requirements 2.5.1
        Test that weekly diet plans can be stored with 7 consecutive days
        """
        user = self._create_test_user(db_session)
        hcd = self._create_test_hcd(db_session, user.id)
        
        # Create a weekly plan with 7 days
        weekly_content = {
            "plan_type": "weekly",
            "days": []
        }
        
        # Add 7 consecutive days
        from datetime import timedelta
        start_date = date.today()
        
        for i in range(7):
            day_date = start_date + timedelta(days=i)
            day_content = {
                "date": day_date.isoformat(),
                "meals": [
                    {
                        "type": "breakfast",
                        "name": f"Breakfast Day {i+1}",
                        "ingredients": [{"name": "Oats", "quantity": 50, "unit": "g"}],
                        "nutrition": {"calories": 200, "protein": 8}
                    },
                    {
                        "type": "lunch", 
                        "name": f"Lunch Day {i+1}",
                        "ingredients": [{"name": "Chicken", "quantity": 100, "unit": "g"}],
                        "nutrition": {"calories": 300, "protein": 25}
                    },
                    {
                        "type": "dinner",
                        "name": f"Dinner Day {i+1}",
                        "ingredients": [{"name": "Fish", "quantity": 120, "unit": "g"}],
                        "nutrition": {"calories": 250, "protein": 30}
                    }
                ],
                "daily_totals": {"calories": 750, "protein": 63}
            }
            weekly_content["days"].append(day_content)
        
        weekly_content["weekly_totals"] = {"calories": 5250, "protein": 441}
        
        plan = DietPlan(
            user_id=user.id,
            hcd_id=hcd.id,
            plan_type="weekly",
            start_date=start_date,
            content=weekly_content
        )
        
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)
        
        # Verify weekly plan structure
        assert plan.plan_type == "weekly"
        assert len(plan.content["days"]) == 7
        assert plan.content["plan_type"] == "weekly"
        
        # Verify each day has proper structure
        for i, day in enumerate(plan.content["days"]):
            assert "date" in day
            assert "meals" in day
            assert "daily_totals" in day
            assert len(day["meals"]) == 3  # breakfast, lunch, dinner
            
            # Verify meal structure
            for meal in day["meals"]:
                assert "type" in meal
                assert "name" in meal
                assert "ingredients" in meal
                assert "nutrition" in meal
        
        # Verify weekly totals
        assert "weekly_totals" in plan.content
        assert plan.content["weekly_totals"]["calories"] == 5250
    
    def test_requirement_2_6_1_daily_plan_storage(self, db_session):
        """
        Validates: Requirements 2.6.1
        Test that daily diet plans can be stored for a specific day
        """
        user = self._create_test_user(db_session)
        hcd = self._create_test_hcd(db_session, user.id)
        
        # Create a daily plan
        daily_content = {
            "plan_type": "daily",
            "date": date.today().isoformat(),
            "meals": [
                {
                    "type": "breakfast",
                    "name": "Avocado Toast",
                    "ingredients": [
                        {"name": "Whole grain bread", "quantity": 2, "unit": "slices"},
                        {"name": "Avocado", "quantity": 1, "unit": "medium"},
                        {"name": "Olive oil", "quantity": 5, "unit": "ml"}
                    ],
                    "instructions": "Toast bread, mash avocado, drizzle with oil",
                    "nutrition": {
                        "calories": 320,
                        "protein": 8.5,
                        "carbohydrates": 28.0,
                        "fat": 22.0,
                        "fiber": 12.0,
                        "sodium": 240
                    }
                },
                {
                    "type": "lunch",
                    "name": "Quinoa Buddha Bowl",
                    "ingredients": [
                        {"name": "Quinoa", "quantity": 80, "unit": "g"},
                        {"name": "Chickpeas", "quantity": 100, "unit": "g"},
                        {"name": "Mixed vegetables", "quantity": 150, "unit": "g"}
                    ],
                    "instructions": "Cook quinoa, combine with chickpeas and vegetables",
                    "nutrition": {
                        "calories": 450,
                        "protein": 18.0,
                        "carbohydrates": 65.0,
                        "fat": 12.0,
                        "fiber": 15.0,
                        "sodium": 320
                    }
                },
                {
                    "type": "dinner",
                    "name": "Grilled Salmon",
                    "ingredients": [
                        {"name": "Salmon fillet", "quantity": 150, "unit": "g"},
                        {"name": "Broccoli", "quantity": 200, "unit": "g"},
                        {"name": "Sweet potato", "quantity": 150, "unit": "g"}
                    ],
                    "instructions": "Grill salmon, steam broccoli, roast sweet potato",
                    "nutrition": {
                        "calories": 420,
                        "protein": 35.0,
                        "carbohydrates": 30.0,
                        "fat": 18.0,
                        "fiber": 8.0,
                        "sodium": 180
                    }
                }
            ],
            "daily_totals": {
                "calories": 1190,
                "protein": 61.5,
                "carbohydrates": 123.0,
                "fat": 52.0,
                "fiber": 35.0,
                "sodium": 740
            }
        }
        
        plan = DietPlan(
            user_id=user.id,
            hcd_id=hcd.id,
            plan_type="daily",
            start_date=date.today(),
            content=daily_content
        )
        
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)
        
        # Verify daily plan structure
        assert plan.plan_type == "daily"
        assert plan.content["plan_type"] == "daily"
        assert "date" in plan.content
        assert "meals" in plan.content
        assert "daily_totals" in plan.content
        
        # Verify meal structure matches design requirements
        assert len(plan.content["meals"]) == 3
        for meal in plan.content["meals"]:
            assert "type" in meal
            assert "name" in meal
            assert "ingredients" in meal
            assert "instructions" in meal
            assert "nutrition" in meal
            
            # Verify ingredient structure
            for ingredient in meal["ingredients"]:
                assert "name" in ingredient
                assert "quantity" in ingredient
                assert "unit" in ingredient
            
            # Verify nutrition structure
            nutrition = meal["nutrition"]
            required_nutrition_fields = ["calories", "protein", "carbohydrates", "fat", "fiber", "sodium"]
            for field in required_nutrition_fields:
                assert field in nutrition
        
        # Verify daily totals
        daily_totals = plan.content["daily_totals"]
        assert daily_totals["calories"] == 1190
        assert daily_totals["protein"] == 61.5
    
    def test_structured_json_content_requirement(self, db_session):
        """
        Test that diet plans store structured JSON content as specified in design
        """
        user = self._create_test_user(db_session)
        hcd = self._create_test_hcd(db_session, user.id)
        
        # Test the exact JSON structure from the design document
        design_content = {
            "plan_type": "weekly",
            "days": [
                {
                    "date": "2024-01-01",
                    "meals": [
                        {
                            "type": "breakfast",
                            "name": "Oatmeal with Berries",
                            "ingredients": [
                                {"name": "Rolled oats", "quantity": 50, "unit": "g"},
                                {"name": "Blueberries", "quantity": 100, "unit": "g"}
                            ],
                            "instructions": "Cook oats, add berries",
                            "nutrition": {
                                "calories": 300,
                                "protein": 10,
                                "carbohydrates": 55,
                                "fat": 5,
                                "fiber": 8,
                                "sodium": 100
                            }
                        }
                    ],
                    "daily_totals": {
                        "calories": 300,
                        "protein": 10,
                        "carbohydrates": 55,
                        "fat": 5,
                        "fiber": 8,
                        "sodium": 100
                    }
                }
            ],
            "weekly_totals": {
                "calories": 2100,
                "protein": 70,
                "carbohydrates": 385,
                "fat": 35,
                "fiber": 56,
                "sodium": 700
            }
        }
        
        plan = DietPlan(
            user_id=user.id,
            hcd_id=hcd.id,
            plan_type="weekly",
            start_date=date.today(),
            content=design_content
        )
        
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)
        
        # Verify the structure is preserved exactly
        assert plan.content == design_content
        
        # Verify nested access works
        assert plan.content["days"][0]["meals"][0]["nutrition"]["calories"] == 300
        assert plan.content["weekly_totals"]["protein"] == 70
        
        # Verify JSON serialization/deserialization
        import json
        json_str = json.dumps(plan.content)
        parsed_content = json.loads(json_str)
        assert parsed_content == design_content
    
    def _create_test_user(self, db_session):
        """Helper method to create a test user"""
        user = User(
            name="Test User",
            age=30,
            gender="female",
            height_cm=165.0,
            weight_kg=60.0,
            activity_level="moderately_active"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    def _create_test_hcd(self, db_session, user_id):
        """Helper method to create a test health context document"""
        hcd = HealthContextDocument(
            user_id=user_id,
            version=1,
            content="Test HCD content",
            bmr_calories=1500.0,
            tdee_calories=1800.0,
            min_daily_calories=1500.0,
            max_calorie_deficit=300.0,
            min_protein_grams=90.0,
            is_active=True
        )
        db_session.add(hcd)
        db_session.commit()
        db_session.refresh(hcd)
        return hcd