"""
Bite Me Buddy - Food Ordering System
Main FastAPI Application
"""

import os
from pathlib import Path
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from core.config import settings
from core.logging import setup_logging
from database import engine
from routers import auth, users, services, orders, admin
from models import Base

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    logger.info("Starting Bite Me Buddy application")
    
    # Create uploads directory if it doesn't exist
    uploads_dir = Path("static/uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    # Create tables if they don't exist (for Render deployment)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Bite Me Buddy application")

# Create FastAPI app
app = FastAPI(
    title="Bite Me Buddy",
    description="Food Ordering System",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(services.router, prefix="/api/services", tags=["services"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/")
async def home(request: Request):
    """Home page with secret admin access via clock"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/admin-login")
async def admin_login_page(request: Request):
    """Admin login page (accessed via secret clock combination)"""
    return templates.TemplateResponse("admin_login.html", {"request": request})

# Custom exception handlers
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    return templates.TemplateResponse(
        "404.html", 
        {"request": request}, 
        status_code=404
    )

@app.exception_handler(500)
async def server_error_exception_handler(request: Request, exc):
    logger.error(f"Server error: {exc}")
    return templates.TemplateResponse(
        "500.html", 
        {"request": request}, 
        status_code=500
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=settings.DEBUG
    )