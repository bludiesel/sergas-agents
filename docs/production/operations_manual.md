# Operations Manual

## Overview

This manual provides comprehensive operational procedures for the Sergas Super Account Manager production system. It covers daily operations, maintenance tasks, monitoring, and incident response.

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [System Monitoring](#system-monitoring)
3. [Maintenance Tasks](#maintenance-tasks)
4. [Backup and Recovery](#backup-and-recovery)
5. [Performance Optimization](#performance-optimization)
6. [User Management](#user-management)
7. [Configuration Management](#configuration-management)
8. [Scaling Operations](#scaling-operations)

---

## Daily Operations

### Morning Health Check

Perform these checks every morning:

```bash
#!/bin/bash
# daily-health-check.sh

echo "=== Sergas Daily Health Check ==="
echo "Date: $(date)"
echo ""

# 1. Check application status
echo "1. Application Status:"
if command -v systemctl &> /dev/null; then
    systemctl status sergas-app | grep Active
elif command -v docker &> /dev/null; then
    docker-compose ps
elif command -v kubectl &> /dev/null; then
    kubectl get pods -l app=sergas-app
fi
echo ""

# 2. Check API health
echo "2. API Health:"
curl -s https://your-domain.com/health | jq
echo ""

# 3. Check database health
echo "3. Database Health:"
psql -d sergas_prod -c "SELECT
    count(*) as total_connections,
    count(*) FILTER (WHERE state = 'active') as active_connections
FROM pg_stat_activity;" -t
echo ""

# 4. Check Redis health
echo "4. Redis Health:"
redis-cli ping
redis-cli info memory | grep used_memory_human
echo ""

# 5. Check disk space
echo "5. Disk Space:"
df -h | grep -E '(Filesystem|/dev/)'
echo ""

# 6. Check recent errors
echo "6. Recent Errors (last hour):"
journalctl -u sergas-app --since "1 hour ago" | grep -i error | wc -l
echo ""

# 7. Check Zoho connectivity
echo "7. Zoho CRM Connectivity:"
curl -s https://your-domain.com/health | jq -r '.zoho'
echo ""

# 8. Check memory usage
echo "8. Memory Usage:"
free -h
echo ""

echo "=== Health Check Complete ==="
```

Run daily check:

```bash
chmod +x daily-health-check.sh
./daily-health-check.sh | tee -a /var/log/sergas/daily-checks.log
```

### Log Review

Review critical logs daily:

```bash
# Application errors (last 24 hours)
journalctl -u sergas-app --since "24 hours ago" | grep -i "ERROR\|CRITICAL"

# Failed API requests
journalctl -u sergas-app --since "24 hours ago" | grep "status_code=5"

# Database slow queries
tail -100 /var/log/postgresql/postgresql-*.log | grep "duration:"

# Failed authentications
journalctl -u sergas-app --since "24 hours ago" | grep "authentication failed"

# Circuit breaker trips
journalctl -u sergas-app --since "24 hours ago" | grep "circuit.*open"
```

### Metric Review

Check key metrics in Grafana:

1. Navigate to https://your-domain.com:3000
2. Open "Sergas Overview" dashboard
3. Review:
   - Request rate and latency
   - Error rate (should be <1%)
   - Agent session success rate
   - Database connection pool usage
   - Memory and CPU usage
   - Zoho API call success rate

### Alert Review

Check AlertManager for active alerts:

```bash
# List active alerts
curl -s http://localhost:9093/api/v2/alerts | jq '.[] | {
    name: .labels.alertname,
    severity: .labels.severity,
    starts_at: .startsAt
}'

# Acknowledge alerts
curl -X POST http://localhost:9093/api/v2/alerts \
  -H 'Content-Type: application/json' \
  -d '[{"labels": {"alertname": "HighErrorRate"}}]'
```

---

## System Monitoring

### Real-Time Monitoring

#### Application Metrics

```bash
# Active sessions
curl -s http://localhost:9090/api/v1/query?query=sergas_agent_sessions_active | \
  jq -r '.data.result[0].value[1]'

# Request rate (per minute)
curl -s http://localhost:9090/api/v1/query?query='rate(sergas_http_requests_total[1m])*60' | \
  jq -r '.data.result[0].value[1]'

# Error rate (percentage)
curl -s http://localhost:9090/api/v1/query?query='rate(sergas_http_requests_total{status=~"5.."}[5m])/rate(sergas_http_requests_total[5m])*100' | \
  jq -r '.data.result[0].value[1]'

# Average response time (ms)
curl -s http://localhost:9090/api/v1/query?query='rate(sergas_http_request_duration_seconds_sum[5m])/rate(sergas_http_request_duration_seconds_count[5m])*1000' | \
  jq -r '.data.result[0].value[1]'
```

#### Database Metrics

```bash
# Active connections
psql -d sergas_prod -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" -t

# Long-running queries
psql -d sergas_prod -c "
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '5 minutes';" -x

# Database size
psql -d sergas_prod -c "
SELECT pg_size_pretty(pg_database_size('sergas_prod'));" -t

# Table sizes
psql -d sergas_prod -c "
SELECT schemaname, tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;"
```

#### Redis Metrics

```bash
# Memory usage
redis-cli info memory | grep -E "used_memory_human|maxmemory_human"

# Connected clients
redis-cli info clients | grep connected_clients

# Hit rate
redis-cli info stats | grep -E "keyspace_hits|keyspace_misses"

# Key count
redis-cli dbsize
```

### Log Monitoring

#### Real-Time Log Streaming

```bash
# Application logs
journalctl -u sergas-app -f

# Filter for errors only
journalctl -u sergas-app -f | grep -i "ERROR\|CRITICAL"

# Filter for specific agent
journalctl -u sergas-app -f | grep "ZohoDataScout"

# Multi-line context for errors
journalctl -u sergas-app -f -o short-precise | grep -B 3 -A 3 "ERROR"
```

#### Log Analysis

```bash
# Error distribution (last hour)
journalctl -u sergas-app --since "1 hour ago" | \
  grep ERROR | \
  awk '{print $NF}' | \
  sort | uniq -c | sort -rn

# Top 10 endpoints by request count (last hour)
journalctl -u sergas-app --since "1 hour ago" | \
  grep "path=" | \
  sed 's/.*path=\([^ ]*\).*/\1/' | \
  sort | uniq -c | sort -rn | head -10

# Slow requests (>5s) in last hour
journalctl -u sergas-app --since "1 hour ago" | \
  grep "duration=" | \
  awk '{for(i=1;i<=NF;i++) if($i~/duration=/) print $i}' | \
  sed 's/duration=//' | \
  awk '$1 > 5000' | wc -l
```

---

## Maintenance Tasks

### Weekly Maintenance

Perform every Sunday at 2 AM:

```bash
#!/bin/bash
# weekly-maintenance.sh

echo "=== Weekly Maintenance Start ==="

# 1. Database vacuum and analyze
echo "1. Running database maintenance..."
psql -d sergas_prod -c "VACUUM ANALYZE;"

# 2. Clean old logs (keep 30 days)
echo "2. Cleaning old logs..."
find /var/log/sergas -name "*.log" -mtime +30 -delete
journalctl --vacuum-time=30d

# 3. Clean old Redis keys
echo "3. Cleaning expired Redis keys..."
redis-cli --scan --pattern "session:*" | xargs -L 1 redis-cli ttl | \
  awk '$1 == -1 {print prev} {prev=$1}' | xargs -L 1 redis-cli del

# 4. Rotate backups
echo "4. Rotating backups..."
find /var/backups/sergas -name "*.sql.gz" -mtime +30 -delete

# 5. Check certificate expiry
echo "5. Checking SSL certificate..."
echo | openssl s_client -servername your-domain.com -connect your-domain.com:443 2>/dev/null | \
  openssl x509 -noout -dates

# 6. Update dependencies (security patches only)
echo "6. Checking for security updates..."
pip list --outdated | grep -i security

# 7. Generate weekly report
echo "7. Generating weekly report..."
python scripts/weekly_report.py > /var/log/sergas/weekly-report-$(date +%Y%m%d).txt

echo "=== Weekly Maintenance Complete ==="
```

Schedule with cron:

```bash
# Add to crontab
0 2 * * 0 /usr/local/bin/weekly-maintenance.sh >> /var/log/sergas/weekly-maintenance.log 2>&1
```

### Monthly Maintenance

Perform first Sunday of each month:

```bash
#!/bin/bash
# monthly-maintenance.sh

echo "=== Monthly Maintenance Start ==="

# 1. Full database backup
echo "1. Creating full database backup..."
pg_dump -U sergas_prod_user -d sergas_prod | \
  gzip > /var/backups/sergas/monthly/sergas_prod_$(date +%Y%m).sql.gz

# 2. Audit log review
echo "2. Reviewing audit logs..."
python scripts/audit_log_analysis.py --period month > \
  /var/log/sergas/audit-analysis-$(date +%Y%m).txt

# 3. Security scan
echo "3. Running security scan..."
bandit -r src/ > /var/log/sergas/security-scan-$(date +%Y%m).txt

# 4. Dependency audit
echo "4. Auditing dependencies..."
pip-audit > /var/log/sergas/dependency-audit-$(date +%Y%m).txt

# 5. Performance benchmarking
echo "5. Running performance benchmarks..."
python scripts/performance_benchmark.py > \
  /var/log/sergas/performance-$(date +%Y%m).txt

# 6. Capacity planning report
echo "6. Generating capacity report..."
python scripts/capacity_planning.py > \
  /var/log/sergas/capacity-$(date +%Y%m).txt

echo "=== Monthly Maintenance Complete ==="
```

### Database Maintenance

#### VACUUM and ANALYZE

```bash
# Manual vacuum for specific table
psql -d sergas_prod -c "VACUUM ANALYZE accounts;"

# Check last vacuum time
psql -d sergas_prod -c "
SELECT schemaname, relname, last_vacuum, last_autovacuum
FROM pg_stat_user_tables
ORDER BY last_autovacuum DESC NULLS LAST;"

# Check bloat
psql -d sergas_prod -c "
SELECT schemaname, tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
  round(100 * pg_total_relation_size(schemaname||'.'||tablename) /
    NULLIF(pg_database_size(current_database()), 0), 2) as pct
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

#### Index Maintenance

```bash
# List unused indexes
psql -d sergas_prod -c "
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND indexname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(indexrelid) DESC;"

# Rebuild index
psql -d sergas_prod -c "REINDEX INDEX CONCURRENTLY index_name;"

# Check index usage
psql -d sergas_prod -c "
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;"
```

---

## Backup and Recovery

### Automated Backups

#### Database Backup Script

```bash
#!/bin/bash
# backup-database.sh

set -euo pipefail

BACKUP_DIR="/var/backups/sergas/database"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/sergas_prod_$TIMESTAMP.sql.gz"
S3_BUCKET="s3://sergas-backups/database"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Perform backup
echo "Starting database backup..."
pg_dump -U sergas_prod_user -d sergas_prod -F c | gzip > "$BACKUP_FILE"

# Verify backup
if [ -f "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "Backup created: $BACKUP_FILE ($SIZE)"
else
    echo "ERROR: Backup failed!"
    exit 1
fi

# Upload to S3
if command -v aws &> /dev/null; then
    echo "Uploading to S3..."
    aws s3 cp "$BACKUP_FILE" "$S3_BUCKET/"
    echo "Upload complete"
fi

# Cleanup old backups (keep 30 days locally, 90 days in S3)
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete
if command -v aws &> /dev/null; then
    aws s3 ls "$S3_BUCKET/" | \
      awk '{if ($1 < "'$(date -d '90 days ago' +%Y-%m-%d)'") print $4}' | \
      xargs -I {} aws s3 rm "$S3_BUCKET/{}"
fi

echo "Backup complete: $BACKUP_FILE"
```

#### Configuration Backup

```bash
#!/bin/bash
# backup-config.sh

BACKUP_DIR="/var/backups/sergas/config"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/config_$TIMESTAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

# Backup configuration files
tar -czf "$BACKUP_FILE" \
  /etc/systemd/system/sergas-app.service \
  /etc/nginx/sites-available/sergas \
  /home/sergas/super-account-manager/.env \
  /home/sergas/super-account-manager/alembic.ini

# Upload to S3
aws s3 cp "$BACKUP_FILE" s3://sergas-backups/config/

# Cleanup old backups
find "$BACKUP_DIR" -name "config_*.tar.gz" -mtime +90 -delete

echo "Configuration backup complete: $BACKUP_FILE"
```

### Recovery Procedures

#### Database Recovery

```bash
#!/bin/bash
# restore-database.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file>"
    exit 1
fi

# Confirm restoration
read -p "This will REPLACE the current database. Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Restoration cancelled"
    exit 0
fi

# Stop application
echo "Stopping application..."
systemctl stop sergas-app

# Drop existing database (careful!)
echo "Dropping existing database..."
psql -U postgres -c "DROP DATABASE IF EXISTS sergas_prod;"
psql -U postgres -c "CREATE DATABASE sergas_prod OWNER sergas_prod_user;"

# Restore from backup
echo "Restoring from $BACKUP_FILE..."
gunzip < "$BACKUP_FILE" | pg_restore -U sergas_prod_user -d sergas_prod

# Verify restoration
echo "Verifying restoration..."
COUNT=$(psql -U sergas_prod_user -d sergas_prod -c "SELECT count(*) FROM accounts;" -t)
echo "Accounts restored: $COUNT"

# Run migrations (if needed)
echo "Running migrations..."
cd /home/sergas/super-account-manager
source venv/bin/activate
alembic upgrade head

# Start application
echo "Starting application..."
systemctl start sergas-app

# Wait for startup
sleep 10

# Verify application
curl -s http://localhost:8000/health | jq

echo "Database restoration complete"
```

#### Point-in-Time Recovery

```bash
# For WAL archiving setups only
pg_restore -U sergas_prod_user -d sergas_prod \
  --target-time="2024-10-19 14:30:00"
```

---

## Performance Optimization

### Database Query Optimization

```bash
# Find slow queries
psql -d sergas_prod -c "
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;"

# Check missing indexes
psql -d sergas_prod -c "
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public' AND n_distinct > 1000
ORDER BY n_distinct DESC;"

# Add index for common query
psql -d sergas_prod -c "
CREATE INDEX CONCURRENTLY idx_accounts_owner_id ON accounts(owner_id);"
```

### Redis Optimization

```bash
# Check memory fragmentation
redis-cli info memory | grep -E "mem_fragmentation|used_memory"

# Optimize memory
redis-cli CONFIG SET activedefrag yes

# Analyze key distribution
redis-cli --bigkeys

# Set eviction policy for cache keys
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Application Optimization

```bash
# Increase worker count (for systemd)
sudo systemctl edit sergas-app
# Add:
# [Service]
# ExecStart=
# ExecStart=/path/to/venv/bin/uvicorn src.main:app --workers 8

# Reload systemd
sudo systemctl daemon-reload
sudo systemctl restart sergas-app

# For Docker Compose, edit docker-compose.yml:
# command: uvicorn src.main:app --workers 8 --host 0.0.0.0

# For Kubernetes, edit deployment.yaml:
# resources:
#   requests:
#     memory: "2Gi"
#     cpu: "1000m"
#   limits:
#     memory: "4Gi"
#     cpu: "2000m"
```

---

## User Management

### Creating Admin User

```bash
# Using CLI
python scripts/create_user.py \
  --username admin@sergas.com \
  --role admin \
  --name "System Administrator"

# Using API
curl -X POST https://your-domain.com/api/v1/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@sergas.com",
    "role": "admin",
    "name": "System Administrator"
  }'
```

### Revoking Access

```bash
# Disable user account
python scripts/manage_user.py \
  --user-id 123 \
  --action disable

# Revoke all sessions
redis-cli --scan --pattern "session:user:123:*" | xargs redis-cli del
```

---

## Configuration Management

### Environment Variable Updates

```bash
# Edit environment file
sudo nano /home/sergas/super-account-manager/.env

# Reload application
sudo systemctl restart sergas-app

# Verify changes
journalctl -u sergas-app -n 50 | grep "Configuration loaded"
```

### Feature Flag Management

```bash
# Enable feature
export ENABLE_NEW_FEATURE=true

# Restart application
sudo systemctl restart sergas-app

# Verify feature is enabled
curl https://your-domain.com/api/v1/features | jq '.new_feature'
```

---

## Scaling Operations

### Horizontal Scaling (Kubernetes)

```bash
# Scale to 5 replicas
kubectl scale deployment sergas-app --replicas=5

# Verify scaling
kubectl get pods -l app=sergas-app

# Auto-scaling configuration
kubectl autoscale deployment sergas-app \
  --min=2 \
  --max=10 \
  --cpu-percent=70
```

### Database Connection Pool Tuning

```bash
# Edit environment
DATABASE_POOL_SIZE=30
DATABASE_MAX_OVERFLOW=50

# Restart application
systemctl restart sergas-app

# Monitor connection usage
psql -d sergas_prod -c "
SELECT count(*), state
FROM pg_stat_activity
GROUP BY state;"
```

---

## Support

For operational support:

- **Runbooks**: `/docs/runbooks/`
- **Troubleshooting**: `/docs/production/troubleshooting_guide.md`
- **On-Call**: devops-oncall@sergas.com
- **Slack**: #sergas-ops

---

**Last Updated**: 2025-10-19
**Version**: 1.0.0
**Maintained by**: Sergas Operations Team
