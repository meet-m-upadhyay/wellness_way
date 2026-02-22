#!/usr/bin/env python3
"""
Test weekly plan vegetarian compliance
"""

import asyncio
import logging
from uuid import UUID
from app.database.connection import get_db
from app.services.diet_plan_service import DietPlanService

# Set up logging to see debug messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_weekly_vegetarian():
    print("🔍 Testing weekly plan vegetarian compliance...")
    
    try:
        # Get database session like FastAPI would
        db_gen = get_db()
        db = next(db_gen)
        
        # Create service like the API endpoint does
        diet_plan_service = DietPlanService(db)
        
        # Use the test user UUID from the context (vegetarian user)
        user_id = UUID("f53f6cb3-4b52-47ca-9cdb-bb61ece32610")
        
        print(f"📋 Testing vegetarian compliance with weekly plan...")
        
        # Generate a weekly plan for vegetarian user
        weekly_plan = await diet_plan_service.generate_weekly_plan(
            user_id=user_id,
            start_date=None
        )
        
        if weekly_plan:
            print(f"✅ Weekly plan generated: {weekly_plan.id}")
            
            # Check meals for vegetarian compliance
            content = weekly_plan.content
            if content and "days" in content:
                print(f"🔍 Checking all meals across 7 days for vegetarian compliance...")
                
                non_veg_ingredients = ["chicken", "beef", "pork", "fish", "salmon", "tuna", "shrimp", "meat", "turkey", "duck"]
                violations = []
                total_meals = 0
                
                for day_idx, day in enumerate(content["days"]):
                    day_name = day.get("day_name", f"Day {day_idx + 1}")
                    print(f"   📅 {day_name}:")
                    
                    meals = day.get("meals", [])
                    for meal in meals:
                        total_meals += 1
                        meal_name = meal.get("name", "").lower()
                        meal_type = meal.get("type", "")
                        
                        print(f"      {meal_type.title()}: {meal.get('name', 'Unknown')}")
                        
                        # Check meal name for non-veg terms
                        for ingredient in non_veg_ingredients:
                            if ingredient in meal_name:
                                violations.append(f"{day_name} {meal_type} contains '{ingredient}' in name: {meal.get('name')}")
                        
                        # Check ingredients list
                        ingredients = meal.get("ingredients", [])
                        for ingredient in ingredients:
                            ingredient_name = ingredient.get("name", "").lower()
                            for non_veg in non_veg_ingredients:
                                if non_veg in ingredient_name:
                                    violations.append(f"{day_name} {meal_type} contains '{non_veg}' ingredient: {ingredient.get('name')}")
                
                print(f"\n📊 Summary: {total_meals} meals across 7 days")
                
                if violations:
                    print("❌ DIETARY VIOLATIONS FOUND:")
                    for violation in violations:
                        print(f"   - {violation}")
                else:
                    print("✅ All meals across the entire week are vegetarian compliant!")
                
                # Show weekly totals
                if "weekly_totals" in content:
                    weekly_totals = content["weekly_totals"]
                    print(f"📈 Weekly totals: {weekly_totals.get('calories', 'N/A')} calories, {weekly_totals.get('protein', 'N/A')}g protein")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_weekly_vegetarian())