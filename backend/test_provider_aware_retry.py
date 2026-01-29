#!/usr/bin/env python3
"""
Comprehensive test for provider-aware retry system with rate-limit safety.

This test demonstrates all retry behaviors:
1. Provider rotation on failures
2. Rate limit handling with exponential backoff
3. Contract violation immediate failure
4. Token budget guards
5. Structured failure responses
"""

import asyncio
import json
import logging
import time
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock the database and settings before importing our services
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock settings
class MockSettings:
    class AI:
        ai_provider = "groq"
        openai_model = "gpt-3.5-turbo"
        openai_max_tokens = 2000
        openai_temperature = 0.7
        openai_timeout = 30
        groq_model = "llama3-8b-8192"
        ollama_base_url = "http://localhost:11434"
        ollama_model = "llama3"
        huggingface_model = "microsoft/DialoGPT-medium"
    
    ai = AI()
    
    @staticmethod
    def get_openai_api_key():
        return "mock-openai-key"
    
    @staticmethod
    def get_groq_api_key():
        return "mock-groq-key"
    
    @staticmethod
    def get_huggingface_api_key():
        return "mock-hf-key"

# Patch settings
with patch('app.core.config.settings', MockSettings()):
    from app.services.ai_provider_manager import (
        AIProviderManager, FailureType, FailureClassifier, 
        TokenBudgetGuard, RetryResult, ProviderAttempt
    )
    from app.services.ai_providers import AIProvider


class TestAIProvider(AIProvider):
    """Test provider that can simulate different failure types"""
    
    def __init__(self, name: str, behavior: str = "success"):
        self.name = name
        self.behavior = behavior
        self.call_count = 0
    
    async def generate_completion(self, system_prompt: str, user_prompt: str):
        self.call_count += 1
        
        if self.behavior == "success":
            return json.dumps({
                "plan_type": "daily",
                "meals": [{"name": "Test Meal", "ingredients": []}]
            }), {"total_tokens": 100}
        
        elif self.behavior == "rate_limit":
            raise Exception("Rate limit exceeded. Try again in 60s")
        
        elif self.behavior == "timeout":
            raise Exception("Request timeout after 30 seconds")
        
        elif self.behavior == "contract_violation":
            raise Exception("Contract violation: forbidden nutrition field found")
        
        elif self.behavior == "api_error":
            raise Exception("API error: 500 Internal Server Error")
        
        elif self.behavior == "auth_error":
            raise Exception("Authentication failed: invalid API key")
        
        elif self.behavior == "network_error":
            raise Exception("Network error: connection refused")
        
        else:
            raise Exception(f"Unknown error from {self.name}")


async def test_failure_classification():
    """Test that failures are correctly classified"""
    print("\n🧪 Testing Failure Classification")
    
    classifier = FailureClassifier()
    
    test_cases = [
        ("Rate limit exceeded", FailureType.RATE_LIMIT),
        ("Request timeout", FailureType.TIMEOUT),
        ("Contract violation", FailureType.CONTRACT_VIOLATION),
        ("Authentication failed", FailureType.AUTHENTICATION),
        ("API error: 500", FailureType.API_ERROR),
        ("Network error", FailureType.NETWORK_ERROR),
        ("Something weird happened", FailureType.UNKNOWN)
    ]
    
    for error_msg, expected_type in test_cases:
        error = Exception(error_msg)
        classified = classifier.classify_error(error, "test_provider")
        assert classified == expected_type, f"Expected {expected_type}, got {classified}"
        print(f"✅ '{error_msg}' -> {classified.value}")
    
    print("✅ Failure classification test passed")


async def test_token_budget_guard():
    """Test token budget guard prevents rate limit failures"""
    print("\n🧪 Testing Token Budget Guard")
    
    guard = TokenBudgetGuard()
    
    # Test normal usage
    assert guard.can_attempt("groq", 1000) == True
    print("✅ Normal usage allowed")
    
    # Record usage
    guard.record_usage("groq", 5000)
    
    # Test near limit
    assert guard.can_attempt("groq", 500) == True
    print("✅ Near limit usage allowed")
    
    # Test over limit
    assert guard.can_attempt("groq", 2000) == False
    print("✅ Over limit usage blocked")
    
    # Test different provider
    assert guard.can_attempt("openai", 10000) == True
    print("✅ Different provider allowed")
    
    print("✅ Token budget guard test passed")


async def test_provider_rotation():
    """Test that providers are rotated on failures"""
    print("\n🧪 Testing Provider Rotation")
    
    # Create manager with test providers
    manager = AIProviderManager()
    
    # Replace with test providers and disable token guard for testing
    manager.providers = {
        "provider1": TestAIProvider("provider1", "rate_limit"),
        "provider2": TestAIProvider("provider2", "timeout"),
        "provider3": TestAIProvider("provider3", "success"),
        "mock": TestAIProvider("mock", "success")  # Add mock as fallback
    }
    
    # Override token guard to always allow attempts for testing
    original_can_attempt = manager.token_guard.can_attempt
    manager.token_guard.can_attempt = lambda provider, tokens: True
    
    try:
        result = await manager.generate_with_retry(
            system_prompt="Test system prompt",
            user_prompt="Test user prompt"
        )
        
        assert result.success == True
        assert result.final_provider == "provider3"
        assert len(result.attempts) == 3  # Should try all providers
        
        # Check that each provider was called once
        assert manager.providers["provider1"].call_count == 1
        assert manager.providers["provider2"].call_count == 1
        assert manager.providers["provider3"].call_count == 1
        
        print(f"✅ Provider rotation successful: {result.final_provider} succeeded after {len(result.attempts)} attempts")
    
    finally:
        # Restore original token guard
        manager.token_guard.can_attempt = original_can_attempt


async def test_contract_violation_no_retry():
    """Test that contract violations are not retried"""
    print("\n🧪 Testing Contract Violation No-Retry")
    
    manager = AIProviderManager()
    
    # All providers return contract violations
    manager.providers = {
        "provider1": TestAIProvider("provider1", "contract_violation"),
        "provider2": TestAIProvider("provider2", "contract_violation"),
        "mock": TestAIProvider("mock", "contract_violation")
    }
    
    # Override token guard for testing
    manager.token_guard.can_attempt = lambda provider, tokens: True
    
    result = await manager.generate_with_retry(
        system_prompt="Test system prompt",
        user_prompt="Test user prompt"
    )
    
    assert result.success == False
    assert len(result.attempts) == 1  # Should only try once
    assert "contract" in result.failure_reason.lower()
    
    print(f"✅ Contract violation correctly failed fast: {len(result.attempts)} attempt(s)")


async def test_rate_limit_backoff():
    """Test exponential backoff for rate limits"""
    print("\n🧪 Testing Rate Limit Exponential Backoff")
    
    manager = AIProviderManager()
    manager.max_attempts = 3  # Reduce for faster testing
    
    # Provider that rate limits then succeeds
    class RateLimitThenSuccessProvider(AIProvider):
        def __init__(self):
            self.call_count = 0
        
        async def generate_completion(self, system_prompt: str, user_prompt: str):
            self.call_count += 1
            if self.call_count <= 2:
                raise Exception("Rate limit exceeded")
            return '{"success": true}', {"total_tokens": 100}
    
    manager.providers = {
        "test_provider": RateLimitThenSuccessProvider(),
        "mock": TestAIProvider("mock", "success")
    }
    
    # Override token guard for testing
    manager.token_guard.can_attempt = lambda provider, tokens: True
    
    start_time = time.time()
    result = await manager.generate_with_retry(
        system_prompt="Test system prompt",
        user_prompt="Test user prompt"
    )
    end_time = time.time()
    
    assert result.success == True
    assert len(result.attempts) >= 2  # Should try at least twice
    
    # Should have taken some time due to backoff
    total_time = end_time - start_time
    assert total_time >= 0.5  # At least some time for backoff
    
    print(f"✅ Rate limit backoff successful: {len(result.attempts)} attempts in {total_time:.2f}s")


async def test_auth_error_no_retry():
    """Test that authentication errors are not retried"""
    print("\n🧪 Testing Authentication Error No-Retry")
    
    manager = AIProviderManager()
    
    manager.providers = {
        "provider1": TestAIProvider("provider1", "auth_error"),
        "mock": TestAIProvider("mock", "auth_error")
    }
    
    # Override token guard for testing
    manager.token_guard.can_attempt = lambda provider, tokens: True
    
    result = await manager.generate_with_retry(
        system_prompt="Test system prompt",
        user_prompt="Test user prompt"
    )
    
    assert result.success == False
    assert len(result.attempts) == 1  # Should only try once
    assert "auth" in result.failure_reason.lower() or "authentication" in result.failure_reason.lower()
    
    print(f"✅ Authentication error correctly failed fast: {len(result.attempts)} attempt(s)")


async def test_mixed_failure_recovery():
    """Test recovery from mixed failure types"""
    print("\n🧪 Testing Mixed Failure Recovery")
    
    manager = AIProviderManager()
    
    manager.providers = {
        "rate_limited": TestAIProvider("rate_limited", "rate_limit"),
        "timeout": TestAIProvider("timeout", "timeout"),
        "api_error": TestAIProvider("api_error", "api_error"),
        "success": TestAIProvider("success", "success"),
        "mock": TestAIProvider("mock", "success")
    }
    
    # Override token guard for testing
    manager.token_guard.can_attempt = lambda provider, tokens: True
    
    result = await manager.generate_with_retry(
        system_prompt="Test system prompt",
        user_prompt="Test user prompt"
    )
    
    assert result.success == True
    assert result.final_provider == "success"
    
    # Should have tried multiple providers
    assert len(result.attempts) >= 2
    
    print(f"✅ Mixed failure recovery successful: {result.final_provider} succeeded after {len(result.attempts)} attempts")


async def test_all_providers_fail():
    """Test behavior when all providers fail with retryable errors"""
    print("\n🧪 Testing All Providers Fail")
    
    manager = AIProviderManager()
    manager.max_attempts = 3  # Reduce for faster testing
    
    manager.providers = {
        "provider1": TestAIProvider("provider1", "rate_limit"),
        "provider2": TestAIProvider("provider2", "timeout"),
        "provider3": TestAIProvider("provider3", "api_error"),
        "mock": TestAIProvider("mock", "api_error")
    }
    
    # Override token guard for testing
    manager.token_guard.can_attempt = lambda provider, tokens: True
    
    result = await manager.generate_with_retry(
        system_prompt="Test system prompt",
        user_prompt="Test user prompt"
    )
    
    assert result.success == False
    assert len(result.attempts) == 3  # Should try max attempts
    assert "attempts failed" in result.failure_reason
    
    print(f"✅ All providers fail handled correctly: {len(result.attempts)} attempts")


async def test_preferred_provider():
    """Test that preferred provider is tried first"""
    print("\n🧪 Testing Preferred Provider Priority")
    
    manager = AIProviderManager()
    
    manager.providers = {
        "provider1": TestAIProvider("provider1", "success"),
        "provider2": TestAIProvider("provider2", "success"),
        "preferred": TestAIProvider("preferred", "success"),
        "mock": TestAIProvider("mock", "success")
    }
    
    # Override token guard for testing
    manager.token_guard.can_attempt = lambda provider, tokens: True
    
    result = await manager.generate_with_retry(
        system_prompt="Test system prompt",
        user_prompt="Test user prompt",
        preferred_provider="preferred"
    )
    
    assert result.success == True
    assert result.final_provider == "preferred"
    assert len(result.attempts) == 1
    
    # Only preferred provider should have been called
    assert manager.providers["preferred"].call_count == 1
    assert manager.providers["provider1"].call_count == 0
    assert manager.providers["provider2"].call_count == 0
    
    print(f"✅ Preferred provider used first: {result.final_provider}")


async def run_comprehensive_test():
    """Run all tests to demonstrate provider-aware retry system"""
    print("🚀 COMPREHENSIVE PROVIDER-AWARE RETRY SYSTEM TEST")
    print("=" * 60)
    
    try:
        await test_failure_classification()
        await test_token_budget_guard()
        await test_provider_rotation()
        await test_contract_violation_no_retry()
        await test_rate_limit_backoff()
        await test_auth_error_no_retry()
        await test_mixed_failure_recovery()
        await test_all_providers_fail()
        await test_preferred_provider()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED - PROVIDER-AWARE RETRY SYSTEM WORKING CORRECTLY")
        print("\n✅ Key Features Verified:")
        print("   • Intelligent failure classification")
        print("   • Provider rotation on failures")
        print("   • Rate limit exponential backoff")
        print("   • Contract violation immediate failure")
        print("   • Authentication error immediate failure")
        print("   • Token budget guards")
        print("   • Preferred provider priority")
        print("   • Structured failure responses")
        print("   • Mixed failure type recovery")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_test())
    exit(0 if success else 1)