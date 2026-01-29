#!/usr/bin/env python3
"""
Test dietary compliance and day regeneration fixes
"""

import asyncio
import logging
from uuid import UUID
from app.database.connection import get_db
from app.services.diet_plan_service import DietPlanService

# Set up logging to see debug messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_dietary_compliance():
    print("🔍 Testing dietary compliance and day regeneration fixes...")
    
    try:
        # Get database session like FastAPI would
        db_gen = get_db()
        db = next(db_gen)
        
        # Create service like the API endpoint does
        diet_plan_service = DietPlanService(db)
        
        # Use the test user UUID from the context (vegetarian user)
        user_id = UUID("f53f6cb3-4b52-47ca-9cdb-bb61ece32610")
        
        print(f"📋 Testing vegetarian compliance with daily plan...")
        
        # Generate a daily plan for vegetarian user
        daily_plan = await diet_plan_service.generate_daily_plan(
            user_id=user_id,
            target_date=None
        )
        
        if daily_plan:
            print(f"✅ Daily plan generated: {daily_plan.id}")
            
            # Check meals for vegetarian compliance
            content = daily_plan.content
            if content and "meals" in content:
                print(f"🔍 Checking meals for vegetarian compliance...")
                
                non_veg_ingredients = ["chicken", "beef", "pork", "fish", "salmon", "tuna", "shrimp", "meat"]
                violations = []
                
                for i, meal in enumerate(content["meals"]):
                    meal_name = meal.get("name", "").lower()
                    meal_type = meal.get("type", "")
                    
                    print(f"   {meal_type.title()}: {meal.get('name', 'Unknown')}")
                    
                    # Check meal name for non-veg terms
                    for ingredient in non_veg_ingredients:
                        if ingredient in meal_name:
                            violations.append(f"{meal_type} contains '{ingredient}' in name: {meal.get('name')}")
                    
                    # Check ingredients list
                    ingredients = meal.get("ingredients", [])
                    for ingredient in ingredients:
                        ingredient_name = ingredient.get("name", "").lower()
                        for non_veg in non_veg_ingredients:
                            if non_veg in ingredient_name:
                                violations.append(f"{meal_type} contains '{non_veg}' ingredient: {ingredient.get('name')}")
                
                if violations:
                    print("❌ DIETARY VIOLATIONS FOUND:")
                    for violation in violations:
                        print(f"   - {violation}")
                else:
                    print("✅ All meals are vegetarian compliant!")
            
            # Test day regeneration on daily plan (should now work)
            print(f"🔄 Testing day regeneration on daily plan (should now work)...")
            try:
                regenerated_plan = await diet_plan_service.regenerate_day(
                    plan_id=daily_plan.id,
                    user_id=user_id,
                    day_index=0
                )
                print(f"✅ Day regeneration on daily plan successful!")
                
                # Check the regenerated plan for compliance too
                content = regenerated_plan.content
                if content and "meals" in content:
                    print(f"🔍 Checking regenerated meals for vegetarian compliance...")
                    
                    violations = []
                    for i, meal in enumerate(content["meals"]):
                        meal_name = meal.get("name", "").lower()
                        meal_type = meal.get("type", "")
                        
                        print(f"   {meal_type.title()}: {meal.get('name', 'Unknown')}")
                        
                        # Check meal name for non-veg terms
                        for ingredient in non_veg_ingredients:
                            if ingredient in meal_name:
                                violations.append(f"{meal_type} contains '{ingredient}' in name: {meal.get('name')}")
                        
                        # Check ingredients list
                        ingredients = meal.get("ingredients", [])
                        for ingredient in ingredients:
                            ingredient_name = ingredient.get("name", "").lower()
                            for non_veg in non_veg_ingredients:
                                if non_veg in ingredient_name:
                                    violations.append(f"{meal_type} contains '{non_veg}' ingredient: {ingredient.get('name')}")
                    
                    if violations:
                        print("❌ DIETARY VIOLATIONS IN REGENERATED PLAN:")
                        for violation in violations:
                            print(f"   - {violation}")
                    else:
                        print("✅ Regenerated meals are also vegetarian compliant!")
                
            except Exception as e:
                print(f"❌ Day regeneration failed: {e}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_dietary_compliance())