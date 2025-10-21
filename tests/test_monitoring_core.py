"""
Core unit tests for the comprehensive monitoring system.

These tests verify the core functionality without requiring external dependencies.
"""

import asyncio
import unittest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import only the comprehensive monitoring module directly to avoid circular imports
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

class TestEnums(unittest.TestCase):
    """Test enum definitions and values."""

    def test_test_type_enum(self):
        """Test TestType enum values."""
        self.assertEqual(TestType.UNIT.value, "unit")
        self.assertEqual(TestType.INTEGRATION.value, "integration")
        self.assertEqual(TestType.PERFORMANCE.value, "performance")
        self.assertEqual(TestType.SECURITY.value, "security")
        self.assertEqual(TestType.LOAD.value, "load")
        self.assertEqual(TestType.REGRESSION.value, "regression")
        self.assertEqual(TestType.SMOKE.value, "smoke")
        self.assertEqual(TestType.E2E.value, "e2e")
        self.assertEqual(TestType.COMPATIBILITY.value, "compatibility")
        self.assertEqual(TestType.STRESS.value, "stress")

    def test_monitor_type_enum(self):
        """Test MonitorType enum values."""
        self.assertEqual(MonitorType.SYSTEM.value, "system")
        self.assertEqual(MonitorType.APPLICATION.value, "application")
        self.assertEqual(MonitorType.DATABASE.value, "database")
        self.assertEqual(MonitorType.NETWORK.value, "network")
        self.assertEqual(MonitorType.MEMORY.value, "memory")
        self.assertEqual(MonitorType.CPU.value, "cpu")
        self.assertEqual(MonitorType.CUSTOM.value, "custom")

    def test_alert_level_enum(self):
        """Test AlertLevel enum values."""
        self.assertEqual(AlertLevel.INFO.value, "info")
        self.assertEqual(AlertLevel.WARNING.value, "warning")
        self.assertEqual(AlertLevel.ERROR.value, "error")
        self.assertEqual(AlertLevel.CRITICAL.value, "critical")

    def test_test_status_enum(self):
        """Test TestStatus enum values."""
        self.assertEqual(TestStatus.PENDING.value, "pending")
        self.assertEqual(TestStatus.RUNNING.value, "running")
        self.assertEqual(TestStatus.PASSED.value, "passed")
        self.assertEqual(TestStatus.FAILED.value, "failed")
        self.assertEqual(TestStatus.SKIPPED.value, "skipped")
        self.assertEqual(TestStatus.TIMEOUT.value, "timeout")
        self.assertEqual(TestStatus.ERROR.value, "error")

    def test_health_status_enum(self):
        """Test HealthStatus enum values."""
        self.assertEqual(HealthStatus.HEALTHY.value, "healthy")
        self.assertEqual(HealthStatus.DEGRADED.value, "degraded")
        self.assertEqual(HealthStatus.UNHEALTHY.value, "unhealthy")
        self.assertEqual(HealthStatus.UNKNOWN.value, "unknown")


class TestDataClasses(unittest.TestCase):
    """Test dataclass functionality."""

    def test_test_result_creation(self):
        """Test TestResult creation and methods."""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=5)

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

        self.assertEqual(result.test_id, "test-123")
        self.assertEqual(result.test_name, "test_function")
        self.assertEqual(result.test_type, TestType.UNIT)
        self.assertEqual(result.status, TestStatus.PASSED)
        self.assertEqual(result.duration, 5.0)
        self.assertEqual(result.assertions, 3)
        self.assertEqual(result.passed_assertions, 3)
        self.assertEqual(result.coverage, 85.5)

        # Test to_dict method
        result_dict = result.to_dict()
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict['test_id'], "test-123")
        self.assertEqual(result_dict['test_type'], "unit")
        self.assertEqual(result_dict['status'], "passed")
        self.assertIn('start_time', result_dict)
        self.assertIn('end_time', result_dict)

    def test_monitoring_metric_creation(self):
        """Test MonitoringMetric creation and methods."""
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

        self.assertEqual(metric.name, "cpu_usage")
        self.assertEqual(metric.value, 75.5)
        self.assertEqual(metric.metric_type, MonitorType.SYSTEM)
        self.assertEqual(metric.labels["host"], "server1")
        self.assertEqual(metric.unit, "percent")
        self.assertEqual(metric.description, "CPU usage percentage")

        # Test to_dict method
        metric_dict = metric.to_dict()
        self.assertIsInstance(metric_dict, dict)
        self.assertEqual(metric_dict['name'], "cpu_usage")
        self.assertEqual(metric_dict['value'], 75.5)
        self.assertEqual(metric_dict['metric_type'], "system")
        self.assertIn('timestamp', metric_dict)

    def test_alert_creation(self):
        """Test Alert creation and methods."""
        timestamp = datetime.now()

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

        self.assertEqual(alert.alert_id, "alert-456")
        self.assertEqual(alert.level, AlertLevel.WARNING)
        self.assertEqual(alert.title, "High CPU Usage")
        self.assertEqual(alert.source, "system_monitor")
        self.assertEqual(alert.metric_name, "cpu_usage")
        self.assertEqual(alert.current_value, 85.0)
        self.assertEqual(alert.threshold, 80.0)
        self.assertFalse(alert.acknowledged)
        self.assertFalse(alert.resolved)

        # Test to_dict method
        alert_dict = alert.to_dict()
        self.assertIsInstance(alert_dict, dict)
        self.assertEqual(alert_dict['alert_id'], "alert-456")
        self.assertEqual(alert_dict['level'], "warning")
        self.assertIn('timestamp', alert_dict)

    def test_health_check_creation(self):
        """Test HealthCheck creation and methods."""
        timestamp = datetime.now()

        health_check = HealthCheck(
            component="database",
            status=HealthStatus.HEALTHY,
            message="Database connection successful",
            details={"response_time": 0.150},
            timestamp=timestamp,
            response_time=0.150
        )

        self.assertEqual(health_check.component, "database")
        self.assertEqual(health_check.status, HealthStatus.HEALTHY)
        self.assertEqual(health_check.message, "Database connection successful")
        self.assertEqual(health_check.details["response_time"], 0.150)
        self.assertEqual(health_check.response_time, 0.150)

        # Test to_dict method
        health_dict = health_check.to_dict()
        self.assertIsInstance(health_dict, dict)
        self.assertEqual(health_dict['component'], "database")
        self.assertEqual(health_dict['status'], "healthy")
        self.assertIn('timestamp', health_dict)

    def test_test_suite_creation(self):
        """Test TestSuite creation."""
        suite = TestSuite(
            name="Unit Tests",
            test_type=TestType.UNIT,
            timeout=60.0,
            retry_count=2,
            parallel=True,
            max_workers=4
        )

        self.assertEqual(suite.name, "Unit Tests")
        self.assertEqual(suite.test_type, TestType.UNIT)
        self.assertEqual(suite.timeout, 60.0)
        self.assertEqual(suite.retry_count, 2)
        self.assertTrue(suite.parallel)
        self.assertEqual(suite.max_workers, 4)
        self.assertEqual(len(suite.tests), 0)  # Empty by default


class TestAlertRule(unittest.TestCase):
    """Test AlertRule functionality."""

    def test_alert_rule_creation(self):
        """Test AlertRule creation."""
        rule = AlertRule(
            name="high_cpu",
            condition=lambda m: m.name == "cpu_usage" and m.value > 80,
            level=AlertLevel.WARNING,
            message_template="CPU usage is {metric_value}%",
            cooldown=300.0
        )

        self.assertEqual(rule.name, "high_cpu")
        self.assertEqual(rule.level, AlertLevel.WARNING)
        self.assertEqual(rule.message_template, "CPU usage is {metric_value}%")
        self.assertEqual(rule.cooldown, 300.0)
        self.assertTrue(rule.enabled)

    def test_alert_rule_evaluation(self):
        """Test AlertRule evaluation."""
        rule = AlertRule(
            name="high_cpu",
            condition=lambda m: m.name == "cpu_usage" and m.value > 80,
            level=AlertLevel.WARNING,
            message_template="CPU usage is {metric_value}%",
            cooldown=300.0
        )

        # Test metric that should trigger alert
        high_cpu_metric = MonitoringMetric(
            name="cpu_usage",
            value=85.0,
            timestamp=datetime.now(),
            metric_type=MonitorType.SYSTEM
        )

        alert = rule.evaluate(high_cpu_metric)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.level, AlertLevel.WARNING)
        self.assertIn("85.0", alert.message)

        # Test metric that should not trigger alert
        low_cpu_metric = MonitoringMetric(
            name="cpu_usage",
            value=50.0,
            timestamp=datetime.now(),
            metric_type=MonitorType.SYSTEM
        )

        alert = rule.evaluate(low_cpu_metric)
        self.assertIsNone(alert)

    def test_alert_rule_cooldown(self):
        """Test AlertRule cooldown functionality."""
        rule = AlertRule(
            name="high_cpu",
            condition=lambda m: m.name == "cpu_usage" and m.value > 80,
            level=AlertLevel.WARNING,
            message_template="CPU usage is {metric_value}%",
            cooldown=0.1  # Short cooldown for testing
        )

        high_cpu_metric = MonitoringMetric(
            name="cpu_usage",
            value=85.0,
            timestamp=datetime.now(),
            metric_type=MonitorType.SYSTEM
        )

        # First evaluation should trigger alert
        alert1 = rule.evaluate(high_cpu_metric)
        self.assertIsNotNone(alert1)

        # Immediate second evaluation should not trigger alert (cooldown)
        alert2 = rule.evaluate(high_cpu_metric)
        self.assertIsNone(alert2)

        # Wait for cooldown to pass
        import time
        time.sleep(0.2)

        # Third evaluation should trigger alert again
        alert3 = rule.evaluate(high_cpu_metric)
        self.assertIsNotNone(alert3)

    def test_disabled_alert_rule(self):
        """Test disabled alert rule."""
        rule = AlertRule(
            name="high_cpu",
            condition=lambda m: m.name == "cpu_usage" and m.value > 80,
            level=AlertLevel.WARNING,
            message_template="CPU usage is {metric_value}%",
            enabled=False
        )

        high_cpu_metric = MonitoringMetric(
            name="cpu_usage",
            value=85.0,
            timestamp=datetime.now(),
            metric_type=MonitorType.SYSTEM
        )

        alert = rule.evaluate(high_cpu_metric)
        self.assertIsNone(alert)


class TestMonitoringIntegration(unittest.TestCase):
    """Integration tests for monitoring components."""

    def test_metric_to_alert_flow(self):
        """Test flow from metric to alert generation."""
        # Create alert rule
        rule = AlertRule(
            name="high_memory",
            condition=lambda m: m.name == "memory_usage" and m.value > 90,
            level=AlertLevel.ERROR,
            message_template="Memory usage is critical: {metric_value}%",
            cooldown=0.0  # No cooldown for testing
        )

        # Create high memory metric
        metric = MonitoringMetric(
            name="memory_usage",
            value=95.0,
            timestamp=datetime.now(),
            metric_type=MonitorType.MEMORY,
            unit="percent"
        )

        # Evaluate metric against rule
        alert = rule.evaluate(metric)

        # Verify alert generated
        self.assertIsNotNone(alert)
        self.assertEqual(alert.level, AlertLevel.ERROR)
        self.assertEqual(alert.metric_name, "memory_usage")
        self.assertEqual(alert.current_value, 95.0)
        self.assertIn("95.0", alert.message)

    def test_test_result_serialization(self):
        """Test TestResult serialization and deserialization."""
        original_result = TestResult(
            test_id="test-789",
            test_name="example_test",
            test_type=TestType.INTEGRATION,
            status=TestStatus.FAILED,
            duration=2.5,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=2.5),
            error="AssertionError: Expected value to be True",
            metadata={"browser": "chrome", "version": "120.0"}
        )

        # Serialize to dict
        result_dict = original_result.to_dict()

        # Verify serialization
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict['test_id'], "test-789")
        self.assertEqual(result_dict['test_type'], "integration")
        self.assertEqual(result_dict['status'], "failed")
        self.assertIn('error', result_dict)
        self.assertIn('metadata', result_dict)

        # Test that all required fields are present
        required_fields = [
            'test_id', 'test_name', 'test_type', 'status', 'duration',
            'start_time', 'end_time', 'message', 'error', 'metadata',
            'assertions', 'passed_assertions', 'coverage'
        ]
        for field in required_fields:
            self.assertIn(field, result_dict)

    def test_health_status_aggregation(self):
        """Test health status aggregation logic."""
        # Create multiple health checks
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
        self.assertEqual(overall_status, HealthStatus.DEGRADED)

        # Add unhealthy check
        health_checks.append(
            HealthCheck(component="external_api", status=HealthStatus.UNHEALTHY)
        )

        # Re-evaluate
        if any(check.status == HealthStatus.UNHEALTHY for check in health_checks):
            overall_status = HealthStatus.UNHEALTHY
        elif any(check.status == HealthStatus.DEGRADED for check in health_checks):
            overall_status = HealthStatus.DEGRADED
        elif all(check.status == HealthStatus.HEALTHY for check in health_checks):
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.UNKNOWN

        # Should be UNHEALTHY due to one unhealthy component
        self.assertEqual(overall_status, HealthStatus.UNHEALTHY)


class TestAsyncComponents(unittest.TestCase):
    """Test async functionality."""

    def test_async_test_function_simulation(self):
        """Test simulation of async test functions."""
        async def mock_async_test():
            """Mock async test function."""
            await asyncio.sleep(0.01)  # Simulate async work
            return True

        # Run the async test
        result = asyncio.run(mock_async_test())
        self.assertTrue(result)

    def test_async_metric_collection_simulation(self):
        """Test simulation of async metric collection."""
        async def mock_metric_collector():
            """Mock async metric collector."""
            await asyncio.sleep(0.01)  # Simulate collection time
            return [
                MonitoringMetric(
                    name="test_metric",
                    value=42.0,
                    timestamp=datetime.now(),
                    metric_type=MonitorType.CUSTOM
                )
            ]

        # Run the async collector
        metrics = asyncio.run(mock_metric_collector())
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0].name, "test_metric")
        self.assertEqual(metrics[0].value, 42.0)

    def test_parallel_execution_simulation(self):
        """Test simulation of parallel execution."""
        async def mock_task(task_id: int, duration: float):
            """Mock async task."""
            await asyncio.sleep(duration)
            return f"Task {task_id} completed"

        async def run_parallel_tasks():
            """Run multiple tasks in parallel."""
            tasks = [
                mock_task(1, 0.01),
                mock_task(2, 0.01),
                mock_task(3, 0.01)
            ]
            return await asyncio.gather(*tasks)

        # Run parallel tasks
        results = asyncio.run(run_parallel_tasks())
        self.assertEqual(len(results), 3)
        self.assertIn("Task 1 completed", results)
        self.assertIn("Task 2 completed", results)
        self.assertIn("Task 3 completed", results)


if __name__ == '__main__':
    unittest.main()