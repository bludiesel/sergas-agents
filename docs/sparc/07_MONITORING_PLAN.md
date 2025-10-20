# Monitoring and Observability Plan: CopilotKit Multi-Agent System

**Version:** 1.0.0
**Created:** 2025-10-19
**Author:** DevOps Architect
**Status:** Implementation Ready

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Monitoring Architecture](#monitoring-architecture)
3. [Logging Strategy](#logging-strategy)
4. [Metrics Collection](#metrics-collection)
5. [Error Tracking](#error-tracking)
6. [Distributed Tracing](#distributed-tracing)
7. [Dashboards](#dashboards)
8. [Alerting Rules](#alerting-rules)
9. [Debugging Toolkit](#debugging-toolkit)
10. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

This document defines comprehensive monitoring, logging, and observability for the CopilotKit-based multi-agent system with HITL workflows spanning:

- **Frontend (React/Next.js)**: User interactions and UI state
- **Next.js API Routes**: CopilotKit runtime and SSE streaming
- **FastAPI Backend**: Agent orchestration and business logic
- **Multi-Agent System**: ZohoDataScout, MemoryAnalyst, RecommendationAuthor agents

### Key Objectives

1. **End-to-End Request Tracking**: Trace requests from frontend clicks through agent execution to final responses
2. **Agent Visibility**: Monitor agent handoffs, state transitions, and execution metrics
3. **HITL Workflow Monitoring**: Track approval/rejection flows, approval latency, and user engagement
4. **Performance Optimization**: Identify bottlenecks in agent execution and API calls
5. **Error Detection**: Capture and categorize errors across the entire stack
6. **Production Readiness**: Enable rapid incident response and debugging

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Metrics** | Prometheus | Time-series metrics collection |
| **Visualization** | Grafana | Dashboards and alerting |
| **Logging** | structlog + Loki | Structured logs with aggregation |
| **Tracing** | OpenTelemetry + Jaeger | Distributed request tracing |
| **Error Tracking** | Sentry (optional) | Exception capture and replay |
| **Frontend Monitoring** | Custom hooks + Vercel Analytics | User interaction tracking |

---

## Monitoring Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  React + CopilotKit + AG UI Protocol                          │  │
│  │  • useCopilotAction hooks                                     │  │
│  │  • AG UI streaming events                                     │  │
│  │  • User interaction tracking                                  │  │
│  │  • Frontend error boundary                                    │  │
│  └───────────────────┬───────────────────────────────────────────┘  │
└────────────────────────┼─────────────────────────────────────────────┘
                         │ HTTPS/SSE
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Next.js API Layer                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  /api/copilotkit (CopilotRuntime)                             │  │
│  │  • AG UI Protocol adapter                                     │  │
│  │  • SSE streaming                                              │  │
│  │  • Request/response logging                                   │  │
│  │  • OpenTelemetry instrumentation                              │  │
│  └───────────────────┬───────────────────────────────────────────┘  │
└────────────────────────┼─────────────────────────────────────────────┘
                         │ HTTP/WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Agent Orchestrator                                           │  │
│  │  • Multi-agent coordination                                   │  │
│  │  • HITL approval workflows                                    │  │
│  │  • AG UI event emission                                       │  │
│  │  • Prometheus metrics export (/metrics)                       │  │
│  │  • structlog structured logging                               │  │
│  │  • OpenTelemetry spans                                        │  │
│  └───────────────────┬───────────────────────────────────────────┘  │
│                      │                                               │
│  ┌──────────────────┴───────────────────────────────────────────┐  │
│  │  Agent Layer                                                  │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │  │
│  │  │ ZohoData     │  │  Memory      │  │Recommendation│       │  │
│  │  │ Scout        │─▶│  Analyst     │─▶│  Author      │       │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘       │  │
│  │  • Agent execution metrics                                    │  │
│  │  • Tool call tracking                                         │  │
│  │  • State transition events                                    │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                         │
                         │ Metrics, Logs, Traces
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Observability Layer                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │
│  │Prometheus  │  │   Loki     │  │  Jaeger    │  │  Grafana   │   │
│  │(Metrics)   │  │  (Logs)    │  │ (Traces)   │  │(Dashboards)│   │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Request Flow with Tracing

```
User Action → Frontend Component → useCopilotAction
                                          │
                                          │ [trace_id: abc123]
                                          ▼
                                   Next.js API Route
                                          │
                                          │ [span: copilot_runtime]
                                          ▼
                                   CopilotRuntime Adapter
                                          │
                                          │ [span: backend_request]
                                          ▼
                                   FastAPI Orchestrator
                                          │
                ┌─────────────────────────┼─────────────────────────┐
                │                         │                         │
        [span: agent_1]            [span: agent_2]          [span: agent_3]
                │                         │                         │
        ZohoDataScout            MemoryAnalyst           RecommendationAuthor
                │                         │                         │
                │          [span: hitl_approval_wait]               │
                │                         │                         │
                └─────────────────────────┴─────────────────────────┘
                                          │
                                          │ [span: response_stream]
                                          ▼
                                   SSE Stream to Client
```

---

## Logging Strategy

### Log Levels and Usage

| Level | Usage | Example Events |
|-------|-------|----------------|
| **DEBUG** | Detailed execution flow, variable values | "Agent executing tool X with params Y" |
| **INFO** | Normal operations, state transitions | "Agent handoff: DataScout → MemoryAnalyst" |
| **WARNING** | Recoverable issues, degraded performance | "Zoho API rate limit approaching", "Retry attempt 2/3" |
| **ERROR** | Failures requiring attention | "Agent execution failed", "HITL timeout" |
| **CRITICAL** | System failures, data loss risk | "Database connection lost", "Circuit breaker open" |

### Structured Logging Schema

#### Base Log Entry

```json
{
  "timestamp": "2025-10-19T14:23:45.123456Z",
  "level": "info",
  "logger": "src.orchestrator",
  "event": "agent_handoff",
  "message": "Handing off from ZohoDataScout to MemoryAnalyst",

  // Request Context
  "trace_id": "abc123xyz",
  "span_id": "span_001",
  "request_id": "req_789",
  "session_id": "sess_456",
  "user_id": "user_123",

  // Agent Context
  "agent_id": "memory_analyst",
  "previous_agent": "zoho_data_scout",
  "execution_step": 2,
  "total_steps": 3,

  // Business Context
  "account_id": "ACC-12345",
  "operation": "account_analysis",

  // Performance
  "duration_ms": 1234,
  "memory_mb": 156.7,

  // Additional metadata
  "environment": "production",
  "hostname": "api-server-01",
  "version": "1.2.3"
}
```

### Event Taxonomy

#### Frontend Events

```python
# User interaction events
frontend_event_types = [
    "user_action_triggered",        # User clicks button
    "copilot_action_started",       # CopilotKit action invoked
    "copilot_action_completed",     # Action finished
    "copilot_action_failed",        # Action error
    "ag_ui_event_received",         # AG UI Protocol event
    "hitl_approval_requested",      # UI shows approval prompt
    "hitl_approval_submitted",      # User approves/rejects
    "sse_connection_opened",        # SSE stream started
    "sse_connection_closed",        # SSE stream ended
    "sse_message_received",         # SSE event received
]
```

#### Backend Events

```python
# Orchestrator events
orchestrator_event_types = [
    "orchestration_started",        # New orchestration request
    "orchestration_completed",      # Orchestration finished
    "orchestration_failed",         # Orchestration error

    "agent_spawned",                # Agent instance created
    "agent_handoff",                # Transition between agents
    "agent_execution_started",      # Agent begins work
    "agent_execution_completed",    # Agent finishes
    "agent_execution_failed",       # Agent error

    "hitl_approval_required",       # HITL workflow triggered
    "hitl_approval_received",       # User responded
    "hitl_approval_timeout",        # No response within timeout

    "tool_call_started",            # Agent calls tool
    "tool_call_completed",          # Tool returns
    "tool_call_failed",             # Tool error

    "state_transition",             # Workflow state change
    "memory_stored",                # Data persisted to memory
    "memory_retrieved",             # Data fetched from memory
]
```

#### Integration Events

```python
# External API events
integration_event_types = [
    "zoho_api_call_started",
    "zoho_api_call_completed",
    "zoho_api_call_failed",
    "zoho_rate_limit_hit",
    "zoho_circuit_breaker_opened",
    "zoho_circuit_breaker_closed",

    "cognee_query_started",
    "cognee_query_completed",
    "cognee_query_failed",

    "database_query_started",
    "database_query_completed",
    "database_query_failed",
    "database_deadlock_detected",
]
```

### Log Correlation

#### Request Tracing

```python
# src/logging/correlation.py
import structlog
from contextvars import ContextVar
import uuid

# Context variables for request tracking
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
session_id_var: ContextVar[str] = ContextVar("session_id", default="")

def bind_request_context(trace_id: str, request_id: str, session_id: str):
    """Bind request context for logging."""
    trace_id_var.set(trace_id)
    request_id_var.set(request_id)
    session_id_var.set(session_id)

    return structlog.contextvars.bind_contextvars(
        trace_id=trace_id,
        request_id=request_id,
        session_id=session_id
    )

def generate_trace_id() -> str:
    """Generate unique trace ID."""
    return f"trace_{uuid.uuid4().hex[:16]}"

def generate_request_id() -> str:
    """Generate unique request ID."""
    return f"req_{uuid.uuid4().hex[:12]}"
```

#### FastAPI Middleware

```python
# src/middleware/logging_middleware.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import structlog

from src.logging.correlation import (
    bind_request_context,
    generate_trace_id,
    generate_request_id
)

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with correlation IDs."""

    async def dispatch(self, request: Request, call_next):
        # Extract or generate trace ID
        trace_id = request.headers.get("X-Trace-Id") or generate_trace_id()
        request_id = generate_request_id()
        session_id = request.headers.get("X-Session-Id", "unknown")

        # Bind context for all logs in this request
        bind_request_context(trace_id, request_id, session_id)

        # Add to request state
        request.state.trace_id = trace_id
        request.state.request_id = request_id
        request.state.session_id = session_id

        start_time = time.time()

        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_ip=request.client.host if request.client else None
        )

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2)
            )

            # Add trace ID to response headers
            response.headers["X-Trace-Id"] = trace_id
            response.headers["X-Request-Id"] = request_id

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error_type=type(e).__name__,
                error_message=str(e),
                duration_ms=round(duration_ms, 2),
                exc_info=True
            )
            raise
```

### Agent Execution Logging

```python
# src/agents/logging.py
import structlog
from typing import Dict, Any
import time

logger = structlog.get_logger(__name__)


class AgentLogger:
    """Helper for agent execution logging."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.logger = logger.bind(agent_id=agent_id)

    def log_execution_start(self, context: Dict[str, Any]):
        """Log agent execution start."""
        self.logger.info(
            "agent_execution_started",
            account_id=context.get("account_id"),
            operation=context.get("operation"),
            input_keys=list(context.keys())
        )

    def log_execution_complete(
        self,
        duration_ms: float,
        result_summary: Dict[str, Any]
    ):
        """Log agent execution completion."""
        self.logger.info(
            "agent_execution_completed",
            duration_ms=round(duration_ms, 2),
            result_summary=result_summary
        )

    def log_execution_error(
        self,
        error: Exception,
        duration_ms: float,
        context: Dict[str, Any]
    ):
        """Log agent execution error."""
        self.logger.error(
            "agent_execution_failed",
            error_type=type(error).__name__,
            error_message=str(error),
            duration_ms=round(duration_ms, 2),
            context=context,
            exc_info=True
        )

    def log_tool_call(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        duration_ms: float,
        success: bool
    ):
        """Log tool call."""
        self.logger.info(
            "tool_call_completed" if success else "tool_call_failed",
            tool_name=tool_name,
            tool_params=tool_params,
            duration_ms=round(duration_ms, 2),
            success=success
        )

    def log_handoff(self, next_agent: str, handoff_data: Dict[str, Any]):
        """Log agent handoff."""
        self.logger.info(
            "agent_handoff",
            next_agent=next_agent,
            handoff_data_keys=list(handoff_data.keys())
        )

    def log_hitl_required(
        self,
        approval_type: str,
        approval_data: Dict[str, Any]
    ):
        """Log HITL approval required."""
        self.logger.info(
            "hitl_approval_required",
            approval_type=approval_type,
            approval_data=approval_data
        )

    def log_hitl_received(
        self,
        approval_type: str,
        approved: bool,
        latency_ms: float
    ):
        """Log HITL approval received."""
        self.logger.info(
            "hitl_approval_received",
            approval_type=approval_type,
            approved=approved,
            latency_ms=round(latency_ms, 2)
        )
```

### Log Aggregation with Loki

#### Loki Configuration

```yaml
# config/loki/loki-config.yaml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
    cache_ttl: 24h
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  ingestion_rate_mb: 16
  ingestion_burst_size_mb: 32

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: true
  retention_period: 720h  # 30 days

query_range:
  align_queries_with_step: true
  max_retries: 5
  cache_results: true
```

#### Promtail Configuration

```yaml
# config/promtail/promtail-config.yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # Scrape FastAPI application logs
  - job_name: fastapi
    static_configs:
      - targets:
          - localhost
        labels:
          job: sergas-api
          app: sergas
          environment: production
          __path__: /var/log/sergas/api/*.log

    pipeline_stages:
      # Parse JSON logs
      - json:
          expressions:
            timestamp: timestamp
            level: level
            logger: logger
            event: event
            trace_id: trace_id
            request_id: request_id
            agent_id: agent_id
            account_id: account_id

      # Extract log level
      - labels:
          level:
          agent_id:
          event:

      # Set timestamp
      - timestamp:
          source: timestamp
          format: RFC3339Nano

      # Drop debug logs in production
      - match:
          selector: '{level="debug"}'
          action: drop

  # Scrape Next.js application logs
  - job_name: nextjs
    static_configs:
      - targets:
          - localhost
        labels:
          job: sergas-frontend
          app: sergas
          environment: production
          __path__: /var/log/sergas/nextjs/*.log

    pipeline_stages:
      - json:
          expressions:
            timestamp: timestamp
            level: level
            message: message
            trace_id: trace_id

      - labels:
          level:

      - timestamp:
          source: timestamp
          format: RFC3339Nano
```

---

## Metrics Collection

### Agent Metrics

#### Agent Execution Metrics

```python
# src/monitoring/agent_metrics.py
from prometheus_client import Counter, Histogram, Gauge, Summary
from typing import Optional

# Agent session metrics
agent_sessions_total = Counter(
    'sergas_agent_sessions_total',
    'Total agent sessions',
    ['agent_type', 'status', 'operation']
)

agent_session_duration_seconds = Histogram(
    'sergas_agent_session_duration_seconds',
    'Agent session execution time',
    ['agent_type', 'operation'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)

agent_sessions_active = Gauge(
    'sergas_agent_sessions_active',
    'Currently active agent sessions',
    ['agent_type']
)

# Agent handoff metrics
agent_handoffs_total = Counter(
    'sergas_agent_handoffs_total',
    'Total agent handoffs',
    ['from_agent', 'to_agent', 'status']
)

agent_handoff_duration_seconds = Histogram(
    'sergas_agent_handoff_duration_seconds',
    'Agent handoff latency',
    ['from_agent', 'to_agent'],
    buckets=[0.1, 0.5, 1, 2, 5, 10]
)

# Tool call metrics
agent_tool_calls_total = Counter(
    'sergas_agent_tool_calls_total',
    'Total agent tool calls',
    ['agent_type', 'tool_name', 'status']
)

agent_tool_call_duration_seconds = Histogram(
    'sergas_agent_tool_call_duration_seconds',
    'Agent tool call execution time',
    ['agent_type', 'tool_name'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30]
)

# Agent state metrics
agent_state_transitions_total = Counter(
    'sergas_agent_state_transitions_total',
    'Total agent state transitions',
    ['agent_type', 'from_state', 'to_state']
)

# Agent error metrics
agent_errors_total = Counter(
    'sergas_agent_errors_total',
    'Total agent errors',
    ['agent_type', 'error_type', 'operation']
)

agent_retries_total = Counter(
    'sergas_agent_retries_total',
    'Total agent retry attempts',
    ['agent_type', 'operation', 'retry_reason']
)
```

#### HITL Workflow Metrics

```python
# Human-in-the-Loop workflow metrics
hitl_approvals_requested_total = Counter(
    'sergas_hitl_approvals_requested_total',
    'Total HITL approvals requested',
    ['approval_type', 'agent_type']
)

hitl_approvals_received_total = Counter(
    'sergas_hitl_approvals_received_total',
    'Total HITL approvals received',
    ['approval_type', 'decision', 'agent_type']
)

hitl_approval_latency_seconds = Histogram(
    'sergas_hitl_approval_latency_seconds',
    'Time from approval request to user response',
    ['approval_type', 'agent_type'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800]  # Up to 30 minutes
)

hitl_approval_timeouts_total = Counter(
    'sergas_hitl_approval_timeouts_total',
    'Total HITL approval timeouts',
    ['approval_type', 'agent_type']
)

hitl_approvals_pending = Gauge(
    'sergas_hitl_approvals_pending',
    'Currently pending HITL approvals',
    ['approval_type']
)
```

#### CopilotKit/AG UI Protocol Metrics

```python
# CopilotKit integration metrics
copilotkit_actions_total = Counter(
    'sergas_copilotkit_actions_total',
    'Total CopilotKit actions invoked',
    ['action_name', 'status']
)

copilotkit_action_duration_seconds = Histogram(
    'sergas_copilotkit_action_duration_seconds',
    'CopilotKit action execution time',
    ['action_name'],
    buckets=[0.5, 1, 2, 5, 10, 30, 60]
)

# AG UI Protocol events
ag_ui_events_emitted_total = Counter(
    'sergas_ag_ui_events_emitted_total',
    'Total AG UI Protocol events emitted',
    ['event_type', 'agent_type']
)

ag_ui_events_received_total = Counter(
    'sergas_ag_ui_events_received_total',
    'Total AG UI Protocol events received by frontend',
    ['event_type']
)

# SSE streaming metrics
sse_connections_active = Gauge(
    'sergas_sse_connections_active',
    'Currently active SSE connections'
)

sse_messages_sent_total = Counter(
    'sergas_sse_messages_sent_total',
    'Total SSE messages sent',
    ['message_type']
)

sse_connection_duration_seconds = Histogram(
    'sergas_sse_connection_duration_seconds',
    'SSE connection duration',
    buckets=[10, 30, 60, 120, 300, 600, 1800]
)
```

### Orchestration Metrics

```python
# src/monitoring/orchestration_metrics.py

# Orchestration workflow metrics
orchestration_requests_total = Counter(
    'sergas_orchestration_requests_total',
    'Total orchestration requests',
    ['operation', 'status']
)

orchestration_duration_seconds = Histogram(
    'sergas_orchestration_duration_seconds',
    'End-to-end orchestration time',
    ['operation'],
    buckets=[5, 10, 30, 60, 120, 300, 600]
)

orchestration_steps_total = Summary(
    'sergas_orchestration_steps_total',
    'Number of steps in orchestration',
    ['operation']
)

# Multi-agent coordination
orchestration_agents_spawned_total = Counter(
    'sergas_orchestration_agents_spawned_total',
    'Total agents spawned per orchestration',
    ['operation', 'agent_type']
)

orchestration_parallel_executions = Gauge(
    'sergas_orchestration_parallel_executions',
    'Number of parallel agent executions',
    ['operation']
)

# Recommendation metrics
recommendations_generated_total = Counter(
    'sergas_recommendations_generated_total',
    'Total recommendations generated',
    ['recommendation_type', 'priority', 'confidence_tier']
)

recommendations_approved_total = Counter(
    'sergas_recommendations_approved_total',
    'Total recommendations approved via HITL',
    ['recommendation_type', 'priority']
)

recommendations_rejected_total = Counter(
    'sergas_recommendations_rejected_total',
    'Total recommendations rejected via HITL',
    ['recommendation_type', 'rejection_reason']
)

recommendation_confidence_score = Histogram(
    'sergas_recommendation_confidence_score',
    'Confidence scores of generated recommendations',
    ['recommendation_type'],
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]
)
```

### Performance Metrics

```python
# Request/Response metrics (already exist, extending)
http_request_body_size_bytes = Histogram(
    'sergas_http_request_body_size_bytes',
    'HTTP request body size',
    ['method', 'endpoint'],
    buckets=[100, 1000, 10000, 100000, 1000000]
)

http_response_body_size_bytes = Histogram(
    'sergas_http_response_body_size_bytes',
    'HTTP response body size',
    ['method', 'endpoint'],
    buckets=[100, 1000, 10000, 100000, 1000000]
)

# Queue metrics
agent_queue_depth = Gauge(
    'sergas_agent_queue_depth',
    'Number of tasks waiting in agent queue',
    ['agent_type', 'priority']
)

agent_queue_wait_time_seconds = Histogram(
    'sergas_agent_queue_wait_time_seconds',
    'Time tasks wait in queue before execution',
    ['agent_type'],
    buckets=[0.1, 0.5, 1, 5, 10, 30, 60]
)

# Memory metrics (per agent)
agent_memory_usage_bytes = Gauge(
    'sergas_agent_memory_usage_bytes',
    'Memory usage per agent instance',
    ['agent_type', 'agent_instance_id']
)

# Integration health
integration_health_status = Gauge(
    'sergas_integration_health_status',
    'Health status of external integrations (1=healthy, 0=unhealthy)',
    ['integration_name']
)
```

### Metrics Collection Implementation

```python
# src/monitoring/metrics_collector.py
import structlog
import time
from typing import Dict, Any, Optional
from contextlib import contextmanager

from src.monitoring.agent_metrics import *
from src.monitoring.orchestration_metrics import *

logger = structlog.get_logger(__name__)


class MetricsCollector:
    """Centralized metrics collection for agents and orchestration."""

    @staticmethod
    def record_agent_session(
        agent_type: str,
        operation: str,
        status: str,
        duration_seconds: float
    ):
        """Record agent session metrics."""
        agent_sessions_total.labels(
            agent_type=agent_type,
            status=status,
            operation=operation
        ).inc()

        agent_session_duration_seconds.labels(
            agent_type=agent_type,
            operation=operation
        ).observe(duration_seconds)

    @staticmethod
    def record_agent_handoff(
        from_agent: str,
        to_agent: str,
        status: str,
        duration_seconds: float
    ):
        """Record agent handoff metrics."""
        agent_handoffs_total.labels(
            from_agent=from_agent,
            to_agent=to_agent,
            status=status
        ).inc()

        agent_handoff_duration_seconds.labels(
            from_agent=from_agent,
            to_agent=to_agent
        ).observe(duration_seconds)

    @staticmethod
    def record_tool_call(
        agent_type: str,
        tool_name: str,
        status: str,
        duration_seconds: float
    ):
        """Record tool call metrics."""
        agent_tool_calls_total.labels(
            agent_type=agent_type,
            tool_name=tool_name,
            status=status
        ).inc()

        agent_tool_call_duration_seconds.labels(
            agent_type=agent_type,
            tool_name=tool_name
        ).observe(duration_seconds)

    @staticmethod
    def record_hitl_approval_request(
        approval_type: str,
        agent_type: str
    ):
        """Record HITL approval request."""
        hitl_approvals_requested_total.labels(
            approval_type=approval_type,
            agent_type=agent_type
        ).inc()

        hitl_approvals_pending.labels(
            approval_type=approval_type
        ).inc()

    @staticmethod
    def record_hitl_approval_response(
        approval_type: str,
        agent_type: str,
        decision: str,
        latency_seconds: float
    ):
        """Record HITL approval response."""
        hitl_approvals_received_total.labels(
            approval_type=approval_type,
            decision=decision,
            agent_type=agent_type
        ).inc()

        hitl_approval_latency_seconds.labels(
            approval_type=approval_type,
            agent_type=agent_type
        ).observe(latency_seconds)

        hitl_approvals_pending.labels(
            approval_type=approval_type
        ).dec()

    @staticmethod
    def record_hitl_timeout(
        approval_type: str,
        agent_type: str
    ):
        """Record HITL approval timeout."""
        hitl_approval_timeouts_total.labels(
            approval_type=approval_type,
            agent_type=agent_type
        ).inc()

        hitl_approvals_pending.labels(
            approval_type=approval_type
        ).dec()

    @staticmethod
    def record_copilotkit_action(
        action_name: str,
        status: str,
        duration_seconds: float
    ):
        """Record CopilotKit action metrics."""
        copilotkit_actions_total.labels(
            action_name=action_name,
            status=status
        ).inc()

        copilotkit_action_duration_seconds.labels(
            action_name=action_name
        ).observe(duration_seconds)

    @staticmethod
    def record_ag_ui_event_emitted(
        event_type: str,
        agent_type: str
    ):
        """Record AG UI Protocol event emission."""
        ag_ui_events_emitted_total.labels(
            event_type=event_type,
            agent_type=agent_type
        ).inc()

    @staticmethod
    def record_orchestration(
        operation: str,
        status: str,
        duration_seconds: float,
        steps_count: int
    ):
        """Record orchestration metrics."""
        orchestration_requests_total.labels(
            operation=operation,
            status=status
        ).inc()

        orchestration_duration_seconds.labels(
            operation=operation
        ).observe(duration_seconds)

        orchestration_steps_total.labels(
            operation=operation
        ).observe(steps_count)

    @staticmethod
    def record_recommendation(
        recommendation_type: str,
        priority: str,
        confidence_score: float,
        approved: Optional[bool] = None,
        rejection_reason: Optional[str] = None
    ):
        """Record recommendation metrics."""
        confidence_tier = "low" if confidence_score < 0.7 else (
            "medium" if confidence_score < 0.85 else "high"
        )

        recommendations_generated_total.labels(
            recommendation_type=recommendation_type,
            priority=priority,
            confidence_tier=confidence_tier
        ).inc()

        recommendation_confidence_score.labels(
            recommendation_type=recommendation_type
        ).observe(confidence_score)

        if approved is True:
            recommendations_approved_total.labels(
                recommendation_type=recommendation_type,
                priority=priority
            ).inc()
        elif approved is False:
            recommendations_rejected_total.labels(
                recommendation_type=recommendation_type,
                rejection_reason=rejection_reason or "unknown"
            ).inc()

    @staticmethod
    @contextmanager
    def track_agent_execution(agent_type: str, operation: str):
        """Context manager to track agent execution."""
        agent_sessions_active.labels(agent_type=agent_type).inc()
        start_time = time.time()
        status = "success"

        try:
            yield
        except Exception:
            status = "failure"
            raise
        finally:
            duration = time.time() - start_time
            agent_sessions_active.labels(agent_type=agent_type).dec()
            MetricsCollector.record_agent_session(
                agent_type, operation, status, duration
            )

    @staticmethod
    @contextmanager
    def track_sse_connection():
        """Context manager to track SSE connection."""
        sse_connections_active.inc()
        start_time = time.time()

        try:
            yield
        finally:
            duration = time.time() - start_time
            sse_connections_active.dec()
            sse_connection_duration_seconds.observe(duration)


# Global metrics collector instance
metrics_collector = MetricsCollector()
```

---

## Error Tracking

### Error Categorization

```python
# src/monitoring/error_tracking.py
from enum import Enum
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class ErrorCategory(Enum):
    """Error categories for tracking and alerting."""

    # Client errors (4xx)
    CLIENT_BAD_REQUEST = "client_bad_request"
    CLIENT_UNAUTHORIZED = "client_unauthorized"
    CLIENT_FORBIDDEN = "client_forbidden"
    CLIENT_NOT_FOUND = "client_not_found"
    CLIENT_RATE_LIMIT = "client_rate_limit"

    # Server errors (5xx)
    SERVER_INTERNAL = "server_internal"
    SERVER_UNAVAILABLE = "server_unavailable"
    SERVER_TIMEOUT = "server_timeout"
    SERVER_BAD_GATEWAY = "server_bad_gateway"

    # Agent errors
    AGENT_EXECUTION_FAILED = "agent_execution_failed"
    AGENT_TOOL_CALL_FAILED = "agent_tool_call_failed"
    AGENT_HANDOFF_FAILED = "agent_handoff_failed"
    AGENT_STATE_INVALID = "agent_state_invalid"
    AGENT_TIMEOUT = "agent_timeout"

    # Integration errors
    ZOHO_API_ERROR = "zoho_api_error"
    ZOHO_RATE_LIMIT = "zoho_rate_limit"
    ZOHO_AUTHENTICATION_ERROR = "zoho_authentication_error"
    COGNEE_ERROR = "cognee_error"
    DATABASE_ERROR = "database_error"
    REDIS_ERROR = "redis_error"

    # HITL workflow errors
    HITL_TIMEOUT = "hitl_timeout"
    HITL_INVALID_RESPONSE = "hitl_invalid_response"
    HITL_COMMUNICATION_ERROR = "hitl_communication_error"

    # CopilotKit/AG UI errors
    COPILOTKIT_ACTION_ERROR = "copilotkit_action_error"
    AG_UI_PROTOCOL_ERROR = "ag_ui_protocol_error"
    SSE_STREAM_ERROR = "sse_stream_error"

    # Unknown/uncategorized
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorTracker:
    """Error tracking with categorization and metrics."""

    def __init__(self):
        self.logger = logger.bind(component="error_tracker")

    def track_error(
        self,
        error: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity,
        context: Dict[str, Any],
        recoverable: bool = True
    ):
        """Track an error with category and severity."""

        # Log the error
        self.logger.error(
            "error_tracked",
            error_type=type(error).__name__,
            error_message=str(error),
            error_category=category.value,
            severity=severity.value,
            recoverable=recoverable,
            context=context,
            exc_info=True
        )

        # Record metrics
        from src.monitoring.agent_metrics import agent_errors_total

        agent_errors_total.labels(
            agent_type=context.get("agent_type", "unknown"),
            error_type=category.value,
            operation=context.get("operation", "unknown")
        ).inc()

        # Send to Sentry (optional)
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self._send_to_sentry(error, category, severity, context)

    def _send_to_sentry(
        self,
        error: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity,
        context: Dict[str, Any]
    ):
        """Send error to Sentry for tracking."""
        try:
            import sentry_sdk

            with sentry_sdk.push_scope() as scope:
                scope.set_tag("error_category", category.value)
                scope.set_tag("severity", severity.value)
                scope.set_context("error_context", context)

                sentry_sdk.capture_exception(error)
        except ImportError:
            # Sentry not installed, skip
            pass
        except Exception as e:
            self.logger.warning(
                "failed_to_send_to_sentry",
                error=str(e)
            )

    def categorize_http_error(self, status_code: int) -> ErrorCategory:
        """Categorize HTTP error by status code."""
        if status_code == 400:
            return ErrorCategory.CLIENT_BAD_REQUEST
        elif status_code == 401:
            return ErrorCategory.CLIENT_UNAUTHORIZED
        elif status_code == 403:
            return ErrorCategory.CLIENT_FORBIDDEN
        elif status_code == 404:
            return ErrorCategory.CLIENT_NOT_FOUND
        elif status_code == 429:
            return ErrorCategory.CLIENT_RATE_LIMIT
        elif status_code == 500:
            return ErrorCategory.SERVER_INTERNAL
        elif status_code == 502:
            return ErrorCategory.SERVER_BAD_GATEWAY
        elif status_code == 503:
            return ErrorCategory.SERVER_UNAVAILABLE
        elif status_code == 504:
            return ErrorCategory.SERVER_TIMEOUT
        else:
            return ErrorCategory.UNKNOWN


# Global error tracker instance
error_tracker = ErrorTracker()
```

### Error Recovery Tracking

```python
# src/monitoring/error_recovery.py
from typing import Optional, Dict, Any, Callable
import structlog
import time
from functools import wraps

from src.monitoring.error_tracking import ErrorCategory, ErrorSeverity, error_tracker

logger = structlog.get_logger(__name__)


def with_error_tracking(
    category: ErrorCategory,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    recoverable: bool = True,
    retry_count: int = 0
):
    """Decorator to track errors with automatic categorization."""

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = {
                "function": func.__name__,
                "module": func.__module__,
                "retry_count": retry_count
            }

            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_tracker.track_error(
                    error=e,
                    category=category,
                    severity=severity,
                    context=context,
                    recoverable=recoverable
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            context = {
                "function": func.__name__,
                "module": func.__module__,
                "retry_count": retry_count
            }

            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_tracker.track_error(
                    error=e,
                    category=category,
                    severity=severity,
                    context=context,
                    recoverable=recoverable
                )
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class ErrorRecoveryTracker:
    """Track error recovery attempts and success rates."""

    def __init__(self):
        self.logger = logger.bind(component="error_recovery")

    def track_recovery_attempt(
        self,
        error_category: ErrorCategory,
        recovery_strategy: str,
        success: bool,
        duration_seconds: float
    ):
        """Track error recovery attempt."""

        self.logger.info(
            "error_recovery_attempted",
            error_category=error_category.value,
            recovery_strategy=recovery_strategy,
            success=success,
            duration_seconds=duration_seconds
        )

        # Record metrics
        from prometheus_client import Counter, Histogram

        error_recovery_attempts = Counter(
            'sergas_error_recovery_attempts_total',
            'Total error recovery attempts',
            ['error_category', 'recovery_strategy', 'success']
        )

        error_recovery_duration = Histogram(
            'sergas_error_recovery_duration_seconds',
            'Error recovery duration',
            ['error_category', 'recovery_strategy']
        )

        error_recovery_attempts.labels(
            error_category=error_category.value,
            recovery_strategy=recovery_strategy,
            success="true" if success else "false"
        ).inc()

        error_recovery_duration.labels(
            error_category=error_category.value,
            recovery_strategy=recovery_strategy
        ).observe(duration_seconds)


# Global recovery tracker
recovery_tracker = ErrorRecoveryTracker()


import asyncio
```

---

## Distributed Tracing

### OpenTelemetry Configuration

```python
# src/tracing/config.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
import structlog

logger = structlog.get_logger(__name__)


def configure_tracing(
    service_name: str = "sergas-super-account-manager",
    jaeger_host: str = "jaeger",
    jaeger_port: int = 6831,
    environment: str = "production"
):
    """Configure OpenTelemetry distributed tracing."""

    # Create resource with service information
    resource = Resource(attributes={
        SERVICE_NAME: service_name,
        "environment": environment,
        "version": "1.0.0"
    })

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=jaeger_host,
        agent_port=jaeger_port,
    )

    # Add span processor
    provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

    # Set as global tracer provider
    trace.set_tracer_provider(provider)

    logger.info(
        "tracing_configured",
        service_name=service_name,
        jaeger_host=jaeger_host,
        jaeger_port=jaeger_port
    )


def instrument_fastapi(app):
    """Instrument FastAPI application with tracing."""
    FastAPIInstrumentor.instrument_app(app)
    logger.info("fastapi_instrumented")


def instrument_clients():
    """Instrument HTTP clients and database drivers."""

    # Instrument HTTPX (for external API calls)
    HTTPXClientInstrumentor().instrument()

    # Instrument AsyncPG (for PostgreSQL)
    AsyncPGInstrumentor().instrument()

    # Instrument Redis
    RedisInstrumentor().instrument()

    logger.info("clients_instrumented")
```

### Agent Tracing

```python
# src/tracing/agent_tracer.py
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class AgentTracer:
    """Helper for agent execution tracing."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.logger = logger.bind(agent_id=agent_id)

    def trace_agent_execution(
        self,
        operation: str,
        context: Dict[str, Any]
    ):
        """Create a span for agent execution."""

        span = tracer.start_span(
            f"agent.{self.agent_id}.{operation}",
            attributes={
                "agent.id": self.agent_id,
                "agent.operation": operation,
                "account.id": context.get("account_id"),
                **{f"context.{k}": str(v) for k, v in context.items()}
            }
        )

        return span

    def trace_tool_call(
        self,
        tool_name: str,
        tool_params: Dict[str, Any]
    ):
        """Create a span for tool call."""

        span = tracer.start_span(
            f"agent.{self.agent_id}.tool.{tool_name}",
            attributes={
                "tool.name": tool_name,
                "tool.params": str(tool_params),
                "agent.id": self.agent_id
            }
        )

        return span

    def trace_handoff(
        self,
        next_agent: str,
        handoff_data: Dict[str, Any]
    ):
        """Create a span for agent handoff."""

        span = tracer.start_span(
            f"agent.handoff.{self.agent_id}.to.{next_agent}",
            attributes={
                "from_agent": self.agent_id,
                "to_agent": next_agent,
                "handoff_keys": ",".join(handoff_data.keys())
            }
        )

        return span

    def trace_hitl_approval(
        self,
        approval_type: str,
        approval_data: Dict[str, Any]
    ):
        """Create a span for HITL approval workflow."""

        span = tracer.start_span(
            f"agent.{self.agent_id}.hitl.{approval_type}",
            attributes={
                "approval.type": approval_type,
                "approval.data": str(approval_data),
                "agent.id": self.agent_id
            }
        )

        return span

    @staticmethod
    def set_span_error(span, error: Exception):
        """Mark span as error."""
        span.set_status(Status(StatusCode.ERROR))
        span.record_exception(error)

    @staticmethod
    def set_span_success(span):
        """Mark span as success."""
        span.set_status(Status(StatusCode.OK))


# Usage example in agent code
"""
tracer = AgentTracer("zoho_data_scout")

with tracer.trace_agent_execution("analyze_account", context) as span:
    try:
        # Execute agent logic
        result = await self._execute(context)

        # Trace tool call
        with tracer.trace_tool_call("fetch_zoho_accounts", params) as tool_span:
            accounts = await zoho_client.fetch_accounts(params)
            tracer.set_span_success(tool_span)

        # Trace handoff
        with tracer.trace_handoff("memory_analyst", handoff_data) as handoff_span:
            await self._handoff_to_next_agent(handoff_data)
            tracer.set_span_success(handoff_span)

        tracer.set_span_success(span)
        return result

    except Exception as e:
        tracer.set_span_error(span, e)
        raise
"""
```

### Cross-Service Trace Propagation

```python
# src/tracing/propagation.py
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from typing import Dict
import structlog

logger = structlog.get_logger(__name__)
propagator = TraceContextTextMapPropagator()


def inject_trace_context(headers: Dict[str, str]) -> Dict[str, str]:
    """Inject trace context into HTTP headers."""

    # Get current span context
    carrier = {}
    propagator.inject(carrier)

    # Merge with existing headers
    headers.update(carrier)

    return headers


def extract_trace_context(headers: Dict[str, str]):
    """Extract trace context from HTTP headers."""

    # Extract context from headers
    context = propagator.extract(carrier=headers)

    # Set as current context
    if context:
        trace.set_span_in_context(trace.get_current_span(context))

    return context


# FastAPI middleware for trace propagation
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class TracePropagationMiddleware(BaseHTTPMiddleware):
    """Middleware to propagate trace context across services."""

    async def dispatch(self, request: Request, call_next):
        # Extract trace context from incoming request
        headers = dict(request.headers)
        context = extract_trace_context(headers)

        # Store in request state
        request.state.trace_context = context

        # Process request
        response = await call_next(request)

        # Inject trace context into response headers
        inject_trace_context(dict(response.headers))

        return response
```

---

## Dashboards

### Dashboard Specifications

#### 1. Multi-Agent Orchestration Dashboard

**Purpose**: Monitor agent coordination and handoffs

**Panels**:

1. **Active Orchestrations** (Gauge)
   ```promql
   sergas_orchestration_parallel_executions
   ```

2. **Orchestration Success Rate** (Graph)
   ```promql
   sum(rate(sergas_orchestration_requests_total{status="success"}[5m])) /
   sum(rate(sergas_orchestration_requests_total[5m])) * 100
   ```

3. **Agent Handoff Flow** (Sankey Diagram)
   ```promql
   sum(rate(sergas_agent_handoffs_total[5m])) by (from_agent, to_agent)
   ```

4. **Agent Execution Time** (Heatmap)
   ```promql
   histogram_quantile(0.95,
     sum(rate(sergas_agent_session_duration_seconds_bucket[5m])) by (agent_type, le)
   )
   ```

5. **Active Agent Sessions** (Stacked Graph)
   ```promql
   sergas_agent_sessions_active by (agent_type)
   ```

6. **Tool Call Distribution** (Pie Chart)
   ```promql
   sum(rate(sergas_agent_tool_calls_total[5m])) by (tool_name)
   ```

7. **Agent Error Rate** (Graph)
   ```promql
   sum(rate(sergas_agent_errors_total[5m])) by (agent_type, error_type)
   ```

8. **Orchestration Duration P95** (Stat + Sparkline)
   ```promql
   histogram_quantile(0.95,
     rate(sergas_orchestration_duration_seconds_bucket[5m])
   )
   ```

#### 2. HITL Workflow Dashboard

**Purpose**: Monitor human-in-the-loop approval flows

**Panels**:

1. **Pending Approvals** (Gauge)
   ```promql
   sergas_hitl_approvals_pending
   ```

2. **Approval Request Rate** (Graph)
   ```promql
   rate(sergas_hitl_approvals_requested_total[5m]) by (approval_type)
   ```

3. **Approval Latency** (Heatmap)
   ```promql
   histogram_quantile(0.95,
     rate(sergas_hitl_approval_latency_seconds_bucket[5m])
   ) by (approval_type)
   ```

4. **Approval Decision Breakdown** (Pie Chart)
   ```promql
   sum(sergas_hitl_approvals_received_total) by (decision)
   ```

5. **Timeout Rate** (Graph)
   ```promql
   rate(sergas_hitl_approval_timeouts_total[5m]) by (approval_type)
   ```

6. **Approval Latency Distribution** (Histogram)
   ```promql
   sum(rate(sergas_hitl_approval_latency_seconds_bucket[5m])) by (le)
   ```

7. **Approval Success Rate** (Graph)
   ```promql
   sum(rate(sergas_hitl_approvals_received_total{decision="approved"}[5m])) /
   sum(rate(sergas_hitl_approvals_received_total[5m])) * 100
   ```

#### 3. CopilotKit/AG UI Protocol Dashboard

**Purpose**: Monitor frontend integration and streaming

**Panels**:

1. **Active SSE Connections** (Gauge)
   ```promql
   sergas_sse_connections_active
   ```

2. **CopilotKit Action Rate** (Graph)
   ```promql
   rate(sergas_copilotkit_actions_total[5m]) by (action_name, status)
   ```

3. **CopilotKit Action Duration** (Graph)
   ```promql
   histogram_quantile(0.95,
     rate(sergas_copilotkit_action_duration_seconds_bucket[5m])
   ) by (action_name)
   ```

4. **AG UI Events Emitted** (Graph)
   ```promql
   rate(sergas_ag_ui_events_emitted_total[5m]) by (event_type)
   ```

5. **SSE Message Rate** (Graph)
   ```promql
   rate(sergas_sse_messages_sent_total[5m]) by (message_type)
   ```

6. **SSE Connection Duration** (Histogram)
   ```promql
   rate(sergas_sse_connection_duration_seconds_bucket[5m])
   ```

7. **Frontend-to-Backend Latency** (Graph)
   ```promql
   histogram_quantile(0.95,
     rate(sergas_http_request_duration_seconds_bucket{endpoint="/api/copilotkit"}[5m])
   )
   ```

#### 4. Error Tracking Dashboard

**Purpose**: Monitor errors across the entire stack

**Panels**:

1. **Total Error Rate** (Stat + Sparkline)
   ```promql
   sum(rate(sergas_errors_total[5m]))
   ```

2. **Errors by Category** (Bar Gauge)
   ```promql
   sum(rate(sergas_agent_errors_total[5m])) by (error_type)
   ```

3. **Errors by Severity** (Pie Chart)
   ```promql
   sum(sergas_errors_total) by (severity)
   ```

4. **Error Timeline** (Graph)
   ```promql
   rate(sergas_errors_total[5m]) by (error_type)
   ```

5. **Top Error Sources** (Table)
   ```promql
   topk(10,
     sum(rate(sergas_agent_errors_total[5m])) by (agent_type, error_type)
   )
   ```

6. **Error Recovery Success Rate** (Graph)
   ```promql
   sum(rate(sergas_error_recovery_attempts_total{success="true"}[5m])) /
   sum(rate(sergas_error_recovery_attempts_total[5m])) * 100
   ```

7. **Unhandled Exceptions** (Table)
   ```promql
   increase(sergas_exceptions_unhandled_total[1h]) by (exception_type, module)
   ```

#### 5. Performance Overview Dashboard

**Purpose**: End-to-end performance monitoring

**Panels**:

1. **Request Rate** (Graph)
   ```promql
   rate(sergas_http_requests_total[5m]) by (endpoint)
   ```

2. **Response Time P50/P95/P99** (Graph)
   ```promql
   histogram_quantile(0.50, rate(sergas_http_request_duration_seconds_bucket[5m]))
   histogram_quantile(0.95, rate(sergas_http_request_duration_seconds_bucket[5m]))
   histogram_quantile(0.99, rate(sergas_http_request_duration_seconds_bucket[5m]))
   ```

3. **Agent Queue Depth** (Graph)
   ```promql
   sergas_agent_queue_depth by (agent_type)
   ```

4. **Database Query Performance** (Graph)
   ```promql
   histogram_quantile(0.95,
     rate(sergas_db_query_duration_seconds_bucket[5m])
   ) by (operation)
   ```

5. **Cache Hit Rate** (Graph)
   ```promql
   sum(rate(sergas_cache_hits_total[5m])) /
   (sum(rate(sergas_cache_hits_total[5m])) + sum(rate(sergas_cache_misses_total[5m]))) * 100
   ```

6. **Memory Usage per Agent** (Graph)
   ```promql
   sergas_agent_memory_usage_bytes by (agent_type)
   ```

7. **Integration Health** (Stat Panel)
   ```promql
   sergas_integration_health_status by (integration_name)
   ```

### Dashboard Export

```json
// grafana/dashboards/multi_agent_orchestration.json
{
  "dashboard": {
    "title": "Multi-Agent Orchestration",
    "tags": ["agents", "orchestration"],
    "timezone": "browser",
    "schemaVersion": 39,
    "refresh": "10s",
    "panels": [
      {
        "id": 1,
        "title": "Active Orchestrations",
        "type": "gauge",
        "targets": [{
          "expr": "sergas_orchestration_parallel_executions",
          "refId": "A"
        }],
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
      },
      // ... more panels
    ]
  }
}
```

---

## Alerting Rules

### Critical Alerts

```yaml
# config/alerts/agent_alerts.yml
groups:
  - name: agent_critical
    interval: 30s
    rules:
      # Agent execution failure spike
      - alert: AgentExecutionFailureSpike
        expr: |
          rate(sergas_agent_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
          team: agents
        annotations:
          summary: "High agent execution failure rate"
          description: "Agent {{ $labels.agent_type }} has {{ $value | humanizePercentage }} failure rate"
          runbook_url: "https://docs.sergas.com/runbooks/agent-failures"
          dashboard_url: "https://grafana.sergas.com/d/agents/multi-agent-orchestration"

      # HITL approval timeout spike
      - alert: HITLApprovalTimeoutSpike
        expr: |
          rate(sergas_hitl_approval_timeouts_total[10m]) > 0.05
        for: 10m
        labels:
          severity: critical
          team: frontend
        annotations:
          summary: "High HITL approval timeout rate"
          description: "{{ $labels.approval_type }} has {{ $value | humanizePercentage }} timeout rate"
          runbook_url: "https://docs.sergas.com/runbooks/hitl-timeouts"

      # Agent handoff failure
      - alert: AgentHandoffFailure
        expr: |
          rate(sergas_agent_handoffs_total{status="failure"}[5m]) > 0
        for: 2m
        labels:
          severity: critical
          team: agents
        annotations:
          summary: "Agent handoff failures detected"
          description: "Handoff from {{ $labels.from_agent }} to {{ $labels.to_agent }} is failing"
          runbook_url: "https://docs.sergas.com/runbooks/agent-handoff-failures"

      # CopilotKit action failure spike
      - alert: CopilotKitActionFailureSpike
        expr: |
          rate(sergas_copilotkit_actions_total{status="failure"}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
          team: frontend
        annotations:
          summary: "High CopilotKit action failure rate"
          description: "Action {{ $labels.action_name }} has {{ $value | humanizePercentage }} failure rate"
          runbook_url: "https://docs.sergas.com/runbooks/copilotkit-failures"

      # Agent queue depth critical
      - alert: AgentQueueDepthCritical
        expr: |
          sergas_agent_queue_depth > 1000
        for: 10m
        labels:
          severity: critical
          team: agents
        annotations:
          summary: "Agent queue depth critical"
          description: "{{ $labels.agent_type }} queue has {{ $value }} pending tasks"
          runbook_url: "https://docs.sergas.com/runbooks/queue-depth"

      # SSE connection drop spike
      - alert: SSEConnectionDropSpike
        expr: |
          rate(sergas_sse_connections_active[5m]) < -10
        for: 5m
        labels:
          severity: critical
          team: frontend
        annotations:
          summary: "SSE connections dropping rapidly"
          description: "SSE connections dropping at {{ $value }} per second"
          runbook_url: "https://docs.sergas.com/runbooks/sse-connection-drops"

  - name: agent_warning
    interval: 1m
    rules:
      # High agent execution latency
      - alert: HighAgentExecutionLatency
        expr: |
          histogram_quantile(0.95,
            rate(sergas_agent_session_duration_seconds_bucket[5m])
          ) > 60
        for: 10m
        labels:
          severity: warning
          team: agents
        annotations:
          summary: "High agent execution latency"
          description: "{{ $labels.agent_type }} P95 latency is {{ $value }}s (threshold: 60s)"
          runbook_url: "https://docs.sergas.com/runbooks/agent-latency"

      # High HITL approval latency
      - alert: HighHITLApprovalLatency
        expr: |
          histogram_quantile(0.95,
            rate(sergas_hitl_approval_latency_seconds_bucket[10m])
          ) > 300
        for: 15m
        labels:
          severity: warning
          team: product
        annotations:
          summary: "High HITL approval latency"
          description: "{{ $labels.approval_type }} P95 latency is {{ $value }}s (threshold: 300s)"
          runbook_url: "https://docs.sergas.com/runbooks/hitl-latency"

      # Low recommendation confidence
      - alert: LowRecommendationConfidence
        expr: |
          histogram_quantile(0.50,
            rate(sergas_recommendation_confidence_score_bucket[1h])
          ) < 0.7
        for: 1h
        labels:
          severity: warning
          team: ml
        annotations:
          summary: "Low recommendation confidence scores"
          description: "{{ $labels.recommendation_type }} median confidence is {{ $value }} (threshold: 0.7)"
          runbook_url: "https://docs.sergas.com/runbooks/low-confidence"

      # High agent memory usage
      - alert: HighAgentMemoryUsage
        expr: |
          sergas_agent_memory_usage_bytes / 1024 / 1024 / 1024 > 2
        for: 10m
        labels:
          severity: warning
          team: devops
        annotations:
          summary: "High agent memory usage"
          description: "{{ $labels.agent_type }} using {{ $value }}GB memory (threshold: 2GB)"
          runbook_url: "https://docs.sergas.com/runbooks/high-memory"

      # Pending HITL approvals accumulating
      - alert: PendingHITLApprovalsAccumulating
        expr: |
          sergas_hitl_approvals_pending > 100
        for: 30m
        labels:
          severity: warning
          team: product
        annotations:
          summary: "HITL approvals accumulating"
          description: "{{ $labels.approval_type }} has {{ $value }} pending approvals"
          runbook_url: "https://docs.sergas.com/runbooks/pending-approvals"
```

### AlertManager Routes

```yaml
# config/alerts/alertmanager.yml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'

route:
  group_by: ['alertname', 'severity', 'team']
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
      group_wait: 0s

    # Warning alerts -> Slack only
    - match:
        severity: warning
      receiver: 'slack-warning'

    # Team-specific routing
    - match:
        team: agents
      receiver: 'slack-agents-team'

    - match:
        team: frontend
      receiver: 'slack-frontend-team'

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
        severity: 'critical'

  - name: 'slack-critical'
    slack_configs:
      - channel: '#sergas-critical'
        color: 'danger'
        title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
        text: |
          *Summary:* {{ .CommonAnnotations.summary }}
          *Description:* {{ .CommonAnnotations.description }}
          *Runbook:* {{ .CommonAnnotations.runbook_url }}
          *Dashboard:* {{ .CommonAnnotations.dashboard_url }}

  - name: 'slack-warning'
    slack_configs:
      - channel: '#sergas-warnings'
        color: 'warning'
        title: '⚠️ WARNING: {{ .GroupLabels.alertname }}'
        text: '{{ .CommonAnnotations.description }}'

  - name: 'slack-agents-team'
    slack_configs:
      - channel: '#sergas-agents-team'
        title: 'Agent System Alert'
        text: '{{ .CommonAnnotations.description }}'

  - name: 'slack-frontend-team'
    slack_configs:
      - channel: '#sergas-frontend-team'
        title: 'Frontend Alert'
        text: '{{ .CommonAnnotations.description }}'

inhibit_rules:
  # Inhibit warning if critical is firing
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'agent_type']

  # Inhibit handoff failures if agent execution is failing
  - source_match:
      alertname: 'AgentExecutionFailureSpike'
    target_match:
      alertname: 'AgentHandoffFailure'
    equal: ['agent_type']
```

---

## Debugging Toolkit

### Request Replay for Debugging

```python
# src/debugging/request_replay.py
import structlog
from typing import Dict, Any, Optional
import json
import asyncio
from datetime import datetime

from src.orchestrator import AgentOrchestrator

logger = structlog.get_logger(__name__)


class RequestReplayer:
    """Replay requests for debugging purposes."""

    def __init__(self, orchestrator: AgentOrchestrator):
        self.orchestrator = orchestrator
        self.logger = logger.bind(component="request_replayer")

    async def replay_from_trace_id(
        self,
        trace_id: str,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """Replay a request using its trace ID."""

        self.logger.info(
            "request_replay_started",
            trace_id=trace_id,
            dry_run=dry_run
        )

        # 1. Fetch request from logs
        request_data = await self._fetch_request_from_logs(trace_id)

        if not request_data:
            raise ValueError(f"No request found for trace_id: {trace_id}")

        # 2. Replay the request
        if dry_run:
            self.logger.info(
                "request_replay_dry_run",
                trace_id=trace_id,
                request_data=request_data
            )
            return {"status": "dry_run", "request_data": request_data}

        # 3. Execute orchestration
        result = await self.orchestrator.orchestrate(
            account_id=request_data.get("account_id"),
            context=request_data.get("context", {})
        )

        self.logger.info(
            "request_replay_completed",
            trace_id=trace_id,
            result_summary=result
        )

        return result

    async def _fetch_request_from_logs(
        self,
        trace_id: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch request data from Loki logs."""

        # Query Loki for request with trace_id
        # This is a placeholder - implement actual Loki query
        query = f'{{app="sergas"}} |= "{trace_id}" | json | event="orchestration_started"'

        # TODO: Implement actual Loki query client
        # For now, return placeholder
        return {
            "account_id": "ACC-12345",
            "context": {
                "operation": "account_analysis"
            }
        }

    async def replay_failed_requests(
        self,
        time_range: str = "1h",
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Replay all failed requests from a time range."""

        self.logger.info(
            "batch_replay_started",
            time_range=time_range,
            max_retries=max_retries
        )

        # 1. Fetch failed requests
        failed_requests = await self._fetch_failed_requests(time_range)

        results = {
            "total": len(failed_requests),
            "replayed": 0,
            "still_failing": 0,
            "details": []
        }

        # 2. Replay each request
        for request in failed_requests:
            try:
                result = await self.replay_from_trace_id(
                    trace_id=request["trace_id"],
                    dry_run=False
                )
                results["replayed"] += 1
                results["details"].append({
                    "trace_id": request["trace_id"],
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                results["still_failing"] += 1
                results["details"].append({
                    "trace_id": request["trace_id"],
                    "status": "failed",
                    "error": str(e)
                })

        self.logger.info(
            "batch_replay_completed",
            results=results
        )

        return results

    async def _fetch_failed_requests(
        self,
        time_range: str
    ) -> list[Dict[str, Any]]:
        """Fetch failed requests from logs."""

        # Query Loki for failed requests
        query = f'{{app="sergas"}} |= "orchestration_failed" | json'

        # TODO: Implement actual Loki query
        return []
```

### Agent State Inspection

```python
# src/debugging/agent_inspector.py
import structlog
from typing import Dict, Any, Optional
import json

logger = structlog.get_logger(__name__)


class AgentInspector:
    """Inspect agent state for debugging."""

    def __init__(self):
        self.logger = logger.bind(component="agent_inspector")

    async def inspect_agent_state(
        self,
        agent_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Inspect current state of an agent session."""

        self.logger.info(
            "agent_inspection_started",
            agent_id=agent_id,
            session_id=session_id
        )

        # Fetch agent state from memory/database
        state = await self._fetch_agent_state(agent_id, session_id)

        inspection = {
            "agent_id": agent_id,
            "session_id": session_id,
            "state": state,
            "metrics": await self._fetch_agent_metrics(agent_id),
            "recent_logs": await self._fetch_recent_logs(agent_id, session_id),
            "trace_data": await self._fetch_trace_data(session_id)
        }

        return inspection

    async def _fetch_agent_state(
        self,
        agent_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Fetch agent state from storage."""
        # TODO: Implement actual state fetch
        return {
            "status": "active",
            "current_step": 2,
            "total_steps": 3
        }

    async def _fetch_agent_metrics(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """Fetch agent metrics from Prometheus."""
        # TODO: Query Prometheus
        return {
            "execution_count": 42,
            "error_count": 3,
            "avg_duration_seconds": 12.5
        }

    async def _fetch_recent_logs(
        self,
        agent_id: str,
        session_id: str,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """Fetch recent logs for agent session."""
        # TODO: Query Loki
        return []

    async def _fetch_trace_data(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """Fetch distributed trace data."""
        # TODO: Query Jaeger
        return {
            "trace_id": "abc123",
            "spans": []
        }


class HandoffDebugger:
    """Debug agent handoff issues."""

    def __init__(self):
        self.logger = logger.bind(component="handoff_debugger")

    async def debug_handoff(
        self,
        from_agent: str,
        to_agent: str,
        trace_id: str
    ) -> Dict[str, Any]:
        """Debug a specific agent handoff."""

        self.logger.info(
            "handoff_debug_started",
            from_agent=from_agent,
            to_agent=to_agent,
            trace_id=trace_id
        )

        # Fetch handoff logs
        handoff_logs = await self._fetch_handoff_logs(
            from_agent, to_agent, trace_id
        )

        # Analyze handoff data
        analysis = {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "trace_id": trace_id,
            "handoff_logs": handoff_logs,
            "data_transferred": await self._analyze_handoff_data(handoff_logs),
            "latency": await self._calculate_handoff_latency(handoff_logs),
            "issues": await self._detect_handoff_issues(handoff_logs)
        }

        return analysis

    async def _fetch_handoff_logs(
        self,
        from_agent: str,
        to_agent: str,
        trace_id: str
    ) -> list[Dict[str, Any]]:
        """Fetch logs related to handoff."""
        # TODO: Query Loki
        return []

    async def _analyze_handoff_data(
        self,
        handoff_logs: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze data transferred during handoff."""
        return {
            "keys_transferred": [],
            "data_size_bytes": 0
        }

    async def _calculate_handoff_latency(
        self,
        handoff_logs: list[Dict[str, Any]]
    ) -> float:
        """Calculate handoff latency."""
        return 0.0

    async def _detect_handoff_issues(
        self,
        handoff_logs: list[Dict[str, Any]]
    ) -> list[str]:
        """Detect issues in handoff."""
        return []
```

### Log Aggregation and Search CLI

```python
# scripts/debug_cli.py
import click
import asyncio
import json
from datetime import datetime, timedelta

from src.debugging.request_replay import RequestReplayer
from src.debugging.agent_inspector import AgentInspector, HandoffDebugger


@click.group()
def cli():
    """Sergas Debugging CLI"""
    pass


@cli.command()
@click.option('--trace-id', required=True, help='Trace ID to replay')
@click.option('--dry-run/--execute', default=True, help='Dry run or execute')
def replay_request(trace_id: str, dry_run: bool):
    """Replay a request by trace ID."""
    replayer = RequestReplayer(orchestrator=None)  # TODO: inject orchestrator
    result = asyncio.run(replayer.replay_from_trace_id(trace_id, dry_run))
    click.echo(json.dumps(result, indent=2))


@cli.command()
@click.option('--agent-id', required=True, help='Agent ID')
@click.option('--session-id', required=True, help='Session ID')
def inspect_agent(agent_id: str, session_id: str):
    """Inspect agent state."""
    inspector = AgentInspector()
    result = asyncio.run(inspector.inspect_agent_state(agent_id, session_id))
    click.echo(json.dumps(result, indent=2))


@cli.command()
@click.option('--from-agent', required=True, help='Source agent')
@click.option('--to-agent', required=True, help='Target agent')
@click.option('--trace-id', required=True, help='Trace ID')
def debug_handoff(from_agent: str, to_agent: str, trace_id: str):
    """Debug agent handoff."""
    debugger = HandoffDebugger()
    result = asyncio.run(debugger.debug_handoff(from_agent, to_agent, trace_id))
    click.echo(json.dumps(result, indent=2))


@cli.command()
@click.option('--query', required=True, help='LogQL query')
@click.option('--limit', default=100, help='Max results')
def search_logs(query: str, limit: int):
    """Search logs with LogQL."""
    # TODO: Implement Loki query
    click.echo(f"Searching logs: {query}")


@cli.command()
@click.option('--time-range', default='1h', help='Time range (e.g., 1h, 24h)')
def replay_failed(time_range: str):
    """Replay all failed requests."""
    replayer = RequestReplayer(orchestrator=None)  # TODO: inject orchestrator
    result = asyncio.run(replayer.replay_failed_requests(time_range))
    click.echo(json.dumps(result, indent=2))


if __name__ == '__main__':
    cli()
```

**Usage**:

```bash
# Replay a specific request
python scripts/debug_cli.py replay-request --trace-id=abc123 --dry-run

# Inspect agent state
python scripts/debug_cli.py inspect-agent --agent-id=zoho_data_scout --session-id=sess_456

# Debug handoff
python scripts/debug_cli.py debug-handoff \
  --from-agent=zoho_data_scout \
  --to-agent=memory_analyst \
  --trace-id=abc123

# Search logs
python scripts/debug_cli.py search-logs --query='{app="sergas"} |= "ERROR"' --limit=50

# Replay all failed requests from last hour
python scripts/debug_cli.py replay-failed --time-range=1h
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1)

**Goal**: Establish basic monitoring infrastructure

**Tasks**:

1. **Deploy Prometheus & Grafana**
   - [ ] Deploy Prometheus server
   - [ ] Deploy Grafana
   - [ ] Configure Prometheus datasource in Grafana
   - [ ] Deploy AlertManager

2. **Implement Structured Logging**
   - [ ] Configure structlog in FastAPI
   - [ ] Implement LoggingMiddleware
   - [ ] Create log correlation utilities
   - [ ] Deploy Loki and Promtail

3. **Basic Metrics Collection**
   - [ ] Implement HTTP metrics (request rate, latency, errors)
   - [ ] Implement agent session metrics
   - [ ] Create `/metrics` endpoint
   - [ ] Configure Prometheus scraping

**Deliverables**:
- Prometheus + Grafana running
- Structured logs with correlation IDs
- Basic metrics being collected
- Simple dashboard showing request metrics

---

### Phase 2: Agent Monitoring (Week 2)

**Goal**: Implement comprehensive agent monitoring

**Tasks**:

1. **Agent Metrics Implementation**
   - [ ] Implement agent execution metrics
   - [ ] Implement tool call metrics
   - [ ] Implement agent handoff metrics
   - [ ] Implement agent state transition metrics

2. **Agent Logging**
   - [ ] Create AgentLogger helper class
   - [ ] Implement agent execution logging
   - [ ] Implement tool call logging
   - [ ] Implement handoff logging

3. **Agent Dashboards**
   - [ ] Create Multi-Agent Orchestration dashboard
   - [ ] Create Agent Performance dashboard
   - [ ] Create Error Tracking dashboard

**Deliverables**:
- Agent metrics collected and visualized
- Agent logs with context
- 3 operational dashboards

---

### Phase 3: HITL Monitoring (Week 3)

**Goal**: Monitor HITL approval workflows

**Tasks**:

1. **HITL Metrics**
   - [ ] Implement approval request metrics
   - [ ] Implement approval latency metrics
   - [ ] Implement timeout metrics
   - [ ] Implement pending approvals gauge

2. **HITL Logging**
   - [ ] Log approval requests
   - [ ] Log approval responses
   - [ ] Log approval timeouts

3. **HITL Dashboard**
   - [ ] Create HITL Workflow dashboard
   - [ ] Add approval latency visualizations
   - [ ] Add decision breakdown charts

**Deliverables**:
- HITL metrics collected
- HITL workflow visibility
- HITL dashboard operational

---

### Phase 4: Distributed Tracing (Week 4)

**Goal**: Implement end-to-end request tracing

**Tasks**:

1. **OpenTelemetry Setup**
   - [ ] Configure OpenTelemetry SDK
   - [ ] Deploy Jaeger backend
   - [ ] Instrument FastAPI
   - [ ] Instrument HTTP clients

2. **Agent Tracing**
   - [ ] Create AgentTracer helper
   - [ ] Implement agent execution spans
   - [ ] Implement tool call spans
   - [ ] Implement handoff spans

3. **Trace Propagation**
   - [ ] Implement trace context injection
   - [ ] Implement trace context extraction
   - [ ] Add TracePropagationMiddleware

**Deliverables**:
- End-to-end request tracing
- Jaeger UI operational
- Trace correlation with logs and metrics

---

### Phase 5: CopilotKit Integration Monitoring (Week 5)

**Goal**: Monitor frontend integration

**Tasks**:

1. **CopilotKit Metrics**
   - [ ] Implement CopilotKit action metrics
   - [ ] Implement AG UI Protocol event metrics
   - [ ] Implement SSE connection metrics

2. **Frontend Logging**
   - [ ] Implement frontend error logging
   - [ ] Implement user interaction logging
   - [ ] Implement SSE event logging

3. **CopilotKit Dashboard**
   - [ ] Create CopilotKit/AG UI Protocol dashboard
   - [ ] Add SSE connection visualizations
   - [ ] Add frontend-to-backend latency tracking

**Deliverables**:
- Frontend metrics collected
- SSE streaming visibility
- CopilotKit dashboard operational

---

### Phase 6: Alerting & Error Tracking (Week 6)

**Goal**: Implement comprehensive alerting

**Tasks**:

1. **Alert Rules**
   - [ ] Define critical alerts
   - [ ] Define warning alerts
   - [ ] Configure AlertManager routes
   - [ ] Set up Slack integration
   - [ ] Set up PagerDuty integration

2. **Error Tracking**
   - [ ] Implement ErrorTracker class
   - [ ] Implement error categorization
   - [ ] Implement error recovery tracking
   - [ ] Optional: Set up Sentry

3. **Testing**
   - [ ] Test alert firing
   - [ ] Test alert routing
   - [ ] Test escalation policies

**Deliverables**:
- Alert rules configured
- Alert routing operational
- Error tracking implemented

---

### Phase 7: Debugging Toolkit (Week 7)

**Goal**: Build debugging and troubleshooting tools

**Tasks**:

1. **Request Replay**
   - [ ] Implement RequestReplayer
   - [ ] Implement Loki query integration
   - [ ] Create replay CLI

2. **Agent Inspection**
   - [ ] Implement AgentInspector
   - [ ] Implement HandoffDebugger
   - [ ] Create inspection CLI

3. **Log Search**
   - [ ] Implement log search CLI
   - [ ] Create common query templates
   - [ ] Document debugging workflows

**Deliverables**:
- Request replay functional
- Agent inspection tools
- Debugging CLI operational

---

### Phase 8: Production Readiness (Week 8)

**Goal**: Prepare for production deployment

**Tasks**:

1. **Performance Tuning**
   - [ ] Optimize Prometheus retention
   - [ ] Optimize Loki retention
   - [ ] Tune scrape intervals
   - [ ] Configure alerting thresholds

2. **Documentation**
   - [ ] Create runbooks for common incidents
   - [ ] Document alert responses
   - [ ] Create troubleshooting guides
   - [ ] Document metric meanings

3. **Validation**
   - [ ] Load test monitoring stack
   - [ ] Validate alert accuracy
   - [ ] Verify dashboard accuracy
   - [ ] Test disaster recovery

**Deliverables**:
- Production-ready monitoring
- Complete documentation
- Validated alerting
- Disaster recovery plan

---

## Summary

This monitoring and observability plan provides comprehensive visibility into the CopilotKit-based multi-agent system with HITL workflows. Key features:

1. **End-to-End Tracing**: Track requests from frontend through Next.js to FastAPI and multi-agent execution
2. **Agent Visibility**: Monitor agent handoffs, state transitions, tool calls, and performance
3. **HITL Monitoring**: Track approval workflows, latency, timeouts, and user engagement
4. **Error Tracking**: Categorize and track errors across the entire stack
5. **Debugging Tools**: Request replay, agent inspection, and log search capabilities
6. **Proactive Alerting**: Critical and warning alerts with proper routing

**Next Steps**:
1. Review and approve this plan
2. Begin Phase 1 implementation
3. Deploy monitoring infrastructure
4. Instrument agents with metrics and logging
5. Create operational dashboards

**Estimated Timeline**: 8 weeks for full implementation

**Resources Required**:
- 1 DevOps Engineer (full-time)
- 1 Backend Engineer (part-time, for instrumentation)
- 1 Frontend Engineer (part-time, for frontend monitoring)

---

**Document Status**: Ready for Implementation
**Last Updated**: 2025-10-19
**Next Review**: After Phase 1 completion
