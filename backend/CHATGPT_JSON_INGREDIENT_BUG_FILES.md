# Files to Share with ChatGPT for JSON & Ingredient Bug Fix

## CRITICAL FILES TO SHARE

### 1. LLM Contract Enforcer (JSON validation logic)
**File**: `backend/app/services/llm_contract_enforcer.py`
- Contains JSON parsing and repair logic
- Has the pre-validation guard that's catching the issues
- Needs enhancement to handle unterminated strings

### 2. AI Service (System prompt and ingredient validation)
**File**: `backend/app/services/ai_service.py`
- Contains the system prompt with JSON constraints (around line 240)
- Contains `_validate_ingredient_contract()` method (around line 694)
- Contains `_get_system_prompt()` method with JSON rules

### 3. Nutrition Database (Allowed ingredients)
**File**: `backend/app/services/nutrition_database.py`
- Contains `get_allowed_ingredients_prompt()` method (around line 458)
- Contains the actual food database with exact ingredient names
- Contains `validate_food_exists()` method
- Shows that database has "lentils (red, dry)" not "lentils (red, cooked)"

### 4. Error Logs (Debugging context)
**Error Log Sample**:
```
ERROR:app.services.llm_contract_enforcer:[LLM_JSON_ERROR] request_id=79de2c0b-8dc3-41a5-9b4b-4479432795f6 first_200_chars='{\n  "plan_type": "daily",\n  "date": "2024-01-26",\n  "breakfast": {\n    "name": "Greek Yogurt and Hemp Seed Bowl",\n    "ingredients": [\n      {"name": "greek yogurt (plain)", "quantity": 150, "unit": "'

WARNING:app.services.llm_contract_enforcer:[WARNING] Initial JSON parse failed (request_id: 79de2c0b-8dc3-41a5-9b4b-4479432795f6): Unterminated string starting at: line 31 column 21 (char 1208)

ERROR:app.services.ai_service:INGREDIENT CONTRACT VIOLATION (request_id: afbe5a86-79ea-4d1a-97c4-9a02608bcbe1): Unknown ingredients found: ['lentils (red, cooked)']
```

## SPECIFIC SECTIONS TO FOCUS ON

### In `llm_contract_enforcer.py`:
- `enforce_contract()` method - the main JSON validation
- `_repair_json()` method - needs to handle unterminated strings
- The JSON guard logic around line 60-70

### In `ai_service.py`:
- `_get_system_prompt()` method - needs stronger JSON constraints
- `_validate_ingredient_contract()` method - ingredient validation logic
- The JSON formatting rules around line 240-250

### In `nutrition_database.py`:
- `get_allowed_ingredients_prompt()` method - what ingredients are actually allowed
- The food database entries - check if "lentils (red, cooked)" should be added
- `validate_food_exists()` method - how ingredient validation works

## KEY QUESTIONS FOR CHATGPT

1. **JSON Issue**: How to enhance the JSON repair logic to handle unterminated strings at character 1208?

2. **Ingredient Issue**: Should we:
   - Add "lentils (red, cooked)" to the database?
   - Improve the allowed ingredients prompt to be clearer?
   - Add ingredient normalization before validation?

3. **System Prompt**: How to make the JSON constraints more explicit to prevent multi-line strings and unescaped quotes?

## EXPECTED SOLUTIONS

1. **Enhanced JSON repair logic** that can handle unterminated strings
2. **Improved system prompt** with explicit string formatting rules
3. **Fixed ingredient mapping** so LLM uses correct ingredient names
4. **Better error handling** for malformed JSON responses

## TESTING REQUIREMENTS

- Must handle the specific JSON that failed at character 1208
- Must accept "lentils (red, dry)" as a valid ingredient
- Must maintain all existing functionality
- Must preserve API stability (201 Created responses)