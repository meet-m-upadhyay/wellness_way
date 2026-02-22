# URGENT: Fix Zero-State Nutrition Aggregation Bug

## PROBLEM SUMMARY
The WellnessWay Diet Planner has a critical data aggregation bug causing infinite AI retry loops. Individual meals have correct nutrition, but daily totals aggregation returns (0, 0), triggering zero-state detection and preventing deterministic scaling.

## OBSERVED LOGS (PROOF OF BUG)
```
WARNING:app.services.nutrition_engine:[SAFETY] Low protein in Greek Yogurt and Hemp Seed Parfait: 22.0g < 33.18g
WARNING:app.services.nutrition_engine:[SAFETY] Low protein in Tofu and Quinoa Bowl: 28.5g < 33.18g  
WARNING:app.services.nutrition_engine:[SAFETY] Low protein in Lentil and Spinach Stew: 31.4g < 33.18g
ERROR:app.services.plan_validation:Could not calculate valid totals from meals
WARNING:app.services.plan_validation:FIXABLE: Meals exist with nutrition but totals extraction failed
WARNING:app.services.diet_plan_service:Fixable aggregation failure: ['Nutrition aggregation missing - fixable']
ERROR:app.services.nutrition_engine:[SCALING] Cannot scale zero-nutrition plan: 0 cal, 0g protein
ERROR:app.services.diet_plan_service:[ERROR] UNEXPECTED ERROR on attempt 1: 'is_active' is an invalid keyword argument for DietPlan
```

**ANALYSIS**: 
- ✅ Meals exist with valid nutrition (22.0g + 28.5g + 31.4g = ~82g protein)
- ✅ System correctly identifies as "fixable" (not retryable)
- ❌ Daily aggregation returns 0 calories, 0 protein in `_extract_daily_totals()`
- ❌ Scaling function receives 0 nutrition from `_extract_plan_totals()`
- ❌ Deterministic scaling fails due to zero input
- ❌ AI retries continue until token exhaustion

## ROOT CAUSE IDENTIFIED
**Data structure mismatch**: The aggregation functions are reading from the wrong meal nutrition structure. The debug logs show meals have nutrition, but both `_extract_daily_totals()` and `_extract_plan_totals()` return (0, 0).

## CRITICAL FUNCTIONS TO FIX

### 1. `_extract_daily_totals()` in `plan_validation.py` (Lines 654-676)
**Current Code**:
```python
def _extract_daily_totals(self, plan_data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    calories = 0.0
    protein = 0.0
    
    meals = plan_data.get("meals", [])
    if not meals:
        return None, None
    
    for meal in meals:
        nutrition = meal.get("nutrition")
        if not isinstance(nutrition, dict):
            continue
        
        calories += float(nutrition.get("calories") or 0)
        protein += float(nutrition.get("protein") or 0)
    
    if calories <= 0 or protein <= 0:
        logger.error("Could not calculate valid totals from meals")
        return None, None
    
    return calories, protein
```

**Problem**: This looks correct, but it's returning (0, 0). The issue might be:
- Meal nutrition is stored differently than expected
- The `nutrition.get("calories")` is returning None/0 when it shouldn't

### 2. `_extract_plan_totals()` in `nutrition_engine.py` (Lines 1010-1102)
**Current Code**: Similar structure-agnostic logic that should work but returns (0, 0)

### 3. Data Structure Investigation Needed
The debug logging shows meals have nutrition, but aggregation fails. Need to:
1. **Add debug logging** to see exact meal structure during aggregation
2. **Fix structure reading** to match actual data format
3. **Ensure consistent data shape** across the pipeline

## REQUIRED FIXES

### Fix 1: Add Debug Logging to Aggregation Functions
Add logging to see exactly what structure is being read:

```python
def _extract_daily_totals(self, plan_data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    # ADD DEBUG LOGGING
    logger.debug(f"[DEBUG] Extracting daily totals from plan with {len(plan_data.get('meals', []))} meals")
    
    for i, meal in enumerate(plan_data.get("meals", [])):
        logger.debug(f"[DEBUG] Meal {i}: {meal.get('name', 'unnamed')}")
        logger.debug(f"[DEBUG] Meal {i} nutrition keys: {list(meal.get('nutrition', {}).keys()) if meal.get('nutrition') else 'None'}")
        if meal.get('nutrition'):
            logger.debug(f"[DEBUG] Meal {i} calories: {meal.get('nutrition', {}).get('calories')}")
            logger.debug(f"[DEBUG] Meal {i} protein: {meal.get('nutrition', {}).get('protein')}")
```

### Fix 2: Structure-Agnostic Aggregation
Make aggregation more robust to handle different data formats:

```python
def _extract_daily_totals(self, plan_data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    calories = 0.0
    protein = 0.0
    
    meals = plan_data.get("meals", [])
    if not meals:
        return None, None
    
    for meal in meals:
        meal_calories = 0
        meal_protein = 0
        
        # Try multiple nutrition formats
        nutrition = meal.get("nutrition")
        if isinstance(nutrition, dict):
            meal_calories = float(nutrition.get("calories") or 0)
            meal_protein = float(nutrition.get("protein") or 0)
        
        # Fallback to legacy format
        if meal_calories == 0:
            meal_calories = float(meal.get("total_calories") or 0)
        if meal_protein == 0:
            meal_protein = float(meal.get("total_protein") or 0)
        
        # Fallback to ingredient-level calculation
        if meal_calories == 0 and meal.get("ingredients"):
            for ingredient in meal.get("ingredients", []):
                meal_calories += float(ingredient.get("calories") or 0)
                meal_protein += float(ingredient.get("protein") or 0)
        
        calories += meal_calories
        protein += meal_protein
    
    logger.debug(f"[DEBUG] Aggregated totals: {calories:.1f} cal, {protein:.1f}g protein")
    
    if calories <= 0 or protein <= 0:
        logger.error("Could not calculate valid totals from meals")
        return None, None
    
    return calories, protein
```

### Fix 3: Fix DietPlan Model Issue
The logs show `'is_active' is an invalid keyword argument for DietPlan`. This suggests a model schema mismatch.

## SUCCESS CRITERIA
After fixes, logs should show:
```
✅ [DEBUG] Aggregated totals: 1401.6 cal, 82.0g protein
✅ [SCALING] Current: 1401 cal, 82.0g protein
✅ [SCALING] Final: 1768 cal, 103g protein
✅ Plan accepted after deterministic scaling
```

And eliminate:
```
❌ Could not calculate valid totals from meals
❌ [SCALING] Cannot scale zero-nutrition plan: 0 cal, 0g protein
❌ 'is_active' is an invalid keyword argument for DietPlan
```

## FILES TO ANALYZE
1. `backend/app/services/plan_validation.py` - Fix `_extract_daily_totals()`
2. `backend/app/services/nutrition_engine.py` - Fix `_extract_plan_totals()`
3. `backend/app/services/diet_plan_service.py` - Fix DietPlan creation
4. `backend/app/models/diet_plan.py` - Check model schema

The core issue is a data structure mismatch in aggregation functions. Individual meals have nutrition, but the aggregation logic can't read it properly.