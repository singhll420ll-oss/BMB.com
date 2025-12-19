"""
Pydantic schemas for UserSession model
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserSessionBase(BaseModel):
    """Base user session schema"""
    pass
    
    class Config:
        from_attributes = True

class UserSessionCreate(UserSessionBase):
    """Schema for creating a user session"""
    user_id: int
    login_time: datetime

class UserSessionUpdate(BaseModel):
    """Schema for updating a user session"""
    logout_time: datetime

class UserSessionResponse(UserSessionBase):
    """Schema for user session response"""
    id: int
    user_id: int
    login_time: datetime
    logout_time: Optional[datetime]
    date: datetime
    duration_minutes: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True
