"""
CRUD operations for Order model
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime, timedelta
import pytz

from models.order import Order, OrderStatus
from models.order_item import OrderItem
from models.menu_item import MenuItem
from models.user import User
from schemas.order import OrderCreate, OrderUpdate, OrderItemCreate
from core.exceptions import NotFoundError, ValidationError
from core.security import generate_otp, otp_expiry_time

IST = pytz.timezone('Asia/Kolkata')

class CRUDOrder:
    """CRUD operations for Order model"""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, order_id: int, with_items: bool = False) -> Optional[Order]:
        """Get order by ID"""
        query = select(Order).where(Order.id == order_id)
        
        if with_items:
            query = query.options(
                selectinload(Order.order_items).selectinload(OrderItem.menu_item),
                selectinload(Order.customer),
                selectinload(Order.service),
                selectinload(Order.team_member)
            )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, order_in: OrderCreate, customer_id: int) -> Order:
        """Create new order"""
        # Calculate total amount and validate items
        total_amount = 0
        order_items_data = []
        
        for item_in in order_in.items:
            menu_item = await db.get(MenuItem, item_in.menu_item_id)
            if not menu_item:
                raise NotFoundError(f"Menu item with ID {item_in.menu_item_id}")
            
            if not menu_item.is_available:
                raise ValidationError(f"Menu item '{menu_item.name}' is not available")
            
            subtotal = menu_item.price * item_in.quantity
            total_amount += subtotal
            
            order_items_data.append({
                "menu_item_id": item_in.menu_item_id,
                "quantity": item_in.quantity,
                "unit_price": menu_item.price,
                "item_name": menu_item.name
            })
        
        # Create order
        order_data = order_in.model_dump(exclude={"items"})
        order = Order(
            **order_data,
            customer_id=customer_id,
            total_amount=total_amount,
            status=OrderStatus.PENDING
        )
        db.add(order)
        await db.flush()  # Get order ID
        
        # Create order items
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                **item_data
            )
            db.add(order_item)
        
        await db.commit()
        await db.refresh(order)
        
        # Load relationships
        order = await CRUDOrder.get_by_id(db, order.id, with_items=True)
        return order
    
    @staticmethod
    async def update(db: AsyncSession, order_id: int, order_in: OrderUpdate) -> Optional[Order]:
        """Update order"""
        order = await CRUDOrder.get_by_id(db, order_id)
        if not order:
            raise NotFoundError("Order")
        
        update_data = order_in.model_dump(exclude_unset=True)
        
        # Handle status update
        if "status" in update_data:
            order.update_status(update_data["status"])
            update_data.pop("status")
        
        # Update other fields
        for field, value in update_data.items():
            setattr(order, field, value)
        
        await db.commit()
        await db.refresh(order)
        return order
    
    @staticmethod
    async def delete(db: AsyncSession, order_id: int) -> bool:
        """Delete order"""
        order = await CRUDOrder.get_by_id(db, order_id)
        if not order:
            raise NotFoundError("Order")
        
        await db.delete(order)
        await db.commit()
        return True
    
    @staticmethod
    async def get_customer_orders(db: AsyncSession, customer_id: int, limit: int = 50) -> List[Order]:
        """Get orders for a customer"""
        result = await db.execute(
            select(Order)
            .where(Order.customer_id == customer_id)
            .options(
                selectinload(Order.order_items),
                selectinload(Order.service)
            )
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_team_member_orders(db: AsyncSession, team_member_id: int) -> List[Order]:
        """Get orders assigned to a team member"""
        result = await db.execute(
            select(Order)
            .where(Order.assigned_to == team_member_id)
            .where(Order.status != OrderStatus.DELIVERED)
            .where(Order.status != OrderStatus.CANCELLED)
            .options(
                selectinload(Order.order_items).selectinload(OrderItem.menu_item),
                selectinload(Order.customer),
                selectinload(Order.service)
            )
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_all_orders(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[OrderStatus] = None,
        assigned_to: Optional[int] = None
    ) -> List[Order]:
        """Get all orders with filters"""
        query = select(Order).options(
            selectinload(Order.order_items),
            selectinload(Order.customer),
            selectinload(Order.service),
            selectinload(Order.team_member)
        )
        
        if status:
            query = query.where(Order.status == status)
        
        if assigned_to:
            query = query.where(Order.assigned_to == assigned_to)
        
        query = query.order_by(Order.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def assign_order(db: AsyncSession, order_id: int, team_member_id: int) -> Optional[Order]:
        """Assign order to team member"""
        order = await CRUDOrder.get_by_id(db, order_id)
        if not order:
            raise NotFoundError("Order")
        
        # Check if team member exists and is a team member
        team_member = await db.get(User, team_member_id)
        if not team_member or team_member.role != "team_member":
            raise ValidationError("Invalid team member")
        
        order.assigned_to = team_member_id
        await db.commit()
        await db.refresh(order)
        return order
    
    @staticmethod
    async def generate_otp_for_delivery(db: AsyncSession, order_id: int) -> str:
        """Generate OTP for order delivery"""
        order = await CRUDOrder.get_by_id(db, order_id)
        if not order:
            raise NotFoundError("Order")
        
        # Generate new OTP
        otp = generate_otp()
        order.otp = otp
        order.otp_expiry = otp_expiry_time()
        order.otp_attempts = 0
        
        await db.commit()
        return otp
    
    @staticmethod
    async def verify_otp(db: AsyncSession, order_id: int, otp: str) -> bool:
        """Verify OTP for order delivery"""
        order = await CRUDOrder.get_by_id(db, order_id)
        if not order:
            raise NotFoundError("Order")
        
        # Check OTP attempts
        if order.otp_attempts >= 3:
            raise ValidationError("Maximum OTP attempts exceeded")
        
        # Check if OTP is expired
        if order.otp_expiry and datetime.now(IST) > order.otp_expiry:
            raise ValidationError("OTP has expired")
        
        # Verify OTP
        if order.otp != otp:
            order.otp_attempts += 1
            await db.commit()
            return False
        
        # OTP verified - mark as delivered
        order.update_status(OrderStatus.DELIVERED)
        order.otp = None
        order.otp_expiry = None
        
        await db.commit()
        return True
    
    @staticmethod
    async def get_order_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get order statistics"""
        # Total orders
        result = await db.execute(select(func.count(Order.id)))
        total_orders = result.scalar()
        
        # Orders by status
        result = await db.execute(
            select(Order.status, func.count(Order.id))
            .group_by(Order.status)
        )
        orders_by_status = {row[0].value: row[1] for row in result.all()}
        
        # Today's orders
        today = datetime.now(IST).date()
        result = await db.execute(
            select(func.count(Order.id))
            .where(func.date(Order.created_at) == today)
        )
        todays_orders = result.scalar()
        
        # Total revenue
        result = await db.execute(
            select(func.sum(Order.total_amount))
            .where(Order.status == OrderStatus.DELIVERED)
        )
        total_revenue = result.scalar() or 0
        
        return {
            "total_orders": total_orders,
            "orders_by_status": orders_by_status,
            "todays_orders": todays_orders,
            "total_revenue": total_revenue
        }
