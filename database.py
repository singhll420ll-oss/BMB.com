import os
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData, create_engine as create_sync_engine

# --------------------------------------------------
# DATABASE URL
# --------------------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./test.db"
)

# Render PostgreSQL fix
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql+asyncpg://",
        1
    )

# --------------------------------------------------
# METADATA (Best practice)
# --------------------------------------------------

metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

Base = declarative_base(metadata=metadata)

# --------------------------------------------------
# ASYNC ENGINE
# --------------------------------------------------

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "false").lower() == "true",
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=(
        {"ssl": "require"} if DATABASE_URL.startswith("postgresql")
        else {"check_same_thread": False}
    )
)

# --------------------------------------------------
# ASYNC SESSION
# --------------------------------------------------

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# --------------------------------------------------
# DEPENDENCY
# --------------------------------------------------

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# --------------------------------------------------
# SYNC ENGINE (Alembic / migrations)
# --------------------------------------------------

if DATABASE_URL.startswith("postgresql+asyncpg"):
    SYNC_DATABASE_URL = DATABASE_URL.replace(
        "postgresql+asyncpg",
        "postgresql",
        1
    )
elif DATABASE_URL.startswith("sqlite+aiosqlite"):
    SYNC_DATABASE_URL = DATABASE_URL.replace(
        "sqlite+aiosqlite",
        "sqlite",
        1
    )
else:
    SYNC_DATABASE_URL = DATABASE_URL

sync_engine = create_sync_engine(
    SYNC_DATABASE_URL,
    connect_args=(
        {"ssl": "require"} if SYNC_DATABASE_URL.startswith("postgresql")
        else {"check_same_thread": False}
    )
)