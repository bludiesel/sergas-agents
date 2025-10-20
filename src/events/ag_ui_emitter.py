"""AG UI Protocol event emitter for multi-agent workflows.

This module provides event emission functionality for streaming
agent execution via AG UI Protocol (Server-Sent Events).

Reference: MASTER_SPARC_PLAN_V3.md lines 1770-1814
"""

import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, AsyncGenerator
import structlog

from src.events.event_schemas import (
    WorkflowStartedEvent,
    WorkflowStartedEventData,
    WorkflowCompletedEvent,
    WorkflowCompletedEventData,
    AgentStartedEvent,
    AgentStartedEventData,
    AgentStreamEvent,
    AgentStreamEventData,
    AgentCompletedEvent,
    AgentCompletedEventData,
    AgentErrorEvent,
    AgentErrorEventData,
    ApprovalRequiredEvent,
    ApprovalRequiredEventData,
    RecommendationData,
    ToolCallEvent,
    ToolCallEventData,
    ToolResultEvent,
    ToolResultEventData,
    StateSnapshotEvent,
    StateSnapshotEventData,
)

logger = structlog.get_logger(__name__)


class AGUIEventEmitter:
    """Emit AG UI Protocol events for streaming agent execution.

    Provides methods to emit all AG UI Protocol event types:
    - workflow_started / workflow_completed
    - agent_started / agent_stream / agent_completed / agent_error
    - approval_required
    - tool_call / tool_result
    - state_snapshot

    Example:
        emitter = AGUIEventEmitter(session_id="session_123")
        event = emitter.emit_workflow_started("account_analysis", "ACC-001")
        # Event ready for SSE streaming
    """

    def __init__(self, session_id: Optional[str] = None):
        """Initialize AG UI event emitter.

        Args:
            session_id: Optional session identifier. If not provided, one will be generated.
        """
        self.session_id = session_id or self._generate_session_id()
        self.start_time = time.time()
        self.step_timers: Dict[str, float] = {}

        self.logger = logger.bind(session_id=self.session_id)
        self.logger.info("ag_ui_emitter_initialized")

    @staticmethod
    def _generate_session_id() -> str:
        """Generate unique session ID."""
        return f"session_{uuid.uuid4().hex[:12]}"

    def _elapsed_ms(self, start_time: Optional[float] = None) -> int:
        """Calculate elapsed time in milliseconds.

        Args:
            start_time: Start timestamp. If None, uses emitter start_time.

        Returns:
            Elapsed time in milliseconds
        """
        start = start_time or self.start_time
        return int((time.time() - start) * 1000)
    # ========================================================================
    # Workflow Events
    # ========================================================================

    def emit_workflow_started(
        self,
        workflow: str,
        account_id: str
    ) -> Dict[str, Any]:
        """Emit workflow_started event.

        Args:
            workflow: Workflow type (e.g., "account_analysis")
            account_id: Account identifier

        Returns:
            AG UI event dictionary ready for SSE streaming
        """
        event = WorkflowStartedEvent(
            data=WorkflowStartedEventData(
                workflow=workflow,
                account_id=account_id,
                session_id=self.session_id
            )
        )

        self.logger.info(
            "workflow_started",
            workflow=workflow,
            account_id=account_id
        )

        return event.model_dump()

    def emit_workflow_completed(
        self,
        workflow: str,
        account_id: str,
        final_output: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Emit workflow_completed event.

        Args:
            workflow: Workflow type
            account_id: Account identifier
            final_output: Optional final workflow results

        Returns:
            AG UI event dictionary
        """
        duration_ms = self._elapsed_ms()

        event = WorkflowCompletedEvent(
            data=WorkflowCompletedEventData(
                workflow=workflow,
                account_id=account_id,
                session_id=self.session_id,
                total_duration_ms=duration_ms,
                final_output=final_output
            )
        )

        self.logger.info(
            "workflow_completed",
            workflow=workflow,
            account_id=account_id,
            duration_ms=duration_ms
        )

        return event.model_dump()

    # ========================================================================
    # Agent Events
    # ========================================================================

    def emit_agent_started(
        self,
        agent: str,
        step: int,
        task: Optional[str] = None
    ) -> Dict[str, Any]:
        """Emit agent_started event.

        Args:
            agent: Agent identifier (e.g., "zoho_scout")
            step: Step number in workflow
            task: Optional task description

        Returns:
            AG UI event dictionary
        """
        # Track agent start time for duration calculation
        self.step_timers[f"{agent}_{step}"] = time.time()

        event = AgentStartedEvent(
            data=AgentStartedEventData(
                agent=agent,
                step=step,
                task=task
            )
        )

        self.logger.info(
            "agent_started",
            agent=agent,
            step=step
        )

        return event.model_dump()

    def emit_agent_stream(
        self,
        agent: str,
        content: str,
        content_type: str = "text"
    ) -> Dict[str, Any]:
        """Emit agent_stream event with streamed content.

        Args:
            agent: Agent identifier
            content: Streamed content
            content_type: Type of content ("text", "tool_call", "tool_result")

        Returns:
            AG UI event dictionary
        """
        event = AgentStreamEvent(
            data=AgentStreamEventData(
                agent=agent,
                content=content,
                content_type=content_type  # type: ignore
            )
        )

        return event.model_dump()

    def emit_agent_completed(
        self,
        agent: str,
        step: int,
        output: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Emit agent_completed event.

        Args:
            agent: Agent identifier
            step: Step number
            output: Optional agent output data

        Returns:
            AG UI event dictionary
        """
        # Calculate agent execution duration
        timer_key = f"{agent}_{step}"
        start_time = self.step_timers.get(timer_key, time.time())
        duration_ms = self._elapsed_ms(start_time)

        event = AgentCompletedEvent(
            data=AgentCompletedEventData(
                agent=agent,
                step=step,
                duration_ms=duration_ms,
                output=output
            )
        )

        self.logger.info(
            "agent_completed",
            agent=agent,
            step=step,
            duration_ms=duration_ms
        )

        return event.model_dump()

    def emit_agent_error(
        self,
        agent: str,
        step: int,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Emit agent_error event.

        Args:
            agent: Agent identifier
            step: Step number where error occurred
            error_type: Error classification
            error_message: Human-readable error message
            stack_trace: Optional stack trace for debugging

        Returns:
            AG UI event dictionary
        """
        event = AgentErrorEvent(
            data=AgentErrorEventData(
                agent=agent,
                step=step,
                error_type=error_type,
                error_message=error_message,
                stack_trace=stack_trace
            )
        )

        self.logger.error(
            "agent_error",
            agent=agent,
            step=step,
            error_type=error_type,
            error_message=error_message
        )

        return event.model_dump()

    # ========================================================================
    # Approval Events
    # ========================================================================

    def emit_approval_required(
        self,
        recommendation: Dict[str, Any],
        timeout_hours: int = 72
    ) -> Dict[str, Any]:
        """Emit approval_required event.

        Args:
            recommendation: Recommendation data requiring approval
            timeout_hours: Hours until auto-rejection

        Returns:
            AG UI event dictionary
        """
        # Build RecommendationData from dict
        rec_data = RecommendationData(**recommendation)

        event = ApprovalRequiredEvent(
            data=ApprovalRequiredEventData(
                recommendation=rec_data,
                timeout_hours=timeout_hours
            )
        )

        self.logger.info(
            "approval_required",
            recommendation_id=rec_data.recommendation_id,
            account_id=rec_data.account_id,
            timeout_hours=timeout_hours
        )

        return event.model_dump()

    # ========================================================================
    # Tool Events
    # ========================================================================

    def emit_tool_call(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        tool_call_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Emit tool_call event.

        Args:
            tool_name: Name of the tool being called
            tool_args: Tool arguments
            tool_call_id: Optional unique identifier for this call

        Returns:
            AG UI event dictionary
        """
        call_id = tool_call_id or f"tool_{uuid.uuid4().hex[:8]}"

        event = ToolCallEvent(
            data=ToolCallEventData(
                tool_name=tool_name,
                tool_args=tool_args,
                tool_call_id=call_id
            )
        )

        self.logger.debug(
            "tool_call",
            tool_name=tool_name,
            tool_call_id=call_id
        )

        return event.model_dump()

    def emit_tool_result(
        self,
        tool_call_id: str,
        tool_name: str,
        result: Any,
        success: bool = True,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Emit tool_result event.

        Args:
            tool_call_id: Tool call identifier
            tool_name: Tool name
            result: Tool execution result
            success: Whether tool call succeeded
            error: Optional error message if failed

        Returns:
            AG UI event dictionary
        """
        event = ToolResultEvent(
            data=ToolResultEventData(
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                result=result,
                success=success,
                error=error
            )
        )

        self.logger.debug(
            "tool_result",
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            success=success
        )

        return event.model_dump()

    # ========================================================================
    # State Snapshot Events
    # ========================================================================

    def emit_state_snapshot(
        self,
        workflow: str,
        current_step: int,
        total_steps: int,
        agent_states: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Emit state_snapshot event.

        Args:
            workflow: Workflow type
            current_step: Current step number
            total_steps: Total number of steps
            agent_states: Current state of each agent
            context: Optional workflow context

        Returns:
            AG UI event dictionary
        """
        event = StateSnapshotEvent(
            data=StateSnapshotEventData(
                session_id=self.session_id,
                workflow=workflow,
                current_step=current_step,
                total_steps=total_steps,
                agent_states=agent_states,
                context=context or {}
            )
        )

        self.logger.debug(
            "state_snapshot",
            workflow=workflow,
            current_step=current_step,
            total_steps=total_steps
        )

        return event.model_dump()

    # ========================================================================
    # SSE Formatting
    # ========================================================================

    @staticmethod
    def format_sse_event(event: Dict[str, Any]) -> str:
        """Format event as Server-Sent Event (SSE).

        Args:
            event: AG UI event dictionary

        Returns:
            SSE formatted string
        """
        import json

        # Convert datetime objects to ISO format strings
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        # SSE format: data: {json}\n\n
        event_json = json.dumps(event, default=serialize_datetime)
        return f"data: {event_json}\n\n"

    async def stream_events(
        self,
        events: AsyncGenerator[Dict[str, Any], None]
    ) -> AsyncGenerator[str, None]:
        """Stream events in SSE format.

        Args:
            events: Async generator of AG UI events

        Yields:
            SSE formatted event strings
        """
        async for event in events:
            yield self.format_sse_event(event)
