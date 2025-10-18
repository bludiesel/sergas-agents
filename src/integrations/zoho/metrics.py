"""Metrics collection for Zoho integration tiers.

Tracks performance, success rates, and errors for all three tiers.
"""

import time
import threading
from typing import Dict, Any, List
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class RequestMetric:
    """Single request metric.

    Attributes:
        timestamp: Unix timestamp of request
        tier: Tier name (MCP, SDK, REST)
        operation: Operation name
        duration: Request duration in seconds
        success: Whether request succeeded
        error: Error message if failed
    """
    timestamp: float
    tier: str
    operation: str
    duration: float
    success: bool
    error: str | None = None


@dataclass
class TierStats:
    """Statistics for a single tier.

    Attributes:
        total_requests: Total number of requests
        successful_requests: Number of successful requests
        failed_requests: Number of failed requests
        total_duration: Total duration of all requests
        durations: Recent request durations for percentile calculation
        errors: Error messages and counts
    """
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_duration: float = 0.0
    durations: deque = field(default_factory=lambda: deque(maxlen=1000))
    errors: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage.

        Returns:
            Success rate (0.0 to 100.0)
        """
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def avg_duration(self) -> float:
        """Calculate average request duration.

        Returns:
            Average duration in seconds
        """
        if self.total_requests == 0:
            return 0.0
        return self.total_duration / self.total_requests

    def get_percentile(self, percentile: int) -> float:
        """Calculate duration percentile.

        Args:
            percentile: Percentile to calculate (e.g., 95, 99)

        Returns:
            Duration at specified percentile in seconds
        """
        if not self.durations:
            return 0.0

        sorted_durations = sorted(self.durations)
        index = int(len(sorted_durations) * (percentile / 100))
        return sorted_durations[min(index, len(sorted_durations) - 1)]

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary.

        Returns:
            Dictionary representation of stats
        """
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(self.success_rate, 2),
            "avg_duration_ms": round(self.avg_duration * 1000, 2),
            "p50_duration_ms": round(self.get_percentile(50) * 1000, 2),
            "p95_duration_ms": round(self.get_percentile(95) * 1000, 2),
            "p99_duration_ms": round(self.get_percentile(99) * 1000, 2),
            "error_count": self.failed_requests,
            "top_errors": dict(sorted(
                self.errors.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]) if self.errors else {},
        }


class IntegrationMetrics:
    """Collect and report metrics for all integration tiers.

    Thread-safe metrics collection with support for:
    - Per-tier statistics
    - Success/failure rates
    - Response time percentiles
    - Error tracking
    - Recent request history

    Example:
        >>> metrics = IntegrationMetrics()
        >>> metrics.record_request("MCP", "get_account", 0.5, True)
        >>> stats = metrics.get_tier_stats("MCP")
    """

    def __init__(self, max_history: int = 1000) -> None:
        """Initialize metrics collector.

        Args:
            max_history: Maximum number of recent requests to keep
        """
        self._lock = threading.Lock()
        self._tier_stats: Dict[str, TierStats] = {
            "MCP": TierStats(),
            "SDK": TierStats(),
            "REST": TierStats(),
        }
        self._recent_requests: deque = deque(maxlen=max_history)
        self._start_time = time.time()
        self.logger = logger.bind(component="IntegrationMetrics")

        self.logger.info("metrics_collector_initialized", max_history=max_history)

    def record_request(
        self,
        tier: str,
        operation: str,
        duration: float,
        success: bool,
        error: str | None = None,
    ) -> None:
        """Record a request to a specific tier.

        Args:
            tier: Tier name (MCP, SDK, or REST)
            operation: Operation name (e.g., get_account)
            duration: Request duration in seconds
            success: Whether request succeeded
            error: Error message if failed
        """
        tier = tier.upper()

        with self._lock:
            # Record metric
            metric = RequestMetric(
                timestamp=time.time(),
                tier=tier,
                operation=operation,
                duration=duration,
                success=success,
                error=error,
            )
            self._recent_requests.append(metric)

            # Update tier stats
            if tier in self._tier_stats:
                stats = self._tier_stats[tier]
                stats.total_requests += 1
                stats.total_duration += duration
                stats.durations.append(duration)

                if success:
                    stats.successful_requests += 1
                else:
                    stats.failed_requests += 1
                    if error:
                        stats.errors[error] += 1

                self.logger.debug(
                    "request_recorded",
                    tier=tier,
                    operation=operation,
                    duration_ms=round(duration * 1000, 2),
                    success=success,
                )

    def get_tier_stats(self, tier: str) -> Dict[str, Any]:
        """Get statistics for a specific tier.

        Args:
            tier: Tier name (MCP, SDK, or REST)

        Returns:
            Tier statistics dictionary
        """
        tier = tier.upper()

        with self._lock:
            if tier not in self._tier_stats:
                return {
                    "error": f"Unknown tier: {tier}",
                    "available_tiers": list(self._tier_stats.keys()),
                }

            stats = self._tier_stats[tier].to_dict()
            stats["tier"] = tier
            return stats

    def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall integration statistics.

        Returns:
            Overall statistics across all tiers
        """
        with self._lock:
            total_requests = sum(s.total_requests for s in self._tier_stats.values())
            total_success = sum(s.successful_requests for s in self._tier_stats.values())
            total_failed = sum(s.failed_requests for s in self._tier_stats.values())

            all_durations = []
            for stats in self._tier_stats.values():
                all_durations.extend(stats.durations)

            uptime = time.time() - self._start_time

            return {
                "uptime_seconds": round(uptime, 2),
                "total_requests": total_requests,
                "successful_requests": total_success,
                "failed_requests": total_failed,
                "overall_success_rate": round(
                    (total_success / total_requests * 100) if total_requests > 0 else 0,
                    2
                ),
                "avg_duration_ms": round(
                    statistics.mean(all_durations) * 1000 if all_durations else 0,
                    2
                ),
                "p95_duration_ms": round(
                    statistics.quantiles(all_durations, n=20)[18] * 1000 if len(all_durations) >= 20 else 0,
                    2
                ),
                "tier_breakdown": {
                    tier: stats.to_dict()
                    for tier, stats in self._tier_stats.items()
                },
            }

    def get_recent_requests(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent request history.

        Args:
            limit: Maximum number of requests to return

        Returns:
            List of recent request metrics
        """
        with self._lock:
            recent = list(self._recent_requests)[-limit:]
            return [
                {
                    "timestamp": metric.timestamp,
                    "tier": metric.tier,
                    "operation": metric.operation,
                    "duration_ms": round(metric.duration * 1000, 2),
                    "success": metric.success,
                    "error": metric.error,
                }
                for metric in recent
            ]

    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary across all tiers.

        Returns:
            Error summary with counts and recent errors
        """
        with self._lock:
            all_errors: Dict[str, int] = defaultdict(int)

            for stats in self._tier_stats.values():
                for error, count in stats.errors.items():
                    all_errors[error] += count

            # Get recent failed requests
            failed_requests = [
                {
                    "timestamp": metric.timestamp,
                    "tier": metric.tier,
                    "operation": metric.operation,
                    "error": metric.error,
                }
                for metric in self._recent_requests
                if not metric.success
            ]

            return {
                "total_errors": sum(all_errors.values()),
                "unique_errors": len(all_errors),
                "top_errors": dict(sorted(
                    all_errors.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]),
                "recent_failures": failed_requests[-50:],
            }

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._tier_stats = {
                "MCP": TierStats(),
                "SDK": TierStats(),
                "REST": TierStats(),
            }
            self._recent_requests.clear()
            self._start_time = time.time()
            self.logger.info("metrics_reset")

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics string
        """
        with self._lock:
            lines = [
                "# HELP zoho_integration_requests_total Total requests per tier",
                "# TYPE zoho_integration_requests_total counter",
            ]

            for tier, stats in self._tier_stats.items():
                lines.append(
                    f'zoho_integration_requests_total{{tier="{tier}"}} {stats.total_requests}'
                )

            lines.extend([
                "",
                "# HELP zoho_integration_success_rate Success rate percentage per tier",
                "# TYPE zoho_integration_success_rate gauge",
            ])

            for tier, stats in self._tier_stats.items():
                lines.append(
                    f'zoho_integration_success_rate{{tier="{tier}"}} {stats.success_rate}'
                )

            lines.extend([
                "",
                "# HELP zoho_integration_duration_seconds Request duration in seconds",
                "# TYPE zoho_integration_duration_seconds histogram",
            ])

            for tier, stats in self._tier_stats.items():
                lines.append(
                    f'zoho_integration_duration_seconds{{tier="{tier}",quantile="0.5"}} {stats.get_percentile(50)}'
                )
                lines.append(
                    f'zoho_integration_duration_seconds{{tier="{tier}",quantile="0.95"}} {stats.get_percentile(95)}'
                )
                lines.append(
                    f'zoho_integration_duration_seconds{{tier="{tier}",quantile="0.99"}} {stats.get_percentile(99)}'
                )

            return "\n".join(lines)
