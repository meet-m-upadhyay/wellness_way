"""
Migrate data from local PostgreSQL to Supabase
No pg_dump required - pure Python!
"""
import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Source database (local)
LOCAL_DB_URL = "postgresql+psycopg://wellnessway:password@localhost:5432/wellnessway_db"

# Target database (Supabase)
SUPABASE_DB_URL = "postgresql://postgres.ytlfneijevuhcwbqqkck:UlhiSGdNxvHm5s06@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"

def get_table_order():
    """Return tables in dependency order (parents before children)"""
    return [
        'users',
        'health_context_documents',
        'diet_plans',
    ]

def migrate_table(table_name, local_session, supabase_session):
    """Migrate a single table"""
    print(f"\n📦 Migrating table: {table_name}")
    
    try:
        # Get data from local
        result = local_session.execute(text(f"SELECT * FROM {table_name}"))
        rows = result.fetchall()
        columns = result.keys()
        
        print(f"   Found {len(rows)} rows")
        
        if len(rows) == 0:
            print(f"   ⚠️  No data to migrate")
            return 0
        
        # Insert into Supabase
        migrated_count = 0
        error_count = 0
        
        for i, row in enumerate(rows, 1):
            # Build INSERT statement
            col_names = ', '.join(columns)
            placeholders = ', '.join([f':{col}' for col in columns])
            
            insert_sql = f"""
                INSERT INTO {table_name} ({col_names})
                VALUES ({placeholders})
                ON CONFLICT DO NOTHING
            """
            
            # Convert row to dict
            row_dict = dict(zip(columns, row))
            
            try:
                supabase_session.execute(text(insert_sql), row_dict)
                migrated_count += 1
                
                if i % 10 == 0:
                    print(f"   Progress: {i}/{len(rows)} rows...")
                    
            except Exception as e:
                error_count += 1
                print(f"   ⚠️  Error on row {i}: {str(e)[:100]}")
                continue
        
        # Commit after each table
        supabase_session.commit()
        print(f"   ✅ Migrated {migrated_count} rows ({error_count} errors)")
        return migrated_count
        
    except Exception as e:
        print(f"   ❌ Failed to migrate {table_name}: {e}")
        return 0

def verify_migration(local_session, supabase_session):
    """Verify data counts match"""
    print("\n🔍 Verifying migration...")
    
    tables = get_table_order()
    all_match = True
    
    for table in tables:
        try:
            local_count = local_session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            supabase_count = supabase_session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            
            match = "✅" if local_count == supabase_count else "❌"
            print(f"   {match} {table}: Local={local_count}, Supabase={supabase_count}")
            
            if local_count != supabase_count:
                all_match = False
                
        except Exception as e:
            print(f"   ⚠️  Could not verify {table}: {e}")
    
    return all_match

def migrate_data():
    """Main migration function"""
    
    print("=" * 60)
    print("🚀 WellnessWay Data Migration: Local → Supabase")
    print("=" * 60)
    
    # Check if Supabase URL is configured
    if "YOUR-REF" in SUPABASE_DB_URL or "YOUR-PASS" in SUPABASE_DB_URL:
        print("\n❌ ERROR: Please update SUPABASE_DB_URL in this script!")
        print("   Set your Supabase connection string at the top of this file.")
        return
    
    print(f"\n📍 Source: {LOCAL_DB_URL.split('@')[1]}")
    print(f"📍 Target: {SUPABASE_DB_URL.split('@')[1]}")
    
    # Confirm
    response = input("\n⚠️  This will copy data to Supabase. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Migration cancelled")
        return
    
    # Create engines
    print("\n🔌 Connecting to databases...")
    try:
        local_engine = create_engine(LOCAL_DB_URL)
        supabase_engine = create_engine(SUPABASE_DB_URL)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Create sessions
    LocalSession = sessionmaker(bind=local_engine)
    SupabaseSession = sessionmaker(bind=supabase_engine)
    
    local_session = LocalSession()
    supabase_session = SupabaseSession()
    
    try:
        # Test connections
        local_session.execute(text("SELECT 1"))
        supabase_session.execute(text("SELECT 1"))
        print("✅ Connected to both databases")
        
        # Migrate tables in order
        tables = get_table_order()
        total_migrated = 0
        
        for table in tables:
            count = migrate_table(table, local_session, supabase_session)
            total_migrated += count
        
        # Verify
        print("\n" + "=" * 60)
        all_match = verify_migration(local_session, supabase_session)
        
        print("\n" + "=" * 60)
        if all_match:
            print("✅ Migration completed successfully!")
            print(f"   Total records migrated: {total_migrated}")
        else:
            print("⚠️  Migration completed with mismatches")
            print("   Please review the verification results above")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        supabase_session.rollback()
        raise
        
    finally:
        local_session.close()
        supabase_session.close()
        print("\n🔌 Disconnected from databases")

if __name__ == "__main__":
    migrate_data()
