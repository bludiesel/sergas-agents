"""Pytest fixtures and utilities for CopilotKit wrapper tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
from datetime import datetime


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for LLM calls."""
    client = MagicMock()
    client.messages.create = AsyncMock(return_value=MagicMock(
        content=[MagicMock(text="Test response")],
        usage=MagicMock(input_tokens=100, output_tokens=50)
    ))
    return client


@pytest.fixture
def mock_zoho_manager():
    """Mock ZohoIntegrationManager for data operations."""
    manager = MagicMock()
    manager.get_account = AsyncMock(return_value={
        "id": "acc_001",
        "Account_Name": "Test Account",
        "Account_Status": "Active",
        "Owner": {"id": "owner_001", "name": "John Doe"},
        "Annual_Revenue": 1000000
    })
    manager.search_records = AsyncMock(return_value=[
        {"id": "deal_001", "Stage": "Negotiation", "Amount": 50000}
    ])
    return manager


@pytest.fixture
def mock_cognee_client():
    """Mock Cognee client for memory operations."""
    client = MagicMock()
    client.add = AsyncMock(return_value={"status": "success"})
    client.search = AsyncMock(return_value={
        "results": [
            {
                "id": "mem_001",
                "content": "Historical account interaction",
                "metadata": {"account_id": "acc_001"},
                "score": 0.85
            }
        ]
    })
    return client


@pytest.fixture
def mock_approval_manager():
    """Mock ApprovalManager for HITL workflows."""
    manager = MagicMock()
    manager.request_approval = AsyncMock(return_value={
        "approval_id": "appr_001",
        "status": "pending"
    })
    manager.wait_for_approval = AsyncMock(return_value={
        "status": "approved",
        "approved_by": "user_123"
    })
    return manager


@pytest.fixture
def sample_account_data() -> Dict[str, Any]:
    """Sample account data for testing."""
    return {
        "id": "acc_test_001",
        "Account_Name": "Test Corporation",
        "Account_Status": "Active",
        "Owner": {
            "id": "owner_001",
            "name": "John Doe",
            "email": "john@example.com"
        },
        "Annual_Revenue": 1000000,
        "Industry": "Technology",
        "Created_Time": "2024-01-01T00:00:00Z",
        "Modified_Time": "2025-10-19T10:00:00Z",
        "Last_Activity_Time": "2025-10-15T14:30:00Z"
    }


@pytest.fixture
def sample_deal_data() -> List[Dict[str, Any]]:
    """Sample deal data for testing."""
    return [
        {
            "id": "deal_001",
            "Deal_Name": "Q4 Enterprise Deal",
            "Stage": "Negotiation",
            "Amount": 75000,
            "Probability": 75,
            "Close_Date": "2025-12-31",
            "Account_Name": {"id": "acc_test_001", "name": "Test Corporation"}
        },
        {
            "id": "deal_002",
            "Deal_Name": "Renewal Contract",
            "Stage": "Proposal",
            "Amount": 50000,
            "Probability": 60,
            "Close_Date": "2025-11-30",
            "Account_Name": {"id": "acc_test_001", "name": "Test Corporation"}
        }
    ]


@pytest.fixture
def sample_activity_data() -> List[Dict[str, Any]]:
    """Sample activity data for testing."""
    return [
        {
            "id": "activity_001",
            "Activity_Type": "Meeting",
            "Subject": "Quarterly Business Review",
            "Created_Time": "2025-10-15T14:00:00Z",
            "Owner": {"id": "owner_001", "name": "John Doe"}
        },
        {
            "id": "activity_002",
            "Activity_Type": "Call",
            "Subject": "Follow-up on proposal",
            "Created_Time": "2025-10-10T10:30:00Z",
            "Owner": {"id": "owner_001", "name": "John Doe"}
        }
    ]


@pytest.fixture
def sample_memory_context() -> Dict[str, Any]:
    """Sample memory context for testing."""
    return {
        "account_id": "acc_test_001",
        "historical_interactions": [
            {
                "date": "2025-09-15",
                "type": "meeting",
                "summary": "Discussed pricing concerns"
            },
            {
                "date": "2025-08-20",
                "type": "email",
                "summary": "Requested product demo"
            }
        ],
        "patterns": {
            "engagement_trend": "increasing",
            "risk_level": "low",
            "opportunity_score": 0.78
        }
    }


@pytest.fixture
def sample_recommendation() -> Dict[str, Any]:
    """Sample recommendation for testing."""
    return {
        "recommendation_id": "rec_001",
        "type": "follow_up",
        "title": "Schedule follow-up call",
        "description": "Follow up on pricing discussion from last meeting",
        "priority": "high",
        "confidence_score": 0.85,
        "rationale": "Account showed strong interest but had pricing concerns",
        "suggested_actions": [
            "Schedule call within 3 days",
            "Prepare pricing alternatives",
            "Include ROI calculator"
        ]
    }


@pytest.fixture
def mock_langgraph_state():
    """Mock LangGraph state dictionary."""
    return {
        "messages": [],
        "account_id": "acc_test_001",
        "zoho_data": None,
        "memory_context": None,
        "recommendations": None,
        "current_step": "init",
        "errors": [],
        "metadata": {
            "session_id": "session_test_001",
            "started_at": datetime.utcnow().isoformat()
        }
    }


@pytest.fixture
def mock_state_graph():
    """Mock LangGraph StateGraph."""
    with patch('langgraph.graph.StateGraph') as mock_graph:
        graph_instance = MagicMock()
        graph_instance.add_node = MagicMock()
        graph_instance.add_edge = MagicMock()
        graph_instance.add_conditional_edges = MagicMock()
        graph_instance.compile = MagicMock(return_value=MagicMock())
        mock_graph.return_value = graph_instance
        yield mock_graph


@pytest.fixture
def mock_memory_saver():
    """Mock MemorySaver checkpointer."""
    with patch('langgraph.checkpoint.MemorySaver') as mock_saver:
        saver_instance = MagicMock()
        saver_instance.aget = AsyncMock(return_value=None)
        saver_instance.aput = AsyncMock()
        mock_saver.return_value = saver_instance
        yield mock_saver


class MockStreamEvent:
    """Mock streaming event for testing."""

    def __init__(self, event_type: str, data: Dict[str, Any]):
        self.type = event_type
        self.data = data

    def __repr__(self):
        return f"MockStreamEvent(type={self.type}, data={self.data})"


@pytest.fixture
def create_mock_stream():
    """Factory fixture for creating mock stream events."""
    def _create_stream(events: List[tuple]):
        """Create async generator of mock events.

        Args:
            events: List of (event_type, data) tuples
        """
        async def _stream():
            for event_type, data in events:
                yield MockStreamEvent(event_type, data)
        return _stream()
    return _create_stream
