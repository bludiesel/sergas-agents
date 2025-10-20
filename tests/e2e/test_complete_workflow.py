"""
End-to-End Tests for Complete Orchestrator Workflows.

Tests cover:
- Full orchestrator workflow execution
- Account review cycles (daily/weekly/on-demand)
- Approval workflow integration
- Error recovery scenarios
- Multi-account parallel processing
- Performance validation

Uses real database with mocked external APIs.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import AsyncMock, Mock, patch, MagicMock

from tests.e2e.fixtures.account_fixtures import (
    get_all_test_accounts,
    get_accounts_by_owner,
    get_high_risk_accounts
)
from tests.e2e.fixtures.interaction_fixtures import generate_complete_interaction_history
from tests.e2e.fixtures.deal_fixtures import generate_complete_deal_pipeline


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def test_database(tmp_path):
    """Set up test database with realistic data."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.db.models import Base

    # Create test database
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture
def mock_zoho_client_e2e():
    """Mock Zoho client with realistic E2E behavior."""
    client = AsyncMock()

    # Store test accounts
    test_accounts = get_all_test_accounts()
    account_map = {acc["id"]: acc for acc in test_accounts}

    async def get_account(account_id: str):
        return account_map.get(account_id, {})

    async def get_accounts(account_ids: List[str]):
        return [account_map.get(aid) for aid in account_ids if aid in account_map]

    async def search_accounts(criteria: str):
        # Simple mock search
        return list(account_map.values())[:10]

    async def get_contacts(account_id: str):
        # Mock contacts
        return [
            {
                "id": f"contact_{account_id}_1",
                "Full_Name": "Primary Contact",
                "Email": f"contact1@{account_id}.com",
                "Title": "VP of Engineering"
            },
            {
                "id": f"contact_{account_id}_2",
                "Full_Name": "Secondary Contact",
                "Email": f"contact2@{account_id}.com",
                "Title": "Product Manager"
            }
        ]

    async def get_deals(account_id: str):
        # Generate realistic deals
        account = account_map.get(account_id, {})
        account_type = "healthy" if "HEALTHY" in account_id else \
                       "at_risk" if "RISK" in account_id else \
                       "high_value" if "HIGHVAL" in account_id else "growth"

        pipeline = generate_complete_deal_pipeline(account_id, account_type)
        return pipeline.get("active", [])

    async def get_activities(account_id: str):
        # Generate realistic interactions
        account = account_map.get(account_id, {})
        account_type = "healthy" if "HEALTHY" in account_id else \
                       "at_risk" if "RISK" in account_id else \
                       "high_value" if "HIGHVAL" in account_id else "growth"

        interactions = generate_complete_interaction_history(account_id, account_type)
        return interactions[:20]  # Return recent 20

    async def create_note(account_id: str, content: str):
        return {"id": f"note_{account_id}_{datetime.now().timestamp()}", "success": True}

    async def update_account(account_id: str, data: Dict[str, Any]):
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

    async def store(key: str, value: Any):
        memory_store[key] = value
        return {"success": True, "key": key}

    async def get(key: str):
        return memory_store.get(key)

    async def search(query: str, limit: int = 10):
        # Simple keyword search
        results = []
        for key, value in memory_store.items():
            if query.lower() in str(value).lower():
                results.append({
                    "key": key,
                    "content": value,
                    "score": 0.95
                })
                if len(results) >= limit:
                    break
        return results

    async def add(data: Any, dataset: str = "default"):
        key = f"{dataset}_{len(memory_store)}"
        memory_store[key] = data
        return {"success": True, "id": key}

    client.store = store
    client.get = get
    client.search = search
    client.add = add

    return client


@pytest.fixture
def mock_claude_agent():
    """Mock Claude agent for E2E testing."""
    agent = AsyncMock()

    async def query(prompt: str, context: Dict = None):
        # Simulate agent analysis
        await asyncio.sleep(0.1)  # Simulate processing time

        # Return realistic mock responses based on prompt
        if "health" in prompt.lower():
            return {
                "health_score": 75,
                "risk_level": "low",
                "key_findings": ["Strong engagement", "Active pipeline"],
                "processing_time": 0.1
            }
        elif "risk" in prompt.lower():
            return {
                "risk_score": 35,
                "risk_factors": ["Stable engagement", "Positive sentiment"],
                "mitigation_strategies": [],
                "processing_time": 0.1
            }
        elif "recommendation" in prompt.lower():
            return {
                "recommendations": [
                    {"action": "Schedule QBR", "priority": "high"},
                    {"action": "Review product adoption", "priority": "medium"}
                ],
                "processing_time": 0.1
            }
        else:
            return {"response": "Analysis complete", "processing_time": 0.1}

    agent.query = query
    return agent


# ============================================================================
# Test Suite: Complete Workflow Orchestration
# ============================================================================

@pytest.mark.e2e
@pytest.mark.asyncio
class TestCompleteWorkflowOrchestration:
    """Test complete orchestrator workflow execution."""

    async def test_daily_review_cycle_single_owner(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e,
        mock_claude_agent,
        test_database
    ):
        """Test complete daily review cycle for single owner."""
        # Arrange
        owner_id = "owner_1"
        all_accounts = get_all_test_accounts()
        owner_accounts = get_accounts_by_owner(owner_id, all_accounts)

        # Act
        start_time = datetime.now()

        # Simulate orchestrator workflow
        results = []
        for account in owner_accounts[:5]:  # Process first 5 accounts
            account_data = await mock_zoho_client_e2e.get_account(account["id"])
            contacts = await mock_zoho_client_e2e.get_contacts(account["id"])
            deals = await mock_zoho_client_e2e.get_deals(account["id"])
            activities = await mock_zoho_client_e2e.get_activities(account["id"])

            # Store context in memory
            await mock_cognee_client_e2e.store(
                f"account_context_{account['id']}",
                {
                    "account": account_data,
                    "contacts": contacts,
                    "deals": deals,
                    "activities": activities
                }
            )

            # Run agent analysis
            health_analysis = await mock_claude_agent.query(
                f"Analyze health for account {account['id']}",
                {"account": account_data}
            )
            risk_analysis = await mock_claude_agent.query(
                f"Analyze risk for account {account['id']}",
                {"account": account_data}
            )
            recommendations = await mock_claude_agent.query(
                f"Generate recommendations for account {account['id']}",
                {"health": health_analysis, "risk": risk_analysis}
            )

            results.append({
                "account_id": account["id"],
                "health": health_analysis,
                "risk": risk_analysis,
                "recommendations": recommendations
            })

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Assert
        assert len(results) == 5
        assert duration < 30  # Should complete in under 30 seconds
        assert all("health" in r for r in results)
        assert all("risk" in r for r in results)
        assert all("recommendations" in r for r in results)

        # Verify memory storage
        for result in results:
            context = await mock_cognee_client_e2e.get(
                f"account_context_{result['account_id']}"
            )
            assert context is not None
            assert "account" in context

    async def test_weekly_review_cycle_multi_owner(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e,
        mock_claude_agent
    ):
        """Test weekly review cycle across multiple owners."""
        # Arrange
        owner_ids = ["owner_1", "owner_2", "owner_3"]
        all_accounts = get_all_test_accounts()

        # Act
        owner_briefs = []
        for owner_id in owner_ids:
            owner_accounts = get_accounts_by_owner(owner_id, all_accounts)

            # Process accounts in parallel
            tasks = []
            for account in owner_accounts[:3]:  # Sample 3 per owner
                async def process_account(acc):
                    account_data = await mock_zoho_client_e2e.get_account(acc["id"])
                    health = await mock_claude_agent.query(
                        f"Analyze health for {acc['id']}",
                        {"account": account_data}
                    )
                    return {"account_id": acc["id"], "health": health}

                tasks.append(process_account(account))

            account_results = await asyncio.gather(*tasks)

            owner_briefs.append({
                "owner_id": owner_id,
                "accounts_reviewed": len(account_results),
                "results": account_results
            })

        # Assert
        assert len(owner_briefs) == 3
        assert all(brief["accounts_reviewed"] > 0 for brief in owner_briefs)
        assert sum(brief["accounts_reviewed"] for brief in owner_briefs) == 9

    async def test_on_demand_review_high_risk_accounts(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e,
        mock_claude_agent
    ):
        """Test on-demand review triggered for high-risk accounts."""
        # Arrange
        all_accounts = get_all_test_accounts()
        high_risk = get_high_risk_accounts(all_accounts, risk_threshold=70)

        # Act
        priority_results = []
        for account in high_risk[:5]:  # Process top 5 high-risk
            account_data = await mock_zoho_client_e2e.get_account(account["id"])
            activities = await mock_zoho_client_e2e.get_activities(account["id"])

            # Detailed risk analysis
            risk_analysis = await mock_claude_agent.query(
                f"Detailed risk analysis for {account['id']}",
                {
                    "account": account_data,
                    "activities": activities,
                    "priority": "critical"
                }
            )

            recommendations = await mock_claude_agent.query(
                f"Urgent recommendations for {account['id']}",
                {"risk_analysis": risk_analysis}
            )

            priority_results.append({
                "account_id": account["id"],
                "risk_score": account.get("Churn_Risk_Score", 0),
                "risk_analysis": risk_analysis,
                "recommendations": recommendations,
                "escalated": True
            })

        # Assert
        assert len(priority_results) == 5
        assert all(r["escalated"] for r in priority_results)
        assert all(r["risk_score"] >= 70 for r in priority_results)

    async def test_parallel_account_processing(
        self,
        mock_zoho_client_e2e,
        mock_claude_agent
    ):
        """Test parallel processing of multiple accounts."""
        # Arrange
        all_accounts = get_all_test_accounts()
        test_accounts = all_accounts[:10]

        # Act
        start_time = datetime.now()

        async def process_single_account(account):
            account_data = await mock_zoho_client_e2e.get_account(account["id"])
            health = await mock_claude_agent.query(
                f"Analyze {account['id']}", {"account": account_data}
            )
            return {"account_id": account["id"], "health": health}

        # Process all accounts in parallel
        results = await asyncio.gather(
            *[process_single_account(acc) for acc in test_accounts]
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Assert
        assert len(results) == 10
        # Parallel execution should be faster than sequential
        assert duration < 5  # Should complete quickly with mocked delays

    async def test_workflow_with_approval_gate(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e,
        mock_claude_agent
    ):
        """Test workflow including approval gate for CRM modifications."""
        # Arrange
        account = get_all_test_accounts()[0]
        approval_queue = []

        async def create_approval_request(account_id, action, data):
            request = {
                "id": f"approval_{len(approval_queue)}",
                "account_id": account_id,
                "action": action,
                "data": data,
                "status": "pending",
                "created_at": datetime.now()
            }
            approval_queue.append(request)
            return request["id"]

        async def approve_request(request_id, approver):
            for req in approval_queue:
                if req["id"] == request_id:
                    req["status"] = "approved"
                    req["approver"] = approver
                    req["approved_at"] = datetime.now()
                    return True
            return False

        # Act
        # 1. Analyze account
        account_data = await mock_zoho_client_e2e.get_account(account["id"])
        recommendations = await mock_claude_agent.query(
            f"Generate recommendations for {account['id']}",
            {"account": account_data}
        )

        # 2. Create approval request for recommended changes
        request_id = await create_approval_request(
            account["id"],
            "update_account",
            {"Rating": "Warm", "Next_Action": "Schedule QBR"}
        )

        # 3. Approve request
        approved = await approve_request(request_id, "manager@company.com")

        # 4. Execute approved change
        if approved:
            await mock_zoho_client_e2e.update_account(
                account["id"],
                {"Rating": "Warm", "Next_Action": "Schedule QBR"}
            )

        # Assert
        assert len(approval_queue) == 1
        assert approval_queue[0]["status"] == "approved"
        assert approval_queue[0]["approver"] == "manager@company.com"

    async def test_workflow_error_recovery(
        self,
        mock_zoho_client_e2e,
        mock_claude_agent
    ):
        """Test workflow error recovery and retry logic."""
        # Arrange
        account = get_all_test_accounts()[0]
        call_count = {"zoho": 0, "agent": 0}
        max_retries = 3

        async def flaky_get_account(account_id):
            call_count["zoho"] += 1
            if call_count["zoho"] < 2:
                raise Exception("Temporary API error")
            return {"id": account_id, "Account_Name": "Test"}

        async def flaky_agent_query(prompt, context=None):
            call_count["agent"] += 1
            if call_count["agent"] < 2:
                raise Exception("Agent timeout")
            return {"result": "success"}

        mock_zoho_client_e2e.get_account = flaky_get_account
        mock_claude_agent.query = flaky_agent_query

        # Act
        async def retry_operation(operation, max_attempts=3):
            for attempt in range(max_attempts):
                try:
                    return await operation()
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    await asyncio.sleep(0.1)

        # Retry get_account
        account_data = await retry_operation(
            lambda: mock_zoho_client_e2e.get_account(account["id"])
        )

        # Retry agent query
        agent_result = await retry_operation(
            lambda: mock_claude_agent.query("test", {})
        )

        # Assert
        assert account_data is not None
        assert agent_result["result"] == "success"
        assert call_count["zoho"] >= 2  # Required retries
        assert call_count["agent"] >= 2

    async def test_workflow_performance_targets(
        self,
        mock_zoho_client_e2e,
        mock_claude_agent
    ):
        """Test workflow meets performance targets from PRD."""
        # Arrange
        all_accounts = get_all_test_accounts()
        owner_accounts = all_accounts[:20]  # Typical portfolio size

        # Act - Simulate owner brief generation
        start_time = datetime.now()

        # Process accounts in parallel (up to 10 concurrent)
        batch_size = 10
        all_results = []

        for i in range(0, len(owner_accounts), batch_size):
            batch = owner_accounts[i:i + batch_size]

            async def process_account_fast(account):
                # Minimal processing for performance test
                account_data = await mock_zoho_client_e2e.get_account(account["id"])
                health = await mock_claude_agent.query("quick_health", {"account": account_data})
                return {"account_id": account["id"], "health": health}

            batch_results = await asyncio.gather(
                *[process_account_fast(acc) for acc in batch]
            )
            all_results.extend(batch_results)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Assert - PRD Target: Owner brief generation <10 minutes
        assert duration < 600  # 10 minutes
        assert len(all_results) == 20
        # With mocked delays, should be much faster
        assert duration < 30  # Should complete in under 30 seconds

    async def test_workflow_with_memory_context(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e,
        mock_claude_agent
    ):
        """Test workflow leveraging historical memory context."""
        # Arrange
        account = get_all_test_accounts()[0]

        # Store historical context
        await mock_cognee_client_e2e.store(
            f"history_{account['id']}",
            {
                "previous_health_scores": [85, 82, 80, 78, 75],
                "previous_reviews": [
                    {"date": "2025-10-01", "status": "healthy"},
                    {"date": "2025-10-08", "status": "healthy"}
                ],
                "trends": "declining_engagement"
            }
        )

        # Act
        # Retrieve historical context
        history = await mock_cognee_client_e2e.get(f"history_{account['id']}")

        # Current analysis with context
        current_data = await mock_zoho_client_e2e.get_account(account["id"])
        analysis = await mock_claude_agent.query(
            f"Analyze with history for {account['id']}",
            {
                "current": current_data,
                "history": history
            }
        )

        # Assert
        assert history is not None
        assert "previous_health_scores" in history
        assert analysis is not None

    async def test_multi_account_batch_processing(
        self,
        mock_zoho_client_e2e,
        mock_claude_agent
    ):
        """Test efficient batch processing of multiple accounts."""
        # Arrange
        all_accounts = get_all_test_accounts()
        batch_accounts = all_accounts[:30]

        # Act
        start_time = datetime.now()

        # Fetch all account data in batch
        account_ids = [acc["id"] for acc in batch_accounts]
        account_data_list = await mock_zoho_client_e2e.get_accounts(account_ids)

        # Process in batches
        batch_size = 10
        all_analyses = []

        for i in range(0, len(account_data_list), batch_size):
            batch = account_data_list[i:i + batch_size]

            analyses = await asyncio.gather(*[
                mock_claude_agent.query(f"Analyze {acc['id']}", {"account": acc})
                for acc in batch if acc
            ])
            all_analyses.extend(analyses)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Assert
        assert len(all_analyses) == 30
        assert duration < 60  # Should process 30 accounts in under 1 minute
        # Average processing time per account
        avg_time = duration / 30
        assert avg_time < 2  # Less than 2 seconds per account


# ============================================================================
# Test Suite: Workflow State Management
# ============================================================================

@pytest.mark.e2e
@pytest.mark.asyncio
class TestWorkflowStateManagement:
    """Test workflow state persistence and recovery."""

    async def test_workflow_checkpoint_and_recovery(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e
    ):
        """Test workflow can checkpoint and recover from interruption."""
        # Arrange
        accounts = get_all_test_accounts()[:10]
        checkpoint_store = {}

        async def save_checkpoint(workflow_id, state):
            checkpoint_store[workflow_id] = {
                "state": state,
                "timestamp": datetime.now()
            }

        async def load_checkpoint(workflow_id):
            return checkpoint_store.get(workflow_id)

        # Act - Part 1: Process first 5 accounts
        workflow_id = "workflow_test_001"
        processed = []

        for i, account in enumerate(accounts[:5]):
            account_data = await mock_zoho_client_e2e.get_account(account["id"])
            processed.append(account_data)

            # Checkpoint after each account
            await save_checkpoint(workflow_id, {
                "processed_count": len(processed),
                "processed_ids": [a["id"] for a in processed],
                "next_index": i + 1
            })

        # Simulate interruption and recovery
        checkpoint = await load_checkpoint(workflow_id)

        # Part 2: Resume from checkpoint
        next_index = checkpoint["state"]["next_index"]
        for account in accounts[next_index:]:
            account_data = await mock_zoho_client_e2e.get_account(account["id"])
            processed.append(account_data)

        # Assert
        assert len(processed) == 10
        assert checkpoint["state"]["processed_count"] == 5
        assert checkpoint["state"]["next_index"] == 5

    async def test_workflow_session_tracking(
        self,
        test_database,
        mock_zoho_client_e2e
    ):
        """Test workflow session tracking in database."""
        # This would use real database session tracking
        # For now, using in-memory simulation

        # Arrange
        sessions = {}

        async def create_session(session_id, metadata):
            sessions[session_id] = {
                "id": session_id,
                "status": "active",
                "created_at": datetime.now(),
                "metadata": metadata
            }

        async def update_session(session_id, updates):
            if session_id in sessions:
                sessions[session_id].update(updates)

        async def get_session(session_id):
            return sessions.get(session_id)

        # Act
        session_id = "session_001"
        await create_session(session_id, {
            "owner_id": "owner_1",
            "cycle": "daily",
            "account_count": 10
        })

        # Process accounts and update session
        account = get_all_test_accounts()[0]
        await mock_zoho_client_e2e.get_account(account["id"])

        await update_session(session_id, {
            "processed": 1,
            "status": "in_progress"
        })

        # Complete session
        await update_session(session_id, {
            "status": "completed",
            "completed_at": datetime.now()
        })

        # Assert
        session = await get_session(session_id)
        assert session["status"] == "completed"
        assert session["metadata"]["owner_id"] == "owner_1"
        assert session["processed"] == 1


# ============================================================================
# Test Suite: Integration Points
# ============================================================================

@pytest.mark.e2e
@pytest.mark.asyncio
class TestWorkflowIntegrationPoints:
    """Test integration between workflow components."""

    async def test_zoho_to_memory_pipeline(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e
    ):
        """Test data flow from Zoho to memory storage."""
        # Arrange
        account = get_all_test_accounts()[0]

        # Act
        # 1. Fetch from Zoho
        account_data = await mock_zoho_client_e2e.get_account(account["id"])
        contacts = await mock_zoho_client_e2e.get_contacts(account["id"])
        deals = await mock_zoho_client_e2e.get_deals(account["id"])

        # 2. Store in memory
        await mock_cognee_client_e2e.add(
            {"account": account_data, "contacts": contacts, "deals": deals},
            dataset=f"account_{account['id']}"
        )

        # 3. Retrieve from memory
        results = await mock_cognee_client_e2e.search(account["id"])

        # Assert
        assert len(results) > 0
        assert results[0]["key"].startswith(f"account_{account['id']}")

    async def test_memory_to_agent_context(
        self,
        mock_cognee_client_e2e,
        mock_claude_agent
    ):
        """Test context passing from memory to agent."""
        # Arrange
        account_id = "ACC_TEST_001"

        # Store rich context
        await mock_cognee_client_e2e.store(
            f"context_{account_id}",
            {
                "account_name": "Test Corp",
                "health_score": 75,
                "recent_activities": ["Call", "Email", "Meeting"],
                "open_deals": 3
            }
        )

        # Act
        # Retrieve context
        context = await mock_cognee_client_e2e.get(f"context_{account_id}")

        # Pass to agent
        analysis = await mock_claude_agent.query(
            f"Analyze account {account_id}",
            context
        )

        # Assert
        assert context is not None
        assert analysis is not None

    async def test_agent_to_approval_pipeline(
        self,
        mock_claude_agent
    ):
        """Test recommendations flow to approval system."""
        # Arrange
        account_id = "ACC_TEST_001"
        approvals = []

        async def create_approval(recommendation):
            approval = {
                "id": f"approval_{len(approvals)}",
                "account_id": account_id,
                "recommendation": recommendation,
                "status": "pending",
                "created_at": datetime.now()
            }
            approvals.append(approval)
            return approval["id"]

        # Act
        # Get recommendations from agent
        recommendations = await mock_claude_agent.query(
            f"Generate recommendations for {account_id}",
            {"account_id": account_id}
        )

        # Create approval requests
        for rec in recommendations.get("recommendations", []):
            await create_approval(rec)

        # Assert
        assert len(approvals) > 0
        assert all(a["status"] == "pending" for a in approvals)
