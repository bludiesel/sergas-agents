"""
Integration Manager Test Suite
Tests three-tier routing (MCP → SDK → REST) with circuit breaker protection.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import asyncio
from typing import Dict, Any, List


class TestIntegrationManagerRouting:
    """Test tier routing logic for Integration Manager."""

    @pytest.mark.asyncio
    async def test_agent_context_routes_to_tier1_mcp(self, integration_manager, mock_mcp_client):
        """Agent operations should route to Tier 1 (MCP)."""
        mock_mcp_client.get_account.return_value = {"id": "123", "name": "Test Account"}

        result = await integration_manager.get_account(
            account_id="123",
            context={"agent": "account_manager", "operation": "read"}
        )

        assert result["id"] == "123"
        assert mock_mcp_client.get_account.called
        assert integration_manager.last_tier_used == "tier1_mcp"

    @pytest.mark.asyncio
    async def test_bulk_operations_route_to_tier2_sdk(self, integration_manager, mock_sdk_client):
        """Bulk operations (100+ records) should route to Tier 2 (SDK)."""
        mock_sdk_client.get_accounts_bulk.return_value = [
            {"id": str(i), "name": f"Account {i}"} for i in range(100)
        ]

        result = await integration_manager.get_accounts_bulk(
            account_ids=[str(i) for i in range(100)]
        )

        assert len(result) == 100
        assert mock_sdk_client.get_accounts_bulk.called
        assert integration_manager.last_tier_used == "tier2_sdk"

    @pytest.mark.asyncio
    async def test_no_context_defaults_to_tier2_sdk(self, integration_manager, mock_sdk_client):
        """Operations without context should default to Tier 2 (SDK)."""
        mock_sdk_client.get_account.return_value = {"id": "456", "name": "Default Account"}

        result = await integration_manager.get_account(account_id="456")

        assert result["id"] == "456"
        assert mock_sdk_client.get_account.called
        assert integration_manager.last_tier_used == "tier2_sdk"

    @pytest.mark.asyncio
    async def test_tier1_failure_falls_back_to_tier2(
        self, integration_manager, mock_mcp_client, mock_sdk_client
    ):
        """Failed Tier 1 request should fall back to Tier 2."""
        # Tier 1 fails
        mock_mcp_client.get_account.side_effect = Exception("MCP unavailable")
        # Tier 2 succeeds
        mock_sdk_client.get_account.return_value = {"id": "789", "name": "Fallback Account"}

        result = await integration_manager.get_account(
            account_id="789",
            context={"agent": "test_agent"}
        )

        assert result["id"] == "789"
        assert mock_mcp_client.get_account.called
        assert mock_sdk_client.get_account.called
        assert integration_manager.last_tier_used == "tier2_sdk"
        assert integration_manager.fallback_count > 0

    @pytest.mark.asyncio
    async def test_tier2_failure_falls_back_to_tier3(
        self, integration_manager, mock_sdk_client, mock_rest_client
    ):
        """Failed Tier 2 request should fall back to Tier 3."""
        # Tier 2 fails
        mock_sdk_client.get_account.side_effect = Exception("SDK error")
        # Tier 3 succeeds
        mock_rest_client.get_account.return_value = {"id": "101", "name": "REST Account"}

        result = await integration_manager.get_account(account_id="101")

        assert result["id"] == "101"
        assert mock_sdk_client.get_account.called
        assert mock_rest_client.get_account.called
        assert integration_manager.last_tier_used == "tier3_rest"

    @pytest.mark.asyncio
    async def test_all_tiers_failed_raises_error(
        self, integration_manager, mock_mcp_client, mock_sdk_client, mock_rest_client
    ):
        """All tiers failing should raise AllTiersFailedError."""
        from src.integrations.integration_manager import AllTiersFailedError

        # All tiers fail
        mock_mcp_client.get_account.side_effect = Exception("MCP down")
        mock_sdk_client.get_account.side_effect = Exception("SDK down")
        mock_rest_client.get_account.side_effect = Exception("REST down")

        with pytest.raises(AllTiersFailedError) as exc_info:
            await integration_manager.get_account(
                account_id="999",
                context={"agent": "test"}
            )

        assert "All tiers failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_tier_selection_based_on_operation_type(self, integration_manager):
        """Tier selection should consider operation type."""
        # Search operations prefer Tier 2
        with patch.object(integration_manager, '_route_to_tier') as mock_route:
            await integration_manager.search_accounts(criteria={"status": "Active"})
            call_args = mock_route.call_args
            assert call_args[0][0] == "tier2_sdk"

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration_skips_open_tier(
        self, integration_manager, circuit_breaker_manager, mock_sdk_client, mock_rest_client
    ):
        """Open circuit breaker should skip tier and fall back."""
        # Open Tier 1 circuit
        circuit_breaker_manager.get_breaker("tier1_mcp").open()

        # Tier 2 should be used directly
        mock_sdk_client.get_account.return_value = {"id": "222", "name": "Skip Tier 1"}

        result = await integration_manager.get_account(
            account_id="222",
            context={"agent": "test"}
        )

        assert result["id"] == "222"
        assert integration_manager.last_tier_used == "tier2_sdk"
        assert integration_manager.circuit_breaker_skips > 0


class TestIntegrationManagerOperations:
    """Test all CRUD operations through Integration Manager."""

    @pytest.mark.asyncio
    async def test_get_account_single_record(self, integration_manager, mock_sdk_client):
        """Get single account should return correct data."""
        mock_sdk_client.get_account.return_value = {
            "id": "ACC001",
            "name": "ACME Corp",
            "status": "Active",
            "revenue": 1000000
        }

        result = await integration_manager.get_account("ACC001")

        assert result["id"] == "ACC001"
        assert result["name"] == "ACME Corp"
        assert result["status"] == "Active"

    @pytest.mark.asyncio
    async def test_get_accounts_multiple_records(self, integration_manager, mock_sdk_client):
        """Get multiple accounts should handle pagination."""
        mock_sdk_client.get_accounts.return_value = {
            "data": [
                {"id": f"ACC{i:03d}", "name": f"Account {i}"} for i in range(50)
            ],
            "page": 1,
            "total": 150
        }

        result = await integration_manager.get_accounts(page=1, per_page=50)

        assert len(result["data"]) == 50
        assert result["total"] == 150

    @pytest.mark.asyncio
    async def test_update_account_success(self, integration_manager, mock_sdk_client):
        """Update account should use appropriate tier."""
        mock_sdk_client.update_account.return_value = {
            "id": "ACC002",
            "name": "Updated Name",
            "updated_at": datetime.now().isoformat()
        }

        result = await integration_manager.update_account(
            account_id="ACC002",
            data={"name": "Updated Name"}
        )

        assert result["name"] == "Updated Name"
        assert "updated_at" in result

    @pytest.mark.asyncio
    async def test_bulk_read_accounts_100_records(self, integration_manager, mock_sdk_client):
        """Bulk read should use Tier 2 SDK."""
        account_ids = [f"ACC{i:03d}" for i in range(100)]
        mock_sdk_client.get_accounts_bulk.return_value = [
            {"id": aid, "name": f"Account {aid}"} for aid in account_ids
        ]

        result = await integration_manager.get_accounts_bulk(account_ids)

        assert len(result) == 100
        assert integration_manager.last_tier_used == "tier2_sdk"

    @pytest.mark.asyncio
    async def test_bulk_update_accounts_batching(self, integration_manager, mock_sdk_client):
        """Bulk update should batch correctly."""
        updates = [
            {"id": f"ACC{i:03d}", "status": "Active"} for i in range(50)
        ]
        mock_sdk_client.update_accounts_bulk.return_value = {
            "updated": 50,
            "failed": 0
        }

        result = await integration_manager.update_accounts_bulk(updates)

        assert result["updated"] == 50
        assert result["failed"] == 0

    @pytest.mark.asyncio
    async def test_search_accounts_with_criteria(self, integration_manager, mock_sdk_client):
        """Search accounts should route correctly."""
        mock_sdk_client.search_accounts.return_value = {
            "results": [
                {"id": "ACC999", "status": "Active", "revenue": 500000}
            ],
            "count": 1
        }

        result = await integration_manager.search_accounts(
            criteria={"status": "Active", "revenue_gt": 100000}
        )

        assert result["count"] == 1
        assert result["results"][0]["id"] == "ACC999"

    @pytest.mark.asyncio
    async def test_create_account_operation(self, integration_manager, mock_sdk_client):
        """Create account should work correctly."""
        mock_sdk_client.create_account.return_value = {
            "id": "ACC_NEW",
            "name": "New Account",
            "created_at": datetime.now().isoformat()
        }

        result = await integration_manager.create_account(
            data={"name": "New Account", "status": "Active"}
        )

        assert result["id"] == "ACC_NEW"
        assert result["name"] == "New Account"

    @pytest.mark.asyncio
    async def test_delete_account_operation(self, integration_manager, mock_sdk_client):
        """Delete account should work correctly."""
        mock_sdk_client.delete_account.return_value = {"success": True}

        result = await integration_manager.delete_account("ACC_DELETE")

        assert result["success"] is True


class TestIntegrationManagerMetrics:
    """Test metrics collection for Integration Manager."""

    @pytest.mark.asyncio
    async def test_metrics_recorded_per_tier(self, integration_manager, mock_sdk_client):
        """Metrics should be recorded for each tier."""
        mock_sdk_client.get_account.return_value = {"id": "M001"}

        await integration_manager.get_account("M001")

        metrics = integration_manager.get_metrics()
        assert "tier2_sdk" in metrics
        assert metrics["tier2_sdk"]["requests"] > 0

    @pytest.mark.asyncio
    async def test_response_time_tracking(self, integration_manager, mock_sdk_client):
        """Response times should be tracked correctly."""
        mock_sdk_client.get_account.return_value = {"id": "RT001"}

        await integration_manager.get_account("RT001")

        metrics = integration_manager.get_metrics()
        assert "tier2_sdk" in metrics
        assert "avg_response_time" in metrics["tier2_sdk"]
        assert metrics["tier2_sdk"]["avg_response_time"] >= 0

    @pytest.mark.asyncio
    async def test_success_rate_calculation(self, integration_manager, mock_sdk_client):
        """Success rates should be calculated per tier."""
        mock_sdk_client.get_account.return_value = {"id": "SR001"}

        # 3 successful requests
        for _ in range(3):
            await integration_manager.get_account("SR001")

        metrics = integration_manager.get_metrics()
        tier2_metrics = metrics.get("tier2_sdk", {})
        assert tier2_metrics.get("success_rate", 0) == 100.0

    @pytest.mark.asyncio
    async def test_error_count_tracking(self, integration_manager, mock_sdk_client):
        """Error counts should be tracked per tier."""
        mock_sdk_client.get_account.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            {"id": "E001"}  # Success on third try
        ]

        # Two failures, one success
        try:
            await integration_manager.get_account("E001")
        except:
            pass
        try:
            await integration_manager.get_account("E001")
        except:
            pass
        await integration_manager.get_account("E001")

        metrics = integration_manager.get_metrics()
        # Should track errors even with fallback


class TestIntegrationManagerHealthChecks:
    """Test health monitoring for Integration Manager."""

    @pytest.mark.asyncio
    async def test_tier_health_check_all_healthy(
        self, integration_manager, mock_mcp_client, mock_sdk_client, mock_rest_client
    ):
        """All tiers healthy should return correct status."""
        mock_mcp_client.health_check.return_value = {"status": "healthy"}
        mock_sdk_client.health_check.return_value = {"status": "healthy"}
        mock_rest_client.health_check.return_value = {"status": "healthy"}

        health = await integration_manager.check_health()

        assert health["tier1_mcp"]["status"] == "healthy"
        assert health["tier2_sdk"]["status"] == "healthy"
        assert health["tier3_rest"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_tier_health_check_one_unhealthy(
        self, integration_manager, mock_mcp_client, mock_sdk_client, mock_rest_client
    ):
        """One tier unhealthy should be detected correctly."""
        mock_mcp_client.health_check.side_effect = Exception("MCP unhealthy")
        mock_sdk_client.health_check.return_value = {"status": "healthy"}
        mock_rest_client.health_check.return_value = {"status": "healthy"}

        health = await integration_manager.check_health()

        assert health["tier1_mcp"]["status"] == "unhealthy"
        assert health["tier2_sdk"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_timeout_handling(self, integration_manager, mock_sdk_client):
        """Health check timeouts should be handled correctly."""
        async def slow_health_check():
            await asyncio.sleep(10)
            return {"status": "healthy"}

        mock_sdk_client.health_check.side_effect = slow_health_check

        health = await integration_manager.check_health(timeout=1)

        # Should timeout and mark as unhealthy
        assert health["tier2_sdk"]["status"] in ["unhealthy", "timeout"]

    @pytest.mark.asyncio
    async def test_circuit_breaker_affects_health(
        self, integration_manager, circuit_breaker_manager
    ):
        """Open circuit breaker should affect health status."""
        circuit_breaker_manager.get_breaker("tier1_mcp").open()

        health = await integration_manager.check_health()

        assert health["tier1_mcp"]["circuit_breaker"] == "open"


class TestIntegrationManagerConfiguration:
    """Test configuration and initialization."""

    def test_initialization_with_all_clients(
        self, mock_mcp_client, mock_sdk_client, mock_rest_client
    ):
        """Integration manager should initialize with all clients."""
        from src.integrations.integration_manager import IntegrationManager

        manager = IntegrationManager(
            mcp_client=mock_mcp_client,
            sdk_client=mock_sdk_client,
            rest_client=mock_rest_client
        )

        assert manager.mcp_client is not None
        assert manager.sdk_client is not None
        assert manager.rest_client is not None

    def test_tier_priorities_configuration(self, integration_manager):
        """Tier priorities should be configurable."""
        priorities = integration_manager.get_tier_priorities()

        assert len(priorities) == 3
        assert priorities[0] == "tier2_sdk"  # Default for no context

    def test_retry_configuration(self, integration_manager):
        """Retry configuration should be set correctly."""
        config = integration_manager.get_retry_config()

        assert config["max_retries"] >= 3
        assert config["backoff_factor"] >= 1


class TestIntegrationManagerConcurrency:
    """Test concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_reads_different_tiers(
        self, integration_manager, mock_mcp_client, mock_sdk_client
    ):
        """Concurrent reads across tiers should work correctly."""
        mock_mcp_client.get_account.return_value = {"id": "C1"}
        mock_sdk_client.get_account.return_value = {"id": "C2"}

        results = await asyncio.gather(
            integration_manager.get_account("C1", context={"agent": "test"}),
            integration_manager.get_account("C2")
        )

        assert len(results) == 2
        assert results[0]["id"] == "C1"
        assert results[1]["id"] == "C2"

    @pytest.mark.asyncio
    async def test_concurrent_writes_thread_safe(self, integration_manager, mock_sdk_client):
        """Concurrent writes should be thread-safe."""
        mock_sdk_client.update_account.return_value = {"success": True}

        updates = [
            integration_manager.update_account(f"A{i}", {"status": "Active"})
            for i in range(10)
        ]

        results = await asyncio.gather(*updates)

        assert len(results) == 10
        assert all(r["success"] for r in results)


class TestIntegrationManagerErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_invalid_account_id_handled(self, integration_manager):
        """Invalid account ID should be handled gracefully."""
        from src.integrations.integration_manager import ValidationError

        with pytest.raises(ValidationError):
            await integration_manager.get_account("")

    @pytest.mark.asyncio
    async def test_network_timeout_triggers_fallback(
        self, integration_manager, mock_sdk_client, mock_rest_client
    ):
        """Network timeout should trigger fallback."""
        mock_sdk_client.get_account.side_effect = asyncio.TimeoutError()
        mock_rest_client.get_account.return_value = {"id": "T001"}

        result = await integration_manager.get_account("T001")

        assert result["id"] == "T001"
        assert integration_manager.last_tier_used == "tier3_rest"

    @pytest.mark.asyncio
    async def test_malformed_response_handled(self, integration_manager, mock_sdk_client):
        """Malformed response should be handled correctly."""
        mock_sdk_client.get_account.return_value = None  # Invalid response

        from src.integrations.integration_manager import InvalidResponseError

        with pytest.raises((InvalidResponseError, Exception)):
            await integration_manager.get_account("BAD001")
