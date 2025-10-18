"""Session management for orchestrator with context preservation and recovery.

This module implements comprehensive session lifecycle management including:
- Session creation and initialization
- Context preservation across agent invocations
- Session state snapshots at milestones
- Session resumption after interruptions
- Session history and audit trail
- Session cleanup and archival
- Integration with Claude SDK session APIs
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set
from enum import Enum
import json
import asyncio
from pathlib import Path
import structlog
from pydantic import BaseModel, Field, ConfigDict
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from contextlib import asynccontextmanager

logger = structlog.get_logger(__name__)


class SessionStatus(str, Enum):
    """Session execution status."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class SessionType(str, Enum):
    """Type of orchestrator session."""

    SCHEDULED = "scheduled"
    ON_DEMAND = "on_demand"
    MANUAL = "manual"
    RECOVERY = "recovery"


class SessionContext(BaseModel):
    """Session context snapshot for preservation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    account_ids: List[str] = Field(default_factory=list)
    owner_id: Optional[str] = None
    current_batch: int = 0
    total_batches: int = 0
    processed_accounts: Set[str] = Field(default_factory=set)
    failed_accounts: Set[str] = Field(default_factory=set)
    recommendations_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    checkpoint_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SessionMetrics(BaseModel):
    """Performance metrics for session execution."""

    total_duration_ms: int = 0
    account_processing_times_ms: List[int] = Field(default_factory=list)
    api_call_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    token_usage: int = 0
    error_count: int = 0


class SessionSnapshot(BaseModel):
    """Complete session state snapshot for recovery."""

    session_id: str
    status: SessionStatus
    session_type: SessionType
    context: SessionContext
    metrics: SessionMetrics
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None


class SessionManager:
    """Manages orchestrator session lifecycle with persistence and recovery.

    Provides comprehensive session management including:
    - Creation and initialization of new sessions
    - Context preservation via snapshots
    - Session recovery after interruptions
    - Audit trail generation
    - Redis caching for fast access
    - PostgreSQL persistence for durability
    """

    def __init__(
        self,
        db_session: AsyncSession,
        redis_url: str,
        snapshot_dir: Path,
        checkpoint_interval_seconds: int = 300,
    ):
        """Initialize session manager.

        Args:
            db_session: AsyncPG database session
            redis_url: Redis connection URL for caching
            snapshot_dir: Directory for session snapshots
            checkpoint_interval_seconds: Interval between automatic checkpoints
        """
        self.db = db_session
        self.redis_url = redis_url
        self.snapshot_dir = Path(snapshot_dir)
        self.checkpoint_interval = checkpoint_interval_seconds
        self._redis_client: Optional[aioredis.Redis] = None
        self._active_sessions: Dict[str, SessionSnapshot] = {}
        self._checkpoint_tasks: Dict[str, asyncio.Task] = {}

        # Ensure snapshot directory exists
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "session_manager_initialized",
            snapshot_dir=str(self.snapshot_dir),
            checkpoint_interval=checkpoint_interval_seconds,
        )

    async def initialize(self) -> None:
        """Initialize async resources (Redis connection)."""
        self._redis_client = await aioredis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("session_manager_redis_connected", url=self.redis_url)

    async def close(self) -> None:
        """Close async resources and cleanup."""
        # Cancel all checkpoint tasks
        for task in self._checkpoint_tasks.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        if self._redis_client:
            await self._redis_client.close()
            logger.info("session_manager_redis_closed")

    async def create_session(
        self,
        orchestrator_id: str,
        session_type: SessionType,
        owner_id: Optional[str] = None,
        account_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionSnapshot:
        """Create a new orchestrator session.

        Args:
            orchestrator_id: ID of the orchestrator agent
            session_type: Type of session being created
            owner_id: Optional account owner ID
            account_ids: Optional list of account IDs to process
            metadata: Optional additional metadata

        Returns:
            SessionSnapshot: Created session snapshot

        Raises:
            ValueError: If orchestrator_id is invalid
        """
        import uuid

        session_id = f"session_{orchestrator_id}_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        context = SessionContext(
            account_ids=account_ids or [],
            owner_id=owner_id,
            metadata=metadata or {},
            checkpoint_timestamp=now,
        )

        snapshot = SessionSnapshot(
            session_id=session_id,
            status=SessionStatus.PENDING,
            session_type=session_type,
            context=context,
            metrics=SessionMetrics(),
            created_at=now,
            updated_at=now,
        )

        # Persist to database
        await self._persist_session_to_db(snapshot, orchestrator_id)

        # Cache in Redis
        await self._cache_session_to_redis(snapshot)

        # Store in memory
        self._active_sessions[session_id] = snapshot

        logger.info(
            "session_created",
            session_id=session_id,
            orchestrator_id=orchestrator_id,
            session_type=session_type.value,
            account_count=len(account_ids or []),
        )

        return snapshot

    async def start_session(self, session_id: str) -> SessionSnapshot:
        """Start a session and begin checkpoint loop.

        Args:
            session_id: ID of session to start

        Returns:
            SessionSnapshot: Updated session snapshot

        Raises:
            ValueError: If session not found or already running
        """
        snapshot = await self.get_session(session_id)
        if not snapshot:
            raise ValueError(f"Session not found: {session_id}")

        if snapshot.status == SessionStatus.RUNNING:
            raise ValueError(f"Session already running: {session_id}")

        snapshot.status = SessionStatus.RUNNING
        snapshot.updated_at = datetime.now(timezone.utc)

        await self._update_session(snapshot)

        # Start automatic checkpoint task
        self._checkpoint_tasks[session_id] = asyncio.create_task(
            self._checkpoint_loop(session_id)
        )

        logger.info("session_started", session_id=session_id)
        return snapshot

    async def pause_session(self, session_id: str) -> SessionSnapshot:
        """Pause a running session.

        Args:
            session_id: ID of session to pause

        Returns:
            SessionSnapshot: Updated session snapshot
        """
        snapshot = await self.get_session(session_id)
        if not snapshot:
            raise ValueError(f"Session not found: {session_id}")

        snapshot.status = SessionStatus.PAUSED
        snapshot.updated_at = datetime.now(timezone.utc)

        # Create checkpoint before pausing
        await self._create_checkpoint(snapshot)

        await self._update_session(snapshot)

        # Cancel checkpoint task
        if session_id in self._checkpoint_tasks:
            self._checkpoint_tasks[session_id].cancel()
            del self._checkpoint_tasks[session_id]

        logger.info("session_paused", session_id=session_id)
        return snapshot

    async def resume_session(self, session_id: str) -> SessionSnapshot:
        """Resume a paused session.

        Args:
            session_id: ID of session to resume

        Returns:
            SessionSnapshot: Updated session snapshot
        """
        snapshot = await self.get_session(session_id)
        if not snapshot:
            raise ValueError(f"Session not found: {session_id}")

        if snapshot.status != SessionStatus.PAUSED:
            raise ValueError(f"Session not paused: {session_id}")

        snapshot.status = SessionStatus.RUNNING
        snapshot.updated_at = datetime.now(timezone.utc)

        await self._update_session(snapshot)

        # Restart checkpoint task
        self._checkpoint_tasks[session_id] = asyncio.create_task(
            self._checkpoint_loop(session_id)
        )

        logger.info("session_resumed", session_id=session_id)
        return snapshot

    async def complete_session(
        self,
        session_id: str,
        error_message: Optional[str] = None,
    ) -> SessionSnapshot:
        """Complete a session (successfully or with failure).

        Args:
            session_id: ID of session to complete
            error_message: Optional error message if failed

        Returns:
            SessionSnapshot: Final session snapshot
        """
        snapshot = await self.get_session(session_id)
        if not snapshot:
            raise ValueError(f"Session not found: {session_id}")

        snapshot.status = SessionStatus.FAILED if error_message else SessionStatus.COMPLETED
        snapshot.error_message = error_message
        snapshot.updated_at = datetime.now(timezone.utc)

        # Final checkpoint
        await self._create_checkpoint(snapshot)

        await self._update_session(snapshot)

        # Cleanup
        if session_id in self._checkpoint_tasks:
            self._checkpoint_tasks[session_id].cancel()
            del self._checkpoint_tasks[session_id]

        if session_id in self._active_sessions:
            del self._active_sessions[session_id]

        logger.info(
            "session_completed",
            session_id=session_id,
            status=snapshot.status.value,
            error=error_message,
        )

        return snapshot

    async def update_context(
        self,
        session_id: str,
        **context_updates: Any,
    ) -> SessionSnapshot:
        """Update session context with new data.

        Args:
            session_id: ID of session to update
            **context_updates: Key-value pairs to update in context

        Returns:
            SessionSnapshot: Updated session snapshot
        """
        snapshot = await self.get_session(session_id)
        if not snapshot:
            raise ValueError(f"Session not found: {session_id}")

        # Update context fields
        for key, value in context_updates.items():
            if hasattr(snapshot.context, key):
                if isinstance(getattr(snapshot.context, key), set):
                    # Handle set updates
                    current = getattr(snapshot.context, key)
                    if isinstance(value, (list, set)):
                        current.update(value)
                    else:
                        current.add(value)
                elif isinstance(getattr(snapshot.context, key), list):
                    # Handle list updates
                    current = getattr(snapshot.context, key)
                    if isinstance(value, list):
                        current.extend(value)
                    else:
                        current.append(value)
                else:
                    setattr(snapshot.context, key, value)
            else:
                snapshot.context.metadata[key] = value

        snapshot.context.checkpoint_timestamp = datetime.now(timezone.utc)
        snapshot.updated_at = datetime.now(timezone.utc)

        await self._update_session(snapshot)

        logger.debug("session_context_updated", session_id=session_id, updates=list(context_updates.keys()))
        return snapshot

    async def update_metrics(
        self,
        session_id: str,
        **metric_updates: Any,
    ) -> SessionSnapshot:
        """Update session metrics.

        Args:
            session_id: ID of session to update
            **metric_updates: Metric updates to apply

        Returns:
            SessionSnapshot: Updated session snapshot
        """
        snapshot = await self.get_session(session_id)
        if not snapshot:
            raise ValueError(f"Session not found: {session_id}")

        for key, value in metric_updates.items():
            if hasattr(snapshot.metrics, key):
                current = getattr(snapshot.metrics, key)
                if isinstance(current, int):
                    setattr(snapshot.metrics, key, current + value)
                elif isinstance(current, list):
                    if isinstance(value, list):
                        current.extend(value)
                    else:
                        current.append(value)

        snapshot.updated_at = datetime.now(timezone.utc)
        await self._update_session(snapshot)

        return snapshot

    async def get_session(self, session_id: str) -> Optional[SessionSnapshot]:
        """Retrieve session snapshot.

        Checks in-memory cache, then Redis, then database.

        Args:
            session_id: ID of session to retrieve

        Returns:
            SessionSnapshot or None if not found
        """
        # Check memory first
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]

        # Check Redis cache
        snapshot = await self._get_session_from_redis(session_id)
        if snapshot:
            self._active_sessions[session_id] = snapshot
            return snapshot

        # Check database
        snapshot = await self._get_session_from_db(session_id)
        if snapshot:
            await self._cache_session_to_redis(snapshot)
            self._active_sessions[session_id] = snapshot
            return snapshot

        return None

    async def recover_session(self, session_id: str) -> SessionSnapshot:
        """Recover interrupted session from last checkpoint.

        Args:
            session_id: ID of session to recover

        Returns:
            SessionSnapshot: Recovered session

        Raises:
            ValueError: If session cannot be recovered
        """
        # Try to load from checkpoint file
        checkpoint_path = self.snapshot_dir / f"{session_id}.checkpoint.json"
        if checkpoint_path.exists():
            try:
                with open(checkpoint_path, "r") as f:
                    data = json.load(f)
                    snapshot = SessionSnapshot(**data)

                snapshot.status = SessionStatus.RUNNING
                snapshot.session_type = SessionType.RECOVERY
                snapshot.updated_at = datetime.now(timezone.utc)

                await self._update_session(snapshot)

                logger.info(
                    "session_recovered_from_checkpoint",
                    session_id=session_id,
                    checkpoint_timestamp=snapshot.context.checkpoint_timestamp,
                )

                return snapshot
            except Exception as e:
                logger.error("checkpoint_recovery_failed", session_id=session_id, error=str(e))

        # Try database recovery
        snapshot = await self.get_session(session_id)
        if snapshot and snapshot.status == SessionStatus.INTERRUPTED:
            snapshot.status = SessionStatus.RUNNING
            snapshot.session_type = SessionType.RECOVERY
            snapshot.updated_at = datetime.now(timezone.utc)

            await self._update_session(snapshot)

            logger.info("session_recovered_from_database", session_id=session_id)
            return snapshot

        raise ValueError(f"Cannot recover session: {session_id}")

    async def list_active_sessions(self) -> List[SessionSnapshot]:
        """List all active (non-completed) sessions.

        Returns:
            List of active session snapshots
        """
        # Import here to avoid circular dependency
        from src.db.models import AgentSession

        result = await self.db.execute(
            select(AgentSession).where(
                AgentSession.status.in_([
                    SessionStatus.PENDING.value,
                    SessionStatus.RUNNING.value,
                    SessionStatus.PAUSED.value,
                ])
            )
        )

        sessions = result.scalars().all()
        snapshots = []

        for session in sessions:
            snapshot = await self.get_session(session.session_id)
            if snapshot:
                snapshots.append(snapshot)

        return snapshots

    async def cleanup_old_sessions(self, older_than_days: int = 7) -> int:
        """Archive and cleanup sessions older than specified days.

        Args:
            older_than_days: Delete sessions older than this many days

        Returns:
            Number of sessions cleaned up
        """
        from src.db.models import AgentSession

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)

        # Get old completed/failed sessions
        result = await self.db.execute(
            select(AgentSession).where(
                AgentSession.status.in_([
                    SessionStatus.COMPLETED.value,
                    SessionStatus.FAILED.value,
                ]),
                AgentSession.updated_at < cutoff_date,
            )
        )

        old_sessions = result.scalars().all()
        count = 0

        for session in old_sessions:
            # Archive checkpoint file if exists
            checkpoint_path = self.snapshot_dir / f"{session.session_id}.checkpoint.json"
            if checkpoint_path.exists():
                archive_path = self.snapshot_dir / "archive" / f"{session.session_id}.archive.json"
                archive_path.parent.mkdir(parents=True, exist_ok=True)
                checkpoint_path.rename(archive_path)

            # Remove from Redis
            if self._redis_client:
                await self._redis_client.delete(f"session:{session.session_id}")

            count += 1

        logger.info("sessions_cleaned_up", count=count, older_than_days=older_than_days)
        return count

    # Private helper methods

    async def _persist_session_to_db(self, snapshot: SessionSnapshot, orchestrator_id: str) -> None:
        """Persist session to database."""
        from src.db.models import AgentSession

        session_record = AgentSession(
            session_id=snapshot.session_id,
            orchestrator_id=orchestrator_id,
            status=snapshot.status.value,
            session_type=snapshot.session_type.value,
            context_snapshot=snapshot.context.model_dump(mode="json"),
            account_ids=snapshot.context.account_ids,
            owner_id=snapshot.context.owner_id,
            created_at=snapshot.created_at,
            updated_at=snapshot.updated_at,
        )

        self.db.add(session_record)
        await self.db.commit()

    async def _update_session(self, snapshot: SessionSnapshot) -> None:
        """Update session in all storage layers."""
        from src.db.models import AgentSession

        # Update database
        await self.db.execute(
            update(AgentSession)
            .where(AgentSession.session_id == snapshot.session_id)
            .values(
                status=snapshot.status.value,
                context_snapshot=snapshot.context.model_dump(mode="json"),
                updated_at=snapshot.updated_at,
            )
        )
        await self.db.commit()

        # Update Redis cache
        await self._cache_session_to_redis(snapshot)

        # Update memory
        self._active_sessions[snapshot.session_id] = snapshot

    async def _cache_session_to_redis(self, snapshot: SessionSnapshot) -> None:
        """Cache session snapshot in Redis."""
        if not self._redis_client:
            return

        key = f"session:{snapshot.session_id}"
        value = snapshot.model_dump_json()

        await self._redis_client.setex(
            key,
            86400,  # 24 hour TTL
            value,
        )

    async def _get_session_from_redis(self, session_id: str) -> Optional[SessionSnapshot]:
        """Retrieve session from Redis cache."""
        if not self._redis_client:
            return None

        key = f"session:{session_id}"
        value = await self._redis_client.get(key)

        if value:
            return SessionSnapshot.model_validate_json(value)

        return None

    async def _get_session_from_db(self, session_id: str) -> Optional[SessionSnapshot]:
        """Retrieve session from database."""
        from src.db.models import AgentSession

        result = await self.db.execute(
            select(AgentSession).where(AgentSession.session_id == session_id)
        )

        session_record = result.scalar_one_or_none()
        if not session_record:
            return None

        context = SessionContext(**session_record.context_snapshot)

        return SessionSnapshot(
            session_id=session_record.session_id,
            status=SessionStatus(session_record.status),
            session_type=SessionType(session_record.session_type),
            context=context,
            metrics=SessionMetrics(),  # Metrics stored separately
            created_at=session_record.created_at,
            updated_at=session_record.updated_at,
        )

    async def _create_checkpoint(self, snapshot: SessionSnapshot) -> None:
        """Create a checkpoint file for session recovery."""
        checkpoint_path = self.snapshot_dir / f"{snapshot.session_id}.checkpoint.json"

        try:
            with open(checkpoint_path, "w") as f:
                f.write(snapshot.model_dump_json(indent=2))

            logger.debug("checkpoint_created", session_id=snapshot.session_id)
        except Exception as e:
            logger.error("checkpoint_creation_failed", session_id=snapshot.session_id, error=str(e))

    async def _checkpoint_loop(self, session_id: str) -> None:
        """Background task for automatic checkpointing."""
        try:
            while True:
                await asyncio.sleep(self.checkpoint_interval)

                snapshot = await self.get_session(session_id)
                if snapshot and snapshot.status == SessionStatus.RUNNING:
                    await self._create_checkpoint(snapshot)
                else:
                    break
        except asyncio.CancelledError:
            logger.debug("checkpoint_loop_cancelled", session_id=session_id)
        except Exception as e:
            logger.error("checkpoint_loop_error", session_id=session_id, error=str(e))

    @asynccontextmanager
    async def session_scope(
        self,
        orchestrator_id: str,
        session_type: SessionType,
        **kwargs: Any,
    ):
        """Context manager for automatic session lifecycle management.

        Usage:
            async with manager.session_scope("orch_1", SessionType.SCHEDULED) as session:
                # Do work with session
                await manager.update_context(session.session_id, ...)

        Args:
            orchestrator_id: ID of orchestrator
            session_type: Type of session
            **kwargs: Additional arguments for create_session

        Yields:
            SessionSnapshot: Active session
        """
        session = await self.create_session(orchestrator_id, session_type, **kwargs)
        await self.start_session(session.session_id)

        try:
            yield session
            await self.complete_session(session.session_id)
        except Exception as e:
            logger.error("session_failed", session_id=session.session_id, error=str(e))
            await self.complete_session(session.session_id, error_message=str(e))
            raise
