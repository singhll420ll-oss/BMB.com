"""
Pydantic schemas for Order model
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderItemBase(BaseModel):
    """Base order item schema"""
    menu_item_id: int
    quantity: int = Field(..., gt=0)
    
    class Config:
        from_attributes = True

class OrderItemCreate(OrderItemBase):
    """Schema for creating an order item"""
    pass

class OrderItemResponse(OrderItemBase):
    """Schema for order item response"""
    id: int
    order_id: int
    unit_price: float
    item_name: str
    subtotal: float
    created_at: datetime
    
    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    """Base order schema"""
    service_id: int
    address: str = Field(..., min_length=10)
    special_instructions: Optional[str] = None
    
    class Config:
        from_attributes = True

class OrderCreate(OrderBase):
    """Schema for creating an order"""
    items: List[OrderItemCreate] = Field(..., min_items=1)
    
    @validator('items')
    def validate_items(cls, v):
        """Validate order items"""
        if len(v) == 0:
            raise ValueError('Order must have at least one item')
        
        # Check for duplicate menu items
        menu_item_ids = [item.menu_item_id for item in v]
        if len(set(menu_item_ids)) != len(menu_item_ids):
            raise ValueError('Duplicate menu items in order')
        
        return v

class OrderUpdate(BaseModel):
    """Schema for updating an order"""
    status: Optional[OrderStatus] = None
    assigned_to: Optional[int] = None
    special_instructions: Optional[str] = None

class OrderResponse(OrderBase):
    """Schema for order response"""
    id: int
    customer_id: int
    total_amount: float
    status: OrderStatus
    assigned_to: Optional[int]
    otp_attempts: int
    items: List[OrderItemResponse]
    
    # Timestamps
    created_at: datetime
    confirmed_at: Optional[datetime]
    prepared_at: Optional[datetime]
    out_for_delivery_at: Optional[datetime]
    delivered_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    
    class Config:
        from_attributes = True
