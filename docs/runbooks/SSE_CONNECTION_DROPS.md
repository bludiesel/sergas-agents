# Runbook: SSE Connection Drops

**Service**: Sergas Super Account Manager
**Component**: AG UI Protocol - Server-Sent Events (SSE)
**Severity**: High
**Last Updated**: 2025-10-19

## Overview

This runbook covers troubleshooting and recovery procedures for Server-Sent Events (SSE) connection drops in the AG UI Protocol implementation.

## Symptoms

- Frontend shows "Connection lost" warnings
- Real-time agent updates not reaching UI
- Approval requests timing out
- Event stream reconnecting frequently
- Error logs showing SSE disconnections

## Impact Assessment

| Severity | Impact | Response Time |
|----------|--------|---------------|
| **Critical** | No approvals possible, system blocked | 15 minutes |
| **High** | Intermittent failures, degraded UX | 1 hour |
| **Medium** | Occasional reconnects, minor delays | 4 hours |

## Diagnostic Steps

### 1. Check SSE Endpoint Health

```bash
# Test SSE endpoint connectivity
curl -N -H "Accept: text/event-stream" \
  https://api.sergas-agents.com/api/sse/session/{session_id}

# Expected: Stream of events
# Failure: HTTP error or immediate disconnect
```

### 2. Check Load Balancer Configuration

```bash
# Verify ALB timeout settings
aws elbv2 describe-target-groups \
  --target-group-arns arn:aws:elasticloadbalancing:... \
  --query 'TargetGroups[0].TargetGroupAttributes'

# Look for: deregistration_delay.timeout_seconds (should be 300+)
# Look for: deregistration_delay.connection_termination.enabled (should be false)
```

### 3. Check Application Logs

```bash
# SSH to application host
ssh app-host-1

# Check SSE handler logs
tail -f /app/logs/sse.log | grep -E "disconnect|timeout|error"

# Check for timeout patterns
grep "SSE keepalive timeout" /app/logs/sse.log | tail -20
```

### 4. Check Network Layer

```bash
# Check for packet loss
ping -c 100 app-host-1

# Check TCP connection states
netstat -ant | grep :8000 | grep ESTABLISHED | wc -l

# Check for SYN floods
netstat -ant | grep SYN_RECV | wc -l
```

### 5. Check Redis Connection Pool

```bash
# Connect to Redis
redis-cli -h redis-host

# Check active connections
INFO clients

# Check connection timeouts
CONFIG GET timeout

# Expected: timeout 0 (no timeout)
# If timeout > 0: connections may be closing prematurely
```

## Common Root Causes

### 1. Load Balancer Idle Timeout

**Symptom**: Connections drop after exactly 60 seconds
**Root Cause**: ALB idle timeout shorter than SSE keepalive interval
**Fix**:

```bash
# Increase ALB idle timeout to 300 seconds
aws elbv2 modify-target-group-attribute \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --attributes Key=deregistration_delay.timeout_seconds,Value=300
```

### 2. Application Keepalive Misconfiguration

**Symptom**: No heartbeat events sent to client
**Root Cause**: SSE keepalive disabled or interval too long
**Fix**:

```python
# Edit src/api/sse_handler.py
SSE_KEEPALIVE_INTERVAL = 15  # Send heartbeat every 15 seconds
SSE_CLIENT_TIMEOUT = 60       # Close if no acknowledgment in 60s
```

### 3. Nginx Reverse Proxy Buffering

**Symptom**: Events buffered, delayed delivery
**Root Cause**: Nginx buffering SSE responses
**Fix**:

```nginx
# Edit /etc/nginx/nginx.conf
location /api/sse/ {
    proxy_pass http://backend;
    proxy_buffering off;
    proxy_cache off;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    chunked_transfer_encoding off;
    proxy_read_timeout 3600s;
}
```

### 4. Client-Side Timeout

**Symptom**: Frontend logs "EventSource timeout"
**Root Cause**: Frontend EventSource timeout shorter than server keepalive
**Fix**:

```typescript
// Edit frontend/src/hooks/useAgentState.ts
const eventSource = new EventSource(url, {
  withCredentials: true,
  heartbeatTimeout: 30000, // 30 seconds
});
```

### 5. Database Connection Exhaustion

**Symptom**: SSE connections fail under load
**Root Cause**: DB connection pool exhausted, blocking SSE handlers
**Fix**:

```bash
# Check PostgreSQL connection count
psql -h postgres-host -U sergas -c "SELECT count(*) FROM pg_stat_activity;"

# Increase connection pool size
# Edit config/database.yml
pool_size: 50
max_overflow: 20
```

## Resolution Procedures

### Quick Fix (Temporary)

```bash
# 1. Restart application containers
docker-compose -f docker/production/docker-compose.yml restart app

# 2. Clear Redis connection state
redis-cli FLUSHDB

# 3. Verify SSE endpoint
curl -N https://api.sergas-agents.com/health/sse
```

### Permanent Fix by Root Cause

#### For Load Balancer Issues

```bash
# Step 1: Increase ALB idle timeout
aws elbv2 modify-target-group-attribute \
  --target-group-arn $TG_ARN \
  --attributes Key=deregistration_delay.timeout_seconds,Value=300

# Step 2: Enable connection draining
aws elbv2 modify-target-group-attribute \
  --target-group-arn $TG_ARN \
  --attributes Key=deregistration_delay.connection_termination.enabled,Value=false

# Step 3: Verify changes
aws elbv2 describe-target-group-attributes --target-group-arn $TG_ARN
```

#### For Application Configuration Issues

```bash
# Step 1: Update SSE configuration
cat > config/sse.yml <<EOF
keepalive_interval: 15
client_timeout: 60
max_connections_per_session: 1
reconnect_backoff_max: 30
EOF

# Step 2: Deploy configuration
kubectl apply -f k8s/configmap-sse.yml

# Step 3: Rolling restart
kubectl rollout restart deployment/sergas-app
kubectl rollout status deployment/sergas-app
```

#### For Network Issues

```bash
# Step 1: Check security group rules
aws ec2 describe-security-groups --group-ids sg-xxx

# Step 2: Ensure port 8000 allows long-lived connections
# Security Group: sergas-app-sg
# Inbound: TCP 8000 from ALB security group

# Step 3: Check NACLs for stateful tracking
aws ec2 describe-network-acls --filters "Name=vpc-id,Values=vpc-xxx"
```

## Validation

After applying fixes, validate SSE functionality:

```bash
# 1. Test SSE connection stability
./scripts/validate/test_sse_connection.sh 300  # 5 minutes

# 2. Monitor reconnection rate
watch -n 5 'grep "SSE reconnect" /app/logs/sse.log | tail -10'

# 3. Check metrics in Grafana
# Dashboard: AG UI Protocol Monitoring
# Panel: SSE Connection Duration
# Expected: >80% connections lasting >5 minutes
```

## Monitoring & Alerts

### Key Metrics to Watch

```promql
# SSE connection duration (should be high)
histogram_quantile(0.95, rate(sse_connection_duration_seconds_bucket[5m]))

# SSE disconnect rate (should be low)
rate(sse_disconnects_total[5m])

# SSE reconnect attempts (should be minimal)
rate(sse_reconnects_total[5m])

# Active SSE connections
sse_active_connections
```

### Alert Thresholds

```yaml
# config/alerts/sse_alerts.yml
groups:
  - name: sse_connection_health
    rules:
      - alert: HighSSEDisconnectRate
        expr: rate(sse_disconnects_total[5m]) > 0.1
        for: 5m
        severity: warning

      - alert: LowSSEConnectionDuration
        expr: histogram_quantile(0.95, rate(sse_connection_duration_seconds_bucket[5m])) < 60
        for: 10m
        severity: critical
```

## Escalation Path

1. **Level 1** (0-15 min): On-call DevOps engineer
   - Run diagnostic steps
   - Apply quick fix if obvious

2. **Level 2** (15-30 min): Backend team lead
   - Deep application debugging
   - Review recent code changes

3. **Level 3** (30+ min): CTO + Anthropic support
   - Architectural review
   - Vendor support engagement

## Post-Incident Review

After resolution, document:

1. **Root Cause**: What caused the SSE drops?
2. **Detection Time**: How long until we noticed?
3. **Resolution Time**: How long to fix?
4. **Lessons Learned**: What can we improve?
5. **Action Items**: Preventive measures

## Related Runbooks

- `/docs/runbooks/APPROVAL_TIMEOUTS.md`
- `/docs/runbooks/DATABASE_ISSUES.md`
- `/docs/runbooks/incident_response.md`

## References

- AG UI Protocol Spec: `/docs/architecture/SYSTEM_ARCHITECTURE_With_AG_UI_Protocol.md`
- SSE Implementation: `/src/api/sse_handler.py`
- Frontend EventSource: `/frontend/src/hooks/useAgentState.ts`

---

**Last Incident**: None
**Next Review**: 2025-11-19
