# Files to Share with ChatGPT for Zero Nutrition Debug

## CRITICAL FILES (Share These First)

### 1. Nutrition Database & Normalization
```
backend/app/services/nutrition_database.py
```
- Contains exact database keys and `normalize_ingredient_name_for_lookup()` function
- Shows what ingredient names should look like

### 2. Ingredient Normalization Pipeline
```
backend/app/services/ingredient_normalizer.py
backend/app/services/ingredient_canonicalizer.py
backend/app/services/ingredient_resolution_service.py
```
- Main normalization logic that should convert names to database keys
- Pipeline that processes ingredient names

### 3. Nutrition Engine
```
backend/app/services/nutrition_engine.py
```
- Where nutrition lookup happens
- Should call nutrition database with normalized names

### 4. Plan Validation
```
backend/app/services/plan_validation.py
```
- Where meal nutrition aggregation happens
- Shows the debug logs we're seeing

## WORKING EXAMPLES (For Comparison)

### 5. Test Files That Work
```
backend/test_nutrition_lookup_debug.py
backend/test_complete_system.py
backend/FINAL_CORRECTNESS_FIXES_COMPLETION_REPORT.md
```
- Shows working nutrition lookup examples
- Demonstrates expected behavior

## PROBLEM DESCRIPTION FILE

### 6. Debug Prompt
```
backend/CHATGPT_ZERO_NUTRITION_DEBUG_PROMPT.md
```
- Detailed problem description
- Root cause analysis
- Expected vs actual behavior

## HOW TO USE THESE FILES

1. **Start with the problem description** (`CHATGPT_ZERO_NUTRITION_DEBUG_PROMPT.md`)
2. **Share the nutrition database** to see exact key formats
3. **Share the normalization pipeline** to see where names should be converted
4. **Share the nutrition engine** to see where lookup happens
5. **Share working examples** to compare expected behavior

## KEY QUESTIONS FOR CHATGPT

1. **Why are ingredient names like `'greek yogurt plain'` not being normalized to `'greek yogurt (plain)'`?**

2. **Where in the pipeline is the normalization failing?**

3. **Is the `normalize_ingredient_name_for_lookup()` function being called?**

4. **Are the normalization mappings complete for all ingredients?**

5. **Why is nutrition lookup failing silently instead of logging errors?**

## EXPECTED OUTCOME

ChatGPT should identify:
- Where the normalization pipeline is breaking
- Why ingredient names don't match database keys
- How to fix the name mapping issue
- Why nutrition lookup is returning zeros instead of real values

The fix should result in logs showing:
```
[NUTRITION_LOOKUP_INPUT] name='greek yogurt (plain)' qty=150 unit=g
[NUTRITION_LOOKUP_RESULT] calories=88.5 protein=15.0g
```

Instead of:
```
[AGG DEBUG] nutrition field: {'calories': 0.0, 'protein': 0.0, ...}
```