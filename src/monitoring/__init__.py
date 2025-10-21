"""
Sergas Super Account Manager - Monitoring Module

Comprehensive testing and monitoring infrastructure including:
- TestType, MonitorType, AlertLevel enums
- TestResult, MonitoringMetric, Alert, HealthCheck dataclasses
- TestRunner class with multiple test suites
- MetricsCollector class with Prometheus integration
- AlertManager class for alerting rules and notifications
- Support for automated testing, performance monitoring, and health checks
"""

from .metrics import (
    metrics_collector,
    setup_metrics,
    track_time,
    track_inprogress,
    count_errors,
    MetricsCollector,
)
from .comprehensive_monitoring import (
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

    # Main Classes
    TestRunner,
    MetricsCollector as ComprehensiveMetricsCollector,
    AlertManager,
    HealthChecker,
    ComprehensiveMonitoringSystem,

    # Alert Infrastructure
    AlertRule,
    NotificationChannel,
    EmailNotificationChannel,
    SlackNotificationChannel,
    WebhookNotificationChannel,

    # Health Check Infrastructure
    HealthCheckProvider,
    DatabaseHealthCheck,
    HTTPHealthCheck,
    SystemHealthCheck,

    # Utilities
    BaseTest,
    monitoring_context,
    test,
    performance_test,
    integration_test,
    measure_time,
)

__all__ = [
    # Legacy metrics
    'metrics_collector',
    'setup_metrics',
    'track_time',
    'track_inprogress',
    'count_errors',
    'MetricsCollector',

    # Enums
    'TestType',
    'MonitorType',
    'AlertLevel',
    'TestStatus',
    'HealthStatus',

    # Dataclasses
    'TestResult',
    'MonitoringMetric',
    'Alert',
    'HealthCheck',
    'TestSuite',

    # Main Classes
    'TestRunner',
    'ComprehensiveMetricsCollector',
    'AlertManager',
    'HealthChecker',
    'ComprehensiveMonitoringSystem',

    # Alert Infrastructure
    'AlertRule',
    'NotificationChannel',
    'EmailNotificationChannel',
    'SlackNotificationChannel',
    'WebhookNotificationChannel',

    # Health Check Infrastructure
    'HealthCheckProvider',
    'DatabaseHealthCheck',
    'HTTPHealthCheck',
    'SystemHealthCheck',

    # Utilities
    'BaseTest',
    'monitoring_context',
    'test',
    'performance_test',
    'integration_test',
    'measure_time',
]
