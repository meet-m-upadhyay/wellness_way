# WellnessWay Supabase Migration - Quick Start Guide

## 🚀 Choose Your Setup

### Option A: Supabase Cloud (Recommended ⭐)
**Best for:** Multi-device development, team collaboration, cloud-hosted data
- No Docker required
- Work from any machine
- Cloud backups included
- Free tier available

### Option B: Docker Local (Existing approach)
**Best for:** Single machine, offline development, full local control
- Everything local
- No Docker knowledge needed (just use docker-compose)
- Perfect for initial development

---

## ⚡ Quick Start - Supabase (5 minutes)

### 1. Get Supabase Credentials (2 min)

Visit [supabase.com](https://supabase.com):
1. Sign up for free account
2. Create new project
3. Go to **Settings → Database**
4. Copy your connection details:
   - Password (created during setup)
   - Host: `db.[PROJECT_REF].supabase.co`

### 2. Configure Environment (1 min)

```bash
cd wellnessway
cp .env.supabase.example .env.supabase
```

Edit `.env.supabase` and add your Supabase password:
```
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres
OPENAI_API_KEY=your_openai_key_here
```

Then activate this configuration:
```bash
cp .env.supabase .env
```

### 3. Verify Connection (1 min)

```bash
cd backend
python setup_supabase.py --test-connection
```

Expected output: `✅ Database connection successful!`

### 4. Create Database Schema (1 min)

```bash
cd backend
python -m alembic upgrade head
```

### 5. Start Application

**Terminal 1 - Backend:**
```bash
cd backend
python start_backend.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install  # first time only
npm start
```

**Open:** http://localhost:3000

---

## 🐳 Quick Start - Docker Local (5 minutes)

### 1. Configure Environment

```bash
cd wellnessway
cp .env.example .env
# Add your OpenAI API key to .env
```

### 2. Start Database

```bash
docker-compose up -d database
```

### 3. Create Database Schema

```bash
cd backend
python -m alembic upgrade head
```

### 4. Start All Services

```bash
docker-compose up -d
```

### 5. Access Application

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🔄 Switching Between Setups

### Switch to Supabase (from Docker)
```bash
# 1. Get Supabase credentials
cp .env.supabase.example .env.supabase
# Edit with your credentials
cp .env.supabase .env

# 2. Verify and migrate
cd backend
python setup_supabase.py --test-connection
python -m alembic upgrade head

# 3. Stop Docker and start backend
docker-compose down
python start_backend.py
```

### Switch to Docker (from Supabase)
```bash
# 1. Update .env to use local database
# Edit .env: DATABASE_URL=postgresql+psycopg://wellnessway:password@localhost:5432/wellnessway_db

# 2. Start Docker
docker-compose up -d

# 3. Verify schema
cd backend
python -m alembic upgrade head
```

---

## 🧪 Verify Setup

**Test connection:**
```bash
cd backend
python setup_supabase.py --test-connection
```

**Check database tables:**
```bash
python setup_supabase.py --verify-tables
```

**Run test queries:**
```bash
python setup_supabase.py --test-query
```

**Complete diagnostics:**
```bash
python setup_supabase.py --diagnose
```

---

## 💡 Common Issues

### Connection Failed
```bash
# Check your connection string in .env
# Verify Supabase project is active
# Test connection:
cd backend
python setup_supabase.py --test-connection
```

### No Tables Found
```bash
# Run migrations:
cd backend
python -m alembic upgrade head

# Verify:
python setup_supabase.py --verify-tables
```

### API Won't Start
```bash
# Check if port 8000 is free:
netstat -ano | findstr :8000  # Windows
lsof -i :8000                # Mac/Linux

# Check backend logs:
tail -f backend/logs/app.log
```

### Frontend Won't Load
```bash
# Rebuild frontend:
cd frontend
rm -rf node_modules
npm install
npm start
```

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `.env` | Active configuration (don't commit) |
| `.env.supabase` | Supabase template (don't commit) |
| `.env.example` | Docker template (committed) |
| `.env.supabase.example` | Supabase example (committed) |
| `docs/SUPABASE_MIGRATION.md` | Detailed migration guide |
| `backend/setup_supabase.py` | Setup verification script |

---

## 🔐 Security Notes

- ✅ Never commit `.env` files
- ✅ Use strong passwords for Supabase
- ✅ Store credentials securely
- ✅ Keep `.env.example` files for reference
- ✅ Each team member gets their own `.env` (not shared via git)

---

## 📚 Detailed Documentation

- **Full Supabase Guide**: See [docs/SUPABASE_MIGRATION.md](docs/SUPABASE_MIGRATION.md)
- **Project README**: See [README.md](README.md)
- **Implementation Details**: See [SUPABASE_MIGRATION_IMPLEMENTATION.md](SUPABASE_MIGRATION_IMPLEMENTATION.md)

---

## 👥 Multi-Device Setup

**On Laptop 1:**
```bash
git clone <repo>
cp .env.supabase.example .env.supabase
# Add same Supabase credentials
cp .env.supabase .env
cd backend && python setup_supabase.py --test-connection
```

**On Laptop 2:**
```bash
git clone <repo>
cp .env.supabase.example .env.supabase
# Add same Supabase credentials as Laptop 1
cp .env.supabase .env
cd backend && python setup_supabase.py --test-connection
```

Both machines now access the same cloud database! 🎉

---

## 🆘 Need Help?

1. Check [docs/SUPABASE_MIGRATION.md](docs/SUPABASE_MIGRATION.md) Troubleshooting section
2. Run: `python setup_supabase.py -v --diagnose`
3. Check Supabase dashboard for alerts
4. Review application logs: `backend/logs/app.log`

---

**Ready to get started? Pick your setup above and follow the steps!** ✨
