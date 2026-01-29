#!/usr/bin/env python3
"""
Debug ingredient name normalization issue
"""

from app.services.nutrition_database import get_nutrition_database, normalize_ingredient_name_for_lookup
from app.services.ingredient_normalizer import get_ingredient_normalizer

def debug_ingredient_names():
    """Debug why ingredient names are not matching database keys"""
    
    print("DEBUGGING INGREDIENT NAME NORMALIZATION")
    print("=" * 60)
    
    # Test problematic ingredient names from logs
    problematic_names = [
        "greek yogurt plain",
        "tofu extrafirm", 
        "lentils red dry"
    ]
    
    # Get services
    nutrition_db = get_nutrition_database()
    normalizer = get_ingredient_normalizer()
    
    print("\n1. TESTING INGREDIENT NORMALIZER")
    print("-" * 40)
    
    for name in problematic_names:
        print(f"\nTesting: '{name}'")
        
        try:
            # Test ingredient normalizer
            result = normalizer.normalize(name)
            canonical_name = result.canonical_name
            print(f"  Normalizer result: '{canonical_name}' (confidence: {result.confidence.value})")
            
            # Test database lookup normalizer
            lookup_name = normalize_ingredient_name_for_lookup(canonical_name)
            print(f"  Lookup normalizer: '{lookup_name}'")
            
            # Test if it exists in database
            exists = nutrition_db.validate_food_exists(lookup_name)
            print(f"  Exists in DB: {exists}")
            
            if not exists:
                print(f"  ❌ PROBLEM: '{lookup_name}' not found in database!")
                # Show similar names
                all_foods = nutrition_db.get_all_food_names()
                similar = [f for f in all_foods if any(word in f for word in name.split())][:5]
                print(f"  Similar names in DB: {similar}")
            else:
                print(f"  ✅ SUCCESS: Found in database")
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
    
    print("\n2. TESTING DIRECT NUTRITION LOOKUP")
    print("-" * 40)
    
    for name in problematic_names:
        print(f"\nTesting nutrition lookup: '{name}'")
        try:
            nutrition = nutrition_db.get_nutrition(name, 100.0)
            if nutrition:
                print(f"  ✅ SUCCESS: {nutrition.calories} cal, {nutrition.protein}g protein")
            else:
                print(f"  ❌ FAILED: No nutrition data returned")
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
    
    print("\n3. CHECKING DATABASE KEYS")
    print("-" * 40)
    
    # Show some actual database keys for comparison
    all_foods = nutrition_db.get_all_food_names()
    yogurt_keys = [f for f in all_foods if 'yogurt' in f]
    tofu_keys = [f for f in all_foods if 'tofu' in f]
    lentil_keys = [f for f in all_foods if 'lentil' in f]
    
    print(f"Yogurt keys in DB: {yogurt_keys}")
    print(f"Tofu keys in DB: {tofu_keys}")
    print(f"Lentil keys in DB: {lentil_keys}")


if __name__ == "__main__":
    debug_ingredient_names()