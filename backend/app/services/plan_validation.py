"""
Diet Plan Validation Service - Stable and User-Friendly

This module implements goal-specific acceptance buffers that mirror real nutrition science.
Plans that are nutritionally safe and realistic are accepted with optional guidance,
preventing infinite AI retries and token exhaustion.

CRITICAL POLICY SHIFT:
- Daily perfection -> Goal-aware safe ranges with weekly logic
- Hard safety bounds -> REJECT (NEVER RETRY)
- Outside exact target but inside safe range -> ACCEPT + GUIDE USER  
- Inside exact target -> ACCEPT silently

GOAL-SPECIFIC ACCEPTANCE RULES (RESEARCH-BACKED):
1. WEIGHT LOSS: 15-25% deficit, ±10% daily acceptable, protein ≥90% target
2. MUSCLE GAIN: 5-15% surplus, ±10-15% acceptable, protein ≥90% target  
3. MAINTENANCE: TDEE ±15-20% acceptable, protein ≥90% target

GLOBAL NON-NEGOTIABLES:
- Zero-calorie plans impossible
- Protein <75% of minimum -> reject
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
    
    # Protein ranges  
    target_protein: float
    min_acceptable_protein: float
    max_acceptable_protein: float
    
    # Goal metadata
    goal_type: str  # "weight_loss", "muscle_gain", "maintenance"
    user_weight_kg: float


@dataclass
class BalanceGuidance:
    """Optional balance guidance for users when plan is acceptable but not exact"""
    type: str = "informational"  # "informational", "warning"
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
            
            min_acceptable = target_calories * (1 - calorie_buffer)
            max_acceptable = target_calories * (1 + calorie_buffer)
            
        elif goal_type == "muscle_gain":
            # MUSCLE GAIN: 5-15% surplus, ±10-15% acceptable
            calorie_buffer = 0.15  # ±15% (more flexible for bulking)
            protein_buffer = 0.10  # ±10%
            
            min_acceptable = target_calories * (1 - calorie_buffer)
            max_acceptable = target_calories * (1 + calorie_buffer)
            
        else:  # maintenance
            # MAINTENANCE: TDEE ±15-20% acceptable
            calorie_buffer = 0.20  # ±20% (most flexible)
            protein_buffer = 0.15  # ±15%
            
            min_acceptable = target_calories * (1 - calorie_buffer)
            max_acceptable = target_calories * (1 + calorie_buffer)
        
        # Protein ranges
        min_acceptable_protein = target_protein_g * (1 - protein_buffer)
        max_acceptable_protein = target_protein_g * (1 + protein_buffer)
        
        return GoalRanges(
            target_calories=target_calories,
            min_acceptable_calories=min_acceptable,
            max_acceptable_calories=max_acceptable,
            target_protein=target_protein_g,
            min_acceptable_protein=min_acceptable_protein,
            max_acceptable_protein=max_acceptable_protein,
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
        Create user-friendly balance guidance with actionable suggestions.
        
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
        
        # Generate user-friendly guidance messages with specific suggestions
        messages = []
        suggestions = []
        
        # Calorie guidance with reassuring tone and specific suggestions
        if calorie_delta < -50:  # Significantly low
            steps_needed = int(abs(calorie_delta) / 0.04)  # ~0.04 cal per step
            messages.append(f"You're ~{abs(calorie_percent):.0f}% below today's calorie target. This is safe.")
            
            # Add specific food suggestions
            if abs(calorie_delta) <= 100:
                suggestions.extend([
                    f"Add 1 medium banana (~100 kcal)",
                    f"Add 150g curd (~90 kcal)",
                    f"Walk ~{steps_needed:,} fewer steps today"
                ])
            elif abs(calorie_delta) <= 200:
                suggestions.extend([
                    f"Add a banana + peanut butter (~{abs(calorie_delta):.0f} kcal)",
                    f"Add 1 protein scoop (24g assumed)",
                    f"Add 200g greek yogurt (~120 kcal)"
                ])
            else:
                suggestions.extend([
                    f"Add a healthy snack (~{abs(calorie_delta):.0f} kcal)",
                    f"Increase portion sizes slightly",
                    f"Add nuts or seeds to meals"
                ])
                
        elif calorie_delta > 50:  # Significantly high
            steps_needed = int(calorie_delta / 0.04)  # ~0.04 cal per step
            messages.append(f"You're ~{calorie_percent:.0f}% above target today. No harm done.")
            
            # Add activity suggestions
            if calorie_delta <= 100:
                suggestions.extend([
                    f"Add a 15-20 min walk",
                    f"Take the stairs today",
                    f"Walk ~{steps_needed:,} extra steps"
                ])
            else:
                suggestions.extend([
                    f"Add a 30 min walk",
                    f"Slightly reduce carbs at dinner",
                    f"Choose lighter cooking methods"
                ])
        
        # Protein guidance with reassuring tone and specific suggestions
        if protein_delta < -3:  # Significantly low
            messages.append(f"Protein is ~{abs(protein_percent):.0f}% below target.")
            
            # Add protein-specific suggestions
            if abs(protein_delta) <= 10:
                suggestions.extend([
                    f"Add a small serving of paneer (~8g protein)",
                    f"Add 100g greek yogurt (~10g protein)",
                    f"Add a handful of almonds (~6g protein)"
                ])
            else:
                suggestions.extend([
                    f"Add 1 protein scoop (24g assumed)",
                    f"Add tofu to your meal (~15g protein per 100g)",
                    f"Include more legumes in meals"
                ])
                
        elif protein_delta > 5:  # Significantly high (less concerning)
            messages.append(f"Protein is {protein_percent:.0f}% above target. This is excellent for your goals.")
        
        if not messages:
            return None
        
        # Determine severity and UI hint
        severity = "medium" if abs(calorie_percent) > 15 or abs(protein_percent) > 15 else "low"
        
        # Combine messages and suggestions
        final_message = " ".join(messages)
        if suggestions:
            final_message += f" Optional suggestions: {', OR '.join(suggestions[:3])}."  # Limit to 3 suggestions
        final_message += " This is a suggestion, not a requirement."
        
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
        GOAL-AWARE VALIDATION WITH DETERMINISTIC SCALING: Accept plans within safe buffers or scale quantities.
        
        NEW VALIDATION FLOW:
        1. Check integrity violations (immediate reject)
        2. ZERO-STATE VALIDATION GUARD (critical fix)
        3. Compute goal-specific acceptable ranges
        4. Check hard safety bounds -> REJECT (NEVER RETRY)
        5. Check acceptable buffer -> ACCEPT + optional guidance (SHORT-CIRCUIT)
        6. Outside buffer -> SCALE QUANTITIES DETERMINISTICALLY
        7. Revalidate after scaling -> ACCEPT or limited retry
        
        Args:
            plan_data: Raw plan data from AI service
            safety_constraints: User's safety constraints from HCD
            user_id: User ID for logging
            goal_type: "weight_loss", "muscle_gain", "maintenance"
            user_weight_kg: User's weight in kg
            
        Returns:
            ValidationResult with validation status and optional balance guidance
            
        Raises:
            PlanValidationError: Only if plan violates hard safety bounds (TERMINAL)
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
        elif plan_data.get("plan_type") == "single_meal":
            # Special handling for single meal validation
            actual_calories, actual_protein = self._extract_single_meal_totals(plan_data)
        else:
            actual_calories, actual_protein = self._extract_daily_totals(plan_data)
        
        # CRITICAL FIX: ZERO-STATE VALIDATION GUARD
        # Only trigger zero-state if meals are missing or have no nutrition
        if actual_calories is None or actual_protein is None:
            # Check if this is truly a zero-state (no meals) or just missing totals
            meals = plan_data.get("meals", []) if plan_data.get("plan_type") != "weekly" else []
            if plan_data.get("plan_type") == "weekly":
                # For weekly plans, check if any day has meals
                for day in plan_data.get("days", []):
                    meals.extend(day.get("meals", []))
            
            if not meals:
                logger.warning("ZERO-STATE DETECTED: No meals found in plan")
                return ValidationResult(
                    is_valid=False,
                    status="retryable_failure",
                    violations=["No meals found - retryable"],
                    balance_guidance=None
                )
            
            # Check if all meals have no nutrition
            if all(not meal.get("nutrition") for meal in meals):
                logger.warning("ZERO-STATE DETECTED: All meals have no nutrition")
                return ValidationResult(
                    is_valid=False,
                    status="retryable_failure",
                    violations=["All meals missing nutrition - retryable"],
                    balance_guidance=None
                )
            
            # If we have meals with nutrition but totals are None, this is FIXABLE
            logger.warning("FIXABLE: Meals exist with nutrition but totals extraction failed")
            return ValidationResult(
                is_valid=False,
                status="fixable",
                violations=["Nutrition aggregation missing - fixable"],
                balance_guidance=None
            )
        
        # Additional check for zero values (but not None)
        if actual_calories == 0 or actual_protein == 0:
            logger.warning("ZERO-STATE DETECTED: Nutrition totals are zero")
            return ValidationResult(
                is_valid=False,
                status="retryable_failure",
                violations=["Nutrition totals are zero - retryable"],
                balance_guidance=None
            )
        
        logger.info(f"Actual nutrition: {actual_calories:.0f} kcal, {actual_protein:.1f}g protein")
        
        # STEP 4: CHECK HARD SAFETY BOUNDS (immediate reject - NEVER RETRY)
        # Only trigger for truly dangerous plans after aggregation is complete
        hard_violations = []
        
        # For single meals, use different safety thresholds
        if plan_data.get("plan_type") == "single_meal":
            # Single meal safety: minimum 150 calories, 8g protein per meal
            absolute_min_calories = 150
            absolute_min_protein = 8
        else:
            # Hard safety: 75% of minimum requirement (not buffer minimum)
            absolute_min_calories = safety_constraints.get('min_daily_calories', 1200) * 0.75
            absolute_min_protein = safety_constraints.get('min_protein_grams', 50) * 0.75  # Use safety constraint, not weight-based
        
        if actual_calories < absolute_min_calories:
            hard_violations.append(f"Dangerously low calories: {actual_calories:.0f} < {absolute_min_calories:.0f} (75% of minimum)")
        
        if actual_protein < absolute_min_protein:
            hard_violations.append(f"Critically low protein: {actual_protein:.1f}g < {absolute_min_protein:.1f}g (75% of minimum)")
        
        if hard_violations:
            logger.error(f"HARD SAFETY VIOLATIONS: {hard_violations}")
            raise PlanValidationError(
                message="Plan violates hard safety bounds - TERMINAL",
                violations=[f"HARD SAFETY VIOLATION: {v}" for v in hard_violations],
                plan_data=None
            )
        
        # STEP 5: CHECK IF WITHIN ACCEPTABLE BUFFER (accept with optional guidance)
        if plan_data.get("plan_type") == "single_meal":
            # For single meals, just check if they meet minimum thresholds
            within_calorie_buffer = actual_calories >= 150  # Minimum meal calories
            within_protein_buffer = actual_protein >= 8     # Minimum meal protein
        else:
            within_calorie_buffer = self._is_within_buffer(actual_calories, ranges.target_calories, 
                                                         (ranges.max_acceptable_calories - ranges.target_calories) / ranges.target_calories)
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
        
        # STEP 6: OUTSIDE ACCEPTABLE BUFFER - SCALE QUANTITIES DETERMINISTICALLY
        # Skip scaling for single meals - they should be accepted as-is if they meet minimum thresholds
        if plan_data.get("plan_type") == "single_meal":
            logger.info(f"[SINGLE_MEAL] Accepting single meal without scaling: {actual_calories:.0f} kcal, {actual_protein:.1f}g protein")
            return ValidationResult(
                is_valid=True,
                status="accepted",
                violations=[],
                balance_guidance=None
            )
        
        logger.info(f"[SCALING] Plan outside buffer - attempting deterministic scaling")
        logger.info(f"   Calories: {actual_calories:.0f} (target: {ranges.target_calories:.0f})")
        logger.info(f"   Protein: {actual_protein:.1f}g (target: {ranges.target_protein:.1f}g)")
        
        # Import scaling function
        from .nutrition_engine import scale_plan_quantities
        
        # Apply deterministic scaling
        try:
            scaled_plan_data = scale_plan_quantities(
                plan_data=plan_data,
                target_calories=ranges.target_calories,
                target_protein=ranges.target_protein
            )
            
            # Revalidate after scaling
            if scaled_plan_data.get("plan_type") == "weekly":
                scaled_calories, scaled_protein = self._extract_weekly_averages(scaled_plan_data)
            elif scaled_plan_data.get("plan_type") == "single_meal":
                scaled_calories, scaled_protein = self._extract_single_meal_totals(scaled_plan_data)
            else:
                scaled_calories, scaled_protein = self._extract_daily_totals(scaled_plan_data)
            
            logger.info(f"[SCALING] After scaling: {scaled_calories:.0f} kcal, {scaled_protein:.1f}g protein")
            
            # Check if scaling brought us within buffer
            scaled_within_calorie_buffer = self._is_within_buffer(scaled_calories, ranges.target_calories,
                                                                (ranges.max_acceptable_calories - ranges.target_calories) / ranges.target_calories)
            scaled_within_protein_buffer = (scaled_protein >= ranges.min_acceptable_protein)
            
            if scaled_within_calorie_buffer and scaled_within_protein_buffer:
                # SUCCESS: Scaling worked - accept plan
                balance_guidance = self.create_balance_guidance(scaled_calories, scaled_protein, ranges)
                
                # Update the original plan data with scaled values
                plan_data.update(scaled_plan_data)
                
                logger.info(f"[SCALING] SUCCESS: Plan accepted after scaling")
                return ValidationResult(
                    is_valid=True,
                    status="accepted_with_guidance" if balance_guidance else "accepted",
                    violations=[],
                    balance_guidance=balance_guidance
                )
            else:
                # Check if plan is within 90-95% of calorie target (soft acceptance)
                calorie_percentage = scaled_calories / ranges.target_calories
                protein_percentage = scaled_protein / ranges.target_protein
                
                if calorie_percentage >= 0.9 and protein_percentage >= 0.9:
                    # SOFT ACCEPTANCE: Close enough to target, provide advisory note
                    logger.info(f"[SOFT_ACCEPTANCE] Plan within 90-95% of target - accepting with advisory")
                    logger.info(f"   Calories: {scaled_calories:.0f} ({calorie_percentage*100:.1f}% of target)")
                    logger.info(f"   Protein: {scaled_protein:.1f}g ({protein_percentage*100:.1f}% of target)")
                    
                    # Create advisory guidance for user
                    calorie_deficit = ranges.target_calories - scaled_calories
                    advisory_note = f"You are ~{calorie_deficit:.0f} kcal below today's calorie target. Optional ways to balance: • Walk ~{calorie_deficit*2:.0f} extra steps • Add 1 fruit + handful of nuts. This is a suggestion, not a requirement."
                    
                    return ValidationResult(
                        is_valid=True,
                        status="accepted_with_advisory",
                        violations=[],
                        balance_guidance=advisory_note
                    )
                else:
                    # Scaling didn't bring us within buffer - this is now a retryable failure
                    logger.warning(f"[SCALING] Scaling insufficient - still outside buffer")
                    retryable_violations = [f"Plan outside buffer even after scaling: {scaled_calories:.0f} cal, {scaled_protein:.1f}g protein"]
                    
                    return ValidationResult(
                        is_valid=False,
                        status="retryable_failure",
                        violations=retryable_violations,
                        balance_guidance=None
                    )
                
        except Exception as e:
            logger.error(f"[SCALING] Scaling failed: {e}")
            # If scaling fails, fall back to retryable failure
            retryable_violations = [f"Scaling failed: {str(e)}"]
            
            return ValidationResult(
                is_valid=False,
                status="retryable_failure", 
                violations=retryable_violations,
                balance_guidance=None
            )
    
    def _is_within_buffer(self, actual: float, target: float, percent: float) -> bool:
        """Check if actual value is within acceptable buffer of target"""
        return target * (1 - percent) <= actual <= target * (1 + percent)
    
    def _check_integrity_violations(self, plan_data: Dict[str, Any]) -> List[str]:
        """
        Check for integrity violations that must cause immediate rejection.
        
        MANDATORY CHECKS:
        1. No cooked/processed ingredients (SAFETY ASSERTION - should never happen)
        2. No excessive decimal precision  
        3. No fractional discrete items
        4. Protein powder in scoops only
        
        CRITICAL SAFETY ASSERTION:
        If integrity validation ever sees cooked ingredients, this indicates
        that canonicalization was not run before validation - HARD FAIL.
        
        MEAL-LEVEL WARNINGS RULE:
        Warnings such as "Low protein in meal X" are informational only
        and must NEVER affect plan acceptance.
        """
        violations = []
        
        # Extract meals based on plan type
        meals = []
        if plan_data.get("plan_type") == "weekly":
            for day in plan_data.get("days", []):
                meals.extend(day.get("meals", []))
        else:
            meals = plan_data.get("meals", [])
        
        # CRITICAL: Log ingredient names that reach integrity validation
        ingredient_names = []
        for meal in meals:
            for ingredient in meal.get("ingredients", []):
                ingredient_names.append(ingredient.get("name", "unknown"))
        
        logger.info(
            "[INTEGRITY_INPUT]",
            extra={
                "ingredient_names": ingredient_names
            }
        )
        
        for meal_idx, meal in enumerate(meals):
            for ing_idx, ingredient in enumerate(meal.get("ingredients", [])):
                name = ingredient.get("name", "").lower()
                quantity = ingredient.get("quantity", 0)
                unit = ingredient.get("unit", "").lower()
                
                # SAFETY ASSERTION: Check for cooked ingredients (should never happen)
                if self._is_cooked_processed_ingredient(name):
                    logger.critical(
                        "[CRITICAL_ASSERTION_FAILED]",
                        extra={
                            "ingredient": ingredient.get('name', 'unknown'),
                            "stage": "integrity_validation"
                        }
                    )
                    raise RuntimeError(
                        f"CRITICAL: Integrity validation ran before canonicalization. "
                        f"Found cooked ingredient: '{ingredient.get('name', 'unknown')}'. "
                        f"Canonicalization must run BEFORE integrity validation."
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
                
                if daily_totals and daily_totals.get("calories", 0) > 0:
                    # Use existing daily totals
                    total_calories += daily_totals.get("calories", 0)
                    total_protein += daily_totals.get("protein", 0)
                    valid_days += 1
                else:
                    # CRITICAL FIX: Calculate from meals if daily_totals missing
                    logger.warning("Daily totals missing for day - calculating from meals")
                    meals = day.get("meals", [])
                    
                    day_calories = 0
                    day_protein = 0
                    
                    for meal in meals:
                        nutrition = meal.get("nutrition", {})
                        if nutrition:
                            day_calories += nutrition.get("calories", 0)
                            day_protein += nutrition.get("protein", 0)
                        else:
                            # Try legacy format
                            day_calories += meal.get("total_calories", 0)
                            day_protein += meal.get("total_protein", 0)
                    
                    if day_calories > 0:
                        # Update the day with calculated totals
                        day["daily_totals"] = {
                            "calories": round(day_calories, 1),
                            "protein": round(day_protein, 1),
                            "carbohydrates": 0,
                            "fat": 0,
                            "fiber": 0,
                            "sodium": 0
                        }
                        total_calories += day_calories
                        total_protein += day_protein
                        valid_days += 1
                        logger.info(f"Calculated day totals from meals: {day_calories:.0f} cal, {day_protein:.1f}g protein")
            
            if valid_days == 0:
                return None, None
            
            avg_calories = total_calories / valid_days
            avg_protein = total_protein / valid_days
            
            return avg_calories, avg_protein
            
        except Exception as e:
            logger.error(f"Error extracting weekly averages: {e}")
            return None, None
    
    def _extract_daily_totals(self, plan_data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
        """Extract calories and protein from daily plan - STRUCTURE-AGNOSTIC VERSION"""
        calories = 0.0
        protein = 0.0
        
        meals = plan_data.get("meals", [])
        if not meals:
            return None, None
        
        for i, meal in enumerate(meals):
            # DEBUG: Print actual meal structure
            logger.error("[AGG DEBUG] Meal %d keys: %s", i, list(meal.keys()))
            logger.error("[AGG DEBUG] nutrition field: %r", meal.get("nutrition"))
            if meal.get("ingredients"):
                logger.error("[AGG DEBUG] ingredients[0]: %r", meal.get("ingredients", [])[:1])
            
            meal_cal = 0.0
            meal_pro = 0.0
            
            # CASE 1: nutrition is a dict
            n = meal.get("nutrition")
            if isinstance(n, dict):
                meal_cal = float(n.get("calories", 0))
                meal_pro = float(n.get("protein", 0))
                logger.error("[AGG DEBUG] Case 1 (dict): %s cal, %s protein", meal_cal, meal_pro)
            
            # CASE 2: nutrition is NutritionData-like object
            elif hasattr(n, "calories"):
                meal_cal = float(n.calories)
                meal_pro = float(n.protein)
                logger.error("[AGG DEBUG] Case 2 (object): %s cal, %s protein", meal_cal, meal_pro)
            
            # CASE 3: fallback -> sum ingredients
            if meal_cal == 0 and meal.get("ingredients"):
                logger.error("[AGG DEBUG] Case 3: Summing from ingredients")
                for ing in meal["ingredients"]:
                    ing_n = ing.get("nutrition")
                    if isinstance(ing_n, dict):
                        meal_cal += float(ing_n.get("calories", 0))
                        meal_pro += float(ing_n.get("protein", 0))
                    elif hasattr(ing_n, "calories"):
                        meal_cal += float(ing_n.calories)
                        meal_pro += float(ing_n.protein)
                logger.error("[AGG DEBUG] Case 3 result: %s cal, %s protein", meal_cal, meal_pro)
            
            calories += meal_cal
            protein += meal_pro
        
        logger.error("[AGG DEBUG] FINAL TOTALS: %s cal, %s protein", calories, protein)
        
        if calories <= 0 or protein <= 0:
            logger.error("Could not calculate valid totals from meals")
            return None, None
        
        return calories, protein
    
    def _extract_single_meal_totals(self, plan_data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
        """Extract calories and protein from single meal plan"""
        meals = plan_data.get("meals", [])
        if not meals:
            return None, None
        
        # For single meal, just extract from the one meal
        meal = meals[0]
        
        # Try to get nutrition from meal
        nutrition = meal.get("nutrition", {})
        if isinstance(nutrition, dict):
            calories = float(nutrition.get("calories", 0))
            protein = float(nutrition.get("protein", 0))
            
            if calories > 0 and protein > 0:
                return calories, protein
        
        # Fallback: sum from ingredients
        calories = 0.0
        protein = 0.0
        
        for ingredient in meal.get("ingredients", []):
            ing_nutrition = ingredient.get("nutrition", {})
            if isinstance(ing_nutrition, dict):
                calories += float(ing_nutrition.get("calories", 0))
                protein += float(ing_nutrition.get("protein", 0))
        
        if calories > 0 and protein > 0:
            return calories, protein
        
        return None, None


# Global validator instance
_plan_validator = None

def get_plan_validator() -> DietPlanValidator:
    """Get the global plan validator instance"""
    global _plan_validator
    if _plan_validator is None:
        _plan_validator = DietPlanValidator()
    return _plan_validator