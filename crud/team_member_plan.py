"""
CRUD operations for TeamMemberPlan model
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload

from models.team_member_plan import TeamMemberPlan
from models.user import User
from schemas.team_member_plan import TeamMemberPlanCreate
from core.exceptions import NotFoundError, ValidationError

class CRUDTeamMemberPlan:
    """CRUD operations for TeamMemberPlan model"""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, plan_id: int) -> Optional[TeamMemberPlan]:
        """Get plan by ID"""
        result = await db.execute(
            select(TeamMemberPlan).where(TeamMemberPlan.id == plan_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(
        db: AsyncSession, 
        plan_in: TeamMemberPlanCreate, 
        admin_id: int
    ) -> List[TeamMemberPlan]:
        """Create new plans for team members"""
        created_plans = []
        
        for team_member_id in plan_in.team_member_ids:
            # Check if team member exists and is a team member
            team_member = await db.get(User, team_member_id)
            if not team_member or team_member.role != "team_member":
                raise ValidationError(f"Invalid team member ID: {team_member_id}")
            
            plan_data = plan_in.model_dump(exclude={"team_member_ids"})
            plan = TeamMemberPlan(
                **plan_data,
                admin_id=admin_id,
                team_member_id=team_member_id
            )
            db.add(plan)
            created_plans.append(plan)
        
        await db.commit()
        
        # Refresh all created plans
        for plan in created_plans:
            await db.refresh(plan)
        
        return created_plans
    
    @staticmethod
    async def delete(db: AsyncSession, plan_id: int) -> bool:
        """Delete plan"""
        plan = await CRUDTeamMemberPlan.get_by_id(db, plan_id)
        if not plan:
            raise NotFoundError("Plan")
        
        await db.delete(plan)
        await db.commit()
        return True
    
    @staticmethod
    async def get_team_member_plans(db: AsyncSession, team_member_id: int) -> List[TeamMemberPlan]:
        """Get plans for a team member"""
        result = await db.execute(
            select(TeamMemberPlan)
            .where(TeamMemberPlan.team_member_id == team_member_id)
            .options(selectinload(TeamMemberPlan.admin))
            .order_by(TeamMemberPlan.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def mark_as_read(db: AsyncSession, plan_id: int, team_member_id: int) -> Optional[TeamMemberPlan]:
        """Mark plan as read by team member"""
        result = await db.execute(
            select(TeamMemberPlan).where(
                and_(
                    TeamMemberPlan.id == plan_id,
                    TeamMemberPlan.team_member_id == team_member_id
                )
            )
        )
        plan = result.scalar_one_or_none()
        
        if plan:
            plan.is_read = True
            await db.commit()
            await db.refresh(plan)
        
        return plan
    
    @staticmethod
    async def get_all_plans(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[TeamMemberPlan]:
        """Get all plans"""
        result = await db.execute(
            select(TeamMemberPlan)
            .options(
                selectinload(TeamMemberPlan.admin),
                selectinload(TeamMemberPlan.team_member)
            )
            .order_by(TeamMemberPlan.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
