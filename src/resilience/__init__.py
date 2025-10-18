"""
Resilience module for circuit breaker pattern and fault tolerance.

Provides:
- Circuit breaker implementation
- Retry policies with exponential backoff
- Tier fallback handling
- Health monitoring
"""

from .circuit_breaker import CircuitBreaker, CircuitState
from .circuit_breaker_manager import CircuitBreakerManager
from .retry_policy import RetryPolicy
from .fallback_handler import FallbackHandler
from .health_monitor import HealthMonitor
from .exceptions import (
    CircuitBreakerOpenError,
    AllTiersFailedError,
    RetryExhaustedError
)

__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "CircuitBreakerManager",
    "RetryPolicy",
    "FallbackHandler",
    "HealthMonitor",
    "CircuitBreakerOpenError",
    "AllTiersFailedError",
    "RetryExhaustedError"
]
