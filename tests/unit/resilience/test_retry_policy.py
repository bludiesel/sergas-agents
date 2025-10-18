"""Unit tests for retry policy."""

import pytest
import asyncio
from src.resilience.retry_policy import RetryPolicy
from src.resilience.exceptions import RetryExhaustedError


class TestRetryPolicy:
    """Test retry policy implementation."""

    @pytest.fixture
    def policy(self):
        """Create retry policy for testing."""
        return RetryPolicy(
            max_attempts=3,
            base_delay=0.1,
            max_delay=1.0,
            exponential_base=2.0,
            jitter=False  # Disable for deterministic tests
        )

    @pytest.mark.asyncio
    async def test_successful_first_attempt(self, policy):
        """Test successful execution on first attempt."""
        async def success_func():
            return "success"

        result = await policy.execute(success_func)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, policy):
        """Test retry on transient failure."""
        attempt_count = [0]

        async def fail_then_succeed():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ValueError("transient error")
            return "success"

        result = await policy.execute(fail_then_succeed)
        assert result == "success"
        assert attempt_count[0] == 2

    @pytest.mark.asyncio
    async def test_max_attempts_exhausted(self, policy):
        """Test retry exhausted after max attempts."""
        attempt_count = [0]

        async def always_fail():
            attempt_count[0] += 1
            raise ValueError("permanent error")

        with pytest.raises(RetryExhaustedError) as exc_info:
            await policy.execute(always_fail)

        assert exc_info.value.attempts == 3
        assert isinstance(exc_info.value.last_error, ValueError)
        assert attempt_count[0] == 3

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff delay calculation."""
        policy = RetryPolicy(
            max_attempts=4,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=False
        )

        # Test delay calculation
        delays = [
            policy._calculate_delay(0),  # 1.0 * 2^0 = 1.0
            policy._calculate_delay(1),  # 1.0 * 2^1 = 2.0
            policy._calculate_delay(2),  # 1.0 * 2^2 = 4.0
            policy._calculate_delay(3),  # 1.0 * 2^3 = 8.0
        ]

        assert delays == [1.0, 2.0, 4.0, 8.0]

    @pytest.mark.asyncio
    async def test_max_delay_cap(self):
        """Test delay is capped at max_delay."""
        policy = RetryPolicy(
            max_attempts=10,
            base_delay=1.0,
            max_delay=5.0,
            exponential_base=2.0,
            jitter=False
        )

        # Large attempt number should be capped
        delay = policy._calculate_delay(10)  # 1.0 * 2^10 = 1024, capped at 5.0
        assert delay == 5.0

    @pytest.mark.asyncio
    async def test_jitter_adds_randomness(self):
        """Test jitter adds randomness to delay."""
        policy = RetryPolicy(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=True
        )

        # Calculate multiple delays, they should vary
        delays = [policy._calculate_delay(1) for _ in range(10)]

        # All delays should be between 0.5 and 1.5 times base calculation (2.0)
        for delay in delays:
            assert 1.0 <= delay <= 3.0  # 2.0 * 0.5 to 2.0 * 1.5

        # Not all delays should be exactly the same (randomness check)
        assert len(set(delays)) > 1

    @pytest.mark.asyncio
    async def test_timing_of_retries(self):
        """Test actual timing of retry delays."""
        import time

        policy = RetryPolicy(
            max_attempts=3,
            base_delay=0.05,  # 50ms
            max_delay=1.0,
            exponential_base=2.0,
            jitter=False
        )

        attempt_times = []

        async def fail_with_timing():
            attempt_times.append(time.time())
            raise ValueError("error")

        with pytest.raises(RetryExhaustedError):
            await policy.execute(fail_with_timing)

        # Check delays between attempts
        # First retry: ~50ms, Second retry: ~100ms
        if len(attempt_times) >= 2:
            delay1 = attempt_times[1] - attempt_times[0]
            assert 0.04 <= delay1 <= 0.15  # Allow some variance

        if len(attempt_times) >= 3:
            delay2 = attempt_times[2] - attempt_times[1]
            assert 0.08 <= delay2 <= 0.20

    @pytest.mark.asyncio
    async def test_configuration_validation(self):
        """Test configuration parameter validation."""
        # max_attempts < 1
        with pytest.raises(ValueError):
            RetryPolicy(max_attempts=0)

        # base_delay <= 0
        with pytest.raises(ValueError):
            RetryPolicy(base_delay=0)

        # max_delay < base_delay
        with pytest.raises(ValueError):
            RetryPolicy(base_delay=10.0, max_delay=5.0)

        # exponential_base <= 1
        with pytest.raises(ValueError):
            RetryPolicy(exponential_base=1.0)

    @pytest.mark.asyncio
    async def test_get_config(self, policy):
        """Test configuration retrieval."""
        config = policy.get_config()

        assert config["max_attempts"] == 3
        assert config["base_delay"] == 0.1
        assert config["max_delay"] == 1.0
        assert config["exponential_base"] == 2.0
        assert config["jitter"] is False

    @pytest.mark.asyncio
    async def test_preserves_exception_type(self, policy):
        """Test that original exception type is preserved."""
        class CustomError(Exception):
            pass

        async def custom_fail():
            raise CustomError("custom error")

        with pytest.raises(RetryExhaustedError) as exc_info:
            await policy.execute(custom_fail)

        assert isinstance(exc_info.value.last_error, CustomError)

    @pytest.mark.asyncio
    async def test_function_with_arguments(self, policy):
        """Test retry with function arguments."""
        attempt_count = [0]

        async def func_with_args(x, y, multiplier=1):
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ValueError("error")
            return (x + y) * multiplier

        result = await policy.execute(func_with_args, 10, 20, multiplier=2)
        assert result == 60
        assert attempt_count[0] == 2
