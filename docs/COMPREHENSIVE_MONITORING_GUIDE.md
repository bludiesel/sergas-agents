# Comprehensive Testing and Monitoring Infrastructure

This document describes the comprehensive testing and monitoring infrastructure implemented for the Sergas Agents system.

## Overview

The `src/monitoring/comprehensive_monitoring.py` module provides a complete testing and monitoring hub with:

- **Multiple Test Suites**: Unit, integration, performance, security, load, regression, smoke, e2e, compatibility, and stress testing
- **Metrics Collection**: Prometheus integration with system, application, database, network, memory, CPU, and custom metrics
- **Alert Management**: Multi-channel alerting with email, Slack, and webhook notifications
- **Health Checks**: Comprehensive system health monitoring with multiple providers
- **Real-time Monitoring**: Continuous monitoring with configurable intervals

## Architecture

### Core Components

#### 1. Enums and Data Classes

```python
# Test Types
class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    SECURITY = "security"
    LOAD = "load"
    REGRESSION = "regression"
    SMOKE = "smoke"
    E2E = "e2e"
    COMPATIBILITY = "compatibility"
    STRESS = "stress"

# Monitor Types
class MonitorType(Enum):
    SYSTEM = "system"
    APPLICATION = "application"
    DATABASE = "database"
    NETWORK = "network"
    MEMORY = "memory"
    CPU = "cpu"
    CUSTOM = "custom"

# Alert Levels
class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
```

#### 2. Test Runner

The `TestRunner` class provides comprehensive test execution capabilities:

- **Parallel Test Execution**: Run multiple tests concurrently for faster execution
- **Test Result Aggregation**: Collect and analyze test results
- **Coverage Reporting**: Track test coverage metrics
- **Performance Benchmarking**: Measure test execution performance
- **Retry Logic**: Automatic retry for failed tests
- **Timeout Handling**: Prevent tests from running indefinitely

```python
# Initialize test runner
test_runner = TestRunner(max_workers=8)

# Register test suite
suite = TestSuite(
    name="Unit Tests",
    test_type=TestType.UNIT,
    timeout=60.0,
    parallel=True,
    max_workers=4
)
test_runner.register_suite(suite)

# Run tests
results = await test_runner.run_suite(TestType.UNIT)
```

#### 3. Metrics Collector

The `MetricsCollector` class provides comprehensive metrics collection with Prometheus integration:

- **System Metrics**: CPU, memory, disk, network usage
- **Application Metrics**: HTTP requests, response times, active connections
- **Business Metrics**: Custom business-specific metrics
- **Prometheus Integration**: Export metrics in Prometheus format
- **Real-time Collection**: Continuous metrics collection

```python
# Initialize metrics collector
metrics_collector = MetricsCollector()

# Collect system metrics
metrics = metrics_collector.collect_metrics()

# Record HTTP request metrics
metrics_collector.record_http_request(
    method="GET",
    endpoint="/api/users",
    status=200,
    duration=0.150
)

# Get Prometheus metrics
prometheus_metrics = metrics_collector.get_prometheus_metrics()
```

#### 4. Alert Manager

The `AlertManager` class provides comprehensive alerting capabilities:

- **Alert Rules**: Define custom alert conditions
- **Multiple Channels**: Email, Slack, webhook notifications
- **Alert Deduplication**: Prevent duplicate alerts
- **Cooldown Management**: Control alert frequency
- **Alert History**: Track alert history and trends

```python
# Initialize alert manager
alert_manager = AlertManager()

# Add notification channel
alert_manager.add_notification_channel(
    SlackNotificationChannel(webhook_url="https://hooks.slack.com/...")
)

# Add custom alert rule
alert_manager.add_rule(AlertRule(
    name="high_cpu_usage",
    condition=lambda m: m.name == "cpu_usage_percent" and m.value > 80,
    level=AlertLevel.WARNING,
    message_template="High CPU usage: {metric_value}%"
))

# Evaluate metrics and generate alerts
alerts = alert_manager.evaluate_metrics(metrics)
```

#### 5. Health Checker

The `HealthChecker` class provides comprehensive health monitoring:

- **Multiple Providers**: Database, HTTP endpoints, system resources
- **Parallel Execution**: Run health checks concurrently
- **Health Status Aggregation**: Determine overall system health
- **Historical Data**: Track health trends over time

```python
# Initialize health checker
health_checker = HealthChecker()

# Add health check provider
health_checker.add_provider(
    DatabaseHealthCheck(connection_string="postgresql://...")
)

# Check all health
health_status = await health_checker.check_all_health()

# Get overall health
overall_health = await health_checker.get_overall_health()
```

## Usage Examples

### Basic Setup

```python
import asyncio
from monitoring.comprehensive_monitoring import ComprehensiveMonitoringSystem

async def main():
    # Initialize monitoring system
    monitoring_system = ComprehensiveMonitoringSystem({
        "max_test_workers": 4,
        "slack_webhook_url": "https://hooks.slack.com/...",
        "smtp": {
            "host": "smtp.gmail.com",
            "port": 587,
            "username": "alerts@company.com",
            "password": "password"
        }
    })

    # Start monitoring
    await monitoring_system.start_monitoring(interval=60.0)

    try:
        # Run comprehensive tests
        test_results = await monitoring_system.run_comprehensive_tests()
        print(f"Tests completed: {test_results['summary']['success_rate']:.1f}% success rate")

        # Get system status
        status = await monitoring_system.get_system_status()
        print(f"System health: {status['health']['overall']['status']}")

        # Keep monitoring running
        await asyncio.sleep(300)  # 5 minutes

    finally:
        await monitoring_system.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
```

### Custom Tests

```python
from monitoring.comprehensive_monitoring import test, performance_test, integration_test

# Unit test
@test(test_type=TestType.UNIT)
async def test_user_creation():
    """Test user creation functionality."""
    # Test logic here
    user = create_user("test@example.com")
    assert user.email == "test@example.com"
    return True

# Performance test
@performance_test(max_duration=2.0, max_memory_mb=100.0)
@test(test_type=TestType.PERFORMANCE)
async def test_api_performance():
    """Test API endpoint performance."""
    start_time = time.time()

    # Make API call
    response = await make_api_call("/api/users")

    duration = time.time() - start_time
    assert duration < 1.0, "API call should complete within 1 second"
    return response.status_code == 200

# Integration test
@integration_test(dependencies=["database", "redis"])
@test(test_type=TestType.INTEGRATION)
async def test_user_workflow():
    """Test complete user workflow."""
    # Create user
    user = await create_user("test@example.com")

    # Verify user in database
    db_user = await get_user_from_db(user.id)
    assert db_user.email == "test@example.com"

    # Cache user in Redis
    await cache_user(user)

    # Verify cache
    cached_user = await get_cached_user(user.id)
    assert cached_user.id == user.id

    return True
```

### Custom Metrics

```python
from monitoring.comprehensive_monitoring import MonitoringMetric, MonitorType

def custom_metrics_collector():
    """Collect custom business metrics."""
    metrics = [
        MonitoringMetric(
            name="active_users",
            value=get_active_user_count(),
            timestamp=datetime.now(),
            metric_type=MonitorType.CUSTOM,
            unit="count",
            description="Number of active users"
        ),
        MonitoringMetric(
            name="conversion_rate",
            value=get_conversion_rate(),
            timestamp=datetime.now(),
            metric_type=MonitorType.BUSINESS,
            unit="percent",
            description="User conversion rate"
        )
    ]

    return metrics

# Add to monitoring system
monitoring_system.add_custom_metric_collector(custom_metrics_collector)
```

### Custom Alert Rules

```python
from monitoring.comprehensive_monitoring import AlertRule, AlertLevel

# Custom alert rule
high_error_rate_rule = AlertRule(
    name="high_error_rate",
    condition=lambda m: m.name == "error_rate" and m.value > 5.0,
    level=AlertLevel.WARNING,
    message_template="High error rate detected: {metric_value} errors/minute",
    cooldown=300.0  # 5 minutes cooldown
)

monitoring_system.add_custom_alert_rule(high_error_rate_rule)

# Custom business alert
low_conversion_rule = AlertRule(
    name="low_conversion_rate",
    condition=lambda m: m.name == "conversion_rate" and m.value < 2.0,
    level=AlertLevel.ERROR,
    message_template="Low conversion rate: {metric_value}%",
    cooldown=600.0  # 10 minutes cooldown
)

monitoring_system.add_custom_alert_rule(low_conversion_rule)
```

## Configuration

### Environment Variables

```bash
# Slack notifications
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

# Email notifications
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="alerts@company.com"
export SMTP_PASSWORD="password"

# Alert webhook
export ALERT_WEBHOOK_URL="https://api.company.com/alerts"

# Prometheus pushgateway
export PROMETHEUS_GATEWAY="http://prometheus-pushgateway:9091"
```

### Configuration File

```python
config = {
    # Test configuration
    "max_test_workers": 8,
    "test_timeout": 300.0,
    "test_retry_count": 2,

    # Monitoring configuration
    "monitoring_interval": 60.0,
    "metrics_retention": 10000,

    # Alert configuration
    "alert_cooldown": 300.0,
    "max_alerts_per_minute": 10,

    # Health check configuration
    "health_check_timeout": 10.0,
    "health_check_interval": 30.0,

    # Notification channels
    "slack_webhook_url": os.getenv("SLACK_WEBHOOK_URL"),
    "alert_webhook_url": os.getenv("ALERT_WEBHOOK_URL"),
    "smtp": {
        "host": os.getenv("SMTP_HOST"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "username": os.getenv("SMTP_USERNAME"),
        "password": os.getenv("SMTP_PASSWORD")
    }
}
```

## API Endpoints

The monitoring system provides several API endpoints:

### Health Check

```
GET /health
```

Returns the overall system health status.

```json
{
  "status": "healthy",
  "component": "overall_system",
  "message": "Overall system health: healthy (5/5 components healthy)",
  "details": {
    "total_checks": 5,
    "healthy_checks": 5,
    "degraded_checks": 0,
    "unhealthy_checks": 0,
    "average_response_time": 0.150
  }
}
```

### Metrics

```
GET /metrics
```

Returns Prometheus-formatted metrics.

```
# HELP system_cpu_usage_percent Current CPU usage percentage
# TYPE system_cpu_usage_percent gauge
system_cpu_usage_percent 25.5

# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/users",status="200"} 1250
```

### System Status

```
GET /api/monitoring/status
```

Returns comprehensive system status including health, alerts, metrics, and tests.

```json
{
  "timestamp": "2025-10-20T10:30:00Z",
  "health": {
    "overall": {
      "status": "healthy",
      "message": "Overall system health: healthy"
    },
    "individual": {
      "SystemHealthCheck": {
        "status": "healthy",
        "message": "System resources: CPU 25%, Memory 45%, Disk 60%"
      }
    }
  },
  "alerts": {
    "total_active": 0,
    "by_level": {},
    "by_source": {}
  },
  "metrics": {
    "latest": [...],
    "prometheus": "..."
  },
  "tests": {
    "total": 50,
    "success_rate": 96.0,
    "by_status": {
      "passed": 48,
      "failed": 2
    }
  }
}
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY src/ /app/src/
COPY examples/ /app/examples/

# Set working directory
WORKDIR /app

# Expose ports
EXPOSE 8000

# Run the application
CMD ["python", "-m", "src.main"]
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sergas-monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: sergas-monitoring
  template:
    metadata:
      labels:
        app: sergas-monitoring
    spec:
      containers:
      - name: monitoring
        image: sergas/monitoring:latest
        ports:
        - containerPort: 8000
        env:
        - name: SLACK_WEBHOOK_URL
          valueFrom:
            secretKeyRef:
              name: monitoring-secrets
              key: slack-webhook-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: sergas-monitoring-service
spec:
  selector:
    app: sergas-monitoring
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

## Best Practices

### 1. Test Organization

- **Organize tests by type**: Unit, integration, performance, security
- **Use descriptive test names**: Clearly indicate what is being tested
- **Keep tests independent**: Each test should run independently
- **Use test fixtures**: Setup and teardown common test data
- **Mock external dependencies**: Isolate tests from external systems

### 2. Metrics Collection

- **Collect relevant metrics**: Focus on business-critical metrics
- **Use appropriate data types**: Counters for cumulative values, gauges for current values
- **Add labels and descriptions**: Make metrics self-documenting
- **Set appropriate retention policies**: Balance storage cost with historical value
- **Monitor metrics collection**: Ensure metrics collection doesn't impact performance

### 3. Alert Management

- **Set meaningful thresholds**: Avoid alert fatigue with appropriate thresholds
- **Use escalation policies**: Route critical alerts to appropriate channels
- **Include actionable information**: Provide context and suggested actions
- **Implement cooldown periods**: Prevent alert storms
- **Regularly review alert rules**: Remove or adjust outdated rules

### 4. Health Checks

- **Check all critical dependencies**: Database, external APIs, resources
- **Use appropriate timeouts**: Prevent health checks from hanging
- **Implement graceful degradation**: Handle partial failures appropriately
- **Monitor health check performance**: Ensure health checks are efficient
- **Document health check behavior**: Clearly define what constitutes healthy/unhealthy

## Troubleshooting

### Common Issues

1. **Tests failing intermittently**
   - Check for race conditions or timing dependencies
   - Ensure proper test isolation
   - Verify external dependencies are available
   - Review test data setup and teardown

2. **High memory usage**
   - Check metrics collection frequency
   - Review retention policies
   - Monitor for memory leaks in custom collectors
   - Consider optimizing data structures

3. **Alert fatigue**
   - Review alert thresholds and cooldown periods
   - Consolidate similar alerts
   - Implement alert suppression during maintenance windows
   - Use different alert levels appropriately

4. **Health check failures**
   - Verify network connectivity
   - Check authentication credentials
   - Review timeout settings
   - Validate health check logic

### Performance Tuning

1. **Test execution**
   - Use parallel execution for independent tests
   - Optimize test data setup
   - Mock slow external dependencies
   - Profile test execution time

2. **Metrics collection**
   - Adjust collection intervals
   - Use efficient data structures
   - Implement sampling for high-frequency metrics
   - Cache expensive computations

3. **Alert processing**
   - Optimize alert rule evaluation
   - Use efficient notification channels
   - Implement alert batching
   - Monitor alert processing time

## Integration Examples

### Integration with FastAPI

```python
from fastapi import FastAPI
from monitoring.comprehensive_monitoring import ComprehensiveMonitoringSystem

app = FastAPI()
monitoring_system = ComprehensiveMonitoringSystem()

@app.on_event("startup")
async def startup():
    await monitoring_system.start_monitoring()

@app.on_event("shutdown")
async def shutdown():
    await monitoring_system.stop_monitoring()

@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Record metrics
    monitoring_system.metrics_collector.record_http_request(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
        duration=process_time
    )

    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/health")
async def health():
    health_status = await monitoring_system.health_checker.get_overall_health()
    return health_status.to_dict()

@app.get("/metrics")
async def metrics():
    from fastapi import Response
    return Response(
        content=monitoring_system.metrics_collector.get_prometheus_metrics(),
        media_type="text/plain"
    )
```

### Integration with Existing Test Frameworks

```python
import pytest
from monitoring.comprehensive_monitoring import test, TestType

# Use pytest with monitoring decorators
@test(test_type=TestType.UNIT)
@pytest.mark.asyncio
async def test_user_service():
    """Test user service functionality."""
    # Existing pytest test logic
    assert True

# Performance test with pytest benchmark
@performance_test(max_duration=1.0)
@test(test_type=TestType.PERFORMANCE)
@pytest.mark.asyncio
async def test_api_performance(benchmark):
    """Test API performance."""
    async def api_call():
        return await make_api_call("/api/users")

    result = await benchmark(api_call)
    assert result.status_code == 200
```

## Conclusion

The comprehensive testing and monitoring infrastructure provides a robust foundation for ensuring the reliability, performance, and security of the Sergas Agents system. By implementing these tools and practices, you can:

- **Ensure Code Quality**: Comprehensive test coverage with multiple test types
- **Monitor System Health**: Real-time monitoring of system resources and application metrics
- **Respond to Issues Quickly**: Automated alerting with multiple notification channels
- **Maintain Performance**: Performance monitoring and optimization
- **Track Trends**: Historical data analysis for capacity planning and optimization

This infrastructure is designed to be extensible and customizable, allowing you to add custom tests, metrics, and alerts as your system evolves.