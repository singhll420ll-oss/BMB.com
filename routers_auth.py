"""
Authentication router
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
import structlog

from database import get_db
from models.user import User
from schemas.auth import LoginRequest, Token, OTPVerifyRequest
from crud.user import CRUDUser
from core.security import create_access_token, verify_token
from core.config import settings
from core.exceptions import AuthenticationError

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = structlog.get_logger(__name__)

# Store sessions in memory (in production, use Redis)
user_sessions = {}

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, role: str = "customer"):
    """Render login page"""
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "role": role
    })

@router.get("/admin-login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Render admin login page (accessed via secret clock)"""
    return templates.TemplateResponse("auth/admin_login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Render registration page"""
    return templates.TemplateResponse("auth/register.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """User login"""
    try:
        # Authenticate user
        user = await CRUDUser.authenticate(
            db, login_data.username, login_data.password
        )
        
        if not user:
            raise AuthenticationError("Invalid username or password")
        
        # Check role if specified
        if login_data.role and user.role.value != login_data.role:
            raise AuthenticationError(f"User is not a {login_data.role}")
        
        # Check if user is active
        if not user.is_active:
            raise AuthenticationError("Account is deactivated")
        
        # Create session
        session = await CRUDUser.create_session(db, user.id)
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.username,
                "user_id": user.id,
                "role": user.role.value
            },
            expires_delta=access_token_expires
        )
        
        # Store session
        user_sessions[user.id] = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value,
            "session_id": session.id,
            "login_time": session.login_time
        }
        
        # Set cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=not settings.DEBUG,
            samesite="lax"
        )
        
        response.set_cookie(
            key="user_id",
            value=str(user.id),
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=not settings.DEBUG,
            samesite="lax"
        )
        
        # Redirect based on role
        if user.role.value == "customer":
            return RedirectResponse(url="/customer/dashboard", status_code=303)
        elif user.role.value == "team_member":
            return RedirectResponse(url="/team/dashboard", status_code=303)
        elif user.role.value == "admin":
            return RedirectResponse(url="/admin/dashboard", status_code=303)
        
    except AuthenticationError as e:
        logger.warning(f"Login failed: {str(e)}", username=login_data.username)
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": str(e),
            "role": login_data.role or "customer"
        })
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}", username=login_data.username)
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": "Internal server error",
            "role": login_data.role or "customer"
        })

@router.post("/register")
async def register(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """User registration"""
    try:
        form_data = await request.form()
        
        # Create user
        user_data = {
            "name": form_data.get("name"),
            "username": form_data.get("username"),
            "email": form_data.get("email"),
            "phone": form_data.get("phone"),
            "password": form_data.get("password"),
            "address": form_data.get("address"),
            "role": "customer"
        }
        
        # Validate and create user
        from schemas.user import CustomerCreate
        user_in = CustomerCreate(**user_data)
        user = await CRUDUser.create(db, user_in)
        
        # Auto-login after registration
        login_data = LoginRequest(
            username=user.username,
            password=form_data.get("password")
        )
        
        # Create response and call login
        response = Response()
        return await login(request, response, login_data, db)
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return templates.TemplateResponse("auth/register.html", {
            "request": request,
            "error": str(e)
        })

@router.get("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """User logout"""
    try:
        # Get token from cookie
        token = request.cookies.get("access_token")
        user_id = request.cookies.get("user_id")
        
        if token and user_id:
            # Verify token
            payload = verify_token(token)
            
            # Update session logout time
            if user_id in user_sessions:
                session_id = user_sessions[user_id]["session_id"]
                await CRUDUser.update_session(db, session_id)
                del user_sessions[user_id]
        
        # Clear cookies
        response.delete_cookie("access_token")
        response.delete_cookie("user_id")
        
        # Redirect to home
        return RedirectResponse(url="/", status_code=303)
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        # Still clear cookies and redirect
        response.delete_cookie("access_token")
        response.delete_cookie("user_id")
        return RedirectResponse(url="/", status_code=303)

@router.post("/verify-otp")
async def verify_otp(
    otp_data: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """Verify OTP for order delivery"""
    from crud.order import CRUDOrder
    
    try:
        success = await CRUDOrder.verify_otp(db, otp_data.order_id, otp_data.otp)
        
        if success:
            return {"success": True, "message": "OTP verified successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )