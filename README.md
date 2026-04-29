# WellnessWay

AI-powered diet planning application that generates personalized meal plans using nutritional science, cultural food pairing, and machine learning.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            FRONTEND                                     │
│  React 18 + TypeScript · Tailwind CSS · Framer Motion                   │
│                                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │  Auth /   │  │  Health  │  │   Diet   │  │  Admin   │               │
│  │  Profile  │  │  Context │  │  Plans   │  │Dashboard │               │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘               │
│       └──────────────┴─────────────┴──────────────┘                     │
│                        Axios API Client                                 │
│                     (JWT auth interceptors)                             │
├─────────────────────────────────────────────────────────────────────────┤
│                         Cloudflare Workers                              │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ HTTPS
┌───────────────────────────────▼─────────────────────────────────────────┐
│                            BACKEND                                      │
│  FastAPI · Python 3.11+ · Google Cloud Run (Docker)                     │
│                                                                         │
│  Middleware: CORS → Security → RateLimit → TrustedHost                  │
│                                                                         │
│  ┌──────────────────────── API Layer (/api/v1) ───────────────────────┐ │
│  │  auth · users · health-context · diet-plans · chat · admin         │ │
│  │  v2/meal-engine/generate-meal · v2/meal-engine/generate-daily      │ │
│  └────────────────────────────┬───────────────────────────────────────┘ │
│                               │                                         │
│  ┌────────────────────────────▼───────────────────────────────────────┐ │
│  │                      SERVICE LAYER                                 │ │
│  │                                                                    │ │
│  │  ┌──────────────────────┐    ┌──────────────────────────────────┐  │ │
│  │  │  V1 ML Diet Pipeline │    │  V2 Meal Engine (feature-flagged)│  │ │
│  │  │                      │    │                                  │  │ │
│  │  │  LLM Suggester       │    │  Archetype-first LLM Generation │  │ │
│  │  │       ↓              │    │       ↓                          │  │ │
│  │  │  Nutrition Resolver  │    │  IngredientMatcher               │  │ │
│  │  │  (USDA/API Ninjas)   │    │  (exact→alias→fuzzy→embedding)  │  │ │
│  │  │       ↓              │    │       ↓                          │  │ │
│  │  │  Daily Assembler     │    │  NutritionRouter                 │  │ │
│  │  │  (protein-first      │    │  (IFCT→Edamam→USDA, by cuisine) │  │ │
│  │  │   portion scaling)   │    │       ↓                          │  │ │
│  │  │       ↓              │    │  UnitNormalizer                  │  │ │
│  │  │  Validation Engine   │    │  (Indian units → grams)          │  │ │
│  │  │       ↓              │    │       ↓                          │  │ │
│  │  │  GenAI Naming        │    │  MealScorer (0-100)              │  │ │
│  │  │                      │    │  (6 deterministic + LLM-judge)   │  │ │
│  │  └──────────────────────┘    │       ↓                          │  │ │
│  │                              │  Auto-retry if score < 70        │  │ │
│  │                              └──────────────────────────────────┘  │ │
│  │                                                                    │ │
│  │  auth_service · health_calculations · health_context_service       │ │
│  │  user_service · email_service · nutrition_database                 │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌──────────── ORM Layer ────────────┐  ┌─────── External APIs ──────┐ │
│  │  SQLAlchemy 2.0 + Alembic         │  │  Groq LLM (generation)     │ │
│  │  User · HealthContext · DietPlan   │  │  USDA FoodData Central     │ │
│  │  Chat · FoodItems · FoodEmbeddings │  │  API Ninjas (fallback)     │ │
│  │  V2Ingredient · V2Region          │  │  Edamam (V2 fallback)      │ │
│  │  V2PairingRule · V2Embedding      │  │  Google OAuth              │ │
│  │  V2ExternalNutritionCache         │  │                            │ │
│  └────────────────┬──────────────────┘  └────────────────────────────┘ │
└───────────────────┼─────────────────────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────────────────────┐
│                          DATABASE                                       │
│  PostgreSQL 15+ (Supabase in prod)                                      │
│                                                                         │
│  Extensions: pgvector · pg_trgm                                         │
│                                                                         │
│  V1 Tables: users, health_goals, diet_preferences, health_context_docs, │
│             diet_plans, food_items, food_embeddings, chat, messages      │
│                                                                         │
│  V2 Tables: v2_ingredients (546 IFCT foods), v2_regions,                │
│             v2_pairing_rules, v2_ingredient_embeddings (384-dim),        │
│             v2_external_nutrition_cache                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### V2 Meal Engine Pipeline (Detail)

```
User Request (cuisine, goal, calories, diet prefs)
        │
        ▼
┌─ Archetype Selection ──────────────────────────────────────────┐
│  Pick from: thali, one_pot, curry_bread, tiffin (Indian)       │
│             grain_bowl, mezze_plate, protein_salad (Med.)       │
│             pasta_side, protein_starch_veg (Italian)            │
└────────────┬───────────────────────────────────────────────────┘
             ▼
┌─ LLM Generation (Groq) ───────────────────────────────────────┐
│  Fill archetype slots with ingredients + grams                  │
│  Constrained to ±5% macro targets                              │
└────────────┬───────────────────────────────────────────────────┘
             ▼
┌─ Ingredient Matching (4-stage cascade) ────────────────────────┐
│  1. Exact name  →  2. Alias (regional names)                   │
│  3. Fuzzy (rapidfuzz, threshold 0.6)                           │
│  4. Semantic (pgvector cosine similarity, threshold 0.75)      │
└────────────┬───────────────────────────────────────────────────┘
             ▼
┌─ Nutrition Resolution (cuisine-aware routing) ─────────────────┐
│  Indian: IFCT local DB → Edamam (cached) → USDA               │
│  Western: USDA → Edamam (cached)                               │
└────────────┬───────────────────────────────────────────────────┘
             ▼
┌─ Unit Normalization ───────────────────────────────────────────┐
│  katori→150g, phulka→30g, idli→40g, etc.                      │
└────────────┬───────────────────────────────────────────────────┘
             ▼
┌─ Meal Scoring (0-100) ────────────────────────────────────────┐
│  Macro Accuracy (30) + Plate Composition (20) +                │
│  Culinary Coherence (20) + Micro Diversity (15) +              │
│  Goal Alignment (10) + Practicality (5)                        │
│                                                                │
│  ≥85 = serve  │  70-84 = review  │  <70 = regenerate (max 3x) │
└────────────┬───────────────────────────────────────────────────┘
             ▼
        Final Meal
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Tailwind CSS, Framer Motion |
| Backend | FastAPI, Python 3.11+, Pydantic v2 |
| Database | PostgreSQL 15+ (Supabase), pgvector, pg_trgm |
| ORM | SQLAlchemy 2.0, Alembic migrations |
| LLM | Groq (meal generation, scoring judge, recipe naming) |
| Nutrition APIs | USDA FoodData Central, API Ninjas, Edamam |
| Nutrition Data | IFCT 2017 (546 Indian foods, locally seeded) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 (384-dim) |
| Fuzzy Matching | rapidfuzz, pgvector cosine similarity |
| Auth | Google OAuth + email/password, JWT |
| Frontend Hosting | Cloudflare Workers |
| Backend Hosting | Docker → Google Cloud Run |
| CI/CD | GitHub Actions |

## Project Structure

```
wellness_way/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app factory + lifespan
│   │   ├── core/config.py             # Pydantic BaseSettings (all env vars)
│   │   ├── api/
│   │   │   ├── router.py              # Route aggregator (/api/v1)
│   │   │   └── endpoints/             # auth, users, diet_plans, chat, admin, meal_engine_v2
│   │   ├── models/                    # SQLAlchemy ORM models
│   │   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── ml_diet_pipeline/      # V1: LLM+API hybrid / template fallback
│   │   │   │   ├── orchestrator.py    # Pipeline entry point
│   │   │   │   ├── suggestion/        # LLM meal suggestion
│   │   │   │   ├── nutrition/         # Resolver + API providers
│   │   │   │   ├── daily_assembler.py # Protein-first portion scaling
│   │   │   │   ├── validation/        # Safety constraints engine
│   │   │   │   └── genai/             # Groq LLM integration
│   │   │   ├── meal_engine/           # V2: IFCT-backed parallel engine
│   │   │   │   ├── orchestrator.py    # V2 pipeline entry point
│   │   │   │   ├── config/            # JSON configs (archetypes, scoring, units, pairings)
│   │   │   │   ├── matching/          # 4-stage ingredient matcher
│   │   │   │   ├── nutrition/         # Cuisine-aware provider router
│   │   │   │   ├── scoring/           # Hybrid deterministic + LLM scorer
│   │   │   │   ├── generation/        # Archetype-first prompt builder
│   │   │   │   └── unit_normalizer.py # Indian units → grams
│   │   │   ├── health_calculations.py # BMR/TDEE (Mifflin-St Jeor)
│   │   │   └── auth_service.py        # JWT + OAuth logic
│   │   └── database/connection.py     # Engine/session management
│   ├── alembic/                       # Database migrations
│   ├── scripts/seed/                  # IFCT seed loader, embeddings, pairing rules
│   └── tests/                         # pytest (unit + property-based)
├── frontend/
│   ├── src/
│   │   ├── App.tsx                    # Root with context providers
│   │   ├── components/                # UI components (auth, diet-plans, forms, layout)
│   │   ├── pages/                     # DietPlans, HistoryView, AdminPage
│   │   ├── context/                   # AuthContext, AppContext, ThemeContext
│   │   ├── services/api.ts            # Axios client with auth interceptors
│   │   ├── hooks/                     # Custom React hooks
│   │   ├── types/                     # TypeScript type definitions
│   │   └── utils/                     # Utility functions
│   └── public/                        # Static assets
├── ifct-test/                         # IFCT seed script (Node.js CSV → JSON)
├── docs/                              # Architecture docs, setup guides
├── e2e/                               # End-to-end tests
├── .github/workflows/                 # CI/CD (tests, Cloud Run deploy)
└── .env.example                       # Environment template
```

## Core Features

- **Personalized Diet Plans** — Weekly/daily meal plans calibrated to user's BMR, TDEE, health goals, and dietary restrictions
- **Dual Generation Engines** — V1 (template + LLM hybrid) and V2 (IFCT-backed archetype-first) run in parallel
- **Indian Food Intelligence** — 546 IFCT 2017 foods with regional names, diet tags, and verified nutrition data
- **Cultural Meal Pairing** — Archetype-based generation (thali, tiffin, curry-bread) with pairing rules (rajma→rice, sambar→idli)
- **Multi-Stage Ingredient Matching** — Exact → alias → fuzzy → semantic embedding cascade
- **Cuisine-Aware Nutrition** — Routes Indian foods through local IFCT data, Western through USDA/Edamam
- **Quality Scoring** — 6-dimension scoring (0-100) with automatic regeneration below threshold
- **Health Context Documents** — Immutable, versioned health snapshots for audit trail
- **Safety Constraints** — Min/max calorie limits, protein requirements, allergy enforcement
- **Auth** — Google OAuth + email/password with JWT, admin approval for new users

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with `pgvector` and `pg_trgm` extensions
- A Supabase account (recommended) or local PostgreSQL

### Quick Setup

1. **Clone and configure**
   ```bash
   git clone <repository-url>
   cd wellness_way
   cp .env.example .env
   # Edit .env with your credentials (see Environment Variables below)
   ```

2. **Backend**
   ```bash
   cd backend
   python -m venv .venv
   .venv/Scripts/activate        # Windows
   # source .venv/bin/activate   # macOS/Linux
   pip install -r requirements.txt
   python -m alembic upgrade head
   python start_backend.py
   ```

3. **Frontend**
   ```bash
   cd frontend
   npm install
   npm start
   ```

4. **Access**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs (Swagger): http://localhost:8000/docs

### Seed V2 Meal Engine Data (optional)

Run from `backend/` with venv activated:

```bash
# 1. Generate IFCT JSON from CSV
cd ../ifct-test && node seed_ifct.js

# 2. Load into PostgreSQL
cd ../backend
python scripts/seed/load_ifct_seed.py --json-path ../ifct-test/ifct_seed_data.json

# 3. Seed pairing rules
python scripts/seed/seed_pairing_rules.py

# 4. Generate embeddings (requires sentence-transformers)
python scripts/seed/generate_embeddings.py
```

## Environment Variables

Copy `.env.example` to `.env` in the repo root. Key variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection (`postgresql+psycopg://...`) |
| `JWT_SECRET_KEY` | Yes | JWT signing key |
| `SECRET_KEY` | Yes | App secret key |
| `GOOGLE_CLIENT_ID` | Yes | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Yes | Google OAuth client secret |
| `CORS_ORIGINS` | Yes | Semicolon-separated allowed origins |
| `GROQ_API_KEY` | Yes | Groq LLM API key |
| `USDA_API_KEY` | V1 | USDA FoodData Central API key (free) |
| `API_NINJAS_API_KEY` | V1 | API Ninjas key (free, fallback) |
| `EDAMAM_APP_ID` | V2 | Edamam Food Database app ID (optional) |
| `EDAMAM_APP_KEY` | V2 | Edamam Food Database app key (optional) |
| `ENABLE_LLM_MEAL_SUGGESTIONS` | No | `true` for V1 hybrid path (default: `false`) |
| `ENABLE_MEAL_ENGINE_V2` | No | `true` for V2 engine endpoints (default: `false`) |
| `REACT_APP_API_URL` | No | Backend URL for frontend (default: `http://localhost:8000/api/v1`) |

**Important:** CORS_ORIGINS must use semicolons, not JSON arrays — `gcloud run deploy` corrupts commas.

## API Endpoints

### V1

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register new user |
| `POST` | `/api/v1/auth/login` | Login (email/password) |
| `POST` | `/api/v1/auth/google` | Google OAuth login |
| `GET` | `/api/v1/users/profile` | Get user profile |
| `PUT` | `/api/v1/users/profile` | Update profile |
| `GET` | `/api/v1/health-context` | Get current health context |
| `POST` | `/api/v1/health-context/update` | Update health context |
| `POST` | `/api/v1/diet-plans/weekly` | Generate weekly plan |
| `POST` | `/api/v1/diet-plans/daily` | Generate daily plan |
| `GET` | `/api/v1/diet-plans` | List plans |
| `GET` | `/api/v1/diet-plans/{id}` | Get specific plan |
| `POST` | `/api/v1/diet-plans/{id}/regenerate-meal` | Regenerate meal |
| `POST` | `/api/v1/diet-plans/{id}/regenerate-day` | Regenerate day |
| `POST` | `/api/v1/diet-plans/{id}/regenerate` | Regenerate full plan |

### V2 Meal Engine (feature-flagged)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/v2/meal-engine/generate-meal` | Generate single meal |
| `POST` | `/api/v1/v2/meal-engine/generate-daily` | Generate daily plan |

## Development

### Backend Commands (from `backend/`)

```bash
# Dev server
python start_backend.py

# Tests
pytest tests/ -v
pytest tests/ -v --cov=app
pytest tests/ -m "property"           # property-based only

# Migrations
python -m alembic upgrade head
python -m alembic revision --autogenerate -m "description"
python -m alembic downgrade -1

# Lint & format
black app/ && isort app/ && flake8 app/
mypy app/ --ignore-missing-imports
```

### Frontend Commands (from `frontend/`)

```bash
npm start           # dev server (port 3000, proxies to :8000)
npm test            # jest
npm run lint        # eslint
npm run type-check  # tsc --noEmit
npm run build
npm run deploy      # Cloudflare Workers
```

## Deployment

- **Backend**: Docker → Google Cloud Run (auto-deploys from `dev` branch via GitHub Actions)
- **Frontend**: Cloudflare Workers (`npm run deploy`)
- **Database**: Supabase (managed PostgreSQL)
- **CI**: GitHub Actions runs tests + linting on PR/push to main/develop

## License

https://dev-wellness-way.meetupadhyaykgp.workers.dev/diet-plans
