"""
Unit tests for rate limiting middleware
"""

import pytest
import time
from unittest.mock import Mock, AsyncMock
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.middleware.security import RateLimitMiddleware, AdvancedRateLimitMiddleware


class TestRateLimitMiddleware:
    """Test basic rate limiting middleware"""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance for testing"""
        app = Mock()
        return RateLimitMiddleware(app, default_requests_per_minute=5)  # Low limit for testing
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request"""
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.url = Mock()
        request.url.path = "/api/v1/test"
        request.headers = {}
        return request
    
    @pytest.fixture
    def mock_call_next(self):
        """Create mock call_next function"""
        async def call_next(request):
            response = Mock(spec=Response)
            response.headers = {}
            return response
        return call_next
    
    @pytest.mark.asyncio
    async def test_rate_limit_within_limit(self, middleware, mock_request, mock_call_next):
        """Test request within rate limit"""
        # First request should pass
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should not be a rate limit response
        assert not isinstance(response, JSONResponse) or response.status_code != 429
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, middleware, mock_request, mock_call_next):
        """Test rate limit exceeded"""
        # Make requests up to the limit
        for i in range(5):
            await middleware.dispatch(mock_request, mock_call_next)
        
        # Next request should be rate limited
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 429
    
    @pytest.mark.asyncio
    async def test_different_ips_separate_limits(self, middleware, mock_call_next):
        """Test that different IPs have separate rate limits"""
        # Create requests from different IPs
        request1 = Mock(spec=Request)
        request1.client = Mock()
        request1.client.host = "127.0.0.1"
        request1.url = Mock()
        request1.url.path = "/api/v1/test"
        request1.headers = {}
        
        request2 = Mock(spec=Request)
        request2.client = Mock()
        request2.client.host = "192.168.1.1"
        request2.url = Mock()
        request2.url.path = "/api/v1/test"
        request2.headers = {}
        
        # Exhaust limit for first IP
        for i in range(5):
            await middleware.dispatch(request1, mock_call_next)
        
        # First IP should be rate limited
        response1 = await middleware.dispatch(request1, mock_call_next)
        assert isinstance(response1, JSONResponse)
        assert response1.status_code == 429
        
        # Second IP should still work
        response2 = await middleware.dispatch(request2, mock_call_next)
        assert not isinstance(response2, JSONResponse) or response2.status_code != 429
    
    @pytest.mark.asyncio
    async def test_endpoint_specific_limits(self, middleware, mock_call_next):
        """Test endpoint-specific rate limits"""
        # Test AI generation endpoint (should have lower limit)
        ai_request = Mock(spec=Request)
        ai_request.client = Mock()
        ai_request.client.host = "127.0.0.1"
        ai_request.url = Mock()
        ai_request.url.path = "/api/v1/diet-plans/generate"
        ai_request.headers = {}
        
        # Should have limit of 5 for AI endpoints
        limit = middleware._get_rate_limit_for_endpoint("/api/v1/diet-plans/generate")
        assert limit == 5
        
        # Test health endpoint (should have higher limit)
        health_limit = middleware._get_rate_limit_for_endpoint("/health")
        assert health_limit == 1000
    
    def test_get_client_ip_forwarded(self, middleware):
        """Test client IP extraction with forwarded headers"""
        request = Mock(spec=Request)
        request.headers = {"X-Forwarded-For": "203.0.113.1, 198.51.100.1"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.1"  # Should use first IP in forwarded chain
    
    def test_get_client_ip_real_ip(self, middleware):
        """Test client IP extraction with Real-IP header"""
        request = Mock(spec=Request)
        request.headers = {"X-Real-IP": "203.0.113.1"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.1"
    
    def test_get_client_ip_fallback(self, middleware):
        """Test client IP extraction fallback"""
        request = Mock(spec=Request)
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        ip = middleware._get_client_ip(request)
        assert ip == "127.0.0.1"
    
    def test_cleanup_old_entries(self, middleware):
        """Test cleanup of old rate limit entries"""
        current_time = int(time.time() / 60)
        
        # Add some old and new entries
        middleware.request_counts = {
            ("127.0.0.1", "/test", current_time - 5): 10,  # Old entry
            ("127.0.0.1", "/test", current_time): 5,       # Current entry
            ("192.168.1.1", "/test", current_time - 3): 3, # Old entry
        }
        
        middleware._cleanup_old_entries(current_time)
        
        # Only current entries should remain
        remaining_keys = list(middleware.request_counts.keys())
        assert len(remaining_keys) == 1
        assert remaining_keys[0][2] == current_time


class TestAdvancedRateLimitMiddleware:
    """Test advanced rate limiting middleware"""
    
    @pytest.fixture
    def middleware(self):
        """Create advanced middleware instance for testing"""
        app = Mock()
        middleware = AdvancedRateLimitMiddleware(app)
        # Lower limits for testing
        middleware.limits = {
            "anonymous": {
                "minute": 3,
                "hour": 10,
                "day": 20
            },
            "authenticated": {
                "minute": 10,
                "hour": 50,
                "day": 100
            }
        }
        return middleware
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request"""
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        return request
    
    @pytest.fixture
    def mock_call_next(self):
        """Create mock call_next function"""
        async def call_next(request):
            response = Mock(spec=Response)
            response.headers = {}
            return response
        return call_next
    
    @pytest.mark.asyncio
    async def test_multiple_time_windows(self, middleware, mock_request, mock_call_next):
        """Test rate limiting across multiple time windows"""
        # Make requests up to minute limit
        for i in range(3):
            response = await middleware.dispatch(mock_request, mock_call_next)
            assert not isinstance(response, JSONResponse) or response.status_code != 429
        
        # Next request should be rate limited (minute window exceeded)
        response = await middleware.dispatch(mock_request, mock_call_next)
        assert isinstance(response, JSONResponse)
        assert response.status_code == 429
        assert "minute" in response.body.decode()
    
    def test_user_type_detection(self, middleware, mock_request):
        """Test user type detection"""
        # Currently all users are anonymous
        user_type = middleware._get_user_type(mock_request)
        assert user_type == "anonymous"
    
    def test_rate_limit_check(self, middleware):
        """Test rate limit checking logic"""
        client_ip = "127.0.0.1"
        user_type = "anonymous"
        
        # Should be under limit initially
        assert middleware._check_rate_limit(client_ip, user_type, "minute", 60)
        
        # Add requests up to limit (limit is 3 for anonymous users in test setup)
        middleware._update_counters(client_ip, user_type)  # 1
        assert middleware._check_rate_limit(client_ip, user_type, "minute", 60)
        
        middleware._update_counters(client_ip, user_type)  # 2
        assert middleware._check_rate_limit(client_ip, user_type, "minute", 60)
        
        middleware._update_counters(client_ip, user_type)  # 3 - at limit
        assert not middleware._check_rate_limit(client_ip, user_type, "minute", 60)  # Should be blocked now
    
    def test_rate_limit_response_format(self, middleware):
        """Test rate limit response format"""
        response = middleware._create_rate_limit_response("anonymous", "minute")
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Window" in response.headers


class TestRateLimitIntegration:
    """Integration tests for rate limiting"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_headers_added(self):
        """Test that rate limit headers are added to responses"""
        app = Mock()
        middleware = RateLimitMiddleware(app, default_requests_per_minute=10)
        
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.url = Mock()
        request.url.path = "/api/v1/test"
        request.headers = {}
        
        async def call_next(request):
            response = Mock(spec=Response)
            response.headers = {}
            return response
        
        response = await middleware.dispatch(request, call_next)
        
        # Check that rate limit headers were added
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_same_ip(self):
        """Test handling of concurrent requests from same IP"""
        app = Mock()
        middleware = RateLimitMiddleware(app, default_requests_per_minute=2)
        
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.url = Mock()
        request.url.path = "/api/v1/test"
        request.headers = {}
        
        async def call_next(request):
            response = Mock(spec=Response)
            response.headers = {}
            return response
        
        # Simulate concurrent requests
        responses = []
        for i in range(5):
            response = await middleware.dispatch(request, call_next)
            responses.append(response)
        
        # Some requests should be rate limited
        rate_limited_count = sum(
            1 for r in responses 
            if isinstance(r, JSONResponse) and r.status_code == 429
        )
        
        assert rate_limited_count > 0  # At least some should be rate limited