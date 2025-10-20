"""Event-driven webhook processor for Cognee updates with retry logic.

Processes webhook events from Redis queue with:
- Event-driven Cognee updates
- Batch processing for efficiency
- Dead letter queue for failed events
- Exponential backoff retry strategy
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum

import structlog
from redis.asyncio import Redis
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from src.services.memory_service import MemoryService

logger = structlog.get_logger(__name__)


class ProcessingStatus(str, Enum):
    """Event processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class WebhookProcessor:
    """Async webhook event processor with retry logic.

    Features:
    - Async event processing from Redis queue
    - Batch processing for efficiency (configurable batch size)
    - Exponential backoff retry (3 attempts)
    - Dead letter queue for failed events
    - Cognee memory synchronization
    - Comprehensive error handling

    Example:
        >>> processor = WebhookProcessor(redis, memory_service)
        >>> await processor.start()
        >>> # Processes events continuously
    """

    def __init__(
        self,
        redis_client: Redis,
        memory_service: MemoryService,
        batch_size: int = 10,
        batch_timeout: int = 5,
        max_retries: int = 3,
        retry_delay_base: int = 2
    ):
        """Initialize webhook processor.

        Args:
            redis_client: Redis client for queue access
            memory_service: Memory service for Cognee updates
            batch_size: Number of events to process in batch
            batch_timeout: Seconds to wait for batch to fill
            max_retries: Maximum retry attempts per event
            retry_delay_base: Base delay for exponential backoff (seconds)
        """
        self.redis = redis_client
        self.memory = memory_service
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.max_retries = max_retries
        self.retry_delay_base = retry_delay_base
        self.logger = logger.bind(component="webhook_processor")

        self._running = False
        self._worker_tasks: List[asyncio.Task] = []

        # Processing metrics
        self._metrics = {
            "events_processed": 0,
            "events_succeeded": 0,
            "events_failed": 0,
            "events_retried": 0,
            "events_dead_letter": 0,
            "batches_processed": 0,
            "average_processing_time": 0.0,
            "last_processed": None
        }

    async def start(self, num_workers: int = 3) -> None:
        """Start event processing workers.

        Args:
            num_workers: Number of concurrent worker tasks
        """
        if self._running:
            self.logger.warning("processor_already_running")
            return

        self._running = True
        self.logger.info("starting_webhook_processor", num_workers=num_workers)

        # Start worker tasks
        for i in range(num_workers):
            task = asyncio.create_task(self._worker(worker_id=i))
            self._worker_tasks.append(task)

        self.logger.info("webhook_processor_started", workers=num_workers)

    async def stop(self) -> None:
        """Stop event processing gracefully."""
        self.logger.info("stopping_webhook_processor")
        self._running = False

        # Wait for workers to finish current batches
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
            self._worker_tasks.clear()

        self.logger.info("webhook_processor_stopped")

    async def _worker(self, worker_id: int) -> None:
        """Event processing worker.

        Args:
            worker_id: Worker identifier
        """
        worker_logger = self.logger.bind(worker_id=worker_id)
        worker_logger.info("worker_started")

        while self._running:
            try:
                # Get batch of events
                events = await self._get_event_batch()

                if not events:
                    # No events available, wait briefly
                    await asyncio.sleep(1)
                    continue

                # Process batch
                await self._process_batch(events, worker_logger)

            except Exception as e:
                worker_logger.error("worker_error", error=str(e))
                await asyncio.sleep(5)  # Wait before retrying

        worker_logger.info("worker_stopped")

    async def _get_event_batch(self) -> List[Dict[str, Any]]:
        """Get batch of events from queue.

        Returns:
            List of event dicts
        """
        events = []

        try:
            # Get events with timeout
            for _ in range(self.batch_size):
                result = await self.redis.brpop(
                    "webhook:queue",
                    timeout=self.batch_timeout
                )

                if result:
                    _, event_json = result
                    event = json.loads(event_json)
                    events.append(event)
                else:
                    # Timeout reached
                    break

        except Exception as e:
            self.logger.error("get_event_batch_failed", error=str(e))

        return events

    async def _process_batch(
        self,
        events: List[Dict[str, Any]],
        worker_logger: Any
    ) -> None:
        """Process batch of events.

        Args:
            events: List of event dicts
            worker_logger: Logger with worker context
        """
        batch_start = datetime.utcnow()
        worker_logger.info("processing_batch", batch_size=len(events))

        # Process events concurrently
        tasks = [
            self._process_event(event)
            for event in events
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Update metrics
        succeeded = sum(1 for r in results if r is True)
        failed = sum(1 for r in results if r is not True)

        self._metrics["batches_processed"] += 1
        self._metrics["events_processed"] += len(events)
        self._metrics["events_succeeded"] += succeeded
        self._metrics["events_failed"] += failed
        self._metrics["last_processed"] = datetime.utcnow().isoformat()

        # Update average processing time
        duration = (datetime.utcnow() - batch_start).total_seconds()
        current_avg = self._metrics["average_processing_time"]
        total_batches = self._metrics["batches_processed"]
        self._metrics["average_processing_time"] = (
            (current_avg * (total_batches - 1) + duration) / total_batches
        )

        worker_logger.info(
            "batch_processed",
            succeeded=succeeded,
            failed=failed,
            duration_seconds=duration
        )

    async def _process_event(self, event: Dict[str, Any]) -> bool:
        """Process single webhook event with retry logic.

        Args:
            event: Event dict

        Returns:
            True if processing succeeded
        """
        event_id = event.get("event_id", "unknown")
        event_type = event.get("event_type", "unknown")
        module = event.get("module", "unknown")
        record_id = event.get("record_id", "")

        self.logger.info(
            "processing_event",
            event_id=event_id,
            event_type=event_type,
            module=module,
            record_id=record_id
        )

        try:
            # Process event with retry
            await self._process_with_retry(event)

            self.logger.info("event_processed_successfully", event_id=event_id)
            return True

        except Exception as e:
            self.logger.error(
                "event_processing_failed",
                event_id=event_id,
                error=str(e)
            )

            # Move to dead letter queue
            await self._move_to_dead_letter(event, str(e))
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type(Exception)
    )
    async def _process_with_retry(self, event: Dict[str, Any]) -> None:
        """Process event with retry logic.

        Args:
            event: Event dict

        Raises:
            Exception: If processing fails after retries
        """
        event_type = event.get("event_type")
        module = event.get("module")
        record_id = event.get("record_id")
        record_data = event.get("record_data", {})

        # Track retry attempts
        self._metrics["events_retried"] += 1

        # Route based on event type
        if event_type == "create":
            await self._handle_create(module, record_id, record_data)
        elif event_type == "update":
            await self._handle_update(module, record_id, record_data, event.get("modified_fields", []))
        elif event_type == "delete":
            await self._handle_delete(module, record_id)
        elif event_type == "restore":
            await self._handle_restore(module, record_id, record_data)
        else:
            self.logger.warning("unknown_event_type", event_type=event_type)

    async def _handle_create(
        self,
        module: str,
        record_id: str,
        record_data: Dict[str, Any]
    ) -> None:
        """Handle record creation event.

        Args:
            module: Zoho module
            record_id: Record identifier
            record_data: Record data
        """
        self.logger.info("handling_create", module=module, record_id=record_id)

        if module == "Accounts":
            # Sync new account to memory
            await self.memory.sync_account_to_memory(record_id, force=True)

        elif module == "Contacts":
            # Update account context with new contact
            account_id = record_data.get("Account_Name", {}).get("id")
            if account_id:
                await self.memory.sync_account_to_memory(account_id, force=True)

        elif module == "Deals":
            # Update account context with new deal
            account_id = record_data.get("Account_Name", {}).get("id")
            if account_id:
                await self.memory.sync_account_to_memory(account_id, force=True)

        elif module == "Activities" or module == "Tasks":
            # Update account activity timeline
            account_id = record_data.get("What_Id", {}).get("id")
            if account_id:
                await self.memory.sync_account_to_memory(account_id, force=True)

        elif module == "Notes":
            # Update account notes
            parent_id = record_data.get("Parent_Id", {}).get("id")
            if parent_id:
                await self.memory.sync_account_to_memory(parent_id, force=True)

    async def _handle_update(
        self,
        module: str,
        record_id: str,
        record_data: Dict[str, Any],
        modified_fields: List[str]
    ) -> None:
        """Handle record update event.

        Args:
            module: Zoho module
            record_id: Record identifier
            record_data: Updated record data
            modified_fields: List of modified field names
        """
        self.logger.info(
            "handling_update",
            module=module,
            record_id=record_id,
            modified_fields=modified_fields
        )

        if module == "Accounts":
            # Check if critical fields changed
            critical_fields = {
                "Account_Status", "Health_Score", "Owner",
                "Annual_Revenue", "Account_Type", "Industry"
            }

            has_critical_changes = any(
                field in modified_fields
                for field in critical_fields
            )

            # Always sync if critical fields changed, otherwise debounce
            await self.memory.sync_account_to_memory(
                record_id,
                force=has_critical_changes
            )

        elif module in {"Contacts", "Deals", "Activities", "Tasks", "Notes"}:
            # Get associated account and sync
            account_id = self._extract_account_id(module, record_data)
            if account_id:
                await self.memory.sync_account_to_memory(account_id, force=True)

    async def _handle_delete(self, module: str, record_id: str) -> None:
        """Handle record deletion event.

        Args:
            module: Zoho module
            record_id: Record identifier
        """
        self.logger.info("handling_delete", module=module, record_id=record_id)

        # Mark record as deleted in memory
        # Implementation depends on Cognee capabilities
        # For now, we'll log the deletion
        self.logger.warning("delete_event_received", module=module, record_id=record_id)

    async def _handle_restore(
        self,
        module: str,
        record_id: str,
        record_data: Dict[str, Any]
    ) -> None:
        """Handle record restoration event.

        Args:
            module: Zoho module
            record_id: Record identifier
            record_data: Restored record data
        """
        self.logger.info("handling_restore", module=module, record_id=record_id)

        # Treat restore like create
        await self._handle_create(module, record_id, record_data)

    def _extract_account_id(
        self,
        module: str,
        record_data: Dict[str, Any]
    ) -> Optional[str]:
        """Extract account ID from record data.

        Args:
            module: Zoho module
            record_data: Record data

        Returns:
            Account ID if found
        """
        if module == "Contacts":
            account_ref = record_data.get("Account_Name", {})
            return account_ref.get("id") if isinstance(account_ref, dict) else None

        elif module == "Deals":
            account_ref = record_data.get("Account_Name", {})
            return account_ref.get("id") if isinstance(account_ref, dict) else None

        elif module in {"Activities", "Tasks"}:
            what_id = record_data.get("What_Id", {})
            # Check if What_Id refers to an Account
            if isinstance(what_id, dict) and what_id.get("module") == "Accounts":
                return what_id.get("id")
            return None

        elif module == "Notes":
            parent = record_data.get("Parent_Id", {})
            # Check if parent is an Account
            if isinstance(parent, dict) and parent.get("module") == "Accounts":
                return parent.get("id")
            return None

        return None

    async def _move_to_dead_letter(
        self,
        event: Dict[str, Any],
        error: str
    ) -> None:
        """Move failed event to dead letter queue.

        Args:
            event: Failed event
            error: Error message
        """
        try:
            event_id = event.get("event_id", "unknown")

            dead_letter_entry = {
                "event": event,
                "error": error,
                "failed_at": datetime.utcnow().isoformat(),
                "retry_count": self.max_retries
            }

            # Store in dead letter queue
            await self.redis.lpush(
                "webhook:dead_letter",
                json.dumps(dead_letter_entry)
            )

            # Set expiry (keep for 7 days)
            await self.redis.expire("webhook:dead_letter", 604800)

            self._metrics["events_dead_letter"] += 1

            self.logger.warning(
                "event_moved_to_dead_letter",
                event_id=event_id,
                error=error
            )

        except Exception as e:
            self.logger.error("dead_letter_move_failed", error=str(e))

    async def get_metrics(self) -> Dict[str, Any]:
        """Get processing metrics.

        Returns:
            Metrics dict
        """
        try:
            queue_size = await self.redis.llen("webhook:queue")
            dead_letter_size = await self.redis.llen("webhook:dead_letter")
        except Exception:
            queue_size = -1
            dead_letter_size = -1

        return {
            **self._metrics,
            "current_queue_size": queue_size,
            "dead_letter_queue_size": dead_letter_size,
            "workers_running": len(self._worker_tasks),
            "processor_running": self._running,
            "success_rate": (
                f"{(self._metrics['events_succeeded'] / self._metrics['events_processed'] * 100):.1f}%"
                if self._metrics['events_processed'] > 0 else "0.0%"
            ),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def reprocess_dead_letter(
        self,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Reprocess events from dead letter queue.

        Args:
            limit: Maximum events to reprocess

        Returns:
            Reprocessing results
        """
        self.logger.info("reprocessing_dead_letter", limit=limit)

        results = {
            "attempted": 0,
            "succeeded": 0,
            "failed": 0
        }

        for _ in range(limit):
            try:
                # Get event from dead letter queue
                result = await self.redis.rpop("webhook:dead_letter")
                if not result:
                    break

                dead_letter_entry = json.loads(result)
                event = dead_letter_entry["event"]

                results["attempted"] += 1

                # Retry processing
                if await self._process_event(event):
                    results["succeeded"] += 1
                else:
                    results["failed"] += 1

            except Exception as e:
                self.logger.error("dead_letter_reprocess_error", error=str(e))
                results["failed"] += 1

        self.logger.info("dead_letter_reprocessing_completed", results=results)
        return results
