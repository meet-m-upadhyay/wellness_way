"""
Security middleware for input sanitization and request validation
"""

import logging
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import json

from app.core.security import InputSanitizer, sanitize_user_input

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware to sanitize and validate all incoming requests
    """
    
    def __init__(self, app, skip_paths: list = None):
        super().__init__(app)
        self.skip_paths = skip_paths or ["/docs", "/redoc", "/openapi.json", "/health"]
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request through security middleware
        """
        # Skip security checks for certain paths
        if any(request.url.path.startswith(path) for path in self.skip_paths):
            return await call_next(request)
        
        try:
            # Validate and sanitize request body if present
            if request.method in ["POST", "PUT", "PATCH"]:
                await self._sanitize_request_body(request)
            
            # Validate query parameters
            self._sanitize_query_params(request)
            
            # Process request
            response = await call_next(request)
            
            return response
            
        except ValueError as e:
            logger.warning(f"Security validation failed for {request.url.path}: {e}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": f"Invalid input: {str(e)}"}
            )
        except Exception as e:
            logger.error(f"Security middleware error for {request.url.path}: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal security error"}
            )
    
    async def _sanitize_request_body(self, request: Request):
        """
        Sanitize request body content
        """
        try:
            # Read and parse request body
            body = await request.body()
            if not body:
                return
            
            # Parse JSON body
            try:
                json_body = json.loads(body)
            except json.JSONDecodeError:
                # Not JSON, skip sanitization
                return
            
            # Sanitize the JSON data
            if isinstance(json_body, dict):
                sanitized_body = self._sanitize_json_recursively(json_body)
                
                # Replace request body with sanitized version
                request._body = json.dumps(sanitized_body).encode()
            
        except Exception as e:
            logger.error(f"Error sanitizing request body: {e}")
            raise ValueError("Invalid request body format")
    
    def _sanitize_json_recursively(self, data):
        """
        Recursively sanitize JSON data
        """
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Sanitize key
                clean_key = InputSanitizer.sanitize_string(str(key), max_length=100)
                
                # Sanitize value
                if isinstance(value, str):
                    sanitized[clean_key] = InputSanitizer.sanitize_string(value, max_length=1000)
                elif isinstance(value, list):
                    sanitized[clean_key] = [
                        InputSanitizer.sanitize_string(str(item), max_length=200) 
                        if isinstance(item, str) else item 
                        for item in value[:50]  # Limit list size
                    ]
                elif isinstance(value, dict):
                    sanitized[clean_key] = self._sanitize_json_recursively(value)
                else:
                    sanitized[clean_key] = value
            return sanitized
        elif isinstance(data, list):
            return [
                self._sanitize_json_recursively(item) if isinstance(item, (dict, list))
                else InputSanitizer.sanitize_string(str(item), max_length=200) if isinstance(item, str)
                else item
                for item in data[:50]  # Limit list size
            ]
        else:
            return data
    
    def _sanitize_query_params(self, request: Request):
        """
        Sanitize query parameters
        """
        try:
            for key, value in request.query_params.items():
                # Validate parameter name
                if not key.replace('_', '').replace('-', '').isalnum():
                    raise ValueError(f"Invalid query parameter name: {key}")
                
                # Sanitize parameter value
                if isinstance(value, str):
                    sanitized_value = InputSanitizer.sanitize_string(value, max_length=200)
                    # Note: We can't modify query_params directly, but we validate them
                    if sanitized_value != value:
                        logger.warning(f"Query parameter {key} was sanitized")
        
        except Exception as e:
            logger.error(f"Error sanitizing query parameters: {e}")
            raise ValueError("Invalid query parameters")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive rate limiting middleware with different limits for different endpoint types
    """
    
    def __init__(self, app, default_requests_per_minute: int = 60):
        super().__init__(app)
        self.default_requests_per_minute = default_requests_per_minute
        self.request_counts = {}  # In production, use Redis
        
        # Define different rate limits for different endpoint types
        self.endpoint_limits = {
            # Authentication endpoints - stricter limits
            "/api/v1/auth/": 10,
            "/api/v1/users/profile": 30,  # Profile creation/updates
            
            # AI generation endpoints - very strict limits (expensive operations)
            "/api/v1/diet-plans/generate": 5,
            "/api/v1/diet-plans/regenerate": 10,
            "/api/v1/health-context/generate": 5,
            
            # Read operations - more lenient
            "/api/v1/users/profiles": 100,
            "/api/v1/diet-plans/": 100,
            "/api/v1/health-context/": 100,
            
            # Health checks - unlimited
            "/health": 1000,
            "/db-health": 1000,
        }
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Apply rate limiting based on endpoint type and client
        """
        client_ip = self._get_client_ip(request)
        current_time = int(time.time() / 60)  # Current minute
        
        # Clean old entries (simple cleanup)
        self._cleanup_old_entries(current_time)
        
        # Determine rate limit for this endpoint
        rate_limit = self._get_rate_limit_for_endpoint(request.url.path)
        
        # Check current requests for this IP and endpoint
        key = (client_ip, request.url.path, current_time)
        current_requests = self.request_counts.get(key, 0)
        
        # Add rate limit headers
        response_headers = {
            "X-RateLimit-Limit": str(rate_limit),
            "X-RateLimit-Remaining": str(max(0, rate_limit - current_requests)),
            "X-RateLimit-Reset": str((current_time + 1) * 60),  # Next minute timestamp
        }
        
        if current_requests >= rate_limit:
            logger.warning(f"Rate limit exceeded for {client_ip} on {request.url.path}: {current_requests}/{rate_limit}")
            
            # Add retry-after header
            response_headers["Retry-After"] = "60"  # Retry after 60 seconds
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "limit": rate_limit,
                    "reset_time": (current_time + 1) * 60
                },
                headers=response_headers
            )
        
        # Increment counter
        self.request_counts[key] = current_requests + 1
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        for header, value in response_headers.items():
            response.headers[header] = value
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address, considering proxy headers
        """
        # Check for forwarded headers (when behind a proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _get_rate_limit_for_endpoint(self, path: str) -> int:
        """
        Determine rate limit for a specific endpoint
        """
        # Check for exact matches first
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]
        
        # Check for prefix matches
        for endpoint_prefix, limit in self.endpoint_limits.items():
            if path.startswith(endpoint_prefix):
                return limit
        
        # Return default limit
        return self.default_requests_per_minute
    
    def _cleanup_old_entries(self, current_time: int):
        """
        Clean up old rate limit entries
        """
        # Remove entries older than 2 minutes
        cutoff_time = current_time - 2
        keys_to_remove = [
            key for key in self.request_counts.keys()
            if len(key) >= 3 and key[2] < cutoff_time
        ]
        
        for key in keys_to_remove:
            del self.request_counts[key]


class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Advanced rate limiting with user-based and IP-based limits
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.ip_limits = {}  # IP-based limits
        self.user_limits = {}  # User-based limits (when authentication is implemented)
        
        # Different time windows for rate limiting
        self.time_windows = {
            "minute": 60,
            "hour": 3600,
            "day": 86400
        }
        
        # Rate limits per time window
        self.limits = {
            "anonymous": {  # Non-authenticated users
                "minute": 30,
                "hour": 500,
                "day": 2000
            },
            "authenticated": {  # Authenticated users (when auth is implemented)
                "minute": 100,
                "hour": 2000,
                "day": 10000
            },
            "premium": {  # Premium users (future feature)
                "minute": 200,
                "hour": 5000,
                "day": 25000
            }
        }
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Apply advanced rate limiting
        """
        client_ip = self._get_client_ip(request)
        user_type = self._get_user_type(request)  # Will be enhanced when auth is implemented
        
        # Check rate limits for all time windows
        for window_name, window_seconds in self.time_windows.items():
            if not self._check_rate_limit(client_ip, user_type, window_name, window_seconds):
                return self._create_rate_limit_response(user_type, window_name)
        
        # Update counters
        self._update_counters(client_ip, user_type)
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _get_user_type(self, request: Request) -> str:
        """
        Determine user type for rate limiting
        TODO: Enhance this when JWT authentication is implemented
        """
        # For now, all users are anonymous
        # In the future, check JWT token for user type
        return "anonymous"
    
    def _check_rate_limit(self, client_ip: str, user_type: str, window_name: str, window_seconds: int) -> bool:
        """
        Check if request is within rate limit for given time window
        """
        current_time = int(time.time())
        window_start = current_time - window_seconds
        
        # Get limit for this user type and window
        limit = self.limits[user_type][window_name]
        
        # Count requests in this time window
        key_prefix = f"{client_ip}:{user_type}:{window_name}"
        
        # Simple in-memory implementation (use Redis in production)
        if key_prefix not in self.ip_limits:
            self.ip_limits[key_prefix] = []
        
        # Remove old entries
        self.ip_limits[key_prefix] = [
            timestamp for timestamp in self.ip_limits[key_prefix]
            if timestamp > window_start
        ]
        
        # Check if under limit
        return len(self.ip_limits[key_prefix]) < limit
    
    def _update_counters(self, client_ip: str, user_type: str):
        """
        Update request counters for all time windows
        """
        current_time = int(time.time())
        
        for window_name in self.time_windows.keys():
            key_prefix = f"{client_ip}:{user_type}:{window_name}"
            
            if key_prefix not in self.ip_limits:
                self.ip_limits[key_prefix] = []
            
            self.ip_limits[key_prefix].append(current_time)
    
    def _create_rate_limit_response(self, user_type: str, exceeded_window: str) -> JSONResponse:
        """
        Create rate limit exceeded response
        """
        limit = self.limits[user_type][exceeded_window]
        window_seconds = self.time_windows[exceeded_window]
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": f"Rate limit exceeded for {exceeded_window} window",
                "limit": limit,
                "window": exceeded_window,
                "retry_after": window_seconds
            },
            headers={
                "Retry-After": str(window_seconds),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Window": exceeded_window
            }
        )


# Import time for rate limiting
import time