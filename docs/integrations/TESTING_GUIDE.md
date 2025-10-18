# Zoho SDK Testing Guide

This guide explains how to run and maintain tests for the Zoho SDK integration.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/unit/integrations/ tests/integration/ -v

# Run with coverage
pytest tests/unit/integrations/ tests/integration/ --cov=src/integrations/zoho --cov-report=html

# Run specific test file
pytest tests/unit/integrations/test_token_store.py -v

# Run tests in parallel
pytest tests/ -n auto
```

## Test Structure

```
tests/
├── unit/
│   └── integrations/
│       ├── test_token_store.py       # Token storage tests
│       └── test_zoho_sdk_client.py   # SDK client tests
└── integration/
    └── test_zoho_sdk.py              # End-to-end tests
```

## Test Coverage Requirements

- **Minimum Coverage**: 85%
- **Current Coverage**: Run `pytest --cov` to check
- **Critical Components**: 100% coverage required
  - Token refresh logic
  - Error handling
  - Retry mechanisms

## Running Tests

### Prerequisites

```bash
# Set up test database
export DATABASE_URL="postgresql://test:test@localhost:5432/test_zoho"

# Or use SQLite for local testing
export DATABASE_URL="sqlite:///test_zoho.db"
```

### Unit Tests

```bash
# Token store tests (18 tests)
pytest tests/unit/integrations/test_token_store.py -v

# SDK client tests (35 tests)
pytest tests/unit/integrations/test_zoho_sdk_client.py -v

# All unit tests
pytest tests/unit/integrations/ -v
```

### Integration Tests

```bash
# All integration tests (12 tests)
pytest tests/integration/test_zoho_sdk.py -v

# Specific test class
pytest tests/integration/test_zoho_sdk.py::TestOAuthFlow -v

# Specific test
pytest tests/integration/test_zoho_sdk.py::TestOAuthFlow::test_token_refresh_flow_end_to_end -v
```

### Coverage Report

```bash
# Generate HTML coverage report
pytest tests/ --cov=src/integrations/zoho --cov-report=html

# Open report
open htmlcov/index.html

# Generate terminal report
pytest tests/ --cov=src/integrations/zoho --cov-report=term-missing
```

## Test Categories

### Unit Tests

**Token Store Tests** (`test_token_store.py`)
- ✓ Model to dictionary conversion
- ✓ Token expiration checking
- ✓ Database initialization
- ✓ Token CRUD operations
- ✓ Thread safety
- ✓ Error handling
- ✓ Cleanup operations

**SDK Client Tests** (`test_zoho_sdk_client.py`)
- ✓ Client initialization
- ✓ SDK configuration
- ✓ API base URL generation
- ✓ Token refresh logic
- ✓ Retry with backoff
- ✓ Account operations (get, update, bulk)
- ✓ Search operations
- ✓ Error handling

### Integration Tests

**OAuth Flow Tests**
- ✓ Initial token setup
- ✓ End-to-end token refresh
- ✓ Automatic refresh on 401

**Database Persistence Tests**
- ✓ Token save and retrieve
- ✓ Concurrent token updates

**Bulk Operations Tests**
- ✓ Bulk read 100+ records
- ✓ Bulk update 100+ records

**Error Handling Tests**
- ✓ Retry on transient errors
- ✓ Rate limit handling
- ✓ Max retries exhausted

**Performance Tests**
- ✓ SDK bulk read performance

## Writing New Tests

### Test Template

```python
"""Test module description."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.integrations.zoho.sdk_client import ZohoSDKClient
from src.integrations.zoho.exceptions import ZohoAPIError


@pytest.fixture
def mock_dependency():
    """Mock description."""
    with patch("module.path") as mock:
        yield mock


class TestFeature:
    """Test feature description."""

    def test_success_case(self, mock_dependency):
        """Test successful operation."""
        # Arrange
        expected = "result"
        mock_dependency.return_value = expected

        # Act
        result = function_to_test()

        # Assert
        assert result == expected
        mock_dependency.assert_called_once()

    def test_error_case(self, mock_dependency):
        """Test error handling."""
        # Arrange
        mock_dependency.side_effect = Exception("Error")

        # Act & Assert
        with pytest.raises(ZohoAPIError):
            function_to_test()
```

### Best Practices

1. **Use descriptive test names**
   ```python
   # ✅ Good
   def test_token_refresh_updates_database_with_new_token():
       pass

   # ❌ Bad
   def test_refresh():
       pass
   ```

2. **Follow AAA pattern** (Arrange, Act, Assert)
   ```python
   def test_example():
       # Arrange
       client = ZohoSDKClient(config, db_url)
       mock.return_value = "expected"

       # Act
       result = client.method()

       # Assert
       assert result == "expected"
   ```

3. **Mock external dependencies**
   ```python
   # Always mock:
   - Database connections
   - API calls
   - Time-dependent operations
   - External services
   ```

4. **Test both success and failure paths**
   ```python
   class TestOperation:
       def test_operation_succeeds(self):
           pass

       def test_operation_handles_api_error(self):
           pass

       def test_operation_handles_network_error(self):
           pass
   ```

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Test Zoho SDK

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_zoho
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.14'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test_zoho
        run: |
          pytest tests/ --cov=src/integrations/zoho --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Debugging Tests

### Run with verbose output

```bash
pytest tests/unit/integrations/test_token_store.py -vv
```

### Stop on first failure

```bash
pytest tests/ -x
```

### Run specific test with debug output

```bash
pytest tests/unit/integrations/test_token_store.py::TestTokenStoreSave::test_save_token_creates_new_token -vv -s
```

### Use pytest debugger

```bash
pytest tests/unit/integrations/test_token_store.py --pdb
```

### Print captured output

```bash
pytest tests/ -s  # Show print statements
```

## Performance Testing

### Benchmark Tests

```bash
# Run performance benchmarks
pytest tests/integration/test_zoho_sdk.py::TestPerformanceBenchmark --benchmark-only

# Compare with previous results
pytest tests/integration/ --benchmark-compare
```

### Load Testing

```python
# tests/performance/test_load.py
def test_concurrent_requests():
    """Test handling of concurrent requests."""
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(client.get_accounts, limit=10)
            for _ in range(100)
        ]

        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len(results) == 100
```

## Troubleshooting

### Issue: Tests hanging

```bash
# Add timeout
pytest tests/ --timeout=30

# Or per test
@pytest.mark.timeout(10)
def test_something():
    pass
```

### Issue: Database connection errors

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Use SQLite for tests
export DATABASE_URL="sqlite:///test.db"
pytest tests/
```

### Issue: Import errors

```bash
# Install in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/sergas_agents"
```

### Issue: Mocking not working

```python
# Make sure patch path is correct
# ❌ Wrong: patch where defined
@patch("zcrmsdk.ZCRMRestClient")

# ✅ Correct: patch where used
@patch("src.integrations.zoho.sdk_client.ZCRMRestClient")
```

## Test Maintenance

### Regular Tasks

1. **Update test data** when API changes
2. **Review coverage** monthly
3. **Refactor flaky tests** immediately
4. **Update mocks** when dependencies change

### Code Quality Checks

```bash
# Type checking
mypy src/integrations/zoho/

# Linting
pylint src/integrations/zoho/

# Formatting
black src/integrations/zoho/ tests/

# Security scan
bandit -r src/integrations/zoho/
```

## Resources

- **pytest docs**: https://docs.pytest.org/
- **pytest-cov**: https://pytest-cov.readthedocs.io/
- **unittest.mock**: https://docs.python.org/3/library/unittest.mock.html

---

**Last Updated**: 2025-10-18
