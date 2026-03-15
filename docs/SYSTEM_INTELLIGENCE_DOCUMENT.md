# WELLNESSWAY - COMPLETE SYSTEM INTELLIGENCE DOCUMENT

**Generated**: February 22, 2026  
**Purpose**: Complete system handover for AI coding agents  
**Status**: Production-ready with ML pipeline active

---

## TABLE OF CONTENTS

1. [PROJECT OVERVIEW](#1-project-overview)
2. [ARCHITECTURE](#2-architecture)
3. [FOLDER & FILE STRUCTURE](#3-folder--file-structure)
4. [DATABASE DESIGN](#4-database-design)
5. [API CONTRACTS](#5-api-contracts)
6. [BUSINESS LOGIC FLOWS](#6-business-logic-flows)
7. [ENVIRONMENT & CONFIGURATION](#7-environment--configuration)
8. [EXTERNAL INTEGRATIONS](#8-external-integrations)
9. [STATE MANAGEMENT](#9-state-management-frontend)
10. [DEPLOYMENT & DEV WORKFLOW](#10-deployment--dev-workflow)
11. [CURRENT LIMITATIONS & TECH DEBT](#11-current-limitations--tech-debt)
12. [CRITICAL ENTRY POINTS](#12-critical-entry-points)
13. [HOW TO EXTEND THE SYSTEM](#13-how-to-extend-the-system)

---


## 1. PROJECT OVERVIEW

### Problem Statement
WellnessWay solves the problem of personalized diet planning by combining:
- Deterministic health calculations (BMR, TDEE)
- AI-powered meal generation
- ML-based template selection
- Nutritional database lookups
- Safety-first constraint enforcement

### Target Users
1. **Individual Users**: People seeking personalized diet plans
2. **Couples**: Two users with shared meal planning (future feature)
3. **Admins**: System administrators managing user approvals

### Core Features

#### Implemented (MVP)
1. **User Authentication**
   - Google OAuth integration
   - JWT-based session management
   - Admin approval workflow for new registrations

2. **Health Profile Management**
   - Physical metrics collection (age, weight, height, body composition)
   - Deterministic BMR/TDEE calculations
   - Health Context Document (HCD) generation
   - Versioned, immutable health profiles

3. **ML Diet Plan Generation** (PRIMARY FEATURE)
   - Template-based meal selection (17 hardcoded templates)
   - Heuristic scoring algorithm
   - Deterministic nutrition calculations
   - Portion scaling to meet calorie targets
   - Weekly and daily plan generation
   - Meal/day/week regeneration

4. **Admin System**
   - User management dashboard
   - Registration approval/rejection
   - User enable/disable functionality

#### Disabled (Legacy)
- AI-powered diet plan generation (GenAI with LLM)
- All AI buttons are commented out in frontend

### Key Differentiators
1. **Safety-First**: Deterministic calculations before any AI usage
2. **Versioned Health Context**: Immutable, traceable health profiles
3. **Dual Pipeline**: ML (active) + AI (disabled but preserved)
4. **Template-Based**: Predictable, consistent meal generation
5. **No Medical Claims**: Explicit disclaimers, no diagnosis

### High-Level Execution Flow

```
User Registration Flow:
User → Google OAuth → Registration Request → Admin Approval → User Account Created

Health Profile Flow:
User Input → BMR/TDEE Calculation → HCD Generation → HCD Storage (versioned)

ML Diet Plan Generation Flow:
User Request → HCD Retrieval → Template Selection (heuristic scoring) 
→ Nutrition Lookup (database) → Portion Scaling (deterministic math)
→ Plan Validation → Plan Storage → Response to User

Regeneration Flow:
User Request (meal/day/week) → Existing Plan Retrieval → Template Re-selection
→ Nutrition Recalculation → Plan Update (flag_modified) → Response
```


## 2. ARCHITECTURE

### System Type
**Monolithic Architecture** with clear service separation

### Technology Stack

#### Backend
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11+
- **ORM**: SQLAlchemy 2.0+
- **Database**: PostgreSQL 17.6 (Supabase hosted)
- **Migrations**: Alembic
- **Caching**: Redis (optional, in-memory fallback)
- **Authentication**: JWT + Google OAuth
- **API Documentation**: Swagger/OpenAPI (auto-generated)

#### Frontend
- **Framework**: React 18
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **State Management**: React Context API
- **Build Tool**: Create React App

#### ML/AI Components
- **Active**: Sentence Transformers (`all-MiniLM-L6-v2`) - ingredient canonicalization (implemented but not actively used)
- **Disabled**: Groq API (LLM provider) - for GenAI diet generation
- **Planned**: LightGBM for template selection

#### Infrastructure
- **Database**: Supabase (PostgreSQL as a Service)
  - Project: `ytlfneijevuhcwbqqkck`
  - Region: `ap-southeast-2` (Sydney)
  - Connection: Transaction pooler (port 5432)
- **Deployment**: Not yet configured (local development)
- **Monitoring**: Basic logging (file + console)

### Authentication Mechanism

```
Google OAuth Flow:
1. User clicks "Sign in with Google"
2. Frontend redirects to Google OAuth
3. Google returns authorization code
4. Backend exchanges code for user info
5. Backend checks if user exists:
   - If new: Create RegistrationRequest (pending approval)
   - If existing: Generate JWT tokens
6. Admin approves/rejects registration
7. User can login and receive JWT tokens

JWT Token Flow:
1. Access token (30 min expiry)
2. Refresh token (7 days expiry)
3. Tokens stored in localStorage
4. Auto-refresh on API calls
5. Middleware validates tokens on protected routes
```

### ML/AI Integration Architecture

```
Current (ML Pipeline - ACTIVE):
User Request → ML Orchestrator → Template Selector (heuristic scoring)
→ Nutrition Engine (database lookup) → Scaling Engine (math)
→ Validation Engine (rules) → Response

Legacy (AI Pipeline - DISABLED):
User Request → HCD Retrieval → AI Service → Groq API (LLM)
→ JSON Parsing → Validation → Ingredient Resolution
→ Nutrition Lookup → Response
```


### Text-Based Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Login   │  │ Profile  │  │Diet Plans│  │  Admin   │       │
│  │  Page    │  │   Page   │  │   Page   │  │Dashboard │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │             │              │              │              │
│       └─────────────┴──────────────┴──────────────┘              │
│                          │                                        │
│                    Axios HTTP Client                              │
└──────────────────────────┼───────────────────────────────────────┘
                           │
                           │ HTTP/JSON
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                    BACKEND (FastAPI)                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Middleware Layer                         │ │
│  │  • CORS  • Security Headers  • Rate Limiting  • Auth       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           │                                       │
│  ┌────────────────────────▼───────────────────────────────────┐ │
│  │                    API Router                               │ │
│  │  /auth  /users  /health-context  /diet-plans  /admin      │ │
│  │  /diet-plans-ml (ML PIPELINE - ACTIVE)                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           │                                       │
│  ┌────────────────────────▼───────────────────────────────────┐ │
│  │                   Service Layer                             │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │ │
│  │  │   Auth   │  │  Health  │  │   Diet   │  │   User   │  │ │
│  │  │ Service  │  │  Context │  │   Plan   │  │ Service  │  │ │
│  │  │          │  │  Service │  │  Service │  │          │  │ │
│  │  └──────────┘  └──────────┘  └────┬─────┘  └──────────┘  │ │
│  │                                    │                        │ │
│  │  ┌─────────────────────────────────▼──────────────────┐   │ │
│  │  │         ML Diet Pipeline (ACTIVE)                   │   │ │
│  │  │  • Orchestrator                                     │   │ │
│  │  │  • Template Selector (heuristic scoring)           │   │ │
│  │  │  • Meal Templates (17 hardcoded)                   │   │ │
│  │  │  • Nutrition Engine Adapter                        │   │ │
│  │  │  • Scaling Engine (deterministic math)             │   │ │
│  │  │  • Validation Engine (rules)                       │   │ │
│  │  └────────────────────────────────────────────────────┘   │ │
│  │                                                             │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │         AI Service (DISABLED)                       │  │ │
│  │  │  • AI Provider Manager                              │  │ │
│  │  │  • Groq API Integration                             │  │ │
│  │  │  • Ingredient Resolution                            │  │ │
│  │  │  • Contract Enforcement                             │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                           │                                       │
│  ┌────────────────────────▼───────────────────────────────────┐ │
│  │                   Data Layer (SQLAlchemy)                   │ │
│  │  • User Model  • HealthContext  • DietPlan  • Admin       │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────┼───────────────────────────────────────┘
                           │
                           │ SQL
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│              SUPABASE (PostgreSQL 17.6)                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  users   │  │health_   │  │diet_     │  │registra- │        │
│  │          │  │context_  │  │plans     │  │tion_     │        │
│  │          │  │documents │  │          │  │requests  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└───────────────────────────────────────────────────────────────────┘

External Services:
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Google OAuth │  │  Groq API    │  │   Redis      │
│  (Active)    │  │  (Disabled)  │  │  (Optional)  │
└──────────────┘  └──────────────┘  └──────────────┘
```


## 3. FOLDER & FILE STRUCTURE

### Backend Structure (`backend/`)

```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/          # API route handlers
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── users.py        # User CRUD endpoints
│   │   │   ├── health_context.py  # HCD endpoints
│   │   │   ├── diet_plans.py   # AI diet plans (DISABLED)
│   │   │   ├── diet_plans_ml.py # ML diet plans (ACTIVE)
│   │   │   ├── admin.py        # Admin management
│   │   │   └── monitoring.py   # Health checks
│   │   └── router.py           # Main API router
│   ├── core/
│   │   ├── config.py           # Pydantic settings
│   │   ├── security.py         # JWT, password hashing
│   │   ├── security_config.py  # CORS, headers
│   │   └── secrets.py          # Secret management
│   ├── database/
│   │   ├── connection.py       # SQLAlchemy engine
│   │   └── init_db.py          # DB initialization
│   ├── middleware/
│   │   ├── auth.py             # JWT validation
│   │   ├── admin.py            # Admin-only routes
│   │   └── security.py         # Rate limiting, sanitization
│   ├── models/
│   │   ├── user.py             # User, HealthGoals, DietPreferences
│   │   ├── health_context.py  # HealthContextDocument
│   │   └── diet_plan.py        # DietPlan
│   ├── schemas/
│   │   ├── user.py             # Pydantic user schemas
│   │   ├── health_context.py  # Pydantic HCD schemas
│   │   ├── diet_plan.py        # Pydantic plan schemas
│   │   ├── auth.py             # Auth request/response
│   │   └── admin.py            # Admin schemas
│   ├── services/
│   │   ├── auth_service.py     # Authentication logic
│   │   ├── user_service.py     # User CRUD logic
│   │   ├── health_context_service.py  # HCD generation
│   │   ├── health_calculations.py     # BMR/TDEE formulas
│   │   ├── diet_plan_service.py       # AI plan service (DISABLED)
│   │   ├── nutrition_database.py      # Food nutrition data
│   │   ├── nutrition_engine.py        # Nutrition calculations
│   │   ├── ai_service.py              # LLM integration (DISABLED)
│   │   ├── ai_provider_manager.py     # Multi-provider support
│   │   ├── ingredient_*.py            # Ingredient processing
│   │   └── ml_diet_pipeline/          # ML PIPELINE (ACTIVE)
│   │       ├── orchestrator.py        # Main ML coordinator
│   │       ├── meal_templates.py      # 17 hardcoded templates
│   │       ├── template_selector.py   # Heuristic scoring
│   │       ├── nutrition_engine_adapter.py  # DB lookup
│   │       ├── scaling_engine.py      # Portion math
│   │       ├── validation_engine.py   # Rules validation
│   │       └── ingredient_canonicalizer.py  # ML model (unused)
│   ├── utils/
│   │   └── safe_logging.py     # PII-safe logging
│   └── main.py                 # FastAPI app entry point
├── alembic/
│   ├── versions/               # Migration files
│   └── env.py                  # Alembic config
├── tests/                      # Organized unit tests
├── start_backend.py            # Server startup script
├── run_migrations.py           # Migration runner
└── requirements.txt            # Python dependencies
```

### Frontend Structure (`frontend/`)

```
frontend/
├── public/
│   └── index.html              # HTML template
├── src/
│   ├── components/
│   │   ├── diet-plans/
│   │   │   ├── PlanTypeSelector.tsx    # Daily/Weekly selector
│   │   │   ├── MealCard.tsx            # Individual meal display
│   │   │   ├── DailyPlanView.tsx       # Single day view
│   │   │   ├── WeeklyPlanView.tsx      # 7-day view
│   │   │   └── NutritionSummary.tsx    # Nutrition totals
│   │   ├── admin/
│   │   │   ├── UserManagement.tsx      # User list/actions
│   │   │   └── RegistrationApproval.tsx # Approval queue
│   │   └── common/
│   │       ├── Navbar.tsx              # Navigation
│   │       └── ProtectedRoute.tsx      # Auth guard
│   ├── pages/
│   │   ├── Login.tsx                   # Google OAuth login
│   │   ├── Profile.tsx                 # User profile form
│   │   ├── DietPlans.tsx               # Main diet plan page
│   │   └── AdminDashboard.tsx          # Admin panel
│   ├── services/
│   │   └── api.ts                      # Axios API client
│   ├── context/
│   │   └── AuthContext.tsx             # Auth state management
│   ├── types/
│   │   └── index.ts                    # TypeScript interfaces
│   ├── App.tsx                         # Main app component
│   └── index.tsx                       # React entry point
├── package.json                        # NPM dependencies
└── tailwind.config.js                  # Tailwind configuration
```

### Key File Responsibilities

#### Backend

**`app/main.py`**: FastAPI application initialization
- Middleware setup (CORS, security, rate limiting)
- Router inclusion
- Lifespan events (startup/shutdown)
- Global exception handling
- Health check endpoints

**`app/api/endpoints/diet_plans_ml.py`**: ML diet plan endpoints (ACTIVE)
- `POST /diet-plans-ml/daily` - Generate daily plan
- `POST /diet-plans-ml/weekly` - Generate weekly plan
- `POST /diet-plans-ml/{id}/regenerate-meal-ml` - Regenerate single meal
- `POST /diet-plans-ml/{id}/regenerate-day-ml` - Regenerate single day
- `POST /diet-plans-ml/{id}/regenerate-week-ml` - Regenerate entire week

**`app/services/ml_diet_pipeline/orchestrator.py`**: ML pipeline coordinator
- Fetches user HCD
- Calls template selector
- Coordinates nutrition lookup
- Applies portion scaling
- Validates output
- Returns structured plan

**`app/services/ml_diet_pipeline/meal_templates.py`**: Hardcoded meal templates
- 17 predefined meal templates
- Each template has: name, meal_type, ingredients, base_nutrition
- Templates cover breakfast, lunch, dinner, snacks
- Vegetarian and non-vegetarian options

**`app/services/health_calculations.py`**: Deterministic health formulas
- BMR calculation (Mifflin-St Jeor equation)
- TDEE calculation (activity multipliers)
- Minimum calorie calculation (safety floor)
- Maximum deficit calculation (safety ceiling)
- Protein requirements (based on weight/goals)

**`app/models/health_context.py`**: Health Context Document model
- Versioned, immutable health profiles
- Stores markdown content + JSON context
- Includes calculated BMR, TDEE, constraints
- Unique constraint on (user_id, version)

#### Frontend

**`src/services/api.ts`**: Centralized API client
- Axios instance with base URL
- Request/response interceptors
- Token management
- Error handling
- All API endpoints defined as functions

**`src/pages/DietPlans.tsx`**: Main diet plan interface
- Plan type selection (daily/weekly)
- Plan generation (ML only)
- Plan display (meals, nutrition)
- Regeneration buttons (meal/day/week)
- State management for plans

**`src/context/AuthContext.tsx`**: Authentication state
- User login/logout
- Token storage (localStorage)
- Token refresh logic
- Protected route logic
- Admin role checking

### Module Dependencies

```
API Endpoints → Services → Models → Database
              ↓
         Middleware (Auth, Admin, Rate Limit)
              ↓
         Schemas (Validation)

ML Pipeline Flow:
diet_plans_ml.py → orchestrator.py → template_selector.py
                                   → nutrition_engine_adapter.py
                                   → scaling_engine.py
                                   → validation_engine.py
                                   → meal_templates.py
```


## 4. DATABASE DESIGN

### Database: PostgreSQL 17.6 (Supabase)

**Connection**: `postgresql://postgres.ytlfneijevuhcwbqqkck:UlhiSGdNxvHm5s06@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres`

### Tables

#### 1. `users`
**Purpose**: Store user accounts and profiles

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid_generate_v4() | User ID |
| email | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | User email |
| google_id | VARCHAR(255) | UNIQUE, INDEX | Google OAuth ID |
| is_active | BOOLEAN | NOT NULL, default TRUE | Account status |
| is_admin | BOOLEAN | NOT NULL, default FALSE | Admin privileges |
| approval_status | VARCHAR(20) | NOT NULL, default 'approved' | 'pending', 'approved', 'declined' |
| name | VARCHAR(255) | NOT NULL | User full name |
| age | INTEGER | CHECK (age > 0 AND age < 150) | User age |
| gender | VARCHAR(20) | CHECK (gender IN ('male', 'female', 'other')) | User gender |
| height_cm | FLOAT | CHECK (height_cm > 50 AND height_cm < 300) | Height in cm |
| weight_kg | FLOAT | CHECK (weight_kg > 20 AND weight_kg < 500) | Weight in kg |
| body_fat_percentage | FLOAT | CHECK (body_fat_percentage >= 0 AND body_fat_percentage <= 100) | Body fat % |
| muscle_mass_kg | FLOAT | CHECK (muscle_mass_kg >= 0) | Muscle mass in kg |
| activity_level | VARCHAR(30) | CHECK (activity_level IN ('sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active')) | Activity level |
| profile_completed | BOOLEAN | NOT NULL, default FALSE | Profile completion status |
| created_at | TIMESTAMP | default NOW() | Creation timestamp |
| updated_at | TIMESTAMP | default NOW(), onupdate NOW() | Update timestamp |

**Indexes**:
- PRIMARY KEY (id)
- UNIQUE INDEX (email)
- UNIQUE INDEX (google_id)

#### 2. `health_context_documents`
**Purpose**: Store versioned, immutable health profiles

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid_generate_v4() | HCD ID |
| user_id | UUID | NOT NULL, FK → users(id) | User reference |
| version | INTEGER | NOT NULL, CHECK (version > 0) | Version number |
| content | TEXT | NOT NULL | Markdown content |
| json_context | JSONB | NULL | Machine-readable JSON |
| bmr_calories | FLOAT | NOT NULL, CHECK (bmr_calories > 0) | Basal Metabolic Rate |
| tdee_calories | FLOAT | NOT NULL, CHECK (tdee_calories > bmr_calories) | Total Daily Energy Expenditure |
| min_daily_calories | FLOAT | NOT NULL, CHECK (min_daily_calories >= bmr_calories) | Minimum safe calories |
| max_calorie_deficit | FLOAT | NOT NULL, CHECK (max_calorie_deficit > 0) | Maximum allowed deficit |
| min_protein_grams | FLOAT | NOT NULL, CHECK (min_protein_grams > 0) | Minimum protein requirement |
| created_at | TIMESTAMP | default NOW() | Creation timestamp |
| is_active | BOOLEAN | default TRUE | Active version flag |

**Indexes**:
- PRIMARY KEY (id)
- UNIQUE INDEX (user_id, version)
- INDEX (user_id, is_active)

**Constraints**:
- UNIQUE (user_id, version) - One version per user
- CHECK (tdee_calories > bmr_calories)
- CHECK (min_daily_calories >= bmr_calories)

#### 3. `diet_plans`
**Purpose**: Store generated diet plans

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid_generate_v4() | Plan ID |
| user_id | UUID | NOT NULL, FK → users(id) | User reference |
| hcd_id | UUID | NOT NULL, FK → health_context_documents(id) | HCD reference |
| plan_type | VARCHAR(20) | NOT NULL, CHECK (plan_type IN ('weekly', 'daily')) | Plan type |
| start_date | DATE | NOT NULL | Plan start date |
| content | JSON | NOT NULL | Plan structure (meals, nutrition) |
| created_at | TIMESTAMP | default NOW() | Creation timestamp |

**Indexes**:
- PRIMARY KEY (id)
- INDEX (user_id, created_at)
- INDEX (hcd_id)

**Content JSON Structure**:
```json
{
  "days": [
    {
      "date": "2026-02-22",
      "meals": [
        {
          "meal_type": "breakfast",
          "name": "Oatmeal with Berries",
          "ingredients": [
            {"name": "oats", "quantity": 50, "unit": "g"},
            {"name": "blueberries", "quantity": 100, "unit": "g"}
          ],
          "nutrition": {
            "calories": 300,
            "protein": 10,
            "carbohydrates": 50,
            "fat": 5
          }
        }
      ],
      "daily_nutrition": {
        "calories": 2000,
        "protein": 150,
        "carbohydrates": 200,
        "fat": 65
      }
    }
  ],
  "weekly_nutrition": {
    "avg_calories": 2000,
    "avg_protein": 150,
    "avg_carbs": 200,
    "avg_fat": 65
  }
}
```

#### 4. `health_goals`
**Purpose**: Store user health goals

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Goal ID |
| user_id | UUID | NOT NULL, FK → users(id) | User reference |
| primary_goal | VARCHAR(20) | NOT NULL, CHECK (primary_goal IN ('fat_loss', 'muscle_gain', 'maintenance')) | Primary goal |
| target_weight_kg | FLOAT | CHECK (target_weight_kg > 20 AND target_weight_kg < 500) | Target weight |
| timeline_weeks | INTEGER | CHECK (timeline_weeks > 0 AND timeline_weeks <= 104) | Timeline (max 2 years) |
| created_at | TIMESTAMP | default NOW() | Creation timestamp |

#### 5. `diet_preferences`
**Purpose**: Store user dietary preferences

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Preference ID |
| user_id | UUID | NOT NULL, FK → users(id) | User reference |
| diet_type | VARCHAR(20) | NOT NULL, CHECK (diet_type IN ('vegetarian', 'non_vegetarian', 'vegan')) | Diet type |
| allergies | JSON | NOT NULL, default [] | List of allergens |
| foods_to_avoid | JSON | NOT NULL, default [] | Foods to avoid |
| meals_per_day | INTEGER | NOT NULL, default 3, CHECK (meals_per_day >= 1 AND meals_per_day <= 8) | Meals per day |
| budget_constraints | TEXT | NULL | Budget notes |
| lifestyle_constraints | TEXT | NULL | Lifestyle notes |
| created_at | TIMESTAMP | default NOW() | Creation timestamp |

#### 6. `registration_requests`
**Purpose**: Admin approval queue for new users

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Request ID |
| email | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | User email |
| name | VARCHAR(255) | NOT NULL | User name |
| google_id | VARCHAR(255) | NOT NULL | Google OAuth ID |
| status | VARCHAR(20) | NOT NULL, default 'pending', INDEX, CHECK (status IN ('pending', 'approved', 'declined')) | Request status |
| created_at | TIMESTAMP | default NOW() | Creation timestamp |
| updated_at | TIMESTAMP | default NOW(), onupdate NOW() | Update timestamp |

#### 7. `alembic_version`
**Purpose**: Track database migrations

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| version_num | VARCHAR(32) | PK | Migration version |

### Relationships

```
users (1) ←→ (N) health_context_documents
users (1) ←→ (N) diet_plans
users (1) ←→ (1) health_goals
users (1) ←→ (1) diet_preferences
health_context_documents (1) ←→ (N) diet_plans
```

### Migration System

**Tool**: Alembic

**Migration Files** (`backend/alembic/versions/`):
- `7d87899f7073_initial_database_schema.py` - Initial schema
- `add_admin_field_to_users.py` - Admin field
- `add_auth_fields_to_users.py` - OAuth fields
- `4323ba1e246b_merge_admin_and_auth_fields.py` - Merge migrations
- `add_admin_approval_system.py` - Registration requests
- `add_json_context_to_hcd.py` - JSON context field
- `cc728301c6c8_merge_heads.py` - Merge conflicts

**Running Migrations**:
```bash
cd backend
python run_migrations.py
```

### Data Flow During Key Operations

#### User Registration
```
1. Google OAuth → google_id, email, name
2. Create RegistrationRequest (status='pending')
3. Admin approves → Create User (approval_status='approved')
4. User can login
```

#### Health Profile Creation
```
1. User submits profile form → age, weight, height, etc.
2. Calculate BMR (Mifflin-St Jeor formula)
3. Calculate TDEE (BMR × activity multiplier)
4. Calculate constraints (min calories, max deficit, min protein)
5. Generate markdown HCD content
6. Create HealthContextDocument (version=1)
7. Store in database
```

#### Diet Plan Generation (ML)
```
1. Fetch active HCD for user
2. Extract calorie target, dietary restrictions
3. Select templates via heuristic scoring
4. Lookup nutrition from database
5. Scale portions to meet targets
6. Validate against constraints
7. Create DietPlan record
8. Store JSON content
9. Return to user
```

#### Plan Regeneration
```
1. Fetch existing DietPlan by ID
2. Identify what to regenerate (meal/day/week)
3. Re-run template selection for that scope
4. Update plan.content JSON
5. Call flag_modified(plan, "content") - CRITICAL for SQLAlchemy
6. Commit to database
7. Return updated plan
```


## 5. API CONTRACTS

### Base URL
- Development: `http://localhost:8000/api/v1`
- Production: TBD

### Authentication
- **Method**: JWT Bearer Token
- **Header**: `Authorization: Bearer <access_token>`
- **Token Expiry**: 30 minutes (access), 7 days (refresh)

### Common Response Codes
- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Missing/invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Endpoints

#### Authentication (`/auth`)

**POST /auth/google**
- **Purpose**: Google OAuth login
- **Auth Required**: No
- **Request**:
```json
{
  "token": "google_oauth_token"
}
```
- **Response** (200):
```json
{
  "access_token": "jwt_access_token",
  "refresh_token": "jwt_refresh_token",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "is_admin": false
  }
}
```
- **Response** (403 - Pending Approval):
```json
{
  "detail": "Registration pending admin approval"
}
```

**POST /auth/refresh**
- **Purpose**: Refresh access token
- **Auth Required**: No (uses refresh token)
- **Request**:
```json
{
  "refresh_token": "jwt_refresh_token"
}
```
- **Response** (200):
```json
{
  "access_token": "new_jwt_access_token",
  "token_type": "bearer"
}
```

#### Users (`/users`)

**GET /users/me**
- **Purpose**: Get current user profile
- **Auth Required**: Yes
- **Response** (200):
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "age": 30,
  "gender": "male",
  "height_cm": 175,
  "weight_kg": 75,
  "body_fat_percentage": 15,
  "muscle_mass_kg": 35,
  "activity_level": "moderately_active",
  "profile_completed": true,
  "is_admin": false,
  "created_at": "2026-02-22T10:00:00Z"
}
```

**PUT /users/me**
- **Purpose**: Update user profile
- **Auth Required**: Yes
- **Request**:
```json
{
  "name": "John Doe",
  "age": 30,
  "gender": "male",
  "height_cm": 175,
  "weight_kg": 75,
  "body_fat_percentage": 15,
  "muscle_mass_kg": 35,
  "activity_level": "moderately_active"
}
```
- **Response** (200): Updated user object

#### Health Context (`/health-context`)

**POST /health-context**
- **Purpose**: Generate Health Context Document
- **Auth Required**: Yes
- **Request**:
```json
{
  "primary_goal": "fat_loss",
  "target_weight_kg": 70,
  "timeline_weeks": 12,
  "diet_type": "vegetarian",
  "allergies": ["peanuts", "shellfish"],
  "foods_to_avoid": ["mushrooms"],
  "meals_per_day": 3
}
```
- **Response** (201):
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "version": 1,
  "content": "# Health Context Document\n\n## User Profile\n...",
  "json_context": {...},
  "bmr_calories": 1650,
  "tdee_calories": 2310,
  "min_daily_calories": 1650,
  "max_calorie_deficit": 770,
  "min_protein_grams": 150,
  "created_at": "2026-02-22T10:00:00Z"
}
```

**GET /health-context/active**
- **Purpose**: Get active HCD for current user
- **Auth Required**: Yes
- **Response** (200): HCD object

#### Diet Plans - ML Pipeline (`/diet-plans-ml`) **ACTIVE**

**POST /diet-plans-ml/daily**
- **Purpose**: Generate daily diet plan using ML
- **Auth Required**: Yes
- **Request**:
```json
{
  "date": "2026-02-22"
}
```
- **Response** (201):
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "hcd_id": "uuid",
  "plan_type": "daily",
  "start_date": "2026-02-22",
  "content": {
    "days": [{
      "date": "2026-02-22",
      "meals": [
        {
          "meal_type": "breakfast",
          "name": "Oatmeal with Berries",
          "ingredients": [
            {"name": "oats", "quantity": 50, "unit": "g"},
            {"name": "blueberries", "quantity": 100, "unit": "g"}
          ],
          "nutrition": {
            "calories": 300,
            "protein": 10,
            "carbohydrates": 50,
            "fat": 5
          }
        }
      ],
      "daily_nutrition": {
        "calories": 2000,
        "protein": 150,
        "carbohydrates": 200,
        "fat": 65
      }
    }]
  },
  "created_at": "2026-02-22T10:00:00Z"
}
```

**POST /diet-plans-ml/weekly**
- **Purpose**: Generate weekly diet plan using ML
- **Auth Required**: Yes
- **Request**:
```json
{
  "start_date": "2026-02-22"
}
```
- **Response** (201): Similar to daily, but with 7 days

**POST /diet-plans-ml/{plan_id}/regenerate-meal-ml**
- **Purpose**: Regenerate single meal
- **Auth Required**: Yes
- **Request**:
```json
{
  "day_index": 0,
  "meal_index": 0
}
```
- **Response** (200): Updated plan object

**POST /diet-plans-ml/{plan_id}/regenerate-day-ml**
- **Purpose**: Regenerate entire day
- **Auth Required**: Yes
- **Request**:
```json
{
  "day_index": 0
}
```
- **Response** (200): Updated plan object

**POST /diet-plans-ml/{plan_id}/regenerate-week-ml**
- **Purpose**: Regenerate entire week
- **Auth Required**: Yes
- **Request**: Empty body
- **Response** (200): Updated plan object

**GET /diet-plans-ml**
- **Purpose**: List user's diet plans
- **Auth Required**: Yes
- **Query Params**: `skip=0`, `limit=10`
- **Response** (200):
```json
{
  "plans": [...],
  "total": 5
}
```

#### Admin (`/admin`)

**GET /admin/users**
- **Purpose**: List all users
- **Auth Required**: Yes (Admin only)
- **Middleware**: `require_admin`
- **Response** (200):
```json
{
  "users": [...],
  "total": 100
}
```

**POST /admin/users/{user_id}/disable**
- **Purpose**: Disable user account
- **Auth Required**: Yes (Admin only)
- **Response** (200): Updated user object

**POST /admin/users/{user_id}/enable**
- **Purpose**: Enable user account
- **Auth Required**: Yes (Admin only)
- **Response** (200): Updated user object

**GET /admin/registration-requests**
- **Purpose**: List pending registration requests
- **Auth Required**: Yes (Admin only)
- **Response** (200):
```json
{
  "requests": [...],
  "total": 5
}
```

**POST /admin/registration-requests/{request_id}/approve**
- **Purpose**: Approve registration
- **Auth Required**: Yes (Admin only)
- **Response** (200): Created user object

**POST /admin/registration-requests/{request_id}/reject**
- **Purpose**: Reject registration
- **Auth Required**: Yes (Admin only)
- **Response** (200): Success message

### Middleware Applied

| Endpoint | Auth | Admin | Rate Limit |
|----------|------|-------|------------|
| POST /auth/google | No | No | 10/min |
| POST /auth/refresh | No | No | 20/min |
| GET /users/me | Yes | No | 60/min |
| PUT /users/me | Yes | No | 30/min |
| POST /health-context | Yes | No | 10/min |
| POST /diet-plans-ml/* | Yes | No | 20/min |
| GET /admin/* | Yes | Yes | 60/min |
| POST /admin/* | Yes | Yes | 30/min |

### Internal Services Called

```
POST /diet-plans-ml/daily:
  → auth_middleware (validate JWT)
  → diet_plans_ml.generate_daily_plan()
    → health_context_service.get_active_hcd()
    → ml_orchestrator.generate_daily_plan()
      → template_selector.select_templates()
      → nutrition_engine_adapter.get_nutrition()
      → scaling_engine.scale_portions()
      → validation_engine.validate_plan()
    → diet_plan_service.create_plan()
  → return response

POST /admin/registration-requests/{id}/approve:
  → auth_middleware (validate JWT)
  → admin_middleware (check is_admin)
  → admin_service.approve_registration()
    → user_service.create_user()
    → registration_request.approve()
  → return response
```


## 6. BUSINESS LOGIC FLOWS

### User Registration/Login Flow

```
Step 1: User clicks "Sign in with Google"
  → Frontend redirects to Google OAuth
  → Google returns authorization code

Step 2: Frontend sends code to POST /auth/google
  → Backend exchanges code for user info (email, name, google_id)
  → Backend checks if user exists in `users` table

Step 3a: If user exists
  → Check approval_status
  → If 'approved': Generate JWT tokens, return to user
  → If 'pending': Return 403 "Registration pending approval"
  → If 'declined': Return 403 "Registration declined"

Step 3b: If user doesn't exist
  → Check if RegistrationRequest exists
  → If exists and pending: Return 403 "Registration pending approval"
  → If not exists: Create RegistrationRequest (status='pending')
  → Return 403 "Registration submitted for approval"

Step 4: Admin reviews registration
  → Admin calls POST /admin/registration-requests/{id}/approve
  → Backend creates User (approval_status='approved')
  → Backend updates RegistrationRequest (status='approved')

Step 5: User tries login again
  → Backend finds approved user
  → Generates JWT tokens
  → Returns tokens + user info
  → Frontend stores tokens in localStorage
  → Frontend redirects to dashboard
```

### Health Profile Creation Flow

```
Step 1: User fills profile form
  → Name, age, gender, height, weight, body_fat, muscle_mass, activity_level
  → Frontend validates input
  → Frontend calls PUT /users/me

Step 2: Backend updates user record
  → Validates constraints (age 0-150, height 50-300, etc.)
  → Updates user.profile_completed = True
  → Returns updated user

Step 3: User fills goals/preferences form
  → Primary goal, target weight, timeline
  → Diet type, allergies, foods to avoid
  → Frontend calls POST /health-context

Step 4: Backend generates HCD
  → health_calculations.calculate_bmr(age, gender, weight, height)
    Formula: Mifflin-St Jeor
    Men: (10 × weight_kg) + (6.25 × height_cm) - (5 × age) + 5
    Women: (10 × weight_kg) + (6.25 × height_cm) - (5 × age) - 161
  
  → health_calculations.calculate_tdee(bmr, activity_level)
    Multipliers:
    - sedentary: 1.2
    - lightly_active: 1.375
    - moderately_active: 1.55
    - very_active: 1.725
    - extremely_active: 1.9
  
  → health_calculations.calculate_min_calories(bmr)
    Return: bmr (never go below BMR)
  
  → health_calculations.calculate_max_deficit(tdee, goal)
    fat_loss: min(1000, tdee * 0.25)
    muscle_gain: 0 (surplus)
    maintenance: 0
  
  → health_calculations.calculate_min_protein(weight, goal)
    fat_loss: weight_kg * 2.0
    muscle_gain: weight_kg * 2.2
    maintenance: weight_kg * 1.6
  
  → health_context_service.generate_markdown_content()
    Creates markdown with all user data, goals, constraints
  
  → health_context_service.generate_json_context()
    Creates machine-readable JSON version
  
  → Create HealthContextDocument (version=1, is_active=True)
  → Store in database
  → Return HCD to user
```

### ML Diet Plan Generation Flow (ACTIVE)

```
Step 1: User clicks "Generate Plan (ML)"
  → Frontend calls POST /diet-plans-ml/weekly or /daily
  → Backend validates user has active HCD

Step 2: ML Orchestrator initializes
  → orchestrator.generate_weekly_plan(user_id, start_date)
  → Fetch active HCD from database
  → Extract: calorie_target, diet_type, allergies, foods_to_avoid

Step 3: Template Selection (for each meal)
  → template_selector.select_template(meal_type, diet_type, calorie_target)
  → Load 17 hardcoded templates from meal_templates.py
  → Filter templates:
    - Match meal_type (breakfast/lunch/dinner/snack)
    - Match diet_type (vegetarian/non_vegetarian/vegan)
    - Exclude allergies
    - Exclude foods_to_avoid
  → Score remaining templates:
    score = 100 - abs(template.calories - target_calories)
    score += 10 if template.protein >= min_protein
    score += 5 for variety (not recently used)
  → Select highest scoring template

Step 4: Nutrition Lookup
  → nutrition_engine_adapter.get_nutrition(ingredient_name)
  → Query nutrition_database.NUTRITION_DATA dictionary
  → Return: calories, protein, carbs, fat per 100g

Step 5: Portion Scaling
  → scaling_engine.scale_meal(template, target_calories)
  → Calculate scaling_factor = target_calories / template.base_calories
  → Scale all ingredient quantities: quantity * scaling_factor
  → Recalculate nutrition: nutrition * scaling_factor
  → Round quantities to reasonable values (50g, 100g, etc.)

Step 6: Validation
  → validation_engine.validate_plan(plan, hcd)
  → Check: total_calories within (min_calories, tdee - max_deficit)
  → Check: total_protein >= min_protein
  → Check: no allergens present
  → Check: no avoided foods present
  → If validation fails: retry with different templates (max 3 attempts)

Step 7: Plan Storage
  → Create DietPlan record
  → plan_type = 'weekly' or 'daily'
  → content = JSON with days, meals, nutrition
  → Store in database
  → Return plan to user

Step 8: Frontend Display
  → Parse plan JSON
  → Render meals in cards
  → Show nutrition summary
  → Enable regeneration buttons
```

### Meal Regeneration Flow

```
Step 1: User clicks "Regenerate Meal" button
  → Frontend calls POST /diet-plans-ml/{plan_id}/regenerate-meal-ml
  → Body: {day_index: 0, meal_index: 1}

Step 2: Backend fetches existing plan
  → Load DietPlan by ID
  → Verify user owns plan
  → Extract current meal at day_index, meal_index

Step 3: Generate new meal
  → Call template_selector with same constraints
  → Exclude current template (for variety)
  → Select new template
  → Lookup nutrition
  → Scale portions
  → Validate

Step 4: Update plan
  → plan.content['days'][day_index]['meals'][meal_index] = new_meal
  → Recalculate daily_nutrition for that day
  → **CRITICAL**: Call flag_modified(plan, "content")
    - SQLAlchemy doesn't detect JSON changes automatically
    - flag_modified forces SQLAlchemy to update the field
  → db.commit()

Step 5: Return updated plan
  → Frontend receives full plan object
  → **CRITICAL**: Use object spreading {...response.data}
    - Forces React to detect state change
    - Triggers re-render
  → Display updated meal
```

### Error Handling Strategy

```
1. Validation Errors (400)
   → Pydantic schema validation
   → Return detailed field errors
   → Frontend displays error messages

2. Authentication Errors (401)
   → JWT token expired/invalid
   → Frontend attempts token refresh
   → If refresh fails: redirect to login

3. Authorization Errors (403)
   → User not approved
   → User not admin (for admin routes)
   → Return clear error message

4. Not Found Errors (404)
   → Resource doesn't exist
   → Return "Resource not found"

5. Rate Limit Errors (429)
   → Too many requests
   → Return "Rate limit exceeded, try again in X seconds"
   → Frontend shows cooldown timer

6. Server Errors (500)
   → Unhandled exceptions
   → Log full stack trace
   → Return generic error in production
   → Return detailed error in development

7. Database Errors
   → Connection failures: Retry 3 times with exponential backoff
   → Constraint violations: Return 400 with specific error
   → Deadlocks: Retry transaction

8. External API Errors (Groq - DISABLED)
   → Timeout: Retry with exponential backoff
   → Rate limit: Wait and retry
   → Invalid response: Log and return error
   → Fallback: Use mock data in development
```


## 7. ENVIRONMENT & CONFIGURATION

### Required Environment Variables

#### Backend (`backend/.env`)

```env
# Database
DATABASE_URL=postgresql://postgres.ytlfneijevuhcwbqqkck:UlhiSGdNxvHm5s06@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres
REDIS_URL=redis://localhost:6379/0  # Optional

# Environment
ENVIRONMENT=development  # development, staging, production
DEBUG=true
TESTING=false

# AI Provider (DISABLED but configured)
AI_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here

# Security
SECRET_KEY=dev-secret-key-change-in-production-12345
JWT_SECRET_KEY=your_jwt_secret_key_here

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

#### Frontend (`frontend/.env`)

```env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_GOOGLE_CLIENT_ID=your_google_client_id_here.apps.googleusercontent.com
```

### Configuration Files

**`backend/app/core/config.py`**: Pydantic Settings
- Loads from environment variables
- Validates types
- Provides defaults
- Environment-specific overrides

**`backend/alembic.ini`**: Alembic configuration
- Database URL (reads from .env)
- Migration script location
- Logging configuration

**`frontend/package.json`**: NPM dependencies
- React, TypeScript, Tailwind
- Axios, React Router
- Build scripts

### Feature Flags

```python
# In backend/app/core/config.py
ENABLE_USER_REGISTRATION = True
ENABLE_AI_GENERATION = False  # AI pipeline disabled
ENABLE_PLAN_REGENERATION = True
ENABLE_ANALYTICS = False
```

### Third-Party Services

1. **Supabase** (PostgreSQL)
   - Purpose: Primary database
   - Connection: Transaction pooler
   - Credentials: In DATABASE_URL

2. **Google OAuth**
   - Purpose: User authentication
   - Client ID: In GOOGLE_CLIENT_ID
   - Client Secret: In GOOGLE_CLIENT_SECRET
   - Redirect URI: http://localhost:3000

3. **Groq API** (DISABLED)
   - Purpose: LLM for AI diet generation
   - API Key: In GROQ_API_KEY
   - Model: llama-3.1-8b-instant
   - Status: Configured but not used

4. **Redis** (Optional)
   - Purpose: Caching
   - Connection: REDIS_URL
   - Fallback: In-memory cache if unavailable

---

## 8. EXTERNAL INTEGRATIONS

### Google OAuth Integration

**Purpose**: User authentication

**Flow**:
1. Frontend uses `@react-oauth/google` library
2. User clicks "Sign in with Google"
3. Google OAuth popup opens
4. User authorizes
5. Google returns authorization code
6. Frontend sends code to backend
7. Backend exchanges code for user info
8. Backend creates/updates user
9. Backend returns JWT tokens

**Configuration**:
- Client ID: `your_google_client_id_here.apps.googleusercontent.com`
- Authorized origins: `http://localhost:3000`
- Authorized redirect URIs: `http://localhost:3000`

**Error Handling**:
- Invalid token: Return 401
- User not approved: Return 403
- Network error: Retry 3 times

### Groq API Integration (DISABLED)

**Purpose**: LLM for AI diet generation (legacy feature)

**Status**: Configured but not actively used. All AI buttons are commented out in frontend.

**Configuration**:
- API Key: `your_groq_api_key_here`
- Model: `llama-3.1-8b-instant`
- Max tokens: 1000
- Temperature: 0.7

**Implementation** (`backend/app/services/ai_service.py`):
- Provider abstraction layer
- Retry logic with exponential backoff
- Rate limit handling
- Response validation
- JSON parsing with repair

**Why Disabled**:
- ML pipeline provides more predictable results
- Eliminates LLM API costs
- Faster response times
- No rate limiting issues
- Easier to debug

### Supabase Integration

**Purpose**: Managed PostgreSQL database

**Connection Details**:
- Host: `aws-1-ap-southeast-2.pooler.supabase.com`
- Port: 5432 (transaction pooler)
- Database: `postgres`
- Project: `ytlfneijevuhcwbqqkck`

**Features Used**:
- PostgreSQL 17.6
- Connection pooling
- Automatic backups
- Dashboard for manual queries

**Not Used**:
- Supabase Auth (using custom JWT)
- Supabase Storage
- Supabase Realtime
- Supabase Edge Functions

### Rate Limiting

**Implementation**: Custom middleware (`backend/app/middleware/security.py`)

**Limits**:
- Default: 60 requests/minute
- Auth endpoints: 10 requests/minute
- Plan generation: 20 requests/minute
- Admin endpoints: 30 requests/minute

**Strategy**:
- In-memory counter (per IP)
- Sliding window
- Returns 429 with Retry-After header

**Future**: Move to Redis for distributed rate limiting

---

## 9. STATE MANAGEMENT (Frontend)

### Architecture

**Pattern**: React Context API + Local State

**Global State** (`src/context/AuthContext.tsx`):
- User authentication status
- User profile data
- JWT tokens
- Admin role

**Local State**:
- Component-specific UI state
- Form inputs
- Loading states
- Error messages

### Auth Context

```typescript
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (token: string) => void;
  logout: () => void;
  refreshToken: () => Promise<void>;
}
```

**Storage**: localStorage
- `access_token`: JWT access token
- `refresh_token`: JWT refresh token
- `user`: User profile JSON

**Token Refresh**:
- Automatic on 401 responses
- Checks token expiry before requests
- Refreshes if < 5 minutes remaining

### API Integration Layer

**File**: `src/services/api.ts`

**Axios Instance**:
```typescript
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});
```

**Request Interceptor**:
- Adds Authorization header
- Adds request ID for tracing

**Response Interceptor**:
- Handles 401 (token refresh)
- Handles 403 (redirect to login)
- Handles 429 (rate limit)
- Parses error messages

### State Flow

```
User Action → Component → API Call → Response → State Update → Re-render

Example: Generate Diet Plan
1. User clicks "Generate Plan (ML)"
2. DietPlans.tsx calls api.generateDailyPlanML()
3. Axios sends POST /diet-plans-ml/daily
4. Backend processes request
5. Response returns plan object
6. Component updates local state: setPlan({...response.data})
7. React re-renders with new plan
8. MealCard components display meals
```

### Critical State Management Patterns

**1. Object Spreading for Re-renders**:
```typescript
// WRONG - React won't detect change
setPlan(response.data);

// CORRECT - Forces new object reference
setPlan({...response.data});
```

**2. Flag Modified for SQLAlchemy**:
```python
# WRONG - SQLAlchemy won't detect JSON change
plan.content['days'][0]['meals'][0] = new_meal
db.commit()

# CORRECT - Explicitly mark as modified
plan.content['days'][0]['meals'][0] = new_meal
flag_modified(plan, "content")
db.commit()
```

**3. Token Refresh**:
```typescript
// Automatic refresh on 401
api.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      await refreshToken();
      return api.request(error.config);
    }
    return Promise.reject(error);
  }
);
```


## 10. DEPLOYMENT & DEV WORKFLOW

### Local Development Setup

**Prerequisites**:
- Python 3.11+
- Node.js 18+
- PostgreSQL (or Supabase account)
- Git

**Backend Setup**:
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
cp .env.example .env  # Edit with your secrets
python run_migrations.py
python start_backend.py
```

**Frontend Setup**:
```bash
cd frontend
npm install
cp .env.example .env  # Edit with your API URL
npm start
```

**Verification**:
- Backend: http://localhost:8000/health
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

### Branching Strategy

**Current**: Feature branches
- `main` - Production-ready code
- `dev` - Development branch
- `fb/mu/*` - Feature branches (e.g., `fb/mu/introduce_machine_learning_for_ingredients_collection`)

**Workflow**:
1. Create feature branch from `dev`
2. Develop feature
3. Test locally
4. Commit with descriptive messages
5. Push to remote
6. Create pull request to `dev`
7. Code review
8. Merge to `dev`
9. Deploy to staging (future)
10. Merge `dev` to `main` for production

### CI/CD

**Status**: Not yet configured

**Planned**:
- GitHub Actions for CI
- Automated testing on PR
- Automated deployment to staging
- Manual approval for production

**Future Pipeline**:
```yaml
# .github/workflows/ci.yml
on: [push, pull_request]
jobs:
  test-backend:
    - Setup Python
    - Install dependencies
    - Run pytest
    - Check coverage
  
  test-frontend:
    - Setup Node
    - Install dependencies
    - Run tests
    - Build production
  
  deploy-staging:
    - If branch is dev
    - Deploy to staging server
  
  deploy-production:
    - If branch is main
    - Require manual approval
    - Deploy to production
```

### Build Process

**Backend**:
```bash
# No build step - Python runs directly
# For production:
pip install -r requirements.txt
gunicorn app.main:app --workers 4 --bind 0.0.0.0:8000
```

**Frontend**:
```bash
npm run build
# Creates optimized production build in build/
# Serve with nginx or static hosting
```

### Docker Usage

**Status**: Docker Compose configured but not actively used

**Files**:
- `docker-compose.yml` - Local development
- `docker-compose.prod.yml` - Production
- `backend/Dockerfile` - Backend image
- `frontend/Dockerfile` - Frontend image

**Usage**:
```bash
docker-compose up -d
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# PostgreSQL: localhost:5432
```

**Current Approach**: Direct execution (no Docker) for faster development

### Database Migrations

**Tool**: Alembic

**Create Migration**:
```bash
cd backend
alembic revision --autogenerate -m "description"
# Review generated file in alembic/versions/
# Edit if needed
alembic upgrade head
```

**Apply Migrations**:
```bash
python run_migrations.py
# Or: alembic upgrade head
```

**Rollback**:
```bash
alembic downgrade -1  # One version back
alembic downgrade <revision>  # Specific version
```

---

## 11. CURRENT LIMITATIONS & TECH DEBT

### Known Issues

1. **ML Pipeline Limitations**
   - Only 17 hardcoded meal templates
   - Limited variety in meal options
   - No actual ML model inference (heuristic scoring only)
   - Ingredient canonicalizer implemented but not used
   - No personalization beyond dietary restrictions

2. **Database**
   - No foreign key constraints (only logical references)
   - No cascading deletes
   - No database-level triggers
   - JSON fields not indexed (slow queries on large datasets)

3. **Authentication**
   - Tokens stored in localStorage (vulnerable to XSS)
   - No refresh token rotation
   - No device tracking
   - No session management

4. **Frontend**
   - No error boundaries
   - No loading skeletons
   - No optimistic updates
   - No offline support
   - No service worker

5. **Testing**
   - Limited test coverage
   - No integration tests
   - No E2E tests
   - No performance tests

6. **Monitoring**
   - Basic logging only
   - No APM (Application Performance Monitoring)
   - No error tracking (Sentry)
   - No metrics dashboard
   - No alerting

### Scalability Concerns

1. **Database**
   - Single PostgreSQL instance
   - No read replicas
   - No connection pooling at application level
   - JSON queries not optimized

2. **Backend**
   - Single server deployment
   - No load balancing
   - No horizontal scaling
   - In-memory rate limiting (not distributed)

3. **Caching**
   - Redis optional (not required)
   - No CDN for static assets
   - No query result caching
   - No API response caching

4. **ML Pipeline**
   - Synchronous processing (blocks request)
   - No background jobs
   - No queue system
   - Template selection is O(n) for each meal

### Security Gaps

1. **Input Validation**
   - Pydantic validation only
   - No SQL injection protection beyond ORM
   - No XSS sanitization in frontend
   - No CSRF protection

2. **Rate Limiting**
   - In-memory only (can be bypassed with multiple IPs)
   - No distributed rate limiting
   - No IP-based blocking

3. **Secrets Management**
   - Secrets in .env files
   - No secret rotation
   - No encryption at rest
   - API keys exposed in git history (need rotation)

4. **API Security**
   - No API versioning strategy
   - No request signing
   - No webhook verification
   - No audit logging

### Performance Bottlenecks

1. **Database Queries**
   - N+1 queries in some endpoints
   - No query optimization
   - No database indexes on foreign keys
   - JSON field queries are slow

2. **ML Pipeline**
   - Template selection loops through all templates
   - Nutrition lookup for each ingredient
   - No caching of template scores
   - No parallel processing

3. **Frontend**
   - No code splitting
   - No lazy loading
   - Large bundle size
   - No image optimization

### Planned Improvements

1. **Short Term** (1-2 months)
   - Add more meal templates (50+)
   - Implement actual ML model for template selection
   - Add database foreign keys
   - Improve error handling
   - Add loading states

2. **Medium Term** (3-6 months)
   - Implement LightGBM for template scoring
   - Add background job queue (Celery)
   - Implement caching layer (Redis)
   - Add comprehensive testing
   - Set up CI/CD pipeline

3. **Long Term** (6-12 months)
   - Implement workout planner
   - Add progress tracking
   - Build native mobile apps
   - Implement real-time features
   - Add AI coaching insights

---

## 12. CRITICAL ENTRY POINTS

### Backend Entry Point

**File**: `backend/app/main.py`

**Initialization Sequence**:
```python
1. Import FastAPI and dependencies
2. Define lifespan context manager
   - Startup: Import models, create tables, setup logging
   - Shutdown: Cleanup resources
3. Create FastAPI app instance
4. Add middleware (CORS, Security, Rate Limiting, Trusted Hosts)
5. Add custom middleware (security headers, HTTPS enforcement)
6. Add exception handlers
7. Define health check endpoints
8. Include API routers
9. Run with uvicorn
```

**Request Lifecycle**:
```
1. Request arrives at uvicorn
2. CORS middleware checks origin
3. Security middleware sanitizes input
4. Rate limit middleware checks limits
5. Trusted host middleware validates host
6. Security headers middleware adds headers
7. HTTPS enforcement (production only)
8. Route to appropriate endpoint
9. Auth middleware validates JWT (if required)
10. Admin middleware checks admin role (if required)
11. Endpoint handler executes
12. Service layer processes business logic
13. Database operations via SQLAlchemy
14. Response serialization via Pydantic
15. Response returned through middleware chain
16. Client receives response
```

### Frontend Entry Point

**File**: `frontend/src/index.tsx`

**Initialization Sequence**:
```typescript
1. Import React and ReactDOM
2. Import App component
3. Import global CSS (Tailwind)
4. Render App component to root div
5. Enable React StrictMode (development)
```

**App Component** (`frontend/src/App.tsx`):
```typescript
1. Setup AuthContext provider
2. Setup React Router
3. Define routes:
   - / → Login
   - /profile → Profile (protected)
   - /diet-plans → DietPlans (protected)
   - /admin → AdminDashboard (protected, admin only)
4. Render Navbar
5. Render route content
```

**Component Lifecycle**:
```
1. Component mounts
2. useEffect hooks run
3. API calls initiated
4. Loading state displayed
5. Response received
6. State updated
7. Component re-renders
8. Data displayed
9. User interactions trigger state changes
10. Component updates
```

### Database Connection

**File**: `backend/app/database/connection.py`

**Initialization**:
```python
1. Load DATABASE_URL from environment
2. Create SQLAlchemy engine
   - Pool size: 5
   - Max overflow: 10
   - Pool timeout: 30s
   - Pool recycle: 3600s
3. Create SessionLocal factory
4. Define Base for models
5. Export engine, SessionLocal, Base
```

**Session Management**:
```python
# Dependency injection pattern
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Usage in endpoints
@router.get("/users/me")
def get_current_user(db: Session = Depends(get_db)):
    # db is automatically managed
    user = db.query(User).filter(...).first()
    return user
```

---

## 13. HOW TO EXTEND THE SYSTEM

### Adding New API Endpoints

**Step 1**: Create endpoint file
```python
# backend/app/api/endpoints/new_feature.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/new-feature", tags=["new-feature"])

@router.get("/")
def list_items(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Implementation
    return {"items": []}
```

**Step 2**: Include router in main router
```python
# backend/app/api/router.py
from app.api.endpoints.new_feature import router as new_feature_router

api_router.include_router(new_feature_router)
```

**Step 3**: Add service layer
```python
# backend/app/services/new_feature_service.py
def create_item(db, user_id, data):
    # Business logic
    pass
```

**Step 4**: Add schemas
```python
# backend/app/schemas/new_feature.py
from pydantic import BaseModel

class ItemCreate(BaseModel):
    name: str
    description: str

class ItemResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
```

**Step 5**: Add frontend API call
```typescript
// frontend/src/services/api.ts
export const newFeatureAPI = {
  listItems: () => api.get('/new-feature'),
  createItem: (data) => api.post('/new-feature', data)
};
```

### Adding New Database Models

**Step 1**: Create model file
```python
# backend/app/models/new_model.py
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database.connection import Base
import uuid

class NewModel(Base):
    __tablename__ = "new_table"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
```

**Step 2**: Import in models/__init__.py
```python
# backend/app/models/__init__.py
from app.models.new_model import NewModel
```

**Step 3**: Create migration
```bash
cd backend
alembic revision --autogenerate -m "add new_table"
# Review generated migration
alembic upgrade head
```

**Step 4**: Add to Supabase
```bash
python run_migrations.py
```

### Modifying Data Models Safely

**Step 1**: Create migration
```bash
alembic revision -m "add column to users"
```

**Step 2**: Edit migration file
```python
def upgrade():
    op.add_column('users', sa.Column('new_field', sa.String(255), nullable=True))

def downgrade():
    op.drop_column('users', 'new_field')
```

**Step 3**: Test migration
```bash
# Apply
alembic upgrade head

# Test rollback
alembic downgrade -1

# Re-apply
alembic upgrade head
```

**Step 4**: Update model
```python
# backend/app/models/user.py
class User(Base):
    # ... existing fields
    new_field = Column(String(255), nullable=True)
```

**Step 5**: Update schemas
```python
# backend/app/schemas/user.py
class UserResponse(BaseModel):
    # ... existing fields
    new_field: Optional[str] = None
```

### Adding New ML Templates

**Step 1**: Edit meal_templates.py
```python
# backend/app/services/ml_diet_pipeline/meal_templates.py
MEAL_TEMPLATES = [
    # ... existing templates
    {
        "id": "new_template_001",
        "name": "New Meal Name",
        "meal_type": "lunch",
        "diet_type": "vegetarian",
        "ingredients": [
            {"name": "ingredient1", "quantity": 100, "unit": "g"},
            {"name": "ingredient2", "quantity": 50, "unit": "g"}
        ],
        "base_nutrition": {
            "calories": 400,
            "protein": 20,
            "carbohydrates": 50,
            "fat": 10
        }
    }
]
```

**Step 2**: Ensure ingredients exist in nutrition database
```python
# backend/app/services/nutrition_database.py
NUTRITION_DATA = {
    # ... existing data
    "ingredient1": {
        "calories": 100,
        "protein": 5,
        "carbohydrates": 20,
        "fat": 2
    }
}
```

**Step 3**: Test template
```bash
# Generate plan and verify new template appears
curl -X POST http://localhost:8000/api/v1/diet-plans-ml/daily \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-02-23"}'
```

### Safe Refactoring Guidelines

1. **Never modify database directly**
   - Always use migrations
   - Test rollback before deploying

2. **Maintain backward compatibility**
   - Add new fields as nullable
   - Deprecate old fields gradually
   - Version API endpoints if breaking changes

3. **Test thoroughly**
   - Unit tests for business logic
   - Integration tests for API endpoints
   - Manual testing in development

4. **Use feature flags**
   - Enable new features gradually
   - Easy rollback if issues arise

5. **Monitor after deployment**
   - Check error logs
   - Monitor performance metrics
   - Watch for user complaints

6. **Document changes**
   - Update API documentation
   - Update README
   - Add migration notes

---

## END OF SYSTEM INTELLIGENCE DOCUMENT

**Document Version**: 1.0  
**Last Updated**: February 22, 2026  
**Maintained By**: Development Team  
**Next Review**: March 2026

This document should be updated whenever:
- New features are added
- Architecture changes
- Database schema changes
- API contracts change
- Deployment process changes

For questions or clarifications, refer to:
- `DOCUMENTATION_INDEX.md` - Documentation hub
- `docs/PROJECT_DOCUMENTATION.md` - Complete project docs
- `spec.md` - Original specification
- API Docs: http://localhost:8000/docs (when running)

