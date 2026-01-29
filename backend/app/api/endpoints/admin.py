"""
Admin API endpoints for managing user approvals
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.middleware.admin import get_current_admin_user
from app.models.user import User, RegistrationRequest
from app.schemas.admin import (
    RegistrationRequestResponse,
    PendingRequestsResponse,
    ApprovalResponse
)


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/pending-requests", response_model=PendingRequestsResponse)
async def get_pending_requests(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all pending registration requests
    
    **ADMIN ONLY**: This endpoint requires admin privileges.
    """
    try:
        # Get all pending registration requests
        pending_requests = db.query(RegistrationRequest).filter(
            RegistrationRequest.status == 'pending'
        ).order_by(RegistrationRequest.created_at.desc()).all()
        
        # Convert to response format
        requests_data = [
            RegistrationRequestResponse(
                id=str(req.id),
                email=req.email,
                name=req.name,
                google_id=req.google_id,
                status=req.status,
                created_at=req.created_at,
                updated_at=req.updated_at
            )
            for req in pending_requests
        ]
        
        return PendingRequestsResponse(
            requests=requests_data,
            count=len(requests_data)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending requests: {str(e)}"
        )


@router.post("/approve-user/{request_id}", response_model=ApprovalResponse)
async def approve_user_request(
    request_id: str,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Approve a user registration request
    
    **ADMIN ONLY**: This endpoint requires admin privileges.
    """
    try:
        # Find the registration request
        registration_request = db.query(RegistrationRequest).filter(
            RegistrationRequest.id == request_id
        ).first()
        
        if not registration_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration request not found"
            )
        
        if registration_request.status != 'pending':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request is already {registration_request.status}"
            )
        
        # Approve the request
        registration_request.approve()
        db.commit()
        
        # Create the user account
        new_user = User(
            email=registration_request.email,
            google_id=registration_request.google_id,
            name=registration_request.name,
            is_active=True,
            is_admin=False,
            approval_status='approved',
            profile_completed=False
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return ApprovalResponse(
            success=True,
            message=f"User {registration_request.email} has been approved and can now access the application"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve user: {str(e)}"
        )


@router.post("/decline-user/{request_id}", response_model=ApprovalResponse)
async def decline_user_request(
    request_id: str,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Decline a user registration request
    
    **ADMIN ONLY**: This endpoint requires admin privileges.
    """
    try:
        # Find the registration request
        registration_request = db.query(RegistrationRequest).filter(
            RegistrationRequest.id == request_id
        ).first()
        
        if not registration_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration request not found"
            )
        
        if registration_request.status != 'pending':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request is already {registration_request.status}"
            )
        
        # Decline the request
        registration_request.decline()
        db.commit()
        
        return ApprovalResponse(
            success=True,
            message=f"User {registration_request.email} registration request has been declined"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to decline user: {str(e)}"
        )


@router.get("/all-requests", response_model=PendingRequestsResponse)
async def get_all_requests(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all registration requests (pending, approved, declined)
    
    **ADMIN ONLY**: This endpoint requires admin privileges.
    """
    try:
        # Get all registration requests
        all_requests = db.query(RegistrationRequest).order_by(
            RegistrationRequest.created_at.desc()
        ).all()
        
        # Convert to response format
        requests_data = [
            RegistrationRequestResponse(
                id=str(req.id),
                email=req.email,
                name=req.name,
                google_id=req.google_id,
                status=req.status,
                created_at=req.created_at,
                updated_at=req.updated_at
            )
            for req in all_requests
        ]
        
        return PendingRequestsResponse(
            requests=requests_data,
            count=len(requests_data)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get all requests: {str(e)}"
        )


@router.post("/enable-user/{user_id}", response_model=ApprovalResponse)
async def enable_user(
    user_id: str,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Enable a user account (set is_active = True)
    
    **ADMIN ONLY**: This endpoint requires admin privileges.
    """
    try:
        # Find the user
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent admin from disabling themselves
        if user.id == admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin cannot disable their own account"
            )
        
        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already enabled"
            )
        
        # Enable the user
        user.is_active = True
        db.commit()
        
        return ApprovalResponse(
            success=True,
            message=f"User {user.email} has been enabled and can now access the application"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable user: {str(e)}"
        )


@router.post("/disable-user/{user_id}", response_model=ApprovalResponse)
async def disable_user(
    user_id: str,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Disable a user account (set is_active = False)
    
    **ADMIN ONLY**: This endpoint requires admin privileges.
    """
    try:
        # Find the user
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent admin from disabling themselves
        if user.id == admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin cannot disable their own account"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already disabled"
            )
        
        # Disable the user
        user.is_active = False
        db.commit()
        
        return ApprovalResponse(
            success=True,
            message=f"User {user.email} has been disabled and can no longer access the application"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable user: {str(e)}"
        )