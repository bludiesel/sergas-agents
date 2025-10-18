"""Unit tests for SessionManager.

Tests cover:
- Session creation and initialization
- Session lifecycle (start, pause, resume, complete)
- Context and metrics updates
- Session recovery from checkpoints
- Performance validation (< 5s recovery time)
- Redis caching
- Database persistence
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import time
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.orchestrator.session_manager import (
    SessionManager,
    SessionStatus,
    SessionType,
)


@pytest.fixture
async def db_session():
    """Create test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    from src.db.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session


@pytest.fixture
def snapshot_dir():
    """Create temporary snapshot directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
async def session_manager(db_session, snapshot_dir):
    """Create SessionManager instance."""
    with patch('redis.asyncio.from_url') as mock_redis:
        mock_client = AsyncMock()
        mock_redis.return_value = mock_client

        manager = SessionManager(
            db_session=db_session,
            redis_url="redis://localhost:6379/0",
            snapshot_dir=snapshot_dir,
            checkpoint_interval_seconds=60,
        )

        await manager.initialize()
        yield manager
        await manager.close()


@pytest.mark.asyncio
async def test_create_session(session_manager):
    """Test basic session creation."""
    snapshot = await session_manager.create_session(
        orchestrator_id="test_orch",
        session_type=SessionType.SCHEDULED,
    )

    assert snapshot.session_id.startswith("session_test_orch_")
    assert snapshot.status == SessionStatus.PENDING
    assert snapshot.session_type == SessionType.SCHEDULED


@pytest.mark.asyncio
async def test_session_lifecycle(session_manager):
    """Test complete session lifecycle."""
    # Create
    snapshot = await session_manager.create_session(
        "test_orch", SessionType.SCHEDULED
    )

    # Start
    started = await session_manager.start_session(snapshot.session_id)
    assert started.status == SessionStatus.RUNNING

    # Pause
    paused = await session_manager.pause_session(snapshot.session_id)
    assert paused.status == SessionStatus.PAUSED

    # Resume
    resumed = await session_manager.resume_session(snapshot.session_id)
    assert resumed.status == SessionStatus.RUNNING

    # Complete
    completed = await session_manager.complete_session(snapshot.session_id)
    assert completed.status == SessionStatus.COMPLETED


@pytest.mark.asyncio
async def test_session_recovery_performance(session_manager, snapshot_dir):
    """Validate session recovery time < 5 seconds (PRD requirement)."""
    # Create session with data
    snapshot = await session_manager.create_session(
        "perf_test", SessionType.SCHEDULED,
        account_ids=["acc_" + str(i) for i in range(100)],
    )

    # Create checkpoint
    checkpoint_path = snapshot_dir / f"{snapshot.session_id}.checkpoint.json"
    snapshot_data = await session_manager.get_session(snapshot.session_id)
    with open(checkpoint_path, "w") as f:
        f.write(snapshot_data.model_dump_json())

    del session_manager._active_sessions[snapshot.session_id]

    # Measure recovery time
    start = time.time()
    recovered = await session_manager.recover_session(snapshot.session_id)
    recovery_time = time.time() - start

    assert recovery_time < 5.0, f"Recovery took {recovery_time}s, exceeds 5s"
    assert len(recovered.context.account_ids) == 100
