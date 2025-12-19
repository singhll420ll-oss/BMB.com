"""
Pydantic schemas for Service model
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ServiceBase(BaseModel):
    """Base service schema"""
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

class ServiceCreate(ServiceBase):
    """Schema for creating a service"""
    pass

class ServiceUpdate(BaseModel):
    """Schema for updating a service"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    image_url: Optional[str] = None

class ServiceResponse(ServiceBase):
    """Schema for service response"""
    id: int
    image_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True