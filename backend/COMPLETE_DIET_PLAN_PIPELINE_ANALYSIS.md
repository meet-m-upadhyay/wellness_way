# COMPLETE DIET PLAN PIPELINE ANALYSIS

## 🚨 CRITICAL ISSUE: AI Still Retrying After Meal Guardrails

Despite the previous fix, the system is still retrying AI after MEAL_GUARDRAIL violations. Here's the complete analysis:

## 1. FULL DIET PLAN PIPELINE (STAGES + OWNERSHIP)

### Stage 0: AI Generation
**Owner**: `ai_service.py`
**Input**: Health Context Document (HCD)
**Output**: Raw plan data (meal names, rough ingredients, no nutrition)
**Failure Types**: LLM contract violations, JSON errors

### Stage 1: Meal Processing with Safety
**Owner**: `diet_plan_service._process_meals_with_safety()`
**Input**: Raw plan data
**Output**: Plan with resolved ingredients and nutrition
**Critical Point**: **THIS IS WHERE MEAL GUARDRAILS TRIGGER**
**Failure Types**: 
- `RetryableMealGenerationError` (low_calories, low_protein) ← **PROBLEM HERE**
- `NutritionCalculationError` (unresolved ingredients)

### Stage 2: Unit Enforcement
**Owner**: `unit_enforcement.py`
**Input**: Plan with nutrition
**Output**: Plan with canonical units (g, scoops only)
**Failure Types**: `ContractViolationError`

### Stage 3: Quantity Rounding
**Owner**: `quantity_rounding.py`
**Input**: Plan with canonical units
**Output**: Plan with human-friendly quantities
**Failure Types**: None (always succeeds)

### Stage 4: Validation Gate with Scaling
**Owner**: `plan_validation.py`
**Input**: Rounded plan
**Output**: Validated plan (may be scaled)
**Scaling Function**: `scale_plan_quantities()` in `nutrition_engine.py`
**Failure Types**: `PlanValidationError`

## 2. RETRY CLASSIFICATION LOGIC (WHERE AI RETRIES ARE DECIDED)

### Location: `diet_plan_service.generate_daily_plan()` lines 259-341

```python
for attempt in range(1, self.max_generation_attempts + 1):
    try:
        # STEP 1: Generate raw plan using AI service
        raw_plan_data = await self.ai_service.generate_diet_plan(...)
        
        # STEP 2: Run through complete safety pipeline
        try:
            safe_plan_data = await self._run_safety_pipeline(...)
            # SUCCESS - return plan
            
        except (ContractViolationError, PlanValidationError) as e:
            # CRITICAL: Check for meal guardrail violations - NO AI RETRY
            if "meal_guardrail_" in str(e):
                # Apply scaling and return
            else:
                # Continue to next attempt - this is retryable
                continue  # ← AI RETRY HAPPENS HERE
```

### The Problem: Exception Conversion Chain

1. **Stage 1**: `create_meal_with_resolution()` raises `RetryableMealGenerationError`
2. **Stage 1**: `_process_daily_plan_meals()` catches it and converts to `PlanValidationError`
3. **Generation Loop**: Catches `PlanValidationError` and checks for "meal_guardrail_" string
4. **Issue**: The string check may not be working correctly

## 3. WHERE scale_plan_quantities() IS INVOKED

### Location 1: Plan Validation (Automatic)
**File**: `backend/app/services/plan_validation.py` line 466
```python
scaled_plan_data = scale_plan_quantities(
    plan_data=plan_data,
    target_calories=ranges.target_calories,
    target_protein=ranges.target_protein
)
```

### Location 2: Diet Plan Service (Manual Fallback)
**File**: `backend/app/services/diet_plan_service.py` line 1314
```python
scaled_plan = scale_plan_quantities(
    plan_data=plan_data,
    target_calories=target_calories,
    target_protein=target_protein
)
```

## 4. INVARIANT THAT BLOCKS AI AFTER MEAL CREATION

### Current Invariant (BROKEN)
**Location**: `diet_plan_service._run_safety_pipeline()` line 495
```python
# CRITICAL: Block AI fallback once meals exist (absolute rule)
if self._plan_has_meals_with_nutrition(plan_to_validate):
    disable_ai_retry = True
    logger.info(f"[AI_FALLBACK_BLOCKED] request_id={request_id} - Meals with nutrition detected")
```

**Problem**: This variable `disable_ai_retry` is set but **NEVER USED** to actually prevent retries.

### Required Fix: Enforce the Invariant
The invariant exists but is not enforced. We need to:
1. Check `disable_ai_retry` before allowing AI retry
2. Route meal guardrail violations directly to scaling
3. Prevent the retry loop from continuing

## 5. DIET-TYPE SPECIFIC GUARDRAIL THRESHOLDS

### Current Thresholds (UNIVERSAL - NO DIET TYPE VARIATION)
**File**: `backend/app/services/nutrition_engine.py` lines 410-422

```python
# MEAL CALORIE GUARDRAIL (Universal)
MIN_MEAL_CALORIES = max(200.0, target_protein_g * 8)  # Minimum 200 kcal per meal

# MEAL PROTEIN GUARDRAIL (Universal)  
MIN_MEAL_PROTEIN = 25.0  # Fixed 25g protein per meal
```

### Diet Type Support in System
**Supported Types**: `vegetarian`, `non_vegetarian`, `vegan`
**Location**: Throughout codebase, stored in HCD `json_context.diet_restrictions.diet_type`

### Recommended Diet-Specific Thresholds
```python
def get_diet_specific_thresholds(diet_type: str) -> Dict[str, float]:
    if diet_type == "vegan":
        return {
            "min_meal_calories": 180.0,  # Lower due to plant-based density
            "min_meal_protein": 20.0     # Lower due to plant protein availability
        }
    elif diet_type == "vegetarian":
        return {
            "min_meal_calories": 200.0,  # Standard
            "min_meal_protein": 22.0     # Slightly lower due to dairy/egg protein
        }
    else:  # non_vegetarian
        return {
            "min_meal_calories": 220.0,  # Higher due to meat density
            "min_meal_protein": 25.0     # Standard with meat protein
        }
```

## 6. ONE FULL REQUEST TRACE

### Hypothetical Request: Generate Daily Plan for Vegetarian User

```
1. API: POST /diet-plans/daily
   └── diet_plan_service.generate_daily_plan()

2. ATTEMPT 1:
   ├── ai_service.generate_diet_plan() → Raw plan with meal names
   ├── _run_safety_pipeline()
   │   ├── _process_meals_with_safety()
   │   │   ├── create_ingredient_with_resolution() → Meal: 150 kcal, 15g protein
   │   │   └── RetryableMealGenerationError("MEAL CALORIE GUARDRAIL VIOLATION: 150 < 200")
   │   └── Converts to PlanValidationError(violations=["meal_guardrail_low_calories"])
   └── Exception caught: "meal_guardrail_" detected → Apply scaling

3. SCALING ATTEMPT:
   ├── _apply_deterministic_scaling()
   ├── scale_plan_quantities() → Increases quantities by 10%
   ├── New meal: 165 kcal, 16.5g protein (still below thresholds)
   └── Scaling insufficient

4. FALLBACK: Continue to next attempt (AI RETRY) ← **PROBLEM**

5. ATTEMPT 2:
   ├── ai_service.generate_diet_plan() → Different raw plan
   ├── Same process repeats...
   └── Eventually exhausts 10 attempts → Terminal failure
```

## 7. ROOT CAUSE ANALYSIS

### The Real Problem: Exception Handling Chain
1. **Meal Creation**: `RetryableMealGenerationError` raised correctly
2. **Exception Conversion**: Converted to `PlanValidationError` correctly  
3. **String Detection**: `"meal_guardrail_"` detection works
4. **Scaling Attempt**: Scaling applied but insufficient
5. **Fallback Logic**: **BROKEN** - Falls back to AI retry instead of accepting scaled plan

### The Missing Piece: Soft Acceptance
The system needs to accept scaled plans even if they don't meet exact thresholds, rather than falling back to AI retry.

## 8. COMPLETE FIX REQUIRED

### Fix 1: Enforce AI Retry Invariant
```python
# In _run_safety_pipeline()
if disable_ai_retry and "meal_guardrail_" in str(e):
    # NEVER allow AI retry - force scaling acceptance
    return self._force_accept_with_scaling(plan_data, safety_constraints)
```

### Fix 2: Soft Acceptance After Scaling
```python
# In generation loop after scaling attempt
if scaling_error:
    # Accept scaled plan even if not perfect
    logger.info("Accepting scaled plan despite imperfections")
    return scaled_diet_plan
```

### Fix 3: Diet-Specific Thresholds
```python
# In create_meal_with_resolution()
diet_type = get_diet_type_from_context()
thresholds = get_diet_specific_thresholds(diet_type)
MIN_MEAL_CALORIES = thresholds["min_meal_calories"]
MIN_MEAL_PROTEIN = thresholds["min_meal_protein"]
```

## 9. VERIFICATION CHECKLIST

After implementing the complete fix:

✅ **Meal guardrail violation detected**
✅ **AI retry blocked (meal already exists)**  
✅ **Scaling applied (+10% quantities)**
✅ **Scaled plan accepted (even if imperfect)**
✅ **No AI service calls after meal creation**
✅ **Works for all diet types: veg, non-veg, vegan**

❌ **Should NEVER see**:
- `ai_service:Diet plan generation failed` after meal exists
- LLM retries after guardrails  
- TokenBudgetGuard after nutrition errors
- Multiple generation attempts for meal guardrail violations