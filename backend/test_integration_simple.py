#!/usr/bin/env python3
"""Simple integration test for JSON guard"""

from app.services.llm_contract_enforcer import enforce_llm_contract, RetryableLLMError, LLMContractViolation

print('Testing JSON guard integration...')

# Test 1: Valid JSON
try:
    result = enforce_llm_contract('{"test": "valid"}', 'integration_test')
    print('✅ Valid JSON works')
except Exception as e:
    print(f'❌ Valid JSON failed: {e}')

# Test 2: Invalid JSON (should be retryable)
try:
    result = enforce_llm_contract('This is not JSON', 'integration_test')
    print('❌ Invalid JSON should have failed')
except RetryableLLMError:
    print('✅ Invalid JSON correctly classified as retryable')
except Exception as e:
    print(f'❌ Wrong exception: {e}')

print('JSON guard integration test complete!')