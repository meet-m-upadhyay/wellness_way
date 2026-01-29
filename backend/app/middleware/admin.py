"""
Admin authentication middleware
"""

from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.middleware.auth import get_current_active_user
from app.models.user import User


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user and verify they have admin privileges.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User: The admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


def require_admin_email(email: str) -> bool:
    """
    Check if email has admin privileges.
    
    Args:
        email: Email address to check
        
    Returns:
        bool: True if email is admin, False otherwise
    """
    ADMIN_EMAIL = "meetupadhyaykgp@gmail.com"
    return email == ADMIN_EMAIL