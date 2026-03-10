"""
Discovery Engine - Dynamic ingredient discovery from food registry
"""

from __future__ import annotations

import logging
import random
from typing import Dict, List, Set, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, not_

from app.models.food_items import FoodItem

logger = logging.getLogger(__name__)


class DiscoveryEngine:
    """Dynamically discover allowed ingredients based on diet and allergies"""

    def __init__(self):
        """Initialize discovery engine"""
        logger.info("[DISCOVERY_ENGINE_INIT] Initialized dynamic discovery engine")

    def discover_daily_portfolio(
        self,
        db: Session,
        diet_type: str,
        allergies: Set[str],
        exclude_ingredients: Optional[Set[str]] = None
    ) -> Dict[str, List[FoodItem]]:
        """
        Discover a portfolio of ingredients for the day.
        
        Returns:
            Dict mapping categories to lists of FoodItem models
        """
        exclude_ingredients = exclude_ingredients or set()
        
        # Categories we want to fill for a balanced day
        portfolio = {
            "proteins": [],
            "starches": [],
            "vegetables": [],
            "fats": []
        }
        
        # 1. Fetch candidates from database
        # Define inclusive diet filtering
        diet_filter = []
        if diet_type == "vegan":
            diet_filter = ["vegan"]
        elif diet_type == "vegetarian":
            diet_filter = ["vegan", "vegetarian"]
        elif diet_type == "eggetarian":
            diet_filter = ["vegan", "vegetarian", "eggetarian"]
        # Non-vegetarian has no diet filter (can eat anything)

        base_query = db.query(FoodItem).filter(FoodItem.is_deprecated == False)
        
        if diet_filter:
            # Hybrid approach: Use flags if they exist, but also fallback to keyword exclusion
            # because some items in the registry might not have flags populated yet.
            from sqlalchemy import or_
            
            # Sub-filters
            flag_match = or_(*[FoodItem.diet_flags.contains([d]) for d in diet_filter])
            
            # If item has NO flags, it might still be compatible if it doesn't have "forbidden" keywords
            # For vegetarian/vegan, we want to exclude meat keywords
            base_query = base_query.filter(
                or_(
                    flag_match,
                    and_(
                        FoodItem.diet_flags == [],  # No flags specified
                        not_(or_(*[
                            FoodItem.canonical_name.ilike(f"%{forbidden}%")
                            for forbidden in ["chicken", "beef", "pork", "fish", "lamb", "shrimp", "salmon", "tuna", "turkey", "ham", "bacon", "meat"]
                        ]))
                    )
                )
            )
            
            # Vegan specific: Also exclude animal products if it's a vegan diet
            if diet_type == "vegan":
                base_query = base_query.filter(
                    not_(or_(*[
                         FoodItem.canonical_name.ilike(f"%{animal}%")
                         for animal in ["egg", "milk", "cheese", "yogurt", "butter", "honey", "cream", "whey", "paneer"]
                    ]))
                )
        
        # Exclude allergens
        for allergen in allergies:
            base_query = base_query.filter(not_(FoodItem.allergen_flags.contains([allergen.lower()])))
            
        # Exclude specific ingredients (for variety)
        if exclude_ingredients:
            base_query = base_query.filter(not_(FoodItem.canonical_name.in_(list(exclude_ingredients))))

        candidates = base_query.all()
        
        if not candidates:
            logger.error(f"[DISCOVERY_ERROR] No candidates found for diet={diet_type} allergies={allergies}")
            raise ValueError(f"No compatible food items found in registry for {diet_type} diet.")

        # 2. Categorize candidates (heuristic for now, could be tags in DB)
        for item in candidates:
            name = item.canonical_name.lower()
            macros = item.macros or {}
            protein_pct = (macros.get("protein", 0) * 4) / max(macros.get("calories", 1), 1)
            
            if "protein" in name or protein_pct > 0.3:
                portfolio["proteins"].append(item)
            elif any(x in name for x in ["rice", "bread", "oats", "quinoa", "potato", "pasta", "tortilla"]):
                portfolio["starches"].append(item)
            elif any(x in name for x in ["oil", "butter", "avocado", "nut", "seed", "tahini"]):
                portfolio["fats"].append(item)
            else:
                portfolio["vegetables"].append(item)

        # 3. Select a unique set for today (Variety via random sampling)
        selected = {
            "protein": random.sample(portfolio["proteins"], min(len(portfolio["proteins"]), 3)),
            "starch": random.sample(portfolio["starches"], min(len(portfolio["starches"]), 3)),
            "vegetables": random.sample(portfolio["vegetables"], min(len(portfolio["vegetables"]), 3)),
            "fat": random.sample(portfolio["fats"], min(len(portfolio["fats"]), 3))
        }
        
        logger.info(
            f"[DISCOVERY_PORTFOLIO] Discoverd {sum(len(v) for v in selected.values())} "
            f"ingredients for diet={diet_type}"
        )
        
        return selected

def get_discovery_engine() -> DiscoveryEngine:
    """Get singleton instance"""
    return DiscoveryEngine()
