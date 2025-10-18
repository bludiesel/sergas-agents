"""Unit tests for circuit breaker."""

import pytest
import asyncio
from datetime import datetime, timedelta
from src.resilience.circuit_breaker import CircuitBreaker, CircuitState
from src.resilience.exceptions import CircuitBreakerOpenError


class TestCircuitBreaker:
    """Test circuit breaker implementation."""

    @pytest.fixture
    def breaker(self):
        """Create circuit breaker for testing."""
        return CircuitBreaker(
            name="test",
            failure_threshold=3,
            recovery_timeout=2,
            half_open_max_calls=2,
            success_threshold=2
        )

    @pytest.mark.asyncio
    async def test_initial_state_is_closed(self, breaker):
        """Test circuit breaker starts in CLOSED state."""
        assert breaker.get_state() == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_successful_call_in_closed_state(self, breaker):
        """Test successful call in CLOSED state."""
        async def success_func():
            return "success"

        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.get_state() == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failed_call_increments_failure_count(self, breaker):
        """Test failed call increments failure count."""
        async def fail_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            await breaker.call(fail_func)

        metrics = breaker.get_metrics()
        assert metrics["failure_count"] == 1
        assert breaker.get_state() == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold(self, breaker):
        """Test circuit opens after failure threshold exceeded."""
        async def fail_func():
            raise ValueError("test error")

        # Fail 3 times (threshold)
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)

        # Circuit should now be OPEN
        assert breaker.get_state() == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_open_circuit_rejects_calls(self, breaker):
        """Test OPEN circuit rejects calls immediately."""
        async def fail_func():
            raise ValueError("test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)

        # Should reject next call
        async def any_func():
            return "should not execute"

        with pytest.raises(CircuitBreakerOpenError) as exc_info:
            await breaker.call(any_func)

        assert exc_info.value.circuit_name == "test"
        assert exc_info.value.retry_after > 0

    @pytest.mark.asyncio
    async def test_circuit_transitions_to_half_open(self, breaker):
        """Test circuit transitions to HALF_OPEN after timeout."""
        async def fail_func():
            raise ValueError("test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)

        assert breaker.get_state() == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(2.1)

        # Next call should transition to HALF_OPEN
        async def success_func():
            return "success"

        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.get_state() == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_closes_on_success(self, breaker):
        """Test HALF_OPEN circuit closes on success threshold."""
        async def fail_func():
            raise ValueError("test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)

        # Wait for recovery
        await asyncio.sleep(2.1)

        # Succeed twice (success_threshold = 2)
        async def success_func():
            return "success"

        await breaker.call(success_func)
        assert breaker.get_state() == CircuitState.HALF_OPEN

        await breaker.call(success_func)
        assert breaker.get_state() == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_reopens_on_failure(self, breaker):
        """Test HALF_OPEN circuit reopens on any failure."""
        async def fail_func():
            raise ValueError("test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)

        # Wait for recovery
        await asyncio.sleep(2.1)

        # First call succeeds, transitions to HALF_OPEN
        async def success_func():
            return "success"

        await breaker.call(success_func)
        assert breaker.get_state() == CircuitState.HALF_OPEN

        # Second call fails, should reopen
        with pytest.raises(ValueError):
            await breaker.call(fail_func)

        assert breaker.get_state() == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_half_open_max_calls_limit(self, breaker):
        """Test HALF_OPEN state limits concurrent calls."""
        async def fail_func():
            raise ValueError("test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)

        # Wait for recovery
        await asyncio.sleep(2.1)

        async def slow_func():
            await asyncio.sleep(0.1)
            return "success"

        # First call transitions to HALF_OPEN
        task1 = asyncio.create_task(breaker.call(slow_func))
        await asyncio.sleep(0.01)  # Ensure first call started

        # Second call should also be allowed (max_calls = 2)
        task2 = asyncio.create_task(breaker.call(slow_func))
        await asyncio.sleep(0.01)

        # Third call should be rejected
        with pytest.raises(CircuitBreakerOpenError):
            await breaker.call(slow_func)

        # Wait for tasks to complete
        await task1
        await task2

    @pytest.mark.asyncio
    async def test_manual_reset(self, breaker):
        """Test manual circuit reset."""
        async def fail_func():
            raise ValueError("test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)

        assert breaker.get_state() == CircuitState.OPEN

        # Manual reset
        breaker.reset()

        assert breaker.get_state() == CircuitState.CLOSED
        assert breaker.get_metrics()["failure_count"] == 0

    @pytest.mark.asyncio
    async def test_get_metrics(self, breaker):
        """Test metrics collection."""
        async def success_func():
            return "success"

        async def fail_func():
            raise ValueError("test error")

        # Mix of success and failure
        await breaker.call(success_func)
        with pytest.raises(ValueError):
            await breaker.call(fail_func)

        metrics = breaker.get_metrics()

        assert metrics["state"] == "closed"
        assert metrics["failure_count"] == 1
        assert metrics["total_calls"] == 2
        assert metrics["error_rate"] == 0.5
        assert metrics["last_failure_time"] is not None

    @pytest.mark.asyncio
    async def test_error_rate_calculation(self, breaker):
        """Test error rate calculation in sliding window."""
        async def success_func():
            return "success"

        async def fail_func():
            raise ValueError("test error")

        # 3 successes, 2 failures = 40% error rate
        await breaker.call(success_func)
        await breaker.call(success_func)
        with pytest.raises(ValueError):
            await breaker.call(fail_func)
        await breaker.call(success_func)
        with pytest.raises(ValueError):
            await breaker.call(fail_func)

        metrics = breaker.get_metrics()
        assert metrics["error_rate"] == pytest.approx(0.4)

    @pytest.mark.asyncio
    async def test_time_until_retry(self, breaker):
        """Test time_until_retry metric when circuit is open."""
        async def fail_func():
            raise ValueError("test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)

        metrics = breaker.get_metrics()
        assert metrics["time_until_retry"] is not None
        assert 0 <= metrics["time_until_retry"] <= 2

    @pytest.mark.asyncio
    async def test_success_resets_failure_count_in_closed(self, breaker):
        """Test success resets failure count in CLOSED state."""
        async def success_func():
            return "success"

        async def fail_func():
            raise ValueError("test error")

        # Some failures
        with pytest.raises(ValueError):
            await breaker.call(fail_func)
        with pytest.raises(ValueError):
            await breaker.call(fail_func)

        assert breaker.get_metrics()["failure_count"] == 2

        # Success should reset
        await breaker.call(success_func)

        assert breaker.get_metrics()["failure_count"] == 0

    @pytest.mark.asyncio
    async def test_concurrent_calls_thread_safety(self, breaker):
        """Test thread safety with concurrent calls."""
        call_count = [0]

        async def counted_func():
            call_count[0] += 1
            await asyncio.sleep(0.01)
            return call_count[0]

        # Execute 10 concurrent calls
        tasks = [breaker.call(counted_func) for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All calls should succeed
        assert len(results) == 10
        assert call_count[0] == 10

    @pytest.mark.asyncio
    async def test_sliding_window_max_length(self, breaker):
        """Test call history sliding window has max length."""
        async def success_func():
            return "success"

        # Make 150 calls (window size is 100)
        for _ in range(150):
            await breaker.call(success_func)

        metrics = breaker.get_metrics()
        # Should only track last 100
        assert metrics["total_calls"] == 100

    @pytest.mark.asyncio
    async def test_custom_configuration(self):
        """Test circuit breaker with custom configuration."""
        breaker = CircuitBreaker(
            name="custom",
            failure_threshold=10,
            recovery_timeout=5,
            half_open_max_calls=5,
            success_threshold=3
        )

        async def fail_func():
            raise ValueError("test error")

        # Should require 10 failures to open
        for i in range(9):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)
            assert breaker.get_state() == CircuitState.CLOSED

        # 10th failure opens it
        with pytest.raises(ValueError):
            await breaker.call(fail_func)
        assert breaker.get_state() == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_call_history_tracks_timestamps(self, breaker):
        """Test call history includes timestamps."""
        async def success_func():
            return "success"

        await breaker.call(success_func)

        # Access internal state for verification
        assert len(breaker._call_history) == 1
        call_type, timestamp = breaker._call_history[0]
        assert call_type == "success"
        assert isinstance(timestamp, datetime)
