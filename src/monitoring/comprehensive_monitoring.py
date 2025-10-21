"""
Comprehensive Testing and Monitoring Infrastructure for Sergas Agents System.

This module provides a complete testing and monitoring hub with:
- Multiple test suites (unit, integration, performance, security, load, regression)
- Prometheus metrics integration
- Alerting system with multiple notification channels
- Health checks and automated testing capabilities
- Real-time monitoring and reporting

Author: Sergas Development Team
Version: 1.0.0
"""

import asyncio
import gc
import json
import os
import psutil
import random
import time
import traceback
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    Set,
    Generator
)
import uuid

import httpx
import structlog
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    CollectorRegistry,
    generate_latest,
    push_to_gateway,
    CONTENT_TYPE_LATEST
)
from pydantic import BaseModel, ValidationError

# Configure structured logging
logger = structlog.get_logger(__name__)

# ========================================
# Enums and Data Classes
# ========================================

class TestType(Enum):
    """Types of tests available in the system."""
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

class MonitorType(Enum):
    """Types of monitoring metrics."""
    SYSTEM = "system"
    APPLICATION = "application"
    DATABASE = "database"
    NETWORK = "network"
    MEMORY = "memory"
    CPU = "cpu"
    CUSTOM = "custom"

class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class TestStatus(Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    ERROR = "error"

class HealthStatus(Enum):
    """System health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class TestResult:
    """Represents the result of a test execution."""
    test_id: str
    test_name: str
    test_type: TestType
    status: TestStatus
    duration: float
    start_time: datetime
    end_time: datetime
    message: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    assertions: int = 0
    passed_assertions: int = 0
    coverage: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            **asdict(self),
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'test_type': self.test_type.value,
            'status': self.status.value
        }

@dataclass
class MonitoringMetric:
    """Represents a monitoring metric."""
    name: str
    value: float
    timestamp: datetime
    metric_type: MonitorType
    labels: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'metric_type': self.metric_type.value
        }

@dataclass
class Alert:
    """Represents an alert."""
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    source: str
    metric_name: Optional[str] = None
    threshold: Optional[float] = None
    current_value: Optional[float] = None
    labels: Dict[str, str] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }

@dataclass
class HealthCheck:
    """Represents a health check result."""
    component: str
    status: HealthStatus
    message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    response_time: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value
        }

@dataclass
class TestSuite:
    """Represents a collection of tests."""
    name: str
    test_type: TestType
    tests: List[Callable] = field(default_factory=list)
    setup: Optional[Callable] = None
    teardown: Optional[Callable] = None
    timeout: float = 300.0  # 5 minutes default
    retry_count: int = 0
    parallel: bool = False
    max_workers: int = 4

# ========================================
# Test Runner Infrastructure
# ========================================

class BaseTest(ABC):
    """Base class for all test implementations."""

    def __init__(self, name: str, test_type: TestType):
        self.name = name
        self.test_type = test_type
        self.test_id = str(uuid.uuid4())
        self.logger = structlog.get_logger(f"test.{name}")

    @abstractmethod
    async def run(self) -> TestResult:
        """Execute the test and return results."""
        pass

    async def setup(self):
        """Setup method called before test execution."""
        pass

    async def teardown(self):
        """Teardown method called after test execution."""
        pass

class TestRunner:
    """
    Comprehensive test runner supporting multiple test suites.

    Features:
    - Parallel test execution
    - Test result aggregation
    - Coverage reporting
    - Performance benchmarking
    - Retry logic
    - Timeout handling
    """

    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self.results: List[TestResult] = []
        self.suites: Dict[TestType, TestSuite] = {}
        self.logger = structlog.get_logger("test_runner")
        self.registry = CollectorRegistry()

        # Prometheus metrics for test execution
        self.test_counter = Counter(
            'test_executions_total',
            'Total number of test executions',
            ['test_type', 'status'],
            registry=self.registry
        )

        self.test_duration = Histogram(
            'test_duration_seconds',
            'Test execution duration',
            ['test_type', 'test_name'],
            registry=self.registry
        )

        self.assertion_counter = Counter(
            'test_assertions_total',
            'Total number of test assertions',
            ['test_type', 'result'],
            registry=self.registry
        )

    def register_suite(self, suite: TestSuite):
        """Register a test suite."""
        self.suites[suite.test_type] = suite
        self.logger.info("test_suite_registered", suite=suite.name, type=suite.test_type.value)

    async def run_suite(self, test_type: TestType) -> List[TestResult]:
        """Run all tests in a specific suite."""
        if test_type not in self.suites:
            raise ValueError(f"Test suite {test_type.value} not registered")

        suite = self.suites[test_type]
        self.logger.info("running_test_suite", suite=suite.name, tests=len(suite.tests))

        # Run setup if provided
        if suite.setup:
            try:
                await suite.setup()
                self.logger.info("test_suite_setup_completed", suite=suite.name)
            except Exception as e:
                self.logger.error("test_suite_setup_failed", suite=suite.name, error=str(e))
                raise

        suite_results = []

        # Execute tests
        if suite.parallel and len(suite.tests) > 1:
            suite_results = await self._run_tests_parallel(suite)
        else:
            suite_results = await self._run_tests_sequential(suite)

        # Run teardown if provided
        if suite.teardown:
            try:
                await suite.teardown()
                self.logger.info("test_suite_teardown_completed", suite=suite.name)
            except Exception as e:
                self.logger.error("test_suite_teardown_failed", suite=suite.name, error=str(e))

        self.results.extend(suite_results)
        return suite_results

    async def _run_tests_sequential(self, suite: TestSuite) -> List[TestResult]:
        """Run tests sequentially."""
        results = []

        for test_func in suite.tests:
            result = await self._run_single_test(test_func, suite)
            results.append(result)

            # Stop on first failure if configured
            if result.status == TestStatus.FAILED and suite.retry_count == 0:
                self.logger.warning("test_failed_stopping_suite", test=result.test_name)
                break

        return results

    async def _run_tests_parallel(self, suite: TestSuite) -> List[TestResult]:
        """Run tests in parallel."""
        results = []

        with ThreadPoolExecutor(max_workers=suite.max_workers) as executor:
            # Submit all tests
            future_to_test = {
                executor.submit(self._run_single_test_sync, test_func, suite): test_func
                for test_func in suite.tests
            }

            # Collect results
            for future in as_completed(future_to_test):
                test_func = future_to_test[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error("test_execution_error", test=test_func.__name__, error=str(e))
                    # Create error result
                    result = TestResult(
                        test_id=str(uuid.uuid4()),
                        test_name=test_func.__name__,
                        test_type=suite.test_type,
                        status=TestStatus.ERROR,
                        duration=0.0,
                        start_time=datetime.now(),
                        end_time=datetime.now(),
                        error=str(e)
                    )
                    results.append(result)

        return results

    async def _run_single_test(self, test_func: Callable, suite: TestSuite) -> TestResult:
        """Run a single test with error handling and retry logic."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._run_single_test_sync, test_func, suite
        )

    def _run_single_test_sync(self, test_func: Callable, suite: TestSuite) -> TestResult:
        """Synchronous test execution for thread pool."""
        test_id = str(uuid.uuid4())
        test_name = test_func.__name__
        start_time = datetime.now()

        # Initialize result with minimal data
        result = TestResult(
            test_id=test_id,
            test_name=test_name,
            test_type=suite.test_type,
            status=TestStatus.PENDING,
            duration=0.0,
            start_time=start_time,
            end_time=start_time
        )

        # Run with retry logic
        last_exception = None
        for attempt in range(suite.retry_count + 1):
            try:
                if attempt > 0:
                    self.logger.info("retrying_test", test=test_name, attempt=attempt)

                # Execute test
                start_time = datetime.now()

                if asyncio.iscoroutinefunction(test_func):
                    # Run async test in new event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        test_result = loop.run_until_complete(test_func())
                    finally:
                        loop.close()
                else:
                    test_result = test_func()

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                # Update result
                if isinstance(test_result, TestResult):
                    result = test_result
                    result.test_id = test_id
                    result.test_name = test_name
                    result.test_type = suite.test_type
                    result.duration = duration
                    result.start_time = start_time
                    result.end_time = end_time
                else:
                    # Simple boolean or assertion result
                    result.status = TestStatus.PASSED if test_result else TestStatus.FAILED
                    result.duration = duration
                    result.end_time = end_time
                    result.assertions = 1
                    result.passed_assertions = 1 if test_result else 0

                # Update Prometheus metrics
                self.test_counter.labels(
                    test_type=result.test_type.value,
                    status=result.status.value
                ).inc()

                self.test_duration.labels(
                    test_type=result.test_type.value,
                    test_name=result.test_name
                ).observe(result.duration)

                self.assertion_counter.labels(
                    test_type=result.test_type.value,
                    result='passed' if result.status == TestStatus.PASSED else 'failed'
                ).inc(result.assertions)

                self.logger.info(
                    "test_completed",
                    test=test_name,
                    status=result.status.value,
                    duration=duration,
                    attempt=attempt + 1
                )

                return result

            except Exception as e:
                last_exception = e
                self.logger.warning(
                    "test_attempt_failed",
                    test=test_name,
                    attempt=attempt + 1,
                    error=str(e)
                )

                if attempt == suite.retry_count:
                    # Final attempt failed
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()

                    result.status = TestStatus.ERROR if not isinstance(e, AssertionError) else TestStatus.FAILED
                    result.duration = duration
                    result.end_time = end_time
                    result.error = str(e)
                    result.message = f"Test failed after {suite.retry_count + 1} attempts"

                    # Update error metrics
                    self.test_counter.labels(
                        test_type=result.test_type.value,
                        status=result.status.value
                    ).inc()

                    self.test_duration.labels(
                        test_type=result.test_type.value,
                        test_name=result.test_name
                    ).observe(duration)

                    self.logger.error(
                        "test_failed",
                        test=test_name,
                        status=result.status.value,
                        error=str(e),
                        duration=duration
                    )

        return result

    async def run_all_suites(self) -> Dict[TestType, List[TestResult]]:
        """Run all registered test suites."""
        self.logger.info("running_all_test_suites", suites=len(self.suites))

        all_results = {}

        # Run suites in parallel where possible
        suite_tasks = []
        suite_types = []

        for test_type in self.suites:
            # Skip certain suites that should run sequentially
            if test_type in [TestType.LOAD, TestType.STRESS]:
                continue
            suite_tasks.append(self.run_suite(test_type))
            suite_types.append(test_type)

        # Execute parallel suites
        if suite_tasks:
            parallel_results = await asyncio.gather(*suite_tasks, return_exceptions=True)

            for test_type, result in zip(suite_types, parallel_results):
                if isinstance(result, Exception):
                    self.logger.error("suite_execution_failed", suite=test_type.value, error=str(result))
                    all_results[test_type] = []
                else:
                    all_results[test_type] = result

        # Run sequential suites
        for test_type in [TestType.LOAD, TestType.STRESS]:
            if test_type in self.suites:
                try:
                    all_results[test_type] = await self.run_suite(test_type)
                except Exception as e:
                    self.logger.error("suite_execution_failed", suite=test_type.value, error=str(e))
                    all_results[test_type] = []

        return all_results

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all test results."""
        if not self.results:
            return {"total": 0, "by_status": {}, "by_type": {}}

        summary = {
            "total": len(self.results),
            "by_status": defaultdict(int),
            "by_type": defaultdict(int),
            "total_duration": sum(r.duration for r in self.results),
            "average_duration": sum(r.duration for r in self.results) / len(self.results),
            "total_assertions": sum(r.assertions for r in self.results),
            "passed_assertions": sum(r.passed_assertions for r in self.results)
        }

        for result in self.results:
            summary["by_status"][result.status.value] += 1
            summary["by_type"][result.test_type.value] += 1

        # Calculate success rate
        total_tests = summary["total"]
        passed_tests = summary["by_status"].get(TestStatus.PASSED.value, 0)
        summary["success_rate"] = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Calculate assertion success rate
        total_assertions = summary["total_assertions"]
        passed_assertions = summary["passed_assertions"]
        summary["assertion_success_rate"] = (passed_assertions / total_assertions * 100) if total_assertions > 0 else 0

        return summary

# ========================================
# Metrics Collection Infrastructure
# ========================================

class MetricsCollector:
    """
    Comprehensive metrics collection system with Prometheus integration.

    Features:
    - System metrics (CPU, memory, disk, network)
    - Application metrics (requests, errors, response times)
    - Custom business metrics
    - Prometheus integration
    - Real-time monitoring
    """

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        self.metrics: Dict[str, MonitoringMetric] = {}
        self.collectors: List[Callable] = []
        self.logger = structlog.get_logger("metrics_collector")

        # Initialize Prometheus metrics
        self._init_prometheus_metrics()

        # Initialize system collectors
        self._init_system_collectors()

    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics."""
        # System metrics
        self.cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'Current CPU usage percentage',
            registry=self.registry
        )

        self.memory_usage = Gauge(
            'system_memory_usage_bytes',
            'Current memory usage in bytes',
            registry=self.registry
        )

        self.memory_percent = Gauge(
            'system_memory_usage_percent',
            'Current memory usage percentage',
            registry=self.registry
        )

        self.disk_usage = Gauge(
            'system_disk_usage_percent',
            'Current disk usage percentage',
            ['mountpoint'],
            registry=self.registry
        )

        # Application metrics
        self.request_count = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )

        self.request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )

        self.active_connections = Gauge(
            'active_connections_total',
            'Number of active connections',
            registry=self.registry
        )

        # Business metrics
        self.workflow_count = Counter(
            'workflows_total',
            'Total workflows executed',
            ['status', 'type'],
            registry=self.registry
        )

        self.agent_tasks = Counter(
            'agent_tasks_total',
            'Total agent tasks executed',
            ['agent', 'status'],
            registry=self.registry
        )

        self.alerts_total = Counter(
            'alerts_total',
            'Total alerts generated',
            ['level', 'source'],
            registry=self.registry
        )

    def _init_system_collectors(self):
        """Initialize system metric collectors."""
        self.collectors.extend([
            self._collect_cpu_metrics,
            self._collect_memory_metrics,
            self._collect_disk_metrics,
            self._collect_network_metrics
        ])

    def add_collector(self, collector_func: Callable[[], List[MonitoringMetric]]):
        """Add a custom metric collector."""
        self.collectors.append(collector_func)

    def collect_metrics(self) -> List[MonitoringMetric]:
        """Collect all metrics."""
        all_metrics = []

        for collector in self.collectors:
            try:
                metrics = collector()
                all_metrics.extend(metrics)
            except Exception as e:
                self.logger.error("metric_collection_failed", collector=collector.__name__, error=str(e))

        # Update internal metrics storage
        for metric in all_metrics:
            self.metrics[f"{metric.name}_{metric.timestamp.timestamp()}"] = metric

        # Clean old metrics (keep last 10000)
        if len(self.metrics) > 10000:
            sorted_keys = sorted(self.metrics.keys())
            for key in sorted_keys[:5000]:
                del self.metrics[key]

        return all_metrics

    def _collect_cpu_metrics(self) -> List[MonitoringMetric]:
        """Collect CPU-related metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]

            # Update Prometheus metrics
            self.cpu_usage.set(cpu_percent)

            metrics = [
                MonitoringMetric(
                    name="cpu_usage_percent",
                    value=cpu_percent,
                    timestamp=datetime.now(),
                    metric_type=MonitorType.SYSTEM,
                    unit="percent",
                    description="Current CPU usage percentage"
                ),
                MonitoringMetric(
                    name="cpu_count",
                    value=cpu_count,
                    timestamp=datetime.now(),
                    metric_type=MonitorType.SYSTEM,
                    unit="count",
                    description="Number of CPU cores"
                ),
                MonitoringMetric(
                    name="load_average_1m",
                    value=load_avg[0],
                    timestamp=datetime.now(),
                    metric_type=MonitorType.SYSTEM,
                    unit="load",
                    description="1-minute load average"
                ),
                MonitoringMetric(
                    name="load_average_5m",
                    value=load_avg[1],
                    timestamp=datetime.now(),
                    metric_type=MonitorType.SYSTEM,
                    unit="load",
                    description="5-minute load average"
                ),
                MonitoringMetric(
                    name="load_average_15m",
                    value=load_avg[2],
                    timestamp=datetime.now(),
                    metric_type=MonitorType.SYSTEM,
                    unit="load",
                    description="15-minute load average"
                )
            ]

            return metrics

        except Exception as e:
            self.logger.error("cpu_metrics_collection_failed", error=str(e))
            return []

    def _collect_memory_metrics(self) -> List[MonitoringMetric]:
        """Collect memory-related metrics."""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Update Prometheus metrics
            self.memory_usage.set(memory.used)
            self.memory_percent.set(memory.percent)

            metrics = [
                MonitoringMetric(
                    name="memory_total_bytes",
                    value=memory.total,
                    timestamp=datetime.now(),
                    metric_type=MonitorType.MEMORY,
                    unit="bytes",
                    description="Total memory in bytes"
                ),
                MonitoringMetric(
                    name="memory_available_bytes",
                    value=memory.available,
                    timestamp=datetime.now(),
                    metric_type=MonitorType.MEMORY,
                    unit="bytes",
                    description="Available memory in bytes"
                ),
                MonitoringMetric(
                    name="memory_used_bytes",
                    value=memory.used,
                    timestamp=datetime.now(),
                    metric_type=MonitorType.MEMORY,
                    unit="bytes",
                    description="Used memory in bytes"
                ),
                MonitoringMetric(
                    name="memory_percent",
                    value=memory.percent,
                    timestamp=datetime.now(),
                    metric_type=MonitorType.MEMORY,
                    unit="percent",
                    description="Memory usage percentage"
                ),
                MonitoringMetric(
                    name="swap_used_bytes",
                    value=swap.used,
                    timestamp=datetime.now(),
                    metric_type=MonitorType.MEMORY,
                    unit="bytes",
                    description="Used swap memory in bytes"
                ),
                MonitoringMetric(
                    name="swap_percent",
                    value=swap.percent,
                    timestamp=datetime.now(),
                    metric_type=MonitorType.MEMORY,
                    unit="percent",
                    description="Swap usage percentage"
                )
            ]

            return metrics

        except Exception as e:
            self.logger.error("memory_metrics_collection_failed", error=str(e))
            return []

    def _collect_disk_metrics(self) -> List[MonitoringMetric]:
        """Collect disk-related metrics."""
        try:
            disk_metrics = []

            # Get disk partitions
            partitions = psutil.disk_partitions()

            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)

                    # Update Prometheus metrics
                    self.disk_usage.labels(mountpoint=partition.mountpoint).set(
                        (usage.used / usage.total) * 100
                    )

                    metrics = [
                        MonitoringMetric(
                            name="disk_total_bytes",
                            value=usage.total,
                            timestamp=datetime.now(),
                            metric_type=MonitorType.SYSTEM,
                            labels={"mountpoint": partition.mountpoint, "device": partition.device},
                            unit="bytes",
                            description=f"Total disk space for {partition.mountpoint}"
                        ),
                        MonitoringMetric(
                            name="disk_used_bytes",
                            value=usage.used,
                            timestamp=datetime.now(),
                            metric_type=MonitorType.SYSTEM,
                            labels={"mountpoint": partition.mountpoint, "device": partition.device},
                            unit="bytes",
                            description=f"Used disk space for {partition.mountpoint}"
                        ),
                        MonitoringMetric(
                            name="disk_free_bytes",
                            value=usage.free,
                            timestamp=datetime.now(),
                            metric_type=MonitorType.SYSTEM,
                            labels={"mountpoint": partition.mountpoint, "device": partition.device},
                            unit="bytes",
                            description=f"Free disk space for {partition.mountpoint}"
                        ),
                        MonitoringMetric(
                            name="disk_percent",
                            value=(usage.used / usage.total) * 100,
                            timestamp=datetime.now(),
                            metric_type=MonitorType.SYSTEM,
                            labels={"mountpoint": partition.mountpoint, "device": partition.device},
                            unit="percent",
                            description=f"Disk usage percentage for {partition.mountpoint}"
                        )
                    ]

                    disk_metrics.extend(metrics)

                except PermissionError:
                    self.logger.warning("disk_permission_denied", mountpoint=partition.mountpoint)
                    continue

            # Get disk I/O stats
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    io_metrics = [
                        MonitoringMetric(
                            name="disk_read_count",
                            value=disk_io.read_count,
                            timestamp=datetime.now(),
                            metric_type=MonitorType.SYSTEM,
                            unit="count",
                            description="Total disk read operations"
                        ),
                        MonitoringMetric(
                            name="disk_write_count",
                            value=disk_io.write_count,
                            timestamp=datetime.now(),
                            metric_type=MonitorType.SYSTEM,
                            unit="count",
                            description="Total disk write operations"
                        ),
                        MonitoringMetric(
                            name="disk_read_bytes",
                            value=disk_io.read_bytes,
                            timestamp=datetime.now(),
                            metric_type=MonitorType.SYSTEM,
                            unit="bytes",
                            description="Total bytes read from disk"
                        ),
                        MonitoringMetric(
                            name="disk_write_bytes",
                            value=disk_io.write_bytes,
                            timestamp=datetime.now(),
                            metric_type=MonitorType.SYSTEM,
                            unit="bytes",
                            description="Total bytes written to disk"
                        )
                    ]
                    disk_metrics.extend(io_metrics)
            except Exception as e:
                self.logger.warning("disk_io_metrics_failed", error=str(e))

            return disk_metrics

        except Exception as e:
            self.logger.error("disk_metrics_collection_failed", error=str(e))
            return []

    def _collect_network_metrics(self) -> List[MonitoringMetric]:
        """Collect network-related metrics."""
        try:
            network_metrics = []

            # Get network I/O stats
            try:
                net_io = psutil.net_io_counters()
                if net_io:
                    metrics = [
                        MonitoringMetric(
                            name="network_bytes_sent",
                            value=net_io.bytes_sent,
                            timestamp=datetime.now(),
                            metric_type=MonitorType.NETWORK,
                            unit="bytes",
                            description="Total bytes sent over network"
                        ),
                        MonitoringMetric(
                            name="network_bytes_recv",
                            value=net_io.bytes_recv,
                            timestamp=datetime.now(),
                            metric_type=MonitorType.NETWORK,
                            unit="bytes",
                            description="Total bytes received over network"
                        ),
                        MonitoringMetric(
                            name="network_packets_sent",
                            value=net_io.packets_sent,
                            timestamp=datetime.now(),
                            metric_type=MonitorType.NETWORK,
                            unit="count",
                            description="Total packets sent over network"
                        ),
                        MonitoringMetric(
                            name="network_packets_recv",
                            value=net_io.packets_recv,
                            timestamp=datetime.now(),
                            metric_type=MonitorType.NETWORK,
                            unit="count",
                            description="Total packets received over network"
                        ),
                        MonitoringMetric(
                            name="network_errin",
                            value=net_io.errin,
                            timestamp=datetime.now(),
                            metric_type=MonitorType.NETWORK,
                            unit="count",
                            description="Total network input errors"
                        ),
                        MonitoringMetric(
                            name="network_errout",
                            value=net_io.errout,
                            timestamp=datetime.now(),
                            metric_type=MonitorType.NETWORK,
                            unit="count",
                            description="Total network output errors"
                        ),
                        MonitoringMetric(
                            name="network_dropin",
                            value=net_io.dropin,
                            timestamp=datetime.now(),
                            metric_type=MonitorType.NETWORK,
                            unit="count",
                            description="Total incoming packets dropped"
                        ),
                        MonitoringMetric(
                            name="network_dropout",
                            value=net_io.dropout,
                            timestamp=datetime.now(),
                            metric_type=MonitorType.NETWORK,
                            unit="count",
                            description="Total outgoing packets dropped"
                        )
                    ]
                    network_metrics.extend(metrics)
            except Exception as e:
                self.logger.warning("network_io_metrics_failed", error=str(e))

            # Get network connections
            try:
                connections = psutil.net_connections()
                connection_stats = defaultdict(int)

                for conn in connections:
                    connection_stats[conn.status] += 1

                for status, count in connection_stats.items():
                    metric = MonitoringMetric(
                        name="network_connections",
                        value=count,
                        timestamp=datetime.now(),
                        metric_type=MonitorType.NETWORK,
                        labels={"status": status},
                        unit="count",
                        description=f"Number of {status} network connections"
                    )
                    network_metrics.append(metric)

                # Update active connections gauge
                self.active_connections.set(len(connections))

            except Exception as e:
                self.logger.warning("network_connections_metrics_failed", error=str(e))

            return network_metrics

        except Exception as e:
            self.logger.error("network_metrics_collection_failed", error=str(e))
            return []

    def record_http_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics."""
        self.request_count.labels(method=method, endpoint=endpoint, status=str(status)).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)

    def record_workflow_execution(self, status: str, workflow_type: str):
        """Record workflow execution metrics."""
        self.workflow_count.labels(status=status, type=workflow_type).inc()

    def record_agent_task(self, agent: str, status: str):
        """Record agent task metrics."""
        self.agent_tasks.labels(agent=agent, status=status).inc()

    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in text format."""
        return generate_latest(self.registry).decode('utf-8')

    async def push_metrics_to_gateway(self, gateway_url: str, job_name: str):
        """Push metrics to Prometheus pushgateway."""
        try:
            push_to_gateway(gateway_url, job=job_name, registry=self.registry)
            self.logger.info("metrics_pushed_to_gateway", gateway=gateway_url, job=job_name)
        except Exception as e:
            self.logger.error("metrics_push_failed", gateway=gateway_url, error=str(e))

# ========================================
# Alert Management Infrastructure
# ========================================

class AlertRule:
    """Represents an alert rule."""

    def __init__(
        self,
        name: str,
        condition: Callable[[MonitoringMetric], bool],
        level: AlertLevel,
        message_template: str,
        cooldown: float = 300.0,  # 5 minutes default cooldown
        enabled: bool = True
    ):
        self.name = name
        self.condition = condition
        self.level = level
        self.message_template = message_template
        self.cooldown = cooldown
        self.enabled = enabled
        self.last_triggered = None
        self.logger = structlog.get_logger(f"alert_rule.{name}")

    def evaluate(self, metric: MonitoringMetric) -> Optional[Alert]:
        """Evaluate the rule against a metric."""
        if not self.enabled:
            return None

        # Check cooldown
        if self.last_triggered:
            time_since_last = (datetime.now() - self.last_triggered).total_seconds()
            if time_since_last < self.cooldown:
                return None

        try:
            if self.condition(metric):
                self.last_triggered = datetime.now()

                # Format message
                message = self.message_template.format(
                    metric_name=metric.name,
                    metric_value=metric.value,
                    metric_unit=metric.unit or "",
                    timestamp=metric.timestamp.isoformat()
                )

                alert = Alert(
                    alert_id=str(uuid.uuid4()),
                    level=self.level,
                    title=f"Alert: {self.name}",
                    message=message,
                    timestamp=datetime.now(),
                    source=self.name,
                    metric_name=metric.name,
                    current_value=metric.value
                )

                self.logger.info(
                    "alert_triggered",
                    rule=self.name,
                    level=self.level.value,
                    metric=metric.name,
                    value=metric.value
                )

                return alert

        except Exception as e:
            self.logger.error("alert_rule_evaluation_failed", rule=self.name, error=str(e))

        return None

class NotificationChannel(ABC):
    """Abstract base class for notification channels."""

    @abstractmethod
    async def send_alert(self, alert: Alert) -> bool:
        """Send an alert through this channel."""
        pass

class EmailNotificationChannel(NotificationChannel):
    """Email notification channel."""

    def __init__(self, smtp_config: Dict[str, Any]):
        self.smtp_config = smtp_config
        self.logger = structlog.get_logger("notification.email")

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via email."""
        # Implementation would require SMTP library
        # This is a placeholder implementation
        self.logger.info(
            "email_alert_sent",
            alert_id=alert.alert_id,
            level=alert.level.value,
            title=alert.title
        )
        return True

class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.logger = structlog.get_logger("notification.slack")

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to Slack."""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "text": f"[{alert.level.value.upper()}] {alert.title}",
                    "attachments": [
                        {
                            "color": self._get_color_for_level(alert.level),
                            "fields": [
                                {"title": "Message", "value": alert.message, "short": False},
                                {"title": "Source", "value": alert.source, "short": True},
                                {"title": "Time", "value": alert.timestamp.isoformat(), "short": True}
                            ]
                        }
                    ]
                }

                if alert.metric_name and alert.current_value is not None:
                    payload["attachments"][0]["fields"].append({
                        "title": "Metric",
                        "value": f"{alert.metric_name}: {alert.current_value}",
                        "short": True
                    })

                response = await client.post(self.webhook_url, json=payload)
                response.raise_for_status()

                self.logger.info(
                    "slack_alert_sent",
                    alert_id=alert.alert_id,
                    status_code=response.status_code
                )

                return True

        except Exception as e:
            self.logger.error("slack_alert_failed", alert_id=alert.alert_id, error=str(e))
            return False

    def _get_color_for_level(self, level: AlertLevel) -> str:
        """Get Slack color for alert level."""
        colors = {
            AlertLevel.INFO: "#36a64f",
            AlertLevel.WARNING: "#ff9500",
            AlertLevel.ERROR: "#ff0000",
            AlertLevel.CRITICAL: "#8b0000"
        }
        return colors.get(level, "#36a64f")

class WebhookNotificationChannel(NotificationChannel):
    """Generic webhook notification channel."""

    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}
        self.logger = structlog.get_logger("notification.webhook")

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via webhook."""
        try:
            async with httpx.AsyncClient() as client:
                payload = alert.to_dict()

                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()

                self.logger.info(
                    "webhook_alert_sent",
                    alert_id=alert.alert_id,
                    status_code=response.status_code
                )

                return True

        except Exception as e:
            self.logger.error("webhook_alert_failed", alert_id=alert.alert_id, error=str(e))
            return False

class AlertManager:
    """
    Comprehensive alert management system.

    Features:
    - Multiple alert rules
    - Various notification channels
    - Alert deduplication
    - Alert history
    - Cooldown management
    """

    def __init__(self):
        self.rules: List[AlertRule] = []
        self.notification_channels: List[NotificationChannel] = []
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        self.logger = structlog.get_logger("alert_manager")

        # Initialize default alert rules
        self._init_default_rules()

    def _init_default_rules(self):
        """Initialize default alert rules."""
        # High CPU usage alert
        self.add_rule(AlertRule(
            name="high_cpu_usage",
            condition=lambda m: m.name == "cpu_usage_percent" and m.value > 80,
            level=AlertLevel.WARNING,
            message_template="High CPU usage detected: {metric_value}%",
            cooldown=300.0
        ))

        # Critical CPU usage alert
        self.add_rule(AlertRule(
            name="critical_cpu_usage",
            condition=lambda m: m.name == "cpu_usage_percent" and m.value > 95,
            level=AlertLevel.CRITICAL,
            message_template="Critical CPU usage detected: {metric_value}%",
            cooldown=60.0
        ))

        # High memory usage alert
        self.add_rule(AlertRule(
            name="high_memory_usage",
            condition=lambda m: m.name == "memory_percent" and m.value > 85,
            level=AlertLevel.WARNING,
            message_template="High memory usage detected: {metric_value}%",
            cooldown=300.0
        ))

        # Critical memory usage alert
        self.add_rule(AlertRule(
            name="critical_memory_usage",
            condition=lambda m: m.name == "memory_percent" and m.value > 95,
            level=AlertLevel.CRITICAL,
            message_template="Critical memory usage detected: {metric_value}%",
            cooldown=60.0
        ))

        # Low disk space alert
        self.add_rule(AlertRule(
            name="low_disk_space",
            condition=lambda m: m.name == "disk_percent" and m.value > 90,
            level=AlertLevel.WARNING,
            message_template="Low disk space detected: {metric_value}% used",
            cooldown=600.0
        ))

        # Critical disk space alert
        self.add_rule(AlertRule(
            name="critical_disk_space",
            condition=lambda m: m.name == "disk_percent" and m.value > 95,
            level=AlertLevel.CRITICAL,
            message_template="Critical disk space detected: {metric_value}% used",
            cooldown=60.0
        ))

    def add_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.rules.append(rule)
        self.logger.info("alert_rule_added", rule=rule.name)

    def add_notification_channel(self, channel: NotificationChannel):
        """Add a notification channel."""
        self.notification_channels.append(channel)
        self.logger.info("notification_channel_added", channel=channel.__class__.__name__)

    def evaluate_metrics(self, metrics: List[MonitoringMetric]) -> List[Alert]:
        """Evaluate metrics against all rules and generate alerts."""
        new_alerts = []

        for metric in metrics:
            for rule in self.rules:
                alert = rule.evaluate(metric)
                if alert:
                    # Check for duplicate alerts
                    alert_key = f"{rule.name}_{alert.metric_name}"

                    if alert_key not in self.alerts or self.alerts[alert_key].resolved:
                        # New or resolved alert
                        self.alerts[alert_key] = alert
                        self.alert_history.append(alert)
                        new_alerts.append(alert)

        # Send notifications for new alerts
        if new_alerts:
            asyncio.create_task(self._send_notifications(new_alerts))

        return new_alerts

    async def _send_notifications(self, alerts: List[Alert]):
        """Send notifications for alerts."""
        for alert in alerts:
            for channel in self.notification_channels:
                try:
                    await channel.send_alert(alert)
                except Exception as e:
                    self.logger.error(
                        "notification_failed",
                        alert_id=alert.alert_id,
                        channel=channel.__class__.__name__,
                        error=str(e)
                    )

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        if alert_id in self.alerts:
            self.alerts[alert_id].acknowledged = True
            self.logger.info("alert_acknowledged", alert_id=alert_id)
            return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved = True
            self.alerts[alert_id].resolved_at = datetime.now()
            self.logger.info("alert_resolved", alert_id=alert_id)
            return True
        return False

    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts."""
        return [alert for alert in self.alerts.values() if not alert.resolved]

    def get_alerts_by_level(self, level: AlertLevel) -> List[Alert]:
        """Get alerts by severity level."""
        return [alert for alert in self.alerts.values() if alert.level == level and not alert.resolved]

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get a summary of alerts."""
        active_alerts = self.get_active_alerts()

        summary = {
            "total_active": len(active_alerts),
            "by_level": defaultdict(int),
            "by_source": defaultdict(int),
            "total_generated": len(self.alert_history),
            "acknowledged": sum(1 for alert in active_alerts if alert.acknowledged),
            "unacknowledged": sum(1 for alert in active_alerts if not alert.acknowledged)
        }

        for alert in active_alerts:
            summary["by_level"][alert.level.value] += 1
            summary["by_source"][alert.source] += 1

        return summary

# ========================================
# Health Check Infrastructure
# ========================================

class HealthCheckProvider(ABC):
    """Abstract base class for health check providers."""

    @abstractmethod
    async def check_health(self) -> HealthCheck:
        """Perform health check."""
        pass

class DatabaseHealthCheck(HealthCheckProvider):
    """Database health check provider."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.logger = structlog.get_logger("health_check.database")

    async def check_health(self) -> HealthCheck:
        """Check database connectivity."""
        start_time = time.time()

        try:
            # Implementation would depend on database type
            # This is a placeholder that simulates database check
            await asyncio.sleep(0.1)  # Simulate query time

            response_time = time.time() - start_time

            return HealthCheck(
                component="database",
                status=HealthStatus.HEALTHY,
                message="Database connection successful",
                details={"response_time": response_time},
                response_time=response_time
            )

        except Exception as e:
            response_time = time.time() - start_time

            return HealthCheck(
                component="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                details={"error": str(e)},
                response_time=response_time
            )

class HTTPHealthCheck(HealthCheckProvider):
    """HTTP endpoint health check provider."""

    def __init__(self, url: str, timeout: float = 10.0, expected_status: int = 200):
        self.url = url
        self.timeout = timeout
        self.expected_status = expected_status
        self.logger = structlog.get_logger("health_check.http")

    async def check_health(self) -> HealthCheck:
        """Check HTTP endpoint."""
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.url)
                response_time = time.time() - start_time

                if response.status_code == self.expected_status:
                    return HealthCheck(
                        component="http_endpoint",
                        status=HealthStatus.HEALTHY,
                        message=f"HTTP endpoint responded with {response.status_code}",
                        details={
                            "url": self.url,
                            "status_code": response.status_code,
                            "response_time": response_time
                        },
                        response_time=response_time
                    )
                else:
                    return HealthCheck(
                        component="http_endpoint",
                        status=HealthStatus.DEGRADED,
                        message=f"HTTP endpoint returned {response.status_code}, expected {self.expected_status}",
                        details={
                            "url": self.url,
                            "status_code": response.status_code,
                            "response_time": response_time
                        },
                        response_time=response_time
                    )

        except Exception as e:
            response_time = time.time() - start_time

            return HealthCheck(
                component="http_endpoint",
                status=HealthStatus.UNHEALTHY,
                message=f"HTTP endpoint check failed: {str(e)}",
                details={
                    "url": self.url,
                    "error": str(e),
                    "response_time": response_time
                },
                response_time=response_time
            )

class SystemHealthCheck(HealthCheckProvider):
    """System resource health check provider."""

    def __init__(self, cpu_threshold: float = 80.0, memory_threshold: float = 85.0, disk_threshold: float = 90.0):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
        self.logger = structlog.get_logger("health_check.system")

    async def check_health(self) -> HealthCheck:
        """Check system resources."""
        start_time = time.time()

        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            response_time = time.time() - start_time

            # Determine overall health status
            if cpu_percent > 95 or memory.percent > 95 or (disk.used / disk.total) * 100 > 95:
                status = HealthStatus.UNHEALTHY
            elif cpu_percent > self.cpu_threshold or memory.percent > self.memory_threshold or (disk.used / disk.total) * 100 > self.disk_threshold:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY

            details = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": (disk.used / disk.total) * 100,
                "cpu_threshold": self.cpu_threshold,
                "memory_threshold": self.memory_threshold,
                "disk_threshold": self.disk_threshold
            }

            message = f"System resources: CPU {cpu_percent}%, Memory {memory.percent}%, Disk {details['disk_percent']:.1f}%"

            return HealthCheck(
                component="system_resources",
                status=status,
                message=message,
                details=details,
                response_time=response_time
            )

        except Exception as e:
            response_time = time.time() - start_time

            return HealthCheck(
                component="system_resources",
                status=HealthStatus.UNHEALTHY,
                message=f"System health check failed: {str(e)}",
                details={"error": str(e)},
                response_time=response_time
            )

class HealthChecker:
    """
    Comprehensive health checking system.

    Features:
    - Multiple health check providers
    - Parallel health check execution
    - Health status aggregation
    - Historical health data
    """

    def __init__(self):
        self.providers: List[HealthCheckProvider] = []
        self.health_history: deque = deque(maxlen=1000)
        self.logger = structlog.get_logger("health_checker")

        # Initialize default providers
        self._init_default_providers()

    def _init_default_providers(self):
        """Initialize default health check providers."""
        self.add_provider(SystemHealthCheck())

        # Add HTTP health check for localhost API
        self.add_provider(HTTPHealthCheck("http://localhost:8000/health"))

    def add_provider(self, provider: HealthCheckProvider):
        """Add a health check provider."""
        self.providers.append(provider)
        self.logger.info("health_provider_added", provider=provider.__class__.__name__)

    async def check_all_health(self) -> Dict[str, HealthCheck]:
        """Check health of all providers."""
        self.logger.info("running_health_checks", providers=len(self.providers))

        # Run health checks in parallel
        tasks = []
        provider_names = []

        for provider in self.providers:
            tasks.append(provider.check_health())
            provider_names.append(provider.__class__.__name__)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        health_checks = {}
        for name, result in zip(provider_names, results):
            if isinstance(result, Exception):
                health_checks[name] = HealthCheck(
                    component=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(result)}",
                    details={"error": str(result)}
                )
            else:
                health_checks[name] = result

        # Store in history
        timestamp = datetime.now()
        self.health_history.append({
            "timestamp": timestamp,
            "checks": health_checks.copy()
        })

        return health_checks

    async def get_overall_health(self) -> HealthCheck:
        """Get overall system health status."""
        health_checks = await self.check_all_health()

        # Determine overall status
        if any(check.status == HealthStatus.UNHEALTHY for check in health_checks.values()):
            overall_status = HealthStatus.UNHEALTHY
        elif any(check.status == HealthStatus.DEGRADED for check in health_checks.values()):
            overall_status = HealthStatus.DEGRADED
        elif all(check.status == HealthStatus.HEALTHY for check in health_checks.values()):
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.UNKNOWN

        # Calculate average response time
        response_times = [check.response_time for check in health_checks.values() if check.response_time is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else None

        details = {
            "total_checks": len(health_checks),
            "healthy_checks": sum(1 for check in health_checks.values() if check.status == HealthStatus.HEALTHY),
            "degraded_checks": sum(1 for check in health_checks.values() if check.status == HealthStatus.DEGRADED),
            "unhealthy_checks": sum(1 for check in health_checks.values() if check.status == HealthStatus.UNHEALTHY),
            "average_response_time": avg_response_time,
            "individual_checks": {name: check.to_dict() for name, check in health_checks.items()}
        }

        message = f"Overall system health: {overall_status.value} ({details['healthy_checks']}/{details['total_checks']} components healthy)"

        return HealthCheck(
            component="overall_system",
            status=overall_status,
            message=message,
            details=details,
            response_time=avg_response_time
        )

# ========================================
# Comprehensive Monitoring System
# ========================================

class ComprehensiveMonitoringSystem:
    """
    Main monitoring system that integrates all components.

    Features:
    - Automated testing
    - Metrics collection
    - Alert management
    - Health checking
    - Real-time monitoring
    - Historical data analysis
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = structlog.get_logger("monitoring_system")

        # Initialize components
        self.test_runner = TestRunner(
            max_workers=self.config.get("max_test_workers", 8)
        )

        self.metrics_collector = MetricsCollector()

        self.alert_manager = AlertManager()

        self.health_checker = HealthChecker()

        # Monitoring state
        self.is_running = False
        self.monitoring_task = None
        self.metrics_task = None

        # Initialize notification channels
        self._init_notification_channels()

        # Initialize test suites
        self._init_test_suites()

    def _init_notification_channels(self):
        """Initialize notification channels based on configuration."""
        # Slack channel
        slack_webhook = self.config.get("slack_webhook_url")
        if slack_webhook:
            self.alert_manager.add_notification_channel(
                SlackNotificationChannel(slack_webhook)
            )

        # Email channel
        smtp_config = self.config.get("smtp")
        if smtp_config:
            self.alert_manager.add_notification_channel(
                EmailNotificationChannel(smtp_config)
            )

        # Webhook channel
        webhook_url = self.config.get("alert_webhook_url")
        if webhook_url:
            self.alert_manager.add_notification_channel(
                WebhookNotificationChannel(webhook_url)
            )

    def _init_test_suites(self):
        """Initialize default test suites."""
        # Unit test suite
        unit_suite = TestSuite(
            name="Unit Tests",
            test_type=TestType.UNIT,
            timeout=60.0,
            parallel=True,
            max_workers=4
        )
        self.test_runner.register_suite(unit_suite)

        # Integration test suite
        integration_suite = TestSuite(
            name="Integration Tests",
            test_type=TestType.INTEGRATION,
            timeout=300.0,
            parallel=False
        )
        self.test_runner.register_suite(integration_suite)

        # Performance test suite
        performance_suite = TestSuite(
            name="Performance Tests",
            test_type=TestType.PERFORMANCE,
            timeout=600.0,
            parallel=False
        )
        self.test_runner.register_suite(performance_suite)

    async def start_monitoring(self, interval: float = 60.0):
        """Start continuous monitoring."""
        if self.is_running:
            self.logger.warning("monitoring_already_running")
            return

        self.is_running = True
        self.logger.info("starting_monitoring", interval=interval)

        # Start background monitoring tasks
        self.monitoring_task = asyncio.create_task(self._monitoring_loop(interval))
        self.metrics_task = asyncio.create_task(self._metrics_collection_loop(interval / 2))

    async def stop_monitoring(self):
        """Stop continuous monitoring."""
        if not self.is_running:
            return

        self.is_running = False
        self.logger.info("stopping_monitoring")

        # Cancel background tasks
        if self.monitoring_task:
            self.monitoring_task.cancel()
        if self.metrics_task:
            self.metrics_task.cancel()

        # Wait for tasks to complete
        try:
            await asyncio.gather(self.monitoring_task, self.metrics_task, return_exceptions=True)
        except asyncio.CancelledError:
            pass

    async def _monitoring_loop(self, interval: float):
        """Main monitoring loop."""
        while self.is_running:
            try:
                # Collect metrics
                metrics = self.metrics_collector.collect_metrics()

                # Evaluate alerts
                alerts = self.alert_manager.evaluate_metrics(metrics)

                # Log summary
                self.logger.info(
                    "monitoring_cycle_completed",
                    metrics_collected=len(metrics),
                    alerts_generated=len(alerts),
                    active_alerts=len(self.alert_manager.get_active_alerts())
                )

                # Sleep until next cycle
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("monitoring_loop_error", error=str(e))
                await asyncio.sleep(10)  # Brief pause before retry

    async def _metrics_collection_loop(self, interval: float):
        """Metrics collection loop."""
        while self.is_running:
            try:
                # Collect system metrics
                self.metrics_collector.collect_metrics()

                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("metrics_collection_error", error=str(e))
                await asyncio.sleep(5)

    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all test suites and return comprehensive results."""
        self.logger.info("running_comprehensive_tests")

        try:
            # Run all test suites
            test_results = await self.test_runner.run_all_suites()

            # Get summary
            summary = self.test_runner.get_summary()

            # Record metrics
            for test_type, results in test_results.items():
                passed = sum(1 for r in results if r.status == TestStatus.PASSED)
                failed = sum(1 for r in results if r.status == TestStatus.FAILED)

                self.metrics_collector.record_workflow_execution(
                    status="passed" if failed == 0 else "failed",
                    workflow_type=f"test_{test_type.value}"
                )

            # Generate alerts for failed tests
            total_failed = summary["by_status"].get(TestStatus.FAILED.value, 0)
            if total_failed > 0:
                alert = Alert(
                    alert_id=str(uuid.uuid4()),
                    level=AlertLevel.WARNING if total_failed < 5 else AlertLevel.ERROR,
                    title="Test Failures Detected",
                    message=f"{total_failed} tests failed out of {summary['total']} tests",
                    timestamp=datetime.now(),
                    source="test_runner",
                    details=summary
                )

                # Send alert notification
                await self.alert_manager._send_notifications([alert])

            return {
                "timestamp": datetime.now().isoformat(),
                "summary": summary,
                "results_by_type": {
                    test_type.value: [result.to_dict() for result in results]
                    for test_type, results in test_results.items()
                },
                "all_results": [result.to_dict() for result in self.test_runner.results]
            }

        except Exception as e:
            self.logger.error("comprehensive_tests_failed", error=str(e))
            raise

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        try:
            # Get health checks
            overall_health = await self.health_checker.get_overall_health()
            individual_health = await self.health_checker.check_all_health()

            # Get alert summary
            alert_summary = self.alert_manager.get_alert_summary()

            # Get latest metrics
            latest_metrics = self.metrics_collector.collect_metrics()

            # Get test summary
            test_summary = self.test_runner.get_summary()

            return {
                "timestamp": datetime.now().isoformat(),
                "health": {
                    "overall": overall_health.to_dict(),
                    "individual": {name: check.to_dict() for name, check in individual_health.items()}
                },
                "alerts": alert_summary,
                "metrics": {
                    "latest": [metric.to_dict() for metric in latest_metrics[-10:]],  # Last 10 metrics
                    "prometheus": self.metrics_collector.get_prometheus_metrics()
                },
                "tests": test_summary,
                "monitoring": {
                    "is_running": self.is_running,
                    "active_alerts": len(self.alert_manager.get_active_alerts()),
                    "total_metrics": len(self.metrics_collector.metrics),
                    "total_tests": len(self.test_runner.results)
                }
            }

        except Exception as e:
            self.logger.error("system_status_failed", error=str(e))
            raise

    def add_custom_test(self, test_func: Callable, test_type: TestType, suite_name: Optional[str] = None):
        """Add a custom test to a suite."""
        if test_type in self.test_runner.suites:
            self.test_runner.suites[test_type].tests.append(test_func)
            self.logger.info("custom_test_added", test=test_func.__name__, type=test_type.value)
        else:
            # Create new suite
            suite = TestSuite(
                name=suite_name or f"{test_type.value.title()} Tests",
                test_type=test_type,
                tests=[test_func]
            )
            self.test_runner.register_suite(suite)

    def add_custom_alert_rule(self, rule: AlertRule):
        """Add a custom alert rule."""
        self.alert_manager.add_rule(rule)

    def add_custom_metric_collector(self, collector_func: Callable[[], List[MonitoringMetric]]):
        """Add a custom metric collector."""
        self.metrics_collector.add_collector(collector_func)

# ========================================
# Test Decorators and Utilities
# ========================================

def test(test_type: TestType = TestType.UNIT, timeout: Optional[float] = None):
    """Decorator to mark functions as tests."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            test_id = str(uuid.uuid4())

            try:
                if timeout:
                    result = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
                else:
                    result = await func(*args, **kwargs)

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                if isinstance(result, TestResult):
                    return result
                else:
                    return TestResult(
                        test_id=test_id,
                        test_name=func.__name__,
                        test_type=test_type,
                        status=TestStatus.PASSED if result else TestStatus.FAILED,
                        duration=duration,
                        start_time=start_time,
                        end_time=end_time,
                        assertions=1,
                        passed_assertions=1 if result else 0
                    )

            except asyncio.TimeoutError:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                return TestResult(
                    test_id=test_id,
                    test_name=func.__name__,
                    test_type=test_type,
                    status=TestStatus.TIMEOUT,
                    duration=duration,
                    start_time=start_time,
                    end_time=end_time,
                    message=f"Test timed out after {timeout} seconds"
                )

            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                return TestResult(
                    test_id=test_id,
                    test_name=func.__name__,
                    test_type=test_type,
                    status=TestStatus.ERROR,
                    duration=duration,
                    start_time=start_time,
                    end_time=end_time,
                    error=str(e),
                    message=f"Test failed with exception: {type(e).__name__}"
                )

        wrapper._test_type = test_type
        wrapper._is_test = True
        return wrapper

    return decorator

def performance_test(max_duration: float = 10.0, max_memory_mb: float = 100.0):
    """Decorator for performance tests."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            import tracemalloc

            # Start memory tracking
            tracemalloc.start()
            process = psutil.Process()
            start_memory = process.memory_info().rss / 1024 / 1024  # MB

            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()

            # Get memory usage
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            peak_memory_mb = peak_memory / 1024 / 1024
            tracemalloc.stop()

            duration = end_time - start_time

            # Check performance constraints
            if duration > max_duration:
                raise AssertionError(f"Test exceeded maximum duration: {duration:.2f}s > {max_duration}s")

            if peak_memory_mb > max_memory_mb:
                raise AssertionError(f"Test exceeded maximum memory: {peak_memory_mb:.2f}MB > {max_memory_mb}MB")

            return result

        return wrapper

    return decorator

def integration_test(dependencies: Optional[List[str]] = None):
    """Decorator for integration tests."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check dependencies
            if dependencies:
                missing_deps = []
                for dep in dependencies:
                    if not await _check_dependency(dep):
                        missing_deps.append(dep)

                if missing_deps:
                    raise AssertionError(f"Missing dependencies: {missing_deps}")

            return await func(*args, **kwargs)

        return wrapper

    return decorator

async def _check_dependency(dependency: str) -> bool:
    """Check if a dependency is available."""
    if dependency.startswith("http://") or dependency.startswith("https://"):
        # Check HTTP endpoint
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(dependency)
                return response.status_code < 500
        except:
            return False
    elif dependency == "database":
        # Check database connectivity
        # Implementation would depend on database type
        return True
    else:
        # Check other dependency types
        return True

# ========================================
# Context Managers and Utilities
# ========================================

@asynccontextmanager
async def monitoring_context(monitoring_system: ComprehensiveMonitoringSystem):
    """Context manager for monitoring operations."""
    await monitoring_system.start_monitoring()
    try:
        yield monitoring_system
    finally:
        await monitoring_system.stop_monitoring()

def measure_time():
    """Decorator to measure function execution time."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                duration = end_time - start_time

                # Log timing
                logger = structlog.get_logger("timing")
                logger.info(
                    "function_execution_time",
                    function=func.__name__,
                    duration=duration,
                    args_count=len(args),
                    kwargs_count=len(kwargs)
                )

        return wrapper

    return decorator

# ========================================
# Main Entry Point
# ========================================

async def main():
    """Example usage of the comprehensive monitoring system."""
    # Initialize monitoring system
    monitoring_system = ComprehensiveMonitoringSystem({
        "slack_webhook_url": os.getenv("SLACK_WEBHOOK_URL"),
        "smtp": {
            "host": os.getenv("SMTP_HOST"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USERNAME"),
            "password": os.getenv("SMTP_PASSWORD")
        }
    })

    async with monitoring_context(monitoring_system):
        # Run comprehensive tests
        test_results = await monitoring_system.run_comprehensive_tests()
        print("Test Results:", json.dumps(test_results, indent=2))

        # Get system status
        system_status = await monitoring_system.get_system_status()
        print("System Status:", json.dumps(system_status, indent=2))

        # Keep monitoring running
        await asyncio.sleep(300)  # 5 minutes

if __name__ == "__main__":
    asyncio.run(main())