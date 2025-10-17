# Test Suite - Account Management Agent System

## Overview

This test suite follows Test-Driven Development (TDD) principles and provides comprehensive coverage for the Account Management Agent System.

## Quick Start

### Install Dependencies

```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term
```

### Run Specific Test Types

```bash
# Unit tests only (fast)
pytest tests/unit -v

# Integration tests only
pytest tests/integration -v

# Tests by marker
pytest -m unit           # Unit tests
pytest -m integration    # Integration tests
pytest -m e2e           # End-to-end tests
pytest -m "not slow"    # Skip slow tests
```

## Test Organization

```
tests/
├── README.md                      # This file
├── conftest.py                    # Global fixtures and configuration
├── unit/                          # Unit tests (70%)
│   └── test_orchestrator_skeleton.py
├── integration/                   # Integration tests (25%)
│   └── test_workflow_skeleton.py
├── e2e/                          # End-to-end tests (5%)
│   └── (to be added)
└── fixtures/                      # Test data
    └── (to be added)
```

## Current Status

**Note**: Tests are currently skeletons (commented out) following TDD principles. They define the expected behavior before implementation.

### Next Steps:
1. Implement the core system components
2. Uncomment tests one by one
3. Make each test pass
4. Refactor while keeping tests green

## Test Coverage Goals

- **Critical Paths**: 100% coverage
  - Account health scoring
  - Risk detection algorithms
  - Recommendation generation
  - Memory operations

- **Standard Paths**: >80% coverage
  - Data retrieval
  - Agent orchestration
  - Response formatting

- **Overall Target**: >80% coverage

## Running Tests in Development

### Watch Mode (Run on File Change)

```bash
pip install pytest-watch
ptw tests/
```

### Debug a Specific Test

```bash
# Run single test with full output
pytest tests/unit/test_orchestrator_skeleton.py::TestOrchestratorInitialization::test_orchestrator_initializes_with_clients -vv

# With debugger
pytest tests/unit/test_orchestrator_skeleton.py::test_name -vv --pdb
```

### Generate Coverage Report

```bash
# HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Terminal report
pytest --cov=src --cov-report=term-missing

# Fail if coverage below 80%
pytest --cov=src --cov-fail-under=80
```

## Writing New Tests

### Unit Test Template

```python
import pytest

class TestYourComponent:
    """Test description."""

    @pytest.mark.asyncio
    async def test_your_feature(self, mock_zoho_client):
        """Test case description."""
        # Arrange
        component = YourComponent(client=mock_zoho_client)

        # Act
        result = await component.do_something()

        # Assert
        assert result.success
```

### Integration Test Template

```python
import pytest

class TestYourWorkflow:
    """Workflow test description."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_workflow(
        self,
        mock_zoho_client,
        mock_cognee_memory
    ):
        """Test complete workflow integration."""
        # Arrange
        system = YourSystem(
            zoho_client=mock_zoho_client,
            memory=mock_cognee_memory
        )

        # Act
        result = await system.execute_workflow()

        # Assert
        assert result.success
        assert len(result.steps) > 0
```

## Available Fixtures

### Mock Clients
- `mock_zoho_client` - Mock Zoho CRM client
- `mock_zoho_client_with_rate_limit` - Zoho client with rate limiting
- `mock_cognee_memory` - Mock Cognee memory client
- `mock_cognee_with_context` - Memory with pre-populated context
- `mock_mcp_server` - Mock MCP server

### Sample Data
- `sample_account_data` - Sample account
- `sample_contact_data` - Sample contact
- `sample_deal_data` - Sample deal
- `sample_activity_data` - Sample activities
- `at_risk_account_data` - At-risk account

### Generators
- `account_generator` - Generate various account types
  - `healthy_account()`
  - `at_risk_account()`
  - `churned_account()`

### Utilities
- `mock_time` - Fixed time for deterministic tests
- `temp_data_dir` - Temporary directory for test data
- `load_fixture_file` - Load JSON fixtures

## CI/CD Integration

Tests run automatically on:
- Push to any branch
- Pull request creation
- Pull request updates

### GitHub Actions Workflow

```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run tests
        run: pytest --cov=src --cov-fail-under=80
```

## Performance Testing

```bash
# Run performance tests
pytest -m performance -v

# With timing information
pytest --durations=10
```

## Debugging Tips

### View Test Output

```bash
# Show print statements
pytest -s

# Capture logs
pytest --log-cli-level=DEBUG
```

### Use Breakpoints

```python
def test_something():
    result = function_under_test()
    breakpoint()  # Debugger will stop here
    assert result.success
```

### Pytest Options

```bash
# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Rerun failed tests
pytest --lf  # last failed
pytest --ff  # failed first
```

## Best Practices

1. **Write tests first** (TDD)
2. **One assertion per test** (when possible)
3. **Descriptive test names** that explain intent
4. **Use fixtures** for common setup
5. **Mock external dependencies**
6. **Keep tests fast** (<100ms for unit tests)
7. **Independent tests** - no dependencies between tests
8. **Clean up** after tests (fixtures handle this)

## Common Issues

### Issue: Tests not discovered
**Solution**: Ensure files start with `test_` and functions start with `test_`

### Issue: Async tests fail
**Solution**: Use `@pytest.mark.asyncio` decorator

### Issue: Fixtures not found
**Solution**: Check `conftest.py` is in the correct location

### Issue: Import errors
**Solution**: Ensure package is installed: `pip install -e .`

## Contributing

When adding new tests:
1. Follow the existing structure
2. Add appropriate markers (`@pytest.mark.unit`, etc.)
3. Update this README if adding new test categories
4. Ensure tests pass locally before committing
5. Maintain >80% coverage

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Testing Strategy](../docs/testing_strategy.md)
- [Test Deliverables Summary](../docs/test_deliverables_summary.md)

---

**Last Updated**: 2025-10-18
**Test Framework**: pytest 8.0+
**Python Version**: 3.11+
