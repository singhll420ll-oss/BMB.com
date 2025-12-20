# database.py
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import logging

logger = logging.getLogger(__name__)

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# If DATABASE_URL is not set, use a default for local development
if not DATABASE_URL:
    logger.warning("DATABASE_URL not found in environment variables")
    # For Render, this should never happen if database is linked
    DATABASE_URL = "postgresql+asyncpg://user:password@localhost/bite_me_buddy"

# Fix the URL format for asyncpg
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

logger.info(f"Database URL: {DATABASE_URL.split('@')[0]}@***")

# Create async engine
try:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        poolclass=NullPool,
        pool_pre_ping=True,
        connect_args={
            "command_timeout": 30,
            "keepalives_idle": 30,
        }
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def test_connection():
    """Test database connection"""
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False