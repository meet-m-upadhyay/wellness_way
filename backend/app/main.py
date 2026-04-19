"""
WellnessWay Diet Planner - FastAPI Application Entry Point
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import logging
from contextlib import asynccontextmanager

# Import configuration
from app.core.config import get_settings
from app.core.security_config import get_security_headers, get_cors_config, get_trusted_hosts

# Import database configuration
from app.database.connection import get_engine, Base

# Import security middleware
from app.middleware.security import SecurityMiddleware, RateLimitMiddleware, AdvancedRateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    settings = get_settings()
    # Startup
    logging.info(f"Starting WellnessWay Diet Planner API in {settings.environment} mode")
    
    # Import models to ensure they are registered
    from app.models import user, health_context, diet_plan
    
    # Create tables if in development mode (DO NOT block startup in production)
    if get_settings().is_development:
        try:
            Base.metadata.create_all(bind=get_engine())
            logging.info("Database tables created/verified")
        except Exception as e:
            logging.error(f"Failed to create tables: {e}")
    
    # Setup logging
    setup_logging()
    
    # Initialize email notification listeners
    from app.services.email_service import init_email_listeners
    init_email_listeners()
    logging.info("Email notification system initialized")

    # Warm up V2 embedding model at startup (avoids 18s cold start on first request)
    if getattr(settings, "enable_meal_engine_v2", False):
        try:
            from sentence_transformers import SentenceTransformer
            from app.services.meal_engine.matching.ingredient_matcher import IngredientMatcher
            if IngredientMatcher._embedding_model is None:
                IngredientMatcher._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                logging.info("V2 embedding model warmed up at startup")
        except ImportError:
            logging.debug("sentence-transformers not available — skipping V2 embedding warmup")
        except Exception as e:
            logging.warning("V2 embedding warmup failed: %s", e)

    yield
    
    # Shutdown
    logging.info("Shutting down WellnessWay Diet Planner API")


def setup_logging():
    """Configure application logging"""
    settings = get_settings()
    log_level = getattr(logging, settings.logging.level.upper())
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if settings.logging.format == 'text' 
               else '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
        handlers=[]
    )
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    logging.getLogger().addHandler(console_handler)
    
    # Add file handler if enabled
    if settings.logging.enable_file_logging:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            settings.logging.log_file_path,
            maxBytes=settings.logging.max_file_size_mb * 1024 * 1024,
            backupCount=settings.logging.backup_count
        )
        file_handler.setLevel(log_level)
        logging.getLogger().addHandler(file_handler)


# Create FastAPI application (Factory-like instantiation)
def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # CORS middleware with enhanced security
    cors_config = get_cors_config(settings.is_production)
    app.add_middleware(CORSMiddleware, **cors_config)
    
    # Security middleware for input sanitization
    app.add_middleware(
        SecurityMiddleware,
        skip_paths=["/docs", "/redoc", "/openapi.json", "/health", "/db-health", "/", "/config-info", "/api/v1/auth"]
    )
    
    # Rate limiting middleware - use basic rate limiting for now
    app.add_middleware(
        RateLimitMiddleware,
        default_requests_per_minute=60  # Default limit, with per-endpoint customization
    )
    
    # Security middleware
    trusted_hosts = get_trusted_hosts(settings.is_production)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)
    
    return app

app = create_app()


@app.middleware("http")
async def add_comprehensive_security_headers(request: Request, call_next):
    """Add comprehensive security headers to all responses"""
    response = await call_next(request)
    
    settings = get_settings()
    # Get security headers based on environment
    security_headers = get_security_headers(settings.is_production)
    
    # Add all security headers to response
    for header, value in security_headers.items():
        response.headers[header] = value
    
    return response


@app.middleware("http")
async def enforce_https_in_production(request: Request, call_next):
    """Enforce HTTPS in production environment"""
    settings = get_settings()
    if settings.is_production and request.url.hostname not in ["localhost", "127.0.0.1"]:
        # Check if request is using HTTPS
        if request.url.scheme != "https":
            # Check for forwarded protocol headers (when behind a proxy)
            forwarded_proto = request.headers.get("X-Forwarded-Proto")
            forwarded_ssl = request.headers.get("X-Forwarded-SSL")
            
            if forwarded_proto != "https" and forwarded_ssl != "on":
                # Redirect to HTTPS
                https_url = request.url.replace(scheme="https")
                return JSONResponse(
                    status_code=status.HTTP_301_MOVED_PERMANENTLY,
                    content={"detail": "HTTPS required", "redirect_url": str(https_url)},
                    headers={"Location": str(https_url)}
                )
    
    return await call_next(request)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    
    settings = get_settings()
    if settings.is_production:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)}
        )


@app.get("/")
async def root():
    """Root endpoint for health checks"""
    settings = get_settings()
    return {
        "message": settings.app_name,
        "version": settings.app_version,
        "status": "healthy",
        "environment": settings.environment
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    settings = get_settings()
    return {
        "status": "healthy", 
        "service": "health-buddy-api",
        "environment": settings.environment,
        "version": settings.app_version
    }


@app.get("/db-health")
async def database_health_check():
    """Database health check endpoint"""
    try:
        from app.database.connection import get_session_local
        db = get_session_local()()
        # Simple query to test database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.close()
        return {
            "status": "healthy", 
            "database": "connected",
            "environment": get_settings().environment
        }
    except Exception as e:
        logging.error(f"Database health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "database": "disconnected", 
                "error": str(e) if not settings.is_production else "Database connection failed"
            }
        )


@app.get("/config-info")
async def config_info():
    """Configuration information endpoint (development only)"""
    settings = get_settings()
    if settings.is_production:
        return JSONResponse(
            status_code=404,
            content={"detail": "Not found"}
        )
    
    return {
        "environment": settings.environment,
        "debug": settings.debug,
        "testing": settings.testing,
        "features": {
            "user_registration": settings.enable_user_registration,
            "ai_generation": settings.enable_ai_generation,
            "plan_regeneration": settings.enable_plan_regeneration,
            "analytics": settings.enable_analytics
        },
        "database": {
            "pool_size": settings.database.pool_size,
            "max_overflow": settings.database.max_overflow
        },
        "security": {
            "cors_origins": settings.security.cors_origins_list,
            "token_expire_minutes": settings.security.access_token_expire_minutes
        }
    }


# Include API routers
from app.api.router import api_router
app.include_router(api_router, prefix=get_settings().api_prefix)


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug and settings.is_development,
        log_level=settings.logging.level.lower()
    )
