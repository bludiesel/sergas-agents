# Resilience Module

Production-grade circuit breaker pattern implementation for preventing cascade failures across the three-tier Zoho integration.

## Features

- ✅ **Circuit Breaker Pattern** - Automatic failure detection and recovery
- ✅ **Multi-Tier Fallback** - Graceful degradation across MCP → SDK → REST
- ✅ **Retry with Exponential Backoff** - Intelligent retry handling
- ✅ **Health Monitoring** - Continuous tier health checks
- ✅ **Thread-Safe** - Concurrent request handling
- ✅ **Comprehensive Metrics** - Real-time circuit state and error rates

## Quick Start

```python
from src.resilience import (
    CircuitBreakerManager,
    FallbackHandler,
    RetryPolicy
)

# Setup
manager = CircuitBreakerManager()
manager.register_breaker("tier1_mcp", failure_threshold=5)
manager.register_breaker("tier2_sdk", failure_threshold=5)
manager.register_breaker("tier3_rest", failure_threshold=5)

handler = FallbackHandler(manager)
retry = RetryPolicy(max_attempts=3, base_delay=1.0)

# Use with automatic fallback
async def get_account(account_id):
    async def tier1():
        return await mcp_client.get_account(account_id)

    async def tier2():
        return await sdk_client.get_account(account_id)

    async def tier3():
        return await rest_client.get_account(account_id)

    return await handler.execute_with_fallback(
        tier1, tier2, tier3, "get_account"
    )
```

## Architecture

### Circuit Breaker States

```
CLOSED (normal) → OPEN (failed) → HALF_OPEN (testing) → CLOSED
```

### Tier Fallback Flow

```
Tier 1 (MCP) → Tier 2 (SDK) → Tier 3 (REST)
     ↓              ↓              ↓
Circuit Breaker  Circuit Breaker  Circuit Breaker
```

## Components

### 1. Circuit Breaker (`circuit_breaker.py`)
Core circuit breaker implementation with state management.

### 2. Circuit Breaker Manager (`circuit_breaker_manager.py`)
Centralized management of multiple circuit breakers.

### 3. Retry Policy (`retry_policy.py`)
Exponential backoff retry mechanism with jitter.

### 4. Fallback Handler (`fallback_handler.py`)
Automatic tier fallback coordination.

### 5. Health Monitor (`health_monitor.py`)
Background tier health monitoring.

## Configuration

See `.env.example` for all configuration options:

```bash
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60
MAX_RETRY_ATTEMPTS=3
HEALTH_CHECK_INTERVAL=30
```

## Testing

```bash
# Unit tests (40+ tests)
pytest tests/unit/resilience/ -v

# Integration tests (15+ tests)
pytest tests/integration/test_resilience.py -v

# Coverage report
pytest tests/unit/resilience/ --cov=src/resilience --cov-report=html
```

## Documentation

- [Circuit Breaker Guide](./CIRCUIT_BREAKER_GUIDE.md) - Complete usage guide
- [API Reference](./API_REFERENCE.md) - Detailed API documentation
- [Architecture](../architecture/RESILIENCE.md) - System design

## Performance

- **Overhead**: < 1ms per call
- **Memory**: ~10KB per circuit breaker
- **Thread-Safe**: Yes (asyncio locks)
- **Concurrent Calls**: Unlimited

## Metrics

```python
# Get circuit metrics
metrics = breaker.get_metrics()
# {
#   "state": "closed",
#   "failure_count": 2,
#   "error_rate": 0.15,
#   "time_until_retry": None
# }

# Monitor all circuits
all_metrics = manager.get_all_metrics()
for name, metrics in all_metrics.items():
    print(f"{name}: {metrics['state']}")
```

## Best Practices

1. **One circuit per service** - Isolate failures
2. **Combine with retries** - Handle transient failures
3. **Implement fallback** - Graceful degradation
4. **Monitor actively** - Alert on circuit state changes
5. **Configure per SLA** - Tune thresholds to requirements

## Error Handling

```python
from src.resilience.exceptions import (
    CircuitBreakerOpenError,
    AllTiersFailedError,
    RetryExhaustedError
)

try:
    result = await handler.execute_with_fallback(t1, t2, t3, "op")
except CircuitBreakerOpenError as e:
    # Circuit is open, retry later
    pass
except AllTiersFailedError as e:
    # All tiers failed, critical alert
    pass
except RetryExhaustedError as e:
    # Retries exhausted
    pass
```

## Production Checklist

- [ ] Circuit breakers configured for all tiers
- [ ] Thresholds tuned to SLA requirements
- [ ] Health monitoring enabled
- [ ] Metrics collection configured
- [ ] Alerting on circuit state changes
- [ ] Fallback strategy implemented
- [ ] Load testing completed
- [ ] Documentation reviewed

## Support

- **Documentation**: `/docs/resilience/`
- **Examples**: `/examples/resilience/`
- **Tests**: `/tests/unit/resilience/`, `/tests/integration/`

## License

Internal use only - Sergas Super Account Manager project.
