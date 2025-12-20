"""
CRUD operations for Bite Me Buddy
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload
import logging

from models import User, Service, MenuItem, Order, OrderItem, TeamMemberPlan, UserSession
from schemas import (
    UserCreate, UserUpdate, ServiceCreate, ServiceUpdate, 
    MenuItemCreate, MenuItemUpdate, OrderCreate, OrderUpdate,
    TeamMemberPlanCreate, UserSessionCreate
)
from core.security import get_password_hash, verify_password, generate_otp
from core.config import settings

logger = logging.getLogger(__name__)

# User CRUD
async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """Create a new user"""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        name=user.name,
        username=user.username,
        email=user.email,
        phone=user.phone,
        address=user.address,
        hashed_password=hashed_password,
        role=user.role.value
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get user by username"""
    result = await db.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email"""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()

async def get_user_by_phone(db: AsyncSession, phone: str) -> Optional[User]:
    """Get user by phone"""
    result = await db.execute(
        select(User).where(User.phone == phone)
    )
    return result.scalar_one_or_none()

async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """Update user"""
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """Delete user"""
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return False
    
    await db.delete(db_user)
    await db.commit()
    return True

async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    """Get all users with pagination"""
    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_users_by_role(db: AsyncSession, role: str, skip: int = 0, limit: int = 100) -> List[User]:
    """Get users by role"""
    result = await db.execute(
        select(User)
        .where(User.role == role)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

# Service CRUD
async def create_service(db: AsyncSession, service: ServiceCreate) -> Service:
    """Create a new service"""
    db_service = Service(
        name=service.name,
        description=service.description
    )
    db.add(db_service)
    await db.commit()
    await db.refresh(db_service)
    return db_service

async def get_service_by_id(db: AsyncSession, service_id: int) -> Optional[Service]:
    """Get service by ID"""
    result = await db.execute(
        select(Service)
        .options(selectinload(Service.menu_items))
        .where(Service.id == service_id)
    )
    return result.scalar_one_or_none()

async def get_all_services(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Service]:
    """Get all services with pagination"""
    result = await db.execute(
        select(Service)
        .order_by(Service.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_service(db: AsyncSession, service_id: int, service_update: ServiceUpdate) -> Optional[Service]:
    """Update service"""
    db_service = await get_service_by_id(db, service_id)
    if not db_service:
        return None
    
    update_data = service_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_service, field, value)
    
    await db.commit()
    await db.refresh(db_service)
    return db_service

async def delete_service(db: AsyncSession, service_id: int) -> bool:
    """Delete service"""
    db_service = await get_service_by_id(db, service_id)
    if not db_service:
        return False
    
    await db.delete(db_service)
    await db.commit()
    return True

# Menu Item CRUD
async def create_menu_item(db: AsyncSession, menu_item: MenuItemCreate) -> MenuItem:
    """Create a new menu item"""
    db_menu_item = MenuItem(
        service_id=menu_item.service_id,
        name=menu_item.name,
        description=menu_item.description,
        price=menu_item.price
    )
    db.add(db_menu_item)
    await db.commit()
    await db.refresh(db_menu_item)
    return db_menu_item

async def get_menu_item_by_id(db: AsyncSession, menu_item_id: int) -> Optional[MenuItem]:
    """Get menu item by ID"""
    result = await db.execute(
        select(MenuItem)
        .where(MenuItem.id == menu_item_id)
    )
    return result.scalar_one_or_none()

async def get_menu_items_by_service(db: AsyncSession, service_id: int) -> List[MenuItem]:
    """Get menu items by service ID"""
    result = await db.execute(
        select(MenuItem)
        .where(MenuItem.service_id == service_id)
        .order_by(MenuItem.name)
    )
    return result.scalars().all()

async def update_menu_item(db: AsyncSession, menu_item_id: int, menu_item_update: MenuItemUpdate) -> Optional[MenuItem]:
    """Update menu item"""
    db_menu_item = await get_menu_item_by_id(db, menu_item_id)
    if not db_menu_item:
        return None
    
    update_data = menu_item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_menu_item, field, value)
    
    await db.commit()
    await db.refresh(db_menu_item)
    return db_menu_item

async def delete_menu_item(db: AsyncSession, menu_item_id: int) -> bool:
    """Delete menu item"""
    db_menu_item = await get_menu_item_by_id(db, menu_item_id)
    if not db_menu_item:
        return False
    
    await db.delete(db_menu_item)
    await db.commit()
    return True

# Order CRUD
async def create_order(db: AsyncSession, order: OrderCreate, customer_id: int) -> Order:
    """Create a new order"""
    # Calculate total amount
    total_amount = Decimal('0')
    for item in order.items:
        menu_item = await get_menu_item_by_id(db, item.menu_item_id)
        if menu_item:
            total_amount += menu_item.price * item.quantity
    
    # Create order
    db_order = Order(
        customer_id=customer_id,
        service_id=order.service_id,
        total_amount=total_amount,
        address=order.address,
        phone=order.phone,
        notes=order.notes,
        status="pending"
    )
    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)
    
    # Create order items
    for item in order.items:
        menu_item = await get_menu_item_by_id(db, item.menu_item_id)
        if menu_item:
            order_item = OrderItem(
                order_id=db_order.id,
                menu_item_id=item.menu_item_id,
                quantity=item.quantity,
                price_at_time=menu_item.price
            )
            db.add(order_item)
    
    await db.commit()
    await db.refresh(db_order)
    return db_order

async def get_order_by_id(db: AsyncSession, order_id: int) -> Optional[Order]:
    """Get order by ID"""
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.customer),
            selectinload(Order.service),
            selectinload(Order.team_member),
            selectinload(Order.order_items).selectinload(OrderItem.menu_item)
        )
        .where(Order.id == order_id)
    )
    return result.scalar_one_or_none()

async def get_orders_by_customer(db: AsyncSession, customer_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
    """Get orders by customer ID"""
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.service),
            selectinload(Order.order_items).selectinload(OrderItem.menu_item)
        )
        .where(Order.customer_id == customer_id)
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_orders_by_team_member(db: AsyncSession, team_member_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
    """Get orders assigned to team member"""
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.customer),
            selectinload(Order.service),
            selectinload(Order.order_items).selectinload(OrderItem.menu_item)
        )
        .where(Order.assigned_to == team_member_id)
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_all_orders(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Order]:
    """Get all orders"""
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.customer),
            selectinload(Order.service),
            selectinload(Order.team_member),
            selectinload(Order.order_items).selectinload(OrderItem.menu_item)
        )
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_order(db: AsyncSession, order_id: int, order_update: OrderUpdate) -> Optional[Order]:
    """Update order"""
    db_order = await get_order_by_id(db, order_id)
    if not db_order:
        return None
    
    update_data = order_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_order, field, value)
    
    await db.commit()
    await db.refresh(db_order)
    return db_order

async def assign_order_to_team_member(db: AsyncSession, order_id: int, team_member_id: int) -> Optional[Order]:
    """Assign order to team member"""
    db_order = await get_order_by_id(db, order_id)
    if not db_order:
        return None
    
    db_order.assigned_to = team_member_id
    await db.commit()
    await db.refresh(db_order)
    return db_order

async def generate_order_otp(db: AsyncSession, order_id: int) -> Optional[Dict[str, Any]]:
    """Generate OTP for order delivery confirmation"""
    db_order = await get_order_by_id(db, order_id)
    if not db_order:
        return None
    
    # Generate OTP
    otp = generate_otp()
    otp_expiry = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    
    # Update order
    db_order.otp = otp
    db_order.otp_expiry = otp_expiry
    db_order.otp_attempts = 0
    
    await db.commit()
    await db.refresh(db_order)
    
    return {
        "order_id": order_id,
        "otp": otp,
        "expires_at": otp_expiry,
        "phone": db_order.phone
    }

async def verify_order_otp(db: AsyncSession, order_id: int, otp: str) -> Dict[str, Any]:
    """Verify OTP for order delivery"""
    db_order = await get_order_by_id(db, order_id)
    if not db_order:
        return {"success": False, "message": "Order not found"}
    
    # Check OTP attempts
    if db_order.otp_attempts >= settings.OTP_MAX_ATTEMPTS:
        return {"success": False, "message": "Maximum OTP attempts exceeded"}
    
    # Check OTP expiry
    if db_order.otp_expiry and datetime.utcnow() > db_order.otp_expiry:
        return {"success": False, "message": "OTP has expired"}
    
    # Verify OTP
    if db_order.otp == otp:
        db_order.status = "delivered"
        db_order.otp = None
        db_order.otp_expiry = None
        await db.commit()
        return {"success": True, "message": "Delivery confirmed successfully"}
    else:
        # Increment OTP attempts
        db_order.otp_attempts += 1
        await db.commit()
        remaining_attempts = settings.OTP_MAX_ATTEMPTS - db_order.otp_attempts
        return {
            "success": False, 
            "message": f"Invalid OTP. {remaining_attempts} attempts remaining"
        }

# Team Member Plan CRUD
async def create_team_member_plan(db: AsyncSession, plan: TeamMemberPlanCreate, admin_id: int) -> TeamMemberPlan:
    """Create a new team member plan"""
    db_plan = TeamMemberPlan(
        admin_id=admin_id,
        team_member_id=plan.team_member_id,
        description=plan.description
    )
    db.add(db_plan)
    await db.commit()
    await db.refresh(db_plan)
    return db_plan

async def get_plans_by_team_member(db: AsyncSession, team_member_id: int, skip: int = 0, limit: int = 100) -> List[TeamMemberPlan]:
    """Get plans for team member"""
    result = await db.execute(
        select(TeamMemberPlan)
        .options(selectinload(TeamMemberPlan.admin))
        .where(TeamMemberPlan.team_member_id == team_member_id)
        .order_by(TeamMemberPlan.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_todays_plans(db: AsyncSession, team_member_id: int) -> List[TeamMemberPlan]:
    """Get today's plans for team member"""
    today = date.today()
    result = await db.execute(
        select(TeamMemberPlan)
        .options(selectinload(TeamMemberPlan.admin))
        .where(
            and_(
                TeamMemberPlan.team_member_id == team_member_id,
                func.date(TeamMemberPlan.created_at) == today
            )
        )
        .order_by(TeamMemberPlan.created_at.desc())
    )
    return result.scalars().all()

# User Session CRUD
async def create_user_session(db: AsyncSession, user_id: int) -> UserSession:
    """Create a new user session"""
    now = datetime.utcnow()
    db_session = UserSession(
        user_id=user_id,
        login_time=now,
        date=now.date()
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session

async def update_user_session_logout(db: AsyncSession, session_id: int) -> Optional[UserSession]:
    """Update user session with logout time"""
    result = await db.execute(
        select(UserSession).where(UserSession.id == session_id)
    )
    db_session = result.scalar_one_or_none()
    if not db_session:
        return None
    
    db_session.logout_time = datetime.utcnow()
    await db.commit()
    await db.refresh(db_session)
    return db_session

async def get_user_sessions(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[UserSession]:
    """Get user sessions"""
    result = await db.execute(
        select(UserSession)
        .where(UserSession.user_id == user_id)
        .order_by(UserSession.login_time.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_user_online_stats(db: AsyncSession, user_id: int) -> Dict[str, Any]:
    """Get user online statistics"""
    result = await db.execute(
        select(
            func.count(UserSession.id).label("total_sessions"),
            func.sum(
                func.extract('epoch', UserSession.logout_time - UserSession.login_time) / 60
            ).label("total_minutes")
        )
        .where(
            and_(
                UserSession.user_id == user_id,
                UserSession.logout_time.is_not(None)
            )
        )
    )
    stats = result.first()
    
    # Get last session
    result = await db.execute(
        select(UserSession)
        .where(UserSession.user_id == user_id)
        .order_by(UserSession.login_time.desc())
        .limit(1)
    )
    last_session = result.scalar_one_or_none()
    
    return {
        "total_sessions": stats.total_sessions or 0,
        "total_minutes": float(stats.total_minutes or 0),
        "avg_session_minutes": float(stats.total_minutes or 0) / (stats.total_sessions or 1),
        "last_login": last_session.login_time if last_session else None,
        "last_logout": last_session.logout_time if last_session else None
    }

async def get_all_users_online_stats(db: AsyncSession) -> List[Dict[str, Any]]:
    """Get online statistics for all users"""
    # Subquery for user stats
    stats_subquery = select(
        UserSession.user_id,
        func.count(UserSession.id).label("total_sessions"),
        func.sum(
            func.extract('epoch', UserSession.logout_time - UserSession.login_time) / 60
        ).label("total_minutes")
    ).where(
        UserSession.logout_time.is_not(None)
    ).group_by(
        UserSession.user_id
    ).subquery()
    
    # Main query
    result = await db.execute(
        select(
            User.id,
            User.name,
            User.role,
            stats_subquery.c.total_sessions,
            stats_subquery.c.total_minutes,
            func.max(UserSession.login_time).label("last_login"),
            func.max(UserSession.logout_time).label("last_logout")
        )
        .outerjoin(stats_subquery, User.id == stats_subquery.c.user_id)
        .outerjoin(UserSession, User.id == UserSession.user_id)
        .group_by(User.id, stats_subquery.c.total_sessions, stats_subquery.c.total_minutes)
        .order_by(User.role, User.name)
    )
    
    users_stats = []
    for row in result:
        total_minutes = float(row.total_minutes or 0)
        total_sessions = row.total_sessions or 0
        avg_minutes = total_minutes / total_sessions if total_sessions > 0 else 0
        
        users_stats.append({
            "user_id": row.id,
            "user_name": row.name,
            "role": row.role,
            "total_sessions": total_sessions,
            "total_minutes": total_minutes,
            "avg_session_minutes": round(avg_minutes, 2),
            "last_login": row.last_login,
            "last_logout": row.last_logout
        })
    
    return users_stats
