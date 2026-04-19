# V2 Meal Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a parallel meal generation system (v2) with IFCT-backed Indian nutrition data, culturally coherent meal archetypes, fuzzy ingredient matching, and a hybrid scoring pipeline — without touching existing tables or routes.

**Architecture:** New `meal_engine/` module under `backend/app/services/` with its own models, providers, config, and API endpoint (`/v2/generate-meal`). IFCT data is seeded via a standalone Node.js script into a new `v2_ingredients` table. A cuisine-aware nutrition router queries v2_ingredients first (for Indian), with Edamam as external fallback (cached in `v2_external_nutrition_cache`), then USDA. Embeddings stored in pgvector for semantic ingredient matching. Meals are generated archetype-first, scored 0-100 via deterministic + LLM-judge hybrid, and auto-regenerated below threshold.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL (JSONB, GIN indexes, pg_trgm, pgvector), Node.js (seed script), Groq LLM (meal generation + scoring judge), rapidfuzz (fuzzy matching), sentence-transformers/all-MiniLM-L6-v2 (384-dim embeddings).

---

## Scope Note

This spec covers ~14 deliverables across 5 subsystems. They have linear dependencies so a single phased plan is appropriate:

```
Phase 1: DB Schema ─► Phase 2: Seed Script ─► Phase 3: Nutrition Router
                                                        │
Phase 4: Config (archetypes/pairings/units) ◄───────────┘
                        │
Phase 5: Fuzzy Matching Layer
                        │
Phase 6: Meal Scoring Module
                        │
Phase 7: V2 Generation Pipeline + API
                        │
Phase 8: Tests
```

---

## Assumptions

1. **PostgreSQL 14+** with `pg_trgm` extension available (needed for trigram fuzzy matching). If not available, we degrade to rapidfuzz in-app.
2. **pgvector extension** is available on PostgreSQL. Used for 384-dim embedding storage and cosine similarity search on `v2_ingredient_embeddings`.
3. **Edamam** is the sole external nutrition API. Keys (`EDAMAM_APP_ID`, `EDAMAM_APP_KEY`) provided via env vars. Nutritionix is excluded. Graceful no-op if keys are missing (dev works without them). Responses cached in `v2_external_nutrition_cache` to conserve the 10K/month free tier.
4. **Groq** remains the LLM provider for generation and scoring judge calls.
5. **The seed script** runs as a standalone Node.js utility that outputs a JSON file. A Python loader then inserts into PostgreSQL. This avoids adding Node.js as a backend runtime dependency.
6. **Embeddings** are precomputed at seed time via `sentence-transformers/all-MiniLM-L6-v2` (384-dim, normalized) and stored in pgvector. At runtime, the matcher embeds the query string and does a pgvector nearest-neighbor lookup — no FAISS needed.
7. **`@ifct2017/compositions`** package is already installed in `ifct-test/`. The seed script will run from there.
8. The existing `food_items` table and all v1 routes remain untouched.
9. **Config loading**: JSON configs (archetypes, scoring_weights, unit_conversions) loaded at startup, hot-reloaded in dev mode, validated on load. `v2_pairing_rules` is a DB table seeded from version-controlled JSON, editable at runtime.

## Resolved Decisions

| # | Question | Decision |
|---|----------|----------|
| 1 | External nutrition API | **Edamam only** (skip Nutritionix). Keys via `EDAMAM_APP_ID` + `EDAMAM_APP_KEY` env vars. Cache responses in `v2_external_nutrition_cache` table. Graceful fallback if keys missing. |
| 2 | Embedding model | **sentence-transformers `all-MiniLM-L6-v2`**, 384-dim, normalized vectors, running locally in Python. |
| 3 | Embedding storage | **pgvector** on PostgreSQL (not FAISS). Precompute at seed time, cosine similarity lookup at runtime. |
| 4 | Embedding generation timing | Separate Python step after Node.js seed (Phase 2b). Keeps seed script Node-only. |
| 5 | LLM-as-judge | One Groq call per meal (simpler, ~3 calls per plan). |
| 6 | Region mapping | Hard-coded (6 values, well-known Indian zones). |
| 7 | Archetypes | **JSON config** file — loaded at startup, hot-reloaded in dev, validated on load. |
| 8 | Pairing rules | **DB table `v2_pairing_rules`** — seeded from version-controlled JSON, editable at runtime. |
| 9 | Scoring weights | **JSON config** file (same as archetypes). |
| 10 | Unit conversions | **JSON config** file (same as archetypes). |

---

## File Structure

```
backend/
├── app/
│   ├── models/
│   │   ├── __init__.py                          # MODIFY: add new v2 models
│   │   ├── v2_ingredients.py                    # CREATE: V2Ingredient model
│   │   ├── v2_regions.py                        # CREATE: V2Region model
│   │   ├── v2_pairing_rules.py                  # CREATE: V2PairingRule model (DB table)
│   │   ├── v2_ingredient_embeddings.py          # CREATE: V2IngredientEmbedding (pgvector)
│   │   └── v2_external_nutrition_cache.py       # CREATE: V2ExternalNutritionCache
│   ├── api/
│   │   ├── router.py                            # MODIFY: add v2 meal engine router
│   │   └── endpoints/
│   │       └── meal_engine_v2.py                # CREATE: /v2/generate-meal endpoint
│   ├── schemas/
│   │   └── meal_engine_v2.py                    # CREATE: request/response Pydantic schemas
│   ├── services/
│   │   └── meal_engine/                         # CREATE: entire module
│   │       ├── __init__.py
│   │       ├── orchestrator.py                  # V2 orchestrator (entry point)
│   │       ├── config/
│   │       │   ├── __init__.py
│   │       │   ├── loader.py                    # Config loader (startup + hot-reload in dev)
│   │       │   ├── archetypes.json              # Meal archetype definitions
│   │       │   ├── pairing_rules_seed.json      # Seed data for v2_pairing_rules table
│   │       │   ├── scoring_weights.json         # Scoring dimension weights
│   │       │   ├── unit_conversions.json         # Indian unit → grams mapping
│   │       │   └── goal_macro_order.json         # Goal → macro display order
│   │       ├── matching/
│   │       │   ├── __init__.py
│   │       │   └── ingredient_matcher.py         # Cascading match (exact/alias/fuzzy/pgvector)
│   │       ├── nutrition/
│   │       │   ├── __init__.py
│   │       │   ├── router.py                    # Cuisine-aware nutrition provider router
│   │       │   └── providers/
│   │       │       ├── __init__.py
│   │       │       ├── ifct_provider.py          # Local IFCT DB provider
│   │       │       └── edamam_provider.py        # Edamam API provider (cached)
│   │       ├── scoring/
│   │       │   ├── __init__.py
│   │       │   └── scorer.py                    # Hybrid deterministic + LLM-judge scorer
│   │       ├── generation/
│   │       │   ├── __init__.py
│   │       │   └── prompt_builder.py            # V2 LLM prompt (archetype-first)
│   │       └── unit_normalizer.py               # Indian unit → grams normalizer
│   └── core/
│       └── config.py                            # MODIFY: add MealEngineV2Settings
├── alembic/
│   └── versions/
│       ├── create_v2_regions_table.py           # CREATE: migration
│       ├── create_v2_ingredients_table.py       # CREATE: migration
│       ├── create_v2_pairing_rules_table.py     # CREATE: migration
│       ├── create_v2_ingredient_embeddings.py   # CREATE: migration (pgvector)
│       └── create_v2_nutrition_cache.py         # CREATE: migration
├── scripts/
│   └── seed/                                    # CREATE: directory
│       ├── README.md                            # Seed script usage docs
│       ├── load_ifct_seed.py                    # Python loader: JSON → PostgreSQL
│       ├── generate_embeddings.py               # Python: sentence-transformers → pgvector
│       └── seed_pairing_rules.py                # Python: pairing_rules_seed.json → DB
├── tests/
│   ├── test_unit_normalizer.py                  # CREATE
│   ├── test_ingredient_matcher.py               # CREATE
│   ├── test_meal_scorer.py                      # CREATE
│   ├── test_pairing_validator.py                # CREATE
│   └── test_ifct_seed_validation.py             # CREATE
│
ifct-test/                                       # EXISTING (already has @ifct2017/compositions)
├── seed_ifct.js                                 # CREATE: Node.js seed script → outputs JSON
└── package.json                                 # EXISTING
```

---

## Database Schemas

### Table: `v2_regions`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | INTEGER | No | autoincrement | PK |
| code | INTEGER | No | | UNIQUE, IFCT regn value (1-6) |
| name | VARCHAR(100) | No | | e.g., "North India" |
| description | TEXT | Yes | | |

```sql
CREATE TABLE v2_regions (
    id SERIAL PRIMARY KEY,
    code INTEGER NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT
);
```

Seed data (6 rows):
```
1=North, 2=South, 3=East, 4=West, 5=Central, 6=North-East
```

### Table: `v2_ingredients`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | UUID | No | uuid4 | PK |
| code | VARCHAR(10) | No | | UNIQUE, IFCT code (e.g., "A001") |
| name | VARCHAR(255) | No | | IFCT food name |
| scientific_name | VARCHAR(255) | Yes | | |
| food_group | VARCHAR(100) | No | | From `grup` field |
| region_code | INTEGER | Yes | | FK → v2_regions.code |
| regional_names | JSONB | No | {} | `{"hindi": "Ramdana", "tamil": "Keerai vidai", ...}` |
| search_aliases | TEXT[] | No | {} | Flattened array, GIN indexed |
| diet_tags | TEXT[] | No | {} | `["vegetarian", "eggetarian", ...]` |
| form | VARCHAR(20) | No | 'unspecified' | CHECK IN ('raw', 'cooked', 'unspecified') |
| kcal | FLOAT | No | | Derived: enerc / 4.184 |
| enerc_kj | FLOAT | No | | Raw IFCT value |
| protein_g | FLOAT | No | | protcnt |
| fat_g | FLOAT | No | | fatce |
| carbs_g | FLOAT | No | | choavldf |
| fiber_g | FLOAT | No | | fibtg |
| sugar_g | FLOAT | Yes | | fsugar |
| starch_g | FLOAT | Yes | | starch |
| sat_fat_g | FLOAT | Yes | | fasat |
| mufa_g | FLOAT | Yes | | fams |
| pufa_g | FLOAT | Yes | | fapu |
| trans_fat_g | FLOAT | Yes | | fatrn |
| omega3_g | FLOAT | Yes | | facn3 |
| omega6_g | FLOAT | Yes | | facn6 |
| cholesterol_mg | FLOAT | Yes | | cholc * 1000 |
| calcium_mg | FLOAT | Yes | | ca * 1000 |
| iron_mg | FLOAT | Yes | | fe * 1000 |
| magnesium_mg | FLOAT | Yes | | mg * 1000 |
| zinc_mg | FLOAT | Yes | | zn * 1000 |
| sodium_mg | FLOAT | Yes | | na * 1000 |
| potassium_mg | FLOAT | Yes | | k * 1000 |
| phosphorus_mg | FLOAT | Yes | | p * 1000 |
| vit_a_mcg | FLOAT | Yes | | vita * 1e6 |
| vit_c_mg | FLOAT | Yes | | vitc * 1000 |
| vit_d_mcg | FLOAT | Yes | | vitd * 1e6 |
| vit_b_mg | FLOAT | Yes | | vitb * 1000 |
| vit_e_mg | FLOAT | Yes | | vite * 1000 |
| folate_mcg | FLOAT | Yes | | folsum * 1e6 |
| water_g | FLOAT | Yes | | water |
| ash_g | FLOAT | Yes | | ash |
| raw_ifct_data | JSONB | No | | Full original CSV row as JSON |
| nutrient_errors | JSONB | Yes | | All `_e` fields as JSON |
| data_quality | VARCHAR(50) | Yes | NULL | Seed QA flag: `suspect_macros`, `energy_derived`, `suspect_fat`, or NULL (clean) |
| data_source | VARCHAR(50) | No | 'ifct_2017' | |
| confidence | VARCHAR(20) | No | 'verified' | |
| app_serving_units | JSONB | Yes | | Populated later: `{"katori": 150, ...}` |
| meal_archetype_roles | TEXT[] | Yes | | Populated later: `["protein", "dairy"]` |
| custom_aliases | TEXT[] | Yes | | Populated later (manual additions) |
| created_at | TIMESTAMPTZ | Yes | now() | |
| updated_at | TIMESTAMPTZ | Yes | now() | |

**Indexes:**
- `ix_v2_ingredients_code` UNIQUE on `code`
- `ix_v2_ingredients_name` on `name`
- `ix_v2_ingredients_food_group` on `food_group`
- `ix_v2_ingredients_search_aliases` GIN on `search_aliases`
- `ix_v2_ingredients_diet_tags` GIN on `diet_tags`
- `ix_v2_ingredients_form` on `form`

**Check Constraints:**
- `form IN ('raw', 'cooked', 'unspecified')`

### Table: `v2_pairing_rules`

Seeded from `config/pairing_rules_seed.json`, editable at runtime via admin.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | UUID | No | uuid4 | PK |
| cuisine | VARCHAR(50) | No | | e.g., "indian" |
| item | VARCHAR(100) | No | | e.g., "rajma" |
| preferred | TEXT[] | No | | e.g., `["rice"]` |
| acceptable | TEXT[] | No | | e.g., `["roti"]` |
| incompatible | TEXT[] | No | | e.g., `["dosa", "idli"]` |
| created_at | TIMESTAMPTZ | Yes | now() | |
| updated_at | TIMESTAMPTZ | Yes | now() | |

**Unique Constraint:** `(cuisine, item)`

### Table: `v2_ingredient_embeddings`

Stores 384-dim normalized vectors from `all-MiniLM-L6-v2`, using pgvector.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | UUID | No | uuid4 | PK |
| ingredient_id | UUID | No | | FK → v2_ingredients.id, UNIQUE |
| embedding | VECTOR(384) | No | | pgvector type |
| text_used | VARCHAR(500) | No | | Concatenation used for embedding |
| model_name | VARCHAR(100) | No | 'all-MiniLM-L6-v2' | |
| created_at | TIMESTAMPTZ | Yes | now() | |

**Index:** HNSW index on `embedding` for cosine similarity search.

### Table: `v2_external_nutrition_cache`

Caches Edamam API responses to conserve the 10K/month free tier.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | UUID | No | uuid4 | PK |
| query_key | VARCHAR(255) | No | | UNIQUE, lowercase trimmed query string |
| provider | VARCHAR(50) | No | | 'edamam' or 'usda' |
| response_data | JSONB | No | | Full API response (per-100g macros) |
| created_at | TIMESTAMPTZ | Yes | now() | |
| expires_at | TIMESTAMPTZ | Yes | | Optional TTL (e.g., 30 days) |

**Index:** `ix_v2_nutrition_cache_query_key` UNIQUE on `query_key`.

---

## Module Boundaries & Interfaces

### 1. `meal_engine.nutrition.router.NutritionRouter`
```python
class NutritionRouter:
    """Picks nutrition source based on cuisine. Edamam responses cached in v2_external_nutrition_cache."""
    async def lookup(self, ingredient_name: str, cuisine: str) -> Optional[NutritionResult]:
        # Indian → IFCTProvider → Edamam (cached) → USDA fallback
        # Mediterranean/Italian/Western → USDA → Edamam (cached)
        # If EDAMAM keys missing, skip Edamam silently
```

### 1b. `meal_engine.config.loader.ConfigLoader`
```python
class ConfigLoader:
    """Loads JSON configs at startup, hot-reloads in dev mode, validates on load."""
    def __init__(self, config_dir: Path, dev_mode: bool = False): ...
    @property
    def archetypes(self) -> dict: ...
    @property
    def scoring_weights(self) -> dict: ...
    @property
    def unit_conversions(self) -> dict: ...
    @property
    def goal_macro_order(self) -> dict: ...
    def reload(self) -> None: ...  # Re-reads all JSON files, validates, logs changes
```

### 2. `meal_engine.matching.ingredient_matcher.IngredientMatcher`
```python
@dataclass
class MatchResult:
    ingredient_code: Optional[str]
    ingredient_name: str
    match_method: str  # "exact" | "alias" | "fuzzy" | "embedding"
    confidence: float  # 0.0-1.0

class IngredientMatcher:
    """Cascading match: exact → alias → fuzzy (rapidfuzz) → pgvector embedding."""
    async def match(self, llm_name: str, db: Session) -> MatchResult: ...
```

### 3. `meal_engine.scoring.scorer.MealScorer`
```python
@dataclass
class ScoreBreakdown:
    macro_accuracy: float      # 0-30
    plate_composition: float   # 0-20
    culinary_coherence: float  # 0-20
    micro_diversity: float     # 0-15
    goal_alignment: float      # 0-10
    practicality: float        # 0-5
    total: float               # 0-100
    band: str                  # "serve" | "review" | "regenerate"

class MealScorer:
    async def score(self, meal: dict, target_macros: dict, user_goal: str) -> ScoreBreakdown: ...
```

### 4. `meal_engine.unit_normalizer.UnitNormalizer`
```python
class UnitNormalizer:
    """Converts Indian serving units to grams using config."""
    def normalize(self, quantity: float, unit: str, ingredient_name: str) -> float: ...
    # "1 katori" → 150.0, "2 phulkas" → 60.0
```

### 5. `meal_engine.orchestrator.MealEngineV2`
```python
class MealEngineV2:
    """V2 meal generation pipeline."""
    async def generate_meal(self, constraints: MealConstraints) -> GeneratedMeal: ...
    # 1. Pick archetype
    # 2. LLM fills slots with ingredients + grams
    # 3. Resolve each ingredient via IngredientMatcher
    # 4. Look up nutrition via NutritionRouter
    # 5. Normalize units via UnitNormalizer
    # 6. Score via MealScorer
    # 7. Auto-regenerate if score < 70 (max 3 retries)
    # 8. Return meal with resolved codes + match confidence
```

---

## Build Order (Tasks)

### Phase 1: Database Schema & Migrations

#### Task 1: V2Region model + migration

**Files:**
- Create: `backend/app/models/v2_regions.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/alembic/env.py`
- Create: `backend/alembic/versions/create_v2_regions_table.py`

- [ ] **Step 1: Create V2Region SQLAlchemy model**

```python
# backend/app/models/v2_regions.py
from sqlalchemy import Column, Integer, String, Text
from app.database.connection import Base

class V2Region(Base):
    __tablename__ = "v2_regions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(Integer, nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
```

- [ ] **Step 2: Register model in `__init__.py` and `env.py`**

Add `V2Region` to `models/__init__.py` imports and `alembic/env.py` imports.

- [ ] **Step 3: Generate and review Alembic migration**

```bash
cd backend && .venv/Scripts/activate && python -m alembic revision --autogenerate -m "create v2_regions table"
```

Verify the generated migration creates `v2_regions` with columns: id, code, name, description.

- [ ] **Step 4: Run migration**

```bash
python -m alembic upgrade head
```

- [ ] **Step 5: Commit**

```bash
git add app/models/v2_regions.py app/models/__init__.py alembic/
git commit -m "feat: add v2_regions table for IFCT region lookup"
```

---

#### Task 2: V2Ingredient model + migration

**Files:**
- Create: `backend/app/models/v2_ingredients.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/alembic/env.py`
- Create: `backend/alembic/versions/create_v2_ingredients_table.py`

- [ ] **Step 1: Create V2Ingredient SQLAlchemy model**

```python
# backend/app/models/v2_ingredients.py
from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Text,
    CheckConstraint, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
import uuid
from app.database.connection import Base

class V2Ingredient(Base):
    __tablename__ = "v2_ingredients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(10), nullable=False, unique=True)  # IFCT code: A001
    name = Column(String(255), nullable=False)
    scientific_name = Column(String(255), nullable=True)
    food_group = Column(String(100), nullable=False)
    region_code = Column(Integer, ForeignKey("v2_regions.code"), nullable=True)

    # Multilingual
    regional_names = Column(JSONB, nullable=False, default=dict)
    search_aliases = Column(ARRAY(Text), nullable=False, default=list)
    diet_tags = Column(ARRAY(Text), nullable=False, default=list)

    # Form
    form = Column(String(20), nullable=False, server_default="unspecified")

    # Macros (per 100g)
    kcal = Column(Float, nullable=False)
    enerc_kj = Column(Float, nullable=False)
    protein_g = Column(Float, nullable=False)
    fat_g = Column(Float, nullable=False)
    carbs_g = Column(Float, nullable=False)
    fiber_g = Column(Float, nullable=False)
    sugar_g = Column(Float, nullable=True)
    starch_g = Column(Float, nullable=True)

    # Fats breakdown
    sat_fat_g = Column(Float, nullable=True)
    mufa_g = Column(Float, nullable=True)
    pufa_g = Column(Float, nullable=True)
    trans_fat_g = Column(Float, nullable=True)
    omega3_g = Column(Float, nullable=True)
    omega6_g = Column(Float, nullable=True)
    cholesterol_mg = Column(Float, nullable=True)

    # Minerals (mg)
    calcium_mg = Column(Float, nullable=True)
    iron_mg = Column(Float, nullable=True)
    magnesium_mg = Column(Float, nullable=True)
    zinc_mg = Column(Float, nullable=True)
    sodium_mg = Column(Float, nullable=True)
    potassium_mg = Column(Float, nullable=True)
    phosphorus_mg = Column(Float, nullable=True)

    # Vitamins
    vit_a_mcg = Column(Float, nullable=True)
    vit_c_mg = Column(Float, nullable=True)
    vit_d_mcg = Column(Float, nullable=True)
    vit_b_mg = Column(Float, nullable=True)
    vit_e_mg = Column(Float, nullable=True)
    folate_mcg = Column(Float, nullable=True)

    # Other composition
    water_g = Column(Float, nullable=True)
    ash_g = Column(Float, nullable=True)

    # Raw data passthrough
    raw_ifct_data = Column(JSONB, nullable=False)
    nutrient_errors = Column(JSONB, nullable=True)

    # Data quality flags (set during seed validation)
    # Values: NULL (clean), 'suspect_macros', 'energy_derived', 'suspect_fat'
    data_quality = Column(String(50), nullable=True)

    # Metadata
    data_source = Column(String(50), nullable=False, server_default="ifct_2017")
    confidence = Column(String(20), nullable=False, server_default="verified")

    # App-specific (populated later)
    app_serving_units = Column(JSONB, nullable=True)
    meal_archetype_roles = Column(ARRAY(Text), nullable=True)
    custom_aliases = Column(ARRAY(Text), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("form IN ('raw', 'cooked', 'unspecified')", name="check_v2_ingredients_form"),
        Index("ix_v2_ingredients_food_group", "food_group"),
        Index("ix_v2_ingredients_search_aliases", "search_aliases", postgresql_using="gin"),
        Index("ix_v2_ingredients_diet_tags", "diet_tags", postgresql_using="gin"),
        Index("ix_v2_ingredients_form", "form"),
    )
```

- [ ] **Step 2: Register model, generate migration, run it**

Same pattern as Task 1. Add to `__init__.py` and `env.py`, then:

```bash
python -m alembic revision --autogenerate -m "create v2_ingredients table"
python -m alembic upgrade head
```

- [ ] **Step 3: Commit**

---

### Phase 2: IFCT Seed Script

#### Task 3: Node.js seed script (CSV → JSON)

**Files:**
- Create: `ifct-test/seed_ifct.js`

This script reads the IFCT CSV, transforms each row, and writes `ifct_seed_data.json`.

- [ ] **Step 1: Write seed_ifct.js**

Key transformations:
1. Parse CSV header to extract field codes (format: `"Display Name; field_code"`)
2. For each of 528 foods:
   - Extract `code`, `name`, `scie` (scientific name), `grup`, `regn`, `tags`, `lang`
   - Compute `kcal = enerc / 4.184`
   - Map macro fields: `protcnt`, `fatce`, `choavldf`, `fibtg`, `water`, `ash`
   - Map fat breakdown: `fasat`, `fams`, `fapu`, `fatrn`, `facn3`, `facn6`
   - Map sugar/starch: `fsugar`, `starch`
   - Map minerals (multiply by 1000 for mg): `ca`, `fe`, `mg`, `zn`, `na`, `k`, `p`
   - Map vitamins: `vita` (×1e6 → mcg), `vitc` (×1000 → mg), `vitd` (×1e6 → mcg), `vitb` (×1000 → mg), `vite` (×1000 → mg), `folsum` (×1e6 → mcg)
   - Map cholesterol: `cholc` × 1000 → mg
   - Parse `lang` field into `regional_names` JSONB + `search_aliases` array
   - Split `tags` into `diet_tags` array
   - Infer `form` from name keywords (raw/cooked/unspecified)
   - Collect all `_e` fields into `nutrient_errors` JSONB
   - Store full row as `raw_ifct_data` JSONB
3. **Data quality checks** (set `data_quality` field per food):
   - **Macro-Calorie Consistency**: `calc_kcal = (protein × 4) + (carbs × 4) + (fat × 9)`. If `|calc - stored| / stored > 15%`, set `data_quality = 'suspect_macros'`. (Known example: chicken leg shows 383 kcal but macros compute to ~192.)
   - **Zero-Calorie Trap**: If `kcal = 0` but protein/fat/carbs are non-zero, use `calc_kcal` as fallback, set `data_quality = 'energy_derived'`. (Known example: ghee returns 0 kcal from IFCT.)
   - **Fats and Oils Sanity**: Foods in `"Fats and Oils"` group should have fat 95-100g and kcal 850-900. Flag outliers as `data_quality = 'suspect_fat'`.
   - **Multiple Entries Per Common Name**: For common names (`ghee`, `rice`, `dal`, `paneer`, `chicken`, `milk`, `curd`, `wheat`, `egg`, `fish`), log all entries sharing that base name so we know disambiguation is needed at match time.
4. Write JSON array to `ifct_seed_data.json`
5. Log summary report:
   - Count per food_group
   - Count per `data_quality` flag (suspect_macros, energy_derived, suspect_fat, clean)
   - Plant foods with cholesterol > 0 (warnings)
   - Animal foods with cholesterol = 0 (warnings)
   - Count of `form = 'unspecified'`
   - Duplicate common name groups (from check #4)

- [ ] **Step 2: Run and verify output**

```bash
cd ifct-test && node seed_ifct.js
```

Expected: `ifct_seed_data.json` with 528 entries, validation report logged to console.

- [ ] **Step 3: Commit**

---

#### Task 4: Python seed loader (JSON → PostgreSQL)

**Files:**
- Create: `backend/scripts/seed/load_ifct_seed.py`

- [ ] **Step 1: Write Python loader**

Reads `ifct_seed_data.json`, upserts into `v2_ingredients` and `v2_regions` tables. Idempotent: uses `ON CONFLICT (code) DO UPDATE`.

```python
# Pseudostructure
def load_regions(db):
    """Insert 6 regions if not present."""
    REGIONS = {1: "North", 2: "South", 3: "East", 4: "West", 5: "Central", 6: "North-East"}
    for code, name in REGIONS.items():
        # upsert

def load_ingredients(db, json_path):
    """Load ifct_seed_data.json → v2_ingredients.
    The JSON already contains data_quality flags set by seed_ifct.js.
    Use merge() for upsert behavior (idempotent re-runs)."""
    data = json.load(open(json_path))
    for item in data:
        # Map JSON keys to V2Ingredient columns
        # data_quality comes pre-set from seed_ifct.js

def run_validation(db):
    """Post-seed validation report."""
    # Count per food_group
    # Count per data_quality flag (suspect_macros, energy_derived, suspect_fat, clean)
    # Plant food groups with cholesterol > 0
    # Animal food groups with cholesterol = 0
    # Count form='unspecified'
    # Duplicate common names (ghee, rice, dal, etc.)

def report_duplicate_names(db):
    """Log ingredients sharing common base names for disambiguation awareness."""
    COMMON_NAMES = ["ghee", "rice", "dal", "paneer", "chicken", "milk", "curd",
                    "wheat", "egg", "fish", "oil", "butter", "potato", "onion"]
    for name in COMMON_NAMES:
        matches = db.query(V2Ingredient).filter(
            V2Ingredient.name.ilike(f"%{name}%")
        ).all()
        if len(matches) > 1:
            print(f"  '{name}' → {len(matches)} entries: {[m.name for m in matches]}")
```

- [ ] **Step 2: Run loader**

```bash
cd backend && .venv/Scripts/activate && python scripts/seed/load_ifct_seed.py --json-path ../ifct-test/ifct_seed_data.json
```

- [ ] **Step 3: Commit**

---

### Phase 3: Nutrition Provider Router

#### Task 5: IFCT local nutrition provider

**Files:**
- Create: `backend/app/services/meal_engine/nutrition/providers/ifct_provider.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_ifct_provider.py
async def test_ifct_lookup_exact_match():
    """IFCT provider finds 'Bajra' by exact name."""
    provider = IFCTProvider(db_session)
    result = await provider.lookup("Bajra")
    assert result is not None
    assert result.source == "ifct_2017"
    assert result.protein > 0

async def test_ifct_lookup_alias_match():
    """IFCT provider finds 'Pearl millet' (English alias for Bajra)."""
    provider = IFCTProvider(db_session)
    result = await provider.lookup("Pearl millet")
    assert result is not None
```

- [ ] **Step 2: Implement IFCTProvider**

Extends the existing `NutritionProvider` ABC from `ml_diet_pipeline/nutrition/providers/base.py`. Queries `v2_ingredients` by name (ILIKE), then by `search_aliases` (array contains).

- [ ] **Step 3: Run tests, commit**

---

#### Task 6: Edamam provider + response cache

**Files:**
- Create: `backend/app/models/v2_external_nutrition_cache.py`
- Create: `backend/app/services/meal_engine/nutrition/providers/edamam_provider.py`
- Modify: `backend/app/core/config.py` (add `EDAMAM_APP_ID`, `EDAMAM_APP_KEY`)
- Create: migration for `v2_external_nutrition_cache`

- [ ] **Step 1: Create V2ExternalNutritionCache model**

```python
# backend/app/models/v2_external_nutrition_cache.py
class V2ExternalNutritionCache(Base):
    __tablename__ = "v2_external_nutrition_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_key = Column(String(255), nullable=False, unique=True)  # lowercase trimmed
    provider = Column(String(50), nullable=False)                  # 'edamam' or 'usda'
    response_data = Column(JSONB, nullable=False)                  # per-100g macros
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)    # optional 30-day TTL
```

- [ ] **Step 2: Add Edamam env vars to config**

```python
# In NutritionAPISettings or new MealEngineV2Settings:
edamam_app_id: Optional[str] = Field(default=None, env="EDAMAM_APP_ID")
edamam_app_key: Optional[str] = Field(default=None, env="EDAMAM_APP_KEY")
```

- [ ] **Step 3: Implement EdamamProvider**

Extends `NutritionProvider` ABC. Checks cache first (`query_key = name.lower().strip()`), then calls Edamam API, caches response. Returns `None` gracefully if env vars missing.

- [ ] **Step 4: Generate migration, run it, commit**

---

#### Task 6b: Cuisine-aware nutrition router

**Files:**
- Create: `backend/app/services/meal_engine/nutrition/router.py`

- [ ] **Step 1: Write failing test**

```python
async def test_router_indian_uses_ifct_first():
    """For Indian cuisine, IFCT is tried before Edamam."""
    router = NutritionRouter(db_session)
    result = await router.lookup("Bajra", cuisine="indian")
    assert result.source == "ifct_2017"

async def test_router_western_uses_usda_then_edamam():
    """For Western cuisine, USDA is primary, Edamam fallback."""
    router = NutritionRouter(db_session)
    result = await router.lookup("Chicken Breast", cuisine="mediterranean")
    assert result.source in ("usda", "edamam")

async def test_router_no_edamam_keys_skips_gracefully():
    """If EDAMAM keys missing, Edamam provider is skipped without error."""
    router = NutritionRouter(db_session, edamam_app_id=None, edamam_app_key=None)
    # Should not raise, just skip Edamam in chain
```

- [ ] **Step 2: Implement NutritionRouter**

```python
class NutritionRouter:
    CUISINE_PROVIDER_CHAIN = {
        "indian": ["ifct", "edamam", "usda"],
        "mediterranean": ["usda", "edamam"],
        "italian": ["usda", "edamam"],
        "default": ["usda", "edamam"],
    }
    async def lookup(self, name: str, cuisine: str) -> Optional[NutritionResult]:
        # Iterate providers in chain order
        # Skip edamam if keys not configured
        # All edamam calls go through cache layer
```

- [ ] **Step 3: Run tests, commit**

---

### Phase 4: Config Layer

#### Task 7: Indian unit normalizer

**Files:**
- Create: `backend/app/services/meal_engine/config/unit_conversions.json`
- Create: `backend/app/services/meal_engine/unit_normalizer.py`
- Create: `backend/tests/test_unit_normalizer.py`

- [ ] **Step 1: Create config JSON**

```json
{
  "katori": 150,
  "roti": 40,
  "phulka": 30,
  "paratha": 60,
  "chapati": 40,
  "naan": 80,
  "cup": 240,
  "tbsp": 15,
  "tsp": 5,
  "glass": 250,
  "bowl": 200,
  "slice": 30,
  "piece": 50,
  "idli": 40,
  "dosa": 80,
  "vada": 50,
  "puri": 25
}
```

- [ ] **Step 2: Write failing tests**

```python
def test_normalize_katori():
    n = UnitNormalizer()
    assert n.normalize(1, "katori", "dal") == 150.0

def test_normalize_roti():
    n = UnitNormalizer()
    assert n.normalize(2, "phulkas", "wheat") == 60.0  # 2 * 30

def test_normalize_unknown_unit_returns_grams():
    n = UnitNormalizer()
    assert n.normalize(100, "g", "rice") == 100.0

def test_normalize_plural_stripping():
    n = UnitNormalizer()
    assert n.normalize(1, "rotis", "wheat") == 40.0  # strips trailing 's'
```

- [ ] **Step 3: Implement UnitNormalizer**

Loads `unit_conversions.json`, strips plurals, returns `quantity * grams_per_unit`. Falls through to raw grams for unknown units.

- [ ] **Step 4: Run tests, commit**

---

#### Task 8: Meal archetypes config

**Files:**
- Create: `backend/app/services/meal_engine/config/archetypes.json`

- [ ] **Step 1: Create archetypes JSON**

Structure per the spec — Indian (thali, one_pot, curry_bread, tiffin), Mediterranean (grain_bowl, mezze_plate, protein_salad_pita), Italian (pasta_side, protein_starch_veg).

```json
{
  "indian": {
    "thali": {
      "name": "Thali",
      "slots": [
        {"role": "sabzi", "allowed_groups": ["Roots and Tubers", "Other Vegetables", "Green Leafy Vegetables"]},
        {"role": "dal", "allowed_groups": ["Pulses and Legumes"]},
        {"role": "grain", "allowed_groups": ["Cereals and Millets"]},
        {"role": "side", "allowed_groups": ["Milk and Milk Products", "Condiments and Spices"]}
      ],
      "meal_types": ["lunch", "dinner"]
    },
    "one_pot": { ... },
    "curry_bread": { ... },
    "tiffin": { ... }
  },
  "mediterranean": { ... },
  "italian": { ... }
}
```

- [ ] **Step 2: Commit**

---

#### Task 9: Pairing rules (DB table + seed JSON + validator)

**Files:**
- Create: `backend/app/models/v2_pairing_rules.py`
- Create: `backend/app/services/meal_engine/config/pairing_rules_seed.json` (version-controlled seed data)
- Create: `backend/scripts/seed/seed_pairing_rules.py`
- Create: migration for `v2_pairing_rules`

- [ ] **Step 1: Create V2PairingRule model**

```python
# backend/app/models/v2_pairing_rules.py
class V2PairingRule(Base):
    __tablename__ = "v2_pairing_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cuisine = Column(String(50), nullable=False)
    item = Column(String(100), nullable=False)
    preferred = Column(ARRAY(Text), nullable=False, default=list)
    acceptable = Column(ARRAY(Text), nullable=False, default=list)
    incompatible = Column(ARRAY(Text), nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("cuisine", "item", name="uq_v2_pairing_rules_cuisine_item"),
    )
```

- [ ] **Step 2: Create seed JSON (version-controlled)**

```json
{
  "indian": [
    {"item": "rajma", "preferred": ["rice"], "acceptable": ["roti"], "incompatible": ["dosa", "idli"]},
    {"item": "sambar", "preferred": ["rice", "idli", "dosa", "vada"], "acceptable": [], "incompatible": ["roti", "naan"]},
    {"item": "chole", "preferred": ["bhature", "rice", "roti"], "acceptable": ["naan"], "incompatible": ["dosa"]},
    {"item": "palak paneer", "preferred": ["roti", "naan"], "acceptable": ["rice"], "incompatible": ["dosa", "idli"]},
    {"item": "dal", "preferred": ["rice", "roti"], "acceptable": ["naan", "paratha"], "incompatible": ["dosa"]},
    {"item": "biryani", "preferred": ["raita"], "acceptable": ["salad"], "incompatible": ["roti", "naan"]},
    {"item": "idli", "preferred": ["sambar", "chutney"], "acceptable": ["podi"], "incompatible": ["roti", "naan"]},
    {"item": "dosa", "preferred": ["sambar", "chutney"], "acceptable": ["potato curry"], "incompatible": ["roti"]}
  ]
}
```

- [ ] **Step 3: Create seed script**

`scripts/seed/seed_pairing_rules.py` — reads `pairing_rules_seed.json`, upserts into `v2_pairing_rules`. Idempotent via `ON CONFLICT (cuisine, item) DO UPDATE`.

- [ ] **Step 4: Write PairingValidator**

Queries `v2_pairing_rules` table (cached in memory on first call). Used by the scorer.

```python
# tests/test_pairing_validator.py
def test_rajma_rice_is_valid(db):
    validator = PairingValidator(db)
    assert validator.is_valid_pairing("rajma", "rice", "indian") == True

def test_sambar_roti_is_invalid(db):
    validator = PairingValidator(db)
    assert validator.is_valid_pairing("sambar", "roti", "indian") == False
```

- [ ] **Step 5: Generate migration, seed, run tests, commit**

---

#### Task 10: Goal-based macro ordering + scoring weights config

**Files:**
- Create: `backend/app/services/meal_engine/config/goal_macro_order.json`
- Create: `backend/app/services/meal_engine/config/scoring_weights.json`

- [ ] **Step 1: Create goal macro ordering config**

```json
{
  "muscle_gain": ["protein", "carbs", "fat", "fiber"],
  "fat_loss": ["calories", "protein", "fiber", "carbs", "fat"],
  "keto": ["fat", "protein", "net_carbs"],
  "endurance": ["carbs", "protein", "fat"],
  "maintenance": ["calories", "protein", "carbs", "fat", "fiber"]
}
```

- [ ] **Step 2: Create scoring weights config**

```json
{
  "macro_accuracy": {"max_points": 30, "full_marks_threshold": 0.05, "zero_marks_threshold": 0.30},
  "plate_composition": {"max_points": 20, "points_per_slot": 5},
  "culinary_coherence": {"max_points": 20, "archetype_match_points": 10, "pairing_valid_points": 10},
  "micro_diversity": {"max_points": 15, "points_per_food_group": 1},
  "goal_alignment": {"max_points": 10},
  "practicality": {"max_points": 5, "min_portion_g": 30, "max_portion_g": 400}
}
```

- [ ] **Step 3: Commit**

---

#### Task 10b: Config loader (startup + hot-reload)

**Files:**
- Create: `backend/app/services/meal_engine/config/loader.py`

- [ ] **Step 1: Implement ConfigLoader**

```python
class ConfigLoader:
    """Loads JSON configs at startup, validates schema, hot-reloads in dev mode."""
    def __init__(self, config_dir: Path, dev_mode: bool = False):
        self._config_dir = config_dir
        self._dev_mode = dev_mode
        self._archetypes = None
        self._scoring_weights = None
        self._unit_conversions = None
        self._goal_macro_order = None
        self._load_all()

    def _load_all(self):
        self._archetypes = self._load_and_validate("archetypes.json")
        self._scoring_weights = self._load_and_validate("scoring_weights.json")
        self._unit_conversions = self._load_and_validate("unit_conversions.json")
        self._goal_macro_order = self._load_and_validate("goal_macro_order.json")

    def _load_and_validate(self, filename: str) -> dict:
        path = self._config_dir / filename
        data = json.loads(path.read_text())
        # Basic validation: non-empty, expected top-level keys
        if not data:
            raise ValueError(f"Config {filename} is empty")
        return data

    @property
    def archetypes(self) -> dict:
        if self._dev_mode:
            self._archetypes = self._load_and_validate("archetypes.json")
        return self._archetypes

    # Same pattern for scoring_weights, unit_conversions, goal_macro_order

    def reload(self) -> None:
        self._load_all()
```

- [ ] **Step 2: Commit**

---

### Phase 5: Embeddings + Fuzzy Matching Layer

#### Task 11a: V2 ingredient embeddings (pgvector)

**Files:**
- Create: `backend/app/models/v2_ingredient_embeddings.py`
- Create: `backend/scripts/seed/generate_embeddings.py`
- Create: migration for `v2_ingredient_embeddings` (enables pgvector extension)

- [ ] **Step 1: Create V2IngredientEmbedding model**

```python
# backend/app/models/v2_ingredient_embeddings.py
from pgvector.sqlalchemy import Vector

class V2IngredientEmbedding(Base):
    __tablename__ = "v2_ingredient_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ingredient_id = Column(UUID(as_uuid=True), ForeignKey("v2_ingredients.id"), nullable=False, unique=True)
    embedding = Column(Vector(384), nullable=False)  # all-MiniLM-L6-v2 output
    text_used = Column(String(500), nullable=False)   # concatenation used
    model_name = Column(String(100), nullable=False, server_default="all-MiniLM-L6-v2")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

Migration must include: `op.execute("CREATE EXTENSION IF NOT EXISTS vector")` before table creation. HNSW index on `embedding` column for cosine similarity.

- [ ] **Step 2: Write embedding generation script**

`scripts/seed/generate_embeddings.py`:
- Loads `sentence-transformers/all-MiniLM-L6-v2` (lazy import)
- For each V2Ingredient: concatenate `name + scientific_name + food_group + top 3 regional aliases`
- Encode, L2-normalize the 384-dim vector
- Upsert into `v2_ingredient_embeddings`
- Idempotent: skips ingredients that already have embeddings

```bash
cd backend && .venv/Scripts/activate && python scripts/seed/generate_embeddings.py
```

- [ ] **Step 3: Generate migration, run embedding script, commit**

---

#### Task 11b: Ingredient matcher (cascading match)

**Files:**
- Create: `backend/app/services/meal_engine/matching/ingredient_matcher.py`
- Create: `backend/tests/test_ingredient_matcher.py`

- [ ] **Step 1: Write failing tests**

```python
async def test_exact_match():
    matcher = IngredientMatcher(db)
    result = await matcher.match("Bajra")
    assert result.match_method == "exact"
    assert result.confidence == 1.0

async def test_alias_match():
    matcher = IngredientMatcher(db)
    result = await matcher.match("Pearl millet")  # English alias for Bajra
    assert result.match_method == "alias"
    assert result.confidence >= 0.95

async def test_fuzzy_match():
    matcher = IngredientMatcher(db)
    result = await matcher.match("Bajraa")  # Typo
    assert result.match_method == "fuzzy"
    assert result.confidence >= 0.6

async def test_embedding_match():
    matcher = IngredientMatcher(db)
    result = await matcher.match("pearl grain millet")  # Semantic match
    assert result.match_method == "embedding"
    assert result.confidence >= 0.75

async def test_no_match():
    matcher = IngredientMatcher(db)
    result = await matcher.match("xyznonexistent")
    assert result.ingredient_code is None
    assert result.confidence == 0.0
```

- [ ] **Step 2: Implement IngredientMatcher**

4-stage cascade:
1. **Exact**: `SELECT * FROM v2_ingredients WHERE LOWER(name) = LOWER(:name)`
2. **Alias**: `SELECT * FROM v2_ingredients WHERE LOWER(:name) = ANY(search_aliases)` (store lowercased aliases at seed time)
3. **Fuzzy**: Use `rapidfuzz.fuzz.ratio` (already in requirements.txt) against name + aliases. Threshold 0.6. Cache name→code mapping in memory on first use to avoid full table scan per call.
4. **Embedding**: Embed query via `all-MiniLM-L6-v2` (lazy import), then pgvector nearest-neighbor: `SELECT ... ORDER BY embedding <=> :query_vec LIMIT 1`. Cosine similarity threshold 0.75.

Log low-confidence matches (<0.8) for manual review — candidates for adding to `custom_aliases`.

- [ ] **Step 3: Run tests, commit**

---

### Phase 6: Meal Scoring Module

#### Task 12: Meal scorer

**Files:**
- Create: `backend/app/services/meal_engine/scoring/scorer.py`
- Create: `backend/tests/test_meal_scorer.py`

- [ ] **Step 1: Write failing tests**

```python
def test_perfect_meal_scores_high():
    scorer = MealScorer()
    meal = {
        "archetype": "thali",
        "components": [
            {"name": "Rajma", "role": "dal", "grams": 100, "food_group": "Pulses and Legumes"},
            {"name": "Rice", "role": "grain", "grams": 150, "food_group": "Cereals and Millets"},
            {"name": "Palak", "role": "sabzi", "grams": 120, "food_group": "Green Leafy Vegetables"},
            {"name": "Curd", "role": "side", "grams": 100, "food_group": "Milk and Milk Products"},
        ],
        "macros": {"calories": 550, "protein": 22, "carbs": 80, "fat": 12, "fiber": 8},
        "cuisine": "indian",
    }
    target = {"calories": 600, "protein": 25, "carbs": 85, "fat": 15}
    result = scorer.score_deterministic(meal, target, "maintenance")
    assert result.total >= 70

def test_culturally_incoherent_meal_penalized():
    scorer = MealScorer()
    meal = {
        "archetype": "thali",
        "components": [
            {"name": "Sambar", "role": "dal", "grams": 100, "food_group": "Pulses and Legumes"},
            {"name": "Roti", "role": "grain", "grams": 80, "food_group": "Cereals and Millets"},  # sambar+roti = bad
        ],
        "macros": {"calories": 400, "protein": 15, "carbs": 60, "fat": 8, "fiber": 5},
        "cuisine": "indian",
    }
    target = {"calories": 600, "protein": 25, "carbs": 85, "fat": 15}
    result = scorer.score_deterministic(meal, target, "maintenance")
    assert result.culinary_coherence < 15  # penalized
```

- [ ] **Step 2: Implement deterministic scorer**

6 dimensions per spec:
- **Macro Accuracy (30 pts)**: % deviation from target. Full marks at <=5%, zero at >=30%.
- **Plate Composition (20 pts)**: Protein + carb + fat + veg all present. 5 pts per slot filled.
- **Culinary Coherence (20 pts)**: Matches archetype slots. Pairings valid per pairing_rules.json. Penalize incompatible pairs.
- **Micronutrient Diversity (15 pts)**: Count distinct food_groups. 1pt per unique group, cap at 15.
- **Goal Alignment (10 pts)**: Priority macro (from goal_macro_order.json) is prominent.
- **Practicality (5 pts)**: Portions between 30-400g each, no exotic ingredients.

- [ ] **Step 3: Implement LLM-judge scoring method (separate)**

A lightweight Groq call with a rubric: "Rate this meal 0-20 for culinary coherence. Does it feel like a real meal?" Returns a number. Used as override/supplement to the deterministic coherence score.

- [ ] **Step 4: Combine into `score()` method**

```python
async def score(self, meal, target_macros, user_goal) -> ScoreBreakdown:
    det = self.score_deterministic(meal, target_macros, user_goal)
    if det.total >= 85:
        return det  # skip LLM call for clearly good meals
    llm_coherence = await self.score_llm_coherence(meal)
    # Blend: replace deterministic coherence with average of both
    det.culinary_coherence = (det.culinary_coherence + llm_coherence) / 2
    det.total = sum of all dimensions
    det.band = "serve" if total >= 85 else "review" if total >= 70 else "regenerate"
    return det
```

- [ ] **Step 5: Run tests, commit**

---

### Phase 7: V2 Generation Pipeline + API

#### Task 13: V2 prompt builder

**Files:**
- Create: `backend/app/services/meal_engine/generation/prompt_builder.py`

- [ ] **Step 1: Implement archetype-first prompt**

The prompt instructs the LLM to:
1. Pick an archetype from the provided list
2. Fill each slot with a specific ingredient + grams
3. Specify cooked vs raw for grains/legumes/meats
4. Output structured JSON:

```json
{
  "archetype": "thali",
  "dish_name": "Rajma Chawal Thali",
  "components": [
    {"name": "Rajma, cooked", "grams": 100, "role": "dal", "food_group": "Pulses and Legumes"},
    {"name": "Rice, cooked", "grams": 150, "role": "grain", "food_group": "Cereals and Millets"},
    {"name": "Palak", "grams": 120, "role": "sabzi", "food_group": "Green Leafy Vegetables"},
    {"name": "Curd", "grams": 100, "role": "side", "food_group": "Milk and Milk Products"}
  ],
  "cultural_note": "Classic North Indian comfort meal",
  "prep_time_minutes": 15
}
```

Key constraints in prompt:
- "Adjust PORTION SIZES to hit macros within +-5%, do NOT swap ingredients"
- "Always specify cooked or raw for: rice, dal, lentils, chicken, fish, eggs"
- "Break composite dishes into base ingredients with grams"

- [ ] **Step 2: Commit**

---

#### Task 14: V2 orchestrator

**Files:**
- Create: `backend/app/services/meal_engine/orchestrator.py`

- [ ] **Step 1: Implement MealEngineV2**

```python
class MealEngineV2:
    def __init__(self, db: Session):
        self.matcher = IngredientMatcher(db)
        self.nutrition_router = NutritionRouter(db)
        self.scorer = MealScorer()
        self.normalizer = UnitNormalizer()
        self.prompt_builder = V2PromptBuilder()

    async def generate_meal(self, constraints: MealConstraints) -> GeneratedMeal:
        best_meal = None
        best_score = 0

        for attempt in range(3):
            # 1. Build prompt with archetype + constraints
            prompt = self.prompt_builder.build(constraints, attempt)

            # 2. Call LLM
            raw_meal = await self._call_llm(prompt)

            # 3. Resolve each ingredient
            resolved_components = []
            for comp in raw_meal["components"]:
                match = await self.matcher.match(comp["name"])
                nutrition = await self.nutrition_router.lookup(comp["name"], constraints.cuisine)
                grams = self.normalizer.normalize(comp.get("quantity", comp["grams"]),
                                                   comp.get("unit", "g"), comp["name"])
                resolved_components.append({
                    "llm_name": comp["name"],
                    "resolved_code": match.ingredient_code,
                    "resolved_name": match.ingredient_name,
                    "match_method": match.match_method,
                    "match_confidence": match.confidence,
                    "grams": grams,
                    "role": comp["role"],
                    "nutrition_per_100g": nutrition.to_macros_dict() if nutrition else None,
                })

            # 4. Calculate meal macros
            meal_macros = self._sum_macros(resolved_components)

            # 5. Score
            meal_data = {**raw_meal, "components": resolved_components, "macros": meal_macros}
            score = await self.scorer.score(meal_data, constraints.target_macros, constraints.goal)

            if score.total > best_score:
                best_meal = meal_data
                best_score = score.total

            if score.band != "regenerate":
                break  # Good enough

        return GeneratedMeal(
            meal=best_meal,
            score=best_score,
            quality_warning=best_score < 70,
        )
```

- [ ] **Step 2: Commit**

---

#### Task 15: V2 API endpoint + schemas

**Files:**
- Create: `backend/app/schemas/meal_engine_v2.py`
- Create: `backend/app/api/endpoints/meal_engine_v2.py`
- Modify: `backend/app/api/router.py`

- [ ] **Step 1: Create Pydantic schemas**

```python
# schemas/meal_engine_v2.py
class V2MealRequest(BaseModel):
    plan_type: Literal["daily", "weekly"] = "daily"
    # Uses constraints from user's active HealthContextDocument

class V2MealComponent(BaseModel):
    llm_name: str
    resolved_code: Optional[str]
    resolved_name: str
    match_method: str
    match_confidence: float
    grams: float
    role: str

class V2MealResponse(BaseModel):
    id: UUID
    archetype: str
    dish_name: str
    components: list[V2MealComponent]
    macros: dict  # Ordered by user's goal
    score: float
    score_breakdown: dict
    quality_warning: bool
    cultural_note: Optional[str]
    prep_time_minutes: Optional[int]
```

- [ ] **Step 2: Create endpoint**

```python
# api/endpoints/meal_engine_v2.py
router = APIRouter(prefix="/v2/generate-meal", tags=["Meal Engine V2"])

@router.post("/daily", response_model=V2DailyPlanResponse)
async def generate_daily_v2(request: V2MealRequest, ...):
    ...
```

- [ ] **Step 3: Register in router.py**

```python
# In api/router.py, add:
from app.api.endpoints.meal_engine_v2 import router as meal_engine_v2_router
api_router.include_router(meal_engine_v2_router)
```

- [ ] **Step 4: Add feature flag in config**

```python
# In Settings class:
enable_meal_engine_v2: bool = Field(default=False)
```

- [ ] **Step 5: Commit**

---

### Phase 8: Tests

#### Task 16: Integration and validation tests

**Files:**
- Create: `backend/tests/test_ifct_seed_validation.py`

- [ ] **Step 1: Write seed validation tests**

```python
# tests/test_ifct_seed_validation.py

def test_ingredient_count(db):
    """Should have ~528 ingredients after seed."""
    count = db.query(V2Ingredient).count()
    assert count >= 500

def test_all_food_groups_represented(db):
    """Every major IFCT food group should be present."""
    groups = db.query(V2Ingredient.food_group).distinct().all()
    assert len(groups) >= 10

def test_plant_foods_zero_cholesterol(db):
    """All plant food groups should have cholesterol = 0."""
    plant_groups = ["Cereals and Millets", "Green Leafy Vegetables", "Fruits", "Roots and Tubers"]
    violations = db.query(V2Ingredient).filter(
        V2Ingredient.food_group.in_(plant_groups),
        V2Ingredient.cholesterol_mg > 0
    ).all()
    for v in violations:
        warnings.warn(f"{v.name} ({v.food_group}): cholesterol={v.cholesterol_mg}mg")

def test_animal_foods_have_cholesterol(db):
    """Animal food groups should have cholesterol > 0."""
    animal_groups = ["Milk and Milk Products", "Egg and Egg Products", "Fish, Shellfish", "Meat and Poultry"]
    violations = db.query(V2Ingredient).filter(
        V2Ingredient.food_group.in_(animal_groups),
        V2Ingredient.cholesterol_mg == 0
    ).all()
    for v in violations:
        warnings.warn(f"{v.name} ({v.food_group}): cholesterol=0mg")

def test_macro_calorie_consistency(db):
    """Foods flagged suspect_macros should have >15% calorie deviation."""
    flagged = db.query(V2Ingredient).filter(
        V2Ingredient.data_quality == "suspect_macros"
    ).all()
    for f in flagged:
        calc = (f.protein_g * 4) + (f.carbs_g * 4) + (f.fat_g * 9)
        deviation = abs(calc - f.kcal) / f.kcal if f.kcal > 0 else 1.0
        assert deviation > 0.15, f"{f.name}: deviation {deviation:.1%} should be >15%"

def test_zero_calorie_trap_flagged(db):
    """Foods with energy_derived flag should have kcal > 0 (backfilled from macros)."""
    flagged = db.query(V2Ingredient).filter(
        V2Ingredient.data_quality == "energy_derived"
    ).all()
    for f in flagged:
        assert f.kcal > 0, f"{f.name}: energy_derived but kcal still 0"

def test_fats_and_oils_sanity(db):
    """Fats and Oils group: unflagged items should have fat ~95-100g, kcal ~850-900."""
    clean = db.query(V2Ingredient).filter(
        V2Ingredient.food_group == "Fats and Oils",
        V2Ingredient.data_quality.is_(None)
    ).all()
    for f in clean:
        assert 85 <= f.fat_g <= 100, f"{f.name}: fat_g={f.fat_g}"
        assert 750 <= f.kcal <= 950, f"{f.name}: kcal={f.kcal}"

def test_data_quality_flags_summary(db):
    """Log summary of data_quality flags for review (informational, always passes)."""
    from sqlalchemy import func as sqlfunc
    summary = db.query(
        V2Ingredient.data_quality, sqlfunc.count()
    ).group_by(V2Ingredient.data_quality).all()
    for flag, count in summary:
        print(f"  data_quality={flag or 'clean'}: {count}")
```

- [ ] **Step 2: Commit**

---

#### Task 17: Module README

**Files:**
- Create: `backend/app/services/meal_engine/README.md`

- [ ] **Step 1: Write README**

Cover:
- Architecture overview (single paragraph + diagram reference)
- How to run the seed script
- How to tune archetypes/pairings/scoring weights (edit JSON configs)
- How to add a new nutrition provider
- How to add a new cuisine
- Scoring dimensions and thresholds

- [ ] **Step 2: Commit**

---

## Summary: Deliverables Checklist vs Spec

| # | Spec Deliverable | Plan Task(s) | Status |
|---|-----------------|-------------|--------|
| 1 | New database tables (migrations) | Tasks 1, 2, 6, 9, 11a | Covered (v2_regions, v2_ingredients, v2_external_nutrition_cache, v2_pairing_rules, v2_ingredient_embeddings) |
| 2 | Nutrition provider router with pluggable sources | Tasks 5, 6, 6b | Covered (IFCT + Edamam cached + USDA, cuisine-routed) |
| 3 | Indian unit normalizer | Task 7 | Covered |
| 4 | Meal archetypes + pairing rules (seeded) | Tasks 8, 9 | Covered (JSON config + DB table seeded from JSON) |
| 5 | New meal generation prompt + pipeline | Tasks 13, 14 | Covered |
| 6 | Meal scoring module (hybrid) | Task 12 | Covered |
| 7 | Goal-based macro ordering in API responses | Task 10 | Covered |
| 8 | Feature flag + separate endpoint | Task 15 | Covered |
| 9 | Basic tests | Tasks 7, 9, 11b, 12, 16 | Covered |
| 10 | Module README | Task 17 | Covered |
| 11 | Fuzzy matching layer (4-stage cascade) | Task 11b | Covered (exact → alias → rapidfuzz → pgvector) |
| 12 | Embedding generation (seed-time) | Task 11a | Covered (all-MiniLM-L6-v2 → pgvector) |
| 13 | Meal record schema with resolved IFCT codes | Task 15 (V2MealComponent) | Covered |
| 14 | Seed validation and integrity reports | Tasks 3, 4, 16 | Covered (incl. data_quality flags) |
| 15 | External nutrition response cache | Task 6 | Covered (v2_external_nutrition_cache, Edamam) |
| 16 | Config loader with hot-reload | Task 10b | Covered |
