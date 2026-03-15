import sys
import os
sys.path.append(os.getcwd())
from sqlalchemy import create_engine, inspect
from app.core.config import get_settings

def check_columns():
    settings = get_settings()
    engine = create_engine(settings.database.url)
    inspector = inspect(engine)
    try:
        columns = [c['name'] for c in inspector.get_columns('diet_preferences')]
        print(f'Columns in diet_preferences: {columns}')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    check_columns()
