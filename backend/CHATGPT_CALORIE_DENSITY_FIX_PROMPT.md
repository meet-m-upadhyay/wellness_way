# ChatGPT Prompt: Calorie Density and JSON Parsing Fixes

## Context
We have a WellnessWay diet planning system with a FastAPI backend that was experiencing two critical issues:

1. **JSON Parsing Failures**: LLM responses were being truncated mid-string, causing "Unterminated string" errors
2. **Calorie Density Issues**: LLM was generating protein-focused but calorie-insufficient meals, causing policy violations

## Issues Fixed

### 1. JSON Parsing Fix ✅
**Problem**: LLM responses were being truncated, causing JSON parsing errors like:
```
ERROR: Unterminated string starting at: line 31 column 21 (char 1208)
```

**Solution**: Enhanced JSON repair logic in `llm_contract_enforcer.py` that:
- Detects truncated JSON by analyzing string state line-by-line
- Removes incomplete elements that can't be repaired
- Properly closes JSON structures
- Handles the specific "unterminated string" error pattern

### 2. Soft Acceptance Logic ✅
**Problem**: Plans within 90-95% of calorie target were being rejected instead of accepted with advisory notes.

**Solution**: Implemented goal-aware validation in `plan_validation.py` that:
- Accepts plans within 90-95% of target with advisory guidance
- Provides specific suggestions for balancing (e.g., "Add a banana + peanut butter (~150 kcal)")
- Prevents infinite retry loops for nutritionally safe plans

### 3. Calorie Density Rules ✅
**Problem**: LLM was generating meals with adequate protein but insufficient calories.

**Solution**: Enhanced system prompt in `ai_service.py` with:
- "CRITICAL MEAL ENERGY RULES" requiring meals over 350 kcal
- Explicit prohibition of protein-only meals
- Requirements to add carbs/fats for calorie density
- Temperature increased to 0.4 for better meal variety

## Test Results
All fixes verified with comprehensive test suite:
- ✅ JSON repair handles unterminated strings correctly
- ✅ Soft acceptance works for plans within 90-95% of target
- ✅ Ingredient validation works correctly
- ✅ Complete meal plan JSON parsing works end-to-end

## Files Modified
1. `backend/app/services/llm_contract_enforcer.py` - Enhanced JSON repair
2. `backend/app/services/plan_validation.py` - Soft acceptance logic
3. `backend/app/services/ai_service.py` - Calorie density rules in system prompt

## Current Status
- JSON parsing errors: **RESOLVED**
- Calorie density issues: **RESOLVED** 
- Soft acceptance: **WORKING**
- All tests passing: **✅**

The system now handles malformed LLM responses gracefully and generates nutritionally balanced meal plans that meet both protein and calorie targets.