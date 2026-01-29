# Files to Share with ChatGPT for Diet Plan Generation Issue

## Core Files (MUST INCLUDE)

### 1. Main Diet Plan Service
- **File**: `backend/app/services/diet_plan_service.py`
- **Purpose**: Main orchestrator for diet plan generation with self-healing loop
- **Key Functions**: `generate_weekly_plan()`, `generate_daily_plan()`, `_run_safety_pipeline()`

### 2. Nutrition Engine
- **File**: `backend/app/services/nutrition_engine.py`
- **Purpose**: Backend nutrition calculations and meal processing
- **Key Functions**: `create_ingredient_with_resolution()`, `validate_plan_nutrition()`

### 3. AI Service Integration
- **File**: `backend/app/services/ai_service.py`
- **Purpose**: LLM integration for meal generation
- **Key Functions**: `generate_diet_plan()`, AI provider management

### 4. Ingredient Resolution Service
- **File**: `backend/app/services/ingredient_resolution_service.py`
- **Purpose**: 9-step ingredient resolution pipeline
- **Key Functions**: `resolve_ingredient()`, offline AI queuing

### 5. Safety Pipeline Components
- **File**: `backend/app/services/plan_validation.py`
- **Purpose**: Plan validation and safety constraints
- **File**: `backend/app/services/unit_enforcement.py`
- **Purpose**: Unit enforcement and canonicalization
- **File**: `backend/app/services/quantity_rounding.py`
- **Purpose**: Human-friendly portion rounding

## Test Files (RECOMMENDED)

### 6. Production Safety Test
- **File**: `backend/test_production_safety_floor.py`
- **Purpose**: Verifies all 6 production safety measures work
- **Status**: ✅ ALL TESTS PASSING

### 7. Ingredient Pipeline Test
- **File**: `backend/test_mandatory_ingredient_pipeline.py`
- **Purpose**: Verifies all 9 mandatory pipeline steps work
- **Status**: ✅ ALL TESTS PASSING

### 8. Complete System Test
- **File**: `backend/test_complete_system.py`
- **Purpose**: End-to-end system testing including plan generation
- **Status**: ❓ May show the actual failure

## Supporting Files (IF NEEDED)

### 9. Nutrition Database
- **File**: `backend/app/services/nutrition_database.py`
- **Purpose**: Authoritative nutrition data source
- **Status**: ✅ WORKING - 102+ foods with accurate data

### 10. AI Provider Manager
- **File**: `backend/app/services/ai_provider_manager.py`
- **Purpose**: Multi-provider AI management with retry logic
- **Status**: ✅ WORKING - Groq, HuggingFace providers healthy

### 11. Error Classification
- **File**: `backend/app/services/failure_classification.py`
- **Purpose**: Classifies generation failures and provides user guidance
- **Status**: ✅ WORKING - Provides actionable error messages

### 12. API Endpoints
- **File**: `backend/app/api/endpoints/diet_plans.py`
- **Purpose**: REST API endpoints for plan generation
- **Status**: ❓ May show HTTP-level errors

## Completion Reports (CONTEXT)

### 13. Production Safety Report
- **File**: `backend/PRODUCTION_SAFETY_FLOOR_COMPLETION_REPORT.md`
- **Purpose**: Documents all implemented safety measures
- **Status**: ✅ COMPLETE - 6/6 safety measures verified

### 14. Ingredient Pipeline Report
- **File**: `backend/MANDATORY_INGREDIENT_PIPELINE_COMPLETION_REPORT.md`
- **Purpose**: Documents the 9-step ingredient resolution architecture
- **Status**: ✅ COMPLETE - 8/8 pipeline steps verified

## How to Use These Files

### Step 1: Start with Core Files (1-5)
These contain the main logic and are most likely where the issue exists.

### Step 2: Check Test Files (6-8)
These will show you what's expected to work vs. what's actually failing.

### Step 3: Reference Supporting Files (9-12) if needed
These provide context about the underlying components.

### Step 4: Review Completion Reports (13-14)
These show what has been verified to work at the component level.

## Key Questions to Answer

1. **Where is the failure occurring?**
   - In the AI service generation?
   - In the safety pipeline processing?
   - In the nutrition calculations?
   - In the database operations?

2. **What specific error is being thrown?**
   - Look for exception traces in the code
   - Check error handling in the self-healing loop
   - Identify if it's a known error type

3. **Is it a component failure or integration failure?**
   - Individual components are verified to work
   - Issue is likely in how they're connected

4. **How can we fix it while maintaining safety?**
   - All existing safety measures must remain
   - Fix should not break the verified architecture

## Expected Debugging Process

1. **Trace the execution flow** through `generate_daily_plan()` or `generate_weekly_plan()`
2. **Identify where exceptions are thrown** in the self-healing loop
3. **Check if safety pipeline components are being called correctly**
4. **Verify AI service integration is working properly**
5. **Ensure database operations are successful**
6. **Test the fix with existing test framework**

---

**Priority**: Focus on files 1-5 first, then use 6-8 to understand the failure pattern.