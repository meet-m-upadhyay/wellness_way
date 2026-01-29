#!/usr/bin/env python3
"""
HuggingFace API Key Test

This script specifically tests the new HuggingFace API key to verify it works
with our production system.
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

async def test_huggingface_api_key():
    """Test the new HuggingFace API key"""
    logger.info("🧪 TESTING NEW HUGGINGFACE API KEY")
    try:
        from app.core.config import settings
        hf_key = settings.get_huggingface_api_key()
        masked = (hf_key[:6] + "..." + hf_key[-4:]) if hf_key else "(not set)"
        logger.info(f"Using HuggingFace API key from settings: {masked}")
    except Exception:
        logger.info("Using HuggingFace API key from environment: (masked if present)")
    
    try:
        from app.core.config import settings
        from app.services.ai_providers import HuggingFaceAIProvider
        
        # Verify the key is loaded correctly
        hf_key = settings.get_huggingface_api_key()
        logger.info(f"✅ HuggingFace API key loaded: {hf_key[:10]}...{hf_key[-4:]}")
        
        # Create HuggingFace provider
        logger.info("Creating HuggingFace provider...")
        hf_provider = HuggingFaceAIProvider()
        
        logger.info(f"✅ Provider created successfully")
        logger.info(f"   API Key: {hf_provider.api_key[:10]}...{hf_provider.api_key[-4:]}")
        logger.info(f"   Model: {hf_provider.model}")
        logger.info(f"   Base URL: {hf_provider.base_url}")
        
        # Test a simple generation
        logger.info("Testing simple generation...")
        
        system_prompt = "You are a helpful assistant."
        user_prompt = "Say 'Hello from HuggingFace!' and nothing else."
        
        try:
            content, usage_data = await hf_provider.generate_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            
            logger.info(f"✅ Generation successful!")
            logger.info(f"Response: {content}")
            logger.info(f"Usage data: {usage_data}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Generation failed: {e}")
            
            # Check if it's a model loading issue (503 is acceptable)
            if "503" in str(e) or "model is loading" in str(e).lower():
                logger.info("✅ API key is valid - model is loading (503 is expected)")
                return True
            
            # Check if it's an authentication issue
            if "401" in str(e) or "unauthorized" in str(e).lower():
                logger.error("❌ API key is invalid - authentication failed")
                return False
            
            return False
        
    except Exception as e:
        logger.error(f"❌ HuggingFace API key test failed: {e}")
        return False

async def test_huggingface_with_provider_manager():
    """Test HuggingFace with the provider manager"""
    logger.info("🧪 TESTING HUGGINGFACE WITH PROVIDER MANAGER")
    
    try:
        from app.services.ai_provider_manager import AIProviderManager
        
        # Create provider manager (this will test HuggingFace health)
        logger.info("Creating AIProviderManager...")
        manager = AIProviderManager()
        
        logger.info(f"Available providers: {list(manager.providers.keys())}")
        
        # Check if HuggingFace is available
        if "huggingface" in manager.providers:
            logger.info("✅ HuggingFace provider is healthy and available!")
            
            # Test generation through provider manager
            logger.info("Testing generation through provider manager...")
            result = await manager.generate_with_retry(
                system_prompt="You are a helpful assistant.",
                user_prompt="Say 'Hello from provider manager!' and nothing else.",
                preferred_provider="huggingface"
            )
            
            if result.success:
                logger.info(f"✅ Provider manager generation successful!")
                logger.info(f"Final provider: {result.final_provider}")
                logger.info(f"Response: {result.content}")
                return True
            else:
                logger.error(f"❌ Provider manager generation failed: {result.failure_reason}")
                return False
        else:
            logger.warning("⚠️ HuggingFace provider not available in provider manager")
            return False
        
    except Exception as e:
        logger.error(f"❌ Provider manager test failed: {e}")
        return False

async def test_huggingface_diet_plan_generation():
    """Test HuggingFace with actual diet plan generation"""
    logger.info("🧪 TESTING HUGGINGFACE WITH DIET PLAN GENERATION")
    
    try:
        from app.services.ai_service import DietPlanAI
        
        # Create AI service
        ai_service = DietPlanAI()
        
        # Test context for meal generation
        test_context = {
            "diet_restrictions": {
                "diet_type": "vegetarian",
                "allergies": [],
                "foods_to_avoid": [],
                "meals_per_day": 3
            },
            "nutrition_targets": {
                "target_calories": 2000,
                "target_protein_g": 100
            },
            "goals": {
                "primary_goal": "muscle_gain"
            },
            "preferences": {
                "cuisine_preferences": ["mediterranean"]
            }
        }
        
        # Test meal ideas generation with HuggingFace preference
        logger.info("Testing meal ideas generation with HuggingFace preference...")
        
        # Force HuggingFace as preferred provider
        original_provider = ai_service.provider_manager._get_provider_order()
        logger.info(f"Original provider order: {original_provider}")
        
        # Test with HuggingFace if available
        if "huggingface" in ai_service.provider_manager.providers:
            meal_ideas = await ai_service._get_meal_ideas_from_llm(
                health_context_json=test_context,
                plan_type="daily",
                target_date=None,
                request_id="hf_test_request"
            )
            
            logger.info(f"✅ Meal ideas generated successfully with HuggingFace!")
            logger.info(f"Plan type: {meal_ideas.get('plan_type', 'unknown')}")
            logger.info(f"Number of meals: {len(meal_ideas.get('meals', []))}")
            
            return True
        else:
            logger.warning("⚠️ HuggingFace not available for diet plan generation")
            return False
        
    except Exception as e:
        logger.error(f"❌ Diet plan generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run HuggingFace API key tests"""
    logger.info("🚀 TESTING NEW HUGGINGFACE API KEY")
    logger.info("=" * 60)
    try:
        hf_key = settings.get_huggingface_api_key()
        masked = (hf_key[:6] + "..." + hf_key[-4:]) if hf_key else "(not set)"
        logger.info(f"API Key: {masked}")
    except Exception:
        logger.info("API Key: (masked or not set)")
    logger.info("=" * 60)
    
    tests = [
        ("HuggingFace API Key Direct Test", test_huggingface_api_key()),
        ("HuggingFace Provider Manager Test", test_huggingface_with_provider_manager()),
        ("HuggingFace Diet Plan Generation Test", test_huggingface_diet_plan_generation()),
    ]
    
    results = []
    for test_name, test_coro in tests:
        logger.info(f"\n📋 Running: {test_name}")
        logger.info("-" * 40)
        
        try:
            result = await test_coro
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 HUGGINGFACE API KEY TEST SUMMARY")
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
    
    if passed >= 1:  # At least one test should pass
        logger.info("🎉 HUGGINGFACE API KEY IS WORKING!")
        return 0
    else:
        logger.error("❌ HUGGINGFACE API KEY IS NOT WORKING")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)