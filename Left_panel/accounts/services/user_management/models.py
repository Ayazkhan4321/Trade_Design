"""
Data models for User Management Service
"""
from typing import Optional
from pydantic import BaseModel, EmailStr


class AddUserToProfileRequest(BaseModel):
    """Request model for adding a user to profile"""
    primaryUserId: int
    secondaryUserEmail: str
    secondaryUserPassword: str


class RemoveUserFromProfileRequest(BaseModel):
    """Request model for removing a user from profile"""
    primaryUserId: int
    secondaryUserEmail: str


class AddUserToProfileResponse(BaseModel):
    """Response model for add user to profile"""
    data: Optional[dict] = None
    message: Optional[str] = None
    statusCode: Optional[int] = None
    
    class Config:
        extra = 'allow'
