"""Custom exceptions for resilience module."""


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, circuit_name: str, retry_after: float):
        """
        Initialize exception.

        Args:
            circuit_name: Name of the circuit breaker
            retry_after: Seconds until retry should be attempted
        """
        self.circuit_name = circuit_name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker '{circuit_name}' is open. "
            f"Retry after {retry_after:.1f} seconds."
        )


class AllTiersFailedError(Exception):
    """Raised when all tiers have failed."""

    def __init__(self, attempted_tiers: list[str]):
        """
        Initialize exception.

        Args:
            attempted_tiers: List of tier names that were attempted
        """
        self.attempted_tiers = attempted_tiers
        super().__init__(
            f"All tiers failed: {', '.join(attempted_tiers)}"
        )


class RetryExhaustedError(Exception):
    """Raised when all retry attempts exhausted."""

    def __init__(self, attempts: int, last_error: Exception):
        """
        Initialize exception.

        Args:
            attempts: Number of retry attempts made
            last_error: The last error encountered
        """
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"Retry exhausted after {attempts} attempts. "
            f"Last error: {str(last_error)}"
        )
