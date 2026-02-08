"""
Validation Engine - Rules-only validation

This module validates diet plans using deterministic rules.
NO exceptions that cause AI retry - only soft/hard failure classification.

CRITICAL RULES:
- Diet-type specific thresholds
- NO AI retry triggers
- Soft vs hard failure classification
- Structured logging
"""

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
        """
        Validate a single meal.
        
        Args:
            meal: Meal dict with nutrition data
            diet_type: User's diet type
            target_calories: Optional target calories
            target_protein: Optional target protein
            
        Returns:
            ValidationResult with pass/fail and violations
        """
        request_id = f"val_meal_{meal.get('name', 'unknown')[:20]}"
        logger.info(f"[VALIDATION_MEAL_START] request_id={request_id} diet={diet_type}")
        
        violations = []
        warnings = []
        
        # Get diet-specific thresholds
        thresholds = self.DIET_THRESHOLDS.get(diet_type, self.DIET_THRESHOLDS["vegetarian"])
        
        nutrition = meal.get("nutrition", {})
        calories = nutrition.get("calories", 0)
        protein = nutrition.get("protein", 0)
        
        # HARD VALIDATION: Minimum calories
        if calories < thresholds["min_meal_calories"]:
            violation = (
                f"Meal '{meal.get('name')}' has {calories:.0f} calories, "
                f"below minimum {thresholds['min_meal_calories']} for {diet_type}"
            )
            violations.append(violation)
            logger.error(f"[VALIDATION_HARD_FAIL] {violation}")
        
        # HARD VALIDATION: Minimum protein
        if protein < thresholds["min_meal_protein"]:
            violation = (
                f"Meal '{meal.get('name')}' has {protein:.1f}g protein, "
                f"below minimum {thresholds['min_meal_protein']}g for {diet_type}"
            )
            violations.append(violation)
            logger.error(f"[VALIDATION_HARD_FAIL] {violation}")
        
        # SOFT VALIDATION: Target calories (if specified)
        if target_calories:
            calorie_diff = abs(calories - target_calories)
            if calorie_diff > target_calories * 0.20:  # 20% tolerance
                warning = (
                    f"Meal calories ({calories:.0f}) differ from target ({target_calories:.0f}) "
                    f"by {calorie_diff:.0f} (>{20}%)"
                )
                warnings.append(warning)
                logger.warning(f"[VALIDATION_SOFT_FAIL] {warning}")
        
        # SOFT VALIDATION: Target protein (if specified)
        if target_protein:
            protein_diff = abs(protein - target_protein)
            if protein_diff > target_protein * 0.20:  # 20% tolerance
                warning = (
                    f"Meal protein ({protein:.1f}g) differs from target ({target_protein:.1f}g) "
                    f"by {protein_diff:.1f}g (>{20}%)"
                )
                warnings.append(warning)
                logger.warning(f"[VALIDATION_SOFT_FAIL] {warning}")
        
        # Determine result
        passed = len(violations) == 0
        severity = ValidationSeverity.HARD if violations else ValidationSeverity.SOFT
        
        if passed:
            logger.info(f"[VALIDATION_MEAL_PASSED] request_id={request_id}")
        
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
        """
        Validate a daily meal plan.
        
        Args:
            meals: List of meal dicts
            diet_type: User's diet type
            target_daily_calories: Target daily calories
            target_daily_protein: Target daily protein
            
        Returns:
            ValidationResult with pass/fail and violations
        """
        logger.info(
            f"[VALIDATION_DAILY_START] diet={diet_type} "
            f"target_cal={target_daily_calories:.0f} target_prot={target_daily_protein:.1f}g"
        )
        
        violations = []
        warnings = []
        
        # Get diet-specific thresholds
        thresholds = self.DIET_THRESHOLDS.get(diet_type, self.DIET_THRESHOLDS["vegetarian"])
        
        # Calculate daily totals
        total_calories = sum(m.get("nutrition", {}).get("calories", 0) for m in meals)
        total_protein = sum(m.get("nutrition", {}).get("protein", 0) for m in meals)
        
        # HARD VALIDATION: Minimum daily calories
        if total_calories < thresholds["min_daily_calories"]:
            violation = (
                f"Daily total {total_calories:.0f} calories below minimum "
                f"{thresholds['min_daily_calories']} for {diet_type}"
            )
            violations.append(violation)
            logger.error(f"[VALIDATION_HARD_FAIL] {violation}")
        
        # HARD VALIDATION: Minimum daily protein
        if total_protein < thresholds["min_daily_protein"]:
            violation = (
                f"Daily total {total_protein:.1f}g protein below minimum "
                f"{thresholds['min_daily_protein']}g for {diet_type}"
            )
            violations.append(violation)
            logger.error(f"[VALIDATION_HARD_FAIL] {violation}")
        
        # SOFT VALIDATION: Target calories
        calorie_diff = abs(total_calories - target_daily_calories)
        if calorie_diff > target_daily_calories * 0.15:  # 15% tolerance
            warning = (
                f"Daily calories ({total_calories:.0f}) differ from target "
                f"({target_daily_calories:.0f}) by {calorie_diff:.0f} (>15%)"
            )
            warnings.append(warning)
            logger.warning(f"[VALIDATION_SOFT_FAIL] {warning}")
        
        # SOFT VALIDATION: Target protein
        protein_diff = abs(total_protein - target_daily_protein)
        if protein_diff > target_daily_protein * 0.15:  # 15% tolerance
            warning = (
                f"Daily protein ({total_protein:.1f}g) differs from target "
                f"({target_daily_protein:.1f}g) by {protein_diff:.1f}g (>15%)"
            )
            warnings.append(warning)
            logger.warning(f"[VALIDATION_SOFT_FAIL] {warning}")
        
        # Validate each meal
        for i, meal in enumerate(meals):
            meal_result = self.validate_meal(
                meal,
                diet_type,
                target_calories=target_daily_calories / len(meals),
                target_protein=target_daily_protein / len(meals)
            )
            
            if not meal_result.passed:
                violations.extend(meal_result.violations)
            warnings.extend(meal_result.warnings)
        
        # Determine result
        passed = len(violations) == 0
        severity = ValidationSeverity.HARD if violations else ValidationSeverity.SOFT
        
        if passed:
            logger.info("[VALIDATION_DAILY_PASSED]")
        
        return ValidationResult(
            passed=passed,
            severity=severity,
            violations=violations,
            warnings=warnings
        )


# Singleton instance
_engine: Optional[ValidationEngine] = None


def get_validation_engine() -> ValidationEngine:
    """Get singleton instance of validation engine"""
    global _engine
    if _engine is None:
        _engine = ValidationEngine()
    return _engine
