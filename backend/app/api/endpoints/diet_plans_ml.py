"""
ML-powered diet plan API endpoints (NEW PIPELINE)

This module implements the ML + constrained GenAI pipeline for diet plan generation.
It lives side-by-side with the existing GenAI-only pipeline without modifying it.

CRITICAL RULES:
- DO NOT modify existing diet_plans.py endpoints
- DO NOT reuse GenAI for numeric decisions
- ALL logic must be isolated under ml_diet_pipeline/
- Failures must be graceful with structured logs
"""

import logging
from typing import Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.diet_plan import (
    DietPlanResponse,
    GenerateWeeklyPlanRequest,
    GenerateDailyPlanRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diet-plans-ml", tags=["diet-plans-ml"])


# Dependency to get current user ID (reuse from existing endpoints)
from fastapi import Header

async def get_current_user_id(x_user_id: Optional[str] = Header(None)) -> UUID:
    """Get current user ID from authentication context or header"""
    if x_user_id:
        try:
            return UUID(x_user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
    # Fallback to test user UUID
    return UUID("f53f6cb3-4b52-47ca-9cdb-bb61ece32610")


async def parse_daily_request(request: Request) -> GenerateDailyPlanRequest:
    """Custom parser for daily plan requests to handle empty bodies"""
    try:
        body = await request.body()
        if not body or body == b'{}':
            return GenerateDailyPlanRequest()
        
        import json
        body_str = body.decode('utf-8')
        body_data = json.loads(body_str)
        return GenerateDailyPlanRequest(**body_data)
    except Exception as e:
        logger.error(f"Error parsing request body: {e}")
        return GenerateDailyPlanRequest()


async def parse_weekly_request(request: Request) -> GenerateWeeklyPlanRequest:
    """Custom parser for weekly plan requests to handle empty bodies"""
    try:
        body = await request.body()
        if not body or body == b'{}':
            return GenerateWeeklyPlanRequest()
        
        import json
        body_str = body.decode('utf-8')
        body_data = json.loads(body_str)
        return GenerateWeeklyPlanRequest(**body_data)
    except Exception as e:
        logger.error(f"Error parsing request body: {e}")
        return GenerateWeeklyPlanRequest()


@router.post("/weekly", response_model=DietPlanResponse, status_code=status.HTTP_201_CREATED)
async def generate_weekly_plan_ml(
    request: Request,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Generate a weekly diet plan using ML + constrained GenAI pipeline.
    
    This endpoint uses the NEW ML-based architecture:
    - ML for ingredient canonicalization
    - ML for meal template selection
    - Deterministic nutrition calculation
    - Constrained GenAI for text generation only
    
    Args:
        request: FastAPI request object
        db: Database session
        current_user_id: Current user ID from authentication
    
    Returns:
        Generated weekly diet plan
        
    Raises:
        HTTPException: If plan generation fails
    """
    from app.services.ml_diet_pipeline.orchestrator import get_ml_pipeline_orchestrator
    from app.models.health_context import HealthContextDocument
    from app.models.diet_plan import DietPlan
    
    request_id = f"ml_weekly_{current_user_id}_{date.today().isoformat()}"
    logger.info(f"[ML_PIPELINE_INIT] request_id={request_id} user_id={current_user_id} plan_type=weekly")
    
    try:
        # Parse request data
        request_data = await parse_weekly_request(request)
        start_date = request_data.start_date or date.today()
        
        # Get user's active Health Context Document
        hcd = db.query(HealthContextDocument).filter(
            HealthContextDocument.user_id == current_user_id,
            HealthContextDocument.is_active == True
        ).first()
        
        if not hcd:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active health context found. Please complete your profile first."
            )
        
        # Get ML pipeline orchestrator
        orchestrator = get_ml_pipeline_orchestrator()
        
        # Generate plan using ML pipeline
        logger.info(f"[ML_PIPELINE_GENERATING] request_id={request_id}")
        plan_data = await orchestrator.generate_weekly_plan(
            user_id=current_user_id,
            health_context=hcd.json_context or {},
            start_date=start_date
        )
        
        # Save to database
        diet_plan = DietPlan(
            user_id=current_user_id,
            hcd_id=hcd.id,
            plan_type="weekly",
            start_date=start_date,
            content=plan_data
        )
        
        db.add(diet_plan)
        db.commit()
        db.refresh(diet_plan)
        
        logger.info(f"[ML_PIPELINE_SUCCESS] request_id={request_id} plan_id={diet_plan.id}")
        
        return DietPlanResponse.model_validate(diet_plan)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ML_PIPELINE_ERROR] request_id={request_id} error={e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML pipeline generation failed: {str(e)}"
        )


@router.post("/daily", response_model=DietPlanResponse, status_code=status.HTTP_201_CREATED)
async def generate_daily_plan_ml(
    request: Request,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Generate a daily diet plan using ML + constrained GenAI pipeline.
    
    This endpoint uses the NEW ML-based architecture:
    - ML for ingredient canonicalization
    - ML for meal template selection
    - Deterministic nutrition calculation
    - Constrained GenAI for text generation only
    
    Args:
        request: FastAPI request object
        db: Database session
        current_user_id: Current user ID from authentication
    
    Returns:
        Generated daily diet plan
        
    Raises:
        HTTPException: If plan generation fails
    """
    from app.services.ml_diet_pipeline.orchestrator import get_ml_pipeline_orchestrator
    from app.models.health_context import HealthContextDocument
    from app.models.diet_plan import DietPlan
    
    request_id = f"ml_daily_{current_user_id}_{date.today().isoformat()}"
    logger.info(f"[ML_PIPELINE_INIT] request_id={request_id} user_id={current_user_id} plan_type=daily")
    
    try:
        # Parse request data
        request_data = await parse_daily_request(request)
        target_date = request_data.target_date or date.today()
        
        # Get user's active Health Context Document
        hcd = db.query(HealthContextDocument).filter(
            HealthContextDocument.user_id == current_user_id,
            HealthContextDocument.is_active == True
        ).first()
        
        if not hcd:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active health context found. Please complete your profile first."
            )
        
        # Get ML pipeline orchestrator
        orchestrator = get_ml_pipeline_orchestrator()
        
        # Generate plan using ML pipeline
        logger.info(f"[ML_PIPELINE_GENERATING] request_id={request_id}")
        plan_data = await orchestrator.generate_daily_plan(
            user_id=current_user_id,
            health_context=hcd.json_context or {},
            target_date=target_date
        )
        
        # Save to database
        diet_plan = DietPlan(
            user_id=current_user_id,
            hcd_id=hcd.id,
            plan_type="daily",
            start_date=target_date,
            content=plan_data
        )
        
        db.add(diet_plan)
        db.commit()
        db.refresh(diet_plan)
        
        logger.info(f"[ML_PIPELINE_SUCCESS] request_id={request_id} plan_id={diet_plan.id}")
        
        return DietPlanResponse.model_validate(diet_plan)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ML_PIPELINE_ERROR] request_id={request_id} error={e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML pipeline generation failed: {str(e)}"
        )


@router.post("/{plan_id}/regenerate-meal-ml", response_model=DietPlanResponse)
async def regenerate_meal_ml(
    plan_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Regenerate a specific meal using ML pipeline.
    
    Args:
        plan_id: Plan ID to modify
        request: FastAPI request object
        db: Database session
        current_user_id: Current user ID from authentication
    
    Returns:
        Updated diet plan with regenerated meal
    """
    from app.services.ml_diet_pipeline.orchestrator import get_ml_pipeline_orchestrator
    from app.models.health_context import HealthContextDocument
    from app.models.diet_plan import DietPlan
    
    request_id = f"ml_regen_meal_{plan_id}"
    logger.info(f"[ML_REGENERATE_MEAL_INIT] request_id={request_id}")
    
    try:
        # Parse request data
        import json
        body = await request.body()
        body_str = body.decode('utf-8')
        body_data = json.loads(body_str)
        
        day_index = body_data.get('day_index', 0)
        meal_index = body_data.get('meal_index', 0)
        
        # Get existing plan
        plan = db.query(DietPlan).filter(
            DietPlan.id == plan_id,
            DietPlan.user_id == current_user_id
        ).first()
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diet plan {plan_id} not found"
            )
        
        # Get user's HCD
        hcd = db.query(HealthContextDocument).filter(
            HealthContextDocument.user_id == current_user_id,
            HealthContextDocument.is_active == True
        ).first()
        
        if not hcd:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active health context found"
            )
        
        # Get orchestrator
        orchestrator = get_ml_pipeline_orchestrator()
        
        # Generate new meal
        meal_types = ["breakfast", "lunch", "dinner", "snack"]
        meal_type = meal_types[meal_index] if meal_index < len(meal_types) else "snack"
        
        # Extract constraints from HCD
        from app.services.ml_diet_pipeline.meal_template_selector import SelectionConstraints, DietType, MealSlot
        
        diet_type_str = hcd.json_context.get("diet_type", "vegetarian").lower()
        diet_type_map = {
            "vegetarian": DietType.VEGETARIAN,
            "vegan": DietType.VEGAN,
            "non-vegetarian": DietType.NON_VEGETARIAN,
            "non_vegetarian": DietType.NON_VEGETARIAN,
            "eggetarian": DietType.EGGETARIAN
        }
        diet_type = diet_type_map.get(diet_type_str, DietType.VEGETARIAN)
        
        meal_slot_map = {
            "breakfast": MealSlot.BREAKFAST,
            "lunch": MealSlot.LUNCH,
            "dinner": MealSlot.DINNER,
            "snack": MealSlot.SNACK
        }
        meal_slot = meal_slot_map.get(meal_type, MealSlot.BREAKFAST)
        
        constraints = SelectionConstraints(
            diet_type=diet_type,
            meal_slot=meal_slot,
            calorie_target=hcd.json_context.get("tdee_calories", 2000) / 3,
            protein_target=hcd.json_context.get("min_protein_grams", 60) / 3,
            allergies=set(hcd.json_context.get("allergies", [])),
            foods_to_avoid=set(hcd.json_context.get("foods_to_avoid", [])),
            preferred_tags=set()
        )
        
        # Select new template
        template_score = orchestrator.template_selector.select_template(constraints)
        
        # Build new meal
        new_meal = await orchestrator._build_meal_from_template(
            template=template_score.template,
            target_calories=constraints.calorie_target,
            target_protein=constraints.protein_target
        )
        
        # Update plan content
        plan_content = plan.content
        
        if plan.plan_type == "weekly":
            if "days" in plan_content and day_index < len(plan_content["days"]):
                day = plan_content["days"][day_index]
                if "meals" in day and meal_index < len(day["meals"]):
                    day["meals"][meal_index] = new_meal
                    
                    # Recalculate daily totals
                    daily_totals = orchestrator.nutrition_adapter.calculate_daily_nutrition(day["meals"])
                    day["daily_totals"] = daily_totals
                    
                    # Recalculate weekly totals
                    weekly_totals = {
                        "calories": sum(d["daily_totals"]["calories"] for d in plan_content["days"]),
                        "protein": sum(d["daily_totals"]["protein"] for d in plan_content["days"]),
                        "carbohydrates": sum(d["daily_totals"]["carbohydrates"] for d in plan_content["days"]),
                        "fat": sum(d["daily_totals"]["fat"] for d in plan_content["days"]),
                        "fiber": sum(d["daily_totals"]["fiber"] for d in plan_content["days"])
                    }
                    plan_content["weekly_totals"] = weekly_totals
        else:  # daily
            if "meals" in plan_content and meal_index < len(plan_content["meals"]):
                plan_content["meals"][meal_index] = new_meal
                
                # Recalculate daily totals
                daily_totals = orchestrator.nutrition_adapter.calculate_daily_nutrition(plan_content["meals"])
                plan_content["daily_totals"] = daily_totals
        
        # Save updated plan - force SQLAlchemy to detect the change
        from sqlalchemy.orm.attributes import flag_modified
        plan.content = plan_content
        flag_modified(plan, "content")
        db.commit()
        db.refresh(plan)
        
        logger.info(f"[ML_REGENERATE_MEAL_SUCCESS] request_id={request_id}")
        
        return DietPlanResponse.model_validate(plan)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ML_REGENERATE_MEAL_ERROR] request_id={request_id} error={e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML meal regeneration failed: {str(e)}"
        )


@router.post("/{plan_id}/regenerate-day-ml", response_model=DietPlanResponse)
async def regenerate_day_ml(
    plan_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Regenerate a specific day using ML pipeline.
    
    Args:
        plan_id: Plan ID to modify
        request: FastAPI request object
        db: Database session
        current_user_id: Current user ID from authentication
    
    Returns:
        Updated diet plan with regenerated day
    """
    from app.services.ml_diet_pipeline.orchestrator import get_ml_pipeline_orchestrator
    from app.models.health_context import HealthContextDocument
    from app.models.diet_plan import DietPlan
    from datetime import timedelta
    
    request_id = f"ml_regen_day_{plan_id}"
    logger.info(f"[ML_REGENERATE_DAY_INIT] request_id={request_id}")
    
    try:
        # Parse request data
        import json
        body = await request.body()
        body_str = body.decode('utf-8')
        body_data = json.loads(body_str)
        
        day_index = body_data.get('day_index', 0)
        
        # Get existing plan
        plan = db.query(DietPlan).filter(
            DietPlan.id == plan_id,
            DietPlan.user_id == current_user_id
        ).first()
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diet plan {plan_id} not found"
            )
        
        # Get user's HCD
        hcd = db.query(HealthContextDocument).filter(
            HealthContextDocument.user_id == current_user_id,
            HealthContextDocument.is_active == True
        ).first()
        
        if not hcd:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active health context found"
            )
        
        # Get orchestrator
        orchestrator = get_ml_pipeline_orchestrator()
        
        # Handle based on plan type
        if plan.plan_type == "weekly":
            # Calculate target date for this day
            target_date = plan.start_date + timedelta(days=day_index)
            
            # Generate new daily plan
            new_day_plan = await orchestrator.generate_daily_plan(
                user_id=current_user_id,
                health_context=hcd.json_context or {},
                target_date=target_date
            )
            
            # Update plan content
            plan_content = plan.content
            
            if "days" in plan_content and day_index < len(plan_content["days"]):
                plan_content["days"][day_index] = new_day_plan
                
                # Recalculate weekly totals
                weekly_totals = {
                    "calories": sum(d["daily_totals"]["calories"] for d in plan_content["days"]),
                    "protein": sum(d["daily_totals"]["protein"] for d in plan_content["days"]),
                    "carbohydrates": sum(d["daily_totals"]["carbohydrates"] for d in plan_content["days"]),
                    "fat": sum(d["daily_totals"]["fat"] for d in plan_content["days"]),
                    "fiber": sum(d["daily_totals"]["fiber"] for d in plan_content["days"])
                }
                plan_content["weekly_totals"] = weekly_totals
            
            # Save updated plan
            plan.content = plan_content
        else:  # daily plan
            # For daily plans, regenerate the entire day (all meals)
            new_day_plan = await orchestrator.generate_daily_plan(
                user_id=current_user_id,
                health_context=hcd.json_context or {},
                target_date=plan.start_date
            )
            
            # Replace the entire plan content
            plan.content = new_day_plan
        
        # Force SQLAlchemy to detect the change
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(plan, "content")
        db.commit()
        db.refresh(plan)
        
        logger.info(f"[ML_REGENERATE_DAY_SUCCESS] request_id={request_id}")
        
        return DietPlanResponse.model_validate(plan)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ML_REGENERATE_DAY_ERROR] request_id={request_id} error={e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML day regeneration failed: {str(e)}"
        )


@router.post("/{plan_id}/regenerate-ml", response_model=DietPlanResponse)
async def regenerate_full_plan_ml(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Regenerate entire plan using ML pipeline.
    
    Args:
        plan_id: Plan ID to regenerate
        db: Database session
        current_user_id: Current user ID from authentication
    
    Returns:
        Completely regenerated diet plan
    """
    from app.services.ml_diet_pipeline.orchestrator import get_ml_pipeline_orchestrator
    from app.models.health_context import HealthContextDocument
    from app.models.diet_plan import DietPlan
    
    request_id = f"ml_regen_full_{plan_id}"
    logger.info(f"[ML_REGENERATE_FULL_INIT] request_id={request_id}")
    
    try:
        # Get existing plan
        plan = db.query(DietPlan).filter(
            DietPlan.id == plan_id,
            DietPlan.user_id == current_user_id
        ).first()
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diet plan {plan_id} not found"
            )
        
        # Get user's HCD
        hcd = db.query(HealthContextDocument).filter(
            HealthContextDocument.user_id == current_user_id,
            HealthContextDocument.is_active == True
        ).first()
        
        if not hcd:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active health context found"
            )
        
        # Get orchestrator
        orchestrator = get_ml_pipeline_orchestrator()
        
        # Generate new plan of same type
        if plan.plan_type == "weekly":
            new_plan_data = await orchestrator.generate_weekly_plan(
                user_id=current_user_id,
                health_context=hcd.json_context or {},
                start_date=plan.start_date
            )
        else:  # daily
            new_plan_data = await orchestrator.generate_daily_plan(
                user_id=current_user_id,
                health_context=hcd.json_context or {},
                target_date=plan.start_date
            )
        
        # Update plan content
        plan.content = new_plan_data
        
        # Force SQLAlchemy to detect the change
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(plan, "content")
        db.commit()
        db.refresh(plan)
        
        logger.info(f"[ML_REGENERATE_FULL_SUCCESS] request_id={request_id}")
        
        return DietPlanResponse.model_validate(plan)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ML_REGENERATE_FULL_ERROR] request_id={request_id} error={e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML full plan regeneration failed: {str(e)}"
        )
