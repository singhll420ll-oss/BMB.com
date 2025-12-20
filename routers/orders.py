"""
Orders router for Bite Me Buddy
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from database import get_db
from models import User
from schemas import OrderCreate, OrderUpdate, OrderResponse, OTPVerify, OTPResponse
from crud import (
    create_order, get_order_by_id, get_orders_by_customer, get_orders_by_team_member,
    get_all_orders, update_order, assign_order_to_team_member, generate_order_otp, verify_order_otp
)
from routers.auth import get_current_user, require_role
from core.config import settings

# Twilio integration for OTP SMS
try:
    from twilio.rest import Client
    
    def send_otp_sms(phone: str, otp: str):
        """Send OTP via SMS using Twilio"""
        if not all([settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
            logger.warning("Twilio credentials not configured")
            return False
        
        try:
            client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=f"Your Bite Me Buddy delivery OTP is: {otp}. Valid for {settings.OTP_EXPIRE_MINUTES} minutes.",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone
            )
            logger.info(f"OTP SMS sent to {phone}: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Error sending OTP SMS: {e}")
            return False
except ImportError:
    def send_otp_sms(phone: str, otp: str):
        """Mock function when Twilio is not available"""
        logger.info(f"Mock OTP SMS to {phone}: {otp}")
        return True

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=OrderResponse)
async def create_new_order(
    order: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new order"""
    db_order = await create_order(db, order, current_user.id)
    logger.info(f"Order created: {db_order.id} by {current_user.username}")
    return OrderResponse.model_validate(db_order)

@router.get("/my-orders", response_model=List[OrderResponse])
async def read_my_orders(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's orders"""
    orders = await get_orders_by_customer(db, current_user.id, skip=skip, limit=limit)
    return [OrderResponse.model_validate(order) for order in orders]

@router.get("/team-member-orders", response_model=List[OrderResponse])
async def read_team_member_orders(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("team_member"))
):
    """Get orders assigned to team member"""
    orders = await get_orders_by_team_member(db, current_user.id, skip=skip, limit=limit)
    return [OrderResponse.model_validate(order) for order in orders]

@router.get("/all", response_model=List[OrderResponse])
async def read_all_orders(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Get all orders (admin only)"""
    orders = await get_all_orders(db, skip=skip, limit=limit)
    return [OrderResponse.model_validate(order) for order in orders]

@router.get("/{order_id}", response_model=OrderResponse)
async def read_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get order by ID"""
    order = await get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check permissions
    if current_user.role not in ["admin", "team_member"] and order.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order"
        )
    
    return OrderResponse.model_validate(order)

@router.put("/{order_id}", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    order_update: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Update order status (admin only)"""
    order = await update_order(db, order_id, order_update)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    logger.info(f"Order updated: {order.id} by {current_user.username}")
    return OrderResponse.model_validate(order)

@router.post("/{order_id}/assign/{team_member_id}")
async def assign_order(
    order_id: int,
    team_member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Assign order to team member (admin only)"""
    order = await assign_order_to_team_member(db, order_id, team_member_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    logger.info(f"Order {order_id} assigned to team member {team_member_id}")
    return {"message": "Order assigned successfully"}

@router.post("/{order_id}/generate-otp", response_model=OTPResponse)
async def generate_delivery_otp(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("team_member"))
):
    """Generate OTP for delivery confirmation (team member only)"""
    otp_data = await generate_order_otp(db, order_id)
    if not otp_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if order is assigned to current team member
    order = await get_order_by_id(db, order_id)
    if order.assigned_to != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate OTP for this order"
        )
    
    # Send OTP via SMS
    if order.phone:
        send_otp_sms(order.phone, otp_data["otp"])
    
    logger.info(f"OTP generated for order {order_id}")
    return OTPResponse(
        message="OTP generated and sent via SMS",
        order_id=order_id,
        expires_at=otp_data["expires_at"]
    )

@router.post("/{order_id}/verify-otp")
async def verify_delivery_otp(
    order_id: int,
    otp_verify: OTPVerify,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("team_member"))
):
    """Verify OTP for delivery confirmation (team member only)"""
    # Check if order exists and is assigned to current team member
    order = await get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.assigned_to != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to verify OTP for this order"
        )
    
    # Verify OTP
    result = await verify_order_otp(db, order_id, otp_verify.otp)
    
    if result["success"]:
        logger.info(f"OTP verified for order {order_id}")
        return {"message": result["message"], "status": "delivered"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )

@router.get("/stats/summary")
async def get_order_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Get order statistics (admin only)"""
    from sqlalchemy import func, select
    
    # Total orders
    result = await db.execute(select(func.count(Order.id)))
    total_orders = result.scalar()
    
    # Orders by status
    result = await db.execute(
        select(Order.status, func.count(Order.id))
        .group_by(Order.status)
    )
    orders_by_status = dict(result.all())
    
    # Total revenue
    result = await db.execute(select(func.sum(Order.total_amount)))
    total_revenue = result.scalar() or 0
    
    # Today's orders
    from datetime import date
    result = await db.execute(
        select(func.count(Order.id))
        .where(func.date(Order.created_at) == date.today())
    )
    today_orders = result.scalar()
    
    return {
        "total_orders": total_orders,
        "orders_by_status": orders_by_status,
        "total_revenue": float(total_revenue),
        "today_orders": today_orders
    }