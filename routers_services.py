"""
Services router for service-related endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import structlog

from database import get_db
from models.service import Service
from crud.service import CRUDService
from crud.menu_item import CRUDMenuItem

router = APIRouter()
logger = structlog.get_logger(__name__)

@router.get("/", response_class=HTMLResponse)
async def get_all_services(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get all services (API endpoint)"""
    try:
        services = await CRUDService.get_all(db)
        
        # Return as JSON for HTMX
        service_list = []
        for service in services:
            service_list.append({
                "id": service.id,
                "name": service.name,
                "description": service.description,
                "image_url": service.image_url
            })
        
        return JSONResponse(content=service_list)
        
    except Exception as e:
        logger.error(f"Error getting services: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving services"
        )

@router.get("/{service_id}/menu")
async def get_service_menu(
    service_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get menu for a specific service"""
    try:
        # Get service
        service = await CRUDService.get_by_id(db, service_id)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        
        # Get menu items
        menu_items = await CRUDMenuItem.get_by_service(db, service_id)
        
        # Format response
        menu_list = []
        for item in menu_items:
            menu_list.append({
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "price": item.price,
                "image_url": item.image_url,
                "is_available": item.is_available
            })
        
        return {
            "service": {
                "id": service.id,
                "name": service.name,
                "description": service.description,
                "image_url": service.image_url
            },
            "menu_items": menu_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service menu: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving service menu"
        )

@router.get("/{service_id}/details")
async def get_service_details(
    service_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get service details"""
    try:
        service = await CRUDService.get_by_id(db, service_id, with_menu=True)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        
        # Format menu items
        menu_items = []
        for item in service.menu_items:
            if item.is_available:  # Only show available items
                menu_items.append({
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "price": item.price,
                    "image_url": item.image_url
                })
        
        return {
            "id": service.id,
            "name": service.name,
            "description": service.description,
            "image_url": service.image_url,
            "menu_items": menu_items
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving service details"
        )