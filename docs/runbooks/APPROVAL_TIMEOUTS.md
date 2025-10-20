# Runbook: Approval Timeouts

**Service**: Sergas Super Account Manager
**Component**: Approval Workflow System
**Severity**: High
**Last Updated**: 2025-10-19

## Overview

This runbook addresses timeout issues in the human-in-the-loop approval workflow, where account owner approvals fail to complete within expected timeframes.

## Symptoms

- Approval requests stuck in "PENDING" state
- Timeout errors in approval gate logs
- Recommendations not executing despite approval
- Frontend shows infinite loading state
- Audit logs missing approval completion events

## Impact Assessment

| Severity | Impact | Response Time |
|----------|--------|---------------|
| **Critical** | All approvals blocked, no CRM updates | 15 minutes |
| **High** | >50% approval failures | 1 hour |
| **Medium** | Sporadic timeouts, retries work | 4 hours |

## Diagnostic Steps

### 1. Check Approval Gate Status

```bash
# SSH to application server
ssh app-host-1

# Check approval gate service
ps aux | grep approval_gate

# View recent approval logs
tail -f /app/logs/approval_gate.log | grep -E "timeout|pending|stuck"

# Check pending approvals count
redis-cli HGETALL "approvals:pending:*" | wc -l
```

### 2. Check Database State

```bash
# Connect to PostgreSQL
psql -h postgres-host -U sergas_user -d sergas_agent_db

# Check stuck approvals
SELECT
  recommendation_id,
  account_id,
  owner_id,
  status,
  created_at,
  NOW() - created_at as age
FROM approval_workflow
WHERE status = 'PENDING'
  AND created_at < NOW() - INTERVAL '10 minutes'
ORDER BY created_at DESC;

# Check for long-running transactions
SELECT pid, usename, state, query_start, NOW() - query_start as duration
FROM pg_stat_activity
WHERE state = 'active' AND NOW() - query_start > INTERVAL '5 minutes';
```

### 3. Check Redis Session State

```bash
# Connect to Redis
redis-cli -h redis-host

# Check active sessions
KEYS "session:*"

# Check specific approval state
HGETALL "approval:rec-{recommendation_id}"

# Check for expired TTLs
TTL "approval:rec-{recommendation_id}"
# If -2: Key doesn't exist (expired)
# If -1: Key has no expiry (should not happen)
# If >0: Time remaining in seconds
```

### 4. Check Network Connectivity

```bash
# Test database connectivity
nc -zv postgres-host 5432

# Test Redis connectivity
nc -zv redis-host 6379

# Check for network latency
ping -c 10 postgres-host

# Check DNS resolution
nslookup postgres-host
```

### 5. Check Application Metrics

```bash
# View Prometheus metrics
curl http://localhost:9090/metrics | grep approval

# Key metrics:
# - approval_requests_total
# - approval_timeouts_total
# - approval_duration_seconds
# - approval_queue_size
```

## Common Root Causes

### 1. Database Transaction Lock

**Symptom**: Approvals hang indefinitely
**Root Cause**: Long-running transaction holding row lock
**Fix**:

```sql
-- Identify blocking queries
SELECT
  blocked.pid AS blocked_pid,
  blocked.usename AS blocked_user,
  blocking.pid AS blocking_pid,
  blocking.usename AS blocking_user,
  blocked.query AS blocked_query,
  blocking.query AS blocking_query
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking
  ON blocking.pid = ANY(pg_blocking_pids(blocked.pid))
WHERE blocked.wait_event_type = 'Lock';

-- Terminate blocking query (use with caution!)
SELECT pg_terminate_backend(blocking_pid);
```

### 2. Redis Key Expiration

**Symptom**: Approval state lost, frontend shows "not found"
**Root Cause**: Redis TTL too short for approval workflow
**Fix**:

```python
# Edit src/approval/approval_gate.py
APPROVAL_TTL = 3600  # 1 hour (was 600 = 10 minutes)

# Update existing approvals
redis_client.expire(f"approval:{recommendation_id}", 3600)
```

### 3. Connection Pool Exhaustion

**Symptom**: Timeouts under load, works when retried
**Root Cause**: All database connections in use
**Fix**:

```python
# Edit config/database.py
DATABASE_POOL_SIZE = 50  # Increase from 20
DATABASE_MAX_OVERFLOW = 20  # Increase from 10
DATABASE_POOL_TIMEOUT = 30  # Seconds to wait for connection
```

### 4. Approval Gate Process Crash

**Symptom**: No approvals processing, no error logs
**Root Cause**: ApprovalGate service not running
**Fix**:

```bash
# Check if process is running
systemctl status approval-gate

# Restart service
systemctl restart approval-gate

# Check logs for crash reason
journalctl -u approval-gate -n 100 --no-pager
```

### 5. Frontend Timeout Configuration

**Symptom**: Frontend shows timeout before backend completes
**Root Cause**: Frontend timeout shorter than backend processing time
**Fix**:

```typescript
// Edit frontend/src/services/approvalService.ts
const APPROVAL_TIMEOUT_MS = 60000;  // 60 seconds (was 30000)

const response = await fetch('/api/approvals', {
  method: 'POST',
  body: JSON.stringify(approvalRequest),
  signal: AbortSignal.timeout(APPROVAL_TIMEOUT_MS),
});
```

## Resolution Procedures

### Quick Fix (Immediate Relief)

```bash
# 1. Restart approval gate service
systemctl restart approval-gate

# 2. Clear stuck approvals from Redis
redis-cli --scan --pattern "approval:*" | xargs redis-cli DEL

# 3. Reset pending approvals in database
psql -h postgres-host -U sergas_user -d sergas_agent_db -c \
  "UPDATE approval_workflow SET status = 'TIMEOUT' WHERE status = 'PENDING' AND created_at < NOW() - INTERVAL '30 minutes';"

# 4. Restart application containers
docker-compose restart app
```

### Permanent Fix by Root Cause

#### For Database Lock Issues

```bash
# Step 1: Enable statement logging
psql -h postgres-host -U sergas_user -c \
  "ALTER SYSTEM SET log_lock_waits = 'on';"
psql -h postgres-host -U sergas_user -c \
  "ALTER SYSTEM SET deadlock_timeout = '1s';"
psql -h postgres-host -U sergas_user -c "SELECT pg_reload_conf();"

# Step 2: Add index on approval_workflow.status
psql -h postgres-host -U sergas_user -d sergas_agent_db -c \
  "CREATE INDEX CONCURRENTLY idx_approval_workflow_status_created ON approval_workflow(status, created_at);"

# Step 3: Use shorter transactions in application code
# Edit src/approval/approval_gate.py
# Use autocommit=True for read-only queries
```

#### For Redis Expiration Issues

```bash
# Step 1: Update Redis configuration
cat > config/redis.yml <<EOF
approval_ttl: 3600  # 1 hour
session_ttl: 7200   # 2 hours
max_pending_approvals: 1000
EOF

# Step 2: Deploy configuration
kubectl apply -f k8s/configmap-redis.yml

# Step 3: Add Redis backup for critical keys
# Edit src/approval/approval_gate.py
# Store approval state in both Redis AND PostgreSQL
```

#### For Connection Pool Issues

```bash
# Step 1: Increase connection pool size
cat > config/database.yml <<EOF
pool_size: 50
max_overflow: 20
pool_timeout: 30
pool_recycle: 3600
EOF

# Step 2: Add connection pool monitoring
# Edit src/database/pool_monitor.py
# Expose pool size and wait time as Prometheus metrics

# Step 3: Configure PostgreSQL max_connections
psql -h postgres-host -U postgres -c \
  "ALTER SYSTEM SET max_connections = 200;"
# Restart PostgreSQL for change to take effect
```

## Validation

After applying fixes, validate approval workflow:

```bash
# 1. Create test approval request
./scripts/validate/test_approval_workflow.sh

# Expected output:
# ✓ Approval created: rec-test-123
# ✓ Approval visible in frontend
# ✓ Approval approved successfully
# ✓ Action executed in Zoho CRM
# ✓ Audit log entry created

# 2. Load test approval system
./scripts/validate/load_test_approvals.sh --concurrent=10 --duration=60

# Expected metrics:
# - 0% timeout rate
# - <2s average approval latency
# - <5s p95 approval latency

# 3. Monitor for 30 minutes
watch -n 10 'redis-cli HGETALL approvals:pending:* | wc -l'
# Should stay < 100 under normal load
```

## Monitoring & Alerts

### Key Metrics to Watch

```promql
# Approval timeout rate (should be <1%)
rate(approval_timeouts_total[5m]) / rate(approval_requests_total[5m]) * 100

# Approval duration p95 (should be <5s)
histogram_quantile(0.95, rate(approval_duration_seconds_bucket[5m]))

# Pending approvals count (should be <50)
approval_queue_size

# Database connection pool exhaustion
(db_connections_in_use / db_connections_max) * 100
```

### Alert Thresholds

```yaml
# config/alerts/approval_alerts.yml
groups:
  - name: approval_workflow_health
    rules:
      - alert: HighApprovalTimeoutRate
        expr: rate(approval_timeouts_total[5m]) / rate(approval_requests_total[5m]) > 0.05
        for: 5m
        severity: critical
        annotations:
          summary: "{{ $value | humanizePercentage }} of approvals timing out"

      - alert: SlowApprovalProcessing
        expr: histogram_quantile(0.95, rate(approval_duration_seconds_bucket[5m])) > 5
        for: 10m
        severity: warning

      - alert: ApprovalQueueBacklog
        expr: approval_queue_size > 100
        for: 5m
        severity: warning
```

## Cleanup Procedures

After incident resolution, clean up stuck approvals:

```sql
-- Archive timed-out approvals
INSERT INTO approval_workflow_history
SELECT * FROM approval_workflow
WHERE status = 'TIMEOUT' AND created_at < NOW() - INTERVAL '7 days';

-- Delete archived records
DELETE FROM approval_workflow
WHERE status = 'TIMEOUT' AND created_at < NOW() - INTERVAL '7 days';

-- Update statistics
VACUUM ANALYZE approval_workflow;
```

## Escalation Path

1. **Level 1** (0-15 min): On-call backend engineer
   - Check logs and metrics
   - Apply quick fix

2. **Level 2** (15-30 min): Database administrator
   - Investigate lock contention
   - Optimize queries

3. **Level 3** (30+ min): Architecture team
   - Review workflow design
   - Implement architectural fixes

## Post-Incident Review

Document the following:

1. **Timeline**: When did timeouts start?
2. **Root Cause**: Database locks? Redis expiration? Network?
3. **User Impact**: How many approvals failed?
4. **Resolution**: What fixed it?
5. **Prevention**: How do we prevent recurrence?

## Related Runbooks

- `/docs/runbooks/DATABASE_ISSUES.md`
- `/docs/runbooks/SSE_CONNECTION_DROPS.md`
- `/docs/runbooks/incident_response.md`

## References

- Approval Workflow Spec: `/docs/architecture/SYSTEM_ARCHITECTURE_With_AG_UI_Protocol.md#approval-workflow`
- Implementation: `/src/approval/approval_gate.py`
- Database Schema: `/migrations/versions/001_approval_workflow.py`

---

**Last Incident**: None
**Next Review**: 2025-11-19
