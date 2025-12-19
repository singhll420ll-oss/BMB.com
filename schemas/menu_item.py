"""
Pydantic schemas for MenuItem model
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class MenuItemBase(BaseModel):
    """Base menu item schema"""
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    
    @validator('price')
    def validate_price(cls, v):
        """Validate price"""
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return round(v, 2)
    
    class Config:
        from_attributes = True

class MenuItemCreate(MenuItemBase):
    """Schema for creating a menu item"""
    service_id: int

class MenuItemUpdate(BaseModel):
    """Schema for updating a menu item"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    is_available: Optional[bool] = None
    image_url: Optional[str] = None
    
    @validator('price')
    def validate_price(cls, v):
        """Validate price if provided"""
        if v is not None:
            if v <= 0:
                raise ValueError('Price must be greater than 0')
            return round(v, 2)
        return v

class MenuItemResponse(MenuItemBase):
    """Schema for menu item response"""
    id: int
    service_id: int
    is_available: bool
    image_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
