"""One-time cleanup: deprecate API-cached food items with bad macros."""
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models.food_items import FoodItem

settings = get_settings()
engine = create_engine(settings.get_database_url())
Session = sessionmaker(bind=engine)
db = Session()

# Find API-cached items with suspiciously low protein (likely bad USDA matches)
bad_items = db.query(FoodItem).filter(
    FoodItem.api_verified.is_(True),
    FoodItem.dataset_source.in_(["usda", "api_ninjas", "calorieninjas"]),
).all()

deprecated_count = 0
for item in bad_items:
    macros = item.macros or {}
    protein = macros.get("protein", 0)
    if protein < 5:
        print(f"  DEPRECATING: {item.canonical_name} (protein={protein}, source={item.dataset_source})")
        item.is_deprecated = True
        deprecated_count += 1

db.commit()
print(f"\nDeprecated {deprecated_count} bad API-cached items. Good manual entries preserved.")
db.close()
