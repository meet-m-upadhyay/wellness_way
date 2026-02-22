# Migrate Data from Local PostgreSQL to Supabase

## Overview

This guide will help you migrate all your data (users, diet plans, health contexts, etc.) from your local PostgreSQL database to Supabase.

---

## Method 1: Using pg_dump and psql (Recommended)

This is the most reliable method for migrating PostgreSQL data.

### Step 1: Export Data from Local Database

```powershell
# Export all data from local database
pg_dump -h localhost -U wellnessway -d wellnessway_db --data-only --column-inserts -f local_data_backup.sql

# If you need password, it will prompt you
# Password: password
```

**Flags explained**:
- `--data-only`: Export only data, not schema (we'll use Alembic for schema)
- `--column-inserts`: Use INSERT statements with column names (more compatible)
- `-f local_data_backup.sql`: Output file name

### Step 2: Set Up Supabase Schema

First, create the schema in Supabase using Alembic:

```powershell
# Update backend/.env with Supabase connection string
# Then run migrations
cd backend
python run_migrations.py
```

This creates all tables in Supabase.

### Step 3: Import Data to Supabase

```powershell
# Import data to Supabase
psql "postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres" -f local_data_backup.sql
```

**Replace**:
- `[ref]`: Your Supabase project reference
- `[password]`: Your Supabase database password
- `[region]`: Your Supabase region (e.g., us-east-1)

---

## Method 2: Using Python Script (More Control)

This method gives you more control and can handle data transformations.

### Create Migration Script

Create `backend/migrate_to_supabase.py`:

```python
"""
Migrate data from local PostgreSQL to Supabase
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Source database (local)
LOCAL_DB_URL = "postgresql+psycopg://wellnessway:password@localhost:5432/wellnessway_db"

# Target database (Supabase)
SUPABASE_DB_URL = "postgresql+psycopg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres"

def migrate_data():
    """Migrate all data from local to Supabase"""
    
    print("🚀 Starting data migration...")
    
    # Create engines
    local_engine = create_engine(LOCAL_DB_URL)
    supabase_engine = create_engine(SUPABASE_DB_URL)
    
    # Create sessions
    LocalSession = sessionmaker(bind=local_engine)
    SupabaseSession = sessionmaker(bind=supabase_engine)
    
    local_session = LocalSession()
    supabase_session = SupabaseSession()
    
    try:
        # Get list of tables to migrate
        tables = [
            'users',
            'health_context_documents',
            'diet_plans',
            # Add other tables as needed
        ]
        
        for table in tables:
            print(f"\n📦 Migrating table: {table}")
            
            # Get data from local
            result = local_session.execute(text(f"SELECT * FROM {table}"))
            rows = result.fetchall()
            columns = result.keys()
            
            print(f"   Found {len(rows)} rows")
            
            if len(rows) == 0:
                print(f"   ⚠️  No data to migrate")
                continue
            
            # Insert into Supabase
            for i, row in enumerate(rows, 1):
                # Build INSERT statement
                col_names = ', '.join(columns)
                placeholders = ', '.join([f':{col}' for col in columns])
                
                insert_sql = f"""
                    INSERT INTO {table} ({col_names})
                    VALUES ({placeholders})
                    ON CONFLICT DO NOTHING
                """
                
                # Convert row to dict
                row_dict = dict(zip(columns, row))
                
                try:
                    supabase_session.execute(text(insert_sql), row_dict)
                    
                    if i % 10 == 0:
                        print(f"   Migrated {i}/{len(rows)} rows...")
                        
                except Exception as e:
                    print(f"   ❌ Error migrating row {i}: {e}")
                    continue
            
            # Commit after each table
            supabase_session.commit()
            print(f"   ✅ Completed {table}")
        
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        supabase_session.rollback()
        raise
        
    finally:
        local_session.close()
        supabase_session.close()

if __name__ == "__main__":
    migrate_data()
```

### Run the Migration Script

```powershell
cd backend
python migrate_to_supabase.py
```

---

## Method 3: Using Supabase CLI (Advanced)

### Install Supabase CLI

```powershell
# Using npm
npm install -g supabase

# Or using scoop (Windows)
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase
```

### Link to Your Project

```powershell
supabase link --project-ref your-project-ref
```

### Push Database

```powershell
# Export local schema
pg_dump -h localhost -U wellnessway -d wellnessway_db --schema-only -f schema.sql

# Push to Supabase
supabase db push
```

---

## Method 4: Manual Export/Import (Simple Tables)

For small amounts of data, you can use CSV export/import.

### Export from Local

```powershell
# Export users table
psql -h localhost -U wellnessway -d wellnessway_db -c "\COPY users TO 'users.csv' CSV HEADER"

# Export diet_plans table
psql -h localhost -U wellnessway -d wellnessway_db -c "\COPY diet_plans TO 'diet_plans.csv' CSV HEADER"

# Export health_context_documents table
psql -h localhost -U wellnessway -d wellnessway_db -c "\COPY health_context_documents TO 'health_context.csv' CSV HEADER"
```

### Import to Supabase

```powershell
# Import users
psql "postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres" -c "\COPY users FROM 'users.csv' CSV HEADER"

# Import diet_plans
psql "postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres" -c "\COPY diet_plans FROM 'diet_plans.csv' CSV HEADER"

# Import health_context_documents
psql "postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres" -c "\COPY health_context_documents FROM 'health_context.csv' CSV HEADER"
```

---

## Complete Migration Checklist

### Pre-Migration

- [ ] Backup local database
  ```powershell
  pg_dump -h localhost -U wellnessway -d wellnessway_db -f full_backup.sql
  ```

- [ ] Update `backend/.env` with Supabase connection string

- [ ] Run migrations on Supabase
  ```powershell
  cd backend
  python run_migrations.py
  ```

- [ ] Verify tables exist in Supabase
  ```powershell
  psql "postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres" -c "\dt"
  ```

### Migration

- [ ] Choose migration method (Method 1 or 2 recommended)

- [ ] Run migration

- [ ] Verify data count matches
  ```sql
  -- Local
  SELECT COUNT(*) FROM users;
  SELECT COUNT(*) FROM diet_plans;
  SELECT COUNT(*) FROM health_context_documents;
  
  -- Supabase (same queries)
  ```

### Post-Migration

- [ ] Test backend connection
  ```powershell
  cd backend
  python start_backend.py
  ```

- [ ] Test API endpoints
  ```powershell
  curl http://localhost:8000/health
  curl http://localhost:8000/api/v1/users
  ```

- [ ] Test frontend
  ```powershell
  cd frontend
  npm start
  ```

- [ ] Verify user login works

- [ ] Verify diet plan generation works

- [ ] Check data integrity (all relationships intact)

---

## Troubleshooting

### Error: "relation does not exist"

**Problem**: Tables not created in Supabase

**Solution**:
```powershell
cd backend
python run_migrations.py
```

### Error: "duplicate key value violates unique constraint"

**Problem**: Data already exists in Supabase

**Solution**: Use `ON CONFLICT DO NOTHING` in INSERT statements, or clear Supabase tables first:
```sql
TRUNCATE users, diet_plans, health_context_documents CASCADE;
```

### Error: "password authentication failed"

**Problem**: Wrong Supabase password

**Solution**: Reset password in Supabase Dashboard → Settings → Database

### Error: "connection timeout"

**Problem**: Can't reach Supabase

**Solution**: 
1. Check internet connection
2. Verify connection string is correct
3. Check Supabase project is active

### Error: "foreign key constraint violation"

**Problem**: Trying to insert child records before parent records

**Solution**: Migrate tables in order:
1. `users` (no dependencies)
2. `health_context_documents` (depends on users)
3. `diet_plans` (depends on users and health_context_documents)

---

## Verification Queries

After migration, run these queries on both databases to verify:

```sql
-- Count records
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'health_context_documents', COUNT(*) FROM health_context_documents
UNION ALL
SELECT 'diet_plans', COUNT(*) FROM diet_plans;

-- Check latest records
SELECT id, email, created_at FROM users ORDER BY created_at DESC LIMIT 5;

-- Check relationships
SELECT 
    u.email,
    COUNT(DISTINCT hcd.id) as health_contexts,
    COUNT(DISTINCT dp.id) as diet_plans
FROM users u
LEFT JOIN health_context_documents hcd ON u.id = hcd.user_id
LEFT JOIN diet_plans dp ON u.id = dp.user_id
GROUP BY u.email;
```

---

## Rollback Plan

If migration fails, you can rollback:

### 1. Keep Local Database Running

Don't delete your local database until you've verified Supabase works!

### 2. Switch Back to Local

Update `backend/.env`:
```env
DATABASE_URL=postgresql+psycopg://wellnessway:password@localhost:5432/wellnessway_db
```

### 3. Restart Backend

```powershell
cd backend
python start_backend.py
```

---

## Best Practices

1. **Test First**: Migrate to a test Supabase project first
2. **Backup**: Always backup before migration
3. **Verify**: Check data counts and relationships after migration
4. **Incremental**: Migrate one table at a time if issues occur
5. **Keep Local**: Don't delete local database until Supabase is verified working

---

## Quick Start (Recommended Path)

```powershell
# 1. Backup local database
pg_dump -h localhost -U wellnessway -d wellnessway_db -f backup_$(date +%Y%m%d).sql

# 2. Update backend/.env with Supabase connection

# 3. Run migrations on Supabase
cd backend
python run_migrations.py

# 4. Export data from local
pg_dump -h localhost -U wellnessway -d wellnessway_db --data-only --column-inserts -f data_export.sql

# 5. Import to Supabase
psql "postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres" -f data_export.sql

# 6. Verify
python start_backend.py
# Test the app!
```

---

**You're ready to migrate!** Choose the method that works best for you. Method 1 (pg_dump) is recommended for most cases.
