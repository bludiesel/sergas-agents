"""
Sync scheduler for automated Cognee sync operations.

Provides scheduled sync operations with:
- Hourly incremental sync
- Nightly full sync
- On-demand sync triggers
- APScheduler integration
- Error handling and alerting
- Monitoring and logging
"""

import asyncio
from datetime import datetime, time
from typing import Optional, Callable, Dict, Any, List
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.events import (
    EVENT_JOB_EXECUTED,
    EVENT_JOB_ERROR,
    EVENT_JOB_MISSED,
    JobExecutionEvent,
)

from src.sync.cognee_sync_pipeline import CogneeSyncPipeline
from src.models.sync.sync_models import SyncType, SyncSummary

logger = structlog.get_logger(__name__)


class SyncScheduler:
    """
    Scheduler for automated Cognee sync operations.

    Features:
    - Hourly incremental sync
    - Nightly full sync at configurable time
    - On-demand sync triggers
    - Job monitoring and error handling
    - Configurable schedules

    Example:
        >>> scheduler = SyncScheduler(
        ...     pipeline=pipeline,
        ...     hourly_incremental=True,
        ...     nightly_full_time="02:00"
        ... )
        >>> await scheduler.start()
        >>> # Scheduler runs automatically
        >>> await scheduler.stop()
    """

    def __init__(
        self,
        pipeline: CogneeSyncPipeline,
        hourly_incremental: bool = True,
        nightly_full_time: str = "02:00",
        timezone: str = "UTC",
        on_sync_complete: Optional[Callable[[SyncSummary], None]] = None,
        on_sync_error: Optional[Callable[[Exception], None]] = None,
    ) -> None:
        """
        Initialize sync scheduler.

        Args:
            pipeline: CogneeSyncPipeline instance
            hourly_incremental: Enable hourly incremental sync
            nightly_full_time: Time for nightly full sync (HH:MM format)
            timezone: Timezone for scheduled jobs
            on_sync_complete: Callback for successful sync completion
            on_sync_error: Callback for sync errors
        """
        self.pipeline = pipeline
        self.hourly_incremental = hourly_incremental
        self.nightly_full_time = nightly_full_time
        self.timezone = timezone
        self.on_sync_complete = on_sync_complete
        self.on_sync_error = on_sync_error

        self.logger = logger.bind(component="sync_scheduler")

        # APScheduler setup
        self.scheduler = AsyncIOScheduler(timezone=timezone)
        self._running = False
        self._job_history: List[Dict[str, Any]] = []

        # Job IDs
        self.incremental_job_id = "hourly_incremental_sync"
        self.full_sync_job_id = "nightly_full_sync"

    async def start(self) -> None:
        """
        Start the sync scheduler.

        Sets up scheduled jobs and starts APScheduler.

        Raises:
            RuntimeError: If scheduler is already running
        """
        if self._running:
            raise RuntimeError("Scheduler is already running")

        # Setup event listeners
        self.scheduler.add_listener(
            self._on_job_executed,
            EVENT_JOB_EXECUTED,
        )
        self.scheduler.add_listener(
            self._on_job_error,
            EVENT_JOB_ERROR,
        )
        self.scheduler.add_listener(
            self._on_job_missed,
            EVENT_JOB_MISSED,
        )

        # Schedule jobs
        if self.hourly_incremental:
            self._schedule_hourly_incremental()

        self._schedule_nightly_full()

        # Start scheduler
        self.scheduler.start()
        self._running = True

        self.logger.info(
            "scheduler_started",
            hourly_incremental=self.hourly_incremental,
            nightly_full_time=self.nightly_full_time,
            timezone=self.timezone,
        )

    async def stop(self, wait: bool = True) -> None:
        """
        Stop the sync scheduler.

        Args:
            wait: Wait for running jobs to complete before stopping
        """
        if not self._running:
            self.logger.warning("scheduler_not_running")
            return

        if wait:
            self.logger.info("stopping_scheduler_waiting_for_jobs")
        else:
            self.logger.info("stopping_scheduler_immediately")

        self.scheduler.shutdown(wait=wait)
        self._running = False

        self.logger.info("scheduler_stopped")

    def _schedule_hourly_incremental(self) -> None:
        """Schedule hourly incremental sync job."""
        # Run every hour at minute 0
        trigger = IntervalTrigger(hours=1, timezone=self.timezone)

        self.scheduler.add_job(
            func=self._run_incremental_sync,
            trigger=trigger,
            id=self.incremental_job_id,
            name="Hourly Incremental Sync",
            replace_existing=True,
            max_instances=1,  # Prevent overlapping runs
        )

        self.logger.info(
            "scheduled_hourly_incremental",
            job_id=self.incremental_job_id,
        )

    def _schedule_nightly_full(self) -> None:
        """Schedule nightly full sync job."""
        # Parse time string
        hour, minute = map(int, self.nightly_full_time.split(":"))

        # Run daily at specified time
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            timezone=self.timezone,
        )

        self.scheduler.add_job(
            func=self._run_full_sync,
            trigger=trigger,
            id=self.full_sync_job_id,
            name="Nightly Full Sync",
            replace_existing=True,
            max_instances=1,
        )

        self.logger.info(
            "scheduled_nightly_full",
            job_id=self.full_sync_job_id,
            time=self.nightly_full_time,
        )

    async def _run_incremental_sync(self) -> SyncSummary:
        """
        Execute hourly incremental sync.

        Returns:
            SyncSummary from the sync operation
        """
        self.logger.info("starting_scheduled_incremental_sync")

        try:
            summary = await self.pipeline.sync_accounts(
                sync_type=SyncType.INCREMENTAL,
            )

            self.logger.info(
                "scheduled_incremental_sync_completed",
                session_id=summary.session_id,
                total=summary.total_records,
                successful=summary.successful_records,
                failed=summary.failed_records,
            )

            # Trigger callback if set
            if self.on_sync_complete:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.on_sync_complete, summary
                    )
                except Exception as e:
                    self.logger.error("sync_complete_callback_failed", error=str(e))

            return summary

        except Exception as e:
            self.logger.error(
                "scheduled_incremental_sync_failed",
                error=str(e),
                error_type=type(e).__name__,
            )

            # Trigger error callback if set
            if self.on_sync_error:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.on_sync_error, e
                    )
                except Exception as callback_error:
                    self.logger.error("sync_error_callback_failed", error=str(callback_error))

            raise

    async def _run_full_sync(self) -> SyncSummary:
        """
        Execute nightly full sync.

        Returns:
            SyncSummary from the sync operation
        """
        self.logger.info("starting_scheduled_full_sync")

        try:
            summary = await self.pipeline.sync_accounts(
                sync_type=SyncType.FULL,
            )

            self.logger.info(
                "scheduled_full_sync_completed",
                session_id=summary.session_id,
                total=summary.total_records,
                successful=summary.successful_records,
                failed=summary.failed_records,
                duration=summary.duration_seconds,
            )

            # Trigger callback if set
            if self.on_sync_complete:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.on_sync_complete, summary
                    )
                except Exception as e:
                    self.logger.error("sync_complete_callback_failed", error=str(e))

            return summary

        except Exception as e:
            self.logger.error(
                "scheduled_full_sync_failed",
                error=str(e),
                error_type=type(e).__name__,
            )

            # Trigger error callback if set
            if self.on_sync_error:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.on_sync_error, e
                    )
                except Exception as callback_error:
                    self.logger.error("sync_error_callback_failed", error=str(callback_error))

            raise

    async def trigger_on_demand_sync(
        self,
        account_ids: Optional[List[str]] = None,
        sync_type: SyncType = SyncType.ON_DEMAND,
        delay_seconds: int = 0,
    ) -> str:
        """
        Trigger an on-demand sync operation.

        Args:
            account_ids: Specific account IDs to sync (for ON_DEMAND type)
            sync_type: Type of sync (ON_DEMAND, INCREMENTAL, or FULL)
            delay_seconds: Delay before starting sync

        Returns:
            Job ID for the triggered sync

        Raises:
            ValueError: If account_ids not provided for ON_DEMAND sync
        """
        if sync_type == SyncType.ON_DEMAND and not account_ids:
            raise ValueError("account_ids required for on-demand sync")

        job_id = f"on_demand_sync_{datetime.utcnow().timestamp()}"

        async def run_on_demand():
            self.logger.info(
                "starting_on_demand_sync",
                job_id=job_id,
                sync_type=sync_type.value,
                account_count=len(account_ids) if account_ids else None,
            )

            try:
                summary = await self.pipeline.sync_accounts(
                    sync_type=sync_type,
                    account_ids=account_ids,
                )

                self.logger.info(
                    "on_demand_sync_completed",
                    job_id=job_id,
                    session_id=summary.session_id,
                    total=summary.total_records,
                    successful=summary.successful_records,
                )

                if self.on_sync_complete:
                    try:
                        await asyncio.get_event_loop().run_in_executor(
                            None, self.on_sync_complete, summary
                        )
                    except Exception as e:
                        self.logger.error("sync_complete_callback_failed", error=str(e))

                return summary

            except Exception as e:
                self.logger.error(
                    "on_demand_sync_failed",
                    job_id=job_id,
                    error=str(e),
                )

                if self.on_sync_error:
                    try:
                        await asyncio.get_event_loop().run_in_executor(
                            None, self.on_sync_error, e
                        )
                    except Exception as callback_error:
                        self.logger.error("sync_error_callback_failed", error=str(callback_error))

                raise

        # Schedule job
        if delay_seconds > 0:
            run_at = datetime.utcnow().timestamp() + delay_seconds
            trigger = DateTrigger(run_date=datetime.fromtimestamp(run_at))
        else:
            trigger = None  # Run immediately

        self.scheduler.add_job(
            func=run_on_demand,
            trigger=trigger,
            id=job_id,
            name=f"On-Demand Sync ({sync_type.value})",
            replace_existing=False,
        )

        self.logger.info(
            "on_demand_sync_scheduled",
            job_id=job_id,
            delay_seconds=delay_seconds,
        )

        return job_id

    def _on_job_executed(self, event: JobExecutionEvent) -> None:
        """Handle successful job execution event."""
        self._job_history.append({
            "job_id": event.job_id,
            "event": "executed",
            "timestamp": datetime.utcnow(),
            "return_value": str(event.retval) if event.retval else None,
        })

        self.logger.info(
            "job_executed",
            job_id=event.job_id,
        )

    def _on_job_error(self, event: JobExecutionEvent) -> None:
        """Handle job execution error event."""
        self._job_history.append({
            "job_id": event.job_id,
            "event": "error",
            "timestamp": datetime.utcnow(),
            "exception": str(event.exception),
        })

        self.logger.error(
            "job_execution_error",
            job_id=event.job_id,
            exception=str(event.exception),
        )

    def _on_job_missed(self, event: JobExecutionEvent) -> None:
        """Handle missed job execution event."""
        self._job_history.append({
            "job_id": event.job_id,
            "event": "missed",
            "timestamp": datetime.utcnow(),
        })

        self.logger.warning(
            "job_missed",
            job_id=event.job_id,
        )

    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """
        Get list of scheduled jobs.

        Returns:
            List of job information dictionaries
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            })

        return jobs

    def get_job_history(
        self,
        limit: int = 100,
        job_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get job execution history.

        Args:
            limit: Maximum number of history entries
            job_id: Filter by specific job ID

        Returns:
            List of job history entries
        """
        history = self._job_history

        if job_id:
            history = [h for h in history if h["job_id"] == job_id]

        # Return most recent entries
        return sorted(
            history,
            key=lambda x: x["timestamp"],
            reverse=True,
        )[:limit]

    def pause_job(self, job_id: str) -> bool:
        """
        Pause a scheduled job.

        Args:
            job_id: Job ID to pause

        Returns:
            True if paused successfully, False if job not found
        """
        try:
            self.scheduler.pause_job(job_id)
            self.logger.info("job_paused", job_id=job_id)
            return True
        except Exception as e:
            self.logger.warning("job_pause_failed", job_id=job_id, error=str(e))
            return False

    def resume_job(self, job_id: str) -> bool:
        """
        Resume a paused job.

        Args:
            job_id: Job ID to resume

        Returns:
            True if resumed successfully, False if job not found
        """
        try:
            self.scheduler.resume_job(job_id)
            self.logger.info("job_resumed", job_id=job_id)
            return True
        except Exception as e:
            self.logger.warning("job_resume_failed", job_id=job_id, error=str(e))
            return False

    def remove_job(self, job_id: str) -> bool:
        """
        Remove a scheduled job.

        Args:
            job_id: Job ID to remove

        Returns:
            True if removed successfully, False if job not found
        """
        try:
            self.scheduler.remove_job(job_id)
            self.logger.info("job_removed", job_id=job_id)
            return True
        except Exception as e:
            self.logger.warning("job_remove_failed", job_id=job_id, error=str(e))
            return False

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running

    def get_status(self) -> Dict[str, Any]:
        """
        Get scheduler status information.

        Returns:
            Dictionary with scheduler status
        """
        return {
            "running": self._running,
            "scheduled_jobs": len(self.scheduler.get_jobs()),
            "job_history_count": len(self._job_history),
            "hourly_incremental_enabled": self.hourly_incremental,
            "nightly_full_time": self.nightly_full_time,
            "timezone": self.timezone,
        }
