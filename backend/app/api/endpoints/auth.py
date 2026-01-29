"""
Authentication API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.auth_service import auth_service
from app.schemas.auth import (
    GoogleTokenRequest, 
    TokenResponse, 
    RefreshTokenRequest,
    AuthenticatedUser,
    UserAuthInfo,
    LogoutRequest,
    LogoutResponse
)
from app.middleware.auth import get_current_active_user
from app.models.user import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/google", response_model=AuthenticatedUser)
async def google_oauth_login(
    request: GoogleTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user with Google OAuth token
    """
    try:
        # Verify Google token and get user info
        google_user_info = auth_service.verify_google_token(request.token)
        
        # Get or create user/registration request
        user, is_new_registration = auth_service.get_or_create_user_from_google(google_user_info, db)
        
        # If user is None, it means they need approval
        if user is None:
            # Check registration status
            status_info = auth_service.get_user_status(google_user_info['email'], db)
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail={
                    "message": status_info["message"],
                    "status": status_info["status"],
                    "email": google_user_info['email'],
                    "is_new_registration": is_new_registration
                }
            )
        
        # Create JWT tokens for approved user
        tokens = auth_service.create_tokens_for_user(user)
        
        # Prepare response
        user_info = UserAuthInfo(
            id=str(user.id),
            email=user.email,
            name=user.name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            profile_completed=user.profile_completed,
            created_at=user.created_at
        )
        
        token_response = TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=30 * 60  # 30 minutes in seconds
        )
        
        return AuthenticatedUser(
            user=user_info,
            tokens=token_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    try:
        tokens = auth_service.refresh_access_token(request.refresh_token, db)
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=30 * 60  # 30 minutes in seconds
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: LogoutRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout user (invalidate tokens)
    Note: In a production system, you would maintain a blacklist of invalidated tokens
    """
    # In a simple implementation, we just return success
    # In production, you would:
    # 1. Add the refresh token to a blacklist/redis cache
    # 2. Optionally add the access token to blacklist (though it expires quickly)
    
    return LogoutResponse(
        message="Successfully logged out"
    )


@router.get("/me", response_model=UserAuthInfo)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information
    """
    return UserAuthInfo(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        profile_completed=current_user.profile_completed,
        created_at=current_user.created_at
    )


@router.get("/status")
async def auth_status():
    """
    Check authentication service status
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "google_oauth": "enabled",
        "jwt_auth": "enabled"
    }


@router.get("/user-status")
async def get_user_status(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Get user approval status by email
    """
    try:
        status_info = auth_service.get_user_status(email, db)
        return status_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get user status: {str(e)}"
        )