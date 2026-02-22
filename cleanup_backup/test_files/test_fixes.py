#!/usr/bin/env python3
"""
Test script to verify the fixes for day regeneration and dietary compliance
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_providers import MockAIProvider, GroqAIProvider
from app.services.ai_service import DietPlanAI
from app.core.config import settings


async def test_mock_dietary_compliance():
    """Test that mock provider generates vegetarian-compliant meals"""
    print("Testing Mock Provider Dietary Compliance...")
    
    mock_provider = MockAIProvider()
    
    # Test daily plan
    daily_response, _ = await mock_provider.generate_completion(
        "You are a vegetarian nutritionist",
        "Generate a daily vegetarian diet plan"
    )
    
    daily_plan = json.loads(daily_response)
    print(f"Daily plan type: {daily_plan.get('plan_type')}")
    
    # Check for forbidden ingredients
    forbidden_ingredients = ['chicken', 'beef', 'pork', 'fish', 'salmon', 'turkey', 'bacon', 'ham']
    
    for meal in daily_plan.get('meals', []):
        meal_name = meal.get('name', '').lower()
        ingredients = [ing.get('name', '').lower() for ing in meal.get('ingredients', [])]
        
        print(f"  Meal: {meal.get('name')}")
        print(f"    Ingredients: {[ing.get('name') for ing in meal.get('ingredients', [])]}")
        
        # Check meal name and ingredients for forbidden items
        for forbidden in forbidden_ingredients:
            if forbidden in meal_name or any(forbidden in ing for ing in ingredients):
                print(f"    ❌ FOUND FORBIDDEN INGREDIENT: {forbidden}")
                return False
    
    print("  ✅ All meals are vegetarian compliant")
    
    # Test weekly plan
    weekly_response, _ = await mock_provider.generate_completion(
        "You are a vegetarian nutritionist",
        "Generate a weekly vegetarian diet plan"
    )
    
    weekly_plan = json.loads(weekly_response)
    print(f"Weekly plan type: {weekly_plan.get('plan_type')}")
    print(f"Number of days: {len(weekly_plan.get('days', []))}")
    
    # Check each day
    for day_idx, day in enumerate(weekly_plan.get('days', [])):
        print(f"  Day {day_idx + 1} ({day.get('day_name')}):")
        for meal in day.get('meals', []):
            meal_name = meal.get('name', '').lower()
            ingredients = [ing.get('name', '').lower() for ing in meal.get('ingredients', [])]
            
            # Check for forbidden ingredients
            for forbidden in forbidden_ingredients:
                if forbidden in meal_name or any(forbidden in ing for ing in ingredients):
                    print(f"    ❌ FOUND FORBIDDEN INGREDIENT: {forbidden} in {meal.get('name')}")
                    return False
        print(f"    ✅ All meals vegetarian compliant")
    
    return True


async def test_groq_fallback():
    """Test that Groq provider falls back to mock data on rate limits"""
    print("\nTesting Groq Provider Fallback...")
    
    try:
        groq_provider = GroqAIProvider()
        print("  Groq provider initialized successfully")
        
        # This might hit rate limits, which should trigger fallback
        response, usage = await groq_provider.generate_completion(
            "You are a vegetarian nutritionist",
            "Generate a daily vegetarian diet plan"
        )
        
        # Parse response to verify it's valid JSON
        plan_data = json.loads(response)
        print(f"  ✅ Got valid response: {plan_data.get('plan_type')} plan")
        print(f"  Usage data: {usage}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Groq provider test failed: {e}")
        return False


async def test_ai_service_integration():
    """Test the AI service with enhanced dietary compliance"""
    print("\nTesting AI Service Integration...")
    
    try:
        ai_service = DietPlanAI()
        
        # Mock health context for vegetarian user
        health_context = """
# Health Context Document

## Personal Information
- Age: 30
- Gender: Female
- Height: 165 cm
- Weight: 60 kg

## Dietary Preferences
- Diet Type: Vegetarian
- Allergies: None
- Food Preferences: Enjoys variety, prefers whole foods

## Health Goals
- Goal: Maintain current weight
- Target Calories: 1800 per day
- Protein Target: 60g per day
"""
        
        # Test daily plan generation
        daily_plan = await ai_service.generate_diet_plan(
            health_context=health_context,
            plan_type="daily"
        )
        
        print(f"  ✅ Generated daily plan: {daily_plan.get('plan_type')}")
        print(f"  Total calories: {daily_plan.get('daily_totals', {}).get('calories')}")
        
        # Check for dietary compliance
        forbidden_ingredients = ['chicken', 'beef', 'pork', 'fish', 'salmon', 'turkey', 'bacon', 'ham']
        
        for meal in daily_plan.get('meals', []):
            meal_name = meal.get('name', '').lower()
            ingredients = [ing.get('name', '').lower() for ing in meal.get('ingredients', [])]
            
            for forbidden in forbidden_ingredients:
                if forbidden in meal_name or any(forbidden in ing for ing in ingredients):
                    print(f"    ❌ DIETARY VIOLATION: {forbidden} found in {meal.get('name')}")
                    return False
        
        print("  ✅ All meals comply with vegetarian diet")
        return True
        
    except Exception as e:
        print(f"  ❌ AI service test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🧪 Running Diet Plan Fixes Tests\n")
    
    tests = [
        ("Mock Dietary Compliance", test_mock_dietary_compliance),
        ("Groq Fallback", test_groq_fallback),
        ("AI Service Integration", test_ai_service_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("TEST RESULTS SUMMARY")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Fixes are working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")


if __name__ == "__main__":
    asyncio.run(main())