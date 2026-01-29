"""
Canonical AI Food Resolver - Async Background Resolution

This service handles AI-based ingredient resolution in the background,
never blocking the event loop. This is exactly how Stripe expands merchant mappings.

CRITICAL RULES:
- NEVER runs inline inside request loop
- NEVER blocks user requests  
- All AI calls are queued for background processing
- Results are cached permanently
- Provides canonical food mappings for unknown ingredients
"""

import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class CanonicalMapping:
    """Result of canonical AI resolution"""
    original_ingredient: str
    canonical_food: str
    confidence: float  # 0.0 to 1.0
    nutrition_basis: str  # "USDA-equivalent", "category-average", etc.
    notes: str
    created_at: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            "original_ingredient": self.original_ingredient,
            "canonical_food": self.canonical_food,
            "confidence": self.confidence,
            "nutrition_basis": self.nutrition_basis,
            "notes": self.notes,
            "created_at": self.created_at.isoformat()
        }


class CanonicalAIResolver:
    """
    Async canonical AI food resolver - NEVER blocks event loop
    
    This implements the exact pattern used by Stripe for merchant mapping:
    Unknown merchant -> log + queue -> AI resolves once -> mapping saved permanently
    
    Our version:
    Unknown ingredient -> log + queue -> AI resolves once -> mapping saved permanently
    """
    
    def __init__(self):
        """Initialize canonical AI resolver"""
        self.resolution_queue = []
        self.cached_mappings = {}  # In production, this would be a database
        self.processing_lock = asyncio.Lock()
        
        logger.info("Canonical AI resolver initialized (async, non-blocking)")
    
    async def queue_for_resolution(self, ingredient_name: str, category: Optional[str] = None):
        """
        Queue ingredient for background AI resolution - NEVER blocks
        
        Args:
            ingredient_name: Unknown ingredient to resolve
            category: Optional category hint for better resolution
        """
        # Check if already cached
        if ingredient_name.lower() in self.cached_mappings:
            logger.info(f"[CACHED] '{ingredient_name}' already resolved")
            return
        
        # Add to queue for background processing
        queue_item = {
            "ingredient": ingredient_name,
            "category": category,
            "queued_at": datetime.now(),
            "status": "queued",
            "attempts": 0
        }
        
        self.resolution_queue.append(queue_item)
        logger.info(f"[QUEUED] '{ingredient_name}' queued for AI resolution (category: {category})")
        
        # In production, this would trigger a background job/worker
        # For now, we simulate the queuing
    
    async def get_cached_mapping(self, ingredient_name: str) -> Optional[CanonicalMapping]:
        """
        Get cached canonical mapping if available
        
        Args:
            ingredient_name: Ingredient to look up
            
        Returns:
            CanonicalMapping if cached, None otherwise
        """
        cached = self.cached_mappings.get(ingredient_name.lower())
        if cached:
            logger.info(f"[CACHE HIT] '{ingredient_name}' -> '{cached.canonical_food}'")
            return cached
        
        return None
    
    async def simulate_ai_resolution(self, ingredient_name: str, category: Optional[str] = None) -> CanonicalMapping:
        """
        Simulate AI resolution for demonstration purposes
        
        In production, this would call the actual AI service with prompts like:
        "Map the ingredient 'whole wheat wrap' to the closest canonical food in our database.
         Available foods: [list of database foods]
         Category hint: grains
         Return: canonical_food_name, confidence_score, reasoning"
        
        Args:
            ingredient_name: Ingredient to resolve
            category: Category hint
            
        Returns:
            CanonicalMapping with AI resolution result
        """
        # Simulate AI mapping logic
        mappings = {
            "whole wheat wrap": {
                "canonical_food": "whole wheat roti",
                "confidence": 0.85,
                "nutrition_basis": "USDA-equivalent",
                "notes": "Mapped whole wheat wrap to whole wheat roti (similar flatbread)"
            },
            "hemp seeds": {
                "canonical_food": "hemp seeds",
                "confidence": 0.95,
                "nutrition_basis": "exact-match",
                "notes": "Direct match found in database"
            },
            "trader joe's wrap": {
                "canonical_food": "whole wheat roti", 
                "confidence": 0.80,
                "nutrition_basis": "brand-normalized",
                "notes": "Removed brand name, mapped to whole wheat roti"
            },
            "mixed berries": {
                "canonical_food": "berries (mixed)",
                "confidence": 0.90,
                "nutrition_basis": "exact-match",
                "notes": "Direct match found in database"
            }
        }
        
        # Default fallback based on category
        if ingredient_name.lower() not in mappings and category:
            category_fallbacks = {
                "seeds": ("seeds (generic)", 0.60, "category-average"),
                "nuts": ("nuts (generic)", 0.60, "category-average"),
                "vegetables": ("vegetables (generic)", 0.60, "category-average"),
                "legumes": ("legumes (generic)", 0.60, "category-average"),
                "grains": ("grains (generic)", 0.60, "category-average"),
                "dairy": ("greek yogurt (plain)", 0.60, "category-representative"),
                "fruits": ("banana", 0.60, "category-representative")
            }
            
            if category in category_fallbacks:
                canonical, confidence, basis = category_fallbacks[category]
                return CanonicalMapping(
                    original_ingredient=ingredient_name,
                    canonical_food=canonical,
                    confidence=confidence,
                    nutrition_basis=basis,
                    notes=f"AI mapped unknown {category} to category fallback",
                    created_at=datetime.now()
                )
        
        # Use specific mapping if available
        if ingredient_name.lower() in mappings:
            mapping_data = mappings[ingredient_name.lower()]
            return CanonicalMapping(
                original_ingredient=ingredient_name,
                canonical_food=mapping_data["canonical_food"],
                confidence=mapping_data["confidence"],
                nutrition_basis=mapping_data["nutrition_basis"],
                notes=mapping_data["notes"],
                created_at=datetime.now()
            )
        
        # Final fallback - use generic category
        return CanonicalMapping(
            original_ingredient=ingredient_name,
            canonical_food="vegetables (generic)",  # Safe default
            confidence=0.40,
            nutrition_basis="generic-fallback",
            notes=f"AI could not resolve '{ingredient_name}', using generic fallback",
            created_at=datetime.now()
        )
    
    async def process_resolution_queue(self, max_items: int = 5):
        """
        Process items from the resolution queue - background job simulation
        
        In production, this would be called by a background worker/cron job
        
        Args:
            max_items: Maximum items to process in this batch
        """
        async with self.processing_lock:
            processed = 0
            
            for item in self.resolution_queue[:max_items]:
                if item["status"] != "queued":
                    continue
                
                try:
                    # Mark as processing
                    item["status"] = "processing"
                    item["attempts"] += 1
                    
                    # Simulate AI resolution
                    mapping = await self.simulate_ai_resolution(
                        item["ingredient"], 
                        item["category"]
                    )
                    
                    # Cache the result
                    self.cached_mappings[item["ingredient"].lower()] = mapping
                    
                    # Mark as completed
                    item["status"] = "completed"
                    item["completed_at"] = datetime.now()
                    
                    logger.info(f"[AI RESOLVED] '{item['ingredient']}' -> '{mapping.canonical_food}' "
                               f"(confidence: {mapping.confidence:.2f})")
                    
                    processed += 1
                    
                except Exception as e:
                    # Mark as failed
                    item["status"] = "failed"
                    item["error"] = str(e)
                    logger.error(f"[AI FAILED] Failed to resolve '{item['ingredient']}': {e}")
            
            # Remove completed/failed items from queue
            self.resolution_queue = [
                item for item in self.resolution_queue 
                if item["status"] in ["queued", "processing"]
            ]
            
            logger.info(f"[BATCH COMPLETE] Processed {processed} items, {len(self.resolution_queue)} remaining in queue")
    
    def get_queue_stats(self) -> Dict:
        """Get statistics about the resolution queue"""
        stats = {
            "queued_items": len([item for item in self.resolution_queue if item["status"] == "queued"]),
            "processing_items": len([item for item in self.resolution_queue if item["status"] == "processing"]),
            "cached_mappings": len(self.cached_mappings),
            "total_queue_size": len(self.resolution_queue)
        }
        
        return stats
    
    def get_cached_mappings(self) -> Dict[str, CanonicalMapping]:
        """Get all cached mappings for inspection"""
        return self.cached_mappings.copy()


# Global resolver instance
_canonical_resolver = None

def get_canonical_ai_resolver() -> CanonicalAIResolver:
    """Get the global canonical AI resolver instance"""
    global _canonical_resolver
    if _canonical_resolver is None:
        _canonical_resolver = CanonicalAIResolver()
    return _canonical_resolver