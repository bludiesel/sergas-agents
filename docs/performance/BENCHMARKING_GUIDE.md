# Performance Benchmarking Guide

**Sergas Super Account Manager - Week 8 Performance Testing**

---

## Overview

This guide explains how to run and interpret performance benchmarks for the AG UI Protocol streaming implementation.

---

## Quick Start

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Run all benchmarks
pytest tests/performance/test_ag_ui_streaming_benchmarks.py -v -m performance --no-cov -s

# 3. Or use automation script
./scripts/run_benchmarks.sh
```

---

## Benchmark Suite Components

### 1. Pytest Benchmarks (Primary)

**File**: `tests/performance/test_ag_ui_streaming_benchmarks.py`

**Tests**:
- ✅ `test_event_streaming_latency` - NFR-P01 compliance (< 200ms)
- ✅ `test_concurrent_streams` - Concurrent handling (10+ streams)
- ✅ `test_complete_workflow_duration` - End-to-end timing (< 10s)
- ✅ `test_memory_usage` - Memory efficiency (< 500 MB)
- ✅ `test_throughput_benchmark` - System throughput (100+ eps)

**Execution**:
```bash
# Run with detailed output
pytest tests/performance/test_ag_ui_streaming_benchmarks.py -v -m performance --no-cov -s

# Run specific test
pytest tests/performance/test_ag_ui_streaming_benchmarks.py::test_event_streaming_latency -v -s

# Run with timing
pytest tests/performance/test_ag_ui_streaming_benchmarks.py -v --durations=10
```

### 2. Load Testing (Optional)

**File**: `tests/performance/locust_load_test.py`

**Requirements**:
```bash
# Install Locust
pip install locust

# Ensure FastAPI server is running
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

**Execution**:
```bash
# Headless mode (CI/CD)
locust -f tests/performance/locust_load_test.py \
    --headless \
    -u 50 \                    # 50 concurrent users
    -r 10 \                    # 10 users/second spawn rate
    -t 60s \                   # 60 second duration
    --host http://localhost:8000

# With web UI
locust -f tests/performance/locust_load_test.py --host http://localhost:8000
# Then open http://localhost:8089

# Generate HTML report
locust -f tests/performance/locust_load_test.py \
    --headless -u 50 -r 10 -t 60s \
    --host http://localhost:8000 \
    --html docs/performance/load_test_report.html
```

### 3. Automation Script

**File**: `scripts/run_benchmarks.sh`

**Usage**:
```bash
# Run pytest benchmarks only
./scripts/run_benchmarks.sh

# Run pytest + load tests
./scripts/run_benchmarks.sh --with-load-test

# Make executable if needed
chmod +x scripts/run_benchmarks.sh
```

---

## Performance Targets

| Metric | Target | Validation |
|--------|--------|------------|
| Event Streaming Latency | < 200ms avg | NFR-P01 requirement |
| P95 Latency | < 300ms | Acceptable threshold |
| Concurrent Streams | 10+ simultaneous | Scalability requirement |
| Workflow Duration | < 10s end-to-end | User experience target |
| Memory Increase | < 500 MB | Resource efficiency |
| Throughput | 100+ events/s | System capacity |
| Error Rate | < 5% | Reliability target |

---

## Interpreting Results

### Success Criteria

✅ **PASS** - All metrics meet or exceed targets
⚠️ **WARNING** - Within 10% of target (investigate)
❌ **FAIL** - Below target (requires optimization)

### Example Output

```
================================================================================
BENCHMARK: Event Streaming Latency (NFR-P01)
================================================================================

Event Streaming Latency Analysis:
  Sample Size:   100 events
  Average:       1.25ms              ✅ PASS (target: 200ms)
  Median:        1.29ms
  P95:           1.32ms              ✅ PASS (target: 300ms)
  P99:           1.34ms
  Min:           0.23ms
  Max:           1.34ms
  Std Dev:       0.13ms

Performance Target Validation:
  Target Avg:    200.0ms (NFR-P01)
  Actual Avg:    1.25ms ✅ PASS     <- 160x better than target!
  Target P95:    300.0ms
  Actual P95:    1.32ms ✅ PASS
================================================================================
```

### What to Look For

1. **Average Latency**: Primary metric for NFR-P01 compliance
2. **P95/P99**: Captures outliers and worst-case scenarios
3. **Standard Deviation**: Low = consistent, High = investigate variability
4. **Error Rate**: Should be 0% ideally, < 5% acceptable
5. **Memory Increase**: Should be minimal (< 10 MB is excellent)

---

## Troubleshooting

### Benchmark Failures

**Problem**: `test_event_streaming_latency` fails with high latency

**Solutions**:
- Check system load (close other applications)
- Verify no background processes consuming CPU
- Re-run benchmark multiple times to average results
- Check for network issues if using remote services

**Problem**: `test_concurrent_streams` fails

**Solutions**:
- Increase timeout values in test
- Check asyncio event loop configuration
- Verify system can handle multiple concurrent tasks
- Monitor CPU usage during test

**Problem**: `test_memory_usage` exceeds threshold

**Solutions**:
- Check for memory leaks in event emitter
- Verify garbage collection is working
- Profile memory usage with `memory_profiler`
- Review object lifecycle and cleanup

### Load Test Issues

**Problem**: Locust not installed

**Solution**:
```bash
pip install locust
```

**Problem**: Server connection refused

**Solution**:
```bash
# Start FastAPI server first
uvicorn src.main:app --host 0.0.0.0 --port 8000

# Then run load test
locust -f tests/performance/locust_load_test.py --host http://localhost:8000
```

**Problem**: High error rate in load test

**Solutions**:
- Reduce concurrent users (-u parameter)
- Increase spawn rate gradually (-r parameter)
- Check server logs for errors
- Verify database and API connections

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Performance Benchmarks

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  benchmarks:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r tests/requirements-test.txt

    - name: Run performance benchmarks
      run: |
        pytest tests/performance/test_ag_ui_streaming_benchmarks.py \
          -v -m performance --no-cov \
          --junit-xml=benchmark-results.xml

    - name: Publish benchmark results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: benchmark-results
        path: benchmark-results.xml
```

---

## Monitoring in Production

### Prometheus Metrics

```python
# Event streaming latency
histogram_quantile(0.95, rate(ag_ui_event_latency_seconds_bucket[5m]))

# Concurrent streams
ag_ui_concurrent_streams

# Memory usage
process_resident_memory_bytes

# Event throughput
rate(ag_ui_events_total[1m])
```

### Grafana Dashboard

Key panels to monitor:
1. Event Latency (P50, P95, P99)
2. Concurrent Streams Count
3. Memory Usage Trend
4. Event Throughput Rate
5. Error Rate Percentage

---

## Advanced Benchmarking

### Custom Benchmarks

Create custom benchmarks by extending the test suite:

```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_custom_scenario():
    """Custom performance test."""

    emitter = StandaloneEventEmitter(session_id="custom-test")

    # Your custom benchmark logic
    start = time.time()
    # ... test code ...
    duration = time.time() - start

    # Assert performance targets
    assert duration < target_duration
```

### Profiling

For detailed profiling:

```bash
# CPU profiling
python -m cProfile -o profile.stats -m pytest tests/performance/test_ag_ui_streaming_benchmarks.py

# Analyze results
python -m pstats profile.stats

# Memory profiling
pip install memory_profiler
python -m memory_profiler tests/performance/test_ag_ui_streaming_benchmarks.py
```

---

## Best Practices

1. **Run benchmarks multiple times** - Average results for accuracy
2. **Consistent environment** - Close other applications, consistent hardware
3. **Version control results** - Track performance changes over time
4. **Set realistic targets** - Based on user experience requirements
5. **Monitor in production** - Benchmarks validate, monitoring verifies
6. **Regression testing** - Re-run benchmarks after major changes
7. **Document bottlenecks** - Track and address performance issues

---

## Resources

- **Full Report**: `docs/performance/WEEK8_PERFORMANCE_BENCHMARK_REPORT.md`
- **Quick Reference**: `docs/performance/BENCHMARK_QUICK_REFERENCE.md`
- **Test Suite**: `tests/performance/test_ag_ui_streaming_benchmarks.py`
- **Load Tests**: `tests/performance/locust_load_test.py`
- **Automation**: `scripts/run_benchmarks.sh`

---

## Support

For questions or issues:
1. Check troubleshooting section above
2. Review test output for specific error messages
3. Consult WEEK8_PERFORMANCE_BENCHMARK_REPORT.md
4. Verify environment setup (Python, dependencies)

---

**Last Updated**: 2025-10-19
**SPARC Phase**: Week 8, Day 15 - Refinement Phase
**Status**: All benchmarks validated ✅
