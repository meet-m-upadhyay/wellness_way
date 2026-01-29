"""
Failure Classification System

This module classifies diet plan generation failures and provides
actionable user guidance based on the root cause analysis.

FAILURE CATEGORIES:
1. Constraint conflict - Protein target too high for calories
2. Unit resolution failure - Ingredient cannot be mapped to raw grams  
3. Diet restriction deadlock - Vegan + allergy + high protein
4. Portion scaling failure - Per-meal protein cap exceeded
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FailureCategory(Enum):
    """Categories of diet plan generation failures"""
    CONSTRAINT_CONFLICT = "constraint_conflict"
    UNIT_RESOLUTION_FAILURE = "unit_resolution_failure"
    DIET_RESTRICTION_DEADLOCK = "diet_restriction_deadlock"
    PORTION_SCALING_FAILURE = "portion_scaling_failure"
    AI_SERVICE_ERROR = "ai_service_error"
    VALIDATION_TIMEOUT = "validation_timeout"


@dataclass
class BlockingIssue:
    """Represents a specific issue blocking plan generation"""
    field: str
    reason: str
    current_value: Optional[Any] = None
    suggested_value: Optional[Any] = None


@dataclass
class FailureAnalysis:
    """Complete failure analysis with actionable guidance"""
    category: FailureCategory
    primary_reason: str
    blocking_issues: List[BlockingIssue]
    suggested_user_actions: List[str]
    technical_details: Optional[str] = None


class FailureClassifier:
    """
    Classifies diet plan generation failures and provides user guidance.
    
    This system analyzes failure patterns and maps them to specific
    Health Context Document fields that users can adjust.
    """
    
    def __init__(self):
        """Initialize failure classifier with analysis patterns"""
        self.constraint_patterns = self._load_constraint_patterns()
        self.unit_patterns = self._load_unit_patterns()
        self.restriction_patterns = self._load_restriction_patterns()
    
    def classify_failure(
        self,
        error_message: str,
        health_context_json: Optional[Dict] = None,
        attempt_count: int = 0,
        violation_history: Optional[List[str]] = None
    ) -> FailureAnalysis:
        """
        Classify failure and provide actionable user guidance.
        
        Args:
            error_message: The error message from failed generation
            health_context_json: User's health context for analysis
            attempt_count: Number of failed attempts
            violation_history: List of violations from all attempts
            
        Returns:
            FailureAnalysis with category and user guidance
        """
        logger.info(f"🔍 CLASSIFYING FAILURE: {error_message[:100]}...")
        
        error_lower = error_message.lower()
        
        # Analyze based on error patterns
        if self._is_constraint_conflict(error_lower, health_context_json):
            return self._analyze_constraint_conflict(error_message, health_context_json)
        
        elif self._is_unit_resolution_failure(error_lower):
            return self._analyze_unit_resolution_failure(error_message)
        
        elif self._is_diet_restriction_deadlock(error_lower, health_context_json):
            return self._analyze_diet_restriction_deadlock(error_message, health_context_json)
        
        elif self._is_portion_scaling_failure(error_lower, violation_history):
            return self._analyze_portion_scaling_failure(error_message, health_context_json)
        
        elif self._is_ai_service_error(error_lower):
            return self._analyze_ai_service_error(error_message)
        
        elif attempt_count >= 10:
            return self._analyze_validation_timeout(error_message, health_context_json)
        
        else:
            return self._analyze_unknown_failure(error_message)
    
    def _is_constraint_conflict(self, error_lower: str, health_context: Optional[Dict]) -> bool:
        """Check if failure is due to conflicting constraints"""
        conflict_indicators = [
            'protein too low', 'calories too low', 'insufficient calories',
            'cannot meet protein target', 'protein target too high',
            'calorie deficit too large', 'unrealistic goal'
        ]
        
        return any(indicator in error_lower for indicator in conflict_indicators)
    
    def _is_unit_resolution_failure(self, error_lower: str) -> bool:
        """Check if failure is due to unit resolution issues"""
        unit_indicators = [
            'banned unit', 'cannot convert unit', 'unit enforcement',
            'non-canonical units', 'cannot map discrete item',
            'cooked ingredient', 'contract violation'
        ]
        
        return any(indicator in error_lower for indicator in unit_indicators)
    
    def _is_diet_restriction_deadlock(self, error_lower: str, health_context: Optional[Dict]) -> bool:
        """Check if failure is due to impossible diet restrictions"""
        if not health_context:
            return False
        
        # Check for restrictive diet + allergies + high protein
        diet_restrictions = health_context.get('diet_restrictions', {})
        nutrition_targets = health_context.get('nutrition_targets', {})
        
        diet_type = diet_restrictions.get('diet_type', '')
        allergies = diet_restrictions.get('allergies', [])
        protein_target = nutrition_targets.get('target_protein_g', 0)
        
        # Vegan/vegetarian + multiple allergies + high protein = potential deadlock
        is_restrictive_diet = diet_type in ['vegan', 'vegetarian']
        has_multiple_allergies = len(allergies) >= 2
        has_high_protein = protein_target > 120  # >120g is quite high
        
        deadlock_indicators = [
            'no suitable ingredients', 'cannot find protein sources',
            'dietary restrictions too restrictive', 'insufficient variety'
        ]
        
        has_deadlock_error = any(indicator in error_lower for indicator in deadlock_indicators)
        
        return (is_restrictive_diet and has_multiple_allergies and has_high_protein) or has_deadlock_error
    
    def _is_portion_scaling_failure(self, error_lower: str, violation_history: Optional[List[str]]) -> bool:
        """Check if failure is due to portion scaling issues"""
        scaling_indicators = [
            'portion too large', 'quantity exceeds maximum',
            'meal protein cap exceeded', 'unrealistic portion size'
        ]
        
        # Also check if multiple attempts failed with similar scaling issues
        if violation_history:
            scaling_violations = sum(1 for v in violation_history 
                                   if any(indicator in v.lower() for indicator in scaling_indicators))
            if scaling_violations >= 3:  # Multiple scaling failures
                return True
        
        return any(indicator in error_lower for indicator in scaling_indicators)
    
    def _is_ai_service_error(self, error_lower: str) -> bool:
        """Check if failure is due to AI service issues"""
        ai_indicators = [
            'rate limit', 'timeout', 'api error', 'service unavailable',
            'invalid json', 'llm error', 'openai error', 'groq error'
        ]
        
        return any(indicator in error_lower for indicator in ai_indicators)
    
    def _analyze_constraint_conflict(self, error_message: str, health_context: Optional[Dict]) -> FailureAnalysis:
        """Analyze constraint conflict failures"""
        blocking_issues = []
        suggested_actions = []
        
        if health_context:
            nutrition_targets = health_context.get('nutrition_targets', {})
            safety_constraints = health_context.get('safety_constraints', {})
            diet_restrictions = health_context.get('diet_restrictions', {})
            
            target_calories = nutrition_targets.get('target_calories', 0)
            target_protein = nutrition_targets.get('target_protein_g', 0)
            min_calories = safety_constraints.get('min_daily_calories', 0)
            meals_per_day = diet_restrictions.get('meals_per_day', 3)
            
            # Analyze specific conflicts
            if target_protein > 0 and target_calories > 0:
                protein_calories = target_protein * 4  # 4 cal per gram protein
                protein_percentage = (protein_calories / target_calories) * 100
                
                if protein_percentage > 40:  # >40% protein is very high
                    blocking_issues.append(BlockingIssue(
                        field="target_protein_g",
                        reason=f"Protein target ({target_protein}g) requires {protein_percentage:.0f}% of calories",
                        current_value=target_protein,
                        suggested_value=int(target_calories * 0.3 / 4)  # 30% of calories from protein
                    ))
                    suggested_actions.append("Reduce protein target to 25-30% of total calories")
            
            if target_calories < min_calories:
                blocking_issues.append(BlockingIssue(
                    field="target_calories",
                    reason=f"Target calories ({target_calories}) below safety minimum ({min_calories})",
                    current_value=target_calories,
                    suggested_value=min_calories + 200
                ))
                suggested_actions.append("Increase daily calorie target")
            
            if meals_per_day < 3 and target_protein > 100:
                per_meal_protein = target_protein / meals_per_day
                if per_meal_protein > 50:  # >50g protein per meal is difficult
                    blocking_issues.append(BlockingIssue(
                        field="meals_per_day",
                        reason=f"Need {per_meal_protein:.0f}g protein per meal with only {meals_per_day} meals",
                        current_value=meals_per_day,
                        suggested_value=4
                    ))
                    suggested_actions.append("Increase meals per day to distribute protein")
        
        if not suggested_actions:
            suggested_actions = [
                "Increase daily calorie target",
                "Reduce protein requirement", 
                "Increase meals per day"
            ]
        
        return FailureAnalysis(
            category=FailureCategory.CONSTRAINT_CONFLICT,
            primary_reason="Nutritional targets conflict with calorie limits or safety constraints",
            blocking_issues=blocking_issues,
            suggested_user_actions=suggested_actions,
            technical_details=error_message
        )
    
    def _analyze_unit_resolution_failure(self, error_message: str) -> FailureAnalysis:
        """Analyze unit resolution failures"""
        return FailureAnalysis(
            category=FailureCategory.UNIT_RESOLUTION_FAILURE,
            primary_reason="AI generated ingredients with non-standard units that cannot be converted",
            blocking_issues=[
                BlockingIssue(
                    field="ai_generation",
                    reason="AI used banned units (cups, pieces, etc.) or cooked ingredients"
                )
            ],
            suggested_user_actions=[
                "Try generating the plan again (AI will use different ingredients)",
                "Simplify dietary restrictions to allow more ingredient options",
                "Contact support if this error persists"
            ],
            technical_details=error_message
        )
    
    def _analyze_diet_restriction_deadlock(self, error_message: str, health_context: Optional[Dict]) -> FailureAnalysis:
        """Analyze diet restriction deadlock failures"""
        blocking_issues = []
        suggested_actions = []
        
        if health_context:
            diet_restrictions = health_context.get('diet_restrictions', {})
            nutrition_targets = health_context.get('nutrition_targets', {})
            
            diet_type = diet_restrictions.get('diet_type', '')
            allergies = diet_restrictions.get('allergies', [])
            foods_to_avoid = diet_restrictions.get('foods_to_avoid', [])
            protein_target = nutrition_targets.get('target_protein_g', 0)
            
            if diet_type in ['vegan', 'vegetarian'] and protein_target > 100:
                blocking_issues.append(BlockingIssue(
                    field="diet_type + target_protein_g",
                    reason=f"{diet_type.title()} diet with {protein_target}g protein target is very challenging",
                    current_value=f"{diet_type}, {protein_target}g protein"
                ))
                suggested_actions.append("Reduce protein target for plant-based diets")
            
            if len(allergies) >= 2:
                blocking_issues.append(BlockingIssue(
                    field="allergies",
                    reason=f"Multiple allergies ({', '.join(allergies)}) severely limit ingredient options",
                    current_value=allergies
                ))
                suggested_actions.append("Remove non-essential allergies if safe to do so")
            
            if len(foods_to_avoid) >= 3:
                blocking_issues.append(BlockingIssue(
                    field="foods_to_avoid",
                    reason=f"Many avoided foods ({len(foods_to_avoid)} items) limit meal variety",
                    current_value=foods_to_avoid
                ))
                suggested_actions.append("Reduce foods to avoid list to essential items only")
        
        if not suggested_actions:
            suggested_actions = [
                "Reduce protein target for restrictive diets",
                "Minimize allergy and avoidance lists",
                "Consider less restrictive diet type temporarily"
            ]
        
        return FailureAnalysis(
            category=FailureCategory.DIET_RESTRICTION_DEADLOCK,
            primary_reason="Combination of diet restrictions makes it impossible to meet nutritional targets",
            blocking_issues=blocking_issues,
            suggested_user_actions=suggested_actions,
            technical_details=error_message
        )
    
    def _analyze_portion_scaling_failure(self, error_message: str, health_context: Optional[Dict]) -> FailureAnalysis:
        """Analyze portion scaling failures"""
        return FailureAnalysis(
            category=FailureCategory.PORTION_SCALING_FAILURE,
            primary_reason="Required portion sizes exceed practical cooking limits",
            blocking_issues=[
                BlockingIssue(
                    field="meals_per_day",
                    reason="Too few meals to distribute protein target practically"
                )
            ],
            suggested_user_actions=[
                "Increase meals per day to 4-5 meals",
                "Reduce protein target to more achievable levels",
                "Add protein snacks between main meals"
            ],
            technical_details=error_message
        )
    
    def _analyze_ai_service_error(self, error_message: str) -> FailureAnalysis:
        """Analyze AI service errors"""
        if 'rate limit' in error_message.lower():
            reason = "AI service is temporarily busy due to high demand"
            actions = ["Wait 1-2 minutes and try again", "Try during off-peak hours"]
        elif 'timeout' in error_message.lower():
            reason = "AI service request timed out"
            actions = ["Try again with a simpler request", "Check internet connection"]
        else:
            reason = "AI service is temporarily unavailable"
            actions = ["Try again in a few minutes", "Contact support if problem persists"]
        
        return FailureAnalysis(
            category=FailureCategory.AI_SERVICE_ERROR,
            primary_reason=reason,
            blocking_issues=[],
            suggested_user_actions=actions,
            technical_details=error_message
        )
    
    def _analyze_validation_timeout(self, error_message: str, health_context: Optional[Dict]) -> FailureAnalysis:
        """Analyze validation timeout after max attempts"""
        return FailureAnalysis(
            category=FailureCategory.VALIDATION_TIMEOUT,
            primary_reason="Unable to generate a valid plan after multiple attempts",
            blocking_issues=[
                BlockingIssue(
                    field="overall_configuration",
                    reason="Current settings make it very difficult to generate valid plans"
                )
            ],
            suggested_user_actions=[
                "Increase calorie target significantly",
                "Reduce protein target to moderate levels",
                "Simplify dietary restrictions",
                "Increase meals per day to 4-5"
            ],
            technical_details=f"Failed after 10 attempts: {error_message}"
        )
    
    def _analyze_unknown_failure(self, error_message: str) -> FailureAnalysis:
        """Analyze unknown failure types"""
        return FailureAnalysis(
            category=FailureCategory.AI_SERVICE_ERROR,
            primary_reason="An unexpected error occurred during plan generation",
            blocking_issues=[],
            suggested_user_actions=[
                "Try generating the plan again",
                "Simplify your requirements temporarily",
                "Contact support with error details"
            ],
            technical_details=error_message
        )
    
    def _load_constraint_patterns(self) -> Dict[str, Any]:
        """Load constraint conflict analysis patterns"""
        return {
            'high_protein_thresholds': {
                'moderate': 100,  # grams
                'high': 120,
                'extreme': 150
            },
            'protein_percentage_limits': {
                'reasonable': 30,  # % of calories
                'high': 35,
                'extreme': 40
            }
        }
    
    def _load_unit_patterns(self) -> Dict[str, Any]:
        """Load unit resolution patterns"""
        return {
            'banned_units': ['cup', 'tbsp', 'piece', 'large', 'medium'],
            'conversion_failures': ['cannot map', 'unknown unit', 'discrete item']
        }
    
    def _load_restriction_patterns(self) -> Dict[str, Any]:
        """Load diet restriction patterns"""
        return {
            'restrictive_diets': ['vegan', 'vegetarian'],
            'high_allergy_threshold': 2,
            'high_avoidance_threshold': 3
        }


# Global failure classifier instance
_failure_classifier = None

def get_failure_classifier() -> FailureClassifier:
    """Get the global failure classifier instance"""
    global _failure_classifier
    if _failure_classifier is None:
        _failure_classifier = FailureClassifier()
    return _failure_classifier