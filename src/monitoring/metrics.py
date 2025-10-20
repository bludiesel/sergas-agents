"""
Sergas Super Account Manager - Prometheus Metrics
Custom metrics for business, performance, and operational monitoring
Generated: 2025-10-19
"""

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    Info,
    Enum,
    generate_latest,
    REGISTRY,
    CollectorRegistry,
)
from prometheus_client.multiprocess import MultiProcessCollector
from typing import Optional, Dict, Any, List
import time
import functools
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


# ============================================
# HTTP Request Metrics
# ============================================
http_requests_total = Counter(
    'sergas_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'sergas_http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

http_requests_in_progress = Gauge(
    'sergas_http_requests_in_progress',
    'HTTP requests currently being processed',
    ['method', 'endpoint']
)


# ============================================
# Zoho Integration Metrics
# ============================================
zoho_api_calls_total = Counter(
    'sergas_zoho_api_calls_total',
    'Total Zoho API calls',
    ['operation', 'status']
)

zoho_api_duration_seconds = Histogram(
    'sergas_zoho_api_duration_seconds',
    'Zoho API call latency',
    ['operation'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

zoho_sync_failures_total = Counter(
    'sergas_zoho_sync_failures_total',
    'Total Zoho sync failures',
    ['sync_type', 'error_type']
)

zoho_accounts_synced_total = Counter(
    'sergas_zoho_accounts_synced_total',
    'Total accounts synced from Zoho',
    ['sync_type']
)

zoho_rate_limit_remaining = Gauge(
    'sergas_zoho_rate_limit_remaining',
    'Remaining Zoho API rate limit',
    ['api_type']
)

zoho_rate_limit_exceeded_total = Counter(
    'sergas_zoho_rate_limit_exceeded_total',
    'Times Zoho rate limit was exceeded',
    ['api_type']
)


# ============================================
# Memory & Knowledge Graph Metrics
# ============================================
memory_processing_duration_seconds = Histogram(
    'sergas_memory_processing_duration_seconds',
    'Memory processing latency',
    ['operation'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

memory_documents_processed_total = Counter(
    'sergas_memory_documents_processed_total',
    'Total documents processed',
    ['document_type', 'status']
)

memory_embeddings_generated_total = Counter(
    'sergas_memory_embeddings_generated_total',
    'Total embeddings generated',
    ['model']
)

memory_graph_nodes_total = Gauge(
    'sergas_memory_graph_nodes_total',
    'Total nodes in knowledge graph',
    ['node_type']
)

memory_graph_relationships_total = Gauge(
    'sergas_memory_graph_relationships_total',
    'Total relationships in knowledge graph',
    ['relationship_type']
)

memory_search_duration_seconds = Histogram(
    'sergas_memory_search_duration_seconds',
    'Memory search latency',
    ['search_type'],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
)


# ============================================
# Agent Performance Metrics
# ============================================
agent_task_duration_seconds = Histogram(
    'sergas_agent_task_duration_seconds',
    'Agent task execution time',
    ['agent_type', 'task_type'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

agent_task_attempts_total = Counter(
    'sergas_agent_task_attempts_total',
    'Total agent task attempts',
    ['agent_type', 'task_type']
)

agent_task_failures_total = Counter(
    'sergas_agent_task_failures_total',
    'Total agent task failures',
    ['agent_type', 'task_type', 'error_type']
)

agent_task_retries_total = Counter(
    'sergas_agent_task_retries_total',
    'Total agent task retries',
    ['agent_type', 'task_type']
)

agent_queue_size = Gauge(
    'sergas_agent_queue_size',
    'Current agent task queue size',
    ['agent_type']
)

agent_concurrent_tasks = Gauge(
    'sergas_agent_concurrent_tasks',
    'Number of concurrent tasks being processed',
    ['agent_type']
)


# ============================================
# Recommendation Metrics
# ============================================
recommendations_generated_total = Counter(
    'sergas_recommendations_generated_total',
    'Total recommendations generated',
    ['recommendation_type', 'priority']
)

recommendations_accepted_total = Counter(
    'sergas_recommendations_accepted_total',
    'Total recommendations accepted by users',
    ['recommendation_type']
)

recommendations_rejected_total = Counter(
    'sergas_recommendations_rejected_total',
    'Total recommendations rejected',
    ['recommendation_type', 'reason']
)

recommendation_confidence_score = Histogram(
    'sergas_recommendation_confidence_score',
    'Recommendation confidence scores',
    ['recommendation_type'],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

recommendation_generation_duration_seconds = Histogram(
    'sergas_recommendation_generation_duration_seconds',
    'Time to generate recommendations',
    ['recommendation_type'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)


# ============================================
# Database Metrics
# ============================================
database_query_duration_seconds = Histogram(
    'sergas_database_query_duration_seconds',
    'Database query execution time',
    ['query_type', 'table'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

database_connections_active = Gauge(
    'sergas_database_connections_active',
    'Active database connections',
    ['pool']
)

database_transactions_total = Counter(
    'sergas_database_transactions_total',
    'Total database transactions',
    ['operation', 'status']
)

database_deadlocks_total = Counter(
    'sergas_database_deadlocks_total',
    'Total database deadlocks',
    ['table']
)


# ============================================
# Cache Metrics
# ============================================
cache_hits_total = Counter(
    'sergas_cache_hits_total',
    'Total cache hits',
    ['cache_type', 'key_pattern']
)

cache_misses_total = Counter(
    'sergas_cache_misses_total',
    'Total cache misses',
    ['cache_type', 'key_pattern']
)

cache_operation_duration_seconds = Histogram(
    'sergas_cache_operation_duration_seconds',
    'Cache operation latency',
    ['operation', 'cache_type'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

cache_size_bytes = Gauge(
    'sergas_cache_size_bytes',
    'Current cache size in bytes',
    ['cache_type']
)

cache_evictions_total = Counter(
    'sergas_cache_evictions_total',
    'Total cache evictions',
    ['cache_type', 'reason']
)


# ============================================
# Business Metrics
# ============================================
accounts_active_total = Gauge(
    'sergas_accounts_active_total',
    'Total active accounts',
    ['account_type']
)

accounts_processed_total = Counter(
    'sergas_accounts_processed_total',
    'Total accounts processed',
    ['operation', 'status']
)

account_enrichment_duration_seconds = Histogram(
    'sergas_account_enrichment_duration_seconds',
    'Account enrichment processing time',
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0]
)

account_sync_lag_seconds = Gauge(
    'sergas_account_sync_lag_seconds',
    'Time since last successful account sync',
    ['sync_type']
)

cross_sell_opportunities_identified_total = Counter(
    'sergas_cross_sell_opportunities_identified_total',
    'Total cross-sell opportunities identified',
    ['product_category']
)

upsell_opportunities_identified_total = Counter(
    'sergas_upsell_opportunities_identified_total',
    'Total upsell opportunities identified',
    ['current_tier', 'target_tier']
)


# ============================================
# Error Tracking Metrics
# ============================================
errors_total = Counter(
    'sergas_errors_total',
    'Total errors',
    ['error_type', 'component', 'severity']
)

exceptions_unhandled_total = Counter(
    'sergas_exceptions_unhandled_total',
    'Unhandled exceptions',
    ['exception_type', 'module']
)


# ============================================
# Rate Limiting Metrics
# ============================================
rate_limit_remaining = Gauge(
    'sergas_rate_limit_remaining',
    'Remaining rate limit quota',
    ['endpoint', 'client_id']
)

rate_limit_total = Gauge(
    'sergas_rate_limit_total',
    'Total rate limit quota',
    ['endpoint']
)

rate_limit_exceeded_total = Counter(
    'sergas_rate_limit_exceeded_total',
    'Times rate limit was exceeded',
    ['endpoint', 'client_id']
)


# ============================================
# System Info Metrics
# ============================================
system_info = Info(
    'sergas_system_info',
    'System information'
)

application_version = Info(
    'sergas_application_version',
    'Application version information'
)


# ============================================
# Helper Functions & Decorators
# ============================================

def track_time(metric: Histogram, labels: Optional[Dict[str, str]] = None):
    """Decorator to track function execution time"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            labels_dict = labels or {}
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metric.labels(**labels_dict).observe(duration)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            labels_dict = labels or {}
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metric.labels(**labels_dict).observe(duration)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


@contextmanager
def track_inprogress(gauge: Gauge, labels: Optional[Dict[str, str]] = None):
    """Context manager to track in-progress operations"""
    labels_dict = labels or {}
    gauge.labels(**labels_dict).inc()
    try:
        yield
    finally:
        gauge.labels(**labels_dict).dec()


def count_errors(counter: Counter, labels: Optional[Dict[str, str]] = None):
    """Decorator to count errors"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            labels_dict = labels or {}
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                labels_dict['error_type'] = type(e).__name__
                counter.labels(**labels_dict).inc()
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            labels_dict = labels or {}
            try:
                return func(*args, **kwargs)
            except Exception as e:
                labels_dict['error_type'] = type(e).__name__
                counter.labels(**labels_dict).inc()
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


# ============================================
# Metrics Collection
# ============================================

class MetricsCollector:
    """Centralized metrics collection"""

    def __init__(self):
        self.registry = REGISTRY

    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float
    ):
        """Record HTTP request metrics"""
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

    def record_zoho_api_call(
        self,
        operation: str,
        status: str,
        duration: float,
        rate_limit_remaining: Optional[int] = None
    ):
        """Record Zoho API call metrics"""
        zoho_api_calls_total.labels(
            operation=operation,
            status=status
        ).inc()

        zoho_api_duration_seconds.labels(
            operation=operation
        ).observe(duration)

        if rate_limit_remaining is not None:
            zoho_rate_limit_remaining.labels(
                api_type='crm'
            ).set(rate_limit_remaining)

    def record_memory_operation(
        self,
        operation: str,
        duration: float,
        document_type: Optional[str] = None,
        status: str = 'success'
    ):
        """Record memory operation metrics"""
        memory_processing_duration_seconds.labels(
            operation=operation
        ).observe(duration)

        if document_type:
            memory_documents_processed_total.labels(
                document_type=document_type,
                status=status
            ).inc()

    def record_agent_task(
        self,
        agent_type: str,
        task_type: str,
        duration: float,
        status: str,
        error_type: Optional[str] = None
    ):
        """Record agent task metrics"""
        agent_task_attempts_total.labels(
            agent_type=agent_type,
            task_type=task_type
        ).inc()

        agent_task_duration_seconds.labels(
            agent_type=agent_type,
            task_type=task_type
        ).observe(duration)

        if status == 'failure' and error_type:
            agent_task_failures_total.labels(
                agent_type=agent_type,
                task_type=task_type,
                error_type=error_type
            ).inc()

    def record_recommendation(
        self,
        recommendation_type: str,
        priority: str,
        confidence: float,
        generation_time: float
    ):
        """Record recommendation metrics"""
        recommendations_generated_total.labels(
            recommendation_type=recommendation_type,
            priority=priority
        ).inc()

        recommendation_confidence_score.labels(
            recommendation_type=recommendation_type
        ).observe(confidence)

        recommendation_generation_duration_seconds.labels(
            recommendation_type=recommendation_type
        ).observe(generation_time)

    def record_cache_operation(
        self,
        operation: str,
        cache_type: str,
        hit: bool,
        duration: float
    ):
        """Record cache operation metrics"""
        if hit:
            cache_hits_total.labels(
                cache_type=cache_type,
                key_pattern='*'
            ).inc()
        else:
            cache_misses_total.labels(
                cache_type=cache_type,
                key_pattern='*'
            ).inc()

        cache_operation_duration_seconds.labels(
            operation=operation,
            cache_type=cache_type
        ).observe(duration)

    def get_metrics(self) -> bytes:
        """Get all metrics in Prometheus format"""
        return generate_latest(self.registry)


# Global metrics collector instance
metrics_collector = MetricsCollector()


# ============================================
# FastAPI Integration
# ============================================

def setup_metrics(app):
    """Setup metrics endpoint for FastAPI"""
    from fastapi import Response

    @app.get("/metrics")
    async def metrics_endpoint():
        """Prometheus metrics endpoint"""
        metrics_data = metrics_collector.get_metrics()
        return Response(
            content=metrics_data,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )

    # Set system info
    system_info.info({
        'version': '1.0.0',
        'environment': 'production',
        'service': 'sergas-crm'
    })

    application_version.info({
        'version': '1.0.0',
        'build_date': '2025-10-19',
        'git_commit': 'main'
    })

    logger.info("Metrics endpoint configured at /metrics")


import asyncio
