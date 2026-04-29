"""
ML Ingredient Canonicalizer - Uses sentence transformers for ingredient matching

This module converts raw ingredient names into canonical ingredients from the
nutrition database using ML-based semantic similarity.

CRITICAL RULES:
- NO GenAI usage - only sentence transformers
- Confidence threshold required (≥ 0.85)
- Extract modifiers (cooked, steamed, raw)
- Soft reject on low confidence (warning, not error)
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CanonicalIngredient:
    """Result of ingredient canonicalization"""
    canonical_name: str
    confidence: float
    modifiers: List[str]
    original_name: str


class IngredientCanonicalizerML:
    """ML-based ingredient canonicalizer using sentence transformers"""
    
    # Confidence threshold for accepting matches
    CONFIDENCE_THRESHOLD = 0.85
    
    # Common cooking modifiers to extract
    COOKING_MODIFIERS = [
        "raw", "cooked", "steamed", "boiled", "grilled", "baked",
        "fried", "roasted", "sauteed", "blanched", "poached"
    ]
    
    def __init__(self):
        """Initialize the ML canonicalizer"""
        self.model = None
        self.nutrition_db_ingredients = []
        self.ingredient_embeddings = None
        self._model_loaded = False
        
        logger.info("[ML_CANONICALIZER_INIT] Initializing ML ingredient canonicalizer")
    
    def _load_model(self):
        """Lazy load the sentence transformer model"""
        if self._model_loaded:
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            
            # Use lightweight model optimized for semantic similarity
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            logger.info(f"[ML_MODEL_LOADING] Loading model: {model_name}")
            
            self.model = SentenceTransformer(model_name)
            self._model_loaded = True
            
            logger.info("[ML_MODEL_LOADED] Sentence transformer model loaded successfully")
            
        except ImportError:
            logger.error("[ML_MODEL_ERROR] sentence-transformers not installed")
            raise RuntimeError(
                "sentence-transformers package required for ML canonicalizer. "
                "Install with: pip install sentence-transformers"
            )
        except Exception as e:
            logger.error(f"[ML_MODEL_ERROR] Failed to load model: {e}")
            raise RuntimeError(f"Failed to load sentence transformer model: {e}")
    
    def _load_nutrition_db_ingredients(self, nutrition_db_ingredients: List[str]):
        """Load and embed nutrition database ingredients"""
        if not nutrition_db_ingredients:
            logger.warning("[ML_CANONICALIZER_WARNING] Empty nutrition database provided")
            return
        
        self.nutrition_db_ingredients = nutrition_db_ingredients
        
        # Lazy load model
        self._load_model()
        
        # Generate embeddings for all nutrition DB ingredients
        logger.info(f"[ML_EMBEDDING_START] Generating embeddings for {len(nutrition_db_ingredients)} ingredients")
        
        self.ingredient_embeddings = self.model.encode(
            nutrition_db_ingredients,
            convert_to_tensor=True,
            show_progress_bar=False
        )
        
        logger.info("[ML_EMBEDDING_COMPLETE] Ingredient embeddings generated")
    
    def _extract_modifiers(self, ingredient_name: str) -> Tuple[str, List[str]]:
        """
        Extract cooking modifiers from ingredient name.
        
        Args:
            ingredient_name: Raw ingredient name
            
        Returns:
            Tuple of (cleaned_name, modifiers_list)
        """
        ingredient_lower = ingredient_name.lower().strip()
        found_modifiers = []
        
        # Extract modifiers
        for modifier in self.COOKING_MODIFIERS:
            if modifier in ingredient_lower:
                found_modifiers.append(modifier)
                # Remove modifier from name
                ingredient_lower = ingredient_lower.replace(modifier, "").strip()
        
        # Clean up extra spaces
        cleaned_name = re.sub(r'\s+', ' ', ingredient_lower).strip()
        
        return cleaned_name, found_modifiers
    
    def canonicalize(
        self,
        raw_ingredient_name: str,
        nutrition_db_ingredients: Optional[List[str]] = None
    ) -> CanonicalIngredient:
        """
        Canonicalize a raw ingredient name using ML semantic similarity.
        
        Args:
            raw_ingredient_name: Raw ingredient name from user/LLM
            nutrition_db_ingredients: List of canonical ingredients from nutrition DB
            
        Returns:
            CanonicalIngredient with match details
            
        Raises:
            RuntimeError: If model loading fails
        """
        request_id = f"canon_{raw_ingredient_name[:20]}"
        logger.info(f"[ING_CANONICALIZE_START] request_id={request_id} ingredient='{raw_ingredient_name}'")
        
        # Load nutrition DB if provided
        if nutrition_db_ingredients and not self.ingredient_embeddings:
            self._load_nutrition_db_ingredients(nutrition_db_ingredients)
        
        if not self.ingredient_embeddings:
            logger.error("[ML_CANONICALIZER_ERROR] No nutrition database loaded")
            raise RuntimeError("Nutrition database not loaded for canonicalization")
        
        # Extract modifiers
        cleaned_name, modifiers = self._extract_modifiers(raw_ingredient_name)
        
        logger.info(f"[ING_MODIFIERS_EXTRACTED] request_id={request_id} cleaned='{cleaned_name}' modifiers={modifiers}")
        
        # Lazy load model
        self._load_model()
        
        # Generate embedding for input ingredient
        input_embedding = self.model.encode(
            [cleaned_name],
            convert_to_tensor=True,
            show_progress_bar=False
        )
        
        # Calculate cosine similarity with all nutrition DB ingredients
        from sentence_transformers import util
        
        similarities = util.cos_sim(input_embedding, self.ingredient_embeddings)[0]
        
        # Find best match
        best_match_idx = similarities.argmax().item()
        best_confidence = similarities[best_match_idx].item()
        best_match_name = self.nutrition_db_ingredients[best_match_idx]
        
        logger.info(
            f"[ING_MATCH_FOUND] request_id={request_id} "
            f"canonical='{best_match_name}' confidence={best_confidence:.3f}"
        )
        
        # Check confidence threshold
        if best_confidence < self.CONFIDENCE_THRESHOLD:
            logger.warning(
                f"[ING_CANONICAL_LOW_CONFIDENCE] request_id={request_id} "
                f"confidence={best_confidence:.3f} < threshold={self.CONFIDENCE_THRESHOLD}"
            )
        else:
            logger.info(f"[ING_CANONICALIZED] request_id={request_id} confidence={best_confidence:.3f} ✓")
        
        return CanonicalIngredient(
            canonical_name=best_match_name,
            confidence=best_confidence,
            modifiers=modifiers,
            original_name=raw_ingredient_name
        )
    
    def canonicalize_batch(
        self,
        raw_ingredient_names: List[str],
        nutrition_db_ingredients: Optional[List[str]] = None
    ) -> List[CanonicalIngredient]:
        """
        Canonicalize multiple ingredients in batch for efficiency.
        
        Args:
            raw_ingredient_names: List of raw ingredient names
            nutrition_db_ingredients: List of canonical ingredients from nutrition DB
            
        Returns:
            List of CanonicalIngredient results
        """
        logger.info(f"[ING_BATCH_CANONICALIZE_START] count={len(raw_ingredient_names)}")
        
        results = []
        for raw_name in raw_ingredient_names:
            try:
                result = self.canonicalize(raw_name, nutrition_db_ingredients)
                results.append(result)
            except Exception as e:
                logger.error(f"[ING_CANONICALIZE_ERROR] ingredient='{raw_name}' error={e}")
                # Create low-confidence result for failed canonicalization
                results.append(CanonicalIngredient(
                    canonical_name=raw_name,
                    confidence=0.0,
                    modifiers=[],
                    original_name=raw_name
                ))
        
        logger.info(f"[ING_BATCH_CANONICALIZE_COMPLETE] count={len(results)}")
        return results


# Singleton instance
_canonicalizer_ml: Optional[IngredientCanonicalizerML] = None


def get_ingredient_canonicalizer_ml() -> IngredientCanonicalizerML:
    """Get singleton instance of ML ingredient canonicalizer"""
    global _canonicalizer_ml
    if _canonicalizer_ml is None:
        _canonicalizer_ml = IngredientCanonicalizerML()
    return _canonicalizer_ml
