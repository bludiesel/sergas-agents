"""Database configuration with automatic PostgreSQL and SQLite detection.

This module provides unified database configuration supporting both PostgreSQL (asyncpg)
and SQLite (aiosqlite) with automatic detection based on DATABASE_URL environment variable.

Features:
- Automatic database type detection from DATABASE_URL
- Async SQLAlchemy engine configuration
- Connection pooling for PostgreSQL
- WAL mode for SQLite performance
- Compatible with Alembic migrations
- Proper error handling and logging

Usage:
    from src.db.config import get_engine, get_database_url, get_db_session

    # Get configured engine
    engine = get_engine()

    # Use database session
    async with get_db_session() as session:
        result = await session.execute(query)
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional, Literal

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool, StaticPool
from sqlalchemy import event, text
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import structlog

logger = structlog.get_logger(__name__)

DatabaseType = Literal["postgresql", "sqlite"]


class DatabaseConfig(BaseSettings):
    """Database configuration with auto-detection support.

    Detects database type from DATABASE_URL:
    - postgresql+asyncpg://... → PostgreSQL with asyncpg
    - sqlite+aiosqlite://... or sqlite://... → SQLite with aiosqlite
    - No DATABASE_URL → Defaults to SQLite at ./data/sergas.db
    """

    # PostgreSQL connection parameters
    host: str = Field(default="localhost", alias="DATABASE_HOST")
    port: int = Field(default=5432, alias="DATABASE_PORT")
    name: str = Field(default="sergas_agent_db", alias="DATABASE_NAME")
    user: str = Field(default="sergas_user", alias="DATABASE_USER")
    password: str = Field(default="", alias="DATABASE_PASSWORD")

    # Connection string override (for testing or custom configurations)
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")

    # SQLite-specific configuration
    sqlite_path: str = Field(default="./data/sergas.db", alias="DATABASE_PATH")

    # PostgreSQL connection pooling settings
    pool_size: int = Field(default=20, ge=1, le=100)
    max_overflow: int = Field(default=10, ge=0, le=50)
    pool_timeout: int = Field(default=30, ge=1, le=300)
    pool_recycle: int = Field(default=3600, ge=300, le=7200)

    # Feature flags
    token_persistence_enabled: bool = Field(
        default=True, alias="TOKEN_PERSISTENCE_ENABLED"
    )
    enable_sql_echo: bool = Field(default=False, alias="SQL_ECHO")

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize DATABASE_URL format."""
        if v is None:
            return None

        # Normalize sqlite:// to sqlite+aiosqlite://
        if v.startswith("sqlite://"):
            # Extract path from sqlite://path or sqlite:///path
            if v.startswith("sqlite:///"):
                path = v[10:]  # Remove 'sqlite:///'
                return f"sqlite+aiosqlite:///{path}"
            else:
                path = v[9:]  # Remove 'sqlite://'
                return f"sqlite+aiosqlite:///{path}"

        return v

    def detect_database_type(self) -> DatabaseType:
        """Detect database type from DATABASE_URL.

        Returns:
            DatabaseType: Either 'postgresql' or 'sqlite'
        """
        url = self.get_database_url()

        if url.startswith("postgresql"):
            return "postgresql"
        elif url.startswith("sqlite"):
            return "sqlite"
        else:
            logger.warning(
                f"Unknown database URL scheme: {url}. Defaulting to SQLite.",
                database_url=url
            )
            return "sqlite"

    def get_database_url(self, use_async: bool = True) -> str:
        """Build database connection string with auto-detection.

        Args:
            use_async: If True, use async drivers (asyncpg/aiosqlite)

        Returns:
            str: SQLAlchemy connection string
        """
        # Use explicit DATABASE_URL if provided
        if self.database_url:
            return self.database_url

        # Check if PostgreSQL credentials are configured
        if self.password:  # Assume PostgreSQL if password is set
            driver = "postgresql+asyncpg" if use_async else "postgresql+psycopg2"
            return (
                f"{driver}://{self.user}:{self.password}@"
                f"{self.host}:{self.port}/{self.name}"
            )

        # Default to SQLite
        path = Path(self.sqlite_path).resolve()
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        driver = "sqlite+aiosqlite" if use_async else "sqlite"
        return f"{driver}:///{path}"

    def get_connection_string(self, use_async: bool = True) -> str:
        """Alias for get_database_url for backward compatibility."""
        return self.get_database_url(use_async=use_async)


def _configure_sqlite_engine(engine: AsyncEngine) -> None:
    """Configure SQLite engine with WAL mode and optimizations.

    Args:
        engine: AsyncEngine instance for SQLite
    """
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Set SQLite pragmas for performance and reliability."""
        cursor = dbapi_conn.cursor()

        # Enable WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")

        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys=ON")

        # Optimize for speed with reasonable safety
        cursor.execute("PRAGMA synchronous=NORMAL")

        # Increase cache size (negative = KB, 64MB cache)
        cursor.execute("PRAGMA cache_size=-64000")

        # Use memory for temporary tables
        cursor.execute("PRAGMA temp_store=MEMORY")

        cursor.close()

    logger.info("SQLite engine configured with WAL mode and optimizations")


def _configure_postgresql_engine(engine: AsyncEngine) -> None:
    """Configure PostgreSQL engine with connection optimizations.

    Args:
        engine: AsyncEngine instance for PostgreSQL
    """
    @event.listens_for(engine.sync_engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Configure PostgreSQL connection parameters."""
        logger.debug("PostgreSQL connection established", pid=dbapi_conn.info.backend_pid)

    logger.info("PostgreSQL engine configured with connection pooling")


# Global database configuration singleton
_db_config: Optional[DatabaseConfig] = None
_engine: Optional[AsyncEngine] = None
_async_session_maker: Optional[async_sessionmaker] = None


def get_database_config() -> DatabaseConfig:
    """Get or create global database configuration.

    Returns:
        DatabaseConfig: Singleton database configuration instance
    """
    global _db_config

    if _db_config is None:
        _db_config = DatabaseConfig()
        logger.info(
            "Database configuration initialized",
            db_type=_db_config.detect_database_type(),
            url_prefix=_db_config.get_database_url()[:20] + "..."
        )

    return _db_config


def get_database_url() -> str:
    """Get configured database URL.

    Returns:
        str: Database connection URL (async driver)
    """
    config = get_database_config()
    return config.get_database_url(use_async=True)


def get_engine(force_recreate: bool = False) -> AsyncEngine:
    """Get or create async SQLAlchemy engine with auto-configuration.

    Args:
        force_recreate: If True, recreate engine even if already exists

    Returns:
        AsyncEngine: Configured async database engine
    """
    global _engine

    if _engine is not None and not force_recreate:
        return _engine

    config = get_database_config()
    db_type = config.detect_database_type()
    database_url = config.get_database_url(use_async=True)

    # Configure pooling based on database type
    if db_type == "postgresql":
        poolclass = QueuePool if config.token_persistence_enabled else NullPool
        engine_kwargs = {
            "poolclass": poolclass,
            "pool_size": config.pool_size,
            "max_overflow": config.max_overflow,
            "pool_timeout": config.pool_timeout,
            "pool_recycle": config.pool_recycle,
            "pool_pre_ping": True,  # Verify connections before using
        }
    else:  # SQLite
        # Use StaticPool for SQLite to maintain single connection
        poolclass = StaticPool
        engine_kwargs = {
            "poolclass": poolclass,
            "connect_args": {"check_same_thread": False},
        }

    # Create engine
    _engine = create_async_engine(
        database_url,
        echo=config.enable_sql_echo,
        **engine_kwargs
    )

    # Apply database-specific configurations
    if db_type == "postgresql":
        _configure_postgresql_engine(_engine)
    else:
        _configure_sqlite_engine(_engine)

    logger.info(
        "Database engine created",
        db_type=db_type,
        poolclass=poolclass.__name__,
        echo=config.enable_sql_echo
    )

    return _engine


def get_async_session_maker() -> async_sessionmaker:
    """Get or create async session maker.

    Returns:
        async_sessionmaker: Session factory for database sessions
    """
    global _async_session_maker

    if _async_session_maker is None:
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        logger.debug("Async session maker created")

    return _async_session_maker


# Backward compatibility exports
db_config = get_database_config()
engine = get_engine()
async_session_maker = get_async_session_maker()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for database sessions.

    Provides automatic transaction management with commit/rollback.

    Usage:
        async with get_db_session() as session:
            result = await session.execute(query)

    Yields:
        AsyncSession: Database session with automatic cleanup
    """
    session_maker = get_async_session_maker()
    session = session_maker()

    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error("Database session error", error=str(e), exc_info=True)
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
            result = await session.execute(text("SELECT 1"))
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
        engine = get_engine()
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
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error("Failed to drop database tables", error=str(e))
        raise


async def close_database_connections() -> None:
    """Close all database connections gracefully."""
    global _engine, _async_session_maker

    if _engine:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None
        logger.info("Database connections closed")


__all__ = [
    "DatabaseConfig",
    "DatabaseType",
    "get_database_config",
    "get_database_url",
    "get_engine",
    "get_async_session_maker",
    "get_db_session",
    "check_database_health",
    "init_database",
    "drop_all_tables",
    "close_database_connections",
    # Backward compatibility
    "db_config",
    "engine",
    "async_session_maker",
]
