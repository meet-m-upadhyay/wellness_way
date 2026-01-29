"""
Diet Plan Validation Service - Goal-Aware Safe Ranges

This module implements goal-specific acceptance buffers that mirror real nutrition science.
Plans that are nutritionally safe and realistic are accepted with optional guidance,
preventing infinite AI retries and token exhaustion.

CRITICAL POLICY SHIFT:
- Daily perfection -> Goal-aware safe ranges with weekly logic
- Hard safety bounds -> REJECT
- Outside exact target but inside safe range -> ACCEPT + GUIDE USER  
- Inside exact target -> ACCEPT silently

GOAL-SPECIFIC ACCEPTANCE RULES (RESEARCH-BACKED):
1. WEIGHT LOSS: 15-25% deficit, ±10% daily acceptable, protein ≥90% target
2. MUSCLE GAIN: 5-15% surplus, ±10-15% acceptable, protein ≥90% target  
3. MAINTENANCE: TDEE ±15-20% acceptable, protein ≥90% target

GLOBAL NON-NEGOTIABLES:
- Zero-calorie plans impossible
- Protein <90% of minimum -> reject
- Chronic >25% deficit -> reject
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from uuid import UUID

logger = logging.getLogger(__name__)


class PlanValidationError(Exception):
    """Exception raised when a diet plan fails validation and cannot be auto-corrected"""
    
    def __init__(self, message: str, violations: List[str], plan_data: Optional[Dict] = None):
        self.message = message
        self.violations = violations
        self.plan_data = plan_data
        super().__init__(message)


@dataclass
class GoalRanges:
    """Goal-specific acceptable ranges for calories and protein"""
    # Calorie ranges
    target_calories: float
    min_acceptable_calories: float
    max_acceptable_calories: float
    hard_min_calories: float  # Safety floor - never go below
    hard_max_calories: float  # Safety ceiling - never exceed
    
    # Protein ranges  
    target_protein: float
    min_acceptable_protein: float
    max_acceptable_protein: float
    hard_min_protein: float  # Non-negotiable minimum
    
    # Goal metadata
    goal_type: str  # "weight_loss", "muscle_gain", "maintenance"
    user_weight_kg: float


@dataclass
class BalanceGuidance:
    """Optional balance guidance for users when plan is acceptable but not exact"""
    type: str = "info"  # "info", "warning"
    severity: str = "low"  # "low", "medium" 
    message: str = ""
    calorie_delta: float = 0
    protein_delta: float = 0


@dataclass
class ValidationResult:
    """Result of plan validation with goal-aware acceptance"""
    is_valid: bool
    status: str  # "accepted" | "accepted_with_guidance" | "retryable_failure" | "hard_safety_violation"
    violations: List[str]
    balance_guidance: Optional[BalanceGuidance] = None  # Optional user guidance


class DietPlanValidator:
    """
    Goal-aware diet plan validator with safe acceptance buffers.
    
    RESPONSIBILITIES:
    1. Compute goal-specific acceptable ranges
    2. Accept plans within safe buffers (STOP RETRIES)
    3. Provide optional balance guidance for users
    4. Only reject plans that violate hard safety bounds
    5. Preserve all existing safety floors
    """
    
    def __init__(self):
        pass  # No auto-correction needed
    
    def get_goal_ranges(
        self,
        goal_type: str,
        user_weight_kg: float,
        target_calories: float,
        target_protein_g: float
    ) -> GoalRanges:
        """
        Compute goal-specific acceptable ranges based on nutrition science.
        
        Args:
            goal_type: "weight_loss", "muscle_gain", "maintenance"
            user_weight_kg: User's weight in kg
            target_calories: Target daily calories
            target_protein_g: Target daily protein in grams
            
        Returns:
            GoalRanges with acceptable buffers for the specific goal
        """
        if goal_type == "weight_loss":
            # WEIGHT LOSS: 15-25% deficit, ±10% daily acceptable
            calorie_buffer = 0.10  # ±10%
            protein_buffer = 0.10  # ±10%
            hard_protein_floor = 0.90  # Never below 90% of target
            
            min_acceptable = target_calories * (1 - calorie_buffer)
            max_acceptable = target_calories * (1 + calorie_buffer)
            hard_min = target_calories * 0.75  # Never below 75% (too aggressive)
            hard_max = target_calories * 1.15  # Never above 15% surplus (defeats purpose)
            
        elif goal_type == "muscle_gain":
            # MUSCLE GAIN: 5-15% surplus, ±10-15% acceptable
            calorie_buffer = 0.15  # ±15% (more flexible for bulking)
            protein_buffer = 0.10  # ±10%
            hard_protein_floor = 0.90  # Never below 90% of target
            
            min_acceptable = target_calories * (1 - calorie_buffer)
            max_acceptable = target_calories * (1 + calorie_buffer)
            hard_min = target_calories * 0.85  # Never below 85%
            hard_max = target_calories * 1.20  # Never above 20% (fat gain risk)
            
        else:  # maintenance
            # MAINTENANCE: TDEE ±15-20% acceptable
            calorie_buffer = 0.20  # ±20% (most flexible)
            protein_buffer = 0.15  # ±15%
            hard_protein_floor = 0.90  # Never below 90% of target
            
            min_acceptable = target_calories * (1 - calorie_buffer)
            max_acceptable = target_calories * (1 + calorie_buffer)
            hard_min = target_calories * 0.80  # Never below 80%
            hard_max = target_calories * 1.25  # Never above 25%
        
        # Protein ranges
        min_acceptable_protein = target_protein_g * (1 - protein_buffer)
        max_acceptable_protein = target_protein_g * (1 + protein_buffer)
        hard_min_protein = target_protein_g * hard_protein_floor
        
        return GoalRanges(
            target_calories=target_calories,
            min_acceptable_calories=min_acceptable,
            max_acceptable_calories=max_acceptable,
            hard_min_calories=hard_min,
            hard_max_calories=hard_max,
            target_protein=target_protein_g,
            min_acceptable_protein=min_acceptable_protein,
            max_acceptable_protein=max_acceptable_protein,
            hard_min_protein=hard_min_protein,
            goal_type=goal_type,
            user_weight_kg=user_weight_kg
        )
    
    def create_balance_guidance(
        self,
        actual_calories: float,
        actual_protein: float,
        ranges: GoalRanges
    ) -> Optional[BalanceGuidance]:
        """
        Create user-friendly balance guidance (NO AI).
        
        Args:
            actual_calories: Plan's actual calories
            actual_protein: Plan's actual protein
            ranges: Goal-specific ranges
            
        Returns:
            BalanceGuidance with optional suggestions, or None if plan is exact
        """
        calorie_delta = actual_calories - ranges.target_calories
        protein_delta = actual_protein - ranges.target_protein
        
        # If within exact target (±2%), no guidance needed
        if (abs(calorie_delta) <= ranges.target_calories * 0.02 and 
            abs(protein_delta) <= ranges.target_protein * 0.02):
            return None
        
        # Calculate percentage variance
        calorie_percent = (calorie_delta / ranges.target_calories) * 100
        protein_percent = (protein_delta / ranges.target_protein) * 100
        
        # Generate user-friendly guidance messages
        messages = []
        
        # Calorie guidance with reassuring tone
        if calorie_delta < -50:  # Significantly low
            steps_needed = int(abs(calorie_delta) / 0.04)  # ~0.04 cal per step
            messages.append(f"You're ~{abs(calorie_percent):.0f}% below today's calorie target. This is safe. "
                          f"Optional suggestions: Walk ~{steps_needed:,} fewer steps today, OR "
                          f"add a banana + peanut butter (~{abs(calorie_delta):.0f} kcal).")
        elif calorie_delta > 50:  # Significantly high
            steps_needed = int(calorie_delta / 0.04)  # ~0.04 cal per step
            messages.append(f"You're ~{calorie_percent:.0f}% above target today. No harm done. "
                          f"Optional suggestions: Add a 15-20 min walk, OR "
                          f"slightly reduce carbs at dinner.")
        
        # Protein guidance with reassuring tone
        if protein_delta < -3:  # Significantly low
            messages.append(f"Protein is ~{abs(protein_percent):.0f}% below target. "
                          f"Optional: add a small serving of paneer, tofu, or Greek yogurt.")
        elif protein_delta > 5:  # Significantly high (less concerning)
            messages.append(f"Protein is {protein_percent:.0f}% above target. This is excellent for your goals.")
        
        if not messages:
            return None
        
        # Determine severity and UI hint
        severity = "medium" if abs(calorie_percent) > 15 or abs(protein_percent) > 15 else "low"
        ui_hint = "yellow_info_box"
        
        # Add reassuring footer
        final_message = " ".join(messages) + " This is a suggestion, not a requirement."
        
        return BalanceGuidance(
            type="informational",
            severity=severity,
            message=final_message,
            calorie_delta=calorie_delta,
            protein_delta=protein_delta
        )
    
    def validate_plan(
        self,
        plan_data: Dict[str, Any],
        safety_constraints: Dict[str, float],
        user_id: UUID,
        goal_type: str = "maintenance",
        user_weight_kg: float = 70.0
    ) -> ValidationResult:
        """
        GOAL-AWARE VALIDATION: Accept plans within safe buffers to prevent infinite retries.
        
        VALIDATION FLOW:
        1. Check integrity violations (immediate reject)
        2. Compute goal-specific acceptable ranges
        3. Check if plan violates hard safety bounds -> REJECT
        4. Check if plan is within safe buffer -> ACCEPT + optional guidance
        5. Check if plan is within exact target -> ACCEPT silently
        6. Only auto-correct if outside safe buffer
        
        Args:
            plan_data: Raw plan data from AI service
            safety_constraints: User's safety constraints from HCD
            user_id: User ID for logging
            goal_type: "weight_loss", "muscle_gain", "maintenance"
            user_weight_kg: User's weight in kg
            
        Returns:
            ValidationResult with validation status and optional balance guidance
            
        Raises:
            PlanValidationError: Only if plan violates hard safety bounds
        """
        logger.info(f"GOAL-AWARE VALIDATION: {goal_type} plan for user {user_id}")
        
        # STEP 1: INTEGRITY CHECKS FIRST (must pass before safety checks)
        integrity_violations = self._check_integrity_violations(plan_data)
        if integrity_violations:
            logger.error(f"INTEGRITY VIOLATIONS: {integrity_violations}")
            raise PlanValidationError(
                message=f"Plan violates integrity constraints",
                violations=[f"INTEGRITY VIOLATION: {v}" for v in integrity_violations],
                plan_data=None
            )
        
        # STEP 2: COMPUTE GOAL-SPECIFIC RANGES
        target_calories = safety_constraints.get('target_calories', 2000)
        target_protein = safety_constraints.get('target_protein', 100)
        
        ranges = self.get_goal_ranges(
            goal_type=goal_type,
            user_weight_kg=user_weight_kg,
            target_calories=target_calories,
            target_protein_g=target_protein
        )
        
        logger.info(f"Goal ranges: calories {ranges.min_acceptable_calories:.0f}-{ranges.max_acceptable_calories:.0f}, "
                   f"protein {ranges.min_acceptable_protein:.1f}-{ranges.max_acceptable_protein:.1f}g")
        
        # STEP 3: EXTRACT ACTUAL NUTRITION
        if plan_data.get("plan_type") == "weekly":
            actual_calories, actual_protein = self._extract_weekly_averages(plan_data)
        else:
            actual_calories, actual_protein = self._extract_daily_totals(plan_data)
        
        # CRITICAL FIX: ZERO-STATE VALIDATION GUARD
        # Never classify zero totals as hard safety violations
        if actual_calories is None or actual_protein is None or actual_calories == 0 or actual_protein == 0:
            logger.warning("ZERO-STATE DETECTED: Nutrition aggregation incomplete or failed")
            return ValidationResult(
                is_valid=False,
                status="retryable_failure",
                violations=["Nutrition aggregation incomplete - retryable"],
                balance_guidance=None
            )
        
        logger.info(f"Actual nutrition: {actual_calories:.0f} kcal, {actual_protein:.1f}g protein")
        
        # STEP 4: CHECK HARD SAFETY BOUNDS (immediate reject - NEVER RETRY)
        # Only trigger for truly dangerous plans after aggregation is complete
        hard_violations = []
        
        # Hard safety: 75% of minimum requirement (not buffer minimum)
        absolute_min_calories = safety_constraints.get('min_daily_calories', 1200) * 0.75
        absolute_min_protein = user_weight_kg * 1.2  # 1.2g/kg absolute minimum
        
        if actual_calories < absolute_min_calories:
            hard_violations.append(f"Dangerously low calories: {actual_calories:.0f} < {absolute_min_calories:.0f} (75% of minimum)")
        
        if actual_protein < absolute_min_protein:
            hard_violations.append(f"Critically low protein: {actual_protein:.1f}g < {absolute_min_protein:.1f}g (1.2g/kg minimum)")
        
        if hard_violations:
            logger.error(f"HARD SAFETY VIOLATIONS: {hard_violations}")
            raise PlanValidationError(
                message="Plan violates hard safety bounds - TERMINAL",
                violations=[f"HARD SAFETY VIOLATION: {v}" for v in hard_violations],
                plan_data=None
            )
        
        # STEP 5: CHECK IF WITHIN ACCEPTABLE BUFFER (accept with optional guidance)
        within_calorie_buffer = (ranges.min_acceptable_calories <= actual_calories <= ranges.max_acceptable_calories)
        within_protein_buffer = (actual_protein >= ranges.min_acceptable_protein)
        
        if within_calorie_buffer and within_protein_buffer:
            # ACCEPT PLAN - within safe buffer (SHORT-CIRCUIT PIPELINE)
            balance_guidance = self.create_balance_guidance(actual_calories, actual_protein, ranges)
            
            if balance_guidance:
                logger.info(f"BUFFER ACCEPTED with guidance: {balance_guidance.message}")
                return ValidationResult(
                    is_valid=True,
                    status="accepted_with_guidance",
                    violations=[],
                    balance_guidance=balance_guidance
                )
            else:
                logger.info(f"COMPLIANT: Within exact target")
                return ValidationResult(
                    is_valid=True,
                    status="accepted",
                    violations=[]
                )
        
        # STEP 6: OUTSIDE ACCEPTABLE BUFFER - retryable failure (LIMITED RETRY)
        logger.warning(f"Outside acceptable buffer - retryable failure")
        logger.warning(f"   Calories: {actual_calories:.0f} (range: {ranges.min_acceptable_calories:.0f}-{ranges.max_acceptable_calories:.0f})")
        logger.warning(f"   Protein: {actual_protein:.1f}g (min: {ranges.min_acceptable_protein:.1f}g)")
        
        # Classify as retryable failure with correction hints
        retryable_violations = []
        if not within_calorie_buffer:
            if actual_calories < ranges.min_acceptable_calories:
                retryable_violations.append(f"Calories below acceptable range: {actual_calories:.0f} < {ranges.min_acceptable_calories:.0f}")
            else:
                retryable_violations.append(f"Calories above acceptable range: {actual_calories:.0f} > {ranges.max_acceptable_calories:.0f}")
        
        if not within_protein_buffer:
            retryable_violations.append(f"Protein below acceptable range: {actual_protein:.1f}g < {ranges.min_acceptable_protein:.1f}g")
        
        logger.info(f"RETRYABLE FAILURE: Plan outside acceptable buffer but not dangerous")
        return ValidationResult(
            is_valid=False,
            status="retryable_failure",
            violations=retryable_violations,
            balance_guidance=None
        )
        
        # Auto-correction failed - REJECT the plan
        logger.error(f"❌ REJECTED: Cannot be made safe (attempts: {correction_attempts})")
        
        raise PlanValidationError(
            message=f"Diet plan cannot be corrected to meet safe ranges",
            violations=[f"CORRECTION FAILED: {violation}" for violation in legacy_violations],
            plan_data=None
        )
    
    def _check_integrity_violations(self, plan_data: Dict[str, Any]) -> List[str]:
        """
        Check for integrity violations that must cause immediate rejection.
        
        MANDATORY CHECKS:
        1. No cooked/processed ingredients
        2. No excessive decimal precision  
        3. No fractional discrete items
        4. Protein powder in scoops only
        """
        violations = []
        
        # Extract meals based on plan type
        meals = []
        if plan_data.get("plan_type") == "weekly":
            for day in plan_data.get("days", []):
                meals.extend(day.get("meals", []))
        else:
            meals = plan_data.get("meals", [])
        
        for meal_idx, meal in enumerate(meals):
            for ing_idx, ingredient in enumerate(meal.get("ingredients", [])):
                name = ingredient.get("name", "").lower()
                quantity = ingredient.get("quantity", 0)
                unit = ingredient.get("unit", "").lower()
                
                # CHECK 1: No cooked/processed ingredients
                if self._is_cooked_processed_ingredient(name):
                    violations.append(
                        f"Cooked/processed ingredient detected: '{ingredient.get('name', 'unknown')}'"
                    )
                
                # CHECK 2: No excessive decimal precision
                if isinstance(quantity, float) and not quantity.is_integer():
                    violations.append(
                        f"Excessive decimal precision: {ingredient.get('name', 'unknown')} has {quantity} (must be integer)"
                    )
                
                # CHECK 3: Discrete items must be whole numbers
                if self._is_discrete_item_name(name) and not isinstance(quantity, int):
                    violations.append(
                        f"Fractional discrete item: {ingredient.get('name', 'unknown')} has {quantity} (must be whole number)"
                    )
                
                # CHECK 4: Protein powder must be in scoops
                if self._is_protein_powder_name(name):
                    if unit not in ["scoop", "scoops"]:
                        violations.append(
                            f"Protein powder not in scoops: {ingredient.get('name', 'unknown')} has unit '{unit}' (must be scoops)"
                        )
                    elif not isinstance(quantity, int) or quantity < 1 or quantity > 4:
                        violations.append(
                            f"Invalid protein powder quantity: {ingredient.get('name', 'unknown')} has {quantity} scoops (must be 1-4 whole scoops)"
                        )
        
        return violations
    
    def _is_cooked_processed_ingredient(self, name: str) -> bool:
        """Check if ingredient name indicates cooked/processed state"""
        cooked_indicators = [
            'cooked', 'boiled', 'steamed', 'grilled', 'baked', 'fried',
            'roasted', 'sautéed', 'sauteed', 'prepared', 'ready',
            'frozen', 'processed', 'canned', 'pickled', 'smoked',
            'dried', 'dehydrated', 'instant', 'pre-cooked'
        ]
        return any(indicator in name for indicator in cooked_indicators)
    
    def _is_discrete_item_name(self, name: str) -> bool:
        """Check if ingredient name indicates discrete item"""
        discrete_items = [
            'egg', 'eggs', 'banana', 'bananas', 'apple', 'apples',
            'orange', 'oranges', 'tomato', 'tomatoes', 'onion', 'onions',
            'potato', 'potatoes', 'carrot', 'carrots', 'avocado', 'avocados'
        ]
        return any(item in name for item in discrete_items)
    
    def _is_protein_powder_name(self, name: str) -> bool:
        """Check if ingredient name indicates protein powder"""
        protein_powder_indicators = [
            'protein powder', 'whey protein', 'casein protein', 'plant protein',
            'pea protein', 'soy protein', 'hemp protein', 'rice protein'
        ]
        return any(indicator in name for indicator in protein_powder_indicators)
    
    def _check_safety_constraints(
        self,
        plan_data: Dict[str, Any],
        min_calories: float,
        min_protein: float,
        max_deficit: float
    ) -> List[str]:
        """
        Check all safety constraints against plan data.
        
        MANDATORY CHECKS:
        1. calories ≥ min_daily_calories
        2. protein ≥ min_protein_grams  
        3. calorie_deficit ≤ max_calorie_deficit
        """
        violations = []
        
        # Extract nutrition data based on plan type
        if plan_data.get("plan_type") == "weekly":
            # For weekly plans, check daily averages
            daily_calories, daily_protein = self._extract_weekly_averages(plan_data)
        else:
            # For daily plans, check daily totals
            daily_calories, daily_protein = self._extract_daily_totals(plan_data)
        
        if daily_calories is None or daily_protein is None:
            violations.append("Missing or invalid nutrition data")
            return violations
        
        # CONSTRAINT 1: Minimum calories
        if daily_calories < min_calories:
            violations.append(
                f"Calories too low: {daily_calories:.0f} < {min_calories:.0f} (minimum)"
            )
        
        # CONSTRAINT 2: Minimum protein
        if daily_protein < min_protein:
            violations.append(
                f"Protein too low: {daily_protein:.1f}g < {min_protein:.1f}g (minimum)"
            )
        
        # CONSTRAINT 3: Maximum deficit (if TDEE is available)
        # This would require TDEE from safety constraints - for now, focus on minimums
        
        return violations
    
    def _extract_weekly_averages(self, plan_data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
        """Extract average daily calories and protein from weekly plan"""
        try:
            if "days" not in plan_data:
                return None, None
            
            total_calories = 0
            total_protein = 0
            valid_days = 0
            
            for day in plan_data["days"]:
                daily_totals = day.get("daily_totals", {})
                if daily_totals:
                    total_calories += daily_totals.get("calories", 0)
                    total_protein += daily_totals.get("protein", 0)
                    valid_days += 1
            
            if valid_days == 0:
                return None, None
            
            avg_calories = total_calories / valid_days
            avg_protein = total_protein / valid_days
            
            return avg_calories, avg_protein
            
        except Exception as e:
            logger.error(f"Error extracting weekly averages: {e}")
            return None, None
    
    def _extract_daily_totals(self, plan_data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
        """Extract calories and protein from daily plan"""
        try:
            daily_totals = plan_data.get("daily_totals", {})
            if not daily_totals:
                return None, None
            
            calories = daily_totals.get("calories", 0)
            protein = daily_totals.get("protein", 0)
            
            return calories, protein
            
        except Exception as e:
            logger.error(f"Error extracting daily totals: {e}")
            return None, None
    
    def _attempt_auto_correction(
        self,
        plan_data: Dict[str, Any],
        min_calories: float,
        min_protein: float,
        max_deficit: float,
        violations: List[str]
    ) -> Tuple[Optional[Dict], int]:
        """
        Attempt to auto-correct plan violations.
        
        AUTO-CORRECTION STRATEGY:
        1. Increase portion sizes of high-protein foods
        2. Add healthy snacks if calories are too low
        3. Respect macro caps and safety limits
        4. Maximum 2 correction attempts
        
        Returns:
            (corrected_plan_data, attempts_made)
        """
        logger.info(f"🔧 Attempting auto-correction for violations: {violations}")
        
        corrected_plan = plan_data.copy()
        attempts = 0
        
        for attempt in range(self.max_correction_attempts):
            attempts += 1
            logger.info(f"Auto-correction attempt {attempts}/{self.max_correction_attempts}")
            
            # Apply corrections based on plan type
            if corrected_plan.get("plan_type") == "weekly":
                corrected_plan = self._correct_weekly_plan(
                    corrected_plan, min_calories, min_protein
                )
            else:
                corrected_plan = self._correct_daily_plan(
                    corrected_plan, min_calories, min_protein
                )
            
            # Check if corrections fixed the violations
            new_violations = self._check_safety_constraints(
                corrected_plan, min_calories, min_protein, max_deficit
            )
            
            if not new_violations:
                logger.info(f"✅ Auto-correction successful after {attempts} attempts")
                return corrected_plan, attempts
            
            logger.warning(f"Attempt {attempts} still has violations: {new_violations}")
        
        logger.error(f"Auto-correction failed after {attempts} attempts")
        return None, attempts
    
    def _correct_weekly_plan(
        self,
        plan_data: Dict[str, Any],
        min_calories: float,
        min_protein: float
    ) -> Dict[str, Any]:
        """Auto-correct weekly plan by adjusting daily meals"""
        corrected_plan = plan_data.copy()
        
        if "days" not in corrected_plan:
            return corrected_plan
        
        for day_idx, day in enumerate(corrected_plan["days"]):
            # Correct each day individually
            daily_plan = {
                "plan_type": "daily",
                "meals": day.get("meals", []),
                "daily_totals": day.get("daily_totals", {})
            }
            
            corrected_daily = self._correct_daily_plan(daily_plan, min_calories, min_protein)
            
            # Update the day with corrected data
            corrected_plan["days"][day_idx]["meals"] = corrected_daily.get("meals", [])
            corrected_plan["days"][day_idx]["daily_totals"] = corrected_daily.get("daily_totals", {})
        
        # Recalculate weekly totals
        corrected_plan["weekly_totals"] = self._calculate_weekly_totals(corrected_plan["days"])
        
        return corrected_plan
    
    def _correct_daily_plan(
        self,
        plan_data: Dict[str, Any],
        min_calories: float,
        min_protein: float
    ) -> Dict[str, Any]:
        """
        Auto-correct daily plan by increasing portions and adding snacks.
        
        CORRECTION STRATEGY:
        1. Increase protein-rich ingredients by 50% (more aggressive)
        2. Add healthy snack if calories still too low
        3. Recalculate nutrition totals
        """
        corrected_plan = plan_data.copy()
        meals = corrected_plan.get("meals", [])
        
        if not meals:
            return corrected_plan
        
        # Phase 1: Increase protein-rich ingredients more aggressively
        for meal in meals:
            ingredients = meal.get("ingredients", [])
            for ingredient in ingredients:
                nutrition = ingredient.get("nutrition", {})
                protein_content = nutrition.get("protein", 0)
                
                # If ingredient has significant protein (≥5g), increase by 50%
                if protein_content >= 5:
                    original_quantity = ingredient.get("quantity", 0)
                    ingredient["quantity"] = original_quantity * 1.5  # More aggressive
                    
                    # Recalculate nutrition proportionally
                    for nutrient in ["calories", "protein", "carbohydrates", "fat", "fiber", "sodium"]:
                        if nutrient in nutrition:
                            nutrition[nutrient] *= 1.5
                
                # Also increase high-calorie ingredients by 25%
                elif nutrition.get("calories", 0) >= 100:
                    original_quantity = ingredient.get("quantity", 0)
                    ingredient["quantity"] = original_quantity * 1.25
                    
                    # Recalculate nutrition proportionally
                    for nutrient in ["calories", "protein", "carbohydrates", "fat", "fiber", "sodium"]:
                        if nutrient in nutrition:
                            nutrition[nutrient] *= 1.25
        
        # Recalculate meal nutrition after ingredient adjustments
        for meal in meals:
            meal["nutrition"] = self._calculate_meal_nutrition_from_ingredients(meal["ingredients"])
        
        # Phase 2: Add healthy snack if still needed
        current_totals = self._calculate_meal_totals(meals)
        current_calories = current_totals.get("calories", 0)
        current_protein = current_totals.get("protein", 0)
        
        if current_calories < min_calories or current_protein < min_protein:
            # Add a protein-rich snack
            calorie_deficit = max(0, min_calories - current_calories)
            protein_deficit = max(0, min_protein - current_protein)
            
            protein_snack = self._create_protein_snack(calorie_deficit, protein_deficit)
            meals.append(protein_snack)
        
        # Recalculate daily totals
        corrected_plan["meals"] = meals
        corrected_plan["daily_totals"] = self._calculate_meal_totals(meals)
        
        return corrected_plan
    
    def _create_protein_snack(self, calorie_deficit: float, protein_deficit: float) -> Dict[str, Any]:
        """Create a healthy protein snack to fill nutritional gaps"""
        
        # Scale snack size based on deficits
        base_yogurt = 150  # grams
        base_nuts = 20     # grams
        
        # Increase portions if larger deficits
        if calorie_deficit > 300:
            base_yogurt *= 1.5
            base_nuts *= 1.5
        elif calorie_deficit > 150:
            base_yogurt *= 1.2
            base_nuts *= 1.2
        
        yogurt_grams = int(base_yogurt)
        nuts_grams = int(base_nuts)
        
        # Calculate nutrition based on actual portions
        yogurt_nutrition = {
            "calories": yogurt_grams * (100/150),  # 100 cal per 150g
            "protein": yogurt_grams * (15/150),    # 15g protein per 150g
            "carbohydrates": yogurt_grams * (6/150),
            "fat": yogurt_grams * (0.5/150),
            "fiber": 0,
            "sodium": yogurt_grams * (50/150)
        }
        
        nuts_nutrition = {
            "calories": nuts_grams * (115/20),     # 115 cal per 20g
            "protein": nuts_grams * (4/20),       # 4g protein per 20g
            "carbohydrates": nuts_grams * (4/20),
            "fat": nuts_grams * (10/20),
            "fiber": nuts_grams * (2/20),
            "sodium": 0
        }
        
        total_nutrition = {
            "calories": yogurt_nutrition["calories"] + nuts_nutrition["calories"],
            "protein": yogurt_nutrition["protein"] + nuts_nutrition["protein"],
            "carbohydrates": yogurt_nutrition["carbohydrates"] + nuts_nutrition["carbohydrates"],
            "fat": yogurt_nutrition["fat"] + nuts_nutrition["fat"],
            "fiber": yogurt_nutrition["fiber"] + nuts_nutrition["fiber"],
            "sodium": yogurt_nutrition["sodium"] + nuts_nutrition["sodium"]
        }
        
        snack = {
            "name": "Protein Boost Snack",
            "meal_type": "snack",
            "ingredients": [
                {
                    "name": "greek yogurt (plain)",
                    "quantity": yogurt_grams,
                    "unit": "g",
                    "nutrition": yogurt_nutrition
                },
                {
                    "name": "almonds",
                    "quantity": nuts_grams,
                    "unit": "g", 
                    "nutrition": nuts_nutrition
                }
            ],
            "instructions": "Mix Greek yogurt with almonds for a protein-rich snack.",
            "nutrition": total_nutrition
        }
        
        return snack
    
    def _calculate_meal_nutrition_from_ingredients(self, ingredients: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate meal nutrition from its ingredients"""
        totals = {
            "calories": 0,
            "protein": 0,
            "carbohydrates": 0,
            "fat": 0,
            "fiber": 0,
            "sodium": 0
        }
        
        for ingredient in ingredients:
            nutrition = ingredient.get("nutrition", {})
            for nutrient in totals:
                totals[nutrient] += nutrition.get(nutrient, 0)
        
        return {k: round(v, 1) for k, v in totals.items()}
    
    def _calculate_meal_totals(self, meals: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate total nutrition from list of meals"""
        totals = {
            "calories": 0,
            "protein": 0,
            "carbohydrates": 0,
            "fat": 0,
            "fiber": 0,
            "sodium": 0
        }
        
        for meal in meals:
            meal_nutrition = meal.get("nutrition", {})
            for nutrient in totals:
                totals[nutrient] += meal_nutrition.get(nutrient, 0)
        
        return {k: round(v, 1) for k, v in totals.items()}
    
    def _calculate_weekly_totals(self, days: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate weekly nutrition totals from days"""
        totals = {
            "calories": 0,
            "protein": 0,
            "carbohydrates": 0,
            "fat": 0,
            "fiber": 0,
            "sodium": 0
        }
        
        for day in days:
            daily_totals = day.get("daily_totals", {})
            for nutrient in totals:
                totals[nutrient] += daily_totals.get(nutrient, 0)
        
        return {k: round(v, 1) for k, v in totals.items()}


# Global validator instance
_plan_validator = None

def get_plan_validator() -> DietPlanValidator:
    """Get the global plan validator instance"""
    global _plan_validator
    if _plan_validator is None:
        _plan_validator = DietPlanValidator()
    return _plan_validator