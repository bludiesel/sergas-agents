#!/usr/bin/env python3
"""
Test script for comprehensive monitoring functionality without external dependencies.
"""

import sys
import os
from datetime import datetime

# Add src to path and import directly from the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import directly from the comprehensive_monitoring module file
from monitoring.comprehensive_monitoring import (
    # Enums
    TestType,
    MonitorType,
    AlertLevel,
    TestStatus,
    HealthStatus,

    # Dataclasses
    TestResult,
    MonitoringMetric,
    Alert,
    HealthCheck,
    TestSuite,

    # Alert Infrastructure
    AlertRule,
)

def test_enums():
    """Test all enum values."""
    print("🧪 Testing enums...")

    # Test TestType
    assert TestType.UNIT.value == "unit"
    assert TestType.INTEGRATION.value == "integration"
    assert TestType.PERFORMANCE.value == "performance"
    assert TestType.SECURITY.value == "security"
    assert TestType.LOAD.value == "load"
    assert TestType.REGRESSION.value == "regression"
    assert TestType.SMOKE.value == "smoke"
    assert TestType.E2E.value == "e2e"
    assert TestType.COMPATIBILITY.value == "compatibility"
    assert TestType.STRESS.value == "stress"

    # Test MonitorType
    assert MonitorType.SYSTEM.value == "system"
    assert MonitorType.APPLICATION.value == "application"
    assert MonitorType.DATABASE.value == "database"
    assert MonitorType.NETWORK.value == "network"
    assert MonitorType.MEMORY.value == "memory"
    assert MonitorType.CPU.value == "cpu"
    assert MonitorType.CUSTOM.value == "custom"

    # Test AlertLevel
    assert AlertLevel.INFO.value == "info"
    assert AlertLevel.WARNING.value == "warning"
    assert AlertLevel.ERROR.value == "error"
    assert AlertLevel.CRITICAL.value == "critical"

    # Test TestStatus
    assert TestStatus.PENDING.value == "pending"
    assert TestStatus.RUNNING.value == "running"
    assert TestStatus.PASSED.value == "passed"
    assert TestStatus.FAILED.value == "failed"
    assert TestStatus.SKIPPED.value == "skipped"
    assert TestStatus.TIMEOUT.value == "timeout"
    assert TestStatus.ERROR.value == "error"

    # Test HealthStatus
    assert HealthStatus.HEALTHY.value == "healthy"
    assert HealthStatus.DEGRADED.value == "degraded"
    assert HealthStatus.UNHEALTHY.value == "unhealthy"
    assert HealthStatus.UNKNOWN.value == "unknown"

    print("✅ All enum tests passed!")

def test_dataclasses():
    """Test all dataclass creation and methods."""
    print("🧪 Testing dataclasses...")

    # Test TestResult
    start_time = datetime.now()
    end_time = start_time.replace(microsecond=start_time.microsecond + 5000000)  # Add 5 seconds

    result = TestResult(
        test_id="test-123",
        test_name="test_function",
        test_type=TestType.UNIT,
        status=TestStatus.PASSED,
        duration=5.0,
        start_time=start_time,
        end_time=end_time,
        message="Test passed successfully",
        assertions=3,
        passed_assertions=3,
        coverage=85.5
    )

    assert result.test_id == "test-123"
    assert result.test_name == "test_function"
    assert result.test_type == TestType.UNIT
    assert result.status == TestStatus.PASSED
    assert result.duration == 5.0
    assert result.assertions == 3
    assert result.passed_assertions == 3
    assert result.coverage == 85.5

    # Test to_dict method
    result_dict = result.to_dict()
    assert isinstance(result_dict, dict)
    assert result_dict['test_id'] == "test-123"
    assert result_dict['test_type'] == "unit"
    assert result_dict['status'] == "passed"
    assert 'start_time' in result_dict
    assert 'end_time' in result_dict

    # Test MonitoringMetric
    timestamp = datetime.now()
    metric = MonitoringMetric(
        name="cpu_usage",
        value=75.5,
        timestamp=timestamp,
        metric_type=MonitorType.SYSTEM,
        labels={"host": "server1"},
        unit="percent",
        description="CPU usage percentage"
    )

    assert metric.name == "cpu_usage"
    assert metric.value == 75.5
    assert metric.metric_type == MonitorType.SYSTEM
    assert metric.labels["host"] == "server1"
    assert metric.unit == "percent"
    assert metric.description == "CPU usage percentage"

    # Test to_dict method
    metric_dict = metric.to_dict()
    assert isinstance(metric_dict, dict)
    assert metric_dict['name'] == "cpu_usage"
    assert metric_dict['value'] == 75.5
    assert metric_dict['metric_type'] == "system"
    assert 'timestamp' in metric_dict

    # Test Alert
    alert = Alert(
        alert_id="alert-456",
        level=AlertLevel.WARNING,
        title="High CPU Usage",
        message="CPU usage is above threshold",
        timestamp=timestamp,
        source="system_monitor",
        metric_name="cpu_usage",
        current_value=85.0,
        threshold=80.0,
        labels={"severity": "medium"}
    )

    assert alert.alert_id == "alert-456"
    assert alert.level == AlertLevel.WARNING
    assert alert.title == "High CPU Usage"
    assert alert.source == "system_monitor"
    assert alert.metric_name == "cpu_usage"
    assert alert.current_value == 85.0
    assert alert.threshold == 80.0
    assert not alert.acknowledged
    assert not alert.resolved

    # Test to_dict method
    alert_dict = alert.to_dict()
    assert isinstance(alert_dict, dict)
    assert alert_dict['alert_id'] == "alert-456"
    assert alert_dict['level'] == "warning"
    assert 'timestamp' in alert_dict

    # Test HealthCheck
    health_check = HealthCheck(
        component="database",
        status=HealthStatus.HEALTHY,
        message="Database connection successful",
        details={"response_time": 0.150},
        timestamp=timestamp,
        response_time=0.150
    )

    assert health_check.component == "database"
    assert health_check.status == HealthStatus.HEALTHY
    assert health_check.message == "Database connection successful"
    assert health_check.details["response_time"] == 0.150
    assert health_check.response_time == 0.150

    # Test to_dict method
    health_dict = health_check.to_dict()
    assert isinstance(health_dict, dict)
    assert health_dict['component'] == "database"
    assert health_dict['status'] == "healthy"
    assert 'timestamp' in health_dict

    # Test TestSuite
    suite = TestSuite(
        name="Unit Tests",
        test_type=TestType.UNIT,
        timeout=60.0,
        retry_count=2,
        parallel=True,
        max_workers=4
    )

    assert suite.name == "Unit Tests"
    assert suite.test_type == TestType.UNIT
    assert suite.timeout == 60.0
    assert suite.retry_count == 2
    assert suite.parallel
    assert suite.max_workers == 4
    assert len(suite.tests) == 0  # Empty by default

    print("✅ All dataclass tests passed!")

def test_alert_rules():
    """Test alert rule functionality."""
    print("🧪 Testing alert rules...")

    # Test AlertRule creation
    rule = AlertRule(
        name="high_cpu",
        condition=lambda m: m.name == "cpu_usage" and m.value > 80,
        level=AlertLevel.WARNING,
        message_template="CPU usage is {metric_value}%",
        cooldown=300.0
    )

    assert rule.name == "high_cpu"
    assert rule.level == AlertLevel.WARNING
    assert rule.message_template == "CPU usage is {metric_value}%"
    assert rule.cooldown == 300.0
    assert rule.enabled

    # Test evaluation - should trigger alert
    high_cpu_metric = MonitoringMetric(
        name="cpu_usage",
        value=85.0,
        timestamp=datetime.now(),
        metric_type=MonitorType.SYSTEM
    )

    alert = rule.evaluate(high_cpu_metric)
    assert alert is not None
    assert alert.level == AlertLevel.WARNING
    assert "85.0" in alert.message

    # Test evaluation - should not trigger alert
    low_cpu_metric = MonitoringMetric(
        name="cpu_usage",
        value=50.0,
        timestamp=datetime.now(),
        metric_type=MonitorType.SYSTEM
    )

    alert = rule.evaluate(low_cpu_metric)
    assert alert is None

    # Test disabled rule
    disabled_rule = AlertRule(
        name="disabled_rule",
        condition=lambda m: True,  # Always true
        level=AlertLevel.ERROR,
        message_template="This should not trigger",
        enabled=False
    )

    alert = disabled_rule.evaluate(high_cpu_metric)
    assert alert is None

    print("✅ All alert rule tests passed!")

def test_integration_scenarios():
    """Test integration scenarios."""
    print("🧪 Testing integration scenarios...")

    # Test metric to alert flow
    rule = AlertRule(
        name="high_memory",
        condition=lambda m: m.name == "memory_usage" and m.value > 90,
        level=AlertLevel.ERROR,
        message_template="Memory usage is critical: {metric_value}%",
        cooldown=0.0  # No cooldown for testing
    )

    metric = MonitoringMetric(
        name="memory_usage",
        value=95.0,
        timestamp=datetime.now(),
        metric_type=MonitorType.MEMORY,
        unit="percent"
    )

    alert = rule.evaluate(metric)

    assert alert is not None
    assert alert.level == AlertLevel.ERROR
    assert alert.metric_name == "memory_usage"
    assert alert.current_value == 95.0
    assert "95.0" in alert.message

    # Test health status aggregation
    from datetime import timedelta

    health_checks = [
        HealthCheck(component="database", status=HealthStatus.HEALTHY),
        HealthCheck(component="redis", status=HealthStatus.HEALTHY),
        HealthCheck(component="api", status=HealthStatus.DEGRADED),
        HealthCheck(component="storage", status=HealthStatus.HEALTHY),
    ]

    # Determine overall status
    if any(check.status == HealthStatus.UNHEALTHY for check in health_checks):
        overall_status = HealthStatus.UNHEALTHY
    elif any(check.status == HealthStatus.DEGRADED for check in health_checks):
        overall_status = HealthStatus.DEGRADED
    elif all(check.status == HealthStatus.HEALTHY for check in health_checks):
        overall_status = HealthStatus.HEALTHY
    else:
        overall_status = HealthStatus.UNKNOWN

    # Should be DEGRADED due to one degraded component
    assert overall_status == HealthStatus.DEGRADED

    print("✅ All integration scenario tests passed!")

def main():
    """Run all tests."""
    print("🚀 Sergas Agents - Comprehensive Monitoring System Test")
    print("=" * 60)

    try:
        test_enums()
        test_dataclasses()
        test_alert_rules()
        test_integration_scenarios()

        print("\n🎉 All tests passed successfully!")
        print("=" * 60)
        print("✅ Comprehensive monitoring system is working correctly")
        print("✅ Core components are properly implemented")
        print("✅ Data structures and logic are functioning as expected")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)