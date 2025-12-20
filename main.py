"""
Bite Me Buddy - Main Application
Production-ready food ordering system with secret admin access
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import structlog

# Import configurations
from core.config import settings
from core.exceptions import setup_exception_handlers
from database import engine
from routers import auth, admin, customer, team_member, public

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False,
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the application"""
    # Startup
    logger.info("Starting Bite Me Buddy application")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Create uploads directory if it doesn't exist
    os.makedirs("static/uploads", exist_ok=True)
    os.makedirs("static/uploads/services", exist_ok=True)
    os.makedirs("static/uploads/menu", exist_ok=True)
    os.makedirs("static/uploads/plans", exist_ok=True)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Bite Me Buddy application")
    await engine.dispose()

# Create FastAPI app
app = FastAPI(
    title="Bite Me Buddy",
    description="Professional Food Ordering System with Secret Admin Access",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# Setup exception handlers
setup_exception_handlers(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(public.router)
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(customer.router, prefix="/customer", tags=["Customer"])
app.include_router(team_member.router, prefix="/team", tags=["Team Member"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Home page with secret clock access"""
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "app_name": "Bite Me Buddy"}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for deployment"""
    return {
        "status": "healthy",
        "service": "Bite Me Buddy",
        "version": "1.0.0"
    }

# Favicon endpoint
@app.get("/favicon.ico")
async def favicon():
    return {"message": "No favicon"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )