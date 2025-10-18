"""Unit tests for fallback handler."""

import pytest
import asyncio
from src.resilience.fallback_handler import FallbackHandler
from src.resilience.circuit_breaker_manager import CircuitBreakerManager
from src.resilience.circuit_breaker import CircuitState
from src.resilience.exceptions import AllTiersFailedError, CircuitBreakerOpenError


class TestFallbackHandler:
    """Test fallback handler implementation."""

    @pytest.fixture
    def cb_manager(self):
        """Create circuit breaker manager."""
        manager = CircuitBreakerManager()
        manager.register_breaker("tier1_mcp", failure_threshold=3)
        manager.register_breaker("tier2_sdk", failure_threshold=3)
        manager.register_breaker("tier3_rest", failure_threshold=3)
        return manager

    @pytest.fixture
    def handler(self, cb_manager):
        """Create fallback handler."""
        return FallbackHandler(cb_manager)

    @pytest.mark.asyncio
    async def test_primary_success(self, handler):
        """Test successful primary tier execution."""
        async def primary():
            return "primary_result"

        async def secondary():
            pytest.fail("Secondary should not be called")

        async def tertiary():
            pytest.fail("Tertiary should not be called")

        result = await handler.execute_with_fallback(
            primary, secondary, tertiary, "test_operation"
        )

        assert result == "primary_result"

    @pytest.mark.asyncio
    async def test_fallback_to_secondary(self, handler):
        """Test fallback to secondary tier on primary failure."""
        async def primary():
            raise ValueError("primary failed")

        async def secondary():
            return "secondary_result"

        async def tertiary():
            pytest.fail("Tertiary should not be called")

        result = await handler.execute_with_fallback(
            primary, secondary, tertiary, "test_operation"
        )

        assert result == "secondary_result"

    @pytest.mark.asyncio
    async def test_fallback_to_tertiary(self, handler):
        """Test fallback to tertiary tier on primary and secondary failure."""
        async def primary():
            raise ValueError("primary failed")

        async def secondary():
            raise ValueError("secondary failed")

        async def tertiary():
            return "tertiary_result"

        result = await handler.execute_with_fallback(
            primary, secondary, tertiary, "test_operation"
        )

        assert result == "tertiary_result"

    @pytest.mark.asyncio
    async def test_all_tiers_failed(self, handler):
        """Test exception when all tiers fail."""
        async def primary():
            raise ValueError("primary failed")

        async def secondary():
            raise ValueError("secondary failed")

        async def tertiary():
            raise ValueError("tertiary failed")

        with pytest.raises(AllTiersFailedError) as exc_info:
            await handler.execute_with_fallback(
                primary, secondary, tertiary, "test_operation"
            )

        assert exc_info.value.attempted_tiers == ["primary", "secondary", "tertiary"]

    @pytest.mark.asyncio
    async def test_skip_tier_with_open_circuit(self, handler, cb_manager):
        """Test skipping tier when circuit is open."""
        # Open primary circuit
        primary_breaker = cb_manager.get_breaker("tier1_mcp")
        for _ in range(3):
            try:
                await primary_breaker.call(self._failing_func)
            except ValueError:
                pass

        assert primary_breaker.get_state() == CircuitState.OPEN

        primary_called = [False]
        secondary_called = [False]

        async def primary():
            primary_called[0] = True
            return "primary_result"

        async def secondary():
            secondary_called[0] = True
            return "secondary_result"

        async def tertiary():
            pytest.fail("Tertiary should not be called")

        result = await handler.execute_with_fallback(
            primary, secondary, tertiary, "test_operation"
        )

        # Primary should be skipped, secondary should succeed
        assert not primary_called[0]
        assert secondary_called[0]
        assert result == "secondary_result"

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, handler, cb_manager):
        """Test circuit breaker integration with fallback."""
        async def primary():
            breaker = cb_manager.get_breaker("tier1_mcp")
            return await breaker.call(self._success_func)

        async def secondary():
            breaker = cb_manager.get_breaker("tier2_sdk")
            return await breaker.call(self._success_func)

        async def tertiary():
            pytest.fail("Tertiary should not be called")

        result = await handler.execute_with_fallback(
            primary, secondary, tertiary, "test_operation"
        )

        assert result == "success"

    @pytest.mark.asyncio
    async def test_should_skip_tier_no_breaker(self, handler):
        """Test should_skip_tier returns False when breaker not registered."""
        # Try to check unregistered tier
        should_skip = handler._should_skip_tier("nonexistent_tier")
        assert should_skip is False

    @pytest.mark.asyncio
    async def test_custom_tier_names(self, handler, cb_manager):
        """Test fallback with custom tier names."""
        # Register custom tiers
        cb_manager.register_breaker("custom_tier1")
        cb_manager.register_breaker("custom_tier2")
        cb_manager.register_breaker("custom_tier3")

        async def primary():
            raise ValueError("failed")

        async def secondary():
            return "secondary_result"

        async def tertiary():
            pytest.fail("Should not be called")

        result = await handler.execute_with_fallback(
            primary, secondary, tertiary,
            "test_operation",
            primary_tier="custom_tier1",
            secondary_tier="custom_tier2",
            tertiary_tier="custom_tier3"
        )

        assert result == "secondary_result"

    @pytest.mark.asyncio
    async def test_custom_fallback_sequence(self, handler, cb_manager):
        """Test execute_with_custom_fallback."""
        cb_manager.register_breaker("custom1")
        cb_manager.register_breaker("custom2")

        async def func1():
            raise ValueError("func1 failed")

        async def func2():
            return "func2_result"

        operations = [
            (func1, "custom1", "first"),
            (func2, "custom2", "second")
        ]

        result = await handler.execute_with_custom_fallback(
            operations, "custom_operation"
        )

        assert result == "func2_result"

    # Helper methods
    async def _failing_func(self):
        """Helper function that always fails."""
        raise ValueError("intentional failure")

    async def _success_func(self):
        """Helper function that always succeeds."""
        return "success"
