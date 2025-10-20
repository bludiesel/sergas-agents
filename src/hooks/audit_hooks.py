"""Audit hook implementation for comprehensive logging of agent actions.

Part of Week 6: Base Agent Infrastructure - Hook System.
"""

import structlog
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from src.db.repositories.audit_repository import AuditRepository
from src.models.audit import AuditEvent


logger = structlog.get_logger(__name__)


@dataclass
class ToolExecutionContext:
    """Context for tracking tool execution."""

    tool_name: str
    agent_id: str
    session_id: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    tool_input: Dict[str, Any] = field(default_factory=dict)
    tool_output: Optional[Any] = None
    status: str = "pending"
    error_message: Optional[str] = None


class AuditHook:
    """Comprehensive audit logging for all agent actions."""

    # Sensitive fields to mask in logs
    SENSITIVE_FIELDS = {
        "password",
        "api_key",
        "secret",
        "token",
        "authorization",
        "refresh_token",
        "access_token",
        "client_secret",
    }

    def __init__(self, db: Optional[AuditRepository] = None):
        """Initialize audit hook.

        Args:
            db: Database repository for storing audit events
        """
        self.db = db
        self.logger = logger
        self.active_executions: Dict[str, ToolExecutionContext] = {}

    async def pre_tool(
        self, tool_name: str, tool_input: Dict[str, Any], context: Dict[str, Any]
    ) -> None:
        """Log tool execution before it runs.

        Args:
            tool_name: Name of the tool being executed
            tool_input: Input parameters for the tool
            context: Execution context with agent_id, session_id, etc.
        """
        agent_id = context.get("agent_id", "unknown")
        session_id = context.get("session_id", "unknown")

        # Create execution context
        execution_key = f"{session_id}:{tool_name}:{datetime.utcnow().isoformat()}"
        execution_ctx = ToolExecutionContext(
            tool_name=tool_name,
            agent_id=agent_id,
            session_id=session_id,
            tool_input=self._mask_sensitive_data(tool_input),
            status="started",
        )
        self.active_executions[execution_key] = execution_ctx

        # Log to structured logger
        self.logger.info(
            "tool_execution_started",
            tool_name=tool_name,
            agent_id=agent_id,
            session_id=session_id,
            execution_key=execution_key,
        )

        # Store audit event in database
        if self.db:
            event = AuditEvent(
                timestamp=execution_ctx.start_time,
                event_type="tool_execution",
                agent_id=agent_id,
                session_id=session_id,
                tool_name=tool_name,
                tool_input=execution_ctx.tool_input,
                status="started",
            )
            await self.db.save(event)

    async def post_tool(
        self, tool_name: str, tool_output: Any, context: Dict[str, Any]
    ) -> None:
        """Log tool execution after completion.

        Args:
            tool_name: Name of the tool that was executed
            tool_output: Output/result from the tool
            context: Execution context with agent_id, session_id, etc.
        """
        agent_id = context.get("agent_id", "unknown")
        session_id = context.get("session_id", "unknown")

        # Find matching execution context
        execution_ctx = self._find_execution_context(session_id, tool_name)

        if execution_ctx:
            execution_ctx.end_time = datetime.utcnow()
            execution_ctx.tool_output = self._mask_sensitive_data(tool_output)
            execution_ctx.status = "completed"

            # Calculate execution time
            execution_time_ms = (
                (execution_ctx.end_time - execution_ctx.start_time).total_seconds()
                * 1000
            )

            # Log completion
            self.logger.info(
                "tool_execution_completed",
                tool_name=tool_name,
                agent_id=agent_id,
                session_id=session_id,
                execution_time_ms=execution_time_ms,
            )

            # Store completion event
            if self.db:
                event = AuditEvent(
                    timestamp=execution_ctx.end_time,
                    event_type="tool_execution",
                    agent_id=agent_id,
                    session_id=session_id,
                    tool_name=tool_name,
                    tool_output=execution_ctx.tool_output,
                    status="completed",
                    execution_time_ms=execution_time_ms,
                )
                await self.db.save(event)

    async def on_tool_error(
        self, tool_name: str, error: Exception, context: Dict[str, Any]
    ) -> None:
        """Log tool execution errors.

        Args:
            tool_name: Name of the tool that failed
            error: Exception that was raised
            context: Execution context
        """
        agent_id = context.get("agent_id", "unknown")
        session_id = context.get("session_id", "unknown")

        # Find execution context
        execution_ctx = self._find_execution_context(session_id, tool_name)

        if execution_ctx:
            execution_ctx.end_time = datetime.utcnow()
            execution_ctx.status = "failed"
            execution_ctx.error_message = str(error)

            # Log error
            self.logger.error(
                "tool_execution_failed",
                tool_name=tool_name,
                agent_id=agent_id,
                session_id=session_id,
                error=str(error),
                exc_info=True,
            )

            # Store error event
            if self.db:
                event = AuditEvent(
                    timestamp=execution_ctx.end_time,
                    event_type="tool_execution",
                    agent_id=agent_id,
                    session_id=session_id,
                    tool_name=tool_name,
                    status="failed",
                    error_message=execution_ctx.error_message,
                )
                await self.db.save(event)

    def _mask_sensitive_data(self, data: Any) -> Any:
        """Mask sensitive fields in data.

        Args:
            data: Data to mask (dict, list, or primitive)

        Returns:
            Data with sensitive fields masked
        """
        if isinstance(data, dict):
            return {
                key: (
                    "***REDACTED***"
                    if key.lower() in self.SENSITIVE_FIELDS
                    else self._mask_sensitive_data(value)
                )
                for key, value in data.items()
            }
        elif isinstance(data, (list, tuple)):
            return [self._mask_sensitive_data(item) for item in data]
        else:
            return data

    def _find_execution_context(
        self, session_id: str, tool_name: str
    ) -> Optional[ToolExecutionContext]:
        """Find the most recent execution context for a tool.

        Args:
            session_id: Session identifier
            tool_name: Tool name

        Returns:
            Execution context if found, None otherwise
        """
        # Find most recent matching execution
        matching_keys = [
            key
            for key in self.active_executions.keys()
            if key.startswith(f"{session_id}:{tool_name}:")
        ]

        if matching_keys:
            # Return most recent (keys are sorted by timestamp)
            latest_key = sorted(matching_keys)[-1]
            return self.active_executions[latest_key]

        return None

    async def get_audit_trail(
        self,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[AuditEvent]:
        """Retrieve audit trail with optional filters.

        Args:
            session_id: Filter by session
            agent_id: Filter by agent
            start_time: Filter by start time
            end_time: Filter by end time

        Returns:
            List of audit events
        """
        if not self.db:
            return []

        return await self.db.query_events(
            session_id=session_id,
            agent_id=agent_id,
            start_time=start_time,
            end_time=end_time,
        )
