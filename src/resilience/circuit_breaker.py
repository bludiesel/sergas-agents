"""
Circuit breaker pattern implementation.

Prevents cascade failures by monitoring error rates and
automatically opening the circuit when threshold exceeded.
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any, Optional
import asyncio
from collections import deque
import structlog
from .exceptions import CircuitBreakerOpenError

logger = structlog.get_logger()


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit tripped
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascade failures by monitoring error rates and
    automatically opening the circuit when threshold exceeded.

    State transitions:
    - CLOSED → OPEN: When failure_threshold exceeded
    - OPEN → HALF_OPEN: After recovery_timeout
    - HALF_OPEN → CLOSED: After success_threshold successes
    - HALF_OPEN → OPEN: On any failure
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Circuit breaker identifier
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            half_open_max_calls: Max calls in half-open state
            success_threshold: Successes needed to close circuit
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._half_open_calls = 0

        # Sliding window for failure tracking
        self._call_history: deque = deque(maxlen=100)

        # Thread safety
        self._lock = asyncio.Lock()

        self.logger = logger.bind(circuit_breaker=name)

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            CircuitBreakerOpenError: When circuit is open
        """
        async with self._lock:
            # Check if we should attempt reset
            if self._is_open() and self._should_attempt_reset():
                self._transition_to_half_open()

            # Reject if open
            if self._is_open():
                retry_after = self._get_retry_after()
                self.logger.warning(
                    "circuit_open",
                    retry_after=retry_after
                )
                raise CircuitBreakerOpenError(self.name, retry_after)

            # Check half-open limits
            if self._is_half_open():
                if self._half_open_calls >= self.half_open_max_calls:
                    self.logger.warning(
                        "half_open_limit_reached",
                        calls=self._half_open_calls
                    )
                    raise CircuitBreakerOpenError(
                        self.name,
                        self.recovery_timeout
                    )
                self._half_open_calls += 1

        # Execute function
        try:
            result = await func(*args, **kwargs)

            async with self._lock:
                self._record_success()

            return result

        except Exception as e:
            async with self._lock:
                self._record_failure()
            raise e

    def _is_closed(self) -> bool:
        """Check if circuit is closed."""
        return self._state == CircuitState.CLOSED

    def _is_open(self) -> bool:
        """Check if circuit is open."""
        return self._state == CircuitState.OPEN

    def _is_half_open(self) -> bool:
        """Check if circuit is half-open."""
        return self._state == CircuitState.HALF_OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self._last_failure_time:
            return False

        elapsed = (datetime.now() - self._last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

    def _get_retry_after(self) -> float:
        """Calculate seconds until retry can be attempted."""
        if not self._last_failure_time:
            return 0.0

        elapsed = (datetime.now() - self._last_failure_time).total_seconds()
        return max(0.0, self.recovery_timeout - elapsed)

    def _record_success(self):
        """Record successful call."""
        self._call_history.append(("success", datetime.now()))

        if self._is_half_open():
            self._success_count += 1
            self.logger.info(
                "half_open_success",
                success_count=self._success_count,
                threshold=self.success_threshold
            )

            if self._success_count >= self.success_threshold:
                self._close_circuit()
        elif self._is_closed():
            # Reset failure count on success
            self._failure_count = 0

    def _record_failure(self):
        """Record failed call."""
        self._call_history.append(("failure", datetime.now()))
        self._failure_count += 1
        self._last_failure_time = datetime.now()

        self.logger.warning(
            "call_failed",
            failure_count=self._failure_count,
            threshold=self.failure_threshold
        )

        if self._is_half_open():
            # Any failure in half-open state reopens circuit
            self._open_circuit()
        elif self._is_closed():
            # Check if threshold exceeded
            if self._failure_count >= self.failure_threshold:
                self._open_circuit()

    def _open_circuit(self):
        """Open the circuit."""
        old_state = self._state
        self._state = CircuitState.OPEN
        self._half_open_calls = 0
        self._success_count = 0

        self.logger.error(
            "circuit_opened",
            old_state=old_state.value,
            failure_count=self._failure_count,
            recovery_timeout=self.recovery_timeout
        )

    def _close_circuit(self):
        """Close the circuit."""
        old_state = self._state
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0

        self.logger.info(
            "circuit_closed",
            old_state=old_state.value
        )

    def _transition_to_half_open(self):
        """Transition to half-open state."""
        old_state = self._state
        self._state = CircuitState.HALF_OPEN
        self._half_open_calls = 0
        self._success_count = 0

        self.logger.info(
            "circuit_half_open",
            old_state=old_state.value,
            max_calls=self.half_open_max_calls
        )

    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    def get_metrics(self) -> dict:
        """
        Get circuit breaker metrics.

        Returns:
            Dictionary with metrics:
            - state: Current state
            - failure_count: Number of failures
            - success_count: Number of successes (in half-open)
            - total_calls: Total calls in history
            - error_rate: Error rate from call history
            - last_failure_time: ISO timestamp of last failure
            - time_until_retry: Seconds until retry (if open)
        """
        total_calls = len(self._call_history)
        failures = sum(1 for call, _ in self._call_history if call == "failure")
        error_rate = failures / total_calls if total_calls > 0 else 0.0

        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "total_calls": total_calls,
            "error_rate": error_rate,
            "last_failure_time": (
                self._last_failure_time.isoformat()
                if self._last_failure_time else None
            ),
            "time_until_retry": (
                self._get_retry_after()
                if self._is_open() else None
            )
        }

    def reset(self):
        """Manually reset circuit breaker to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._last_failure_time = None
        self._call_history.clear()

        self.logger.info("circuit_reset")
