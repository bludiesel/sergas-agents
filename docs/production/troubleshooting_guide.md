# Troubleshooting Guide

## Overview

This guide provides comprehensive troubleshooting procedures for common issues in the Sergas Super Account Manager production system.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Application Issues](#application-issues)
3. [Database Issues](#database-issues)
4. [Integration Issues](#integration-issues)
5. [Performance Issues](#performance-issues)
6. [Security Issues](#security-issues)
7. [Infrastructure Issues](#infrastructure-issues)

---

## Quick Diagnostics

### First Response Checklist

When an issue is reported, run these commands immediately:

```bash
#!/bin/bash
# quick-diagnostic.sh

echo "=== Quick Diagnostic Report ==="
echo "Timestamp: $(date)"
echo ""

# 1. Application Status
echo "1. APPLICATION STATUS"
systemctl status sergas-app --no-pager | head -20
echo ""

# 2. Recent Errors
echo "2. RECENT ERRORS (last 5 minutes)"
journalctl -u sergas-app --since "5 minutes ago" | grep -i "ERROR\|CRITICAL" | tail -20
echo ""

# 3. API Health
echo "3. API HEALTH"
curl -s -m 5 http://localhost:8000/health | jq || echo "API not responding"
echo ""

# 4. Database Connectivity
echo "4. DATABASE CONNECTIVITY"
psql -d sergas_prod -c "SELECT 1;" >/dev/null 2>&1 && echo "OK" || echo "FAILED"
echo ""

# 5. Redis Connectivity
echo "5. REDIS CONNECTIVITY"
redis-cli ping 2>&1
echo ""

# 6. Resource Usage
echo "6. RESOURCE USAGE"
free -h | head -2
df -h / | tail -1
echo ""

# 7. Active Connections
echo "7. ACTIVE CONNECTIONS"
ss -tunap | grep :8000 | wc -l
echo ""

echo "=== End Diagnostic Report ==="
```

### Health Check Matrix

| Component | Check Command | Expected Result | If Failed |
|-----------|---------------|-----------------|-----------|
| **API** | `curl localhost:8000/health` | HTTP 200 + JSON | Check app logs |
| **Database** | `psql -c "SELECT 1"` | Returns 1 | Check DB logs |
| **Redis** | `redis-cli ping` | PONG | Check Redis service |
| **Zoho** | Check health endpoint | "authenticated" | Check credentials |
| **Disk** | `df -h /` | <80% used | Clean logs |
| **Memory** | `free -h` | <80% used | Check for leaks |
| **CPU** | `top -bn1` | <80% average | Check processes |

---

## Application Issues

### Issue: Application Won't Start

**Symptoms:**
- Service fails to start
- Immediate crash after startup
- Port binding errors

**Diagnosis:**

```bash
# Check service status
systemctl status sergas-app

# Check detailed logs
journalctl -u sergas-app -n 100 --no-pager

# Check for port conflicts
sudo lsof -i :8000

# Verify configuration
python -c "from src.config import settings; print(settings.dict())"
```

**Common Causes and Solutions:**

1. **Port Already in Use**
   ```bash
   # Find process using port
   sudo lsof -i :8000

   # Kill conflicting process
   sudo kill -9 <PID>

   # Or change port in .env
   API_PORT=8001
   ```

2. **Missing Environment Variables**
   ```bash
   # Check environment file
   cat .env | grep -v "^#" | grep -v "^$"

   # Verify required variables
   python scripts/check_env.py

   # Add missing variables to .env
   ```

3. **Database Connection Failed**
   ```bash
   # Test database connectivity
   psql -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME -c "SELECT 1;"

   # Check credentials
   grep DATABASE_ .env

   # Verify database is running
   systemctl status postgresql
   ```

4. **Import Errors**
   ```bash
   # Check Python path
   python -c "import sys; print(sys.path)"

   # Reinstall dependencies
   pip install --force-reinstall -r requirements.txt

   # Check for missing packages
   python -c "from src import agents"
   ```

---

### Issue: Application Crashes Intermittently

**Symptoms:**
- Application stops randomly
- Segmentation faults
- Out of memory errors

**Diagnosis:**

```bash
# Check for OOM killer
dmesg | grep -i "out of memory"
journalctl | grep -i "killed process"

# Monitor memory usage
watch -n 1 'free -h && ps aux | grep python | grep -v grep'

# Check for memory leaks
python -m memory_profiler src/main.py

# Review crash dumps
ls -lh /var/crash/
```

**Solutions:**

1. **Memory Leak**
   ```bash
   # Analyze memory usage
   python scripts/memory_profiler.py

   # Increase memory limits (systemd)
   sudo systemctl edit sergas-app
   # Add: MemoryLimit=8G

   # Or for Docker
   # docker-compose.yml: mem_limit: 8g

   # Restart service
   sudo systemctl restart sergas-app
   ```

2. **Resource Exhaustion**
   ```bash
   # Reduce concurrent workers
   # In .env:
   MAX_CONCURRENT_ACCOUNTS=5
   CELERY_WORKER_CONCURRENCY=2

   # Limit database connections
   DATABASE_POOL_SIZE=10
   DATABASE_MAX_OVERFLOW=20
   ```

3. **Unhandled Exceptions**
   ```bash
   # Enable debug logging
   LOG_LEVEL=DEBUG

   # Restart and monitor
   sudo systemctl restart sergas-app
   journalctl -u sergas-app -f
   ```

---

### Issue: High Error Rate

**Symptoms:**
- Increased 500 errors
- Failed agent sessions
- Timeout errors

**Diagnosis:**

```bash
# Count errors by type
journalctl -u sergas-app --since "1 hour ago" | \
  grep ERROR | \
  awk '{print $NF}' | \
  sort | uniq -c | sort -rn

# Check error rate
curl -s 'http://localhost:9090/api/v1/query?query=rate(sergas_http_requests_total{status=~"5.."}[5m])' | jq

# Find slow endpoints
journalctl -u sergas-app --since "1 hour ago" | \
  grep "duration=" | \
  awk '{for(i=1;i<=NF;i++) if($i~/path=/) print $i}' | \
  sort | uniq -c | sort -rn
```

**Solutions:**

1. **Database Timeout**
   ```bash
   # Check slow queries
   psql -d sergas_prod -c "
   SELECT pid, now() - query_start as duration, query
   FROM pg_stat_activity
   WHERE state = 'active' AND now() - query_start > interval '1 minute';"

   # Increase timeout
   DATABASE_TIMEOUT=60

   # Add indexes for slow queries
   psql -d sergas_prod -c "CREATE INDEX CONCURRENTLY idx_slow_query ON table_name(column);"
   ```

2. **External API Failures**
   ```bash
   # Check Zoho API status
   curl -s https://your-domain.com/health | jq '.zoho'

   # Enable circuit breaker
   CIRCUIT_BREAKER_FAILURE_THRESHOLD=3
   ENABLE_FAILOVER=true

   # Increase retry attempts
   MAX_RETRY_ATTEMPTS=5
   ```

3. **Resource Contention**
   ```bash
   # Check CPU usage
   top -bn1 | grep "Cpu(s)"

   # Check I/O wait
   iostat -x 1 5

   # Scale horizontally
   kubectl scale deployment sergas-app --replicas=5
   ```

---

## Database Issues

### Issue: Database Connection Pool Exhausted

**Symptoms:**
- "Too many connections" errors
- Slow response times
- Connection timeout errors

**Diagnosis:**

```bash
# Check active connections
psql -d sergas_prod -c "
SELECT count(*), state
FROM pg_stat_activity
GROUP BY state;"

# Check connection limit
psql -d sergas_prod -c "SHOW max_connections;"

# Check application pool usage
grep -E "pool_size|max_overflow" .env
```

**Solutions:**

```bash
# Increase PostgreSQL max_connections
# Edit postgresql.conf
sudo nano /etc/postgresql/14/main/postgresql.conf
# Change: max_connections = 200

# Restart PostgreSQL
sudo systemctl restart postgresql

# Or increase application pool size
# In .env:
DATABASE_POOL_SIZE=30
DATABASE_MAX_OVERFLOW=50

# Restart application
sudo systemctl restart sergas-app

# Kill idle connections
psql -d sergas_prod -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle' AND state_change < now() - interval '5 minutes';"
```

---

### Issue: Slow Database Queries

**Symptoms:**
- Requests timeout
- High database CPU
- Long query execution times

**Diagnosis:**

```bash
# Enable slow query logging
psql -d sergas_prod -c "
ALTER DATABASE sergas_prod SET log_min_duration_statement = 1000;"

# Find slow queries
psql -d sergas_prod -c "
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;"

# Check for missing indexes
psql -d sergas_prod -c "
SELECT schemaname, tablename, attname, n_distinct
FROM pg_stats
WHERE schemaname = 'public' AND n_distinct > 1000
ORDER BY n_distinct DESC;"

# Check table bloat
psql -d sergas_prod -c "
SELECT schemaname, tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

**Solutions:**

```bash
# Add missing indexes
psql -d sergas_prod -c "
CREATE INDEX CONCURRENTLY idx_accounts_owner_id ON accounts(owner_id);
CREATE INDEX CONCURRENTLY idx_activities_account_id ON activities(account_id);
"

# Vacuum and analyze
psql -d sergas_prod -c "VACUUM ANALYZE;"

# Optimize query
# Before:
# SELECT * FROM accounts WHERE owner_id = 123;
# After:
# SELECT id, name, status FROM accounts WHERE owner_id = 123;

# Enable connection pooling (pgbouncer)
sudo apt install pgbouncer
# Configure and use pgbouncer as proxy
```

---

### Issue: Database Disk Space Full

**Symptoms:**
- "No space left on device" errors
- Write operations fail
- Application crashes

**Diagnosis:**

```bash
# Check disk usage
df -h /var/lib/postgresql

# Check database size
psql -d sergas_prod -c "
SELECT pg_database.datname,
  pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
ORDER BY pg_database_size(pg_database.datname) DESC;"

# Check largest tables
psql -d sergas_prod -c "
SELECT schemaname, tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;"
```

**Solutions:**

```bash
# Clean up WAL files
psql -d sergas_prod -c "SELECT pg_switch_wal();"
psql -d sergas_prod -c "CHECKPOINT;"

# Truncate old audit logs
psql -d sergas_prod -c "
DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '90 days';"

# Vacuum full (requires downtime)
psql -d sergas_prod -c "VACUUM FULL;"

# Add more disk space
# Expand volume and resize filesystem
sudo resize2fs /dev/vdb1

# Or move to larger disk
# 1. Stop application
# 2. Backup database
# 3. Restore to new disk
# 4. Update mount point
```

---

## Integration Issues

### Issue: Zoho CRM Authentication Failed

**Symptoms:**
- "Invalid token" errors
- 401 Unauthorized responses
- Failed account syncs

**Diagnosis:**

```bash
# Check authentication status
curl -s http://localhost:8000/health | jq '.zoho'

# Check token expiry
python scripts/check_zoho_token.py

# Test OAuth flow
python scripts/test_zoho_auth.py

# Check credentials in environment
grep ZOHO_ .env
```

**Solutions:**

```bash
# Refresh OAuth token
python scripts/refresh_zoho_token.py

# Verify credentials
# 1. Login to Zoho Developer Console
# 2. Verify Client ID and Secret
# 3. Check redirect URL matches
# 4. Regenerate refresh token if needed

# Update credentials in .env
ZOHO_MCP_CLIENT_ID=<new-client-id>
ZOHO_MCP_CLIENT_SECRET=<new-client-secret>
ZOHO_SDK_REFRESH_TOKEN=<new-refresh-token>

# Clear cached tokens
redis-cli DEL zoho:access_token
redis-cli DEL zoho:refresh_token

# Restart application
sudo systemctl restart sergas-app

# Verify authentication
curl -s http://localhost:8000/health | jq '.zoho'
```

---

### Issue: Zoho API Rate Limiting

**Symptoms:**
- "Rate limit exceeded" errors
- 429 Too Many Requests
- Delayed responses

**Diagnosis:**

```bash
# Check rate limit status
journalctl -u sergas-app | grep "rate.*limit"

# Check API call frequency
curl -s 'http://localhost:9090/api/v1/query?query=rate(sergas_zoho_api_calls_total[1m])*60' | jq

# Monitor circuit breaker
journalctl -u sergas-app | grep "circuit.*open"
```

**Solutions:**

```bash
# Enable request throttling
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=50

# Enable caching
REDIS_CACHE_TTL=300  # 5 minutes

# Use batch operations
ZOHO_BATCH_SIZE=10
ZOHO_BATCH_DELAY=2  # seconds

# Enable circuit breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60

# Restart application
sudo systemctl restart sergas-app
```

---

### Issue: Cognee Memory Service Down

**Symptoms:**
- "Connection refused" to Cognee
- Failed memory queries
- Missing historical context

**Diagnosis:**

```bash
# Check Cognee service
curl -s http://localhost:8001/health

# Check Docker container (if containerized)
docker ps | grep cognee

# Check logs
docker logs cognee

# Test connectivity
curl -s http://localhost:8001/api/v1/query \
  -H "Authorization: Bearer $COGNEE_API_KEY" \
  -d '{"query": "test"}'
```

**Solutions:**

```bash
# Restart Cognee service
docker-compose restart cognee

# Or with Docker
docker restart cognee

# Check configuration
grep COGNEE_ .env

# Verify network connectivity
ping cognee-host
telnet cognee-host 8001

# Check firewall rules
sudo ufw status

# Rebuild Cognee container
docker-compose up -d --build cognee
```

---

## Performance Issues

### Issue: High Response Times

**Symptoms:**
- Slow API responses (>5s)
- Request timeouts
- Poor user experience

**Diagnosis:**

```bash
# Measure response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/accounts

# curl-format.txt:
time_namelookup:  %{time_namelookup}\n
time_connect:  %{time_connect}\n
time_appconnect:  %{time_appconnect}\n
time_pretransfer:  %{time_pretransfer}\n
time_redirect:  %{time_redirect}\n
time_starttransfer:  %{time_starttransfer}\n
----------\n
time_total:  %{time_total}\n

# Check application metrics
curl -s 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(sergas_http_request_duration_seconds_bucket[5m]))*1000' | jq

# Profile slow endpoint
python -m cProfile -o profile.stats src/main.py
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumtime').print_stats(20)"
```

**Solutions:**

1. **Database Optimization**
   ```bash
   # Add indexes
   psql -d sergas_prod -c "CREATE INDEX CONCURRENTLY idx_accounts_status ON accounts(status);"

   # Enable query caching
   ENABLE_QUERY_CACHE=true
   CACHE_TTL=300

   # Use connection pooling
   DATABASE_POOL_SIZE=20
   ```

2. **Application Caching**
   ```bash
   # Enable Redis caching
   ENABLE_CACHE=true
   REDIS_CACHE_TTL=300

   # Cache expensive operations
   # In code: @cache.memoize(timeout=300)
   ```

3. **Horizontal Scaling**
   ```bash
   # Add more workers
   kubectl scale deployment sergas-app --replicas=5

   # Or for systemd
   # Edit service to use more workers
   # --workers 8
   ```

---

### Issue: High Memory Usage

**Symptoms:**
- Memory usage >80%
- OOM killer triggered
- Swap usage high

**Diagnosis:**

```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Check Python memory
python -m memory_profiler src/main.py

# Monitor over time
watch -n 5 'free -h && ps aux | grep python | grep -v grep'

# Check for memory leaks
valgrind --leak-check=full python src/main.py
```

**Solutions:**

```bash
# Increase system memory
# Upgrade instance or add swap

# Reduce memory footprint
MAX_CONCURRENT_ACCOUNTS=10
CELERY_WORKER_CONCURRENCY=2
DATABASE_POOL_SIZE=10

# Enable garbage collection tuning
# In code:
import gc
gc.set_threshold(700, 10, 10)

# Restart application regularly
# Add to cron: 0 2 * * * systemctl restart sergas-app

# Use memory limits
# systemd: MemoryLimit=4G
# Docker: mem_limit: 4g
# Kubernetes: resources.limits.memory: 4Gi
```

---

## Security Issues

### Issue: Unauthorized Access Attempts

**Symptoms:**
- Failed authentication logs
- Suspicious IP addresses
- Brute force attempts

**Diagnosis:**

```bash
# Check failed authentications
journalctl -u sergas-app | grep "authentication failed" | tail -50

# Analyze access patterns
journalctl -u sergas-app | grep "path=/api" | \
  awk '{print $(NF-2)}' | sort | uniq -c | sort -rn

# Check for unusual IPs
journalctl -u sergas-app | grep "remote_ip=" | \
  sed 's/.*remote_ip=\([^ ]*\).*/\1/' | sort | uniq -c | sort -rn
```

**Solutions:**

```bash
# Enable rate limiting
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=60

# Block suspicious IPs
sudo ufw deny from <IP-ADDRESS>

# Enable fail2ban
sudo apt install fail2ban
# Configure jail for sergas-app

# Enforce strong authentication
REQUIRE_MFA=true
SESSION_TIMEOUT=1800  # 30 minutes

# Review and revoke old sessions
python scripts/revoke_old_sessions.py --older-than 7d
```

---

## Infrastructure Issues

### Issue: Load Balancer Health Check Failures

**Symptoms:**
- Instances marked unhealthy
- Traffic not routed
- 503 Service Unavailable

**Diagnosis:**

```bash
# Test health endpoint
curl -v http://localhost:8000/health

# Check load balancer logs
# (varies by provider: AWS ELB, GCP LB, etc.)

# Verify instance is running
systemctl status sergas-app

# Check network connectivity
netstat -tulpn | grep 8000
```

**Solutions:**

```bash
# Fix health endpoint
# Ensure returns HTTP 200

# Increase health check timeout
# Load balancer config: timeout = 10s

# Fix application startup time
# Ensure starts within health check interval

# Check firewall rules
sudo ufw allow from <LB-IP> to any port 8000
```

---

## Support

For additional troubleshooting support:

- **Runbooks**: `/docs/runbooks/`
- **Operations Manual**: `/docs/production/operations_manual.md`
- **On-Call**: devops-oncall@sergas.com
- **Slack**: #sergas-ops

---

**Last Updated**: 2025-10-19
**Version**: 1.0.0
**Maintained by**: Sergas DevOps Team
