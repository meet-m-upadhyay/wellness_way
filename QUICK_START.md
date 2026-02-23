# WellnessWay - Quick Start Guide

Get the application running in 5 minutes!

---

## 📋 Prerequisites

- **Python 3.11+** - Backend runtime
- **Node.js 18+** - Frontend runtime
- **Git** - Version control
- **Supabase Account** (or local PostgreSQL)

---

## 🚀 Quick Setup (5 Minutes)

### Step 1: Clone Repository

```bash
git clone https://github.com/meet-m-upadhyay/wellness_way.git
cd wellness_way
```

### Step 2: Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate  # Windows
# OR
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file (see Environment Variables section below)
# Copy your secrets from Notion or create new ones

# Run database migrations (if you want to create a new database)
python run_migrations.py
# ELSE (if you want to continue with same database on supabase)
python test_supabase_connection.py

# Start backend server
python start_backend.py
```

Backend will run on: **http://localhost:8000**(configurable via `PORT` in `.env`)

### Step 3: Setup Frontend

```bash
# Open new terminal
cd frontend

# Install dependencies
npm install

# Create .env file (see Environment Variables section below)

# Start frontend
npm start
```

Frontend will run on: **http://localhost:3000**

### Step 4: Verify Setup

- **Backend Health**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000

---

## 🔐 Environment Variables

### Backend Environment File (`backend/.env`)

Create `backend/.env` with the following content:

```env
# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
DATABASE_URL=postgresql://postgres.ytlfneijevuhcwbqqkck:UlhiSGdNxvHm5s06@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres
REDIS_URL=redis://localhost:6379/0

# =============================================================================
# ENVIRONMENT
# =============================================================================
ENVIRONMENT=development
DEBUG=true

# =============================================================================
# AI PROVIDER (Currently disabled, but configured)
# =============================================================================
AI_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here

# =============================================================================
# SECURITY
# =============================================================================
SECRET_KEY=dev-secret-key-change-in-production-12345
JWT_SECRET_KEY=your_jwt_secret_key_here

# =============================================================================
# GOOGLE OAUTH
# =============================================================================
GOOGLE_CLIENT_ID=your_google_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

**Where to get these values:**
- **DATABASE_URL**: From your Supabase dashboard (Settings → Database → Connection String)
- **GROQ_API_KEY**: From https://console.groq.com/keys
- **JWT_SECRET_KEY**: Generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"`
- **GOOGLE_CLIENT_ID & SECRET**: From https://console.cloud.google.com/apis/credentials

### Frontend Environment File (`frontend/.env`)

Create `frontend/.env` with the following content:

```env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_GOOGLE_CLIENT_ID=your_google_client_id_here.apps.googleusercontent.com
```

---

## 🗄️ Database Setup

### Option 1: Supabase (Recommended)

1. **Create Supabase Project**
   - Go to https://supabase.com/dashboard
   - Create new project
   - Note your connection details

2. **Get Connection String**
   - Settings → Database → Connection String
   - Select "URI" tab
   - Copy the connection string
   - Replace `[YOUR-PASSWORD]` with your actual password

3. **Update backend/.env**
   - Set `DATABASE_URL` to your Supabase connection string

4. **Run Migrations**
   ```bash
   cd backend
   python run_migrations.py
   ```

### Option 2: Local PostgreSQL

1. **Install PostgreSQL**
   - Download from https://www.postgresql.org/download/

2. **Create Database**
   ```bash
   createdb wellnessway_db
   ```

3. **Update backend/.env**
   ```env
   DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/wellnessway_db
   ```

4. **Run Migrations**
   ```bash
   cd backend
   python run_migrations.py
   ```

---

## 🔑 Getting API Keys

### 1. Groq API Key (AI Provider - Optional)

1. Go to https://console.groq.com/keys
2. Sign up / Login
3. Create new API key
4. Copy and paste into `backend/.env`

**Note**: AI features are currently disabled. ML pipeline is active instead.

### 2. Google OAuth Credentials

1. Go to https://console.cloud.google.com/apis/credentials
2. Create new project (or select existing)
3. Click "Create Credentials" → "OAuth 2.0 Client ID"
4. Configure consent screen if prompted
5. Application type: "Web application"
6. Add authorized origins:
   - `http://localhost:3000`
   - Your production domain (when deploying)
7. Add authorized redirect URIs:
   - `http://localhost:3000`
   - Your production domain (when deploying)
8. Copy Client ID and Client Secret
9. Paste into `backend/.env` and `frontend/.env`

### 3. JWT Secret Key

Generate a secure random key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Copy the output and paste into `backend/.env` as `JWT_SECRET_KEY`

---

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Can access http://localhost:8000/health (returns `{"status":"healthy"}`)
- [ ] Can access http://localhost:8000/docs (Swagger UI loads)
- [ ] Can access http://localhost:3000 (Frontend loads)
- [ ] Can click "Sign in with Google" (OAuth popup appears)
- [ ] Database connection works (check backend logs)

---

## 🐛 Common Issues

### Backend won't start

**Error**: `Database connection failed`
- **Solution**: Check `DATABASE_URL` in `backend/.env`
- **Solution**: Verify Supabase project is active
- **Solution**: Run `python backend/test_supabase_connection.py`

**Error**: `Module not found`
- **Solution**: Activate virtual environment: `venv\Scripts\activate`
- **Solution**: Install dependencies: `pip install -r requirements.txt`

### Frontend won't start

**Error**: `Cannot find module`
- **Solution**: Install dependencies: `npm install`

**Error**: `API request failed`
- **Solution**: Ensure backend is running on port 8000
- **Solution**: Check `REACT_APP_API_URL` in `frontend/.env`

### Google OAuth not working

**Error**: `Invalid client ID`
- **Solution**: Check `GOOGLE_CLIENT_ID` matches in both `backend/.env` and `frontend/.env`
- **Solution**: Verify authorized origins in Google Console

**Error**: `Redirect URI mismatch`
- **Solution**: Add `http://localhost:3000` to authorized redirect URIs in Google Console

### Database migration fails

**Error**: `Relation already exists`
- **Solution**: Database already has tables, skip migration or reset database

**Error**: `Connection refused`
- **Solution**: Check database is running
- **Solution**: Verify connection string format

---

## 📚 Next Steps

After successful setup:

1. **Create Admin User**
   - Login with Google OAuth
   - Admin will need to approve your registration
   - Or manually set `is_admin=true` in database

2. **Complete Profile**
   - Fill in age, weight, height, etc.
   - Set health goals
   - Set dietary preferences

3. **Generate Diet Plan**
   - Click "Generate Plan (ML)" button
   - View your personalized meal plan
   - Try regenerating meals/days/weeks

4. **Explore Features**
   - View nutrition summaries
   - Check different meal types
   - Test admin dashboard (if admin)

---

## 📖 Documentation

For detailed information, see:

- **Complete System Docs**: `docs/SYSTEM_INTELLIGENCE_DOCUMENT.md`
- **Project Documentation**: `docs/PROJECT_DOCUMENTATION.md`
- **Environment Setup**: `docs/ENVIRONMENT_SETUP.md`
- **Supabase Migration**: `docs/SUPABASE_MIGRATION.md`
- **API Documentation**: http://localhost:8000/docs (when running)

---

## 🆘 Need Help?

1. Check `docs/PROJECT_DOCUMENTATION.md` for detailed guides
2. Review `docs/SYSTEM_INTELLIGENCE_DOCUMENT.md` for architecture
3. Check GitHub issues: https://github.com/meet-m-upadhyay/wellness_way/issues
4. Review backend logs for error messages

---

## 🔄 Development Workflow

### Starting Development

```bash
# Terminal 1 - Backend
cd backend
venv\Scripts\activate
python start_backend.py

# Terminal 2 - Frontend
cd frontend
npm start
```

### Making Changes

1. Make code changes
2. Backend auto-reloads (if using `start_backend.py`)
3. Frontend auto-reloads (React hot reload)
4. Test changes in browser

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests (if configured)
cd frontend
npm test
```

### Database Migrations

```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "description"

# Review generated migration file
# Edit if needed

# Apply migration
python run_migrations.py
```

---

## 🚢 Deployment

For production deployment, see:
- `docs/CI_CD_SETUP.md` - CI/CD configuration
- Update environment variables for production
- Use production database
- Enable HTTPS
- Set `DEBUG=false`

---

## 📝 Project Structure

```
wellness_way/
├── backend/           # FastAPI backend
│   ├── app/          # Application code
│   ├── alembic/      # Database migrations
│   ├── tests/        # Unit tests
│   └── .env          # Environment variables (create this)
├── frontend/         # React frontend
│   ├── src/          # Source code
│   ├── public/       # Static files
│   └── .env          # Environment variables (create this)
├── docs/             # Documentation
└── README.md         # Project overview
```

---

**You're all set! Happy coding!** 🎉

For detailed documentation, see `docs/` folder.
