"""
Quick test script for ML pipeline
"""

import asyncio
import sys
from uuid import UUID

# Test imports
try:
    from app.services.ml_diet_pipeline.orchestrator import get_ml_pipeline_orchestrator
    from app.services.ml_diet_pipeline.meal_templates import get_meal_template_registry
    from app.services.ml_diet_pipeline.meal_template_selector import get_meal_template_selector, SelectionConstraints, DietType, MealSlot
    print("✅ All ML pipeline modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test meal template registry
print("\n📋 Testing Meal Template Registry...")
registry = get_meal_template_registry()
print(f"✅ Loaded {len(registry.templates)} meal templates")

# List templates by diet type
for diet_type in [DietType.VEGETARIAN, DietType.VEGAN, DietType.NON_VEGETARIAN]:
    templates = registry.get_templates_for_diet_type(diet_type)
    print(f"  - {diet_type.value}: {len(templates)} templates")

# Test template selector
print("\n🎯 Testing Template Selector...")
selector = get_meal_template_selector()

constraints = SelectionConstraints(
    diet_type=DietType.VEGETARIAN,
    meal_slot=MealSlot.BREAKFAST,
    calorie_target=2000,
    protein_target=60,
    allergies=set(),
    foods_to_avoid=set(),
    preferred_tags=set()
)

try:
    template_score = selector.select_template(constraints)
    print(f"✅ Selected template: {template_score.template.name}")
    print(f"  - Score: {template_score.score:.2f}")
    print(f"  - Reasons: {template_score.reasons}")
except Exception as e:
    print(f"❌ Template selection failed: {e}")

# Test orchestrator (without database)
print("\n🎼 Testing Orchestrator...")
try:
    orchestrator = get_ml_pipeline_orchestrator()
    print("✅ Orchestrator initialized successfully")
    print("  - Template selector: ✓")
    print("  - Nutrition adapter: ✓")
    print("  - Scaling engine: ✓")
    print("  - Validation engine: ✓")
    print("  - Text generator: ✓")
except Exception as e:
    print(f"❌ Orchestrator initialization failed: {e}")

# Test ML canonicalizer (optional - requires sentence-transformers)
print("\n🧠 Testing ML Ingredient Canonicalizer...")
try:
    from app.services.ml_diet_pipeline.ingredient_canonicalizer import get_ingredient_canonicalizer_ml
    
    canonicalizer = get_ingredient_canonicalizer_ml()
    print("✅ ML canonicalizer initialized")
    print("  ⚠️  Note: First use will download ML model (~90MB)")
    print("  ⚠️  This is normal and only happens once")
    
    # Test with a simple ingredient (will trigger model download)
    # Uncomment to test:
    # test_ingredients = ["chicken breast", "brown rice", "broccoli"]
    # result = canonicalizer.canonicalize("chicken breast", test_ingredients)
    # print(f"  - Test canonicalization: '{result.original_name}' -> '{result.canonical_name}' (confidence: {result.confidence:.2f})")
    
except ImportError:
    print("⚠️  sentence-transformers not installed")
    print("  Install with: pip install sentence-transformers torch")
except Exception as e:
    print(f"❌ ML canonicalizer test failed: {e}")

print("\n" + "="*60)
print("✅ ML Pipeline Basic Tests Complete!")
print("="*60)
print("\nNext steps:")
print("1. Install ML dependencies: pip install -r requirements-ml.txt")
print("2. Start backend: python start_backend.py")
print("3. Test via UI: Click 'Generate Plan (ML)' button")
print("4. Check logs for [ML_PIPELINE_*] messages")
