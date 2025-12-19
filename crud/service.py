"""
CRUD operations for Service model
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from models.service import Service
from models.menu_item import MenuItem
from schemas.service import ServiceCreate, ServiceUpdate
from core.exceptions import NotFoundError, ValidationError

class CRUDService:
    """CRUD operations for Service model"""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, service_id: int, with_menu: bool = False) -> Optional[Service]:
        """Get service by ID"""
        query = select(Service).where(Service.id == service_id)
        
        if with_menu:
            query = query.options(selectinload(Service.menu_items))
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Optional[Service]:
        """Get service by name"""
        result = await db.execute(
            select(Service).where(Service.name == name)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, service_in: ServiceCreate) -> Service:
        """Create new service"""
        # Check if service name exists
        existing = await CRUDService.get_by_name(db, service_in.name)
        if existing:
            raise ValidationError(f"Service '{service_in.name}' already exists")
        
        service = Service(**service_in.model_dump())
        db.add(service)
        await db.commit()
        await db.refresh(service)
        return service
    
    @staticmethod
    async def update(db: AsyncSession, service_id: int, service_in: ServiceUpdate) -> Optional[Service]:
        """Update service"""
        service = await CRUDService.get_by_id(db, service_id)
        if not service:
            raise NotFoundError("Service")
        
        update_data = service_in.model_dump(exclude_unset=True)
        
        # Check name uniqueness if name is being updated
        if "name" in update_data and update_data["name"] != service.name:
            existing = await CRUDService.get_by_name(db, update_data["name"])
            if existing:
                raise ValidationError(f"Service '{update_data['name']}' already exists")
        
        # Update service
        for field, value in update_data.items():
            setattr(service, field, value)
        
        await db.commit()
        await db.refresh(service)
        return service
    
    @staticmethod
    async def delete(db: AsyncSession, service_id: int) -> bool:
        """Delete service"""
        service = await CRUDService.get_by_id(db, service_id)
        if not service:
            raise NotFoundError("Service")
        
        await db.delete(service)
        await db.commit()
        return True
    
    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Service]:
        """Get all services"""
        result = await db.execute(
            select(Service)
            .offset(skip)
            .limit(limit)
            .order_by(Service.name)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_services_with_menu(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Service]:
        """Get all services with their menu items"""
        result = await db.execute(
            select(Service)
            .options(selectinload(Service.menu_items))
            .offset(skip)
            .limit(limit)
            .order_by(Service.name)
        )
        return result.scalars().all()
