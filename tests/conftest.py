"""
Pytest configuration and global fixtures for Account Management Agent System.

This module provides:
- Mock clients for Zoho CRM and Cognee memory
- Test data generators
- Common test utilities
- Pytest configuration
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, MagicMock

import pytest
from pydantic import BaseModel


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (component interactions)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (complete workflows)"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and load tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take >5 seconds"
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_account_data() -> Dict[str, Any]:
    """Provide sample account data for testing."""
    return {
        "id": "acc_123456",
        "Account_Name": "Acme Corporation",
        "Annual_Revenue": 5000000,
        "Industry": "Technology",
        "Account_Type": "Customer",
        "Rating": "Hot",
        "Owner": {
            "name": "John Smith",
            "id": "user_789"
        },
        "Created_Time": "2024-01-15T10:30:00Z",
        "Modified_Time": "2025-10-15T14:20:00Z"
    }


@pytest.fixture
def sample_contact_data() -> Dict[str, Any]:
    """Provide sample contact data for testing."""
    return {
        "id": "contact_456",
        "Full_Name": "Jane Doe",
        "Email": "jane.doe@acme.com",
        "Title": "VP of Engineering",
        "Phone": "+1-555-0123",
        "Account_Name": {
            "name": "Acme Corporation",
            "id": "acc_123456"
        }
    }


@pytest.fixture
def sample_deal_data() -> Dict[str, Any]:
    """Provide sample deal data for testing."""
    return {
        "id": "deal_789",
        "Deal_Name": "Acme - Enterprise License",
        "Amount": 250000,
        "Stage": "Negotiation",
        "Probability": 75,
        "Expected_Revenue": 187500,
        "Closing_Date": "2025-11-30",
        "Account_Name": {
            "name": "Acme Corporation",
            "id": "acc_123456"
        }
    }


@pytest.fixture
def sample_activity_data() -> List[Dict[str, Any]]:
    """Provide sample activity history for testing."""
    return [
        {
            "id": "activity_1",
            "Activity_Type": "Call",
            "Subject": "Quarterly Business Review",
            "Date": "2025-10-10",
            "Status": "Completed",
            "Who_Id": {
                "name": "Jane Doe",
                "id": "contact_456"
            }
        },
        {
            "id": "activity_2",
            "Activity_Type": "Email",
            "Subject": "Product Demo Follow-up",
            "Date": "2025-10-12",
            "Status": "Completed"
        },
        {
            "id": "activity_3",
            "Activity_Type": "Meeting",
            "Subject": "Contract Negotiation",
            "Date": "2025-10-17",
            "Status": "Scheduled"
        }
    ]


@pytest.fixture
def at_risk_account_data() -> Dict[str, Any]:
    """Provide data for an at-risk account."""
    return {
        "id": "acc_999",
        "Account_Name": "Beta Industries",
        "Annual_Revenue": 1000000,
        "Industry": "Manufacturing",
        "Rating": "Cold",
        "Last_Activity_Time": "2025-08-15T10:00:00Z",  # 2 months ago
        "Open_Deals_Count": 0,
        "Support_Tickets_Count": 5,
        "NPS_Score": 3
    }


# ============================================================================
# Mock Zoho CRM Client
# ============================================================================

class MockZohoResponse:
    """Mock response from Zoho API."""

    def __init__(self, data: Any, status_code: int = 200):
        self.data = data
        self.status_code = status_code

    def json(self):
        return {"data": [self.data]} if not isinstance(self.data, list) else {"data": self.data}


class MockZohoClient:
    """Mock Zoho CRM client for testing."""

    def __init__(self):
        self.access_token = "mock_access_token"
        self.refresh_token = "mock_refresh_token"
        self.accounts = {}
        self.contacts = {}
        self.deals = {}
        self.activities = {}
        self.call_count = 0
        self.rate_limited = False

    def get_account(self, account_id: str) -> Dict[str, Any]:
        """Mock get account by ID."""
        self.call_count += 1
        if self.rate_limited:
            raise Exception("Rate limit exceeded")
        return self.accounts.get(account_id, {"id": account_id, "Account_Name": "Test Account"})

    def search_accounts(self, criteria: str) -> List[Dict[str, Any]]:
        """Mock search accounts."""
        self.call_count += 1
        return list(self.accounts.values())

    def get_contacts(self, account_id: str) -> List[Dict[str, Any]]:
        """Mock get contacts for account."""
        self.call_count += 1
        return [c for c in self.contacts.values() if c.get("Account_Name", {}).get("id") == account_id]

    def get_deals(self, account_id: str) -> List[Dict[str, Any]]:
        """Mock get deals for account."""
        self.call_count += 1
        return [d for d in self.deals.values() if d.get("Account_Name", {}).get("id") == account_id]

    def get_activities(self, account_id: str) -> List[Dict[str, Any]]:
        """Mock get activities for account."""
        self.call_count += 1
        return [a for a in self.activities.values() if a.get("account_id") == account_id]

    def create_note(self, account_id: str, content: str) -> Dict[str, Any]:
        """Mock create note."""
        self.call_count += 1
        return {"id": "note_123", "content": content, "account_id": account_id}

    def update_account(self, account_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock update account."""
        self.call_count += 1
        if account_id in self.accounts:
            self.accounts[account_id].update(data)
            return self.accounts[account_id]
        return {"id": account_id, **data}

    def refresh_access_token(self) -> str:
        """Mock refresh access token."""
        self.call_count += 1
        self.access_token = "mock_refreshed_token"
        return self.access_token


@pytest.fixture
def mock_zoho_client(sample_account_data, sample_contact_data, sample_deal_data) -> MockZohoClient:
    """Provide a mock Zoho CRM client."""
    client = MockZohoClient()

    # Populate with sample data
    client.accounts[sample_account_data["id"]] = sample_account_data
    client.contacts[sample_contact_data["id"]] = sample_contact_data
    client.deals[sample_deal_data["id"]] = sample_deal_data

    return client


@pytest.fixture
def mock_zoho_client_with_rate_limit(mock_zoho_client) -> MockZohoClient:
    """Provide a mock Zoho client that simulates rate limiting."""
    mock_zoho_client.rate_limited = True
    return mock_zoho_client


# ============================================================================
# Mock Cognee Memory Client
# ============================================================================

class MockCogneeMemory:
    """Mock Cognee memory client for testing."""

    def __init__(self):
        self.storage: Dict[str, Any] = {}
        self.datasets: Dict[str, List[Any]] = {}
        self.call_count = 0

    async def add(self, data: Any, dataset_name: str = "default") -> Dict[str, Any]:
        """Mock add data to memory."""
        self.call_count += 1
        if dataset_name not in self.datasets:
            self.datasets[dataset_name] = []
        self.datasets[dataset_name].append(data)
        return {"status": "success", "id": f"mem_{len(self.datasets[dataset_name])}"}

    async def search(self, query: str, dataset_name: str = "default") -> List[Dict[str, Any]]:
        """Mock search memory."""
        self.call_count += 1
        if dataset_name not in self.datasets:
            return []

        # Simple mock search - return all items (in real tests, would filter)
        return [
            {
                "content": item,
                "score": 0.95,
                "metadata": {"dataset": dataset_name}
            }
            for item in self.datasets[dataset_name]
        ]

    async def get(self, key: str) -> Optional[Any]:
        """Mock get from memory by key."""
        self.call_count += 1
        return self.storage.get(key)

    async def store(self, key: str, value: Any) -> None:
        """Mock store in memory."""
        self.call_count += 1
        self.storage[key] = value

    async def delete(self, key: str) -> bool:
        """Mock delete from memory."""
        self.call_count += 1
        if key in self.storage:
            del self.storage[key]
            return True
        return False

    async def clear(self) -> None:
        """Mock clear all memory."""
        self.call_count += 1
        self.storage.clear()
        self.datasets.clear()

    def get_raw_storage(self) -> Dict[str, Any]:
        """Get raw storage for testing (not part of real API)."""
        return self.storage


@pytest.fixture
def mock_cognee_memory() -> MockCogneeMemory:
    """Provide a mock Cognee memory client."""
    return MockCogneeMemory()


@pytest.fixture
async def mock_cognee_with_context(mock_cognee_memory, sample_account_data) -> MockCogneeMemory:
    """Provide a mock Cognee memory with pre-populated context."""
    await mock_cognee_memory.store(
        f"account_context_{sample_account_data['id']}",
        {
            "account_id": sample_account_data["id"],
            "account_name": sample_account_data["Account_Name"],
            "last_analysis": "2025-10-15T10:00:00Z",
            "health_score": 85,
            "risk_level": "low"
        }
    )
    return mock_cognee_memory


# ============================================================================
# Mock MCP Server
# ============================================================================

class MockMCPServer:
    """Mock MCP server for testing tool invocations."""

    def __init__(self):
        self.tools = {}
        self.call_history = []

    def register_tool(self, name: str, response: Any):
        """Register a mock tool response."""
        self.tools[name] = response

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Mock tool invocation."""
        self.call_history.append({"tool": name, "arguments": arguments})
        if name in self.tools:
            return self.tools[name]
        return {"error": f"Tool {name} not found"}

    def tool_called(self, name: str) -> bool:
        """Check if a tool was called."""
        return any(call["tool"] == name for call in self.call_history)

    def get_tool_calls(self, name: str) -> List[Dict[str, Any]]:
        """Get all calls to a specific tool."""
        return [call for call in self.call_history if call["tool"] == name]


@pytest.fixture
def mock_mcp_server() -> MockMCPServer:
    """Provide a mock MCP server."""
    return MockMCPServer()


# ============================================================================
# Test Data Generators
# ============================================================================

class AccountDataGenerator:
    """Generate test account data with various characteristics."""

    @staticmethod
    def healthy_account() -> Dict[str, Any]:
        """Generate data for a healthy account."""
        return {
            "id": "acc_healthy_001",
            "Account_Name": "Healthy Corp",
            "Annual_Revenue": 10000000,
            "Rating": "Hot",
            "Last_Activity_Time": "2025-10-17T10:00:00Z",
            "Open_Deals_Count": 3,
            "Deal_Value": 500000,
            "NPS_Score": 9
        }

    @staticmethod
    def at_risk_account() -> Dict[str, Any]:
        """Generate data for an at-risk account."""
        return {
            "id": "acc_risk_001",
            "Account_Name": "At Risk Inc",
            "Annual_Revenue": 500000,
            "Rating": "Cold",
            "Last_Activity_Time": "2025-06-01T10:00:00Z",
            "Open_Deals_Count": 0,
            "Deal_Value": 0,
            "NPS_Score": 3,
            "Support_Tickets_Count": 8
        }

    @staticmethod
    def churned_account() -> Dict[str, Any]:
        """Generate data for a churned account."""
        return {
            "id": "acc_churned_001",
            "Account_Name": "Churned LLC",
            "Annual_Revenue": 0,
            "Rating": "Cold",
            "Last_Activity_Time": "2024-12-01T10:00:00Z",
            "Account_Status": "Inactive",
            "Churn_Date": "2025-01-15"
        }


@pytest.fixture
def account_generator() -> AccountDataGenerator:
    """Provide account data generator."""
    return AccountDataGenerator()


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def mock_time(monkeypatch):
    """Mock time for deterministic testing."""
    import time
    from datetime import datetime

    fixed_time = datetime(2025, 10, 18, 12, 0, 0).timestamp()

    def mock_time_func():
        return fixed_time

    monkeypatch.setattr(time, "time", mock_time_func)
    return fixed_time


@pytest.fixture
def temp_data_dir(tmp_path):
    """Provide a temporary directory for test data."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def load_fixture_file():
    """Provide a helper to load JSON fixture files."""
    def _load(filename: str) -> Any:
        fixture_path = Path(__file__).parent / "fixtures" / filename
        with open(fixture_path, "r") as f:
            return json.load(f)
    return _load


# ============================================================================
# Assertion Helpers
# ============================================================================

def assert_valid_account_data(data: Dict[str, Any]) -> None:
    """Assert that account data has required fields."""
    required_fields = ["id", "Account_Name"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


def assert_valid_health_score(score: float) -> None:
    """Assert that health score is within valid range."""
    assert isinstance(score, (int, float)), "Health score must be numeric"
    assert 0 <= score <= 100, f"Health score {score} out of range [0, 100]"


def assert_valid_risk_level(level: str) -> None:
    """Assert that risk level is valid."""
    valid_levels = ["low", "medium", "high", "critical"]
    assert level in valid_levels, f"Invalid risk level: {level}"


# ============================================================================
# Cleanup
# ============================================================================

@pytest.fixture(autouse=True)
def reset_state():
    """Reset global state before each test."""
    # Clear any global caches, singletons, etc.
    yield
    # Cleanup after test
    pass
