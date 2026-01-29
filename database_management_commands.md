# Database Management Commands

## Connect to PostgreSQL Database
```bash
# Using psql command line
psql -h localhost -p 5432 -U wellnessway -d wellnessway_db

# Or using connection string
psql "postgresql://wellnessway:password@localhost:5432/wellnessway_db"
```

## Common Database Operations

### View all tables
```sql
\dt
```

### Check table sizes
```sql
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public';
```

### Count records in each table
```sql
SELECT 
    'users' as table_name, 
    COUNT(*) as record_count 
FROM users
UNION ALL
SELECT 
    'health_context_documents' as table_name, 
    COUNT(*) as record_count 
FROM health_context_documents
UNION ALL
SELECT 
    'diet_plans' as table_name, 
    COUNT(*) as record_count 
FROM diet_plans
UNION ALL
SELECT 
    'health_goals' as table_name, 
    COUNT(*) as record_count 
FROM health_goals
UNION ALL
SELECT 
    'diet_preferences' as table_name, 
    COUNT(*) as record_count 
FROM diet_preferences;
```

### Delete old records (keep only latest 6)
```sql
-- For users table
DELETE FROM users 
WHERE id NOT IN (
    SELECT id FROM (
        SELECT id 
        FROM users 
        ORDER BY created_at DESC 
        LIMIT 6
    ) AS subquery
);

-- For diet_plans table
DELETE FROM diet_plans 
WHERE id NOT IN (
    SELECT id FROM (
        SELECT id 
        FROM diet_plans 
        ORDER BY created_at DESC 
        LIMIT 6
    ) AS subquery
);
```

### Clear all data from specific table
```sql
-- Clear all diet plans
DELETE FROM diet_plans;

-- Clear all health context documents
DELETE FROM health_context_documents;

-- Clear all users (this will cascade to related tables)
DELETE FROM users;
```

### Reset database to clean state
```sql
-- Delete in order to respect foreign key constraints
DELETE FROM diet_plans;
DELETE FROM health_context_documents;
DELETE FROM diet_preferences;
DELETE FROM health_goals;
DELETE FROM users;
```

## Python Database Management

### Using the seed script
```bash
# Clear and reseed database
python scripts/seed_database.py --clear

# Just add sample data (don't clear existing)
python scripts/seed_database.py
```

### Direct database connection in Python
```python
from sqlalchemy import create_engine, text
from app.core.config import settings

# Create engine
engine = create_engine(settings.database.url)

# Execute raw SQL
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM users"))
    print(f"User count: {result.scalar()}")
```

## Delete Specific Entries

### Method 1: Using SQL Commands

#### Connect to the database first:
```bash
psql "postgresql://wellnessway:password@localhost:5432/wellnessway_db"
```

#### Find the entry you want to delete:
```sql
-- Find users by name
SELECT id, name, age, created_at FROM users WHERE name LIKE '%Alice%';

-- Find diet plans by user
SELECT id, plan_type, start_date, created_at FROM diet_plans WHERE user_id = 'USER_UUID_HERE';

-- Find health context documents
SELECT id, user_id, version, created_at FROM health_context_documents WHERE user_id = 'USER_UUID_HERE';
```

#### Delete specific entries by ID:
```sql
-- Delete a specific user (this will cascade to related records)
DELETE FROM users WHERE id = 'USER_UUID_HERE';

-- Delete a specific diet plan
DELETE FROM diet_plans WHERE id = 'PLAN_UUID_HERE';

-- Delete a specific health context document
DELETE FROM health_context_documents WHERE id = 'HCD_UUID_HERE';

-- Delete by name (if you know the name)
DELETE FROM users WHERE name = 'Alice Johnson';

-- Delete by date range
DELETE FROM diet_plans WHERE created_at < '2024-01-01';
```

#### Delete with conditions:
```sql
-- Delete all diet plans for a specific user
DELETE FROM diet_plans WHERE user_id = 'USER_UUID_HERE';

-- Delete users created before a certain date
DELETE FROM users WHERE created_at < '2024-01-15';

-- Delete by multiple conditions
DELETE FROM users WHERE age > 40 AND activity_level = 'sedentary';
```

### Method 2: Using API Endpoints

#### Delete a diet plan via API:
```bash
# Get the plan ID first
curl -X GET "http://localhost:8000/api/v1/diet-plans" -H "X-User-Id: USER_UUID"

# Delete the specific plan
curl -X DELETE "http://localhost:8000/api/v1/diet-plans/PLAN_UUID" -H "X-User-Id: USER_UUID"
```

#### Delete a user profile via API:
```bash
# Delete user profile (this will cascade to related data)
curl -X DELETE "http://localhost:8000/api/v1/users/profile/USER_UUID"
```

### Method 3: Using PowerShell/REST API

#### Find and delete a specific diet plan:
```powershell
# Get user's diet plans
$plans = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/diet-plans" -Headers @{"X-User-Id"="USER_UUID"}

# Delete a specific plan
$planId = "PLAN_UUID_TO_DELETE"
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/diet-plans/$planId" -Method DELETE -Headers @{"X-User-Id"="USER_UUID"}
```

#### Delete a user profile:
```powershell
$userId = "USER_UUID_TO_DELETE"
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/profile/$userId" -Method DELETE
```