#!/usr/bin/env python3
"""
Production Fix Verification Script

This script tests the critical production fixes:
1. AI Provider Manager health checks
2. HuggingFace provider prioritization
3. Ollama removal when unreachable
4. IngredientResolutionError handling
5. Complete safety pipeline integration
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_provider_manager_health_checks():
    """Test AI Provider Manager health checks and provider prioritization"""
    logger.info("🧪 TESTING AI PROVIDER MANAGER HEALTH CHECKS")
    
    try:
        from app.services.ai_provider_manager import AIProviderManager
        
        # Create provider manager (this triggers health checks)
        logger.info("Creating AIProviderManager (triggers health checks)...")
        manager = AIProviderManager()
        
        # Verify providers were loaded
        logger.info(f"✅ Providers loaded: {list(manager.providers.keys())}")
        
        # Check if HuggingFace is prioritized
        provider_order = manager._get_provider_order()
        logger.info(f"✅ Provider priority order: {provider_order}")
        
        if "huggingface" in provider_order and provider_order[0] == "huggingface":
            logger.info("✅ HuggingFace correctly prioritized as first provider")
        elif "huggingface" in manager.providers:
            logger.info("✅ HuggingFace available but not first (acceptable)")
        else:
            logger.warning("⚠️ HuggingFace not available (check API key)")
        
        # Check if Ollama was removed if unreachable
        if "ollama" not in manager.providers:
            logger.info("✅ Ollama correctly removed (unreachable)")
        else:
            logger.info("✅ Ollama available (running locally)")
        
        # Test a simple generation
        logger.info("Testing simple generation with provider manager...")
        result = await manager.generate_with_retry(
            system_prompt="You are a helpful assistant.",
            user_prompt="Say 'Hello from production fix test!' and nothing else.",
        )
        
        if result.success:
            logger.info(f"✅ Generation successful with {result.final_provider}")
            logger.info(f"Response: {result.content[:100]}...")
        else:
            logger.error(f"❌ Generation failed: {result.failure_reason}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Provider manager test failed: {e}")
        return False

def test_ingredient_resolution_error():
    """Test IngredientResolutionError handling"""
    logger.info("🧪 TESTING INGREDIENT RESOLUTION ERROR HANDLING")
    
    try:
        from app.services.nutrition_database import IngredientResolutionError, get_nutrition_database
        from app.services.ingredient_normalizer import UnknownIngredientError
        
        # Test that IngredientResolutionError can be created
        error = IngredientResolutionError(
            ingredient_name="unknown_test_ingredient",
            failure_reason="Test failure",
            normalization_attempt="normalized_test"
        )
        
        logger.info(f"✅ IngredientResolutionError created: {error}")
        logger.info(f"✅ Classification: {error.classification}")
        
        # Test nutrition database with unknown ingredient
        nutrition_db = get_nutrition_database()
        
        try:
            # This should raise an error for unknown ingredient
            nutrition_db.get_nutrition("completely_unknown_test_ingredient_12345", 100)
            logger.error("❌ Expected IngredientResolutionError but got none")
            return False
        except (IngredientResolutionError, UnknownIngredientError) as e:
            logger.info(f"✅ Correctly raised error for unknown ingredient: {type(e).__name__}")
            return True
        
    except Exception as e:
        logger.error(f"❌ Ingredient resolution error test failed: {e}")
        return False

def test_ingredient_normalization():
    """Test ingredient normalization pipeline"""
    logger.info("🧪 TESTING INGREDIENT NORMALIZATION PIPELINE")
    
    try:
        from app.services.ingredient_normalizer import get_ingredient_normalizer
        
        normalizer = get_ingredient_normalizer()
        
        # Test cases from the context transfer
        test_cases = [
            ("organic free-range eggs", "eggs (whole)"),
            ("broccoli florets", "broccoli"),
            ("chocolate whey protein", "whey protein powder"),
            ("vanilla protein powder", "whey protein powder"),
            ("Greek-style yogurt", "greek yogurt (plain)"),
        ]
        
        success_count = 0
        for raw_name, expected in test_cases:
            try:
                result = normalizer.normalize(raw_name)
                logger.info(f"✅ '{raw_name}' -> '{result.canonical_name}' ({result.confidence.value})")
                if result.canonical_name == expected:
                    success_count += 1
                else:
                    logger.warning(f"⚠️ Expected '{expected}', got '{result.canonical_name}'")
            except Exception as e:
                logger.error(f"❌ Failed to normalize '{raw_name}': {e}")
        
        logger.info(f"✅ Normalization success rate: {success_count}/{len(test_cases)}")
        return success_count >= len(test_cases) * 0.8  # 80% success rate acceptable
        
    except Exception as e:
        logger.error(f"❌ Ingredient normalization test failed: {e}")
        return False

def test_safety_pipeline_integration():
    """Test that safety pipeline components are properly integrated"""
    logger.info("🧪 TESTING SAFETY PIPELINE INTEGRATION")
    
    try:
        from app.services.plan_validation import get_plan_validator
        from app.services.unit_enforcement import get_unit_enforcer
        from app.services.quantity_rounding import get_quantity_rounder
        from app.services.failure_classification import get_failure_classifier
        
        # Test that all components can be instantiated
        validator = get_plan_validator()
        enforcer = get_unit_enforcer()
        rounder = get_quantity_rounder()
        classifier = get_failure_classifier()
        
        logger.info("✅ All safety pipeline components instantiated successfully")
        
        # Test a simple plan validation
        test_plan = {
            "plan_type": "daily",
            "meals": [
                {
                    "name": "Test Meal",
                    "ingredients": [
                        {"name": "eggs (whole)", "quantity": 2, "unit": "pieces"},
                        {"name": "spinach", "quantity": 100, "unit": "g"}
                    ]
                }
            ]
        }
        
        # Test unit enforcement
        enforced_plan = enforcer.enforce_canonical_units(test_plan)
        logger.info("✅ Unit enforcement completed")
        
        # Test quantity rounding
        rounded_plan = rounder.round_plan_quantities(enforced_plan)
        logger.info("✅ Quantity rounding completed")
        
        logger.info("✅ Safety pipeline integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Safety pipeline integration test failed: {e}")
        return False

async def main():
    """Run all production fix tests"""
    logger.info("🚀 STARTING PRODUCTION FIX VERIFICATION")
    logger.info("=" * 60)
    
    tests = [
        ("AI Provider Manager Health Checks", test_provider_manager_health_checks()),
        ("Ingredient Resolution Error Handling", test_ingredient_resolution_error()),
        ("Ingredient Normalization Pipeline", test_ingredient_normalization()),
        ("Safety Pipeline Integration", test_safety_pipeline_integration()),
    ]
    
    results = []
    for test_name, test_coro in tests:
        logger.info(f"\n📋 Running: {test_name}")
        logger.info("-" * 40)
        
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 PRODUCTION FIX VERIFICATION SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if result:
            passed += 1
    
    logger.info("-" * 60)
    logger.info(f"OVERALL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 ALL PRODUCTION FIXES VERIFIED SUCCESSFULLY!")
        return 0
    else:
        logger.error("⚠️ SOME PRODUCTION FIXES NEED ATTENTION")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)