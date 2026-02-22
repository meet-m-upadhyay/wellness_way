"""
Test Supabase connection
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load .env
load_dotenv()

# Get DATABASE_URL
db_url = os.getenv("DATABASE_URL")

print("=" * 60)
print("🔍 Testing Supabase Connection")
print("=" * 60)

if not db_url:
    print("❌ DATABASE_URL not found in .env file!")
    exit(1)

# Mask password
display_url = db_url.split('@')[0].split(':')[0] + ":***@" + db_url.split('@')[1] if '@' in db_url else db_url
print(f"\n📍 Connection String: {display_url}")

# Extract host
if '@' in db_url:
    host_part = db_url.split('@')[1].split(':')[0]
    print(f"🌐 Host: {host_part}")

print("\n🔌 Attempting to connect...")

try:
    # Create engine
    engine = create_engine(db_url)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        
        print("✅ Connection successful!")
        print(f"\n📊 PostgreSQL Version:")
        print(f"   {version[:80]}...")
        
        # Test if we can query tables
        result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
        table_count = result.scalar()
        print(f"\n📦 Tables in database: {table_count}")
        
        if table_count > 0:
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))
            tables = [row[0] for row in result]
            print(f"\n📋 Existing tables:")
            for table in tables:
                print(f"   - {table}")
        
except Exception as e:
    print(f"❌ Connection failed!")
    print(f"\n🔴 Error: {e}")
    print(f"\n💡 Troubleshooting:")
    print("   1. Check your Supabase connection string is correct")
    print("   2. Use the POOLER connection (port 6543), not direct (port 5432)")
    print("   3. Verify your password is correct")
    print("   4. Check your internet connection")
    print("   5. Make sure your Supabase project is active")
    exit(1)

print("\n" + "=" * 60)
print("✅ All checks passed!")
print("=" * 60)
