"""
Admin-related Pydantic schemas
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class RegistrationRequestResponse(BaseModel):
    """Registration request response schema"""
    id: str = Field(..., description="Registration request ID")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User name")
    google_id: Optional[str] = Field(None, description="Google ID")
    status: str = Field(..., description="Request status (pending, approved, declined)")
    created_at: datetime = Field(..., description="Request creation timestamp")
    updated_at: datetime = Field(..., description="Request last update timestamp")

    class Config:
        from_attributes = True


class PendingRequestsResponse(BaseModel):
    """Response for pending requests list"""
    requests: List[RegistrationRequestResponse] = Field(..., description="List of registration requests")
    count: int = Field(..., description="Total number of requests")


class ApprovalResponse(BaseModel):
    """Response for approval/decline actions"""
    success: bool = Field(..., description="Whether the action was successful")
    message: str = Field(..., description="Response message")