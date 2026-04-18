# V2 Meal Engine

Parallel meal generation system with IFCT-backed Indian nutrition data, culturally coherent archetypes, fuzzy ingredient matching, and hybrid scoring.

## Architecture

```
LLM (Groq) → archetype-first prompt → structured JSON
                ↓
    IngredientMatcher (exact → alias → canonical → fuzzy → embedding)
                ↓
    NutritionRouter (IFCT → Edamam → USDA, cuisine-aware)
                ↓
    UnitNormalizer (katori → 150g, phulka → 30g, etc.)
                ↓
    MealScorer (6 deterministic dimensions + LLM coherence judge)
                ↓
    Auto-retry if score < 70 (max 3 attempts)
```

## API Endpoints

- `POST /api/v1/v2/meal-engine/generate-meal` — single meal
- `POST /api/v1/v2/meal-engine/generate-daily` — full day (breakfast + lunch + dinner)

Feature-flagged: set `ENABLE_MEAL_ENGINE_V2=true` in `.env`.

## Database Tables

| Table | Purpose |
|-------|---------|
| `v2_ingredients` | 546 foods from IFCT 2017 + 4 manual dairy entries |
| `v2_regions` | 6 Indian geographic zones |
| `v2_pairing_rules` | 17 cultural pairing rules (seeded, runtime-editable) |
| `v2_ingredient_embeddings` | 384-dim vectors for semantic matching (pgvector) |
| `v2_external_nutrition_cache` | Edamam API response cache |

## Seed Scripts

Run from `backend/`:

```bash
# 1. Generate IFCT JSON (Node.js)
cd ../ifct-test && node seed_ifct.js

# 2. Load into PostgreSQL (with corrections)
python scripts/seed/load_ifct_seed.py --json-path ../ifct-test/ifct_seed_data.json

# 3. Seed pairing rules
python scripts/seed/seed_pairing_rules.py

# 4. Generate embeddings (requires sentence-transformers)
python scripts/seed/generate_embeddings.py

# 5. (Optional) Classify food forms via Groq LLM
python scripts/seed/classify_forms_groq.py        # full run
python scripts/seed/classify_forms_groq.py --dry-run  # 10 entries only
```

## Config Files

All in `config/`:

| File | What to tune |
|------|-------------|
| `archetypes.json` | Meal archetypes per cuisine (slots, allowed food groups) |
| `scoring_weights.json` | Scoring dimension weights and band thresholds |
| `unit_conversions.json` | Indian unit → grams mappings |
| `goal_macro_order.json` | Macro display order per diet goal |
| `canonical_foods.json` | Default IFCT entry for ambiguous common names |
| `pairing_rules_seed.json` | Source for DB pairing rules (re-run seed script after editing) |

Configs load at startup. In dev mode (`ENVIRONMENT=development`), they hot-reload on every access.

## Adding a New Cuisine

1. Add archetype entries in `archetypes.json` under the new cuisine key
2. Add pairing rules in `pairing_rules_seed.json`, re-run seed
3. Add cuisine routing in `nutrition/router.py` CUISINE_CHAINS
4. Add canonical food overrides in `canonical_foods.json` if needed

## Adding a New Nutrition Provider

1. Create a class extending `NutritionProvider` from `ml_diet_pipeline/nutrition/providers/base.py`
2. Implement `async lookup(name) → NutritionResult` and `source_name` property
3. Register in `nutrition/router.py` CUISINE_CHAINS

## Scoring Dimensions

| Dimension | Max | What it measures |
|-----------|-----|-----------------|
| Macro Accuracy | 30 | % deviation from target macros |
| Plate Composition | 20 | Protein + carb + fat + veg all present |
| Culinary Coherence | 20 | Archetype match + no pairing violations |
| Micro Diversity | 15 | Distinct food groups in the meal |
| Goal Alignment | 10 | Priority macro close to target |
| Practicality | 5 | Portion sizes 30-400g each |

Bands: 85+ = serve, 70-84 = serve with log, <70 = auto-regenerate.
