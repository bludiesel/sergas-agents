"""
Comprehensive fixtures for Week 3 Integration & Circuit Breaker tests.
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timedelta


@pytest.fixture
def mock_mcp_client():
    """Mock MCP client with configurable responses."""
    client = AsyncMock()
    client.get_account = AsyncMock()
    client.update_account = AsyncMock()
    client.search_accounts = AsyncMock()
    client.create_account = AsyncMock()
    client.delete_account = AsyncMock()
    client.health_check = AsyncMock(return_value={"status": "healthy"})
    client.list_tools = AsyncMock(return_value=[])
    client.get_metrics = Mock(return_value={"total_requests": 0, "avg_response_time": 0})
    client.is_initialized = True
    client.client_id = "mock_mcp_id"
    return client


@pytest.fixture
def mock_sdk_client():
    """Mock SDK client (from Week 2)."""
    client = AsyncMock()
    client.get_account = AsyncMock()
    client.get_accounts = AsyncMock()
    client.get_accounts_bulk = AsyncMock()
    client.update_account = AsyncMock()
    client.update_accounts_bulk = AsyncMock()
    client.search_accounts = AsyncMock()
    client.create_account = AsyncMock()
    client.create_accounts_bulk = AsyncMock()
    client.delete_account = AsyncMock()
    client.health_check = AsyncMock(return_value={"status": "healthy"})
    client.get_metrics = Mock(return_value={"total_requests": 0})
    return client


@pytest.fixture
def mock_rest_client():
    """Mock REST client with rate limiting."""
    client = AsyncMock()
    client.get_account = AsyncMock()
    client.get_accounts = AsyncMock()
    client.update_account = AsyncMock()
    client.search_accounts = AsyncMock()
    client.create_account = AsyncMock()
    client.create_accounts_bulk = AsyncMock()
    client.update_accounts_bulk = AsyncMock()
    client.delete_account = AsyncMock()
    client.health_check = AsyncMock(return_value={"status": "healthy"})
    client.rate_limit_remaining = 5000
    client.rate_limit_total = 5000
    client.rate_limit_reset = None
    client.api_domain = "https://www.zohoapis.com"
    return client


@pytest.fixture
def circuit_breaker():
    """Create circuit breaker for testing."""
    from src.resilience.circuit_breaker import CircuitBreaker
    return CircuitBreaker(
        name="test_breaker",
        failure_threshold=5,
        recovery_timeout=60,
        half_open_max_calls=1,
        success_threshold=2
    )


@pytest.fixture
def circuit_breaker_manager():
    """Circuit breaker manager with test configuration."""
    from src.resilience.circuit_breaker_manager import CircuitBreakerManager

    manager = CircuitBreakerManager()
    manager.register_breaker("tier1_mcp", failure_threshold=5, recovery_timeout=60)
    manager.register_breaker("tier2_sdk", failure_threshold=5, recovery_timeout=60)
    manager.register_breaker("tier3_rest", failure_threshold=5, recovery_timeout=60)
    return manager


@pytest.fixture
def integration_manager(
    mock_mcp_client,
    mock_sdk_client,
    mock_rest_client,
    circuit_breaker_manager
):
    """Fully configured integration manager for testing."""
    from src.integrations.integration_manager import IntegrationManager

    manager = IntegrationManager(
        mcp_client=mock_mcp_client,
        sdk_client=mock_sdk_client,
        rest_client=mock_rest_client,
        circuit_breaker_manager=circuit_breaker_manager
    )
    return manager


@pytest.fixture
def tier_failure_simulator():
    """Simulate tier failures with configurable patterns."""
    class TierFailureSimulator:
        def __init__(self):
            self.tier1_fail_count = 0
            self.tier2_fail_count = 0
            self.tier3_fail_count = 0
            self.failure_patterns = {}

        def set_failure_pattern(self, tier, pattern):
            """
            Set failure pattern for a tier.
            Pattern examples:
            - [True, True, False] = fail, fail, success
            - "always_fail" = always fail
            - "always_succeed" = always succeed
            - "intermittent:3" = fail every 3rd call
            """
            self.failure_patterns[tier] = pattern

        async def execute_with_pattern(self, tier, operation):
            """Execute operation according to failure pattern."""
            pattern = self.failure_patterns.get(tier, "always_succeed")

            if pattern == "always_fail":
                raise Exception(f"{tier} failure")
            elif pattern == "always_succeed":
                return await operation()
            elif isinstance(pattern, list):
                # Pop first pattern item
                if not pattern:
                    return await operation()
                should_fail = pattern.pop(0)
                if should_fail:
                    raise Exception(f"{tier} configured failure")
                return await operation()
            elif isinstance(pattern, str) and pattern.startswith("intermittent:"):
                # Fail every Nth call
                n = int(pattern.split(":")[1])
                count_attr = f"{tier}_fail_count"
                count = getattr(self, count_attr, 0) + 1
                setattr(self, count_attr, count)

                if count % n == 0:
                    raise Exception(f"{tier} intermittent failure")
                return await operation()

            return await operation()

    return TierFailureSimulator()


@pytest.fixture
def mock_mcp_server():
    """Mock MCP server for MCP client tests."""
    server = AsyncMock()
    server.call_tool = AsyncMock()
    server.list_tools = AsyncMock()
    server.ping = AsyncMock(return_value={"status": "ok"})
    return server


@pytest.fixture
def mock_oauth_server():
    """Mock OAuth server for token refresh."""
    server = Mock()
    server.post = Mock()
    return server


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for REST API tests."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    return client


@pytest.fixture
def mock_oauth_client():
    """Mock OAuth client for authentication."""
    client = AsyncMock()
    client.post = AsyncMock()
    return client


@pytest.fixture
def mcp_client(mock_mcp_server, mock_oauth_server):
    """Configured MCP client for testing."""
    from src.integrations.mcp_client import MCPClient

    client = MCPClient(
        client_id="test_mcp_client",
        client_secret="test_secret",
        refresh_token="test_token"
    )
    client._server = mock_mcp_server
    client._oauth = mock_oauth_server
    return client


@pytest.fixture
def rest_client(mock_http_client, mock_oauth_client):
    """Configured REST client for testing."""
    from src.integrations.rest_client import RESTClient

    client = RESTClient(
        client_id="test_rest_client",
        client_secret="test_secret",
        refresh_token="test_token"
    )
    client._http = mock_http_client
    client._oauth = mock_oauth_client
    return client


@pytest.fixture
def sample_account_data():
    """Sample account data for testing."""
    return {
        "id": "ACC12345",
        "Account_Name": "Test Corporation",
        "Account_Number": "12345",
        "Account_Type": "Customer",
        "Industry": "Technology",
        "Annual_Revenue": 1000000,
        "Number_of_Employees": 50,
        "Phone": "+1-555-0100",
        "Website": "https://testcorp.example.com",
        "Billing_Street": "123 Test St",
        "Billing_City": "San Francisco",
        "Billing_State": "CA",
        "Billing_Code": "94105",
        "Billing_Country": "USA",
        "Description": "Test account for integration tests",
        "Created_Time": datetime.now().isoformat(),
        "Modified_Time": datetime.now().isoformat()
    }


@pytest.fixture
def sample_bulk_accounts():
    """Sample bulk account data for testing."""
    return [
        {
            "id": f"ACC{i:05d}",
            "Account_Name": f"Test Company {i}",
            "Account_Number": str(10000 + i),
            "Status": "Active",
            "Annual_Revenue": 100000 * i
        }
        for i in range(100)
    ]


@pytest.fixture
def performance_timer():
    """Timer for performance testing."""
    import time

    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.elapsed = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()
            self.elapsed = self.end_time - self.start_time
            return self.elapsed

        def assert_under(self, max_seconds):
            assert self.elapsed is not None, "Timer not stopped"
            assert self.elapsed < max_seconds, \
                f"Elapsed time {self.elapsed:.3f}s exceeded limit {max_seconds}s"

    return PerformanceTimer()


@pytest.fixture
def metrics_collector():
    """Collect metrics during tests."""
    class MetricsCollector:
        def __init__(self):
            self.metrics = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "tier1_calls": 0,
                "tier2_calls": 0,
                "tier3_calls": 0,
                "fallback_count": 0,
                "circuit_breaker_opens": 0,
                "response_times": []
            }

        def record_call(self, tier, success, response_time):
            self.metrics["total_calls"] += 1
            if success:
                self.metrics["successful_calls"] += 1
            else:
                self.metrics["failed_calls"] += 1

            self.metrics[f"{tier}_calls"] += 1
            self.metrics["response_times"].append(response_time)

        def record_fallback(self):
            self.metrics["fallback_count"] += 1

        def record_circuit_open(self):
            self.metrics["circuit_breaker_opens"] += 1

        def get_summary(self):
            if not self.metrics["response_times"]:
                avg_response_time = 0
            else:
                avg_response_time = sum(self.metrics["response_times"]) / len(self.metrics["response_times"])

            return {
                **self.metrics,
                "success_rate": self.metrics["successful_calls"] / max(self.metrics["total_calls"], 1) * 100,
                "avg_response_time": avg_response_time
            }

    return MetricsCollector()
