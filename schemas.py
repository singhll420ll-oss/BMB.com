"""
Pydantic schemas for Bite Me Buddy
"""

from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict
from enum import Enum

# Enums
class UserRole(str, Enum):
    CUSTOMER = "customer"
    TEAM_MEMBER = "team_member"
    ADMIN = "admin"

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# Base schemas
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# User schemas
class UserBase(BaseSchema):
    name: str = Field(..., min_length=2, max_length=100)
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    address: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserLogin(BaseSchema):
    username: str
    password: str

class UserUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    address: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime

class UserWithSessions(UserResponse):
    sessions: List["UserSessionResponse"] = []

# Service schemas
class ServiceBase(BaseSchema):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None

class ServiceResponse(ServiceBase):
    id: int
    image_url: Optional[str] = None
    created_at: datetime
    menu_items: List["MenuItemResponse"] = []

# Menu Item schemas
class MenuItemBase(BaseSchema):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)

class MenuItemCreate(MenuItemBase):
    service_id: int

class MenuItemUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)

class MenuItemResponse(MenuItemBase):
    id: int
    service_id: int
    image_url: Optional[str] = None
    created_at: datetime

# Order schemas
class OrderItemBase(BaseSchema):
    menu_item_id: int
    quantity: int = Field(..., gt=0)

class OrderCreate(BaseSchema):
    service_id: int
    items: List[OrderItemBase]
    address: str
    phone: str = Field(..., min_length=10, max_length=20)
    notes: Optional[str] = None

class OrderUpdate(BaseSchema):
    status: Optional[OrderStatus] = None
    assigned_to: Optional[int] = None

class OrderItemResponse(BaseSchema):
    id: int
    menu_item_id: int
    menu_item_name: str
    quantity: int
    price_at_time: Decimal
    created_at: datetime

class OrderResponse(BaseSchema):
    id: int
    customer_id: int
    service_id: int
    service_name: str
    total_amount: Decimal
    address: str
    phone: str
    notes: Optional[str]
    status: OrderStatus
    assigned_to: Optional[int]
    assigned_to_name: Optional[str]
    otp_attempts: int
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []

# Team Member Plan schemas
class TeamMemberPlanBase(BaseSchema):
    team_member_id: int
    description: Optional[str] = None

class TeamMemberPlanCreate(TeamMemberPlanBase):
    pass

class TeamMemberPlanResponse(TeamMemberPlanBase):
    id: int
    admin_id: int
    admin_name: str
    image_url: Optional[str]
    created_at: datetime

# User Session schemas
class UserSessionBase(BaseSchema):
    login_time: datetime
    logout_time: Optional[datetime] = None
    date: date

class UserSessionCreate(UserSessionBase):
    user_id: int

class UserSessionResponse(UserSessionBase):
    id: int
    user_id: int
    duration_minutes: Optional[float] = None
    
    @validator("duration_minutes", always=True)
    def calculate_duration(cls, v, values):
        if values.get("logout_time") and values.get("login_time"):
            duration = (values["logout_time"] - values["login_time"]).total_seconds() / 60
            return round(duration, 2)
        return None

# OTP schemas
class OTPVerify(BaseSchema):
    order_id: int
    otp: str = Field(..., min_length=4, max_length=6)

class OTPResponse(BaseSchema):
    message: str
    order_id: int
    expires_at: Optional[datetime] = None

# File upload schemas
class FileUploadResponse(BaseSchema):
    filename: str
    url: str
    size: int

# Statistics schemas
class UserOnlineStats(BaseSchema):
    user_id: int
    user_name: str
    role: str
    total_sessions: int
    total_minutes: float
    avg_session_minutes: float
    last_login: Optional[datetime]
    last_logout: Optional[datetime]

# Update forward references
UserResponse.update_forward_refs()
ServiceResponse.update_forward_refs()
