"""
Test fixtures for memory integration tests.

Provides:
- Sample account data
- Pilot account collections (50 accounts)
- Zoho mock data
- Cognee mock clients
- Memory service instances
- Test data generators
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock

# These imports will be available after Week 4 implementation
# from src.memory.memory_service import MemoryService
# from src.memory.cognee_client import CogneeClient
# from src.memory.ingestion import AccountIngestionPipeline
# from src.integrations.zoho_client import ZohoClient


# ============================================================================
# Account ID Fixtures
# ============================================================================

@pytest.fixture
def sample_account_id() -> str:
    """Single sample account ID for testing."""
    return "test_account_123456"


@pytest.fixture
def pilot_account_ids_50() -> List[str]:
    """
    50 pilot account IDs (PRD requirement).

    PRD: System must support 50 pilot accounts initially.
    """
    return [f"pilot_account_{i:04d}" for i in range(1, 51)]


@pytest.fixture
def healthy_account_id() -> str:
    """Account ID for healthy account (high health score)."""
    return "healthy_account_001"


@pytest.fixture
def at_risk_account_id() -> str:
    """Account ID for at-risk account (low health score)."""
    return "at_risk_account_001"


def generate_account_ids(count: int) -> List[str]:
    """Generate list of account IDs for testing."""
    return [f"generated_account_{i:06d}" for i in range(count)]


# ============================================================================
# Account Data Fixtures
# ============================================================================

@pytest.fixture
def sample_account() -> Dict[str, Any]:
    """Sample account data in Cognee format."""
    return {
        "account_id": "test_account_123456",
        "account_name": "Acme Corporation",
        "industry": "Technology",
        "annual_revenue": 5000000,
        "employee_count": 250,
        "region": "North America",
        "account_owner": "John Doe",
        "health_score": 75,
        "created_date": "2023-01-15",
        "last_modified": datetime.now().isoformat()
    }


@pytest.fixture
def sample_zoho_account() -> Dict[str, Any]:
    """Sample account data in Zoho CRM format."""
    return {
        "id": "test_account_123456",
        "Account_Name": "Acme Corporation",
        "Industry": "Technology",
        "Annual_Revenue": 5000000,
        "Employees": 250,
        "Billing_Country": "United States",
        "Billing_State": "California",
        "Account_Owner": {
            "name": "John Doe",
            "id": "owner_123"
        },
        "Created_Time": "2023-01-15T10:30:00Z",
        "Modified_Time": datetime.now().isoformat()
    }


@pytest.fixture
def pilot_accounts_50() -> List[Dict[str, Any]]:
    """
    50 pilot accounts in Cognee format.

    PRD: System must support 50 pilot accounts.
    """
    industries = [
        "Technology", "Manufacturing", "Healthcare",
        "Finance", "Retail", "Energy"
    ]
    regions = [
        "North America", "Europe", "Asia Pacific", "Latin America"
    ]

    accounts = []
    for i in range(1, 51):
        accounts.append({
            "account_id": f"pilot_account_{i:04d}",
            "account_name": f"Pilot Company {i}",
            "industry": industries[i % len(industries)],
            "annual_revenue": 500000 + (i * 100000),
            "employee_count": 50 + (i * 10),
            "region": regions[i % len(regions)],
            "account_owner": f"Owner {(i % 5) + 1}",
            "health_score": 50 + (i % 50),
            "created_date": "2024-01-01",
            "last_modified": datetime.now().isoformat()
        })

    return accounts


def generate_accounts(count: int, industry: str = None) -> List[Dict[str, Any]]:
    """Generate test account data."""
    industries = [
        "Technology", "Manufacturing", "Healthcare",
        "Finance", "Retail", "Energy", "Automotive"
    ]

    accounts = []
    for i in range(count):
        accounts.append({
            "account_id": f"generated_account_{i:06d}",
            "account_name": f"Generated Company {i}",
            "industry": industry or industries[i % len(industries)],
            "annual_revenue": 1000000 + (i * 50000),
            "employee_count": 100 + (i * 20),
            "region": "North America",
            "health_score": 60 + (i % 40),
            "last_modified": datetime.now().isoformat()
        })

    return accounts


# ============================================================================
# Interaction Data Fixtures
# ============================================================================

@pytest.fixture
def sample_email_interaction(sample_account_id) -> Dict[str, Any]:
    """Sample email interaction."""
    return {
        "account_id": sample_account_id,
        "type": "email",
        "subject": "Q1 Business Review",
        "content": "Great discussion about quarterly performance and future plans.",
        "sentiment": "positive",
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def sample_meeting_interaction(sample_account_id) -> Dict[str, Any]:
    """Sample meeting interaction."""
    return {
        "account_id": sample_account_id,
        "type": "meeting",
        "title": "Strategic Planning Session",
        "attendees": ["John Doe", "Jane Smith", "Bob Johnson"],
        "notes": "Discussed expansion plans and strategic initiatives for next year.",
        "sentiment": "positive",
        "timestamp": datetime.now().isoformat()
    }


def generate_interactions(
    account_id: str,
    count: int = 10,
    start_date: datetime = None
) -> List[Dict[str, Any]]:
    """Generate test interactions for account."""
    if start_date is None:
        start_date = datetime.now() - timedelta(days=90)

    interaction_types = ["email", "meeting", "call", "note"]
    sentiments = ["positive", "neutral", "negative"]

    interactions = []
    for i in range(count):
        timestamp = start_date + timedelta(days=i * 3)

        interactions.append({
            "account_id": account_id,
            "type": interaction_types[i % len(interaction_types)],
            "subject": f"Interaction {i+1}",
            "content": f"Content for interaction {i+1}",
            "sentiment": sentiments[i % len(sentiments)],
            "timestamp": timestamp.isoformat()
        })

    return interactions


# ============================================================================
# Health Analysis Fixtures
# ============================================================================

@pytest.fixture
def healthy_account_analysis() -> Dict[str, Any]:
    """Health analysis for healthy account."""
    return {
        "health_score": 85,
        "risk_level": "low",
        "risk_factors": [],
        "positive_indicators": [
            {"type": "high_engagement", "score": 90},
            {"type": "on_time_payments", "score": 100},
            {"type": "positive_sentiment", "score": 85}
        ],
        "recommendations": [
            "Continue current engagement strategy",
            "Explore upsell opportunities",
            "Schedule quarterly business review"
        ]
    }


@pytest.fixture
def at_risk_account_analysis() -> Dict[str, Any]:
    """Health analysis for at-risk account."""
    return {
        "health_score": 45,
        "risk_level": "high",
        "risk_factors": [
            {"type": "declining_engagement", "score": -25},
            {"type": "payment_delays", "score": -15},
            {"type": "support_tickets", "score": -10}
        ],
        "positive_indicators": [
            {"type": "long_relationship", "score": 5}
        ],
        "recommendations": [
            "Schedule urgent check-in call",
            "Review support ticket resolution",
            "Offer account health assessment",
            "Consider customer success intervention"
        ]
    }


# ============================================================================
# Service Instance Fixtures
# ============================================================================

@pytest.fixture
def memory_service():
    """
    Configured memory service instance.

    Note: Will be fully functional after Week 4 implementation.
    """
    # return MemoryService()
    pytest.skip("Week 4 implementation pending")


@pytest.fixture
def cognee_client():
    """
    Configured Cognee client instance.

    Note: Will be fully functional after Week 4 implementation.
    """
    # return CogneeClient()
    pytest.skip("Week 4 implementation pending")


@pytest.fixture
def ingestion_pipeline():
    """
    Configured ingestion pipeline instance.

    Note: Will be fully functional after Week 4 implementation.
    """
    # return AccountIngestionPipeline()
    pytest.skip("Week 4 implementation pending")


@pytest.fixture
def zoho_client():
    """
    Configured Zoho client instance.

    Note: Will be fully functional after integration.
    """
    # return ZohoClient()
    pytest.skip("Week 4 implementation pending")


# ============================================================================
# Mock Client Fixtures
# ============================================================================

@pytest.fixture
def mock_cognee_client():
    """Mock Cognee client for unit tests."""
    client = MagicMock()

    # Mock async methods
    client.add_account = AsyncMock(return_value={"success": True})
    client.get_account_context = AsyncMock(return_value={
        "account_id": "test_123",
        "current_data": {
            "account_name": "Test Company",
            "industry": "Technology"
        }
    })
    client.search_accounts = AsyncMock(return_value=[])
    client.analyze_health = AsyncMock(return_value={
        "health_score": 75,
        "risk_level": "low"
    })
    client.get_related_accounts = AsyncMock(return_value=[])
    client.store_interaction = AsyncMock(return_value={"success": True})

    return client


@pytest.fixture
def mock_zoho_client():
    """Mock Zoho client for unit tests."""
    client = MagicMock()

    # Mock async methods
    client.get_account = AsyncMock(return_value={
        "id": "test_123",
        "Account_Name": "Test Company",
        "Industry": "Technology",
        "Annual_Revenue": 5000000
    })
    client.get_accounts = AsyncMock(return_value=[])
    client.get_account_interactions = AsyncMock(return_value=[])

    return client


@pytest.fixture
def mock_memory_service():
    """Mock memory service for unit tests."""
    service = MagicMock()

    # Mock async methods
    service.get_account_brief = AsyncMock(return_value={
        "account_id": "test_123",
        "current_data": {},
        "historical_context": {},
        "health_analysis": {},
        "timeline": [],
        "recommendations": []
    })
    service.sync_account_to_memory = AsyncMock(return_value={"success": True})
    service.get_account_context = AsyncMock(return_value={})
    service.find_similar_accounts = AsyncMock(return_value=[])

    return service


# ============================================================================
# MCP Tool Fixtures
# ============================================================================

@pytest.fixture
def mcp_server():
    """
    Test MCP server instance.

    Note: Will be fully functional after Week 4 implementation.
    """
    pytest.skip("Week 4 implementation pending")


@pytest.fixture
def cognee_mcp_tools():
    """
    Cognee MCP tools collection.

    Note: Will be fully functional after Week 4 implementation.
    """
    pytest.skip("Week 4 implementation pending")


# ============================================================================
# Data Generator Helpers
# ============================================================================

def generate_account_data(
    account_id: str,
    **overrides
) -> Dict[str, Any]:
    """Generate account data with optional overrides."""
    base_data = {
        "account_id": account_id,
        "account_name": f"Company {account_id}",
        "industry": "Technology",
        "annual_revenue": 1000000,
        "employee_count": 100,
        "region": "North America",
        "health_score": 70,
        "last_modified": datetime.now().isoformat()
    }

    base_data.update(overrides)
    return base_data


def generate_search_results(
    count: int,
    query: str
) -> List[Dict[str, Any]]:
    """Generate mock search results."""
    results = []
    for i in range(count):
        results.append({
            "account_id": f"search_result_{i}",
            "account_name": f"Company {i}",
            "industry": "Technology",
            "relevance_score": 0.95 - (i * 0.05),
            "match_reason": f"Matched query: {query}"
        })

    return results


# ============================================================================
# Test Data Validation Fixtures
# ============================================================================

@pytest.fixture
def valid_account_data() -> Dict[str, Any]:
    """Valid account data for validation tests."""
    return {
        "account_id": "valid_123",
        "account_name": "Valid Company",
        "industry": "Technology",
        "annual_revenue": 1000000,
        "employee_count": 100,
        "region": "North America"
    }


@pytest.fixture
def invalid_account_data() -> Dict[str, Any]:
    """Invalid account data for validation tests."""
    return {
        "account_id": "invalid_123",
        # Missing required fields
        "some_random_field": "value"
    }


# ============================================================================
# Performance Test Fixtures
# ============================================================================

@pytest.fixture
def performance_test_accounts() -> List[Dict[str, Any]]:
    """Accounts for performance testing."""
    return generate_accounts(100)


@pytest.fixture
def large_interaction_history(sample_account_id) -> List[Dict[str, Any]]:
    """Large interaction history for performance testing."""
    return generate_interactions(sample_account_id, count=100)


# ============================================================================
# Async Fixture Helpers
# ============================================================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
async def cleanup_test_data():
    """Cleanup test data after each test."""
    yield
    # Cleanup code will go here after Week 4 implementation
    # For now, just pass
    pass


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Test configuration."""
    return {
        "cognee": {
            "base_url": "http://localhost:8000",
            "timeout": 30
        },
        "zoho": {
            "api_domain": "https://www.zohoapis.com",
            "timeout": 30
        },
        "cache": {
            "enabled": True,
            "ttl": 300
        },
        "ingestion": {
            "batch_size": 10,
            "max_retries": 3
        }
    }
