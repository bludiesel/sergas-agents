"""Circuit breaker implementation for fault tolerance.

Prevents cascade failures by temporarily blocking requests to failing services.
"""

import time
import threading
from enum import Enum
from typing import Callable, Any, TypeVar, ParamSpec
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)

T = TypeVar('T')
P = ParamSpec('P')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration.

    Attributes:
        failure_threshold: Number of failures before opening circuit
        success_threshold: Number of successes to close circuit from half-open
        timeout: Seconds to wait before moving to half-open
        name: Circuit breaker name for logging
    """
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: int = 60
    name: str = "default"


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, message: str, circuit_name: str, retry_after: float):
        """Initialize circuit breaker error.

        Args:
            message: Error message
            circuit_name: Name of the circuit that is open
            retry_after: Seconds until circuit may close
        """
        self.circuit_name = circuit_name
        self.retry_after = retry_after
        super().__init__(message)


class CircuitBreaker:
    """Circuit breaker for preventing cascade failures.

    The circuit breaker has three states:
    - CLOSED: Requests pass through normally. Failures increment counter.
    - OPEN: Requests are blocked immediately. After timeout, moves to HALF_OPEN.
    - HALF_OPEN: Limited requests allowed. Success closes circuit, failure opens it.

    Example:
        >>> breaker = CircuitBreaker(failure_threshold=5, timeout=60, name="zoho-api")
        >>> result = breaker.call(lambda: api_request())
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 60,
        name: str = "default",
    ) -> None:
        """Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit
            success_threshold: Successes to close from half-open
            timeout: Seconds before retry (open to half-open)
            name: Circuit breaker name
        """
        self.config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout=timeout,
            name=name,
        )

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._lock = threading.Lock()
        self.logger = logger.bind(circuit_breaker=name)

        self.logger.info(
            "circuit_breaker_initialized",
            failure_threshold=failure_threshold,
            timeout=timeout,
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        with self._lock:
            return self._failure_count

    @property
    def success_count(self) -> int:
        """Get current success count."""
        with self._lock:
            return self._success_count

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset.

        Returns:
            True if circuit should move to half-open
        """
        if self._last_failure_time is None:
            return False

        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.config.timeout

    def _on_success(self) -> None:
        """Handle successful request."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                self.logger.info(
                    "circuit_breaker_success",
                    state="half_open",
                    success_count=self._success_count,
                    threshold=self.config.success_threshold,
                )

                # Close circuit if enough successes
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    self.logger.info("circuit_breaker_closed")

            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0

    def _on_failure(self, exception: Exception) -> None:
        """Handle failed request.

        Args:
            exception: The exception that occurred
        """
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            self.logger.warning(
                "circuit_breaker_failure",
                state=self._state.value,
                failure_count=self._failure_count,
                threshold=self.config.failure_threshold,
                error=str(exception),
            )

            # Open circuit if threshold exceeded
            if self._failure_count >= self.config.failure_threshold:
                if self._state != CircuitState.OPEN:
                    self._state = CircuitState.OPEN
                    self._success_count = 0
                    self.logger.error(
                        "circuit_breaker_opened",
                        failure_count=self._failure_count,
                        timeout=self.config.timeout,
                    )

            # If in half-open, immediately reopen
            elif self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._success_count = 0
                self.logger.error("circuit_breaker_reopened")

    def call(self, func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        """Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Original exception from function
        """
        with self._lock:
            current_state = self._state

            # Check if we should attempt reset
            if current_state == CircuitState.OPEN and self._should_attempt_reset():
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
                current_state = CircuitState.HALF_OPEN
                self.logger.info("circuit_breaker_half_open")

            # Block if circuit is open
            if current_state == CircuitState.OPEN:
                retry_after = self.config.timeout - (
                    time.time() - (self._last_failure_time or 0)
                )
                retry_after = max(0, retry_after)

                self.logger.warning(
                    "circuit_breaker_blocking_request",
                    retry_after=retry_after,
                )

                raise CircuitBreakerError(
                    f"Circuit breaker '{self.config.name}' is open",
                    circuit_name=self.config.name,
                    retry_after=retry_after,
                )

        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure(e)
            raise

    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            self.logger.info("circuit_breaker_reset")

    def get_status(self) -> dict[str, Any]:
        """Get circuit breaker status.

        Returns:
            Status dictionary with state and metrics
        """
        with self._lock:
            status = {
                "name": self.config.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout,
            }

            if self._last_failure_time:
                elapsed = time.time() - self._last_failure_time
                status["time_since_last_failure"] = elapsed
                status["retry_after"] = max(0, self.config.timeout - elapsed)

            return status
