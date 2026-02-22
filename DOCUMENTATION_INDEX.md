# WellnessWay Documentation Index

**Last Updated**: February 22, 2026

This is your central hub for all project documentation. Everything you need is organized here.

---

## 📖 Essential Reading

### Start Here
1. **[README.md](README.md)** - Project overview and introduction
2. **[QUICK_START.md](QUICK_START.md)** - Get the app running in 5 minutes
3. **[docs/PROJECT_DOCUMENTATION.md](docs/PROJECT_DOCUMENTATION.md)** - Complete consolidated documentation

### For New Developers
- [docs/ENVIRONMENT_SETUP.md](docs/ENVIRONMENT_SETUP.md) - Development environment setup
- [spec.md](spec.md) - Project specification and requirements
- [NOTIFICATION_SYSTEM_ARCHITECTURE.md](NOTIFICATION_SYSTEM_ARCHITECTURE.md) - System architecture

---

## 🗄️ Database & Infrastructure

### Setup & Migration
- **[SUPABASE_MIGRATION_SUCCESS.md](SUPABASE_MIGRATION_SUCCESS.md)** - Supabase setup guide (CURRENT)
- [docs/SUPABASE_MIGRATION.md](docs/SUPABASE_MIGRATION.md) - Detailed migration guide
- [backend/DATABASE_SETUP.md](backend/DATABASE_SETUP.md) - Database configuration
- [database_management_commands.md](database_management_commands.md) - Common DB commands

### Migrations
- [backend/ALEMBIC_MIGRATION_SYSTEM.md](backend/ALEMBIC_MIGRATION_SYSTEM.md) - Alembic migration system

---

## 🤖 ML & AI Features

### ML Pipeline
- **[ML_MODELS_USED.md](ML_MODELS_USED.md)** - ML models and architecture
- [docs/PROJECT_DOCUMENTATION.md#ml-pipeline](docs/PROJECT_DOCUMENTATION.md#ml-pipeline) - ML pipeline details

### Features
- Diet plan generation (ML-based)
- Meal regeneration
- Ingredient canonicalization
- Nutrition calculations

---

## 🔐 Authentication & Security

### Setup
- **[GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md)** - Google OAuth configuration
- **[SECURITY_REMINDER.md](SECURITY_REMINDER.md)** - Security best practices

### Features
- JWT authentication
- Google OAuth integration
- Admin access control
- User approval workflow

---

## 🚀 Deployment & CI/CD

- [docs/CI_CD_SETUP.md](docs/CI_CD_SETUP.md) - Deployment and CI/CD setup
- Environment configuration
- Production best practices

---

## 🧪 Testing

### Test Organization
- `backend/tests/` - Organized unit tests (KEEP)
- `backend/test_supabase_connection.py` - Connection testing utility
- `backend/test_ml_pipeline.py` - ML pipeline tests
- `backend/test_admin_system.py` - Admin system tests

### Running Tests
```bash
cd backend
pytest                          # Run all tests
pytest tests/                   # Run organized tests only
pytest test_ml_pipeline.py      # Run specific test
```

---

## 📚 API Documentation

### Interactive Docs
When backend is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints
- `/api/v1/auth/*` - Authentication
- `/api/v1/users/*` - User management
- `/api/v1/diet-plans/*` - AI diet plans (disabled)
- `/api/v1/diet-plans-ml/*` - ML diet plans (active)
- `/api/v1/health-context/*` - Health profiles
- `/api/v1/admin/*` - Admin functions

---

## 🛠️ Development Guide

### Code Organization
```
wellness_way/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/     # API routes
│   │   ├── services/          # Business logic
│   │   │   └── ml_diet_pipeline/  # ML pipeline
│   │   ├── models/            # Database models
│   │   └── schemas/           # Pydantic schemas
│   └── tests/                 # Unit tests
├── frontend/
│   └── src/
│       ├── components/        # React components
│       ├── pages/             # Page components
│       └── services/          # API client
└── docs/                      # Documentation
```

### Key Files
- `backend/start_backend.py` - Start backend server
- `backend/run_migrations.py` - Run database migrations
- `backend/test_supabase_connection.py` - Test DB connection
- `cleanup_project.py` - Clean up unnecessary files

---

## 🧹 Project Maintenance

### Cleanup
- **[docs/CLEANUP_PLAN.md](docs/CLEANUP_PLAN.md)** - What files can be deleted
- Run `python cleanup_project.py` to clean up automatically

### What Was Cleaned
- ~85 ad-hoc test files removed
- ~35 redundant documentation files consolidated
- ~15 debug scripts removed
- All essential functionality preserved

---

## 🆘 Troubleshooting

### Common Issues

**Backend won't start**
- Check `backend/.env` has correct DATABASE_URL
- Verify Supabase project is active
- Run: `python backend/test_supabase_connection.py`

**Frontend can't connect**
- Ensure backend is running on port 8000
- Check `frontend/.env` has correct REACT_APP_API_URL
- Verify CORS settings

**Database errors**
- Run migrations: `python backend/run_migrations.py`
- Check connection: `python backend/test_supabase_connection.py`
- Verify Supabase credentials

**ML pipeline errors**
- Check meal templates exist
- Verify nutrition database is populated
- Review logs for specific errors

See [docs/PROJECT_DOCUMENTATION.md#troubleshooting](docs/PROJECT_DOCUMENTATION.md#troubleshooting) for detailed solutions.

---

## 📋 Quick Reference

### Start Development
```bash
# Backend
cd backend
venv\Scripts\activate
python start_backend.py

# Frontend
cd frontend
npm start
```

### Run Tests
```bash
cd backend
pytest tests/
```

### Database Operations
```bash
# Run migrations
python run_migrations.py

# Test connection
python test_supabase_connection.py
```

### Cleanup Project
```bash
python cleanup_project.py
```

---

## 📞 Support

- **GitHub Issues**: https://github.com/meet-m-upadhyay/wellness_way/issues
- **Documentation**: This index and linked files
- **API Docs**: http://localhost:8000/docs (when running)

---

## 🗂️ File Organization

### Keep These Files
- All files in `backend/tests/` folder
- `backend/test_supabase_connection.py`
- `backend/test_ml_pipeline.py`
- `backend/test_admin_system.py`
- All documentation listed in this index

### Can Delete
- Ad-hoc test files in `backend/` root (except those listed above)
- `*_COMPLETION_REPORT.md` files
- `CHATGPT_*.md` files
- Debug scripts (`debug_*.py`)
- See [docs/CLEANUP_PLAN.md](docs/CLEANUP_PLAN.md) for complete list

---

## 📝 Contributing

1. Read [docs/PROJECT_DOCUMENTATION.md](docs/PROJECT_DOCUMENTATION.md)
2. Follow code style guidelines
3. Write tests for new features
4. Update documentation
5. Submit pull request

---

**This index is your starting point. For detailed information, follow the links to specific documentation files.**

Generated: February 22, 2026
