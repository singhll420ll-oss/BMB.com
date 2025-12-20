"""
Bite Me Buddy - Main FastAPI Application
Production-ready food ordering system
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog

from core.config import settings
from core.logging import setup_logging
from database import engine, Base
from routers import auth, customer, admin, team_member, services, orders
from core.exceptions import add_exception_handlers

# --------------------------------------------------
# LOGGING
# --------------------------------------------------

setup_logging()
logger = structlog.get_logger(__name__)

# --------------------------------------------------
# LIFESPAN (Startup / Shutdown)
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # -------- STARTUP --------
    logger.info(
        "Starting Bite Me Buddy application",
        env=settings.ENVIRONMENT,
        debug=settings.DEBUG
    )

    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # 🔥 CREATE DATABASE TABLES (ASYNC SAFE)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # -------- SHUTDOWN --------
    logger.info("Shutting down Bite Me Buddy application")
    await engine.dispose()

# --------------------------------------------------
# FASTAPI APP
# --------------------------------------------------

app = FastAPI(
    title="Bite Me Buddy",
    description="Professional Food Ordering System",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# --------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------

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

# --------------------------------------------------
# EXCEPTION HANDLERS
# --------------------------------------------------

add_exception_handlers(app)

# --------------------------------------------------
# TEMPLATES & STATIC
# --------------------------------------------------

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.state.templates = templates

# --------------------------------------------------
# ROUTERS
# --------------------------------------------------

app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(customer.router, prefix="/api/customer", tags=["customer"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(team_member.router, prefix="/api/team", tags=["team"])
app.include_router(services.router, prefix="/api/services", tags=["services"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])

# --------------------------------------------------
# ROUTES
# --------------------------------------------------

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Bite Me Buddy",
        "version": "1.0.0"
    }

# --------------------------------------------------
# LOCAL RUN
# --------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None
    )