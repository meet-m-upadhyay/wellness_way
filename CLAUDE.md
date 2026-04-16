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
- **ML Diet Pipeline** (`services/ml_diet_pipeline/`): The core feature. `orchestrator.py` coordinates: template selection (discovery_engine) -> nutrition lookup -> portion scaling -> safety validation -> store plan. GenAI integration exists but is **disabled** — all diet plan generation is deterministic math.
- **Models**: SQLAlchemy ORM in `models/`. Key entities: User (with health metrics), HealthGoals, DietPreferences, HealthContextDocument (immutable versioned snapshots), DietPlan (JSON content), Chat/Message.
- **Database**: `database/connection.py` manages engine/sessions. Supabase PostgreSQL in prod, local Postgres for dev.

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

API docs available at `http://localhost:8000/docs` when backend is running.