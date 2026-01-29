"""
Unit tests for security configuration
"""

import pytest
from app.core.security_config import (
    get_security_headers,
    get_cors_config,
    get_trusted_hosts,
    SecurityHeaders,
    CORSConfig,
    TrustedHostConfig,
    RateLimitConfig,
    SecurityConstants
)


class TestSecurityHeaders:
    """Test security headers configuration"""
    
    def test_production_security_headers(self):
        """Test production security headers"""
        headers = get_security_headers(is_production=True)
        
        # Check required security headers
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in headers
        assert headers["X-XSS-Protection"] == "1; mode=block"
        
        assert "Referrer-Policy" in headers
        assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        
        # Production-specific headers
        assert "Strict-Transport-Security" in headers
        assert "max-age=31536000" in headers["Strict-Transport-Security"]
        assert "includeSubDomains" in headers["Strict-Transport-Security"]
        assert "preload" in headers["Strict-Transport-Security"]
        
        assert "Content-Security-Policy" in headers
        assert "default-src 'self'" in headers["Content-Security-Policy"]
        
        assert "Permissions-Policy" in headers
        assert "geolocation=()" in headers["Permissions-Policy"]
        
        assert "Expect-CT" in headers
        assert "Cross-Origin-Embedder-Policy" in headers
        assert "Cross-Origin-Opener-Policy" in headers
        assert "Cross-Origin-Resource-Policy" in headers
        
        assert "Server" in headers
        assert headers["Server"] == "WellnessWay"
    
    def test_development_security_headers(self):
        """Test development security headers"""
        headers = get_security_headers(is_production=False)
        
        # Check basic security headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Referrer-Policy" in headers
        assert "Content-Security-Policy" in headers
        assert "Permissions-Policy" in headers
        
        # Development-specific headers
        assert "X-Development-Mode" in headers
        assert headers["X-Development-Mode"] == "true"
        
        # Should not have production-only headers
        assert "Strict-Transport-Security" not in headers
        assert "Expect-CT" not in headers
        assert "Cross-Origin-Embedder-Policy" not in headers
    
    def test_csp_policy_differences(self):
        """Test CSP policy differences between environments"""
        prod_headers = get_security_headers(is_production=True)
        dev_headers = get_security_headers(is_production=False)
        
        prod_csp = prod_headers["Content-Security-Policy"]
        dev_csp = dev_headers["Content-Security-Policy"]
        
        # Development should allow unsafe-inline and unsafe-eval for scripts
        assert "'unsafe-inline'" in dev_csp
        assert "'unsafe-eval'" in dev_csp
        
        # Production should be more restrictive
        assert "'unsafe-eval'" not in prod_csp
        
        # Both should have basic security
        assert "default-src 'self'" in prod_csp
        assert "default-src 'self'" in dev_csp


class TestCORSConfig:
    """Test CORS configuration"""
    
    def test_production_cors_config(self):
        """Test production CORS configuration"""
        config = get_cors_config(is_production=True)
        
        assert "allow_origins" in config
        assert "allow_credentials" in config
        assert "allow_methods" in config
        assert "allow_headers" in config
        assert "expose_headers" in config
        
        # Production should have specific origins
        assert config["allow_origins"] == CORSConfig.PRODUCTION_ALLOWED_ORIGINS
        assert "https://wellnessway.com" in config["allow_origins"]
        
        # Should allow credentials
        assert config["allow_credentials"] is True
        
        # Should have restricted methods (no OPTIONS)
        assert "OPTIONS" not in config["allow_methods"]
        assert "GET" in config["allow_methods"]
        assert "POST" in config["allow_methods"]
        
        # Should have specific headers
        assert config["allow_headers"] == CORSConfig.PRODUCTION_ALLOWED_HEADERS
        assert "Authorization" in config["allow_headers"]
        assert "*" not in config["allow_headers"]
    
    def test_development_cors_config(self):
        """Test development CORS configuration"""
        config = get_cors_config(is_production=False)
        
        # Development should have localhost origins
        assert config["allow_origins"] == CORSConfig.DEVELOPMENT_ALLOWED_ORIGINS
        assert "http://localhost:3000" in config["allow_origins"]
        
        # Should include OPTIONS for development
        assert "OPTIONS" in config["allow_methods"]
        
        # Should allow all headers in development
        assert "*" in config["allow_headers"]
    
    def test_exposed_headers(self):
        """Test exposed headers configuration"""
        prod_config = get_cors_config(is_production=True)
        dev_config = get_cors_config(is_production=False)
        
        # Both should expose rate limit headers
        for config in [prod_config, dev_config]:
            assert "X-RateLimit-Limit" in config["expose_headers"]
            assert "X-RateLimit-Remaining" in config["expose_headers"]
            assert "X-RateLimit-Reset" in config["expose_headers"]


class TestTrustedHosts:
    """Test trusted hosts configuration"""
    
    def test_production_trusted_hosts(self):
        """Test production trusted hosts"""
        hosts = get_trusted_hosts(is_production=True)
        
        assert hosts == TrustedHostConfig.PRODUCTION_HOSTS
        assert "wellnessway.com" in hosts
        assert "app.wellnessway.com" in hosts
        assert "api.wellnessway.com" in hosts
        
        # Should not allow wildcard in production
        assert "*" not in hosts
    
    def test_development_trusted_hosts(self):
        """Test development trusted hosts"""
        hosts = get_trusted_hosts(is_production=False)
        
        assert hosts == TrustedHostConfig.DEVELOPMENT_HOSTS
        assert "localhost" in hosts
        assert "127.0.0.1" in hosts
        assert "*" in hosts  # Allow all in development


class TestRateLimitConfig:
    """Test rate limiting configuration"""
    
    def test_endpoint_limits(self):
        """Test endpoint-specific rate limits"""
        limits = RateLimitConfig.ENDPOINT_LIMITS
        
        # AI endpoints should have low limits
        assert limits["/api/v1/diet-plans/generate"] == 5
        assert limits["/api/v1/health-context/generate"] == 5
        
        # Read endpoints should have higher limits
        assert limits["/api/v1/users/profiles"] == 100
        
        # Health checks should have very high limits
        assert limits["/health"] == 1000
    
    def test_user_type_limits(self):
        """Test user type rate limits"""
        limits = RateLimitConfig.USER_TYPE_LIMITS
        
        # Anonymous users should have lowest limits
        assert limits["anonymous"]["minute"] < limits["authenticated"]["minute"]
        assert limits["authenticated"]["minute"] < limits["premium"]["minute"]
        
        # All user types should have minute, hour, and day limits
        for user_type in ["anonymous", "authenticated", "premium"]:
            assert "minute" in limits[user_type]
            assert "hour" in limits[user_type]
            assert "day" in limits[user_type]


class TestSecurityConstants:
    """Test security constants"""
    
    def test_input_limits(self):
        """Test input validation limits"""
        assert SecurityConstants.MAX_NAME_LENGTH == 255
        assert SecurityConstants.MAX_TEXT_FIELD_LENGTH == 1000
        assert SecurityConstants.MAX_LIST_ITEMS == 50
        assert SecurityConstants.MAX_LIST_ITEM_LENGTH == 100
        
        # Limits should be reasonable
        assert SecurityConstants.MAX_NAME_LENGTH > 0
        assert SecurityConstants.MAX_TEXT_FIELD_LENGTH > SecurityConstants.MAX_NAME_LENGTH
    
    def test_file_upload_limits(self):
        """Test file upload limits"""
        assert SecurityConstants.MAX_FILE_SIZE > 0
        assert SecurityConstants.MAX_FILE_SIZE <= 50 * 1024 * 1024  # Reasonable max
        
        # Should have allowed file types
        assert len(SecurityConstants.ALLOWED_FILE_TYPES) > 0
        assert ".jpg" in SecurityConstants.ALLOWED_FILE_TYPES
        assert ".pdf" in SecurityConstants.ALLOWED_FILE_TYPES
    
    def test_password_requirements(self):
        """Test password requirements"""
        assert SecurityConstants.MIN_PASSWORD_LENGTH >= 8
        assert SecurityConstants.REQUIRE_UPPERCASE is True
        assert SecurityConstants.REQUIRE_LOWERCASE is True
        assert SecurityConstants.REQUIRE_NUMBERS is True
        assert SecurityConstants.REQUIRE_SPECIAL_CHARS is True
    
    def test_time_windows(self):
        """Test rate limiting time windows"""
        windows = SecurityConstants.RATE_LIMIT_WINDOWS
        
        assert windows["minute"] == 60
        assert windows["hour"] == 3600
        assert windows["day"] == 86400
        
        # Windows should be in ascending order
        assert windows["minute"] < windows["hour"] < windows["day"]


class TestSecurityConfigIntegration:
    """Integration tests for security configuration"""
    
    def test_production_vs_development_differences(self):
        """Test that production and development configs are appropriately different"""
        prod_headers = get_security_headers(is_production=True)
        dev_headers = get_security_headers(is_production=False)
        
        prod_cors = get_cors_config(is_production=True)
        dev_cors = get_cors_config(is_production=False)
        
        prod_hosts = get_trusted_hosts(is_production=True)
        dev_hosts = get_trusted_hosts(is_production=False)
        
        # Production should be more restrictive
        assert len(prod_headers) > len(dev_headers)  # More security headers
        assert len(prod_cors["allow_origins"]) < len(dev_cors["allow_origins"])  # Fewer origins
        assert "*" not in prod_cors["allow_headers"]  # No wildcard headers
        assert "*" not in prod_hosts  # No wildcard hosts
        
        # Development should be more permissive
        assert "*" in dev_cors["allow_headers"]
        assert "*" in dev_hosts
        assert "OPTIONS" in dev_cors["allow_methods"]
    
    def test_security_header_completeness(self):
        """Test that all important security headers are included"""
        headers = get_security_headers(is_production=True)
        
        # OWASP recommended headers
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Content-Security-Policy",
            "Strict-Transport-Security",
            "Referrer-Policy"
        ]
        
        for header in required_headers:
            assert header in headers, f"Missing required security header: {header}"
    
    def test_csp_policy_security(self):
        """Test that CSP policy is secure"""
        prod_headers = get_security_headers(is_production=True)
        csp = prod_headers["Content-Security-Policy"]
        
        # Should not allow unsafe practices in production
        assert "'unsafe-eval'" not in csp
        assert "data:" not in csp or "img-src" in csp  # data: only for images
        
        # Should have frame protection
        assert "frame-ancestors 'none'" in csp
        
        # Should restrict default sources
        assert "default-src 'self'" in csp