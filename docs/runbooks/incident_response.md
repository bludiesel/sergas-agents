# Incident Response Runbook

## Purpose

This runbook provides step-by-step procedures for responding to production incidents in the Sergas Super Account Manager system.

## Severity Classification

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| **P0** | Critical - Complete outage | Immediate | API down, database unavailable, data loss |
| **P1** | High - Major degradation | 15 minutes | High error rate, slow performance, auth failures |
| **P2** | Medium - Partial impact | 1 hour | Non-critical feature broken, increased latency |
| **P3** | Low - Minor impact | 4 hours | UI glitch, logging issue, non-blocking warning |

---

## Incident Response Workflow

```
DETECTION → TRIAGE → INVESTIGATION → MITIGATION → RESOLUTION → POST-MORTEM
```

---

## Step 1: Detection & Alerting

### Alert Sources

- **Monitoring**: Prometheus/Grafana alerts
- **Users**: Support tickets, emails
- **Automated**: Health check failures
- **External**: Zoho/Partner notifications

### First Actions (within 2 minutes)

```bash
# 1. Acknowledge alert
curl -X POST http://alertmanager:9093/api/v2/alerts/acknowledge

# 2. Create incident channel
# Slack: Create #incident-YYYYMMDD-HH

# 3. Run quick diagnostic
./scripts/quick-diagnostic.sh > /tmp/incident-$(date +%s).log

# 4. Check status page
curl https://status.sergas.com/api/status
```

---

## Step 2: Triage

### Severity Assessment

**Questions to ask:**
1. How many users affected?
2. Is data at risk?
3. Is service completely unavailable or degraded?
4. Is this a security incident?

### Assign Severity

```bash
# P0: Complete outage
if [ "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)" != "200" ]; then
    SEVERITY="P0"
    PAGE_ONCALL=true
fi

# P1: High error rate
ERROR_RATE=$(curl -s 'http://prometheus:9090/api/v1/query?query=rate(sergas_http_requests_total{status=~"5.."}[5m])/rate(sergas_http_requests_total[5m])*100' | jq -r '.data.result[0].value[1]')
if (( $(echo "$ERROR_RATE > 10" | bc -l) )); then
    SEVERITY="P1"
fi
```

### Incident Commander Assignment

**P0/P1**: On-call engineer becomes Incident Commander
**P2/P3**: First responder handles incident

---

## Step 3: Investigation

### System Health Check

```bash
#!/bin/bash
# incident-investigation.sh

echo "=== Incident Investigation Report ==="
echo "Timestamp: $(date)"
echo ""

# Application status
echo "1. APPLICATION STATUS:"
systemctl status sergas-app | head -10

# Recent errors
echo -e "\n2. RECENT ERRORS (last 10 minutes):"
journalctl -u sergas-app --since "10 minutes ago" | grep -i "ERROR\|CRITICAL" | tail -20

# Resource usage
echo -e "\n3. RESOURCE USAGE:"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')"
echo "Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo "Disk: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 " used)"}')"

# Database connections
echo -e "\n4. DATABASE:"
psql -d sergas_prod -c "SELECT count(*) as connections, state FROM pg_stat_activity GROUP BY state;"

# Redis status
echo -e "\n5. REDIS:"
redis-cli ping
redis-cli info memory | grep used_memory_human

# API health
echo -e "\n6. API HEALTH:"
curl -s http://localhost:8000/health | jq

# Recent deployments
echo -e "\n7. RECENT DEPLOYMENTS:"
git log --oneline -5

# Active alerts
echo -e "\n8. ACTIVE ALERTS:"
curl -s http://alertmanager:9093/api/v2/alerts | jq '.[] | {name: .labels.alertname, severity: .labels.severity}'
```

### Common Investigation Paths

#### High Error Rate

```bash
# Find most common errors
journalctl -u sergas-app --since "1 hour ago" | \
  grep ERROR | \
  awk -F'ERROR:' '{print $2}' | \
  sort | uniq -c | sort -rn | head -10

# Check error distribution by endpoint
journalctl -u sergas-app --since "1 hour ago" | \
  grep "path=" | \
  grep "status=5" | \
  sed 's/.*path=\([^ ]*\).*/\1/' | \
  sort | uniq -c | sort -rn
```

#### Slow Performance

```bash
# Check slow queries
psql -d sergas_prod -c "
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '5 seconds'
ORDER BY duration DESC;"

# Check API latency
curl -s 'http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95,rate(sergas_http_request_duration_seconds_bucket[5m]))*1000' | jq

# Check system load
uptime
iostat -x 1 5
```

#### Database Issues

```bash
# Connection pool status
psql -d sergas_prod -c "
SELECT count(*), state
FROM pg_stat_activity
GROUP BY state;"

# Locks
psql -d sergas_prod -c "
SELECT pid, usename, pg_blocking_pids(pid) as blocked_by, query
FROM pg_stat_activity
WHERE cardinality(pg_blocking_pids(pid)) > 0;"

# Database size
psql -d sergas_prod -c "
SELECT pg_size_pretty(pg_database_size('sergas_prod'));"
```

---

## Step 4: Mitigation

### Immediate Mitigations

#### Restart Service

```bash
# P0: Complete outage - restart immediately
sudo systemctl restart sergas-app

# Verify restart
sleep 10
curl http://localhost:8000/health
```

#### Scale Resources

```bash
# Kubernetes: Scale up pods
kubectl scale deployment sergas-app --replicas=10

# Increase database connections
# Edit .env: DATABASE_POOL_SIZE=50
sudo systemctl restart sergas-app
```

#### Enable Circuit Breaker

```bash
# If Zoho API is down
curl -X POST http://localhost:8000/admin/circuit-breaker/zoho/open

# Verify
curl http://localhost:8000/admin/circuit-breaker/status | jq
```

#### Rollback Deployment

```bash
# Kubernetes
kubectl rollout undo deployment/sergas-app

# Docker Compose
docker-compose down
git checkout v1.0.0
docker-compose up -d --build

# Traditional
cd /home/sergas/super-account-manager
git checkout v1.0.0
sudo systemctl restart sergas-app
```

### Communication Templates

**P0 Initial Update (within 5 minutes):**
```
🚨 Incident Alert - P0

We are investigating a complete service outage.
Started: [TIME]
Impact: All users unable to access the system
Status: Investigating
Next update: 15 minutes

Status: https://status.sergas.com
```

**P0 Mitigation Update:**
```
🔧 Incident Update - P0

We have identified the issue and are implementing a fix.
Root cause: [BRIEF DESCRIPTION]
ETA: [TIME]
Next update: 15 minutes
```

---

## Step 5: Resolution

### Verification Checklist

```bash
# 1. Health check passes
curl http://localhost:8000/health | jq '.status' | grep -q "healthy"

# 2. Error rate below 1%
ERROR_RATE=$(curl -s 'http://prometheus:9090/api/v1/query?query=rate(sergas_http_requests_total{status=~"5.."}[5m])/rate(sergas_http_requests_total[5m])*100' | jq -r '.data.result[0].value[1]')
echo "Error rate: $ERROR_RATE%"

# 3. Response time normal (<200ms p95)
LATENCY=$(curl -s 'http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95,rate(sergas_http_request_duration_seconds_bucket[5m]))*1000' | jq -r '.data.result[0].value[1]')
echo "P95 latency: ${LATENCY}ms"

# 4. No active alerts
ACTIVE_ALERTS=$(curl -s http://alertmanager:9093/api/v2/alerts | jq 'length')
echo "Active alerts: $ACTIVE_ALERTS"

# 5. Test critical flows
python scripts/smoke_test.py
```

### Resolution Announcement

```
✅ Incident Resolved - P0

The issue has been resolved and all systems are operational.
Resolved at: [TIME]
Total downtime: [DURATION]

Root cause: [BRIEF DESCRIPTION]
Fix: [WHAT WAS DONE]

A detailed post-mortem will be published within 48 hours.
Thank you for your patience.
```

---

## Step 6: Post-Incident Activities

### Incident Report

Create incident report within 24 hours:

```markdown
# Incident Report: [INCIDENT-ID]

## Summary
- **Date**: [DATE]
- **Duration**: [START] - [END] ([DURATION])
- **Severity**: P0
- **Impact**: [DESCRIPTION]

## Timeline
- 10:00 - Alert triggered: High error rate
- 10:02 - Incident declared (P0)
- 10:05 - Investigation started
- 10:15 - Root cause identified
- 10:20 - Fix deployed
- 10:25 - Verified resolution
- 10:30 - Incident closed

## Root Cause
[DETAILED DESCRIPTION]

## Resolution
[WHAT WAS DONE]

## Action Items
- [ ] Add monitoring for [SPECIFIC METRIC]
- [ ] Improve error handling in [COMPONENT]
- [ ] Update runbook with [NEW PROCEDURE]
- [ ] Schedule post-mortem meeting

## Lessons Learned
- [WHAT WENT WELL]
- [WHAT COULD BE IMPROVED]
```

### Post-Mortem Meeting

Schedule within 48 hours with:
- Incident Commander
- On-call engineers
- Engineering manager
- Product stakeholders

**Agenda:**
1. Timeline review
2. Root cause analysis (5 Whys)
3. Action items
4. Process improvements

---

## Common Incident Scenarios

### Scenario: Database Connection Pool Exhausted

**Symptoms:**
- "Too many connections" errors
- Slow API responses
- Connection timeouts

**Investigation:**
```bash
psql -d sergas_prod -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"
```

**Mitigation:**
```bash
# Immediate: Kill idle connections
psql -d sergas_prod -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle' AND state_change < now() - interval '5 minutes';"

# Long-term: Increase pool size
# Edit .env: DATABASE_POOL_SIZE=30
sudo systemctl restart sergas-app
```

---

### Scenario: Zoho API Rate Limiting

**Symptoms:**
- 429 Too Many Requests errors
- Failed account syncs
- Circuit breaker open

**Investigation:**
```bash
journalctl -u sergas-app | grep "rate.*limit"
curl http://localhost:9090/api/v1/query?query=sergas_zoho_circuit_breaker_state
```

**Mitigation:**
```bash
# Enable request throttling
curl -X POST http://localhost:8000/admin/config \
  -d '{"ZOHO_RATE_LIMIT": 50}'

# Use cached data temporarily
curl -X POST http://localhost:8000/admin/cache/extend-ttl \
  -d '{"ttl": 1800}'
```

---

### Scenario: High Memory Usage / OOM

**Symptoms:**
- Application crashes
- OOM killer in logs
- High swap usage

**Investigation:**
```bash
free -h
ps aux --sort=-%mem | head -10
dmesg | grep -i "out of memory"
```

**Mitigation:**
```bash
# Immediate: Restart with memory limit
sudo systemctl stop sergas-app
# Edit service: MemoryLimit=4G
sudo systemctl daemon-reload
sudo systemctl start sergas-app

# Long-term: Investigate memory leak
python -m memory_profiler src/main.py
```

---

## Escalation Paths

### When to Escalate

- Incident not resolved within 1 hour
- Data loss suspected
- Security breach suspected
- Cross-system impact
- Need for additional expertise

### Escalation Contacts

1. **Engineering Manager**: manager@sergas.com
2. **CTO**: cto@sergas.com
3. **Security Team**: security@sergas.com
4. **Database Expert**: dba@sergas.com
5. **Vendor Support**: Zoho, Anthropic, AWS

---

## Tools & Resources

### Monitoring

- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093

### Logs

```bash
# Application logs
journalctl -u sergas-app -f

# Database logs
tail -f /var/log/postgresql/postgresql-14-main.log

# Nginx logs
tail -f /var/log/nginx/error.log
```

### Diagnostics

```bash
# Health check
curl http://localhost:8000/health | jq

# Metrics
curl http://localhost:8000/metrics | grep sergas_

# Database check
psql -d sergas_prod -c "SELECT 1;"

# Redis check
redis-cli ping
```

---

**Last Updated**: 2025-10-19
**Version**: 1.0.0
**Maintained by**: Sergas SRE Team
