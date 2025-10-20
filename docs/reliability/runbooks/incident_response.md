# Incident Response Runbook

## Overview

This runbook provides step-by-step procedures for responding to production incidents in the Sergas Agents system.

## Incident Severity Levels

### Severity 1 (Critical)
- **Definition**: Complete service outage or data loss
- **Response Time**: Immediate (< 5 minutes)
- **Escalation**: CTO, Engineering Manager, On-call Engineer

### Severity 2 (High)
- **Definition**: Major functionality degraded, affecting multiple users
- **Response Time**: < 15 minutes
- **Escalation**: Engineering Manager, On-call Engineer

### Severity 3 (Medium)
- **Definition**: Minor functionality impaired, workaround available
- **Response Time**: < 1 hour
- **Escalation**: On-call Engineer

### Severity 4 (Low)
- **Definition**: Cosmetic issues, no functional impact
- **Response Time**: Next business day
- **Escalation**: Standard ticket queue

## Incident Response Process

### 1. Detection and Alert (0-5 minutes)

**Automated Detection:**
```bash
# Check health endpoints
curl https://api.sergas.com/health

# View recent alerts
kubectl logs -n monitoring alertmanager-0 --tail=100

# Check circuit breaker status
python -m src.reliability.check_circuit_breakers
```

**Manual Detection:**
- User reports
- Monitoring dashboard alerts
- Performance degradation

**Actions:**
1. Acknowledge alert in PagerDuty/monitoring system
2. Create incident channel in Slack: `#incident-YYYY-MM-DD-description`
3. Post initial status update

### 2. Assessment (5-15 minutes)

**Quick Checks:**
```bash
# System health overview
python scripts/reliability/health_check_all.py

# Database health
python scripts/db/check_db_health.py

# Service status
kubectl get pods -n production
kubectl describe pod <pod-name> -n production

# Recent deployments
kubectl rollout history deployment -n production

# Error rates
python scripts/monitoring/check_error_rates.py --last 30m
```

**Determine Severity:**
- Impact: How many users affected?
- Scope: Which services/features?
- Data integrity: Any data loss risk?

**Document Initial Assessment:**
```markdown
## Incident Assessment
- **Time Detected**: 2025-10-19 14:23 UTC
- **Severity**: SEV-2
- **Impact**: Authentication service degraded, 30% of users affected
- **Services**: auth-service, session-manager
- **Data Risk**: None identified
```

### 3. Immediate Mitigation (15-30 minutes)

**Common Mitigation Actions:**

#### Service Restart
```bash
# Restart specific service
kubectl rollout restart deployment auth-service -n production

# Watch rollout
kubectl rollout status deployment auth-service -n production
```

#### Rollback Deployment
```bash
# View deployment history
kubectl rollout history deployment auth-service -n production

# Rollback to previous version
kubectl rollout undo deployment auth-service -n production

# Rollback to specific revision
kubectl rollout undo deployment auth-service --to-revision=3 -n production
```

#### Enable Circuit Breakers
```python
from src.resilience.circuit_breaker_manager import CircuitBreakerManager

# Force open circuit to failing service
manager = CircuitBreakerManager()
manager.get_breaker("external_api").reset()
```

#### Activate Graceful Degradation
```python
from src.reliability.graceful_degradation import DegradationManager, DegradationLevel

# Set degradation level
degradation = DegradationManager()
degradation.set_degradation_level(DegradationLevel.DEGRADED)

# Disable specific features
degradation.feature_flags.disable("recommendations")
degradation.feature_flags.disable("analytics")
```

#### Database Issues
```bash
# Check database connections
psql -h db-host -U sergas -c "SELECT count(*) FROM pg_stat_activity;"

# Kill long-running queries
psql -h db-host -U sergas -c "
  SELECT pg_terminate_backend(pid)
  FROM pg_stat_activity
  WHERE state = 'active' AND query_start < now() - interval '5 minutes';"

# Check replication lag
psql -h db-replica -U sergas -c "
  SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()));"
```

#### Cache Issues
```bash
# Clear Redis cache
redis-cli FLUSHDB

# Check Redis memory
redis-cli INFO memory

# Restart Redis
kubectl rollout restart statefulset redis -n production
```

### 4. Root Cause Analysis (Parallel with Mitigation)

**Log Analysis:**
```bash
# Application logs
kubectl logs -n production deployment/auth-service --tail=1000 | grep ERROR

# Aggregated logs with timestamps
kubectl logs -n production deployment/auth-service --since=30m --timestamps

# Stream logs
kubectl logs -n production -f deployment/auth-service
```

**Metrics Analysis:**
```bash
# Check Prometheus metrics
curl 'http://prometheus:9090/api/v1/query?query=rate(http_requests_total{job="auth-service"}[5m])'

# Error rate
curl 'http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~"5.."}[5m])'

# Response time percentiles
curl 'http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95, http_request_duration_seconds_bucket)'
```

**Common Root Causes:**
1. Recent deployment introduced bug
2. External dependency failure
3. Database connection pool exhaustion
4. Memory leak
5. Rate limit exceeded
6. Certificate expiration
7. Configuration error

### 5. Communication

**Status Page Updates:**
```markdown
## [INVESTIGATING] Authentication Service Degraded

**Posted:** 2025-10-19 14:30 UTC

We are investigating reports of authentication failures. Our team is actively working on the issue.

**Update 1** (14:45 UTC): We have identified the root cause as a database connection pool issue and are implementing a fix.

**Update 2** (15:00 UTC): Fix deployed. Monitoring for recovery.

**Resolved** (15:15 UTC): Authentication service fully recovered. We are continuing to monitor.
```

**Internal Communication:**
- Post updates to incident channel every 15-30 minutes
- Use threaded messages for technical details
- Keep stakeholders informed

**External Communication:**
- Update status page
- Send customer notifications for SEV-1/SEV-2
- Prepare customer-facing incident report

### 6. Resolution (Variable Timeline)

**Verification Checklist:**
```bash
# All health checks passing
python scripts/reliability/health_check_all.py

# Error rates back to normal
python scripts/monitoring/check_error_rates.py

# Response times acceptable
python scripts/monitoring/check_response_times.py

# No active circuit breakers
python scripts/reliability/check_circuit_breakers.py

# Queue depths normal
python scripts/monitoring/check_queue_depths.py
```

**Confirm Resolution:**
- [ ] All health checks green
- [ ] Error rates < baseline
- [ ] Response times < SLA
- [ ] No user reports for 15+ minutes
- [ ] Monitoring dashboards normal
- [ ] Stakeholders notified

### 7. Post-Incident (24-48 hours)

**Post-Mortem Document:**
```markdown
# Post-Mortem: Authentication Service Outage

## Incident Summary
- **Date**: 2025-10-19
- **Duration**: 52 minutes
- **Severity**: SEV-2
- **Impact**: 30% of users unable to authenticate

## Timeline
- 14:23 - Alert fired: High error rate in auth-service
- 14:28 - Incident channel created, team assembled
- 14:35 - Root cause identified: Database connection pool exhaustion
- 14:42 - Fix deployed: Increased connection pool size
- 14:50 - Service recovering
- 15:15 - Full recovery confirmed

## Root Cause
Database connection pool was sized for average load (20 connections) but spike traffic required 50+ connections.

## Contributing Factors
1. Connection pool configuration not updated after recent traffic increase
2. No alerting on connection pool utilization
3. Load testing didn't simulate peak traffic patterns

## Resolution
1. Increased connection pool from 20 to 50 connections
2. Added connection pool monitoring
3. Updated load test scenarios

## Action Items
- [ ] Add connection pool utilization alerts (Owner: DevOps, Due: 2025-10-22)
- [ ] Review all connection pool configurations (Owner: Backend, Due: 2025-10-25)
- [ ] Implement circuit breaker for database connections (Owner: Platform, Due: 2025-10-30)
- [ ] Update load test scenarios to include traffic spikes (Owner: QA, Due: 2025-10-27)
- [ ] Document connection pool sizing guidelines (Owner: Backend, Due: 2025-10-24)

## Lessons Learned
1. **What went well**: Fast detection, clear communication, quick mitigation
2. **What could improve**: Better monitoring, proactive capacity planning
3. **Where we got lucky**: Issue occurred during business hours with full team available
```

## Common Incident Scenarios

### Database Connection Failures

**Symptoms:**
- "Too many connections" errors
- Slow query responses
- Connection timeouts

**Diagnosis:**
```bash
# Check active connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check connection limits
psql -c "SHOW max_connections;"

# Identify connection sources
psql -c "SELECT application_name, count(*) FROM pg_stat_activity GROUP BY application_name;"
```

**Mitigation:**
```bash
# Kill idle connections
psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < now() - interval '10 minutes';"

# Restart connection-heavy services
kubectl rollout restart deployment api-server -n production
```

### Circuit Breaker Opened

**Symptoms:**
- CircuitBreakerOpenError in logs
- Degraded functionality
- Fallback responses

**Diagnosis:**
```python
from src.resilience.circuit_breaker_manager import CircuitBreakerManager

manager = CircuitBreakerManager()
metrics = manager.get_all_metrics()
for name, m in metrics.items():
    if m['state'] == 'open':
        print(f"Circuit {name} is OPEN: {m}")
```

**Mitigation:**
```python
# Check if underlying service recovered
# If yes, reset circuit breaker
manager.get_breaker("external_api").reset()

# If no, enable fallback
from src.reliability.graceful_degradation import DegradationManager
degradation = DegradationManager()
degradation.execute_with_fallback("external_api", fallback_strategy="cached")
```

### Memory Leak

**Symptoms:**
- Increasing memory usage
- OOMKilled pod restarts
- Slow performance over time

**Diagnosis:**
```bash
# Check memory usage
kubectl top pods -n production

# Check pod restart history
kubectl get pods -n production -o json | jq '.items[] | {name: .metadata.name, restarts: .status.containerStatuses[].restartCount}'

# Get memory profile
kubectl exec -it <pod-name> -n production -- python -m memory_profiler app.py
```

**Mitigation:**
```bash
# Temporary: Increase memory limits
kubectl set resources deployment api-server --limits=memory=2Gi -n production

# Restart to clear memory
kubectl rollout restart deployment api-server -n production

# Long-term: Fix code, add memory monitoring
```

### External Dependency Failure

**Symptoms:**
- Timeout errors from external APIs
- Failed integrations
- Zoho/external service errors

**Diagnosis:**
```bash
# Check external service status
curl -I https://api.external-service.com/health

# Review circuit breaker state
python -c "from src.resilience.circuit_breaker_manager import CircuitBreakerManager; print(CircuitBreakerManager().get_all_metrics())"
```

**Mitigation:**
```python
# Enable graceful degradation
from src.reliability.graceful_degradation import DegradationManager

manager = DegradationManager()
manager.execute_with_fallback(
    "zoho_integration",
    fallback_strategy="cached_fallback"
)
```

## Escalation Procedures

### Escalation Criteria
- Incident duration > 30 minutes
- Multiple services affected
- Data integrity concerns
- Severity increase during incident

### Escalation Contacts
1. **On-Call Engineer**: PagerDuty rotation
2. **Engineering Manager**: manager@sergas.com
3. **CTO**: cto@sergas.com
4. **CEO**: (SEV-1 only) ceo@sergas.com

### Escalation Commands
```bash
# Page on-call engineer
pagerduty-cli trigger --service-key=<key> --description="SEV-2: Auth service down"

# Send executive summary
python scripts/incidents/send_executive_summary.py --incident-id=INC-2025-001
```

## Tools and Resources

### Monitoring Dashboards
- **System Health**: https://grafana.sergas.com/d/system-health
- **Application Metrics**: https://grafana.sergas.com/d/app-metrics
- **Database Performance**: https://grafana.sergas.com/d/db-performance

### Log Aggregation
- **Kibana**: https://kibana.sergas.com
- **CloudWatch**: https://console.aws.amazon.com/cloudwatch

### Status Communication
- **Status Page**: https://status.sergas.com
- **Incident Channel Template**: #incident-YYYY-MM-DD-description

### Scripts Location
- Health checks: `/scripts/reliability/`
- Monitoring: `/scripts/monitoring/`
- Recovery: `/scripts/recovery/`
