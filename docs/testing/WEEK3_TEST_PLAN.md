# Week 3 Test Plan: Three-Tier Integration & Circuit Breaker

## Overview

Comprehensive testing strategy for Week 3 implementation covering three-tier routing (MCP → SDK → REST) with circuit breaker resilience patterns.

## Test Coverage Matrix

| Component | Unit Tests | Integration Tests | Performance Tests | Total |
|-----------|------------|-------------------|-------------------|-------|
| Integration Manager | 35+ | Included in E2E | Yes | 35+ |
| MCP Client (Tier 1) | 15+ | Yes | Yes | 15+ |
| REST Client (Tier 3) | 15+ | Yes | Yes | 15+ |
| Circuit Breaker | 25+ | Yes | Yes | 25+ |
| Retry Policy | 12+ | Yes | No | 12+ |
| Fallback Handler | 15+ | Yes | Yes | 15+ |
| Three-Tier Workflows | - | 20+ | 10+ | 30+ |
| Error Scenarios | - | 25+ | - | 25+ |
| **Total** | **117+** | **45+** | **10+** | **172+** |

## Test Categories

### 1. Unit Tests (117+ tests)

#### Integration Manager Tests (`tests/unit/integrations/test_integration_manager.py`)
- **Routing Logic** (7 tests)
  - Agent context routes to Tier 1 (MCP)
  - Bulk operations route to Tier 2 (SDK)
  - No context defaults to Tier 2
  - Tier 1 failure falls back to Tier 2
  - Tier 2 failure falls back to Tier 3
  - All tiers failed raises error
  - Circuit breaker integration skips open tiers

- **CRUD Operations** (8 tests)
  - Get single account
  - Get multiple accounts with pagination
  - Update account
  - Bulk read 100+ accounts
  - Bulk update with batching
  - Search accounts with criteria
  - Create account
  - Delete account

- **Metrics Collection** (4 tests)
  - Metrics recorded per tier
  - Response time tracking
  - Success rate calculation
  - Error count tracking

- **Health Checks** (4 tests)
  - All tiers healthy
  - One tier unhealthy detection
  - Timeout handling
  - Circuit breaker affects health

- **Configuration** (3 tests)
  - Initialization with all clients
  - Tier priorities configuration
  - Retry configuration

- **Concurrency** (2 tests)
  - Concurrent reads across tiers
  - Concurrent writes thread-safe

- **Error Handling** (3 tests)
  - Invalid account ID handled
  - Network timeout triggers fallback
  - Malformed response handled

#### MCP Client Tests (`tests/unit/integrations/test_mcp_client.py`)
- **Initialization** (3 tests)
- **Account Operations** (5 tests)
- **Authentication** (3 tests)
- **Error Handling** (4 tests)

#### REST Client Tests (`tests/unit/integrations/test_rest_client.py`)
- **Initialization** (3 tests)
- **Account Operations** (6 tests)
- **Rate Limiting** (4 tests)
- **Token Management** (3 tests)
- **Error Handling** (4 tests)
- **Health Checks** (3 tests)
- **Bulk Operations** (2 tests)

#### Circuit Breaker Tests (`tests/unit/resilience/test_circuit_breaker.py`)
- **State Transitions** (8 tests)
- **Metrics** (6 tests)
- **Configuration** (4 tests)
- **Concurrency** (3 tests)
- **Callbacks** (3 tests)
- **Reset** (3 tests)
- **Timeout** (2 tests)
- **Manager** (4 tests)

#### Retry Policy Tests (`tests/unit/resilience/test_retry_policy.py`)
- **Basic Retry** (3 tests)
- **Backoff** (3 tests)
- **Configuration** (2 tests)
- **Edge Cases** (4 tests)

#### Fallback Handler Tests (`tests/unit/resilience/test_fallback_handler.py`)
- **Basic Fallback** (4 tests)
- **Circuit Breaker Integration** (3 tests)
- **Custom Configurations** (3 tests)
- **Error Scenarios** (5 tests)

### 2. Integration Tests (45+ tests)

#### Three-Tier Workflows (`tests/integration/test_three_tier_integration.py`)
- **End-to-End Workflows** (6 tests)
  - Agent operation full workflow
  - Bulk operation full workflow
  - Tier 1 failure automatic fallback
  - Tier 2 failure fallback to Tier 3
  - Circuit breaker recovery
  - Concurrent requests different tiers

- **Failover Scenarios** (4 tests)
  - Tier 1 timeout falls back
  - Tiers 1 & 2 down uses Tier 3
  - Tier recovery resumes normal routing
  - Rapid tier switching

- **Performance Requirements** (4 tests)
  - Tier 1 response < 500ms
  - Tier 2 bulk 1000 records < 5s
  - Tier 3 response < 1s
  - Failover time < 2s

- **Concurrent Operations** (2 tests)
  - 100 concurrent reads
  - Concurrent mixed operations

#### Error Scenarios (`tests/integration/test_three_tier_error_scenarios.py`)
- **Authentication Errors** (3 tests)
  - Invalid credentials (all tiers)
  - Expired token refresh
  - Missing permissions

- **Network Errors** (5 tests)
  - Connection timeout
  - Connection refused
  - DNS resolution failure
  - SSL errors
  - Network partition

- **Rate Limiting** (3 tests)
  - Tier 3 rate limit exceeded
  - Rate limit recovery
  - Burst rate limiting

- **Data Errors** (4 tests)
  - Malformed JSON response
  - Missing required fields
  - Invalid data types
  - Null/empty responses

- **Circuit Breaker Cascades** (4 tests)
  - Sequential tier failures
  - Concurrent tier failures
  - Circuit breaker recovery
  - All circuits open scenario

- **Edge Cases** (6 tests)
  - Zero records bulk operation
  - Maximum payload size
  - Unicode/special characters
  - Very long field values
  - Concurrent circuit state changes
  - Partial batch failures

### 3. Performance Tests (10+ tests)

#### Performance Benchmarks (`tests/performance/test_three_tier_performance.py`)
- **Tier Latency** (3 tests)
  - Tier 1 (MCP) single operation < 500ms
  - Tier 2 (SDK) single operation < 1s
  - Tier 3 (REST) single operation < 1s

- **Throughput** (3 tests)
  - Tier 2 bulk 1000 records < 5s
  - Concurrent 100 operations < 10s
  - Mixed operations throughput

- **Circuit Breaker Overhead** (2 tests)
  - Circuit breaker call overhead < 1ms
  - State check overhead < 0.1ms

- **Failover Performance** (2 tests)
  - Tier failover time < 2s
  - Full cascade failover < 3s

## Test Execution

### Prerequisites

```bash
# Ensure test dependencies are installed
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Check Python version
python --version  # Should be 3.14+
```

### Running Tests

#### Run All Week 3 Tests
```bash
pytest tests/unit/integrations/ tests/unit/resilience/ tests/integration/ -v
```

#### Run with Coverage
```bash
pytest tests/ --cov=src/integrations --cov=src/resilience --cov-report=html --cov-report=term
```

#### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/integrations/ tests/unit/resilience/ -v

# Integration tests only
pytest tests/integration/test_three_tier_integration.py -v

# Performance tests only
pytest tests/performance/test_three_tier_performance.py --benchmark-only
```

#### Run in Parallel (4 workers)
```bash
pytest tests/ -n 4
```

#### Run with Detailed Output
```bash
pytest tests/ -vv --tb=long
```

#### Run Specific Test Classes
```bash
pytest tests/unit/integrations/test_integration_manager.py::TestIntegrationManagerRouting -v
```

## Performance SLA Definitions

| Metric | SLA | Measurement |
|--------|-----|-------------|
| Tier 1 Response Time | < 500ms | Single account read |
| Tier 2 Response Time | < 1s | Single account read |
| Tier 3 Response Time | < 1s | Single account read |
| Tier 2 Bulk Read | < 5s | 1000 records |
| Failover Time | < 2s | Tier 1 → Tier 2 |
| Circuit Breaker Overhead | < 1ms | Per call |
| Concurrent Operations | 100 ops/10s | Mixed read/write |

## Coverage Requirements

### Minimum Coverage Targets

- **Overall Coverage**: 90%+
- **Integration Manager**: 95%+
- **Circuit Breaker**: 95%+
- **MCP Client**: 85%+
- **REST Client**: 85%+
- **Retry Policy**: 90%+
- **Fallback Handler**: 95%+

### Current Coverage

```bash
# Generate coverage report
pytest --cov=src/integrations --cov=src/resilience --cov-report=term --cov-report=html

# View HTML report
open htmlcov/index.html
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Week 3 Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.14'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov pytest-mock

      - name: Run Unit Tests
        run: pytest tests/unit/ -v --cov=src --cov-report=xml

      - name: Run Integration Tests
        run: pytest tests/integration/ -v

      - name: Run Performance Tests
        run: pytest tests/performance/ --benchmark-only

      - name: Upload Coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Troubleshooting Test Failures

### Common Issues

#### 1. Circuit Breaker Tests Timing Out

**Symptom**: Tests using `asyncio.sleep()` taking too long

**Solution**:
```python
# Reduce recovery_timeout in test fixtures
circuit_breaker = CircuitBreaker(
    name="test",
    failure_threshold=3,
    recovery_timeout=2  # Instead of 60
)
```

#### 2. Mock Not Being Called

**Symptom**: `assert mock.called` fails

**Solution**:
```python
# Verify mock setup
assert mock.get_account.called
# Or use call_count
assert mock.get_account.call_count > 0
```

#### 3. Async Tests Not Running

**Symptom**: `RuntimeWarning: coroutine was never awaited`

**Solution**:
```python
# Ensure @pytest.mark.asyncio decorator
@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
```

#### 4. Concurrent Tests Flaky

**Symptom**: Tests pass sometimes, fail sometimes

**Solution**:
```python
# Add small delays to ensure ordering
await asyncio.sleep(0.01)
# Or use asyncio.gather with proper exception handling
results = await asyncio.gather(*tasks, return_exceptions=True)
```

#### 5. Performance Tests Failing

**Symptom**: Response times exceed SLA

**Solution**:
- Run tests on clean environment
- Disable other processes
- Use `time.perf_counter()` for precise timing
- Add tolerance: `assert duration < 0.5 + 0.1  # 10% tolerance`

## Test Data Management

### Fixtures Location

All test fixtures are in `tests/fixtures/integration_fixtures.py`:

- `mock_mcp_client` - Mocked MCP client
- `mock_sdk_client` - Mocked SDK client
- `mock_rest_client` - Mocked REST client
- `circuit_breaker_manager` - Pre-configured circuit breakers
- `integration_manager` - Fully wired integration manager
- `tier_failure_simulator` - Configurable failure patterns
- `performance_timer` - Performance measurement
- `metrics_collector` - Test metrics aggregation

### Sample Data

```python
# Use provided fixtures for test data
def test_with_sample_data(sample_account_data):
    assert sample_account_data["id"] == "ACC12345"
    assert sample_account_data["Account_Name"] == "Test Corporation"

def test_bulk_operations(sample_bulk_accounts):
    assert len(sample_bulk_accounts) == 100
```

## Metrics & Reporting

### Test Execution Metrics

Track during test runs:
- Total tests executed
- Pass/fail rates
- Average execution time
- Coverage percentage
- Performance benchmark results

### Generate Test Report

```bash
# Generate detailed HTML report
pytest tests/ --html=report.html --self-contained-html

# Generate JUnit XML (for CI/CD)
pytest tests/ --junitxml=results.xml
```

## Continuous Improvement

### Weekly Review

- Review failed tests and root causes
- Update SLAs based on actual performance
- Add tests for new edge cases discovered
- Refactor slow or flaky tests
- Update fixtures for new scenarios

### Test Quality Metrics

- Test execution time trending
- Flaky test detection
- Coverage trending
- Performance regression detection

## Appendix

### Quick Reference Commands

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific file
pytest tests/unit/integrations/test_integration_manager.py -v

# Run with keyword filter
pytest tests/ -k "circuit_breaker"

# Run last failed tests
pytest --lf

# Run in verbose mode with traceback
pytest tests/ -vv --tb=long

# Show test durations
pytest tests/ --durations=10
```

### Environment Variables for Testing

```bash
# Set test mode
export TEST_MODE=1

# Mock external services
export MOCK_ZOHO_API=1

# Reduce timeouts for faster tests
export CIRCUIT_BREAKER_RECOVERY_TIMEOUT=2
```

## Success Criteria

- ✅ 172+ tests created and passing
- ✅ 90%+ overall code coverage
- ✅ All performance SLAs met
- ✅ All error scenarios covered
- ✅ CI/CD integration working
- ✅ Documentation complete
- ✅ Zero flaky tests
- ✅ Test execution < 5 minutes

---

**Document Version**: 1.0
**Last Updated**: 2025-10-18
**Owner**: QA Team / Integration Test Specialist
