#!/usr/bin/env python3
"""
Test rate limit handling and fallback mechanisms
"""

import asyncio
import logging
from uuid import UUID
from app.database.connection import get_db
from app.services.diet_plan_service import DietPlanService

# Set up logging to see debug messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rate_limit_handling():
    print("🔍 Testing rate limit handling...")
    
    try:
        # Get database session like FastAPI would
        db_gen = get_db()
        db = next(db_gen)
        
        # Create service like the API endpoint does
        diet_plan_service = DietPlanService(db)
        
        # Use the test user UUID from the context
        user_id = UUID("f53f6cb3-4b52-47ca-9cdb-bb61ece32610")
        
        print(f"📋 Testing daily plan generation (may hit rate limit)...")
        
        # Try to generate a daily plan - this might hit rate limit
        try:
            daily_plan = await diet_plan_service.generate_daily_plan(
                user_id=user_id,
                target_date=None
            )
            
            if daily_plan:
                print(f"✅ Daily plan generated successfully: {daily_plan.id}")
                
                # Check if it's real AI data or mock fallback
                content = daily_plan.content
                if content and "meals" in content:
                    first_meal = content["meals"][0]
                    meal_name = first_meal.get("name", "")
                    print(f"   First meal: {meal_name}")
                    
                    # Check if it looks like mock data (fallback)
                    if "Protein-Packed" in meal_name or "Vegetarian Protein" in meal_name:
                        print("ℹ️  This appears to be mock data (rate limit fallback)")
                    else:
                        print("✅ This appears to be real AI-generated data")
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Daily plan generation failed: {error_msg}")
            
            if "rate limit" in error_msg.lower():
                print("ℹ️  This is expected - we hit the rate limit")
                print("ℹ️  The system should now use mock data as fallback")
            elif "busy" in error_msg.lower():
                print("ℹ️  User-friendly rate limit message is working")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rate_limit_handling())