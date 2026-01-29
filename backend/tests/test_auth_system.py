"""
Unit tests for JWT authentication system
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.services.auth_service import AuthService, auth_service
from app.models.user import User
from app.middleware.auth import get_current_user, get_current_active_user
from app.core.config import get_settings


class TestAuthService:
    """Test cases for AuthService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.auth_service = AuthService()
        self.mock_db = Mock(spec=Session)
        
    def test_create_access_token(self):
        """Test JWT access token creation"""
        data = {"sub": "test-user-id", "email": "test@example.com"}
        
        token = self.auth_service.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        payload = self.auth_service.verify_token(token, "access")
        assert payload["sub"] == "test-user-id"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
    
    def test_create_refresh_token(self):
        """Test JWT refresh token creation"""
        data = {"sub": "test-user-id", "email": "test@example.com"}
        
        token = self.auth_service.create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        payload = self.auth_service.verify_token(token, "refresh")
        assert payload["sub"] == "test-user-id"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "refresh"
    
    def test_verify_token_success(self):
        """Test successful token verification"""
        data = {"sub": "test-user-id", "email": "test@example.com"}
        token = self.auth_service.create_access_token(data)
        
        payload = self.auth_service.verify_token(token, "access")
        
        assert payload["sub"] == "test-user-id"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
    
    def test_verify_token_invalid_type(self):
        """Test token verification with wrong token type"""
        data = {"sub": "test-user-id"}
        access_token = self.auth_service.create_access_token(data)
        
        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.verify_token(access_token, "refresh")
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token type" in str(exc_info.value.detail)
    
    def test_verify_token_invalid_token(self):
        """Test token verification with invalid token"""
        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.verify_token("invalid-token", "access")
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in str(exc_info.value.detail)
    
    @patch('app.services.auth_service.id_token')
    @patch('app.services.auth_service.requests')
    def test_verify_google_token_success(self, mock_requests, mock_id_token):
        """Test successful Google token verification"""
        # Mock Google token verification
        mock_id_token.verify_oauth2_token.return_value = {
            'sub': 'google-user-id',
            'email': 'user@gmail.com',
            'name': 'Test User',
            'picture': 'https://example.com/photo.jpg',
            'email_verified': True,
            'aud': 'test-client-id'
        }
        
        # Mock settings
        with patch.object(self.auth_service.settings.security, 'google_client_id', 'test-client-id'):
            result = self.auth_service.verify_google_token('valid-google-token')
        
        assert result['google_id'] == 'google-user-id'
        assert result['email'] == 'user@gmail.com'
        assert result['name'] == 'Test User'
        assert result['email_verified'] is True
    
    @patch('app.services.auth_service.id_token')
    def test_verify_google_token_invalid(self, mock_id_token):
        """Test Google token verification with invalid token"""
        mock_id_token.verify_oauth2_token.side_effect = ValueError("Invalid token")
        
        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.verify_google_token('invalid-token')
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid Google token" in str(exc_info.value.detail)
    
    def test_get_or_create_user_existing_google_id(self):
        """Test getting existing user by Google ID"""
        # Create mock user
        existing_user = User(
            id=uuid.uuid4(),
            email='user@gmail.com',
            google_id='google-123',
            name='Test User',
            is_active=True
        )
        
        # Mock database query
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        
        google_user_info = {
            'google_id': 'google-123',
            'email': 'user@gmail.com',
            'name': 'Test User'
        }
        
        result = self.auth_service.get_or_create_user_from_google(google_user_info, self.mock_db)
        
        assert result == existing_user
        self.mock_db.commit.assert_called_once()
    
    def test_get_or_create_user_new_user(self):
        """Test creating new user from Google info"""
        # Mock database queries to return None (user doesn't exist)
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        google_user_info = {
            'google_id': 'google-123',
            'email': 'newuser@gmail.com',
            'name': 'New User'
        }
        
        result = self.auth_service.get_or_create_user_from_google(google_user_info, self.mock_db)
        
        assert result.email == 'newuser@gmail.com'
        assert result.google_id == 'google-123'
        assert result.name == 'New User'
        assert result.is_active is True
        assert result.profile_completed is False
        
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
    
    def test_get_user_by_id_success(self):
        """Test getting user by ID"""
        user_id = str(uuid.uuid4())
        mock_user = User(
            id=uuid.UUID(user_id),
            email='user@example.com',
            name='Test User',
            is_active=True
        )
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = self.auth_service.get_user_by_id(user_id, self.mock_db)
        
        assert result == mock_user
    
    def test_get_user_by_id_invalid_uuid(self):
        """Test getting user by invalid UUID"""
        result = self.auth_service.get_user_by_id('invalid-uuid', self.mock_db)
        
        assert result is None
    
    def test_create_tokens_for_user(self):
        """Test creating tokens for user"""
        user = User(
            id=uuid.uuid4(),
            email='user@example.com',
            name='Test User'
        )
        
        tokens = self.auth_service.create_tokens_for_user(user)
        
        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        assert tokens['token_type'] == 'bearer'
        
        # Verify tokens are valid
        access_payload = self.auth_service.verify_token(tokens['access_token'], 'access')
        refresh_payload = self.auth_service.verify_token(tokens['refresh_token'], 'refresh')
        
        assert access_payload['sub'] == str(user.id)
        assert refresh_payload['sub'] == str(user.id)
    
    def test_refresh_access_token_success(self):
        """Test successful access token refresh"""
        user = User(
            id=uuid.uuid4(),
            email='user@example.com',
            name='Test User',
            is_active=True
        )
        
        # Create refresh token
        refresh_token = self.auth_service.create_refresh_token({
            'sub': str(user.id),
            'email': user.email
        })
        
        # Mock database query
        self.mock_db.query.return_value.filter.return_value.first.return_value = user
        
        result = self.auth_service.refresh_access_token(refresh_token, self.mock_db)
        
        assert 'access_token' in result
        assert 'refresh_token' in result
        assert result['token_type'] == 'bearer'
    
    def test_refresh_access_token_invalid_token(self):
        """Test access token refresh with invalid token"""
        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.refresh_access_token('invalid-token', self.mock_db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthMiddleware:
    """Test cases for authentication middleware"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db = Mock(spec=Session)
        self.mock_request = Mock()
        self.mock_request.headers = {}
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_valid_token(self):
        """Test getting current user with valid JWT token"""
        # Create test user
        user = User(
            id=uuid.uuid4(),
            email='user@example.com',
            name='Test User',
            is_active=True
        )
        
        # Create valid token
        token_data = {'sub': str(user.id), 'email': user.email}
        access_token = auth_service.create_access_token(token_data)
        
        # Mock credentials
        mock_credentials = Mock()
        mock_credentials.credentials = access_token
        
        # Mock database query
        self.mock_db.query.return_value.filter.return_value.first.return_value = user
        
        # Mock auth_service.get_user_by_id
        with patch.object(auth_service, 'get_user_by_id', return_value=user):
            result = await get_current_user(self.mock_request, mock_credentials, self.mock_db)
        
        assert result == user
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_credentials(self):
        """Test getting current user without credentials"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(self.mock_request, None, self.mock_db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Not authenticated" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_x_user_id_header(self):
        """Test backward compatibility with X-User-Id header"""
        user_id = str(uuid.uuid4())
        user = User(
            id=uuid.UUID(user_id),
            email='user@example.com',
            name='Test User',
            is_active=True
        )
        
        # Set X-User-Id header
        self.mock_request.headers = {'X-User-Id': user_id}
        
        # Mock auth_service.get_user_by_id
        with patch.object(auth_service, 'get_user_by_id', return_value=user):
            result = await get_current_user(self.mock_request, None, self.mock_db)
        
        assert result == user
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_success(self):
        """Test getting current active user"""
        user = User(
            id=uuid.uuid4(),
            email='user@example.com',
            name='Test User',
            is_active=True
        )
        
        result = await get_current_active_user(user)
        
        assert result == user
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self):
        """Test getting current user when user is inactive"""
        user = User(
            id=uuid.uuid4(),
            email='user@example.com',
            name='Test User',
            is_active=False
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(user)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Inactive user" in str(exc_info.value.detail)


class TestAuthConfiguration:
    """Test cases for authentication configuration"""
    
    def test_jwt_secret_key_configuration(self):
        """Test JWT secret key configuration"""
        settings = get_settings()
        
        # JWT secret key should be configured
        jwt_secret = settings.get_jwt_secret_key()
        assert jwt_secret is not None
        assert len(jwt_secret) >= 32
    
    def test_google_oauth_configuration(self):
        """Test Google OAuth configuration"""
        settings = get_settings()
        
        # Google client ID should be configurable
        assert hasattr(settings.security, 'google_client_id')
        assert hasattr(settings.security, 'google_client_secret')
    
    def test_token_expiration_configuration(self):
        """Test token expiration configuration"""
        settings = get_settings()
        
        # Token expiration should be configurable
        assert settings.security.access_token_expire_minutes > 0
        assert settings.security.refresh_token_expire_days > 0


if __name__ == "__main__":
    pytest.main([__file__])