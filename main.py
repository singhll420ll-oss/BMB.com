"""
Bite Me Buddy - Main Application
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import asyncio

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # ========== STARTUP ==========
    logger.info("=" * 50)
    logger.info("🚀 Starting Bite Me Buddy Application")
    logger.info("=" * 50)
    
    # Check environment
    logger.info(f"Environment: {'PRODUCTION' if not os.getenv('DEBUG') else 'DEVELOPMENT'}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Create directories
    directories = [
        "static/uploads",
        "static/css", 
        "static/js",
        "templates"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Directory ready: {directory}")
    
    # Initialize database
    try:
        logger.info("🔌 Initializing database connection...")
        from database import test_connection, create_tables, get_database_info
        
        # Test connection
        if await test_connection():
            logger.info("✅ Database connection successful")
            
            # Get database info
            db_info = await get_database_info()
            if db_info:
                logger.info(f"📊 Database: {db_info['database']}")
                logger.info(f"👤 User: {db_info['user']}")
                logger.info(f"🌐 Host: {db_info['host']}:{db_info['port']}")
                logger.info(f"🔧 Version: {db_info['version'][:50]}...")
            
            # Create tables
            logger.info("🛠️ Creating database tables...")
            if await create_tables():
                logger.info("✅ Database tables ready")
            else:
                logger.warning("⚠️ Table creation had issues")
        else:
            logger.error("❌ Database connection failed")
            
    except ImportError as e:
        logger.error(f"❌ Could not import database module: {e}")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")
    
    logger.info("✅ Application startup complete")
    logger.info("=" * 50)
    
    yield
    
    # ========== SHUTDOWN ==========
    logger.info("👋 Shutting down application...")

# Create FastAPI app
app = FastAPI(
    title="Bite Me Buddy",
    description="Food Ordering System",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("DEBUG") == "True" else None,
    redoc_url="/redoc" if os.getenv("DEBUG") == "True" else None,
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
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("✅ Static files mounted")
else:
    logger.warning("⚠️ Static directory not found")

# Setup templates
templates_dir = Path("templates")
if templates_dir.exists():
    templates = Jinja2Templates(directory="templates")
    logger.info("✅ Templates loaded")
else:
    logger.warning("⚠️ Templates directory not found")
    templates = None

# ========== ROUTES ==========

@app.get("/")
async def home(request: Request):
    """Home page"""
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    return JSONResponse(content={"message": "Welcome to Bite Me Buddy", "status": "running"})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from database import test_connection
    
    db_status = "unknown"
    try:
        db_status = "connected" if await test_connection() else "disconnected"
    except:
        db_status = "error"
    
    return {
        "status": "healthy",
        "service": "Bite Me Buddy",
        "version": "2.0.0",
        "database": db_status,
        "timestamp": asyncio.get_event_loop().time()
    }

@app.get("/api/db-info")
async def db_info():
    """Database information endpoint"""
    try:
        from database import get_database_info
        info = await get_database_info()
        if info:
            return {
                "success": True,
                "data": info
            }
        return {
            "success": False,
            "error": "Could not get database info"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/test")
async def api_test():
    """Test API endpoint"""
    return {
        "message": "Bite Me Buddy API is working",
        "status": "success",
        "debug": os.getenv("DEBUG", "False")
    }

@app.get("/test-db")
async def test_db_page(request: Request):
    """Database test page"""
    if templates:
        return templates.TemplateResponse("test_db.html", {"request": request})
    return JSONResponse(content={"message": "Test page not available"})

# ========== ERROR HANDLERS ==========

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    if templates and Path("templates/404.html").exists():
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "message": "The requested resource was not found"}
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    logger.error(f"Server error: {exc}")
    if templates and Path("templates/500.html").exists():
        return templates.TemplateResponse("500.html", {"request": request}, status_code=500)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "Something went wrong"}
    )

# ========== APPLICATION ENTRY ==========

if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    logger.info(f"🌐 Starting server on {host}:{port}")
    logger.info(f"🔧 Debug mode: {debug}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        access_log=True,
        timeout_keep_alive=30,
        log_level="info" if debug else "warning",
        workers=1
    )