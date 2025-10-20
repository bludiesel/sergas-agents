# Reliability Module Documentation

## Overview

The Reliability module provides comprehensive production-hardening capabilities for the Sergas Agents system, including health monitoring, graceful degradation, disaster recovery, and rate limiting.

## Components

### 1. Health Checks (`health_checks.py`)

Comprehensive health monitoring system with multiple check types.

**Features:**
- Service health endpoints
- Database health validation
- Cache (Redis) health monitoring
- External dependency checks
- Centralized health registry
- Automated health reporting

**Usage:**

```python
from src.reliability.health_checks import (
    HealthCheckRegistry,
    ServiceHealthCheck,
    DatabaseHealthCheck,
    CacheHealthCheck,
)

# Create registry
registry = HealthCheckRegistry()

# Register health checks
db_check = DatabaseHealthCheck(
    name="database_primary",
    connection_string="postgresql://user:pass@localhost/db",
    max_connections=20
)
registry.register(db_check)

cache_check = CacheHealthCheck(
    name="redis_cache",
    redis_url="redis://localhost:6379/0"
)
registry.register(cache_check)

# Run all checks
results = await registry.check_all()
summary = registry.get_summary(results)

print(f"Overall Status: {summary['status']}")
print(f"Healthy: {summary['healthy']}/{summary['total_checks']}")
```

**CLI Tool:**

```bash
# Run comprehensive health checks
python scripts/reliability/health_check_all.py

# Verbose output
python scripts/reliability/health_check_all.py --verbose

# JSON output
python scripts/reliability/health_check_all.py --json
```

---

### 2. Graceful Degradation (`graceful_degradation.py`)

Fallback strategies and feature flags for maintaining availability during failures.

**Features:**
- Feature flag system with rollout percentage
- Multiple fallback strategies (cached, static, service)
- Partial failure handling
- Degradation level management
- Circuit breaker integration

**Usage:**

```python
from src.reliability.graceful_degradation import (
    DegradationManager,
    FeatureFlags,
    CachedFallback,
    DegradationLevel,
)

# Create manager
manager = DegradationManager()

# Register feature flags
manager.feature_flags.register(
    "recommendations",
    enabled=True,
    description="Product recommendations",
    rollout_percentage=100.0
)

# Register fallback strategy
cached_fallback = CachedFallback(
    name="api_cache",
    cache_ttl=300
)
manager.register_fallback("external_api", cached_fallback)

# Execute with fallback
result = await manager.execute_with_fallback(
    "external_api",
    primary_func=call_external_api,
    fallback_strategy="api_cache",
    user_id="123"
)

# Set degradation level
manager.set_degradation_level(DegradationLevel.DEGRADED)
```

**Feature Flag Example:**

```python
# Check if feature enabled
if manager.feature_flags.is_enabled("recommendations", user_id="user123"):
    # Show recommendations
    recommendations = get_recommendations(user_id)
else:
    # Feature disabled, skip
    recommendations = []

# Gradual rollout
manager.feature_flags.set_rollout_percentage("new_feature", 25.0)  # 25% of users
```

---

### 3. Disaster Recovery (`disaster_recovery.py`)

Automated backup, restoration, and recovery testing.

**Features:**
- Multiple backup types (full, incremental, differential, snapshot)
- Filesystem and database backup strategies
- Point-in-time recovery (PITR)
- Backup verification and testing
- Automated retention management

**Usage:**

```python
from src.reliability.disaster_recovery import (
    BackupManager,
    BackupType,
    FileSystemBackupStrategy,
    RecoveryTestRunner,
)
from pathlib import Path

# Create backup manager
backup_dir = Path("/var/backups")
manager = BackupManager(backup_dir)

# Register backup strategy
fs_strategy = FileSystemBackupStrategy(compress=True)
manager.register_strategy("filesystem", fs_strategy)

# Create backup
metadata = await manager.create_backup(
    name="daily_backup",
    source="/data/application",
    backup_type=BackupType.FULL,
    strategy="filesystem",
    retention_days=30
)

# List backups
backups = manager.list_backups(backup_type=BackupType.FULL)

# Restore backup
success = await manager.restore_backup(
    backup_id="backup_20251019_120000",
    restore_path="/data/restore"
)

# Test recovery
test_runner = RecoveryTestRunner(manager, Path("/tmp/test_recovery"))
results = await test_runner.run_recovery_drill()
```

**CLI Tool:**

```bash
# Create backup
python scripts/reliability/example_disaster_recovery.py create-backup \
  --name=emergency \
  --source=/data \
  --type=full \
  --retention=30

# List backups
python scripts/reliability/example_disaster_recovery.py list-backups

# Restore backup
python scripts/reliability/example_disaster_recovery.py restore \
  --backup-id=backup_20251019_120000 \
  --destination=/data/restore

# Test recovery
python scripts/reliability/example_disaster_recovery.py test-recovery

# Cleanup old backups
python scripts/reliability/example_disaster_recovery.py cleanup
```

---

### 4. Rate Limiting (`rate_limiting.py`)

Multi-strategy rate limiting, queue management, and backpressure handling.

**Features:**
- Multiple rate limiting strategies (token bucket, sliding window, fixed window, leaky bucket)
- Queue management with priority and timeout
- Throttling based on system load
- Backpressure handling
- Detailed metrics

**Usage:**

```python
from src.reliability.rate_limiting import (
    RateLimiter,
    RateLimitConfig,
    RateLimitStrategy,
    QueueManager,
    BackpressureHandler,
)

# Create rate limiter
config = RateLimitConfig(
    name="api_rate_limiter",
    max_requests=100,
    window_seconds=60,
    strategy=RateLimitStrategy.SLIDING_WINDOW
)

limiter = RateLimiter(config)

# Check if request allowed
is_allowed, retry_after = await limiter.allow_request(cost=1)

if is_allowed:
    # Process request
    result = await process_request()
else:
    # Rate limited
    return {"error": "Rate limit exceeded", "retry_after": retry_after}

# Create queue manager
queue = QueueManager(
    name="request_queue",
    max_size=1000,
    max_workers=10,
    timeout=30.0
)

# Start queue processing
await queue.start()

# Enqueue work
success = await queue.enqueue(
    process_request,
    priority=0,
    request_id="123"
)

# Setup backpressure handling
handler = BackpressureHandler(
    name="api_backpressure",
    queue_manager=queue,
    rate_limiter=limiter,
    alert_threshold=0.8
)

is_active = await handler.check_and_apply_backpressure()
```

**CLI Examples:**

```bash
# Demo token bucket
python scripts/reliability/example_rate_limiting.py demo-token-bucket

# Demo sliding window
python scripts/reliability/example_rate_limiting.py demo-sliding-window

# Demo queue management
python scripts/reliability/example_rate_limiting.py demo-queue

# Run load test
python scripts/reliability/example_rate_limiting.py load-test
```

---

## Operational Runbooks

Detailed operational procedures are available in `/docs/reliability/runbooks/`:

### 1. Incident Response (`incident_response.md`)

Step-by-step procedures for handling production incidents.

**Sections:**
- Incident severity levels
- Detection and alert procedures
- Assessment and mitigation
- Common incident scenarios
- Escalation procedures
- Post-incident reviews

### 2. Disaster Recovery (`disaster_recovery.md`)

Comprehensive disaster recovery procedures.

**Sections:**
- Recovery time/point objectives (RTO/RPO)
- Disaster scenarios (database loss, infrastructure failure, data corruption)
- Backup verification procedures
- Recovery validation
- Communication templates

### 3. Scaling (`scaling.md`)

Procedures for scaling the system under load.

**Sections:**
- Load indicators and thresholds
- Horizontal and vertical scaling
- Database and cache scaling
- Rate limiting adjustments
- Capacity planning
- Auto-scaling configuration

### 4. Troubleshooting (`troubleshooting.md`)

Systematic troubleshooting procedures.

**Sections:**
- General troubleshooting framework
- Common issues and solutions
- Advanced debugging techniques
- Emergency procedures

---

## Integration with Existing Systems

### Circuit Breakers

The reliability module integrates with the existing circuit breaker system:

```python
from src.resilience.circuit_breaker_manager import CircuitBreakerManager
from src.reliability.graceful_degradation import DegradationManager

# Create degradation manager with circuit breakers
cb_manager = CircuitBreakerManager()
degradation = DegradationManager(circuit_breaker_manager=cb_manager)

# Automatically uses circuit breakers
result = await degradation.execute_with_fallback(
    "external_api",
    primary_func=call_api,
    fallback_strategy="cached"
)
```

### Health Monitoring

Integrate with existing health monitor:

```python
from src.resilience.health_monitor import HealthMonitor as ExistingMonitor
from src.reliability.health_checks import HealthCheckRegistry

# Use both systems
existing_monitor = ExistingMonitor(mcp_client, sdk_client, rest_client)
new_registry = HealthCheckRegistry()

# Run both
existing_results = await existing_monitor.check_all_tiers()
new_results = await new_registry.check_all()
```

---

## Testing

### Unit Tests

```bash
# Run all reliability tests
pytest tests/reliability/

# Run specific test
pytest tests/reliability/test_health_checks.py -v

# Run with coverage
pytest tests/reliability/ --cov=src/reliability --cov-report=html
```

### Integration Tests

```bash
# Test with real services (requires setup)
pytest tests/reliability/ --integration

# Test disaster recovery
pytest tests/reliability/test_disaster_recovery.py --run-recovery-tests
```

---

## Monitoring and Metrics

### Health Check Metrics

```python
# Get health summary
summary = registry.get_summary(results)

metrics = {
    "status": summary["status"],  # Overall health status
    "total_checks": summary["total_checks"],
    "healthy": summary["healthy"],
    "degraded": summary["degraded"],
    "unhealthy": summary["unhealthy"],
}
```

### Rate Limiter Metrics

```python
# Get rate limiter metrics
metrics = limiter.get_metrics()

{
    "name": "api_rate_limiter",
    "strategy": "sliding_window",
    "max_requests": 100,
    "window_seconds": 60,
    "current_requests": 45,
    "utilization_percent": 45.0,
    "requests_per_second": 1.67
}
```

### Queue Metrics

```python
# Get queue metrics
metrics = queue.get_metrics()

{
    "name": "request_queue",
    "queue_size": 25,
    "max_size": 1000,
    "utilization_percent": 2.5,
    "active_workers": 10,
    "processed_count": 1523,
    "failed_count": 12,
    "timeout_count": 3
}
```

---

## Best Practices

### Health Checks

1. **Regular Monitoring**: Run health checks every 30-60 seconds
2. **Timeout Configuration**: Set reasonable timeouts (5-10 seconds)
3. **Degraded State**: Use degraded status for partial failures
4. **Dependency Checks**: Monitor all external dependencies

### Graceful Degradation

1. **Essential Features**: Identify core features that must always work
2. **Fallback Data**: Maintain cached fallback data
3. **User Communication**: Inform users when features are degraded
4. **Automatic Recovery**: Automatically restore features when healthy

### Disaster Recovery

1. **Regular Backups**: Daily full backups, hourly incrementals
2. **Offsite Storage**: Store backups in different region/datacenter
3. **Test Restores**: Monthly recovery drills
4. **Documentation**: Keep runbooks updated
5. **Automation**: Automate backup and recovery processes

### Rate Limiting

1. **Appropriate Limits**: Set limits based on capacity testing
2. **Gradual Rollout**: Implement rate limiting gradually
3. **Clear Errors**: Provide helpful error messages with retry-after
4. **Monitoring**: Track rate limit utilization
5. **Exemptions**: Allow exemptions for critical operations

---

## Configuration Examples

### Production Configuration

```python
# config/reliability.py

HEALTH_CHECK_CONFIG = {
    "interval_seconds": 60,
    "timeout_seconds": 10,
    "checks": {
        "database": {"enabled": True},
        "cache": {"enabled": True},
        "external_apis": {"enabled": True},
    }
}

BACKUP_CONFIG = {
    "schedule": "0 2 * * *",  # 2 AM daily
    "retention_days": 30,
    "backup_type": "full",
    "compression": True,
    "encryption": True,
}

RATE_LIMIT_CONFIG = {
    "api": {
        "max_requests": 1000,
        "window_seconds": 60,
        "strategy": "sliding_window",
    },
    "batch_operations": {
        "max_requests": 10,
        "window_seconds": 60,
        "strategy": "token_bucket",
    }
}

DEGRADATION_CONFIG = {
    "auto_degrade_threshold": 0.85,  # Auto-degrade at 85% capacity
    "feature_flags_path": "/config/feature_flags.json",
}
```

---

## Support

For issues or questions:

1. Check the troubleshooting guide
2. Review operational runbooks
3. Contact platform team: platform-team@sergas.com
4. Escalate via PagerDuty for production issues

---

## Version History

- **v1.0.0** (2025-10-19): Initial release
  - Health check system
  - Graceful degradation
  - Disaster recovery
  - Rate limiting
  - Operational runbooks
