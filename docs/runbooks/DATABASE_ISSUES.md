# Runbook: Database Issues

**Service**: Sergas Super Account Manager
**Component**: PostgreSQL Database
**Severity**: Critical
**Last Updated**: 2025-10-19

## Overview

This runbook covers troubleshooting and recovery procedures for PostgreSQL database issues affecting the Sergas Super Account Manager system.

## Symptoms

- Database connection failures
- Slow query performance
- Transaction deadlocks
- Replication lag (if applicable)
- Disk space warnings
- Connection pool exhaustion

## Impact Assessment

| Severity | Impact | Response Time |
|----------|--------|---------------|
| **Critical** | Database unreachable, system down | 5 minutes |
| **High** | Severe performance degradation | 15 minutes |
| **Medium** | Isolated slow queries | 1 hour |
| **Low** | Minor performance issues | 4 hours |

## Diagnostic Steps

### 1. Check Database Connectivity

```bash
# Test basic connectivity
pg_isready -h postgres-host -p 5432 -U sergas_user

# Test connection with psql
psql -h postgres-host -U sergas_user -d sergas_agent_db -c "SELECT 1;"

# Check database server status
systemctl status postgresql  # On database host
```

### 2. Check Database Performance

```sql
-- Connect to database
psql -h postgres-host -U sergas_user -d sergas_agent_db

-- Check active connections
SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active';

-- Check long-running queries
SELECT
  pid,
  usename,
  application_name,
  client_addr,
  state,
  query_start,
  NOW() - query_start as duration,
  LEFT(query, 100) as query_preview
FROM pg_stat_activity
WHERE state != 'idle'
  AND NOW() - query_start > INTERVAL '30 seconds'
ORDER BY query_start;

-- Check for locks
SELECT
  blocked.pid AS blocked_pid,
  blocked.usename AS blocked_user,
  blocking.pid AS blocking_pid,
  blocking.usename AS blocking_user,
  LEFT(blocked.query, 100) AS blocked_query
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking
  ON blocking.pid = ANY(pg_blocking_pids(blocked.pid))
WHERE blocked.wait_event_type = 'Lock';

-- Check table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
  n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```

### 3. Check Disk Space

```bash
# SSH to database server
ssh postgres-host

# Check disk usage
df -h /var/lib/postgresql

# Check PostgreSQL data directory size
du -sh /var/lib/postgresql/data

# Check for large log files
du -sh /var/log/postgresql/*.log | sort -h

# Check for bloat in tables
psql -U sergas_user -d sergas_agent_db -c \
  "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
   FROM pg_stat_user_tables
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
   LIMIT 10;"
```

### 4. Check Logs

```bash
# View PostgreSQL logs
tail -f /var/log/postgresql/postgresql-16-main.log

# Search for errors
grep -i error /var/log/postgresql/postgresql-16-main.log | tail -50

# Search for slow queries
grep -i "duration:" /var/log/postgresql/postgresql-16-main.log | tail -50

# Check for deadlocks
grep -i deadlock /var/log/postgresql/postgresql-16-main.log
```

### 5. Check Metrics

```bash
# Query Prometheus for database metrics
curl http://prometheus:9090/api/v1/query?query=pg_up

# Check connection count
curl http://prometheus:9090/api/v1/query?query=pg_stat_activity_count

# Check database size
curl http://prometheus:9090/api/v1/query?query=pg_database_size_bytes
```

## Common Root Causes

### 1. Connection Pool Exhaustion

**Symptom**: "FATAL: sorry, too many clients already"
**Root Cause**: Application exhausting connection pool
**Fix**:

```bash
# Check current max_connections
psql -U postgres -c "SHOW max_connections;"

# Check active connections
psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Increase max_connections (requires restart)
# Edit /etc/postgresql/16/main/postgresql.conf
max_connections = 200  # Was 100

# Restart PostgreSQL
systemctl restart postgresql

# Or: Increase application pool size instead
# Edit config/database.yml
pool_size: 30
max_overflow: 10
```

### 2. Long-Running Queries

**Symptom**: Queries taking minutes instead of seconds
**Root Cause**: Missing indexes, table bloat, or inefficient queries
**Fix**:

```sql
-- Identify slow queries
SELECT
  query,
  calls,
  total_exec_time,
  mean_exec_time,
  max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Create missing indexes
-- Example: Index on approval_workflow.status
CREATE INDEX CONCURRENTLY idx_approval_workflow_status
ON approval_workflow(status, created_at);

-- Analyze tables to update statistics
ANALYZE approval_workflow;
ANALYZE audit_events;
ANALYZE zoho_oauth_tokens;
```

### 3. Table Bloat

**Symptom**: Tables growing larger than expected, slow queries
**Root Cause**: Dead tuples not reclaimed by autovacuum
**Fix**:

```sql
-- Check for bloat
SELECT
  schemaname,
  tablename,
  n_dead_tup,
  n_live_tup,
  ROUND(n_dead_tup::float / NULLIF(n_live_tup, 0) * 100, 2) as dead_tuple_percent
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;

-- Manual vacuum for heavily bloated tables
VACUUM VERBOSE ANALYZE approval_workflow;
VACUUM VERBOSE ANALYZE audit_events;

-- Tune autovacuum
-- Edit /etc/postgresql/16/main/postgresql.conf
autovacuum_vacuum_scale_factor = 0.1  # Was 0.2
autovacuum_analyze_scale_factor = 0.05  # Was 0.1
autovacuum_max_workers = 4  # Was 3
```

### 4. Disk Space Exhaustion

**Symptom**: Database write failures, "No space left on device"
**Root Cause**: Transaction logs, audit logs, or table growth
**Fix**:

```bash
# Check disk space
df -h /var/lib/postgresql

# Clean up old WAL files
# Edit /etc/postgresql/16/main/postgresql.conf
wal_keep_size = 1GB  # Was unlimited
max_wal_size = 2GB

# Archive old audit logs
psql -U sergas_user -d sergas_agent_db <<EOF
-- Archive audit events older than 90 days
INSERT INTO audit_events_archive
SELECT * FROM audit_events
WHERE event_timestamp < NOW() - INTERVAL '90 days';

DELETE FROM audit_events
WHERE event_timestamp < NOW() - INTERVAL '90 days';

VACUUM FULL audit_events;
EOF

# Rotate PostgreSQL logs
logrotate -f /etc/logrotate.d/postgresql
```

### 5. Deadlocks

**Symptom**: "deadlock detected" errors
**Root Cause**: Concurrent transactions locking resources in different orders
**Fix**:

```sql
-- Enable deadlock logging
ALTER SYSTEM SET log_lock_waits = 'on';
ALTER SYSTEM SET deadlock_timeout = '1s';
SELECT pg_reload_conf();

-- Review deadlock logs
grep "deadlock detected" /var/log/postgresql/postgresql-16-main.log

-- Fix application code to acquire locks in consistent order
-- Example: Always lock approval_workflow before audit_events
```

## Resolution Procedures

### Emergency Procedures (System Down)

```bash
# 1. Check if PostgreSQL is running
systemctl status postgresql

# If not running:
systemctl start postgresql

# 2. If start fails, check logs
journalctl -u postgresql -n 100 --no-pager

# 3. If corruption detected:
# Restore from latest backup (see Backup/Restore section)

# 4. If out of disk space:
# Free space immediately
rm -f /var/lib/postgresql/data/pg_wal/archive_status/*.ready
rm -f /var/log/postgresql/*.log.gz

# Then restart
systemctl restart postgresql
```

### Performance Issues

```bash
# 1. Kill long-running queries
psql -U postgres -d sergas_agent_db <<EOF
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active'
  AND NOW() - query_start > INTERVAL '10 minutes'
  AND usename != 'postgres';
EOF

# 2. Rebuild statistics
psql -U postgres -d sergas_agent_db -c "ANALYZE VERBOSE;"

# 3. Reindex heavily used tables
psql -U postgres -d sergas_agent_db <<EOF
REINDEX TABLE CONCURRENTLY approval_workflow;
REINDEX TABLE CONCURRENTLY audit_events;
EOF

# 4. Restart connection pooler
systemctl restart pgbouncer  # If using PgBouncer
```

### Connection Pool Exhaustion

```bash
# 1. Find idle connections
psql -U postgres <<EOF
SELECT
  pid,
  usename,
  application_name,
  state,
  NOW() - state_change as idle_time
FROM pg_stat_activity
WHERE state = 'idle'
  AND NOW() - state_change > INTERVAL '1 hour'
ORDER BY state_change;
EOF

# 2. Terminate idle connections
psql -U postgres <<EOF
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND NOW() - state_change > INTERVAL '1 hour'
  AND usename != 'postgres';
EOF

# 3. Restart application to reset connection pool
docker-compose restart app
```

## Backup and Restore

### Create Backup

```bash
# Full database backup
pg_dump -h postgres-host -U sergas_user -d sergas_agent_db \
  -F c -b -v -f /backups/sergas_agent_db_$(date +%Y%m%d_%H%M%S).dump

# Backup with compression
pg_dump -h postgres-host -U sergas_user -d sergas_agent_db \
  -F c -Z 9 -f /backups/sergas_agent_db_$(date +%Y%m%d_%H%M%S).dump.gz

# Backup specific tables
pg_dump -h postgres-host -U sergas_user -d sergas_agent_db \
  -t approval_workflow -t audit_events \
  -F c -f /backups/critical_tables_$(date +%Y%m%d_%H%M%S).dump
```

### Restore Backup

```bash
# Restore full database (drops and recreates)
pg_restore -h postgres-host -U sergas_user -d postgres \
  -C -c -v /backups/sergas_agent_db_20251019_120000.dump

# Restore specific tables
pg_restore -h postgres-host -U sergas_user -d sergas_agent_db \
  -t approval_workflow -t audit_events \
  -c -v /backups/critical_tables_20251019_120000.dump

# Restore to point in time (if WAL archiving enabled)
pg_basebackup -h postgres-host -U replication_user -D /var/lib/postgresql/data_restore
# Edit recovery.conf
# restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
# recovery_target_time = '2025-10-19 12:00:00'
```

## Monitoring & Alerts

### Key Metrics

```promql
# Database up/down
pg_up

# Active connections
pg_stat_activity_count{state="active"}

# Connection utilization
(pg_stat_activity_count / pg_settings_max_connections) * 100

# Long-running queries
pg_stat_activity_max_tx_duration

# Database size
pg_database_size_bytes{datname="sergas_agent_db"}

# Disk space
node_filesystem_avail_bytes{mountpoint="/var/lib/postgresql"}

# Deadlocks
rate(pg_stat_database_deadlocks[5m])

# Cache hit ratio (should be >95%)
pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read)
```

### Alert Thresholds

```yaml
# config/alerts/database_alerts.yml
groups:
  - name: database_health
    rules:
      - alert: DatabaseDown
        expr: pg_up == 0
        for: 1m
        severity: critical

      - alert: HighConnectionUtilization
        expr: (pg_stat_activity_count / pg_settings_max_connections) * 100 > 80
        for: 5m
        severity: warning

      - alert: LongRunningQuery
        expr: pg_stat_activity_max_tx_duration > 300
        for: 5m
        severity: warning

      - alert: LowDiskSpace
        expr: (node_filesystem_avail_bytes{mountpoint="/var/lib/postgresql"} / node_filesystem_size_bytes) * 100 < 10
        for: 5m
        severity: critical

      - alert: HighDeadlockRate
        expr: rate(pg_stat_database_deadlocks[5m]) > 0.1
        for: 5m
        severity: warning
```

## Escalation Path

1. **Level 1** (0-5 min): On-call DevOps engineer
   - Check database status
   - Restart if down

2. **Level 2** (5-15 min): Database administrator
   - Deep diagnostics
   - Query optimization

3. **Level 3** (15+ min): CTO + AWS support
   - Infrastructure review
   - RDS parameter tuning

## Post-Incident Review

Document:

1. **Root Cause**: What caused the database issue?
2. **Detection**: How was it detected? Monitoring alerts?
3. **Impact**: How many requests failed?
4. **Resolution**: What fixed it?
5. **Prevention**: Index creation? Query optimization? Hardware upgrade?

## Related Runbooks

- `/docs/runbooks/APPROVAL_TIMEOUTS.md`
- `/docs/runbooks/SCALING.md`
- `/docs/runbooks/incident_response.md`

## References

- Database Schema: `/migrations/versions/`
- Connection Pool Config: `/config/database.yml`
- PostgreSQL Docs: https://www.postgresql.org/docs/16/

---

**Last Incident**: None
**Next Review**: 2025-11-19
