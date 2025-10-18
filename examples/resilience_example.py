"""
Example usage of the resilience module for Sergas Super Account Manager.

Demonstrates circuit breaker, retry policy, and tier fallback patterns.
"""

import asyncio
from src.resilience import (
    CircuitBreaker,
    CircuitBreakerManager,
    RetryPolicy,
    FallbackHandler,
    HealthMonitor,
    CircuitBreakerOpenError,
    AllTiersFailedError
)


# ========================================
# Example 1: Basic Circuit Breaker
# ========================================

async def example_basic_circuit_breaker():
    """Basic circuit breaker usage."""
    print("\n=== Example 1: Basic Circuit Breaker ===\n")
    
    # Create circuit breaker
    breaker = CircuitBreaker(
        name="zoho_api",
        failure_threshold=3,
        recovery_timeout=5
    )
    
    # Simulate API calls
    call_count = [0]
    
    async def api_call():
        call_count[0] += 1
        print(f"API call #{call_count[0]}")
        
        # Fail first 3 calls
        if call_count[0] <= 3:
            raise ValueError("API error")
        return "Success"
    
    # Make calls
    for i in range(5):
        try:
            result = await breaker.call(api_call)
            print(f"Call {i+1}: {result}")
        except (ValueError, CircuitBreakerOpenError) as e:
            print(f"Call {i+1}: {type(e).__name__}: {e}")
        
        # Check state
        state = breaker.get_state()
        print(f"Circuit state: {state.value}\n")
        
        await asyncio.sleep(0.5)


# ========================================
# Example 2: Retry Policy
# ========================================

async def example_retry_policy():
    """Retry policy with exponential backoff."""
    print("\n=== Example 2: Retry Policy ===\n")
    
    retry = RetryPolicy(
        max_attempts=3,
        base_delay=0.5,
        exponential_base=2.0,
        jitter=False  # Disable for predictable example
    )
    
    attempt_count = [0]
    
    async def flaky_operation():
        attempt_count[0] += 1
        print(f"Attempt #{attempt_count[0]}")
        
        # Succeed on 3rd attempt
        if attempt_count[0] < 3:
            raise ValueError("Transient error")
        return "Success after retries"
    
    try:
        result = await retry.execute(flaky_operation)
        print(f"\nResult: {result}")
    except Exception as e:
        print(f"\nFailed: {e}")


# ========================================
# Example 3: Multi-Tier Fallback
# ========================================

async def example_tier_fallback():
    """Multi-tier fallback with circuit breakers."""
    print("\n=== Example 3: Multi-Tier Fallback ===\n")
    
    # Setup circuit breakers
    manager = CircuitBreakerManager()
    manager.register_breaker("tier1_mcp", failure_threshold=2)
    manager.register_breaker("tier2_sdk", failure_threshold=2)
    manager.register_breaker("tier3_rest", failure_threshold=2)
    
    handler = FallbackHandler(manager)
    
    # Tier functions
    async def tier1_mcp():
        print("Tier 1 (MCP): Attempting...")
        raise ValueError("MCP unavailable")
    
    async def tier2_sdk():
        print("Tier 2 (SDK): Attempting...")
        return "Success from SDK"
    
    async def tier3_rest():
        print("Tier 3 (REST): Attempting...")
        return "Success from REST"
    
    # Execute with fallback
    try:
        result = await handler.execute_with_fallback(
            tier1_mcp,
            tier2_sdk,
            tier3_rest,
            "get_account"
        )
        print(f"\nResult: {result}")
    except AllTiersFailedError as e:
        print(f"\nAll tiers failed: {e.attempted_tiers}")


# ========================================
# Example 4: Complete Resilience Stack
# ========================================

async def example_complete_stack():
    """Complete resilience stack with all components."""
    print("\n=== Example 4: Complete Resilience Stack ===\n")
    
    # Setup
    manager = CircuitBreakerManager()
    manager.register_breaker("primary", failure_threshold=2, recovery_timeout=3)
    manager.register_breaker("secondary", failure_threshold=2, recovery_timeout=3)
    
    handler = FallbackHandler(manager)
    retry = RetryPolicy(max_attempts=2, base_delay=0.3, jitter=False)
    
    # Simulate services
    primary_calls = [0]
    secondary_calls = [0]
    
    async def primary_service():
        primary_calls[0] += 1
        print(f"Primary service call #{primary_calls[0]}")
        raise ValueError("Primary down")
    
    async def secondary_service():
        secondary_calls[0] += 1
        print(f"Secondary service call #{secondary_calls[0]}")
        
        # Succeed on 2nd call
        if secondary_calls[0] < 2:
            raise ValueError("Secondary transient error")
        return "Success from secondary"
    
    # Wrap in circuit breakers
    async def primary_with_circuit():
        breaker = manager.get_breaker("primary")
        return await breaker.call(primary_service)
    
    async def secondary_with_circuit():
        breaker = manager.get_breaker("secondary")
        return await retry.execute(lambda: breaker.call(secondary_service))
    
    async def tertiary():
        return "Fallback result"
    
    # Execute
    try:
        result = await handler.execute_with_fallback(
            primary_with_circuit,
            secondary_with_circuit,
            tertiary,
            "complex_operation"
        )
        print(f"\nFinal result: {result}")
        
        # Show metrics
        print("\nCircuit Metrics:")
        for name, metrics in manager.get_all_metrics().items():
            print(f"  {name}: {metrics['state']} "
                  f"(failures: {metrics['failure_count']}, "
                  f"error_rate: {metrics['error_rate']:.1%})")
    
    except Exception as e:
        print(f"\nFailed: {e}")


# ========================================
# Example 5: Health Monitoring
# ========================================

class MockClient:
    """Mock client for health monitoring example."""
    def __init__(self, name, healthy=True):
        self.name = name
        self.healthy = healthy
        self.ping = lambda: healthy


async def example_health_monitoring():
    """Health monitoring example."""
    print("\n=== Example 5: Health Monitoring ===\n")
    
    # Create mock clients
    mcp_client = MockClient("MCP", healthy=True)
    sdk_client = MockClient("SDK", healthy=True)
    rest_client = MockClient("REST", healthy=False)
    
    # Create health monitor
    monitor = HealthMonitor(
        mcp_client=mcp_client,
        sdk_client=sdk_client,
        rest_client=rest_client,
        check_interval=1
    )
    
    # Manual health check
    print("Performing health check...")
    status = await monitor.check_all_tiers()
    
    for tier, healthy in status.items():
        print(f"  {tier}: {'✓ Healthy' if healthy else '✗ Unhealthy'}")
    
    # Get health status
    health_info = monitor.get_health_status()
    print(f"\nAll tiers healthy: {health_info['all_healthy']}")
    
    # Background monitoring (commented out to avoid long running)
    # await monitor.start_monitoring()
    # await asyncio.sleep(3)
    # await monitor.stop_monitoring()


# ========================================
# Example 6: Circuit Recovery
# ========================================

async def example_circuit_recovery():
    """Demonstrate circuit recovery flow."""
    print("\n=== Example 6: Circuit Recovery ===\n")
    
    breaker = CircuitBreaker(
        name="recovery_demo",
        failure_threshold=2,
        recovery_timeout=2,
        success_threshold=2
    )
    
    fail_count = [0]
    
    async def toggling_service():
        fail_count[0] += 1
        
        # Fail first 2 calls (open circuit)
        if fail_count[0] <= 2:
            print(f"Call {fail_count[0]}: Failing")
            raise ValueError("Service down")
        
        # Succeed afterward
        print(f"Call {fail_count[0]}: Success")
        return "Service recovered"
    
    # Phase 1: Open the circuit
    print("Phase 1: Opening circuit...")
    for i in range(2):
        try:
            await breaker.call(toggling_service)
        except ValueError:
            pass
    
    print(f"Circuit state: {breaker.get_state().value}\n")
    
    # Phase 2: Circuit is open
    print("Phase 2: Circuit open, requests fail fast...")
    try:
        await breaker.call(toggling_service)
    except CircuitBreakerOpenError as e:
        print(f"Rejected: {e}")
    
    print(f"Circuit state: {breaker.get_state().value}\n")
    
    # Phase 3: Wait for recovery timeout
    print("Phase 3: Waiting for recovery timeout (2s)...")
    await asyncio.sleep(2.1)
    
    # Phase 4: Half-open state
    print("\nPhase 4: Testing recovery (half-open)...")
    await breaker.call(toggling_service)
    print(f"Circuit state: {breaker.get_state().value}\n")
    
    # Phase 5: Close circuit
    print("Phase 5: Second success, closing circuit...")
    await breaker.call(toggling_service)
    print(f"Circuit state: {breaker.get_state().value}")


# ========================================
# Main
# ========================================

async def main():
    """Run all examples."""
    print("=" * 60)
    print("Resilience Module Examples")
    print("=" * 60)
    
    await example_basic_circuit_breaker()
    await example_retry_policy()
    await example_tier_fallback()
    await example_complete_stack()
    await example_health_monitoring()
    await example_circuit_recovery()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
