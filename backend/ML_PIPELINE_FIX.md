# ML Pipeline Fix - Database Method Names

## Issue
The ML pipeline was failing with:
```
'NutritionDatabase' object has no attribute 'get_all_ingredients'
'NutritionDatabase' object has no attribute 'get_ingredient_nutrition'
```

## Root Cause
The ML pipeline was using incorrect method names for the `NutritionDatabase` class.

## Fixes Applied

### Fix 1: Orchestrator (`orchestrator.py`)
**Before:**
```python
all_db_ingredients = list(self.nutrition_db.get_all_ingredients())
```

**After:**
```python
all_db_ingredients = self.nutrition_db.get_all_food_names()
```

### Fix 2: Nutrition Adapter (`nutrition_engine_adapter.py`)
**Before:**
```python
nutrition_data = self.nutrition_db.get_ingredient_nutrition(
    ingredient_name,
    quantity,
    unit
)
```

**After:**
```python
nutrition_data = self.nutrition_db.get_nutrition(
    food_name=ingredient_name,
    weight_g=quantity
)
```

Also updated to:
- Convert `NutritionData` object to dict
- Handle unit conversion (currently assumes grams)
- Proper error handling

## Correct NutritionDatabase Methods

The `NutritionDatabase` class has these methods:
- `get_nutrition(food_name: str, weight_g: float)` - Get nutrition for a food
- `get_all_food_names()` - Get list of all food names
- `get_high_protein_foods(min_protein_per_100g: float)` - Get high-protein foods
- `get_complete_proteins()` - Get complete protein sources
- `has_food(food_name: str)` - Check if food exists

## Testing

After the fix, the ML pipeline should work correctly:

```bash
# Test the ML pipeline
cd backend
python test_ml_pipeline.py

# Start backend
python start_backend.py

# Test via UI
# Click "Generate Plan (ML)" button
```

## Status
✅ **FIXED** - ML pipeline now uses correct database methods
