# Week 1 Testing Guide

## Overview

This guide covers the comprehensive test suite created for Week 1 validation of the Sergas Super Account Manager project.

## Test Structure

```
tests/
├── conftest.py                      # Pytest configuration and fixtures
├── test_environment.py              # Environment validation tests
├── unit/                            # Unit tests
│   └── test_orchestrator_skeleton.py
├── integration/                     # Integration tests
│   ├── test_week1_integration.py   # Week 1 specific integration tests
│   └── test_workflow_skeleton.py
└── fixtures/                        # Test data fixtures
```

## Test Categories

### 1. Environment Validation Tests (`test_environment.py`)

Validates the development environment setup:

- **Python Environment**
  - Python 3.10+ version check
  - Python 3.14 recommended version check
  - Virtual environment validation

- **Core SDKs**
  - Claude Agent SDK import
  - Pydantic v2 import

- **Zoho Integration**
  - Zoho CRM SDK availability
  - HTTP clients (requests, aiohttp, httpx)

- **Cognee Memory**
  - Cognee import
  - LanceDB vector database

- **Database Support**
  - PostgreSQL driver (psycopg2)
  - SQLAlchemy ORM
  - Redis client

- **API Framework**
  - FastAPI
  - Uvicorn

- **Security Libraries**
  - Authlib (OAuth)
  - python-jose (JWT)
  - passlib (password hashing)

- **Monitoring**
  - Prometheus client
  - Structlog
  - OpenTelemetry

- **Code Quality**
  - pytest
  - black
  - mypy

- **Project Structure**
  - Configuration files
  - Git repository

- **Development Tools**
  - IPython
  - pre-commit

### 2. Week 1 Integration Tests (`test_week1_integration.py`)

Validates project integration and completeness:

- **Project Structure**
  - All required directories present
  - Integration subdirectories

- **Configuration**
  - All config files present
  - Config environments setup

- **Dependency Integration**
  - Pydantic-FastAPI compatibility
  - SQLAlchemy-Pydantic compatibility
  - Async libraries compatibility

- **Python Path**
  - src/ in Python path
  - `__init__.py` files present

- **Git Workflow**
  - Comprehensive .gitignore patterns
  - Git attributes (optional)

- **Testing Infrastructure**
  - pytest configuration
  - conftest.py exists
  - Coverage configuration

- **Documentation Structure**
  - Documentation directories
  - PRD document

- **Scripts Setup**
  - Scripts directory structure
  - Executable permissions

- **Environment Variables**
  - .env.example comprehensive
  - .env not committed

- **Week 1 Deliverables**
  - Complete checklist validation
  - Readiness for Week 2

## Running Tests

### Quick Environment Check

Before running full tests, check your environment:

```bash
python3 scripts/check_environment.py
```

This will validate:
- Python version
- Key dependencies
- Project structure
- Configuration files
- Git repository

### Run All Week 1 Tests

```bash
# Using the validation script (recommended)
./scripts/run_week1_validation.sh

# Or manually with pytest
python3 -m pytest tests/test_environment.py tests/integration/test_week1_integration.py -v
```

### Run Specific Test Categories

```bash
# Environment tests only
python3 -m pytest tests/test_environment.py -v

# Integration tests only
python3 -m pytest tests/integration/test_week1_integration.py -v

# Tests with specific marker
python3 -m pytest -m week1 -v
python3 -m pytest -m environment -v
```

### Generate Coverage Report

```bash
# HTML coverage report
python3 -m pytest tests/ --cov=src --cov-report=html

# Terminal coverage report
python3 -m pytest tests/ --cov=src --cov-report=term

# XML coverage report (for CI/CD)
python3 -m pytest tests/ --cov=src --cov-report=xml
```

## Test Markers

Tests are marked for easy filtering:

- `@pytest.mark.week1` - Week 1 validation tests
- `@pytest.mark.environment` - Environment setup tests
- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Component interaction tests
- `@pytest.mark.e2e` - End-to-end workflow tests
- `@pytest.mark.slow` - Tests taking >5 seconds

## Fixtures

### Environment Fixtures

- `project_root` - Project root directory path
- `src_path` - src/ directory path
- `tests_path` - tests/ directory path
- `docs_path` - docs/ directory path
- `config_path` - config/ directory path

### Mock Fixtures

- `mock_zoho_client` - Mock Zoho CRM client
- `mock_cognee_memory` - Mock Cognee memory client
- `mock_mcp_server` - Mock MCP server

### Data Fixtures

- `sample_account_data` - Sample account data
- `sample_contact_data` - Sample contact data
- `sample_deal_data` - Sample deal data
- `sample_activity_data` - Sample activity history
- `at_risk_account_data` - At-risk account data

### Utility Fixtures

- `temp_data_dir` - Temporary directory for test data
- `mock_time` - Fixed time for deterministic testing
- `test_helpers` - Common test helper methods

## Validation Report

After running tests, a comprehensive validation report is generated:

```
docs/setup/WEEK1_VALIDATION.md
```

This report includes:
- Test results summary
- Pass/fail statistics
- Validation checklist
- Week 1 deliverables status
- Recommendations for Week 2
- Quick start commands

## Test Requirements

### Before Running Tests

1. **Python 3.10+** (Python 3.14+ recommended)
2. **Virtual environment** activated
3. **Dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```

### Expected Results

For Week 1 completion, all tests should pass:

- ✅ Environment tests: Python, dependencies, structure
- ✅ Integration tests: Configuration, compatibility, workflow
- ✅ 100% pass rate required to proceed to Week 2

## Troubleshooting

### Tests Failing

1. **Import errors**: Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

2. **Python version errors**: Upgrade Python
   ```bash
   # Check version
   python3 --version

   # Install Python 3.14 if needed
   # (instructions vary by OS)
   ```

3. **Virtual environment not active**:
   ```bash
   # Create venv
   python3 -m venv venv

   # Activate (macOS/Linux)
   source venv/bin/activate

   # Activate (Windows)
   venv\Scripts\activate
   ```

4. **Missing directories**: Re-run project setup
   ```bash
   mkdir -p src/{agents,integrations,models,hooks,utils}
   mkdir -p tests/{unit,integration}
   mkdir -p docs/setup
   mkdir -p config/environments
   mkdir -p scripts
   ```

### Coverage Issues

If coverage is low or missing:

1. **Ensure src/ in coverage source**:
   Check `pyproject.toml` has:
   ```toml
   [tool.coverage.run]
   source = ["src"]
   ```

2. **Run with coverage explicitly**:
   ```bash
   python3 -m pytest --cov=src --cov-report=term-missing
   ```

## CI/CD Integration

For continuous integration, use:

```yaml
# .github/workflows/week1-validation.yml
name: Week 1 Validation

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
        run: pip install -r requirements.txt
      - name: Run Week 1 tests
        run: python3 -m pytest tests/ -v --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Next Steps

After all Week 1 tests pass:

1. ✅ Review validation report
2. 📖 Read Week 2 requirements
3. 🔧 Set up Zoho CRM sandbox
4. 🗄️ Configure PostgreSQL database
5. 🧪 Prepare integration environments

## Test Development Guidelines

When adding new tests:

1. **Follow naming convention**: `test_*.py`
2. **Use descriptive test names**: `test_should_do_something_when_condition()`
3. **One assertion per test** (when possible)
4. **Use fixtures** for common setup
5. **Mark tests appropriately**: `@pytest.mark.unit`, etc.
6. **Document test purpose** in docstrings
7. **Keep tests fast**: Unit tests <100ms, integration <1s

## Resources

- **pytest documentation**: https://docs.pytest.org/
- **Coverage.py**: https://coverage.readthedocs.io/
- **Project README**: ../README.md (when created)
- **PRD**: ../../prd_super_account_manager.md

---

**Note**: This testing guide is specific to Week 1 validation. Additional testing documentation will be added in subsequent weeks for integration testing, E2E testing, and performance testing.
