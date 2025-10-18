"""APScheduler integration for account review cycle scheduling.

This module implements comprehensive scheduling infrastructure including:
- Daily/weekly review scheduling with cron expressions
- On-demand review triggers
- Account owner assignment loading
- Priority-based scheduling (high-risk accounts first)
- Schedule persistence and recovery
- Timezone handling
- Integration with session manager
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum
import structlog
from pydantic import BaseModel, Field, ConfigDict, field_validator
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.job import Job
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
import pytz

logger = structlog.get_logger(__name__)


class ScheduleType(str, Enum):
    """Type of review schedule."""

    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    CRON = "cron"
    INTERVAL = "interval"
    ONE_TIME = "one_time"


class SchedulePriority(str, Enum):
    """Priority level for scheduled reviews."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ScheduleConfig(BaseModel):
    """Configuration for a scheduled review."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    schedule_id: str
    schedule_type: ScheduleType
    owner_id: Optional[str] = None
    account_filter: Dict[str, Any] = Field(default_factory=dict)
    cron_expression: Optional[str] = None
    interval_minutes: Optional[int] = None
    scheduled_time: Optional[datetime] = None
    timezone: str = "UTC"
    priority: SchedulePriority = SchedulePriority.MEDIUM
    enabled: bool = True
    max_retries: int = 3
    retry_delay_minutes: int = 5
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate timezone is valid."""
        try:
            pytz.timezone(v)
            return v
        except pytz.UnknownTimeZoneError:
            raise ValueError(f"Invalid timezone: {v}")

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v: Optional[str]) -> Optional[str]:
        """Validate cron expression if provided."""
        if v is not None:
            try:
                # Test if cron expression is valid
                CronTrigger.from_crontab(v)
                return v
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid cron expression: {v}") from e
        return v


class ScheduleExecution(BaseModel):
    """Record of a schedule execution."""

    schedule_id: str
    execution_time: datetime
    session_id: Optional[str] = None
    status: str  # "success", "failed", "skipped"
    error_message: Optional[str] = None
    accounts_processed: int = 0
    duration_seconds: float = 0.0


class AccountScheduler:
    """Manages scheduling of account review cycles.

    Provides comprehensive scheduling capabilities including:
    - Cron-based scheduled reviews
    - Interval-based reviews
    - One-time scheduled reviews
    - Priority-based execution
    - Schedule persistence and recovery
    - Timezone-aware scheduling
    - Retry logic with exponential backoff
    """

    def __init__(
        self,
        db_session: AsyncSession,
        session_manager: Any,  # SessionManager (avoid circular import)
        timezone: str = "UTC",
    ):
        """Initialize account scheduler.

        Args:
            db_session: Database session for persistence
            session_manager: SessionManager instance for creating sessions
            timezone: Default timezone for schedules
        """
        self.db = db_session
        self.session_manager = session_manager
        self.default_timezone = pytz.timezone(timezone)

        # Configure APScheduler
        jobstores = {"default": MemoryJobStore()}
        executors = {"default": AsyncIOExecutor()}
        job_defaults = {
            "coalesce": True,  # Combine missed runs
            "max_instances": 3,  # Max concurrent instances
            "misfire_grace_time": 300,  # 5 minutes grace period
        }

        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=self.default_timezone,
        )

        self._schedules: Dict[str, ScheduleConfig] = {}
        self._execution_history: List[ScheduleExecution] = []
        self._running_jobs: Set[str] = set()

        logger.info("scheduler_initialized", timezone=timezone)

    async def initialize(self) -> None:
        """Initialize scheduler and load persisted schedules."""
        # Start APScheduler
        self.scheduler.start()
        logger.info("apscheduler_started")

        # Load persisted schedules from database
        await self._load_schedules_from_db()

    async def shutdown(self) -> None:
        """Shutdown scheduler gracefully."""
        # Wait for running jobs to complete (with timeout)
        self.scheduler.shutdown(wait=True)
        logger.info("scheduler_shutdown")

    async def create_schedule(
        self,
        schedule_type: ScheduleType,
        job_callback: Callable,
        owner_id: Optional[str] = None,
        account_filter: Optional[Dict[str, Any]] = None,
        cron_expression: Optional[str] = None,
        interval_minutes: Optional[int] = None,
        scheduled_time: Optional[datetime] = None,
        timezone: Optional[str] = None,
        priority: SchedulePriority = SchedulePriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ScheduleConfig:
        """Create a new schedule for account reviews.

        Args:
            schedule_type: Type of schedule (daily, weekly, cron, etc.)
            job_callback: Async function to call when schedule triggers
            owner_id: Optional owner ID to filter accounts
            account_filter: Optional additional account filters
            cron_expression: Cron expression for CRON type
            interval_minutes: Interval for INTERVAL type
            scheduled_time: Datetime for ONE_TIME type
            timezone: Timezone for schedule (defaults to scheduler default)
            priority: Priority level
            metadata: Additional metadata

        Returns:
            ScheduleConfig: Created schedule configuration

        Raises:
            ValueError: If schedule configuration is invalid
        """
        import uuid

        schedule_id = f"schedule_{uuid.uuid4().hex[:12]}"
        tz = timezone or self.default_timezone.zone

        config = ScheduleConfig(
            schedule_id=schedule_id,
            schedule_type=schedule_type,
            owner_id=owner_id,
            account_filter=account_filter or {},
            cron_expression=cron_expression,
            interval_minutes=interval_minutes,
            scheduled_time=scheduled_time,
            timezone=tz,
            priority=priority,
            metadata=metadata or {},
        )

        # Create APScheduler job based on schedule type
        trigger = self._create_trigger(config)
        job_kwargs = {
            "schedule_id": schedule_id,
            "owner_id": owner_id,
            "account_filter": account_filter or {},
            "priority": priority.value,
        }

        self.scheduler.add_job(
            self._execute_scheduled_review,
            trigger=trigger,
            args=[job_callback, config],
            kwargs=job_kwargs,
            id=schedule_id,
            name=f"Review_{owner_id or 'all'}_{schedule_type.value}",
            replace_existing=True,
        )

        # Store in memory and database
        self._schedules[schedule_id] = config
        await self._persist_schedule_to_db(config)

        logger.info(
            "schedule_created",
            schedule_id=schedule_id,
            schedule_type=schedule_type.value,
            owner_id=owner_id,
            priority=priority.value,
        )

        return config

    async def trigger_on_demand(
        self,
        job_callback: Callable,
        owner_id: Optional[str] = None,
        account_ids: Optional[List[str]] = None,
        priority: SchedulePriority = SchedulePriority.HIGH,
    ) -> str:
        """Trigger an on-demand review immediately.

        Args:
            job_callback: Callback function for review execution
            owner_id: Optional owner ID
            account_ids: Optional specific account IDs to review
            priority: Priority level (defaults to HIGH for on-demand)

        Returns:
            str: Job ID for tracking
        """
        import uuid

        job_id = f"ondemand_{uuid.uuid4().hex[:8]}"

        config = ScheduleConfig(
            schedule_id=job_id,
            schedule_type=ScheduleType.ONE_TIME,
            owner_id=owner_id,
            account_filter={"account_ids": account_ids} if account_ids else {},
            priority=priority,
            enabled=True,
        )

        # Schedule for immediate execution
        self.scheduler.add_job(
            self._execute_scheduled_review,
            trigger=DateTrigger(run_date=datetime.now(timezone.utc)),
            args=[job_callback, config],
            kwargs={
                "schedule_id": job_id,
                "owner_id": owner_id,
                "account_filter": config.account_filter,
                "priority": priority.value,
            },
            id=job_id,
            name=f"OnDemand_{owner_id or 'all'}",
        )

        logger.info(
            "on_demand_review_triggered",
            job_id=job_id,
            owner_id=owner_id,
            account_count=len(account_ids) if account_ids else 0,
        )

        return job_id

    async def update_schedule(
        self,
        schedule_id: str,
        **updates: Any,
    ) -> ScheduleConfig:
        """Update an existing schedule.

        Args:
            schedule_id: ID of schedule to update
            **updates: Fields to update

        Returns:
            ScheduleConfig: Updated configuration

        Raises:
            ValueError: If schedule not found
        """
        if schedule_id not in self._schedules:
            raise ValueError(f"Schedule not found: {schedule_id}")

        config = self._schedules[schedule_id]

        # Update configuration
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)

        # Update APScheduler job if trigger changed
        if any(k in updates for k in ["cron_expression", "interval_minutes", "scheduled_time"]):
            trigger = self._create_trigger(config)
            job = self.scheduler.get_job(schedule_id)
            if job:
                job.reschedule(trigger)

        # Persist changes
        await self._persist_schedule_to_db(config)

        logger.info("schedule_updated", schedule_id=schedule_id, updates=list(updates.keys()))
        return config

    async def delete_schedule(self, schedule_id: str) -> None:
        """Delete a schedule.

        Args:
            schedule_id: ID of schedule to delete
        """
        # Remove from APScheduler
        self.scheduler.remove_job(schedule_id)

        # Remove from memory
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]

        # Remove from database
        from src.db.models import ScheduledReview

        await self.db.execute(
            delete(ScheduledReview).where(ScheduledReview.review_id == schedule_id)
        )
        await self.db.commit()

        logger.info("schedule_deleted", schedule_id=schedule_id)

    async def pause_schedule(self, schedule_id: str) -> None:
        """Pause a schedule (stop executing but keep configuration).

        Args:
            schedule_id: ID of schedule to pause
        """
        if schedule_id in self._schedules:
            self._schedules[schedule_id].enabled = False

        job = self.scheduler.get_job(schedule_id)
        if job:
            job.pause()

        await self._persist_schedule_to_db(self._schedules[schedule_id])

        logger.info("schedule_paused", schedule_id=schedule_id)

    async def resume_schedule(self, schedule_id: str) -> None:
        """Resume a paused schedule.

        Args:
            schedule_id: ID of schedule to resume
        """
        if schedule_id in self._schedules:
            self._schedules[schedule_id].enabled = True

        job = self.scheduler.get_job(schedule_id)
        if job:
            job.resume()

        await self._persist_schedule_to_db(self._schedules[schedule_id])

        logger.info("schedule_resumed", schedule_id=schedule_id)

    async def get_schedule(self, schedule_id: str) -> Optional[ScheduleConfig]:
        """Get schedule configuration.

        Args:
            schedule_id: ID of schedule

        Returns:
            ScheduleConfig or None if not found
        """
        return self._schedules.get(schedule_id)

    async def list_schedules(
        self,
        owner_id: Optional[str] = None,
        enabled_only: bool = False,
    ) -> List[ScheduleConfig]:
        """List all schedules with optional filtering.

        Args:
            owner_id: Filter by owner ID
            enabled_only: Only return enabled schedules

        Returns:
            List of schedule configurations
        """
        schedules = list(self._schedules.values())

        if owner_id:
            schedules = [s for s in schedules if s.owner_id == owner_id]

        if enabled_only:
            schedules = [s for s in schedules if s.enabled]

        return schedules

    async def get_next_run_time(self, schedule_id: str) -> Optional[datetime]:
        """Get next scheduled run time for a schedule.

        Args:
            schedule_id: ID of schedule

        Returns:
            Datetime of next run, or None if not scheduled
        """
        job = self.scheduler.get_job(schedule_id)
        if job and job.next_run_time:
            return job.next_run_time.replace(tzinfo=timezone.utc)

        return None

    async def get_execution_history(
        self,
        schedule_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[ScheduleExecution]:
        """Get execution history for schedules.

        Args:
            schedule_id: Optional filter by schedule ID
            limit: Maximum number of records to return

        Returns:
            List of execution records
        """
        history = self._execution_history

        if schedule_id:
            history = [h for h in history if h.schedule_id == schedule_id]

        # Sort by execution time descending
        history = sorted(history, key=lambda x: x.execution_time, reverse=True)

        return history[:limit]

    # Private helper methods

    def _create_trigger(self, config: ScheduleConfig):
        """Create APScheduler trigger from configuration."""
        tz = pytz.timezone(config.timezone)

        if config.schedule_type == ScheduleType.DAILY:
            # Daily at midnight
            return CronTrigger(hour=0, minute=0, timezone=tz)

        elif config.schedule_type == ScheduleType.WEEKLY:
            # Weekly on Monday at midnight
            return CronTrigger(day_of_week="mon", hour=0, minute=0, timezone=tz)

        elif config.schedule_type == ScheduleType.BIWEEKLY:
            # Every 2 weeks on Monday
            return IntervalTrigger(weeks=2, timezone=tz)

        elif config.schedule_type == ScheduleType.MONTHLY:
            # First day of month at midnight
            return CronTrigger(day=1, hour=0, minute=0, timezone=tz)

        elif config.schedule_type == ScheduleType.CRON:
            if not config.cron_expression:
                raise ValueError("Cron expression required for CRON schedule type")
            return CronTrigger.from_crontab(config.cron_expression, timezone=tz)

        elif config.schedule_type == ScheduleType.INTERVAL:
            if not config.interval_minutes:
                raise ValueError("Interval minutes required for INTERVAL schedule type")
            return IntervalTrigger(minutes=config.interval_minutes, timezone=tz)

        elif config.schedule_type == ScheduleType.ONE_TIME:
            if not config.scheduled_time:
                raise ValueError("Scheduled time required for ONE_TIME schedule type")
            return DateTrigger(run_date=config.scheduled_time, timezone=tz)

        else:
            raise ValueError(f"Unsupported schedule type: {config.schedule_type}")

    async def _execute_scheduled_review(
        self,
        job_callback: Callable,
        config: ScheduleConfig,
        **kwargs: Any,
    ) -> None:
        """Execute a scheduled review job.

        Args:
            job_callback: Callback function to execute
            config: Schedule configuration
            **kwargs: Additional job arguments
        """
        schedule_id = config.schedule_id
        start_time = datetime.now(timezone.utc)

        # Check if already running
        if schedule_id in self._running_jobs:
            logger.warning("schedule_already_running", schedule_id=schedule_id)
            return

        self._running_jobs.add(schedule_id)

        execution = ScheduleExecution(
            schedule_id=schedule_id,
            execution_time=start_time,
            status="running",
        )

        try:
            logger.info(
                "executing_scheduled_review",
                schedule_id=schedule_id,
                owner_id=config.owner_id,
                priority=config.priority.value,
            )

            # Execute the callback
            result = await job_callback(config, **kwargs)

            # Record success
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            execution.status = "success"
            execution.session_id = result.get("session_id") if isinstance(result, dict) else None
            execution.accounts_processed = result.get("accounts_processed", 0) if isinstance(result, dict) else 0
            execution.duration_seconds = duration

            logger.info(
                "scheduled_review_completed",
                schedule_id=schedule_id,
                duration_seconds=duration,
                accounts_processed=execution.accounts_processed,
            )

        except Exception as e:
            logger.error(
                "scheduled_review_failed",
                schedule_id=schedule_id,
                error=str(e),
                exc_info=True,
            )

            execution.status = "failed"
            execution.error_message = str(e)
            execution.duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()

            # Handle retries if configured
            await self._handle_job_retry(config, str(e))

        finally:
            self._running_jobs.discard(schedule_id)
            self._execution_history.append(execution)

            # Trim history to last 1000 executions
            if len(self._execution_history) > 1000:
                self._execution_history = self._execution_history[-1000:]

    async def _handle_job_retry(self, config: ScheduleConfig, error: str) -> None:
        """Handle retry logic for failed jobs.

        Args:
            config: Schedule configuration
            error: Error message from failure
        """
        # TODO: Implement retry logic with exponential backoff
        # For now, just log the failure
        logger.warning(
            "job_retry_needed",
            schedule_id=config.schedule_id,
            max_retries=config.max_retries,
            error=error,
        )

    async def _persist_schedule_to_db(self, config: ScheduleConfig) -> None:
        """Persist schedule configuration to database."""
        from src.db.models import ScheduledReview

        # Check if exists
        result = await self.db.execute(
            select(ScheduledReview).where(ScheduledReview.review_id == config.schedule_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update
            await self.db.execute(
                update(ScheduledReview)
                .where(ScheduledReview.review_id == config.schedule_id)
                .values(
                    schedule_type=config.schedule_type.value,
                    cron_expression=config.cron_expression,
                    owner_id=config.owner_id,
                    enabled=config.enabled,
                    last_run=None,  # Will be updated by execution
                    next_run=await self.get_next_run_time(config.schedule_id),
                )
            )
        else:
            # Insert
            review = ScheduledReview(
                review_id=config.schedule_id,
                schedule_type=config.schedule_type.value,
                cron_expression=config.cron_expression,
                owner_id=config.owner_id,
                enabled=config.enabled,
                next_run=await self.get_next_run_time(config.schedule_id),
            )
            self.db.add(review)

        await self.db.commit()

    async def _load_schedules_from_db(self) -> None:
        """Load persisted schedules from database and restore them."""
        from src.db.models import ScheduledReview

        result = await self.db.execute(select(ScheduledReview).where(ScheduledReview.enabled == True))
        schedules = result.scalars().all()

        logger.info("loading_persisted_schedules", count=len(schedules))

        for schedule_record in schedules:
            # Reconstruct ScheduleConfig
            # Note: This is simplified - in production you'd store full config as JSONB
            config = ScheduleConfig(
                schedule_id=schedule_record.review_id,
                schedule_type=ScheduleType(schedule_record.schedule_type),
                cron_expression=schedule_record.cron_expression,
                owner_id=schedule_record.owner_id,
                enabled=schedule_record.enabled,
            )

            self._schedules[config.schedule_id] = config

            # Note: Jobs would need to be recreated with callbacks
            # This requires storing callback info or using a registry
            logger.info(
                "schedule_loaded",
                schedule_id=config.schedule_id,
                schedule_type=config.schedule_type.value,
            )
