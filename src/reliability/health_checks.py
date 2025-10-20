"""
Comprehensive health check system for production monitoring.

Provides multi-layered health checks for services, databases, caches,
and external dependencies with detailed status reporting.
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
import structlog
import psycopg
from redis import asyncio as aioredis

logger = structlog.get_logger()


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    timestamp: datetime = field(default_factory=datetime.now)
    response_time_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "name": self.name,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "response_time_ms": self.response_time_ms,
            "details": self.details,
            "error": self.error,
        }


class BaseHealthCheck(ABC):
    """Base class for health checks."""

    def __init__(self, name: str, timeout: float = 5.0):
        """
        Initialize health check.

        Args:
            name: Health check identifier
            timeout: Maximum execution time in seconds
        """
        self.name = name
        self.timeout = timeout
        self.logger = logger.bind(health_check=name)

    @abstractmethod
    async def check(self) -> HealthCheckResult:
        """
        Perform health check.

        Returns:
            HealthCheckResult with status and details
        """
        pass

    async def execute(self) -> HealthCheckResult:
        """
        Execute health check with timeout and error handling.

        Returns:
            HealthCheckResult
        """
        start_time = datetime.now()

        try:
            result = await asyncio.wait_for(
                self.check(),
                timeout=self.timeout
            )

            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            result.response_time_ms = response_time

            self.logger.info(
                "health_check_completed",
                status=result.status.value,
                response_time_ms=response_time
            )

            return result

        except asyncio.TimeoutError:
            self.logger.error("health_check_timeout", timeout=self.timeout)
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                error=f"Timeout after {self.timeout}s"
            )
        except Exception as e:
            self.logger.error(
                "health_check_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                error=str(e)
            )


class ServiceHealthCheck(BaseHealthCheck):
    """Health check for internal services."""

    def __init__(
        self,
        name: str,
        service_url: Optional[str] = None,
        check_func: Optional[Callable] = None,
        timeout: float = 5.0
    ):
        """
        Initialize service health check.

        Args:
            name: Service name
            service_url: Optional HTTP endpoint to check
            check_func: Optional custom check function
            timeout: Check timeout in seconds
        """
        super().__init__(name, timeout)
        self.service_url = service_url
        self.check_func = check_func

    async def check(self) -> HealthCheckResult:
        """Perform service health check."""
        details = {}

        try:
            if self.check_func:
                # Custom check function
                result = await self.check_func()
                is_healthy = bool(result)
                details["custom_check"] = result
            elif self.service_url:
                # HTTP endpoint check
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.service_url}/health",
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        is_healthy = response.status == 200
                        details["status_code"] = response.status
                        details["url"] = self.service_url
            else:
                # Basic availability check
                is_healthy = True
                details["check_type"] = "basic"

            status = HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY

            return HealthCheckResult(
                name=self.name,
                status=status,
                details=details
            )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                error=str(e),
                details=details
            )


class DatabaseHealthCheck(BaseHealthCheck):
    """Health check for database connections."""

    def __init__(
        self,
        name: str,
        connection_string: str,
        max_connections: int = 20,
        timeout: float = 5.0
    ):
        """
        Initialize database health check.

        Args:
            name: Database identifier
            connection_string: PostgreSQL connection string
            max_connections: Expected max connections
            timeout: Check timeout in seconds
        """
        super().__init__(name, timeout)
        self.connection_string = connection_string
        self.max_connections = max_connections

    async def check(self) -> HealthCheckResult:
        """Perform database health check."""
        details = {}

        try:
            # Test connection
            async with await psycopg.AsyncConnection.connect(
                self.connection_string,
                connect_timeout=self.timeout
            ) as conn:
                # Check database is accessible
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
                    result = await cur.fetchone()
                    details["connectivity"] = "ok" if result else "failed"

                    # Check database stats
                    await cur.execute("""
                        SELECT
                            numbackends,
                            xact_commit,
                            xact_rollback,
                            blks_read,
                            blks_hit
                        FROM pg_stat_database
                        WHERE datname = current_database()
                    """)
                    stats = await cur.fetchone()

                    if stats:
                        details["active_connections"] = stats[0]
                        details["committed_transactions"] = stats[1]
                        details["rolled_back_transactions"] = stats[2]
                        details["blocks_read"] = stats[3]
                        details["blocks_hit"] = stats[4]

                        # Calculate cache hit ratio
                        total_blocks = stats[3] + stats[4]
                        if total_blocks > 0:
                            cache_hit_ratio = stats[4] / total_blocks
                            details["cache_hit_ratio"] = round(cache_hit_ratio, 4)

                    # Check connection pool health
                    await cur.execute("""
                        SELECT
                            count(*) as total,
                            count(*) FILTER (WHERE state = 'active') as active,
                            count(*) FILTER (WHERE state = 'idle') as idle
                        FROM pg_stat_activity
                        WHERE datname = current_database()
                    """)
                    pool_stats = await cur.fetchone()

                    if pool_stats:
                        details["total_connections"] = pool_stats[0]
                        details["active_connections"] = pool_stats[1]
                        details["idle_connections"] = pool_stats[2]

                        # Determine health status
                        connection_usage = pool_stats[0] / self.max_connections
                        details["connection_usage_percent"] = round(connection_usage * 100, 2)

                        if connection_usage > 0.9:
                            status = HealthStatus.DEGRADED
                            details["warning"] = "Connection pool near capacity"
                        elif connection_usage > 0.95:
                            status = HealthStatus.UNHEALTHY
                            details["warning"] = "Connection pool at capacity"
                        else:
                            status = HealthStatus.HEALTHY
                    else:
                        status = HealthStatus.HEALTHY

            return HealthCheckResult(
                name=self.name,
                status=status,
                details=details
            )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                error=str(e),
                details=details
            )


class CacheHealthCheck(BaseHealthCheck):
    """Health check for cache systems (Redis)."""

    def __init__(
        self,
        name: str,
        redis_url: str,
        memory_threshold_percent: float = 90.0,
        timeout: float = 5.0
    ):
        """
        Initialize cache health check.

        Args:
            name: Cache identifier
            redis_url: Redis connection URL
            memory_threshold_percent: Warning threshold for memory usage
            timeout: Check timeout in seconds
        """
        super().__init__(name, timeout)
        self.redis_url = redis_url
        self.memory_threshold_percent = memory_threshold_percent

    async def check(self) -> HealthCheckResult:
        """Perform cache health check."""
        details = {}

        try:
            # Connect to Redis
            redis = await aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=self.timeout
            )

            try:
                # Test connectivity
                ping_result = await redis.ping()
                details["connectivity"] = "ok" if ping_result else "failed"

                # Get server info
                info = await redis.info()

                # Memory stats
                used_memory = info.get("used_memory", 0)
                max_memory = info.get("maxmemory", 0)

                details["used_memory_mb"] = round(used_memory / 1024 / 1024, 2)
                details["max_memory_mb"] = round(max_memory / 1024 / 1024, 2) if max_memory > 0 else "unlimited"

                if max_memory > 0:
                    memory_usage_percent = (used_memory / max_memory) * 100
                    details["memory_usage_percent"] = round(memory_usage_percent, 2)

                    if memory_usage_percent > self.memory_threshold_percent:
                        status = HealthStatus.DEGRADED
                        details["warning"] = "Memory usage high"
                    else:
                        status = HealthStatus.HEALTHY
                else:
                    status = HealthStatus.HEALTHY

                # Connection stats
                details["connected_clients"] = info.get("connected_clients", 0)
                details["blocked_clients"] = info.get("blocked_clients", 0)

                # Performance stats
                details["total_commands_processed"] = info.get("total_commands_processed", 0)
                details["keyspace_hits"] = info.get("keyspace_hits", 0)
                details["keyspace_misses"] = info.get("keyspace_misses", 0)

                # Calculate hit rate
                hits = info.get("keyspace_hits", 0)
                misses = info.get("keyspace_misses", 0)
                total = hits + misses
                if total > 0:
                    hit_rate = hits / total
                    details["cache_hit_rate"] = round(hit_rate, 4)

                # Persistence stats
                details["rdb_last_save_time"] = info.get("rdb_last_save_time", 0)
                details["aof_enabled"] = info.get("aof_enabled", 0) == 1

            finally:
                await redis.close()

            return HealthCheckResult(
                name=self.name,
                status=status,
                details=details
            )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                error=str(e),
                details=details
            )


class DependencyHealthCheck(BaseHealthCheck):
    """Health check for external dependencies."""

    def __init__(
        self,
        name: str,
        endpoint: str,
        expected_status: int = 200,
        timeout: float = 10.0,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize dependency health check.

        Args:
            name: Dependency name
            endpoint: HTTP endpoint to check
            expected_status: Expected HTTP status code
            timeout: Check timeout in seconds
            headers: Optional HTTP headers
        """
        super().__init__(name, timeout)
        self.endpoint = endpoint
        self.expected_status = expected_status
        self.headers = headers or {}

    async def check(self) -> HealthCheckResult:
        """Perform dependency health check."""
        details = {"endpoint": self.endpoint}

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                start = datetime.now()
                async with session.get(
                    self.endpoint,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    latency = (datetime.now() - start).total_seconds() * 1000

                    details["status_code"] = response.status
                    details["latency_ms"] = round(latency, 2)

                    if response.status == self.expected_status:
                        status = HealthStatus.HEALTHY
                    elif 200 <= response.status < 300:
                        status = HealthStatus.DEGRADED
                        details["warning"] = f"Unexpected status: {response.status}"
                    else:
                        status = HealthStatus.UNHEALTHY
                        details["error"] = f"HTTP {response.status}"

            return HealthCheckResult(
                name=self.name,
                status=status,
                details=details
            )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                error=str(e),
                details=details
            )


class HealthCheckRegistry:
    """
    Central registry for all health checks.

    Manages registration, execution, and aggregation of health checks.
    """

    def __init__(self):
        """Initialize health check registry."""
        self.checks: Dict[str, BaseHealthCheck] = {}
        self.logger = logger.bind(component="health_check_registry")

    def register(self, check: BaseHealthCheck):
        """
        Register a health check.

        Args:
            check: Health check instance
        """
        self.checks[check.name] = check
        self.logger.info("health_check_registered", name=check.name)

    def unregister(self, name: str):
        """
        Unregister a health check.

        Args:
            name: Health check name
        """
        if name in self.checks:
            del self.checks[name]
            self.logger.info("health_check_unregistered", name=name)

    async def check_all(self) -> Dict[str, HealthCheckResult]:
        """
        Execute all registered health checks in parallel.

        Returns:
            Dictionary mapping check names to results
        """
        if not self.checks:
            self.logger.warning("no_health_checks_registered")
            return {}

        self.logger.info("executing_health_checks", count=len(self.checks))

        # Execute all checks in parallel
        results = await asyncio.gather(
            *[check.execute() for check in self.checks.values()],
            return_exceptions=True
        )

        # Map results to check names
        check_results = {}
        for check, result in zip(self.checks.values(), results):
            if isinstance(result, Exception):
                check_results[check.name] = HealthCheckResult(
                    name=check.name,
                    status=HealthStatus.UNHEALTHY,
                    error=str(result)
                )
            else:
                check_results[check.name] = result

        return check_results

    async def check_one(self, name: str) -> Optional[HealthCheckResult]:
        """
        Execute a single health check.

        Args:
            name: Health check name

        Returns:
            HealthCheckResult or None if not found
        """
        check = self.checks.get(name)
        if not check:
            self.logger.warning("health_check_not_found", name=name)
            return None

        return await check.execute()

    def get_summary(self, results: Dict[str, HealthCheckResult]) -> Dict[str, Any]:
        """
        Get aggregated health summary.

        Args:
            results: Health check results

        Returns:
            Summary with overall status and statistics
        """
        if not results:
            return {
                "status": HealthStatus.UNKNOWN.value,
                "total_checks": 0,
                "healthy": 0,
                "degraded": 0,
                "unhealthy": 0,
                "timestamp": datetime.now().isoformat(),
            }

        # Count statuses
        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.DEGRADED: 0,
            HealthStatus.UNHEALTHY: 0,
            HealthStatus.UNKNOWN: 0,
        }

        for result in results.values():
            status_counts[result.status] += 1

        # Determine overall status
        if status_counts[HealthStatus.UNHEALTHY] > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif status_counts[HealthStatus.DEGRADED] > 0:
            overall_status = HealthStatus.DEGRADED
        elif status_counts[HealthStatus.HEALTHY] > 0:
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.UNKNOWN

        return {
            "status": overall_status.value,
            "total_checks": len(results),
            "healthy": status_counts[HealthStatus.HEALTHY],
            "degraded": status_counts[HealthStatus.DEGRADED],
            "unhealthy": status_counts[HealthStatus.UNHEALTHY],
            "unknown": status_counts[HealthStatus.UNKNOWN],
            "timestamp": datetime.now().isoformat(),
            "checks": {name: result.to_dict() for name, result in results.items()},
        }
