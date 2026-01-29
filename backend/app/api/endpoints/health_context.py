"""
Health Context Document API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database.connection import get_db
from app.schemas.health_context import (
    HealthContextDocumentCreate,
    HealthContextDocumentResponse,
    HealthContextDocumentListResponse,
    HealthContextMetrics
)
from app.services.health_context_service import HealthContextService

router = APIRouter(prefix="/health-context", tags=["health-context"])


@router.post("/{user_id}", response_model=HealthContextDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_health_context_document(
    user_id: UUID,
    hcd_data: HealthContextDocumentCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new Health Context Document for a user.
    
    This generates a new HCD version from the user's current profile, goals, and preferences.
    
    **Validates: Requirements 2.4.1, 2.4.2, 2.4.3, 2.4.4**
    """
    try:
        hcd_service = HealthContextService(db)
        hcd = await hcd_service.create_health_context_document(user_id, hcd_data)
        return hcd
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create health context document"
        )


@router.get("/{user_id}/current", response_model=HealthContextDocumentResponse)
async def get_current_health_context_document(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get the current (active) Health Context Document for a user.
    
    **Validates: Requirements 2.4.1**
    """
    try:
        hcd_service = HealthContextService(db)
        hcd = await hcd_service.get_current_health_context_document(user_id)
        if not hcd:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active health context document found for user"
            )
        return hcd
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve current health context document"
        )


@router.get("/{user_id}/version/{version}", response_model=HealthContextDocumentResponse)
async def get_health_context_document_by_version(
    user_id: UUID,
    version: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific version of a Health Context Document.
    
    **Validates: Requirements 2.4.4, 2.4.5**
    """
    try:
        hcd_service = HealthContextService(db)
        hcd = await hcd_service.get_health_context_document_by_version(user_id, version)
        if not hcd:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Health context document version {version} not found for user"
            )
        return hcd
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health context document"
        )


@router.get("/{user_id}/history", response_model=HealthContextDocumentListResponse)
async def get_health_context_document_history(
    user_id: UUID,
    limit: Optional[int] = 10,
    offset: Optional[int] = 0,
    db: Session = Depends(get_db)
):
    """
    Get the version history of Health Context Documents for a user.
    
    **Validates: Requirements 2.4.4, 2.4.5**
    """
    try:
        hcd_service = HealthContextService(db)
        history = await hcd_service.get_health_context_document_history(user_id, limit, offset)
        return history
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health context document history"
        )


@router.post("/{user_id}/update-from-profile", response_model=HealthContextDocumentResponse, status_code=status.HTTP_201_CREATED)
async def update_health_context_from_profile(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Create a new HCD version from the user's current profile, goals, and preferences.
    
    This is a convenience endpoint that automatically pulls the user's current data
    and generates a new HCD version.
    
    **Validates: Requirements 2.4.1, 2.4.2, 2.4.3, 2.4.4, 2.4.5**
    """
    try:
        hcd_service = HealthContextService(db)
        hcd = await hcd_service.update_health_context_from_profile(user_id)
        return hcd
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update health context document from profile"
        )


@router.get("/{user_id}/metrics", response_model=HealthContextMetrics)
async def get_health_context_metrics(
    user_id: UUID,
    version: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get calculated health metrics from a Health Context Document.
    
    If no version is specified, uses the current active version.
    
    **Validates: Requirements 2.4.2, 2.4.3**
    """
    try:
        hcd_service = HealthContextService(db)
        metrics = await hcd_service.get_health_context_metrics(user_id, version)
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health context document not found"
            )
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health context metrics"
        )


@router.delete("/{user_id}/version/{version}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_health_context_document_version(
    user_id: UUID,
    version: int,
    db: Session = Depends(get_db)
):
    """
    Delete a specific version of a Health Context Document.
    
    Note: Cannot delete the active version. Must activate another version first.
    """
    try:
        hcd_service = HealthContextService(db)
        success = await hcd_service.delete_health_context_document_version(user_id, version)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Health context document version {version} not found or cannot be deleted"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete health context document version"
        )


@router.post("/{user_id}/version/{version}/activate", response_model=HealthContextDocumentResponse)
async def activate_health_context_document_version(
    user_id: UUID,
    version: int,
    db: Session = Depends(get_db)
):
    """
    Activate a specific version of a Health Context Document.
    
    This makes the specified version the active one and deactivates all others.
    """
    try:
        hcd_service = HealthContextService(db)
        hcd = await hcd_service.activate_health_context_document_version(user_id, version)
        if not hcd:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Health context document version {version} not found"
            )
        return hcd
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate health context document version"
        )