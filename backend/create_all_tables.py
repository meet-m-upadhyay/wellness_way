#!/usr/bin/env python3
"""
Create all database tables using SQLAlchemy models
"""

def create_tables():
    from app.database.connection import Base, engine
    from app.models.user import User, HealthGoals, DietPreferences
    from app.models.health_context import HealthContextDocument
    from app.models.diet_plan import DietPlan
    
    print('🚀 Creating all database tables...')
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print('✅ All tables created successfully!')
        
        # List created tables
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = result.fetchall()
            print(f'📋 Created tables: {[table[0] for table in tables]}')
            
            # Show table details
            for table in tables:
                table_name = table[0]
                result = conn.execute(text(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """))
                columns = result.fetchall()
                print(f'\n📊 Table: {table_name}')
                for col in columns:
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    default = f" DEFAULT {col[3]}" if col[3] else ""
                    print(f"  - {col[0]}: {col[1]} {nullable}{default}")
        
        return True
        
    except Exception as e:
        print(f'❌ Error creating tables: {e}')
        return False

if __name__ == "__main__":
    success = create_tables()
    if success:
        print("\n🎉 Database schema setup complete!")
    else:
        print("\n💥 Database schema setup failed!")