"""
Tests for health check system.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from src.reliability.health_checks import (
    HealthCheckRegistry,
    ServiceHealthCheck,
    DatabaseHealthCheck,
    CacheHealthCheck,
    DependencyHealthCheck,
    HealthStatus,
    HealthCheckResult,
)


@pytest.fixture
def health_registry():
    """Create health check registry."""
    return HealthCheckRegistry()


@pytest.mark.asyncio
async def test_service_health_check_success():
    """Test successful service health check."""
    check = ServiceHealthCheck(name="test_service")
    result = await check.execute()

    assert isinstance(result, HealthCheckResult)
    assert result.name == "test_service"
    assert result.status == HealthStatus.HEALTHY
    assert result.response_time_ms > 0


@pytest.mark.asyncio
async def test_service_health_check_timeout():
    """Test service health check timeout."""
    async def slow_check():
        await asyncio.sleep(10)
        return True

    check = ServiceHealthCheck(
        name="slow_service",
        check_func=slow_check,
        timeout=0.1
    )

    result = await check.execute()

    assert result.status == HealthStatus.UNHEALTHY
    assert "Timeout" in result.error


@pytest.mark.asyncio
async def test_health_registry_registration():
    """Test health check registration."""
    registry = HealthCheckRegistry()
    check = ServiceHealthCheck(name="test_service")

    registry.register(check)

    assert "test_service" in registry.checks
    assert registry.checks["test_service"] == check


@pytest.mark.asyncio
async def test_health_registry_check_all():
    """Test checking all registered health checks."""
    registry = HealthCheckRegistry()

    check1 = ServiceHealthCheck(name="service1")
    check2 = ServiceHealthCheck(name="service2")

    registry.register(check1)
    registry.register(check2)

    results = await registry.check_all()

    assert len(results) == 2
    assert "service1" in results
    assert "service2" in results
    assert all(isinstance(r, HealthCheckResult) for r in results.values())


@pytest.mark.asyncio
async def test_health_registry_summary():
    """Test health summary generation."""
    registry = HealthCheckRegistry()

    # Register checks
    healthy_check = ServiceHealthCheck(name="healthy_service")
    registry.register(healthy_check)

    # Get results
    results = await registry.check_all()
    summary = registry.get_summary(results)

    assert summary["status"] == HealthStatus.HEALTHY.value
    assert summary["total_checks"] == 1
    assert summary["healthy"] == 1
    assert summary["unhealthy"] == 0


@pytest.mark.asyncio
async def test_dependency_health_check():
    """Test external dependency health check."""
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response

        mock_session.return_value.__aenter__.return_value.get.return_value = mock_response

        check = DependencyHealthCheck(
            name="external_api",
            endpoint="https://api.example.com/health"
        )

        result = await check.execute()

        assert result.status == HealthStatus.HEALTHY
        assert result.details["status_code"] == 200


@pytest.mark.asyncio
async def test_health_check_with_error():
    """Test health check error handling."""
    async def failing_check():
        raise ValueError("Test error")

    check = ServiceHealthCheck(
        name="failing_service",
        check_func=failing_check
    )

    result = await check.execute()

    assert result.status == HealthStatus.UNHEALTHY
    assert "Test error" in result.error


@pytest.mark.asyncio
async def test_health_registry_check_one():
    """Test checking single health check."""
    registry = HealthCheckRegistry()
    check = ServiceHealthCheck(name="test_service")
    registry.register(check)

    result = await registry.check_one("test_service")

    assert result is not None
    assert result.name == "test_service"


@pytest.mark.asyncio
async def test_health_registry_check_one_not_found():
    """Test checking non-existent health check."""
    registry = HealthCheckRegistry()

    result = await registry.check_one("nonexistent")

    assert result is None


def test_health_check_result_to_dict():
    """Test HealthCheckResult serialization."""
    result = HealthCheckResult(
        name="test",
        status=HealthStatus.HEALTHY,
        response_time_ms=123.45,
        details={"key": "value"}
    )

    result_dict = result.to_dict()

    assert result_dict["name"] == "test"
    assert result_dict["status"] == "healthy"
    assert result_dict["response_time_ms"] == 123.45
    assert result_dict["details"] == {"key": "value"}
    assert "timestamp" in result_dict
