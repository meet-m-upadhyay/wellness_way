"""
Diet plan API endpoints
"""

import logging
from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Body, BackgroundTasks, Request
from fastapi.security import HTTPBearer
import json
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.diet_plan_service import DietPlanService, DietPlanServiceError
from app.schemas.diet_plan import (
    DietPlanResponse,
    DietPlanListResponse,
    DietPlanSummaryListResponse,
    DietPlanSummary,
    GenerateWeeklyPlanRequest,
    GenerateDailyPlanRequest,
    RegenerateMealRequest,
    RegenerateDayRequest,
    ErrorResponse,
    SafetyViolationResponse,
    SuccessResponse,
    PlanGenerationStatusResponse
)
from app.services.plan_validation import PlanValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diet-plans", tags=["diet-plans"])


# Dependency to get current user ID (simplified for now)
# In a real application, this would extract user ID from JWT token
from fastapi import Header
from typing import Optional

async def parse_daily_request(request: Request) -> GenerateDailyPlanRequest:
    """Custom parser for daily plan requests to handle empty bodies"""
    try:
        body = await request.body()
        if not body or body == b'{}':
            # Empty body, return default request
            return GenerateDailyPlanRequest()
        
        # Parse JSON body
        body_str = body.decode('utf-8')
        body_data = json.loads(body_str)
        
        # Create request object from parsed data
        return GenerateDailyPlanRequest(**body_data)
    except Exception as e:
        logger.error(f"Error parsing request body: {e}")
        # Return default on any parsing error
        return GenerateDailyPlanRequest()


async def parse_weekly_request(request: Request) -> GenerateWeeklyPlanRequest:
    """Custom parser for weekly plan requests to handle empty bodies"""
    try:
        body = await request.body()
        if not body or body == b'{}':
            # Empty body, return default request
            return GenerateWeeklyPlanRequest()
        
        # Parse JSON body
        body_str = body.decode('utf-8')
        body_data = json.loads(body_str)
        
        # Create request object from parsed data
        return GenerateWeeklyPlanRequest(**body_data)
    except Exception as e:
        logger.error(f"Error parsing request body: {e}")
        # Return default on any parsing error
        return GenerateWeeklyPlanRequest()


async def parse_regenerate_meal_request(request: Request) -> RegenerateMealRequest:
    """Custom parser for regenerate meal requests"""
    try:
        body = await request.body()
        body_str = body.decode('utf-8')
        body_data = json.loads(body_str)
        
        # Create request object from parsed data
        return RegenerateMealRequest(**body_data)
    except Exception as e:
        logger.error(f"Error parsing regenerate meal request body: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request body for meal regeneration"
        )


async def parse_regenerate_day_request(request: Request) -> RegenerateDayRequest:
    """Custom parser for regenerate day requests"""
    try:
        body = await request.body()
        body_str = body.decode('utf-8')
        body_data = json.loads(body_str)
        
        # Create request object from parsed data
        return RegenerateDayRequest(**body_data)
    except Exception as e:
        logger.error(f"Error parsing regenerate day request body: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request body for day regeneration"
        )


async def get_current_user_id(x_user_id: Optional[str] = Header(None)) -> UUID:
    """Get current user ID from authentication context or header"""
    # TODO: Implement proper authentication
    # For now, accept user ID from header or use test user UUID
    if x_user_id:
        try:
            return UUID(x_user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
    # Fallback to test user UUID (created during testing)
    return UUID("f53f6cb3-4b52-47ca-9cdb-bb61ece32610")


@router.post("/weekly", response_model=DietPlanResponse, status_code=status.HTTP_201_CREATED)
async def generate_weekly_plan(
    request: Request,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Generate a weekly diet plan for the current user.
    
    This endpoint creates a 7-day diet plan based on the user's active
    Health Context Document. The plan includes breakfast, lunch, dinner,
    and optional snacks for each day.
    
    Args:
        request: FastAPI request object
        db: Database session
        current_user_id: Current user ID from authentication
    
    Returns:
        Generated weekly diet plan
        
    Raises:
        HTTPException: If plan generation fails
    """
    try:
        logger.info(f"Generating weekly diet plan for user {current_user_id}")
        
        # Parse request data using our custom parser
        request_data = await parse_weekly_request(request)
        
        diet_plan_service = DietPlanService(db)
        
        # Generate the weekly plan
        diet_plan = await diet_plan_service.generate_weekly_plan(
            user_id=current_user_id,
            start_date=request_data.start_date
        )
        
        logger.info(f"Successfully generated weekly plan {diet_plan.id}")
        return DietPlanResponse.model_validate(diet_plan)
        
    except DietPlanServiceError as e:
        error_msg = str(e)
        logger.error(f"Weekly plan generation failed: {error_msg}")
        
        # Check if this is a structured failure with user guidance
        if "Suggested actions:" in error_msg:
            # Extract failure analysis from error message
            parts = error_msg.split("Suggested actions:")
            primary_reason = parts[0].strip()
            suggested_actions = parts[1].strip() if len(parts) > 1 else ""
            
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "status": "generation_failed",
                    "primary_reason": primary_reason,
                    "suggested_actions": suggested_actions.split("; ") if suggested_actions else [],
                    "message": "Unable to generate safe diet plan after multiple attempts"
                }
            )
        
        # Check if this is a safety violation
        elif "safety constraints" in error_msg.lower():
            # Extract violations from error message
            violations = [error_msg]
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "status": "rejected",
                    "violations": violations,
                    "message": "Generated plan violates safety constraints and cannot be auto-corrected"
                }
            )
        
        # Provide user-friendly error messages for common issues
        elif "rate limit" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI service is temporarily busy. Please wait a moment and try again."
            )
        elif "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Request timed out. Please try again."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    
    except PlanValidationError as e:
        # Handle validation errors with structured response
        logger.error(f"🚫 Plan validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "status": "rejected",
                "violations": e.violations,
                "message": "Generated plan violates safety constraints"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error during plan generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during plan generation"
        )


@router.post("/daily", response_model=DietPlanResponse, status_code=status.HTTP_201_CREATED)
async def generate_daily_plan(
    request: Request,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Generate a daily diet plan for the current user.
    
    This endpoint creates a single-day diet plan based on the user's active
    Health Context Document. The plan includes all meals for the specified day.
    
    Args:
        request: FastAPI request object
        db: Database session
        current_user_id: Current user ID from authentication
    
    Returns:
        Generated daily diet plan
        
    Raises:
        HTTPException: If plan generation fails
    """
    try:
        logger.info(f"Generating daily diet plan for user {current_user_id}")
        
        # Parse request data using our custom parser
        request_data = await parse_daily_request(request)
        
        diet_plan_service = DietPlanService(db)
        
        # Generate the daily plan
        diet_plan = await diet_plan_service.generate_daily_plan(
            user_id=current_user_id,
            target_date=request_data.target_date
        )
        
        logger.info(f"Successfully generated daily plan {diet_plan.id}")
        return DietPlanResponse.model_validate(diet_plan)
        
    except DietPlanServiceError as e:
        error_msg = str(e)
        logger.error(f"Daily plan generation failed: {error_msg}")
        
        # Check if this is a structured failure with user guidance
        if "Suggested actions:" in error_msg:
            # Extract failure analysis from error message
            parts = error_msg.split("Suggested actions:")
            primary_reason = parts[0].strip()
            suggested_actions = parts[1].strip() if len(parts) > 1 else ""
            
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "status": "generation_failed",
                    "primary_reason": primary_reason,
                    "suggested_actions": suggested_actions.split("; ") if suggested_actions else [],
                    "message": "Unable to generate safe diet plan after multiple attempts"
                }
            )
        
        # Check if this is a safety violation
        elif "safety constraints" in error_msg.lower():
            # Extract violations from error message
            violations = [error_msg]
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "status": "rejected",
                    "violations": violations,
                    "message": "Generated plan violates safety constraints and cannot be auto-corrected"
                }
            )
        
        # Provide user-friendly error messages for common issues
        elif "rate limit" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI service is temporarily busy. Please wait a moment and try again."
            )
        elif "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Request timed out. Please try again."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    
    except PlanValidationError as e:
        # Handle validation errors with structured response
        logger.error(f"🚫 Plan validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "status": "rejected",
                "violations": e.violations,
                "message": "Generated plan violates safety constraints"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error during plan generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during plan generation"
        )


@router.get("", response_model=DietPlanSummaryListResponse)
async def get_user_plans(
    plan_type: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Get diet plans for the current user.
    
    This endpoint retrieves a list of diet plans created by the user,
    with optional filtering by plan type.
    
    Args:
        plan_type: Optional plan type filter ('weekly' or 'daily')
        limit: Maximum number of plans to return (default: 10)
        db: Database session
        current_user_id: Current user ID from authentication
    
    Returns:
        List of user's diet plans
    """
    try:
        logger.info(f"Retrieving diet plans for user {current_user_id}")
        
        diet_plan_service = DietPlanService(db)
        
        # Get user's plans
        plans = diet_plan_service.get_user_plans(
            user_id=current_user_id,
            plan_type=plan_type,
            limit=limit
        )
        
        # Convert to summary format
        plan_summaries = []
        for plan in plans:
            # Calculate summary statistics
            total_calories = None
            total_meals = None
            
            if plan.content:
                if plan.plan_type == "weekly" and "weekly_totals" in plan.content:
                    total_calories = plan.content["weekly_totals"].get("calories")
                    if "days" in plan.content:
                        total_meals = sum(len(day.get("meals", [])) for day in plan.content["days"])
                elif plan.plan_type == "daily" and "daily_totals" in plan.content:
                    total_calories = plan.content["daily_totals"].get("calories")
                    total_meals = len(plan.content.get("meals", []))
            
            plan_summaries.append(DietPlanSummary(
                id=plan.id,
                plan_type=plan.plan_type,
                start_date=plan.start_date,
                created_at=plan.created_at,
                total_calories=total_calories,
                total_meals=total_meals
            ))
        
        logger.info(f"Retrieved {len(plan_summaries)} diet plans for user {current_user_id}")
        return DietPlanSummaryListResponse(
            plans=plan_summaries,
            total=len(plan_summaries)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving diet plans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving plans"
        )


@router.get("/{plan_id}", response_model=DietPlanResponse)
async def get_plan_by_id(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Get a specific diet plan by ID.
    
    This endpoint retrieves the complete details of a specific diet plan,
    including all meals and nutritional information.
    
    Args:
        plan_id: Plan ID to retrieve
        db: Database session
        current_user_id: Current user ID from authentication
    
    Returns:
        Complete diet plan details
        
    Raises:
        HTTPException: If plan not found or access denied
    """
    try:
        logger.info(f"Retrieving diet plan {plan_id} for user {current_user_id}")
        
        diet_plan_service = DietPlanService(db)
        
        # Get the plan
        plan = diet_plan_service.get_plan_by_id(plan_id, current_user_id)
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diet plan {plan_id} not found"
            )
        
        logger.info(f"Successfully retrieved diet plan {plan_id}")
        return DietPlanResponse.model_validate(plan)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving diet plan {plan_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving plan"
        )


@router.post("/{plan_id}/regenerate-meal", response_model=DietPlanResponse)
async def regenerate_meal(
    plan_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Regenerate a specific meal in a diet plan.
    
    This endpoint regenerates a single meal while keeping the rest of the
    plan unchanged. The new meal will respect all dietary constraints and
    preferences.
    
    Args:
        plan_id: Plan ID to modify
        request: FastAPI request object
        db: Database session
        current_user_id: Current user ID from authentication
    
    Returns:
        Updated diet plan with regenerated meal
        
    Raises:
        HTTPException: If regeneration fails
    """
    try:
        # Parse request data using our custom parser
        request_data = await parse_regenerate_meal_request(request)
        
        logger.info(f"Regenerating meal for plan {plan_id}, day {request_data.day_index}, meal {request_data.meal_index}")
        
        diet_plan_service = DietPlanService(db)
        
        # Regenerate the meal
        updated_plan = await diet_plan_service.regenerate_meal(
            plan_id=plan_id,
            user_id=current_user_id,
            day_index=request_data.day_index,
            meal_index=request_data.meal_index
        )
        
        logger.info(f"Successfully regenerated meal for plan {plan_id}")
        return DietPlanResponse.model_validate(updated_plan)
        
    except DietPlanServiceError as e:
        error_msg = str(e)
        logger.error(f"Meal regeneration failed: {error_msg}")
        
        # Provide user-friendly error messages for common issues
        if "rate limit" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI service is temporarily busy. Please wait a moment and try again."
            )
        elif "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Request timed out. Please try again."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    except Exception as e:
        logger.error(f"Unexpected error during meal regeneration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during meal regeneration"
        )


@router.post("/{plan_id}/regenerate-day", response_model=DietPlanResponse)
async def regenerate_day(
    plan_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Regenerate a specific day in a weekly diet plan.
    
    This endpoint regenerates all meals for a specific day while keeping
    the rest of the week unchanged. Only available for weekly plans.
    
    Args:
        plan_id: Plan ID to modify
        request: FastAPI request object
        db: Database session
        current_user_id: Current user ID from authentication
    
    Returns:
        Updated diet plan with regenerated day
        
    Raises:
        HTTPException: If regeneration fails
    """
    try:
        # Parse request data using our custom parser
        request_data = await parse_regenerate_day_request(request)
        
        logger.info(f"Regenerating day {request_data.day_index} for plan {plan_id}")
        
        diet_plan_service = DietPlanService(db)
        
        # Regenerate the day
        updated_plan = await diet_plan_service.regenerate_day(
            plan_id=plan_id,
            user_id=current_user_id,
            day_index=request_data.day_index
        )
        
        logger.info(f"Successfully regenerated day for plan {plan_id}")
        return DietPlanResponse.model_validate(updated_plan)
        
    except DietPlanServiceError as e:
        error_msg = str(e)
        logger.error(f"Day regeneration failed: {error_msg}")
        
        # Provide user-friendly error messages for common issues
        if "rate limit" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI service is temporarily busy. Please wait a moment and try again."
            )
        elif "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Request timed out. Please try again."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    except Exception as e:
        logger.error(f"Unexpected error during day regeneration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during day regeneration"
        )


@router.post("/{plan_id}/regenerate", response_model=DietPlanResponse)
async def regenerate_entire_plan(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Regenerate an entire diet plan.
    
    This endpoint creates a completely new plan of the same type,
    replacing the existing plan content while maintaining the same
    start date and preferences.
    
    Args:
        plan_id: Plan ID to regenerate
        db: Database session
        current_user_id: Current user ID from authentication
    
    Returns:
        Completely regenerated diet plan
        
    Raises:
        HTTPException: If regeneration fails
    """
    try:
        logger.info(f"Regenerating entire plan {plan_id}")
        
        diet_plan_service = DietPlanService(db)
        
        # Get existing plan to determine type and start date
        existing_plan = diet_plan_service.get_plan_by_id(plan_id, current_user_id)
        if not existing_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diet plan {plan_id} not found"
            )
        
        # Generate new plan of the same type
        if existing_plan.plan_type == "weekly":
            new_plan = await diet_plan_service.generate_weekly_plan(
                user_id=current_user_id,
                start_date=existing_plan.start_date
            )
        else:  # daily
            new_plan = await diet_plan_service.generate_daily_plan(
                user_id=current_user_id,
                target_date=existing_plan.start_date
            )
        
        # Update existing plan with new content
        existing_plan.content = new_plan.content
        db.commit()
        db.refresh(existing_plan)
        
        # Delete the temporary new plan
        db.delete(new_plan)
        db.commit()
        
        logger.info(f"Successfully regenerated entire plan {plan_id}")
        return DietPlanResponse.model_validate(existing_plan)
        
    except HTTPException:
        raise
    except DietPlanServiceError as e:
        logger.error(f"Plan regeneration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during plan regeneration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during plan regeneration"
        )


@router.delete("/{plan_id}", response_model=SuccessResponse)
async def delete_plan(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Delete a diet plan.
    
    This endpoint permanently deletes a diet plan. This action cannot be undone.
    
    Args:
        plan_id: Plan ID to delete
        db: Database session
        current_user_id: Current user ID from authentication
    
    Returns:
        Success confirmation
        
    Raises:
        HTTPException: If plan not found or deletion fails
    """
    try:
        logger.info(f"Deleting diet plan {plan_id} for user {current_user_id}")
        
        diet_plan_service = DietPlanService(db)
        
        # Get the plan to verify ownership
        plan = diet_plan_service.get_plan_by_id(plan_id, current_user_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diet plan {plan_id} not found"
            )
        
        # Delete the plan
        db.delete(plan)
        db.commit()
        
        logger.info(f"Successfully deleted diet plan {plan_id}")
        return SuccessResponse(
            message=f"Diet plan {plan_id} deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting diet plan {plan_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error deleting plan"
        )