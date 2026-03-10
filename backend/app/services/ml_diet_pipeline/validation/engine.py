"""
Validation Engine - Rules-only validation
"""

from __future__ import annotations

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Validation failure severity"""
    SOFT = "soft"  # Acceptable with warning
    HARD = "hard"  # Unacceptable, return error


@dataclass
class ValidationResult:
    """Result of validation check"""
    passed: bool
    severity: ValidationSeverity
    violations: List[str]
    warnings: List[str]


class ValidationEngine:
    """Rules-only validation engine"""
    
    # Diet-specific thresholds
    DIET_THRESHOLDS = {
        "vegetarian": {
            "min_daily_calories": 1200,
            "min_meal_calories": 300,
            "min_daily_protein": 50,
            "min_meal_protein": 15
        },
        "vegan": {
            "min_daily_calories": 1200,
            "min_meal_calories": 300,
            "min_daily_protein": 50,
            "min_meal_protein": 15
        },
        "non-vegetarian": {
            "min_daily_calories": 1200,
            "min_meal_calories": 300,
            "min_daily_protein": 60,
            "min_meal_protein": 18
        },
        "eggetarian": {
            "min_daily_calories": 1200,
            "min_meal_calories": 300,
            "min_daily_protein": 55,
            "min_meal_protein": 16
        }
    }
    
    def __init__(self):
        """Initialize validation engine"""
        logger.info("[VALIDATION_ENGINE_INIT] Initialized rules-only validation engine")
    
    def validate_meal(
        self,
        meal: Dict[str, Any],
        diet_type: str,
        target_calories: Optional[float] = None,
        target_protein: Optional[float] = None
    ) -> ValidationResult:
        """Validate a single meal"""
        violations = []
        warnings = []
        
        # Get diet-specific thresholds
        thresholds = self.DIET_THRESHOLDS.get(diet_type, self.DIET_THRESHOLDS["vegetarian"])
        
        nutrition = meal.get("nutrition", {})
        calories = nutrition.get("calories", 0)
        protein = nutrition.get("protein", 0)
        
        # HARD VALIDATION: Minimum calories
        if calories < thresholds["min_meal_calories"]:
            violations.append(f"Meal below min calories ({calories:.0f} < {thresholds['min_meal_calories']})")
        
        # HARD VALIDATION: Minimum protein
        if protein < thresholds["min_meal_protein"]:
            violations.append(f"Meal below min protein ({protein:.1f}g < {thresholds['min_meal_protein']}g)")
        
        passed = len(violations) == 0
        severity = ValidationSeverity.HARD if violations else ValidationSeverity.SOFT
        
        return ValidationResult(
            passed=passed,
            severity=severity,
            violations=violations,
            warnings=warnings
        )
    
    def validate_daily_plan(
        self,
        meals: List[Dict[str, Any]],
        diet_type: str,
        target_daily_calories: float,
        target_daily_protein: float
    ) -> ValidationResult:
        """Validate a daily meal plan"""
        violations = []
        warnings = []
        
        thresholds = self.DIET_THRESHOLDS.get(diet_type, self.DIET_THRESHOLDS["vegetarian"])
        
        total_calories = sum(m.get("nutrition", {}).get("calories", 0) for m in meals)
        total_protein = sum(m.get("nutrition", {}).get("protein", 0) for m in meals)
        
        if total_calories < thresholds["min_daily_calories"]:
            violations.append(f"Daily total {total_calories:.0f} cal below minimum {thresholds['min_daily_calories']}")
        
        if total_protein < thresholds["min_daily_protein"]:
            violations.append(f"Daily total {total_protein:.1f}g protein below minimum {thresholds['min_daily_protein']}g")
        
        # Validation passed if no hard violations
        passed = len(violations) == 0
        severity = ValidationSeverity.HARD if violations else ValidationSeverity.SOFT
        
        return ValidationResult(
            passed=passed,
            severity=severity,
            violations=violations,
            warnings=warnings
        )


def get_validation_engine() -> ValidationEngine:
    """Get singleton instance"""
    return ValidationEngine()
