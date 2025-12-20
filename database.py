"""
Database configuration for Render with PostgreSQL + asyncpg
"""

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import declarative_base
import logging

logger = logging.getLogger(__name__)

# ========== DATABASE URL CONFIGURATION ==========
def get_database_url():
    """Get and validate database URL"""
    # First check environment variable
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        logger.info("✅ DATABASE_URL found in environment")
        
        # Fix for Render's PostgreSQL URL
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            logger.info("✅ Fixed URL format for asyncpg")
        
        return database_url
    
    # Fallback for local development (PostgreSQL required)
    logger.warning("⚠️ DATABASE_URL not found, using local PostgreSQL")
    return "postgresql+asyncpg://postgres:password@localhost/bite_me_buddy"

# Get database URL
DATABASE_URL = get_database_url()

# Validate URL contains asyncpg
if "asyncpg" not in DATABASE_URL:
    logger.error("❌ Database URL must use asyncpg driver")
    logger.error(f"Current URL: {DATABASE_URL}")
    raise ValueError("Database URL must use postgresql+asyncpg:// protocol")

logger.info(f"Using database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")

# ========== CREATE ASYNC ENGINE ==========
try:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,  # Production: False, Development: True
        poolclass=NullPool,  # Required for Render
        pool_pre_ping=True,
        connect_args={
            "command_timeout": 60,
            "server_settings": {
                "application_name": "bite_me_buddy",
                "timezone": "UTC",
            }
        },
        # Future-proof settings
        future=True,
    )
    logger.info("✅ Async database engine created successfully")
    
except Exception as e:
    logger.error(f"❌ Failed to create async database engine: {e}")
    logger.error("Make sure:")
    logger.error("1. DATABASE_URL uses postgresql+asyncpg://")
    logger.error("2. PostgreSQL database is running")
    logger.error("3. asyncpg is installed (pip install asyncpg)")
    raise

# ========== SESSION CONFIGURATION ==========
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# ========== BASE MODEL ==========
Base = declarative_base()

# ========== HELPER FUNCTIONS ==========
async def get_db():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

async def test_connection():
    """Test database connection"""
    try:
        async with engine.begin() as conn:
            # Test with a simple query
            result = await conn.execute("SELECT version(), current_timestamp")
            row = result.first()
            if row:
                logger.info(f"✅ Database connected: {row[0]}")
                logger.info(f"📅 Server time: {row[1]}")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

async def create_tables():
    """Create all tables"""
    try:
        async with engine.begin() as conn:
            # Import models first
            import models
            await conn.run_sync(Base.metadata.create_all)
            
            # Count tables
            result = await conn.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            count = result.scalar()
            logger.info(f"✅ Created/verified {count} database tables")
            return True
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return False

async def get_database_info():
    """Get database information"""
    try:
        async with engine.connect() as conn:
            # Get database info
            result = await conn.execute("""
                SELECT 
                    current_database() as db_name,
                    current_user as db_user,
                    inet_server_addr() as host,
                    inet_server_port() as port,
                    version() as version
            """)
            info = result.first()
            return {
                "database": info[0],
                "user": info[1],
                "host": info[2],
                "port": info[3],
                "version": info[4]
            }
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return None

# ========== INITIALIZE ON IMPORT ==========
# This helps catch configuration errors early
logger.info("Database module loaded successfully")