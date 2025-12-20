"""
Admin router for Bite Me Buddy
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
import os
import shutil
import uuid
from pathlib import Path
import logging

from database import get_db
from models import User
from schemas import (
    UserCreate, UserResponse, TeamMemberPlanCreate, TeamMemberPlanResponse,
    UserOnlineStats
)
from crud import (
    create_user, get_all_users_online_stats, create_team_member_plan,
    get_plans_by_team_member, get_todays_plans
)
from routers.auth import require_role
from core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/dashboard-stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Get dashboard statistics (admin only)"""
    from sqlalchemy import func, select
    from models import User, Order, Service
    
    # Total users by role
    result = await db.execute(
        select(User.role, func.count(User.id))
        .group_by(User.role)
    )
    users_by_role = dict(result.all())
    
    # Total services
    result = await db.execute(select(func.count(Service.id)))
    total_services = result.scalar()
    
    # Total orders
    result = await db.execute(select(func.count(Order.id)))
    total_orders = result.scalar()
    
    # Recent orders (last 7 days)
    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    result = await db.execute(
        select(func.count(Order.id))
        .where(Order.created_at >= week_ago)
    )
    recent_orders = result.scalar()
    
    return {
        "users_by_role": users_by_role,
        "total_services": total_services,
        "total_orders": total_orders,
        "recent_orders": recent_orders,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/online-stats", response_model=List[UserOnlineStats])
async def get_all_users_online_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Get online statistics for all users (admin only)"""
    return await get_all_users_online_stats(db)

@router.post("/team-members")
async def create_team_member(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Create a new team member (admin only)"""
    # Set role to team_member
    user_create.role = "team_member"
    
    # Create user
    db_user = await create_user(db, user_create)
    logger.info(f"Team member created: {db_user.username} by {current_user.username}")
    return UserResponse.model_validate(db_user)

@router.post("/team-member-plans", response_model=TeamMemberPlanResponse)
async def create_team_member_plan_admin(
    plan: TeamMemberPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Create a team member plan (admin only)"""
    db_plan = await create_team_member_plan(db, plan, current_user.id)
    logger.info(f"Team member plan created for {plan.team_member_id} by {current_user.username}")
    return TeamMemberPlanResponse.model_validate(db_plan)

@router.post("/team-member-plans/{plan_id}/upload-image")
async def upload_plan_image(
    plan_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Upload plan image (admin only)"""
    # Check plan exists
    from crud import get_team_member_plan_by_id
    plan = await get_team_member_plan_by_id(db, plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    # Validate file
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Generate unique filename
    unique_filename = f"plan_{plan_id}_{uuid.uuid4().hex}{file_ext}"
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
    
    # Update plan with image URL
    plan.image_url = f"/static/uploads/{unique_filename}"
    await db.commit()
    await db.refresh(plan)
    
    logger.info(f"Plan image uploaded for plan {plan_id}")
    return {
        "filename": unique_filename,
        "url": plan.image_url,
        "message": "Image uploaded successfully"
    }

@router.get("/team-member-plans/{team_member_id}", response_model=List[TeamMemberPlanResponse])
async def get_team_member_plans_admin(
    team_member_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Get plans for a team member (admin only)"""
    plans = await get_plans_by_team_member(db, team_member_id, skip=skip, limit=limit)
    return [TeamMemberPlanResponse.model_validate(plan) for plan in plans]

@router.get("/team-member-plans/today/{team_member_id}", response_model=List[TeamMemberPlanResponse])
async def get_todays_plans_admin(
    team_member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Get today's plans for a team member (admin only)"""
    plans = await get_todays_plans(db, team_member_id)
    return [TeamMemberPlanResponse.model_validate(plan) for plan in plans]

# Additional helper function for CRUD
async def get_team_member_plan_by_id(db: AsyncSession, plan_id: int):
    """Get team member plan by ID"""
    from sqlalchemy import select
    from models import TeamMemberPlan
    
    result = await db.execute(
        select(TeamMemberPlan).where(TeamMemberPlan.id == plan_id)
    )
    return result.scalar_one_or_none()