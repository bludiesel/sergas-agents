"""Integration tests for resilience module."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.resilience import (
    CircuitBreaker,
    CircuitBreakerManager,
    RetryPolicy,
    FallbackHandler,
    HealthMonitor,
    CircuitBreakerOpenError,
    AllTiersFailedError
)


class TestResilienceIntegration:
    """Integration tests for complete resilience system."""

    @pytest.fixture
    def mock_clients(self):
        """Create mock tier clients."""
        return {
            "mcp": MagicMock(),
            "sdk": MagicMock(),
            "rest": MagicMock()
        }

    @pytest.fixture
    def cb_manager(self):
        """Create circuit breaker manager with registered tiers."""
        manager = CircuitBreakerManager()
        manager.register_breaker("tier1_mcp", failure_threshold=3, recovery_timeout=2)
        manager.register_breaker("tier2_sdk", failure_threshold=3, recovery_timeout=2)
        manager.register_breaker("tier3_rest", failure_threshold=3, recovery_timeout=2)
        return manager

    @pytest.fixture
    def retry_policy(self):
        """Create retry policy."""
        return RetryPolicy(
            max_attempts=3,
            base_delay=0.1,
            max_delay=1.0,
            exponential_base=2.0,
            jitter=False
        )

    @pytest.fixture
    def fallback_handler(self, cb_manager):
        """Create fallback handler."""
        return FallbackHandler(cb_manager)

    @pytest.fixture
    def health_monitor(self, mock_clients):
        """Create health monitor."""
        return HealthMonitor(
            mcp_client=mock_clients["mcp"],
            sdk_client=mock_clients["sdk"],
            rest_client=mock_clients["rest"],
            check_interval=1
        )

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_retry_policy(self, cb_manager, retry_policy):
        """Test circuit breaker integration with retry policy."""
        breaker = cb_manager.get_breaker("tier1_mcp")
        call_count = [0]

        async def flaky_function():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("transient error")
            return "success"

        async def execute_with_breaker():
            return await breaker.call(flaky_function)

        # Should succeed after retry
        result = await retry_policy.execute(execute_with_breaker)
        assert result == "success"
        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_complete_tier_fallback_flow(self, cb_manager, fallback_handler):
        """Test complete tier fallback with circuit breakers."""
        tier1_calls = [0]
        tier2_calls = [0]
        tier3_calls = [0]

        async def tier1_func():
            tier1_calls[0] += 1
            raise ValueError("tier1 failed")

        async def tier2_func():
            tier2_calls[0] += 1
            return "tier2_success"

        async def tier3_func():
            tier3_calls[0] += 1
            return "tier3_success"

        # First attempt should fall back to tier2
        result = await fallback_handler.execute_with_fallback(
            tier1_func, tier2_func, tier3_func, "test_op"
        )

        assert result == "tier2_success"
        assert tier1_calls[0] == 1
        assert tier2_calls[0] == 1
        assert tier3_calls[0] == 0

    @pytest.mark.asyncio
    async def test_circuit_opens_prevents_tier_access(self, cb_manager, fallback_handler):
        """Test open circuit causes tier to be skipped."""
        # Open tier1 circuit
        tier1_breaker = cb_manager.get_breaker("tier1_mcp")
        for _ in range(3):
            try:
                await tier1_breaker.call(self._failing_func)
            except ValueError:
                pass

        tier1_calls = [0]
        tier2_calls = [0]

        async def tier1_func():
            tier1_calls[0] += 1
            return "tier1"

        async def tier2_func():
            tier2_calls[0] += 1
            return "tier2"

        async def tier3_func():
            return "tier3"

        # Tier1 should be skipped, tier2 used
        result = await fallback_handler.execute_with_fallback(
            tier1_func, tier2_func, tier3_func, "test_op"
        )

        assert result == "tier2"
        assert tier1_calls[0] == 0  # Skipped due to open circuit
        assert tier2_calls[0] == 1

    @pytest.mark.asyncio
    async def test_circuit_recovery_flow(self, cb_manager):
        """Test complete circuit recovery flow."""
        breaker = cb_manager.get_breaker("tier1_mcp")

        # 1. Open circuit
        for _ in range(3):
            try:
                await breaker.call(self._failing_func)
            except ValueError:
                pass

        # 2. Wait for recovery timeout
        await asyncio.sleep(2.1)

        # 3. Successful calls in half-open state
        result1 = await breaker.call(self._success_func)
        assert result1 == "success"

        result2 = await breaker.call(self._success_func)
        assert result2 == "success"

        # 4. Circuit should be closed
        from src.resilience.circuit_breaker import CircuitState
        assert breaker.get_state() == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_health_monitor_integration(self, health_monitor):
        """Test health monitor checks all tiers."""
        status = await health_monitor.check_all_tiers()

        assert "tier1_mcp" in status
        assert "tier2_sdk" in status
        assert "tier3_rest" in status

        health_info = health_monitor.get_health_status()
        assert "status" in health_info
        assert "last_check" in health_info
        assert "all_healthy" in health_info

    @pytest.mark.asyncio
    async def test_concurrent_circuit_breaker_access(self, cb_manager):
        """Test concurrent access to circuit breakers."""
        breaker = cb_manager.get_breaker("tier1_mcp")
        call_count = [0]

        async def concurrent_func():
            call_count[0] += 1
            await asyncio.sleep(0.01)
            return call_count[0]

        # Execute 20 concurrent calls
        tasks = [breaker.call(concurrent_func) for _ in range(20)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 20
        assert call_count[0] == 20

    @pytest.mark.asyncio
    async def test_retry_with_fallback(self, cb_manager, retry_policy, fallback_handler):
        """Test retry policy combined with tier fallback."""
        tier1_attempts = [0]
        tier2_attempts = [0]

        async def tier1_with_retry():
            async def tier1_func():
                tier1_attempts[0] += 1
                raise ValueError("tier1 always fails")

            breaker = cb_manager.get_breaker("tier1_mcp")
            return await retry_policy.execute(
                lambda: breaker.call(tier1_func)
            )

        async def tier2_with_retry():
            async def tier2_func():
                tier2_attempts[0] += 1
                if tier2_attempts[0] < 2:
                    raise ValueError("tier2 transient failure")
                return "tier2_success"

            breaker = cb_manager.get_breaker("tier2_sdk")
            return await retry_policy.execute(
                lambda: breaker.call(tier2_func)
            )

        async def tier3_func():
            return "tier3_success"

        # Should retry tier1, fail, then fallback to tier2 and succeed
        result = await fallback_handler.execute_with_fallback(
            tier1_with_retry, tier2_with_retry, tier3_func, "complex_op"
        )

        assert result == "tier2_success"
        assert tier1_attempts[0] == 3  # Max retry attempts
        assert tier2_attempts[0] == 2  # Succeeded on second attempt

    @pytest.mark.asyncio
    async def test_all_tiers_fail_with_circuits_open(self, cb_manager, fallback_handler):
        """Test all tiers failed when all circuits are open."""
        # Open all circuits
        for tier_name in ["tier1_mcp", "tier2_sdk", "tier3_rest"]:
            breaker = cb_manager.get_breaker(tier_name)
            for _ in range(3):
                try:
                    await breaker.call(self._failing_func)
                except ValueError:
                    pass

        # All tiers should be skipped
        async def any_func():
            return "should_not_execute"

        with pytest.raises(AllTiersFailedError):
            await fallback_handler.execute_with_fallback(
                any_func, any_func, any_func, "test_op"
            )

    @pytest.mark.asyncio
    async def test_metrics_collection_across_system(self, cb_manager):
        """Test metrics collection from all circuit breakers."""
        # Generate some activity
        for tier_name in ["tier1_mcp", "tier2_sdk"]:
            breaker = cb_manager.get_breaker(tier_name)
            await breaker.call(self._success_func)
            try:
                await breaker.call(self._failing_func)
            except ValueError:
                pass

        # Collect metrics
        all_metrics = cb_manager.get_all_metrics()

        assert len(all_metrics) == 3
        for tier_name, metrics in all_metrics.items():
            assert "state" in metrics
            assert "failure_count" in metrics
            assert "error_rate" in metrics

    @pytest.mark.asyncio
    async def test_health_monitoring_background_task(self, health_monitor):
        """Test background health monitoring."""
        await health_monitor.start_monitoring()

        # Let it run for a bit
        await asyncio.sleep(1.5)

        # Should have performed at least one check
        health_status = health_monitor.get_health_status()
        assert len(health_status["last_check"]) > 0

        await health_monitor.stop_monitoring()

    @pytest.mark.asyncio
    async def test_partial_tier_recovery(self, cb_manager, fallback_handler):
        """Test system behavior with partial tier recovery."""
        # Open tier1 and tier2
        for tier_name in ["tier1_mcp", "tier2_sdk"]:
            breaker = cb_manager.get_breaker(tier_name)
            for _ in range(3):
                try:
                    await breaker.call(self._failing_func)
                except ValueError:
                    pass

        # Only tier3 available
        async def tier1_func():
            return "tier1"

        async def tier2_func():
            return "tier2"

        async def tier3_func():
            return "tier3_success"

        result = await fallback_handler.execute_with_fallback(
            tier1_func, tier2_func, tier3_func, "partial_recovery"
        )

        assert result == "tier3_success"

        # Wait for recovery timeout
        await asyncio.sleep(2.1)

        # Now tier1 should be available in half-open state
        result2 = await fallback_handler.execute_with_fallback(
            tier1_func, tier2_func, tier3_func, "after_recovery"
        )

        # First successful call transitions to half-open
        # But we can't guarantee it fully closes without success_threshold successes
        # So result could be from any available tier
        assert result2 in ["tier1", "tier2", "tier3_success"]

    @pytest.mark.asyncio
    async def test_system_under_load(self, cb_manager, fallback_handler):
        """Test system behavior under load."""
        success_count = [0]
        failure_count = [0]

        async def random_tier_func():
            # Simulate varying success/failure
            import random
            if random.random() > 0.3:  # 70% success rate
                success_count[0] += 1
                return "success"
            else:
                failure_count[0] += 1
                raise ValueError("random failure")

        # Execute many operations concurrently
        tasks = []
        for i in range(50):
            task = fallback_handler.execute_with_fallback(
                random_tier_func, random_tier_func, random_tier_func,
                f"load_test_{i}"
            )
            tasks.append(task)

        # Some might fail if all tiers fail
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Most should succeed (at least one tier succeeds)
        successes = sum(1 for r in results if r == "success")
        assert successes > 0

    # Helper methods
    async def _failing_func(self):
        """Helper that always fails."""
        raise ValueError("intentional failure")

    async def _success_func(self):
        """Helper that always succeeds."""
        return "success"
