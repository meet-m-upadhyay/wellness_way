import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.connection import SessionLocal
from app.models.food_items import FoodItem

def list_foods():
    db = SessionLocal()
    try:
        foods = db.query(FoodItem).all()
        print(f"Total foods: {len(foods)}")
        for f in foods[:20]:
            print(f"- {f.canonical_name} (id: {f.id})")
    finally:
        db.close()

if __name__ == "__main__":
    list_foods()
