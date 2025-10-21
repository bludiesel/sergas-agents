# Integration Tests for SERGAS Agents System

This directory contains comprehensive integration tests for the SERGAS Agents system, ensuring all components work together seamlessly and the system is production-ready.

## Overview

The integration test suite covers:

- **Workflow Engine Testing**: Real scenario execution with conditional logic and parallel processing
- **GLM Integration Testing**: Model selection, chat completion, and error handling
- **Self-Modification System Testing**: Code modification with rollback validation and safety checks
- **Zoho Evolution System Testing**: Adaptive API calls with learning and intelligent field selection
- **Monitoring System Testing**: Metrics collection, alerting, and performance monitoring
- **End-to-End Workflow Testing**: Complete system integration scenarios
- **Performance Benchmarks**: Load testing, stress testing, and performance validation

## Test Structure

```
tests/integration/
├── conftest.py                    # Test configuration and fixtures
├── full_system_integration_test.py # Main integration test suite
├── run_integration_tests.py       # Test runner script
├── requirements.txt               # Test dependencies
├── README.md                      # This file
└── reports/                       # Test reports (created automatically)
    ├── integration_report_*.txt
    ├── integration_results_*.json
    ├── coverage_html/
    ├── test_report.html
    └── test_report.json
```

## Prerequisites

1. **Python 3.8+**: Required for async/await support
2. **Dependencies**: Install via `pip install -r requirements.txt`
3. **Environment Variables**: Set up required environment variables:
   ```bash
   export GLM_API_KEY="your_glm_api_key"
   export GLM_BASE_URL="https://open.bigmodel.cn/api/paas/v4"
   export ZOHO_CLIENT_ID="your_zoho_client_id"
   export ZOHO_CLIENT_SECRET="your_zoho_client_secret"
   export ZOHO_REFRESH_TOKEN="your_zoho_refresh_token"
   ```

## Quick Start

### 1. Health Check
Run a quick health check to verify the environment:
```bash
python tests/integration/run_integration_tests.py --health-check-only
```

### 2. Install Dependencies
If the health check fails, install dependencies:
```bash
python tests/integration/run_integration_tests.py --install-deps
```

### 3. Run All Tests
Run the complete integration test suite:
```bash
python tests/integration/run_integration_tests.py
```

### 4. Run Specific Tests
Run specific test categories:
```bash
# Run only integration tests
python tests/integration/run_integration_tests.py --markers integration

# Run only performance tests
python tests/integration/run_integration_tests.py --markers performance

# Run with parallel execution
python tests/integration/run_integration_tests.py --parallel --workers 8

# Run without coverage (faster)
python tests/integration/run_integration_tests.py --no-coverage
```

## Test Categories

### 1. GLM Integration Tests (`TestGLMIntegration`)
- **Model Selection**: Test available models and selection logic
- **Chat Completion**: Test message processing and response handling
- **Error Handling**: Test invalid models, empty messages, and API errors
- **Performance**: Measure response times and token usage

### 2. Workflow Engine Tests (`TestWorkflowEngine`)
- **Basic Execution**: Test workflow creation and execution
- **Conditional Logic**: Test if/else branches and decision points
- **Parallel Execution**: Test concurrent step execution
- **Error Recovery**: Test workflow failure and recovery

### 3. Self-Modification System Tests (`TestSelfModificationSystem`)
- **Code Modification**: Test safe code changes and enhancements
- **Rollback Validation**: Test ability to revert changes
- **Safety Checks**: Test protection against dangerous modifications
- **History Tracking**: Test modification history and audit trail

### 4. Zoho Evolution System Tests (`TestZohoEvolutionSystem`)
- **Adaptive API Calls**: Test learning from API usage patterns
- **Intelligent Field Selection**: Test smart field recommendations
- **Error Recovery**: Test API error handling and adaptation
- **Learning Insights**: Test pattern recognition and optimization

### 5. Monitoring System Tests (`TestMonitoringSystem`)
- **Metrics Collection**: Test metric recording and aggregation
- **Alert System**: Test threshold-based alerting
- **Performance Monitoring**: Test system performance tracking
- **Data Retention**: Test metric cleanup and storage

### 6. Orchestrator Integration Tests (`TestOrchestratorIntegration`)
- **End-to-End Workflows**: Test complete request processing
- **Component Coordination**: Test multi-component workflows
- **Error Propagation**: Test error handling across components
- **Performance Validation**: Test orchestrator performance

### 7. Performance Benchmarks (`TestPerformanceBenchmarks`)
- **System Benchmarks**: Test performance against defined thresholds
- **Load Testing**: Test concurrent request handling
- **Memory Validation**: Test memory usage and leaks
- **Response Time**: Test API and workflow response times

## Test Configuration

### Performance Thresholds
```python
PERFORMANCE_THRESHOLDS = {
    "workflow_completion_time": 30.0,  # seconds
    "api_response_time": 2.0,          # seconds
    "memory_usage_mb": 512,            # MB
    "cpu_usage_percent": 80            # %
}
```

### Alert Thresholds
```python
ALERT_THRESHOLDS = {
    "error_rate": 0.1,      # 10%
    "response_time": 5000,  # milliseconds
    "memory_usage": 0.8     # 80%
}
```

### Test Data
- **Account ID**: `test_account_001`
- **Contact ID**: `test_contact_001`
- **Deal ID**: `test_deal_001`

## Mock Services

The tests use mock services to simulate external dependencies:

### Mock GLM Client
- Simulates chat completion responses
- Tracks call counts and response times
- Provides error simulation capabilities

### Mock Zoho Client
- Simulates account, contact, and deal operations
- Tracks learning data and usage patterns
- Provides error simulation for testing recovery

## Test Reports

After running tests, reports are generated in the `reports/` directory:

### Integration Report (`integration_report_*.txt`)
- Human-readable summary of test results
- Performance metrics and recommendations
- Failed test details (if any)

### JSON Results (`integration_results_*.json`)
- Machine-readable test results
- Detailed timing and performance data
- Test metadata and configuration

### Coverage Report (`coverage_html/`)
- HTML code coverage report
- Line-by-line coverage analysis
- Coverage statistics by module

### HTML Report (`test_report.html`)
- Interactive test results viewer
- Detailed test execution information
- Visual performance metrics

## Performance Validation

The tests validate the following performance criteria:

### Response Times
- **Workflow Completion**: < 30 seconds
- **API Response**: < 2 seconds
- **GLM Chat Completion**: < 1 second

### Resource Usage
- **Memory Usage**: < 512 MB
- **CPU Usage**: < 80%
- **Concurrent Requests**: Handle 10+ concurrent requests

### Reliability
- **Success Rate**: > 95%
- **Error Recovery**: < 10 second recovery time
- **System Stability**: No memory leaks or crashes

## Continuous Integration

### GitHub Actions Example
```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r tests/integration/requirements.txt
      - name: Run integration tests
        run: |
          python tests/integration/run_integration_tests.py
        env:
          GLM_API_KEY: ${{ secrets.GLM_API_KEY }}
          ZOHO_CLIENT_ID: ${{ secrets.ZOHO_CLIENT_ID }}
          ZOHO_CLIENT_SECRET: ${{ secrets.ZOHO_CLIENT_SECRET }}
          ZOHO_REFRESH_TOKEN: ${{ secrets.ZOHO_REFRESH_TOKEN }}
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'src.agents.orchestrator'
   ```
   **Solution**: Ensure you're running from the project root directory

2. **Missing Dependencies**
   ```
   pytest: command not found
   ```
   **Solution**: Run `python tests/integration/run_integration_tests.py --install-deps`

3. **Environment Variables**
   ```
   KeyError: 'GLM_API_KEY'
   ```
   **Solution**: Set required environment variables before running tests

4. **Permission Errors**
   ```
   PermissionError: [Errno 13] Permission denied
   ```
   **Solution**: Ensure write permissions for the tests directory

### Debug Mode

Run tests with debug output:
```bash
python tests/integration/run_integration_tests.py --verbose
```

### Individual Test Debugging

Run specific test classes or methods:
```bash
# Run specific test class
pytest tests/integration/full_system_integration_test.py::TestGLMIntegration -v

# Run specific test method
pytest tests/integration/full_system_integration_test.py::TestGLMIntegration::test_model_selection_and_chat_completion -v -s
```

## Production Readiness Checklist

The integration tests verify the following production readiness criteria:

### ✅ Functional Requirements
- [ ] All components integrate correctly
- [ ] End-to-end workflows execute successfully
- [ ] Error handling works as expected
- [ ] Data consistency is maintained

### ✅ Performance Requirements
- [ ] Response times meet thresholds
- [ ] System handles expected load
- [ ] Resource usage stays within limits
- [ ] No memory leaks or performance degradation

### ✅ Reliability Requirements
- [ ] High success rate (>95%)
- [ ] Graceful error recovery
- [ ] System stability under load
- [ ] Proper error logging and monitoring

### ✅ Security Requirements
- [ ] Input validation works correctly
- [ ] No sensitive data exposure
- [ ] Safe self-modification operations
- [ ] Proper authentication and authorization

## Contributing

When adding new integration tests:

1. **Follow Naming Conventions**: Use descriptive test names
2. **Use Fixtures**: Leverage existing fixtures for consistency
3. **Mock External Dependencies**: Don't rely on external services
4. **Add Performance Tests**: Include performance validation for new features
5. **Update Documentation**: Keep this README updated

## Support

For issues with the integration tests:

1. Check the troubleshooting section above
2. Review test logs and reports
3. Verify environment configuration
4. Create an issue with detailed error information

---

**Note**: These tests are designed to validate that the SERGAS Agents system is production-ready. All tests should pass before deploying to production environments.