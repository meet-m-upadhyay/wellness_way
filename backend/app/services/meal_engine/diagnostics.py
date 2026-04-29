"""
V2 Pipeline Diagnostics — structured stats collection for performance analysis.

Collects per-ingredient, per-meal, and pipeline-level stats as the pipeline runs.
Output as JSON for aggregation. No performance fixes — observation only.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class IngredientDiag:
    """Stats for a single ingredient resolution."""
    raw_llm_name: str = ""
    cleaned_name: str = ""
    # Matcher results
    matcher_tiers_tried: List[str] = field(default_factory=list)
    match_tier: str = "none"          # exact / alias / canonical / fuzzy / embedding / none
    match_confidence: float = 0.0
    matched_ifct_name: Optional[str] = None
    matched_ifct_code: Optional[str] = None
    matcher_time_ms: float = 0.0
    # Nutrition resolution
    nutrition_provider: str = "none"   # ifct / edamam / edamam_cached / usda / none
    nutrition_providers_tried: List[str] = field(default_factory=list)
    nutrition_provider_statuses: Dict[str, int] = field(default_factory=dict)  # provider -> HTTP status
    nutrition_time_ms: float = 0.0
    total_time_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "raw_llm_name": self.raw_llm_name,
            "cleaned_name": self.cleaned_name,
            "match_tier": self.match_tier,
            "match_confidence": round(self.match_confidence, 3),
            "matched_ifct_name": self.matched_ifct_name,
            "matched_ifct_code": self.matched_ifct_code,
            "matcher_tiers_tried": self.matcher_tiers_tried,
            "matcher_time_ms": round(self.matcher_time_ms, 1),
            "nutrition_provider": self.nutrition_provider,
            "nutrition_providers_tried": self.nutrition_providers_tried,
            "nutrition_provider_statuses": self.nutrition_provider_statuses,
            "nutrition_time_ms": round(self.nutrition_time_ms, 1),
            "total_time_ms": round(self.total_time_ms, 1),
        }


@dataclass
class MealAttemptDiag:
    """Stats for a single meal generation attempt."""
    attempt_number: int = 0
    meal_type: str = ""
    archetype: str = ""
    dish_name: str = ""
    ingredients: List[IngredientDiag] = field(default_factory=list)
    # Stage timings (ms)
    llm_generation_ms: float = 0.0
    ingredient_resolution_ms: float = 0.0
    macro_calculation_ms: float = 0.0
    scoring_ms: float = 0.0
    total_ms: float = 0.0
    # Score
    score_total: float = 0.0
    score_band: str = ""
    # Outcome
    kept: bool = False  # Was this the attempt that was used?
    retry_reason: str = ""  # "low_score" / "exception" / ""

    def to_dict(self) -> dict:
        return {
            "attempt": self.attempt_number,
            "meal_type": self.meal_type,
            "archetype": self.archetype,
            "dish_name": self.dish_name,
            "ingredients": [i.to_dict() for i in self.ingredients],
            "timing_ms": {
                "llm_generation": round(self.llm_generation_ms, 1),
                "ingredient_resolution": round(self.ingredient_resolution_ms, 1),
                "macro_calculation": round(self.macro_calculation_ms, 1),
                "scoring": round(self.scoring_ms, 1),
                "total": round(self.total_ms, 1),
            },
            "score_total": round(self.score_total, 1),
            "score_band": self.score_band,
            "kept": self.kept,
            "retry_reason": self.retry_reason,
        }


@dataclass
class PipelineDiagnostics:
    """Aggregated diagnostics for a full daily plan generation."""
    meal_attempts: List[MealAttemptDiag] = field(default_factory=list)
    total_pipeline_ms: float = 0.0
    # Counters
    edamam_call_count: int = 0
    edamam_status_codes: Dict[int, int] = field(default_factory=dict)  # status -> count
    usda_call_count: int = 0
    usda_status_codes: Dict[int, int] = field(default_factory=dict)
    ifct_lookup_count: int = 0

    def record_edamam_call(self, status_code: int):
        self.edamam_call_count += 1
        self.edamam_status_codes[status_code] = self.edamam_status_codes.get(status_code, 0) + 1

    def record_usda_call(self, status_code: int):
        self.usda_call_count += 1
        self.usda_status_codes[status_code] = self.usda_status_codes.get(status_code, 0) + 1

    def record_ifct_lookup(self):
        self.ifct_lookup_count += 1

    def summary(self) -> dict:
        """Compute aggregate stats for the full pipeline."""
        all_ingredients: List[IngredientDiag] = []
        for attempt in self.meal_attempts:
            all_ingredients.extend(attempt.ingredients)

        total_lookups = len(all_ingredients)

        # Match tier distribution
        tier_counts: Dict[str, int] = {}
        for ing in all_ingredients:
            tier_counts[ing.match_tier] = tier_counts.get(ing.match_tier, 0) + 1

        # Provider distribution
        provider_counts: Dict[str, int] = {}
        for ing in all_ingredients:
            provider_counts[ing.nutrition_provider] = provider_counts.get(ing.nutrition_provider, 0) + 1

        # IFCT match rate
        ifct_matches = sum(1 for i in all_ingredients if i.match_tier != "none")
        ifct_match_rate = (ifct_matches / total_lookups * 100) if total_lookups else 0

        # Top failed ingredients
        failed = [i for i in all_ingredients if i.match_tier == "none"]
        failed_names: Dict[str, int] = {}
        for f in failed:
            failed_names[f.cleaned_name] = failed_names.get(f.cleaned_name, 0) + 1
        top_failed = sorted(failed_names.items(), key=lambda x: -x[1])[:10]

        # Timing breakdown
        kept_attempts = [a for a in self.meal_attempts if a.kept]
        total_llm = sum(a.llm_generation_ms for a in self.meal_attempts)
        total_ingredient = sum(a.ingredient_resolution_ms for a in self.meal_attempts)
        total_scoring = sum(a.scoring_ms for a in self.meal_attempts)
        total_macro = sum(a.macro_calculation_ms for a in self.meal_attempts)
        total_active = total_llm + total_ingredient + total_scoring + total_macro

        # Retry stats
        meals_generated = len(set(a.meal_type for a in self.meal_attempts))
        total_attempts = len(self.meal_attempts)
        retry_count = total_attempts - meals_generated

        return {
            "total_pipeline_ms": round(self.total_pipeline_ms, 1),
            "total_pipeline_seconds": round(self.total_pipeline_ms / 1000, 1),
            "meals_generated": meals_generated,
            "total_attempts": total_attempts,
            "retry_count": retry_count,
            "total_ingredient_lookups": total_lookups,
            "ifct_match_rate_pct": round(ifct_match_rate, 1),
            "match_tier_distribution": {
                tier: {"count": count, "pct": round(count / total_lookups * 100, 1) if total_lookups else 0}
                for tier, count in sorted(tier_counts.items())
            },
            "nutrition_provider_distribution": {
                prov: {"count": count, "pct": round(count / total_lookups * 100, 1) if total_lookups else 0}
                for prov, count in sorted(provider_counts.items())
            },
            "api_calls": {
                "edamam": {
                    "total_calls": self.edamam_call_count,
                    "status_codes": self.edamam_status_codes,
                },
                "usda": {
                    "total_calls": self.usda_call_count,
                    "status_codes": self.usda_status_codes,
                },
                "ifct_db_lookups": self.ifct_lookup_count,
            },
            "top_10_failed_ingredients": [
                {"name": name, "fail_count": count} for name, count in top_failed
            ],
            "timing_breakdown": {
                "llm_generation_ms": round(total_llm, 1),
                "ingredient_resolution_ms": round(total_ingredient, 1),
                "scoring_ms": round(total_scoring, 1),
                "macro_calculation_ms": round(total_macro, 1),
                "total_active_ms": round(total_active, 1),
                "overhead_ms": round(self.total_pipeline_ms - total_active, 1),
            },
            "timing_pct": {
                "llm_generation": round(total_llm / self.total_pipeline_ms * 100, 1) if self.total_pipeline_ms else 0,
                "ingredient_resolution": round(total_ingredient / self.total_pipeline_ms * 100, 1) if self.total_pipeline_ms else 0,
                "scoring": round(total_scoring / self.total_pipeline_ms * 100, 1) if self.total_pipeline_ms else 0,
                "macro_calculation": round(total_macro / self.total_pipeline_ms * 100, 1) if self.total_pipeline_ms else 0,
                "overhead": round((self.total_pipeline_ms - total_active) / self.total_pipeline_ms * 100, 1) if self.total_pipeline_ms else 0,
            },
        }

    def to_full_log(self) -> dict:
        """Full diagnostic output: all attempts + summary."""
        return {
            "attempts": [a.to_dict() for a in self.meal_attempts],
            "summary": self.summary(),
        }

    def log_output(self):
        """Log the full diagnostics as structured JSON and save to file."""
        import os
        from datetime import datetime

        output = self.to_full_log()

        # Save to file
        logs_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs")
        logs_dir = os.path.normpath(logs_dir)
        os.makedirs(logs_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(logs_dir, f"pipeline_diagnostic_{timestamp}.json")
        with open(filepath, "w") as f:
            json.dump(output, f, indent=2)
        logger.info("[V2_PIPELINE_DIAGNOSTICS] Full log saved to %s", filepath)

        # Log compact summary to stdout
        s = self.summary()
        logger.info(
            "[V2_PIPELINE_SUMMARY] total=%.1fs | meals=%d | attempts=%d | retries=%d | "
            "ifct_match=%.1f%% | edamam_calls=%d(429s:%d) | usda_calls=%d | "
            "llm=%.1f%% | ingredient=%.1f%% | scoring=%.1f%%",
            s["total_pipeline_seconds"],
            s["meals_generated"],
            s["total_attempts"],
            s["retry_count"],
            s["ifct_match_rate_pct"],
            s["api_calls"]["edamam"]["total_calls"],
            s["api_calls"]["edamam"]["status_codes"].get(429, 0),
            s["api_calls"]["usda"]["total_calls"],
            s["timing_pct"]["llm_generation"],
            s["timing_pct"]["ingredient_resolution"],
            s["timing_pct"]["scoring"],
        )
