"""
Database configuration for Neon PostgreSQL
Handles async connection pooling and session management
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine
)
from sqlalchemy.pool import NullPool
from .models import Base

# Global engine instance
_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_database_url() -> str:
    """
    Get database URL from environment variables

    Supports:
    - DATABASE_URL: Full PostgreSQL connection string
    - Neon format: postgresql://user:pass@host/db
    - Automatically converts to async driver (asyncpg)

    Returns:
        Database URL with asyncpg driver

    Raises:
        ValueError: If DATABASE_URL is not set
    """
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        raise ValueError(
            "DATABASE_URL environment variable not set. "
            "Please set it to your Neon PostgreSQL connection string."
        )

    # Remove asyncpg-incompatible parameters (sslmode, channel_binding)
    # asyncpg handles SSL automatically for Neon connections
    import re
    # Remove sslmode parameter
    database_url = re.sub(r'[?&]sslmode=[^&]*', '', database_url)
    # Remove channel_binding parameter
    database_url = re.sub(r'[?&]channel_binding=[^&]*', '', database_url)
    # Clean up any trailing ? or &
    database_url = re.sub(r'[?&]$', '', database_url)

    # Convert postgresql:// to postgresql+asyncpg:// for async support
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    elif database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+asyncpg://', 1)

    return database_url


def get_engine() -> AsyncEngine:
    """
    Get or create the database engine

    Uses connection pooling for optimal performance:
    - Pool size: 5-20 connections
    - Pool recycle: 3600 seconds (1 hour) - Neon compatible
    - Echo: Disabled in production (set SQLALCHEMY_ECHO=1 to enable)

    Returns:
        Async SQLAlchemy engine
    """
    global _engine

    if _engine is None:
        database_url = get_database_url()
        echo = os.getenv('SQLALCHEMY_ECHO', '0') == '1'

        _engine = create_async_engine(
            database_url,
            echo=echo,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,  # Recycle connections after 1 hour (Neon compatible)
            pool_pre_ping=True,  # Verify connections before using
        )

        print(f"✅ Database engine created (Neon PostgreSQL)")

    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """
    Get or create the session maker

    Returns:
        Async session maker for creating database sessions
    """
    global _session_maker

    if _session_maker is None:
        engine = get_engine()
        _session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )

    return _session_maker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session (async context manager)

    Usage:
        async with get_session() as session:
            result = await session.execute(select(OrchestratorState))

    Yields:
        AsyncSession instance
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database tables

    Creates all tables defined in models.py if they don't exist.
    Safe to call multiple times (idempotent).

    Usage:
        await init_db()
    """
    engine = get_engine()

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Database tables initialized")


async def close_db():
    """
    Close database connections

    Should be called during application shutdown
    """
    global _engine, _session_maker

    if _engine:
        await _engine.dispose()
        _engine = None
        _session_maker = None
        print("Database connections closed")
