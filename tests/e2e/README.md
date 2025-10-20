# End-to-End (E2E) Test Suite

Comprehensive end-to-end integration tests for the Account Management Agent System.

## Overview

The E2E test suite validates complete workflows using realistic test data and mocked external APIs. Tests use a real database (test environment) to ensure accurate integration testing while maintaining test isolation and speed.

## Test Structure

```
tests/e2e/
├── __init__.py                    # E2E test package
├── conftest.py                    # E2E-specific fixtures
├── README.md                      # This file
│
├── fixtures/                      # Realistic test data
│   ├── __init__.py
│   ├── account_fixtures.py        # 50+ realistic accounts
│   ├── interaction_fixtures.py    # Historical interaction data
│   └── deal_fixtures.py          # Deal pipeline data
│
├── test_complete_workflow.py     # Full orchestrator workflows (800+ lines, 40+ tests)
├── test_sync_workflows.py        # Sync cycle tests (500+ lines, 30+ tests)
└── test_user_scenarios.py        # User journey tests (600+ lines, 35+ tests)
```

## Test Coverage

### 1. Complete Workflow Tests (`test_complete_workflow.py`)

**Coverage**: 40+ tests validating complete orchestrator workflows

#### Test Classes:
- `TestCompleteWorkflowOrchestration`: Core workflow execution
  - Daily review cycle (single/multi-owner)
  - Weekly review cycle
  - On-demand high-risk reviews
  - Parallel account processing
  - Approval gate integration
  - Error recovery
  - Performance validation

- `TestWorkflowStateManagement`: State persistence and recovery
  - Workflow checkpointing
  - Session tracking
  - Recovery from interruption

- `TestWorkflowIntegrationPoints`: Component integration
  - Zoho → Memory pipeline
  - Memory → Agent context
  - Agent → Approval pipeline

**Key Scenarios**:
- Process 20 accounts in under 10 minutes (PRD requirement)
- Handle parallel subagent execution (up to 10 concurrent)
- Recover from mid-workflow failures
- Maintain audit trail across workflow steps

### 2. Sync Workflow Tests (`test_sync_workflows.py`)

**Coverage**: 30+ tests validating data synchronization workflows

#### Test Classes:
- `TestFullSyncCycles`: Complete data synchronization
  - Full account sync
  - Relationship syncing (contacts, deals, activities)
  - Performance targets (<1 minute for 50 accounts)
  - Rate limit compliance

- `TestIncrementalSync`: Delta synchronization
  - Modified-only syncing
  - Change detection
  - Checkpoint recovery

- `TestWebhookProcessing`: Real-time sync
  - Account update webhooks
  - Bulk webhook processing
  - Processing order maintenance
  - Deduplication

- `TestSyncErrorRecovery`: Error handling
  - Retry with exponential backoff
  - Partial failure handling
  - Data validation
  - Conflict resolution

- `TestSyncPerformance`: Scalability
  - Throughput validation (>1 account/second)
  - Memory efficiency
  - Concurrent sync operations

**Key Scenarios**:
- Sync 50 accounts in under 60 seconds
- Handle webhook bursts (15+ simultaneous)
- Recover from transient failures
- Maintain data consistency

### 3. User Scenario Tests (`test_user_scenarios.py`)

**Coverage**: 35+ tests validating realistic user workflows

#### Test Classes:
- `TestDailyReviewScenario`: Morning briefing workflow
  - Account manager daily brief
  - Multi-manager simultaneous briefs
  - Email notification delivery

- `TestWeeklyReviewScenario`: Strategic review workflow
  - Comprehensive weekly analysis
  - Executive rollup reports
  - Trend analysis

- `TestOnDemandReviewScenario`: Ad-hoc requests
  - Immediate account analysis (<30 seconds)
  - Bulk on-demand analysis
  - Meeting preparation

- `TestEscalationScenario`: Critical account alerts
  - Automatic escalation (risk score ≥85)
  - Chain of command notifications
  - Multi-level escalation

- `TestApprovalRejectionScenario`: Change approval workflow
  - Recommendation approval
  - Rejection with feedback
  - Bulk approval processing

- `TestPerformanceUnderLoad`: Realistic load testing
  - Concurrent user sessions (5+ simultaneous)
  - Peak morning load (50 accounts)
  - Throughput validation

**Key Scenarios**:
- Generate daily brief in under 30 seconds
- Handle 5 concurrent user sessions
- Process escalations in real-time
- Maintain sub-minute response times

## Test Data

### Account Fixtures (50 realistic accounts)

1. **Healthy Accounts (15)**: Strong engagement, active pipeline
   - IDs: `ACC_HEALTHY_000` - `ACC_HEALTHY_014`
   - Characteristics: Recent activity, high NPS, multiple deals

2. **At-Risk Accounts (15)**: Declining engagement
   - IDs: `ACC_RISK_000` - `ACC_RISK_014`
   - Characteristics: Stale activity, low NPS, support issues

3. **High-Value Accounts (10)**: Strategic importance
   - IDs: `ACC_HIGHVAL_000` - `ACC_HIGHVAL_009`
   - Characteristics: Large revenue, executive sponsorship

4. **Growth Accounts (10)**: Expansion potential
   - IDs: `ACC_GROWTH_000` - `ACC_GROWTH_009`
   - Characteristics: Growing revenue, expansion opportunities

### Interaction Fixtures

- **Email Interactions**: 10-20 per account
- **Call Logs**: 5-15 per account
- **Meetings**: 3-8 per account
- **Support Tickets**: 1-10 per account
- **Product Usage**: 90 days of daily usage data

### Deal Pipeline Fixtures

- **Active Deals**: 0-10 per account
- **Won Deals**: 1-15 historical wins
- **Lost Deals**: 0-4 historical losses
- **Pipeline Metrics**: Calculated from deal data

## Running E2E Tests

### Run All E2E Tests
```bash
pytest tests/e2e/ -v
```

### Run Specific Test Suite
```bash
# Complete workflows
pytest tests/e2e/test_complete_workflow.py -v

# Sync workflows
pytest tests/e2e/test_sync_workflows.py -v

# User scenarios
pytest tests/e2e/test_user_scenarios.py -v
```

### Run by Test Class
```bash
# Daily review scenarios
pytest tests/e2e/test_user_scenarios.py::TestDailyReviewScenario -v

# Sync performance
pytest tests/e2e/test_sync_workflows.py::TestSyncPerformance -v
```

### Run with Performance Monitoring
```bash
pytest tests/e2e/ -v --durations=10
```

### Run Only Fast Tests (exclude slow)
```bash
pytest tests/e2e/ -v -m "not slow"
```

### Run with Coverage
```bash
pytest tests/e2e/ --cov=src --cov-report=html --cov-report=term
```

## Test Configuration

### Environment Variables

```bash
# Database
E2E_DATABASE_URL=sqlite:///./test_e2e.db  # Default SQLite
# E2E_DATABASE_URL=postgresql://user:pass@localhost/test_e2e  # For PostgreSQL

# External APIs (mocked by default)
MOCK_ZOHO=true
MOCK_COGNEE=true
MOCK_CLAUDE=true

# Performance thresholds
MAX_WORKFLOW_DURATION_SECONDS=600  # 10 minutes
MAX_SYNC_DURATION_SECONDS=60       # 1 minute
MAX_ANALYSIS_DURATION_SECONDS=30   # 30 seconds
```

### Pytest Configuration

E2E-specific markers:
- `@pytest.mark.e2e`: All E2E tests
- `@pytest.mark.slow`: Tests >30 seconds
- `@pytest.mark.e2e_workflow`: Workflow tests
- `@pytest.mark.e2e_sync`: Sync tests
- `@pytest.mark.e2e_scenarios`: User scenario tests

## Performance Targets

Tests validate these PRD requirements:

| Metric | Target | Test Validation |
|--------|--------|-----------------|
| Owner brief generation | <10 minutes | `test_workflow_performance_targets` |
| Account analysis | <30 seconds | `test_manager_requests_account_analysis` |
| Full sync (50 accounts) | <60 seconds | `test_full_sync_performance` |
| Concurrent agents | Up to 10 | `test_parallel_account_processing` |
| Webhook processing | Real-time | `test_webhook_account_update` |
| System throughput | >1 account/sec | `test_sync_throughput` |

## Mock vs Real Components

### Mocked (for speed and isolation):
- ✅ Zoho CRM API calls
- ✅ Cognee memory API calls
- ✅ Claude agent LLM calls
- ✅ Email/Slack notifications

### Real (for integration validation):
- ✅ Database operations (test database)
- ✅ Orchestrator logic
- ✅ Workflow engine
- ✅ State management
- ✅ Data transformations

## Best Practices

### Writing E2E Tests

1. **Use Realistic Data**: Leverage fixture generators for realistic scenarios
2. **Test Complete Flows**: Validate end-to-end, not individual steps
3. **Assert Business Outcomes**: Focus on user-visible results
4. **Monitor Performance**: Use performance fixtures to track metrics
5. **Clean State**: Each test should be independent and isolated

### Example E2E Test Structure

```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_user_workflow(
    mock_zoho_client_e2e,
    mock_cognee_client_e2e,
    mock_claude_agent,
    performance_monitor
):
    """Test complete user workflow from start to finish."""
    # Arrange: Set up realistic scenario
    account = get_all_test_accounts()[0]

    # Act: Execute complete workflow
    performance_monitor.start()

    # 1. Fetch data
    account_data = await mock_zoho_client_e2e.get_account(account["id"])

    # 2. Analyze
    analysis = await mock_claude_agent.query(
        "Analyze account", {"account": account_data}
    )

    # 3. Store results
    await mock_cognee_client_e2e.store(
        f"analysis_{account['id']}", analysis
    )

    performance_monitor.stop()

    # Assert: Validate business outcomes
    assert analysis is not None
    assert performance_monitor.metrics["duration_seconds"] < 30
```

## Continuous Integration

E2E tests run on:
- Pull request creation
- Merge to main branch
- Nightly full test suite

GitHub Actions configuration:
```yaml
- name: Run E2E Tests
  run: |
    pytest tests/e2e/ -v --cov=src --cov-report=xml

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
```

## Troubleshooting

### Common Issues

**Tests timing out:**
- Check performance thresholds in test assertions
- Verify mock delays aren't too aggressive
- Consider marking long tests with `@pytest.mark.slow`

**Database issues:**
- Ensure test database is properly cleaned between tests
- Check database URL environment variable
- Verify migrations are applied

**Flaky tests:**
- Review test isolation (each test should be independent)
- Check for race conditions in async code
- Add appropriate `await` statements

**Mock data issues:**
- Verify fixture generators produce valid data
- Check fixture relationships (accounts → contacts → deals)
- Validate data matches expected schema

## Maintenance

### Adding New E2E Tests

1. Identify complete user workflow to test
2. Create realistic test data using fixtures
3. Write test validating end-to-end flow
4. Add performance assertions
5. Document in this README

### Updating Test Data

1. Modify fixture generators in `fixtures/`
2. Ensure backward compatibility
3. Update dependent tests if needed
4. Regenerate fixture documentation

## Metrics & Reporting

E2E test execution generates:
- Test execution time per suite
- Coverage reports
- Performance metrics
- Failure analysis

Access reports:
```bash
# Generate HTML coverage report
pytest tests/e2e/ --cov=src --cov-report=html
open htmlcov/index.html

# Performance profiling
pytest tests/e2e/ --durations=0 > test_performance.txt
```

## Support

For questions or issues with E2E tests:
1. Check this README
2. Review test code comments
3. Consult main test documentation in `tests/README.md`
4. Contact: QA Team

---

**Week 12 Deliverable**: Comprehensive E2E test suite with 100+ tests covering complete workflows, sync operations, and realistic user scenarios.
