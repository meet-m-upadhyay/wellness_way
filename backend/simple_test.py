#!/usr/bin/env python3
import asyncio
import json
from app.services.ai_providers import MockAIProvider

async def test():
    provider = MockAIProvider()
    response, usage = await provider.generate_completion('system', 'Generate a daily vegetarian diet plan')
    plan = json.loads(response)
    print('Plan type:', plan.get('plan_type'))
    print('Meals:')
    for meal in plan.get('meals', []):
        print(f'  - {meal.get("name")}')
        ingredients = [ing.get('name') for ing in meal.get('ingredients', [])]
        print(f'    Ingredients: {ingredients}')
        # Check for non-vegetarian ingredients
        forbidden = ['chicken', 'beef', 'pork', 'fish', 'salmon', 'turkey', 'bacon', 'ham']
        violations = [f for f in forbidden if any(f in ing.lower() for ing in ingredients)]
        if violations:
            print(f'    ❌ VIOLATIONS: {violations}')
        else:
            print('    ✅ All vegetarian')

asyncio.run(test())