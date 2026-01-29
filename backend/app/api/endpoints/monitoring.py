"""
AI Monitoring API endpoints
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.ai_monitoring import get_monitoring_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


# Dependency to get current user ID (simplified for now)
async def get_current_user_id() -> UUID:
    """Get current user ID from authentication context"""
    # TODO: Implement proper authentication
    return UUID("12345678-1234-5678-9012-123456789012")


@router.get("/ai-usage/summary")
async def get_ai_usage_summary(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    user_id: Optional[UUID] = Query(default=None, description="Filter by specific user ID"),
    db: Session = Depends(get_db)
):
    """
    Get AI usage summary for the specified period.
    
    This endpoint provides comprehensive usage statistics including:
    - Total requests and success rates
    - Token usage and costs
    - Performance metrics
    - Breakdown by request type
    
    Args:
        days: Number of days to analyze (1-365)
        user_id: Optional user ID filter
        db: Database session
    
    Returns:
        AI usage summary with costs and performance data
    """
    try:
        logger.info(f"Getting AI usage summary for {days} days")
        
        monitoring_service = get_monitoring_service(db)
        summary = monitoring_service.get_usage_summary(user_id=user_id, days=days)
        
        return {
            "status": "success",
            "data": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting AI usage summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving usage summary"
        )


@router.get("/ai-usage/alerts")
async def get_cost_alerts(
    daily_limit: float = Query(default=10.0, ge=0.01, description="Daily cost limit in USD"),
    monthly_limit: float = Query(default=100.0, ge=0.01, description="Monthly cost limit in USD"),
    db: Session = Depends(get_db)
):
    """
    Check for cost alerts based on usage limits.
    
    This endpoint monitors AI usage costs and returns alerts when:
    - Daily or monthly limits are exceeded
    - Usage approaches warning thresholds (80% of limits)
    
    Args:
        daily_limit: Daily cost limit in USD
        monthly_limit: Monthly cost limit in USD
        db: Database session
    
    Returns:
        List of cost alerts with severity levels
    """
    try:
        logger.info(f"Checking cost alerts (daily: ${daily_limit}, monthly: ${monthly_limit})")
        
        monitoring_service = get_monitoring_service(db)
        alerts = monitoring_service.get_cost_alerts(
            daily_limit=daily_limit,
            monthly_limit=monthly_limit
        )
        
        return {
            "status": "success",
            "alerts": alerts,
            "limits": {
                "daily_limit_usd": daily_limit,
                "monthly_limit_usd": monthly_limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error checking cost alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error checking cost alerts"
        )


@router.get("/ai-usage/performance")
async def get_performance_metrics(
    days: int = Query(default=7, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get AI performance metrics for the specified period.
    
    This endpoint provides performance analytics including:
    - Response times (average, median, 95th percentile)
    - Success rates by request type
    - Performance trends
    
    Args:
        days: Number of days to analyze (1-90)
        db: Database session
    
    Returns:
        Performance metrics and statistics
    """
    try:
        logger.info(f"Getting AI performance metrics for {days} days")
        
        monitoring_service = get_monitoring_service(db)
        metrics = monitoring_service.get_performance_metrics(days=days)
        
        return {
            "status": "success",
            "data": metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving performance metrics"
        )


@router.get("/ai-usage/costs")
async def get_cost_breakdown(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    group_by: str = Query(default="day", regex="^(day|week|month|request_type)$", 
                         description="Group costs by time period or request type"),
    db: Session = Depends(get_db)
):
    """
    Get detailed cost breakdown for AI usage.
    
    This endpoint provides cost analysis grouped by different dimensions:
    - Time periods (day, week, month)
    - Request types (weekly_plan, daily_plan, etc.)
    
    Args:
        days: Number of days to analyze
        group_by: Grouping dimension (day, week, month, request_type)
        db: Database session
    
    Returns:
        Detailed cost breakdown and analysis
    """
    try:
        logger.info(f"Getting cost breakdown for {days} days, grouped by {group_by}")
        
        monitoring_service = get_monitoring_service(db)
        
        # Get base usage summary
        summary = monitoring_service.get_usage_summary(days=days)
        
        # Extract cost data based on grouping
        if group_by == "request_type":
            cost_data = summary.get("by_request_type", [])
        else:
            # For time-based grouping, use daily breakdown
            cost_data = summary.get("daily_breakdown", [])
        
        return {
            "status": "success",
            "period_days": days,
            "group_by": group_by,
            "total_cost_usd": summary.get("total_summary", {}).get("total_cost_usd", 0.0),
            "cost_breakdown": cost_data
        }
        
    except Exception as e:
        logger.error(f"Error getting cost breakdown: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving cost breakdown"
        )


@router.get("/system/health")
async def get_system_health(db: Session = Depends(get_db)):
    """
    Get system health status including AI service availability.
    
    This endpoint checks:
    - Database connectivity
    - AI service configuration
    - Recent error rates
    
    Returns:
        System health status and diagnostics
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        # Check database connectivity
        try:
            monitoring_service = get_monitoring_service(db)
            health_status["checks"]["database"] = {
                "status": "healthy",
                "message": "Database connection successful"
            }
        except Exception as e:
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}"
            }
            health_status["status"] = "degraded"
        
        # Check AI service configuration
        try:
            from app.core.config import settings
            api_key = settings.get_openai_api_key()
            
            if api_key:
                health_status["checks"]["ai_service"] = {
                    "status": "healthy",
                    "message": "OpenAI API key configured"
                }
            else:
                health_status["checks"]["ai_service"] = {
                    "status": "unhealthy",
                    "message": "OpenAI API key not configured"
                }
                health_status["status"] = "degraded"
                
        except Exception as e:
            health_status["checks"]["ai_service"] = {
                "status": "unhealthy",
                "message": f"AI service check failed: {str(e)}"
            }
            health_status["status"] = "degraded"
        
        # Check recent error rates (last 24 hours)
        try:
            summary = monitoring_service.get_usage_summary(days=1)
            total_summary = summary.get("total_summary", {})
            success_rate = total_summary.get("success_rate", 100)
            
            if success_rate >= 95:
                health_status["checks"]["ai_error_rate"] = {
                    "status": "healthy",
                    "message": f"AI success rate: {success_rate:.1f}%"
                }
            elif success_rate >= 90:
                health_status["checks"]["ai_error_rate"] = {
                    "status": "warning",
                    "message": f"AI success rate below 95%: {success_rate:.1f}%"
                }
                if health_status["status"] == "healthy":
                    health_status["status"] = "degraded"
            else:
                health_status["checks"]["ai_error_rate"] = {
                    "status": "unhealthy",
                    "message": f"AI success rate critically low: {success_rate:.1f}%"
                }
                health_status["status"] = "unhealthy"
                
        except Exception as e:
            health_status["checks"]["ai_error_rate"] = {
                "status": "unknown",
                "message": f"Could not check error rates: {str(e)}"
            }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error checking system health: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }