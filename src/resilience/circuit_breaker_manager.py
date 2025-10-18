"""Circuit breaker manager for managing multiple circuit breakers."""

import structlog
from typing import Optional
from .circuit_breaker import CircuitBreaker, CircuitState

logger = structlog.get_logger()


class CircuitBreakerManager:
    """
    Manages multiple circuit breakers for different services/tiers.

    Provides centralized management and monitoring of circuit breakers
    across the entire system.
    """

    def __init__(self):
        """Initialize circuit breaker manager."""
        self._breakers: dict[str, CircuitBreaker] = {}
        self.logger = logger.bind(component="circuit_breaker_manager")

    def register_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3,
        success_threshold: int = 2
    ) -> CircuitBreaker:
        """
        Register a new circuit breaker.

        Args:
            name: Unique identifier for the circuit breaker
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            half_open_max_calls: Max calls in half-open state
            success_threshold: Successes needed to close circuit

        Returns:
            The registered circuit breaker

        Raises:
            ValueError: If breaker with name already exists
        """
        if name in self._breakers:
            raise ValueError(f"Circuit breaker '{name}' already registered")

        breaker = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            half_open_max_calls=half_open_max_calls,
            success_threshold=success_threshold
        )

        self._breakers[name] = breaker

        self.logger.info(
            "breaker_registered",
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout
        )

        return breaker

    def get_breaker(self, name: str) -> CircuitBreaker:
        """
        Get circuit breaker by name.

        Args:
            name: Circuit breaker identifier

        Returns:
            The circuit breaker

        Raises:
            KeyError: If breaker not found
        """
        if name not in self._breakers:
            raise KeyError(f"Circuit breaker '{name}' not found")

        return self._breakers[name]

    def get_all_states(self) -> dict[str, CircuitState]:
        """
        Get states of all circuit breakers.

        Returns:
            Dictionary mapping breaker names to their states
        """
        return {
            name: breaker.get_state()
            for name, breaker in self._breakers.items()
        }

    def get_all_metrics(self) -> dict[str, dict]:
        """
        Get metrics for all circuit breakers.

        Returns:
            Dictionary mapping breaker names to their metrics
        """
        return {
            name: breaker.get_metrics()
            for name, breaker in self._breakers.items()
        }

    def reset_all(self):
        """Reset all circuit breakers to closed state."""
        for name, breaker in self._breakers.items():
            breaker.reset()
            self.logger.info("breaker_reset", name=name)

    def reset_breaker(self, name: str):
        """
        Reset specific circuit breaker.

        Args:
            name: Circuit breaker identifier

        Raises:
            KeyError: If breaker not found
        """
        breaker = self.get_breaker(name)
        breaker.reset()
        self.logger.info("breaker_reset", name=name)

    def unregister_breaker(self, name: str):
        """
        Unregister a circuit breaker.

        Args:
            name: Circuit breaker identifier

        Raises:
            KeyError: If breaker not found
        """
        if name not in self._breakers:
            raise KeyError(f"Circuit breaker '{name}' not found")

        del self._breakers[name]
        self.logger.info("breaker_unregistered", name=name)

    def get_breaker_count(self) -> int:
        """Get total number of registered circuit breakers."""
        return len(self._breakers)

    def list_breakers(self) -> list[str]:
        """Get list of all registered circuit breaker names."""
        return list(self._breakers.keys())
