import os
import sys
import json
import logging
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to allow absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.food_items import FoodItem
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def expand_food_database():
    """
    Script to quickly add variety to the food_items table.
    """
    settings = get_settings()
    engine = create_engine(settings.get_database_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    new_items_data = [
        # PROTEIN - INDIAN
        {"name": "Paneer (Low Fat)", "macros": {"calories": 200, "protein": 20, "fat": 12, "carbohydrates": 4, "fiber": 0}, "diet_flags": ["vegetarian", "eggetarian"]},
        {"name": "Soya Chunks", "macros": {"calories": 345, "protein": 52, "fat": 0.5, "carbohydrates": 33, "fiber": 13}, "diet_flags": ["vegan", "vegetarian", "eggetarian"]},
        {"name": "Masoor Dal (Cooked)", "macros": {"calories": 116, "protein": 9, "fat": 0.4, "carbohydrates": 20, "fiber": 8}, "diet_flags": ["vegan", "vegetarian", "eggetarian"]},
        {"name": "Chickpeas (Boiled)", "macros": {"calories": 164, "protein": 9, "fat": 2.6, "carbohydrates": 27, "fiber": 7.6}, "diet_flags": ["vegan", "vegetarian", "eggetarian"]},
        {"name": "Tandoori Chicken Breast", "macros": {"calories": 165, "protein": 31, "fat": 3.6, "carbohydrates": 0, "fiber": 0}, "diet_flags": ["non-vegetarian"]},
        
        # STARCH - INDIAN
        {"name": "Bajra Roti", "macros": {"calories": 116, "protein": 3.3, "fat": 1.4, "carbohydrates": 22, "fiber": 3.4}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Jowar Roti", "macros": {"calories": 105, "protein": 3, "fat": 1, "carbohydrates": 21, "fiber": 3}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Brown Rice (Cooked)", "macros": {"calories": 111, "protein": 2.6, "fat": 0.9, "carbohydrates": 23, "fiber": 1.8}, "diet_flags": ["vegan", "vegetarian", "eggetarian"]},
        {"name": "Dalia (Bulgur)", "macros": {"calories": 83, "protein": 3, "fat": 0.4, "carbohydrates": 18, "fiber": 4.5}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        
        # VEGETABLES
        {"name": "Bhindi (Okra) Stir-fry", "macros": {"calories": 33, "protein": 1.9, "fat": 0.2, "carbohydrates": 7, "fiber": 3.2}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Baingan Bharta (Mashed Eggplant)", "macros": {"calories": 45, "protein": 1.5, "fat": 2, "carbohydrates": 6, "fiber": 3}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Lauki (Bottle Gourd)", "macros": {"calories": 15, "protein": 0.6, "fat": 0.1, "carbohydrates": 4, "fiber": 1}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Mixed Sprouts", "macros": {"calories": 100, "protein": 7, "fat": 0.5, "carbohydrates": 17, "fiber": 5}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        
        # FATS
        {"name": "Ghee", "macros": {"calories": 900, "protein": 0, "fat": 100, "carbohydrates": 0, "fiber": 0}, "diet_flags": ["vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Flax Seeds", "macros": {"calories": 534, "protein": 18, "fat": 42, "carbohydrates": 29, "fiber": 27}, "diet_flags": ["vegan", "vegetarian", "eggetarian"]},
    ]

    try:
        added_count = 0
        skipped_count = 0
        for item in new_items_data:
            # Check if exists (case-insensitive)
            exists = db.query(FoodItem).filter(FoodItem.canonical_name.ilike(item["name"])).first()
            if not exists:
                try:
                    new_food = FoodItem(
                        id=uuid4(),
                        canonical_name=item["name"],
                        macros=item["macros"],
                        diet_flags=item.get("diet_flags", []),
                        cuisine_tags=item.get("cuisine_tags", []),
                        is_deprecated=False
                    )
                    db.add(new_food)
                    db.flush() # Check for integrity errors here
                    added_count += 1
                except Exception as inner_e:
                    db.rollback()
                    logger.warning(f"[SKIPPED] Could not add '{item['name']}': {inner_e}")
                    skipped_count += 1
            else:
                skipped_count += 1
        
        db.commit()
        logger.info(f"[DATABASE_EXPANDED] Added {added_count} new food items. Skipped {skipped_count} (existing or error).")
        
        # Reminder to rebuild FAISS
        if added_count > 0:
            logger.info("[REBUILD_REMINDER] New items added! Please run 'python backend/scripts/build_vector_index.py' to update the FAISS index.")
        
    except Exception as e:
        db.rollback()
        logger.error(f"[DATABASE_EXPAND_FAILED] Global error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    expand_food_database()
