"""
Authentication router for Bite Me Buddy
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from database import get_db
from models import User
from schemas import UserCreate, UserLogin, UserResponse
from crud import create_user, get_user_by_username, create_user_session, update_user_session_logout
from core.security import verify_password, create_access_token, verify_token, get_password_hash
from core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)
security = HTTPBearer()

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user from token"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = await get_user_by_username(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Store user in request state
    request.state.user = user
    return user

async def require_role(role: str):
    """Dependency to require specific role"""
    async def role_checker(user: User = Depends(get_current_user)):
        if user.role != role and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {role}"
            )
        return user
    return role_checker

@router.post("/register", response_model=UserResponse)
async def register(
    user: UserCreate,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    # Check if username exists
    existing_user = await get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    if user.email:
        existing_email = await get_user_by_email(db, user.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Check if phone exists
    if user.phone:
        existing_phone = await get_user_by_phone(db, user.phone)
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
    
    # Create user
    db_user = await create_user(db, user)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username},
        expires_delta=access_token_expires
    )
    
    # Create user session
    await create_user_session(db, db_user.id)
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=not settings.DEBUG,
        samesite="lax"
    )
    
    logger.info(f"User registered: {db_user.username}")
    return db_user

@router.post("/login")
async def login(
    user_login: UserLogin,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Login user"""
    # Get user
    user = await get_user_by_username(db, user_login.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # Create user session
    session = await create_user_session(db, user.id)
    request.state.session_id = session.id
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=not settings.DEBUG,
        samesite="lax"
    )
    
    logger.info(f"User logged in: {user.username}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Logout user"""
    # Update session logout time
    if hasattr(request.state, "session_id"):
        await update_user_session_logout(db, request.state.session_id)
    
    # Clear cookie
    response.delete_cookie("access_token")
    
    logger.info(f"User logged out: {user.username}")
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(get_current_user)
):
    """Get current user information"""
    return user

@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    # Verify old password
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid old password"
        )
    
    # Update password
    user.hashed_password = get_password_hash(new_password)
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"Password changed for user: {user.username}")
    return {"message": "Password changed successfully"}
