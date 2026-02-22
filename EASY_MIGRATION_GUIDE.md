# Easy Migration Guide (No pg_dump Required!)

## Step-by-Step Migration Using Python

### Step 1: Get Your Supabase Connection String

1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to **Settings** → **Database**
4. Find **Connection String** section
5. Select **URI** tab
6. Copy the connection string

It looks like:
```
postgresql://postgres.abcdefghijklmnop:your-password@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### Step 2: Update the Migration Script

Open `backend/migrate_to_supabase.py` and update line 11:

**Change this**:
```python
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL", "postgresql+psycopg://postgres.YOUR-REF:YOUR-PASS@aws-0-REGION.pooler.supabase.com:6543/postgres")
```

**To this** (add `+psycopg` after `postgresql`):
```python
SUPABASE_DB_URL = "postgresql+psycopg://postgres.abcdefghijklmnop:your-password@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
```

### Step 3: Create Tables in Supabase

First, update `backend/.env` with your Supabase connection:

```env
DATABASE_URL=postgresql+psycopg://postgres.abcdefghijklmnop:your-password@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

Then run migrations:

```powershell
cd backend
python run_migrations.py
```

This creates all tables in Supabase.

### Step 4: Run the Migration Script

```powershell
cd backend
python migrate_to_supabase.py
```

You'll see:
```
============================================================
🚀 WellnessWay Data Migration: Local → Supabase
============================================================

📍 Source: localhost:5432/wellnessway_db
📍 Target: aws-0-us-east-1.pooler.supabase.com:6543/postgres

⚠️  This will copy data to Supabase. Continue? (yes/no):
```

Type `yes` and press Enter.

### Step 5: Watch the Migration

The script will:
1. Connect to both databases
2. Migrate each table in order:
   - users
   - health_context_documents
   - diet_plans
3. Show progress for each table
4. Verify data counts match

Example output:
```
📦 Migrating table: users
   Found 5 rows
   Progress: 5/5 rows...
   ✅ Migrated 5 rows (0 errors)

📦 Migrating table: health_context_documents
   Found 3 rows
   Progress: 3/3 rows...
   ✅ Migrated 3 rows (0 errors)

📦 Migrating table: diet_plans
   Found 10 rows
   Progress: 10/10 rows...
   ✅ Migrated 10 rows (0 errors)

🔍 Verifying migration...
   ✅ users: Local=5, Supabase=5
   ✅ health_context_documents: Local=3, Supabase=3
   ✅ diet_plans: Local=10, Supabase=10

============================================================
✅ Migration completed successfully!
   Total records migrated: 18
============================================================
```

### Step 6: Test Your Backend

```powershell
cd backend
python start_backend.py
```

You should see:
```
🚀 Starting WellnessWay Backend...
Database URL: postgresql+psycopg://postgres.abcdefghijklmnop:***@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### Step 7: Test the App

1. Open http://localhost:8000/health
2. Should return: `{"status": "healthy"}`
3. Test login with your existing user
4. Try generating a diet plan

---

## Troubleshooting

### Error: "Connection refused" or "Can't connect to local database"

**Problem**: Local PostgreSQL not running

**Solution**: Start your local PostgreSQL:
```powershell
# If using Docker
docker-compose up -d database

# If using Windows service
# Start PostgreSQL service from Services app
```

### Error: "Can't connect to Supabase"

**Problem**: Wrong connection string or password

**Solution**:
1. Double-check your Supabase connection string
2. Make sure you added `+psycopg` after `postgresql`
3. Verify your password is correct
4. Try resetting password in Supabase Dashboard

### Error: "relation does not exist"

**Problem**: Tables not created in Supabase

**Solution**:
```powershell
cd backend
python run_migrations.py
```

### Error: "duplicate key value violates unique constraint"

**Problem**: Data already exists in Supabase

**Solution**: The script uses `ON CONFLICT DO NOTHING`, so this shouldn't happen. If it does, you can clear Supabase tables:

```python
# Create a file: backend/clear_supabase.py
from sqlalchemy import create_engine, text

SUPABASE_DB_URL = "postgresql+psycopg://postgres.YOUR-REF:YOUR-PASS@..."
engine = create_engine(SUPABASE_DB_URL)

with engine.connect() as conn:
    conn.execute(text("TRUNCATE users, health_context_documents, diet_plans CASCADE"))
    conn.commit()
    print("✅ Cleared all tables")
```

Then run: `python clear_supabase.py`

---

## Alternative: Manual Migration (If Script Fails)

If the Python script doesn't work, you can migrate manually using a database GUI tool:

### Option A: Using DBeaver (Free)

1. Download DBeaver: https://dbeaver.io/download/
2. Connect to local database:
   - Host: localhost
   - Port: 5432
   - Database: wellnessway_db
   - Username: wellnessway
   - Password: password
3. Connect to Supabase:
   - Use your Supabase connection string
4. Right-click local database → Tools → Export Data
5. Select tables to export
6. Choose format: SQL INSERT statements
7. Save file
8. Open Supabase connection
9. Execute the SQL file

### Option B: Using pgAdmin (Free)

1. Download pgAdmin: https://www.pgadmin.org/download/
2. Add local server
3. Add Supabase server
4. Right-click local database → Backup
5. Choose "Plain" format
6. Save file
7. Right-click Supabase database → Restore
8. Select the backup file

---

## Verification Checklist

After migration, verify:

- [ ] All tables exist in Supabase
  ```powershell
  # Check in Supabase Dashboard → Table Editor
  ```

- [ ] Record counts match
  ```sql
  SELECT COUNT(*) FROM users;
  SELECT COUNT(*) FROM health_context_documents;
  SELECT COUNT(*) FROM diet_plans;
  ```

- [ ] Backend connects to Supabase
  ```powershell
  python start_backend.py
  # Check logs for Supabase URL
  ```

- [ ] Can login with existing user

- [ ] Can view existing diet plans

- [ ] Can generate new diet plans

---

## Quick Reference

### Local Database Connection
```
Host: localhost
Port: 5432
Database: wellnessway_db
Username: wellnessway
Password: password
```

### Supabase Connection Format
```
postgresql+psycopg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

### Important Files
- `backend/.env` - Update with Supabase connection
- `backend/migrate_to_supabase.py` - Migration script
- `backend/run_migrations.py` - Create tables in Supabase

---

## Need Help?

If you encounter issues:

1. Check that local PostgreSQL is running
2. Verify Supabase connection string is correct
3. Make sure you ran `python run_migrations.py` first
4. Check the error message carefully
5. Try the manual migration methods above

**The Python script is the easiest method - no pg_dump needed!**
