"""
Cascading ingredient matcher for the v2 meal engine.

5-stage resolution (raw-ingredient model):
  1. Exact name match (case-insensitive)
  2. Alias match (search_aliases array)
  3. Canonical match (canonical_foods.json defaults)
  4. Fuzzy match (rapidfuzz, threshold 0.85, form-filtered)
  5. Embedding match (pgvector cosine similarity, threshold 0.75, 2s timeout)

All ingredients are raw by contract (LLM prompt enforces this).
Fuzzy and embedding tiers filter for form IN ('raw', 'unspecified', NULL).
"""

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.meal_engine.config.loader import ConfigLoader

logger = logging.getLogger(__name__)

# Forms compatible with raw/as-purchased ingredients.
# 'prepared' covers oils, ghee, paneer, curd (bought as-is, not home-cooked).
# 'fresh' covers vegetables, fruits, milk (as-purchased from market).
_RAW_COMPATIBLE_FORMS = {'raw', 'unspecified', 'dry_ingredient', 'prepared', 'fresh', None}

# Embedding match hard timeout (seconds)
_EMBEDDING_TIMEOUT_S = 2.0


@dataclass
class MatchResult:
    """Result of an ingredient match attempt."""
    ingredient_code: Optional[str]
    ingredient_name: str
    match_method: str       # "exact", "alias", "canonical", "fuzzy", "embedding", "none"
    confidence: float       # 0.0 - 1.0
    tiers_tried: List[str] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return self.ingredient_code is not None


class IngredientMatcher:
    """Cascading matcher: exact → alias → canonical → fuzzy → embedding."""

    # In-memory cache: [(code, name, aliases, form)]
    _name_cache: Optional[List[Tuple[str, str, list, Optional[str]]]] = None

    def __init__(self, db: Session, config: Optional[ConfigLoader] = None):
        self._db = db
        self._config = config or ConfigLoader()

    @staticmethod
    def _clean_llm_name(name: str) -> str:
        """Normalize LLM ingredient name for matching.

        Raw-by-contract: no cooked/raw suffix stripping needed.
        Just lowercase and strip whitespace.
        """
        return name.strip().lower()

    async def match(self, llm_name: str) -> MatchResult:
        """Resolve a raw ingredient name to a v2_ingredients entry.

        Returns MatchResult with code, name, method, confidence, tiers_tried.
        """
        query = self._clean_llm_name(llm_name)
        if not query:
            return MatchResult(None, llm_name, "none", 0.0, tiers_tried=[])

        tiers_tried = []

        # Stage 1: Exact name match
        tiers_tried.append("exact")
        row = self._exact_match(query)
        if row:
            return MatchResult(row[0], row[1], "exact", 1.0, tiers_tried=tiers_tried)

        # Stage 2: Alias match
        tiers_tried.append("alias")
        row = self._alias_match(query)
        if row:
            return MatchResult(row[0], row[1], "alias", 0.95, tiers_tried=tiers_tried)

        # Stage 3: Canonical defaults
        tiers_tried.append("canonical")
        row = self._canonical_match(query)
        if row:
            result = MatchResult(row[0], row[1], "canonical", 0.90, tiers_tried=tiers_tried)
            canonical_entry = self._find_canonical_entry(query)
            if canonical_entry and canonical_entry.get("ambiguous"):
                logger.info("Ambiguous canonical match: '%s' -> %s (multiple IFCT entries exist)", llm_name, row[1])
            return result

        # Stage 4: Fuzzy match (form-filtered, threshold 0.85)
        tiers_tried.append("fuzzy")
        result = self._fuzzy_match(query)
        if result:
            code, name, score = result
            confidence = score / 100.0
            if confidence >= 0.85:
                return MatchResult(code, name, "fuzzy", confidence, tiers_tried=tiers_tried)

        # Stage 5: Embedding match (form-filtered, 2s timeout)
        tiers_tried.append("embedding")
        result = self._embedding_match(query)
        if result:
            code, name, similarity = result
            if similarity >= 0.75:
                if similarity < 0.8:
                    logger.info("Low-confidence embedding match: '%s' -> %s (%.3f) — review candidate", llm_name, name, similarity)
                return MatchResult(code, name, "embedding", similarity, tiers_tried=tiers_tried)

        # No match
        logger.warning("No match found for ingredient: '%s'", llm_name)
        return MatchResult(None, llm_name, "none", 0.0, tiers_tried=tiers_tried)

    # --- Stage implementations ---

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
        if query in canonical and isinstance(canonical[query], dict):
            return canonical[query]
        for key, entry in canonical.items():
            if not isinstance(entry, dict):
                continue
            if key in query or query in key:
                return entry
        return None

    def _fuzzy_match(self, query: str) -> Optional[Tuple[str, str, float]]:
        """Stage 4: Fuzzy string match using rapidfuzz.

        Only considers entries with raw-compatible form.
        """
        from rapidfuzz import fuzz

        if IngredientMatcher._name_cache is None:
            self._load_name_cache()

        best_code = None
        best_name = None
        best_score = 0.0

        for code, name, aliases, form in IngredientMatcher._name_cache:
            # Form filter: only match raw-compatible entries
            if form not in _RAW_COMPATIBLE_FORMS:
                continue

            score = fuzz.ratio(query, name.lower())
            if score > best_score:
                best_score = score
                best_code = code
                best_name = name

            for alias in aliases[:5]:
                score = fuzz.ratio(query, alias)
                if score > best_score:
                    best_score = score
                    best_code = code
                    best_name = name

        if best_score >= 85:
            return (best_code, best_name, best_score)
        return None

    # Class-level embedding model cache (load once, reuse)
    _embedding_model = None

    def _embedding_match(self, query: str) -> Optional[Tuple[str, str, float]]:
        """Stage 5: Semantic match via pgvector nearest neighbor.

        Uses HNSW index for fast cosine similarity.
        Hard timeout of 2 seconds — aborts and falls through if exceeded.
        Form-filtered: only considers raw-compatible IFCT entries.
        """
        try:
            t_start = time.perf_counter()

            # Lazy import + singleton model
            if IngredientMatcher._embedding_model is None:
                t0 = time.perf_counter()
                from sentence_transformers import SentenceTransformer
                IngredientMatcher._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                load_ms = (time.perf_counter() - t0) * 1000
                logger.info("Embedding model loaded in %.0fms", load_ms)

            # Check timeout after model load
            elapsed = time.perf_counter() - t_start
            if elapsed > _EMBEDDING_TIMEOUT_S:
                logger.warning("Embedding timeout after model load (%.1fs) for '%s'", elapsed, query)
                return None

            query_vec = IngredientMatcher._embedding_model.encode(query, normalize_embeddings=True)
            vec_str = "[" + ",".join(str(float(x)) for x in query_vec) + "]"

            # Form-filtered similarity search
            row = self._db.execute(
                text("""
                    SELECT vi.code, vi.name,
                           1 - (vie.embedding <=> CAST(:vec AS vector)) AS similarity
                    FROM v2_ingredient_embeddings vie
                    JOIN v2_ingredients vi ON vi.id = vie.ingredient_id
                    WHERE vi.form IS NULL OR vi.form IN ('raw', 'unspecified', 'dry_ingredient')
                    ORDER BY vie.embedding <=> CAST(:vec AS vector)
                    LIMIT 1
                """),
                {"vec": vec_str},
            ).fetchone()

            # Check timeout after query
            elapsed = time.perf_counter() - t_start
            if elapsed > _EMBEDDING_TIMEOUT_S:
                logger.warning("Embedding timeout after query (%.1fs) for '%s'", elapsed, query)
                return None

            if row and row.similarity >= 0.75:
                return (row.code, row.name, float(row.similarity))

        except ImportError:
            logger.debug("sentence-transformers not available for embedding match")
        except Exception as e:
            logger.warning("Embedding match failed: %s", e)

        return None

    def _load_name_cache(self):
        """Load all ingredient names + aliases + form into memory for fuzzy matching."""
        rows = self._db.execute(
            text("SELECT code, name, search_aliases, form FROM v2_ingredients")
        ).fetchall()
        IngredientMatcher._name_cache = [
            (row.code, row.name, row.search_aliases or [], row.form) for row in rows
        ]
        logger.debug("Loaded %d ingredients into fuzzy match cache", len(rows))

    @classmethod
    def clear_cache(cls):
        """Clear the in-memory name cache (e.g., after re-seeding)."""
        cls._name_cache = None
