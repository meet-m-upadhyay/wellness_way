# WELLNESSWAY - QUICK REFERENCE GUIDE

**Companion to**: SYSTEM_INTELLIGENCE_DOCUMENT.md

---

## 🎯 WHAT IS THIS PROJECT?

AI-powered diet planning app with ML-based meal generation, health profile management, and admin approval system.

**Status**: MVP complete, ML pipeline active, AI pipeline disabled

---

## 🏗️ ARCHITECTURE AT A GLANCE

```
React (TypeScript) → FastAPI (Python) → PostgreSQL (Supabase)
                   ↓
            ML Pipeline (Active)
            AI Pipeline (Disabled)
```

---

## 📁 KEY FILES TO KNOW

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI entry point |
| `backend/app/api/endpoints/diet_plans_ml.py` | ML diet plan endpoints (ACTIVE) |
| `backend/app/services/ml_diet_pipeline/orchestrator.py` | ML pipeline coordinator |
| `backend/app/services/ml_diet_pipeline/meal_templates.py` | 17 hardcoded templates |
| `backend/app/models/user.py` | User, HealthGoals, DietPreferences models |
| `backend/app/models/health_context.py` | HealthContextDocument model |
| `backend/app/models/diet_plan.py` | DietPlan model |
| `frontend/src/pages/DietPlans.tsx` | Main diet plan UI |
| `frontend/src/services/api.ts` | API client |

---

## 🗄️ DATABASE TABLES

1. `users` - User accounts
2. `health_context_documents` - Versioned health profiles
3. `diet_plans` - Generated meal plans
4. `health_goals` - User goals
5. `diet_preferences` - Dietary preferences
6. `registration_requests` - Admin approval queue
7. `alembic_version` - Migration tracking

---

## 🔑 CRITICAL PATTERNS

### 1. SQLAlchemy JSON Updates
```python
# WRONG
plan.content['days'][0] = new_day
db.commit()

# CORRECT
plan.content['days'][0] = new_day
flag_modified(plan, "content")
db.commit()
```

### 2. React State Updates
```typescript
// WRONG
setPlan(response.data);

// CORRECT
setPlan({...response.data});
```

### 3. Health Calculations
```python
# BMR (Mifflin-St Jeor)
Men: (10 × weight) + (6.25 × height) - (5 × age) + 5
Women: (10 × weight) + (6.25 × height) - (5 × age) - 161

# TDEE
TDEE = BMR × activity_multiplier
```

---

## 🚀 QUICK START

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run_migrations.py
python start_backend.py

# Frontend
cd frontend
npm install
npm start
```

---

## 🔐 ENVIRONMENT SECRETS

See `NOTION_SECRETS_TEMPLATE.md` for complete list.

**Critical**:
- `DATABASE_URL` - Supabase connection
- `GROQ_API_KEY` - AI provider (disabled but configured)
- `GOOGLE_CLIENT_ID` - OAuth
- `GOOGLE_CLIENT_SECRET` - OAuth
- `JWT_SECRET_KEY` - Token signing

---

## 🎨 ML PIPELINE FLOW

```
User Request
  → Fetch HCD
  → Select Templates (heuristic scoring)
  → Lookup Nutrition (database)
  → Scale Portions (math)
  → Validate (rules)
  → Store Plan
  → Return Response
```

---

## 🐛 COMMON ISSUES

1. **Plan not updating after regeneration**
   - Backend: Missing `flag_modified(plan, "content")`
   - Frontend: Missing object spreading `{...response.data}`

2. **JWT token expired**
   - Frontend auto-refreshes on 401
   - Check token expiry logic in AuthContext

3. **Database connection fails**
   - Verify Supabase project is active
   - Check DATABASE_URL format
   - Run `python test_supabase_connection.py`

4. **Templates not appearing**
   - Check diet_type matches user preferences
   - Verify ingredients exist in nutrition database
   - Check template scoring logic

---

## 📊 API ENDPOINTS (ACTIVE)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/google` | POST | Google OAuth login |
| `/users/me` | GET | Get current user |
| `/health-context` | POST | Create HCD |
| `/diet-plans-ml/daily` | POST | Generate daily plan (ML) |
| `/diet-plans-ml/weekly` | POST | Generate weekly plan (ML) |
| `/diet-plans-ml/{id}/regenerate-meal-ml` | POST | Regenerate meal |
| `/diet-plans-ml/{id}/regenerate-day-ml` | POST | Regenerate day |
| `/diet-plans-ml/{id}/regenerate-week-ml` | POST | Regenerate week |
| `/admin/users` | GET | List users (admin) |
| `/admin/registration-requests` | GET | List pending registrations |

---

## 🔧 EXTENDING THE SYSTEM

### Add New Endpoint
1. Create file in `backend/app/api/endpoints/`
2. Include router in `backend/app/api/router.py`
3. Add service in `backend/app/services/`
4. Add schema in `backend/app/schemas/`
5. Add frontend API call in `frontend/src/services/api.ts`

### Add New Model
1. Create model in `backend/app/models/`
2. Import in `backend/app/models/__init__.py`
3. Create migration: `alembic revision --autogenerate`
4. Apply migration: `python run_migrations.py`

### Add New Template
1. Edit `backend/app/services/ml_diet_pipeline/meal_templates.py`
2. Ensure ingredients exist in `nutrition_database.py`
3. Test with plan generation

---

## 📚 DOCUMENTATION

- **Complete System Docs**: `SYSTEM_INTELLIGENCE_DOCUMENT.md`
- **Project Docs**: `docs/PROJECT_DOCUMENTATION.md`
- **Documentation Hub**: `DOCUMENTATION_INDEX.md`
- **Specification**: `spec.md`
- **API Docs**: http://localhost:8000/docs (when running)

---

## ⚠️ KNOWN LIMITATIONS

1. Only 17 hardcoded meal templates
2. No actual ML model inference (heuristic scoring)
3. No foreign key constraints in database
4. Tokens in localStorage (XSS vulnerable)
5. No comprehensive testing
6. No CI/CD pipeline
7. Single server deployment
8. In-memory rate limiting

---

## 🎯 NEXT STEPS

**Short Term**:
- Add more meal templates (50+)
- Implement actual ML model
- Add database foreign keys
- Improve error handling

**Medium Term**:
- Implement LightGBM for scoring
- Add background job queue
- Implement Redis caching
- Add comprehensive testing
- Set up CI/CD

**Long Term**:
- Implement workout planner
- Add progress tracking
- Build native mobile apps
- Add AI coaching insights

---

**For detailed information, see**: `SYSTEM_INTELLIGENCE_DOCUMENT.md`
