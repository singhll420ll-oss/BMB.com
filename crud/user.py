"""
CRUD operations for User model
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, date, timedelta
import pytz

from models.user import User, UserRole
from models.user_session import UserSession
from schemas.user import UserCreate, UserUpdate
from core.security import get_password_hash, verify_password
from core.exceptions import NotFoundError, ValidationError

IST = pytz.timezone('Asia/Kolkata')

class CRUDUser:
    """CRUD operations for User model"""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username"""
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_phone(db: AsyncSession, phone: str) -> Optional[User]:
        """Get user by phone"""
        result = await db.execute(
            select(User).where(User.phone == phone)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def authenticate(db: AsyncSession, username: str, password: str) -> Optional[User]:
        """Authenticate user"""
        user = await CRUDUser.get_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    async def create(db: AsyncSession, user_in: UserCreate) -> User:
        """Create new user"""
        # Check if username exists
        existing_user = await CRUDUser.get_by_username(db, user_in.username)
        if existing_user:
            raise ValidationError(f"Username '{user_in.username}' already exists")
        
        # Check if email exists
        existing_email = await CRUDUser.get_by_email(db, user_in.email)
        if existing_email:
            raise ValidationError(f"Email '{user_in.email}' already exists")
        
        # Check if phone exists
        existing_phone = await CRUDUser.get_by_phone(db, user_in.phone)
        if existing_phone:
            raise ValidationError(f"Phone number '{user_in.phone}' already exists")
        
        # Create user
        user_data = user_in.model_dump(exclude={"password"})
        user_data["hashed_password"] = get_password_hash(user_in.password)
        
        user = User(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def update(db: AsyncSession, user_id: int, user_in: UserUpdate) -> Optional[User]:
        """Update user"""
        user = await CRUDUser.get_by_id(db, user_id)
        if not user:
            raise NotFoundError("User")
        
        update_data = user_in.model_dump(exclude_unset=True)
        
        # Hash password if provided
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        # Check unique constraints for updated fields
        if "username" in update_data and update_data["username"] != user.username:
            existing = await CRUDUser.get_by_username(db, update_data["username"])
            if existing:
                raise ValidationError(f"Username '{update_data['username']}' already exists")
        
        if "email" in update_data and update_data["email"] != user.email:
            existing = await CRUDUser.get_by_email(db, update_data["email"])
            if existing:
                raise ValidationError(f"Email '{update_data['email']}' already exists")
        
        if "phone" in update_data and update_data["phone"] != user.phone:
            existing = await CRUDUser.get_by_phone(db, update_data["phone"])
            if existing:
                raise ValidationError(f"Phone number '{update_data['phone']}' already exists")
        
        # Update user
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def delete(db: AsyncSession, user_id: int) -> bool:
        """Delete user"""
        user = await CRUDUser.get_by_id(db, user_id)
        if not user:
            raise NotFoundError("User")
        
        await db.delete(user)
        await db.commit()
        return True
    
    @staticmethod
    async def get_all(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """Get all users with filters"""
        query = select(User)
        
        if role:
            query = query.where(User.role == role)
        
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_customers(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all customers"""
        return await CRUDUser.get_all(db, skip, limit, role=UserRole.CUSTOMER)
    
    @staticmethod
    async def get_team_members(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all team members"""
        return await CRUDUser.get_all(db, skip, limit, role=UserRole.TEAM_MEMBER)
    
    @staticmethod
    async def create_session(db: AsyncSession, user_id: int) -> UserSession:
        """Create user session on login"""
        session = UserSession(
            user_id=user_id,
            login_time=datetime.now(IST),
            date=date.today()
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session
    
    @staticmethod
    async def update_session(db: AsyncSession, session_id: int) -> UserSession:
        """Update user session on logout"""
        session = await db.get(UserSession, session_id)
        if session:
            session.logout_time = datetime.now(IST)
            await db.commit()
            await db.refresh(session)
        return session
    
    @staticmethod
    async def get_user_sessions(
        db: AsyncSession, 
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[UserSession]:
        """Get user sessions within date range"""
        query = select(UserSession).where(UserSession.user_id == user_id)
        
        if start_date:
            query = query.where(UserSession.date >= start_date)
        
        if end_date:
            query = query.where(UserSession.date <= end_date)
        
        query = query.order_by(UserSession.login_time.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_online_time_report(
        db: AsyncSession,
        user_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Get online time report for users"""
        query = select(
            User.id,
            User.username,
            User.name,
            User.role,
            func.count(UserSession.id).label("session_count"),
            func.sum(
                func.extract('epoch', UserSession.logout_time - UserSession.login_time) / 60
            ).label("total_minutes")
        ).join(UserSession, User.id == UserSession.user_id)
        
        if user_id:
            query = query.where(User.id == user_id)
        
        if start_date:
            query = query.where(UserSession.date >= start_date)
        
        if end_date:
            query = query.where(UserSession.date <= end_date)
        
        query = query.where(UserSession.logout_time.is_not(None))
        query = query.group_by(User.id)
        
        result = await db.execute(query)
        rows = result.all()
        
        return [
            {
                "user_id": row[0],
                "username": row[1],
                "name": row[2],
                "role": row[3].value,
                "session_count": row[4],
                "total_minutes": round(float(row[5] or 0), 2)
            }
            for row in rows
        ]
