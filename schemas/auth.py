"""
Authentication related schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=50)
    role: Optional[str] = None

class Token(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    role: str
    username: str

class TokenData(BaseModel):
    """Schema for token data"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None

class OTPVerifyRequest(BaseModel):
    """Schema for OTP verification"""
    order_id: int
    otp: str = Field(..., min_length=4, max_length=4)
