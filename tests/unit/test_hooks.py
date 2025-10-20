"""Tests for hook system (audit, permission, metrics).

Test-Driven Development for Week 6 hook implementations.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, call
from datetime import datetime
from typing import Dict, Any

from src.hooks.audit_hooks import AuditHook
from src.hooks.permission_hooks import PermissionHook
from src.hooks.metrics_hooks import MetricsHook


@pytest.fixture
def mock_db():
    """Mock database for audit logging."""
    db = AsyncMock()
    db.save = AsyncMock()
    db.query = AsyncMock()
    return db


@pytest.fixture
def audit_hook(mock_db):
    """Create audit hook instance."""
    return AuditHook(db=mock_db)


@pytest.fixture
def permission_hook():
    """Create permission hook instance."""
    return PermissionHook()


@pytest.fixture
def metrics_hook():
    """Create metrics hook instance."""
    return MetricsHook()


class TestAuditHook:
    """Test audit hook functionality."""

    @pytest.mark.asyncio
    async def test_pre_tool_logs_execution_start(self, audit_hook, mock_db):
        """Test that pre_tool logs tool execution start."""
        tool_name = "zoho_query_accounts"
        tool_input = {"account_id": "ACC-001"}
        context = {"agent_id": "test-agent", "session_id": "sess-123"}

        await audit_hook.pre_tool(tool_name, tool_input, context)

        # Verify database save was called
        mock_db.save.assert_called_once()
        saved_event = mock_db.save.call_args[0][0]

        assert saved_event.event_type == "tool_execution"
        assert saved_event.tool_name == tool_name
        assert saved_event.agent_id == "test-agent"
        assert saved_event.status == "started"
        assert saved_event.tool_input == tool_input

    @pytest.mark.asyncio
    async def test_post_tool_logs_execution_completion(self, audit_hook, mock_db):
        """Test that post_tool logs tool execution completion."""
        tool_name = "zoho_query_accounts"
        tool_output = {"accounts": [{"id": "ACC-001"}]}
        context = {"agent_id": "test-agent", "session_id": "sess-123"}

        await audit_hook.post_tool(tool_name, tool_output, context)

        # Verify database update was called
        mock_db.save.assert_called_once()
        saved_event = mock_db.save.call_args[0][0]

        assert saved_event.event_type == "tool_execution"
        assert saved_event.tool_name == tool_name
        assert saved_event.status == "completed"
        assert saved_event.tool_output == tool_output

    @pytest.mark.asyncio
    async def test_logs_tool_execution_time(self, audit_hook, mock_db):
        """Test that execution time is calculated and logged."""
        tool_name = "test_tool"
        tool_input = {"test": "input"}
        context = {"agent_id": "test-agent"}

        # Start execution
        await audit_hook.pre_tool(tool_name, tool_input, context)
        start_call = mock_db.save.call_args[0][0]

        # Simulate some delay
        import asyncio
        await asyncio.sleep(0.1)

        # End execution
        await audit_hook.post_tool(tool_name, {"result": "success"}, context)
        end_call = mock_db.save.call_args[0][0]

        # Verify execution time was recorded
        assert hasattr(end_call, 'execution_time_ms')
        assert end_call.execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_handles_tool_errors(self, audit_hook, mock_db):
        """Test audit logging of tool errors."""
        tool_name = "failing_tool"
        error = Exception("Tool execution failed")
        context = {"agent_id": "test-agent"}

        await audit_hook.on_tool_error(tool_name, error, context)

        saved_event = mock_db.save.call_args[0][0]
        assert saved_event.status == "failed"
        assert saved_event.error_message == "Tool execution failed"

    @pytest.mark.asyncio
    async def test_masks_sensitive_data(self, audit_hook, mock_db):
        """Test that sensitive data is masked in audit logs."""
        tool_name = "zoho_auth"
        tool_input = {
            "username": "user@example.com",
            "password": "secret123",
            "api_key": "sk-123456",
        }
        context = {"agent_id": "test-agent"}

        await audit_hook.pre_tool(tool_name, tool_input, context)

        saved_event = mock_db.save.call_args[0][0]
        masked_input = saved_event.tool_input

        # Verify sensitive fields are masked
        assert masked_input["username"] == "user@example.com"
        assert masked_input["password"] == "***REDACTED***"
        assert masked_input["api_key"] == "***REDACTED***"


class TestPermissionHook:
    """Test permission hook functionality."""

    @pytest.mark.asyncio
    async def test_enforces_allowed_tools(self, permission_hook):
        """Test that only allowed tools can be executed."""
        allowed_tools = ["tool_a", "tool_b"]
        context = {"allowed_tools": allowed_tools}

        # Allowed tool should pass
        result = await permission_hook.check_tool_permission("tool_a", {}, context)
        assert result is True

        # Disallowed tool should be blocked
        with pytest.raises(PermissionError, match="Tool 'tool_c' not allowed"):
            await permission_hook.check_tool_permission("tool_c", {}, context)

    @pytest.mark.asyncio
    async def test_bypass_permissions_mode(self, permission_hook):
        """Test bypassPermissions mode allows all tools."""
        context = {
            "allowed_tools": ["tool_a"],
            "permission_mode": "bypassPermissions",
        }

        # Any tool should be allowed in bypass mode
        result = await permission_hook.check_tool_permission("tool_x", {}, context)
        assert result is True

    @pytest.mark.asyncio
    async def test_validates_tool_input_schema(self, permission_hook):
        """Test validation of tool input against schema."""
        tool_schemas = {
            "zoho_query": {
                "required": ["account_id"],
                "properties": {
                    "account_id": {"type": "string"},
                    "limit": {"type": "integer"},
                },
            }
        }

        context = {"allowed_tools": ["zoho_query"], "tool_schemas": tool_schemas}

        # Valid input should pass
        valid_input = {"account_id": "ACC-001", "limit": 10}
        result = await permission_hook.check_tool_permission(
            "zoho_query", valid_input, context
        )
        assert result is True

        # Missing required field should fail
        invalid_input = {"limit": 10}  # Missing account_id
        with pytest.raises(ValueError, match="Missing required field: account_id"):
            await permission_hook.check_tool_permission(
                "zoho_query", invalid_input, context
            )

    @pytest.mark.asyncio
    async def test_logs_permission_checks(self, permission_hook):
        """Test that permission checks are logged."""
        context = {"allowed_tools": ["tool_a"], "agent_id": "test-agent"}

        with patch.object(permission_hook.logger, 'info') as mock_log:
            await permission_hook.check_tool_permission("tool_a", {}, context)

            mock_log.assert_called()
            call_args = mock_log.call_args
            assert "permission_check" in str(call_args)


class TestMetricsHook:
    """Test metrics hook functionality."""

    @pytest.mark.asyncio
    async def test_tracks_session_start(self, metrics_hook):
        """Test session start metrics."""
        context = {"agent_id": "test-agent", "session_id": "sess-123"}

        await metrics_hook.on_session_start(context)

        # Verify session metrics were initialized
        assert "sess-123" in metrics_hook.sessions
        session_metrics = metrics_hook.sessions["sess-123"]
        assert session_metrics.agent_id == "test-agent"
        assert session_metrics.start_time is not None

    @pytest.mark.asyncio
    async def test_tracks_session_end(self, metrics_hook):
        """Test session end metrics."""
        context = {"agent_id": "test-agent", "session_id": "sess-123"}

        # Start session
        await metrics_hook.on_session_start(context)

        # End session
        await metrics_hook.on_session_end(context)

        session_metrics = metrics_hook.sessions["sess-123"]
        assert session_metrics.end_time is not None
        assert session_metrics.duration_ms > 0

    @pytest.mark.asyncio
    async def test_tracks_tool_execution_count(self, metrics_hook):
        """Test tracking of tool execution count."""
        context = {"session_id": "sess-123"}

        await metrics_hook.on_session_start(context)

        # Execute multiple tools
        await metrics_hook.on_tool_execution("tool_a", context)
        await metrics_hook.on_tool_execution("tool_b", context)
        await metrics_hook.on_tool_execution("tool_a", context)

        session_metrics = metrics_hook.sessions["sess-123"]
        assert session_metrics.tool_execution_count == 3
        assert session_metrics.tools_used["tool_a"] == 2
        assert session_metrics.tools_used["tool_b"] == 1

    @pytest.mark.asyncio
    async def test_tracks_token_usage(self, metrics_hook):
        """Test tracking of token usage."""
        context = {"session_id": "sess-123"}

        await metrics_hook.on_session_start(context)

        # Track token usage
        await metrics_hook.on_token_usage(
            input_tokens=100,
            output_tokens=50,
            context=context,
        )

        await metrics_hook.on_token_usage(
            input_tokens=200,
            output_tokens=75,
            context=context,
        )

        session_metrics = metrics_hook.sessions["sess-123"]
        assert session_metrics.total_input_tokens == 300
        assert session_metrics.total_output_tokens == 125

    @pytest.mark.asyncio
    async def test_calculates_cost_estimate(self, metrics_hook):
        """Test cost estimation based on token usage."""
        context = {"session_id": "sess-123", "model": "claude-3-5-sonnet-20241022"}

        await metrics_hook.on_session_start(context)

        await metrics_hook.on_token_usage(
            input_tokens=1000,
            output_tokens=500,
            context=context,
        )

        session_metrics = metrics_hook.sessions["sess-123"]
        # Cost calculation: input ($3/MTok) + output ($15/MTok)
        expected_cost = (1000 / 1_000_000 * 3) + (500 / 1_000_000 * 15)
        assert abs(session_metrics.estimated_cost_usd - expected_cost) < 0.0001

    @pytest.mark.asyncio
    async def test_exports_prometheus_metrics(self, metrics_hook):
        """Test export of Prometheus metrics."""
        context = {"session_id": "sess-123", "agent_id": "test-agent"}

        await metrics_hook.on_session_start(context)
        await metrics_hook.on_tool_execution("test_tool", context)
        await metrics_hook.on_session_end(context)

        # Export metrics
        prometheus_metrics = metrics_hook.export_prometheus_metrics()

        # Verify metrics are exported
        assert "agent_session_count" in prometheus_metrics
        assert "agent_tool_executions_total" in prometheus_metrics
        assert "agent_session_duration_seconds" in prometheus_metrics

    @pytest.mark.asyncio
    async def test_tracks_error_rate(self, metrics_hook):
        """Test tracking of error rate."""
        context = {"session_id": "sess-123"}

        await metrics_hook.on_session_start(context)

        # Track successful and failed executions
        await metrics_hook.on_tool_execution("tool_a", context, success=True)
        await metrics_hook.on_tool_execution("tool_b", context, success=False)
        await metrics_hook.on_tool_execution("tool_c", context, success=True)

        session_metrics = metrics_hook.sessions["sess-123"]
        assert session_metrics.successful_executions == 2
        assert session_metrics.failed_executions == 1
        assert session_metrics.error_rate == 1 / 3


class TestHookIntegration:
    """Test integration between hooks."""

    @pytest.mark.asyncio
    async def test_all_hooks_work_together(self, audit_hook, permission_hook, metrics_hook, mock_db):
        """Test that all hooks work together in workflow."""
        tool_name = "test_tool"
        tool_input = {"test": "data"}
        context = {
            "agent_id": "test-agent",
            "session_id": "sess-123",
            "allowed_tools": ["test_tool"],
        }

        # Start session (metrics)
        await metrics_hook.on_session_start(context)

        # Check permission (permission)
        permission_result = await permission_hook.check_tool_permission(
            tool_name, tool_input, context
        )
        assert permission_result is True

        # Log execution start (audit)
        await audit_hook.pre_tool(tool_name, tool_input, context)

        # Track tool execution (metrics)
        await metrics_hook.on_tool_execution(tool_name, context, success=True)

        # Log execution end (audit)
        await audit_hook.post_tool(tool_name, {"result": "success"}, context)

        # End session (metrics)
        await metrics_hook.on_session_end(context)

        # Verify all hooks executed
        assert mock_db.save.call_count == 2  # pre_tool and post_tool
        assert metrics_hook.sessions["sess-123"].tool_execution_count == 1
