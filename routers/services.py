"""
Services router for Bite Me Buddy
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
import os
import shutil
import uuid
from pathlib import Path
import logging

from database import get_db
from models import User
from schemas import ServiceCreate, ServiceUpdate, ServiceResponse, MenuItemCreate, MenuItemUpdate, MenuItemResponse
from crud import (
    create_service, get_service_by_id, get_all_services, update_service, delete_service,
    create_menu_item, get_menu_items_by_service, get_menu_item_by_id, update_menu_item, delete_menu_item
)
from routers.auth import get_current_user, require_role
from core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Service endpoints
@router.get("/", response_model=List[ServiceResponse])
async def read_services(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all services"""
    return await get_all_services(db, skip=skip, limit=limit)

@router.get("/{service_id}", response_model=ServiceResponse)
async def read_service(
    service_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get service by ID"""
    service = await get_service_by_id(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    return service

@router.post("/", response_model=ServiceResponse)
async def create_new_service(
    service: ServiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Create a new service (admin only)"""
    db_service = await create_service(db, service)
    logger.info(f"Service created: {db_service.name} by {current_user.username}")
    return db_service

@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service_info(
    service_id: int,
    service_update: ServiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Update service (admin only)"""
    service = await update_service(db, service_id, service_update)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    logger.info(f"Service updated: {service.name} by {current_user.username}")
    return service

@router.delete("/{service_id}")
async def delete_service_info(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Delete service (admin only)"""
    success = await delete_service(db, service_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    logger.info(f"Service deleted: {service_id} by {current_user.username}")
    return {"message": "Service deleted successfully"}

@router.post("/{service_id}/upload-image")
async def upload_service_image(
    service_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Upload service image (admin only)"""
    # Check service exists
    service = await get_service_by_id(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Validate file
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Generate unique filename
    unique_filename = f"service_{service_id}_{uuid.uuid4().hex}{file_ext}"
    upload_path = Path(settings.UPLOAD_DIR) / unique_filename
    
    # Save file
    try:
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error saving file"
        )
    
    # Update service with image URL
    service.image_url = f"/static/uploads/{unique_filename}"
    await db.commit()
    await db.refresh(service)
    
    logger.info(f"Service image uploaded: {service.name}")
    return {
        "filename": unique_filename,
        "url": service.image_url,
        "message": "Image uploaded successfully"
    }

# Menu Item endpoints
@router.get("/{service_id}/menu-items", response_model=List[MenuItemResponse])
async def read_service_menu_items(
    service_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all menu items for a service"""
    return await get_menu_items_by_service(db, service_id)

@router.post("/{service_id}/menu-items", response_model=MenuItemResponse)
async def create_service_menu_item(
    service_id: int,
    menu_item: MenuItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Create a new menu item for a service (admin only)"""
    # Verify service exists
    service = await get_service_by_id(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Set service_id
    menu_item_data = menu_item.model_dump()
    menu_item_data["service_id"] = service_id
    
    db_menu_item = await create_menu_item(db, MenuItemCreate(**menu_item_data))
    logger.info(f"Menu item created: {db_menu_item.name} for service {service.name}")
    return db_menu_item

@router.put("/menu-items/{menu_item_id}", response_model=MenuItemResponse)
async def update_menu_item_info(
    menu_item_id: int,
    menu_item_update: MenuItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Update menu item (admin only)"""
    menu_item = await update_menu_item(db, menu_item_id, menu_item_update)
    if not menu_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )
    logger.info(f"Menu item updated: {menu_item.name}")
    return menu_item

@router.delete("/menu-items/{menu_item_id}")
async def delete_menu_item_info(
    menu_item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Delete menu item (admin only)"""
    success = await delete_menu_item(db, menu_item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )
    logger.info(f"Menu item deleted: {menu_item_id}")
    return {"message": "Menu item deleted successfully"}

@router.post("/menu-items/{menu_item_id}/upload-image")
async def upload_menu_item_image(
    menu_item_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Upload menu item image (admin only)"""
    # Check menu item exists
    menu_item = await get_menu_item_by_id(db, menu_item_id)
    if not menu_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )
    
    # Validate file
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Generate unique filename
    unique_filename = f"menu_{menu_item_id}_{uuid.uuid4().hex}{file_ext}"
    upload_path = Path(settings.UPLOAD_DIR) / unique_filename
    
    # Save file
    try:
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error saving file"
        )
    
    # Update menu item with image URL
    menu_item.image_url = f"/static/uploads/{unique_filename}"
    await db.commit()
    await db.refresh(menu_item)
    
    logger.info(f"Menu item image uploaded: {menu_item.name}")
    return {
        "filename": unique_filename,
        "url": menu_item.image_url,
        "message": "Image uploaded successfully"
    }