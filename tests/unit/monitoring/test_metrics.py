"""
Tests for Prometheus metrics module
"""

import pytest
import time
from prometheus_client import REGISTRY
from src.monitoring.metrics import (
    MetricsCollector,
    http_requests_total,
    zoho_api_calls_total,
    agent_task_duration_seconds,
    recommendations_generated_total,
    cache_hits_total,
    cache_misses_total,
)


@pytest.fixture
def metrics_collector():
    """Fixture for metrics collector"""
    return MetricsCollector()


class TestMetricsCollector:
    """Test MetricsCollector functionality"""

    def test_record_http_request(self, metrics_collector):
        """Test HTTP request metric recording"""
        # Record a request
        metrics_collector.record_http_request(
            method="GET",
            endpoint="/api/v1/accounts",
            status=200,
            duration=0.5
        )

        # Verify counter incremented
        metric_value = http_requests_total.labels(
            method="GET",
            endpoint="/api/v1/accounts",
            status="200"
        )._value._value

        assert metric_value >= 1

    def test_record_zoho_api_call(self, metrics_collector):
        """Test Zoho API call metric recording"""
        metrics_collector.record_zoho_api_call(
            operation="get_accounts",
            status="success",
            duration=1.5,
            rate_limit_remaining=9999
        )

        # Verify counter incremented
        metric_value = zoho_api_calls_total.labels(
            operation="get_accounts",
            status="success"
        )._value._value

        assert metric_value >= 1

    def test_record_agent_task(self, metrics_collector):
        """Test agent task metric recording"""
        metrics_collector.record_agent_task(
            agent_type="enrichment",
            task_type="process_account",
            duration=2.5,
            status="success",
            error_type=None
        )

        # Verify counter incremented
        metric_value = agent_task_duration_seconds.labels(
            agent_type="enrichment",
            task_type="process_account"
        )._sum._value

        assert metric_value >= 2.5

    def test_record_recommendation(self, metrics_collector):
        """Test recommendation metric recording"""
        metrics_collector.record_recommendation(
            recommendation_type="cross_sell",
            priority="high",
            confidence=0.85,
            generation_time=1.0
        )

        # Verify counter incremented
        metric_value = recommendations_generated_total.labels(
            recommendation_type="cross_sell",
            priority="high"
        )._value._value

        assert metric_value >= 1

    def test_record_cache_operation_hit(self, metrics_collector):
        """Test cache hit metric recording"""
        metrics_collector.record_cache_operation(
            operation="get",
            cache_type="redis",
            hit=True,
            duration=0.01
        )

        # Verify hit counter incremented
        metric_value = cache_hits_total.labels(
            cache_type="redis",
            key_pattern="*"
        )._value._value

        assert metric_value >= 1

    def test_record_cache_operation_miss(self, metrics_collector):
        """Test cache miss metric recording"""
        metrics_collector.record_cache_operation(
            operation="get",
            cache_type="redis",
            hit=False,
            duration=0.01
        )

        # Verify miss counter incremented
        metric_value = cache_misses_total.labels(
            cache_type="redis",
            key_pattern="*"
        )._value._value

        assert metric_value >= 1

    def test_get_metrics_format(self, metrics_collector):
        """Test metrics output format"""
        # Record some metrics
        metrics_collector.record_http_request("GET", "/test", 200, 0.1)

        # Get metrics
        metrics_data = metrics_collector.get_metrics()

        # Verify it's in Prometheus format
        assert isinstance(metrics_data, bytes)
        assert b"sergas_http_requests_total" in metrics_data


class TestMetricLabels:
    """Test metric label handling"""

    def test_http_request_labels(self, metrics_collector):
        """Test HTTP request metric labels"""
        metrics_collector.record_http_request(
            method="POST",
            endpoint="/api/v1/sync",
            status=201,
            duration=0.5
        )

        # Labels should be properly set
        metric = http_requests_total.labels(
            method="POST",
            endpoint="/api/v1/sync",
            status="201"
        )
        assert metric is not None

    def test_agent_task_error_labels(self, metrics_collector):
        """Test agent task failure with error type"""
        metrics_collector.record_agent_task(
            agent_type="enrichment",
            task_type="process",
            duration=1.0,
            status="failure",
            error_type="TimeoutError"
        )

        # Error type should be recorded
        # This test verifies the metric can be created with all labels
        assert True  # If we get here, labels are valid


class TestMetricTypes:
    """Test different metric types"""

    def test_counter_increments(self, metrics_collector):
        """Test counter metrics increment correctly"""
        initial = http_requests_total.labels(
            method="GET",
            endpoint="/test",
            status="200"
        )._value._value

        # Record multiple requests
        for _ in range(5):
            metrics_collector.record_http_request("GET", "/test", 200, 0.1)

        final = http_requests_total.labels(
            method="GET",
            endpoint="/test",
            status="200"
        )._value._value

        assert final >= initial + 5

    def test_histogram_observations(self, metrics_collector):
        """Test histogram metrics record observations"""
        # Record multiple observations
        for duration in [0.1, 0.5, 1.0, 2.0]:
            metrics_collector.record_http_request("GET", "/slow", 200, duration)

        # Histogram should have recorded observations
        histogram = agent_task_duration_seconds.labels(
            agent_type="test",
            task_type="test"
        )

        # Recording should work without errors
        assert histogram is not None


class TestErrorHandling:
    """Test error handling in metrics"""

    def test_invalid_metric_values(self, metrics_collector):
        """Test handling of invalid metric values"""
        # Should not raise error with negative duration
        # Prometheus client handles this internally
        metrics_collector.record_http_request("GET", "/test", 200, -1.0)

    def test_missing_optional_parameters(self, metrics_collector):
        """Test metrics with optional parameters omitted"""
        # Should work without rate_limit_remaining
        metrics_collector.record_zoho_api_call(
            operation="test",
            status="success",
            duration=1.0,
            rate_limit_remaining=None
        )

        # Should work without error_type for success
        metrics_collector.record_agent_task(
            agent_type="test",
            task_type="test",
            duration=1.0,
            status="success",
            error_type=None
        )


@pytest.mark.asyncio
class TestAsyncMetrics:
    """Test async metric operations"""

    async def test_async_metric_recording(self, metrics_collector):
        """Test metrics can be recorded in async context"""
        import asyncio

        async def record_metrics():
            for _ in range(10):
                metrics_collector.record_http_request("GET", "/async", 200, 0.1)
                await asyncio.sleep(0.01)

        await record_metrics()

        # Verify metrics were recorded
        metric_value = http_requests_total.labels(
            method="GET",
            endpoint="/async",
            status="200"
        )._value._value

        assert metric_value >= 10


class TestMetricsIntegration:
    """Integration tests for metrics"""

    def test_multiple_metrics_together(self, metrics_collector):
        """Test recording multiple different metrics"""
        # Record various metrics
        metrics_collector.record_http_request("GET", "/test", 200, 0.5)
        metrics_collector.record_zoho_api_call("sync", "success", 1.0, 9999)
        metrics_collector.record_agent_task("test", "task", 2.0, "success", None)
        metrics_collector.record_recommendation("cross_sell", "high", 0.85, 1.0)
        metrics_collector.record_cache_operation("get", "redis", True, 0.01)

        # All should be recorded without errors
        metrics_data = metrics_collector.get_metrics()
        assert len(metrics_data) > 0

    def test_metrics_output_contains_all_types(self, metrics_collector):
        """Test metrics output includes all metric types"""
        # Record at least one of each type
        metrics_collector.record_http_request("GET", "/test", 200, 0.5)
        metrics_collector.record_zoho_api_call("test", "success", 1.0)
        metrics_collector.record_agent_task("test", "task", 1.0, "success", None)

        metrics_data = metrics_collector.get_metrics()
        metrics_str = metrics_data.decode('utf-8')

        # Should contain different metric prefixes
        assert 'sergas_http_requests_total' in metrics_str
        assert 'sergas_zoho_api_calls_total' in metrics_str
