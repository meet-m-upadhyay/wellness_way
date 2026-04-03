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
        {"name": "Store-bought Paratha", "macros": {"calories": 250, "protein": 5, "fat": 10, "carbohydrates": 35, "fiber": 2}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Whole Wheat Roti", "macros": {"calories": 104, "protein": 3, "fat": 0.5, "carbohydrates": 22, "fiber": 3}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Naan Bread", "macros": {"calories": 260, "protein": 8, "fat": 5, "carbohydrates": 45, "fiber": 2}, "diet_flags": ["vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Poha (Rice Flakes)", "macros": {"calories": 180, "protein": 3.5, "fat": 0.5, "carbohydrates": 39, "fiber": 1}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Upma (Semolina)", "macros": {"calories": 200, "protein": 5, "fat": 4, "carbohydrates": 35, "fiber": 2}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        
        # VEGETABLES
        {"name": "Bhindi (Okra) Stir-fry", "macros": {"calories": 33, "protein": 1.9, "fat": 0.2, "carbohydrates": 7, "fiber": 3.2}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Baingan Bharta (Mashed Eggplant)", "macros": {"calories": 45, "protein": 1.5, "fat": 2, "carbohydrates": 6, "fiber": 3}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Lauki (Bottle Gourd)", "macros": {"calories": 15, "protein": 0.6, "fat": 0.1, "carbohydrates": 4, "fiber": 1}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Mixed Sprouts", "macros": {"calories": 100, "protein": 7, "fat": 0.5, "carbohydrates": 17, "fiber": 5}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Palak (Spinach Puree)", "macros": {"calories": 40, "protein": 3, "fat": 1, "carbohydrates": 6, "fiber": 4}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Gobi (Cauliflower)", "macros": {"calories": 25, "protein": 2, "fat": 0.3, "carbohydrates": 5, "fiber": 2}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Methi (Fenugreek Leaves)", "macros": {"calories": 35, "protein": 3.5, "fat": 0.5, "carbohydrates": 6, "fiber": 4.5}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        
        # FATS - INDIAN
        {"name": "Ghee", "macros": {"calories": 900, "protein": 0, "fat": 100, "carbohydrates": 0, "fiber": 0}, "diet_flags": ["vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Flax Seeds", "macros": {"calories": 534, "protein": 18, "fat": 42, "carbohydrates": 29, "fiber": 27}, "diet_flags": ["vegan", "vegetarian", "eggetarian"]},
        {"name": "Mustard Oil", "macros": {"calories": 884, "protein": 0, "fat": 100, "carbohydrates": 0, "fiber": 0}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},

        # ── MORE INDIAN PROTEIN ──
        {"name": "Moong Dal (Cooked)", "macros": {"calories": 105, "protein": 7, "fat": 0.4, "carbohydrates": 18, "fiber": 8}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Toor Dal (Cooked)", "macros": {"calories": 120, "protein": 8, "fat": 0.6, "carbohydrates": 20, "fiber": 5}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Rajma (Kidney Beans Cooked)", "macros": {"calories": 127, "protein": 9, "fat": 0.5, "carbohydrates": 23, "fiber": 7}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Kadhi (Yogurt Curry)", "macros": {"calories": 60, "protein": 3, "fat": 2, "carbohydrates": 8, "fiber": 1}, "diet_flags": ["vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Chole (Spiced Chickpeas)", "macros": {"calories": 180, "protein": 9, "fat": 4, "carbohydrates": 28, "fiber": 8}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Fish Curry (Indian)", "macros": {"calories": 150, "protein": 18, "fat": 6, "carbohydrates": 5, "fiber": 1}, "diet_flags": ["non-vegetarian"], "cuisine_tags": ["indian"]},
        {"name": "Egg Bhurji", "macros": {"calories": 170, "protein": 13, "fat": 12, "carbohydrates": 2, "fiber": 0}, "diet_flags": ["eggetarian"], "cuisine_tags": ["indian"]},

        # ── MORE INDIAN STARCH ──
        {"name": "Idli (Steamed Rice Cake)", "macros": {"calories": 40, "protein": 2, "fat": 0.2, "carbohydrates": 8, "fiber": 0.5}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Dosa (Crispy Crepe)", "macros": {"calories": 120, "protein": 3, "fat": 3, "carbohydrates": 20, "fiber": 1}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Puri (Fried Bread)", "macros": {"calories": 200, "protein": 4, "fat": 8, "carbohydrates": 28, "fiber": 1}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Khichdi (Rice & Lentil Mix)", "macros": {"calories": 130, "protein": 5, "fat": 2, "carbohydrates": 22, "fiber": 3}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},

        # ── MORE INDIAN VEGETABLES ──
        {"name": "Aloo Gobi (Potato Cauliflower)", "macros": {"calories": 90, "protein": 2, "fat": 3, "carbohydrates": 15, "fiber": 3}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Tinda (Apple Gourd)", "macros": {"calories": 18, "protein": 1, "fat": 0.1, "carbohydrates": 4, "fiber": 1.5}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Karela (Bitter Gourd)", "macros": {"calories": 20, "protein": 1, "fat": 0.2, "carbohydrates": 4, "fiber": 3}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},
        {"name": "Raita (Yogurt Side)", "macros": {"calories": 45, "protein": 3, "fat": 1.5, "carbohydrates": 5, "fiber": 0}, "diet_flags": ["vegetarian", "eggetarian"], "cuisine_tags": ["indian"]},

        # ── MEDITERRANEAN PROTEIN ──
        {"name": "Falafel (Baked)", "macros": {"calories": 180, "protein": 7, "fat": 8, "carbohydrates": 22, "fiber": 4}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Feta Cheese", "macros": {"calories": 264, "protein": 14, "fat": 21, "carbohydrates": 4, "fiber": 0}, "diet_flags": ["vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Grilled Chicken (Mediterranean)", "macros": {"calories": 165, "protein": 31, "fat": 3.6, "carbohydrates": 0, "fiber": 0}, "diet_flags": ["non-vegetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Grilled Salmon Fillet", "macros": {"calories": 208, "protein": 20, "fat": 13, "carbohydrates": 0, "fiber": 0}, "diet_flags": ["non-vegetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Tzatziki (Yogurt Dip)", "macros": {"calories": 50, "protein": 3, "fat": 2.5, "carbohydrates": 4, "fiber": 0}, "diet_flags": ["vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Halloumi Cheese", "macros": {"calories": 321, "protein": 22, "fat": 25, "carbohydrates": 3, "fiber": 0}, "diet_flags": ["vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Stuffed Grape Leaves (Dolma)", "macros": {"calories": 90, "protein": 2, "fat": 5, "carbohydrates": 10, "fiber": 2}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Shakshuka Egg", "macros": {"calories": 200, "protein": 14, "fat": 12, "carbohydrates": 10, "fiber": 2}, "diet_flags": ["eggetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Labneh (Strained Yogurt)", "macros": {"calories": 80, "protein": 5, "fat": 5, "carbohydrates": 4, "fiber": 0}, "diet_flags": ["vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},

        # ── MEDITERRANEAN STARCH ──
        {"name": "Whole Wheat Pita Bread", "macros": {"calories": 170, "protein": 6, "fat": 2, "carbohydrates": 35, "fiber": 5}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Couscous (Cooked)", "macros": {"calories": 112, "protein": 4, "fat": 0.2, "carbohydrates": 23, "fiber": 1.4}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Bulgur Wheat (Cooked)", "macros": {"calories": 83, "protein": 3, "fat": 0.2, "carbohydrates": 18.6, "fiber": 4.5}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Orzo Pasta (Cooked)", "macros": {"calories": 200, "protein": 7, "fat": 1, "carbohydrates": 42, "fiber": 2}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Focaccia Bread", "macros": {"calories": 270, "protein": 7, "fat": 7, "carbohydrates": 44, "fiber": 2}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Tabbouleh Base (Bulgur)", "macros": {"calories": 90, "protein": 3, "fat": 3, "carbohydrates": 14, "fiber": 4}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},

        # ── MEDITERRANEAN VEGETABLES ──
        {"name": "Roasted Eggplant", "macros": {"calories": 35, "protein": 1, "fat": 0.2, "carbohydrates": 9, "fiber": 3}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Kalamata Olives", "macros": {"calories": 145, "protein": 1, "fat": 13, "carbohydrates": 4, "fiber": 3}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Sun-Dried Tomatoes", "macros": {"calories": 258, "protein": 14, "fat": 3, "carbohydrates": 56, "fiber": 12}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Artichoke Hearts", "macros": {"calories": 47, "protein": 3, "fat": 0.2, "carbohydrates": 11, "fiber": 5}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Grilled Zucchini", "macros": {"calories": 17, "protein": 1.2, "fat": 0.3, "carbohydrates": 3, "fiber": 1}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Roasted Red Peppers", "macros": {"calories": 30, "protein": 1, "fat": 0.3, "carbohydrates": 6, "fiber": 2}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Baba Ganoush (Eggplant Dip)", "macros": {"calories": 70, "protein": 2, "fat": 4, "carbohydrates": 7, "fiber": 3}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},

        # ── MEDITERRANEAN FATS ──
        {"name": "Extra Virgin Olive Oil", "macros": {"calories": 884, "protein": 0, "fat": 100, "carbohydrates": 0, "fiber": 0}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Tahini Paste", "macros": {"calories": 595, "protein": 17, "fat": 54, "carbohydrates": 21, "fiber": 9}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},
        {"name": "Pine Nuts", "macros": {"calories": 673, "protein": 14, "fat": 68, "carbohydrates": 13, "fiber": 4}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["mediterranean"]},

        # ══════════════════════════════════
        # ── ITALIAN PROTEIN ──
        # ══════════════════════════════════
        {"name": "Ricotta Cheese", "macros": {"calories": 174, "protein": 11, "fat": 13, "carbohydrates": 3, "fiber": 0}, "diet_flags": ["vegetarian", "eggetarian"], "cuisine_tags": ["italian"]},
        {"name": "Fresh Mozzarella", "macros": {"calories": 280, "protein": 22, "fat": 22, "carbohydrates": 1, "fiber": 0}, "diet_flags": ["vegetarian", "eggetarian"], "cuisine_tags": ["italian"]},
        {"name": "Parmesan Cheese (Grated)", "macros": {"calories": 431, "protein": 38, "fat": 29, "carbohydrates": 4, "fiber": 0}, "diet_flags": ["vegetarian", "eggetarian"], "cuisine_tags": ["italian"]},
        {"name": "Italian Grilled Chicken", "macros": {"calories": 165, "protein": 31, "fat": 3.6, "carbohydrates": 0, "fiber": 0}, "diet_flags": ["non-vegetarian"], "cuisine_tags": ["italian"]},
        {"name": "Prosciutto (Lean)", "macros": {"calories": 195, "protein": 26, "fat": 10, "carbohydrates": 0, "fiber": 0}, "diet_flags": ["non-vegetarian"], "cuisine_tags": ["italian"]},
        {"name": "Italian Sausage (Turkey)", "macros": {"calories": 150, "protein": 17, "fat": 8, "carbohydrates": 2, "fiber": 0}, "diet_flags": ["non-vegetarian"], "cuisine_tags": ["italian"]},
        {"name": "White Beans (Cannellini)", "macros": {"calories": 118, "protein": 8, "fat": 0.5, "carbohydrates": 21, "fiber": 6}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["italian"]},

        # ── ITALIAN STARCH ──
        {"name": "Penne Pasta (Whole Wheat)", "macros": {"calories": 174, "protein": 7, "fat": 1, "carbohydrates": 37, "fiber": 6}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["italian"]},
        {"name": "Spaghetti (Cooked)", "macros": {"calories": 158, "protein": 6, "fat": 0.9, "carbohydrates": 31, "fiber": 2}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["italian"]},
        {"name": "Risotto Rice (Arborio)", "macros": {"calories": 130, "protein": 2.5, "fat": 0.2, "carbohydrates": 28, "fiber": 0.4}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["italian"]},
        {"name": "Ciabatta Bread", "macros": {"calories": 271, "protein": 9, "fat": 4, "carbohydrates": 50, "fiber": 2}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["italian"]},
        {"name": "Gnocchi (Potato)", "macros": {"calories": 133, "protein": 3, "fat": 0.5, "carbohydrates": 30, "fiber": 2}, "diet_flags": ["vegetarian", "eggetarian"], "cuisine_tags": ["italian"]},
        {"name": "Polenta (Cooked)", "macros": {"calories": 70, "protein": 1.5, "fat": 0.3, "carbohydrates": 15, "fiber": 1}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["italian"]},

        # ── ITALIAN VEGETABLES ──
        {"name": "Marinara Sauce", "macros": {"calories": 35, "protein": 1, "fat": 0.5, "carbohydrates": 7, "fiber": 2}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["italian"]},
        {"name": "Roasted Cherry Tomatoes", "macros": {"calories": 25, "protein": 1, "fat": 0.5, "carbohydrates": 5, "fiber": 1.5}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["italian"]},
        {"name": "Grilled Asparagus", "macros": {"calories": 22, "protein": 2.4, "fat": 0.2, "carbohydrates": 4, "fiber": 2}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["italian"]},
        {"name": "Sauteed Mushrooms", "macros": {"calories": 28, "protein": 2, "fat": 0.5, "carbohydrates": 4, "fiber": 1.5}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["italian"]},
        {"name": "Italian Mixed Salad (Insalata)", "macros": {"calories": 15, "protein": 1, "fat": 0.2, "carbohydrates": 3, "fiber": 1.5}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["italian"]},
        {"name": "Roasted Fennel", "macros": {"calories": 31, "protein": 1, "fat": 0.2, "carbohydrates": 7, "fiber": 3}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["italian"]},

        # ── ITALIAN FATS ──
        {"name": "Basil Pesto", "macros": {"calories": 270, "protein": 6, "fat": 25, "carbohydrates": 6, "fiber": 2}, "diet_flags": ["vegetarian", "eggetarian"], "cuisine_tags": ["italian"]},
        {"name": "Italian Olive Oil", "macros": {"calories": 884, "protein": 0, "fat": 100, "carbohydrates": 0, "fiber": 0}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["italian"]},
        {"name": "Balsamic Vinaigrette", "macros": {"calories": 90, "protein": 0, "fat": 7, "carbohydrates": 6, "fiber": 0}, "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["italian"]},
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
                        dataset_source="manual",
                        dataset_food_id=str(uuid4()),
                        registry_version=1,
                        macros=item["macros"],
                        diet_flags=item.get("diet_flags", []),
                        cuisine_tags=item.get("cuisine_tags", []),
                        allergen_flags=[],
                        is_deprecated=False
                    )
                    db.add(new_food)
                    db.commit() # Commit individually to isolate failures
                    added_count += 1
                except Exception as inner_e:
                    db.rollback()
                    logger.warning(f"[SKIPPED] Could not add '{item['name']}': {inner_e}")
                    skipped_count += 1
            else:
                skipped_count += 1
        
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
