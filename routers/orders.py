"""
Orders router for order-related endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import structlog

from database import get_db
from models.order import Order, OrderStatus
from crud.order import CRUDOrder
from core.exceptions import NotFoundError

router = APIRouter()
logger = structlog.get_logger(__name__)

@router.get("/stats")
async def get_order_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get order statistics"""
    try:
        stats = await CRUDOrder.get_order_stats(db)
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error(f"Error getting order stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving order statistics"
        )

@router.get("/recent")
async def get_recent_orders(
    limit: int = 10,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get recent orders"""
    try:
        # Validate status
        order_status = None
        if status:
            if status not in [s.value for s in OrderStatus]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid status"
                )
            order_status = OrderStatus(status)
        
        orders = await CRUDOrder.get_all_orders(db, limit=limit, status=order_status)
        
        # Format response
        order_list = []
        for order in orders:
            order_list.append({
                "id": order.id,
                "customer_id": order.customer_id,
                "customer_name": order.customer.name if order.customer else "Unknown",
                "service_id": order.service_id,
                "service_name": order.service.name if order.service else "Unknown",
                "total_amount": order.total_amount,
                "status": order.status.value,
                "assigned_to": order.assigned_to,
                "team_member_name": order.team_member.name if order.team_member else None,
                "created_at": order.created_at.isoformat(),
                "item_count": len(order.order_items)
            })
        
        return JSONResponse(content=order_list)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recent orders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving recent orders"
        )

@router.get("/{order_id}")
async def get_order_by_id(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get order by ID"""
    try:
        order = await CRUDOrder.get_by_id(db, order_id, with_items=True)
        if not order:
            raise NotFoundError("Order")
        
        # Format order items
        items = []
        for item in order.order_items:
            items.append({
                "id": item.id,
                "menu_item_id": item.menu_item_id,
                "item_name": item.item_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.subtotal
            })
        
        # Format response
        return {
            "id": order.id,
            "customer_id": order.customer_id,
            "customer_name": order.customer.name if order.customer else "Unknown",
            "service_id": order.service_id,
            "service_name": order.service.name if order.service else "Unknown",
            "total_amount": order.total_amount,
            "address": order.address,
            "special_instructions": order.special_instructions,
            "status": order.status.value,
            "assigned_to": order.assigned_to,
            "team_member_name": order.team_member.name if order.team_member else None,
            "created_at": order.created_at.isoformat(),
            "confirmed_at": order.confirmed_at.isoformat() if order.confirmed_at else None,
            "prepared_at": order.prepared_at.isoformat() if order.prepared_at else None,
            "out_for_delivery_at": order.out_for_delivery_at.isoformat() if order.out_for_delivery_at else None,
            "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
            "cancelled_at": order.cancelled_at.isoformat() if order.cancelled_at else None,
            "items": items
        }
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving order"
        )

@router.post("/{order_id}/assign")
async def assign_order(
    order_id: int,
    team_member_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Assign order to team member"""
    try:
        order = await CRUDOrder.assign_order(db, order_id, team_member_id)
        return {
            "success": True,
            "message": f"Order #{order_id} assigned successfully",
            "assigned_to": team_member_id
        }
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error assigning order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error assigning order"
        )

@router.post("/{order_id}/status")
async def update_order_status_api(
    order_id: int,
    status: str,
    db: AsyncSession = Depends(get_db)
):
    """Update order status (API endpoint)"""
    try:
        # Validate status
        if status not in [s.value for s in OrderStatus]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status"
            )
        
        order = await CRUDOrder.update(db, order_id, {"status": OrderStatus(status)})
        
        return {
            "success": True,
            "message": f"Order #{order_id} status updated to {status}",
            "status": status
        }
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating order status"
        )

@router.post("/{order_id}/generate-otp")
async def generate_otp_api(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Generate OTP for order delivery (API endpoint)"""
    try:
        otp = await CRUDOrder.generate_otp_for_delivery(db, order_id)
        
        return {
            "success": True,
            "message": "OTP generated successfully",
            "otp": otp,
            "order_id": order_id,
            "expires_in": "5 minutes"
        }
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating OTP"
        )

@router.post("/{order_id}/verify-otp")
async def verify_otp_api(
    order_id: int,
    otp: str,
    db: AsyncSession = Depends(get_db)
):
    """Verify OTP for order delivery (API endpoint)"""
    try:
        success = await CRUDOrder.verify_otp(db, order_id, otp)
        
        if success:
            return {
                "success": True,
                "message": "OTP verified successfully. Order marked as delivered.",
                "order_id": order_id,
                "status": "delivered"
            }
        else:
            return {
                "success": False,
                "message": "Invalid OTP",
                "order_id": order_id
            }
        
    except Exception as e:
        logger.error(f"Error verifying OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
