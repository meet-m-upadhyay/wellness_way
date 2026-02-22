#!/usr/bin/env python3
"""
Test Groq API integration directly
"""

import asyncio
import logging
from uuid import UUID
from app.database.connection import get_db
from app.services.diet_plan_service import DietPlanService

# Set up logging to see debug messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_groq_api():
    print("🔍 Testing Groq API integration...")
    
    try:
        # Get database session like FastAPI would
        db_gen = get_db()
        db = next(db_gen)
        
        # Create service like the API endpoint does
        diet_plan_service = DietPlanService(db)
        
        # Use the test user UUID from the context
        user_id = UUID("f53f6cb3-4b52-47ca-9cdb-bb61ece32610")
        
        print(f"📋 Generating daily plan for user {user_id}...")
        
        # Generate a daily plan
        plan = await diet_plan_service.generate_daily_plan(
            user_id=user_id,
            target_date=None  # Use today
        )
        
        if plan:
            print(f"✅ Plan generated successfully!")
            print(f"   Plan ID: {plan.id}")
            print(f"   Plan Type: {plan.plan_type}")
            print(f"   Start Date: {plan.start_date}")
            
            # Check if it's mock data or real AI data
            content = plan.content
            if content and "meals" in content:
                first_meal = content["meals"][0]
                meal_name = first_meal.get("name", "")
                print(f"   First meal: {meal_name}")
                
                # Mock data typically has very specific meal names
                if "Protein-Packed Oatmeal Bowl" in meal_name:
                    print("⚠️  This looks like mock data - Groq API might not be called")
                else:
                    print("✅ This looks like real AI-generated data")
            
        else:
            print("❌ No plan generated")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_groq_api())