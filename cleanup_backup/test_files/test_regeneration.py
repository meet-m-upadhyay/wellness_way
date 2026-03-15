#!/usr/bin/env python3
"""
Test regeneration endpoints
"""

import asyncio
import logging
from uuid import UUID
from app.database.connection import get_db
from app.services.diet_plan_service import DietPlanService

# Set up logging to see debug messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_regeneration():
    print("🔍 Testing regeneration endpoints...")
    
    try:
        # Get database session like FastAPI would
        db_gen = get_db()
        db = next(db_gen)
        
        # Create service like the API endpoint does
        diet_plan_service = DietPlanService(db)
        
        # Use the test user UUID from the context
        user_id = UUID("f53f6cb3-4b52-47ca-9cdb-bb61ece32610")
        
        print(f"📋 Generating weekly plan for testing...")
        
        # Generate a weekly plan first
        weekly_plan = await diet_plan_service.generate_weekly_plan(
            user_id=user_id,
            start_date=None
        )
        
        if weekly_plan:
            print(f"✅ Weekly plan generated: {weekly_plan.id}")
            
            # Test meal regeneration
            print(f"🔄 Testing meal regeneration...")
            try:
                regenerated_plan = await diet_plan_service.regenerate_meal(
                    plan_id=weekly_plan.id,
                    user_id=user_id,
                    day_index=0,  # First day
                    meal_index=0  # First meal (breakfast)
                )
                print(f"✅ Meal regeneration successful!")
            except Exception as e:
                print(f"❌ Meal regeneration failed: {e}")
            
            # Test day regeneration
            print(f"🔄 Testing day regeneration...")
            try:
                regenerated_plan = await diet_plan_service.regenerate_day(
                    plan_id=weekly_plan.id,
                    user_id=user_id,
                    day_index=1  # Second day
                )
                print(f"✅ Day regeneration successful!")
            except Exception as e:
                print(f"❌ Day regeneration failed: {e}")
        
        # Test daily plan regeneration (should fail for day regeneration)
        print(f"📋 Generating daily plan for testing...")
        daily_plan = await diet_plan_service.generate_daily_plan(
            user_id=user_id,
            target_date=None
        )
        
        if daily_plan:
            print(f"✅ Daily plan generated: {daily_plan.id}")
            
            # Test meal regeneration on daily plan
            print(f"🔄 Testing meal regeneration on daily plan...")
            try:
                regenerated_plan = await diet_plan_service.regenerate_meal(
                    plan_id=daily_plan.id,
                    user_id=user_id,
                    day_index=0,  # Only day
                    meal_index=1  # Second meal (lunch)
                )
                print(f"✅ Daily meal regeneration successful!")
            except Exception as e:
                print(f"❌ Daily meal regeneration failed: {e}")
            
            # Test day regeneration on daily plan (should fail)
            print(f"🔄 Testing day regeneration on daily plan (should fail)...")
            try:
                regenerated_plan = await diet_plan_service.regenerate_day(
                    plan_id=daily_plan.id,
                    user_id=user_id,
                    day_index=0
                )
                print(f"❌ Day regeneration should have failed!")
            except Exception as e:
                print(f"✅ Day regeneration correctly failed: {e}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_regeneration())