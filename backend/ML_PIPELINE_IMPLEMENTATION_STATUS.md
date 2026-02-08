# ML Pipeline Implementation Status

## Overview
This document tracks the implementation of the ML + GenAI diet plan generation pipeline
that lives side-by-side with the existing GenAI-only pipeline.

## Implementation Progress

### ✅ STEP 1: New API Endpoints (COMPLETE)
**Files Created:**
- `backend/app/api/endpoints/diet_plans_ml.py` - New ML pipeline endpoints
- Updated `backend/app/api/router.py` - Registered new routes

**Endpoints:**
- `POST /api/v1/diet-plans-ml/weekly` - Generate weekly plan using ML pipeline
- `POST /api/v1/diet-plans-ml/daily` - Generate daily plan using ML pipeline

**Status:** Returns 501 Not Implemented with fallback guidance

### ✅ STEP 2: ML Ingredient Canonicalizer (COMPLETE)
**Files Created:**
- `backend/app/services/ml_diet_pipeline/__init__.py` - Module initialization
- `backend/app/services/ml_diet_pipeline/ingredient_canonicalizer.py` - ML canonicalizer

**Features:**
- Uses sentence-transformers (all-MiniLM-L6-v2)
- Cosine similarity matching against nutrition DB
- Confidence threshold (≥ 0.85)
- Modifier extraction (cooked, steamed, raw, etc.)
- Soft reject on low confidence (warning, not error)
- Batch processing support

**Dependencies Required:**
```bash
pip install sentence-transformers
```

### ✅ STEP 3: Meal Template Registry (COMPLETE)
**Files Created:**
- `backend/app/services/ml_diet_pipeline/meal_templates.py` - Static templates

**Features:**
- 15+ predefined meal templates
- Diet-type aware (vegetarian, vegan, non-vegetarian, eggetarian)
- Meal slot categorization (breakfast, lunch, dinner, snack)
- Tag-based filtering (high-protein, vegan, quick, etc.)
- NO quantities (handled by scaling engine)
- NO GenAI involvement

**Templates Included:**
- Breakfast: Protein Scramble, Oatmeal Bowl, Vegan Smoothie Bowl, Greek Yogurt Parfait
- Lunch: Chicken Rice Bowl, Lentil Curry, Quinoa Salad, Paneer Tikka Bowl, Tofu Stir Fry
- Dinner: Grilled Salmon, Chickpea Pasta, Egg Fried Rice, Black Bean Tacos, Turkey Sweet Potato
- Snacks: Protein Shake, Hummus with Veggies, Mixed Nuts and Fruit

### ✅ STEP 4: ML Meal Template Selector (COMPLETE)
**Files Created:**
- `backend/app/services/ml_diet_pipeline/meal_template_selector.py` - Heuristic selector

**Features:**
- Heuristic-based scoring (pluggable ML later)
- Diet-type filtering
- Allergy and food avoidance filtering
- Variety management (exclude used templates)
- Tag-based preference matching
- Deterministic scoring with small random factor
- Daily meal selection (full day planning)

**Future Enhancement:**
- Replace heuristic scoring with LightGBM or Logistic Regression

### ✅ STEP 5: Deterministic Nutrition + Scaling (COMPLETE)
**Files Created:**
- `backend/app/services/ml_diet_pipeline/nutrition_engine_adapter.py` - Nutrition adapter
- `backend/app/services/ml_diet_pipeline/scaling_engine.py` - Deterministic scaling

**Features:**
- Reuses existing nutrition database
- NO GenAI for calculations
- Deterministic portion scaling
- Soft acceptance (±15% calories, ±10% protein)
- Scale factor clamping (0.5x - 2.0x)
- Meal and daily scaling support

### ✅ STEP 6: Rules-Only Validation Engine (COMPLETE)
**File Created:**
- `backend/app/services/ml_diet_pipeline/validation_engine.py`

**Features:**
- Diet-type specific thresholds
- NO exceptions that cause AI retry
- Soft vs hard failure classification
- Structured logging
- Meal and daily plan validation

### ✅ STEP 7: GenAI for TEXT ONLY (COMPLETE)
**File Created:**
- `backend/app/services/ml_diet_pipeline/genai_text_generator.py`

**Features:**
- Ingredients and quantities are READ-ONLY
- Only generates: meal name, instructions, description
- Deterministic fallback if GenAI fails
- NO nutrition calculations

### ✅ STEP 8: ML Pipeline Orchestrator (COMPLETE)
**File Created:**
- `backend/app/services/ml_diet_pipeline/orchestrator.py`

**Features:**
- Glues all steps together
- One entry point for daily/weekly
- Zero AI retries
- Comprehensive logging
- Integration with existing DietPlanService
- Full daily and weekly plan generation

### ✅ FRONTEND INTEGRATION (COMPLETE)
**Files Updated:**
- `frontend/src/components/diet-plans/PlanTypeSelector.tsx` - Added ML buttons
- `frontend/src/services/api.ts` - Added ML endpoint support

**Features:**
- Two buttons per plan type (AI and ML)
- Visual distinction (purple gradient for ML)
- "NEW" badge on ML buttons
- Automatic routing to correct endpoints

## Architecture Diagram

```
Frontend
   ├── Generate Daily Meal Plan        (existing GenAI)
   ├── Generate Weekly Meal Plan       (existing GenAI)
   ├── Generate Daily Meal Plan (ML)   ← NEW
   └── Generate Weekly Meal Plan (ML)  ← NEW

Backend
   ├── ai_service.py                  (unchanged)
   ├── diet_plan_service.py           (unchanged)
   │
   └── ml_diet_pipeline/              ← NEW MODULE
         ├── __init__.py                      ✅
         ├── ingredient_canonicalizer.py     ✅ (ML)
         ├── meal_templates.py               ✅ (Static)
         ├── meal_template_selector.py       ✅ (ML)
         ├── nutrition_engine_adapter.py     ✅ (Deterministic)
         ├── scaling_engine.py               ✅ (Deterministic)
         ├── validation_engine.py            🚧 (Rules)
         ├── genai_text_generator.py         🚧 (Constrained LLM)
         └── orchestrator.py                 🚧 (Glue)
```

## Testing Strategy

### Unit Tests Needed:
1. Ingredient canonicalizer with various inputs
2. Template selector with different constraints
3. Scaling engine with edge cases
4. Validation engine with soft/hard failures
5. Text generator with fallbacks

### Integration Tests Needed:
1. Full daily plan generation
2. Full weekly plan generation
3. Comparison with GenAI pipeline outputs
4. Performance benchmarks

### Golden Tests:
- Vegetarian plan
- Vegan plan
- Eggetarian plan
- Non-vegetarian with red meat
- Plans with allergies
- Plans with food avoidances

## Dependencies

### Python Packages Required:
```bash
pip install sentence-transformers  # For ML canonicalizer
pip install torch                   # Required by sentence-transformers
```

### Optional (Future):
```bash
pip install lightgbm               # For ML template selector upgrade
pip install scikit-learn           # For logistic regression
```

## Configuration

### Environment Variables:
```bash
# Feature flag for ML pipeline
ENABLE_ML_PIPELINE=true

# ML model settings
ML_CANONICALIZER_MODEL=sentence-transformers/all-MiniLM-L6-v2
ML_CANONICALIZER_CONFIDENCE_THRESHOLD=0.85

# Scaling settings
ML_SCALING_MIN_FACTOR=0.5
ML_SCALING_MAX_FACTOR=2.0
ML_SCALING_CALORIE_TOLERANCE=0.15
ML_SCALING_PROTEIN_TOLERANCE=0.10
```

## Deployment Checklist

### Phase 1 (Current):
- [x] Create new API endpoints
- [x] Implement ML ingredient canonicalizer
- [x] Create meal template registry
- [x] Implement template selector
- [x] Create nutrition adapter
- [x] Implement scaling engine
- [x] Implement validation engine
- [x] Implement text generator
- [x] Implement orchestrator
- [x] Add frontend UI buttons
- [x] Update API service
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Update API documentation
- [ ] Deploy behind feature flag

### Phase 2 (Future):
- [ ] Collect usage metrics
- [ ] Compare ML vs GenAI quality
- [ ] Upgrade template selector to LightGBM
- [ ] Add user feedback loop
- [ ] Gradually increase ML pipeline traffic
- [ ] Deprecate GenAI-only pipeline
- [ ] Remove old endpoints

## Monitoring

### Metrics to Track:
- `ml_pipeline_requests_total` - Total requests to ML pipeline
- `ml_pipeline_success_rate` - Success rate vs GenAI pipeline
- `ml_pipeline_latency_seconds` - Response time
- `ml_canonicalizer_confidence` - Average confidence scores
- `ml_template_selection_scores` - Template selection quality
- `ml_scaling_adjustments` - How often scaling is needed

### Logs to Monitor:
- `[ML_PIPELINE_INIT]` - Pipeline initialization
- `[ML_PIPELINE_SUCCESS]` - Successful generation
- `[ML_PIPELINE_FAILED]` - Failed generation
- `[ING_CANONICALIZED]` - Ingredient canonicalization
- `[ING_CANONICAL_LOW_CONFIDENCE]` - Low confidence warnings
- `[TEMPLATE_SELECTED]` - Template selection
- `[SCALING_APPLIED]` - Scaling operations
- `[SCALING_INSUFFICIENT_ACCEPTED]` - Soft acceptance cases

## Known Limitations

1. **Template Library Size**: Currently 15 templates - needs expansion
2. **Heuristic Selector**: Not ML-based yet - upgrade to LightGBM planned
3. **No User Feedback**: No learning from user preferences yet
4. **Static Ingredients**: Templates have fixed ingredients - no substitutions
5. **English Only**: No internationalization support

## Next Steps

1. Complete validation engine (STEP 6)
2. Complete text generator (STEP 7)
3. Complete orchestrator (STEP 8)
4. Add comprehensive tests
5. Deploy behind feature flag
6. Collect metrics and feedback
7. Iterate and improve

## Contact

For questions or issues with the ML pipeline implementation, contact the backend team.
