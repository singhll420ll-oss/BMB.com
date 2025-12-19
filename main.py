
"""
Bite Me Buddy - Main FastAPI Application
Production-ready food ordering system
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog

from core.config import settings
from core.logging import setup_logging
from .database import engine, Base
from routers import auth, customer, admin, team_member, services, orders
from core.exceptions import add_exception_handlers

# Setup structured logging
setup_logging()
logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Bite Me Buddy application", 
                env=settings.ENVIRONMENT, debug=settings.DEBUG)
    
    # Create upload directory if not exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Bite Me Buddy application")
    await engine.dispose()

# Create FastAPI app
app = FastAPI(
    title="Bite Me Buddy",
    description="Professional Food Ordering System",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Add exception handlers
add_exception_handlers(app)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(customer.router, prefix="/api/customer", tags=["customer"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(team_member.router, prefix="/api/team", tags=["team"])
app.include_router(services.router, prefix="/api/services", tags=["services"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])

# Store templates in app state
app.state.templates = templates

@app.get("/")
async def home(request: Request):
    """Home page with secret clock"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Bite Me Buddy",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None
    )