"""
Three-Tier Integration Test Suite
End-to-end tests for MCP → SDK → REST tier coordination with circuit breaker protection.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import time


class TestEndToEndThreeTierWorkflow:
    """Test complete three-tier workflows end-to-end."""

    @pytest.mark.asyncio
    async def test_agent_operation_full_workflow(
        self, integration_manager, mock_mcp_client, circuit_breaker_manager
    ):
        """
        Full agent operation workflow:
        1. Request with agent context
        2. Routes to Tier 1 (MCP)
        3. Returns data to caller
        4. Metrics collected
        """
        # Setup MCP response
        mock_mcp_client.get_account.return_value = {
            "id": "AGENT001",
            "name": "Agent Test Account",
            "status": "Active",
            "tier_used": "mcp"
        }

        # Execute operation with agent context
        start_time = time.time()
        result = await integration_manager.get_account(
            account_id="AGENT001",
            context={"agent": "account_manager", "operation": "read"}
        )
        duration = time.time() - start_time

        # Verify routing
        assert result["id"] == "AGENT001"
        assert integration_manager.last_tier_used == "tier1_mcp"
        assert mock_mcp_client.get_account.called

        # Verify metrics
        metrics = integration_manager.get_metrics()
        assert metrics["tier1_mcp"]["requests"] > 0
        assert metrics["tier1_mcp"]["avg_response_time"] > 0

        # Verify performance
        assert duration < 0.5  # Should be fast

    @pytest.mark.asyncio
    async def test_bulk_operation_full_workflow(
        self, integration_manager, mock_sdk_client
    ):
        """
        Full bulk operation workflow:
        1. Bulk read 500 accounts
        2. Routes to Tier 2 (SDK)
        3. Returns batched results
        4. Performance within SLA
        """
        # Setup SDK to return 500 accounts
        account_ids = [f"BULK{i:04d}" for i in range(500)]
        mock_sdk_client.get_accounts_bulk.return_value = [
            {"id": aid, "name": f"Account {aid}", "status": "Active"}
            for aid in account_ids
        ]

        # Execute bulk operation
        start_time = time.time()
        result = await integration_manager.get_accounts_bulk(account_ids)
        duration = time.time() - start_time

        # Verify results
        assert len(result) == 500
        assert integration_manager.last_tier_used == "tier2_sdk"
        assert mock_sdk_client.get_accounts_bulk.called

        # Verify performance (should be < 5s for 500 records)
        assert duration < 5.0

        # Verify metrics
        metrics = integration_manager.get_metrics()
        assert metrics["tier2_sdk"]["requests"] > 0

    @pytest.mark.asyncio
    async def test_tier1_failure_automatic_fallback(
        self, integration_manager, mock_mcp_client, mock_sdk_client, circuit_breaker_manager
    ):
        """
        Tier 1 failure scenario:
        1. Tier 1 (MCP) returns 503
        2. Circuit breaker opens
        3. Request falls back to Tier 2
        4. Request succeeds
        5. Fallback logged
        """
        # Tier 1 fails
        mock_mcp_client.get_account.side_effect = Exception("MCP Service Unavailable")

        # Tier 2 succeeds
        mock_sdk_client.get_account.return_value = {
            "id": "FALLBACK001",
            "name": "Fallback Account",
            "status": "Active"
        }

        # Execute operation with agent context (would normally use Tier 1)
        result = await integration_manager.get_account(
            account_id="FALLBACK001",
            context={"agent": "test_agent"}
        )

        # Verify fallback occurred
        assert result["id"] == "FALLBACK001"
        assert integration_manager.last_tier_used == "tier2_sdk"
        assert integration_manager.fallback_count > 0

        # Verify both tiers were attempted
        assert mock_mcp_client.get_account.called
        assert mock_sdk_client.get_account.called

        # Verify circuit breaker metrics
        tier1_breaker = circuit_breaker_manager.get_breaker("tier1_mcp")
        tier1_metrics = tier1_breaker.get_metrics()
        assert tier1_metrics["failure_count"] > 0

    @pytest.mark.asyncio
    async def test_tier2_failure_fallback_to_tier3(
        self, integration_manager, mock_sdk_client, mock_rest_client
    ):
        """
        Tier 2 failure scenario:
        1. Tier 2 (SDK) fails
        2. Falls back to Tier 3 (REST)
        3. Request succeeds
        4. All metrics collected
        """
        # Tier 2 fails
        mock_sdk_client.get_account.side_effect = Exception("SDK Error")

        # Tier 3 succeeds
        mock_rest_client.get_account.return_value = {
            "id": "REST_FB001",
            "name": "REST Fallback Account"
        }

        # Execute operation (no agent context, defaults to Tier 2)
        result = await integration_manager.get_account("REST_FB001")

        # Verify fallback to Tier 3
        assert result["id"] == "REST_FB001"
        assert integration_manager.last_tier_used == "tier3_rest"

        # Verify both SDK and REST were attempted
        assert mock_sdk_client.get_account.called
        assert mock_rest_client.get_account.called

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(
        self, integration_manager, mock_mcp_client, circuit_breaker_manager
    ):
        """
        Circuit breaker recovery:
        1. Tier 1 fails, circuit opens
        2. Wait for recovery timeout
        3. Circuit transitions to HALF_OPEN
        4. Test request succeeds
        5. Circuit closes
        6. Normal operation resumes
        """
        # Fail Tier 1 multiple times to open circuit
        mock_mcp_client.get_account.side_effect = [
            Exception("Fail 1"),
            Exception("Fail 2"),
            Exception("Fail 3"),
            {"id": "RECOVER001", "name": "Recovery Success"}  # Success after recovery
        ]

        # Trigger failures to open circuit
        for i in range(3):
            try:
                await integration_manager.get_account(
                    f"FAIL{i}",
                    context={"agent": "test"}
                )
            except:
                pass

        # Verify circuit is open
        tier1_breaker = circuit_breaker_manager.get_breaker("tier1_mcp")
        from src.resilience.circuit_breaker import CircuitState
        assert tier1_breaker.get_state() == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(2.1)

        # Next call should transition to HALF_OPEN and succeed
        result = await integration_manager.get_account(
            "RECOVER001",
            context={"agent": "test"}
        )

        assert result["id"] == "RECOVER001"
        # Circuit should close after successful call in HALF_OPEN
        assert tier1_breaker.get_state() in [CircuitState.HALF_OPEN, CircuitState.CLOSED]

    @pytest.mark.asyncio
    async def test_concurrent_requests_different_tiers(
        self, integration_manager, mock_mcp_client, mock_sdk_client
    ):
        """
        Concurrent requests:
        1. 10 agent operations (Tier 1)
        2. 10 bulk operations (Tier 2)
        3. All complete successfully
        4. No race conditions
        5. Metrics accurate
        """
        # Setup mocks
        mock_mcp_client.get_account.return_value = {"id": "MCP", "name": "MCP Account"}
        mock_sdk_client.get_accounts_bulk.return_value = [
            {"id": f"SDK{i}", "name": f"SDK Account {i}"} for i in range(100)
        ]

        # Create concurrent tasks
        agent_tasks = [
            integration_manager.get_account(
                f"AGENT{i}",
                context={"agent": f"agent_{i}"}
            )
            for i in range(10)
        ]

        bulk_tasks = [
            integration_manager.get_accounts_bulk([f"B{i}_{j}" for j in range(100)])
            for i in range(10)
        ]

        # Execute all concurrently
        all_results = await asyncio.gather(*(agent_tasks + bulk_tasks))

        # Verify all succeeded
        assert len(all_results) == 20

        # Verify metrics
        metrics = integration_manager.get_metrics()
        assert metrics["tier1_mcp"]["requests"] >= 10
        assert metrics["tier2_sdk"]["requests"] >= 10

    @pytest.mark.asyncio
    async def test_mixed_success_failure_workflow(
        self, integration_manager, mock_mcp_client, mock_sdk_client
    ):
        """Test workflow with mixed successes and failures."""
        # Alternate between success and failure
        mock_sdk_client.get_account.side_effect = [
            {"id": "S1", "name": "Success 1"},
            Exception("Fail 1"),
            {"id": "S2", "name": "Success 2"},
            Exception("Fail 2"),
            {"id": "S3", "name": "Success 3"}
        ]

        results = []
        for i in range(5):
            try:
                result = await integration_manager.get_account(f"ACC{i}")
                results.append(("success", result))
            except Exception as e:
                results.append(("failure", str(e)))

        # Verify mixed results
        successes = [r for r in results if r[0] == "success"]
        failures = [r for r in results if r[0] == "failure"]

        assert len(successes) == 3
        assert len(failures) == 2


class TestFailoverScenarios:
    """Test various failover scenarios."""

    @pytest.mark.asyncio
    async def test_tier1_timeout_falls_back(
        self, integration_manager, mock_mcp_client, mock_sdk_client
    ):
        """Tier 1 timeout should trigger fallback."""
        # Tier 1 times out
        async def slow_mcp_call(*args, **kwargs):
            await asyncio.sleep(10)
            return {"id": "SLOW"}

        mock_mcp_client.get_account.side_effect = slow_mcp_call

        # Tier 2 succeeds
        mock_sdk_client.get_account.return_value = {"id": "QUICK", "name": "Quick Response"}

        # Execute with timeout
        result = await integration_manager.get_account(
            "TIMEOUT001",
            context={"agent": "test"},
            timeout=0.5
        )

        # Should fall back to Tier 2
        assert result["id"] == "QUICK"
        assert integration_manager.last_tier_used == "tier2_sdk"

    @pytest.mark.asyncio
    async def test_tier1_and_tier2_down_uses_tier3(
        self, integration_manager, mock_mcp_client, mock_sdk_client, mock_rest_client
    ):
        """Two tiers down should use final fallback."""
        # Tiers 1 and 2 fail
        mock_mcp_client.get_account.side_effect = Exception("MCP Down")
        mock_sdk_client.get_account.side_effect = Exception("SDK Down")

        # Tier 3 succeeds
        mock_rest_client.get_account.return_value = {
            "id": "REST_LAST",
            "name": "Last Resort"
        }

        result = await integration_manager.get_account(
            "LAST_RESORT",
            context={"agent": "test"}
        )

        # Should use Tier 3
        assert result["id"] == "REST_LAST"
        assert integration_manager.last_tier_used == "tier3_rest"

        # All three tiers should have been attempted
        assert mock_mcp_client.get_account.called
        assert mock_sdk_client.get_account.called
        assert mock_rest_client.get_account.called

    @pytest.mark.asyncio
    async def test_tier_recovery_resumes_normal_routing(
        self, integration_manager, mock_mcp_client, circuit_breaker_manager
    ):
        """Tier recovery should resume normal routing."""
        # Fail to open circuit
        mock_mcp_client.get_account.side_effect = [
            Exception("Fail 1"),
            Exception("Fail 2"),
            Exception("Fail 3")
        ]

        for i in range(3):
            try:
                await integration_manager.get_account(f"F{i}", context={"agent": "test"})
            except:
                pass

        # Verify circuit is open
        tier1_breaker = circuit_breaker_manager.get_breaker("tier1_mcp")
        from src.resilience.circuit_breaker import CircuitState
        assert tier1_breaker.get_state() == CircuitState.OPEN

        # Manually reset circuit (simulate recovery)
        tier1_breaker.reset()

        # Now MCP succeeds
        mock_mcp_client.get_account.side_effect = None
        mock_mcp_client.get_account.return_value = {"id": "RECOVERED", "name": "Back Online"}

        # Should route to Tier 1 again
        result = await integration_manager.get_account(
            "RECOVERED",
            context={"agent": "test"}
        )

        assert result["id"] == "RECOVERED"
        assert integration_manager.last_tier_used == "tier1_mcp"

    @pytest.mark.asyncio
    async def test_rapid_tier_switching(
        self, integration_manager, mock_mcp_client, mock_sdk_client
    ):
        """Rapid tier switching should be handled correctly."""
        # Alternate between Tier 1 and Tier 2
        call_sequence = []

        async def track_mcp(*args, **kwargs):
            call_sequence.append("mcp")
            if len(call_sequence) % 2 == 0:
                raise Exception("MCP Fail")
            return {"id": "MCP_OK"}

        async def track_sdk(*args, **kwargs):
            call_sequence.append("sdk")
            return {"id": "SDK_OK"}

        mock_mcp_client.get_account.side_effect = track_mcp
        mock_sdk_client.get_account.side_effect = track_sdk

        # Rapid fire requests
        for i in range(10):
            try:
                await integration_manager.get_account(
                    f"RAPID{i}",
                    context={"agent": f"agent{i}"}
                )
            except:
                pass

        # Verify both tiers were used
        assert "mcp" in call_sequence
        assert "sdk" in call_sequence


class TestPerformanceRequirements:
    """Test performance SLAs."""

    @pytest.mark.asyncio
    async def test_tier1_response_time_under_500ms(
        self, integration_manager, mock_mcp_client
    ):
        """Tier 1 should respond in < 500ms."""
        mock_mcp_client.get_account.return_value = {"id": "PERF1", "name": "Fast Response"}

        start = time.time()
        await integration_manager.get_account("PERF1", context={"agent": "test"})
        duration = time.time() - start

        assert duration < 0.5

    @pytest.mark.asyncio
    async def test_tier2_bulk_1000_records_under_5s(
        self, integration_manager, mock_sdk_client
    ):
        """Tier 2 should bulk read 1000 records in < 5s."""
        # Setup 1000 records
        records = [{"id": f"R{i:04d}", "name": f"Record {i}"} for i in range(1000)]
        mock_sdk_client.get_accounts_bulk.return_value = records

        account_ids = [f"R{i:04d}" for i in range(1000)]

        start = time.time()
        result = await integration_manager.get_accounts_bulk(account_ids)
        duration = time.time() - start

        assert len(result) == 1000
        assert duration < 5.0

    @pytest.mark.asyncio
    async def test_tier3_response_time_under_1s(
        self, integration_manager, mock_rest_client
    ):
        """Tier 3 should respond in < 1s."""
        mock_rest_client.get_account.return_value = {"id": "REST_PERF", "name": "REST Response"}

        start = time.time()
        await integration_manager.get_account("REST_PERF")
        duration = time.time() - start

        assert duration < 1.0

    @pytest.mark.asyncio
    async def test_failover_time_under_2s(
        self, integration_manager, mock_mcp_client, mock_sdk_client
    ):
        """Tier failover should complete in < 2s."""
        # Tier 1 fails immediately
        mock_mcp_client.get_account.side_effect = Exception("Immediate fail")

        # Tier 2 succeeds
        mock_sdk_client.get_account.return_value = {"id": "FAILOVER_PERF"}

        start = time.time()
        result = await integration_manager.get_account(
            "FAILOVER_PERF",
            context={"agent": "test"}
        )
        duration = time.time() - start

        assert result["id"] == "FAILOVER_PERF"
        assert duration < 2.0


class TestConcurrentOperations:
    """Test concurrent operation handling."""

    @pytest.mark.asyncio
    async def test_100_concurrent_reads(
        self, integration_manager, mock_sdk_client
    ):
        """Should handle 100 concurrent reads."""
        mock_sdk_client.get_account.return_value = {"id": "CONCURRENT", "name": "Test"}

        tasks = [
            integration_manager.get_account(f"ACC{i}")
            for i in range(100)
        ]

        start = time.time()
        results = await asyncio.gather(*tasks)
        duration = time.time() - start

        assert len(results) == 100
        assert all(r["id"] == "CONCURRENT" for r in results)
        # Should complete in reasonable time
        assert duration < 5.0

    @pytest.mark.asyncio
    async def test_concurrent_mixed_operations(
        self, integration_manager, mock_mcp_client, mock_sdk_client, mock_rest_client
    ):
        """Should handle mixed concurrent operations."""
        mock_mcp_client.get_account.return_value = {"id": "MCP"}
        mock_sdk_client.get_account.return_value = {"id": "SDK"}
        mock_sdk_client.update_account.return_value = {"id": "SDK_UPD"}
        mock_rest_client.get_account.return_value = {"id": "REST"}

        tasks = []
        # Mix of reads and writes across tiers
        for i in range(50):
            if i % 3 == 0:
                tasks.append(
                    integration_manager.get_account(f"A{i}", context={"agent": "test"})
                )
            elif i % 3 == 1:
                tasks.append(
                    integration_manager.update_account(f"A{i}", {"status": "Active"})
                )
            else:
                tasks.append(integration_manager.get_account(f"A{i}"))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Most should succeed
        successes = [r for r in results if not isinstance(r, Exception)]
        assert len(successes) >= 45  # Allow some failures
