# Sergas Super Account Manager - Monitoring Setup Guide

**Version:** 1.0.0
**Last Updated:** 2025-10-19
**Maintainer:** DevOps Team

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Components](#components)
5. [Metrics Reference](#metrics-reference)
6. [Dashboard Guide](#dashboard-guide)
7. [Alert Configuration](#alert-configuration)
8. [Troubleshooting](#troubleshooting)
9. [Production Deployment](#production-deployment)
10. [Best Practices](#best-practices)

---

## Overview

This guide covers the complete observability stack for the Sergas Super Account Manager application, including:

- **Prometheus**: Time-series metrics collection and storage
- **Grafana**: Visualization and dashboards
- **AlertManager**: Alert routing and notification
- **Exporters**: System, database, and cache metrics
- **Custom Metrics**: Business and application-specific metrics

### Key Features

- Real-time monitoring of system health
- Business metrics tracking (accounts, recommendations)
- Performance monitoring (latency, throughput)
- Error tracking and alerting
- Pre-configured dashboards
- Production-ready alert rules

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Sergas Application Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  FastAPI App │  │   Agents     │  │  Background  │          │
│  │  /metrics    │  │  (Custom)    │  │    Jobs      │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          ├──────────────────┴──────────────────┘
          │ prometheus_client metrics
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Metrics Collection Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Prometheus  │◄─┤Node Exporter │  │   cAdvisor   │          │
│  │   (Server)   │◄─┤  (System)    │  │ (Containers) │          │
│  │   :9090      │◄─┤Postgres Exp. │  │Redis Exporter│          │
│  └──────┬───────┘  └──────────────┘  └──────────────┘          │
└─────────┼───────────────────────────────────────────────────────┘
          │
          ├───────────► AlertManager (Alerts) :9093
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Visualization Layer                           │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              Grafana Dashboards :3000                 │       │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐             │       │
│  │  │ System   │ │  Agent   │ │Business  │ ...         │       │
│  │  │ Overview │ │  Perf.   │ │ Metrics  │             │       │
│  │  └──────────┘ └──────────┘ └──────────┘             │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Sergas application configured with metrics endpoint
- Network access to application services

### 1. Start Monitoring Stack

```bash
# Navigate to monitoring directory
cd docker/monitoring

# Start all monitoring services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f
```

### 2. Access Dashboards

- **Grafana**: http://localhost:3000
  - Username: `admin`
  - Password: `sergas_admin_2025`
- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093

### 3. Verify Metrics Collection

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Test application metrics endpoint
curl http://localhost:8000/metrics
```

### 4. Import Dashboards

Dashboards are automatically provisioned from `/grafana/dashboards/`:

1. System Overview
2. Agent Performance
3. Sync Pipeline
4. Error Tracking
5. Business Metrics

---

## Components

### Prometheus Server

**Port:** 9090
**Configuration:** `/config/prometheus/prometheus.yml`

**Key Features:**
- 15-second scrape interval
- 30-day data retention
- Alert rule evaluation
- Service discovery

**Configuration Example:**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'sergas_app'
    static_configs:
      - targets: ['host.docker.internal:8000']
```

**Useful Queries:**

```promql
# Request rate
rate(sergas_http_requests_total[5m])

# Error percentage
rate(sergas_http_requests_total{status=~"5.."}[5m])
  / rate(sergas_http_requests_total[5m]) * 100

# P95 latency
histogram_quantile(0.95,
  rate(sergas_http_request_duration_seconds_bucket[5m]))
```

### AlertManager

**Port:** 9093
**Configuration:** `/config/alerts/alertmanager.yml`

**Alert Routing:**

```yaml
route:
  receiver: 'default-receiver'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
      repeat_interval: 5m
```

**Notification Channels:**
- Slack (critical alerts)
- Email (daily digest)
- PagerDuty (production incidents)

### Grafana

**Port:** 3000
**Configuration:** Auto-provisioned datasources and dashboards

**Features:**
- Pre-configured Prometheus datasource
- 5 production-ready dashboards
- Alert annotations
- User authentication

**Dashboard Locations:**
- `/grafana/dashboards/system_overview.json`
- `/grafana/dashboards/agent_performance.json`
- `/grafana/dashboards/sync_pipeline.json`
- `/grafana/dashboards/error_tracking.json`
- `/grafana/dashboards/business_metrics.json`

### Exporters

#### Node Exporter (System Metrics)
**Port:** 9100
**Metrics:** CPU, Memory, Disk, Network

```promql
# CPU usage
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory usage
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes)
  / node_memory_MemTotal_bytes * 100
```

#### PostgreSQL Exporter
**Port:** 9187
**Metrics:** Connections, queries, transactions

```promql
# Active connections
pg_stat_database_numbackends

# Query performance
rate(pg_stat_statements_mean_exec_time[5m])
```

#### Redis Exporter
**Port:** 9121
**Metrics:** Memory, keys, operations

```promql
# Hit rate
rate(redis_keyspace_hits_total[5m])
  / (rate(redis_keyspace_hits_total[5m])
  + rate(redis_keyspace_misses_total[5m]))
```

#### cAdvisor (Container Metrics)
**Port:** 8080
**Metrics:** Container CPU, memory, network

```promql
# Container CPU
rate(container_cpu_usage_seconds_total[5m])

# Container memory
container_memory_usage_bytes
```

---

## Metrics Reference

### HTTP Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `sergas_http_requests_total` | Counter | Total HTTP requests | method, endpoint, status |
| `sergas_http_request_duration_seconds` | Histogram | Request latency | method, endpoint |
| `sergas_http_requests_in_progress` | Gauge | In-flight requests | method, endpoint |

### Zoho Integration Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `sergas_zoho_api_calls_total` | Counter | Zoho API calls | operation, status |
| `sergas_zoho_api_duration_seconds` | Histogram | API call latency | operation |
| `sergas_zoho_sync_failures_total` | Counter | Sync failures | sync_type, error_type |
| `sergas_zoho_accounts_synced_total` | Counter | Accounts synced | sync_type |
| `sergas_zoho_rate_limit_remaining` | Gauge | Rate limit quota | api_type |

### Memory & Knowledge Graph Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `sergas_memory_processing_duration_seconds` | Histogram | Processing time | operation |
| `sergas_memory_documents_processed_total` | Counter | Documents processed | document_type, status |
| `sergas_memory_graph_nodes_total` | Gauge | Graph nodes | node_type |
| `sergas_memory_graph_relationships_total` | Gauge | Graph edges | relationship_type |

### Agent Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `sergas_agent_task_duration_seconds` | Histogram | Task execution time | agent_type, task_type |
| `sergas_agent_task_attempts_total` | Counter | Task attempts | agent_type, task_type |
| `sergas_agent_task_failures_total` | Counter | Task failures | agent_type, task_type, error_type |
| `sergas_agent_queue_size` | Gauge | Queue size | agent_type |
| `sergas_agent_concurrent_tasks` | Gauge | Active tasks | agent_type |

### Business Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `sergas_recommendations_generated_total` | Counter | Recommendations | recommendation_type, priority |
| `sergas_recommendations_accepted_total` | Counter | Accepted recommendations | recommendation_type |
| `sergas_recommendation_confidence_score` | Histogram | Confidence scores | recommendation_type |
| `sergas_accounts_active_total` | Gauge | Active accounts | account_type |
| `sergas_cross_sell_opportunities_identified_total` | Counter | Cross-sell opportunities | product_category |

### Cache Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `sergas_cache_hits_total` | Counter | Cache hits | cache_type, key_pattern |
| `sergas_cache_misses_total` | Counter | Cache misses | cache_type, key_pattern |
| `sergas_cache_operation_duration_seconds` | Histogram | Operation latency | operation, cache_type |

---

## Dashboard Guide

### 1. System Overview Dashboard

**Purpose:** High-level system health and performance

**Key Panels:**
- Service health status (UP/DOWN)
- HTTP request rate and error rate
- API latency (p95, p99)
- CPU and memory usage
- Database connections
- Cache hit rate

**Use Cases:**
- Daily health checks
- Incident response
- Capacity planning

**Alert Triggers:**
- Service down > 1 minute
- Error rate > 5%
- P95 latency > 2 seconds

### 2. Agent Performance Dashboard

**Purpose:** Monitor AI agent task execution

**Key Panels:**
- Agent task execution time
- Task success rate
- Queue size and backlog
- Concurrent task processing
- Failure breakdown by type

**Use Cases:**
- Agent optimization
- Bottleneck identification
- Performance tuning

**Alert Triggers:**
- Queue size > 1000 items for 15m
- Failure rate > 5%
- P95 execution time degradation

### 3. Sync Pipeline Dashboard

**Purpose:** Zoho integration monitoring

**Key Panels:**
- Zoho API call rate
- API latency
- Rate limit status
- Accounts synced
- Sync failures
- Sync lag

**Use Cases:**
- Integration health
- Rate limit management
- Data freshness monitoring

**Alert Triggers:**
- Sync lag > 1 hour
- Rate limit < 20%
- Sync failure rate spike

### 4. Error Tracking Dashboard

**Purpose:** Comprehensive error monitoring

**Key Panels:**
- Overall error rate
- HTTP error breakdown
- Errors by severity
- Top error types
- Unhandled exceptions

**Use Cases:**
- Debugging issues
- Error pattern analysis
- Quality assurance

**Alert Triggers:**
- Unhandled exceptions > 0.1/sec
- Critical error count spike

### 5. Business Metrics Dashboard

**Purpose:** Track business KPIs

**Key Panels:**
- Active accounts
- Recommendations generated
- Acceptance rate
- Cross-sell opportunities
- Confidence score distribution

**Use Cases:**
- Business reporting
- Feature effectiveness
- ROI tracking

---

## Alert Configuration

### Critical Alerts

**ServiceDown**
```yaml
expr: up{job=~"sergas_app|postgres|redis"} == 0
for: 1m
severity: critical
action: Immediate investigation required
```

**HighErrorRate**
```yaml
expr: rate(sergas_http_requests_total{status=~"5.."}[5m]) > 0.05
for: 5m
severity: critical
action: Check application logs, investigate root cause
```

**APILatencyCritical**
```yaml
expr: histogram_quantile(0.95, rate(sergas_http_request_duration_seconds_bucket[5m])) > 2
for: 5m
severity: critical
action: Check database performance, agent queue
```

### Warning Alerts

**HighCPUUsage**
```yaml
expr: 100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 85
for: 10m
severity: warning
action: Consider scaling, optimize workload
```

**DatabaseConnectionPoolExhausted**
```yaml
expr: pg_stat_database_numbackends / pg_settings_max_connections > 0.9
for: 2m
severity: critical
action: Increase pool size or investigate connection leaks
```

### Info Alerts

**APIRateLimitApproaching**
```yaml
expr: sergas_rate_limit_remaining / sergas_rate_limit_total < 0.2
for: 5m
severity: info
action: Monitor usage, consider rate limiting clients
```

### Alert Routing

```yaml
# Critical → Slack + PagerDuty + Email
# Warning → Slack + Email
# Info → Email digest (daily)

route:
  receiver: 'default-receiver'
  routes:
    - match: {severity: critical}
      receiver: 'critical-alerts'
      repeat_interval: 5m
    - match: {severity: warning}
      receiver: 'warning-alerts'
      repeat_interval: 4h
```

---

## Troubleshooting

### Prometheus Not Scraping Targets

**Symptoms:** Targets show as "DOWN" in Prometheus UI

**Solutions:**
```bash
# Check network connectivity
docker exec sergas_prometheus ping sergas_app

# Verify application metrics endpoint
curl http://localhost:8000/metrics

# Check Prometheus config
docker exec sergas_prometheus cat /etc/prometheus/prometheus.yml

# Reload Prometheus configuration
curl -X POST http://localhost:9090/-/reload
```

### Grafana Dashboards Not Loading

**Symptoms:** Blank dashboards or "No data" errors

**Solutions:**
```bash
# Verify Prometheus datasource
curl http://localhost:3000/api/datasources

# Check dashboard provisioning
docker exec sergas_grafana ls -la /var/lib/grafana/dashboards

# Restart Grafana
docker-compose restart grafana

# Check Grafana logs
docker-compose logs grafana
```

### High Memory Usage in Prometheus

**Symptoms:** Prometheus container OOM, slow queries

**Solutions:**
```yaml
# Reduce retention period
--storage.tsdb.retention.time=15d

# Increase memory limit
mem_limit: 4g

# Drop unnecessary metrics via relabel_configs
metric_relabel_configs:
  - source_labels: [__name__]
    regex: 'expensive_metric.*'
    action: drop
```

### Missing Metrics

**Symptoms:** Expected metrics not appearing

**Solutions:**
```python
# Verify metric registration in application
from src.monitoring import metrics_collector

# Check metric naming
metrics_collector.record_http_request(
    method="GET",
    endpoint="/api/v1/accounts",
    status=200,
    duration=0.5
)

# Enable debug logging
import logging
logging.getLogger('prometheus_client').setLevel(logging.DEBUG)
```

### Alerts Not Firing

**Symptoms:** No alerts despite metric thresholds exceeded

**Solutions:**
```bash
# Check alert rules
curl http://localhost:9090/api/v1/rules

# Verify AlertManager config
docker exec sergas_alertmanager cat /etc/alertmanager/config.yml

# Test alert evaluation
curl 'http://localhost:9090/api/v1/query?query=ALERTS'

# Check AlertManager logs
docker-compose logs alertmanager
```

---

## Production Deployment

### Security Hardening

1. **Change Default Credentials**
```yaml
# Grafana
environment:
  - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
```

2. **Enable TLS**
```yaml
# Prometheus
command:
  - '--web.config.file=/etc/prometheus/web-config.yml'
```

3. **Restrict Network Access**
```yaml
# Only expose necessary ports
ports:
  - "127.0.0.1:9090:9090"  # Prometheus (localhost only)
```

4. **Authentication**
```yaml
# Grafana LDAP/OAuth
environment:
  - GF_AUTH_LDAP_ENABLED=true
  - GF_AUTH_LDAP_CONFIG_FILE=/etc/grafana/ldap.toml
```

### High Availability Setup

**Multi-node Prometheus:**
```yaml
# Prometheus federation
- job_name: 'federate'
  scrape_interval: 15s
  honor_labels: true
  metrics_path: '/federate'
  params:
    'match[]':
      - '{job=~"sergas_.*"}'
  static_configs:
    - targets:
      - 'prometheus-1:9090'
      - 'prometheus-2:9090'
```

**Grafana Clustering:**
```yaml
# Shared database
environment:
  - GF_DATABASE_TYPE=postgres
  - GF_DATABASE_HOST=postgres:5432
  - GF_DATABASE_NAME=grafana
```

### Backup Strategy

**Prometheus Data:**
```bash
# Snapshot API
curl -XPOST http://localhost:9090/api/v1/admin/tsdb/snapshot

# Regular backups
docker run --rm -v prometheus_data:/data \
  -v /backup:/backup alpine \
  tar czf /backup/prometheus-$(date +%Y%m%d).tar.gz /data
```

**Grafana Dashboards:**
```bash
# Export all dashboards
for dash in $(curl -s "http://admin:password@localhost:3000/api/search" | jq -r '.[] | .uid'); do
  curl -s "http://admin:password@localhost:3000/api/dashboards/uid/$dash" | \
    jq -r '.dashboard' > "backup/dashboard-${dash}.json"
done
```

### Performance Tuning

**Prometheus:**
```yaml
command:
  - '--storage.tsdb.retention.time=30d'
  - '--storage.tsdb.min-block-duration=2h'
  - '--storage.tsdb.max-block-duration=2h'
  - '--query.max-concurrency=20'
  - '--query.timeout=2m'
```

**Grafana:**
```yaml
environment:
  - GF_DATABASE_CACHE_MODE=shared
  - GF_DATAPROXY_TIMEOUT=30
  - GF_DATAPROXY_MAX_IDLE_CONNECTIONS=100
```

---

## Best Practices

### Metric Design

1. **Use Appropriate Metric Types**
   - Counter: Monotonically increasing (requests, errors)
   - Gauge: Can go up/down (queue size, temperature)
   - Histogram: Distributions (latency, size)

2. **Label Best Practices**
   - Keep cardinality low (< 1000 unique label combinations)
   - Use meaningful, consistent labels
   - Avoid high-cardinality labels (user IDs, timestamps)

3. **Naming Conventions**
   ```
   <namespace>_<subsystem>_<metric>_<unit>
   Example: sergas_http_requests_total
   ```

### Dashboard Design

1. **Information Hierarchy**
   - Most critical metrics at top
   - Group related panels
   - Use consistent time ranges

2. **Color Usage**
   - Green: Healthy/Good
   - Yellow: Warning
   - Red: Critical/Error
   - Blue: Informational

3. **Panel Types**
   - Stat: Single values, KPIs
   - Graph: Time-series trends
   - Gauge: Thresholds, percentages
   - Table: Detailed breakdowns

### Alert Design

1. **Alert Fatigue Prevention**
   - Set appropriate thresholds
   - Use `for` duration to avoid flapping
   - Group related alerts
   - Implement inhibition rules

2. **Actionable Alerts**
   - Clear description
   - Runbook URL
   - Suggested remediation
   - Dashboard link

3. **Severity Levels**
   - Critical: Immediate action required
   - Warning: Investigate soon
   - Info: Awareness only

### Operational Excellence

1. **Regular Reviews**
   - Weekly dashboard review
   - Monthly alert tuning
   - Quarterly capacity planning

2. **Documentation**
   - Keep runbooks updated
   - Document metric meanings
   - Maintain change log

3. **Testing**
   - Test alerts in staging
   - Validate dashboards
   - Simulate failures

---

## Support and Resources

### Documentation
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [AlertManager Guide](https://prometheus.io/docs/alerting/latest/alertmanager/)

### Internal Resources
- Runbooks: `/docs/runbooks/`
- Alert Definitions: `/config/alerts/alert_rules.yml`
- Dashboard JSON: `/grafana/dashboards/`

### Contact
- **DevOps Team**: devops@sergas.com
- **On-Call**: Use PagerDuty escalation
- **Slack**: #sergas-monitoring

---

**Document Version:** 1.0.0
**Last Review:** 2025-10-19
**Next Review:** 2025-11-19
