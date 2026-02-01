#!/usr/bin/env python
"""
Supabase Database Setup and Verification Script for WellnessWay Diet Planner

This script provides utilities for:
- Testing Supabase database connection
- Verifying table creation
- Running sample queries
- Checking migration status
- Troubleshooting connection issues

Usage:
    python setup_supabase.py --test-connection
    python setup_supabase.py --verify-tables
    python setup_supabase.py --test-query
    python setup_supabase.py --check-migrations
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_environment():
    """Load environment variables from .env file"""
    from dotenv import load_dotenv
    
    # Load from root .env
    root_env = Path(__file__).parent.parent / '.env'
    if root_env.exists():
        load_dotenv(root_env)
        logger.info(f"Loaded environment from {root_env}")
    
    # Load from backend/.env (overrides root)
    backend_env = Path(__file__).parent / '.env'
    if backend_env.exists():
        load_dotenv(backend_env)
        logger.info(f"Loaded environment from {backend_env}")

def get_database_url() -> Optional[str]:
    """Get database URL from environment"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL not found in environment variables")
        logger.info("Please set DATABASE_URL in your .env file")
        logger.info("Format: postgresql+psycopg://user:password@host:port/database")
        return None
    return db_url

def parse_connection_string(url: str) -> Dict[str, str]:
    """Parse PostgreSQL connection string"""
    try:
        # Remove protocol prefix
        if url.startswith('postgresql+psycopg://'):
            url = url.replace('postgresql+psycopg://', '')
        elif url.startswith('postgresql://'):
            url = url.replace('postgresql://', '')
        
        # Split credentials and host
        if '@' in url:
            credentials, host_db = url.split('@', 1)
            user, password = credentials.split(':', 1)
        else:
            user = 'postgres'
            password = ''
            host_db = url
        
        # Split host and database
        if ':' in host_db:
            host_port, database = host_db.split('/', 1)
            host, port = host_port.split(':')
        else:
            host = host_db.split('/')[0]
            port = '5432'
            database = host_db.split('/')[-1] if '/' in host_db else 'postgres'
        
        return {
            'user': user,
            'password': '***' if password else '',
            'host': host,
            'port': port,
            'database': database,
            'password_actual': password  # For actual connection
        }
    except Exception as e:
        logger.error(f"Failed to parse connection string: {e}")
        return None

def test_connection(verbose: bool = False) -> bool:
    """Test database connection"""
    print("\n" + "="*60)
    print("SUPABASE CONNECTION TEST")
    print("="*60)
    
    db_url = get_database_url()
    if not db_url:
        return False
    
    # Parse and display connection details
    conn_info = parse_connection_string(db_url)
    if not conn_info:
        return False
    
    print(f"\n📋 Connection Details:")
    print(f"  Host: {conn_info['host']}")
    print(f"  Port: {conn_info['port']}")
    print(f"  Database: {conn_info['database']}")
    print(f"  User: {conn_info['user']}")
    
    # Test connection
    print(f"\n🔌 Testing connection...")
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.pool import NullPool
        
        # Create engine with minimal pooling for testing
        engine = create_engine(
            db_url,
            poolclass=NullPool,
            connect_args={'connect_timeout': 10}
        )
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            
        print(f"✅ Database connection successful!")
        print(f"\n📊 PostgreSQL Version:")
        print(f"  {version.split(',')[0] if version else 'Unknown'}")
        
        # Get table count
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'"
            ))
            table_count = result.scalar()
        
        print(f"\n📦 Database Status:")
        print(f"  Tables: {table_count}")
        
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed!")
        print(f"\n❌ Error: {str(e)}")
        print(f"\n💡 Troubleshooting:")
        print(f"  1. Verify DATABASE_URL in .env file")
        print(f"  2. Check password contains no special characters")
        print(f"  3. Ensure Supabase project is active")
        print(f"  4. Verify internet connection")
        return False

def verify_tables(verbose: bool = False) -> bool:
    """Verify database schema and tables"""
    print("\n" + "="*60)
    print("DATABASE SCHEMA VERIFICATION")
    print("="*60)
    
    db_url = get_database_url()
    if not db_url:
        return False
    
    try:
        from sqlalchemy import create_engine, text, inspect
        from sqlalchemy.pool import NullPool
        
        engine = create_engine(db_url, poolclass=NullPool)
        
        print(f"\n📊 Schema Analysis:")
        
        # Get all tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if not tables:
            print(f"⚠️  No tables found (database may be empty)")
            print(f"\n💡 To create tables, run:")
            print(f"  cd backend")
            print(f"  python -m alembic upgrade head")
            engine.dispose()
            return False
        
        print(f"✅ Found {len(tables)} table(s):\n")
        
        # List tables with row counts
        with engine.connect() as conn:
            for table_name in sorted(tables):
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM \"{table_name}\""))
                    row_count = result.scalar()
                    columns = len(inspector.get_columns(table_name))
                    print(f"  ✓ {table_name:<30} ({columns} columns, {row_count} rows)")
                except Exception as e:
                    print(f"  ✗ {table_name:<30} (Error reading: {str(e)})")
        
        print(f"\n✅ Schema verification complete!")
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Verification failed!")
        print(f"\n❌ Error: {str(e)}")
        return False

def test_query(verbose: bool = False) -> bool:
    """Run sample test queries"""
    print("\n" + "="*60)
    print("TEST QUERY EXECUTION")
    print("="*60)
    
    db_url = get_database_url()
    if not db_url:
        return False
    
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.pool import NullPool
        
        engine = create_engine(db_url, poolclass=NullPool)
        
        print(f"\n🔍 Executing test queries:\n")
        
        with engine.connect() as conn:
            # Test 1: Simple SELECT
            print(f"  1️⃣  Simple version check...")
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"     ✅ Success: {version.split(',')[0]}")
            
            # Test 2: Table enumeration
            print(f"\n  2️⃣  Table enumeration...")
            result = conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname='public'"
            ))
            tables = result.fetchall()
            print(f"     ✅ Found {len(tables)} tables")
            
            # Test 3: Check specific tables if they exist
            print(f"\n  3️⃣  Checking application tables...")
            essential_tables = ['users', 'diet_plans', 'meals', 'ingredients']
            found_tables = [t[0] for t in tables]
            
            for table in essential_tables:
                if table in found_tables:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM \"{table}\""))
                    count = count_result.scalar()
                    print(f"     ✅ {table}: {count} rows")
                else:
                    print(f"     ⚠️  {table}: NOT FOUND (may need migrations)")
        
        print(f"\n✅ Test queries completed!")
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Query execution failed!")
        print(f"\n❌ Error: {str(e)}")
        return False

def check_migrations(verbose: bool = False) -> bool:
    """Check migration status"""
    print("\n" + "="*60)
    print("ALEMBIC MIGRATION STATUS")
    print("="*60)
    
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import create_engine, text
        from sqlalchemy.pool import NullPool
        
        db_url = get_database_url()
        if not db_url:
            return False
        
        # Create engine
        engine = create_engine(db_url, poolclass=NullPool)
        
        # Get alembic config
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", db_url)
        
        script = ScriptDirectory.from_config(config)
        
        # Get current revision
        with engine.begin() as connection:
            context = MigrationContext.configure(connection)
            current_revision = context.get_current_revision()
        
        print(f"\n📝 Migration Information:\n")
        
        # Get all revisions
        revisions = list(script.walk_revisions('heads', 'bases'))
        print(f"  Total migrations available: {len(revisions)}")
        print(f"  Current revision: {current_revision if current_revision else 'NONE (no migrations applied)'}")
        
        # Get head revision
        head_revisions = list(script.get_heads())
        if head_revisions:
            print(f"  Target revision (head): {head_revisions[0]}")
            
            if current_revision:
                if current_revision == head_revisions[0]:
                    print(f"\n  ✅ All migrations applied!")
                else:
                    print(f"\n  ⚠️  Migrations pending")
                    print(f"     Run: python -m alembic upgrade head")
            else:
                print(f"\n  ⚠️  No migrations applied yet")
                print(f"     Run: python -m alembic upgrade head")
        
        engine.dispose()
        print(f"\n✅ Migration check complete!")
        return True
        
    except Exception as e:
        print(f"❌ Migration check failed!")
        print(f"\n❌ Error: {str(e)}")
        logger.debug(f"Full error: {e}", exc_info=True)
        return False

def diagnose():
    """Run complete diagnostic"""
    print("\n" + "="*60)
    print("SUPABASE SETUP DIAGNOSTIC")
    print("="*60)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print(f"Python Version: {sys.version}")
    print(f"Platform: {sys.platform}")
    
    # Check environment
    print(f"\n📋 Environment Check:")
    db_url = get_database_url()
    if db_url:
        conn_info = parse_connection_string(db_url)
        print(f"  ✅ DATABASE_URL set")
        print(f"     Host: {conn_info['host']}")
    else:
        print(f"  ❌ DATABASE_URL not set")
    
    # Run all checks
    results = []
    results.append(("Connection Test", test_connection()))
    results.append(("Schema Verification", verify_tables()))
    results.append(("Query Test", test_query()))
    results.append(("Migration Check", check_migrations()))
    
    # Summary
    print(f"\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {check_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print(f"\n✅ All checks passed! Your Supabase setup is ready.")
    else:
        print(f"\n❌ Some checks failed. Please review the errors above.")
        print(f"\n💡 Common fixes:")
        print(f"  1. Verify DATABASE_URL in .env file")
        print(f"  2. Test connection manually")
        print(f"  3. Check Supabase project is active")
        print(f"  4. Run migrations: python -m alembic upgrade head")
    
    return all_passed

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Supabase Database Setup and Verification for WellnessWay",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup_supabase.py --test-connection
  python setup_supabase.py --verify-tables
  python setup_supabase.py --test-query
  python setup_supabase.py --check-migrations
  python setup_supabase.py --diagnose
  python setup_supabase.py -v --test-connection
        """
    )
    
    parser.add_argument(
        '--test-connection',
        action='store_true',
        help='Test database connection'
    )
    parser.add_argument(
        '--verify-tables',
        action='store_true',
        help='Verify database schema and tables'
    )
    parser.add_argument(
        '--test-query',
        action='store_true',
        help='Run sample test queries'
    )
    parser.add_argument(
        '--check-migrations',
        action='store_true',
        help='Check Alembic migration status'
    )
    parser.add_argument(
        '--diagnose',
        action='store_true',
        help='Run complete diagnostic'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Load environment
    load_environment()
    
    # If verbose, enable debug logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Default action if no specific option provided
    if not any([args.test_connection, args.verify_tables, args.test_query, 
                args.check_migrations, args.diagnose]):
        args.diagnose = True
    
    # Run requested actions
    success = True
    
    if args.test_connection:
        success = test_connection(args.verbose) and success
    
    if args.verify_tables:
        success = verify_tables(args.verbose) and success
    
    if args.test_query:
        success = test_query(args.verbose) and success
    
    if args.check_migrations:
        success = check_migrations(args.verbose) and success
    
    if args.diagnose:
        success = diagnose()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
