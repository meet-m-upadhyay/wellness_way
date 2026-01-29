# CRITICAL BUG: Zero Nutrition Values Despite Successful API Response

## PROBLEM DESCRIPTION

We're seeing zero nutrition values in meal plans even though the API returns 201 Created successfully. The logs show:

```
ERROR:app.services.plan_validation:[AGG DEBUG] nutrition field: {'calories': 0.0, 'protein': 0.0, 'carbohydrates': 0.0, 'fat': 0.0, 'fiber': 0.0, 'sodium': 0.0}
ERROR:app.services.plan_validation:[AGG DEBUG] ingredients[0]: [{'name': 'greek yogurt plain', 'quantity': 150, 'unit': 'g', 'original_quantity': 150.0, 'rounding_applied': True}]
ERROR:app.services.plan_validation:[AGG DEBUG] Case 1 (dict): 0.0 cal, 0.0 protein
ERROR:app.services.plan_validation:[AGG DEBUG] FINAL TOTALS: 0.0 cal, 0.0 protein
```

## ROOT CAUSE ANALYSIS

The issue appears to be ingredient name normalization. The logs show:
- `'greek yogurt plain'` (should be `'greek yogurt (plain)'`)
- `'tofu extrafirm'` (should be `'tofu (extra-firm)'`)
- `'lentils red dry'` (should be `'lentils (red, dry)'`)

These names don't match the exact database keys, causing nutrition lookup failures.

## EXPECTED BEHAVIOR

The system should:
1. Normalize ingredient names to exact database keys
2. Successfully look up nutrition data
3. Return meals with real nutrition values (not zeros)

## FILES TO ANALYZE

Please analyze these key files to identify the normalization issue:

### 1. Nutrition Database (Database Keys)
- `backend/app/services/nutrition_database.py` - Contains the exact database keys and normalization function

### 2. Ingredient Normalization Pipeline
- `backend/app/services/ingredient_normalizer.py` - Main normalization logic
- `backend/app/services/ingredient_canonicalizer.py` - Cooked-to-raw canonicalization
- `backend/app/services/ingredient_resolution_service.py` - Resolution service

### 3. Nutrition Engine (Where Lookup Happens)
- `backend/app/services/nutrition_engine.py` - Where ingredients get nutrition data

### 4. Plan Validation (Where Aggregation Happens)
- `backend/app/services/plan_validation.py` - Where meal nutrition is aggregated

### 5. Test Files (For Understanding Expected Behavior)
- `backend/test_nutrition_lookup_debug.py` - Shows working nutrition lookup
- `backend/test_complete_system.py` - Shows working end-to-end system

## SPECIFIC QUESTIONS

1. **Why are ingredient names not getting normalized to database keys?**
   - Is the normalization pipeline being bypassed?
   - Are the normalization mappings incomplete?

2. **Where in the pipeline are ingredient names getting corrupted?**
   - Are they correct after LLM generation?
   - Do they get corrupted during processing?

3. **Why is nutrition lookup failing silently?**
   - Should there be error logs for failed lookups?
   - Is the lookup function being called at all?

## DEBUGGING STEPS NEEDED

1. **Trace ingredient name transformation** through the entire pipeline
2. **Verify normalization mappings** are complete and correct
3. **Check if nutrition lookup is being called** for each ingredient
4. **Identify where the pipeline breaks** and names stop matching database keys

## SUCCESS CRITERIA

The fix should result in:
- Ingredient names matching exact database keys
- Successful nutrition lookups with real values
- Meals showing actual calories/protein (not zeros)
- Logs showing `[NUTRITION_LOOKUP_RESULT] calories=X.X protein=Y.Yg`

Please analyze the files and identify why ingredient name normalization is failing, causing zero nutrition values despite successful API responses.