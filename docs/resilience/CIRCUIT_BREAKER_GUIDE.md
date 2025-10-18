# Circuit Breaker Pattern Guide

## Overview

The Circuit Breaker Pattern prevents cascade failures by monitoring service health and automatically opening the circuit when error thresholds are exceeded. This guide covers implementation, configuration, and best practices for the Sergas Super Account Manager.

## Circuit Breaker States

```
┌─────────────────────────────────────────┐
│  Circuit Breaker State Machine          │
│                                         │
│  CLOSED ──[failures ≥ threshold]──→ OPEN│
│    ↑                                 │  │
│    │                                 ↓  │
│    │                          [timeout] │
│    │                                 │  │
│    │                                 ↓  │
│    └──[successes ≥ threshold]← HALF_OPEN│
│                                         │
└─────────────────────────────────────────┘
```

### State Behaviors

1. **CLOSED** (Normal Operation)
   - All requests pass through
   - Failures are counted
   - Opens when failure_threshold exceeded

2. **OPEN** (Circuit Tripped)
   - Requests fail immediately
   - No backend calls made
   - Transitions to HALF_OPEN after recovery_timeout

3. **HALF_OPEN** (Testing Recovery)
   - Limited requests allowed through
   - Success → CLOSED (after success_threshold met)
   - Failure → OPEN (any failure reopens)

## Quick Start

### Basic Usage

```python
from src.resilience import CircuitBreaker

# Create circuit breaker
breaker = CircuitBreaker(
    name="zoho_mcp",
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=60,      # Wait 60s before testing recovery
    half_open_max_calls=3,    # Allow 3 calls in half-open
    success_threshold=2       # Close after 2 successes
)

# Use circuit breaker
async def fetch_account(account_id):
    async def operation():
        # Your Zoho API call here
        return await zoho_client.get_account(account_id)

    return await breaker.call(operation)
```

### Multi-Tier Configuration

```python
from src.resilience import CircuitBreakerManager, FallbackHandler

# Create manager
manager = CircuitBreakerManager()

# Register tier circuit breakers
manager.register_breaker(
    "tier1_mcp",
    failure_threshold=5,
    recovery_timeout=60
)

manager.register_breaker(
    "tier2_sdk",
    failure_threshold=5,
    recovery_timeout=60
)

manager.register_breaker(
    "tier3_rest",
    failure_threshold=5,
    recovery_timeout=60
)

# Create fallback handler
handler = FallbackHandler(manager)

# Execute with automatic tier fallback
async def get_account_with_fallback(account_id):
    async def tier1():
        breaker = manager.get_breaker("tier1_mcp")
        return await breaker.call(
            lambda: mcp_client.get_account(account_id)
        )

    async def tier2():
        breaker = manager.get_breaker("tier2_sdk")
        return await breaker.call(
            lambda: sdk_client.get_account(account_id)
        )

    async def tier3():
        breaker = manager.get_breaker("tier3_rest")
        return await breaker.call(
            lambda: rest_client.get_account(account_id)
        )

    return await handler.execute_with_fallback(
        tier1, tier2, tier3,
        operation_name="get_account"
    )
```

## Configuration

### Environment Variables

```bash
# Circuit Breaker Settings
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60
CIRCUIT_BREAKER_HALF_OPEN_CALLS=3
CIRCUIT_BREAKER_SUCCESS_THRESHOLD=2

# Retry Policy
MAX_RETRY_ATTEMPTS=3
RETRY_BASE_DELAY=1.0
RETRY_MAX_DELAY=60.0
RETRY_EXPONENTIAL_BASE=2.0
RETRY_JITTER_ENABLED=true

# Health Monitoring
HEALTH_CHECK_INTERVAL=30
```

### Configuration Tuning

**Aggressive (Fast Failure Detection)**
```python
CircuitBreaker(
    failure_threshold=3,      # Open quickly
    recovery_timeout=30,      # Short recovery window
    half_open_max_calls=2,
    success_threshold=2
)
```

**Conservative (Tolerant of Transients)**
```python
CircuitBreaker(
    failure_threshold=10,     # More tolerance
    recovery_timeout=120,     # Longer recovery
    half_open_max_calls=5,
    success_threshold=3
)
```

**Production Recommended**
```python
CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    half_open_max_calls=3,
    success_threshold=2
)
```

## Retry Policy Integration

```python
from src.resilience import RetryPolicy

# Create retry policy
retry = RetryPolicy(
    max_attempts=3,
    base_delay=1.0,           # Start with 1s delay
    max_delay=60.0,           # Cap at 60s
    exponential_base=2.0,     # Double each time (1s, 2s, 4s)
    jitter=True               # Add randomness
)

# Combine with circuit breaker
async def resilient_operation():
    async def execute_with_breaker():
        return await breaker.call(zoho_api_call)

    return await retry.execute(execute_with_breaker)
```

**Delay Calculation:**
```
delay = min(base_delay * (exponential_base ^ attempt), max_delay)
With jitter: delay * random(0.5, 1.5)

Example:
Attempt 0: 1.0s * (2^0) = 1.0s
Attempt 1: 1.0s * (2^1) = 2.0s
Attempt 2: 1.0s * (2^2) = 4.0s
```

## Health Monitoring

```python
from src.resilience import HealthMonitor

# Create health monitor
monitor = HealthMonitor(
    mcp_client=mcp_client,
    sdk_client=sdk_client,
    rest_client=rest_client,
    check_interval=30  # Check every 30 seconds
)

# Start background monitoring
await monitor.start_monitoring()

# Get current health status
health = monitor.get_health_status()
print(f"All healthy: {health['all_healthy']}")
print(f"Status: {health['status']}")

# Manual health check
await monitor.check_all_tiers()

# Stop monitoring
await monitor.stop_monitoring()
```

## Monitoring and Metrics

### Collect Metrics

```python
# Single breaker metrics
metrics = breaker.get_metrics()
print(f"State: {metrics['state']}")
print(f"Failure count: {metrics['failure_count']}")
print(f"Error rate: {metrics['error_rate']:.2%}")
print(f"Time until retry: {metrics['time_until_retry']}s")

# All breaker metrics
all_metrics = manager.get_all_metrics()
for name, metrics in all_metrics.items():
    print(f"{name}: {metrics['state']} (errors: {metrics['error_rate']:.1%})")
```

### Metrics Structure

```python
{
    "state": "closed",               # closed|open|half_open
    "failure_count": 3,              # Current failures
    "success_count": 0,              # Successes in half-open
    "total_calls": 100,              # Calls in sliding window
    "error_rate": 0.15,              # Error rate (0.0 - 1.0)
    "last_failure_time": "2025-...", # ISO timestamp
    "time_until_retry": 45.2         # Seconds (null if not open)
}
```

### Logging

Circuit breakers emit structured logs:

```python
# Circuit opened
{
    "event": "circuit_opened",
    "circuit_breaker": "tier1_mcp",
    "old_state": "closed",
    "failure_count": 5,
    "recovery_timeout": 60
}

# Circuit closed
{
    "event": "circuit_closed",
    "circuit_breaker": "tier1_mcp",
    "old_state": "half_open"
}

# Call failed
{
    "event": "call_failed",
    "circuit_breaker": "tier1_mcp",
    "failure_count": 3,
    "threshold": 5
}
```

## Error Handling

### Exceptions

```python
from src.resilience.exceptions import (
    CircuitBreakerOpenError,
    AllTiersFailedError,
    RetryExhaustedError
)

# Handle circuit open
try:
    result = await breaker.call(operation)
except CircuitBreakerOpenError as e:
    print(f"Circuit '{e.circuit_name}' open, retry after {e.retry_after}s")
    # Fallback or queue for later

# Handle all tiers failed
try:
    result = await handler.execute_with_fallback(t1, t2, t3, "op")
except AllTiersFailedError as e:
    print(f"All tiers failed: {e.attempted_tiers}")
    # Critical alert

# Handle retry exhausted
try:
    result = await retry.execute(operation)
except RetryExhaustedError as e:
    print(f"Failed after {e.attempts} attempts: {e.last_error}")
    # Log and alert
```

## Troubleshooting

### Circuit Stuck Open

**Symptoms:**
- Circuit remains open even when service is healthy
- Constant `CircuitBreakerOpenError`

**Solutions:**
```python
# 1. Check recovery timeout
metrics = breaker.get_metrics()
if metrics['time_until_retry'] is not None:
    print(f"Wait {metrics['time_until_retry']}s for recovery")

# 2. Manual reset (use carefully)
breaker.reset()

# 3. Adjust configuration
breaker = CircuitBreaker(
    recovery_timeout=30,  # Shorter timeout
    success_threshold=1   # Easier to close
)
```

### Flapping Circuit

**Symptoms:**
- Circuit rapidly opens and closes
- State changes frequently

**Solutions:**
```python
# Increase thresholds for stability
breaker = CircuitBreaker(
    failure_threshold=10,      # More tolerance
    success_threshold=5,       # Require more successes
    half_open_max_calls=1      # Limit half-open traffic
)
```

### High Error Rates

**Symptoms:**
- `error_rate > 0.3` consistently
- Frequent failures

**Solutions:**
```python
# 1. Check service health
health = await monitor.check_tier("tier1_mcp")
if not health:
    # Service issue, not circuit breaker

# 2. Review failure patterns
metrics = breaker.get_metrics()
print(f"Recent failures: {metrics['failure_count']}")

# 3. Adjust retry policy
retry = RetryPolicy(
    max_attempts=5,        # More retries
    base_delay=2.0,        # Longer delays
    jitter=True            # Spread load
)
```

## Best Practices

### 1. **One Circuit Per Service/Tier**
```python
# ✅ Good - Separate circuits
manager.register_breaker("zoho_mcp")
manager.register_breaker("zoho_sdk")
manager.register_breaker("zoho_rest")

# ❌ Bad - Single circuit for all
manager.register_breaker("zoho")
```

### 2. **Combine with Retry Policy**
```python
# ✅ Good - Retry transient failures
async def resilient_call():
    return await retry.execute(
        lambda: breaker.call(operation)
    )

# ❌ Bad - No retry for transients
await breaker.call(operation)
```

### 3. **Implement Fallback Strategy**
```python
# ✅ Good - Graceful degradation
result = await handler.execute_with_fallback(
    primary_tier, secondary_tier, tertiary_tier, "op"
)

# ❌ Bad - No fallback
result = await primary_tier_only()
```

### 4. **Monitor Circuit States**
```python
# ✅ Good - Active monitoring
states = manager.get_all_states()
if any(s == CircuitState.OPEN for s in states.values()):
    alert_ops_team()

# ❌ Bad - No monitoring
# Hope for the best
```

### 5. **Configure Based on SLA**
```python
# If SLA allows 99.9% uptime (43min downtime/month)
breaker = CircuitBreaker(
    failure_threshold=5,       # Quick detection
    recovery_timeout=60,       # 1min recovery attempts
    success_threshold=2        # Fast recovery
)
```

### 6. **Use Health Checks**
```python
# ✅ Good - Proactive health monitoring
await monitor.start_monitoring()

# Check before critical operations
health = monitor.get_health_status()
if not health['all_healthy']:
    # Alert or use degraded mode
```

### 7. **Log Circuit Events**
```python
# Circuit breakers auto-log events
# Integrate with your logging pipeline
import structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
```

## Performance Impact

- **Overhead per call**: < 1ms
- **Memory per circuit**: ~10KB
- **Thread-safe**: Yes (uses asyncio locks)
- **Concurrent calls**: Unlimited (lock-protected state changes)

## Production Checklist

- [ ] Circuit breakers registered for all tiers
- [ ] Failure thresholds configured appropriately
- [ ] Recovery timeouts aligned with SLA
- [ ] Retry policy with exponential backoff
- [ ] Health monitoring enabled
- [ ] Metrics collection configured
- [ ] Alerting on circuit state changes
- [ ] Fallback strategy implemented
- [ ] Load testing completed
- [ ] Documentation updated

## Additional Resources

- [Martin Fowler: Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Release It! by Michael Nygard](https://pragprog.com/titles/mnee2/release-it-second-edition/)
- [Sergas Architecture Docs](../architecture/RESILIENCE.md)

## Support

For issues or questions:
- Internal Wiki: `https://wiki.sergas.com/resilience`
- Slack: `#sergas-super-account-manager`
- On-call: `resilience-team@sergas.com`
