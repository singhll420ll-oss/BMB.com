

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData

# Database URL - Render ke liye fix
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

# IMPORTANT: Render PostgreSQL URL fix
# postgres:// → postgresql+asyncpg://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

# For sync connections (Alembic/migrations)
SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "") if "+asyncpg" in DATABASE_URL else DATABASE_URL

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "False").lower() == "true",
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"ssl": "require"} if "postgresql" in DATABASE_URL else {}
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Base model class
Base = declarative_base()

# Naming convention for constraints
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)
Base.metadata = metadata

async def get_db() -> AsyncSession:
    """
    Dependency to get database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Sync engine for Alembic (migrations)
from sqlalchemy import create_engine as create_sync_engine
sync_engine = None

if "postgresql" in SYNC_DATABASE_URL:
    sync_engine = create_sync_engine(
        SYNC_DATABASE_URL,
        connect_args={"ssl": "require"}
    )
elif "sqlite" in SYNC_DATABASE_URL:
    sync_engine = create_sync_engine(
        SYNC_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )