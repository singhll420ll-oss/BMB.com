"""
Bite Me Buddy - Minimal Version
"""
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

# Database
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Config
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/bitebuddy")
Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Bite Me Buddy Starting...")
    os.makedirs("static/uploads", exist_ok=True)
    yield
    # Shutdown
    print("🛑 Shutting down...")
    await engine.dispose()

# Create app
app = FastAPI(lifespan=lifespan, title="Bite Me Buddy")

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    return {"status": "ok", "service": "Bite Me Buddy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
# ... your existing code (imports and engine setup) ...

# --- Add Custom Exception Handlers ---
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handles explicitly raised HTTPExceptions (like 404 errors)."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles request validation errors (like invalid data types)."""
    # Format validation errors for a cleaner response
    errors = exc.errors()
    simplified_errors = []
    for error in errors:
        # Extract field location and error message
        field = " -> ".join([str(loc) for loc in error.get("loc", [])])
        msg = error.get("msg")
        simplified_errors.append(f"Field '{field}': {msg}")
    return JSONResponse(
        status_code=422,  # Unprocessable Entity
        content={"detail": "Validation failed", "errors": simplified_errors}
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Catches any other unhandled exceptions to prevent server crash."""
    # In a real app, you should log 'exc' here for debugging
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."}
    )

# --- Create the FastAPI app ---
# Now create your app and link the handlers
app = FastAPI(
    lifespan=lifespan,
    title="Bite Me Buddy",
    exception_handlers={
        HTTPException: http_exception_handler,
        RequestValidationError: validation_exception_handler,
        Exception: general_exception_handler  # Broad catch-all
    }
)