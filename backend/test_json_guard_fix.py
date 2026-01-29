#!/usr/bin/env python3
"""
Test JSON Guard Fix - Verify LLM JSON formatting constraints work

This test verifies that the JSON guard prevents terminal failures from malformed LLM responses.

PROBLEM BEING FIXED:
- LLM sometimes emits invalid JSON (unescaped quotes, comments, multi-line strings)
- This causes terminal failures instead of retries
- API crashes instead of graceful error handling

SOLUTION IMPLEMENTED:
1. Explicit JSON hard-constraint in system prompt
2. Pre-validation JSON guard (checks if response starts with "{")
3. Proper error classification (RetryableLLMError vs LLMContractViolation)
4. Enhanced logging for debugging

SUCCESS CRITERIA:
✅ Invalid JSON responses are caught immediately
✅ Retry happens cleanly (no terminal failures)
✅ API stability is preserved
✅ Proper error logging for debugging
"""

import logging
from app.services.llm_contract_enforcer import enforce_llm_contract, LLMContractViolation, RetryableLLMError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


def test_json_guard_fix():
    """Test the JSON guard fix for malformed LLM responses"""
    
    print("TESTING JSON GUARD FIX")
    print("=" * 50)
    print("PROBLEM: LLM emits invalid JSON causing terminal failures")
    print("SOLUTION: JSON guard + proper error classification")
    print("=" * 50)
    
    # Test 1: Valid JSON (should pass)
    print("\n1. VALID JSON TEST")
    valid_json = '{"plan_type": "daily", "breakfast": {"name": "Test Meal"}}'
    
    try:
        result = enforce_llm_contract(valid_json, "test_valid")
        print("✅ Valid JSON passed contract enforcement")
        print(f"   Result: {result}")
    except Exception as e:
        print(f"❌ Valid JSON failed: {e}")
        return False
    
    # Test 2: Non-JSON response (should raise RetryableLLMError)
    print("\n2. NON-JSON RESPONSE TEST")
    non_json_response = "I'll help you create a meal plan. Here's what I suggest..."
    
    try:
        result = enforce_llm_contract(non_json_response, "test_non_json")
        print("❌ Non-JSON response should have been rejected")
        return False
    except RetryableLLMError as e:
        print("✅ Non-JSON response correctly caught as retryable error")
        print(f"   Error: {e}")
    except Exception as e:
        print(f"❌ Wrong exception type: {type(e).__name__}: {e}")
        return False
    
    # Test 3: Malformed JSON (should raise RetryableLLMError)
    print("\n3. MALFORMED JSON TEST")
    malformed_json = '{"plan_type": "daily", "breakfast": {"name": "Test Meal"'  # Missing closing braces
    
    try:
        result = enforce_llm_contract(malformed_json, "test_malformed")
        print("❌ Malformed JSON should have been rejected")
        return False
    except RetryableLLMError as e:
        print("✅ Malformed JSON correctly caught as retryable error")
        print(f"   Error: {e}")
    except Exception as e:
        print(f"❌ Wrong exception type: {type(e).__name__}: {e}")
        return False
    
    # Test 4: JSON with forbidden fields (should raise LLMContractViolation)
    print("\n4. CONTRACT VIOLATION TEST")
    violation_json = '{"plan_type": "daily", "breakfast": {"name": "Test", "nutrition": {"calories": 300}}}'
    
    try:
        result = enforce_llm_contract(violation_json, "test_violation")
        print("❌ Contract violation should have been caught")
        return False
    except LLMContractViolation as e:
        print("✅ Contract violation correctly caught")
        print(f"   Error: {e.message}")
        print(f"   Forbidden fields: {e.forbidden_fields}")
    except Exception as e:
        print(f"❌ Wrong exception type: {type(e).__name__}: {e}")
        return False
    
    # Test 5: JSON with comments (should raise RetryableLLMError)
    print("\n5. JSON WITH COMMENTS TEST")
    json_with_comments = '''
    {
        // This is a comment
        "plan_type": "daily",
        "breakfast": {
            "name": "Test Meal" // Another comment
        }
    }
    '''
    
    try:
        result = enforce_llm_contract(json_with_comments, "test_comments")
        print("❌ JSON with comments should have been rejected")
        return False
    except RetryableLLMError as e:
        print("✅ JSON with comments correctly caught as retryable error")
        print(f"   Error: {e}")
    except Exception as e:
        print(f"❌ Wrong exception type: {type(e).__name__}: {e}")
        return False
    
    # Test 6: Markdown wrapped JSON (should raise RetryableLLMError)
    print("\n6. MARKDOWN WRAPPED JSON TEST")
    markdown_json = '''
    Here's the meal plan you requested:
    
    ```json
    {"plan_type": "daily", "breakfast": {"name": "Test Meal"}}
    ```
    
    I hope this helps!
    '''
    
    try:
        result = enforce_llm_contract(markdown_json, "test_markdown")
        print("❌ Markdown wrapped JSON should have been rejected")
        return False
    except RetryableLLMError as e:
        print("✅ Markdown wrapped JSON correctly caught as retryable error")
        print(f"   Error: {e}")
    except Exception as e:
        print(f"❌ Wrong exception type: {type(e).__name__}: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("JSON GUARD FIX TEST RESULTS")
    print("=" * 50)
    print("✅ All tests passed!")
    print("")
    print("KEY IMPROVEMENTS:")
    print("- Non-JSON responses caught immediately")
    print("- Malformed JSON classified as retryable")
    print("- Contract violations still caught properly")
    print("- Enhanced logging for debugging")
    print("- API stability preserved")
    print("")
    print("EXPECTED BEHAVIOR:")
    print("- RetryableLLMError → Retry with different provider")
    print("- LLMContractViolation → Terminal failure (don't retry)")
    print("- Enhanced logging helps debug JSON issues")
    
    return True


if __name__ == "__main__":
    success = test_json_guard_fix()
    if not success:
        exit(1)
    print("\n🎯 JSON GUARD FIX VERIFICATION COMPLETE")