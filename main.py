"""
Bite Me Buddy - Main Application
"""

import os
from pathlib import Path
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    logger.info("🚀 Starting Bite Me Buddy application...")
    
    # Create uploads directory
    uploads_dir = Path("static/uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Uploads directory: {uploads_dir.absolute()}")
    
    # Test database connection
    try:
        from database import test_connection
        if await test_connection():
            logger.info("✅ Database connection successful")
        else:
            logger.warning("⚠️ Database connection test failed")
    except Exception as e:
        logger.error(f"❌ Database setup error: {e}")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down Bite Me Buddy application")

# Create FastAPI app
app = FastAPI(
    title="Bite Me Buddy",
    description="Food Ordering System",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Health check endpoint (required by Render)
@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {
        "status": "healthy",
        "service": "Bite Me Buddy",
        "database": os.getenv("DATABASE_URL", "not_set")[:20] + "..." if os.getenv("DATABASE_URL") else "not_set"
    }

@app.get("/")
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/test")
async def test_page(request: Request):
    """Test page to verify templates are working"""
    return templates.TemplateResponse("test.html", {"request": request})

# Simple database test endpoint
@app.get("/api/test-db")
async def test_db_connection():
    """Test database connection API endpoint"""
    try:
        from database import test_connection
        success = await test_connection()
        return {
            "success": success,
            "message": "Database connected successfully" if success else "Database connection failed",
            "database_url_set": bool(os.getenv("DATABASE_URL"))
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "database_url_set": bool(os.getenv("DATABASE_URL"))
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )