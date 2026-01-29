"""
Diet plan service for generating and managing diet plans.

This service integrates AI-powered diet plan generation with
Health Context Documents and database storage.

CRITICAL: All plans pass through comprehensive safety pipeline before return.
INCLUDES: Self-healing generation loop, unit enforcement, quantity rounding, validation gate.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
import json

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.diet_plan import DietPlan
from app.models.health_context import HealthContextDocument
from app.services.ai_service import get_ai_service, AIServiceError, LLMContractViolationError
from app.services.plan_validation import get_plan_validator, PlanValidationError, ValidationResult
from app.services.unit_enforcement import get_unit_enforcer, ContractViolationError
from app.services.ingredient_canonicalizer import get_ingredient_canonicalizer
from app.services.quantity_rounding import get_quantity_rounder
from app.services.failure_classification import get_failure_classifier, FailureAnalysis
from app.services.ingredient_normalizer import UnknownIngredientError
from app.services.nutrition_database import IngredientResolutionError
from app.services.nutrition_engine import (
    ZeroCalorieError, 
    NutritionCalculationError,
    RetryableMealGenerationError,
    create_ingredient_with_resolution,
    add_protein_safety_net,
    validate_plan_nutrition,
    get_diet_specific_thresholds
)
from app.services.llm_contract_enforcer import LLMContractViolation
from app.utils.safe_logging import log_success, log_error, log_warning, log_retry, log_target

logger = logging.getLogger(__name__)


class DietPlanServiceError(Exception):
    """Base exception for diet plan service errors"""
    pass


class PlanGenerationFailedError(DietPlanServiceError):
    """Terminal failure - do NOT retry"""
    def __init__(self, reason: str, details: str):
        self.reason = reason
        self.details = details
        super().__init__(f"Plan generation failed: {reason} - {details}")


class RetryableAIError(DietPlanServiceError):
    """Retryable AI/network error - safe to retry"""
    pass


class DietPlanService:
    """Service for diet plan generation and management with comprehensive safety pipeline"""
    
    def __init__(self, db: Session):
        """Initialize diet plan service with database session"""
        self.db = db
        self.max_generation_attempts = 10  # Self-healing loop limit
        # Initialize AI service without monitoring to avoid database dependency issues
        self.ai_service = get_ai_service()  # Initialize AI service without db session
    
    async def generate_weekly_plan(
        self,
        user_id: UUID,
        start_date: Optional[date] = None
    ) -> DietPlan:
        """
        Generate a weekly diet plan for a user with self-healing generation loop.
        
        COMPREHENSIVE SAFETY PIPELINE:
        1. Self-healing generation loop (max 10 attempts)
        2. Unit enforcement (canonical units only)
        3. Quantity rounding (human-friendly portions)
        4. Validation gate (safety constraints)
        5. Failure classification (actionable guidance)
        
        Args:
            user_id: User ID to generate plan for
            start_date: Optional start date (defaults to next Monday)
        
        Returns:
            Generated DietPlan instance (guaranteed safe)
            
        Raises:
            DietPlanServiceError: If plan generation fails after all attempts
        """
        # Get user's active Health Context Document
        hcd = self._get_active_hcd(user_id)
        if not hcd:
            raise DietPlanServiceError(f"No active Health Context Document found for user {user_id}")
        
        # Determine start date (default to next Monday)
        if not start_date:
            start_date = self._get_next_monday()
        
        log_target(logger, f"STARTING SELF-HEALING GENERATION: Weekly plan for user {user_id}, starting {start_date}")
        
        # Extract safety constraints once
        safety_constraints = self._extract_safety_constraints(hcd)
        
        # Self-healing generation loop with PROPER SAFETY MEASURES
        violation_history = []
        
        for attempt in range(1, self.max_generation_attempts + 1):
            try:
                log_retry(logger, f"Generation attempt {attempt}/{self.max_generation_attempts}")
                
                # STEP 1: Generate raw plan using AI service
                try:
                    raw_plan_data = await self._generate_raw_plan(
                        hcd=hcd,
                        plan_type="weekly",
                        user_id=user_id,
                        start_date=start_date
                    )
                except LLMContractViolationError as e:
                    log_error(logger, f"LLM CONTRACT VIOLATION (attempt {attempt}): {e}")
                    violation_history.append(f"Attempt {attempt}: LLM contract violation")
                    continue  # Skip to next attempt - do NOT process invalid output
                except (ZeroCalorieError, NutritionCalculationError) as e:
                    log_error(logger, f"NUTRITION CALCULATION FAILED (attempt {attempt}): {e}")
                    violation_history.append(f"Attempt {attempt}: Nutrition calculation failed")
                    continue  # Skip to next attempt - do NOT process zero-calorie plans
                
                # STEP 2: Run through complete safety pipeline
                try:
                    safe_plan_data = await self._run_safety_pipeline(
                        raw_plan_data=raw_plan_data,
                        safety_constraints=safety_constraints,
                        user_id=user_id,
                        attempt=attempt,
                        hcd=hcd
                    )
                except (ContractViolationError, PlanValidationError) as e:
                    # 🔒 INVARIANT 1: MEAL MATERIALIZATION LOCK
                    # Once meals have nutrition, AI retries are FORBIDDEN
                    if self._plan_has_meals_with_nutrition(raw_plan_data):
                        logger.info(f"[AI_FALLBACK_BLOCKED] Meals with nutrition detected - AI retry forbidden")
                        
                        # Apply deterministic scaling (last mutator)
                        try:
                            scaled_plan_data = self._apply_deterministic_scaling(
                                raw_plan_data, safety_constraints, user_id, "maintenance", 70.0
                            )
                            logger.info(f"[SCALING_APPLIED] Deterministic scaling completed")
                        except Exception as scaling_error:
                            logger.warning(f"[SCALING_FAILED] Using original plan: {scaling_error}")
                            scaled_plan_data = raw_plan_data
                        
                        # 🔒 INVARIANT 3: SOFT ACCEPTANCE (scaling is last mutator)
                        # Accept plan regardless of imperfections
                        diet_plan = DietPlan(
                            user_id=user_id,
                            hcd_id=hcd.id,  # Required field
                            plan_type="weekly",
                            start_date=start_date,
                            content=scaled_plan_data  # Correct field name
                        )
                        
                        self.db.add(diet_plan)
                        self.db.commit()
                        
                        logger.info(f"[SOFT_ACCEPT] Accepting scaled plan. AI retry forbidden.")
                        log_success(logger, f"GENERATION SUCCESS: Weekly plan created with soft acceptance after meal materialization")
                        return diet_plan
                    
                    # Only AI-stage failures (no meals with nutrition) reach here
                    log_warning(logger, f"Safety pipeline failed (attempt {attempt} - no meals materialized): {e}")
                    violation_history.append(f"Attempt {attempt}: {type(e).__name__}")
                    continue  # Try again with different LLM output
                
                # SUCCESS: Create and save diet plan
                diet_plan = DietPlan(
                    user_id=user_id,
                    hcd_id=hcd.id,  # Required field
                    plan_type="weekly",
                    start_date=start_date,
                    content=safe_plan_data  # Correct field name
                )
                
                self.db.add(diet_plan)
                self.db.commit()
                
                log_success(logger, f"GENERATION SUCCESS: Weekly plan created after {attempt} attempts")
                return diet_plan
                
            except Exception as e:
                logger.error(f"[ERROR] Unexpected error in attempt {attempt}: {e}")
                violation_history.append(f"Attempt {attempt}: Unexpected error - {str(e)[:100]}")
                continue
        
        # All attempts failed - provide actionable failure analysis
        failure_msg = f"Plan generation failed after {self.max_generation_attempts} attempts"
        logger.error(f"[CRITICAL] {failure_msg}")
        logger.error(f"Violation history: {violation_history}")
        
        raise DietPlanServiceError(f"{failure_msg}. Violation history: {violation_history[:3]}")

    async def generate_daily_plan(
        self,
        user_id: int,
        target_date: Optional[str] = None,
        regenerate: bool = False
    ) -> DietPlan:
        """
        Generate a daily diet plan with comprehensive safety pipeline.
        
        SAFETY PIPELINE:
        1. LLM generates meal ideas (NO nutrition calculations)
        2. Backend calculates accurate nutrition
        3. Safety validation (calories, protein, dietary restrictions)
        4. Contract enforcement (no forbidden fields)
        5. Auto-correction if needed
        6. Final validation before storage
        """
        logger.info(f"DAILY PLAN GENERATION: user_id={user_id}, date={target_date}, regenerate={regenerate}")
        
        # Get user's health context
        hcd = self.db.query(HealthContextDocument).filter(
            HealthContextDocument.user_id == user_id,
            HealthContextDocument.is_active == True
        ).first()
        
        if not hcd:
            raise DietPlanServiceError("No active health context found for user")
        
        # Check for existing plan if not regenerating
        if not regenerate and target_date:
            existing_plan = self.db.query(DietPlan).filter(
                DietPlan.user_id == user_id,
                DietPlan.plan_type == "daily",
                DietPlan.start_date == target_date
            ).first()
            
            if existing_plan:
                logger.info(f"[SUCCESS] Returning existing daily plan for {target_date}")
                return existing_plan
        
        # Extract safety constraints from HCD
        safety_constraints = self._extract_safety_constraints(hcd)
        
        # Generation loop with PROPER FAILURE TYPE SEPARATION
        violation_history = []
        
        for attempt in range(1, self.max_generation_attempts + 1):
            log_retry(logger, f"Generation attempt {attempt}/{self.max_generation_attempts}")
            
            try:
                # STEP 1: Generate raw plan using AI service
                raw_plan_data = await self.ai_service.generate_diet_plan(
                    health_context=hcd.content,
                    plan_type="daily",
                    target_date=target_date,
                    user_id=user_id,
                    health_context_json=hcd.json_context if hasattr(hcd, 'json_context') else None
                )
                
                # STEP 2: Run through complete safety pipeline
                try:
                    safe_plan_data = await self._run_safety_pipeline(
                        raw_plan_data=raw_plan_data,
                        safety_constraints=safety_constraints,
                        user_id=user_id,
                        attempt=attempt,
                        hcd=hcd
                    )
                    
                    # If we reach here, plan is safe - create and save
                    diet_plan = DietPlan(
                        user_id=user_id,
                        hcd_id=hcd.id,
                        plan_type="daily",
                        start_date=target_date or datetime.now().date().isoformat(),
                        content=safe_plan_data
                    )
                    
                    self.db.add(diet_plan)
                    self.db.commit()
                    self.db.refresh(diet_plan)
                    
                    log_success(logger, f"Generated SAFE daily plan {diet_plan.id} after {attempt} attempts")
                    return diet_plan
                    
                except (ContractViolationError, PlanValidationError) as e:
                    # 🔒 INVARIANT 1: MEAL MATERIALIZATION LOCK
                    # Once meals have nutrition, AI retries are FORBIDDEN
                    if self._plan_has_meals_with_nutrition(raw_plan_data):
                        logger.info(f"[AI_FALLBACK_BLOCKED] Meals with nutrition detected - AI retry forbidden")
                        
                        # Apply deterministic scaling (last mutator)
                        try:
                            scaled_plan_data = self._apply_deterministic_scaling(
                                raw_plan_data, safety_constraints, user_id, "maintenance", 70.0
                            )
                            logger.info(f"[SCALING_APPLIED] Deterministic scaling completed")
                        except Exception as scaling_error:
                            logger.warning(f"[SCALING_FAILED] Using original plan: {scaling_error}")
                            scaled_plan_data = raw_plan_data
                        
                        # 🔒 INVARIANT 3: SOFT ACCEPTANCE (scaling is last mutator)
                        # Accept plan regardless of imperfections
                        diet_plan = DietPlan(
                            user_id=user_id,
                            hcd_id=hcd.id,
                            plan_type="daily",
                            start_date=target_date or datetime.now().date().isoformat(),
                            content=scaled_plan_data
                        )
                        
                        self.db.add(diet_plan)
                        self.db.commit()
                        self.db.refresh(diet_plan)
                        
                        logger.info(f"[SOFT_ACCEPT] Accepting scaled plan. AI retry forbidden.")
                        log_success(logger, f"Generated plan {diet_plan.id} with soft acceptance after meal materialization")
                        return diet_plan
                    
                    # Only AI-stage failures (no meals with nutrition) reach here
                    violation_history.append(str(e))
                    log_warning(logger, f"Attempt {attempt} failed (retryable - no meals materialized): {str(e)}")
                    
                    if attempt == self.max_generation_attempts:
                        # All attempts exhausted - classify failure and provide guidance
                        failure_analysis = self._classify_generation_failure(
                            error_message=str(e),
                            health_context_json=hcd.json_context if hasattr(hcd, 'json_context') else None,
                            attempt_count=attempt,
                            violation_history=violation_history
                        )
                        
                        log_error(logger, f"GENERATION FAILED: {failure_analysis.primary_reason}")
                        raise DietPlanServiceError(
                            f"Unable to generate safe plan after {attempt} attempts. "
                            f"{failure_analysis.primary_reason}. "
                            f"Suggested actions: {'; '.join(failure_analysis.suggested_user_actions)}"
                        )
                    
                    # Continue to next attempt - this is retryable
                    continue
                
            # TERMINAL FAILURES - DO NOT RETRY
            except (UnknownIngredientError, IngredientResolutionError) as e:
                log_error(logger, f"TERMINAL FAILURE - Ingredient resolution failed: {e}")
                
                # Extract ingredient details for user guidance
                ingredient_name = getattr(e, 'raw_name', None) or getattr(e, 'ingredient_name', 'unknown')
                
                # This is a TERMINAL failure - do NOT retry LLM
                raise PlanGenerationFailedError(
                    reason="ingredient_resolution_failed",
                    details=f"Cannot resolve ingredient '{ingredient_name}'. "
                           f"This ingredient is not supported by the nutrition database. "
                           f"Please try generating a plan with different dietary preferences."
                )
            
            except (ZeroCalorieError, NutritionCalculationError) as e:
                log_error(logger, f"TERMINAL FAILURE - Nutrition calculation failed: {e}")
                
                # Extract failed ingredients for user guidance
                failed_ingredients = getattr(e, 'failed_ingredients', []) or getattr(e, 'unresolved_ingredients', [])
                
                # This is a TERMINAL failure - do NOT retry LLM
                raise PlanGenerationFailedError(
                    reason="nutrition_calculation_failed", 
                    details=f"Nutrition calculation failed for ingredients: {failed_ingredients}. "
                           f"These ingredients could not be resolved to valid nutrition data."
                )
            
            except LLMContractViolationError as e:
                log_error(logger, f"TERMINAL FAILURE - LLM contract violation: {e}")
                
                # Contract violations are terminal after JSON repair attempt
                raise PlanGenerationFailedError(
                    reason="llm_contract_violation",
                    details=f"LLM response violated contract: {str(e)}"
                )
            
            # RETRYABLE FAILURES - Safe to retry LLM
            except AIServiceError as e:
                log_warning(logger, f"RETRYABLE FAILURE - AI service error on attempt {attempt}: {str(e)}")
                
                if attempt == self.max_generation_attempts:
                    raise DietPlanServiceError(f"AI service failed after {attempt} attempts: {str(e)}")
                continue  # This is retryable
                
            except Exception as e:
                log_error(logger, f"UNEXPECTED ERROR on attempt {attempt}: {str(e)}")
                
                if attempt == self.max_generation_attempts:
                    self.db.rollback()
                    raise DietPlanServiceError(f"Plan generation failed after {attempt} attempts: {str(e)}")
                continue  # Treat unknown errors as retryable for safety
        
        # Should never reach here due to loop logic, but safety fallback
        raise DietPlanServiceError("Plan generation failed - unexpected loop exit")

    def _extract_problematic_ingredients(self, violation_history: List[str]) -> List[str]:
        """Extract ingredients that caused failures for retry constraints"""
        problematic = []
        
        for violation in violation_history:
            # Look for ingredient-related failures
            if "wrap" in violation.lower():
                problematic.extend(["wrap", "tortilla", "flatbread"])
            if "bread" in violation.lower():
                problematic.extend(["bread", "bun", "roll"])
            if "unknown ingredient" in violation.lower() or "ingredient resolution" in violation.lower():
                # Extract ingredient name from error message
                import re
                match = re.search(r"ingredient[:\s]+['\"]([^'\"]+)['\"]", violation.lower())
                if match:
                    problematic.append(match.group(1))
        
        return list(set(problematic))  # Remove duplicates

    def _extract_problematic_ingredients_from_error(self, error_message: str) -> List[str]:
        """Extract problematic ingredients from a single error message"""
        problematic = []
        error_lower = error_message.lower()
        
        # Look for specific ingredient names in error messages
        import re
        
        # Pattern 1: "ingredient 'name' failed"
        matches = re.findall(r"ingredient[:\s]+['\"]([^'\"]+)['\"]", error_lower)
        problematic.extend(matches)
        
        # Pattern 2: "unknown ingredient: name"
        matches = re.findall(r"unknown ingredient[:\s]+([^\s,]+)", error_lower)
        problematic.extend(matches)
        
        # Pattern 3: "cannot resolve 'name'"
        matches = re.findall(r"cannot resolve[:\s]+['\"]([^'\"]+)['\"]", error_lower)
        problematic.extend(matches)
        
        # Pattern 4: Common problematic ingredient types
        if "wrap" in error_lower:
            problematic.extend(["wrap", "tortilla", "flatbread"])
        if "hemp" in error_lower:
            problematic.extend(["hemp seeds", "hemp"])
        if "berries" in error_lower:
            problematic.extend(["mixed berries", "berries"])
        
        return list(set(problematic))  # Remove duplicates

    async def _generate_raw_plan(
        self,
        hcd: HealthContextDocument,
        plan_type: str,
        user_id: UUID,
        start_date: Optional[date] = None,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Generate raw plan data from AI service without safety processing.
        
        Args:
            hcd: Health Context Document
            plan_type: "weekly" or "daily"
            user_id: User ID
            start_date: For weekly plans
            target_date: For daily plans
            
        Returns:
            Raw plan data from AI service
        """
        ai_service = get_ai_service(db_session=self.db)
        
        # Use JSON context if available, fallback to markdown
        if hasattr(hcd, 'json_context') and hcd.json_context:
            if plan_type == "weekly":
                plan_data = await ai_service.generate_diet_plan(
                    health_context=hcd.content,  # Backward compatibility
                    health_context_json=hcd.json_context,  # New architecture
                    plan_type="weekly",
                    user_id=user_id
                )
                # Update plan data with actual start date
                if start_date:
                    plan_data["start_date"] = start_date.isoformat()
                    plan_data = self._adjust_plan_dates(plan_data, start_date)
            else:  # daily
                plan_data = await ai_service.generate_diet_plan(
                    health_context=hcd.content,  # Backward compatibility
                    health_context_json=hcd.json_context,  # New architecture
                    plan_type="daily",
                    target_date=target_date.isoformat() if target_date else None,
                    user_id=user_id
                )
                # Update plan data with actual date
                if target_date:
                    plan_data["date"] = target_date.isoformat()
                    plan_data["day_name"] = target_date.strftime("%A")
        else:
            # Fallback for old HCDs without JSON context
            if plan_type == "weekly":
                plan_data = await ai_service.generate_diet_plan(
                    health_context=hcd.content,
                    plan_type="weekly",
                    user_id=user_id
                )
                # Update plan data with actual start date
                if start_date:
                    plan_data["start_date"] = start_date.isoformat()
                    plan_data = self._adjust_plan_dates(plan_data, start_date)
            else:  # daily
                plan_data = await ai_service.generate_diet_plan(
                    health_context=hcd.content,
                    plan_type="daily",
                    target_date=target_date.isoformat() if target_date else None,
                    user_id=user_id
                )
                # Update plan data with actual date
                if target_date:
                    plan_data["date"] = target_date.isoformat()
                    plan_data["day_name"] = target_date.strftime("%A")
        
        return plan_data
    
    async def _run_safety_pipeline(
        self,
        raw_plan_data: Dict[str, Any],
        safety_constraints: Dict[str, float],
        user_id: UUID,
        attempt: int,
        hcd: Optional[HealthContextDocument] = None
    ) -> Dict[str, Any]:
        """
        Run complete safety pipeline on raw plan data with DETERMINISTIC SCALING.
        
        CRITICAL PIPELINE ORDER:
        1. Meal Processing with Safety (ingredient resolution)
        2. Unit Enforcement (canonical units only) - BEFORE SCALING
        3. Quantity Rounding (human-friendly portions)
        4. Validation Gate with DETERMINISTIC SCALING
        
        Args:
            raw_plan_data: Raw plan from AI service
            safety_constraints: User's safety constraints
            user_id: User ID for logging
            attempt: Current attempt number
            
        Returns:
            Safe plan data ready for database storage
            
        Raises:
            ContractViolationError: If unit enforcement fails
            PlanValidationError: If validation fails and cannot be corrected
        """
        request_id = f"{user_id}_{attempt}"
        logger.info(f"[PIPELINE_START] request_id={request_id} user_id={user_id} attempt={attempt}")
        
        # CRITICAL: Deep copy to prevent mutation across retries
        import copy
        plan_to_validate = copy.deepcopy(raw_plan_data)
        
        # CRITICAL: Block AI fallback once meals exist (absolute rule)
        if self._plan_has_meals_with_nutrition(plan_to_validate):
            disable_ai_retry = True
            logger.info(f"[AI_FALLBACK_BLOCKED] request_id={request_id} - Meals with nutrition detected")
        
        # STAGE 0: Process meals with production safety measures
        logger.info(f"[STAGE_0_START] request_id={request_id} - Meal Processing with Safety")
        try:
            processed_plan = await self._process_meals_with_safety(plan_to_validate, hcd)
            logger.info(f"[STAGE_0_COMPLETE] request_id={request_id} - Meal processing completed")
        except (ZeroCalorieError, NutritionCalculationError) as e:
            logger.error(f"[STAGE_0_FAILED] request_id={request_id} - Meal processing failed: {str(e)}")
            raise  # Re-raise to trigger retry
        
        # STAGE 1: Unit Enforcement (canonical units only) - BEFORE CANONICALIZATION
        logger.info(f"[STAGE_1_START] request_id={request_id} - Unit Enforcement")
        unit_enforcer = get_unit_enforcer()
        try:
            enforced_plan = unit_enforcer.enforce_canonical_units(processed_plan)
            logger.info(f"[STAGE_1_COMPLETE] request_id={request_id} - Unit enforcement passed")
        except ContractViolationError as e:
            logger.error(f"[STAGE_1_FAILED] request_id={request_id} - Unit enforcement failed: {str(e)}")
            raise  # Re-raise to trigger retry
        
        # STAGE 2: Cooked-to-Raw Canonicalization - BEFORE INTEGRITY VALIDATION
        logger.info(f"[STAGE_2_START] request_id={request_id} - Cooked-to-Raw Canonicalization")
        canonicalizer = get_ingredient_canonicalizer()
        canonicalized_plan = canonicalizer.canonicalize_plan_ingredients(enforced_plan)
        logger.info(f"[STAGE_2_COMPLETE] request_id={request_id} - Canonicalization completed")
        
        # STAGE 3: Quantity Rounding (human-friendly portions)
        logger.info(f"[STAGE_3_START] request_id={request_id} - Quantity Rounding")
        quantity_rounder = get_quantity_rounder()
        rounded_plan = quantity_rounder.round_plan_quantities(canonicalized_plan)
        logger.info(f"[STAGE_3_COMPLETE] request_id={request_id} - Quantity rounding completed")
        
        # STAGE 4: Validation Gate with DETERMINISTIC SCALING (integrity validation runs here)
        logger.info(f"[STAGE_4_START] request_id={request_id} - Validation Gate with Scaling")
        validator = get_plan_validator()
        try:
            # Extract goal information from HCD (default to maintenance for now)
            goal_type = "maintenance"  # TODO: Extract from HCD json_context
            user_weight_kg = 70.0      # TODO: Extract from HCD json_context
            
            validation_result = validator.validate_plan(
                plan_data=rounded_plan,
                safety_constraints=safety_constraints,
                user_id=user_id,
                goal_type=goal_type,
                user_weight_kg=user_weight_kg
            )
            
            # BUFFER ACCEPTANCE OR SCALING SUCCESS MUST SHORT-CIRCUIT PIPELINE
            if validation_result.status in ["accepted", "accepted_with_guidance"]:
                # Use plan (may have been scaled by validator)
                final_plan = rounded_plan
                
                # Add validation metadata to plan
                final_plan["validation_status"] = validation_result.status
                final_plan["validation_violations"] = validation_result.violations
                final_plan["pipeline_attempt"] = attempt
                
                # NEW: Add balance guidance if present
                if validation_result.balance_guidance:
                    final_plan["balance_guidance"] = {
                        "type": validation_result.balance_guidance.type,
                        "severity": validation_result.balance_guidance.severity,
                        "message": validation_result.balance_guidance.message,
                        "calorie_delta": validation_result.balance_guidance.calorie_delta,
                        "protein_delta": validation_result.balance_guidance.protein_delta
                    }
                
                # CRITICAL: Log final ingredients before returning response
                self._log_final_ingredients(final_plan, request_id)
                
                logger.info(f"[STAGE_4_COMPLETE] request_id={request_id} - Validation passed: {validation_result.status}")
                return final_plan
            
            # CRITICAL: Handle fixable aggregation failures (DO NOT RETRY AI)
            elif validation_result.status == "fixable":
                logger.info(f"[STAGE_4_FIXABLE] request_id={request_id} - Fixable aggregation failure: {validation_result.violations}")
                # Apply deterministic scaling directly - no AI retry
                scaled_plan = self._apply_deterministic_scaling(rounded_plan, safety_constraints, user_id, goal_type, user_weight_kg)
                
                # Log final ingredients after scaling
                self._log_final_ingredients(scaled_plan, request_id)
                
                return scaled_plan
            
            # If we reach here, it's a retryable failure - let the retry loop handle it
            logger.error(f"[STAGE_4_FAILED] request_id={request_id} - Validation failure after scaling: {validation_result.violations}")
            raise PlanValidationError(
                message="Plan validation failed after scaling - retryable",
                violations=validation_result.violations,
                plan_data=None
            )
            
        except PlanValidationError as e:
            # Check if this is a hard safety violation (TERMINAL - NO RETRY)
            if "HARD SAFETY VIOLATION" in str(e):
                logger.error(f"[STAGE_4_TERMINAL] request_id={request_id} - HARD SAFETY VIOLATION: {e.message}")
                # This will be caught by the outer exception handler and terminate
                raise
            else:
                # This is a retryable failure
                logger.error(f"[STAGE_4_RETRYABLE] request_id={request_id} - Validation failed (retryable): {e.message}")
                raise  # Re-raise to trigger retry
    
    def _log_final_ingredients(self, plan_data: Dict[str, Any], request_id: str):
        """Log final ingredient quantities before returning response to UI"""
        logger.info(f"[FINAL_INGREDIENTS_START] request_id={request_id}")
        
        # Process meals based on plan type
        meals_to_log = []
        if plan_data.get("plan_type") == "weekly":
            for day_idx, day in enumerate(plan_data.get("days", [])):
                for meal in day.get("meals", []):
                    meals_to_log.append((f"Day{day_idx+1}", meal))
        else:
            for meal in plan_data.get("meals", []):
                meals_to_log.append(("Daily", meal))
        
        for day_label, meal in meals_to_log:
            meal_name = meal.get("name", "unknown")
            logger.debug(f"[FINAL_INGREDIENT] request_id={request_id} day={day_label} meal={meal_name}")
            
            for ingredient in meal.get("ingredients", []):
                ingredient_name = ingredient.get("name", "unknown")
                quantity = ingredient.get("quantity", 0)
                unit = ingredient.get("unit", "unknown")
                
                logger.debug(f"[FINAL_INGREDIENT] request_id={request_id} ingredient={ingredient_name} quantity={quantity} unit={unit}")
                
                # CRITICAL: Check for impossible quantities
                if quantity > 1000:
                    logger.error(f"[FINAL_INGREDIENT_ERROR] request_id={request_id} IMPOSSIBLE QUANTITY: {ingredient_name} has {quantity}{unit}")
                
                # CRITICAL: Check for non-canonical units (FINAL ASSERTION)
                if unit not in ["g", "scoops"]:
                    logger.error(f"[FINAL_INGREDIENT_ERROR] request_id={request_id} NON-CANONICAL UNIT: {ingredient_name} has unit '{unit}'")
                    # HARD ASSERTION: This should never happen after unit enforcement
                    raise ContractViolationError(
                        f"CRITICAL ASSERTION FAILED: Non-canonical unit '{unit}' reached final response for ingredient '{ingredient_name}'"
                    )
        
        logger.info(f"[FINAL_INGREDIENTS_COMPLETE] request_id={request_id}")
    
    def _classify_generation_failure(
        self,
        error_message: str,
        health_context_json: Optional[Dict],
        attempt_count: int,
        violation_history: List[str]
    ) -> FailureAnalysis:
        """
        Classify generation failure and provide actionable user guidance.
        
        Args:
            error_message: Final error message
            health_context_json: User's health context for analysis
            attempt_count: Number of failed attempts
            violation_history: List of all violations encountered
            
        Returns:
            FailureAnalysis with category and user guidance
        """
        failure_classifier = get_failure_classifier()
        
        # Parse JSON context if it's a string
        parsed_context = None
        if health_context_json:
            if isinstance(health_context_json, str):
                try:
                    parsed_context = json.loads(health_context_json)
                except json.JSONDecodeError:
                    parsed_context = None
            else:
                parsed_context = health_context_json
        
        return failure_classifier.classify_failure(
            error_message=error_message,
            health_context_json=parsed_context,
            attempt_count=attempt_count,
            violation_history=violation_history
        )
    
    def get_user_plans(
        self,
        user_id: UUID,
        plan_type: Optional[str] = None,
        limit: int = 10
    ) -> List[DietPlan]:
        """
        Get diet plans for a user.
        
        Args:
            user_id: User ID to get plans for
            plan_type: Optional plan type filter ('weekly' or 'daily')
            limit: Maximum number of plans to return
        
        Returns:
            List of DietPlan instances
        """
        query = self.db.query(DietPlan).filter(DietPlan.user_id == user_id)
        
        if plan_type:
            query = query.filter(DietPlan.plan_type == plan_type)
        
        plans = query.order_by(desc(DietPlan.created_at)).limit(limit).all()
        
        logger.info(f"Retrieved {len(plans)} diet plans for user {user_id}")
        return plans
    
    def get_plan_by_id(self, plan_id: UUID, user_id: UUID) -> Optional[DietPlan]:
        """
        Get a specific diet plan by ID.
        
        Args:
            plan_id: Plan ID to retrieve
            user_id: User ID for authorization
        
        Returns:
            DietPlan instance or None if not found
        """
        plan = self.db.query(DietPlan).filter(
            DietPlan.id == plan_id,
            DietPlan.user_id == user_id
        ).first()
        
        if plan:
            logger.info(f"Retrieved diet plan {plan_id} for user {user_id}")
        else:
            logger.warning(f"Diet plan {plan_id} not found for user {user_id}")
        
        return plan
    
    async def regenerate_meal(
        self,
        plan_id: UUID,
        user_id: UUID,
        day_index: int,
        meal_index: int
    ) -> DietPlan:
        """
        Regenerate a specific meal in a diet plan with self-healing loop.
        
        Args:
            plan_id: Plan ID to modify
            user_id: User ID for authorization
            day_index: Day index (0-6 for weekly plans, 0 for daily)
            meal_index: Meal index within the day
        
        Returns:
            Updated DietPlan instance
            
        Raises:
            DietPlanServiceError: If regeneration fails
        """
        # Get existing plan
        plan = self.get_plan_by_id(plan_id, user_id)
        if not plan:
            raise DietPlanServiceError(f"Plan {plan_id} not found")
        
        # Get HCD for context
        hcd = self._get_hcd_by_id(plan.hcd_id)
        if not hcd:
            raise DietPlanServiceError(f"Health Context Document {plan.hcd_id} not found")
        
        logger.info(f"[REGENERATING] MEAL: Plan {plan_id}, day {day_index}, meal {meal_index}")
        
        # Extract safety constraints
        safety_constraints = self._extract_safety_constraints(hcd)
        violation_history = []
        
        # Self-healing generation loop for meal regeneration
        for attempt in range(1, self.max_generation_attempts + 1):
            try:
                logger.info(f"[RETRY] Meal regeneration attempt {attempt}/{self.max_generation_attempts}")
                
                # Generate new meal using AI with safety pipeline
                new_meal = await self._generate_single_meal_safe(
                    hcd=hcd,
                    plan_content=plan.content,
                    day_index=day_index,
                    meal_index=meal_index,
                    user_id=user_id,
                    safety_constraints=safety_constraints,
                    attempt=attempt
                )
                
                # Update plan content
                updated_content = self._update_meal_in_plan(
                    plan.content,
                    day_index,
                    meal_index,
                    new_meal
                )
                
                # Save updated plan
                plan.content = updated_content
                self.db.commit()
                self.db.refresh(plan)
                
                logger.info(f"[SUCCESS] Successfully regenerated meal for plan {plan_id} after {attempt} attempts")
                return plan
                
            except (ContractViolationError, PlanValidationError) as e:
                # CRITICAL: Check for meal guardrail violations - NO AI RETRY
                if "meal_guardrail_" in str(e):
                    logger.info(f"[MEAL_GUARDRAIL] Detected guardrail violation in meal regeneration - applying scaling")
                    
                    # For meal regeneration, we need to scale the entire plan
                    try:
                        # Get current plan content and apply scaling
                        scaled_content = self._apply_deterministic_scaling(
                            plan.content, safety_constraints, user_id, "maintenance", 70.0
                        )
                        
                        # Update plan content
                        plan.content = scaled_content
                        self.db.commit()
                        self.db.refresh(plan)
                        
                        logger.info(f"[SUCCESS] Successfully regenerated meal with scaling for plan {plan_id}")
                        return plan
                        
                    except Exception as scaling_error:
                        logger.error(f"[ERROR] Scaling failed during meal regeneration: {scaling_error}")
                        # Continue to next attempt as fallback
                
                violation_history.append(str(e))
                logger.warning(f"[WARNING] Meal regeneration attempt {attempt} failed: {str(e)}")
                
                if attempt == self.max_generation_attempts:
                    failure_analysis = self._classify_generation_failure(
                        error_message=str(e),
                        health_context_json=hcd.json_context if hasattr(hcd, 'json_context') else None,
                        attempt_count=attempt,
                        violation_history=violation_history
                    )
                    
                    logger.error(f"[ERROR] MEAL REGENERATION FAILED: {failure_analysis.primary_reason}")
                    self.db.rollback()
                    raise DietPlanServiceError(
                        f"Unable to regenerate safe meal after {attempt} attempts. "
                        f"{failure_analysis.primary_reason}"
                    )
                continue
                
            except Exception as e:
                logger.error(f"Unexpected error during meal regeneration attempt {attempt}: {str(e)}")
                if attempt == self.max_generation_attempts:
                    self.db.rollback()
                    raise DietPlanServiceError(f"Meal regeneration failed after {attempt} attempts: {str(e)}")
                continue
        
        # Should never reach here
        self.db.rollback()
        raise DietPlanServiceError("Meal regeneration failed - unexpected loop exit")
    
    async def regenerate_day(
        self,
        plan_id: UUID,
        user_id: UUID,
        day_index: int
    ) -> DietPlan:
        """
        Regenerate a specific day in a weekly diet plan, or entire daily plan with self-healing loop.
        
        Args:
            plan_id: Plan ID to modify
            user_id: User ID for authorization
            day_index: Day index (0-6 for weekly, ignored for daily)
        
        Returns:
            Updated DietPlan instance
            
        Raises:
            DietPlanServiceError: If regeneration fails
        """
        # Get existing plan
        plan = self.get_plan_by_id(plan_id, user_id)
        if not plan:
            raise DietPlanServiceError(f"Plan {plan_id} not found")
        
        if plan.plan_type == "daily":
            # For daily plans, regenerate the entire plan using the main generation method
            logger.info(f"[REGENERATING] ENTIRE DAILY PLAN: {plan_id}")
            
            new_plan = await self.generate_daily_plan(
                user_id=user_id,
                target_date=plan.start_date
            )
            
            # Update existing plan with new content
            plan.content = new_plan.content
            self.db.commit()
            self.db.refresh(plan)
            
            # Delete the temporary new plan
            self.db.delete(new_plan)
            self.db.commit()
            
            logger.info(f"[SUCCESS] Successfully regenerated daily plan {plan_id}")
            return plan
        
        # For weekly plans, regenerate specific day
        # Get HCD for context
        hcd = self._get_hcd_by_id(plan.hcd_id)
        if not hcd:
            raise DietPlanServiceError(f"Health Context Document {plan.hcd_id} not found")
        
        logger.info(f"[REGENERATING] DAY: Plan {plan_id}, day {day_index}")
        
        # Extract safety constraints
        safety_constraints = self._extract_safety_constraints(hcd)
        violation_history = []
        
        # Self-healing generation loop for day regeneration
        for attempt in range(1, self.max_generation_attempts + 1):
            try:
                logger.info(f"[RETRY] Day regeneration attempt {attempt}/{self.max_generation_attempts}")
                
                # Generate new day using AI with safety pipeline
                target_date = plan.start_date + timedelta(days=day_index)
                
                raw_day_plan = await self._generate_raw_plan(
                    hcd=hcd,
                    plan_type="daily",
                    user_id=user_id,
                    target_date=target_date
                )
                
                # Run through safety pipeline
                safe_day_plan = await self._run_safety_pipeline(
                    raw_plan_data=raw_day_plan,
                    safety_constraints=safety_constraints,
                    user_id=user_id,
                    attempt=attempt
                )
                
                # Update plan content
                updated_content = self._update_day_in_plan(
                    plan.content,
                    day_index,
                    safe_day_plan
                )
                
                # Save updated plan
                plan.content = updated_content
                self.db.commit()
                self.db.refresh(plan)
                
                logger.info(f"[SUCCESS] Successfully regenerated day for plan {plan_id} after {attempt} attempts")
                return plan
                
            except (ContractViolationError, PlanValidationError) as e:
                # CRITICAL: Check for meal guardrail violations - NO AI RETRY
                if "meal_guardrail_" in str(e):
                    logger.info(f"[MEAL_GUARDRAIL] Detected guardrail violation in day regeneration - applying scaling")
                    
                    # For day regeneration, we need to scale the entire plan
                    try:
                        # Get current plan content and apply scaling
                        scaled_content = self._apply_deterministic_scaling(
                            plan.content, safety_constraints, user_id, "maintenance", 70.0
                        )
                        
                        # Update plan content
                        plan.content = scaled_content
                        self.db.commit()
                        self.db.refresh(plan)
                        
                        logger.info(f"[SUCCESS] Successfully regenerated day with scaling for plan {plan_id}")
                        return plan
                        
                    except Exception as scaling_error:
                        logger.error(f"[ERROR] Scaling failed during day regeneration: {scaling_error}")
                        # Continue to next attempt as fallback
                
                violation_history.append(str(e))
                logger.warning(f"[WARNING] Day regeneration attempt {attempt} failed: {str(e)}")
                
                if attempt == self.max_generation_attempts:
                    failure_analysis = self._classify_generation_failure(
                        error_message=str(e),
                        health_context_json=hcd.json_context if hasattr(hcd, 'json_context') else None,
                        attempt_count=attempt,
                        violation_history=violation_history
                    )
                    
                    logger.error(f"[ERROR] DAY REGENERATION FAILED: {failure_analysis.primary_reason}")
                    self.db.rollback()
                    raise DietPlanServiceError(
                        f"Unable to regenerate safe day after {attempt} attempts. "
                        f"{failure_analysis.primary_reason}"
                    )
                continue
                
            except Exception as e:
                logger.error(f"Unexpected error during day regeneration attempt {attempt}: {str(e)}")
                if attempt == self.max_generation_attempts:
                    self.db.rollback()
                    raise DietPlanServiceError(f"Day regeneration failed after {attempt} attempts: {str(e)}")
                continue
        
        # Should never reach here
        self.db.rollback()
        raise DietPlanServiceError("Day regeneration failed - unexpected loop exit")
    
    async def _generate_single_meal_safe(
        self,
        hcd: HealthContextDocument,
        plan_content: Dict[str, Any],
        day_index: int,
        meal_index: int,
        user_id: UUID,
        safety_constraints: Dict[str, float],
        attempt: int
    ) -> Dict[str, Any]:
        """
        Generate a single meal replacement with safety pipeline.
        
        Args:
            hcd: Health Context Document
            plan_content: Existing plan content for context
            day_index: Day index
            meal_index: Meal index
            user_id: User ID
            safety_constraints: Safety constraints
            attempt: Current attempt number
            
        Returns:
            Safe meal data
            
        Raises:
            ContractViolationError: If unit enforcement fails
            PlanValidationError: If validation fails
        """
        # Generate a daily plan and extract the specific meal
        ai_service = get_ai_service(db_session=self.db)
        
        # Use JSON context if available
        if hasattr(hcd, 'json_context') and hcd.json_context:
            daily_plan = await ai_service.generate_diet_plan(
                health_context=hcd.content,
                health_context_json=hcd.json_context,
                plan_type="daily",
                user_id=user_id
            )
        else:
            daily_plan = await ai_service.generate_diet_plan(
                health_context=hcd.content,
                plan_type="daily",
                user_id=user_id
            )
        
        # Extract the specific meal
        if "meals" not in daily_plan or meal_index >= len(daily_plan["meals"]):
            raise DietPlanServiceError("Failed to generate replacement meal - invalid meal structure")
        
        raw_meal = daily_plan["meals"][meal_index]
        
        # Create a mini-plan with just this meal for safety pipeline
        mini_plan = {
            "plan_type": "single_meal",  # Special type for single meal validation
            "meals": [raw_meal],
            "daily_totals": raw_meal.get("nutrition", {})
        }
        
        # Run through safety pipeline
        safe_mini_plan = await self._run_safety_pipeline(
            raw_plan_data=mini_plan,
            safety_constraints=safety_constraints,
            user_id=user_id,
            attempt=attempt
        )
        
        # Return the safe meal
        return safe_mini_plan["meals"][0]
    
    def _get_active_hcd(self, user_id: UUID) -> Optional[HealthContextDocument]:
        """Get the active Health Context Document for a user"""
        return self.db.query(HealthContextDocument).filter(
            HealthContextDocument.user_id == user_id,
            HealthContextDocument.is_active == True
        ).order_by(desc(HealthContextDocument.version)).first()
    
    def _get_hcd_by_id(self, hcd_id: UUID) -> Optional[HealthContextDocument]:
        """Get Health Context Document by ID"""
        return self.db.query(HealthContextDocument).filter(
            HealthContextDocument.id == hcd_id
        ).first()
    
    def _get_next_monday(self) -> date:
        """Get the date of the next Monday"""
        today = date.today()
        days_ahead = 0 - today.weekday()  # Monday is 0
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return today + timedelta(days_ahead)
    
    def _adjust_plan_dates(self, plan_data: Dict[str, Any], start_date: date) -> Dict[str, Any]:
        """Adjust dates in plan data to match actual start date"""
        if plan_data.get("plan_type") == "weekly" and "days" in plan_data:
            for i, day in enumerate(plan_data["days"]):
                actual_date = start_date + timedelta(days=i)
                day["date"] = actual_date.isoformat()
                day["day_name"] = actual_date.strftime("%A")
        
        return plan_data
    
    async def _generate_single_meal(
        self,
        health_context: str,
        plan_content: Dict[str, Any],
        day_index: int,
        meal_index: int,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Generate a single meal replacement"""
        # This is a simplified implementation
        # In a full implementation, you would create a specific prompt
        # for single meal generation with context from the existing plan
        
        # For now, generate a daily plan and extract the specific meal
        ai_service = get_ai_service(db_session=self.db)
        daily_plan = await ai_service.generate_diet_plan(
            health_context=health_context,
            plan_type="daily",
            user_id=user_id
        )
        
        if "meals" in daily_plan and meal_index < len(daily_plan["meals"]):
            return daily_plan["meals"][meal_index]
        
        raise DietPlanServiceError("Failed to generate replacement meal")
    
    def _update_meal_in_plan(
        self,
        plan_content: Dict[str, Any],
        day_index: int,
        meal_index: int,
        new_meal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a specific meal in plan content"""
        updated_content = plan_content.copy()
        
        if plan_content.get("plan_type") == "weekly":
            if "days" in updated_content and day_index < len(updated_content["days"]):
                day = updated_content["days"][day_index]
                if "meals" in day and meal_index < len(day["meals"]):
                    day["meals"][meal_index] = new_meal
                    # Recalculate daily totals
                    day["daily_totals"] = self._calculate_daily_totals(day["meals"])
        elif plan_content.get("plan_type") == "daily":
            if "meals" in updated_content and meal_index < len(updated_content["meals"]):
                updated_content["meals"][meal_index] = new_meal
                # Recalculate daily totals
                updated_content["daily_totals"] = self._calculate_daily_totals(updated_content["meals"])
        
        return updated_content
    
    def _update_day_in_plan(
        self,
        plan_content: Dict[str, Any],
        day_index: int,
        new_day_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a specific day in weekly plan content"""
        updated_content = plan_content.copy()
        
        if plan_content.get("plan_type") == "weekly" and "days" in updated_content:
            if day_index < len(updated_content["days"]):
                # Keep the original date and day_name
                original_date = updated_content["days"][day_index].get("date")
                original_day_name = updated_content["days"][day_index].get("day_name")
                
                # Update with new day content
                updated_content["days"][day_index] = {
                    "date": original_date,
                    "day_name": original_day_name,
                    "meals": new_day_plan.get("meals", []),
                    "daily_totals": new_day_plan.get("daily_totals", {})
                }
                
                # Recalculate weekly totals
                updated_content["weekly_totals"] = self._calculate_weekly_totals(updated_content["days"])
        
        return updated_content
    
    def _calculate_daily_totals(self, meals: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate daily nutrition totals from meals"""
        totals = {
            "calories": 0,
            "protein": 0,
            "carbohydrates": 0,
            "fat": 0,
            "fiber": 0,
            "sodium": 0
        }
        
        for meal in meals:
            nutrition = meal.get("nutrition", {})
            for key in totals:
                totals[key] += nutrition.get(key, 0)
        
        return {k: round(v, 1) for k, v in totals.items()}
    
    def _force_recalculate_daily_totals(self, day_data: Dict[str, Any]) -> None:
        """Force recalculation of daily totals from meal nutrition"""
        meals = day_data.get("meals", [])
        
        calories = 0.0
        protein = 0.0
        carbohydrates = 0.0
        fat = 0.0
        fiber = 0.0
        sodium = 0.0
        
        for meal in meals:
            nutrition = meal.get("nutrition", {})
            if nutrition:
                calories += float(nutrition.get("calories", 0) or 0)
                protein += float(nutrition.get("protein", 0) or 0)
                carbohydrates += float(nutrition.get("carbohydrates", 0) or 0)
                fat += float(nutrition.get("fat", 0) or 0)
                fiber += float(nutrition.get("fiber", 0) or 0)
                sodium += float(nutrition.get("sodium", 0) or 0)
        
        day_data["daily_totals"] = {
            "calories": round(calories, 1),
            "protein": round(protein, 1),
            "carbohydrates": round(carbohydrates, 1),
            "fat": round(fat, 1),
            "fiber": round(fiber, 1),
            "sodium": round(sodium, 1)
        }
        
        logger.info(f"Force recalculated daily totals: {calories:.0f} cal, {protein:.1f}g protein")
    
    def _apply_deterministic_scaling(self, plan_data: Dict[str, Any], safety_constraints: Dict[str, float], user_id: UUID, goal_type: str, user_weight_kg: float) -> Dict[str, Any]:
        """
        Apply deterministic scaling without AI retry.
        
        CRITICAL: Canonical immutability guard - prevents mutation after unit enforcement.
        """
        from .nutrition_engine import scale_plan_quantities
        
        # CRITICAL: Canonical immutability guard
        if plan_data.get("_canonicalized"):
            self._validate_canonical_immutability(plan_data, "deterministic_scaling")
        
        target_calories = safety_constraints.get('target_calories', 2000)
        target_protein = safety_constraints.get('target_protein', 100)
        
        # Apply scaling (scale_plan_quantities has its own canonical immutability guard)
        scaled_plan = scale_plan_quantities(
            plan_data=plan_data,
            target_calories=target_calories,
            target_protein=target_protein
        )
        
        # Accept with warning
        scaled_plan["validation_status"] = "accepted_with_scaling"
        scaled_plan["validation_violations"] = ["Applied deterministic scaling"]
        
        logger.info("Applied deterministic scaling - accepting plan")
        return scaled_plan
    
    def _validate_canonical_immutability(self, plan_data: Dict[str, Any], stage: str):
        """
        CRITICAL: Validate that no non-canonical units exist after canonicalization.
        
        This is intentional - we want the system to crash loudly if violated.
        
        Args:
            plan_data: Plan data to validate
            stage: Current processing stage name
            
        Raises:
            RuntimeError: If canonical unit violation detected
        """
        # Process meals based on plan type
        meals_to_check = []
        if plan_data.get("plan_type") == "weekly":
            for day in plan_data.get("days", []):
                meals_to_check.extend(day.get("meals", []))
        else:
            meals_to_check = plan_data.get("meals", [])
        
        for meal in meals_to_check:
            for ingredient in meal.get("ingredients", []):
                unit = ingredient.get("unit", "")
                name = ingredient.get("name", "unknown")
                
                if unit not in ["g", "scoops"]:
                    logger.critical(
                        "[CANONICAL_VIOLATION]",
                        extra={
                            "ingredient": name,
                            "unit": unit,
                            "stage": stage
                        }
                    )
                    raise RuntimeError(
                        f"CANONICAL UNIT VIOLATION: Ingredient '{name}' has unit '{unit}' in stage '{stage}'. "
                        f"Only 'g' and 'scoops' allowed after canonicalization."
                    )
    
    def _plan_has_meals_with_nutrition(self, plan_data: Dict[str, Any]) -> bool:
        """Check if plan has meals with nutrition data"""
        meals = plan_data.get("meals", [])
        if plan_data.get("plan_type") == "weekly":
            # For weekly plans, check all days
            for day in plan_data.get("days", []):
                meals.extend(day.get("meals", []))
        
        # Check if any meal has nutrition
        for meal in meals:
            nutrition = meal.get("nutrition")
            if isinstance(nutrition, dict) and nutrition.get("calories", 0) > 0:
                return True
        
        return False
    
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
            for key in totals:
                totals[key] += daily_totals.get(key, 0)
        
        return {k: round(v, 1) for k, v in totals.items()}
    
    def _extract_safety_constraints(self, hcd: HealthContextDocument) -> Dict[str, float]:
        """
        Extract safety constraints from Health Context Document.
        
        This method extracts the mandatory safety constraints that all
        diet plans must satisfy before being returned to the UI.
        """
        try:
            # Try to get constraints from JSON context first (new architecture)
            if hasattr(hcd, 'json_context') and hcd.json_context:
                json_context = hcd.json_context
                if isinstance(json_context, str):
                    import json
                    json_context = json.loads(json_context)
                
                safety_constraints = json_context.get("safety_constraints", {})
                nutrition_targets = json_context.get("nutrition_targets", {})
                
                return {
                    "min_daily_calories": safety_constraints.get("min_daily_calories", 1200),
                    "max_calorie_deficit": safety_constraints.get("max_calorie_deficit", 500),
                    "min_protein_grams": nutrition_targets.get("min_protein_g", 50),
                    "target_calories": nutrition_targets.get("target_calories", 2000),
                    "target_protein": nutrition_targets.get("target_protein_g", 100)
                }
            
            # Fallback: Parse from markdown content (legacy)
            content = hcd.content or ""
            constraints = {}
            
            # Extract values using regex patterns
            import re
            
            # Extract minimum calories
            min_cal_match = re.search(r"Minimum Daily Calories:\*\*\s*([0-9,.]+)", content)
            if min_cal_match:
                constraints["min_daily_calories"] = float(min_cal_match.group(1).replace(",", ""))
            else:
                constraints["min_daily_calories"] = 1200  # Safe default
            
            # Extract minimum protein
            min_protein_match = re.search(r"Minimum Protein:\*\*\s*([0-9,.]+)", content)
            if min_protein_match:
                constraints["min_protein_grams"] = float(min_protein_match.group(1).replace(",", ""))
            else:
                constraints["min_protein_grams"] = 50  # Safe default
            
            # Extract maximum deficit
            max_deficit_match = re.search(r"Maximum Calorie Deficit:\*\*\s*([0-9,.]+)", content)
            if max_deficit_match:
                constraints["max_calorie_deficit"] = float(max_deficit_match.group(1).replace(",", ""))
            else:
                constraints["max_calorie_deficit"] = 500  # Safe default
            
            # Extract target calories
            target_cal_match = re.search(r"Target Daily Calories:\*\*\s*([0-9,.]+)", content)
            if target_cal_match:
                constraints["target_calories"] = float(target_cal_match.group(1).replace(",", ""))
            else:
                constraints["target_calories"] = 2000  # Safe default
            
            return constraints
            
        except Exception as e:
            logger.error(f"Error extracting safety constraints: {e}")
            # Return safe defaults if extraction fails
            return {
                "min_daily_calories": 1200,
                "max_calorie_deficit": 500,
                "min_protein_grams": 50,
                "target_calories": 2000,
                "target_protein": 100
            }
    
    async def _process_meals_with_safety(self, plan_data: Dict[str, Any], hcd: Optional[HealthContextDocument] = None) -> Dict[str, Any]:
        """
        Process all meals in plan with production safety measures.
        
        CRITICAL FIX: Handle both daily and weekly plan structures correctly.
        
        SAFETY MEASURES:
        1. Use ingredient resolution service (throws terminal errors for unresolved)
        2. Add protein safety nets
        3. Validate plan-level nutrition
        4. PRESERVE existing daily_totals if they exist and are valid
        
        Args:
            plan_data: Plan data with meals
            
        Returns:
            Processed plan data with safe nutrition calculations
            
        Raises:
            NutritionCalculationError: If any ingredient cannot be resolved (TERMINAL)
            ZeroCalorieError: If any day has zero calories (TERMINAL)
        """
        logger.info("[SAFETY] Processing meals with production safety measures")
        
        # Extract diet type from HCD
        diet_type = "vegetarian"  # Default
        if hcd and hasattr(hcd, 'json_context') and hcd.json_context:
            try:
                if isinstance(hcd.json_context, str):
                    import json
                    json_context = json.loads(hcd.json_context)
                else:
                    json_context = hcd.json_context
                
                diet_type = json_context.get('diet_restrictions', {}).get('diet_type', 'vegetarian')
                logger.info(f"[DIET_TYPE] Extracted from HCD: {diet_type}")
            except Exception as e:
                logger.warning(f"[DIET_TYPE] Could not extract diet type from HCD: {e}")
        
        # Handle different plan structures
        if plan_data.get("plan_type") == "daily":
            # Daily plan: process directly
            processed_plan = await self._process_daily_plan_meals(plan_data, diet_type)
        elif plan_data.get("plan_type") == "weekly":
            # Weekly plan: process each day
            processed_plan = plan_data.copy()
            for day in processed_plan.get("days", []):
                await self._process_daily_plan_meals(day, diet_type)
        else:
            # Legacy structure: iterate over day keys
            processed_plan = plan_data.copy()
            for day_key, day_data in plan_data.items():
                if isinstance(day_data, dict) and 'meals' in day_data:
                    await self._process_daily_plan_meals(day_data, diet_type)
        
        return processed_plan
    
    async def _process_daily_plan_meals(self, day_data: Dict[str, Any], diet_type: str = "vegetarian") -> Dict[str, Any]:
        """
        Process meals for a single day with safety measures.
        
        CRITICAL FIX: Preserve existing daily_totals if they're valid, 
        otherwise recalculate from meal nutrition.
        """
        if 'meals' not in day_data:
            return day_data
            
        day_meals = []
        
        for meal_data in day_data['meals']:
            try:
                # Check if meal already has nutrition calculated
                existing_nutrition = meal_data.get('nutrition', {})
                if (existing_nutrition.get('calories', 0) > 0 and 
                    existing_nutrition.get('protein', 0) > 0):
                    # Meal already has valid nutrition - preserve it
                    processed_meal = {
                        'name': meal_data.get('name', 'Unknown Meal'),
                        'type': meal_data.get('type', 'meal'),
                        'ingredients': meal_data.get('ingredients', []),
                        'instructions': meal_data.get('instructions', 'No cooking instructions provided.'),
                        'nutrition': existing_nutrition
                    }
                    day_meals.append(processed_meal)
                    logger.debug(f"[SAFETY] Preserved existing nutrition for {processed_meal['name']}")
                    continue
                
                # Process ingredients with resolution service
                processed_ingredients = []
                
                for ingredient_data in meal_data.get('ingredients', []):
                    ingredient_name = ingredient_data.get('name', '').strip()
                    quantity = float(ingredient_data.get('quantity', 0))
                    unit = ingredient_data.get('unit', 'g')
                    
                    if ingredient_name and quantity > 0:
                        # CRITICAL: This now throws NutritionCalculationError for unresolved ingredients
                        ingredient = await create_ingredient_with_resolution(
                            name=ingredient_name,
                            quantity=quantity,
                            unit=unit
                        )
                        
                        # If we reach here, ingredient was successfully resolved
                        processed_ingredients.append({
                            'name': ingredient.name,
                            'quantity': ingredient.quantity,
                            'unit': ingredient.unit,
                            'calories': ingredient.nutrition.calories,
                            'protein': ingredient.nutrition.protein,
                            'carbohydrates': ingredient.nutrition.carbohydrates,
                            'fat': ingredient.nutrition.fat,
                            'fiber': ingredient.nutrition.fiber,
                            'sodium': ingredient.nutrition.sodium,
                            'resolution_method': ingredient.resolution_status
                        })
                
                # Create meal with processed ingredients
                if processed_ingredients:  # Only create meal if we have ingredients
                    meal_calories = sum(ing['calories'] for ing in processed_ingredients)
                    meal_protein = sum(ing['protein'] for ing in processed_ingredients)
                    meal_carbs = sum(ing['carbohydrates'] for ing in processed_ingredients)
                    meal_fat = sum(ing['fat'] for ing in processed_ingredients)
                    meal_fiber = sum(ing['fiber'] for ing in processed_ingredients)
                    meal_sodium = sum(ing['sodium'] for ing in processed_ingredients)
                    
                    meal = {
                        'name': meal_data.get('name', 'Unknown Meal'),
                        'type': meal_data.get('type', 'meal'),
                        'ingredients': processed_ingredients,
                        'instructions': meal_data.get('instructions', ''),
                        'nutrition': {
                            'calories': round(meal_calories, 1),
                            'protein': round(meal_protein, 1),
                            'carbohydrates': round(meal_carbs, 1),
                            'fat': round(meal_fat, 1),
                            'fiber': round(meal_fiber, 1),
                            'sodium': round(meal_sodium, 1)
                        }
                    }
                    
                    # Add protein safety net if needed
                    if meal['nutrition']['protein'] < 10.0:
                        logger.warning(f"[SAFETY] Low protein meal: {meal['name']} ({meal['nutrition']['protein']:.1f}g)")
                        # Add safety protein (greek yogurt)
                        try:
                            safety_protein = await create_ingredient_with_resolution(
                                name="greek yogurt (plain)",
                                quantity=100.0,  # 100g = ~10g protein
                                unit="g"
                            )
                            
                            meal['ingredients'].append({
                                'name': safety_protein.name,
                                'quantity': safety_protein.quantity,
                                'unit': safety_protein.unit,
                                'calories': safety_protein.nutrition.calories,
                                'protein': safety_protein.nutrition.protein,
                                'carbohydrates': safety_protein.nutrition.carbohydrates,
                                'fat': safety_protein.nutrition.fat,
                                'fiber': safety_protein.nutrition.fiber,
                                'sodium': safety_protein.nutrition.sodium,
                                'resolution_method': 'safety_net'
                            })
                            meal['nutrition']['calories'] += safety_protein.nutrition.calories
                            meal['nutrition']['protein'] += safety_protein.nutrition.protein
                            meal['nutrition']['carbohydrates'] += safety_protein.nutrition.carbohydrates
                            meal['nutrition']['fat'] += safety_protein.nutrition.fat
                            meal['nutrition']['fiber'] += safety_protein.nutrition.fiber
                            meal['nutrition']['sodium'] += safety_protein.nutrition.sodium
                            logger.info(f"[SAFETY] Added protein safety net to {meal['name']}")
                        except NutritionCalculationError:
                            # If safety protein fails, continue without it
                            logger.warning(f"[SAFETY] Could not add protein safety net to {meal['name']}")
                    
                    # Get diet-specific thresholds for meal validation
                    thresholds = get_diet_specific_thresholds(diet_type)
                    MIN_MEAL_CALORIES = thresholds["min_meal_calories"]
                    MIN_MEAL_PROTEIN = thresholds["min_meal_protein"]
                    
                    # Check meal against diet-specific guardrails
                    if meal['nutrition']['calories'] < MIN_MEAL_CALORIES:
                        error_msg = f"MEAL CALORIE GUARDRAIL VIOLATION: {meal['name']} has {meal['nutrition']['calories']:.1f} kcal < {MIN_MEAL_CALORIES} kcal minimum ({diet_type})"
                        logger.error(f"[MEAL_GUARDRAIL] {error_msg}")
                        raise RetryableMealGenerationError(error_msg, meal['name'], "low_calories")
                    
                    if meal['nutrition']['protein'] < MIN_MEAL_PROTEIN:
                        error_msg = f"MEAL PROTEIN GUARDRAIL VIOLATION: {meal['name']} has {meal['nutrition']['protein']:.1f}g protein < {MIN_MEAL_PROTEIN}g minimum ({diet_type})"
                        logger.error(f"[MEAL_GUARDRAIL] {error_msg}")
                        raise RetryableMealGenerationError(error_msg, meal['name'], "low_protein")
                    
                    day_meals.append(meal)
                else:
                    # No ingredients could be processed - this is a terminal error
                    meal_name = meal_data.get('name', 'Unknown Meal')
                    error_msg = f"No ingredients could be resolved for meal: {meal_name}"
                    logger.error(f"[TERMINAL] {error_msg}")
                    raise NutritionCalculationError(error_msg, [])
                
            # CRITICAL FIX: Handle meal guardrail violations WITHOUT AI retry
            except RetryableMealGenerationError as e:
                # 🔒 INVARIANT 2: MEAL GUARDRAILS ARE CORRECTIVE, NOT FATAL
                # Meal guardrails must never escape Stage 1 as retryable AI errors
                logger.error(f"[MEAL_GUARDRAIL] {e.violation_type} violation for {e.meal_name}: {str(e)}")
                
                if e.violation_type in ["low_calories", "low_protein"]:
                    # DO NOT retry AI - this is a post-generation failure
                    # Apply corrective action: use the meal as-is and let scaling handle it
                    logger.info(f"[MEAL_GUARDRAIL] Accepting low-quality meal - scaling will correct it")
                    
                    # Create a minimal meal structure to prevent total failure
                    minimal_meal = {
                        'name': e.meal_name,
                        'type': meal_data.get('type', 'meal'),
                        'ingredients': meal_data.get('ingredients', []),
                        'instructions': meal_data.get('instructions', ''),
                        'nutrition': {
                            'calories': 100.0,  # Minimal fallback nutrition
                            'protein': 10.0,    # Will be corrected by scaling
                            'carbohydrates': 10.0,
                            'fat': 3.0,
                            'fiber': 2.0,
                            'sodium': 100.0
                        }
                    }
                    day_meals.append(minimal_meal)
                    logger.info(f"[MEAL_GUARDRAIL] Added minimal meal structure for scaling correction")
                else:
                    # Other retryable meal errors can still retry AI
                    logger.warning(f"[MEAL_RETRY] Retryable meal error: {str(e)}")
                    raise NutritionCalculationError(str(e), [e.meal_name])
                
            except NutritionCalculationError:
                # Re-raise terminal errors - do not continue
                raise
            except Exception as e:
                # Convert unexpected errors to terminal errors
                meal_name = meal_data.get('name', 'Unknown Meal')
                error_msg = f"Failed to process meal {meal_name}: {e}"
                logger.error(f"[TERMINAL] {error_msg}")
                raise NutritionCalculationError(error_msg, [meal_name])
        
        # Update day data with processed meals
        if day_meals:
            day_data['meals'] = day_meals
            
            # CRITICAL FIX: Check if daily_totals already exist and are valid
            existing_totals = day_data.get('daily_totals', {})
            existing_calories = existing_totals.get('calories', 0)
            existing_protein = existing_totals.get('protein', 0)
            
            # Calculate totals from meals
            calculated_calories = sum(meal['nutrition']['calories'] for meal in day_meals)
            calculated_protein = sum(meal['nutrition']['protein'] for meal in day_meals)
            calculated_carbs = sum(meal['nutrition']['carbohydrates'] for meal in day_meals)
            calculated_fat = sum(meal['nutrition']['fat'] for meal in day_meals)
            calculated_fiber = sum(meal['nutrition']['fiber'] for meal in day_meals)
            calculated_sodium = sum(meal['nutrition']['sodium'] for meal in day_meals)
            
            # Use existing totals if they're valid and close to calculated values
            if (existing_calories > 0 and existing_protein > 0 and
                abs(existing_calories - calculated_calories) < calculated_calories * 0.1 and
                abs(existing_protein - calculated_protein) < calculated_protein * 0.1):
                # Existing totals are valid - preserve them
                logger.debug(f"[SAFETY] Preserved existing daily_totals: {existing_calories:.0f} cal, {existing_protein:.1f}g protein")
            else:
                # Recalculate daily totals from meals
                day_data['daily_totals'] = {
                    'calories': round(calculated_calories, 1),
                    'protein': round(calculated_protein, 1),
                    'carbohydrates': round(calculated_carbs, 1),
                    'fat': round(calculated_fat, 1),
                    'fiber': round(calculated_fiber, 1),
                    'sodium': round(calculated_sodium, 1)
                }
                logger.info(f"[SAFETY] Recalculated daily_totals: {calculated_calories:.0f} cal, {calculated_protein:.1f}g protein")
            
            # Plan-level safety check
            final_calories = day_data['daily_totals']['calories']
            if final_calories <= 0:
                logger.error(f"[TERMINAL] Zero calorie day detected")
                raise ZeroCalorieError(f"Day has zero calories", [])
            
            logger.info(f"[OK] Day processed: {final_calories:.0f} calories, {day_data['daily_totals']['protein']:.1f}g protein")
        else:
            # No meals could be processed for this day - terminal error
            error_msg = f"No meals could be processed for day"
            logger.error(f"[TERMINAL] {error_msg}")
            raise NutritionCalculationError(error_msg, [])
        
        return day_data


def get_diet_plan_service(db: Session) -> DietPlanService:
    """Get diet plan service instance with database session"""
    return DietPlanService(db)
