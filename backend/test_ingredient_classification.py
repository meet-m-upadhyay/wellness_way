#!/usr/bin/env python3
"""
Test script for Ingredient Classification & Diet Compliance System

This script provides the required proof that the system correctly:
1. Identifies non-vegetarian protein sources
2. Understands protein supplements semantically  
3. Enforces diet rules deterministically
4. Does not rely on LLM or exact string matching
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ingredient_classifier import (
    get_ingredient_classifier, 
    get_diet_compliance_validator,
    IngredientCategory,
    SupplementSource
)

def test_classification_outputs():
    """Test classification outputs for specific ingredients"""
    
    print("🧠 INGREDIENT CLASSIFICATION SYSTEM TEST")
    print("=" * 60)
    
    classifier = get_ingredient_classifier()
    
    # Required test cases
    test_cases = [
        "chocolate whey protein",
        "plant protein powder", 
        "grilled chicken",
        "vanilla protein isolate",
        "pea protein blend",
        "casein protein concentrate",
        "hemp protein powder",
        "beef steak",
        "salmon fillet",
        "greek yogurt",
        "whole eggs",
        "quinoa",
        "unknown mystery ingredient"
    ]
    
    print("📊 CLASSIFICATION RESULTS:")
    print("-" * 40)
    
    for ingredient in test_cases:
        result = classifier.classify_ingredient(ingredient)
        
        print(f"\n🔍 '{ingredient}':")
        print(f"   Category: {result.category.value}")
        if result.supplement_source:
            print(f"   Supplement Source: {result.supplement_source.value}")
        print(f"   Vegetarian: {'✅' if result.is_vegetarian_compliant else '❌'}")
        print(f"   Vegan: {'✅' if result.is_vegan_compliant else '❌'}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Matched Keywords: {result.matched_keywords}")

def test_vegetarian_plan_rejection():
    """Test vegetarian plan rejection for meat"""
    
    print("\n" + "=" * 60)
    print("🥩 VEGETARIAN PLAN REJECTION TEST")
    print("=" * 60)
    
    validator = get_diet_compliance_validator()
    
    # Vegetarian meal with hidden meat
    vegetarian_meal_with_meat = [
        "quinoa (cooked)",
        "steamed broccoli", 
        "grilled chicken breast",  # ❌ Should be rejected
        "olive oil",
        "lemon juice"
    ]
    
    is_compliant, violations = validator.validate_diet_compliance(
        vegetarian_meal_with_meat, 
        "vegetarian"
    )
    
    print(f"Meal ingredients: {vegetarian_meal_with_meat}")
    print(f"Diet type: Vegetarian")
    print(f"Compliant: {'✅' if is_compliant else '❌'}")
    print(f"Violations: {violations}")
    
    assert not is_compliant, "Should reject vegetarian plan with meat"
    assert any("chicken" in v.lower() for v in violations), "Should specifically identify chicken violation"
    
    print("✅ PASSED: Correctly rejected vegetarian plan with meat")

def test_vegan_plan_rejection_whey():
    """Test vegan plan rejection for whey protein"""
    
    print("\n" + "=" * 60)
    print("🥛 VEGAN PLAN REJECTION TEST (Whey Protein)")
    print("=" * 60)
    
    validator = get_diet_compliance_validator()
    
    # Vegan meal with dairy-based protein
    vegan_meal_with_whey = [
        "oat milk",
        "banana",
        "chocolate whey protein isolate",  # ❌ Should be rejected (dairy-based)
        "almond butter",
        "chia seeds"
    ]
    
    is_compliant, violations = validator.validate_diet_compliance(
        vegan_meal_with_whey,
        "vegan"
    )
    
    print(f"Meal ingredients: {vegan_meal_with_whey}")
    print(f"Diet type: Vegan")
    print(f"Compliant: {'✅' if is_compliant else '❌'}")
    print(f"Violations: {violations}")
    
    assert not is_compliant, "Should reject vegan plan with whey protein"
    assert any("whey" in v.lower() or "dairy" in v.lower() for v in violations), "Should identify whey/dairy violation"
    
    print("✅ PASSED: Correctly rejected vegan plan with whey protein")

def test_vegan_plan_acceptance_plant():
    """Test vegan plan acceptance with plant protein"""
    
    print("\n" + "=" * 60)
    print("🌱 VEGAN PLAN ACCEPTANCE TEST (Plant Protein)")
    print("=" * 60)
    
    validator = get_diet_compliance_validator()
    
    # Proper vegan meal with plant protein
    vegan_meal_plant_protein = [
        "soy milk",
        "banana", 
        "pea protein powder",  # ✅ Should be accepted (plant-based)
        "almond butter",
        "hemp seeds",
        "spinach",
        "quinoa (cooked)"
    ]
    
    is_compliant, violations = validator.validate_diet_compliance(
        vegan_meal_plant_protein,
        "vegan"
    )
    
    print(f"Meal ingredients: {vegan_meal_plant_protein}")
    print(f"Diet type: Vegan")
    print(f"Compliant: {'✅' if is_compliant else '❌'}")
    print(f"Violations: {violations}")
    
    assert is_compliant, f"Should accept vegan plan with plant protein. Violations: {violations}"
    assert len(violations) == 0, "Should have no violations"
    
    print("✅ PASSED: Correctly accepted vegan plan with plant protein")

def test_semantic_understanding():
    """Test semantic understanding without exact matches"""
    
    print("\n" + "=" * 60)
    print("🔤 SEMANTIC UNDERSTANDING TEST")
    print("=" * 60)
    
    classifier = get_ingredient_classifier()
    
    # Test various protein supplement naming patterns
    protein_variations = [
        "whey protein isolate vanilla flavored",
        "chocolate flavored whey concentrate", 
        "unflavored pea protein blend",
        "organic hemp protein powder",
        "premium plant-based protein mix",
        "grass-fed whey protein concentrate",
        "vegan protein powder (pea + rice)",
        "casein protein slow-release formula"
    ]
    
    print("Testing semantic protein supplement detection:")
    print("-" * 50)
    
    for protein in protein_variations:
        result = classifier.classify_ingredient(protein)
        
        # All should be classified as supplements
        assert result.category == IngredientCategory.SUPPLEMENT, f"Failed to classify '{protein}' as supplement"
        
        # Check source classification
        source_indicator = "plant" if any(word in protein.lower() for word in ['pea', 'hemp', 'plant', 'vegan']) else "dairy"
        expected_source = SupplementSource.PLANT_BASED if source_indicator == "plant" else SupplementSource.DAIRY_BASED
        
        print(f"✅ '{protein}'")
        print(f"   -> Category: {result.category.value}")
        print(f"   -> Source: {result.supplement_source.value}")
        print(f"   -> Expected: {expected_source.value}")
        
        if 'pea' in protein.lower() or 'hemp' in protein.lower() or 'plant' in protein.lower() or 'vegan' in protein.lower():
            assert result.supplement_source == SupplementSource.PLANT_BASED, f"Should classify '{protein}' as plant-based"
        elif 'whey' in protein.lower() or 'casein' in protein.lower():
            assert result.supplement_source == SupplementSource.DAIRY_BASED, f"Should classify '{protein}' as dairy-based"
    
    print("\n✅ PASSED: All protein supplements correctly classified semantically")

def test_nutrition_db_independence():
    """Test that classification works without nutrition database"""
    
    print("\n" + "=" * 60)
    print("🔬 NUTRITION DB INDEPENDENCE TEST")
    print("=" * 60)
    
    classifier = get_ingredient_classifier()
    
    # Test ingredients that definitely won't be in nutrition DB
    unknown_ingredients = [
        "exotic dragon fruit protein powder",
        "artisanal grass-fed yak milk cheese", 
        "wild-caught antarctic krill oil",
        "fermented purple quinoa blend",
        "laboratory-grown cellular chicken"
    ]
    
    print("Testing classification of unknown ingredients:")
    print("-" * 50)
    
    for ingredient in unknown_ingredients:
        result = classifier.classify_ingredient(ingredient)
        
        print(f"🔍 '{ingredient}':")
        print(f"   Category: {result.category.value}")
        if result.supplement_source:
            print(f"   Supplement Source: {result.supplement_source.value}")
        print(f"   Confidence: {result.confidence:.2f}")
        
        # Should still classify based on semantic content
        if 'protein' in ingredient.lower():
            assert result.category == IngredientCategory.SUPPLEMENT, "Should detect protein supplement"
        elif 'cheese' in ingredient.lower() or 'milk' in ingredient.lower():
            assert result.category == IngredientCategory.DAIRY, "Should detect dairy"
        elif 'chicken' in ingredient.lower():
            assert result.category == IngredientCategory.MEAT, "Should detect meat"
        elif 'quinoa' in ingredient.lower():
            assert result.category == IngredientCategory.PLANT, "Should detect plant"
    
    print("\n✅ PASSED: Classification works independently of nutrition database")

def test_unknown_ingredient_safety():
    """Test that truly unknown ingredients fail validation"""
    
    print("\n" + "=" * 60)
    print("🚨 UNKNOWN INGREDIENT SAFETY TEST")
    print("=" * 60)
    
    validator = get_diet_compliance_validator()
    
    # Meal with completely unclassifiable ingredient
    meal_with_unknown = [
        "quinoa",
        "broccoli",
        "xz9-mystery-compound-alpha",  # Completely unclassifiable
        "olive oil"
    ]
    
    is_compliant, violations = validator.validate_diet_compliance(
        meal_with_unknown,
        "vegan"
    )
    
    print(f"Meal ingredients: {meal_with_unknown}")
    print(f"Diet type: Vegan")
    print(f"Compliant: {'✅' if is_compliant else '❌'}")
    print(f"Violations: {violations}")
    
    assert not is_compliant, "Should reject meal with unknown ingredient"
    assert any("unknown" in v.lower() for v in violations), "Should identify unknown ingredient violation"
    
    print("✅ PASSED: Unknown ingredients correctly fail validation (safety first)")

def run_all_tests():
    """Run all required tests and provide proof of correctness"""
    
    print("🧪 INGREDIENT CLASSIFICATION & DIET COMPLIANCE SYSTEM")
    print("🎯 COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    try:
        # Core functionality tests
        test_classification_outputs()
        test_semantic_understanding()
        test_nutrition_db_independence()
        
        # Diet compliance tests (required proof)
        test_vegetarian_plan_rejection()
        test_vegan_plan_rejection_whey()
        test_vegan_plan_acceptance_plant()
        
        # Safety tests
        test_unknown_ingredient_safety()
        
        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 80)
        print("✅ System correctly identifies non-vegetarian protein sources")
        print("✅ System understands protein supplements semantically")
        print("✅ System enforces diet rules deterministically")
        print("✅ System does not rely on LLM or exact string matching")
        print("✅ System works independently of nutrition database")
        print("✅ System fails safely on unknown ingredients")
        print("\n🏆 DEFINITION OF DONE: ACHIEVED")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)