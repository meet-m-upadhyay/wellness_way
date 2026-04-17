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


# Priority scores by user diet type → item diet tier.
# Higher score = stronger preference. Every allowed tier gets a score;
# tiers not listed for a diet type are excluded by the SQL filter anyway.
_DIET_PRIORITY = {
    "non-vegetarian": {"non-vegetarian": 4.0, "eggetarian": 3.0, "vegetarian": 2.0, "vegan": 1.0},
    "eggetarian":     {"eggetarian": 3.0, "vegetarian": 2.0, "vegan": 1.0},
    "vegetarian":     {"vegetarian": 2.0, "vegan": 1.0},
    "vegan":          {"vegan": 1.0},
}


def _item_diet_tier(diet_flags: list) -> str:
    """Determine the diet tier of a food item from its diet_flags.

    Returns the most specific category the item belongs to:
      non-vegetarian  →  meat/fish
      eggetarian      →  egg (but not dairy/plant)
      vegetarian      →  dairy (but not plant-only)
      vegan           →  plant-only / generic
    """
    flags = {f.lower() for f in (diet_flags or [])}
    if "non-vegetarian" in flags:
        return "non-vegetarian"
    if "eggetarian" in flags and "vegetarian" not in flags:
        return "eggetarian"
    if "vegetarian" in flags and "vegan" not in flags:
        return "vegetarian"
    return "vegan"


class DiscoveryEngine:
    """Dynamically discover allowed ingredients based on diet, allergies, cuisine, and goals"""

    def __init__(self):
        """Initialize discovery engine"""
        logger.info("[DISCOVERY_ENGINE_INIT] Initialized dynamic discovery engine")

    def discover_daily_portfolio(
        self,
        db: Session,
        diet_type: str,
        allergies: Set[str],
        cuisine: Optional[str] = "indian",
        primary_goal: Optional[str] = "maintain",
        foods_to_avoid: Optional[Set[str]] = None,
        exclude_ingredients: Optional[Set[str]] = None
    ) -> Dict[str, List[FoodItem]]:
        """
        Discover a portfolio of ingredients for the day with strict filtering and scoring.
        """
        exclude_ingredients = exclude_ingredients or set()
        foods_to_avoid = foods_to_avoid or set()
        cuisine = (cuisine or "indian").lower()
        primary_goal = (primary_goal or "maintain").lower()
        
        # 1. Base Query
        base_query = db.query(FoodItem).filter(FoodItem.is_deprecated == False)
        
        # 2. Strict Diet Policy
        diet_filter = []
        if diet_type == "vegan":
            diet_filter = ["vegan"]
        elif diet_type == "vegetarian":
            diet_filter = ["vegan", "vegetarian"]
        elif diet_type == "eggetarian":
            diet_filter = ["vegan", "vegetarian", "eggetarian"]
        elif diet_type == "non-vegetarian":
            diet_filter = ["vegan", "vegetarian", "eggetarian", "non-vegetarian"]

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
        
        # 3. Strict Allergen & Avoidance Policy
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

        # 4. Goal-Based Scoring & Cuisine Prioritization
        scored_candidates = []
        for item in all_allowed_candidates:
            score = 1.0
            name = item.canonical_name.lower()

            # Cuisine prioritization - strict boundary enforcement
            item_cuisines = [c.lower() for c in item.cuisine_tags] if item.cuisine_tags else []

            if item_cuisines:
                # Item has explicit cuisine tags
                if cuisine in item_cuisines:
                    # Matches requested cuisine - strong boost
                    score += 5.0
                else:
                    # Tagged for a DIFFERENT cuisine - heavy penalty
                    score -= 10.0
            # Items with no cuisine tags (generic foods like "Banana", "Oats") stay neutral at score=1.0

            # Diet-type prioritization — rank items by how closely they
            # match the user's chosen diet (e.g. non-veg user prefers meat
            # over egg over dairy over plant).
            priority_map = _DIET_PRIORITY.get(diet_type, {})
            if priority_map:
                tier = _item_diet_tier(item.diet_flags)
                score += priority_map.get(tier, 0)

            # Goal logic prioritization
            macros = item.macros or {}
            protein_pct = (macros.get("protein", 0) * 4) / max(macros.get("calories", 0) or 1, 1)

            if primary_goal == "fat loss":
                if protein_pct > 0.4: score += 1.5
                if "green" in name or "spinach" in name or "lettuce" in name: score += 1.0
            elif primary_goal == "muscle gain":
                if protein_pct > 0.3: score += 2.0
                if macros.get("calories", 0) > 150: score += 0.5

            scored_candidates.append((item, score))
            
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        final_candidates = [x[0] for x in scored_candidates]

        # 5. Categorize and Select
        categorized = {"protein": [], "starch": [], "vegetables": [], "fat": []}
        
        for item in final_candidates:
            name = item.canonical_name.lower()
            macros = item.macros or {}
            protein_pct = (macros.get("protein", 0) * 4) / max(macros.get("calories", 0) or 1, 1)
            
            if protein_pct > 0.25:
                categorized["protein"].append(item)
            elif any(x in name for x in ["rice", "bread", "oats", "quinoa", "potato", "pasta", "tortilla", "poha", "upma", "roti", "paratha", "naan", "pita", "couscous", "bulgur", "orzo", "focaccia", "dalia", "chapati", "idli", "dosa", "puri", "khichdi", "spaghetti", "penne", "risotto", "ciabatta", "gnocchi", "polenta", "tabbouleh"]):
                categorized["starch"].append(item)
            elif any(x in name for x in ["oil", "butter", "avocado", "nut", "seed", "tahini", "ghee", "olive", "pesto", "balsamic", "vinaigrette"]):
                categorized["fat"].append(item)
            else:
                categorized["vegetables"].append(item)

        # 6. Build the selected portfolio
        selected = {}
        for cat, items in categorized.items():
            non_excluded = [it for it in items if it.canonical_name not in exclude_ingredients]
            target_count = 4 
            
            if len(non_excluded) >= target_count:
                selected[cat] = non_excluded[:target_count]
            elif len(non_excluded) > 0:
                selected[cat] = non_excluded
                remaining = target_count - len(non_excluded)
                excluded_items = [it for it in items if it.canonical_name in exclude_ingredients]
                if excluded_items:
                    selected[cat].extend(excluded_items[:remaining])
            else:
                selected[cat] = items[:target_count]

        logger.info(
            f"[DISCOVERY_PORTFOLIO] Discoverd {sum(len(v) for v in selected.values())} "
            f"ingredients for diet={diet_type} goal={primary_goal} cuisine={cuisine}"
        )
        
        return selected

def get_discovery_engine() -> DiscoveryEngine:
    """Get singleton instance"""
    return DiscoveryEngine()
