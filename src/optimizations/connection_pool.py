"""
Connection Pool Manager.

Manages database connection pools for optimal performance:
- Dynamic pool sizing
- Connection health monitoring
- Load balancing across connections
- Connection lifecycle management
- Performance metrics

Author: Performance Testing Engineer
Date: 2025-10-19
"""

import asyncio
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import psutil


# ============================================================================
# Pool Models
# ============================================================================

class ConnectionState(Enum):
    """Connection states."""
    IDLE = "idle"
    BUSY = "busy"
    CLOSED = "closed"
    ERROR = "error"


@dataclass
class PoolConfig:
    """Connection pool configuration."""
    min_size: int = 5
    max_size: int = 20
    max_lifetime: float = 3600.0  # 1 hour
    idle_timeout: float = 300.0  # 5 minutes
    connection_timeout: float = 30.0
    health_check_interval: float = 60.0


@dataclass
class PoolMetrics:
    """Connection pool metrics."""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    peak_connections: int = 0
    total_acquires: int = 0
    total_releases: int = 0
    total_timeouts: int = 0
    total_errors: int = 0
    avg_acquire_time_ms: float = 0.0
    avg_connection_lifetime_s: float = 0.0

    def print_report(self):
        """Print formatted metrics report."""
        print(f"\n{'='*80}")
        print("Connection Pool Metrics")
        print(f"{'='*80}")
        print(f"Connections:")
        print(f"  Total: {self.total_connections}")
        print(f"  Active: {self.active_connections}")
        print(f"  Idle: {self.idle_connections}")
        print(f"  Peak: {self.peak_connections}")
        print(f"\nOperations:")
        print(f"  Acquires: {self.total_acquires}")
        print(f"  Releases: {self.total_releases}")
        print(f"  Timeouts: {self.total_timeouts}")
        print(f"  Errors: {self.total_errors}")
        print(f"\nPerformance:")
        print(f"  Avg Acquire Time: {self.avg_acquire_time_ms:.2f}ms")
        print(f"  Avg Connection Lifetime: {self.avg_connection_lifetime_s:.2f}s")
        print(f"{'='*80}\n")


# ============================================================================
# Connection Wrapper
# ============================================================================

@dataclass
class PooledConnection:
    """Wrapper for pooled connection."""
    connection: Any
    created_at: float
    last_used: float
    state: ConnectionState = ConnectionState.IDLE
    use_count: int = 0
    error_count: int = 0

    def mark_busy(self):
        """Mark connection as busy."""
        self.state = ConnectionState.BUSY
        self.last_used = time.time()
        self.use_count += 1

    def mark_idle(self):
        """Mark connection as idle."""
        self.state = ConnectionState.IDLE
        self.last_used = time.time()

    def mark_error(self):
        """Mark connection as error."""
        self.state = ConnectionState.ERROR
        self.error_count += 1

    def is_expired(self, max_lifetime: float) -> bool:
        """Check if connection has exceeded max lifetime."""
        return time.time() - self.created_at > max_lifetime

    def is_idle_timeout(self, idle_timeout: float) -> bool:
        """Check if connection has been idle too long."""
        return (self.state == ConnectionState.IDLE and
                time.time() - self.last_used > idle_timeout)

    def is_healthy(self) -> bool:
        """Check if connection is healthy."""
        return (self.state in (ConnectionState.IDLE, ConnectionState.BUSY) and
                self.error_count < 3)


# ============================================================================
# Connection Pool Manager
# ============================================================================

class ConnectionPoolManager:
    """
    Manages database connection pool with advanced features.

    Features:
    - Dynamic pool sizing based on demand
    - Connection health monitoring
    - Automatic reconnection
    - Load balancing
    - Performance metrics
    """

    def __init__(
        self,
        connection_factory,
        config: Optional[PoolConfig] = None
    ):
        self.connection_factory = connection_factory
        self.config = config or PoolConfig()
        self.pool: List[PooledConnection] = []
        self.metrics = PoolMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._health_check_task = None

    async def initialize(self):
        """Initialize the connection pool."""
        async with self._lock:
            if self._initialized:
                return

            # Create minimum connections
            for _ in range(self.config.min_size):
                await self._create_connection()

            # Start health check task
            self._health_check_task = asyncio.create_task(self._health_check_loop())

            self._initialized = True

    async def acquire(self, timeout: Optional[float] = None) -> Any:
        """
        Acquire connection from pool.

        Args:
            timeout: Timeout in seconds

        Returns:
            Connection object
        """
        start_time = time.perf_counter()
        timeout = timeout or self.config.connection_timeout

        try:
            async with asyncio.timeout(timeout):
                while True:
                    async with self._lock:
                        # Find idle connection
                        conn = await self._find_idle_connection()

                        if conn:
                            conn.mark_busy()
                            self.metrics.active_connections += 1
                            self.metrics.total_acquires += 1

                            # Update avg acquire time
                            acquire_time_ms = (time.perf_counter() - start_time) * 1000
                            self._update_avg_acquire_time(acquire_time_ms)

                            # Update peak connections
                            self.metrics.peak_connections = max(
                                self.metrics.peak_connections,
                                self.metrics.active_connections
                            )

                            return conn.connection

                        # No idle connections, try to create new one
                        if len(self.pool) < self.config.max_size:
                            conn = await self._create_connection()
                            conn.mark_busy()
                            self.metrics.active_connections += 1
                            self.metrics.total_acquires += 1
                            return conn.connection

                    # Pool is full, wait a bit
                    await asyncio.sleep(0.01)

        except asyncio.TimeoutError:
            self.metrics.total_timeouts += 1
            raise ConnectionPoolTimeoutError(
                f"Failed to acquire connection within {timeout}s"
            )

    async def release(self, connection: Any):
        """
        Release connection back to pool.

        Args:
            connection: Connection to release
        """
        async with self._lock:
            # Find pooled connection
            for conn in self.pool:
                if conn.connection == connection:
                    conn.mark_idle()
                    self.metrics.active_connections -= 1
                    self.metrics.total_releases += 1
                    break

    async def close(self):
        """Close all connections and shutdown pool."""
        async with self._lock:
            # Cancel health check
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            # Close all connections
            for conn in self.pool:
                await self._close_connection(conn)

            self.pool.clear()
            self._initialized = False

    async def _create_connection(self) -> PooledConnection:
        """Create new connection."""
        try:
            # Create connection using factory
            connection = await self.connection_factory()

            conn = PooledConnection(
                connection=connection,
                created_at=time.time(),
                last_used=time.time()
            )

            self.pool.append(conn)
            self.metrics.total_connections += 1
            self.metrics.idle_connections += 1

            return conn

        except Exception as e:
            self.metrics.total_errors += 1
            raise ConnectionPoolError(f"Failed to create connection: {e}")

    async def _find_idle_connection(self) -> Optional[PooledConnection]:
        """Find healthy idle connection."""
        for conn in self.pool:
            if conn.state == ConnectionState.IDLE and conn.is_healthy():
                # Check if expired or idle timeout
                if (conn.is_expired(self.config.max_lifetime) or
                    conn.is_idle_timeout(self.config.idle_timeout)):
                    # Replace connection
                    await self._close_connection(conn)
                    self.pool.remove(conn)
                    return await self._create_connection()

                return conn

        return None

    async def _close_connection(self, conn: PooledConnection):
        """Close single connection."""
        try:
            conn.state = ConnectionState.CLOSED

            # In production, actually close the connection
            # await conn.connection.close()

            self.metrics.idle_connections -= 1

            # Update avg lifetime
            lifetime = time.time() - conn.created_at
            self._update_avg_lifetime(lifetime)

        except Exception as e:
            self.metrics.total_errors += 1
            print(f"Error closing connection: {e}")

    async def _health_check_loop(self):
        """Periodic health check of connections."""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)

                async with self._lock:
                    for conn in self.pool[:]:  # Copy list
                        if not conn.is_healthy():
                            # Replace unhealthy connection
                            await self._close_connection(conn)
                            self.pool.remove(conn)

                            # Create replacement if below min_size
                            if len(self.pool) < self.config.min_size:
                                await self._create_connection()

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Health check error: {e}")

    def _update_avg_acquire_time(self, acquire_time_ms: float):
        """Update average acquire time."""
        total = self.metrics.avg_acquire_time_ms * (self.metrics.total_acquires - 1)
        self.metrics.avg_acquire_time_ms = (total + acquire_time_ms) / self.metrics.total_acquires

    def _update_avg_lifetime(self, lifetime_s: float):
        """Update average connection lifetime."""
        closed_count = self.metrics.total_connections - len(self.pool)
        if closed_count > 0:
            total = self.metrics.avg_connection_lifetime_s * (closed_count - 1)
            self.metrics.avg_connection_lifetime_s = (total + lifetime_s) / closed_count

    def get_metrics(self) -> PoolMetrics:
        """Get pool metrics."""
        self.metrics.idle_connections = sum(
            1 for conn in self.pool if conn.state == ConnectionState.IDLE
        )
        return self.metrics

    async def resize_pool(self, new_min: int, new_max: int):
        """Dynamically resize pool."""
        async with self._lock:
            self.config.min_size = new_min
            self.config.max_size = new_max

            # Add connections if below min
            while len(self.pool) < new_min:
                await self._create_connection()

            # Remove excess idle connections if above max
            while len(self.pool) > new_max:
                idle_conns = [c for c in self.pool if c.state == ConnectionState.IDLE]
                if not idle_conns:
                    break

                conn = idle_conns[0]
                await self._close_connection(conn)
                self.pool.remove(conn)


# ============================================================================
# Exceptions
# ============================================================================

class ConnectionPoolError(Exception):
    """Base exception for connection pool errors."""
    pass


class ConnectionPoolTimeoutError(ConnectionPoolError):
    """Raised when connection acquire times out."""
    pass


class ConnectionPoolExhaustedError(ConnectionPoolError):
    """Raised when pool is exhausted."""
    pass


# ============================================================================
# Context Manager
# ============================================================================

class PooledConnectionContext:
    """Context manager for pooled connections."""

    def __init__(self, pool: ConnectionPoolManager):
        self.pool = pool
        self.connection = None

    async def __aenter__(self):
        """Acquire connection."""
        self.connection = await self.pool.acquire()
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release connection."""
        if self.connection:
            await self.pool.release(self.connection)
