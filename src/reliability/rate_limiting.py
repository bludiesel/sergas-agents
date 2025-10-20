"""
Rate limiting and backpressure handling system.

Provides API rate limiting, queue management, throttling strategies,
and backpressure handling for production reliability.
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import deque
import structlog
import time

logger = structlog.get_logger()


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""
    TOKEN_BUCKET = "token_bucket"      # Token bucket algorithm
    LEAKY_BUCKET = "leaky_bucket"      # Leaky bucket algorithm
    FIXED_WINDOW = "fixed_window"      # Fixed window counter
    SLIDING_WINDOW = "sliding_window"  # Sliding window log


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    name: str
    max_requests: int                  # Maximum requests
    window_seconds: int                # Time window in seconds
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    burst_size: Optional[int] = None   # Maximum burst size
    metadata: Dict[str, Any] = field(default_factory=dict)

    def requests_per_second(self) -> float:
        """Calculate requests per second."""
        return self.max_requests / self.window_seconds


class RateLimiter:
    """
    Multi-strategy rate limiter.

    Supports token bucket, leaky bucket, fixed window, and sliding window algorithms.
    """

    def __init__(self, config: RateLimitConfig):
        """
        Initialize rate limiter.

        Args:
            config: Rate limit configuration
        """
        self.config = config
        self.logger = logger.bind(
            rate_limiter=config.name,
            strategy=config.strategy.value
        )

        # Initialize strategy-specific state
        if config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            self.tokens = float(config.max_requests)
            self.last_refill = time.time()
        elif config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            self.request_log: deque = deque()
        elif config.strategy == RateLimitStrategy.FIXED_WINDOW:
            self.window_start = time.time()
            self.request_count = 0
        elif config.strategy == RateLimitStrategy.LEAKY_BUCKET:
            self.queue: deque = deque()
            self.last_leak = time.time()

        self._lock = asyncio.Lock()

    async def allow_request(self, cost: int = 1) -> tuple[bool, Optional[float]]:
        """
        Check if request is allowed under rate limit.

        Args:
            cost: Request cost (tokens/credits consumed)

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        async with self._lock:
            if self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
                return await self._token_bucket_allow(cost)
            elif self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
                return await self._sliding_window_allow(cost)
            elif self.config.strategy == RateLimitStrategy.FIXED_WINDOW:
                return await self._fixed_window_allow(cost)
            elif self.config.strategy == RateLimitStrategy.LEAKY_BUCKET:
                return await self._leaky_bucket_allow(cost)

            return False, None

    async def _token_bucket_allow(self, cost: int) -> tuple[bool, Optional[float]]:
        """Token bucket algorithm."""
        now = time.time()
        elapsed = now - self.last_refill

        # Refill tokens based on time elapsed
        refill_rate = self.config.max_requests / self.config.window_seconds
        tokens_to_add = elapsed * refill_rate
        self.tokens = min(
            float(self.config.max_requests),
            self.tokens + tokens_to_add
        )
        self.last_refill = now

        # Check if enough tokens available
        if self.tokens >= cost:
            self.tokens -= cost
            self.logger.debug(
                "request_allowed",
                tokens_remaining=self.tokens,
                cost=cost
            )
            return True, None
        else:
            # Calculate retry after time
            tokens_needed = cost - self.tokens
            retry_after = tokens_needed / refill_rate

            self.logger.warning(
                "request_rate_limited",
                tokens_available=self.tokens,
                cost=cost,
                retry_after=retry_after
            )
            return False, retry_after

    async def _sliding_window_allow(self, cost: int) -> tuple[bool, Optional[float]]:
        """Sliding window log algorithm."""
        now = time.time()
        window_start = now - self.config.window_seconds

        # Remove requests outside current window
        while self.request_log and self.request_log[0] < window_start:
            self.request_log.popleft()

        # Check if under limit
        current_count = len(self.request_log)

        if current_count + cost <= self.config.max_requests:
            # Add request timestamps
            for _ in range(cost):
                self.request_log.append(now)

            self.logger.debug(
                "request_allowed",
                current_count=current_count + cost,
                max_requests=self.config.max_requests
            )
            return True, None
        else:
            # Calculate retry after time
            if self.request_log:
                oldest_request = self.request_log[0]
                retry_after = (oldest_request + self.config.window_seconds) - now
            else:
                retry_after = self.config.window_seconds

            self.logger.warning(
                "request_rate_limited",
                current_count=current_count,
                max_requests=self.config.max_requests,
                retry_after=retry_after
            )
            return False, max(0, retry_after)

    async def _fixed_window_allow(self, cost: int) -> tuple[bool, Optional[float]]:
        """Fixed window counter algorithm."""
        now = time.time()

        # Check if we need to reset the window
        if now >= self.window_start + self.config.window_seconds:
            self.window_start = now
            self.request_count = 0

        # Check if under limit
        if self.request_count + cost <= self.config.max_requests:
            self.request_count += cost
            self.logger.debug(
                "request_allowed",
                current_count=self.request_count,
                max_requests=self.config.max_requests
            )
            return True, None
        else:
            retry_after = (self.window_start + self.config.window_seconds) - now

            self.logger.warning(
                "request_rate_limited",
                current_count=self.request_count,
                max_requests=self.config.max_requests,
                retry_after=retry_after
            )
            return False, max(0, retry_after)

    async def _leaky_bucket_allow(self, cost: int) -> tuple[bool, Optional[float]]:
        """Leaky bucket algorithm."""
        now = time.time()
        elapsed = now - self.last_leak

        # Leak requests from bucket
        leak_rate = self.config.max_requests / self.config.window_seconds
        leaks = int(elapsed * leak_rate)

        for _ in range(min(leaks, len(self.queue))):
            self.queue.popleft()

        self.last_leak = now

        # Check if bucket has space
        bucket_size = self.config.burst_size or self.config.max_requests
        if len(self.queue) + cost <= bucket_size:
            for _ in range(cost):
                self.queue.append(now)

            self.logger.debug(
                "request_allowed",
                queue_size=len(self.queue),
                bucket_size=bucket_size
            )
            return True, None
        else:
            retry_after = len(self.queue) / leak_rate

            self.logger.warning(
                "request_rate_limited",
                queue_size=len(self.queue),
                bucket_size=bucket_size,
                retry_after=retry_after
            )
            return False, retry_after

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get rate limiter metrics.

        Returns:
            Metrics dictionary
        """
        metrics = {
            "name": self.config.name,
            "strategy": self.config.strategy.value,
            "max_requests": self.config.max_requests,
            "window_seconds": self.config.window_seconds,
            "requests_per_second": self.config.requests_per_second(),
        }

        if self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            metrics["tokens_available"] = self.tokens
            metrics["utilization_percent"] = (
                (1 - self.tokens / self.config.max_requests) * 100
            )
        elif self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            metrics["current_requests"] = len(self.request_log)
            metrics["utilization_percent"] = (
                len(self.request_log) / self.config.max_requests * 100
            )
        elif self.config.strategy == RateLimitStrategy.FIXED_WINDOW:
            metrics["current_requests"] = self.request_count
            metrics["utilization_percent"] = (
                self.request_count / self.config.max_requests * 100
            )
        elif self.config.strategy == RateLimitStrategy.LEAKY_BUCKET:
            metrics["queue_size"] = len(self.queue)
            bucket_size = self.config.burst_size or self.config.max_requests
            metrics["utilization_percent"] = (
                len(self.queue) / bucket_size * 100
            )

        return metrics

    async def reset(self):
        """Reset rate limiter state."""
        async with self._lock:
            if self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
                self.tokens = float(self.config.max_requests)
                self.last_refill = time.time()
            elif self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
                self.request_log.clear()
            elif self.config.strategy == RateLimitStrategy.FIXED_WINDOW:
                self.window_start = time.time()
                self.request_count = 0
            elif self.config.strategy == RateLimitStrategy.LEAKY_BUCKET:
                self.queue.clear()
                self.last_leak = time.time()

            self.logger.info("rate_limiter_reset")


class QueueManager:
    """
    Queue manager for asynchronous request processing.

    Manages request queues with priority, timeout, and backpressure handling.
    """

    def __init__(
        self,
        name: str,
        max_size: int = 1000,
        max_workers: int = 10,
        timeout: float = 30.0
    ):
        """
        Initialize queue manager.

        Args:
            name: Queue identifier
            max_size: Maximum queue size
            max_workers: Maximum concurrent workers
            timeout: Request timeout in seconds
        """
        self.name = name
        self.max_size = max_size
        self.max_workers = max_workers
        self.timeout = timeout

        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self.workers: List[asyncio.Task] = []
        self.running = False

        self.processed_count = 0
        self.failed_count = 0
        self.timeout_count = 0

        self.logger = logger.bind(queue_manager=name)

    async def enqueue(
        self,
        func: Callable,
        *args,
        priority: int = 0,
        **kwargs
    ) -> bool:
        """
        Add request to queue.

        Args:
            func: Async function to execute
            *args: Positional arguments
            priority: Priority level (lower = higher priority)
            **kwargs: Keyword arguments

        Returns:
            True if enqueued successfully
        """
        try:
            # Check if queue is full
            if self.queue.full():
                self.logger.warning(
                    "queue_full",
                    size=self.queue.qsize(),
                    max_size=self.max_size
                )
                return False

            # Create work item
            item = {
                "func": func,
                "args": args,
                "kwargs": kwargs,
                "priority": priority,
                "enqueued_at": time.time()
            }

            await self.queue.put(item)

            self.logger.debug(
                "request_enqueued",
                queue_size=self.queue.qsize(),
                priority=priority
            )

            return True

        except asyncio.QueueFull:
            self.logger.warning("queue_full_rejected")
            return False

    async def start(self):
        """Start processing queue."""
        if self.running:
            self.logger.warning("queue_already_running")
            return

        self.running = True

        # Start worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)

        self.logger.info(
            "queue_started",
            workers=self.max_workers,
            max_size=self.max_size
        )

    async def stop(self):
        """Stop processing queue."""
        if not self.running:
            return

        self.running = False

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)

        self.workers.clear()

        self.logger.info("queue_stopped")

    async def _worker(self, worker_id: int):
        """Queue worker task."""
        self.logger.info("worker_started", worker_id=worker_id)

        while self.running:
            try:
                # Get work item with timeout
                item = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )

                # Check if item has timed out
                enqueued_at = item["enqueued_at"]
                wait_time = time.time() - enqueued_at

                if wait_time > self.timeout:
                    self.timeout_count += 1
                    self.logger.warning(
                        "request_timeout",
                        worker_id=worker_id,
                        wait_time=wait_time
                    )
                    continue

                # Execute work item
                try:
                    func = item["func"]
                    args = item["args"]
                    kwargs = item["kwargs"]

                    await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=self.timeout
                    )

                    self.processed_count += 1

                    self.logger.debug(
                        "request_processed",
                        worker_id=worker_id,
                        wait_time=wait_time
                    )

                except asyncio.TimeoutError:
                    self.timeout_count += 1
                    self.logger.warning(
                        "request_execution_timeout",
                        worker_id=worker_id
                    )

                except Exception as e:
                    self.failed_count += 1
                    self.logger.error(
                        "request_failed",
                        worker_id=worker_id,
                        error=str(e)
                    )

            except asyncio.TimeoutError:
                # Queue get timeout - continue
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    "worker_error",
                    worker_id=worker_id,
                    error=str(e)
                )

        self.logger.info("worker_stopped", worker_id=worker_id)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get queue metrics.

        Returns:
            Metrics dictionary
        """
        queue_size = self.queue.qsize()
        utilization = queue_size / self.max_size * 100

        return {
            "name": self.name,
            "queue_size": queue_size,
            "max_size": self.max_size,
            "utilization_percent": utilization,
            "active_workers": len(self.workers),
            "max_workers": self.max_workers,
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "timeout_count": self.timeout_count,
            "running": self.running,
        }


class ThrottlingStrategy:
    """
    Adaptive throttling based on system load.

    Automatically adjusts rate limits based on system metrics.
    """

    def __init__(
        self,
        name: str,
        base_rate_limiter: RateLimiter,
        min_reduction: float = 0.5,
        max_reduction: float = 0.1
    ):
        """
        Initialize throttling strategy.

        Args:
            name: Strategy identifier
            base_rate_limiter: Base rate limiter
            min_reduction: Minimum reduction factor (50%)
            max_reduction: Maximum reduction factor (10%)
        """
        self.name = name
        self.base_rate_limiter = base_rate_limiter
        self.min_reduction = min_reduction
        self.max_reduction = max_reduction

        self.current_multiplier = 1.0
        self.logger = logger.bind(throttling_strategy=name)

    async def adjust_for_load(self, load_percent: float):
        """
        Adjust throttling based on system load.

        Args:
            load_percent: System load percentage (0-100)
        """
        if load_percent < 50:
            # Low load - full rate
            new_multiplier = 1.0
        elif load_percent < 70:
            # Moderate load - slight reduction
            new_multiplier = 0.8
        elif load_percent < 85:
            # High load - significant reduction
            new_multiplier = 0.6
        else:
            # Critical load - maximum reduction
            new_multiplier = self.max_reduction

        if new_multiplier != self.current_multiplier:
            self.current_multiplier = new_multiplier

            self.logger.warning(
                "throttling_adjusted",
                load_percent=load_percent,
                multiplier=new_multiplier
            )

    def get_adjusted_limit(self) -> int:
        """
        Get adjusted rate limit.

        Returns:
            Adjusted max requests
        """
        return int(
            self.base_rate_limiter.config.max_requests * self.current_multiplier
        )


class BackpressureHandler:
    """
    Backpressure handling for overloaded systems.

    Implements various backpressure strategies to prevent system overload.
    """

    def __init__(
        self,
        name: str,
        queue_manager: QueueManager,
        rate_limiter: RateLimiter,
        alert_threshold: float = 0.8
    ):
        """
        Initialize backpressure handler.

        Args:
            name: Handler identifier
            queue_manager: Queue manager instance
            rate_limiter: Rate limiter instance
            alert_threshold: Alert when queue utilization exceeds this (0-1)
        """
        self.name = name
        self.queue_manager = queue_manager
        self.rate_limiter = rate_limiter
        self.alert_threshold = alert_threshold

        self.backpressure_active = False
        self.logger = logger.bind(backpressure_handler=name)

    async def check_and_apply_backpressure(self) -> bool:
        """
        Check system state and apply backpressure if needed.

        Returns:
            True if backpressure is active
        """
        metrics = self.queue_manager.get_metrics()
        utilization = metrics["utilization_percent"] / 100

        if utilization >= self.alert_threshold:
            if not self.backpressure_active:
                self.backpressure_active = True
                self.logger.warning(
                    "backpressure_activated",
                    queue_utilization=utilization,
                    threshold=self.alert_threshold
                )

                # Apply backpressure strategies
                await self._apply_backpressure()

        else:
            if self.backpressure_active:
                self.backpressure_active = False
                self.logger.info(
                    "backpressure_deactivated",
                    queue_utilization=utilization
                )

                # Remove backpressure
                await self._remove_backpressure()

        return self.backpressure_active

    async def _apply_backpressure(self):
        """Apply backpressure strategies."""
        # Reduce rate limit
        current_limit = self.rate_limiter.config.max_requests
        reduced_limit = int(current_limit * 0.5)

        self.logger.info(
            "reducing_rate_limit",
            from_limit=current_limit,
            to_limit=reduced_limit
        )

        # Note: Would need to update rate limiter config
        # This is a simplified example

    async def _remove_backpressure(self):
        """Remove backpressure strategies."""
        self.logger.info("restoring_normal_rate_limits")

        # Note: Would restore original rate limiter config
        # This is a simplified example

    def get_status(self) -> Dict[str, Any]:
        """
        Get backpressure status.

        Returns:
            Status dictionary
        """
        queue_metrics = self.queue_manager.get_metrics()
        rate_metrics = self.rate_limiter.get_metrics()

        return {
            "name": self.name,
            "backpressure_active": self.backpressure_active,
            "alert_threshold": self.alert_threshold,
            "queue_utilization": queue_metrics["utilization_percent"] / 100,
            "rate_utilization": rate_metrics["utilization_percent"] / 100,
            "queue_size": queue_metrics["queue_size"],
            "processed_count": queue_metrics["processed_count"],
            "failed_count": queue_metrics["failed_count"],
        }
