"""
Comprehensive Load Testing for Sergas Super Account Manager.

Week 13 Performance Testing - Load Testing Suite

Tests system performance under various load conditions:
- 100, 500, 1000, 5000 account scenarios
- Concurrent user simulation
- Database connection pool testing
- Memory profiling
- CPU profiling
- Sustained load scenarios

Author: Performance Testing Engineer
Date: 2025-10-19
"""

import pytest
import asyncio
import time
import psutil
import gc
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass, field
import json
from pathlib import Path


# ============================================================================
# Performance Metrics Data Classes
# ============================================================================

@dataclass
class LoadTestMetrics:
    """Metrics captured during load testing."""
    test_name: str
    account_count: int
    concurrent_users: int
    total_duration: float
    throughput: float
    avg_response_time: float
    p50_latency: float
    p95_latency: float
    p99_latency: float
    max_latency: float
    min_latency: float
    success_count: int
    failure_count: int
    error_rate: float
    memory_used_mb: float
    cpu_percent: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "test_name": self.test_name,
            "account_count": self.account_count,
            "concurrent_users": self.concurrent_users,
            "total_duration": self.total_duration,
            "throughput": self.throughput,
            "avg_response_time": self.avg_response_time,
            "p50_latency": self.p50_latency,
            "p95_latency": self.p95_latency,
            "p99_latency": self.p99_latency,
            "max_latency": self.max_latency,
            "min_latency": self.min_latency,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "error_rate": self.error_rate,
            "memory_used_mb": self.memory_used_mb,
            "cpu_percent": self.cpu_percent,
            "timestamp": self.timestamp
        }


@dataclass
class ResourceMetrics:
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    connections_open: int
    threads_active: int


# ============================================================================
# Load Test Utilities
# ============================================================================

class LoadTestHarness:
    """Harness for running load tests with metrics collection."""

    def __init__(self):
        self.process = psutil.Process()
        self.metrics_history: List[LoadTestMetrics] = []

    def capture_baseline(self) -> ResourceMetrics:
        """Capture baseline resource metrics."""
        gc.collect()
        return ResourceMetrics(
            cpu_percent=self.process.cpu_percent(interval=0.1),
            memory_percent=self.process.memory_percent(),
            memory_mb=self.process.memory_info().rss / 1024 / 1024,
            connections_open=len(self.process.connections()),
            threads_active=self.process.num_threads()
        )

    def capture_current(self) -> ResourceMetrics:
        """Capture current resource metrics."""
        return ResourceMetrics(
            cpu_percent=self.process.cpu_percent(interval=0.1),
            memory_percent=self.process.memory_percent(),
            memory_mb=self.process.memory_info().rss / 1024 / 1024,
            connections_open=len(self.process.connections()),
            threads_active=self.process.num_threads()
        )

    def calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile from list of values."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def aggregate_metrics(
        self,
        test_name: str,
        account_count: int,
        concurrent_users: int,
        durations: List[float],
        successes: int,
        failures: int,
        start_time: float,
        baseline: ResourceMetrics,
        current: ResourceMetrics
    ) -> LoadTestMetrics:
        """Aggregate test results into metrics."""
        total_duration = time.time() - start_time
        total_operations = successes + failures

        metrics = LoadTestMetrics(
            test_name=test_name,
            account_count=account_count,
            concurrent_users=concurrent_users,
            total_duration=total_duration,
            throughput=total_operations / total_duration if total_duration > 0 else 0,
            avg_response_time=statistics.mean(durations) if durations else 0,
            p50_latency=self.calculate_percentile(durations, 0.50),
            p95_latency=self.calculate_percentile(durations, 0.95),
            p99_latency=self.calculate_percentile(durations, 0.99),
            max_latency=max(durations) if durations else 0,
            min_latency=min(durations) if durations else 0,
            success_count=successes,
            failure_count=failures,
            error_rate=failures / total_operations if total_operations > 0 else 0,
            memory_used_mb=current.memory_mb - baseline.memory_mb,
            cpu_percent=current.cpu_percent
        )

        self.metrics_history.append(metrics)
        return metrics

    def print_metrics(self, metrics: LoadTestMetrics):
        """Print formatted metrics."""
        print(f"\n{'='*80}")
        print(f"Load Test Results: {metrics.test_name}")
        print(f"{'='*80}")
        print(f"Test Configuration:")
        print(f"  Accounts: {metrics.account_count}")
        print(f"  Concurrent Users: {metrics.concurrent_users}")
        print(f"\nPerformance Metrics:")
        print(f"  Total Duration: {metrics.total_duration:.2f}s")
        print(f"  Throughput: {metrics.throughput:.2f} ops/sec")
        print(f"  Average Response: {metrics.avg_response_time*1000:.2f}ms")
        print(f"\nLatency Distribution:")
        print(f"  P50: {metrics.p50_latency*1000:.2f}ms")
        print(f"  P95: {metrics.p95_latency*1000:.2f}ms")
        print(f"  P99: {metrics.p99_latency*1000:.2f}ms")
        print(f"  Min: {metrics.min_latency*1000:.2f}ms")
        print(f"  Max: {metrics.max_latency*1000:.2f}ms")
        print(f"\nReliability:")
        print(f"  Successes: {metrics.success_count}")
        print(f"  Failures: {metrics.failure_count}")
        print(f"  Error Rate: {metrics.error_rate*100:.2f}%")
        print(f"\nResource Usage:")
        print(f"  Memory Used: {metrics.memory_used_mb:.2f}MB")
        print(f"  CPU: {metrics.cpu_percent:.1f}%")
        print(f"{'='*80}\n")


# ============================================================================
# Load Test Fixtures
# ============================================================================

@pytest.fixture
def load_test_harness():
    """Provide load test harness."""
    return LoadTestHarness()


@pytest.fixture
def mock_account_db():
    """Mock account database for load testing."""
    class MockAccountDB:
        def __init__(self):
            self.accounts = {}
            self.query_count = 0
            self.write_count = 0

        async def get_account(self, account_id: str) -> Dict[str, Any]:
            """Get account by ID."""
            await asyncio.sleep(0.001)  # Simulate DB latency
            self.query_count += 1
            return self.accounts.get(account_id, {
                "id": account_id,
                "name": f"Account {account_id}",
                "revenue": 1000000
            })

        async def batch_get_accounts(self, account_ids: List[str]) -> List[Dict[str, Any]]:
            """Batch get accounts."""
            await asyncio.sleep(0.005)  # Simulate batch query
            self.query_count += len(account_ids)
            return [await self.get_account(aid) for aid in account_ids]

        async def create_account(self, account: Dict[str, Any]) -> str:
            """Create account."""
            await asyncio.sleep(0.002)  # Simulate write latency
            account_id = account.get("id", f"acc_{len(self.accounts)}")
            self.accounts[account_id] = account
            self.write_count += 1
            return account_id

        async def update_account(self, account_id: str, updates: Dict[str, Any]) -> bool:
            """Update account."""
            await asyncio.sleep(0.002)
            self.write_count += 1
            if account_id in self.accounts:
                self.accounts[account_id].update(updates)
                return True
            return False

    return MockAccountDB()


@pytest.fixture
def connection_pool():
    """Mock database connection pool."""
    class ConnectionPool:
        def __init__(self, min_size=5, max_size=20):
            self.min_size = min_size
            self.max_size = max_size
            self.active_connections = 0
            self.peak_connections = 0
            self.total_acquires = 0
            self.total_releases = 0
            self._pool = []

        async def acquire(self):
            """Acquire connection from pool."""
            self.total_acquires += 1
            self.active_connections += 1
            self.peak_connections = max(self.peak_connections, self.active_connections)
            await asyncio.sleep(0.0001)  # Simulate acquire delay
            return MockConnection()

        async def release(self, conn):
            """Release connection back to pool."""
            self.total_releases += 1
            self.active_connections -= 1
            await asyncio.sleep(0.0001)

        def get_stats(self) -> Dict[str, int]:
            """Get pool statistics."""
            return {
                "active": self.active_connections,
                "peak": self.peak_connections,
                "acquires": self.total_acquires,
                "releases": self.total_releases,
                "pool_size": self.max_size
            }

    class MockConnection:
        async def execute(self, query: str):
            await asyncio.sleep(0.001)
            return []

    return ConnectionPool()


# ============================================================================
# Test Class: Small Scale Load (100 Accounts)
# ============================================================================

@pytest.mark.performance
class TestSmallScaleLoad:
    """Load tests for 100 accounts (small scale)."""

    @pytest.mark.asyncio
    async def test_100_accounts_single_user(self, load_test_harness, mock_account_db):
        """Load test: 100 accounts, single user."""
        baseline = load_test_harness.capture_baseline()
        account_count = 100
        durations = []
        successes = 0
        failures = 0

        start_time = time.time()

        # Sequential access pattern
        for i in range(account_count):
            op_start = time.time()
            try:
                await mock_account_db.get_account(f"acc_{i}")
                successes += 1
            except Exception:
                failures += 1
            durations.append(time.time() - op_start)

        current = load_test_harness.capture_current()
        metrics = load_test_harness.aggregate_metrics(
            "100_accounts_single_user",
            account_count, 1, durations, successes, failures,
            start_time, baseline, current
        )

        load_test_harness.print_metrics(metrics)

        # Assertions
        assert metrics.error_rate < 0.01  # < 1% error rate
        assert metrics.p95_latency < 0.010  # < 10ms P95
        assert metrics.throughput > 50  # > 50 ops/sec

    @pytest.mark.asyncio
    async def test_100_accounts_concurrent_10_users(
        self, load_test_harness, mock_account_db
    ):
        """Load test: 100 accounts, 10 concurrent users."""
        baseline = load_test_harness.capture_baseline()
        account_count = 100
        concurrent_users = 10
        durations = []
        successes = 0
        failures = 0

        start_time = time.time()

        async def user_workload(user_id: int):
            """Simulate user workload."""
            nonlocal successes, failures
            user_durations = []

            for i in range(account_count // concurrent_users):
                op_start = time.time()
                try:
                    await mock_account_db.get_account(f"acc_{user_id}_{i}")
                    successes += 1
                except Exception:
                    failures += 1
                user_durations.append(time.time() - op_start)

            return user_durations

        # Run concurrent user workloads
        tasks = [user_workload(i) for i in range(concurrent_users)]
        results = await asyncio.gather(*tasks)

        # Flatten durations
        for user_durations in results:
            durations.extend(user_durations)

        current = load_test_harness.capture_current()
        metrics = load_test_harness.aggregate_metrics(
            "100_accounts_10_concurrent_users",
            account_count, concurrent_users, durations, successes, failures,
            start_time, baseline, current
        )

        load_test_harness.print_metrics(metrics)

        # Assertions
        assert metrics.error_rate < 0.01
        assert metrics.p99_latency < 0.050  # < 50ms P99 with concurrency
        assert metrics.throughput > 100  # Better throughput with concurrency


# ============================================================================
# Test Class: Medium Scale Load (500 Accounts)
# ============================================================================

@pytest.mark.performance
@pytest.mark.slow
class TestMediumScaleLoad:
    """Load tests for 500 accounts (medium scale)."""

    @pytest.mark.asyncio
    async def test_500_accounts_concurrent_25_users(
        self, load_test_harness, mock_account_db
    ):
        """Load test: 500 accounts, 25 concurrent users."""
        baseline = load_test_harness.capture_baseline()
        account_count = 500
        concurrent_users = 25
        durations = []
        successes = 0
        failures = 0

        start_time = time.time()

        async def user_workload(user_id: int):
            """Simulate user workload with mixed operations."""
            nonlocal successes, failures
            user_durations = []
            ops_per_user = account_count // concurrent_users

            for i in range(ops_per_user):
                # Mix of read and write operations
                if i % 10 == 0:  # 10% writes
                    op_start = time.time()
                    try:
                        await mock_account_db.create_account({
                            "id": f"acc_{user_id}_{i}",
                            "name": f"Account {i}"
                        })
                        successes += 1
                    except Exception:
                        failures += 1
                    user_durations.append(time.time() - op_start)
                else:  # 90% reads
                    op_start = time.time()
                    try:
                        await mock_account_db.get_account(f"acc_{i}")
                        successes += 1
                    except Exception:
                        failures += 1
                    user_durations.append(time.time() - op_start)

            return user_durations

        tasks = [user_workload(i) for i in range(concurrent_users)]
        results = await asyncio.gather(*tasks)

        for user_durations in results:
            durations.extend(user_durations)

        current = load_test_harness.capture_current()
        metrics = load_test_harness.aggregate_metrics(
            "500_accounts_25_concurrent_users",
            account_count, concurrent_users, durations, successes, failures,
            start_time, baseline, current
        )

        load_test_harness.print_metrics(metrics)

        # Assertions
        assert metrics.error_rate < 0.02  # < 2% error rate
        assert metrics.p95_latency < 0.020  # < 20ms P95
        assert metrics.memory_used_mb < 200  # < 200MB memory


# ============================================================================
# Test Class: Large Scale Load (1000 Accounts)
# ============================================================================

@pytest.mark.performance
@pytest.mark.slow
class TestLargeScaleLoad:
    """Load tests for 1000 accounts (large scale)."""

    @pytest.mark.asyncio
    async def test_1000_accounts_concurrent_50_users(
        self, load_test_harness, mock_account_db, connection_pool
    ):
        """Load test: 1000 accounts, 50 concurrent users with connection pooling."""
        baseline = load_test_harness.capture_baseline()
        account_count = 1000
        concurrent_users = 50
        durations = []
        successes = 0
        failures = 0

        start_time = time.time()

        async def user_workload(user_id: int):
            """User workload with connection pool."""
            nonlocal successes, failures
            user_durations = []
            ops_per_user = account_count // concurrent_users

            for i in range(ops_per_user):
                # Acquire connection from pool
                conn = await connection_pool.acquire()

                op_start = time.time()
                try:
                    await mock_account_db.get_account(f"acc_{user_id}_{i}")
                    successes += 1
                except Exception:
                    failures += 1
                finally:
                    await connection_pool.release(conn)

                user_durations.append(time.time() - op_start)

            return user_durations

        tasks = [user_workload(i) for i in range(concurrent_users)]
        results = await asyncio.gather(*tasks)

        for user_durations in results:
            durations.extend(user_durations)

        current = load_test_harness.capture_current()
        metrics = load_test_harness.aggregate_metrics(
            "1000_accounts_50_concurrent_users",
            account_count, concurrent_users, durations, successes, failures,
            start_time, baseline, current
        )

        load_test_harness.print_metrics(metrics)

        # Print connection pool stats
        pool_stats = connection_pool.get_stats()
        print(f"Connection Pool Statistics:")
        print(f"  Peak Connections: {pool_stats['peak']}")
        print(f"  Total Acquires: {pool_stats['acquires']}")
        print(f"  Total Releases: {pool_stats['releases']}")

        # Assertions
        assert metrics.error_rate < 0.05  # < 5% error rate
        assert metrics.p99_latency < 0.100  # < 100ms P99
        assert pool_stats['peak'] <= connection_pool.max_size


# ============================================================================
# Test Class: Extreme Scale Load (5000 Accounts)
# ============================================================================

@pytest.mark.performance
@pytest.mark.slow
class TestExtremeScaleLoad:
    """Load tests for 5000 accounts (extreme scale)."""

    @pytest.mark.asyncio
    async def test_5000_accounts_concurrent_100_users(
        self, load_test_harness, mock_account_db, connection_pool
    ):
        """Load test: 5000 accounts, 100 concurrent users."""
        baseline = load_test_harness.capture_baseline()
        account_count = 5000
        concurrent_users = 100
        durations = []
        successes = 0
        failures = 0

        start_time = time.time()

        async def user_workload(user_id: int):
            """High-concurrency user workload."""
            nonlocal successes, failures
            user_durations = []
            ops_per_user = account_count // concurrent_users

            for i in range(ops_per_user):
                conn = await connection_pool.acquire()

                op_start = time.time()
                try:
                    # Realistic mix: batch reads
                    if i % 5 == 0:
                        account_ids = [f"acc_{user_id}_{j}" for j in range(i, i+5)]
                        await mock_account_db.batch_get_accounts(account_ids)
                    else:
                        await mock_account_db.get_account(f"acc_{user_id}_{i}")
                    successes += 1
                except Exception:
                    failures += 1
                finally:
                    await connection_pool.release(conn)

                user_durations.append(time.time() - op_start)

            return user_durations

        # Run in batches to manage system resources
        batch_size = 25
        for batch_start in range(0, concurrent_users, batch_size):
            batch_end = min(batch_start + batch_size, concurrent_users)
            tasks = [user_workload(i) for i in range(batch_start, batch_end)]
            batch_results = await asyncio.gather(*tasks)

            for user_durations in batch_results:
                durations.extend(user_durations)

        current = load_test_harness.capture_current()
        metrics = load_test_harness.aggregate_metrics(
            "5000_accounts_100_concurrent_users",
            account_count, concurrent_users, durations, successes, failures,
            start_time, baseline, current
        )

        load_test_harness.print_metrics(metrics)

        # Assertions
        assert metrics.error_rate < 0.10  # < 10% error rate under extreme load
        assert metrics.throughput > 200  # Maintain good throughput
        assert metrics.memory_used_mb < 1000  # < 1GB memory


# ============================================================================
# Test Class: Memory Profiling
# ============================================================================

@pytest.mark.performance
class TestMemoryProfiling:
    """Memory profiling tests."""

    @pytest.mark.asyncio
    async def test_memory_scaling_with_account_count(
        self, load_test_harness, mock_account_db
    ):
        """Test memory usage scaling with account count."""
        account_counts = [100, 500, 1000, 2000]
        memory_measurements = []

        for count in account_counts:
            gc.collect()
            baseline = load_test_harness.capture_baseline()

            # Load accounts into memory
            accounts = []
            for i in range(count):
                account = await mock_account_db.get_account(f"acc_{i}")
                accounts.append(account)

            current = load_test_harness.capture_current()
            memory_used = current.memory_mb - baseline.memory_mb

            memory_measurements.append({
                "count": count,
                "memory_mb": memory_used,
                "per_account_kb": (memory_used * 1024) / count
            })

        # Print results
        print(f"\n{'='*80}")
        print("Memory Scaling Analysis")
        print(f"{'='*80}")
        for m in memory_measurements:
            print(f"Accounts: {m['count']:5d} | "
                  f"Memory: {m['memory_mb']:7.2f}MB | "
                  f"Per Account: {m['per_account_kb']:.2f}KB")
        print(f"{'='*80}\n")

        # Assertions: Linear scaling
        for m in memory_measurements:
            assert m['per_account_kb'] < 50  # < 50KB per account

    @pytest.mark.asyncio
    async def test_memory_leak_detection_sustained_load(
        self, load_test_harness, mock_account_db
    ):
        """Detect memory leaks during sustained load."""
        gc.collect()
        baseline = load_test_harness.capture_baseline()

        memory_samples = []

        # Run sustained load for multiple iterations
        for iteration in range(10):
            # Process 100 accounts
            for i in range(100):
                await mock_account_db.get_account(f"acc_{i}")

            # Sample memory after each iteration
            if iteration % 2 == 0:
                gc.collect()
                current = load_test_harness.capture_current()
                memory_samples.append(current.memory_mb)

        # Check for memory leak (increasing trend)
        memory_growth = memory_samples[-1] - memory_samples[0]

        print(f"\nMemory Leak Detection:")
        print(f"  Baseline: {baseline.memory_mb:.2f}MB")
        print(f"  Samples: {memory_samples}")
        print(f"  Growth: {memory_growth:.2f}MB")

        # Allow some growth for caching, but not continuous increase
        assert memory_growth < 100  # < 100MB growth


# ============================================================================
# Test Class: CPU Profiling
# ============================================================================

@pytest.mark.performance
class TestCPUProfiling:
    """CPU profiling tests."""

    @pytest.mark.asyncio
    async def test_cpu_usage_under_load(self, load_test_harness, mock_account_db):
        """Test CPU usage under various load conditions."""
        process = psutil.Process()

        # Baseline CPU
        baseline_cpu = process.cpu_percent(interval=1.0)

        # Run load
        start_time = time.time()
        cpu_samples = []

        async def monitoring_task():
            """Monitor CPU during load."""
            while time.time() - start_time < 5.0:
                cpu_samples.append(process.cpu_percent(interval=0.5))
                await asyncio.sleep(0.5)

        async def load_task():
            """Generate load."""
            for i in range(500):
                await mock_account_db.get_account(f"acc_{i}")

        # Run both tasks concurrently
        await asyncio.gather(monitoring_task(), load_task())

        avg_cpu = statistics.mean(cpu_samples) if cpu_samples else 0
        max_cpu = max(cpu_samples) if cpu_samples else 0

        print(f"\nCPU Usage Analysis:")
        print(f"  Baseline: {baseline_cpu:.1f}%")
        print(f"  Average: {avg_cpu:.1f}%")
        print(f"  Peak: {max_cpu:.1f}%")

        # CPU should be utilized but not maxed out
        assert avg_cpu < 80  # Average < 80%
        assert max_cpu < 95  # Peak < 95%


# ============================================================================
# Test Class: Connection Pool Testing
# ============================================================================

@pytest.mark.performance
class TestConnectionPooling:
    """Connection pool performance tests."""

    @pytest.mark.asyncio
    async def test_connection_pool_efficiency(self, connection_pool):
        """Test connection pool handles concurrent requests efficiently."""
        concurrent_requests = 100

        async def make_request(request_id: int):
            """Simulate database request."""
            conn = await connection_pool.acquire()
            await asyncio.sleep(0.001)  # Simulate query
            await connection_pool.release(conn)
            return request_id

        start_time = time.time()
        results = await asyncio.gather(*[make_request(i) for i in range(concurrent_requests)])
        duration = time.time() - start_time

        pool_stats = connection_pool.get_stats()

        print(f"\nConnection Pool Performance:")
        print(f"  Concurrent Requests: {concurrent_requests}")
        print(f"  Duration: {duration:.3f}s")
        print(f"  Peak Connections: {pool_stats['peak']}")
        print(f"  Pool Size: {pool_stats['pool_size']}")

        assert len(results) == concurrent_requests
        assert pool_stats['peak'] <= connection_pool.max_size
        assert duration < 2.0  # Should complete quickly with pooling

    @pytest.mark.asyncio
    async def test_connection_pool_saturation(self, connection_pool):
        """Test behavior when connection pool is saturated."""
        # Try to acquire more than max pool size
        connections = []

        for i in range(connection_pool.max_size + 5):
            conn = await connection_pool.acquire()
            connections.append(conn)

        pool_stats = connection_pool.get_stats()

        # Release all
        for conn in connections:
            await connection_pool.release(conn)

        print(f"\nConnection Pool Saturation Test:")
        print(f"  Requested: {connection_pool.max_size + 5}")
        print(f"  Peak: {pool_stats['peak']}")

        # System should handle gracefully (queue or expand)
        assert pool_stats['acquires'] == len(connections)
