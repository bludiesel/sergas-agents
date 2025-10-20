# Testing Strategy for CopilotKit Integration Migration

**Document Version:** 1.0
**Last Updated:** 2025-10-19
**Status:** Draft

## Executive Summary

This document defines the comprehensive testing strategy for migrating the multi-agent system from Claude Agent SDK to CopilotKit-LangGraph integration. The strategy ensures zero regression, validates HITL workflows, and maintains 90%+ code coverage across all integration layers.

## Table of Contents

1. [Testing Approach](#testing-approach)
2. [Test Pyramid](#test-pyramid)
3. [Unit Testing Strategy](#unit-testing-strategy)
4. [Integration Testing Strategy](#integration-testing-strategy)
5. [E2E Testing Strategy](#e2e-testing-strategy)
6. [Performance Testing Strategy](#performance-testing-strategy)
7. [Monitoring & Observability Tests](#monitoring--observability-tests)
8. [Test Data & Fixtures](#test-data--fixtures)
9. [Testing Tools & Infrastructure](#testing-tools--infrastructure)
10. [Coverage Requirements](#coverage-requirements)
11. [CI/CD Integration](#cicd-integration)
12. [Test Execution Plan](#test-execution-plan)

---

## Testing Approach

### Core Testing Principles

1. **Test-First Development**: Write tests before implementing CopilotKit integration
2. **Regression Prevention**: Ensure existing functionality remains intact
3. **HITL Validation**: Thoroughly test human approval workflows
4. **Performance Benchmarking**: Validate response times and throughput
5. **Isolation**: Each layer tested independently before integration

### Testing Phases

```
Phase 1: Unit Tests        → Backend/Frontend components in isolation
Phase 2: Integration Tests → Layer-to-layer communication
Phase 3: E2E Tests         → Complete user workflows
Phase 4: Performance Tests → Load, stress, and scalability
Phase 5: Monitoring Tests  → Observability and metrics
```

---

## Test Pyramid

```
         /\
        /E2E\        ← 10% (Critical paths, HITL workflows)
       /------\
      /Integr. \     ← 30% (API contracts, agent coordination)
     /----------\
    /   Unit     \   ← 60% (Component logic, state management)
   /--------------\
```

**Coverage Targets:**
- **Unit Tests**: 60% of test suite, 95%+ code coverage
- **Integration Tests**: 30% of test suite, 85%+ coverage
- **E2E Tests**: 10% of test suite, covering critical paths

---

## Unit Testing Strategy

### 1. LangGraph Agent Wrapper Tests

**Test Location:** `tests/unit/langgraph/test_agent_wrappers.py`

#### Test Cases

```python
class TestOrchestratorAgentWrapper:
    """Unit tests for OrchestratorAgent LangGraph wrapper."""

    def test_initialization_with_config(self):
        """Verify agent initializes with correct configuration."""
        pass

    def test_creates_langgraph_graph(self):
        """Verify LangGraph StateGraph is created correctly."""
        pass

    def test_defines_state_schema(self):
        """Verify state schema matches requirements."""
        pass

    def test_adds_nodes_for_each_step(self):
        """Verify all workflow nodes are added to graph."""
        pass

    def test_defines_edges_correctly(self):
        """Verify workflow edges connect nodes properly."""
        pass

    def test_compiles_without_errors(self):
        """Verify graph compiles successfully."""
        pass

    @pytest.mark.asyncio
    async def test_stream_method_yields_events(self):
        """Verify stream() yields AG UI Protocol events."""
        pass

    @pytest.mark.asyncio
    async def test_handles_interruption_for_approval(self):
        """Verify agent interrupts for HITL approval."""
        pass

    @pytest.mark.asyncio
    async def test_resumes_after_approval(self):
        """Verify agent resumes after approval received."""
        pass

    @pytest.mark.asyncio
    async def test_state_persistence_during_interruption(self):
        """Verify state is preserved during interruption."""
        pass
```

**Additional Agent Wrapper Tests:**
- `TestZohoDataScoutWrapper`: Data fetching and aggregation
- `TestMemoryAnalystWrapper`: Memory operations and pattern analysis
- `TestRecommendationAuthorWrapper`: Recommendation generation with approval

**Coverage Target:** 95%+ per wrapper class

---

### 2. CopilotKitSDK Initialization Tests

**Test Location:** `tests/unit/backend/test_copilotkit_sdk.py`

```python
class TestCopilotKitSDKInitialization:
    """Unit tests for CopilotKitSDK initialization."""

    def test_initializes_with_default_model(self):
        """Verify SDK uses claude-3-5-sonnet-20241022 by default."""
        pass

    def test_accepts_custom_model(self):
        """Verify custom model can be specified."""
        pass

    def test_registers_all_agent_wrappers(self):
        """Verify all 4 agents are registered with SDK."""
        pass

    def test_configures_checkpointer(self):
        """Verify MemorySaver checkpointer is configured."""
        pass

    def test_enables_streaming(self):
        """Verify streaming is enabled by default."""
        pass

    def test_handles_missing_api_key(self):
        """Verify raises error when ANTHROPIC_API_KEY missing."""
        pass

    def test_validates_agent_configurations(self):
        """Verify agent configs are validated on init."""
        pass
```

**Coverage Target:** 90%+

---

### 3. FastAPI Endpoint Tests

**Test Location:** `tests/unit/backend/test_fastapi_endpoints.py`

```python
class TestCopilotKitAPIEndpoints:
    """Unit tests for FastAPI CopilotKit endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_200(self):
        """Verify health check endpoint works."""
        pass

    @pytest.mark.asyncio
    async def test_copilotkit_endpoint_exists(self):
        """Verify /copilotkit endpoint is registered."""
        pass

    @pytest.mark.asyncio
    async def test_endpoint_accepts_post_requests(self):
        """Verify endpoint accepts POST requests."""
        pass

    @pytest.mark.asyncio
    async def test_validates_request_payload(self):
        """Verify request validation for required fields."""
        pass

    @pytest.mark.asyncio
    async def test_returns_sse_stream(self):
        """Verify endpoint returns SSE event stream."""
        pass

    @pytest.mark.asyncio
    async def test_handles_invalid_agent_type(self):
        """Verify error handling for invalid agent type."""
        pass

    @pytest.mark.asyncio
    async def test_includes_cors_headers(self):
        """Verify CORS headers are included in response."""
        pass

    @pytest.mark.asyncio
    async def test_authenticates_requests(self):
        """Verify authentication is enforced."""
        pass
```

**Coverage Target:** 90%+

---

### 4. Next.js API Route Tests

**Test Location:** `tests/unit/frontend/test_copilotkit_route.test.ts`

```typescript
describe('CopilotKit API Route', () => {
  it('forwards POST requests to FastAPI backend', async () => {
    // Test request forwarding
  });

  it('preserves request headers', async () => {
    // Test header forwarding
  });

  it('streams SSE events from backend', async () => {
    // Test streaming
  });

  it('handles backend connection errors', async () => {
    // Test error handling
  });

  it('returns 405 for non-POST requests', async () => {
    // Test method validation
  });

  it('adds security headers to response', async () => {
    // Test security headers
  });

  it('logs requests for monitoring', async () => {
    // Test logging
  });
});
```

**Coverage Target:** 85%+

---

### 5. Frontend Component Tests

**Test Location:** `tests/unit/frontend/test_copilotkit_components.test.tsx`

```typescript
describe('CopilotKitProvider', () => {
  it('initializes with correct API endpoint', () => {
    // Test provider initialization
  });

  it('configures claude-3-5-sonnet model', () => {
    // Test model configuration
  });

  it('wraps children components', () => {
    // Test component wrapping
  });

  it('provides context to useCopilotAction hooks', () => {
    // Test context provision
  });
});

describe('useCopilotAction Hooks', () => {
  it('registers analyzeAccount action', () => {
    // Test action registration
  });

  it('streams response updates', () => {
    // Test streaming
  });

  it('handles approval interruptions', () => {
    // Test HITL interruption
  });

  it('displays approval UI when interrupted', () => {
    // Test approval UI
  });

  it('resumes after user approval/rejection', () => {
    // Test resumption
  });

  it('displays streaming results in UI', () => {
    // Test result display
  });
});
```

**Coverage Target:** 85%+

---

## Integration Testing Strategy

### 1. Frontend → Next.js → FastAPI Flow

**Test Location:** `tests/integration/test_full_stack_flow.py`

```python
class TestFullStackFlow:
    """Integration tests for complete request flow."""

    @pytest.mark.asyncio
    async def test_frontend_to_backend_communication(self):
        """Test complete request flow from frontend to backend."""
        # 1. Simulate frontend request
        # 2. Verify Next.js route receives it
        # 3. Verify FastAPI receives forwarded request
        # 4. Verify response streams back to frontend
        pass

    @pytest.mark.asyncio
    async def test_sse_streaming_end_to_end(self):
        """Test SSE streaming works across all layers."""
        pass

    @pytest.mark.asyncio
    async def test_error_propagation(self):
        """Test errors propagate correctly through layers."""
        pass

    @pytest.mark.asyncio
    async def test_authentication_flow(self):
        """Test authentication works across stack."""
        pass
```

**Coverage Target:** 85%+

---

### 2. Multi-Agent Coordination Tests

**Test Location:** `tests/integration/test_agent_coordination.py`

```python
class TestAgentCoordination:
    """Integration tests for multi-agent orchestration."""

    @pytest.mark.asyncio
    async def test_orchestrator_calls_data_scout(self):
        """Test Orchestrator invokes ZohoDataScout correctly."""
        pass

    @pytest.mark.asyncio
    async def test_data_scout_calls_memory_analyst(self):
        """Test ZohoDataScout invokes MemoryAnalyst."""
        pass

    @pytest.mark.asyncio
    async def test_orchestrator_calls_recommendation_author(self):
        """Test Orchestrator invokes RecommendationAuthor."""
        pass

    @pytest.mark.asyncio
    async def test_state_passed_between_agents(self):
        """Test state is correctly passed between agents."""
        pass

    @pytest.mark.asyncio
    async def test_agent_error_handling(self):
        """Test error handling when agent fails."""
        pass

    @pytest.mark.asyncio
    async def test_agent_retry_logic(self):
        """Test retry logic for transient failures."""
        pass
```

**Coverage Target:** 85%+

---

### 3. State Management Tests

**Test Location:** `tests/integration/test_state_management.py`

```python
class TestStateManagement:
    """Integration tests for LangGraph state management."""

    @pytest.mark.asyncio
    async def test_state_persists_during_execution(self):
        """Test state is maintained throughout workflow."""
        pass

    @pytest.mark.asyncio
    async def test_state_persists_during_interruption(self):
        """Test state persists when interrupted for approval."""
        pass

    @pytest.mark.asyncio
    async def test_checkpointer_saves_state(self):
        """Test MemorySaver checkpointer saves state correctly."""
        pass

    @pytest.mark.asyncio
    async def test_state_restored_after_interruption(self):
        """Test state is restored after approval."""
        pass

    @pytest.mark.asyncio
    async def test_concurrent_session_state_isolation(self):
        """Test state isolation between concurrent sessions."""
        pass
```

**Coverage Target:** 90%+

---

### 4. Error Handling & Recovery Tests

**Test Location:** `tests/integration/test_error_handling.py`

```python
class TestErrorHandling:
    """Integration tests for error handling and recovery."""

    @pytest.mark.asyncio
    async def test_handles_backend_connection_failure(self):
        """Test handling of backend connection failures."""
        pass

    @pytest.mark.asyncio
    async def test_handles_agent_timeout(self):
        """Test handling of agent execution timeout."""
        pass

    @pytest.mark.asyncio
    async def test_handles_invalid_state(self):
        """Test handling of corrupted state."""
        pass

    @pytest.mark.asyncio
    async def test_retries_transient_failures(self):
        """Test automatic retry on transient failures."""
        pass

    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test graceful degradation when subagent fails."""
        pass
```

**Coverage Target:** 85%+

---

## E2E Testing Strategy

### 1. Complete Account Analysis Workflow

**Test Location:** `tests/e2e/test_account_analysis_workflow.spec.ts`

```typescript
describe('Account Analysis E2E Workflow', () => {
  it('completes full account analysis without interruption', async ({ page }) => {
    // 1. Navigate to account analysis page
    // 2. Enter account ID
    // 3. Click "Analyze Account"
    // 4. Verify ZohoDataScout fetches data
    // 5. Verify MemoryAnalyst analyzes patterns
    // 6. Verify recommendations are generated
    // 7. Verify final results displayed
  });

  it('displays real-time progress updates', async ({ page }) => {
    // Test progress indicator updates
  });

  it('streams partial results during execution', async ({ page }) => {
    // Test streaming UI updates
  });

  it('handles network interruptions gracefully', async ({ page }) => {
    // Test network failure recovery
  });
});
```

**Tool:** Playwright
**Coverage Target:** Critical path validation

---

### 2. HITL Approval Workflow Tests

**Test Location:** `tests/e2e/test_hitl_approval_workflow.spec.ts`

```typescript
describe('HITL Approval Workflow E2E', () => {
  it('interrupts workflow for recommendation approval', async ({ page }) => {
    // 1. Start account analysis
    // 2. Wait for recommendation generation
    // 3. Verify approval modal appears
    // 4. Verify workflow is paused
  });

  it('resumes workflow after approval', async ({ page }) => {
    // 1. Trigger approval interruption
    // 2. Click "Approve" button
    // 3. Verify workflow resumes
    // 4. Verify final results are displayed
  });

  it('cancels workflow on rejection', async ({ page }) => {
    // 1. Trigger approval interruption
    // 2. Click "Reject" button
    // 3. Verify workflow stops
    // 4. Verify rejection message shown
  });

  it('allows editing recommendations before approval', async ({ page }) => {
    // 1. Trigger approval interruption
    // 2. Edit recommendation text
    // 3. Click "Approve with changes"
    // 4. Verify edited recommendation is used
  });

  it('preserves state during long approval delay', async ({ page }) => {
    // 1. Trigger approval interruption
    // 2. Wait 5 minutes
    // 3. Approve recommendation
    // 4. Verify workflow resumes correctly
  });

  it('handles session timeout during approval', async ({ page }) => {
    // Test session timeout handling
  });
});
```

**Tool:** Playwright
**Coverage Target:** All HITL scenarios

---

### 3. Concurrent User Sessions Tests

**Test Location:** `tests/e2e/test_concurrent_sessions.spec.ts`

```typescript
describe('Concurrent User Sessions E2E', () => {
  it('handles 10 concurrent account analyses', async ({ browser }) => {
    // 1. Open 10 browser contexts
    // 2. Start account analysis in each
    // 3. Verify all complete successfully
    // 4. Verify state isolation
  });

  it('isolates approval workflows between sessions', async ({ browser }) => {
    // Test approval isolation
  });

  it('maintains independent state per session', async ({ browser }) => {
    // Test state isolation
  });
});
```

**Tool:** Playwright (multi-context)
**Coverage Target:** Concurrency scenarios

---

### 4. Real-Time Streaming Tests

**Test Location:** `tests/e2e/test_realtime_streaming.spec.ts`

```typescript
describe('Real-Time Streaming E2E', () => {
  it('displays streaming data scout results', async ({ page }) => {
    // Test data scout streaming
  });

  it('updates memory analysis in real-time', async ({ page }) => {
    // Test memory analyst streaming
  });

  it('streams recommendation generation progress', async ({ page }) => {
    // Test recommendation streaming
  });

  it('handles dropped SSE connections', async ({ page }) => {
    // Test SSE reconnection
  });
});
```

**Tool:** Playwright
**Coverage Target:** All streaming scenarios

---

## Performance Testing Strategy

### 1. Load Testing

**Test Location:** `tests/performance/test_load.py`

```python
class TestLoadPerformance:
    """Load tests for CopilotKit integration."""

    @pytest.mark.performance
    def test_handles_10_concurrent_requests(self):
        """Test system handles 10 concurrent account analyses."""
        # Use locust or pytest-benchmark
        pass

    @pytest.mark.performance
    def test_handles_50_concurrent_requests(self):
        """Test system handles 50 concurrent requests."""
        pass

    @pytest.mark.performance
    def test_response_time_under_load(self):
        """Test response times remain acceptable under load."""
        # Target: P95 < 5s, P99 < 10s
        pass
```

**Tool:** Locust or pytest-benchmark
**Target Metrics:**
- **Throughput**: 10 req/s sustained
- **P95 Response Time**: < 5 seconds
- **P99 Response Time**: < 10 seconds
- **Error Rate**: < 1%

---

### 2. Agent Scaling Tests

**Test Location:** `tests/performance/test_agent_scaling.py`

```python
class TestAgentScaling:
    """Performance tests for agent scaling."""

    @pytest.mark.performance
    def test_agent_execution_time_single(self):
        """Measure single agent execution time."""
        # Target: < 30s for complete analysis
        pass

    @pytest.mark.performance
    def test_agent_execution_time_concurrent(self):
        """Measure concurrent agent execution time."""
        pass

    @pytest.mark.performance
    def test_agent_memory_usage(self):
        """Measure memory usage during agent execution."""
        # Target: < 500MB per agent instance
        pass
```

**Target Metrics:**
- **Single Analysis**: < 30 seconds
- **Memory per Agent**: < 500MB
- **CPU per Agent**: < 50% of single core

---

### 3. Memory Usage Tests

**Test Location:** `tests/performance/test_memory_usage.py`

```python
class TestMemoryUsage:
    """Memory usage tests for long-running workflows."""

    @pytest.mark.performance
    def test_memory_usage_during_long_workflow(self):
        """Test memory usage during 10-minute workflow."""
        pass

    @pytest.mark.performance
    def test_memory_leak_detection(self):
        """Test for memory leaks during repeated operations."""
        pass

    @pytest.mark.performance
    def test_checkpointer_memory_usage(self):
        """Test memory usage of state checkpointer."""
        pass
```

**Target Metrics:**
- **Baseline Memory**: < 200MB idle
- **Peak Memory**: < 1GB during execution
- **Memory Growth**: < 10MB over 1 hour

---

## Monitoring & Observability Tests

### 1. Logging Tests

**Test Location:** `tests/observability/test_logging.py`

```python
class TestLogging:
    """Tests for logging across all layers."""

    def test_frontend_logs_requests(self):
        """Verify frontend logs API requests."""
        pass

    def test_nextjs_logs_forwarding(self):
        """Verify Next.js logs request forwarding."""
        pass

    def test_fastapi_logs_agent_execution(self):
        """Verify FastAPI logs agent execution."""
        pass

    def test_agents_log_state_transitions(self):
        """Verify agents log state transitions."""
        pass

    def test_logs_include_correlation_id(self):
        """Verify all logs include correlation ID."""
        pass

    def test_structured_logging_format(self):
        """Verify logs use structured JSON format."""
        pass
```

**Coverage Target:** 100% of critical operations logged

---

### 2. Metrics Collection Tests

**Test Location:** `tests/observability/test_metrics.py`

```python
class TestMetrics:
    """Tests for metrics collection."""

    def test_collects_request_count(self):
        """Verify request count metric is collected."""
        pass

    def test_collects_response_time(self):
        """Verify response time metric is collected."""
        pass

    def test_collects_agent_execution_time(self):
        """Verify agent execution time is tracked."""
        pass

    def test_collects_approval_wait_time(self):
        """Verify approval wait time is tracked."""
        pass

    def test_metrics_exported_to_prometheus(self):
        """Verify metrics are exported to Prometheus."""
        pass
```

**Coverage Target:** All key metrics instrumented

---

### 3. Error Tracking Tests

**Test Location:** `tests/observability/test_error_tracking.py`

```python
class TestErrorTracking:
    """Tests for error tracking integration."""

    def test_errors_sent_to_sentry(self):
        """Verify errors are sent to Sentry."""
        pass

    def test_error_includes_context(self):
        """Verify error reports include full context."""
        pass

    def test_error_grouping(self):
        """Verify errors are grouped correctly."""
        pass

    def test_performance_issues_tracked(self):
        """Verify slow transactions are tracked."""
        pass
```

**Coverage Target:** 100% of exceptions tracked

---

## Test Data & Fixtures

### Mock Zoho CRM Data

**Location:** `tests/fixtures/zoho_data.py`

```python
# Account fixtures
MOCK_ACCOUNT_ACTIVE = {
    "id": "acc_active_001",
    "Account_Name": "Acme Corporation",
    "Account_Status": "Active",
    "Owner": {"id": "owner_001", "name": "John Doe"},
    "Annual_Revenue": 1000000,
    "Total_Deal_Value": 250000,
    "Open_Deals_Count": 5,
    "Last_Activity_Time": "2025-10-15T10:00:00Z",
}

MOCK_ACCOUNT_AT_RISK = {
    "id": "acc_risk_001",
    "Account_Name": "Risk Corp",
    "Account_Status": "At Risk",
    "Owner": {"id": "owner_002", "name": "Jane Smith"},
    "Annual_Revenue": 500000,
    "Total_Deal_Value": 0,
    "Open_Deals_Count": 0,
    "Last_Activity_Time": "2025-08-01T10:00:00Z",
}

# Deal fixtures
MOCK_DEAL_NEGOTIATION = {
    "id": "deal_001",
    "Deal_Name": "Q4 Enterprise Deal",
    "Stage": "Negotiation",
    "Amount": 75000,
    "Probability": 75,
    "Close_Date": "2025-12-31",
}

# Activity fixtures
MOCK_ACTIVITY_MEETING = {
    "id": "activity_001",
    "Activity_Type": "Meeting",
    "Subject": "Quarterly Business Review",
    "Created_Time": "2025-10-15T14:00:00Z",
}

# Note fixtures
MOCK_NOTE_RISK = {
    "id": "note_001",
    "Content": "Customer expressed concerns about pricing",
    "Created_Time": "2025-10-14T16:30:00Z",
}
```

---

### Sample Request Payloads

**Location:** `tests/fixtures/request_payloads.py`

```python
# Account analysis request
ACCOUNT_ANALYSIS_REQUEST = {
    "agent_type": "orchestrator",
    "action": "analyze_account",
    "parameters": {
        "account_id": "acc_active_001",
        "include_memory": True,
        "generate_recommendations": True,
    },
    "session_id": "session_test_001",
}

# Approval response
APPROVAL_ACCEPT = {
    "session_id": "session_test_001",
    "action": "approve",
    "comment": "Approved by test user",
}

APPROVAL_REJECT = {
    "session_id": "session_test_001",
    "action": "reject",
    "reason": "Recommendation needs revision",
}
```

---

### Expected Response Formats

**Location:** `tests/fixtures/response_formats.py`

```python
# AG UI Protocol event formats
AG_UI_EVENT_AGENT_STARTED = {
    "type": "agent_started",
    "agent": "orchestrator",
    "step": 0,
    "task": "analyze_account",
    "timestamp": "2025-10-19T12:00:00Z",
}

AG_UI_EVENT_AGENT_STREAM = {
    "type": "agent_stream",
    "agent": "zoho_data_scout",
    "content": "Fetched 5 deals for account",
    "content_type": "text",
}

AG_UI_EVENT_AGENT_COMPLETED = {
    "type": "agent_completed",
    "agent": "recommendation_author",
    "step": 3,
    "output": {
        "recommendation": "...",
        "confidence_score": 0.85,
    },
}

AG_UI_EVENT_WORKFLOW_INTERRUPTED = {
    "type": "workflow_interrupted",
    "reason": "approval_required",
    "data": {
        "recommendation": "...",
        "approval_required": True,
    },
}
```

---

## Testing Tools & Infrastructure

### Python Testing Stack

```bash
# Core testing framework
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-mock==3.12.0
pytest-cov==4.1.0

# Test utilities
freezegun==1.4.0      # Time mocking
factory-boy==3.3.0    # Test data factories
faker==20.1.0         # Fake data generation

# Async testing
anyio==4.1.0
trio==0.23.2

# Performance testing
pytest-benchmark==4.0.0
locust==2.15.1

# Code quality
pytest-xdist==3.5.0   # Parallel execution
pytest-timeout==2.2.0 # Timeout handling
```

---

### TypeScript/JavaScript Testing Stack

```json
{
  "devDependencies": {
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.1.4",
    "@testing-library/user-event": "^14.5.1",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0",
    "@playwright/test": "^1.40.0",
    "msw": "^2.0.0",
    "@types/jest": "^29.5.8"
  }
}
```

---

### E2E Testing (Playwright)

```typescript
// playwright.config.ts
export default {
  testDir: './tests/e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
};
```

---

### Load Testing (Locust)

```python
# locustfile.py
from locust import HttpUser, task, between

class CopilotKitUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def analyze_account(self):
        self.client.post("/copilotkit", json={
            "agent_type": "orchestrator",
            "action": "analyze_account",
            "parameters": {"account_id": "acc_001"},
        }, stream=True)
```

---

## Coverage Requirements

### Coverage Targets by Layer

| Layer                  | Unit Tests | Integration Tests | E2E Tests | Total Target |
|------------------------|------------|-------------------|-----------|--------------|
| LangGraph Wrappers     | 95%        | 85%               | -         | 95%          |
| CopilotKitSDK          | 90%        | 85%               | -         | 90%          |
| FastAPI Endpoints      | 90%        | 85%               | 80%       | 90%          |
| Next.js API Routes     | 85%        | 80%               | 75%       | 85%          |
| Frontend Components    | 85%        | -                 | 75%       | 85%          |
| **Overall Target**     | **90%**    | **85%**           | **75%**   | **90%+**     |

---

### Coverage Reporting

```bash
# Python coverage
pytest --cov=src --cov-report=html --cov-report=term

# JavaScript coverage
npm run test:coverage

# Combined coverage report
npm run coverage:report
```

---

### Coverage Enforcement

```yaml
# .github/workflows/tests.yml
- name: Check coverage
  run: |
    pytest --cov --cov-fail-under=90
    npm run test:coverage -- --coverageThreshold='{"global":{"lines":85}}'
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test-copilotkit-integration.yml
name: CopilotKit Integration Tests

on:
  pull_request:
    branches: [main, develop]
    paths:
      - 'src/backend/copilotkit/**'
      - 'src/frontend/copilotkit/**'
      - 'tests/**'

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements-test.txt

      - name: Run unit tests
        run: pytest tests/unit --cov=src --cov-fail-under=90

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
    steps:
      - uses: actions/checkout@v3

      - name: Run integration tests
        run: pytest tests/integration --cov=src --cov-fail-under=85

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Playwright
        run: |
          npm install
          npx playwright install --with-deps

      - name: Start backend
        run: |
          python -m uvicorn src.backend.main:app &
          sleep 10

      - name: Start frontend
        run: |
          npm run dev &
          sleep 10

      - name: Run E2E tests
        run: npx playwright test

      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/

  performance-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request' && contains(github.event.pull_request.labels.*.name, 'performance')
    steps:
      - uses: actions/checkout@v3

      - name: Run load tests
        run: |
          pip install locust
          locust -f tests/performance/locustfile.py --headless -u 50 -r 5 -t 5m
```

---

### Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: run-tests
        name: Run unit tests
        entry: pytest tests/unit -x
        language: system
        pass_filenames: false

      - id: check-coverage
        name: Check test coverage
        entry: pytest tests/unit --cov=src --cov-fail-under=90 --quiet
        language: system
        pass_filenames: false
```

---

## Test Execution Plan

### Phase 1: Unit Tests (Week 1)

```bash
# Day 1-2: LangGraph wrappers
pytest tests/unit/langgraph -v

# Day 3: CopilotKitSDK
pytest tests/unit/backend/test_copilotkit_sdk.py -v

# Day 4: FastAPI endpoints
pytest tests/unit/backend/test_fastapi_endpoints.py -v

# Day 5: Frontend components
npm run test:unit
```

---

### Phase 2: Integration Tests (Week 2)

```bash
# Day 1-2: Full stack flow
pytest tests/integration/test_full_stack_flow.py -v

# Day 3: Agent coordination
pytest tests/integration/test_agent_coordination.py -v

# Day 4: State management
pytest tests/integration/test_state_management.py -v

# Day 5: Error handling
pytest tests/integration/test_error_handling.py -v
```

---

### Phase 3: E2E Tests (Week 3)

```bash
# Day 1-2: Account analysis workflow
npx playwright test tests/e2e/test_account_analysis_workflow.spec.ts

# Day 3: HITL approval workflow
npx playwright test tests/e2e/test_hitl_approval_workflow.spec.ts

# Day 4: Concurrent sessions
npx playwright test tests/e2e/test_concurrent_sessions.spec.ts

# Day 5: Real-time streaming
npx playwright test tests/e2e/test_realtime_streaming.spec.ts
```

---

### Phase 4: Performance Tests (Week 4)

```bash
# Day 1: Load testing
locust -f tests/performance/locustfile.py --headless -u 50 -r 5 -t 10m

# Day 2: Agent scaling
pytest tests/performance/test_agent_scaling.py -v

# Day 3: Memory usage
pytest tests/performance/test_memory_usage.py -v

# Day 4-5: Optimization and retesting
```

---

### Continuous Testing

```bash
# Watch mode for development
pytest tests/unit --watch

# Parallel execution for speed
pytest tests -n auto

# Run only failed tests
pytest --lf

# Run specific test markers
pytest -m "integration and not slow"
```

---

## Test Case Matrix

### Comprehensive Test Case Coverage

| Component                    | Unit | Integration | E2E | Performance | Total |
|------------------------------|------|-------------|-----|-------------|-------|
| OrchestratorAgent Wrapper    | 15   | 8           | 3   | 2           | 28    |
| ZohoDataScout Wrapper        | 12   | 6           | 2   | 1           | 21    |
| MemoryAnalyst Wrapper        | 12   | 6           | 2   | 1           | 21    |
| RecommendationAuthor Wrapper | 15   | 8           | 5   | 1           | 29    |
| CopilotKitSDK                | 10   | 5           | -   | 1           | 16    |
| FastAPI Endpoints            | 12   | 8           | 5   | 3           | 28    |
| Next.js API Routes           | 8    | 5           | 5   | 2           | 20    |
| Frontend Components          | 10   | -           | 8   | 1           | 19    |
| State Management             | 8    | 10          | 3   | 2           | 23    |
| Error Handling               | 12   | 10          | 5   | -           | 27    |
| HITL Workflows               | 8    | 8           | 10  | 1           | 27    |
| Monitoring & Logging         | 15   | 5           | -   | -           | 20    |
| **Total Test Cases**         | **137** | **79**   | **48** | **15**   | **279** |

---

## Success Criteria

### Must-Have (Blocking)

- ✅ Unit test coverage ≥ 90%
- ✅ Integration test coverage ≥ 85%
- ✅ All E2E critical paths pass
- ✅ Zero regression in existing functionality
- ✅ HITL approval workflow fully validated
- ✅ Performance benchmarks met (P95 < 5s)

### Should-Have (High Priority)

- ✅ E2E test coverage ≥ 75%
- ✅ Load testing with 50 concurrent users
- ✅ All error scenarios handled gracefully
- ✅ Monitoring and logging fully instrumented

### Nice-to-Have (Optional)

- ⭕ Visual regression testing
- ⭕ Accessibility testing
- ⭕ Security penetration testing
- ⭕ Chaos engineering tests

---

## Risk Mitigation

### High-Risk Areas

1. **HITL State Management**: Interruption and resumption complexity
   - **Mitigation**: Extensive integration and E2E tests for all scenarios

2. **Concurrent Session Isolation**: State leakage between sessions
   - **Mitigation**: Dedicated concurrent session tests with state validation

3. **SSE Connection Reliability**: Dropped connections and reconnection
   - **Mitigation**: Network failure simulation tests

4. **Agent Coordination**: Complex multi-agent interactions
   - **Mitigation**: Agent coordination integration tests with mock agents

---

## Test Data Management

### Test Database

```python
# tests/conftest.py
@pytest.fixture(scope="session")
def test_database():
    """Create test database with sample data."""
    db = create_test_database()
    seed_test_data(db)
    yield db
    drop_test_database(db)
```

### Data Factories

```python
# tests/factories.py
import factory

class AccountFactory(factory.Factory):
    class Meta:
        model = dict

    id = factory.Sequence(lambda n: f"acc_{n:03d}")
    Account_Name = factory.Faker('company')
    Account_Status = factory.Iterator(['Active', 'Inactive', 'At Risk'])
    Annual_Revenue = factory.Faker('random_int', min=10000, max=10000000)
```

---

## Appendix A: Test Execution Commands

### Quick Reference

```bash
# Run all tests
npm run test:all

# Run specific suites
npm run test:unit
npm run test:integration
npm run test:e2e
npm run test:performance

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Run specific file
pytest tests/unit/langgraph/test_orchestrator_wrapper.py -v

# Run with markers
pytest -m "unit and not slow"

# Run failed tests only
pytest --lf

# Run with debugging
pytest --pdb tests/integration/test_agent_coordination.py

# Generate HTML coverage report
pytest --cov --cov-report=html
```

---

## Appendix B: Test Markers

```python
# pytest.ini
[pytest]
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    slow: Slow-running tests (>5s)
    critical: Critical path tests
    hitl: Human-in-the-loop tests
    concurrent: Concurrency tests
```

---

## Appendix C: Test Templates

### Unit Test Template

```python
"""Unit tests for [Component]."""
import pytest
from unittest.mock import AsyncMock, patch

class Test[Component]:
    """Unit tests for [Component]."""

    @pytest.fixture
    def component(self):
        """Create component instance for testing."""
        return [Component]()

    def test_initialization(self, component):
        """Test component initializes correctly."""
        assert component is not None

    @pytest.mark.asyncio
    async def test_async_method(self, component):
        """Test async method behavior."""
        result = await component.async_method()
        assert result is not None
```

### Integration Test Template

```python
"""Integration tests for [Feature]."""
import pytest

@pytest.mark.integration
class Test[Feature]Integration:
    """Integration tests for [Feature]."""

    @pytest.mark.asyncio
    async def test_end_to_end_flow(self):
        """Test complete flow from start to finish."""
        # Setup
        # Execute
        # Verify
        pass
```

### E2E Test Template

```typescript
// E2E test template
import { test, expect } from '@playwright/test';

test.describe('[Feature] E2E', () => {
  test('completes [workflow] successfully', async ({ page }) => {
    // Navigate
    await page.goto('/');

    // Interact
    await page.click('button#start');

    // Verify
    await expect(page.locator('.result')).toBeVisible();
  });
});
```

---

## Document Control

**Version History:**

| Version | Date       | Author              | Changes                           |
|---------|------------|---------------------|-----------------------------------|
| 1.0     | 2025-10-19 | Testing Strategist  | Initial comprehensive strategy    |

**Approvals Required:**
- [ ] Technical Lead
- [ ] QA Lead
- [ ] DevOps Lead

**Next Steps:**
1. Review and approve testing strategy
2. Set up testing infrastructure
3. Implement test suites (Phases 1-4)
4. Execute tests and track coverage
5. Address gaps and optimize

---

**End of Testing Strategy Document**
