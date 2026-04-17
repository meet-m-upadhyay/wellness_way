# Hybrid Nutrition Pipeline — Design Spec

**Date:** 2026-04-18
**Status:** Approved
**Branch:** work-pc-test

## Problem

The current ML diet pipeline relies on a manually curated `food_items` database for ingredient selection and macro calculations. This limits food variety to what has been manually added (~80 items). Scaling the database by hand is unsustainable — the user must add every new food item manually before it can appear in a plan.

The previous pure-AI approach was abandoned because LLMs generate unreliable macro numbers. We need the best of both: infinite food variety with verified nutritional data.

## Solution

**Approach B: LLM replaces the discovery engine only.** The daily assembler, validation engine, nutrition totals, and GenAI naming remain unchanged.

- An LLM suggests *what* to eat (ingredients + categories + metadata)
- A nutrition API verifies *the macros* (CalorieNinjas primary, USDA fallback)
- The existing assembler calculates *how much* (protein-first portion scaler)
- The `food_items` table becomes a permanent auto-growing cache
- If the LLM or API path fails, the system falls back to the existing template-based discovery engine

### Core Principle

AI picks food. API verifies nutrition. Math sizes portions. No component does another's job.

---

## Architecture

### Component Map

| Component | Status | Role |
|---|---|---|
| **LLM Meal Suggester** | NEW | Suggests ingredients + categories + metadata |
| **Nutrition Provider Layer** | NEW | Abstract interface for nutrition APIs |
| **Nutrition Resolver** | NEW | Cache check, API lookup, name simplification, LLM substitution |
| **food_items table** | MODIFIED | New `api_verified` column, becomes auto-growing cache |
| **Orchestrator** | MODIFIED | New Step 1 (LLM + resolver), fallback to old discovery |
| **Daily Assembler** | UNCHANGED | Protein-first portion math |
| **Validation Engine** | UNCHANGED | Checks against HCD constraints |
| **GenAI Naming** | UNCHANGED | Generates meal names from ingredients |
| **Template Discovery Engine** | KEPT | Fallback when LLM/API path fails |

### Pipeline Flow (Daily Plan)

```
STEP 0: Extract constraints (unchanged)
        |
STEP 1: LLM Meal Suggestion (NEW — replaces discovery engine)
        |
        |-- success --> ingredient names + categories + metadata
        |               |
        |         STEP 1b: Nutrition Resolver (NEW)
        |               |
        |               |-- all resolved --> portfolio of FoodItems with verified macros
        |               |
        |               |-- some failed --> resolved items + warnings logged
        |
        |-- failure --> FALLBACK to old DiscoveryEngine
        |
STEP 2: Daily Assembly (unchanged)
        |
STEP 3: Creative Recipe Generation (unchanged)
        |
STEP 4: Validation (unchanged)
        |
STEP 5: Summary (unchanged)
        |
STEP 6: Nutrition Totals (unchanged)
```

Fallback is per-meal: if the LLM path works for breakfast and lunch but fails for dinner, only dinner falls back to the template-based discovery engine.

---

## 1. Nutrition Provider Layer

### Interface

```python
class NutritionProvider(ABC):
    """All nutrition APIs implement this."""

    @abstractmethod
    async def lookup(self, ingredient_name: str) -> NutritionResult | None:
        """Look up macros for an ingredient. Returns None if not found."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Provider identifier for dataset_source field. e.g. 'calorieninjas'"""
```

### NutritionResult

```python
@dataclass
class NutritionResult:
    name: str               # canonical name from API
    calories: float         # per 100g
    protein: float          # per 100g
    fat: float              # per 100g
    carbohydrates: float    # per 100g
    fiber: float            # per 100g
    serving_size_g: float   # API's default serving size (for reference)
    source: str             # provider name
```

All macros normalized to per-100g regardless of what the API returns. This matches the existing `food_items.macros` convention.

### Providers Built Now

**CalorieNinjas (primary)**
- Endpoint: `GET https://api.calorieninjas.com/v1/nutrition?query={name}`
- Auth: `X-Api-Key` header
- Rate limit: 10,000 requests/month (free tier)
- Returns macros per serving — normalize to per-100g using `serving_size_g`
- Good coverage for Indian, Mediterranean, Italian foods

**USDA FoodData Central (secondary)**
- Endpoint: `GET https://api.nal.usda.gov/fdc/v1/foods/search?query={name}&api_key={key}`
- Auth: API key in query string
- Rate limit: Unlimited (free)
- Two-step: search for food -> extract nutrient values from response
- Lab-verified data, best for raw ingredients

### Future Providers (Reference)

| Provider | Key Features | Cost | When to Consider |
|---|---|---|---|
| **Nutritionix** | Best NLP parsing ("1 cup brown rice" -> exact macros), barcode lookup, exercise DB | Free: 1k req/day | Food logging, barcode scanning |
| **Edamam** | Recipe-level analysis (full recipe -> total macros), diet/health labels, meal planning API | Free: 100 req/day | Full recipe validation |
| **FatSecret** | Large DB, OAuth, meal diary API, weight tracking | Free tier available | Social/sharing features |
| **Open Food Facts** | Crowdsourced, barcode DB, fully open source, no key needed | Unlimited, free | Packaged/branded food lookup |
| **Spoonacular** | Meal planning API, ingredient substitution, grocery lists, wine pairing | Free: 150 req/day | Pre-built meal planning features |

To add any future provider: create a class implementing `NutritionProvider`, register it in config. No other code changes needed.

### Resolution Chain

CalorieNinjas -> USDA -> fail (triggers name simplification or LLM substitution)

---

## 2. Nutrition Resolver

Sits between the LLM and the assembler. Resolves ingredient names to verified macros with caching.

### Resolution Flow (per ingredient)

```
1. DB Cache Lookup
   SELECT from food_items
   WHERE canonical_name ILIKE '%{name}%'
   AND api_verified = True
   --> HIT: return cached macros
   --> MISS: continue

2. CalorieNinjas API
   GET /v1/nutrition?query={name}
   --> HIT: cache in DB, return macros
   --> MISS: continue

3. USDA API
   GET /fdc/v1/foods/search?query={name}
   --> HIT: cache in DB, return macros
   --> MISS: continue

4. Name Simplification (up to 3 attempts)
   "Amritsari Fish Tikka" -> "Fish Tikka" -> "Fish"
   Retry steps 1-3 with simplified name
   --> HIT: cache in DB, return macros
   --> MISS: continue

5. LLM Substitution
   Ask LLM: "Can't find macros for '{name}'.
   Suggest a common alternative {diet_type} {cuisine} {category}."
   Resolve the substitute through steps 1-3
   --> HIT: cache in DB, return macros
   --> MISS: continue

6. FAIL
   Skip ingredient, log warning
```

### Name Simplification Strategy

Strip qualifiers progressively, in this order:
1. Remove parenthetical: "Paneer (Low Fat)" -> "Paneer"
2. Remove leading qualifier (first word): "Amritsari Fish Tikka" -> "Fish Tikka"
3. Remove trailing qualifier (last word): "Fish Tikka" -> "Fish"

Each simplified name is tried through steps 1-3 (cache + CalorieNinjas + USDA) before simplifying further. Stop as soon as any step returns a result. Maximum 3 simplification rounds.

### Caching Rules

- On any API hit, write/update `food_items` row with `api_verified=True`
- DB lookup uses fuzzy ILIKE matching
- Cache entries never expire (food macros are stable data)
- Existing `manual` items with `api_verified=False`: use for metadata (`diet_flags`, `cuisine_tags`), but re-verify macros via API on first use

### Method Signature

```python
class NutritionResolver:
    async def resolve_portfolio(
        self,
        ingredients: list[LLMIngredient],
        diet_type: str,
        cuisine: str,
    ) -> Dict[str, List[ResolvedIngredient]]:
        """Resolve LLM-suggested ingredients to FoodItem-compatible objects
        with verified macros. Returns a portfolio grouped by category
        (protein, starch, vegetables, fat) — same shape the assembler expects."""
```

Each `ResolvedIngredient` has the same attributes as `FoodItem` (`canonical_name`, `macros`, `diet_flags`, `cuisine_tags`, `allergen_flags`, `id`). The resolver groups them by the `category` field the LLM provided. The assembler receives `Dict[str, List[...]]` exactly as it does today.

### Threshold

If >50% of a meal's ingredients fail resolution, the entire meal falls back to the template-based discovery engine.

---

## 3. LLM Meal Suggestion Service

Replaces the discovery engine as the ingredient source.

### Prompt Input

- Diet type, cuisine preference, allergies, foods to avoid
- Calorie target per meal, protein target per meal
- Meal type (breakfast / lunch / dinner)
- Budget and lifestyle constraints
- Ingredients to exclude (for variety across meals/days)
- Diet priority rules (non-veg > egg > veg > vegan for non-veg users, etc.)

### Expected Output (Pydantic-validated JSON)

```json
{
  "meals": [
    {
      "meal_type": "lunch",
      "ingredients": [
        {
          "name": "Chicken Tikka",
          "category": "protein",
          "diet_flags": ["non-vegetarian"],
          "cuisine_tags": ["indian"],
          "allergen_flags": []
        },
        {
          "name": "Brown Rice",
          "category": "starch",
          "diet_flags": ["vegan", "vegetarian", "eggetarian"],
          "cuisine_tags": ["indian"],
          "allergen_flags": []
        },
        {
          "name": "Palak (Spinach)",
          "category": "vegetables",
          "diet_flags": ["vegan", "vegetarian", "eggetarian"],
          "cuisine_tags": ["indian"],
          "allergen_flags": []
        },
        {
          "name": "Ghee",
          "category": "fat",
          "diet_flags": ["vegetarian", "eggetarian"],
          "cuisine_tags": ["indian"],
          "allergen_flags": []
        }
      ]
    }
  ]
}
```

### Design Decisions

1. **LLM outputs categories** (`protein`, `starch`, `vegetables`, `fat`) matching what the assembler expects. No assembler changes needed.

2. **LLM does NOT output quantities.** It picks *what* to eat. The assembler calculates *how much*. AI is bad at math — this boundary is non-negotiable.

3. **Diet priority enforced in the prompt.** The hierarchy (non-veg > egg > veg > vegan for non-veg users) is written into the system prompt as explicit rules.

4. **Schema-enforced via Pydantic.** Same pattern as existing `GenAIMealText`. Bad JSON triggers fallback to template-based discovery.

5. **LLM assigns metadata** (`diet_flags`, `cuisine_tags`, `allergen_flags`) for each ingredient. The LLM is good at classification. These are stored in `food_items` alongside API-verified macros.

### Integration Point

```python
# Same return type as the old discovery engine
BEFORE:  DiscoveryEngine.discover_daily_portfolio() -> Dict[str, List[FoodItem]]
AFTER:   LLMMealSuggester.suggest_portfolio()       -> Dict[str, List[FoodItem]]
```

The orchestrator doesn't care which produced the portfolio.

---

## 4. Database Changes

### No new tables.

### One new column on `food_items`

```python
api_verified = Column(Boolean, default=False, nullable=False)
```

### Alembic migration

```python
def upgrade():
    op.add_column('food_items', sa.Column('api_verified', sa.Boolean(), nullable=False, server_default='false'))

def downgrade():
    op.drop_column('food_items', 'api_verified')
```

All existing rows get `api_verified=False`. No data loss.

### New `dataset_source` values

| Value | Meaning |
|---|---|
| `manual` | Existing hand-added items |
| `calorieninjas` | Cached from CalorieNinjas API |
| `usda` | Cached from USDA FoodData Central |
| `csv` | Existing CSV imports |

### Automatic Verification of Existing Items

Existing `manual` items get verified organically — the first time the LLM suggests an ingredient that matches an existing unverified row, the resolver updates its macros from the API and sets `api_verified=True`. No migration script needed.

### Cache Lookup Priority

1. `api_verified=True` items: trust immediately, return cached macros
2. `api_verified=False` items: use for metadata, re-verify macros via API
3. No match: full API lookup, create new row

---

## 5. Orchestrator Changes

### Modified Flow

Step 1 of the daily plan generation changes from:

```python
# OLD
portfolio = self.discovery_engine.discover_daily_portfolio(db, diet_type, ...)
```

To:

```python
# NEW
if settings.enable_llm_meal_suggestions:
    try:
        llm_suggestions = await self.meal_suggester.suggest_meals(
            diet_type=constraints.diet_type.value,
            cuisine=constraints.cuisine,
            allergies=constraints.allergies,
            # ... other constraints
        )
        portfolio = await self.nutrition_resolver.resolve_ingredients(
            ingredients=llm_suggestions,
            diet_type=constraints.diet_type.value,
            cuisine=constraints.cuisine,
        )
    except Exception:
        logger.warning("[DEBUG][ML_PIPELINE_FALLBACK] LLM path failed, using template discovery")
        portfolio = self.discovery_engine.discover_daily_portfolio(db, diet_type, ...)
else:
    portfolio = self.discovery_engine.discover_daily_portfolio(db, diet_type, ...)
```

### Fallback Triggers

- LLM API unreachable (Groq down)
- LLM returns invalid JSON (Pydantic validation fails)
- Nutrition resolver can't resolve >50% of ingredients in a meal
- Any unhandled exception in the new path

### Applies To All Generation Paths

- `generate_daily_plan()` — new LLM path with fallback
- `generate_weekly_plan()` — same, per-day
- `regenerate_meal()` — same, per-meal

### Configuration

```env
# Feature flag
ENABLE_LLM_MEAL_SUGGESTIONS=true

# Nutrition API
NUTRITION_API_PROVIDER=calorieninjas
CALORIENINJAS_API_KEY=your_key_here
NUTRITION_FALLBACK_PROVIDER=usda
USDA_API_KEY=your_key_here
```

When `ENABLE_LLM_MEAL_SUGGESTIONS=false`, the system uses the existing template-based pipeline. Zero-risk deploy.

---

## 6. Error Handling & Observability

### Error Matrix

| Scenario | Detection | Response | Log Tag |
|---|---|---|---|
| CalorieNinjas rate limited (429) | HTTP 429 | Switch to USDA for rest of request | `[DEBUG][NUTRITION_RATE_LIMITED]` |
| CalorieNinjas down (5xx/timeout) | httpx error | Switch to USDA | `[DEBUG][NUTRITION_PROVIDER_DOWN]` |
| Both APIs down | Both fail | Fallback to template discovery | `[DEBUG][NUTRITION_ALL_PROVIDERS_DOWN]` |
| LLM returns bad JSON | Pydantic validation | Fallback to template discovery | `[DEBUG][LLM_SUGGESTION_INVALID]` |
| Ingredient unresolvable | Resolver exhausts all 6 steps | Skip ingredient, log warning | `[DEBUG][NUTRITION_UNRESOLVED]` |
| >50% of meal unresolved | Count check | Fallback entire meal to old pipeline | `[DEBUG][NUTRITION_RESOLVE_THRESHOLD]` |
| DB cache write fails | SQLAlchemy exception | Continue without caching | `[DEBUG][NUTRITION_CACHE_WRITE_FAILED]` |
| Groq LLM down | httpx error | Fallback to template discovery | `[DEBUG][LLM_PROVIDER_DOWN]` |

Every failure has a fallback. The user always gets a plan.

### Log Format

All new hybrid pipeline logs prefixed with `[DEBUG]` for easy filtering:

```
[DEBUG][LLM_SUGGEST_START] request_id=ml_daily_abc123 diet=non-vegetarian cuisine=indian
[DEBUG][NUTRITION_CACHE_HIT] ingredient="Chicken Tikka" source=calorieninjas
[DEBUG][NUTRITION_API_CALL] ingredient="Mutton Curry" provider=calorieninjas
[DEBUG][NUTRITION_CACHE_WRITE] ingredient="Mutton Curry" source=calorieninjas api_verified=True
[DEBUG][NUTRITION_SIMPLIFY] original="Amritsari Fish Tikka" simplified="Fish Tikka"
[DEBUG][NUTRITION_RESOLVE_COMPLETE] resolved=11/12 failed=1 cached=8 api_calls=3
[DEBUG][ML_PIPELINE_FALLBACK] reason="LLM returned invalid JSON" meal_type=dinner
```

Uses existing Python `logging` setup. No new monitoring infrastructure.

---

## 7. File Structure

New files under `backend/app/services/ml_diet_pipeline/`:

```
ml_diet_pipeline/
    nutrition/
        engine.py              # existing (unchanged)
        providers/
            __init__.py
            base.py            # NutritionProvider ABC + NutritionResult dataclass
            calorieninjas.py   # CalorieNinjas implementation
            usda.py            # USDA FoodData Central implementation
        resolver.py            # NutritionResolver (cache + API + simplification)
    suggestion/
        __init__.py
        service.py             # LLMMealSuggester
        schema.py              # Pydantic models for LLM input/output
    orchestrator.py            # modified (new Step 1 + fallback)
    discovery_engine.py        # kept (fallback)
    daily_assembler.py         # unchanged
    meal_templates.py          # kept (fallback)
    validation/
        engine.py              # unchanged
    genai/
        service.py             # unchanged
        schema.py              # unchanged
```

---

## 8. What Does NOT Change

- **Frontend** — no API contract changes, no new endpoints
- **Auth system** — untouched
- **Health Context Documents** — untouched
- **Daily Assembler** — receives portfolio, calculates portions (same interface)
- **Validation Engine** — checks against HCD (same interface)
- **GenAI Naming** — generates names from ingredients (same interface)
- **Deployment config** — same Docker/GCP setup, just new env vars
- **Existing API endpoints** — same request/response contracts

---

## 9. Testing Strategy

### Unit Tests

- `test_nutrition_providers.py` — mock HTTP responses, verify normalization to per-100g
- `test_nutrition_resolver.py` — mock providers + DB, test cache hit/miss/simplification/substitution flows
- `test_llm_meal_suggester.py` — mock LLM responses, verify Pydantic validation and fallback
- `test_orchestrator_fallback.py` — verify fallback triggers correctly for each failure mode

### Integration Tests

- End-to-end with real CalorieNinjas API (mark as `@pytest.mark.integration`)
- Verify DB cache is populated after first API call
- Verify second call for same ingredient doesn't hit API

### Manual Verification

- Generate plans for each diet type (non-veg, eggetarian, vegetarian, vegan)
- Confirm non-veg users get non-veg meals with verified macros
- Toggle `ENABLE_LLM_MEAL_SUGGESTIONS=false` and verify old pipeline still works
