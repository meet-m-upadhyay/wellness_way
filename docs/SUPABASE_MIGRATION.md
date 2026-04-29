# Supabase Cloud Database Migration Guide

This guide provides step-by-step instructions to migrate WellnessWay Diet Planner from local Docker PostgreSQL to Supabase cloud database. This enables seamless multi-device development without requiring Docker.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Supabase Project Setup](#supabase-project-setup)
3. [Environment Configuration](#environment-configuration)
4. [Database Migration](#database-migration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Switching Between Local and Cloud](#switching-between-local-and-cloud)

---

## Prerequisites

- Supabase account (free tier available at [supabase.com](https://supabase.com))
- Python 3.11+ (backend environment)
- Git and version control
- Basic understanding of environment variables

---

## Supabase Project Setup

### Step 1: Create a Supabase Account

1. Visit [supabase.com](https://supabase.com)
2. Sign up with your email, GitHub, or Google account
3. Verify your email address

### Step 2: Create a New Project

1. Click **"New Project"** in the Supabase dashboard
2. Configure project details:
   - **Name**: `wellnessway` (or your preferred name)
   - **Region**: Choose closest to your location (e.g., `us-east-1` for North America)
   - **Database Password**: Create a strong password (you'll need this)
   - **Pricing Plan**: Start with the free tier

3. Wait for the project to initialize (usually 1-2 minutes)

### Step 3: Extract Connection Credentials

Once your project is ready:

1. Go to **Settings → Database** in your Supabase project
2. Locate the connection string section
3. Note the following information:
   - **Host**: `db.[PROJECT_REF].supabase.co`
   - **Port**: `5432`
   - **Database**: `postgres`
   - **User**: `postgres`
   - **Password**: The password you created during project setup
   - **Project Reference** (from the connection URL): The alphanumeric code in your host

### Step 4: Get Your API Keys (Optional - for Frontend)

1. Go to **Settings → API** in your Supabase project
2. Note your:
   - **Project URL**: Used for Supabase client libraries
   - **Anon Key**: Used for public operations (frontend)
   - **Service Role Key**: Used for private operations (backend)

---

## Environment Configuration

### Step 1: Create .env.supabase File

Create a new `.env.supabase` file in your project root with your Supabase credentials:

```bash
cp .env.supabase.example .env.supabase
```

### Step 2: Update Connection String

Edit `.env.supabase` and replace the placeholder values:

```dotenv
# Supabase Configuration
DATABASE_URL=postgresql+psycopg://postgres:[YOUR_PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres

# Example:
# DATABASE_URL=postgresql+psycopg://postgres:MySecurePass123@db.abcdef123456.supabase.co:5432/postgres
```

### Step 3: Configure for Development

For local development, create or update your root `.env` file:

```bash
# Option A: Use Supabase (Recommended for multi-device development)
cp .env.supabase .env

# Option B: Use local Docker (Standalone development)
# Keep existing .env with: DATABASE_URL=postgresql+psycopg://wellnessway:password@localhost:5432/wellnessway_db
```

### Important Security Notes

- ⚠️ **Never commit `.env` files to git**
- ⚠️ **Never share your database password**
- ✅ Use `.env.supabase.example` as a template in the repository
- ✅ Keep actual credentials in local `.env` files only
- ✅ Add `.env` to `.gitignore` (already configured)

---

## Database Migration

### Step 1: Verify Connection

Run the setup automation script to verify your Supabase connection:

```bash
cd backend

# Windows PowerShell:
.\venv\Scripts\python.exe setup_supabase.py --test-connection

# macOS/Linux:
python setup_supabase.py --test-connection
```

Expected output:
```
✓ Database connection successful
  Host: db.xxxxx.supabase.co
  Database: postgres
  Tables: 0 (empty database)
```

### Step 2: Run Alembic Migrations

Run all database migrations to create your schema:

```bash
cd backend

# Windows PowerShell:
.\venv\Scripts\python.exe -m alembic upgrade head

# macOS/Linux:
python -m alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.migration] Running upgrade  -> 001_initial_migration, 1001_initial_migration
...
INFO  [alembic.migration] Running upgrade xxxxx -> yyyyy, zzz_description
```

### Step 3: Verify Schema Creation

Use the setup script to verify all tables were created:

```bash
cd backend

# Windows PowerShell:
.\venv\Scripts\python.exe setup_supabase.py --verify-tables

# macOS/Linux:
python setup_supabase.py --verify-tables
```

Expected output:
```
✓ Schema verification successful
  Tables found: 12
  - users (15 rows)
  - diet_plans (8 rows)
  - meals (24 rows)
  - ingredients (342 rows)
  ... etc
```

---

## Verification

### Step 1: Test Database Connection

```bash
cd backend
python setup_supabase.py --test-connection
```

### Step 2: Verify All Tables

```bash
cd backend
python setup_supabase.py --verify-tables
```

### Step 3: Run Sample Query

```bash
cd backend
python setup_supabase.py --test-query
```

### Step 4: Start Backend and Frontend

```bash
# Terminal 1: Backend
cd backend
python start_backend.py

# Terminal 2: Frontend (if running locally)
cd frontend
npm start
```

### Step 5: Test Application

- Navigate to `http://localhost:3000`
- Create a new account and test functionality
- Verify diet plans can be created and viewed
- Check that all API endpoints work correctly

---

## Troubleshooting

### Connection Issues

**Problem**: `psycopg.OperationalError: connection failed`

**Solutions**:
1. Verify DATABASE_URL format: `postgresql+psycopg://user:password@host:5432/database`
2. Check password doesn't contain special characters that need escaping
3. Ensure Supabase project is active (check dashboard)
4. Verify IP is not blocked (Supabase allows all IPs by default)
5. Test connection: `python setup_supabase.py --test-connection`

**Problem**: `Connection timeout (60 seconds)`

**Solutions**:
1. Check your internet connection
2. Verify the Supabase host is correct
3. Try a different region if available
4. Contact Supabase support if the region is down

### Authentication Issues

**Problem**: `FATAL: password authentication failed`

**Solutions**:
1. Double-check your password in the DATABASE_URL
2. If special characters, try URL-encoding them
3. Reset password in Supabase dashboard: Settings → Database → Reset Password
4. Update your `.env` with the new password

### Migration Issues

**Problem**: `RuntimeError: Can't locate revision identified by` error during migration

**Solutions**:
1. Ensure you're in the `backend/` directory
2. Verify alembic.ini exists in the current directory
3. Check for corrupted migration files
4. Try rolling back: `alembic downgrade -1` then `alembic upgrade head`

**Problem**: `Column "..." does not exist` after migrations

**Solutions**:
1. Clear existing schema in Supabase:
   ```sql
   DROP SCHEMA public CASCADE;
   CREATE SCHEMA public;
   ```
   (Use Supabase SQL editor: https://app.supabase.com/project/YOUR_PROJECT_REF/sql)
2. Re-run migrations: `alembic upgrade head`

### Performance Issues

**Problem**: Slow queries or timeout issues

**Solutions**:
1. Check connection pooling settings in `.env`
2. Upgrade Supabase plan if hitting limits
3. Monitor query performance in Supabase dashboard
4. Use indexes for frequently queried columns

---

## Switching Between Local and Cloud

### Switch to Supabase (Recommended)

```bash
# Copy Supabase configuration
cp .env.supabase .env

# Verify connection
cd backend
python setup_supabase.py --test-connection

# Start application
python start_backend.py
```

### Switch Back to Local Docker

```bash
# Edit .env to use local database
# DATABASE_URL=postgresql+psycopg://wellnessway:password@localhost:5432/wellnessway_db

# Start Docker containers
docker-compose up -d

# Run migrations (if needed)
cd backend
python -m alembic upgrade head

# Start application
python start_backend.py
```

### Important Notes

- Both configurations use the same database schema and Alembic migrations
- No code changes required to switch between local and cloud
- Always verify connection before starting the application
- Keep both `.env` and `.env.supabase` updated for team collaboration

---

## Advanced Topics

### Connection Pooling

Supabase works best with connection pooling. Current settings in `.env`:

```dotenv
DATABASE_POOL_SIZE=5           # Number of connections to maintain
DATABASE_MAX_OVERFLOW=10       # Additional connections when needed
DATABASE_POOL_TIMEOUT=30       # Seconds to wait for a connection
DATABASE_POOL_RECYCLE=3600     # Recycle connections after 1 hour
```

For Supabase, these defaults are optimized. Only adjust if experiencing issues.

### IP Whitelisting

Supabase allows all IPs by default. To restrict access:

1. Go to **Settings → Network** in Supabase
2. Configure IP whitelist as needed
3. Note: This might break mobile/multi-device access

### SSL/TLS Connection

Supabase requires SSL connections. The `psycopg` driver handles this automatically. To force SSL:

```python
# In your connection string (already handled by setup script)
sslmode=require
```

### Backup and Recovery

Supabase provides automatic backups:
- Free tier: 7-day backup retention
- Paid tiers: 30-day retention

To restore from backup:
1. Go to **Settings → Backups** in Supabase
2. Click restore for your desired backup date
3. Your database will be restored (you'll need to re-run migrations if needed)

---

## Support and Resources

- **Supabase Documentation**: https://supabase.com/docs
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Alembic Migration Guide**: https://alembic.sqlalchemy.org/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/

---

## Quick Reference: Common Commands

```bash
# Test Supabase connection
cd backend && python setup_supabase.py --test-connection

# Verify database schema
cd backend && python setup_supabase.py --verify-tables

# Run all pending migrations
cd backend && python -m alembic upgrade head

# Create new migration
cd backend && python -m alembic revision --autogenerate -m "Description"

# Rollback last migration
cd backend && python -m alembic downgrade -1

# View migration history
cd backend && python -m alembic history

# Start backend server
cd backend && python start_backend.py

# View backend logs
tail -f backend/logs/app.log
```

---

## Feedback and Issues

If you encounter issues during migration:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review setup script output: `python setup_supabase.py -v`
3. Check Supabase dashboard for any alerts
4. Consult project documentation in `backend/DATABASE_SETUP.md`

