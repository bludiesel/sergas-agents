"""Pytest fixtures for database tests."""

import asyncio
import pytest
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.db.models import Base
from src.db.config import DatabaseConfig
from src.db.repositories.token_repository import TokenRepository


# Test database configuration
@pytest.fixture(scope="session")
def test_db_config() -> DatabaseConfig:
    """Test database configuration."""
    return DatabaseConfig(
        host="localhost",
        port=5432,
        name="sergas_agent_test_db",
        user="sergas_user",
        password="test_password",
        pool_size=5,
        max_overflow=5,
        token_persistence_enabled=True,
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine(test_db_config: DatabaseConfig) -> AsyncGenerator[AsyncEngine, None]:
    """Create test database engine."""
    engine = create_async_engine(
        test_db_config.get_connection_string(use_async=True),
        echo=False,
        poolclass=NullPool,  # No pooling for tests
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session with transaction rollback."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest.fixture
async def token_repository(db_session: AsyncSession) -> TokenRepository:
    """Create token repository with test session."""
    return TokenRepository(session=db_session)


@pytest.fixture
def sample_token_data() -> dict:
    """Sample token data for testing."""
    return {
        "token_type": "oauth",
        "access_token": "test_access_token_abc123",
        "refresh_token": "test_refresh_token_xyz789",
        "expires_in": 3600,
    }
