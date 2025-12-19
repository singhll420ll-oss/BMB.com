"""
CRUD operations for MenuItem model
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload

from models.menu_item import MenuItem
from models.service import Service
from schemas.menu_item import MenuItemCreate, MenuItemUpdate
from core.exceptions import NotFoundError, ValidationError

class CRUDMenuItem:
    """CRUD operations for MenuItem model"""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, menu_item_id: int) -> Optional[MenuItem]:
        """Get menu item by ID"""
        result = await db.execute(
            select(MenuItem).where(MenuItem.id == menu_item_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_name_and_service(db: AsyncSession, name: str, service_id: int) -> Optional[MenuItem]:
        """Get menu item by name and service"""
        result = await db.execute(
            select(MenuItem).where(
                and_(
                    MenuItem.name == name,
                    MenuItem.service_id == service_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, menu_item_in: MenuItemCreate) -> MenuItem:
        """Create new menu item"""
        # Check if service exists
        service = await db.get(Service, menu_item_in.service_id)
        if not service:
            raise NotFoundError("Service")
        
        # Check if menu item name exists in same service
        existing = await CRUDMenuItem.get_by_name_and_service(
            db, menu_item_in.name, menu_item_in.service_id
        )
        if existing:
            raise ValidationError(f"Menu item '{menu_item_in.name}' already exists in this service")
        
        menu_item = MenuItem(**menu_item_in.model_dump())
        db.add(menu_item)
        await db.commit()
        await db.refresh(menu_item)
        return menu_item
    
    @staticmethod
    async def update(db: AsyncSession, menu_item_id: int, menu_item_in: MenuItemUpdate) -> Optional[MenuItem]:
        """Update menu item"""
        menu_item = await CRUDMenuItem.get_by_id(db, menu_item_id)
        if not menu_item:
            raise NotFoundError("Menu item")
        
        update_data = menu_item_in.model_dump(exclude_unset=True)
        
        # Check name uniqueness if name is being updated
        if "name" in update_data and update_data["name"] != menu_item.name:
            existing = await CRUDMenuItem.get_by_name_and_service(
                db, update_data["name"], menu_item.service_id
            )
            if existing:
                raise ValidationError(f"Menu item '{update_data['name']}' already exists in this service")
        
        # Update menu item
        for field, value in update_data.items():
            setattr(menu_item, field, value)
        
        await db.commit()
        await db.refresh(menu_item)
        return menu_item
    
    @staticmethod
    async def delete(db: AsyncSession, menu_item_id: int) -> bool:
        """Delete menu item"""
        menu_item = await CRUDMenuItem.get_by_id(db, menu_item_id)
        if not menu_item:
            raise NotFoundError("Menu item")
        
        await db.delete(menu_item)
        await db.commit()
        return True
    
    @staticmethod
    async def get_by_service(db: AsyncSession, service_id: int, available_only: bool = True) -> List[MenuItem]:
        """Get menu items by service"""
        query = select(MenuItem).where(MenuItem.service_id == service_id)
        
        if available_only:
            query = query.where(MenuItem.is_available == True)
        
        query = query.order_by(MenuItem.name)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[MenuItem]:
        """Get all menu items"""
        result = await db.execute(
            select(MenuItem)
            .offset(skip)
            .limit(limit)
            .order_by(MenuItem.service_id, MenuItem.name)
        )
        return result.scalars().all()
    
    @staticmethod
    async def toggle_availability(db: AsyncSession, menu_item_id: int) -> Optional[MenuItem]:
        """Toggle menu item availability"""
        menu_item = await CRUDMenuItem.get_by_id(db, menu_item_id)
        if not menu_item:
            raise NotFoundError("Menu item")
        
        menu_item.is_available = not menu_item.is_available
        await db.commit()
        await db.refresh(menu_item)
        return menu_item
