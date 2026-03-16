"""
from app.core.config import settings

from typing import Dict, List


class SecurityHeaders:
    """Security headers configuration"""
    
    # Content Security Policy
    CSP_POLICY = {
        "production": (
            "default-src 'self'; "
            "script-src 'self' cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "upgrade-insecure-requests"
        ),
        "development": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https: ws: wss:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
    }
    
    # Permissions Policy (Feature Policy)
    PERMISSIONS_POLICY = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=(), "
        "magnetometer=(), "
        "gyroscope=(), "
        "speaker=(), "
        "vibrate=(), "
        "fullscreen=(self), "
        "sync-xhr=()"
    )
    
    # Strict Transport Security
    HSTS_POLICY = "max-age=31536000; includeSubDomains; preload"
    
    # Referrer Policy
    REFERRER_POLICY = "no-referrer-when-downgrade"


class CORSConfig:
    """CORS configuration for different environments"""
    
    PRODUCTION_ALLOWED_ORIGINS = settings.security.cors_origins
    
    DEVELOPMENT_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ]
    
    ALLOWED_METHODS = ["*"]
    
    PRODUCTION_ALLOWED_HEADERS = ["*"]
    
    DEVELOPMENT_ALLOWED_HEADERS = ["*"]
    
    EXPOSED_HEADERS = [
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining", 
        "X-RateLimit-Reset",
        "X-Total-Count"
    ]


class RateLimitConfig:
    """Rate limiting configuration"""
    
    # Default limits per minute
    DEFAULT_LIMIT = 60
    
    # Endpoint-specific limits
    ENDPOINT_LIMITS = {
        # Authentication endpoints - stricter limits
        "/api/v1/auth/": 10,
        "/api/v1/users/profile": 30,
        
        # AI generation endpoints - very strict limits (expensive operations)
        "/api/v1/diet-plans/generate": 5,
        "/api/v1/diet-plans/regenerate": 10,
        "/api/v1/health-context/generate": 5,
        
        # Read operations - more lenient
        "/api/v1/users/profiles": 100,
        "/api/v1/diet-plans/": 100,
        "/api/v1/health-context/": 100,
        
        # Health checks - high limits
        "/health": 1000,
        "/db-health": 1000,
    }
    
    # User type limits (for future authentication system)
    USER_TYPE_LIMITS = {
        "anonymous": {
            "minute": 30,
            "hour": 500,
            "day": 2000
        },
        "authenticated": {
            "minute": 100,
            "hour": 2000,
            "day": 10000
        },
        "premium": {
            "minute": 200,
            "hour": 5000,
            "day": 25000
        }
    }


class TrustedHostConfig:
    """Trusted host configuration"""
    
    PRODUCTION_HOSTS = settings.security.trusted_hosts
    
    DEVELOPMENT_HOSTS = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "*"  # Allow all in development
    ]


class SecurityConstants:
    """Security-related constants"""
    
    # Input sanitization limits
    MAX_NAME_LENGTH = 255
    MAX_TEXT_FIELD_LENGTH = 1000
    MAX_LIST_ITEMS = 50
    MAX_LIST_ITEM_LENGTH = 100
    MAX_JSON_DEPTH = 5
    
    # File upload limits (for future file upload features)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES = [".jpg", ".jpeg", ".png", ".pdf", ".txt"]
    
    # Session and token settings (for future authentication)
    SESSION_TIMEOUT_MINUTES = 30
    TOKEN_EXPIRE_MINUTES = 60
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    # Password requirements (for future authentication)
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = True
    
    # Rate limiting time windows
    RATE_LIMIT_WINDOWS = {
        "minute": 60,
        "hour": 3600,
        "day": 86400
    }


def get_security_headers(is_production: bool) -> Dict[str, str]:
    """
    Get security headers based on environment
    
    Args:
        is_production: Whether running in production
        
    Returns:
        Dictionary of security headers
    """
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": SecurityHeaders.REFERRER_POLICY,
        "Content-Security-Policy": SecurityHeaders.CSP_POLICY["production" if is_production else "development"],
        "Permissions-Policy": SecurityHeaders.PERMISSIONS_POLICY,
    }
    if is_production:
        headers.update({
            "Strict-Transport-Security": SecurityHeaders.HSTS_POLICY,
            "Expect-CT": "max-age=86400, enforce",
            "Cross-Origin-Embedder-Policy": "unsafe-none",
            "Cross-Origin-Opener-Policy": "unsafe-none",
            "Cross-Origin-Resource-Policy": "cross-origin",
            "Server": "WellnessWay"  # Hide server information
        })
    else:
        headers["X-Development-Mode"] = "true"
    
    return headers


def get_cors_config(is_production: bool) -> Dict:
    """
    Get CORS configuration based on environment
    
    Args:
        is_production: Whether running in production
        
    Returns:
        CORS configuration dictionary
    """
    if is_production:
        return {
            "allow_origins": CORSConfig.PRODUCTION_ALLOWED_ORIGINS,
            "allow_credentials": True,
            "allow_methods": CORSConfig.ALLOWED_METHODS,
            "allow_headers": CORSConfig.PRODUCTION_ALLOWED_HEADERS,
            "expose_headers": CORSConfig.EXPOSED_HEADERS
        }
    else:
        return {
            "allow_origins": CORSConfig.DEVELOPMENT_ALLOWED_ORIGINS,
            "allow_credentials": True,
            "allow_methods": CORSConfig.ALLOWED_METHODS + ["OPTIONS"],
            "allow_headers": CORSConfig.DEVELOPMENT_ALLOWED_HEADERS,
            "expose_headers": CORSConfig.EXPOSED_HEADERS
        }


def get_trusted_hosts(is_production: bool) -> List[str]:
    """
    Get trusted hosts based on environment
    
    Args:
        is_production: Whether running in production
        
    Returns:
        List of trusted hosts
    """
    return TrustedHostConfig.PRODUCTION_HOSTS if is_production else TrustedHostConfig.DEVELOPMENT_HOSTS