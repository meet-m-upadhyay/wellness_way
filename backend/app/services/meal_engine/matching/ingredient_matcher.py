"""
Cascading ingredient matcher for the v2 meal engine.

4-stage resolution:
  1. Exact name match (case-insensitive)
  2. Alias match (search_aliases array)
  3. Fuzzy match (rapidfuzz against names + aliases, threshold 0.6)
  4. Embedding match (pgvector cosine similarity, threshold 0.75)

Also checks canonical_foods.json for ambiguous common terms.
Logs low-confidence matches (<0.8) for manual review.
"""

import logging
from dataclasses import dataclass
from typing import Optional, List, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.meal_engine.config.loader import ConfigLoader

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Result of an ingredient match attempt."""
    ingredient_code: Optional[str]
    ingredient_name: str
    match_method: str       # "exact", "alias", "canonical", "fuzzy", "embedding", "none"
    confidence: float       # 0.0 - 1.0

    @property
    def found(self) -> bool:
        return self.ingredient_code is not None


class IngredientMatcher:
    """Cascading matcher: exact → alias → canonical → fuzzy → embedding."""

    # In-memory cache of (name, aliases) for fuzzy matching
    _name_cache: Optional[List[Tuple[str, str, list]]] = None  # [(code, name, aliases)]

    def __init__(self, db: Session, config: Optional[ConfigLoader] = None):
        self._db = db
        self._config = config or ConfigLoader()

    @staticmethod
    def _clean_llm_name(name: str) -> str:
        """Strip grams, quantities, and units from LLM output names.

        'Naan, cooked, 100g' -> 'naan, cooked'
        'Butter, 10g' -> 'butter'
        'Rice, raw, 80 g' -> 'rice, raw'
        """
        import re
        cleaned = name.strip().lower()
        # Remove trailing quantity+unit patterns: ", 100g", ", 80 g", ", 2 cups"
        cleaned = re.sub(r',?\s*\d+\.?\d*\s*(g|gm|grams?|ml|kg|cups?|tbsp|tsp|katori|pieces?)\s*$', '', cleaned)
        # Remove leading quantity: "2 rotis" -> "rotis"
        cleaned = re.sub(r'^\d+\.?\d*\s+(g|gm|grams?\s+of\s+)?', '', cleaned)
        return cleaned.strip().rstrip(',').strip()

    async def match(self, llm_name: str) -> MatchResult:
        """Resolve an LLM-output ingredient name to a v2_ingredients entry.

        Args:
            llm_name: Ingredient name as output by the LLM.

        Returns:
            MatchResult with code, name, method, confidence.
        """
        query = self._clean_llm_name(llm_name)
        if not query:
            return MatchResult(None, llm_name, "none", 0.0)

        # Stage 1: Exact name match
        row = self._exact_match(query)
        if row:
            return MatchResult(row[0], row[1], "exact", 1.0)

        # Stage 2: Alias match
        row = self._alias_match(query)
        if row:
            return MatchResult(row[0], row[1], "alias", 0.95)

        # Stage 3: Canonical defaults (for common ambiguous terms)
        row = self._canonical_match(query)
        if row:
            result = MatchResult(row[0], row[1], "canonical", 0.90)
            canonical_entry = self._find_canonical_entry(query)
            if canonical_entry and canonical_entry.get("ambiguous"):
                logger.info("Ambiguous canonical match: '%s' -> %s (multiple IFCT entries exist)", llm_name, row[1])
            return result

        # Stage 4: Fuzzy match (rapidfuzz)
        result = self._fuzzy_match(query)
        if result:
            code, name, score = result
            confidence = score / 100.0  # rapidfuzz returns 0-100
            if confidence >= 0.6:
                if confidence < 0.8:
                    logger.info("Low-confidence fuzzy match: '%s' -> %s (%.1f%%) — review candidate", llm_name, name, score)
                return MatchResult(code, name, "fuzzy", confidence)

        # Stage 5: Embedding match (pgvector)
        result = self._embedding_match(query)
        if result:
            code, name, similarity = result
            if similarity >= 0.75:
                if similarity < 0.8:
                    logger.info("Low-confidence embedding match: '%s' -> %s (%.3f) — review candidate", llm_name, name, similarity)
                return MatchResult(code, name, "embedding", similarity)

        # No match
        logger.warning("No match found for ingredient: '%s'", llm_name)
        return MatchResult(None, llm_name, "none", 0.0)

    def _exact_match(self, query: str) -> Optional[Tuple[str, str]]:
        """Stage 1: Exact case-insensitive name match."""
        row = self._db.execute(
            text("SELECT code, name FROM v2_ingredients WHERE LOWER(name) = :q LIMIT 1"),
            {"q": query},
        ).fetchone()
        return (row.code, row.name) if row else None

    def _alias_match(self, query: str) -> Optional[Tuple[str, str]]:
        """Stage 2: Match against search_aliases array."""
        row = self._db.execute(
            text("SELECT code, name FROM v2_ingredients WHERE :q = ANY(search_aliases) LIMIT 1"),
            {"q": query},
        ).fetchone()
        return (row.code, row.name) if row else None

    def _canonical_match(self, query: str) -> Optional[Tuple[str, str]]:
        """Stage 3: Check canonical_foods.json for a default."""
        entry = self._find_canonical_entry(query)
        if not entry or not entry.get("default_code"):
            return None

        row = self._db.execute(
            text("SELECT code, name FROM v2_ingredients WHERE code = :c LIMIT 1"),
            {"c": entry["default_code"]},
        ).fetchone()
        return (row.code, row.name) if row else None

    def _find_canonical_entry(self, query: str) -> Optional[dict]:
        """Find the canonical_foods entry for a query."""
        canonical = self._config.canonical_foods
        # Direct key match
        if query in canonical and isinstance(canonical[query], dict):
            return canonical[query]
        # Partial match: "chicken breast" checks if "chicken" is a key
        for key, entry in canonical.items():
            if not isinstance(entry, dict):
                continue
            if key in query or query in key:
                return entry
        return None

    def _fuzzy_match(self, query: str) -> Optional[Tuple[str, str, float]]:
        """Stage 4: Fuzzy string match using rapidfuzz."""
        from rapidfuzz import fuzz

        # Load name cache if not present
        if IngredientMatcher._name_cache is None:
            self._load_name_cache()

        best_code = None
        best_name = None
        best_score = 0.0

        for code, name, aliases in IngredientMatcher._name_cache:
            # Check against primary name
            score = fuzz.ratio(query, name.lower())
            if score > best_score:
                best_score = score
                best_code = code
                best_name = name

            # Check against aliases (but don't check all — limit for performance)
            for alias in aliases[:5]:
                score = fuzz.ratio(query, alias)
                if score > best_score:
                    best_score = score
                    best_code = code
                    best_name = name

        if best_score >= 60:  # threshold 0.6 (rapidfuzz uses 0-100)
            return (best_code, best_name, best_score)
        return None

    # Class-level embedding model cache (load once, reuse)
    _embedding_model = None

    def _embedding_match(self, query: str) -> Optional[Tuple[str, str, float]]:
        """Stage 5: Semantic match via pgvector nearest neighbor."""
        try:
            # Lazy import + singleton model (avoid reloading 90MB per call)
            if IngredientMatcher._embedding_model is None:
                from sentence_transformers import SentenceTransformer
                IngredientMatcher._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

            query_vec = IngredientMatcher._embedding_model.encode(query, normalize_embeddings=True)
            vec_str = "[" + ",".join(str(float(x)) for x in query_vec) + "]"

            row = self._db.execute(
                text("""
                    SELECT vi.code, vi.name,
                           1 - (vie.embedding <=> CAST(:vec AS vector)) AS similarity
                    FROM v2_ingredient_embeddings vie
                    JOIN v2_ingredients vi ON vi.id = vie.ingredient_id
                    ORDER BY vie.embedding <=> CAST(:vec AS vector)
                    LIMIT 1
                """),
                {"vec": vec_str},
            ).fetchone()

            if row and row.similarity >= 0.75:
                return (row.code, row.name, float(row.similarity))

        except ImportError:
            logger.debug("sentence-transformers not available for embedding match")
        except Exception as e:
            logger.warning("Embedding match failed: %s", e)

        return None

    def _load_name_cache(self):
        """Load all ingredient names + aliases into memory for fuzzy matching."""
        rows = self._db.execute(
            text("SELECT code, name, search_aliases FROM v2_ingredients")
        ).fetchall()
        IngredientMatcher._name_cache = [
            (row.code, row.name, row.search_aliases or []) for row in rows
        ]
        logger.debug("Loaded %d ingredients into fuzzy match cache", len(rows))

    @classmethod
    def clear_cache(cls):
        """Clear the in-memory name cache (e.g., after re-seeding)."""
        cls._name_cache = None
