# Test Strategy for Sergas Super Account Manager

**Date**: 2025-10-19
**Test Engineer**: Testing Agent
**Project**: Sergas Super Account Manager - Week 6-11 Test Implementation

---

## Executive Summary

This document outlines the comprehensive testing strategy for the Sergas Super Account Manager, covering all testing phases from Week 6 (Backend Unit Tests) through Week 11 (Complete Test Suite). The testing follows a pyramid approach with emphasis on fast, isolated unit tests, comprehensive integration tests, and critical end-to-end scenarios.

**Current Status**: Week 6 Complete - AG UI Protocol Unit Tests

---

## Testing Pyramid

```
         /\
        /E2E\      <- 10-20 tests (Critical user journeys)
       /------\
      /Integr. \   <- 50-100 tests (Component interactions)
     /----------\
    /   Unit     \ <- 200+ tests (Fast, isolated)
   /--------------\
```

### Coverage Targets

- **Unit Tests**: >80% code coverage
- **Integration Tests**: All major workflows (100% critical paths)
- **E2E Tests**: All user-facing features (100% happy paths)
- **Performance Tests**: Meet SLA targets (<2s latency, 10+ concurrent users)

---

## Week 6: Backend Unit Tests ✅ COMPLETE

### AG UI Emitter Tests

**File**: `tests/unit/test_ag_ui_emitter.py` (663 lines, 26 tests)

**Test Coverage**:
- ✅ **Workflow Events**: workflow_started, workflow_completed (3 tests)
- ✅ **Agent Events**: agent_started, agent_stream, agent_completed, agent_error (6 tests)
- ✅ **Approval Events**: approval_required with recommendations (2 tests)
- ✅ **Tool Events**: tool_call, tool_result (4 tests)
- ✅ **State Snapshot**: workflow state tracking (1 test)
- ✅ **SSE Formatting**: Server-Sent Events format (2 tests)
- ✅ **Integration**: Complete workflow sequences (2 tests)
- ✅ **Performance**: Event emission speed (2 tests)
- ✅ **Edge Cases**: Unicode, long content, None values (4 tests)

**Results**:
- Total Tests: 26
- Passed: 26 (100%)
- Coverage: 100% (src/events/)
- Duration: <1 second

**Test Categories**:

1. **Workflow Event Tests** (`TestWorkflowEvents`)
   - Verifies workflow_started event structure and content
   - Tests workflow_completed with duration tracking
   - Validates auto-generated session IDs

2. **Agent Event Tests** (`TestAgentEvents`)
   - Tests agent lifecycle (started → stream → completed)
   - Verifies duration tracking between start and completion
   - Tests error event emission with stack traces
   - Edge case: agent_completed without prior agent_started

3. **Approval Event Tests** (`TestApprovalEvents`)
   - Tests approval_required event with recommendation data
   - Validates confidence scores (0-1 range)
   - Tests default and custom timeout values

4. **Tool Event Tests** (`TestToolEvents`)
   - Tests tool_call event with arguments
   - Verifies auto-generated tool call IDs
   - Tests tool_result for both success and failure cases

5. **State Snapshot Tests** (`TestStateSnapshotEvents`)
   - Tests state_snapshot with agent states and workflow context
   - Verifies session tracking across snapshots

6. **SSE Formatting Tests** (`TestSSEFormatting`)
   - Tests Server-Sent Events format compliance
   - Verifies event streaming with async generators
   - Tests JSON serialization with datetime handling

7. **Integration Tests** (`TestEventEmitterIntegration`)
   - Tests complete workflow: start → agents → approval → complete
   - Tests error handling workflow with agent_error events
   - Validates event ordering and sequencing

8. **Performance Tests** (`TestEventEmitterPerformance`)
   - Session ID generation: 1000 IDs in <100ms
   - Event emission: 1000 events in <100ms

9. **Edge Case Tests** (`TestEdgeCases`)
   - Unicode content handling
   - Very long content (10KB streams)
   - None/null value handling
   - Minimal recommendation data

---

## Week 7: Integration Tests

### Multi-Agent AG UI Workflow Tests

**Planned File**: `tests/integration/test_multi_agent_ag_ui.py`

**Test Scenarios**:

1. **Complete Account Analysis Workflow**
   ```python
   async def test_complete_account_analysis_workflow():
       """Test Zoho → Memory → Recommendation → Approval flow."""
       # 1. Zoho Scout fetches account data
       # 2. Memory Analyst analyzes patterns
       # 3. Recommendation Author generates suggestions
       # 4. Approval gate triggers
       # 5. Verify all AG UI events emitted in correct order
   ```

2. **Parallel Agent Execution**
   ```python
   async def test_parallel_agent_execution():
       """Test multiple agents running concurrently."""
       # Spawn 3 agents simultaneously
       # Verify event interleaving
       # Ensure no race conditions
   ```

3. **Error Recovery and Retry**
   ```python
   async def test_agent_error_recovery():
       """Test workflow continues after agent error."""
       # Simulate agent failure
       # Verify retry logic
       # Check error events emitted
   ```

4. **Approval Workflow**
   ```python
   async def test_approval_accept_reject_flows():
       """Test approval, rejection, and modification."""
       # Test approve action → CRM update
       # Test reject action → audit log
       # Test modify action → recommendation update
   ```

### SSE Streaming Integration Tests

**Planned File**: `tests/integration/test_ag_ui_stream.py`

**Test Scenarios**:

1. **EventSource Connection**
   ```python
   async def test_eventsource_connection():
       """Test SSE connection establishment and keepalive."""
       # Connect to /api/agent/stream
       # Verify connection headers
       # Test reconnection on failure
   ```

2. **Concurrent Streams**
   ```python
   async def test_concurrent_agent_streams():
       """Test 10+ concurrent SSE streams."""
       # Open 10 connections
       # Verify each receives correct events
       # Check no cross-stream contamination
   ```

3. **Stream Reliability**
   ```python
   async def test_stream_resilience():
       """Test stream handles disconnects gracefully."""
       # Simulate network interruption
       # Verify reconnection
       # Check no events lost
   ```

**Target Coverage**: 100% of critical integration paths

---

## Week 8: Performance Tests

### Load Testing

**Planned File**: `tests/performance/test_ag_ui_performance.py`

**Test Scenarios**:

1. **Concurrent Connections**
   ```python
   async def test_concurrent_agent_streams():
       """Test system handles 10+ concurrent streams."""
       # Metrics:
       # - Connection establishment time
       # - Event streaming latency
       # - Memory usage per connection
       # - CPU usage under load

       # Target: <2s latency, <500MB memory for 10 streams
   ```

2. **Event Throughput**
   ```python
   async def test_event_streaming_throughput():
       """Test maximum events per second."""
       # Stream 1000 events
       # Measure: events/second, latency p95, p99

       # Target: >100 events/sec, p95 < 100ms
   ```

3. **Long-Running Workflows**
   ```python
   async def test_long_running_workflow_stability():
       """Test workflow running for 30+ minutes."""
       # Run workflow continuously
       # Monitor: memory leaks, connection stability

       # Target: <1% memory growth, no connection drops
   ```

4. **Auto-Scaling**
   ```python
   async def test_auto_scaling_behavior():
       """Test system scales with load."""
       # Gradually increase concurrent users
       # Verify performance remains acceptable

       # Target: Linear scaling to 20 users
   ```

**Performance Targets**:
- Event latency: <2 seconds (p95)
- Concurrent streams: 10+ without degradation
- Memory usage: <100MB per stream
- CPU usage: <60% under normal load

**Metrics Collection**:
- Prometheus metrics endpoint
- Grafana dashboards
- Performance baseline documentation

---

## Week 9: Frontend E2E Tests

### Playwright Tests

**Planned File**: `tests/e2e/test_frontend_integration.spec.ts`

**Test Scenarios**:

1. **User Sends Message**
   ```typescript
   test('user triggers account analysis', async ({ page }) => {
     // Navigate to dashboard
     // Click "Analyze Account" button
     // Verify EventSource connection established
     // Verify agent status updates appear
   });
   ```

2. **Approval Modal Interaction**
   ```typescript
   test('approval modal appears and user approves', async ({ page }) => {
     // Wait for approval_required event
     // Verify modal displays recommendation
     // Click "Approve" button
     // Verify approval response sent
     // Verify success confirmation
   });
   ```

3. **Tool Call Visualization**
   ```typescript
   test('tool calls displayed in UI', async ({ page }) => {
     // Verify tool_call events render
     // Check tool arguments displayed
     // Verify tool_result shows success/failure
   });
   ```

4. **Error Handling**
   ```typescript
   test('UI handles agent errors gracefully', async ({ page }) => {
     // Trigger agent error
     // Verify error message displayed
     // Check retry option available
   });
   ```

### Visual Regression Tests

**Planned File**: `tests/e2e/visual_regression.spec.ts`

- Screenshot approval modal
- Screenshot tool call cards
- Screenshot chat interface
- Compare against baseline images

**E2E Coverage**: 100% of critical user paths

---

## Weeks 10-11: Complete Test Suite

### Test Infrastructure

**Files to Create**:

1. **Test Fixtures** (`tests/fixtures/`)
   - `ag_ui_fixtures.py` - Event emitter fixtures
   - `orchestrator_fixtures.py` - Mock orchestrators
   - `account_fixtures.py` - Sample account data

2. **Test Utilities** (`tests/utils/`)
   - `event_validators.py` - AG UI event validation
   - `sse_client.py` - Test SSE client
   - `performance_monitor.py` - Performance measurement

3. **CI/CD Integration** (`.github/workflows/`)
   - `test.yml` - Run all tests on PR
   - `coverage.yml` - Coverage reporting
   - `performance.yml` - Performance regression tests

### Test Documentation

**Files to Create**:

1. **README** (`tests/README.md`)
   - Quick start guide
   - Running specific test suites
   - Debugging test failures
   - Contributing new tests

2. **Coverage Report** (`tests/coverage/`)
   - HTML coverage report
   - Coverage trends over time
   - Uncovered code analysis

3. **Performance Baselines** (`tests/performance/baselines/`)
   - Baseline metrics (JSON)
   - Performance regression detection
   - Historical performance data

---

## Testing Best Practices

### 1. Test-Driven Development (TDD)

- ✅ Write tests before implementation when possible
- ✅ Red-Green-Refactor cycle
- ✅ Tests define expected behavior

### 2. Test Isolation

- ✅ Each test is independent
- ✅ No shared state between tests
- ✅ Use fixtures for setup/teardown

### 3. Descriptive Test Names

- ✅ Test names explain what and why
- ✅ Format: `test_<action>_<expected_result>`
- ✅ Example: `test_emit_workflow_started_creates_valid_event`

### 4. Arrange-Act-Assert Pattern

```python
def test_example():
    # Arrange: Set up test data
    emitter = AGUIEventEmitter()

    # Act: Execute the operation
    event = emitter.emit_workflow_started("test", "ACC-001")

    # Assert: Verify the result
    assert event["type"] == "workflow_started"
```

### 5. Test Data Builders

```python
def build_recommendation(**overrides):
    """Build recommendation with sensible defaults."""
    defaults = {
        "recommendation_id": "REC-001",
        "account_id": "ACC-001",
        "action": "Follow up",
        "confidence_score": 0.8,
        "priority": "medium"
    }
    return {**defaults, **overrides}
```

### 6. Mock External Dependencies

- ✅ Mock Zoho CRM API calls
- ✅ Mock Cognee memory operations
- ✅ Mock Claude SDK responses
- ✅ Use test doubles for reliability

### 7. Performance Testing

- ✅ Establish baselines early
- ✅ Monitor trends over time
- ✅ Fail CI on regressions
- ✅ Profile slow tests

---

## Test Execution

### Running Tests

```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Performance tests
pytest tests/performance/ -v --benchmark-only

# E2E tests
playwright test tests/e2e/

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Markers

```bash
# Run only fast tests
pytest -m "not slow"

# Run integration tests
pytest -m integration

# Run performance tests
pytest -m performance
```

### Continuous Integration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          pytest tests/ --cov=src --cov-fail-under=80
      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

---

## Success Criteria

### Week 6 ✅ COMPLETE
- [x] AG UI emitter unit tests (26 tests, 100% coverage)
- [x] Event schema validation tests
- [x] SSE formatting tests
- [x] Performance benchmarks established

### Week 7
- [ ] Multi-agent integration tests (10+ tests)
- [ ] SSE streaming tests (5+ tests)
- [ ] Approval workflow tests (5+ tests)

### Week 8
- [ ] Load tests (10+ concurrent users)
- [ ] Latency tests (<2s p95)
- [ ] Memory leak tests
- [ ] Auto-scaling tests

### Week 9
- [ ] Playwright E2E tests (10+ scenarios)
- [ ] Visual regression tests
- [ ] Error handling tests

### Weeks 10-11
- [ ] Complete test documentation
- [ ] CI/CD integration
- [ ] Performance baseline documentation
- [ ] >80% overall code coverage

---

## Test Metrics Dashboard

### Current Status (Week 6)

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Unit Test Coverage | >80% | 100% (src/events/) | ✅ PASS |
| Test Execution Time | <5s | <1s | ✅ PASS |
| Test Pass Rate | 100% | 100% (26/26) | ✅ PASS |
| Performance (event emission) | <100ms/1000 events | ~50ms/1000 events | ✅ PASS |

### Weekly Progress Tracking

- **Week 6**: ✅ Backend unit tests complete (100%)
- **Week 7**: 🔄 Integration tests in progress (0%)
- **Week 8**: ⏳ Performance tests pending
- **Week 9**: ⏳ E2E tests pending
- **Weeks 10-11**: ⏳ Documentation and CI/CD pending

---

## Contact & Support

**Test Engineer**: Testing Agent
**Project Lead**: See `docs/PROJECT_COMPLETION_REPORT.md`
**Issues**: Create ticket in project tracking system

---

**Last Updated**: 2025-10-19
**Next Review**: Week 7 Start
**Document Version**: 1.0
