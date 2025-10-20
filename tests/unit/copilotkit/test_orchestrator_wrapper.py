"""
Unit tests for OrchestratorAgent LangGraph wrapper.

Tests the LangGraph wrapper without requiring full integration setup.
"""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch


def test_orchestrator_state_structure():
    """Test OrchestratorState TypedDict structure."""
    from src.copilotkit.agents.orchestrator_wrapper import OrchestratorState
    from typing import get_type_hints

    # Get type hints
    hints = get_type_hints(OrchestratorState)

    # Verify required fields
    assert "messages" in hints, "State should have messages field"

    # Verify optional fields exist
    optional_fields = [
        "account_id",
        "session_id",
        "workflow",
        "account_data",
        "historical_context",
        "recommendations",
        "approval_status",
        "workflow_status",
        "error",
        "event_stream"
    ]

    for field in optional_fields:
        assert field in hints, f"State should have {field} field"


def test_create_orchestrator_graph():
    """Test graph creation without full execution."""
    from src.copilotkit.agents.orchestrator_wrapper import create_orchestrator_graph

    # Create graph
    graph = create_orchestrator_graph()

    # Verify graph was created
    assert graph is not None, "Graph should be created"

    # Verify graph has nodes (LangGraph StateGraph structure)
    # Note: Cannot directly inspect nodes without importing LangGraph internals
    # Just verify it's callable
    assert hasattr(graph, "ainvoke"), "Graph should have ainvoke method"


def test_format_orchestration_summary():
    """Test orchestration summary formatting."""
    from src.copilotkit.agents.orchestrator_wrapper import _format_orchestration_summary

    final_output = {
        "status": "completed",
        "account_id": "ACC-001",
        "execution_summary": {
            "zoho_data_fetched": True,
            "historical_context_retrieved": True,
            "recommendations_generated": 2,
            "risk_level": "medium",
            "sentiment_trend": "stable"
        },
        "approval": {
            "status": "approved"
        }
    }

    agent_messages = [
        "Fetched account data",
        "Retrieved historical context",
        "Generated recommendations"
    ]

    summary = _format_orchestration_summary(final_output, agent_messages)

    # Verify summary structure
    assert "ACC-001" in summary
    assert "completed" in summary
    assert "Zoho Data: ✓" in summary
    assert "Historical Context: ✓" in summary
    assert "Recommendations: 2" in summary
    assert "Risk Level: medium" in summary
    assert "Sentiment: stable" in summary
    assert "Approval Status: approved" in summary


def test_format_recommendations():
    """Test recommendation formatting."""
    from src.copilotkit.agents.orchestrator_wrapper import _format_recommendations

    recommendations = [
        {
            "action_type": "follow_up_call",
            "priority": "high",
            "reasoning": "Customer engagement declining",
            "expected_impact": "Improve relationship"
        },
        {
            "action_type": "schedule_meeting",
            "priority": "medium",
            "reasoning": "Quarterly review pending",
            "expected_impact": "Maintain account health"
        }
    ]

    formatted = _format_recommendations(recommendations)

    # Verify formatting
    assert "1. follow_up_call" in formatted
    assert "Priority: high" in formatted
    assert "Customer engagement declining" in formatted
    assert "2. schedule_meeting" in formatted
    assert "Priority: medium" in formatted


def test_should_request_approval_with_high_priority():
    """Test approval routing with high priority recommendations."""
    from src.copilotkit.agents.orchestrator_wrapper import should_request_approval

    state = {
        "recommendations": [
            {"priority": "high", "action_type": "test"}
        ]
    }

    result = should_request_approval(state)
    assert result == "approval", "Should request approval for high priority"


def test_should_request_approval_with_low_priority():
    """Test approval routing with low priority recommendations."""
    from src.copilotkit.agents.orchestrator_wrapper import should_request_approval

    state = {
        "recommendations": [
            {"priority": "low", "action_type": "test"}
        ]
    }

    result = should_request_approval(state)
    assert result == "end", "Should skip approval for low priority"


def test_should_request_approval_with_no_recommendations():
    """Test approval routing with no recommendations."""
    from src.copilotkit.agents.orchestrator_wrapper import should_request_approval

    state = {
        "recommendations": []
    }

    result = should_request_approval(state)
    assert result == "end", "Should skip approval with no recommendations"


def test_should_request_approval_with_critical_priority():
    """Test approval routing with critical priority recommendations."""
    from src.copilotkit.agents.orchestrator_wrapper import should_request_approval

    state = {
        "recommendations": [
            {"priority": "critical", "action_type": "test"}
        ]
    }

    result = should_request_approval(state)
    assert result == "approval", "Should request approval for critical priority"


@pytest.mark.asyncio
async def test_orchestrator_node_error_handling():
    """Test orchestrator node error handling."""
    from src.copilotkit.agents.orchestrator_wrapper import orchestrator_node
    from langchain_core.messages import HumanMessage

    # State with no account_id
    state = {
        "messages": [HumanMessage(content="Analyze something")],
        "session_id": "test_session"
    }

    # Should handle missing account_id gracefully
    result = await orchestrator_node(state)

    assert "error" in result or "workflow_status" in result
    assert result.get("workflow_status") == "error" or result.get("error") is not None


@pytest.mark.asyncio
async def test_approval_node_with_no_recommendations():
    """Test approval node with no recommendations."""
    from src.copilotkit.agents.orchestrator_wrapper import approval_node
    from langchain_core.messages import HumanMessage

    state = {
        "messages": [HumanMessage(content="Test")],
        "recommendations": []
    }

    result = await approval_node(state)

    assert result["approval_status"] == "no_recommendations"
    assert len(result["messages"]) > len(state["messages"])


@pytest.mark.asyncio
async def test_approval_node_with_recommendations():
    """Test approval node with recommendations."""
    from src.copilotkit.agents.orchestrator_wrapper import approval_node
    from langchain_core.messages import HumanMessage

    state = {
        "messages": [HumanMessage(content="Test")],
        "recommendations": [
            {
                "action_type": "test_action",
                "priority": "high",
                "reasoning": "Test reasoning",
                "expected_impact": "Test impact"
            }
        ]
    }

    result = await approval_node(state)

    assert result["approval_status"] == "pending_approval"
    assert len(result["messages"]) > len(state["messages"])
    # Check message contains recommendation info
    last_message = result["messages"][-1]
    assert "1 recommendations" in last_message.content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
