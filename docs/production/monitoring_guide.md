# Monitoring and Observability Guide

## Overview

This guide covers comprehensive monitoring, alerting, and observability for the Sergas Super Account Manager production system.

## Table of Contents

1. [Monitoring Stack](#monitoring-stack)
2. [Metrics Collection](#metrics-collection)
3. [Dashboards](#dashboards)
4. [Alerting](#alerting)
5. [Logging](#logging)
6. [Tracing](#tracing)
7. [Health Checks](#health-checks)

---

## Monitoring Stack

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Application Layer                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  FastAPI + Agents                                       │  │
│  │  • Prometheus metrics exporter                          │  │
│  │  • Structured logging (JSON)                            │  │
│  │  • OpenTelemetry instrumentation                        │  │
│  └──────┬───────────────┬───────────────┬──────────────────┘  │
└─────────┼───────────────┼───────────────┼─────────────────────┘
          │               │               │
     Metrics          Logs           Traces
          │               │               │
┌─────────▼───────┐ ┌─────▼──────┐ ┌─────▼──────────┐
│  Prometheus     │ │  Loki      │ │  Jaeger        │
│  (Metrics)      │ │  (Logs)    │ │  (Traces)      │
│  • Time-series  │ │  • Log     │ │  • Distributed │
│  • Scraping     │ │    aggr    │ │    tracing     │
│  • PromQL       │ │  • Search  │ │  • Sampling    │
└─────────┬───────┘ └─────┬──────┘ └─────┬──────────┘
          │               │               │
          └───────────────┴───────────────┘
                          │
                ┌─────────▼──────────┐
                │     Grafana        │
                │  (Visualization)   │
                │  • Dashboards      │
                │  • Alerts          │
                │  • Annotations     │
                └─────────┬──────────┘
                          │
                ┌─────────▼──────────┐
                │   AlertManager     │
                │  (Alert Routing)   │
                │  • PagerDuty       │
                │  • Slack           │
                │  • Email           │
                └────────────────────┘
```

### Components

| Component | Purpose | Port | Storage |
|-----------|---------|------|---------|
| **Prometheus** | Metrics collection & storage | 9090 | 100GB SSD |
| **Grafana** | Visualization & dashboards | 3000 | 10GB SSD |
| **AlertManager** | Alert routing & grouping | 9093 | 1GB SSD |
| **Loki** | Log aggregation | 3100 | 200GB SSD |
| **Jaeger** | Distributed tracing | 16686 | 50GB SSD |

---

## Metrics Collection

### Application Metrics

#### Agent Metrics

```python
# src/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Session metrics
agent_sessions_total = Counter(
    'sergas_agent_sessions_total',
    'Total agent sessions',
    ['agent_type', 'status']
)

agent_session_duration = Histogram(
    'sergas_agent_session_duration_seconds',
    'Agent session duration',
    ['agent_type'],
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

agent_sessions_active = Gauge(
    'sergas_agent_sessions_active',
    'Currently active agent sessions',
    ['agent_type']
)

# Tool call metrics
agent_tool_calls_total = Counter(
    'sergas_agent_tool_calls_total',
    'Total agent tool calls',
    ['agent_type', 'tool_name', 'status']
)

agent_tool_call_duration = Histogram(
    'sergas_agent_tool_call_duration_seconds',
    'Agent tool call duration',
    ['agent_type', 'tool_name'],
    buckets=[0.1, 0.5, 1, 2, 5, 10]
)

# Recommendation metrics
recommendations_generated = Counter(
    'sergas_recommendations_generated_total',
    'Total recommendations generated',
    ['type', 'priority']
)

recommendations_approved = Counter(
    'sergas_recommendations_approved_total',
    'Total recommendations approved',
    ['type']
)

recommendation_confidence = Histogram(
    'sergas_recommendation_confidence',
    'Recommendation confidence scores',
    ['type'],
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)
```

#### API Metrics

```python
# HTTP request metrics
http_requests_total = Counter(
    'sergas_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'sergas_http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5]
)

http_requests_in_progress = Gauge(
    'sergas_http_requests_in_progress',
    'Currently processing HTTP requests',
    ['method', 'endpoint']
)
```

#### Integration Metrics

```python
# Zoho API metrics
zoho_api_calls_total = Counter(
    'sergas_zoho_api_calls_total',
    'Total Zoho API calls',
    ['tier', 'operation', 'status']
)

zoho_api_call_duration = Histogram(
    'sergas_zoho_api_call_duration_seconds',
    'Zoho API call duration',
    ['tier', 'operation'],
    buckets=[0.5, 1, 2, 5, 10, 30]
)

zoho_circuit_breaker_state = Gauge(
    'sergas_zoho_circuit_breaker_state',
    'Zoho circuit breaker state (0=closed, 1=open, 2=half-open)',
    ['tier']
)

# Cognee metrics
cognee_queries_total = Counter(
    'sergas_cognee_queries_total',
    'Total Cognee queries',
    ['operation', 'status']
)

cognee_query_duration = Histogram(
    'sergas_cognee_query_duration_seconds',
    'Cognee query duration',
    ['operation']
)
```

#### Database Metrics

```python
# Database connection pool
db_connections_active = Gauge(
    'sergas_db_connections_active',
    'Active database connections'
)

db_connections_total = Gauge(
    'sergas_db_connections_total',
    'Total database connections'
)

db_query_duration = Histogram(
    'sergas_db_query_duration_seconds',
    'Database query duration',
    ['operation'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 5]
)

db_queries_total = Counter(
    'sergas_db_queries_total',
    'Total database queries',
    ['operation', 'status']
)
```

### System Metrics

#### Resource Usage

```python
# Memory
process_memory_bytes = Gauge(
    'sergas_process_memory_bytes',
    'Process memory usage in bytes'
)

# CPU
process_cpu_seconds_total = Counter(
    'sergas_process_cpu_seconds_total',
    'Total CPU time consumed'
)

# File descriptors
process_open_fds = Gauge(
    'sergas_process_open_fds',
    'Number of open file descriptors'
)
```

### Metrics Endpoint

```python
# src/main.py
from prometheus_client import make_asgi_app

# Mount metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

**Access metrics:**
```bash
curl http://localhost:8000/metrics

# Output:
# HELP sergas_agent_sessions_total Total agent sessions
# TYPE sergas_agent_sessions_total counter
sergas_agent_sessions_total{agent_type="ZohoDataScout",status="success"} 1543.0
sergas_agent_sessions_total{agent_type="MemoryAnalyst",status="success"} 1502.0
# ...
```

---

## Dashboards

### Grafana Setup

#### 1. Install Grafana

```bash
# Docker Compose
docker-compose up -d grafana

# Or Kubernetes
kubectl apply -f kubernetes/base/grafana-deployment.yaml

# Access Grafana
open http://localhost:3000
# Default credentials: admin/admin
```

#### 2. Configure Data Sources

```bash
# Add Prometheus data source
curl -X POST http://admin:admin@localhost:3000/api/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://prometheus:9090",
    "access": "proxy",
    "isDefault": true
  }'

# Add Loki data source
curl -X POST http://admin:admin@localhost:3000/api/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Loki",
    "type": "loki",
    "url": "http://loki:3100",
    "access": "proxy"
  }'
```

### Pre-Built Dashboards

#### System Overview Dashboard

**Panels:**
1. **Request Rate**: HTTP requests per second
2. **Error Rate**: 5xx errors percentage
3. **Response Time**: P50, P95, P99 latency
4. **Active Sessions**: Currently running agent sessions
5. **Resource Usage**: CPU, Memory, Disk
6. **Integration Health**: Zoho, Cognee, Database status

**Import:**
```bash
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @grafana/dashboards/system-overview.json
```

#### Agent Performance Dashboard

**Panels:**
1. **Session Success Rate**: Success vs failure ratio
2. **Session Duration**: Agent execution time by type
3. **Tool Call Distribution**: Tool usage breakdown
4. **Recommendation Generation**: Recommendations per hour
5. **Confidence Scores**: Distribution of confidence scores
6. **Approval Rate**: Approved vs rejected recommendations

**PromQL Queries:**
```promql
# Session success rate
rate(sergas_agent_sessions_total{status="success"}[5m]) /
rate(sergas_agent_sessions_total[5m]) * 100

# Average session duration
rate(sergas_agent_session_duration_seconds_sum[5m]) /
rate(sergas_agent_session_duration_seconds_count[5m])

# Recommendations per hour
rate(sergas_recommendations_generated_total[1h]) * 3600

# P95 tool call duration
histogram_quantile(0.95, rate(sergas_agent_tool_call_duration_seconds_bucket[5m]))
```

#### Integration Health Dashboard

**Panels:**
1. **Zoho API Status**: Calls per tier, success rate
2. **Circuit Breaker States**: Open/closed status
3. **Cognee Performance**: Query latency, success rate
4. **Database Performance**: Connection pool, query time
5. **Redis Performance**: Hit rate, latency

**PromQL Queries:**
```promql
# Zoho API success rate by tier
sum(rate(sergas_zoho_api_calls_total{status="success"}[5m])) by (tier) /
sum(rate(sergas_zoho_api_calls_total[5m])) by (tier) * 100

# Circuit breaker state (0=closed, 1=open)
sergas_zoho_circuit_breaker_state

# Database connection pool usage
sergas_db_connections_active / sergas_db_connections_total * 100

# Cognee query P99 latency
histogram_quantile(0.99, rate(sergas_cognee_query_duration_seconds_bucket[5m]))
```

---

## Alerting

### Alert Rules

Create `/etc/prometheus/alerts.yml`:

```yaml
groups:
  - name: sergas_critical
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          sum(rate(sergas_http_requests_total{status=~"5.."}[5m])) /
          sum(rate(sergas_http_requests_total[5m])) * 100 > 5
        for: 5m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}% (threshold: 5%)"

      # Service down
      - alert: ServiceDown
        expr: up{job="sergas-app"} == 0
        for: 1m
        labels:
          severity: critical
          team: devops
        annotations:
          summary: "Service is down"
          description: "{{ $labels.instance }} is unreachable"

      # Database connection pool exhausted
      - alert: DatabasePoolExhausted
        expr: |
          sergas_db_connections_active / sergas_db_connections_total > 0.9
        for: 2m
        labels:
          severity: critical
          team: database
        annotations:
          summary: "Database connection pool exhausted"
          description: "Pool usage: {{ $value | humanizePercentage }}"

      # Circuit breaker open
      - alert: CircuitBreakerOpen
        expr: sergas_zoho_circuit_breaker_state == 1
        for: 5m
        labels:
          severity: warning
          team: integrations
        annotations:
          summary: "Zoho circuit breaker open"
          description: "Circuit breaker for {{ $labels.tier }} is open"

  - name: sergas_warning
    interval: 1m
    rules:
      # High response time
      - alert: HighResponseTime
        expr: |
          histogram_quantile(0.95,
            rate(sergas_http_request_duration_seconds_bucket[5m])
          ) > 2
        for: 10m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "High API response time"
          description: "P95 latency: {{ $value }}s (threshold: 2s)"

      # High memory usage
      - alert: HighMemoryUsage
        expr: |
          process_resident_memory_bytes / 1024 / 1024 / 1024 > 3
        for: 10m
        labels:
          severity: warning
          team: devops
        annotations:
          summary: "High memory usage"
          description: "Memory usage: {{ $value }}GB (threshold: 3GB)"

      # Low recommendation confidence
      - alert: LowRecommendationConfidence
        expr: |
          histogram_quantile(0.5,
            rate(sergas_recommendation_confidence_bucket[1h])
          ) < 0.7
        for: 1h
        labels:
          severity: warning
          team: ml
        annotations:
          summary: "Low recommendation confidence"
          description: "Median confidence: {{ $value }} (threshold: 0.7)"

      # Disk space low
      - alert: DiskSpaceLow
        expr: |
          (node_filesystem_avail_bytes{mountpoint="/"} /
           node_filesystem_size_bytes{mountpoint="/"}) * 100 < 20
        for: 5m
        labels:
          severity: warning
          team: devops
        annotations:
          summary: "Low disk space"
          description: "Available: {{ $value }}%"
```

### AlertManager Configuration

Create `/etc/alertmanager/config.yml`:

```yaml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    # Critical alerts -> PagerDuty + Slack
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
      continue: true

    - match:
        severity: critical
      receiver: 'slack-critical'

    # Warning alerts -> Slack only
    - match:
        severity: warning
      receiver: 'slack-warning'

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#sergas-alerts'
        title: 'Sergas Alert'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
        description: '{{ .CommonAnnotations.summary }}'

  - name: 'slack-critical'
    slack_configs:
      - channel: '#sergas-critical'
        color: 'danger'
        title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
        text: |
          *Summary:* {{ .CommonAnnotations.summary }}
          *Description:* {{ .CommonAnnotations.description }}
          *Severity:* {{ .CommonLabels.severity }}

  - name: 'slack-warning'
    slack_configs:
      - channel: '#sergas-warnings'
        color: 'warning'
        title: '⚠️ WARNING: {{ .GroupLabels.alertname }}'
        text: '{{ .CommonAnnotations.description }}'

inhibit_rules:
  # Inhibit warning if critical is firing
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']
```

---

## Logging

### Structured Logging

```python
# src/logging_config.py
import structlog
import logging

def configure_logging():
    """Configure structured logging."""

    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Usage
logger = structlog.get_logger(__name__)

logger.info(
    "account_analysis_started",
    account_id="ACC-123",
    session_id="sess_abc",
    user_id="USR-456"
)
```

### Log Format

```json
{
  "event": "account_analysis_started",
  "timestamp": "2024-10-19T10:00:00.123456Z",
  "level": "info",
  "logger": "src.agents.orchestrator",
  "account_id": "ACC-123",
  "session_id": "sess_abc",
  "user_id": "USR-456",
  "request_id": "req_abc123"
}
```

### Log Aggregation (Loki)

```yaml
# docker-compose.yml
loki:
  image: grafana/loki:2.9.0
  ports:
    - "3100:3100"
  volumes:
    - ./loki-config.yaml:/etc/loki/local-config.yaml
    - loki-data:/loki

promtail:
  image: grafana/promtail:2.9.0
  volumes:
    - /var/log:/var/log
    - ./promtail-config.yaml:/etc/promtail/config.yaml
  command: -config.file=/etc/promtail/config.yaml
```

**Query logs in Grafana:**
```logql
# All errors
{app="sergas"} |= "ERROR"

# Specific agent errors
{app="sergas", agent="ZohoDataScout"} |= "ERROR"

# By account
{app="sergas"} | json | account_id="ACC-123"

# Slow queries
{app="sergas"} | json | duration > 5000
```

---

## Tracing

### OpenTelemetry Setup

```python
# src/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def configure_tracing():
    """Configure OpenTelemetry tracing."""

    resource = Resource(attributes={
        SERVICE_NAME: "sergas-super-account-manager"
    })

    provider = TracerProvider(resource=resource)

    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",
        agent_port=6831,
    )

    provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    trace.set_tracer_provider(provider)

# Usage
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("analyze_account") as span:
    span.set_attribute("account_id", account_id)
    span.set_attribute("priority", priority)

    # Your code here
    result = await orchestrator.analyze(account_id)

    span.set_attribute("recommendations_count", len(result.recommendations))
```

---

## Health Checks

### Liveness & Readiness

```python
# src/health.py
from fastapi import APIRouter, Response, status

router = APIRouter()

@router.get("/health/live")
async def liveness():
    """Liveness probe - is the service running?"""
    return {"status": "alive"}

@router.get("/health/ready")
async def readiness():
    """Readiness probe - is the service ready to accept traffic?"""
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "zoho": await check_zoho(),
        "cognee": await check_cognee()
    }

    all_healthy = all(checks.values())

    return Response(
        content=json.dumps({
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks
        }),
        status_code=status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    )
```

**Kubernetes configuration:**
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

**Last Updated**: 2025-10-19
**Version**: 1.0.0
**Maintained by**: Sergas Monitoring Team
