"""
AI Canonical Food Resolver - SINGLE PURPOSE ONLY

This module does ONE job: rename unknown foods to known foods.

CRITICAL RULES:
1. AI ONLY renames foods - NO nutrition calculations
2. AI ONLY chooses from provided known foods - NO invention
3. Backend decides acceptance based on confidence - NOT AI
4. All nutrition calculations MUST use existing nutrition database
5. This is an additive safety layer - NOT a refactor

FLOW:
Unknown ingredient -> AI maps to known food -> Backend validates -> Cache result
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

from app.services.ai_provider_manager import get_provider_manager

logger = logging.getLogger(__name__)


@dataclass
class CanonicalMapping:
    """Result of AI canonical food resolution"""
    canonical_food: str  # Known food name OR "UNRESOLVED"
    confidence: float    # 0.0 to 1.0
    original_food: str   # Original unknown food name


class ConfidenceLevel(Enum):
    """Confidence-based action levels"""
    HIGH = "high"        # ≥ 0.7 - Accept mapping
    MEDIUM = "medium"    # 0.4-0.69 - Accept with warning  
    LOW = "low"          # < 0.4 - Reject mapping


class AICanonicalFoodResolver:
    """
    AI service for mapping unknown foods to known foods ONLY.
    
    RESPONSIBILITIES (STRICTLY LIMITED):
    1. Map unknown ingredient names to known database foods
    2. Return confidence score for backend decision-making
    3. Cache successful mappings for performance
    
    NOT RESPONSIBLE FOR:
    - Nutrition calculations (nutrition database handles this)
    - Acceptance decisions (backend validates confidence)
    - Food invention (only chooses from provided known foods)
    """
    
    def __init__(self):
        """Initialize resolver with provider manager and cache"""
        self.provider_manager = get_provider_manager()
        self._mapping_cache = {}  # Cache for resolved mappings
        
        logger.info("AI Canonical Food Resolver initialized")
    
    async def resolve_unknown_food(
        self, 
        unknown_food: str, 
        known_foods: List[str],
        max_suggestions: int = 10
    ) -> CanonicalMapping:
        """
        Resolve unknown food to known food using AI.
        
        Args:
            unknown_food: The unknown ingredient name
            known_foods: List of known foods from nutrition database
            max_suggestions: Maximum number of known foods to present to AI
            
        Returns:
            CanonicalMapping with AI's suggestion and confidence
            
        Raises:
            Exception: If AI resolution fails
        """
        # Check cache first (faster, cheaper, deterministic)
        cache_key = unknown_food.lower().strip()
        if cache_key in self._mapping_cache:
            cached_result = self._mapping_cache[cache_key]
            logger.info(f"[CACHE HIT] '{unknown_food}' -> '{cached_result.canonical_food}' "
                       f"(confidence: {cached_result.confidence:.2f})")
            return cached_result
        
        # Limit known foods to prevent prompt bloat
        limited_known_foods = known_foods[:max_suggestions]
        
        # Get AI mapping
        mapping = await self._get_ai_mapping(unknown_food, limited_known_foods)
        
        # Cache successful mappings (confidence ≥ 0.4)
        if mapping.confidence >= 0.4:
            self._mapping_cache[cache_key] = mapping
            logger.info(f"[CACHED] '{unknown_food}' -> '{mapping.canonical_food}' "
                       f"(confidence: {mapping.confidence:.2f})")
        
        return mapping
    
    async def _get_ai_mapping(self, unknown_food: str, known_foods: List[str]) -> CanonicalMapping:
        """Get AI mapping for unknown food to known foods"""
        
        system_prompt = self._get_system_prompt()
        user_prompt = self._get_mapping_prompt(unknown_food, known_foods)
        
        logger.info(f"Resolving unknown food: '{unknown_food}' using AI")
        
        # Use provider manager for reliable AI calls
        retry_result = await self.provider_manager.generate_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            preferred_provider=None  # Use any available provider
        )
        
        if not retry_result.success:
            logger.error(f"AI resolution failed: {retry_result.failure_reason}")
            # CRITICAL: Do NOT retry ingredient resolution failures
            # Return UNRESOLVED mapping immediately
            return CanonicalMapping(
                canonical_food="UNRESOLVED",
                confidence=0.0,
                original_food=unknown_food
            )
        
        # Parse AI response
        try:
            response_data = json.loads(retry_result.content.strip())
            
            # Validate response structure
            if not isinstance(response_data, dict):
                raise ValueError("Response is not a JSON object")
            
            canonical_food = response_data.get("canonical_food", "UNRESOLVED")
            confidence = float(response_data.get("confidence", 0.0))
            
            # Validate confidence range
            confidence = max(0.0, min(1.0, confidence))
            
            # CRITICAL: Validate canonical_food exists in database
            if canonical_food != "UNRESOLVED":
                if canonical_food not in known_foods:
                    logger.warning(f"AI suggested unknown food '{canonical_food}', marking as UNRESOLVED")
                    canonical_food = "UNRESOLVED"
                    confidence = 0.0
                else:
                    # Double-check: ensure it's an exact match (no new names generated)
                    if canonical_food not in known_foods:
                        logger.error(f"SAFETY VIOLATION: AI attempted to create new canonical name '{canonical_food}'")
                        canonical_food = "UNRESOLVED"
                        confidence = 0.0
            
            mapping = CanonicalMapping(
                canonical_food=canonical_food,
                confidence=confidence,
                original_food=unknown_food
            )
            
            logger.info(f"[AI RESOLVED] '{unknown_food}' -> '{canonical_food}' "
                       f"(confidence: {confidence:.2f})")
            
            return mapping
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.error(f"Raw AI response: {retry_result.content}")
            
            # Return UNRESOLVED mapping
            return CanonicalMapping(
                canonical_food="UNRESOLVED",
                confidence=0.0,
                original_food=unknown_food
            )
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI canonical food resolution"""
        return """You are a food name resolver for WellnessWay Diet Planner.

ROLE: Map unknown food names to known foods ONLY.

CRITICAL RULES:
1. You ONLY rename foods - NO nutrition calculations
2. You ONLY choose from the provided known foods list
3. You NEVER invent new foods
4. You NEVER calculate calories, protein, or macros
5. You NEVER bypass database validation

TASK:
- Look at the unknown food name
- Find the closest match from the known foods list
- Return confidence score (0.0 to 1.0)
- If no good match exists, return "UNRESOLVED"

OUTPUT: Valid JSON only. No explanations."""
    
    def _get_mapping_prompt(self, unknown_food: str, known_foods: List[str]) -> str:
        """Get mapping prompt for specific unknown food"""
        
        known_foods_list = "\n".join([f"- {food}" for food in known_foods])
        
        return f"""Unknown food: "{unknown_food}"

Choose the CLOSEST match from these known foods:
{known_foods_list}

Return JSON only:
{{
  "canonical_food": "exact_name_from_list_above OR UNRESOLVED",
  "confidence": 0.85
}}

RULES:
- Use EXACT name from the list above
- confidence 0.9+ = very similar (e.g., "wheat wrap" -> "whole wheat roti")
- confidence 0.7-0.8 = similar category (e.g., "flatbread" -> "whole wheat roti")  
- confidence 0.4-0.6 = same food group (e.g., "protein bar" -> "whey protein powder")
- confidence < 0.4 = use "UNRESOLVED"

No explanations. JSON only."""
    
    def get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Get confidence level for backend decision making"""
        if confidence >= 0.7:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.4:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def should_accept_mapping(self, confidence: float) -> bool:
        """Backend decision: should we accept this mapping?"""
        return confidence >= 0.4  # Accept medium and high confidence
    
    def clear_cache(self):
        """Clear the mapping cache (for testing/debugging)"""
        self._mapping_cache.clear()
        logger.info("Mapping cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "cached_mappings": len(self._mapping_cache),
            "cache_keys": list(self._mapping_cache.keys())
        }


# Global resolver instance
_canonical_resolver = None

def get_canonical_food_resolver() -> AICanonicalFoodResolver:
    """Get the global AI canonical food resolver instance"""
    global _canonical_resolver
    if _canonical_resolver is None:
        _canonical_resolver = AICanonicalFoodResolver()
    return _canonical_resolver