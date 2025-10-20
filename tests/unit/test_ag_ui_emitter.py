"""Unit tests for AG UI Protocol event emitter.

Tests all event emission methods with >80% code coverage.

Reference: MASTER_SPARC_PLAN_V3.md lines 1770-1814
Reference: AG_UI_PROTOCOL_Implementation_Requirements.md Section 6.1
"""

import pytest
import time
from datetime import datetime
from unittest.mock import patch

from src.events.ag_ui_emitter import AGUIEventEmitter
from src.events.event_schemas import (
    WorkflowStartedEvent,
    AgentStartedEvent,
    AgentStreamEvent,
    AgentCompletedEvent,
    AgentErrorEvent,
    ApprovalRequiredEvent,
    ToolCallEvent,
    ToolResultEvent,
    StateSnapshotEvent,
)


# ============================================================================
# Workflow Event Tests
# ============================================================================

class TestWorkflowEvents:
    """Test workflow_started and workflow_completed events."""

    def test_emit_workflow_started(self):
        """Test workflow_started event formatting."""
        emitter = AGUIEventEmitter(session_id="test_session_123")
        event = emitter.emit_workflow_started("account_analysis", "ACC-001")

        # Verify event structure
        assert event["type"] == "workflow_started"
        assert "data" in event
        assert "timestamp" in event

        # Verify event data
        data = event["data"]
        assert data["workflow"] == "account_analysis"
        assert data["account_id"] == "ACC-001"
        assert data["session_id"] == "test_session_123"

    def test_emit_workflow_completed(self):
        """Test workflow_completed event with duration tracking."""
        emitter = AGUIEventEmitter(session_id="test_session_456")

        # Simulate workflow execution time
        time.sleep(0.1)  # 100ms

        final_output = {
            "health_score": 85,
            "risk_level": "low",
            "recommendations_count": 3
        }

        event = emitter.emit_workflow_completed(
            "account_analysis",
            "ACC-001",
            final_output=final_output
        )

        # Verify event structure
        assert event["type"] == "workflow_completed"
        assert event["data"]["workflow"] == "account_analysis"
        assert event["data"]["account_id"] == "ACC-001"
        assert event["data"]["session_id"] == "test_session_456"

        # Verify duration tracking (should be >= 100ms)
        assert event["data"]["total_duration_ms"] >= 100

        # Verify final output
        assert event["data"]["final_output"] == final_output

    def test_workflow_started_generates_session_id(self):
        """Test that session_id is auto-generated if not provided."""
        emitter = AGUIEventEmitter()  # No session_id
        event = emitter.emit_workflow_started("daily_review", "ACC-002")

        assert "session_id" in event["data"]
        assert event["data"]["session_id"].startswith("session_")
        assert len(event["data"]["session_id"]) > 8


# ============================================================================
# Agent Event Tests
# ============================================================================

class TestAgentEvents:
    """Test agent lifecycle events."""

    def test_emit_agent_started(self):
        """Test agent_started event with step tracking."""
        emitter = AGUIEventEmitter()
        event = emitter.emit_agent_started(
            agent="zoho_scout",
            step=1,
            task="Fetch account data from Zoho CRM"
        )

        assert event["type"] == "agent_started"
        assert event["data"]["agent"] == "zoho_scout"
        assert event["data"]["step"] == 1
        assert event["data"]["task"] == "Fetch account data from Zoho CRM"

    def test_emit_agent_stream_text(self):
        """Test agent_stream event with text content."""
        emitter = AGUIEventEmitter()
        event = emitter.emit_agent_stream(
            agent="memory_analyst",
            content="Analyzing historical account interactions...",
            content_type="text"
        )

        assert event["type"] == "agent_stream"
        assert event["data"]["agent"] == "memory_analyst"
        assert event["data"]["content"] == "Analyzing historical account interactions..."
        assert event["data"]["content_type"] == "text"

    def test_emit_agent_stream_tool_call(self):
        """Test agent_stream event with tool_call content."""
        emitter = AGUIEventEmitter()
        event = emitter.emit_agent_stream(
            agent="zoho_scout",
            content="Calling get_account_details tool",
            content_type="tool_call"
        )

        assert event["data"]["content_type"] == "tool_call"

    def test_emit_agent_completed_with_duration(self):
        """Test agent_completed event tracks execution time."""
        emitter = AGUIEventEmitter()

        # Start agent
        emitter.emit_agent_started(agent="recommendation_author", step=3)

        # Simulate agent work
        time.sleep(0.05)  # 50ms

        # Complete agent
        output = {
            "recommendations": [
                {"action": "schedule_followup", "priority": "high"}
            ]
        }
        event = emitter.emit_agent_completed(
            agent="recommendation_author",
            step=3,
            output=output
        )

        assert event["type"] == "agent_completed"
        assert event["data"]["agent"] == "recommendation_author"
        assert event["data"]["step"] == 3
        assert event["data"]["duration_ms"] >= 50
        assert event["data"]["output"] == output

    def test_emit_agent_completed_without_prior_start(self):
        """Test agent_completed works even without prior agent_started."""
        emitter = AGUIEventEmitter()

        # Complete agent without starting it first
        event = emitter.emit_agent_completed(
            agent="test_agent",
            step=1
        )

        # Should still work, duration will be small
        assert event["type"] == "agent_completed"
        assert "duration_ms" in event["data"]

    def test_emit_agent_error(self):
        """Test agent_error event with error details."""
        emitter = AGUIEventEmitter()

        error_stack = """
        Traceback (most recent call last):
          File "agent.py", line 42
            raise ValueError("Invalid account ID")
        ValueError: Invalid account ID
        """

        event = emitter.emit_agent_error(
            agent="zoho_scout",
            step=1,
            error_type="ValueError",
            error_message="Invalid account ID: must start with 'ACC-'",
            stack_trace=error_stack.strip()
        )

        assert event["type"] == "agent_error"
        assert event["data"]["agent"] == "zoho_scout"
        assert event["data"]["step"] == 1
        assert event["data"]["error_type"] == "ValueError"
        assert event["data"]["error_message"] == "Invalid account ID: must start with 'ACC-'"
        assert "Traceback" in event["data"]["stack_trace"]


# ============================================================================
# Approval Event Tests
# ============================================================================

class TestApprovalEvents:
    """Test approval_required event."""

    def test_emit_approval_required(self):
        """Test approval_required event with recommendation data."""
        emitter = AGUIEventEmitter()

        recommendation = {
            "recommendation_id": "REC-789",
            "account_id": "ACC-001",
            "recommendation_type": "follow_up",
            "action": "Schedule quarterly business review",
            "rationale": "Account shows strong engagement and expansion opportunity",
            "confidence_score": 0.87,
            "priority": "high",
            "estimated_impact": "Potential $50K expansion deal",
            "data": {
                "suggested_date": "2025-11-15",
                "attendees": ["VP Engineering", "Account Manager"]
            }
        }

        event = emitter.emit_approval_required(
            recommendation=recommendation,
            timeout_hours=48
        )

        assert event["type"] == "approval_required"
        assert event["data"]["recommendation"]["recommendation_id"] == "REC-789"
        assert event["data"]["recommendation"]["account_id"] == "ACC-001"
        assert event["data"]["recommendation"]["action"] == "Schedule quarterly business review"
        assert event["data"]["recommendation"]["confidence_score"] == 0.87
        assert event["data"]["timeout_hours"] == 48

    def test_approval_required_default_timeout(self):
        """Test approval_required uses default 72 hour timeout."""
        emitter = AGUIEventEmitter()

        recommendation = {
            "recommendation_id": "REC-123",
            "account_id": "ACC-002",
            "recommendation_type": "upsell",
            "action": "Propose enterprise tier upgrade",
            "rationale": "Usage metrics indicate need for higher limits",
            "confidence_score": 0.75,
            "priority": "medium"
        }

        event = emitter.emit_approval_required(recommendation=recommendation)

        assert event["data"]["timeout_hours"] == 72  # Default


# ============================================================================
# Tool Event Tests
# ============================================================================

class TestToolEvents:
    """Test tool_call and tool_result events."""

    def test_emit_tool_call(self):
        """Test tool_call event with arguments."""
        emitter = AGUIEventEmitter()

        tool_args = {
            "account_id": "ACC-001",
            "include_contacts": True,
            "include_deals": True
        }

        event = emitter.emit_tool_call(
            tool_name="zoho_get_account",
            tool_args=tool_args,
            tool_call_id="tool_abc123"
        )

        assert event["type"] == "tool_call"
        assert event["data"]["tool_name"] == "zoho_get_account"
        assert event["data"]["tool_args"] == tool_args
        assert event["data"]["tool_call_id"] == "tool_abc123"

    def test_emit_tool_call_auto_generates_id(self):
        """Test tool_call auto-generates call ID if not provided."""
        emitter = AGUIEventEmitter()

        event = emitter.emit_tool_call(
            tool_name="cognee_search",
            tool_args={"query": "similar accounts"}
        )

        assert "tool_call_id" in event["data"]
        assert event["data"]["tool_call_id"].startswith("tool_")

    def test_emit_tool_result_success(self):
        """Test tool_result event for successful execution."""
        emitter = AGUIEventEmitter()

        result = {
            "account": {
                "id": "ACC-001",
                "name": "Acme Corp",
                "revenue": 5000000
            },
            "contacts": [
                {"id": "CONT-1", "name": "John Doe"}
            ]
        }

        event = emitter.emit_tool_result(
            tool_call_id="tool_abc123",
            tool_name="zoho_get_account",
            result=result,
            success=True
        )

        assert event["type"] == "tool_result"
        assert event["data"]["tool_call_id"] == "tool_abc123"
        assert event["data"]["tool_name"] == "zoho_get_account"
        assert event["data"]["result"] == result
        assert event["data"]["success"] is True
        assert event["data"]["error"] is None

    def test_emit_tool_result_failure(self):
        """Test tool_result event for failed execution."""
        emitter = AGUIEventEmitter()

        event = emitter.emit_tool_result(
            tool_call_id="tool_def456",
            tool_name="zoho_get_account",
            result=None,
            success=False,
            error="Rate limit exceeded (429)"
        )

        assert event["data"]["success"] is False
        assert event["data"]["error"] == "Rate limit exceeded (429)"


# ============================================================================
# State Snapshot Tests
# ============================================================================

class TestStateSnapshotEvents:
    """Test state_snapshot events."""

    def test_emit_state_snapshot(self):
        """Test state_snapshot event with agent states."""
        emitter = AGUIEventEmitter(session_id="session_xyz")

        agent_states = {
            "zoho_scout": {
                "status": "completed",
                "progress": 100,
                "output_summary": "Fetched account and 3 contacts"
            },
            "memory_analyst": {
                "status": "running",
                "progress": 60,
                "current_task": "Analyzing interaction patterns"
            },
            "recommendation_author": {
                "status": "pending",
                "progress": 0
            }
        }

        context = {
            "account_id": "ACC-001",
            "workflow_start_time": "2025-10-19T10:00:00Z",
            "total_tools_called": 5
        }

        event = emitter.emit_state_snapshot(
            workflow="account_analysis",
            current_step=2,
            total_steps=3,
            agent_states=agent_states,
            context=context
        )

        assert event["type"] == "state_snapshot"
        assert event["data"]["session_id"] == "session_xyz"
        assert event["data"]["workflow"] == "account_analysis"
        assert event["data"]["current_step"] == 2
        assert event["data"]["total_steps"] == 3
        assert event["data"]["agent_states"] == agent_states
        assert event["data"]["context"] == context


# ============================================================================
# SSE Formatting Tests
# ============================================================================

class TestSSEFormatting:
    """Test Server-Sent Events formatting."""

    def test_format_sse_event(self):
        """Test SSE format for events."""
        emitter = AGUIEventEmitter()

        event = {
            "type": "agent_started",
            "timestamp": "2025-10-19T10:00:00Z",
            "data": {
                "agent": "zoho_scout",
                "step": 1
            }
        }

        sse_formatted = emitter.format_sse_event(event)

        # SSE format: data: {json}\n\n
        assert sse_formatted.startswith("data: {")
        assert sse_formatted.endswith("}\n\n")
        assert '"type": "agent_started"' in sse_formatted
        assert '"agent": "zoho_scout"' in sse_formatted

    @pytest.mark.asyncio
    async def test_stream_events(self):
        """Test streaming events in SSE format."""
        emitter = AGUIEventEmitter()

        # Create async generator of events
        async def event_generator():
            # Convert events to JSON-serializable format
            import json
            from datetime import datetime

            def make_serializable(event):
                # Convert datetime objects to ISO strings
                if 'timestamp' in event:
                    event['timestamp'] = event['timestamp'].isoformat() if isinstance(event['timestamp'], datetime) else event['timestamp']
                return event

            yield make_serializable(emitter.emit_workflow_started("test_workflow", "ACC-001"))
            yield make_serializable(emitter.emit_agent_started("test_agent", 1))
            yield make_serializable(emitter.emit_agent_completed("test_agent", 1))
            yield make_serializable(emitter.emit_workflow_completed("test_workflow", "ACC-001"))

        # Stream events in SSE format
        sse_events = []
        async for sse_event in emitter.stream_events(event_generator()):
            sse_events.append(sse_event)

        # Verify we got 4 SSE formatted events
        assert len(sse_events) == 4

        # Verify each is properly formatted
        for sse_event in sse_events:
            assert sse_event.startswith("data: ")
            assert sse_event.endswith("\n\n")


# ============================================================================
# Integration Tests
# ============================================================================

class TestEventEmitterIntegration:
    """Test complete event emission workflows."""

    def test_complete_workflow_event_sequence(self):
        """Test complete sequence of events for account analysis workflow."""
        emitter = AGUIEventEmitter(session_id="integration_test_123")

        events = []

        # 1. Workflow starts
        events.append(emitter.emit_workflow_started("account_analysis", "ACC-001"))

        # 2. Agent 1: Zoho Scout
        events.append(emitter.emit_agent_started("zoho_scout", 1, "Fetch account data"))
        events.append(emitter.emit_tool_call("zoho_get_account", {"account_id": "ACC-001"}))
        events.append(emitter.emit_tool_result(
            "tool_1",
            "zoho_get_account",
            {"account": {"id": "ACC-001", "name": "Acme"}},
            success=True
        ))
        events.append(emitter.emit_agent_completed("zoho_scout", 1))

        # 3. Agent 2: Memory Analyst
        events.append(emitter.emit_agent_started("memory_analyst", 2))
        events.append(emitter.emit_agent_stream("memory_analyst", "Analyzing patterns..."))
        events.append(emitter.emit_agent_completed("memory_analyst", 2))

        # 4. Agent 3: Recommendation Author
        events.append(emitter.emit_agent_started("recommendation_author", 3))
        recommendation = {
            "recommendation_id": "REC-001",
            "account_id": "ACC-001",
            "recommendation_type": "follow_up",
            "action": "Schedule call",
            "rationale": "High engagement",
            "confidence_score": 0.9,
            "priority": "high"
        }
        events.append(emitter.emit_approval_required(recommendation))
        events.append(emitter.emit_agent_completed("recommendation_author", 3))

        # 5. Workflow completes
        events.append(emitter.emit_workflow_completed(
            "account_analysis",
            "ACC-001",
            final_output={"status": "success", "recommendations": 1}
        ))

        # Verify event count
        assert len(events) == 12

        # Verify event types in order
        expected_types = [
            "workflow_started",
            "agent_started",
            "tool_call",
            "tool_result",
            "agent_completed",
            "agent_started",
            "agent_stream",
            "agent_completed",
            "agent_started",
            "approval_required",
            "agent_completed",
            "workflow_completed"
        ]

        actual_types = [event["type"] for event in events]
        assert actual_types == expected_types

    def test_error_handling_workflow(self):
        """Test workflow with agent error."""
        emitter = AGUIEventEmitter()

        events = []

        # Start workflow
        events.append(emitter.emit_workflow_started("account_analysis", "ACC-999"))

        # Agent starts
        events.append(emitter.emit_agent_started("zoho_scout", 1))

        # Agent encounters error
        events.append(emitter.emit_agent_error(
            agent="zoho_scout",
            step=1,
            error_type="AccountNotFoundError",
            error_message="Account ACC-999 does not exist"
        ))

        # Workflow completes with error
        events.append(emitter.emit_workflow_completed(
            "account_analysis",
            "ACC-999",
            final_output={"status": "error", "error": "Account not found"}
        ))

        # Verify error event was emitted
        assert any(e["type"] == "agent_error" for e in events)
        error_event = next(e for e in events if e["type"] == "agent_error")
        assert error_event["data"]["error_type"] == "AccountNotFoundError"


# ============================================================================
# Performance Tests
# ============================================================================

class TestEventEmitterPerformance:
    """Test event emitter performance characteristics."""

    def test_session_id_generation_performance(self):
        """Test session ID generation is fast."""
        start = time.time()

        for _ in range(1000):
            emitter = AGUIEventEmitter()
            assert emitter.session_id is not None

        duration = time.time() - start

        # Should generate 1000 session IDs in <100ms
        assert duration < 0.1

    def test_event_emission_performance(self):
        """Test event emission is fast."""
        emitter = AGUIEventEmitter()

        start = time.time()

        # Emit 1000 events
        for i in range(1000):
            emitter.emit_agent_stream("test_agent", f"Message {i}")

        duration = time.time() - start

        # Should emit 1000 events in <100ms
        assert duration < 0.1


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_recommendation_data(self):
        """Test approval_required with minimal recommendation data."""
        emitter = AGUIEventEmitter()

        minimal_recommendation = {
            "recommendation_id": "REC-MIN",
            "account_id": "ACC-MIN",
            "recommendation_type": "test",
            "action": "test action",
            "rationale": "test rationale",
            "confidence_score": 0.5,
            "priority": "low"
        }

        event = emitter.emit_approval_required(minimal_recommendation)

        assert event["type"] == "approval_required"
        assert event["data"]["recommendation"]["recommendation_id"] == "REC-MIN"

    def test_very_long_content_stream(self):
        """Test agent_stream with very long content."""
        emitter = AGUIEventEmitter()

        long_content = "A" * 10000  # 10KB content

        event = emitter.emit_agent_stream("test_agent", long_content)

        assert event["data"]["content"] == long_content
        assert len(event["data"]["content"]) == 10000

    def test_unicode_content(self):
        """Test events handle Unicode content correctly."""
        emitter = AGUIEventEmitter()

        unicode_content = "Hello 世界 🚀 émojis and spëcial chârs"

        event = emitter.emit_agent_stream("test_agent", unicode_content)

        assert event["data"]["content"] == unicode_content

    def test_none_values_handled(self):
        """Test events handle None values gracefully."""
        emitter = AGUIEventEmitter()

        # Agent completed without output
        event = emitter.emit_agent_completed("test_agent", 1, output=None)

        assert event["data"]["output"] is None

        # Tool result without error
        event = emitter.emit_tool_result(
            "tool_1",
            "test_tool",
            result={},
            success=True,
            error=None
        )

        assert event["data"]["error"] is None
