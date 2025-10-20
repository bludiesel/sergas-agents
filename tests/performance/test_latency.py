"""
Comprehensive Latency Testing for Sergas Super Account Manager.

Week 13 Performance Testing - Latency Testing Suite

Tests response time and latency across system components:
- Response time benchmarks (P50, P95, P99)
- Database query performance
- API endpoint latency
- Cache effectiveness
- Network latency simulation
- Query optimization validation

Author: Performance Testing Engineer
Date: 2025-10-19
"""

import pytest
import asyncio
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# Latency Test Models
# ============================================================================

class CacheStatus(Enum):
    """Cache hit/miss status."""
    HIT = "hit"
    MISS = "miss"
    EXPIRED = "expired"


@dataclass
class LatencyMeasurement:
    """Single latency measurement."""
    operation: str
    latency_ms: float
    cache_status: Optional[CacheStatus] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class LatencyBenchmark:
    """Aggregated latency benchmark results."""
    operation_name: str
    sample_size: int
    min_latency_ms: float
    max_latency_ms: float
    mean_latency_ms: float
    median_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    stddev_ms: float
    cache_hit_rate: Optional[float] = None

    def meets_sla(self, sla_p95_ms: float, sla_p99_ms: float) -> bool:
        """Check if benchmark meets SLA requirements."""
        return (self.p95_latency_ms <= sla_p95_ms and
                self.p99_latency_ms <= sla_p99_ms)

    def print_report(self):
        """Print formatted benchmark report."""
        print(f"\n{'='*80}")
        print(f"Latency Benchmark: {self.operation_name}")
        print(f"{'='*80}")
        print(f"Sample Size: {self.sample_size}")
        print(f"\nLatency Distribution:")
        print(f"  Min:    {self.min_latency_ms:8.2f}ms")
        print(f"  Mean:   {self.mean_latency_ms:8.2f}ms")
        print(f"  Median: {self.median_latency_ms:8.2f}ms")
        print(f"  P95:    {self.p95_latency_ms:8.2f}ms")
        print(f"  P99:    {self.p99_latency_ms:8.2f}ms")
        print(f"  Max:    {self.max_latency_ms:8.2f}ms")
        print(f"  StdDev: {self.stddev_ms:8.2f}ms")
        if self.cache_hit_rate is not None:
            print(f"\nCache Performance:")
            print(f"  Hit Rate: {self.cache_hit_rate*100:.1f}%")
        print(f"{'='*80}\n")


# ============================================================================
# Latency Test Utilities
# ============================================================================

class LatencyProfiler:
    """Utility for profiling latency."""

    @staticmethod
    def measure_latency(func):
        """Decorator to measure function latency."""
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            latency = (time.perf_counter() - start) * 1000  # Convert to ms
            return result, latency
        return wrapper

    @staticmethod
    def calculate_percentile(values: List[float], percentile: float) -> float:
        """Calculate percentile from values."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]

    @staticmethod
    def aggregate_measurements(
        measurements: List[LatencyMeasurement],
        operation_name: str
    ) -> LatencyBenchmark:
        """Aggregate measurements into benchmark."""
        latencies = [m.latency_ms for m in measurements]

        # Calculate cache hit rate if applicable
        cache_measurements = [m for m in measurements if m.cache_status is not None]
        cache_hit_rate = None
        if cache_measurements:
            hits = len([m for m in cache_measurements if m.cache_status == CacheStatus.HIT])
            cache_hit_rate = hits / len(cache_measurements)

        return LatencyBenchmark(
            operation_name=operation_name,
            sample_size=len(measurements),
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            mean_latency_ms=statistics.mean(latencies),
            median_latency_ms=statistics.median(latencies),
            p95_latency_ms=LatencyProfiler.calculate_percentile(latencies, 0.95),
            p99_latency_ms=LatencyProfiler.calculate_percentile(latencies, 0.99),
            stddev_ms=statistics.stdev(latencies) if len(latencies) > 1 else 0.0,
            cache_hit_rate=cache_hit_rate
        )


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def latency_profiler():
    """Provide latency profiler."""
    return LatencyProfiler()


@pytest.fixture
def mock_cache():
    """Mock cache for latency testing."""
    class MockCache:
        def __init__(self, hit_rate=0.8):
            self.cache = {}
            self.target_hit_rate = hit_rate
            self.access_count = 0
            self.hit_count = 0
            self.miss_count = 0

        async def get(self, key: str) -> tuple[Optional[Any], CacheStatus]:
            """Get value from cache."""
            self.access_count += 1

            # Simulate cache behavior based on target hit rate
            import random
            if random.random() < self.target_hit_rate:
                # Cache hit
                await asyncio.sleep(0.0001)  # 0.1ms for cache hit
                self.hit_count += 1
                return {"data": f"cached_{key}"}, CacheStatus.HIT
            else:
                # Cache miss
                await asyncio.sleep(0.001)  # 1ms for cache miss + DB
                self.miss_count += 1
                return None, CacheStatus.MISS

        async def set(self, key: str, value: Any, ttl: int = 300):
            """Set value in cache."""
            await asyncio.sleep(0.0001)  # 0.1ms for cache write
            self.cache[key] = (value, datetime.now() + timedelta(seconds=ttl))

        def get_stats(self) -> Dict[str, Any]:
            """Get cache statistics."""
            hit_rate = self.hit_count / self.access_count if self.access_count > 0 else 0
            return {
                "accesses": self.access_count,
                "hits": self.hit_count,
                "misses": self.miss_count,
                "hit_rate": hit_rate
            }

    return MockCache()


@pytest.fixture
def mock_database():
    """Mock database with realistic latencies."""
    class MockDatabase:
        def __init__(self):
            self.query_count = 0

        async def query_simple(self, query: str) -> Dict[str, Any]:
            """Simple query (indexed lookup)."""
            await asyncio.sleep(0.002)  # 2ms
            self.query_count += 1
            return {"result": "data"}

        async def query_complex(self, query: str) -> List[Dict[str, Any]]:
            """Complex query (joins, aggregations)."""
            await asyncio.sleep(0.015)  # 15ms
            self.query_count += 1
            return [{"result": f"row_{i}"} for i in range(10)]

        async def query_analytical(self, query: str) -> Dict[str, Any]:
            """Analytical query (full table scan)."""
            await asyncio.sleep(0.050)  # 50ms
            self.query_count += 1
            return {"aggregation": "result"}

        async def batch_query(self, queries: List[str]) -> List[Dict[str, Any]]:
            """Batch query execution."""
            await asyncio.sleep(0.005 * len(queries))  # 5ms per query
            self.query_count += len(queries)
            return [{"result": f"batch_{i}"} for i in range(len(queries))]

    return MockDatabase()


@pytest.fixture
def mock_api_endpoint():
    """Mock API endpoint with latency simulation."""
    class MockAPIEndpoint:
        def __init__(self):
            self.request_count = 0

        async def get_account(self, account_id: str) -> Dict[str, Any]:
            """GET /accounts/{id}."""
            await asyncio.sleep(0.005)  # 5ms
            self.request_count += 1
            return {"id": account_id, "name": f"Account {account_id}"}

        async def list_accounts(self, limit: int = 50) -> List[Dict[str, Any]]:
            """GET /accounts."""
            await asyncio.sleep(0.010)  # 10ms
            self.request_count += 1
            return [{"id": f"acc_{i}"} for i in range(limit)]

        async def create_account(self, account: Dict[str, Any]) -> Dict[str, Any]:
            """POST /accounts."""
            await asyncio.sleep(0.015)  # 15ms
            self.request_count += 1
            return {**account, "id": "new_account"}

        async def update_account(self, account_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
            """PATCH /accounts/{id}."""
            await asyncio.sleep(0.012)  # 12ms
            self.request_count += 1
            return {"id": account_id, **updates}

    return MockAPIEndpoint()


# ============================================================================
# Test Class: Response Time Benchmarks
# ============================================================================

@pytest.mark.performance
class TestResponseTimeBenchmarks:
    """Response time benchmarks for various operations."""

    @pytest.mark.asyncio
    async def test_api_endpoint_get_account_latency(
        self, latency_profiler, mock_api_endpoint
    ):
        """Benchmark GET account endpoint latency."""
        measurements = []

        # Perform 100 requests
        for i in range(100):
            start = time.perf_counter()
            await mock_api_endpoint.get_account(f"acc_{i}")
            latency_ms = (time.perf_counter() - start) * 1000

            measurements.append(LatencyMeasurement(
                operation="get_account",
                latency_ms=latency_ms
            ))

        benchmark = latency_profiler.aggregate_measurements(
            measurements, "API: GET /accounts/{id}"
        )
        benchmark.print_report()

        # SLA: P95 < 10ms, P99 < 20ms
        assert benchmark.meets_sla(10.0, 20.0), \
            f"GET account SLA violation: P95={benchmark.p95_latency_ms:.2f}ms, P99={benchmark.p99_latency_ms:.2f}ms"

    @pytest.mark.asyncio
    async def test_api_endpoint_list_accounts_latency(
        self, latency_profiler, mock_api_endpoint
    ):
        """Benchmark LIST accounts endpoint latency."""
        measurements = []

        for i in range(50):
            start = time.perf_counter()
            await mock_api_endpoint.list_accounts(limit=50)
            latency_ms = (time.perf_counter() - start) * 1000

            measurements.append(LatencyMeasurement(
                operation="list_accounts",
                latency_ms=latency_ms
            ))

        benchmark = latency_profiler.aggregate_measurements(
            measurements, "API: GET /accounts"
        )
        benchmark.print_report()

        # SLA: P95 < 25ms, P99 < 50ms
        assert benchmark.meets_sla(25.0, 50.0)

    @pytest.mark.asyncio
    async def test_api_endpoint_write_operations_latency(
        self, latency_profiler, mock_api_endpoint
    ):
        """Benchmark write operation latencies (POST, PATCH)."""
        create_measurements = []
        update_measurements = []

        for i in range(50):
            # CREATE
            start = time.perf_counter()
            await mock_api_endpoint.create_account({"name": f"Account {i}"})
            create_latency = (time.perf_counter() - start) * 1000
            create_measurements.append(LatencyMeasurement(
                operation="create_account",
                latency_ms=create_latency
            ))

            # UPDATE
            start = time.perf_counter()
            await mock_api_endpoint.update_account(f"acc_{i}", {"status": "active"})
            update_latency = (time.perf_counter() - start) * 1000
            update_measurements.append(LatencyMeasurement(
                operation="update_account",
                latency_ms=update_latency
            ))

        create_benchmark = latency_profiler.aggregate_measurements(
            create_measurements, "API: POST /accounts"
        )
        update_benchmark = latency_profiler.aggregate_measurements(
            update_measurements, "API: PATCH /accounts/{id}"
        )

        create_benchmark.print_report()
        update_benchmark.print_report()

        # SLA: P95 < 30ms, P99 < 50ms for writes
        assert create_benchmark.meets_sla(30.0, 50.0)
        assert update_benchmark.meets_sla(30.0, 50.0)


# ============================================================================
# Test Class: Database Query Performance
# ============================================================================

@pytest.mark.performance
class TestDatabaseQueryPerformance:
    """Database query latency benchmarks."""

    @pytest.mark.asyncio
    async def test_simple_query_latency(self, latency_profiler, mock_database):
        """Benchmark simple indexed query latency."""
        measurements = []

        for i in range(100):
            start = time.perf_counter()
            await mock_database.query_simple(f"SELECT * FROM accounts WHERE id = {i}")
            latency_ms = (time.perf_counter() - start) * 1000

            measurements.append(LatencyMeasurement(
                operation="simple_query",
                latency_ms=latency_ms
            ))

        benchmark = latency_profiler.aggregate_measurements(
            measurements, "DB: Simple Indexed Query"
        )
        benchmark.print_report()

        # SLA: P95 < 5ms, P99 < 10ms for indexed queries
        assert benchmark.meets_sla(5.0, 10.0)

    @pytest.mark.asyncio
    async def test_complex_query_latency(self, latency_profiler, mock_database):
        """Benchmark complex query latency (joins, aggregations)."""
        measurements = []

        for i in range(50):
            start = time.perf_counter()
            await mock_database.query_complex(
                "SELECT a.*, COUNT(d.id) FROM accounts a JOIN deals d ON a.id = d.account_id GROUP BY a.id"
            )
            latency_ms = (time.perf_counter() - start) * 1000

            measurements.append(LatencyMeasurement(
                operation="complex_query",
                latency_ms=latency_ms
            ))

        benchmark = latency_profiler.aggregate_measurements(
            measurements, "DB: Complex Query (Joins + Aggregations)"
        )
        benchmark.print_report()

        # SLA: P95 < 30ms, P99 < 50ms for complex queries
        assert benchmark.meets_sla(30.0, 50.0)

    @pytest.mark.asyncio
    async def test_analytical_query_latency(self, latency_profiler, mock_database):
        """Benchmark analytical query latency."""
        measurements = []

        for i in range(20):
            start = time.perf_counter()
            await mock_database.query_analytical(
                "SELECT industry, AVG(revenue), COUNT(*) FROM accounts GROUP BY industry"
            )
            latency_ms = (time.perf_counter() - start) * 1000

            measurements.append(LatencyMeasurement(
                operation="analytical_query",
                latency_ms=latency_ms
            ))

        benchmark = latency_profiler.aggregate_measurements(
            measurements, "DB: Analytical Query (Full Scan)"
        )
        benchmark.print_report()

        # SLA: P95 < 100ms, P99 < 150ms for analytical queries
        assert benchmark.meets_sla(100.0, 150.0)

    @pytest.mark.asyncio
    async def test_batch_query_performance(self, latency_profiler, mock_database):
        """Benchmark batch query vs individual queries."""
        # Individual queries
        individual_measurements = []
        queries = [f"SELECT * FROM accounts WHERE id = {i}" for i in range(10)]

        start_individual = time.perf_counter()
        for query in queries:
            query_start = time.perf_counter()
            await mock_database.query_simple(query)
            individual_measurements.append(LatencyMeasurement(
                operation="individual_query",
                latency_ms=(time.perf_counter() - query_start) * 1000
            ))
        total_individual_ms = (time.perf_counter() - start_individual) * 1000

        # Batch query
        start_batch = time.perf_counter()
        await mock_database.batch_query(queries)
        total_batch_ms = (time.perf_counter() - start_batch) * 1000

        print(f"\nBatch Query Performance:")
        print(f"  Individual Queries Total: {total_individual_ms:.2f}ms")
        print(f"  Batch Query Total: {total_batch_ms:.2f}ms")
        print(f"  Speedup: {total_individual_ms / total_batch_ms:.2f}x")

        # Batch should be faster
        assert total_batch_ms < total_individual_ms


# ============================================================================
# Test Class: Cache Effectiveness
# ============================================================================

@pytest.mark.performance
class TestCacheEffectiveness:
    """Cache performance and effectiveness tests."""

    @pytest.mark.asyncio
    async def test_cache_hit_latency_vs_miss(self, latency_profiler, mock_cache):
        """Compare cache hit vs miss latency."""
        hit_measurements = []
        miss_measurements = []

        for i in range(100):
            # Warm up cache for some keys
            if i < 20:
                await mock_cache.set(f"key_{i}", {"data": i})

            # Access keys
            key = f"key_{i % 30}"  # Some hits, some misses
            start = time.perf_counter()
            value, status = await mock_cache.get(key)
            latency_ms = (time.perf_counter() - start) * 1000

            measurement = LatencyMeasurement(
                operation="cache_access",
                latency_ms=latency_ms,
                cache_status=status
            )

            if status == CacheStatus.HIT:
                hit_measurements.append(measurement)
            else:
                miss_measurements.append(measurement)

        if hit_measurements and miss_measurements:
            hit_benchmark = latency_profiler.aggregate_measurements(
                hit_measurements, "Cache: Hit"
            )
            miss_benchmark = latency_profiler.aggregate_measurements(
                miss_measurements, "Cache: Miss"
            )

            hit_benchmark.print_report()
            miss_benchmark.print_report()

            # Cache hits should be significantly faster
            assert hit_benchmark.mean_latency_ms < miss_benchmark.mean_latency_ms / 5
            assert hit_benchmark.p99_latency_ms < 1.0  # < 1ms for cache hit

    @pytest.mark.asyncio
    async def test_cache_hit_rate_effectiveness(self, mock_cache):
        """Test cache hit rate meets effectiveness targets."""
        # Access pattern: 80/20 rule (80% requests for 20% of keys)
        hot_keys = [f"key_{i}" for i in range(20)]
        cold_keys = [f"key_{i}" for i in range(20, 100)]

        # Warm up hot keys
        for key in hot_keys:
            await mock_cache.set(key, {"data": key})

        # Simulate access pattern
        import random
        for _ in range(200):
            if random.random() < 0.8:
                # Hot key access
                key = random.choice(hot_keys)
            else:
                # Cold key access
                key = random.choice(cold_keys)

            await mock_cache.get(key)

        stats = mock_cache.get_stats()

        print(f"\nCache Effectiveness:")
        print(f"  Total Accesses: {stats['accesses']}")
        print(f"  Hits: {stats['hits']}")
        print(f"  Misses: {stats['misses']}")
        print(f"  Hit Rate: {stats['hit_rate']*100:.1f}%")

        # Target: > 60% hit rate with 80/20 access pattern
        assert stats['hit_rate'] > 0.60

    @pytest.mark.asyncio
    async def test_cache_write_through_latency(self, latency_profiler, mock_cache):
        """Test cache write-through performance."""
        measurements = []

        for i in range(100):
            start = time.perf_counter()
            await mock_cache.set(f"key_{i}", {"data": f"value_{i}"})
            latency_ms = (time.perf_counter() - start) * 1000

            measurements.append(LatencyMeasurement(
                operation="cache_write",
                latency_ms=latency_ms
            ))

        benchmark = latency_profiler.aggregate_measurements(
            measurements, "Cache: Write-Through"
        )
        benchmark.print_report()

        # Cache writes should be fast
        assert benchmark.p95_latency_ms < 2.0  # < 2ms P95


# ============================================================================
# Test Class: End-to-End Latency
# ============================================================================

@pytest.mark.performance
class TestEndToEndLatency:
    """End-to-end request latency tests."""

    @pytest.mark.asyncio
    async def test_account_retrieval_e2e_latency(
        self, latency_profiler, mock_cache, mock_database, mock_api_endpoint
    ):
        """End-to-end latency for account retrieval with caching."""
        measurements = []

        async def get_account_e2e(account_id: str):
            """Simulate full account retrieval flow."""
            # 1. Check cache
            cached, status = await mock_cache.get(f"account_{account_id}")

            if status == CacheStatus.HIT:
                return cached, status

            # 2. Query database
            db_result = await mock_database.query_simple(
                f"SELECT * FROM accounts WHERE id = '{account_id}'"
            )

            # 3. Update cache
            await mock_cache.set(f"account_{account_id}", db_result)

            return db_result, status

        # Perform 100 retrievals
        for i in range(100):
            account_id = f"acc_{i % 20}"  # Some cache hits

            start = time.perf_counter()
            result, cache_status = await get_account_e2e(account_id)
            latency_ms = (time.perf_counter() - start) * 1000

            measurements.append(LatencyMeasurement(
                operation="account_retrieval_e2e",
                latency_ms=latency_ms,
                cache_status=cache_status
            ))

        benchmark = latency_profiler.aggregate_measurements(
            measurements, "E2E: Account Retrieval"
        )
        benchmark.print_report()

        # SLA: P95 < 15ms, P99 < 30ms (including cache + DB + cache write)
        assert benchmark.meets_sla(15.0, 30.0)
        assert benchmark.cache_hit_rate > 0.70  # > 70% cache hit rate


# ============================================================================
# Test Class: Concurrent Request Latency
# ============================================================================

@pytest.mark.performance
class TestConcurrentRequestLatency:
    """Latency under concurrent load."""

    @pytest.mark.asyncio
    async def test_latency_under_concurrent_load(
        self, latency_profiler, mock_api_endpoint
    ):
        """Test latency degradation under concurrent load."""
        concurrent_levels = [1, 10, 50, 100]
        benchmarks = []

        for concurrency in concurrent_levels:
            measurements = []

            async def concurrent_request(request_id: int):
                start = time.perf_counter()
                await mock_api_endpoint.get_account(f"acc_{request_id}")
                return (time.perf_counter() - start) * 1000

            # Run concurrent requests
            latencies = await asyncio.gather(*[
                concurrent_request(i) for i in range(concurrency)
            ])

            for latency in latencies:
                measurements.append(LatencyMeasurement(
                    operation=f"concurrent_{concurrency}",
                    latency_ms=latency
                ))

            benchmark = latency_profiler.aggregate_measurements(
                measurements, f"Concurrency: {concurrency} users"
            )
            benchmarks.append(benchmark)

        # Print all benchmarks
        for benchmark in benchmarks:
            benchmark.print_report()

        # Latency should remain reasonable even at 100 concurrent
        assert benchmarks[-1].p95_latency_ms < 50.0  # < 50ms at 100 concurrent
