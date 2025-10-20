"""Metrics hook implementation for performance tracking and monitoring.

Part of Week 6: Base Agent Infrastructure - Hook System.
"""

import structlog
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict

logger = structlog.get_logger(__name__)


@dataclass
class SessionMetrics:
    """Metrics for an agent session."""

    agent_id: str
    session_id: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    tool_execution_count: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    tools_used: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    error_rate: float = 0.0


class MetricsHook:
    """Performance metrics and monitoring for agents."""

    # Token pricing per model (input/output per million tokens)
    TOKEN_PRICING = {
        "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
        "claude-3-5-haiku-20241022": {"input": 1.00, "output": 5.00},
        "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
    }

    def __init__(self):
        """Initialize metrics hook."""
        self.logger = logger
        self.sessions: Dict[str, SessionMetrics] = {}

    async def on_session_start(self, context: Dict[str, Any]) -> None:
        """Track session start.

        Args:
            context: Session context with agent_id, session_id
        """
        agent_id = context.get("agent_id", "unknown")
        session_id = context.get("session_id", "unknown")

        metrics = SessionMetrics(
            agent_id=agent_id,
            session_id=session_id,
        )
        self.sessions[session_id] = metrics

        self.logger.info(
            "session_started",
            agent_id=agent_id,
            session_id=session_id,
            timestamp=metrics.start_time.isoformat(),
        )

    async def on_session_end(self, context: Dict[str, Any]) -> None:
        """Track session end and calculate final metrics.

        Args:
            context: Session context
        """
        session_id = context.get("session_id", "unknown")

        if session_id not in self.sessions:
            self.logger.warning("session_not_found", session_id=session_id)
            return

        metrics = self.sessions[session_id]
        metrics.end_time = datetime.utcnow()
        metrics.duration_ms = (
            (metrics.end_time - metrics.start_time).total_seconds() * 1000
        )

        # Calculate error rate
        total_executions = metrics.successful_executions + metrics.failed_executions
        if total_executions > 0:
            metrics.error_rate = metrics.failed_executions / total_executions

        self.logger.info(
            "session_ended",
            agent_id=metrics.agent_id,
            session_id=session_id,
            duration_ms=metrics.duration_ms,
            tool_executions=metrics.tool_execution_count,
            successful=metrics.successful_executions,
            failed=metrics.failed_executions,
            error_rate=metrics.error_rate,
            total_tokens=metrics.total_input_tokens + metrics.total_output_tokens,
            estimated_cost_usd=metrics.estimated_cost_usd,
        )

    async def on_tool_execution(
        self, tool_name: str, context: Dict[str, Any], success: bool = True
    ) -> None:
        """Track tool execution.

        Args:
            tool_name: Name of executed tool
            context: Execution context
            success: Whether execution was successful
        """
        session_id = context.get("session_id", "unknown")

        if session_id not in self.sessions:
            self.logger.warning("session_not_found", session_id=session_id)
            return

        metrics = self.sessions[session_id]
        metrics.tool_execution_count += 1
        metrics.tools_used[tool_name] += 1

        if success:
            metrics.successful_executions += 1
        else:
            metrics.failed_executions += 1

        self.logger.debug(
            "tool_executed",
            session_id=session_id,
            tool_name=tool_name,
            success=success,
            total_executions=metrics.tool_execution_count,
        )

    async def on_token_usage(
        self, input_tokens: int, output_tokens: int, context: Dict[str, Any]
    ) -> None:
        """Track token usage and calculate cost.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            context: Execution context with model info
        """
        session_id = context.get("session_id", "unknown")
        model = context.get("model", "claude-3-5-sonnet-20241022")

        if session_id not in self.sessions:
            self.logger.warning("session_not_found", session_id=session_id)
            return

        metrics = self.sessions[session_id]
        metrics.total_input_tokens += input_tokens
        metrics.total_output_tokens += output_tokens

        # Calculate cost
        pricing = self.TOKEN_PRICING.get(model, self.TOKEN_PRICING["claude-3-5-sonnet-20241022"])
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        metrics.estimated_cost_usd += input_cost + output_cost

        self.logger.debug(
            "token_usage",
            session_id=session_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=input_cost + output_cost,
            total_cost_usd=metrics.estimated_cost_usd,
        )

    def get_session_metrics(self, session_id: str) -> Optional[SessionMetrics]:
        """Get metrics for a specific session.

        Args:
            session_id: Session identifier

        Returns:
            Session metrics or None
        """
        return self.sessions.get(session_id)

    def get_aggregate_metrics(
        self, agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get aggregate metrics across sessions.

        Args:
            agent_id: Filter by agent (optional)

        Returns:
            Aggregated metrics
        """
        sessions_to_aggregate = [
            m
            for m in self.sessions.values()
            if agent_id is None or m.agent_id == agent_id
        ]

        if not sessions_to_aggregate:
            return {}

        total_sessions = len(sessions_to_aggregate)
        total_executions = sum(m.tool_execution_count for m in sessions_to_aggregate)
        total_successful = sum(m.successful_executions for m in sessions_to_aggregate)
        total_failed = sum(m.failed_executions for m in sessions_to_aggregate)
        total_tokens = sum(
            m.total_input_tokens + m.total_output_tokens
            for m in sessions_to_aggregate
        )
        total_cost = sum(m.estimated_cost_usd for m in sessions_to_aggregate)

        # Calculate average error rate
        avg_error_rate = (
            total_failed / total_executions if total_executions > 0 else 0.0
        )

        # Aggregate tool usage
        tool_usage_aggregate = defaultdict(int)
        for metrics in sessions_to_aggregate:
            for tool, count in metrics.tools_used.items():
                tool_usage_aggregate[tool] += count

        return {
            "total_sessions": total_sessions,
            "total_tool_executions": total_executions,
            "successful_executions": total_successful,
            "failed_executions": total_failed,
            "average_error_rate": avg_error_rate,
            "total_tokens_used": total_tokens,
            "total_cost_usd": total_cost,
            "average_cost_per_session_usd": total_cost / total_sessions,
            "tool_usage": dict(tool_usage_aggregate),
        }

    def export_prometheus_metrics(self) -> Dict[str, Any]:
        """Export metrics in Prometheus format.

        Returns:
            Prometheus-compatible metrics
        """
        aggregate = self.get_aggregate_metrics()

        return {
            "agent_session_count": aggregate.get("total_sessions", 0),
            "agent_tool_executions_total": aggregate.get("total_tool_executions", 0),
            "agent_successful_executions_total": aggregate.get(
                "successful_executions", 0
            ),
            "agent_failed_executions_total": aggregate.get("failed_executions", 0),
            "agent_error_rate": aggregate.get("average_error_rate", 0.0),
            "agent_tokens_used_total": aggregate.get("total_tokens_used", 0),
            "agent_cost_usd_total": aggregate.get("total_cost_usd", 0.0),
            "agent_session_duration_seconds": sum(
                m.duration_ms / 1000 for m in self.sessions.values() if m.end_time
            ),
        }

    def reset_session_metrics(self, session_id: Optional[str] = None) -> None:
        """Reset metrics for a session or all sessions.

        Args:
            session_id: Session to reset, or None for all
        """
        if session_id:
            if session_id in self.sessions:
                del self.sessions[session_id]
                self.logger.info("session_metrics_reset", session_id=session_id)
        else:
            self.sessions.clear()
            self.logger.info("all_session_metrics_reset")
