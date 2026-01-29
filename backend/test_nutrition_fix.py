#!/usr/bin/env python3
"""
Test script to verify the nutrition database lookup fix works in actual diet plan generation.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import get_db
from app.services.diet_plan_service import get_diet_plan_service
from app.models.user import User
from app.models.health_context import HealthContextDocument
from uuid import uuid4
import json

async def test_diet_plan_generation():
    print('🧪 TESTING DIET PLAN GENERATION WITH FIXED NUTRITION DATABASE')
    print('=' * 60)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Find a user with an active HCD
        user = db.query(User).first()
        if not user:
            print('❌ No users found in database')
            return
        
        hcd = db.query(HealthContextDocument).filter(
            HealthContextDocument.user_id == user.id,
            HealthContextDocument.is_active == True
        ).first()
        
        if not hcd:
            print(f'❌ No active HCD found for user {user.id}')
            return
        
        print(f'✅ Found user {user.id} with active HCD {hcd.id}')
        
        # Test daily plan generation
        service = get_diet_plan_service(db)
        
        print('🚀 Generating daily diet plan...')
        daily_plan = await service.generate_daily_plan(user_id=user.id)
        
        print(f'✅ SUCCESS: Generated daily plan {daily_plan.id}')
        
        # Check the plan content for nutrition data
        content = daily_plan.content
        if 'daily_totals' in content:
            totals = content['daily_totals']
            print(f'📊 DAILY TOTALS:')
            print(f'   Calories: {totals.get("calories", 0):.1f}')
            print(f'   Protein: {totals.get("protein", 0):.1f}g')
            print(f'   Carbs: {totals.get("carbohydrates", 0):.1f}g')
            print(f'   Fat: {totals.get("fat", 0):.1f}g')
            
            # Check if we have proper nutrition values (not zeros)
            if totals.get('calories', 0) > 0 and totals.get('protein', 0) > 0:
                print('✅ NUTRITION DATA LOOKS GOOD - No more zero values!')
            else:
                print('❌ Still getting zero nutrition values')
        else:
            print('❌ No daily_totals found in plan content')
        
        # Show a sample meal for verification
        if 'meals' in content and len(content['meals']) > 0:
            first_meal = content['meals'][0]
            print(f'\n🍽️ SAMPLE MEAL: {first_meal.get("name", "Unknown")}')
            if 'ingredients' in first_meal:
                for ing in first_meal['ingredients'][:3]:  # Show first 3 ingredients
                    print(f'   - {ing.get("name", "Unknown")}: {ing.get("quantity", 0)}{ing.get("unit", "g")}')
            
            if 'nutrition' in first_meal:
                meal_nutrition = first_meal['nutrition']
                print(f'   Meal calories: {meal_nutrition.get("calories", 0):.1f}')
                print(f'   Meal protein: {meal_nutrition.get("protein", 0):.1f}g')
        
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    asyncio.run(test_diet_plan_generation())