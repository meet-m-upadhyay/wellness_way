# CRITICAL: Zero Nutrition Aggregation Bug - API Format Conversion Issue

## PROBLEM STATEMENT

**CRITICAL ISSUE**: Meals are being created successfully with proper nutrition data internally, but when converted to API format, the **meal-level nutrition becomes 0** for all fields.

### Key Evidence from Logs:
```
WARNING: [SAFETY] Low protein in Greek Yogurt and Hemp Seed Delight: 22.0g < 33.18g
```
**↑ This shows meals HAVE nutrition data internally (22g protein)**

```
ERROR: [AGG DEBUG] nutrition field: {'calories': 0.0, 'protein': 0.0, 'carbohydrates': 0.0, 'fat': 0.0, 'fiber': 0.0, 'sodium': 0.0}
ERROR: [AGG DEBUG] Case 1 (dict): 0.0 cal, 0.0 protein
ERROR: [AGG DEBUG] FINAL TOTALS: 0.0 cal, 0.0 protein
```
**↑ But API format has 0 nutrition for the same meals**

## ROOT CAUSE IDENTIFIED

### The Issue: API Format Conversion Losing Nutrition Data

**CONFIRMED**: The problem is in `_convert_day_plan_to_api_format()` method in `ai_service.py`.

1. ✅ **Internal Meal Objects**: Have real nutrition data (`meal.nutrition.calories = 150`, `meal.nutrition.protein = 15`)
2. ❌ **API Format Conversion**: Converts to `{"calories": 0.0, "protein": 0.0, ...}`
3. ❌ **Plan Validation**: Receives API format with 0 nutrition → Aggregation fails

### Evidence from Reproduction Test:
```python
# API format structure received by plan validation:
"nutrition": {
    "calories": 0.0,  # ← Should be ~150 but shows 0
    "protein": 0.0,   # ← Should be ~15 but shows 0
    "carbohydrates": 0.0,
    "fat": 0.0,
    "fiber": 0.0,
    "sodium": 0.0
}
```

## THE EXACT BUG LOCATION

**File**: `backend/app/services/ai_service.py`  
**Method**: `_convert_day_plan_to_api_format()` (around line 853-890)

**Problematic Code**:
```python
"nutrition": {
    "calories": round(meal.nutrition.calories, 1),  # ← This is evaluating to 0
    "protein": round(meal.nutrition.protein, 1),    # ← This is evaluating to 0
    # ...
}
```

### Why This Is Happening:
1. **Meal Creation**: `meal.nutrition` property calculates nutrition correctly
2. **API Conversion**: `meal.nutrition.calories` somehow returns 0 instead of real value
3. **Possible Causes**:
   - `meal.nutrition` property not working correctly in API conversion context
   - Ingredient names mismatch causing nutrition calculation to fail
   - Serialization issue where NutritionData becomes empty

## CRITICAL ARCHITECTURE ISSUE

This is **NOT** the same bug we fixed before. This is a **different layer**:

- **Previous fix**: Fixed ingredient normalization in database lookup
- **Current issue**: API format conversion is getting 0 from `meal.nutrition` property

## REQUIRED INVESTIGATION

### 1. Debug Meal.nutrition Property
**Question**: Why does `meal.nutrition.calories` return 0 in API conversion?
- Check if `meal.ingredients` have nutrition data attached
- Verify the `@property nutrition` calculation in `Meal` class
- Test if ingredient names are causing lookup failures

### 2. Trace Ingredient Data Flow
**Question**: What ingredient names/nutrition are stored in meal objects?
- Check `meal.ingredients[0].name` (canonical vs original)
- Check `meal.ingredients[0].nutrition` (should have NutritionData)
- Verify ingredient resolution is working in meal creation

### 3. Test Meal Property Calculation
**Question**: Is the `Meal.nutrition` property calculation broken?
- Test `meal.nutrition` directly on created meal objects
- Check if ingredients are missing nutrition data
- Verify the aggregation logic in `Meal` class

## SUCCESS CRITERIA

After fixing this issue:
1. ✅ `meal.nutrition.calories` should return **real values** in API conversion
2. ✅ API format should show **actual nutrition data** instead of 0s
3. ✅ Plan validation should receive **meaningful nutrition** for aggregation
4. ✅ `[AGG DEBUG] FINAL TOTALS` should show actual calories/protein

## CONSTRAINTS

- **DO NOT BREAK**: Existing meal creation logic
- **DO NOT CHANGE**: Plan validation aggregation logic
- **PRESERVE**: All current functionality  
- **FIX ONLY**: The API format conversion nutrition calculation

## DEBUGGING STRATEGY

1. **Add logging** in `_convert_day_plan_to_api_format()` to see what `meal.nutrition` returns
2. **Test meal.nutrition property** directly on meal objects before API conversion
3. **Check ingredient data** to see if nutrition is attached to ingredients
4. **Identify why** `meal.nutrition.calories` evaluates to 0

## THE SMOKING GUN

**Reproduction Test Confirms**: The exact same structure from the logs can be reproduced, showing that:
- Plan validation logic is working correctly
- The issue is that it receives 0 nutrition data from API format conversion
- The bug is in `_convert_day_plan_to_api_format()` where `meal.nutrition` returns 0

This is a **meal property calculation bug** in the API conversion layer, not an aggregation bug.