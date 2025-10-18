"""Claude SDK hook implementations for orchestrator.

This module implements hooks for the orchestrator agent:
- pre_tool: Log all tool invocations with metadata
- post_tool: Record tool results and performance metrics
- session_end: Export audit trail and metrics
- pre_task: Initialize task context
- post_task: Store task results in memory

Hooks never fail the main workflow - all errors are logged but not raised.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import time
import json
from pathlib import Path
import structlog
from prometheus_client import Counter, Histogram, Gauge
import asyncio

logger = structlog.get_logger(__name__)


# Prometheus metrics
TOOL_INVOCATIONS = Counter(
    "orchestrator_tool_invocations_total",
    "Total tool invocations",
    ["tool_name", "agent_name"],
)

TOOL_DURATION = Histogram(
    "orchestrator_tool_duration_seconds",
    "Tool execution duration",
    ["tool_name", "agent_name"],
)

TOOL_ERRORS = Counter(
    "orchestrator_tool_errors_total",
    "Tool execution errors",
    ["tool_name", "agent_name", "error_type"],
)

TASK_EXECUTIONS = Counter(
    "orchestrator_task_executions_total",
    "Total task executions",
    ["task_type", "agent_name"],
)

TASK_DURATION = Histogram(
    "orchestrator_task_duration_seconds",
    "Task execution duration",
    ["task_type", "agent_name"],
)

SESSION_DURATION = Histogram(
    "orchestrator_session_duration_seconds",
    "Session duration",
    ["session_type", "status"],
)

ACTIVE_SESSIONS = Gauge(
    "orchestrator_active_sessions",
    "Number of active sessions",
)


class HookContext:
    """Context object for hook execution."""

    def __init__(self, session_id: Optional[str] = None):
        """Initialize hook context.

        Args:
            session_id: Optional session ID for context
        """
        self.session_id = session_id
        self.metadata: Dict[str, Any] = {}
        self.start_time: Optional[float] = None
        self.audit_entries: list[Dict[str, Any]] = []

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to context."""
        self.metadata[key] = value

    def record_audit(self, event_type: str, details: Dict[str, Any]) -> None:
        """Record an audit entry."""
        self.audit_entries.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "details": details,
            "session_id": self.session_id,
        })


class OrchestratorHooks:
    """Hook implementations for orchestrator agent.

    All hooks are designed to never fail the main workflow.
    Errors are logged but not raised.
    """

    def __init__(
        self,
        audit_dir: Path,
        session_manager: Optional[Any] = None,
        memory_client: Optional[Any] = None,
    ):
        """Initialize hooks.

        Args:
            audit_dir: Directory for audit trail exports
            session_manager: Optional SessionManager for session integration
            memory_client: Optional memory client for storing artifacts
        """
        self.audit_dir = Path(audit_dir)
        self.session_manager = session_manager
        self.memory_client = memory_client

        # Ensure audit directory exists
        self.audit_dir.mkdir(parents=True, exist_ok=True)

        # Hook context storage
        self._contexts: Dict[str, HookContext] = {}

        logger.info("orchestrator_hooks_initialized", audit_dir=str(self.audit_dir))

    def pre_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Hook called before tool invocation.

        Logs tool invocation with metadata and increments metrics.

        Args:
            tool_name: Name of the tool being invoked
            tool_input: Input parameters to the tool
            agent_name: Name of the agent invoking the tool
            session_id: Optional session ID
            **kwargs: Additional context
        """
        try:
            agent = agent_name or "unknown"

            # Get or create context
            context = self._get_or_create_context(session_id)
            context.start_time = time.time()
            context.add_metadata("tool_name", tool_name)
            context.add_metadata("agent_name", agent)

            # Log invocation
            logger.info(
                "tool_invocation",
                tool_name=tool_name,
                agent_name=agent,
                session_id=session_id,
                input_size=len(json.dumps(tool_input)),
            )

            # Record audit entry
            context.record_audit("tool_invocation", {
                "tool_name": tool_name,
                "agent_name": agent,
                "input_keys": list(tool_input.keys()),
            })

            # Update metrics
            TOOL_INVOCATIONS.labels(tool_name=tool_name, agent_name=agent).inc()

        except Exception as e:
            logger.error("pre_tool_hook_error", error=str(e), exc_info=True)

    def post_tool(
        self,
        tool_name: str,
        tool_output: Any,
        error: Optional[Exception] = None,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Hook called after tool invocation.

        Records tool results, performance metrics, and any errors.

        Args:
            tool_name: Name of the tool that was invoked
            tool_output: Output from the tool
            error: Optional exception if tool failed
            agent_name: Name of the agent
            session_id: Optional session ID
            **kwargs: Additional context
        """
        try:
            agent = agent_name or "unknown"
            context = self._get_or_create_context(session_id)

            # Calculate duration
            duration = 0.0
            if context.start_time:
                duration = time.time() - context.start_time

            # Log result
            if error:
                logger.error(
                    "tool_error",
                    tool_name=tool_name,
                    agent_name=agent,
                    session_id=session_id,
                    error=str(error),
                    duration_seconds=duration,
                )

                # Record error in metrics
                error_type = type(error).__name__
                TOOL_ERRORS.labels(
                    tool_name=tool_name,
                    agent_name=agent,
                    error_type=error_type,
                ).inc()

                # Audit entry for error
                context.record_audit("tool_error", {
                    "tool_name": tool_name,
                    "agent_name": agent,
                    "error_type": error_type,
                    "error_message": str(error),
                })

            else:
                logger.info(
                    "tool_success",
                    tool_name=tool_name,
                    agent_name=agent,
                    session_id=session_id,
                    duration_seconds=duration,
                    output_type=type(tool_output).__name__,
                )

                # Audit entry for success
                context.record_audit("tool_success", {
                    "tool_name": tool_name,
                    "agent_name": agent,
                    "duration_seconds": duration,
                })

            # Update duration metrics
            TOOL_DURATION.labels(tool_name=tool_name, agent_name=agent).observe(duration)

            # Update session metrics if session manager available
            if self.session_manager and session_id:
                asyncio.create_task(self._update_session_metrics(
                    session_id,
                    api_call_count=1,
                    error_count=1 if error else 0,
                ))

        except Exception as e:
            logger.error("post_tool_hook_error", error=str(e), exc_info=True)

    def pre_task(
        self,
        task_type: str,
        task_description: str,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Hook called before task execution.

        Initializes task context and logs task start.

        Args:
            task_type: Type of task being executed
            task_description: Description of the task
            agent_name: Name of the agent executing task
            session_id: Optional session ID
            **kwargs: Additional context
        """
        try:
            agent = agent_name or "unknown"
            context = self._get_or_create_context(session_id)
            context.start_time = time.time()
            context.add_metadata("task_type", task_type)
            context.add_metadata("task_description", task_description)

            logger.info(
                "task_started",
                task_type=task_type,
                agent_name=agent,
                session_id=session_id,
                description=task_description[:100],  # Truncate long descriptions
            )

            # Record audit entry
            context.record_audit("task_started", {
                "task_type": task_type,
                "agent_name": agent,
                "description": task_description,
            })

            # Update metrics
            TASK_EXECUTIONS.labels(task_type=task_type, agent_name=agent).inc()

        except Exception as e:
            logger.error("pre_task_hook_error", error=str(e), exc_info=True)

    def post_task(
        self,
        task_type: str,
        task_result: Any,
        error: Optional[Exception] = None,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Hook called after task execution.

        Stores task results in memory and records metrics.

        Args:
            task_type: Type of task that was executed
            task_result: Result from the task
            error: Optional exception if task failed
            agent_name: Name of the agent
            session_id: Optional session ID
            **kwargs: Additional context
        """
        try:
            agent = agent_name or "unknown"
            context = self._get_or_create_context(session_id)

            # Calculate duration
            duration = 0.0
            if context.start_time:
                duration = time.time() - context.start_time

            if error:
                logger.error(
                    "task_failed",
                    task_type=task_type,
                    agent_name=agent,
                    session_id=session_id,
                    error=str(error),
                    duration_seconds=duration,
                )

                context.record_audit("task_failed", {
                    "task_type": task_type,
                    "agent_name": agent,
                    "error": str(error),
                    "duration_seconds": duration,
                })

            else:
                logger.info(
                    "task_completed",
                    task_type=task_type,
                    agent_name=agent,
                    session_id=session_id,
                    duration_seconds=duration,
                )

                context.record_audit("task_completed", {
                    "task_type": task_type,
                    "agent_name": agent,
                    "duration_seconds": duration,
                })

                # Store result in memory if available
                if self.memory_client and session_id:
                    asyncio.create_task(self._store_task_result(
                        session_id,
                        task_type,
                        task_result,
                    ))

            # Update duration metrics
            TASK_DURATION.labels(task_type=task_type, agent_name=agent).observe(duration)

        except Exception as e:
            logger.error("post_task_hook_error", error=str(e), exc_info=True)

    def session_end(
        self,
        session_id: str,
        session_status: str,
        session_type: str = "unknown",
        **kwargs: Any,
    ) -> None:
        """Hook called at session end.

        Exports complete audit trail and metrics.

        Args:
            session_id: ID of the session ending
            session_status: Final status of session
            session_type: Type of session
            **kwargs: Additional context
        """
        try:
            context = self._get_or_create_context(session_id)

            # Calculate session duration
            duration = 0.0
            if context.start_time:
                duration = time.time() - context.start_time

            logger.info(
                "session_ended",
                session_id=session_id,
                status=session_status,
                session_type=session_type,
                duration_seconds=duration,
                audit_entries=len(context.audit_entries),
            )

            # Update session duration metrics
            SESSION_DURATION.labels(
                session_type=session_type,
                status=session_status,
            ).observe(duration)

            # Export audit trail
            self._export_audit_trail(session_id, context, session_status)

            # Export metrics summary
            self._export_metrics_summary(session_id, context, duration)

            # Cleanup context
            if session_id in self._contexts:
                del self._contexts[session_id]

            # Update active sessions gauge
            ACTIVE_SESSIONS.dec()

        except Exception as e:
            logger.error("session_end_hook_error", error=str(e), exc_info=True)

    def session_start(
        self,
        session_id: str,
        session_type: str = "unknown",
        **kwargs: Any,
    ) -> None:
        """Hook called at session start.

        Args:
            session_id: ID of the session starting
            session_type: Type of session
            **kwargs: Additional context
        """
        try:
            context = self._get_or_create_context(session_id)
            context.start_time = time.time()
            context.add_metadata("session_type", session_type)

            logger.info(
                "session_started",
                session_id=session_id,
                session_type=session_type,
            )

            # Update active sessions gauge
            ACTIVE_SESSIONS.inc()

            context.record_audit("session_started", {
                "session_type": session_type,
            })

        except Exception as e:
            logger.error("session_start_hook_error", error=str(e), exc_info=True)

    # Private helper methods

    def _get_or_create_context(self, session_id: Optional[str]) -> HookContext:
        """Get or create hook context for session.

        Args:
            session_id: Optional session ID

        Returns:
            HookContext: Context object
        """
        if not session_id:
            session_id = "default"

        if session_id not in self._contexts:
            self._contexts[session_id] = HookContext(session_id)

        return self._contexts[session_id]

    def _export_audit_trail(
        self,
        session_id: str,
        context: HookContext,
        status: str,
    ) -> None:
        """Export complete audit trail to file.

        Args:
            session_id: Session ID
            context: Hook context with audit entries
            status: Final session status
        """
        try:
            audit_file = self.audit_dir / f"{session_id}_audit.json"

            audit_trail = {
                "session_id": session_id,
                "status": status,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "total_entries": len(context.audit_entries),
                "entries": context.audit_entries,
                "metadata": context.metadata,
            }

            with open(audit_file, "w") as f:
                json.dump(audit_trail, f, indent=2)

            logger.info(
                "audit_trail_exported",
                session_id=session_id,
                file=str(audit_file),
                entries=len(context.audit_entries),
            )

        except Exception as e:
            logger.error("audit_export_failed", session_id=session_id, error=str(e))

    def _export_metrics_summary(
        self,
        session_id: str,
        context: HookContext,
        duration: float,
    ) -> None:
        """Export metrics summary to file.

        Args:
            session_id: Session ID
            context: Hook context
            duration: Total session duration
        """
        try:
            metrics_file = self.audit_dir / f"{session_id}_metrics.json"

            # Count event types
            event_counts = {}
            for entry in context.audit_entries:
                event_type = entry.get("event_type", "unknown")
                event_counts[event_type] = event_counts.get(event_type, 0) + 1

            metrics = {
                "session_id": session_id,
                "duration_seconds": duration,
                "event_counts": event_counts,
                "total_events": len(context.audit_entries),
                "metadata": context.metadata,
                "exported_at": datetime.now(timezone.utc).isoformat(),
            }

            with open(metrics_file, "w") as f:
                json.dump(metrics, f, indent=2)

            logger.info(
                "metrics_exported",
                session_id=session_id,
                file=str(metrics_file),
            )

        except Exception as e:
            logger.error("metrics_export_failed", session_id=session_id, error=str(e))

    async def _update_session_metrics(
        self,
        session_id: str,
        **metrics: Any,
    ) -> None:
        """Update session metrics via session manager.

        Args:
            session_id: Session ID
            **metrics: Metric updates
        """
        try:
            if self.session_manager:
                await self.session_manager.update_metrics(session_id, **metrics)
        except Exception as e:
            logger.error("session_metrics_update_failed", session_id=session_id, error=str(e))

    async def _store_task_result(
        self,
        session_id: str,
        task_type: str,
        result: Any,
    ) -> None:
        """Store task result in memory.

        Args:
            session_id: Session ID
            task_type: Type of task
            result: Task result
        """
        try:
            if self.memory_client:
                key = f"task_result:{session_id}:{task_type}"
                # Store result in memory with 7 day TTL
                await self.memory_client.store(key, result, ttl=604800)

                logger.debug(
                    "task_result_stored",
                    session_id=session_id,
                    task_type=task_type,
                    key=key,
                )
        except Exception as e:
            logger.error("task_result_storage_failed", session_id=session_id, error=str(e))


def create_hook_registry(
    audit_dir: Path,
    session_manager: Optional[Any] = None,
    memory_client: Optional[Any] = None,
) -> Dict[str, callable]:
    """Create hook registry for Claude SDK integration.

    Args:
        audit_dir: Directory for audit exports
        session_manager: Optional SessionManager instance
        memory_client: Optional memory client

    Returns:
        Dictionary mapping hook names to callables
    """
    hooks = OrchestratorHooks(audit_dir, session_manager, memory_client)

    return {
        "pre_tool": hooks.pre_tool,
        "post_tool": hooks.post_tool,
        "pre_task": hooks.pre_task,
        "post_task": hooks.post_task,
        "session_end": hooks.session_end,
        "session_start": hooks.session_start,
    }
