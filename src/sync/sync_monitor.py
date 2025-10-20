"""
Sync monitoring and metrics collection for Cognee sync pipeline.

Provides comprehensive monitoring with:
- Prometheus metrics collection
- Sync metrics tracking (duration, throughput, errors)
- Performance monitoring
- Error tracking and alerting
- Health checks
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from contextlib import contextmanager
import time
import structlog
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    Info,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

from src.models.sync.sync_models import (
    SyncType,
    SyncStatus,
    SyncSummary,
)

logger = structlog.get_logger(__name__)


class SyncMonitor:
    """
    Monitor and collect metrics for Cognee sync operations.

    Provides Prometheus-compatible metrics for:
    - Sync session tracking
    - Performance metrics (duration, throughput)
    - Error tracking
    - Resource utilization
    - Health checks

    Example:
        >>> monitor = SyncMonitor()
        >>> # Track sync session
        >>> monitor.record_sync_started(sync_type=SyncType.INCREMENTAL)
        >>> monitor.record_sync_completed(summary)
        >>> # Export metrics
        >>> metrics = monitor.get_metrics()
    """

    def __init__(
        self,
        registry: Optional[CollectorRegistry] = None,
        namespace: str = "cognee_sync",
    ) -> None:
        """
        Initialize sync monitor.

        Args:
            registry: Prometheus registry (creates new if None)
            namespace: Metric namespace prefix
        """
        self.registry = registry or CollectorRegistry()
        self.namespace = namespace

        self.logger = logger.bind(component="sync_monitor")

        # Initialize Prometheus metrics
        self._init_metrics()

        # Internal state
        self._active_syncs: Dict[str, Dict[str, Any]] = {}

        self.logger.info("sync_monitor_initialized", namespace=namespace)

    def _init_metrics(self) -> None:
        """Initialize Prometheus metrics."""

        # Sync session metrics
        self.sync_sessions_total = Counter(
            name=f"{self.namespace}_sessions_total",
            documentation="Total number of sync sessions",
            labelnames=["sync_type", "status"],
            registry=self.registry,
        )

        self.sync_records_total = Counter(
            name=f"{self.namespace}_records_total",
            documentation="Total number of records processed",
            labelnames=["sync_type", "status"],
            registry=self.registry,
        )

        self.sync_duration_seconds = Histogram(
            name=f"{self.namespace}_duration_seconds",
            documentation="Sync session duration in seconds",
            labelnames=["sync_type"],
            buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600],
            registry=self.registry,
        )

        self.sync_throughput = Histogram(
            name=f"{self.namespace}_throughput_records_per_second",
            documentation="Sync throughput (records per second)",
            labelnames=["sync_type"],
            buckets=[1, 5, 10, 25, 50, 100, 200, 500, 1000],
            registry=self.registry,
        )

        # Error metrics
        self.sync_errors_total = Counter(
            name=f"{self.namespace}_errors_total",
            documentation="Total number of sync errors",
            labelnames=["sync_type", "error_type"],
            registry=self.registry,
        )

        self.sync_error_rate = Gauge(
            name=f"{self.namespace}_error_rate",
            documentation="Current sync error rate (0-1)",
            labelnames=["sync_type"],
            registry=self.registry,
        )

        # Active sync metrics
        self.active_syncs = Gauge(
            name=f"{self.namespace}_active_syncs",
            documentation="Number of currently active sync sessions",
            labelnames=["sync_type"],
            registry=self.registry,
        )

        self.sync_progress = Gauge(
            name=f"{self.namespace}_progress_percentage",
            documentation="Current sync progress percentage",
            labelnames=["session_id", "sync_type"],
            registry=self.registry,
        )

        # Performance metrics
        self.batch_processing_duration = Summary(
            name=f"{self.namespace}_batch_processing_seconds",
            documentation="Batch processing duration",
            labelnames=["batch_size"],
            registry=self.registry,
        )

        self.cognee_ingestion_duration = Summary(
            name=f"{self.namespace}_cognee_ingestion_seconds",
            documentation="Cognee ingestion duration per account",
            registry=self.registry,
        )

        self.zoho_fetch_duration = Summary(
            name=f"{self.namespace}_zoho_fetch_seconds",
            documentation="Zoho account fetch duration",
            registry=self.registry,
        )

        # Health metrics
        self.last_successful_sync = Gauge(
            name=f"{self.namespace}_last_successful_sync_timestamp",
            documentation="Timestamp of last successful sync",
            labelnames=["sync_type"],
            registry=self.registry,
        )

        self.health_status = Gauge(
            name=f"{self.namespace}_health_status",
            documentation="Health status (1=healthy, 0=unhealthy)",
            registry=self.registry,
        )

        # System info
        self.info = Info(
            name=f"{self.namespace}_info",
            documentation="Sync monitor information",
            registry=self.registry,
        )
        self.info.info({
            "version": "1.0.0",
            "namespace": self.namespace,
        })

    def record_sync_started(
        self,
        session_id: str,
        sync_type: SyncType,
        total_records: int = 0,
    ) -> None:
        """
        Record sync session start.

        Args:
            session_id: Sync session ID
            sync_type: Type of sync operation
            total_records: Total records to process
        """
        self._active_syncs[session_id] = {
            "sync_type": sync_type,
            "started_at": datetime.utcnow(),
            "total_records": total_records,
            "processed_records": 0,
        }

        # Update active syncs gauge
        self.active_syncs.labels(sync_type=sync_type.value).inc()

        self.logger.info(
            "sync_started_recorded",
            session_id=session_id,
            sync_type=sync_type.value,
            total_records=total_records,
        )

    def record_sync_progress(
        self,
        session_id: str,
        processed_records: int,
        total_records: int,
    ) -> None:
        """
        Record sync progress update.

        Args:
            session_id: Sync session ID
            processed_records: Number of records processed
            total_records: Total records to process
        """
        if session_id in self._active_syncs:
            self._active_syncs[session_id]["processed_records"] = processed_records

            progress = (processed_records / total_records * 100) if total_records > 0 else 0

            sync_type = self._active_syncs[session_id]["sync_type"]
            self.sync_progress.labels(
                session_id=session_id,
                sync_type=sync_type.value,
            ).set(progress)

    def record_sync_completed(
        self,
        summary: SyncSummary,
    ) -> None:
        """
        Record sync session completion.

        Args:
            summary: Sync summary with results
        """
        session_id = summary.session_id
        sync_type = summary.sync_type

        # Update counters
        self.sync_sessions_total.labels(
            sync_type=sync_type.value,
            status=summary.status.value,
        ).inc()

        self.sync_records_total.labels(
            sync_type=sync_type.value,
            status="success",
        ).inc(summary.successful_records)

        self.sync_records_total.labels(
            sync_type=sync_type.value,
            status="failed",
        ).inc(summary.failed_records)

        # Record duration
        if summary.duration_seconds:
            self.sync_duration_seconds.labels(
                sync_type=sync_type.value,
            ).observe(summary.duration_seconds)

        # Record throughput
        if summary.records_per_second:
            self.sync_throughput.labels(
                sync_type=sync_type.value,
            ).observe(summary.records_per_second)

        # Update error rate
        error_rate = (
            summary.failed_records / summary.total_records
            if summary.total_records > 0
            else 0.0
        )
        self.sync_error_rate.labels(sync_type=sync_type.value).set(error_rate)

        # Update last successful sync timestamp
        if summary.status == SyncStatus.COMPLETED:
            self.last_successful_sync.labels(sync_type=sync_type.value).set(
                summary.completed_at.timestamp() if summary.completed_at else time.time()
            )

        # Remove from active syncs
        if session_id in self._active_syncs:
            del self._active_syncs[session_id]
            self.active_syncs.labels(sync_type=sync_type.value).dec()

        # Clear progress gauge
        self.sync_progress.remove(session_id, sync_type.value)

        self.logger.info(
            "sync_completed_recorded",
            session_id=session_id,
            sync_type=sync_type.value,
            status=summary.status.value,
            duration=summary.duration_seconds,
            throughput=summary.records_per_second,
        )

    def record_sync_error(
        self,
        sync_type: SyncType,
        error_type: str,
        error_message: str,
    ) -> None:
        """
        Record sync error.

        Args:
            sync_type: Type of sync operation
            error_type: Type/class of error
            error_message: Error message
        """
        self.sync_errors_total.labels(
            sync_type=sync_type.value,
            error_type=error_type,
        ).inc()

        self.logger.warning(
            "sync_error_recorded",
            sync_type=sync_type.value,
            error_type=error_type,
            error_message=error_message[:100],  # Truncate long messages
        )

    @contextmanager
    def track_batch_processing(self, batch_size: int):
        """
        Context manager to track batch processing duration.

        Args:
            batch_size: Number of records in batch

        Example:
            >>> with monitor.track_batch_processing(100):
            ...     process_batch()
        """
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            self.batch_processing_duration.labels(
                batch_size=str(batch_size),
            ).observe(duration)

    @contextmanager
    def track_cognee_ingestion(self):
        """
        Context manager to track Cognee ingestion duration.

        Example:
            >>> with monitor.track_cognee_ingestion():
            ...     await cognee_client.add_account(account)
        """
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            self.cognee_ingestion_duration.observe(duration)

    @contextmanager
    def track_zoho_fetch(self):
        """
        Context manager to track Zoho fetch duration.

        Example:
            >>> with monitor.track_zoho_fetch():
            ...     accounts = zoho_client.get_accounts()
        """
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            self.zoho_fetch_duration.observe(duration)

    def update_health_status(self, healthy: bool) -> None:
        """
        Update overall health status.

        Args:
            healthy: True if system is healthy, False otherwise
        """
        self.health_status.set(1 if healthy else 0)

        self.logger.info("health_status_updated", healthy=healthy)

    def get_metrics(self) -> bytes:
        """
        Get Prometheus metrics in text format.

        Returns:
            Metrics in Prometheus text exposition format
        """
        return generate_latest(self.registry)

    def get_metrics_content_type(self) -> str:
        """
        Get Prometheus metrics content type.

        Returns:
            Content type for Prometheus metrics
        """
        return CONTENT_TYPE_LATEST

    def get_active_syncs(self) -> List[Dict[str, Any]]:
        """
        Get information about active sync sessions.

        Returns:
            List of active sync information
        """
        active = []
        for session_id, info in self._active_syncs.items():
            elapsed = (datetime.utcnow() - info["started_at"]).total_seconds()
            progress = (
                info["processed_records"] / info["total_records"] * 100
                if info["total_records"] > 0
                else 0
            )

            active.append({
                "session_id": session_id,
                "sync_type": info["sync_type"].value,
                "started_at": info["started_at"].isoformat(),
                "elapsed_seconds": elapsed,
                "total_records": info["total_records"],
                "processed_records": info["processed_records"],
                "progress_percentage": progress,
            })

        return active

    def get_health_check(self) -> Dict[str, Any]:
        """
        Perform health check and return status.

        Returns:
            Health check results
        """
        now = datetime.utcnow()
        healthy = True
        issues = []

        # Check for stale syncs (running > 1 hour)
        for session_id, info in self._active_syncs.items():
            elapsed = (now - info["started_at"]).total_seconds()
            if elapsed > 3600:  # 1 hour
                healthy = False
                issues.append(
                    f"Sync {session_id} running for {elapsed/60:.1f} minutes"
                )

        # Check last successful sync (should be within last 24 hours for incremental)
        # This would require access to metrics, simplified here

        self.update_health_status(healthy)

        return {
            "healthy": healthy,
            "timestamp": now.isoformat(),
            "active_syncs": len(self._active_syncs),
            "issues": issues,
        }

    def get_summary_stats(
        self,
        sync_type: Optional[SyncType] = None,
    ) -> Dict[str, Any]:
        """
        Get summary statistics for syncs.

        Args:
            sync_type: Filter by sync type (None for all)

        Returns:
            Summary statistics
        """
        # Note: This is a simplified version
        # In production, you'd query the actual metric values from Prometheus

        stats = {
            "active_syncs": len(self._active_syncs),
            "total_sessions": "N/A",  # Would come from Prometheus
            "total_records_processed": "N/A",
            "average_duration_seconds": "N/A",
            "average_throughput": "N/A",
            "error_rate": "N/A",
        }

        return stats

    def reset_metrics(self) -> None:
        """
        Reset all metrics (use with caution in production).

        This recreates the registry and reinitializes all metrics.
        """
        self.registry = CollectorRegistry()
        self._init_metrics()
        self._active_syncs.clear()

        self.logger.warning("metrics_reset")


class MetricsExporter:
    """
    HTTP server for exporting Prometheus metrics.

    Example:
        >>> monitor = SyncMonitor()
        >>> exporter = MetricsExporter(monitor, port=9090)
        >>> exporter.start()
        >>> # Metrics available at http://localhost:9090/metrics
    """

    def __init__(
        self,
        monitor: SyncMonitor,
        port: int = 9090,
        host: str = "0.0.0.0",
    ) -> None:
        """
        Initialize metrics exporter.

        Args:
            monitor: SyncMonitor instance
            port: HTTP port for metrics endpoint
            host: Host to bind to
        """
        self.monitor = monitor
        self.port = port
        self.host = host

        self.logger = logger.bind(component="metrics_exporter")

    def start(self) -> None:
        """
        Start HTTP server for metrics export.

        Note: In production, use prometheus_client.start_http_server()
        or integrate with your web framework (FastAPI, Flask, etc.)
        """
        from prometheus_client import start_http_server

        start_http_server(port=self.port, addr=self.host, registry=self.monitor.registry)

        self.logger.info(
            "metrics_exporter_started",
            host=self.host,
            port=self.port,
        )

    def get_metrics_handler(self):
        """
        Get metrics handler for web frameworks.

        Returns:
            Handler function that returns metrics

        Example (FastAPI):
            >>> from fastapi import FastAPI, Response
            >>> app = FastAPI()
            >>> @app.get("/metrics")
            >>> async def metrics():
            ...     return Response(
            ...         content=exporter.monitor.get_metrics(),
            ...         media_type=exporter.monitor.get_metrics_content_type()
            ...     )
        """
        def metrics_handler():
            return self.monitor.get_metrics()

        return metrics_handler
