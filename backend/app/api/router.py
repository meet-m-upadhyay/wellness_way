"""
Main API router that includes all endpoint routers
"""

from fastapi import APIRouter

from app.api.endpoints.users import router as users_router
from app.api.endpoints.health_context import router as health_context_router
# from app.api.endpoints.diet_plans import router as diet_plans_router # DELETED
from app.api.endpoints.diet_plans_ml import router as diet_plans_ml_router  # NEW ML PIPELINE
# from app.api.endpoints.monitoring import router as monitoring_router # DELETED
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.admin import router as admin_router

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(health_context_router)
# api_router.include_router(diet_plans_router) # DELETED
api_router.include_router(diet_plans_ml_router)  # NEW ML PIPELINE
# api_router.include_router(monitoring_router) # DELETED
api_router.include_router(admin_router)

# Health check endpoint at API level
@api_router.get("/health")
async def api_health_check():
    """API-level health check"""
    return {
        "status": "healthy",
        "service": "health-buddy-api",
        "endpoints": [
            "/auth",
            "/users",
            "/health-context",
            # "/diet-plans", # DELETED
            "/diet-plans-ml",  # NEW ML PIPELINE
            # "/monitoring", # DELETED
            "/admin"
        ]
    }