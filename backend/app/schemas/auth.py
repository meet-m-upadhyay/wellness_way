"""
Authentication-related Pydantic schemas
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class GoogleTokenRequest(BaseModel):
    """Request schema for Google OAuth token verification"""
    token: str = Field(..., description="Google OAuth ID token")


class EmailSignupRequest(BaseModel):
    """Request schema for email/password signup"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")
    confirm_password: str = Field(..., min_length=8, description="Password confirmation")
    name: Optional[str] = Field(None, description="User display name")


class EmailLoginRequest(BaseModel):
    """Request schema for email/password login"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Response schema for authentication tokens"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh"""
    refresh_token: str = Field(..., description="JWT refresh token")


class UserAuthInfo(BaseModel):
    """User authentication information"""
    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email")
    name: str = Field(..., description="User name")
    is_active: bool = Field(..., description="User active status")
    is_admin: bool = Field(..., description="User admin status")
    profile_completed: bool = Field(..., description="Profile completion status")
    created_at: datetime = Field(..., description="Account creation timestamp")


class AuthenticatedUser(BaseModel):
    """Authenticated user response"""
    user: UserAuthInfo
    tokens: TokenResponse


class LogoutRequest(BaseModel):
    """Request schema for logout"""
    refresh_token: Optional[str] = Field(None, description="JWT refresh token to invalidate")


class LogoutResponse(BaseModel):
    """Response schema for logout"""
    message: str = Field(default="Successfully logged out", description="Logout confirmation message")