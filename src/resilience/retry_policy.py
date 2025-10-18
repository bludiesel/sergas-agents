"""Retry policy with exponential backoff."""

import asyncio
import random
from typing import Callable, Any, Optional
import structlog
from .exceptions import RetryExhaustedError

logger = structlog.get_logger()


class RetryPolicy:
    """
    Retry policy with exponential backoff.

    Works with circuit breaker to handle transient failures.
    Uses exponential backoff with optional jitter to prevent
    thundering herd problem.

    Formula: delay = min(base_delay * (exponential_base ^ attempt), max_delay)
    With jitter: delay * random(0.5, 1.5)
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize retry policy.

        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter
        """
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if base_delay <= 0:
            raise ValueError("base_delay must be > 0")
        if max_delay < base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if exponential_base <= 1:
            raise ValueError("exponential_base must be > 1")

        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

        self.logger = logger.bind(component="retry_policy")

    async def execute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic.

        Uses exponential backoff with optional jitter.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from successful execution

        Raises:
            RetryExhaustedError: When all retry attempts exhausted
        """
        last_error: Optional[Exception] = None

        for attempt in range(self.max_attempts):
            try:
                self.logger.debug(
                    "retry_attempt",
                    attempt=attempt + 1,
                    max_attempts=self.max_attempts
                )

                result = await func(*args, **kwargs)

                if attempt > 0:
                    self.logger.info(
                        "retry_succeeded",
                        attempt=attempt + 1
                    )

                return result

            except Exception as e:
                last_error = e

                self.logger.warning(
                    "retry_failed",
                    attempt=attempt + 1,
                    max_attempts=self.max_attempts,
                    error=str(e),
                    error_type=type(e).__name__
                )

                # Don't sleep after last attempt
                if attempt < self.max_attempts - 1:
                    delay = self._calculate_delay(attempt)

                    self.logger.debug(
                        "retry_backoff",
                        delay=delay,
                        next_attempt=attempt + 2
                    )

                    await asyncio.sleep(delay)

        # All attempts exhausted
        self.logger.error(
            "retry_exhausted",
            attempts=self.max_attempts,
            last_error=str(last_error)
        )

        raise RetryExhaustedError(self.max_attempts, last_error)

    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt.

        Args:
            attempt: Zero-based attempt number

        Returns:
            Delay in seconds
        """
        # Exponential backoff: base_delay * (exponential_base ^ attempt)
        delay = self.base_delay * (self.exponential_base ** attempt)

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add jitter if enabled (random factor between 0.5 and 1.5)
        if self.jitter:
            jitter_factor = random.uniform(0.5, 1.5)
            delay = delay * jitter_factor

        return delay

    def get_config(self) -> dict:
        """
        Get retry policy configuration.

        Returns:
            Configuration dictionary
        """
        return {
            "max_attempts": self.max_attempts,
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "exponential_base": self.exponential_base,
            "jitter": self.jitter
        }
