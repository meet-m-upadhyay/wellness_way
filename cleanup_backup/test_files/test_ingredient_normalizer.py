#!/usr/bin/env python3
"""
Test script for ingredient normalizer - verifies LLM ingredient name handling.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ingredient_normalizer import get_ingredient_normalizer, UnknownIngredientError, ConfidenceLevel

def test_ingredient_normalizer():
    """Test ingredient normalizer with LLM-style ingredient names"""
    
    print("🧪 TESTING INGREDIENT NORMALIZER")
    print("=" * 50)
    
    normalizer = get_ingredient_normalizer()
    
    # Test cases that should work (LLM variations -> database keys)
    test_cases = [
        # Eggs
        ("organic free-range eggs", "eggs (whole)"),
        ("farm fresh eggs", "eggs (whole)"),
        ("large brown eggs", "eggs (whole)"),
        ("2 large eggs", "eggs (whole)"),
        
        # Dairy
        ("Greek-style yogurt", "greek yogurt (plain)"),
        ("plain Greek yogurt", "greek yogurt (plain)"),
        ("thick yogurt", "greek yogurt (plain)"),
        ("strained yogurt", "greek yogurt (plain)"),
        
        # Oils
        ("extra virgin olive oil", "olive oil"),
        ("cold pressed olive oil", "olive oil"),
        ("EVOO", "olive oil"),
        
        # Vegetables
        ("broccoli florets", "broccoli"),
        ("baby spinach", "spinach"),
        ("cherry tomatoes", "tomato"),
        ("roma tomatoes", "tomato"),
        ("red onions", "onions"),
        ("yellow bell peppers", "bell peppers"),
        
        # Protein powders
        ("chocolate whey protein", "whey protein powder"),
        ("vanilla protein powder", "whey protein powder"),
        ("plant protein blend", "pea protein powder"),  # Should classify as plant-based
        
        # Grains
        ("organic quinoa", "quinoa (dry)"),
        ("rolled oats", "oats (rolled, dry)"),
        ("brown rice", "brown rice (dry)"),
        
        # Legumes
        ("red lentils", "lentils (red, dry)"),
        ("garbanzo beans", "chickpeas (dry)"),
        ("canned chickpeas", "chickpeas (dry)"),  # Should normalize to dry
        
        # Nuts
        ("sliced almonds", "almonds"),
        ("chopped walnuts", "walnuts"),
        
        # Fruits
        ("fresh berries", "berries (mixed)"),
        ("mixed berries", "berries (mixed)"),
        ("organic bananas", "banana"),
    ]
    
    print("✅ SUCCESSFUL NORMALIZATIONS:")
    print("-" * 30)
    
    success_count = 0
    for raw_name, expected_canonical in test_cases:
        try:
            result = normalizer.normalize(raw_name)
            if result.canonical_name == expected_canonical:
                print(f"✅ '{raw_name}' -> '{result.canonical_name}' ({result.confidence.value})")
                if result.removed_tokens:
                    print(f"   Removed: {result.removed_tokens}")
                success_count += 1
            else:
                print(f"❌ '{raw_name}' -> '{result.canonical_name}' (expected '{expected_canonical}')")
        except UnknownIngredientError as e:
            print(f"❌ '{raw_name}' -> FAILED: {e}")
    
    print(f"\nSuccess rate: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    
    # Test cases that should fail (unknown ingredients)
    print("\n❌ EXPECTED FAILURES (Unknown Ingredients):")
    print("-" * 30)
    
    unknown_ingredients = [
        "mysterious superfood xyz",
        "brand new exotic fruit",
        "unknown protein source",
        "made up ingredient"
    ]
    
    failure_count = 0
    for unknown in unknown_ingredients:
        try:
            result = normalizer.normalize(unknown)
            print(f"⚠️ '{unknown}' -> '{result.canonical_name}' (should have failed!)")
        except UnknownIngredientError as e:
            print(f"✅ '{unknown}' -> CORRECTLY FAILED: {e.normalized_attempt}")
            failure_count += 1
    
    print(f"\nCorrect failures: {failure_count}/{len(unknown_ingredients)}")
    
    # Test transformation steps
    print("\n🔍 DETAILED TRANSFORMATION EXAMPLE:")
    print("-" * 30)
    
    try:
        result = normalizer.normalize("Silk Organic Free-Range Large Brown Eggs")
        print(f"Input: 'Silk Organic Free-Range Large Brown Eggs'")
        print(f"Output: '{result.canonical_name}' ({result.confidence.value})")
        print(f"Removed tokens: {result.removed_tokens}")
        print("Transformation steps:")
        for i, step in enumerate(result.transformation_steps, 1):
            print(f"  {i}. {step}")
    except UnknownIngredientError as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_ingredient_normalizer()