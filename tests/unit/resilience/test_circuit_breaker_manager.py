"""Unit tests for circuit breaker manager."""

import pytest
from src.resilience.circuit_breaker_manager import CircuitBreakerManager
from src.resilience.circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreakerManager:
    """Test circuit breaker manager implementation."""

    @pytest.fixture
    def manager(self):
        """Create circuit breaker manager."""
        return CircuitBreakerManager()

    def test_register_breaker(self, manager):
        """Test registering a new circuit breaker."""
        breaker = manager.register_breaker(
            "test_service",
            failure_threshold=5,
            recovery_timeout=30
        )

        assert isinstance(breaker, CircuitBreaker)
        assert breaker.name == "test_service"
        assert breaker.failure_threshold == 5
        assert breaker.recovery_timeout == 30

    def test_register_duplicate_breaker_raises_error(self, manager):
        """Test registering duplicate breaker raises ValueError."""
        manager.register_breaker("test_service")

        with pytest.raises(ValueError, match="already registered"):
            manager.register_breaker("test_service")

    def test_get_breaker(self, manager):
        """Test retrieving registered breaker."""
        registered = manager.register_breaker("test_service")
        retrieved = manager.get_breaker("test_service")

        assert retrieved is registered

    def test_get_nonexistent_breaker_raises_error(self, manager):
        """Test retrieving nonexistent breaker raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            manager.get_breaker("nonexistent")

    def test_get_all_states(self, manager):
        """Test retrieving all breaker states."""
        manager.register_breaker("service1")
        manager.register_breaker("service2")
        manager.register_breaker("service3")

        states = manager.get_all_states()

        assert len(states) == 3
        assert all(state == CircuitState.CLOSED for state in states.values())

    def test_get_all_metrics(self, manager):
        """Test retrieving all breaker metrics."""
        manager.register_breaker("service1")
        manager.register_breaker("service2")

        metrics = manager.get_all_metrics()

        assert len(metrics) == 2
        assert "service1" in metrics
        assert "service2" in metrics
        assert all("state" in m for m in metrics.values())

    def test_reset_all(self, manager):
        """Test resetting all breakers."""
        breaker1 = manager.register_breaker("service1")
        breaker2 = manager.register_breaker("service2")

        # Modify states
        breaker1._failure_count = 5
        breaker2._failure_count = 3

        manager.reset_all()

        assert breaker1._failure_count == 0
        assert breaker2._failure_count == 0

    def test_reset_breaker(self, manager):
        """Test resetting specific breaker."""
        breaker1 = manager.register_breaker("service1")
        breaker2 = manager.register_breaker("service2")

        breaker1._failure_count = 5
        breaker2._failure_count = 3

        manager.reset_breaker("service1")

        assert breaker1._failure_count == 0
        assert breaker2._failure_count == 3  # Unchanged

    def test_reset_nonexistent_breaker_raises_error(self, manager):
        """Test resetting nonexistent breaker raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            manager.reset_breaker("nonexistent")

    def test_unregister_breaker(self, manager):
        """Test unregistering a breaker."""
        manager.register_breaker("test_service")
        assert manager.get_breaker_count() == 1

        manager.unregister_breaker("test_service")
        assert manager.get_breaker_count() == 0

        with pytest.raises(KeyError):
            manager.get_breaker("test_service")

    def test_unregister_nonexistent_breaker_raises_error(self, manager):
        """Test unregistering nonexistent breaker raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            manager.unregister_breaker("nonexistent")

    def test_get_breaker_count(self, manager):
        """Test getting breaker count."""
        assert manager.get_breaker_count() == 0

        manager.register_breaker("service1")
        assert manager.get_breaker_count() == 1

        manager.register_breaker("service2")
        manager.register_breaker("service3")
        assert manager.get_breaker_count() == 3

        manager.unregister_breaker("service2")
        assert manager.get_breaker_count() == 2

    def test_list_breakers(self, manager):
        """Test listing all breaker names."""
        manager.register_breaker("service1")
        manager.register_breaker("service2")
        manager.register_breaker("service3")

        names = manager.list_breakers()

        assert len(names) == 3
        assert "service1" in names
        assert "service2" in names
        assert "service3" in names

    def test_multiple_managers_independent(self):
        """Test multiple managers are independent."""
        manager1 = CircuitBreakerManager()
        manager2 = CircuitBreakerManager()

        manager1.register_breaker("service1")
        manager2.register_breaker("service2")

        assert manager1.get_breaker_count() == 1
        assert manager2.get_breaker_count() == 1
        assert "service1" in manager1.list_breakers()
        assert "service2" in manager2.list_breakers()
