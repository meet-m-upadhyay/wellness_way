# CRITICAL: LLM JSON Parsing & Ingredient Contract Violations

## PROBLEM STATEMENT

We have TWO critical issues in our diet planning system:

### Issue 1: JSON Parsing Failures
```
ERROR: Unterminated string starting at: line 31 column 21 (char 1208)
ERROR: JSON repair also failed: Expecting ',' delimiter: line 29 column 55 (char 1180)
```

**Root Cause**: LLM is generating JSON with:
- Unterminated strings (likely multi-line strings)
- Unescaped quotes in ingredient names or instructions
- Malformed JSON structure

### Issue 2: Ingredient Contract Violations
```
ERROR: INGREDIENT CONTRACT VIOLATION: Unknown ingredients found: ['lentils (red, cooked)']
```

**Root Cause**: LLM is using ingredient names that don't exist in our nutrition database:
- Database has: `"lentils (red, dry)"`
- LLM generated: `"lentils (red, cooked)"`

## CURRENT SYSTEM ARCHITECTURE

1. **LLM Contract Enforcer** (`llm_contract_enforcer.py`):
   - Pre-validates JSON format
   - Checks for forbidden nutrition fields
   - Has JSON repair logic but it's failing

2. **AI Service** (`ai_service.py`):
   - Contains system prompt with JSON constraints
   - Validates ingredient contract against nutrition database
   - Uses allowed ingredients list from nutrition database

3. **Nutrition Database** (`nutrition_database.py`):
   - Contains exact ingredient names that are allowed
   - Generates allowed ingredients prompt for LLM
   - Has `validate_food_exists()` method

## REQUIRED FIXES

### Fix 1: Strengthen JSON Generation Constraints
- Enhance system prompt to be more explicit about string formatting
- Add specific rules about escaping quotes and avoiding multi-line strings
- Improve JSON repair logic to handle unterminated strings

### Fix 2: Fix Ingredient Name Mapping
- The database has "lentils (red, dry)" but LLM is generating "lentils (red, cooked)"
- Need to either:
  - Add "lentils (red, cooked)" to the database, OR
  - Fix the allowed ingredients prompt to be clearer about exact names, OR
  - Add ingredient name normalization before validation

## CRITICAL CONSTRAINTS

- **DO NOT BREAK**: Existing nutrition calculations, API contracts, validation logic
- **PRESERVE**: All existing functionality and error handling
- **MAINTAIN**: API stability (must still return 201 Created for valid requests)

## SUCCESS CRITERIA

1. ✅ No more "Unterminated string" JSON parsing errors
2. ✅ No more ingredient contract violations for common ingredients like lentils
3. ✅ System gracefully handles malformed JSON with proper retries
4. ✅ LLM consistently uses correct ingredient names from database

## FILES TO ANALYZE

See `CHATGPT_JSON_INGREDIENT_BUG_FILES.md` for the complete file contents needed to understand and fix these issues.

## DEBUGGING INFO

**Request ID with JSON issue**: `79de2c0b-8dc3-41a5-9b4b-4479432795f6`
**Request ID with ingredient issue**: `afbe5a86-79ea-4d1a-97c4-9a02608bcbe1`

The JSON starts correctly but fails around character 1208, suggesting the issue is in the middle of the response, likely in ingredient instructions or meal names.