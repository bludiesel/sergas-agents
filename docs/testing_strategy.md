# Testing Strategy - Account Management Agent System

## Overview

This document outlines the comprehensive testing strategy for the Account Management Agent System built with Claude Agent SDK, Cognee memory, and Zoho CRM integration.

## Testing Philosophy

- **Test-Driven Development (TDD)**: Write tests before implementation
- **Fast Feedback**: Unit tests run in milliseconds, integration tests in seconds
- **Isolated Tests**: No dependencies between tests, deterministic results
- **Realistic Mocking**: Mock external services (Zoho, Cognee) with realistic behavior
- **Coverage-Driven**: >80% coverage for critical paths, 100% for business logic

## Test Pyramid Structure

```
         /\
        /E2E\      <- Few (5-10 scenarios), high-value workflows
       /------\
      /Integr. \   <- Moderate (20-30), component interactions
     /----------\
    /   Unit     \ <- Many (100+), fast, focused on logic
   /--------------\
```

### Unit Tests (70%)
- **Scope**: Individual functions, classes, and modules
- **Speed**: <100ms per test
- **Isolation**: Mock all external dependencies
- **Coverage Target**: >90%

### Integration Tests (25%)
- **Scope**: Component interactions (agent + memory, agent + Zoho)
- **Speed**: <5s per test
- **Isolation**: Mock external APIs, use in-memory databases
- **Coverage Target**: >80%

### End-to-End Tests (5%)
- **Scope**: Complete workflows from user intent to output
- **Speed**: <30s per test
- **Isolation**: Mock only external services (Zoho, LLM APIs)
- **Coverage Target**: Critical user journeys

## Testing Framework Stack

### Core Framework
- **pytest** (v8.0+): Test runner and framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Code coverage reporting
- **pytest-mock**: Enhanced mocking capabilities

### Mocking & Fixtures
- **unittest.mock**: Standard library mocking
- **responses**: HTTP request mocking
- **freezegun**: Time mocking for temporal tests
- **factory_boy**: Test data generation

### Assertion Libraries
- **pytest** built-in assertions
- **jsonschema**: JSON response validation
- **pydantic**: Data model validation

## Test Organization

```
tests/
├── conftest.py                 # Global fixtures and configuration
├── unit/                       # Unit tests (fast, isolated)
│   ├── test_orchestrator.py   # Main orchestrator logic
│   ├── test_subagents.py      # Individual subagent logic
│   ├── test_memory.py          # Cognee integration
│   └── test_zoho_client.py    # Zoho client wrapper
├── integration/                # Integration tests
│   ├── test_workflow.py        # Agent workflow integration
│   ├── test_memory_agent.py   # Agent + memory integration
│   └── test_zoho_agent.py     # Agent + Zoho integration
├── e2e/                        # End-to-end tests
│   ├── test_account_analysis.py
│   ├── test_risk_detection.py
│   └── test_recommendation_generation.py
└── fixtures/                   # Test data and fixtures
    ├── account_data.json
    ├── crm_responses.json
    └── memory_snapshots.json
```

## Unit Testing Approach

### 1. Orchestrator Tests
Test the main agent orchestrator in isolation:

```python
@pytest.mark.asyncio
async def test_orchestrator_delegates_to_data_retrieval(mock_zoho_client, mock_memory):
    """Orchestrator should delegate data retrieval to appropriate subagent."""
    orchestrator = AccountOrchestrator(zoho_client=mock_zoho_client, memory=mock_memory)

    result = await orchestrator.process("Get account data for Acme Corp")

    assert result.success
    assert "account_data" in result.data
    mock_zoho_client.get_account.assert_called_once()
```

### 2. Subagent Tests
Test individual subagent logic:

```python
@pytest.mark.asyncio
async def test_data_retrieval_agent_fetches_account_data(mock_zoho_client):
    """Data retrieval agent should fetch and structure account data."""
    agent = DataRetrievalAgent(zoho_client=mock_zoho_client)
    mock_zoho_client.get_account.return_value = {"id": "123", "name": "Acme Corp"}

    result = await agent.retrieve_account("123")

    assert result["id"] == "123"
    assert result["name"] == "Acme Corp"
    mock_zoho_client.get_account.assert_called_once_with("123")
```

### 3. Memory Integration Tests
Test Cognee memory operations:

```python
@pytest.mark.asyncio
async def test_memory_stores_account_context(mock_cognee):
    """Memory should store and retrieve account context correctly."""
    memory = AccountMemory(cognee_client=mock_cognee)
    context = {"account_id": "123", "last_interaction": "2025-10-18"}

    await memory.store_context("123", context)
    retrieved = await memory.get_context("123")

    assert retrieved["account_id"] == "123"
    mock_cognee.store.assert_called_once()
```

### 4. Zoho Client Tests
Test Zoho CRM wrapper:

```python
def test_zoho_client_handles_rate_limiting(mock_requests):
    """Zoho client should handle rate limiting with exponential backoff."""
    mock_requests.get.side_effect = [
        MockResponse(429, {"error": "Rate limit exceeded"}),
        MockResponse(200, {"data": "success"})
    ]

    client = ZohoClient(access_token="test_token")
    result = client.get_account("123")

    assert result["data"] == "success"
    assert mock_requests.get.call_count == 2
```

## Integration Testing Patterns

### 1. Agent + Memory Integration
Test agents working with real Cognee operations (mocked backend):

```python
@pytest.mark.asyncio
async def test_agent_workflow_uses_memory_for_context(
    mock_zoho_client,
    in_memory_cognee
):
    """Agent should use memory to maintain context across interactions."""
    orchestrator = AccountOrchestrator(
        zoho_client=mock_zoho_client,
        memory=in_memory_cognee
    )

    # First interaction - store context
    result1 = await orchestrator.process("Analyze account 123")

    # Second interaction - should use stored context
    result2 = await orchestrator.process("What was the risk level?")

    assert result2.used_context
    assert "risk_level" in result2.data
```

### 2. Agent + Zoho Integration
Test agents with realistic Zoho API responses:

```python
@pytest.mark.asyncio
async def test_data_retrieval_handles_complex_crm_data(
    mock_zoho_server
):
    """Agent should correctly parse complex CRM data structures."""
    mock_zoho_server.add_response("/accounts/123", {
        "data": [{
            "id": "123",
            "Account_Name": "Acme Corp",
            "Annual_Revenue": 5000000,
            "Contacts": [{"id": "c1", "Full_Name": "John Doe"}]
        }]
    })

    agent = DataRetrievalAgent(zoho_client=ZohoClient())
    result = await agent.retrieve_account("123")

    assert result["annual_revenue"] == 5000000
    assert len(result["contacts"]) == 1
```

### 3. MCP Integration
Test MCP tool invocation patterns:

```python
@pytest.mark.asyncio
async def test_agent_uses_mcp_tools_correctly(mock_mcp_server):
    """Agent should correctly invoke MCP tools for Zoho operations."""
    mock_mcp_server.register_tool("zoho_get_account", {"id": "123"})

    agent = DataRetrievalAgent(use_mcp=True)
    result = await agent.retrieve_account("123")

    assert mock_mcp_server.tool_called("zoho_get_account")
    assert result["id"] == "123"
```

## End-to-End Testing Scenarios

### Scenario 1: Account Health Analysis
```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_account_health_analysis():
    """Complete workflow: retrieve data → analyze → store insights → generate report."""
    system = AccountManagementSystem()

    result = await system.analyze_account("123")

    assert result.health_score > 0
    assert result.risk_factors is not None
    assert result.recommendations is not None
    assert result.insights_stored
```

### Scenario 2: At-Risk Account Detection
```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_at_risk_account_detection_and_notification():
    """Detect at-risk account and generate actionable recommendations."""
    system = AccountManagementSystem()

    result = await system.check_account_health("123")

    if result.risk_level == "high":
        assert result.recommendations is not None
        assert len(result.recommendations) > 0
        assert result.notification_sent
```

### Scenario 3: Memory-Driven Context Awareness
```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_multi_turn_conversation_with_context():
    """Agent maintains context across multiple interactions using memory."""
    system = AccountManagementSystem()

    # Turn 1: Initial analysis
    result1 = await system.process("Analyze Acme Corp")

    # Turn 2: Follow-up using context
    result2 = await system.process("What are the main risks?")

    # Turn 3: Action-oriented query
    result3 = await system.process("Suggest next steps")

    assert result3.suggestions is not None
    assert result3.context_from_previous_turns
```

## Test Data Management

### Mock Data Strategy
1. **Fixture Files**: Store realistic test data in `tests/fixtures/`
2. **Data Builders**: Use factory_boy for dynamic test data generation
3. **Versioning**: Version test data with corresponding API versions
4. **Isolation**: Each test gets fresh data copies

### Example Fixture Structure
```python
# tests/fixtures/accounts.py
SAMPLE_ACCOUNTS = {
    "healthy_account": {
        "id": "123",
        "name": "Acme Corp",
        "health_score": 85,
        "annual_revenue": 5000000,
        "engagement_score": 90
    },
    "at_risk_account": {
        "id": "456",
        "name": "Beta Inc",
        "health_score": 45,
        "annual_revenue": 1000000,
        "engagement_score": 30
    }
}
```

### Data Factory Pattern
```python
# tests/factories.py
class AccountFactory(factory.Factory):
    class Meta:
        model = Account

    id = factory.Sequence(lambda n: f"acc_{n}")
    name = factory.Faker("company")
    annual_revenue = factory.Faker("random_int", min=100000, max=10000000)
    health_score = factory.Faker("random_int", min=0, max=100)
```

## Coverage Requirements

### Critical Paths (100% Coverage)
- Account health scoring logic
- Risk detection algorithms
- Recommendation generation
- Memory storage and retrieval
- Error handling and recovery

### Standard Paths (>80% Coverage)
- Data retrieval and transformation
- Agent orchestration logic
- MCP tool invocation
- Response formatting

### Monitoring Coverage
```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Fail if coverage below threshold
pytest --cov=src --cov-fail-under=80
```

## Continuous Testing in CI/CD

### GitHub Actions Workflow
```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run unit tests
        run: pytest tests/unit -v --cov=src

      - name: Run integration tests
        run: pytest tests/integration -v

      - name: Run E2E tests
        run: pytest tests/e2e -v -m e2e

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest tests/unit -x
        language: system
        pass_filenames: false
        always_run: true
```

## Performance Testing Approach

### Load Testing
Test agent performance under load:

```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_agent_handles_concurrent_requests():
    """Agent should handle multiple concurrent requests efficiently."""
    system = AccountManagementSystem()

    tasks = [system.analyze_account(f"acc_{i}") for i in range(100)]

    start = time.time()
    results = await asyncio.gather(*tasks)
    duration = time.time() - start

    assert duration < 10  # Should complete 100 analyses in <10s
    assert all(r.success for r in results)
```

### Memory Usage Testing
```python
@pytest.mark.performance
def test_memory_usage_stays_within_bounds():
    """System should not leak memory during extended operations."""
    import psutil
    import gc

    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    system = AccountManagementSystem()
    for i in range(1000):
        system.quick_operation()
        if i % 100 == 0:
            gc.collect()

    final_memory = process.memory_info().rss / 1024 / 1024
    memory_increase = final_memory - initial_memory

    assert memory_increase < 50  # Should not increase by >50MB
```

## Security Testing Requirements

### 1. Input Validation
Test that agents validate and sanitize inputs:

```python
def test_agent_rejects_malicious_input():
    """Agent should reject inputs with potential SQL injection patterns."""
    agent = DataRetrievalAgent()

    with pytest.raises(ValueError):
        agent.retrieve_account("123'; DROP TABLE accounts; --")
```

### 2. Authentication & Authorization
Test that Zoho client handles auth correctly:

```python
def test_zoho_client_refreshes_expired_tokens():
    """Client should automatically refresh expired access tokens."""
    client = ZohoClient(access_token="expired_token")

    result = client.get_account("123")

    assert result is not None
    assert client.token_refresh_called
```

### 3. Data Privacy
Test that sensitive data is handled securely:

```python
def test_memory_encrypts_sensitive_data():
    """Memory should encrypt sensitive account data at rest."""
    memory = AccountMemory()
    sensitive_data = {"ssn": "123-45-6789", "credit_card": "4111111111111111"}

    memory.store_sensitive("acc_123", sensitive_data)
    raw_storage = memory.get_raw_storage()

    assert "123-45-6789" not in str(raw_storage)
    assert "4111111111111111" not in str(raw_storage)
```

## Testing Best Practices

### 1. Test Naming Convention
```python
# Pattern: test_<unit>_<scenario>_<expected_result>
def test_orchestrator_invalid_input_raises_error():
    """Clear, descriptive test names that explain intent."""
    pass
```

### 2. Arrange-Act-Assert Pattern
```python
def test_example():
    # Arrange: Set up test data and mocks
    agent = DataRetrievalAgent()
    mock_data = {"id": "123"}

    # Act: Execute the operation
    result = agent.process(mock_data)

    # Assert: Verify expectations
    assert result.success
```

### 3. One Assertion Per Test
```python
# Good: Single, focused assertion
def test_health_score_calculation_returns_number():
    score = calculate_health_score(account_data)
    assert isinstance(score, (int, float))

def test_health_score_within_valid_range():
    score = calculate_health_score(account_data)
    assert 0 <= score <= 100
```

### 4. Test Independence
```python
# Each test should be completely independent
@pytest.fixture(autouse=True)
def reset_state():
    """Reset global state before each test."""
    clear_caches()
    reset_singletons()
    yield
    cleanup()
```

### 5. Mock External Dependencies
```python
# Always mock external services (APIs, databases, file systems)
@pytest.fixture
def mock_zoho_client(mocker):
    """Mock Zoho client to avoid real API calls."""
    client = mocker.Mock(spec=ZohoClient)
    client.get_account.return_value = {"id": "123", "name": "Test"}
    return client
```

## Debugging Failed Tests

### 1. Verbose Output
```bash
pytest -vv --tb=long  # Detailed output with full tracebacks
```

### 2. Debug Specific Test
```bash
pytest tests/unit/test_orchestrator.py::test_specific_case -vv
```

### 3. Interactive Debugging
```python
# Add breakpoint in test
def test_example():
    result = function_under_test()
    breakpoint()  # Drop into debugger
    assert result.success
```

### 4. Capture Logs
```python
# conftest.py
@pytest.fixture
def caplog(caplog):
    """Capture logs during test execution."""
    caplog.set_level(logging.DEBUG)
    return caplog

# In test
def test_with_logs(caplog):
    function_that_logs()
    assert "Expected log message" in caplog.text
```

## Maintenance & Evolution

### 1. Quarterly Review
- Review test coverage and identify gaps
- Update mocks to match current API versions
- Refactor slow or flaky tests
- Update test data fixtures

### 2. Test Metrics Tracking
- Monitor test execution time trends
- Track flaky test rates
- Measure coverage trends over time
- Analyze test failure patterns

### 3. Documentation Updates
- Keep testing strategy aligned with architecture changes
- Document new testing patterns as they emerge
- Share learnings from production incidents

## Conclusion

This testing strategy provides a comprehensive framework for ensuring the quality, reliability, and maintainability of the Account Management Agent System. By following TDD principles and maintaining high test coverage, we can confidently evolve the system while preventing regressions.

**Key Takeaways**:
- Write tests first (TDD)
- Mock external dependencies
- Maintain >80% coverage for critical paths
- Run tests in CI/CD pipeline
- Keep tests fast, isolated, and deterministic
