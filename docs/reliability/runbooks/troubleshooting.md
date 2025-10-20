# Troubleshooting Guide

## Overview

This guide provides systematic troubleshooting procedures for common issues in the Sergas Agents system.

---

## General Troubleshooting Framework

### The STARR Method

1. **S**ituation: What is the problem?
2. **T**ask: What needs to be fixed?
3. **A**ction: What actions to take?
4. **R**esult: What was the outcome?
5. **R**eflection: What did we learn?

### Diagnostic Commands Quick Reference

```bash
# Health checks
python scripts/reliability/health_check_all.py

# Service status
kubectl get pods -n production
kubectl get services -n production

# Logs
kubectl logs -f deployment/api-server -n production

# Metrics
kubectl top pods -n production
kubectl top nodes

# Database
psql -c "SELECT version();"
psql -c "SELECT * FROM pg_stat_activity;"

# Cache
redis-cli INFO
redis-cli PING

# Circuit breakers
python scripts/reliability/check_circuit_breakers.py
```

---

## Common Issues and Solutions

### Issue: High Error Rates

#### Symptoms
- Error rate > 5%
- 5xx HTTP responses
- Failed health checks

#### Diagnostic Steps

```bash
# 1. Check error distribution
kubectl logs deployment/api-server -n production --tail=1000 | grep ERROR | sort | uniq -c | sort -rn

# 2. View recent errors
kubectl logs deployment/api-server -n production --since=10m | grep ERROR

# 3. Check error types
python scripts/monitoring/analyze_errors.py --period=30m

# 4. Database errors
psql -c "SELECT * FROM error_logs WHERE created_at > now() - interval '30 minutes' ORDER BY created_at DESC LIMIT 100;"
```

#### Common Causes

##### 1. Database Connection Failures
```bash
# Check connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check max connections
psql -c "SHOW max_connections;"

# Solution: Increase connection pool
python scripts/db/increase_connection_pool.py --size=100
```

##### 2. External API Failures
```python
from src.resilience.circuit_breaker_manager import CircuitBreakerManager

# Check circuit breaker status
manager = CircuitBreakerManager()
metrics = manager.get_all_metrics()

# If circuit open, enable fallback
from src.reliability.graceful_degradation import DegradationManager
degradation = DegradationManager()
degradation.execute_with_fallback(
    "external_api",
    fallback_strategy="cached_fallback"
)
```

##### 3. Memory Issues
```bash
# Check memory usage
kubectl top pods -n production

# Check for OOMKilled
kubectl get pods -n production | grep OOMKilled

# Solution: Increase memory limits
kubectl set resources deployment api-server --limits=memory=4Gi -n production
```

##### 4. Code Bugs
```bash
# Rollback to previous version
kubectl rollout undo deployment api-server -n production

# Monitor for improvement
python scripts/monitoring/check_error_rates.py --duration=15m
```

---

### Issue: Slow Response Times

#### Symptoms
- p95 latency > 2000ms
- User complaints about slowness
- Timeout errors

#### Diagnostic Steps

```bash
# 1. Check response time distribution
python scripts/monitoring/analyze_latency.py --period=30m

# 2. Identify slow endpoints
kubectl logs deployment/api-server -n production --tail=1000 | python scripts/monitoring/parse_slow_requests.py

# 3. Database query performance
psql -c "
  SELECT
    query,
    calls,
    mean_exec_time,
    max_exec_time
  FROM pg_stat_statements
  ORDER BY mean_exec_time DESC
  LIMIT 20;"

# 4. Check for slow external calls
python scripts/monitoring/analyze_external_calls.py
```

#### Common Causes

##### 1. Slow Database Queries
```sql
-- Identify slow queries
SELECT
  pid,
  now() - query_start AS duration,
  query
FROM pg_stat_activity
WHERE state = 'active'
  AND now() - query_start > interval '5 seconds'
ORDER BY duration DESC;

-- Check missing indexes
SELECT
  schemaname,
  tablename,
  seq_scan,
  seq_tup_read,
  idx_scan,
  seq_tup_read / seq_scan as avg_seq_tup_read
FROM pg_stat_user_tables
WHERE seq_scan > 0
ORDER BY seq_tup_read DESC
LIMIT 20;

-- Solution: Add indexes
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
ANALYZE users;
```

##### 2. N+1 Query Problem
```python
# Identify N+1 queries in logs
python scripts/monitoring/detect_n_plus_1.py --logs=/var/log/app.log

# Solution: Use eager loading or batch queries
# Example fix in code:
# Bad: for user in users: user.profile  # N+1
# Good: users.select_related('profile')  # 1 query
```

##### 3. Cache Misses
```bash
# Check cache hit rate
redis-cli INFO stats | grep hit_rate

# Check cache usage
python scripts/cache/analyze_usage.py

# Solution: Warm cache or increase TTL
python scripts/cache/warm_cache.py --keys=popular_queries
python scripts/cache/adjust_ttl.py --increase=50%
```

##### 4. Insufficient Resources
```bash
# Check CPU throttling
kubectl top pods -n production

# Check if HPA should scale
kubectl describe hpa api-server -n production

# Solution: Scale horizontally
kubectl scale deployment api-server --replicas=10 -n production
```

##### 5. External API Slowness
```bash
# Check external API response times
python scripts/monitoring/check_external_apis.py

# Solution: Increase timeouts or enable caching
python scripts/integrations/increase_timeouts.py --service=zoho --timeout=30
python scripts/integrations/enable_caching.py --service=zoho --ttl=300
```

---

### Issue: Database Connection Pool Exhausted

#### Symptoms
- "Too many connections" errors
- Connection timeout errors
- Degraded performance

#### Diagnostic Steps

```bash
# 1. Check current connections
psql -c "SELECT count(*) as total, state, application_name FROM pg_stat_activity GROUP BY state, application_name;"

# 2. Check connection limits
psql -c "SHOW max_connections;"

# 3. Identify connection leaks
psql -c "
  SELECT
    application_name,
    client_addr,
    count(*),
    max(state_change) as last_activity
  FROM pg_stat_activity
  GROUP BY application_name, client_addr
  ORDER BY count(*) DESC;"

# 4. Check idle connections
psql -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'idle' AND state_change < now() - interval '10 minutes';"
```

#### Solutions

##### 1. Increase Connection Pool Size
```python
from src.db.connection_pool import ConnectionPoolManager

pool_manager = ConnectionPoolManager()
pool_manager.resize_pool(
    min_connections=20,
    max_connections=100
)
```

##### 2. Kill Idle Connections
```sql
-- Kill long-idle connections
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND state_change < now() - interval '10 minutes'
  AND pid != pg_backend_pid();
```

##### 3. Implement Connection Pooling (PgBouncer)
```bash
# Deploy PgBouncer
kubectl apply -f manifests/pgbouncer-deployment.yaml

# Update application to use PgBouncer
kubectl set env deployment/api-server \
  DATABASE_HOST=pgbouncer.production.svc.cluster.local \
  -n production
```

##### 4. Fix Connection Leaks in Code
```python
# Bad: Connection leak
def get_data():
    conn = get_connection()
    result = conn.execute("SELECT * FROM users")
    return result  # Connection never closed!

# Good: Proper cleanup
def get_data():
    with get_connection() as conn:
        result = conn.execute("SELECT * FROM users")
        return result  # Connection auto-closed
```

---

### Issue: Circuit Breaker Stuck Open

#### Symptoms
- CircuitBreakerOpenError in logs
- Fallback responses to users
- Service degradation

#### Diagnostic Steps

```python
from src.resilience.circuit_breaker_manager import CircuitBreakerManager

# Check circuit breaker status
manager = CircuitBreakerManager()
metrics = manager.get_all_metrics()

for name, m in metrics.items():
    if m['state'] == 'open':
        print(f"Circuit {name}:")
        print(f"  State: {m['state']}")
        print(f"  Failure count: {m['failure_count']}")
        print(f"  Error rate: {m['error_rate']}")
        print(f"  Time until retry: {m['time_until_retry']}s")
```

#### Solutions

##### 1. Verify Underlying Service is Healthy
```bash
# Test external service directly
curl -v https://api.external-service.com/health

# Check service logs
kubectl logs deployment/external-service -n production --tail=100
```

##### 2. Manually Reset Circuit Breaker
```python
from src.resilience.circuit_breaker_manager import CircuitBreakerManager

manager = CircuitBreakerManager()
manager.get_breaker("external_api").reset()

# Monitor for issues
import asyncio
import time

async def monitor():
    for i in range(10):
        metrics = manager.get_breaker("external_api").get_metrics()
        print(f"Attempt {i+1}: State={metrics['state']}, Failures={metrics['failure_count']}")
        await asyncio.sleep(10)

asyncio.run(monitor())
```

##### 3. Adjust Circuit Breaker Thresholds
```python
# If circuit is too sensitive
from src.resilience.circuit_breaker import CircuitBreaker

# Recreate with higher threshold
new_breaker = CircuitBreaker(
    name="external_api",
    failure_threshold=10,  # Increased from 5
    recovery_timeout=120,  # Increased from 60
    half_open_max_calls=5  # Increased from 3
)

manager.register("external_api", new_breaker)
```

##### 4. Enable Fallback Strategy
```python
from src.reliability.graceful_degradation import (
    DegradationManager,
    CachedFallback
)

# Use cached data while circuit is open
degradation = DegradationManager()

cached_fallback = CachedFallback(
    name="external_api_cache",
    cache_ttl=600  # 10 minutes
)

degradation.register_fallback("external_api", cached_fallback)

# Execute with fallback
result = await degradation.execute_with_fallback(
    "external_api",
    primary_func=call_external_api,
    fallback_strategy="external_api_cache"
)
```

---

### Issue: Memory Leak

#### Symptoms
- Increasing memory usage over time
- OOMKilled pod restarts
- Slow performance degradation

#### Diagnostic Steps

```bash
# 1. Monitor memory over time
watch -n 30 'kubectl top pods -n production'

# 2. Check pod restart count
kubectl get pods -n production -o json | jq '.items[] | {name: .metadata.name, restarts: .status.containerStatuses[].restartCount}'

# 3. Check OOMKilled events
kubectl get events -n production | grep OOMKilled

# 4. Get memory profile
kubectl exec -it api-server-pod -n production -- python -m memory_profiler /app/main.py
```

#### Common Causes

##### 1. Unclosed Resources
```python
# Bad: Resource leak
def process_data():
    file = open('data.txt')
    data = file.read()
    return data  # File never closed!

# Good: Proper cleanup
def process_data():
    with open('data.txt') as file:
        data = file.read()
        return data  # File auto-closed
```

##### 2. Growing Caches
```python
# Bad: Unbounded cache
cache = {}
def get_data(key):
    if key not in cache:
        cache[key] = expensive_operation(key)
    return cache[key]  # Cache grows forever!

# Good: Bounded cache
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_data(key):
    return expensive_operation(key)  # Auto-evicts old entries
```

##### 3. Event Listeners Not Removed
```python
# Bad: Listener leak
def setup_listener():
    event_emitter.on('data', handler)
    # Handler never removed!

# Good: Cleanup
def setup_listener():
    event_emitter.on('data', handler)
    # Later...
    event_emitter.off('data', handler)
```

#### Solutions

##### 1. Temporary: Periodic Restarts
```bash
# Rolling restart to clear memory
kubectl rollout restart deployment api-server -n production

# Or schedule periodic restarts
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: api-server-restart
  namespace: production
spec:
  schedule: "0 3 * * *"  # 3 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: restart
            image: bitnami/kubectl
            command:
            - kubectl
            - rollout
            - restart
            - deployment/api-server
            - -n
            - production
          restartPolicy: Never
EOF
```

##### 2. Permanent: Fix Memory Leaks
```bash
# Use memory profiler to identify leaks
python -m memory_profiler scripts/find_memory_leaks.py

# Add memory monitoring
python scripts/monitoring/track_memory_usage.py --alert-threshold=2GB
```

##### 3. Increase Memory Limits (Temporary)
```bash
kubectl set resources deployment api-server \
  --limits=memory=4Gi \
  -n production
```

---

### Issue: High Queue Depth

#### Symptoms
- Request queue > 100
- Increasing response times
- Timeout errors

#### Diagnostic Steps

```python
from src.reliability.rate_limiting import QueueManager

# Check queue metrics
queue = QueueManager.get_instance("request_queue")
metrics = queue.get_metrics()

print(f"Queue size: {metrics['queue_size']}/{metrics['max_size']}")
print(f"Utilization: {metrics['utilization_percent']}%")
print(f"Active workers: {metrics['active_workers']}/{metrics['max_workers']}")
print(f"Processed: {metrics['processed_count']}")
print(f"Failed: {metrics['failed_count']}")
print(f"Timeouts: {metrics['timeout_count']}")
```

#### Solutions

##### 1. Scale Workers
```python
from src.reliability.rate_limiting import QueueManager

queue = QueueManager.get_instance("request_queue")

# Increase workers
await queue.scale_workers(new_worker_count=50)

# Increase queue capacity
queue.resize_queue(new_max_size=5000)
```

##### 2. Optimize Worker Processing
```python
# Profile worker performance
python scripts/profiling/profile_worker_performance.py

# Identify slow operations
python scripts/monitoring/identify_slow_workers.py
```

##### 3. Enable Backpressure
```python
from src.reliability.rate_limiting import BackpressureHandler

# Activate backpressure to slow incoming requests
handler = BackpressureHandler(
    name="api_backpressure",
    queue_manager=queue,
    rate_limiter=rate_limiter,
    alert_threshold=0.8
)

await handler.check_and_apply_backpressure()
```

##### 4. Scale Horizontally
```bash
# Add more service instances
kubectl scale deployment api-server --replicas=20 -n production
```

---

### Issue: Cache Performance Problems

#### Symptoms
- Low cache hit rate (< 70%)
- High cache memory usage
- Slow cache responses

#### Diagnostic Steps

```bash
# 1. Check Redis stats
redis-cli INFO stats

# 2. Check memory usage
redis-cli INFO memory

# 3. Check slow log
redis-cli SLOWLOG GET 10

# 4. Check client connections
redis-cli INFO clients
```

#### Solutions

##### 1. Low Hit Rate
```bash
# Analyze cache keys
redis-cli --scan --pattern '*' | head -100

# Check key TTLs
python scripts/cache/analyze_ttls.py

# Increase TTL for stable data
python scripts/cache/adjust_ttl.py --pattern='user:*' --ttl=3600
```

##### 2. High Memory Usage
```bash
# Check key sizes
redis-cli --bigkeys

# Evict large keys
python scripts/cache/evict_large_keys.py --threshold=10MB

# Enable eviction policy
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

##### 3. Slow Responses
```bash
# Check network latency
redis-cli --latency

# Check if Redis is swapping
redis-cli INFO stats | grep swap

# Solution: Increase Redis resources
kubectl set resources statefulset redis --limits=memory=8Gi -n production
```

---

## Advanced Debugging

### Enable Debug Logging

```python
# Temporarily enable debug logging
import logging
import structlog

# Configure structlog for debug level
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG)
)

# Run operation with debug logging
# Debug logs will now include detailed information
```

### Distributed Tracing

```bash
# Check traces in Jaeger
curl 'http://jaeger:16686/api/traces?service=api-server&limit=20'

# Analyze slow traces
python scripts/tracing/analyze_slow_traces.py --threshold=2000ms
```

### Profiling

```python
# CPU profiling
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run operation
result = expensive_operation()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

---

## Emergency Procedures

### Kill Switch (Disable All Traffic)

```bash
# Emergency traffic shutdown
kubectl scale deployment --all --replicas=0 -n production

# Enable maintenance mode
python scripts/maintenance/enable_maintenance_mode.py

# Update status page
python scripts/status/update_status.py --status=maintenance
```

### Force Restart All Services

```bash
# Nuclear option: restart everything
kubectl rollout restart deployment -n production

# Monitor recovery
watch kubectl get pods -n production
```

### Emergency Contact List

- **On-Call Engineer**: PagerDuty
- **Database Team**: db-team@sergas.com
- **Platform Team**: platform-team@sergas.com
- **Security Team**: security@sergas.com
- **CTO**: cto@sergas.com

---

## Troubleshooting Checklist

When troubleshooting any issue:

- [ ] Identify and document symptoms
- [ ] Check monitoring dashboards
- [ ] Review recent deployments/changes
- [ ] Check error logs
- [ ] Verify external dependencies
- [ ] Review metrics (CPU, memory, network)
- [ ] Check database health
- [ ] Verify cache health
- [ ] Review circuit breaker status
- [ ] Test with curl/API client
- [ ] Document findings
- [ ] Implement fix
- [ ] Verify fix worked
- [ ] Update runbooks if needed
- [ ] Schedule post-mortem

---

## Additional Resources

- **Monitoring Dashboards**: https://grafana.sergas.com
- **Log Aggregation**: https://kibana.sergas.com
- **Tracing**: https://jaeger.sergas.com
- **Status Page**: https://status.sergas.com
- **Documentation**: https://docs.sergas.com
