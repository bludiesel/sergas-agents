"""
Pytest configuration and fixtures for E2E tests.

Provides:
- Real database setup/teardown
- Mock external API clients
- Performance monitoring
- Test data management
"""

import pytest
import asyncio
import os
from datetime import datetime
from typing import Generator
from unittest.mock import AsyncMock

from tests.e2e.fixtures.account_fixtures import get_all_test_accounts
from tests.e2e.fixtures.interaction_fixtures import generate_complete_interaction_history
from tests.e2e.fixtures.deal_fixtures import generate_complete_deal_pipeline


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def e2e_database_url():
    """Get E2E test database URL from environment or use SQLite."""
    return os.getenv("E2E_DATABASE_URL", "sqlite:///./test_e2e.db")


@pytest.fixture(scope="function")
async def test_db_session(e2e_database_url):
    """Create test database session with proper setup/teardown."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.db.models import Base

    # Create engine
    engine = create_engine(
        e2e_database_url,
        connect_args={"check_same_thread": False} if "sqlite" in e2e_database_url else {}
    )

    # Create all tables
    Base.metadata.create_all(engine)

    # Create session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


# ============================================================================
# Mock External API Clients
# ============================================================================

@pytest.fixture
def mock_zoho_client_e2e():
    """Mock Zoho CRM client with realistic E2E behavior."""
    client = AsyncMock()

    # Load test data
    test_accounts = get_all_test_accounts()
    account_map = {acc["id"]: acc for acc in test_accounts}

    async def get_account(account_id: str):
        await asyncio.sleep(0.01)  # Simulate network delay
        return account_map.get(account_id, {})

    async def get_accounts(account_ids: list):
        await asyncio.sleep(0.05)  # Simulate batch fetch delay
        return [account_map.get(aid) for aid in account_ids if aid in account_map]

    async def search_accounts(criteria: str):
        await asyncio.sleep(0.02)
        return list(account_map.values())

    async def get_contacts(account_id: str):
        await asyncio.sleep(0.01)
        return [
            {
                "id": f"contact_{account_id}_1",
                "Full_Name": "Primary Contact",
                "Email": f"contact1@{account_id}.com",
                "Title": "VP of Engineering",
                "Phone": "+1-555-0001"
            },
            {
                "id": f"contact_{account_id}_2",
                "Full_Name": "Secondary Contact",
                "Email": f"contact2@{account_id}.com",
                "Title": "Product Manager",
                "Phone": "+1-555-0002"
            }
        ]

    async def get_deals(account_id: str):
        await asyncio.sleep(0.01)
        account = account_map.get(account_id, {})
        account_type = "healthy" if "HEALTHY" in account_id else \
                       "at_risk" if "RISK" in account_id else \
                       "high_value" if "HIGHVAL" in account_id else "growth"

        pipeline = generate_complete_deal_pipeline(account_id, account_type)
        return pipeline.get("active", [])

    async def get_activities(account_id: str):
        await asyncio.sleep(0.02)
        account = account_map.get(account_id, {})
        account_type = "healthy" if "HEALTHY" in account_id else \
                       "at_risk" if "RISK" in account_id else \
                       "high_value" if "HIGHVAL" in account_id else "growth"

        interactions = generate_complete_interaction_history(account_id, account_type)
        return interactions[:20]

    async def create_note(account_id: str, content: str):
        await asyncio.sleep(0.01)
        return {
            "id": f"note_{account_id}_{datetime.now().timestamp()}",
            "success": True,
            "content": content
        }

    async def update_account(account_id: str, data: dict):
        await asyncio.sleep(0.02)
        if account_id in account_map:
            account_map[account_id].update(data)
        return account_map.get(account_id, {})

    client.get_account = get_account
    client.get_accounts = get_accounts
    client.search_accounts = search_accounts
    client.get_contacts = get_contacts
    client.get_deals = get_deals
    client.get_activities = get_activities
    client.create_note = create_note
    client.update_account = update_account
    client.health_check = AsyncMock(return_value={"status": "healthy"})

    return client


@pytest.fixture
def mock_cognee_client_e2e():
    """Mock Cognee memory client with realistic E2E behavior."""
    client = AsyncMock()
    memory_store = {}

    async def store(key: str, value):
        await asyncio.sleep(0.01)  # Simulate storage delay
        memory_store[key] = {
            "value": value,
            "stored_at": datetime.now().isoformat()
        }
        return {"success": True, "key": key}

    async def get(key: str):
        await asyncio.sleep(0.01)
        item = memory_store.get(key)
        return item["value"] if item else None

    async def search(query: str, limit: int = 10):
        await asyncio.sleep(0.02)
        results = []
        for key, item in memory_store.items():
            if query.lower() in str(item["value"]).lower():
                results.append({
                    "key": key,
                    "content": item["value"],
                    "score": 0.95,
                    "stored_at": item["stored_at"]
                })
                if len(results) >= limit:
                    break
        return results

    async def add(data, dataset: str = "default"):
        await asyncio.sleep(0.01)
        key = f"{dataset}_{len(memory_store)}"
        memory_store[key] = {
            "value": data,
            "stored_at": datetime.now().isoformat()
        }
        return {"success": True, "id": key}

    async def delete(key: str):
        await asyncio.sleep(0.01)
        if key in memory_store:
            del memory_store[key]
            return True
        return False

    client.store = store
    client.get = get
    client.search = search
    client.add = add
    client.delete = delete
    client.memory_store = memory_store  # For testing/inspection

    return client


@pytest.fixture
def mock_claude_agent():
    """Mock Claude agent with realistic E2E behavior."""
    agent = AsyncMock()
    call_count = {"total": 0}

    async def query(prompt: str, context: dict = None):
        call_count["total"] += 1
        await asyncio.sleep(0.1)  # Simulate LLM processing time

        # Generate realistic responses based on prompt type
        if "health" in prompt.lower():
            return {
                "health_score": 75,
                "risk_level": "low",
                "key_findings": [
                    "Strong engagement metrics",
                    "Active pipeline",
                    "Regular communication"
                ],
                "processing_time": 0.1,
                "call_number": call_count["total"]
            }
        elif "risk" in prompt.lower():
            return {
                "risk_score": 35,
                "risk_factors": ["Stable engagement", "Positive sentiment"],
                "mitigation_strategies": ["Continue current engagement"],
                "processing_time": 0.1,
                "call_number": call_count["total"]
            }
        elif "recommendation" in prompt.lower():
            return {
                "recommendations": [
                    {
                        "action": "Schedule quarterly business review",
                        "priority": "high",
                        "timeline": "within_2_weeks"
                    },
                    {
                        "action": "Review product adoption metrics",
                        "priority": "medium",
                        "timeline": "within_month"
                    }
                ],
                "processing_time": 0.1,
                "call_number": call_count["total"]
            }
        else:
            return {
                "response": "Analysis complete",
                "processing_time": 0.1,
                "call_number": call_count["total"]
            }

    agent.query = query
    agent.call_count = call_count
    return agent


# ============================================================================
# Performance Monitoring
# ============================================================================

@pytest.fixture
def performance_monitor():
    """Monitor performance metrics during E2E tests."""
    class PerformanceMonitor:
        def __init__(self):
            self.metrics = {
                "start_time": None,
                "end_time": None,
                "api_calls": 0,
                "database_queries": 0,
                "memory_operations": 0,
                "agent_calls": 0
            }

        def start(self):
            self.metrics["start_time"] = datetime.now()

        def stop(self):
            self.metrics["end_time"] = datetime.now()
            if self.metrics["start_time"]:
                self.metrics["duration_seconds"] = (
                    self.metrics["end_time"] - self.metrics["start_time"]
                ).total_seconds()

        def record_api_call(self):
            self.metrics["api_calls"] += 1

        def record_db_query(self):
            self.metrics["database_queries"] += 1

        def record_memory_op(self):
            self.metrics["memory_operations"] += 1

        def record_agent_call(self):
            self.metrics["agent_calls"] += 1

        def get_summary(self):
            return {
                **self.metrics,
                "avg_api_call_time": (
                    self.metrics.get("duration_seconds", 0) /
                    max(self.metrics["api_calls"], 1)
                ) if self.metrics.get("duration_seconds") else 0
            }

    return PerformanceMonitor()


@pytest.fixture
def assert_performance():
    """Helper to assert performance requirements."""
    def _assert_performance(duration: float, max_duration: float, operation: str):
        assert duration < max_duration, (
            f"{operation} took {duration:.2f}s, exceeding max {max_duration}s"
        )

    return _assert_performance


# ============================================================================
# Test Data Management
# ============================================================================

@pytest.fixture
def e2e_test_accounts():
    """Provide all E2E test accounts."""
    return get_all_test_accounts()


@pytest.fixture
def e2e_healthy_accounts(e2e_test_accounts):
    """Provide only healthy accounts."""
    return [acc for acc in e2e_test_accounts if "HEALTHY" in acc["id"]]


@pytest.fixture
def e2e_at_risk_accounts(e2e_test_accounts):
    """Provide only at-risk accounts."""
    return [acc for acc in e2e_test_accounts if "RISK" in acc["id"]]


@pytest.fixture
def e2e_high_value_accounts(e2e_test_accounts):
    """Provide only high-value accounts."""
    return [acc for acc in e2e_test_accounts if "HIGHVAL" in acc["id"]]


# ============================================================================
# Event Loop Configuration
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async E2E tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Cleanup
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup resources after each E2E test."""
    yield
    # Cleanup logic here
    pass


# ============================================================================
# Test Markers
# ============================================================================

def pytest_configure(config):
    """Register custom markers for E2E tests."""
    config.addinivalue_line(
        "markers", "e2e: End-to-end integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e_workflow: Complete workflow E2E tests"
    )
    config.addinivalue_line(
        "markers", "e2e_sync: Sync workflow E2E tests"
    )
    config.addinivalue_line(
        "markers", "e2e_scenarios: User scenario E2E tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take >30 seconds"
    )
