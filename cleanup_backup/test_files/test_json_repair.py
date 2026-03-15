#!/usr/bin/env python3
"""
Test JSON repair logic for the specific unterminated string error
"""

from app.services.llm_contract_enforcer import enforce_llm_contract, RetryableLLMError

def test_json_repair():
    # Test the specific malformed JSON from the error logs
    malformed_json = '''{\n  "plan_type": "daily",\n  "date": "2024-01-26",\n  "breakfast": {\n    "name": "Greek Yogurt and Hemp Seed Bowl",\n    "ingredients": [\n      {"name": "greek yogurt (plain)", "quantity": 150, "unit": "'''

    print('Original JSON length:', len(malformed_json))
    print('Last 50 chars:', repr(malformed_json[-50:]))

    try:
        # Use the actual contract enforcer which has the enhanced repair logic
        parsed = enforce_llm_contract(malformed_json, "test-request-id")
        print('✅ JSON repair successful!')
        print('Keys:', list(parsed.keys()))
        
        # Check the structure
        if 'breakfast' in parsed:
            breakfast = parsed['breakfast']
            print('Breakfast keys:', list(breakfast.keys()))
            if 'ingredients' in breakfast:
                ingredients = breakfast['ingredients']
                print(f'Number of ingredients: {len(ingredients)}')
                if ingredients:
                    print('First ingredient:', ingredients[0])
        
        return True
        
    except RetryableLLMError as e:
        print('❌ JSON repair failed (retryable):', e)
        return False
    except Exception as e:
        print('❌ JSON repair failed (other):', e)
        print('Error type:', type(e).__name__)
        return False

def test_complete_json():
    """Test that complete JSON still works"""
    complete_json = '''{
  "plan_type": "daily",
  "date": "2024-01-26",
  "breakfast": {
    "name": "Greek Yogurt Bowl",
    "ingredients": [
      {"name": "greek yogurt (plain)", "quantity": 150, "unit": "g"}
    ]
  }
}'''
    
    try:
        parsed = enforce_llm_contract(complete_json, "test-complete")
        print('✅ Complete JSON parsing successful!')
        return True
    except Exception as e:
        print('❌ Complete JSON parsing failed:', e)
        return False

if __name__ == "__main__":
    print("=== Testing malformed JSON repair ===")
    success1 = test_json_repair()
    
    print("\n=== Testing complete JSON parsing ===")
    success2 = test_complete_json()
    
    if not (success1 and success2):
        exit(1)