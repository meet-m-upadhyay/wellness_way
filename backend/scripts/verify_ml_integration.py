import sys
import os
import uuid
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.services.ml_diet_pipeline.orchestrator import get_ml_pipeline_orchestrator

async def verify_integration():
    db = SessionLocal()
    try:
        # 1. Initialize Orchestrator with database components
        orchestrator = get_ml_pipeline_orchestrator(db)
        
        # 2. Mock health context (vegetarian)
        health_context = {
            "diet_type": "vegetarian",
            "tdee_calories": 2000,
            "min_protein_grams": 60,
            "allergies": [],
            "foods_to_avoid": []
        }
        user_id = uuid.uuid4()
        
        # 3. Generate a daily plan
        print("--- GENERATING DAILY PLAN ---")
        plan = await orchestrator.generate_daily_plan(
            db=db,
            user_id=user_id,
            health_context=health_context
        )
        
        print(f"Plan Date: {plan['date']}")
        print(f"Daily Calories: {plan['daily_totals']['calories']:.1f}")
        print(f"Daily Protein: {plan['daily_totals']['protein']:.1f}g")
        
        print("\n--- MEAL DETAILS ---")
        for meal in plan['meals']:
            print(f"Meal: {meal['name']} ({meal['type']})")
            for ing in meal['ingredients']:
                print(f"  - {ing['name']}: {ing['nutrition']['calories']:.1f} cal")
            print(f"  Macros: {meal['nutrition']['calories']:.1f} cal, {meal['nutrition']['protein']:.1f}g protein")
            
        print("\n--- FAISS CANONICALIZATION CHECK ---")
        # Test the canonicalizer directly if it exists
        if orchestrator.canonicalizer:
            test_items = ["plain yogurt", "tofu", "quinoa"]
            for item in test_items:
                try:
                    res = orchestrator.canonicalizer.canonicalize(db, item)
                    print(f"Match found for '{item}': {res['canonical_name']} (id: {res['ingredient_id']}, conf: {res['confidence']:.3f})")
                except Exception as e:
                    print(f"No match for '{item}': {e}")
        else:
            print("Canonicalizer NOT found in orchestrator.")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(verify_integration())
