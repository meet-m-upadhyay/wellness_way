#!/usr/bin/env python3
"""
Test weekly plan generation
"""

import asyncio
import logging
from uuid import UUID
from app.database.connection import get_db
from app.services.diet_plan_service import DietPlanService

# Set up logging to see debug messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_weekly_plan():
    print("🔍 Testing weekly plan generation...")
    
    try:
        # Get database session like FastAPI would
        db_gen = get_db()
        db = next(db_gen)
        
        # Create service like the API endpoint does
        diet_plan_service = DietPlanService(db)
        
        # Use the test user UUID from the context
        user_id = UUID("f53f6cb3-4b52-47ca-9cdb-bb61ece32610")
        
        print(f"📋 Generating weekly plan for user {user_id}...")
        
        # Generate a weekly plan
        plan = await diet_plan_service.generate_weekly_plan(
            user_id=user_id,
            start_date=None  # Use next Monday
        )
        
        if plan:
            print(f"✅ Weekly plan generated successfully!")
            print(f"   Plan ID: {plan.id}")
            print(f"   Plan Type: {plan.plan_type}")
            print(f"   Start Date: {plan.start_date}")
            
            # Check if it's mock data or real AI data
            content = plan.content
            if content and "days" in content:
                first_day = content["days"][0]
                if "meals" in first_day:
                    first_meal = first_day["meals"][0]
                    meal_name = first_meal.get("name", "")
                    print(f"   First meal: {meal_name}")
                    
                    # Check if it looks like mock data
                    if "Protein-Packed Oatmeal Bowl" in meal_name:
                        print("⚠️  This looks like mock data - AI response may have failed")
                    else:
                        print("✅ This looks like real AI-generated data")
                
                print(f"   Total days: {len(content['days'])}")
                
                # Show weekly totals if available
                if "weekly_totals" in content:
                    weekly_totals = content["weekly_totals"]
                    print(f"   Weekly calories: {weekly_totals.get('calories', 'N/A')}")
            
        else:
            print("❌ No plan generated")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_weekly_plan())