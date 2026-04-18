# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WellnessWay is a full-stack diet planning application. React/TypeScript frontend, FastAPI/Python backend, Supabase PostgreSQL database. Diet plans are generated via an ML pipeline (template-based math, not LLM calls) that selects meal templates, looks up nutrition data, and scales portions to calorie targets.

## Development Commands

### Backend (run from `backend/`)

```bash
# Install dependencies
pip install -r requirements.txt

# Run dev server
python start_backend.py
# or: uvicorn app.main:app --reload

# Database migrations
python -m alembic upgrade head
python -m alembic revision --autogenerate -m "description"
python -m alembic downgrade -1

# Tests
pytest tests/ -v
pytest tests/ -v --cov=app
pytest tests/test_health_calculations.py -v   # single file
pytest tests/ -m "property"                    # property-based only

# Lint & format
black app/
isort app/
flake8 app/
mypy app/ --ignore-missing-imports
```

### Frontend (run from `frontend/`)

```bash
npm install
npm start           # dev server on port 3000, proxies to localhost:8000
npm test            # jest
npm run lint        # eslint
npm run lint:fix
npm run format      # prettier
npm run type-check  # tsc --noEmit
npm run build
npm run deploy      # build + wrangler deploy (Cloudflare Workers)
```

## Architecture

### Backend (`backend/app/`)

- **Entry point**: `main.py` — FastAPI factory with lifespan events. Middleware stack: CORS -> Security -> RateLimit -> TrustedHost.
- **Config**: `core/config.py` — Pydantic v2 `BaseSettings` with nested settings classes (Database, Security, AI, Logging, etc.). Loads `.env` from repo root then `backend/.env`.
- **Routing**: `api/router.py` aggregates endpoint modules. All routes under `/api/v1`.
- **Auth**: Google OAuth + email/password with JWT (30 min access, 7 day refresh). Admin approval system for new users.
- **ML Diet Pipeline** (`services/ml_diet_pipeline/`): The core feature. Two paths controlled by `ENABLE_LLM_MEAL_SUGGESTIONS` env var:
  - **Hybrid path (new)**: LLM suggests ingredients -> nutrition API (USDA/API Ninjas) verifies macros -> cache in `food_items` -> assembler calculates portions. Falls back to template path on any failure.
  - **Template path (fallback)**: `discovery_engine.py` queries `food_items` DB -> `daily_assembler.py` scales portions -> `genai/service.py` names meals.
  - Both paths share: `daily_assembler.py` (protein-first portion scaler), `validation/engine.py`, `nutrition/engine.py`, `genai/service.py`.
  - New components: `suggestion/service.py` (LLM meal suggester), `nutrition/resolver.py` (cache + API + name simplification), `nutrition/providers/` (pluggable API providers).
- **Models**: SQLAlchemy ORM in `models/`. Key entities: User (with health metrics), HealthGoals, DietPreferences, HealthContextDocument (immutable versioned snapshots), DietPlan (JSON content), Chat/Message.
- **Database**: `database/connection.py` manages engine/sessions. Supabase PostgreSQL in prod, local Postgres for dev.
- **V2 Meal Engine** (`services/meal_engine/`): Parallel meal generation system (does NOT replace v1). Feature-flagged via `ENABLE_MEAL_ENGINE_V2` env var.
  - **Data**: 546 IFCT 2017 Indian foods in `v2_ingredients` table + 4 manual dairy entries. pgvector embeddings for semantic matching.
  - **Pipeline**: Archetype-first LLM prompt → IngredientMatcher (exact/alias/canonical/fuzzy/embedding) → NutritionRouter (IFCT→Edamam→USDA, cuisine-aware) → UnitNormalizer → MealScorer (6 deterministic dimensions + LLM-judge) → auto-retry on low scores.
  - **Config**: JSON files in `meal_engine/config/` for archetypes, scoring weights, unit conversions, pairing rules, canonical food defaults. Hot-reload in dev mode.
  - **DB tables**: `v2_ingredients`, `v2_regions`, `v2_pairing_rules`, `v2_ingredient_embeddings`, `v2_external_nutrition_cache`.
  - **API**: `POST /v2/meal-engine/generate-meal`, `POST /v2/meal-engine/generate-daily`.
  - **Tests**: `tests/test_unit_normalizer.py`, `tests/test_meal_scorer.py`, `tests/test_pairing_validator.py`, `tests/test_ingredient_matcher.py` (46 tests).
  - **Seed scripts** (run from `backend/`):
    1. `cd ../ifct-test && node seed_ifct.js` — IFCT CSV → JSON
    2. `python scripts/seed/load_ifct_seed.py --json-path ../ifct-test/ifct_seed_data.json` — JSON → PostgreSQL
    3. `python scripts/seed/seed_pairing_rules.py` — Pairing rules → DB
    4. `python scripts/seed/generate_embeddings.py` — sentence-transformers embeddings → pgvector
    5. `python scripts/seed/classify_forms_groq.py` — Groq LLM form classification (optional)

### Frontend (`frontend/src/`)

- **React 18 + TypeScript**, Create React App, Tailwind CSS, Framer Motion.
- **Context providers** (wrap app in `App.tsx`): AuthContext (tokens, OAuth), AppContext (global state), ThemeContext (dark/light).
- **API client**: `services/api.ts` — Axios instance with auth interceptors.
- **Routing**: React Router v6. ProtectedRoute component gates authenticated pages.

### Deployment

- Backend: Docker -> Google Cloud Run (deploys from `dev` branch via GitHub Actions `google-cloud-run.yml`)
- Frontend: Cloudflare Workers (`npm run deploy`)
- CI: `ci-cd.yml` runs tests + linting on PR/push to main/develop

## Critical Gotchas

### CORS/TrustedHosts in env vars must use semicolons, not JSON arrays
```
CORS_ORIGINS=https://example.com;http://localhost:3000      # correct
CORS_ORIGINS=["https://example.com","http://localhost:3000"] # breaks on gcloud deploy
```
`gcloud run deploy --set-env-vars` corrupts commas in JSON-style values.

### SQLAlchemy JSON field mutations are not auto-detected
```python
# WRONG — change won't persist
plan.content['days'][0] = new_day
db.commit()

# CORRECT
from sqlalchemy.orm.attributes import flag_modified
plan.content['days'][0] = new_day
flag_modified(plan, "content")
db.commit()
```

### ML pipeline uses lazy imports for heavy libraries
torch, sentence_transformers, etc. are imported inline within async handlers, not at module level. This avoids 30+ second Cloud Run cold starts. Preserve this pattern.

### Health calculations use Mifflin-St Jeor
BMR formulas and TDEE activity multipliers are in `services/health_calculations.py`. The specific constants matter for plan accuracy — don't change them without understanding the nutritional science.

### BaseHTTPMiddleware breaks Pydantic body parsing
The SecurityMiddleware uses `BaseHTTPMiddleware` which consumes the request body as bytes. New POST endpoints **cannot** use Pydantic model parameters directly. Use `Request` + manual JSON parse instead:
```python
# WRONG — will 422 with "Input should be a valid dictionary"
async def my_endpoint(request: MyModel, db: Session = Depends(get_db)): ...

# CORRECT — parse body manually
async def my_endpoint(raw_request: Request, db: Session = Depends(get_db)):
    body = await raw_request.body()
    request = MyModel(**json.loads(body)) if body else MyModel()
```

### V2 Meal Engine: sentence-transformers must be singleton
The embedding model (`all-MiniLM-L6-v2`, 90MB) must be cached at class level, not loaded per request. See `IngredientMatcher._embedding_model` pattern.

### React state updates with API responses
```typescript
// Create new object reference to trigger re-render
setPlan({...response.data});
```

## Environment Setup

Copy `.env.example` or `.env.supabase.example` to `.env` in the repo root. Key variables:
- `DATABASE_URL` — PostgreSQL connection string (format: `postgresql+psycopg://...`)
- `JWT_SECRET_KEY`, `SECRET_KEY` — token signing
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` — OAuth
- `CORS_ORIGINS` — semicolon-separated allowed origins
- `REACT_APP_API_URL` — backend URL for frontend (e.g., `http://localhost:8000/api/v1`)
- `ENABLE_LLM_MEAL_SUGGESTIONS` — `true` to use hybrid LLM+API path, `false` for template-only (default)
- `USDA_API_KEY` — USDA FoodData Central API key (free, primary nutrition provider)
- `API_NINJAS_API_KEY` — API Ninjas key (free, fallback nutrition provider)
- `GROQ_API_KEY` — Groq LLM key (used for meal suggestions and recipe naming)
- `ENABLE_MEAL_ENGINE_V2` — `true` to enable V2 meal engine endpoints (default: `false`)
- `EDAMAM_APP_ID`, `EDAMAM_APP_KEY` — Edamam Food Database API keys (V2 fallback nutrition provider, optional)

API docs available at `http://localhost:8000/docs` when backend is running.