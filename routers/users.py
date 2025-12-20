"""
Users router for Bite Me Buddy
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from database import get_db
from models import User
from schemas import UserResponse, UserUpdate, UserWithSessions
from crud import (
    get_user_by_id, update_user, delete_user, get_all_users,
    get_users_by_role, get_user_sessions, get_user_online_stats
)
from routers.auth import get_current_user, require_role

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    role: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Get all users (admin only)"""
    if role:
        return await get_users_by_role(db, role, skip=skip, limit=limit)
    return await get_all_users(db, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=UserWithSessions)
async def read_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Get user by ID with sessions (admin only)"""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user sessions
    sessions = await get_user_sessions(db, user_id)
    
    # Create response
    user_data = UserResponse.model_validate(user)
    sessions_data = [UserSessionResponse.model_validate(s) for s in sessions]
    
    return UserWithSessions(
        **user_data.model_dump(),
        sessions=sessions_data
    )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user_info(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user information"""
    # Only admin or the user themselves can update
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    user = await update_user(db, user_id, user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"User updated: {user.username}")
    return user

@router.delete("/{user_id}")
async def delete_user_account(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Delete user (admin only)"""
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"User deleted: {user_id}")
    return {"message": "User deleted successfully"}

@router.get("/{user_id}/online-stats")
async def get_user_online_statistics(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Get user online statistics (admin only)"""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    stats = await get_user_online_stats(db, user_id)
    return {
        "user_id": user_id,
        "user_name": user.name,
        "role": user.role,
        **stats
    }

@router.get("/team-members/all", response_model=List[UserResponse])
async def get_all_team_members(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all team members"""
    return await get_users_by_role(db, "team_member", skip=skip, limit=limit)

@router.get("/customers/all", response_model=List[UserResponse])
async def get_all_customers(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Get all customers (admin only)"""
    return await get_users_by_role(db, "customer", skip=skip, limit=limit)
