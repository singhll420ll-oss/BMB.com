import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData, create_engine

# --------------------------------------------------
# DATABASE URL
# --------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

# fallback for local
if not DATABASE_URL:
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# PostgreSQL async fix
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

# --------------------------------------------------
# METADATA
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
# ASYNC ENGINE (FastAPI)
# --------------------------------------------------

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# --------------------------------------------------
# ASYNC SESSION
# --------------------------------------------------

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# --------------------------------------------------
# SYNC ENGINE (Alembic only)
# --------------------------------------------------

if DATABASE_URL.startswith("postgresql+asyncpg"):
    SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg", "postgresql", 1)
elif DATABASE_URL.startswith("sqlite+aiosqlite"):
    SYNC_DATABASE_URL = DATABASE_URL.replace("sqlite+aiosqlite", "sqlite", 1)
else:
    SYNC_DATABASE_URL = DATABASE_URL

sync_engine = create_engine(SYNC_DATABASE_URL)