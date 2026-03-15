# WellnessWay - Complete Project Documentation

**Last Updated**: February 22, 2026

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [ML Pipeline](#ml-pipeline)
4. [Database Setup](#database-setup)
5. [Authentication](#authentication)
6. [Admin System](#admin-system)
7. [Troubleshooting](#troubleshooting)
8. [Development Guide](#development-guide)

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Supabase account (or PostgreSQL)
- Redis (optional, for caching)

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/meet-m-upadhyay/wellness_way.git
cd wellness_way

# Backend setup
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

### 2. Configure Environment

Create `backend/.env`:
```env
DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
REDIS_URL=redis://localhost:6379/0
ENVIRONMENT=development
DEBUG=true

# AI Provider
AI_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_here

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
```

Create `frontend/.env`:
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
```

### 3. Run Application

```bash
# Terminal 1: Backend
cd backend
python start_backend.py

# Terminal 2: Frontend
cd frontend
npm start
```

Access at: http://localhost:3000

---

## Architecture Overview

### Tech Stack

**Backend**:
- FastAPI (Python web framework)
- SQLAlchemy (ORM)
- PostgreSQL (Supabase)
- Redis (caching)
- Alembic (migrations)

**Frontend**:
- React 18
- TypeScript
- Tailwind CSS
- Axios (API client)

**AI/ML**:
- Groq API (LLM provider)
- Sentence Transformers (ingredient canonicalization)
- Deterministic nutrition calculations

### Project Structure

```
wellness_way/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/     # API routes
│   │   ├── core/              # Config, security
│   │   ├── database/          # DB connection
│   │   ├── middleware/        # Auth, admin
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business logic
│   │       └── ml_diet_pipeline/  # ML pipeline
│   ├── alembic/               # Database migrations
│   └── tests/                 # Unit tests
├── frontend/
│   └── src/
│       ├── components/        # React components
│       ├── pages/             # Page components
│       ├── services/          # API client
│       └── context/           # React context
└── docs/                      # Documentation
```

---

## ML Pipeline

### Overview

The ML pipeline generates personalized diet plans using:
1. Hardcoded meal templates (17 templates)
2. Heuristic template selection
3. Deterministic nutrition calculations
4. Portion scaling algorithms

### How It Works

#### 1. Template Selection
```python
# Templates are scored based on:
- Meal type match (breakfast, lunch, dinner, snack)
- Dietary restrictions (vegetarian, vegan, etc.)
- Calorie target proximity
- Protein requirements
```

#### 2. Nutrition Calculation
```python
# Deterministic calculations:
- Lookup nutrition from database
- Scale portions to meet targets
- Aggregate meal nutrition
- Validate against requirements
```

#### 3. Plan Generation

**Daily Plan**:
- 3 meals + 2 snacks
- Meets calorie target ±10%
- Respects dietary restrictions

**Weekly Plan**:
- 7 days of daily plans
- Variety across days
- Consistent nutrition targets

### API Endpoints

```
POST /api/v1/diet-plans-ml/daily
POST /api/v1/diet-plans-ml/weekly
POST /api/v1/diet-plans-ml/{plan_id}/regenerate-meal-ml
POST /api/v1/diet-plans-ml/{plan_id}/regenerate-day-ml
POST /api/v1/diet-plans-ml/{plan_id}/regenerate-week-ml
```

### ML Models Used

**Active**:
- Sentence Transformer (`all-MiniLM-L6-v2`) - ingredient canonicalization (implemented but not actively used)

**Planned**:
- LightGBM - template selection (not yet implemented)
- Neural networks - portion optimization (future)

**Current Reality**:
- Heuristic scoring for template selection
- Deterministic math for nutrition calculations
- No active ML inference in production

### Frontend Integration

ML buttons (purple 🧠) are available for:
- Generate Plan (ML)
- Regenerate Meal
- Regenerate Day
- Regenerate Week

AI buttons (blue 🤖) are currently disabled.

---

## Database Setup

### Supabase (Recommended)

#### 1. Create Project
1. Go to https://supabase.com/dashboard
2. Create new project
3. Note your connection details

#### 2. Get Connection String
- Settings → Database → Connection String
- Use **Transaction pooler** (port 5432)
- Format: `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres`

#### 3. Run Migrations
```bash
cd backend
python run_migrations.py
```

#### 4. Verify Connection
```bash
python test_supabase_connection.py
```

### Local PostgreSQL (Alternative)

```bash
# Install PostgreSQL
# Create database
createdb wellnessway_db

# Update backend/.env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/wellnessway_db

# Run migrations
python run_migrations.py
```

### Database Schema

**Tables**:
- `users` - User accounts
- `health_context_documents` - User health profiles
- `health_goals` - User fitness goals
- `diet_preferences` - Dietary restrictions
- `diet_plans` - Generated diet plans
- `registration_requests` - Admin approval queue
- `alembic_version` - Migration tracking

---

## Authentication

### Google OAuth Setup

#### 1. Create OAuth Credentials
1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID
3. Add authorized origins:
   - `http://localhost:3000`
   - Your production domain
4. Add authorized redirect URIs:
   - `http://localhost:3000`
   - Your production domain

#### 2. Configure Application
Update `backend/.env` and `frontend/.env` with your credentials.

#### 3. Test Login
- Click "Sign in with Google"
- Authorize application
- Should redirect to dashboard

### JWT Authentication

- Access tokens expire in 30 minutes
- Refresh tokens expire in 7 days
- Tokens stored in localStorage
- Auto-refresh on API calls

### Admin Access

Admins can:
- View all users
- Approve/reject registrations
- Disable/enable users
- View system statistics

To make a user admin:
```sql
UPDATE users SET is_admin = true WHERE email = 'admin@example.com';
```

---

## Admin System

### Features

1. **User Management**
   - View all users
   - Search and filter
   - Enable/disable accounts

2. **Registration Approval**
   - Review pending requests
   - Approve/reject with reason
   - Email notifications (planned)

3. **System Monitoring**
   - User statistics
   - Plan generation metrics
   - Error tracking

### Access Admin Panel

1. Login as admin user
2. Navigate to `/admin`
3. View dashboard

---

## Troubleshooting

### Backend Won't Start

**Error**: `Database connection failed`
- Check DATABASE_URL in `backend/.env`
- Verify Supabase project is active
- Test connection: `python test_supabase_connection.py`

**Error**: `Module not found`
- Activate virtual environment: `venv\Scripts\activate`
- Install dependencies: `pip install -r requirements.txt`

### Frontend Issues

**Error**: `API request failed`
- Ensure backend is running on port 8000
- Check REACT_APP_API_URL in `frontend/.env`
- Verify CORS settings in backend

**Error**: `Google OAuth not working`
- Check REACT_APP_GOOGLE_CLIENT_ID in `frontend/.env`
- Verify authorized origins in Google Console
- Clear browser cache and cookies

### ML Pipeline Issues

**Error**: `No suitable template found`
- Check meal templates in `ml_diet_pipeline/meal_templates.py`
- Verify dietary restrictions are supported
- Review calorie targets (should be 1200-4000)

**Error**: `Nutrition lookup failed`
- Verify nutrition database is populated
- Check ingredient names match database
- Review logs for specific ingredient errors

### Database Issues

**Error**: `Relation does not exist`
- Run migrations: `python run_migrations.py`
- Check Alembic version: `alembic current`

**Error**: `Connection pool exhausted`
- Use pooler connection (port 6543 for Supabase)
- Increase pool size in connection settings
- Check for connection leaks in code

---

## Development Guide

### Running Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_auth_system.py

# Run with coverage
pytest --cov=app tests/
```

### Code Style

**Python**:
- Follow PEP 8
- Use type hints
- Document functions with docstrings

**TypeScript**:
- Follow ESLint rules
- Use TypeScript strict mode
- Document complex functions

### Adding New Features

1. **Backend**:
   - Create endpoint in `app/api/endpoints/`
   - Add business logic in `app/services/`
   - Create tests in `tests/`
   - Update API documentation

2. **Frontend**:
   - Create component in `src/components/`
   - Add API call in `src/services/api.ts`
   - Update routing if needed
   - Test in browser

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Review migration file
# Edit if needed

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Deployment

See `docs/CI_CD_SETUP.md` for deployment instructions.

---

## API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Support

- GitHub Issues: https://github.com/meet-m-upadhyay/wellness_way/issues
- Documentation: `/docs` folder
- Email: support@wellnessway.com (if applicable)

---

## License

[Your License Here]

---

**Generated**: February 22, 2026
**Version**: 1.0.0
