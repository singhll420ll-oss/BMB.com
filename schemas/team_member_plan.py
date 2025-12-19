"""
Pydantic schemas for TeamMemberPlan model
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TeamMemberPlanBase(BaseModel):
    """Base team member plan schema"""
    description: str = Field(..., min_length=1)
    
    class Config:
        from_attributes = True

class TeamMemberPlanCreate(TeamMemberPlanBase):
    """Schema for creating a team member plan"""
    team_member_ids: List[int] = Field(..., min_items=1)
    image_url: Optional[str] = None

class TeamMemberPlanResponse(TeamMemberPlanBase):
    """Schema for team member plan response"""
    id: int
    admin_id: int
    team_member_id: int
    image_url: Optional[str]
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
