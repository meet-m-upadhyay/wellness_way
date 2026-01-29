# Files to Share with ChatGPT for Calorie Density Fix Verification

## Core Files Modified

### 1. LLM Contract Enforcer (JSON Parsing Fix)
**File**: `backend/app/services/llm_contract_enforcer.py`
- Enhanced `_repair_json()` method with robust truncation handling
- Detects unterminated strings and removes incomplete elements
- Properly closes JSON structures

### 2. Plan Validation (Soft Acceptance Logic)
**File**: `backend/app/services/plan_validation.py`
- Implemented goal-aware validation with 90-95% acceptance buffers
- Added `create_balance_guidance()` for user-friendly suggestions
- Prevents infinite retry loops for nutritionally safe plans

### 3. AI Service (Calorie Density Rules)
**File**: `backend/app/services/ai_service.py`
- Enhanced system prompt with "CRITICAL MEAL ENERGY RULES"
- Explicit prohibition of protein-only meals
- Requirements for meals over 350 kcal
- Temperature adjustment for better variety

## Test Files (Verification)

### 4. Comprehensive Test Suite
**File**: `backend/test_complete_fixes.py`
- Tests JSON repair for malformed responses
- Tests soft acceptance logic
- Tests ingredient validation
- Tests complete meal plan JSON parsing

### 5. Soft Acceptance Test
**File**: `backend/test_soft_acceptance.py`
- Specific test for 90-95% acceptance rule
- Verifies advisory guidance generation

### 6. JSON Repair Test
**File**: `backend/test_json_repair.py`
- Tests specific "unterminated string" error handling
- Verifies repair logic works correctly

## Supporting Files

### 7. Nutrition Database
**File**: `backend/app/services/nutrition_database.py`
- Contains ingredient validation logic
- Provides allowed ingredients list for LLM

### 8. Nutrition Engine
**File**: `backend/app/services/nutrition_engine.py`
- Handles nutrition calculations
- Contains nutrition snapshot implementation

## Key Changes Summary

1. **JSON Repair**: Line-by-line analysis to detect and remove incomplete strings
2. **Soft Acceptance**: Accept plans within 90-95% of target with guidance
3. **Calorie Rules**: Enhanced LLM prompt with explicit energy requirements
4. **Temperature**: Increased from 0.2 to 0.4 for better meal variety

## Test Results
All tests pass:
- JSON repair: ✅ Handles unterminated strings
- Soft acceptance: ✅ Accepts 91.7% calorie plans with guidance  
- Ingredient validation: ✅ All known ingredients validated
- Complete flow: ✅ End-to-end meal plan generation works

The system now robustly handles malformed LLM responses and generates nutritionally balanced meal plans.