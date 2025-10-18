# Week 2 Test Suite - Quick Start Guide

⚡ **Get testing in under 2 minutes**

---

## Step 1: Install Dependencies

```bash
# Navigate to project root
cd /Users/mohammadabdelrahman/Projects/sergas_agents

# Activate virtual environment
source venv/bin/activate

# Install all dependencies including test packages
pip install -r requirements.txt
```

**New test dependencies added**:
- `pytest-xdist` - Parallel test execution
- `pytest-benchmark` - Performance benchmarking
- `responses` - Mock HTTP responses
- `faker` - Generate test data
- `factory-boy` - Test data factories

---

## Step 2: Run Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ -v --cov=src --cov-report=html --cov-report=term
```

### Run Fast (Parallel)
```bash
pytest tests/ -n auto
```

### Run Specific Suite
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Performance tests only
pytest tests/performance/ -v -m performance
```

---

## Step 3: View Coverage Report

```bash
# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html
```

---

## Test Organization

```
tests/
├── fixtures/zoho_fixtures.py ........... Mock data & generators
├── unit/
│   ├── test_zoho_sdk_client.py ......... 22 SDK client tests
│   └── test_token_store.py ............. 21 token store tests
├── integration/
│   ├── test_zoho_sdk_integration.py .... 15 integration tests
│   └── test_error_scenarios.py ......... 33 error tests
├── db/
│   └── test_token_repository.py ........ 20 database tests
└── performance/
    └── test_sdk_performance.py ......... 15 performance tests

Total: 126+ tests
```

---

## Common Commands

```bash
# Skip slow tests (faster)
pytest tests/ -m "not slow"

# Verbose with print statements
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -x

# Run specific test
pytest tests/unit/test_zoho_sdk_client.py::TestGetAccount::test_get_account_with_valid_id -v

# List all tests without running
pytest tests/ --collect-only
```

---

## Expected Output

```bash
$ pytest tests/ -v

======================== test session starts ========================
collected 126+ items

tests/unit/test_zoho_sdk_client.py::TestSDKClientInitialization::test_client_initialization_with_valid_config PASSED
tests/unit/test_zoho_sdk_client.py::TestGetAccount::test_get_account_with_valid_id PASSED
tests/unit/test_token_store.py::TestSaveToken::test_save_token_creates_new_record PASSED
...
tests/integration/test_zoho_sdk_integration.py::TestOAuthFlow::test_complete_oauth_flow_mock PASSED
tests/integration/test_error_scenarios.py::TestInvalidOAuthCredentials::test_invalid_client_id PASSED
tests/performance/test_sdk_performance.py::TestBulkReadPerformance::test_bulk_read_1000_records_performance PASSED
...

======================== 126 passed in 5.2s ========================
```

---

## Troubleshooting

### "No module named 'zcrmsdk'"
```bash
# Install Zoho SDK
pip install zohocrmsdk8-0
```

### "No module named 'asyncpg'"
```bash
# Install async PostgreSQL driver
pip install asyncpg
```

### Tests hanging
```bash
# Install pytest-asyncio
pip install pytest-asyncio
```

### Coverage not working
```bash
# Install pytest-cov
pip install pytest-cov
```

---

## Next Steps

1. ✅ Tests created
2. ⏭️ Install missing dependencies: `pip install zohocrmsdk8-0 asyncpg`
3. ⏭️ Implement SDK client using tests as specification
4. ⏭️ Run tests against real implementation
5. ⏭️ Achieve 90%+ coverage

---

## Documentation

- **Test Plan**: [`docs/testing/WEEK2_TEST_PLAN.md`](/Users/mohammadabdelrahman/Projects/sergas_agents/docs/testing/WEEK2_TEST_PLAN.md)
- **Test Summary**: [`docs/testing/WEEK2_TEST_SUMMARY.md`](/Users/mohammadabdelrahman/Projects/sergas_agents/docs/testing/WEEK2_TEST_SUMMARY.md)
- **Quick Start**: This file

---

**Status**: ✅ Ready to run (after installing zohocrmsdk8-0 and asyncpg)
