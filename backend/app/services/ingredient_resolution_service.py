"""
Ingredient Resolution Service - MANDATORY 9-STEP PIPELINE

This service implements the EXACT architecture specified for production-grade resolution.

MANDATORY PIPELINE:
1. Normalization (remove noise) - FIRST, REQUIRED
2. Exact match (fast path)
3. Rule-based canonicalization
4. Category-constrained fuzzy match
5. Category nutrition fallback (SAFE DEFAULT)
6. Canonical LLM (OFFLINE ONLY - NO EVENT LOOP)
7. Hard failure ONLY if truly impossible

CORE PRINCIPLE: LLMs suggest names, ONLY deterministic backend decides nutrition.

CRITICAL RULES:
- AI resolution is NOT allowed inline (no event loop blocking)
- Category fallback PREVENTS 0-calorie plans
- Unknown foods alone must NEVER block plans
- This is the final, correct architecture
"""

import logging
import asyncio
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from .ingredient_normalizer import (
    get_ingredient_normalizer, 
    UnknownIngredientError, 
    NormalizationResult,
    UnresolvedIngredient
)
from .ai_canonical_food_resolver import get_canonical_food_resolver
from .nutrition_database import get_nutrition_database

logger = logging.getLogger(__name__)


from enum import Enum

class ResolutionStatus(Enum):
    """Structured resolution status - NEVER throw exceptions"""
    RESOLVED = "resolved"           # Successfully resolved to known food
    FALLBACK_USED = "fallback_used" # Used generic fallback food
    SKIPPED = "skipped"            # Ingredient skipped, continue plan generation

@dataclass
class ResolutionResult:
    """Result of ingredient resolution with fallback handling - NEVER fails"""
    status: ResolutionStatus
    canonical_name: Optional[str]  # None if skipped
    confidence: str  # "exact", "high", "medium", "low", "generic", "skipped"
    resolution_method: str  # "normalizer", "ai_mapping", "generic_fallback", "skipped"
    warning_message: Optional[str] = None
    original_name: str = ""


class IngredientResolutionService:
    """
    MANDATORY 9-STEP INGREDIENT RESOLUTION PIPELINE
    
    This implements the exact architecture specified for production-grade resolution.
    
    FLOW:
    1. Normalization (remove noise) - handled by normalizer
    2. Exact match (fast path) - handled by normalizer
    3. Rule-based canonicalization - handled by normalizer
    4. Category-constrained fuzzy match - handled by normalizer
    5. Category nutrition fallback - handled by normalizer
    6. Canonical LLM (OFFLINE ONLY) - queued for background processing
    7. Hard failure ONLY if truly impossible
    
    CRITICAL: NO AI CALLS IN EVENT LOOP - all AI resolution is offline/cached
    """
    
    def __init__(self):
        """Initialize resolution service with mandatory pipeline"""
        self.normalizer = get_ingredient_normalizer()
        self.ai_resolver = get_canonical_food_resolver()
        self.nutrition_db = get_nutrition_database()
        
        # AI resolution queue for offline processing (not implemented in this phase)
        self._ai_resolution_queue = []
        
        logger.info("MANDATORY 9-step ingredient resolution service initialized")
    
    async def resolve_ingredient(self, ingredient_name: str) -> ResolutionResult:
        """
        MANDATORY 9-STEP INGREDIENT RESOLUTION PIPELINE
        
        This follows the EXACT architecture specified. The normalizer handles steps 1-5.
        This service only handles the final coordination and AI queuing.
        
        Args:
            ingredient_name: Raw ingredient name
            
        Returns:
            ResolutionResult with status (RESOLVED/FALLBACK_USED/SKIPPED)
        """
        original_name = ingredient_name.strip()
        
        # STEPS 1-5: Handled by normalizer (deterministic, fast)
        try:
            result = self.normalizer.normalize(original_name)
            
            if isinstance(result, NormalizationResult) and result.is_resolved:
                # Successfully resolved by normalizer pipeline
                return ResolutionResult(
                    status=ResolutionStatus.RESOLVED,
                    canonical_name=result.canonical_name,
                    confidence=result.confidence.value,
                    resolution_method=result.transformation_steps[-1] if result.transformation_steps else "normalizer",
                    original_name=original_name
                )
            elif isinstance(result, UnresolvedIngredient):
                # STEP 6: Queue for offline AI resolution (don't block)
                self._queue_for_ai_resolution(original_name, result.category)
                
                # STEP 7: Use category fallback or skip
                if result.suggested_fallback:
                    return ResolutionResult(
                        status=ResolutionStatus.FALLBACK_USED,
                        canonical_name=result.suggested_fallback,
                        confidence="generic",
                        resolution_method="category_fallback",
                        warning_message=f"Used category fallback for '{original_name}'",
                        original_name=original_name
                    )
                else:
                    # Skip ingredient - don't block plan generation
                    return ResolutionResult(
                        status=ResolutionStatus.SKIPPED,
                        canonical_name=None,
                        confidence="skipped",
                        resolution_method="skipped",
                        warning_message=f"Unknown ingredient '{original_name}' skipped - continuing plan generation",
                        original_name=original_name
                    )
            
        except UnknownIngredientError as e:
            # STEP 6: Queue for offline AI resolution
            self._queue_for_ai_resolution(original_name, "unknown")
            
            # STEP 7: Hard failure only if category is completely unknown
            logger.error(f"Hard failure: {e}")
            return ResolutionResult(
                status=ResolutionStatus.SKIPPED,
                canonical_name=None,
                confidence="skipped",
                resolution_method="hard_failure",
                warning_message=f"Unknown ingredient category '{original_name}' - skipped to prevent plan failure",
                original_name=original_name
            )
        except Exception as e:
            # NEVER let exceptions escape - always return a result
            logger.error(f"Unexpected error resolving '{original_name}': {e}")
            return ResolutionResult(
                status=ResolutionStatus.SKIPPED,
                canonical_name=None,
                confidence="skipped",
                resolution_method="error_recovery",
                warning_message=f"Error resolving '{original_name}' - skipped to prevent plan failure",
                original_name=original_name
            )
    
    def _queue_for_ai_resolution(self, ingredient_name: str, category: Optional[str]):
        """
        STEP 6: CANONICAL LLM (OFFLINE ONLY - NO EVENT LOOP)
        
        Queue unknown ingredient for background AI resolution.
        This is exactly how Stripe expands merchant mappings.
        
        Flow:
        Unknown ingredient -> log + queue -> canonical LLM resolves once -> mapping saved permanently
        """
        # Add to queue for background processing
        self._ai_resolution_queue.append({
            "ingredient": ingredient_name,
            "category": category,
            "queued_at": "2026-01-26",  # Would use actual timestamp
            "status": "queued"
        })
        
        logger.info(f"[QUEUED] '{ingredient_name}' queued for offline AI resolution (category: {category})")
        
        # In production, this would trigger a background job
        # For now, we just log the queuing
    
    def get_ai_resolution_queue_stats(self) -> Dict:
        """Get statistics about the AI resolution queue"""
        return {
            "queued_items": len(self._ai_resolution_queue),
            "queue": self._ai_resolution_queue
        }


# Global service instance
_resolution_service = None

def get_ingredient_resolution_service() -> IngredientResolutionService:
    """Get the global ingredient resolution service instance"""
    global _resolution_service
    if _resolution_service is None:
        _resolution_service = IngredientResolutionService()
    return _resolution_service