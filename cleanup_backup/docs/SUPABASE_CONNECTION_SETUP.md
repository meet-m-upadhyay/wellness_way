# Connect Backend to Supabase Database

## Step 1: Get Supabase Connection String

1. Go to your Supabase project dashboard: https://supabase.com/dashboard
2. Select your project
3. Go to **Settings** → **Database**
4. Scroll to **Connection String** section
5. Select **URI** tab
6. Copy the connection string (it looks like this):

```
postgresql://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
```

**IMPORTANT**: Replace `[YOUR-PASSWORD]` with your actual database password!

## Step 2: Convert to SQLAlchemy Format

Supabase gives you a `postgresql://` URL, but we need `postgresql+psycopg://` for SQLAlchemy.

**Original Supabase URL**:
```
postgresql://postgres.abcdefgh:mypassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

**Convert to**:
```
postgresql+psycopg://postgres.abcdefgh:mypassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

Just add `+psycopg` after `postgresql`!

## Step 3: Update backend/.env File

Open `backend/.env` and replace the DATABASE_URL:

```env
# OLD (local database)
DATABASE_URL=postgresql+psycopg://wellnessway:password@localhost:5432/wellnessway_db

# NEW (Supabase)
DATABASE_URL=postgresql+psycopg://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
```

**Full example**:
```env
DATABASE_URL=postgresql+psycopg://postgres.abcdefgh:mypassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres
REDIS_URL=redis://localhost:6379/0
ENVIRONMENT=development
DEBUG=true
AI_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=dev-secret-key-change-in-production-12345

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
JWT_SECRET_KEY=your_jwt_secret_key_here
```

## Step 4: Update start_backend.py

Open `backend/start_backend.py` and update the DATABASE_URL:

```python
def start_backend():
    # Set environment variables before importing anything
    os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    os.environ["ENVIRONMENT"] = "development"
    os.environ["DEBUG"] = "true"
    
    # ... rest of the code
```

## Step 5: Run Database Migrations

Since this is a fresh Supabase database, you need to create all tables:

```powershell
cd backend

# Run migrations to create tables
python run_migrations.py
```

This will create all the necessary tables in your Supabase database.

## Step 6: Start Backend

```powershell
cd backend
python start_backend.py
```

You should see:
```
🚀 Starting WellnessWay Backend...
Database URL: postgresql+psycopg://postgres.abcdefgh:***@aws-0-us-east-1.pooler.supabase.com:6543/postgres
Redis URL: redis://localhost:6379/0
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 7: Verify Connection

Test the connection:

```powershell
# In another terminal
curl http://localhost:8000/health
```

Should return:
```json
{"status": "healthy"}
```

## Troubleshooting

### Error: "connection refused"

**Problem**: Can't connect to Supabase

**Solutions**:
1. Check your password is correct
2. Make sure you're using the **pooler** connection string (port 6543)
3. Check your IP is allowed in Supabase (Settings → Database → Connection pooling)

### Error: "SSL required"

**Problem**: Supabase requires SSL connections

**Solution**: Add `?sslmode=require` to the end of your connection string:
```
postgresql+psycopg://postgres.abcdefgh:mypassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require
```

### Error: "relation does not exist"

**Problem**: Tables haven't been created yet

**Solution**: Run migrations:
```powershell
cd backend
python run_migrations.py
```

### Error: "password authentication failed"

**Problem**: Wrong password

**Solution**: 
1. Go to Supabase Dashboard → Settings → Database
2. Click "Reset Database Password"
3. Copy the new password
4. Update your .env file

## Connection Pooling

Supabase provides two connection modes:

### 1. Direct Connection (Port 5432)
```
postgresql+psycopg://postgres.[ref]:[pass]@db.[ref].supabase.co:5432/postgres
```
- Use for: Migrations, admin tasks
- Limit: 60 connections max

### 2. Pooler Connection (Port 6543) - RECOMMENDED
```
postgresql+psycopg://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:6543/postgres
```
- Use for: Application connections
- Limit: Unlimited (pooled)
- Better for production

**Use the Pooler connection (port 6543) for your backend!**

## Environment Variables Summary

After setup, your `backend/.env` should have:

```env
# Supabase Database (UPDATED)
DATABASE_URL=postgresql+psycopg://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:6543/postgres

# Local Redis (keep as is)
REDIS_URL=redis://localhost:6379/0

# Environment
ENVIRONMENT=development
DEBUG=true

# AI Provider
AI_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here

# Security
SECRET_KEY=dev-secret-key-change-in-production-12345
JWT_SECRET_KEY=your_jwt_secret_key_here

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

## Next Steps

1. ✅ Update `backend/.env` with Supabase connection string
2. ✅ Update `backend/start_backend.py` with Supabase connection string
3. ✅ Run migrations: `python run_migrations.py`
4. ✅ Start backend: `python start_backend.py`
5. ✅ Test connection: `curl http://localhost:8000/health`
6. ✅ Create a user and test the app!

## Benefits of Using Supabase

- ✅ No need to run local PostgreSQL
- ✅ Automatic backups
- ✅ Built-in authentication (can integrate later)
- ✅ Real-time subscriptions (can use later)
- ✅ Free tier: 500MB database, 2GB bandwidth
- ✅ Accessible from anywhere (not just localhost)

---

**You're now using Supabase as your production database!** 🎉
