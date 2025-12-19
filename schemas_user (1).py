"""
Pydantic schemas for User model
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import re
from enum import Enum

class UserRole(str, Enum):
    """User role enumeration for schemas"""
    CUSTOMER = "customer"
    TEAM_MEMBER = "team_member"
    ADMIN = "admin"

class UserBase(BaseModel):
    """Base user schema"""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        # Remove any non-digit characters
        digits = re.sub(r'\D', '', v)
        
        # Check if it's a valid Indian mobile number
        if len(digits) != 10 or not digits.startswith(('6', '7', '8', '9')):
            raise ValueError('Invalid Indian mobile number')
        
        return digits
    
    class Config:
        from_attributes = True

class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str = Field(..., min_length=8, max_length=50)
    address: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isalpha() for char in v):
            raise ValueError('Password must contain at least one letter')
        return v

class CustomerCreate(UserCreate):
    """Schema for creating a customer"""
    role: UserRole = UserRole.CUSTOMER

class TeamMemberCreate(UserCreate):
    """Schema for creating a team member"""
    role: UserRole = UserRole.TEAM_MEMBER

class AdminCreate(UserCreate):
    """Schema for creating an admin"""
    role: UserRole = UserRole.ADMIN

class UserUpdate(BaseModel):
    """Schema for updating a user"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=15)
    address: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=50)
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number if provided"""
        if v is not None:
            digits = re.sub(r'\D', '', v)
            if len(digits) != 10 or not digits.startswith(('6', '7', '8', '9')):
                raise ValueError('Invalid Indian mobile number')
            return digits
        return v

class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    role: UserRole
    address: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True