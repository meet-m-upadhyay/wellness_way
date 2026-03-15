"""
Discovery Engine - Dynamic ingredient discovery from food registry
"""

from __future__ import annotations

import logging
import random
from typing import Dict, List, Set, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, not_, or_

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
        foods_to_avoid: Optional[Set[str]] = None,
        exclude_ingredients: Optional[Set[str]] = None
    ) -> Dict[str, List[FoodItem]]:
        """
        Discover a portfolio of ingredients for the day.
        
        Returns:
            Dict mapping categories to lists of FoodItem models
        """
        exclude_ingredients = exclude_ingredients or set()
        foods_to_avoid = foods_to_avoid or set()
        
        # 1. Fetch ALL candidates matching STRICTOR constraints (Diet, Allergies)
        diet_filter = []
        if diet_type == "vegan":
            diet_filter = ["vegan"]
        elif diet_type == "vegetarian":
            diet_filter = ["vegan", "vegetarian"]
        elif diet_type == "eggetarian":
            diet_filter = ["vegan", "vegetarian", "eggetarian"]

        base_query = db.query(FoodItem).filter(FoodItem.is_deprecated == False)
        
        if diet_filter:
            flag_match = or_(*[FoodItem.diet_flags.contains([d]) for d in diet_filter])
            base_query = base_query.filter(
                or_(
                    flag_match,
                    and_(
                        FoodItem.diet_flags == [],
                        not_(or_(*[
                            FoodItem.canonical_name.ilike(f"%{forbidden}%")
                            for forbidden in ["chicken", "beef", "pork", "fish", "lamb", "shrimp", "salmon", "tuna", "turkey", "ham", "bacon", "meat"]
                        ]))
                    )
                )
            )
            
            if diet_type == "vegan":
                base_query = base_query.filter(
                    not_(or_(*[
                         FoodItem.canonical_name.ilike(f"%{animal}%")
                         for animal in ["egg", "milk", "cheese", "yogurt", "butter", "honey", "cream", "whey", "paneer"]
                    ]))
                )
        
        for allergen in allergies:
            base_query = base_query.filter(
                and_(
                    not_(FoodItem.allergen_flags.contains([allergen.lower()])),
                    not_(FoodItem.canonical_name.ilike(f"%{allergen}%"))
                )
            )
            
        for food in foods_to_avoid:
            base_query = base_query.filter(not_(FoodItem.canonical_name.ilike(f"%{food}%")))
            
        all_allowed_candidates = base_query.all()
        
        if not all_allowed_candidates:
            logger.error(f"[DISCOVERY_ERROR] No candidates found for diet={diet_type} allergies={allergies}")
            raise ValueError(f"No compatible food items found in registry for {diet_type} diet.")

        # 2. Categorize candidates
        categorized = {
            "protein": [],
            "starch": [],
            "vegetables": [],
            "fat": []
        }
        
        for item in all_allowed_candidates:
            name = item.canonical_name.lower()
            macros = item.macros or {}
            # Heuristic for protein: >30% energy or name-based
            protein_pct = (macros.get("protein", 0) * 4) / max(macros.get("calories", 0) or 1, 1)
            
            if "protein" in name or protein_pct > 0.3:
                categorized["protein"].append(item)
            elif any(x in name for x in ["rice", "bread", "oats", "quinoa", "potato", "pasta", "tortilla"]):
                categorized["starch"].append(item)
            elif any(x in name for x in ["oil", "butter", "avocado", "nut", "seed", "tahini"]):
                categorized["fat"].append(item)
            else:
                categorized["vegetables"].append(item)

        # 3. Apply exclusions with soft fallback per category
        selected = {}
        for cat, items in categorized.items():
            # Try applying variety exclusions
            non_excluded = [it for it in items if it.canonical_name not in exclude_ingredients]
            
            if len(non_excluded) >= 3:
                selected[cat] = random.sample(non_excluded, 3)
            elif len(non_excluded) > 0:
                # Use what we have, then supplement from excluded if needed to hit 3
                selected[cat] = non_excluded
                remaining = 3 - len(non_excluded)
                excluded_items = [it for it in items if it.canonical_name in exclude_ingredients]
                if excluded_items:
                    selected[cat].extend(random.sample(excluded_items, min(len(excluded_items), remaining)))
            else:
                # No non-excluded items! Fallback completely to the full allowed list for this category
                logger.warning(f"[DISCOVERY_VARIETY_WARNING] category={cat} depleted due to exclusions. Falling back.")
                selected[cat] = random.sample(items, min(len(items), 3))

        logger.info(
            f"[DISCOVERY_PORTFOLIO] Discoverd {sum(len(v) for v in selected.values())} "
            f"ingredients for diet={diet_type} (variety fallback check complete)"
        )
        
        return selected

def get_discovery_engine() -> DiscoveryEngine:
    """Get singleton instance"""
    return DiscoveryEngine()
