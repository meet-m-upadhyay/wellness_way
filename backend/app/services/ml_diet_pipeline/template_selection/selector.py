"""
Template selection scaffold (heuristic baseline)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Set


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TemplateCandidate:
    template_id: str
    meal_type: str
    diet_flags: Set[str]
    allergen_flags: Set[str]
    tags: Set[str]
    calories: float
    protein: float


@dataclass(frozen=True)
class SelectionConstraints:
    diet_type: str
    meal_type: str
    calorie_target: float
    protein_target: float
    allergies: Set[str]
    foods_to_avoid: Set[str]
    preferred_tags: Set[str]


class TemplateSelector:
    """Heuristic template selector with logging"""

    def select_template(
        self,
        constraints: SelectionConstraints,
        candidates: List[TemplateCandidate],
    ) -> TemplateCandidate:
        eligible = []
        for candidate in candidates:
            if candidate.meal_type != constraints.meal_type:
                self._log_reject(candidate, "meal_type_mismatch")
                continue
            if constraints.diet_type not in candidate.diet_flags:
                self._log_reject(candidate, "diet_mismatch")
                continue
            if candidate.allergen_flags.intersection(constraints.allergies):
                self._log_reject(candidate, "allergen_conflict")
                continue
            eligible.append(candidate)

        if not eligible:
            raise ValueError("No eligible templates after filtering.")

        scored = sorted(
            eligible,
            key=lambda c: (
                abs(c.calories - constraints.calorie_target),
                -c.protein,
            ),
        )

        selected = scored[0]
        logger.info(
            "[TEMPLATE_SELECTED] template_id=%s meal_type=%s",
            selected.template_id,
            selected.meal_type,
        )
        return selected

    def _log_reject(self, candidate: TemplateCandidate, reason: str) -> None:
        logger.info(
            "[TEMPLATE_REJECTED] template_id=%s reason=%s",
            candidate.template_id,
            reason,
        )
