#!/usr/bin/env python3
"""
Comprehensive Monitoring System Demo

This script demonstrates the usage of the comprehensive monitoring infrastructure
for the Sergas Agents system. It shows how to:
- Set up test suites
- Configure metrics collection
- Set up alerting rules
- Run health checks
- Monitor system performance

Usage:
    python examples/monitoring_demo.py
"""

import asyncio
import os
import sys
import time
import random
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from monitoring.comprehensive_monitoring import (
    TestType,
    AlertLevel,
    TestStatus,
    ComprehensiveMonitoringSystem,
    test,
    performance_test,
    integration_test,
    measure_time
)


# Example Tests
@test(test_type=TestType.UNIT)
async def test_basic_functionality():
    """Basic unit test example."""
    # Simulate some test logic
    result = 2 + 2
    assert result == 4, "Basic math should work"
    return True


@test(test_type=TestType.UNIT)
async def test_api_response_format():
    """Test API response format."""
    # Simulate API response validation
    response = {"status": "success", "data": {"id": 123, "name": "Test"}}

    assert "status" in response, "Response should have status"
    assert "data" in response, "Response should have data"
    assert response["status"] == "success", "Status should be success"

    return True


@performance_test(max_duration=2.0, max_memory_mb=50.0)
@test(test_type=TestType.PERFORMANCE)
async def test_performance_load():
    """Performance test example."""
    # Simulate some computational work
    total = 0
    for i in range(100000):
        total += i * i

    # Simulate some I/O work
    await asyncio.sleep(0.1)

    assert total > 0, "Total should be positive"
    return True


@integration_test(dependencies=["http://localhost:8000/health"])
@test(test_type=TestType.INTEGRATION)
async def test_api_connectivity():
    """Integration test for API connectivity."""
    # This would test actual API endpoints
    await asyncio.sleep(0.05)  # Simulate API call

    # Simulate successful API response
    response_status = 200
    assert response_status == 200, "API should respond with 200"

    return True


@test(test_type=TestType.SECURITY)
async def test_security_validation():
    """Security test example."""
    # Simulate security validation
    malicious_input = "'; DROP TABLE users; --"
    sanitized = malicious_input.replace("'", "''")

    assert sanitized != malicious_input, "Input should be sanitized"
    assert "'" not in sanitized or sanitized.count("'") == 2, "SQL injection should be prevented"

    return True


@measure_time()
async def simulate_workload(duration: float = 1.0):
    """Simulate some workload for monitoring."""
    start_time = time.time()

    # Do some work
    result = 0
    while time.time() - start_time < duration:
        result += random.randint(1, 100)
        await asyncio.sleep(0.01)  # Small delay to simulate async work

    return result


async def create_custom_alert_rules(monitoring_system):
    """Create custom alert rules for demonstration."""
    from monitoring.comprehensive_monitoring import AlertRule

    # Custom alert rule for high error rate
    error_rate_rule = AlertRule(
        name="high_error_rate",
        condition=lambda m: m.name == "error_rate" and m.value > 5.0,
        level=AlertLevel.WARNING,
        message_template="High error rate detected: {metric_value} errors/minute",
        cooldown=300.0
    )
    monitoring_system.add_custom_alert_rule(error_rate_rule)

    # Custom alert rule for slow response times
    response_time_rule = AlertRule(
        name="slow_response_time",
        condition=lambda m: m.name == "api_response_time" and m.value > 2.0,
        level=AlertLevel.WARNING,
        message_template="Slow API response time: {metric_value} seconds",
        cooldown=180.0
    )
    monitoring_system.add_custom_alert_rule(response_time_rule)


async def create_custom_metrics(monitoring_system):
    """Create custom metric collectors."""
    def business_metrics_collector():
        """Collect business-specific metrics."""
        from monitoring.comprehensive_monitoring import MonitoringMetric, MonitorType

        # Simulate business metrics
        metrics = [
            MonitoringMetric(
                name="active_users",
                value=random.randint(100, 500),
                timestamp=datetime.now(),
                metric_type=MonitorType.CUSTOM,
                unit="count",
                description="Number of active users"
            ),
            MonitoringMetric(
                name="error_rate",
                value=random.uniform(0, 10),
                timestamp=datetime.now(),
                metric_type=MonitorType.APPLICATION,
                unit="errors_per_minute",
                description="Error rate per minute"
            ),
            MonitoringMetric(
                name="api_response_time",
                value=random.uniform(0.1, 3.0),
                timestamp=datetime.now(),
                metric_type=MonitorType.APPLICATION,
                unit="seconds",
                description="Average API response time"
            )
        ]

        return metrics

    monitoring_system.add_custom_metric_collector(business_metrics_collector)


async def main():
    """Main demonstration function."""
    print("🚀 Sergas Agents - Comprehensive Monitoring System Demo")
    print("=" * 60)

    # Initialize monitoring system with demo configuration
    config = {
        "max_test_workers": 4,
        # Add notification channels if environment variables are set
        "slack_webhook_url": os.getenv("SLACK_WEBHOOK_URL"),
        "alert_webhook_url": os.getenv("ALERT_WEBHOOK_URL"),
    }

    monitoring_system = ComprehensiveMonitoringSystem(config)

    # Add custom tests to suites
    monitoring_system.add_custom_test(test_basic_functionality, TestType.UNIT)
    monitoring_system.add_custom_test(test_api_response_format, TestType.UNIT)
    monitoring_system.add_custom_test(test_performance_load, TestType.PERFORMANCE)
    monitoring_system.add_custom_test(test_api_connectivity, TestType.INTEGRATION)
    monitoring_system.add_custom_test(test_security_validation, TestType.SECURITY)

    # Create custom alert rules
    await create_custom_alert_rules(monitoring_system)

    # Create custom metrics
    await create_custom_metrics(monitoring_system)

    print("\n📊 Running comprehensive test suite...")

    # Run comprehensive tests
    test_results = await monitoring_system.run_comprehensive_tests()

    print(f"\n✅ Test Results Summary:")
    print(f"   Total Tests: {test_results['summary']['total']}")
    print(f"   Passed: {test_results['summary']['by_status'].get('passed', 0)}")
    print(f"   Failed: {test_results['summary']['by_status'].get('failed', 0)}")
    print(f"   Success Rate: {test_results['summary']['success_rate']:.1f}%")
    print(f"   Total Duration: {test_results['summary']['total_duration']:.2f}s")

    print("\n🏥 Checking system health...")

    # Get health status
    system_status = await monitoring_system.get_system_status()

    print(f"   Overall Health: {system_status['health']['overall']['status']}")
    print(f"   Active Alerts: {system_status['alerts']['total_active']}")
    print(f"   Components Checked: {system_status['health']['overall']['details']['total_checks']}")

    print("\n📈 Starting continuous monitoring...")

    # Start monitoring
    await monitoring_system.start_monitoring(interval=30.0)

    try:
        # Simulate some workload
        print("\n💼 Simulating application workload...")

        for i in range(5):
            print(f"   Workload iteration {i+1}/5")
            result = await simulate_workload(0.5)
            print(f"     Computation result: {result}")

            # Collect some metrics
            metrics = monitoring_system.metrics_collector.collect_metrics()
            print(f"     Metrics collected: {len(metrics)}")

            # Check for alerts
            active_alerts = monitoring_system.alert_manager.get_active_alerts()
            if active_alerts:
                print(f"     ⚠️  Active alerts: {len(active_alerts)}")
                for alert in active_alerts[:3]:  # Show first 3 alerts
                    print(f"        - {alert.title}: {alert.message}")

            await asyncio.sleep(2)

        print("\n📊 Final System Status:")
        final_status = await monitoring_system.get_system_status()

        print(f"   Monitoring Active: {final_status['monitoring']['is_running']}")
        print(f"   Total Metrics: {final_status['monitoring']['total_metrics']}")
        print(f"   Latest Health: {final_status['health']['overall']['status']}")

        # Show some example metrics
        latest_metrics = final_status['metrics']['latest']
        if latest_metrics:
            print(f"   Sample Metrics:")
            for metric in latest_metrics[:3]:
                print(f"     - {metric['name']}: {metric['value']:.2f} {metric.get('unit', '')}")

    finally:
        print("\n🛑 Stopping monitoring...")
        await monitoring_system.stop_monitoring()

    print("\n🎉 Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    # Run the demonstration
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()