"""Database configuration with async SQLAlchemy engine and connection pooling."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool
from pydantic_settings import BaseSettings
from pydantic import Field
import structlog

logger = structlog.get_logger(__name__)


class DatabaseConfig(BaseSettings):
    """Database configuration from environment variables."""

    host: str = Field(default="localhost", alias="DATABASE_HOST")
    port: int = Field(default=5432, alias="DATABASE_PORT")
    name: str = Field(default="sergas_agent_db", alias="DATABASE_NAME")
    user: str = Field(default="sergas_user", alias="DATABASE_USER")
    password: str = Field(default="", alias="DATABASE_PASSWORD")

    # Connection pooling settings
    pool_size: int = Field(default=20, ge=1, le=100)
    max_overflow: int = Field(default=10, ge=0, le=50)
    pool_timeout: int = Field(default=30, ge=1, le=300)
    pool_recycle: int = Field(default=3600, ge=300, le=7200)

    # Connection string override (for testing)
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")

    # Feature flags
    token_persistence_enabled: bool = Field(
        default=True, alias="TOKEN_PERSISTENCE_ENABLED"
    )
    enable_sql_echo: bool = Field(default=False, alias="SQL_ECHO")

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        case_sensitive = False

    def get_connection_string(self, use_async: bool = True) -> str:
        """Build database connection string.

        Args:
            use_async: If True, use asyncpg driver; otherwise psycopg2

        Returns:
            str: SQLAlchemy connection string
        """
        if self.database_url:
            return self.database_url

        driver = "postgresql+asyncpg" if use_async else "postgresql+psycopg2"
        return (
            f"{driver}://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.name}"
        )


# Global database configuration
db_config = DatabaseConfig()

# Create async engine with connection pooling
engine: AsyncEngine = create_async_engine(
    db_config.get_connection_string(use_async=True),
    echo=db_config.enable_sql_echo,
    poolclass=QueuePool if db_config.token_persistence_enabled else NullPool,
    pool_size=db_config.pool_size,
    max_overflow=db_config.max_overflow,
    pool_timeout=db_config.pool_timeout,
    pool_recycle=db_config.pool_recycle,
    pool_pre_ping=True,  # Verify connections before using
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for database sessions.

    Usage:
        async with get_db_session() as session:
            result = await session.execute(query)

    Yields:
        AsyncSession: Database session with automatic cleanup
    """
    session = async_session_maker()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error("Database session error", error=str(e))
        raise
    finally:
        await session.close()


async def check_database_health() -> bool:
    """Check database connection health.

    Returns:
        bool: True if database is accessible and healthy
    """
    try:
        async with get_db_session() as session:
            # Simple query to verify connection
            result = await session.execute("SELECT 1")
            result.scalar()
            logger.info("Database health check passed")
            return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False


async def init_database() -> None:
    """Initialize database schema (create all tables).

    WARNING: Only use in development. Use Alembic migrations in production.
    """
    from src.db.models import Base

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database schema", error=str(e))
        raise


async def drop_all_tables() -> None:
    """Drop all database tables.

    WARNING: DESTRUCTIVE OPERATION. Only use in development/testing.
    """
    from src.db.models import Base

    env = os.getenv("ENV", "development")
    if env == "production":
        raise RuntimeError("Cannot drop tables in production environment!")

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error("Failed to drop database tables", error=str(e))
        raise


async def close_database_connections() -> None:
    """Close all database connections gracefully."""
    await engine.dispose()
    logger.info("Database connections closed")
