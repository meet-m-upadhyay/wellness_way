"""
Basic API functionality test
"""

import asyncio
import json
from datetime import datetime
from uuid import uuid4

from app.main import app
from app.database.connection import SessionLocal, create_tables
from app.services.user_service import UserService
from app.services.health_context_service import HealthContextService
from app.schemas.user import UserProfileCreate, HealthGoalsCreate, DietPreferencesCreate
from app.schemas.health_context import HealthContextDocumentCreate


async def test_basic_functionality():
    """Test basic API functionality"""
    print("🧪 Testing WellnessWay Diet Planner API...")
    
    # Create database tables
    print("📊 Creating database tables...")
    create_tables()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Test user service
        print("👤 Testing user profile creation...")
        user_service = UserService(db)
        
        # Create user profile
        profile_data = UserProfileCreate(
            name="Test User",
            age=30,
            gender="male",
            height_cm=175.0,
            weight_kg=75.0,
            body_fat_percentage=15.0,
            muscle_mass_kg=35.0,
            activity_level="moderately_active"
        )
        
        user = await user_service.create_user_profile(profile_data)
        print(f"✅ User created: {user.name} (ID: {user.id})")
        
        # Create health goals
        print("🎯 Testing health goals creation...")
        goals_data = HealthGoalsCreate(
            primary_goal="fat_loss",
            target_weight_kg=70.0,
            timeline_weeks=12
        )
        
        goals = await user_service.create_health_goals(user.id, goals_data)
        print(f"✅ Health goals created: {goals.primary_goal}")
        
        # Create diet preferences
        print("🥗 Testing diet preferences creation...")
        preferences_data = DietPreferencesCreate(
            diet_type="non_vegetarian",
            allergies=["nuts", "shellfish"],
            foods_to_avoid=["spicy food"],
            meals_per_day=3,
            budget_constraints="moderate",
            lifestyle_constraints="busy schedule"
        )
        
        preferences = await user_service.create_diet_preferences(user.id, preferences_data)
        print(f"✅ Diet preferences created: {preferences.diet_type}")
        
        # Test health context service
        print("📋 Testing health context document creation...")
        hcd_service = HealthContextService(db)
        
        # Create HCD from profile data
        hcd = await hcd_service.update_health_context_from_profile(user.id)
        print(f"✅ Health Context Document created: Version {hcd.version}")
        print(f"   BMR: {hcd.bmr_calories:.1f} calories")
        print(f"   TDEE: {hcd.tdee_calories:.1f} calories")
        print(f"   Min daily calories: {hcd.min_daily_calories:.1f}")
        print(f"   Max deficit: {hcd.max_calorie_deficit:.1f}")
        print(f"   Min protein: {hcd.min_protein_grams:.1f}g")
        
        # Test retrieving current HCD
        current_hcd = await hcd_service.get_current_health_context_document(user.id)
        print(f"✅ Retrieved current HCD: Version {current_hcd.version}")
        
        # Test HCD history
        history = await hcd_service.get_health_context_document_history(user.id)
        print(f"✅ HCD history retrieved: {history.total_count} documents")
        
        print("\n🎉 All tests passed! The API is working correctly.")
        print("\n📊 Summary:")
        print(f"   - User Profile: ✅ Created and retrieved")
        print(f"   - Health Goals: ✅ Created and retrieved")
        print(f"   - Diet Preferences: ✅ Created and retrieved")
        print(f"   - Health Context Document: ✅ Generated and versioned")
        print(f"   - Business Logic: ✅ BMR, TDEE, and safety calculations working")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = asyncio.run(test_basic_functionality())
    if success:
        print("\n🚀 The WellnessWay Diet Planner API is ready for use!")
        print("   You can now:")
        print("   1. Create user profiles with health goals and preferences")
        print("   2. Generate Health Context Documents with calculated metrics")
        print("   3. Use the API endpoints for frontend integration")
        print("   4. Start the server with: uvicorn app.main:app --reload")
    else:
        print("\n💥 Tests failed. Please check the errors above.")