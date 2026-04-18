"""
SQLAlchemy ORM models for WellnessWay Diet Planner
"""

from .user import User, HealthGoals, DietPreferences
from .health_context import HealthContextDocument
from .diet_plan import DietPlan
from .food_items import FoodItem
from .food_datasets import FoodDataset
from .food_embeddings import FoodEmbedding
from .chat import Chat, Message

# V2 Meal Engine models
from .v2_regions import V2Region
from .v2_ingredients import V2Ingredient
from .v2_pairing_rules import V2PairingRule
from .v2_ingredient_embeddings import V2IngredientEmbedding
from .v2_external_nutrition_cache import V2ExternalNutritionCache

__all__ = [
    "User",
    "HealthGoals",
    "DietPreferences",
    "HealthContextDocument",
    "DietPlan",
    "FoodItem",
    "FoodDataset",
    "FoodEmbedding",
    "Chat",
    "Message",
    # V2 Meal Engine
    "V2Region",
    "V2Ingredient",
    "V2PairingRule",
    "V2IngredientEmbedding",
    "V2ExternalNutritionCache",
]