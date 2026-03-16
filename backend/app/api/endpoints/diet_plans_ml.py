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
from typing import Optional, List, Any
from uuid import UUID
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.diet_plan import (
    DietPlanResponse,
    DietPlanSummaryListResponse,
    GenerateWeeklyPlanRequest,
    GenerateDailyPlanRequest,
    SuccessResponse
)
from app.models.diet_plan import DietPlan
from app.models.chat import Chat, Message
from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diet-plans-ml", tags=["diet-plans-ml"])


async def log_diet_event_to_history(
    db: Session, 
    user_id: UUID, 
    event_type: str, 
    scope: str, 
    details: dict
):
    """Log a diet-related event to the user's latest conversation or create a new one"""
    try:
        # Get or create active chat
        chat = db.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.created_at.desc()).first()
        if not chat:
            chat = Chat(user_id=user_id, title="Diet Consultation")
            db.add(chat)
            db.flush() # Ensure chat.id is available without committing yet
        
        # Log the user intent
        if event_type == "generation":
            message_content = f"I want to generate a new {scope} plan."
        elif event_type == "regeneration":
            message_content = f"I want to regenerate the {scope}."
            if scope == "meal":
                message_content = f"I want to regenerate the {details.get('meal_type', 'meal')} for day {details.get('day_index', 0) + 1}."
            elif scope == "day":
                message_content = f"I want to regenerate all meals for day {details.get('day_index', 0) + 1}."
        else:
            message_content = f"Action: {event_type} on {scope}"
        
        user_msg = Message(
            chat_id=chat.id,
            role="user",
            content=message_content,
            metadata_json={"event_type": event_type, "scope": scope, "details": details}
        )
        db.add(user_msg)
        
        # Log the system action
        if event_type == "generation":
            content = f"Great! I've created a personalized {scope} diet plan for you based on your health goals."
        else:
            content = f"Sure! I've regenerated that {scope} for you with updated nutrition and variety."
            
        system_msg = Message(
            chat_id=chat.id,
            role="assistant",
            content=content,
            metadata_json={"action": f"{event_type}_completed", "scope": scope}
        )
        db.add(system_msg)
        # We don't commit here anymore, let the endpoint handle it
    except Exception as e:
        logger.error(f"Failed to log history: {e}")
        # Don't raise, logging failure shouldn't break the main flow


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


def ensure_ml_pipeline_enabled() -> None:
    if not settings.enable_ml_pipeline:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ML pipeline is disabled",
        )


@router.get("/", response_model=DietPlanSummaryListResponse)
async def list_diet_plans(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """List diet plans for the current user"""
    query = db.query(DietPlan).filter(DietPlan.user_id == current_user_id)
    total = query.count()
    plans = query.order_by(DietPlan.created_at.desc()).offset(offset).limit(limit).all()
    
    # Format plans for summary
    formatted_plans = []
    for plan in plans:
        summary = {
            "id": plan.id,
            "plan_type": plan.plan_type,
            "start_date": plan.start_date,
            "created_at": plan.created_at,
            "total_calories": plan.content.get("daily_totals", {}).get("calories") or plan.content.get("weekly_totals", {}).get("calories"),
            "total_meals": len(plan.content.get("meals", [])) if plan.plan_type == "daily" else sum(len(day.get("meals", [])) for day in plan.content.get("days", []))
        }
        formatted_plans.append(summary)
        
    return {"plans": formatted_plans, "total": total}


@router.get("/{plan_id}", response_model=DietPlanResponse)
async def get_diet_plan(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Get a specific diet plan by ID"""
    plan = db.query(DietPlan).filter(
        DietPlan.id == plan_id,
        DietPlan.user_id == current_user_id
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Diet plan not found")
        
    return plan


@router.delete("/{plan_id}", response_model=SuccessResponse)
async def delete_diet_plan(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Delete a diet plan"""
    plan = db.query(DietPlan).filter(
        DietPlan.id == plan_id,
        DietPlan.user_id == current_user_id
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Diet plan not found")
        
    db.delete(plan)
    db.commit()
    
    return {"message": "Diet plan deleted successfully"}


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
    ensure_ml_pipeline_enabled()
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
        orchestrator = get_ml_pipeline_orchestrator(db)
        
        # Phase 1: Heavy Database Discovery
        # Grouping all DB-bound work here to minimize session time
        logger.info(f"[ML_PIPELINE_DISCOVERY] request_id={request_id}")
        constraints = orchestrator._extract_constraints(hcd.json_context or {})
        
        # We'll use a local helper or call discovery directly if we want to be super clean,
        # but since we already refactored orchestrator to group DB work, 
        # we'll just ensure we don't hold a transaction if not needed.
        
        # Actually, let's keep the orchestrator call but be aware it's the AI part that's slow.
        # To truly fix "Slow database session", we could theoretically yield the session back,
        # but that's complex with FastAPI's Dependency Injection.
        # GROUPING DB WORK in orchestrator.py was the key first step.
        
        plan_data = await orchestrator.generate_weekly_plan(
            db=db,
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
        
        # Log to history
        await log_diet_event_to_history(
            db=db,
            user_id=current_user_id,
            event_type="generation",
            scope="weekly",
            details={"plan_id": str(diet_plan.id)}
        )
        
        # Enforce max 3 weekly diet plans per user
        existing_weekly = db.query(DietPlan.id)\
            .filter(DietPlan.user_id == current_user_id)\
            .filter(DietPlan.plan_type == "weekly")\
            .order_by(DietPlan.created_at.desc())\
            .all()
            
        if len(existing_weekly) > 3:
            ids_to_keep = [p[0] for p in existing_weekly[:3]]
            db.query(DietPlan)\
                .filter(DietPlan.user_id == current_user_id)\
                .filter(DietPlan.plan_type == "weekly")\
                .filter(DietPlan.id.notin_(ids_to_keep))\
                .delete(synchronize_session=False)
            db.commit()
        
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
    ensure_ml_pipeline_enabled()
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
        orchestrator = get_ml_pipeline_orchestrator(db)
        
        # Generate plan using ML pipeline
        logger.info(f"[ML_PIPELINE_GENERATING] request_id={request_id}")
        plan_data = await orchestrator.generate_daily_plan(
            db=db,
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
        
        # Log to history
        await log_diet_event_to_history(
            db=db,
            user_id=current_user_id,
            event_type="generation",
            scope="daily",
            details={"plan_id": str(diet_plan.id)}
        )
        
        # Enforce max 3 daily diet plans per user
        existing_daily = db.query(DietPlan.id)\
            .filter(DietPlan.user_id == current_user_id)\
            .filter(DietPlan.plan_type == "daily")\
            .order_by(DietPlan.created_at.desc())\
            .all()
            
        if len(existing_daily) > 3:
            ids_to_keep = [p[0] for p in existing_daily[:3]]
            db.query(DietPlan)\
                .filter(DietPlan.user_id == current_user_id)\
                .filter(DietPlan.plan_type == "daily")\
                .filter(DietPlan.id.notin_(ids_to_keep))\
                .delete(synchronize_session=False)
            db.commit()
        
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
    ensure_ml_pipeline_enabled()
    from app.services.ml_diet_pipeline.orchestrator import get_ml_pipeline_orchestrator
    from app.models.health_context import HealthContextDocument
    from app.models.diet_plan import DietPlan
    
    request_id = f"ml_regen_meal_{plan_id}"
    logger.info(f"[ML_REGENERATE_MEAL_INIT] request_id={request_id}")
    logger.info(f"[USER_REGENERATE] request_id={request_id} user_id={current_user_id} scope=meal")
    
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
        orchestrator = get_ml_pipeline_orchestrator(db)
        
        # Get existing meal to exclude its ingredients (for variety)
        plan_content = plan.content
        exclude_ingredients = set()
        meal_type = "breakfast"
        other_meals_cal = 0
        other_meals_prot = 0
        
        if plan.plan_type == "weekly":
            if "days" in plan_content and day_index < len(plan_content["days"]):
                day = plan_content["days"][day_index]
                if "meals" in day and meal_index < len(day["meals"]):
                    for i, m in enumerate(day["meals"]):
                        if i == meal_index:
                            old_meal = m
                            meal_type = old_meal.get("type", "breakfast")
                            for ing in old_meal.get("ingredients", []):
                                exclude_ingredients.add(ing["name"])
                        else:
                            other_meals_cal += m.get("nutrition", {}).get("calories", 0)
                            other_meals_prot += m.get("nutrition", {}).get("protein", 0)
        else:  # daily
            if "meals" in plan_content and meal_index < len(plan_content["meals"]):
                for i, m in enumerate(plan_content["meals"]):
                    if i == meal_index:
                        old_meal = m
                        meal_type = old_meal.get("type", "breakfast")
                        for ing in old_meal.get("ingredients", []):
                            exclude_ingredients.add(ing["name"])
                    else:
                        other_meals_cal += m.get("nutrition", {}).get("calories", 0)
                        other_meals_prot += m.get("nutrition", {}).get("protein", 0)

        # Calculate remainder daily macros
        constraints = orchestrator._extract_constraints(hcd.json_context or {})
        remaining_cal = max(100, constraints.calorie_target - other_meals_cal)
        remaining_prot = max(5, constraints.protein_target - other_meals_prot)

        # Generate new meal using the ML orchestrator
        new_meal = await orchestrator.regenerate_meal(
            db=db,
            user_id=current_user_id,
            health_context=hcd.json_context or {},
            meal_type=meal_type,
            exclude_ingredients=exclude_ingredients,
            target_calories=remaining_cal,
            target_protein=remaining_prot
        )
        
        # Log to history
        await log_diet_event_to_history(
            db=db, 
            user_id=current_user_id, 
            event_type="regeneration",
            scope="meal", 
            details={"meal_type": meal_type, "day_index": day_index, "plan_id": str(plan_id)}
        )

        # Update plan content
        if plan.plan_type == "weekly":
            day = plan_content["days"][day_index]
            day["meals"][meal_index] = new_meal
            
            # Recalculate daily totals
            day["daily_totals"] = orchestrator.nutrition_engine.calculate_daily_nutrition(day["meals"])
            
            # Recalculate weekly totals
            plan_content["weekly_totals"] = {
                "calories": sum(d["daily_totals"]["calories"] for d in plan_content["days"]),
                "protein": sum(d["daily_totals"]["protein"] for d in plan_content["days"]),
                "carbohydrates": sum(d["daily_totals"]["carbohydrates"] for d in plan_content["days"]),
                "fat": sum(d["daily_totals"]["fat"] for d in plan_content["days"]),
                "fiber": sum(d["daily_totals"]["fiber"] for d in plan_content["days"])
            }
        else:  # daily
            plan_content["meals"][meal_index] = new_meal
            plan_content["daily_totals"] = orchestrator.nutrition_engine.calculate_daily_nutrition(plan_content["meals"])
        
        # Save updated plan - force SQLAlchemy to detect the change
        from sqlalchemy.orm.attributes import flag_modified
        plan.content = plan_content
        flag_modified(plan, "content")
        plan.updated_at = datetime.now()
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
    ensure_ml_pipeline_enabled()
    from app.services.ml_diet_pipeline.orchestrator import get_ml_pipeline_orchestrator
    from app.models.health_context import HealthContextDocument
    from app.models.diet_plan import DietPlan
    from datetime import timedelta
    
    request_id = f"ml_regen_day_{plan_id}"
    logger.info(f"[ML_REGENERATE_DAY_INIT] request_id={request_id}")
    logger.info(f"[USER_REGENERATE] request_id={request_id} user_id={current_user_id} scope=day")
    
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
        orchestrator = get_ml_pipeline_orchestrator(db)
        
        # Handle based on plan type
        if plan.plan_type == "weekly":
            # Calculate target date for this day
            target_date = plan.start_date + timedelta(days=day_index)
            
            # Generate new daily plan
            new_day_plan = await orchestrator.generate_daily_plan(
                db=db,
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
            
            # Log to history
            await log_diet_event_to_history(
                db=db, 
                user_id=current_user_id, 
                event_type="regeneration",
                scope="day", 
                details={"day_index": day_index, "plan_id": str(plan_id)}
            )

            # Save updated plan
            plan.content = plan_content
        else:  # daily plan
            # For daily plans, regenerate the entire day (all meals)
            new_day_plan = await orchestrator.generate_daily_plan(
                db=db,
                user_id=current_user_id,
                health_context=hcd.json_context or {},
                target_date=plan.start_date
            )
            
            # Replace the entire plan content
            plan.content = new_day_plan

            # Log to history for daily plan regeneration
            await log_diet_event_to_history(
                db=db,
                user_id=current_user_id,
                event_type="regeneration",
                scope="day",
                details={"plan_id": str(plan_id)}
            )
        
        # Force SQLAlchemy to detect the change
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(plan, "content")
        plan.updated_at = datetime.now()
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
    ensure_ml_pipeline_enabled()
    from app.services.ml_diet_pipeline.orchestrator import get_ml_pipeline_orchestrator
    from app.models.health_context import HealthContextDocument
    from app.models.diet_plan import DietPlan
    
    request_id = f"ml_regen_full_{plan_id}"
    logger.info(f"[ML_REGENERATE_FULL_INIT] request_id={request_id}")
    logger.info(f"[USER_REGENERATE] request_id={request_id} user_id={current_user_id} scope=full")
    
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
        orchestrator = get_ml_pipeline_orchestrator(db)
        
        # Generate new plan of same type
        if plan.plan_type == "weekly":
            new_plan_data = await orchestrator.generate_weekly_plan(
                db=db,
                user_id=current_user_id,
                health_context=hcd.json_context or {},
                start_date=plan.start_date
            )
        else:  # daily
            new_plan_data = await orchestrator.generate_daily_plan(
                db=db,
                user_id=current_user_id,
                health_context=hcd.json_context or {},
                target_date=plan.start_date
            )
        
        # Log to history
        await log_diet_event_to_history(
            db=db, 
            user_id=current_user_id, 
            event_type="regeneration",
            scope="full_plan", 
            details={"plan_type": plan.plan_type, "plan_id": str(plan_id)}
        )

        # Update plan content
        plan.content = new_plan_data
        
        # Force SQLAlchemy to detect the change
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(plan, "content")
        plan.updated_at = datetime.now()
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
