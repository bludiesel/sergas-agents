"""
Reliability module for production hardening.

Provides comprehensive reliability patterns including:
- Health checks and monitoring
- Graceful degradation and fallback strategies
- Disaster recovery and backup automation
- Rate limiting and backpressure handling
"""

from .health_checks import (
    HealthCheckRegistry,
    ServiceHealthCheck,
    DatabaseHealthCheck,
    CacheHealthCheck,
    DependencyHealthCheck,
    HealthStatus,
    HealthCheckResult,
)

from .graceful_degradation import (
    DegradationManager,
    FeatureFlags,
    FallbackStrategy,
    PartialFailureHandler,
    DegradationLevel,
)

from .disaster_recovery import (
    BackupManager,
    RecoveryManager,
    PointInTimeRecovery,
    BackupStrategy,
    RecoveryTestRunner,
)

from .rate_limiting import (
    RateLimiter,
    QueueManager,
    ThrottlingStrategy,
    BackpressureHandler,
    RateLimitConfig,
)

__all__ = [
    # Health Checks
    "HealthCheckRegistry",
    "ServiceHealthCheck",
    "DatabaseHealthCheck",
    "CacheHealthCheck",
    "DependencyHealthCheck",
    "HealthStatus",
    "HealthCheckResult",
    # Graceful Degradation
    "DegradationManager",
    "FeatureFlags",
    "FallbackStrategy",
    "PartialFailureHandler",
    "DegradationLevel",
    # Disaster Recovery
    "BackupManager",
    "RecoveryManager",
    "PointInTimeRecovery",
    "BackupStrategy",
    "RecoveryTestRunner",
    # Rate Limiting
    "RateLimiter",
    "QueueManager",
    "ThrottlingStrategy",
    "BackpressureHandler",
    "RateLimitConfig",
]

__version__ = "1.0.0"
