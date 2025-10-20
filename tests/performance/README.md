# Performance Testing Suite - Week 13

Comprehensive performance testing and optimization for Sergas Super Account Manager.

## Overview

This directory contains production-ready performance tests covering:
- **Load Testing** (100-5000 accounts, 1-100 concurrent users)
- **Latency Benchmarking** (API, database, cache, end-to-end)
- **Scalability Testing** (horizontal scaling, partitioning, sharding)

## Test Files

| File | Lines | Description |
|------|-------|-------------|
| `test_load.py` | 802 | Load testing with concurrent users and resource monitoring |
| `test_latency.py` | 695 | Response time benchmarks and latency analysis |
| `test_scalability.py` | 706 | Scalability tests for workers, partitions, and cache |
| `test_memory_performance.py` | 605 | Memory profiling tests (existing) |
| `test_sdk_performance.py` | 418 | SDK performance tests (existing) |

**Total:** 3,226 lines of performance test code

## Running Tests

### Quick Start

```bash
# Run all performance tests
pytest tests/performance/ -v

# Run specific test suite
pytest tests/performance/test_load.py -v
pytest tests/performance/test_latency.py -v
pytest tests/performance/test_scalability.py -v

# Run only fast tests (exclude slow tests)
pytest tests/performance/ -v -m "performance and not slow"
```

### Run Specific Test Classes

```bash
# Load Testing
pytest tests/performance/test_load.py::TestSmallScaleLoad -v
pytest tests/performance/test_load.py::TestMediumScaleLoad -v
pytest tests/performance/test_load.py::TestLargeScaleLoad -v
pytest tests/performance/test_load.py::TestExtremeScaleLoad -v

# Latency Testing
pytest tests/performance/test_latency.py::TestResponseTimeBenchmarks -v
pytest tests/performance/test_latency.py::TestDatabaseQueryPerformance -v
pytest tests/performance/test_latency.py::TestCacheEffectiveness -v

# Scalability Testing
pytest tests/performance/test_scalability.py::TestHorizontalScaling -v
pytest tests/performance/test_scalability.py::TestDatabasePartitioning -v
pytest tests/performance/test_scalability.py::TestRedisCacheScaling -v
```

### Run Individual Tests

```bash
# Load test: 100 accounts, single user
pytest tests/performance/test_load.py::TestSmallScaleLoad::test_100_accounts_single_user -v

# Load test: 5000 accounts, 100 concurrent users
pytest tests/performance/test_load.py::TestExtremeScaleLoad::test_5000_accounts_concurrent_100_users -v

# Latency test: API endpoint
pytest tests/performance/test_latency.py::TestResponseTimeBenchmarks::test_api_endpoint_get_account_latency -v

# Scalability test: horizontal scaling
pytest tests/performance/test_scalability.py::TestHorizontalScaling::test_throughput_scaling_with_workers -v
```

### Pytest Markers

```bash
# Run only performance tests
pytest -m performance -v

# Run only slow tests (> 5 seconds)
pytest -m slow -v

# Exclude slow tests
pytest -m "performance and not slow" -v
```

## Test Structure

### Load Testing (`test_load.py`)

**Test Classes:**
1. `TestSmallScaleLoad` - 100 accounts
   - Single user workload
   - 10 concurrent users

2. `TestMediumScaleLoad` - 500 accounts
   - 25 concurrent users
   - Mixed read/write operations

3. `TestLargeScaleLoad` - 1,000 accounts
   - 50 concurrent users
   - Connection pool testing

4. `TestExtremeScaleLoad` - 5,000 accounts
   - 100 concurrent users
   - Batch processing

5. `TestMemoryProfiling`
   - Memory scaling analysis
   - Memory leak detection

6. `TestCPUProfiling`
   - CPU usage monitoring

7. `TestConnectionPooling`
   - Pool efficiency
   - Saturation handling

### Latency Testing (`test_latency.py`)

**Test Classes:**
1. `TestResponseTimeBenchmarks`
   - API endpoint latency (GET, POST, PATCH)
   - P50, P95, P99 measurements

2. `TestDatabaseQueryPerformance`
   - Simple indexed queries
   - Complex queries (joins + aggregations)
   - Analytical queries
   - Batch operations

3. `TestCacheEffectiveness`
   - Cache hit vs miss latency
   - Hit rate effectiveness
   - Write-through performance

4. `TestEndToEndLatency`
   - Full stack traversal
   - Cache + DB + API

5. `TestConcurrentRequestLatency`
   - Latency under load
   - Concurrency levels: 1, 10, 50, 100

### Scalability Testing (`test_scalability.py`)

**Test Classes:**
1. `TestHorizontalScaling`
   - Throughput scaling (1, 2, 4, 8 workers)
   - CPU-bound task scaling

2. `TestWorkerParallelization`
   - Task distribution
   - Parallel processing speedup
   - Pool saturation handling

3. `TestDatabasePartitioning`
   - Partition distribution
   - Parallel queries
   - Scalability (2, 4, 8 partitions)

4. `TestRedisCacheScaling`
   - Shard distribution
   - Concurrent access scaling

5. `TestLoadDistribution`
   - Round-robin
   - Least-connections

6. `TestThroughputScaling`
   - Data size scaling

## Test Output

### Metrics Reported

Each test provides detailed metrics:

```
================================================================================
Load Test Results: 1000_accounts_50_concurrent_users
================================================================================
Test Configuration:
  Accounts: 1000
  Concurrent Users: 50

Performance Metrics:
  Total Duration: 5.23s
  Throughput: 191.23 ops/sec
  Average Response: 8.45ms

Latency Distribution:
  P50: 7.20ms
  P95: 16.30ms
  P99: 24.80ms
  Min: 4.50ms
  Max: 45.67ms

Reliability:
  Successes: 980
  Failures: 20
  Error Rate: 2.00%

Resource Usage:
  Memory Used: 174.23MB
  CPU: 56.8%
================================================================================
```

## Success Criteria

Tests validate against these SLA targets:

| Metric | Target | Critical |
|--------|--------|----------|
| API P95 Latency | < 20ms | < 50ms |
| API P99 Latency | < 50ms | < 100ms |
| DB Query P95 | < 10ms | < 30ms |
| Cache Hit Rate | > 80% | > 60% |
| Throughput | > 100 ops/sec | > 50 ops/sec |
| Error Rate | < 1% | < 5% |
| Memory @ 1K accounts | < 500MB | < 1GB |
| Scaling Efficiency | > 70% | > 50% |

## Configuration

### Test Configuration Options

Tests are configured via fixtures in `conftest.py`:

```python
# Load test harness
@pytest.fixture
def load_test_harness():
    return LoadTestHarness()

# Mock database
@pytest.fixture
def mock_account_db():
    return MockAccountDB()

# Connection pool
@pytest.fixture
def connection_pool():
    return ConnectionPool(min_size=5, max_size=20)
```

### Environment Variables

```bash
# Optional: Configure test timeouts
export PYTEST_TIMEOUT=300  # 5 minutes for slow tests

# Optional: Configure resource limits
export MAX_WORKERS=8
export MAX_MEMORY_MB=2048
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Performance Tests

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.14'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run performance tests
        run: |
          pytest tests/performance/ -v --tb=short
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: performance-results
          path: performance-report.html
```

## Optimization Implementations

Related optimization implementations in `/src/optimizations/`:

| Module | Lines | Description |
|--------|-------|-------------|
| `query_optimizer.py` | 509 | Database query optimization |
| `cache_manager.py` | 461 | Multi-level caching |
| `parallel_processor.py` | 470 | Parallel processing |
| `connection_pool.py` | 414 | Connection pool management |

**Total:** 1,854 lines of optimization code

## Reports

See comprehensive performance analysis:
- **`/docs/performance_report.md`** - Full performance testing report with analysis and recommendations

## Troubleshooting

### Tests Running Slowly

```bash
# Run only fast tests
pytest tests/performance/ -m "not slow" -v

# Reduce test data size
pytest tests/performance/test_load.py::TestSmallScaleLoad -v
```

### Memory Issues

```bash
# Run tests with memory limits
pytest tests/performance/ --memray -v

# Run single test at a time
pytest tests/performance/test_load.py::TestSmallScaleLoad::test_100_accounts_single_user -v
```

### Connection Pool Errors

Check connection pool configuration in fixtures:
- `min_size`: Minimum connections
- `max_size`: Maximum connections
- Ensure `max_size >= concurrent_users / 5`

## Best Practices

1. **Run performance tests regularly** (weekly or before major releases)
2. **Compare results to baseline** in performance report
3. **Monitor for regressions** - P95 latency increases > 20%
4. **Profile bottlenecks** using test output metrics
5. **Update success criteria** as system evolves

## Contributing

When adding new performance tests:

1. Follow existing test structure
2. Include comprehensive metrics collection
3. Add test to appropriate test class
4. Document success criteria
5. Update this README

## Related Documentation

- `/docs/performance_report.md` - Full performance analysis
- `/tests/conftest.py` - Global test fixtures
- `/src/optimizations/README.md` - Optimization implementations

---

**Last Updated:** 2025-10-19
**Author:** Performance Testing Engineer
**Status:** Production-Ready
