"""Integration Tests for Multi-Agent Workflow.

Tests complete end-to-end workflow: Zoho → Memory → Recommendation → Approval

Week 6-9 Critical Implementation - SPARC V3 Compliance (lines 1989-2042)

Test Coverage:
- Complete workflow orchestration (Zoho → Memory → Recommendation)
- AG UI Protocol event streaming via SSE
- Approval workflow (approve/reject/timeout)
- Error handling at each agent step
- Context passing between agents
- Performance requirements (<10s workflow, <200ms event latency)
- Concurrent workflow execution

Test Strategy:
- Mock Zoho API responses for deterministic testing
- Mock Cognee memory for historical context
- Real OrchestratorAgent and ApprovalManager instances
- Realistic mock data matching production scenarios
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from src.agents.orchestrator import OrchestratorAgent
from src.agents.zoho_data_scout import ZohoDataScout
from src.agents.memory_analyst import MemoryAnalyst
from src.events.approval_manager import ApprovalManager, ApprovalStatus
from src.agents.models import (
    AccountRecord,
    AccountSnapshot,
    AggregatedData,
    ChangeDetectionResult,
    RiskSignal,
    RiskLevel,
    ChangeType,
)
from src.agents.memory_models import (
    HistoricalContext,
    AccountTimeline,
    PatternRecognition,
    SentimentTrend,
    RelationshipStrength,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_account_snapshot():
    """Create realistic account snapshot for testing."""
    return AccountSnapshot(
        snapshot_id=f"snapshot_{uuid.uuid4().hex[:8]}",
        account=AccountRecord(
            account_id="acc_test_001",
            account_name="Test Corporation",
            owner_id="owner_123",
            owner_name="John Smith",
            industry="Technology",
            annual_revenue=5000000.0,
            website="https://testcorp.com",
            phone="+1-555-0100",
            billing_city="San Francisco",
            billing_country="USA",
            created_time=datetime.utcnow() - timedelta(days=365),
            modified_time=datetime.utcnow() - timedelta(days=2),
            last_activity_time=datetime.utcnow() - timedelta(days=7)
        ),
        aggregated_data=AggregatedData(
            total_contacts=5,
            total_deals=3,
            total_deal_value=250000.0,
            open_deals_count=2,
            won_deals_count=1,
            lost_deals_count=0,
            total_activities=25,
            activities_last_30_days=8,
            activities_last_90_days=18,
            last_interaction_date=datetime.utcnow() - timedelta(days=7),
            average_deal_size=83333.0,
            win_rate=0.5,
            days_since_last_activity=7,
            engagement_score=75.0
        ),
        changes=ChangeDetectionResult(
            changes_detected=2,
            change_summary="Revenue decreased 15%, Activity declined",
            changes=[
                {
                    "field": "annual_revenue",
                    "change_type": ChangeType.DECREASED,
                    "old_value": 5882353.0,
                    "new_value": 5000000.0,
                    "change_percentage": -15.0
                },
                {
                    "field": "activities_last_30_days",
                    "change_type": ChangeType.DECREASED,
                    "old_value": 12,
                    "new_value": 8,
                    "change_percentage": -33.3
                }
            ]
        ),
        risk_signals=[
            RiskSignal(
                signal_type="engagement_decline",
                severity="medium",
                description="Activity decreased by 33% in last 30 days",
                detected_at=datetime.utcnow(),
                data_points={
                    "previous_activity_count": 12,
                    "current_activity_count": 8,
                    "decline_percentage": 33.3
                }
            ),
            RiskSignal(
                signal_type="revenue_decline",
                severity="medium",
                description="Revenue decreased by 15%",
                detected_at=datetime.utcnow(),
                data_points={
                    "previous_revenue": 5882353.0,
                    "current_revenue": 5000000.0,
                    "decline_percentage": 15.0
                }
            )
        ],
        risk_level=RiskLevel.MEDIUM,
        priority_score=65.0,
        needs_review=True,
        metadata={
            "scout_version": "1.0.0",
            "execution_time_ms": 450
        }
    )


@pytest.fixture
def mock_historical_context():
    """Create realistic historical context for testing."""
    return HistoricalContext(
        account_id="acc_test_001",
        lookback_days=365,
        timeline=[
            AccountTimeline(
                event_type="deal_won",
                event_date=datetime.utcnow() - timedelta(days=90),
                description="Won Enterprise License deal - $150K",
                impact_score=8.5,
                metadata={"deal_id": "deal_789", "amount": 150000}
            ),
            AccountTimeline(
                event_type="interaction",
                event_date=datetime.utcnow() - timedelta(days=7),
                description="Quarterly Business Review call",
                impact_score=7.0,
                metadata={"activity_type": "call", "duration_minutes": 60}
            ),
            AccountTimeline(
                event_type="support_ticket",
                event_date=datetime.utcnow() - timedelta(days=3),
                description="Critical support ticket resolved",
                impact_score=-3.5,
                metadata={"ticket_id": "TKT-456", "severity": "high"}
            )
        ],
        patterns=[
            PatternRecognition(
                pattern_type="engagement_pattern",
                pattern_name="quarterly_review_cycle",
                confidence=0.85,
                description="Regular QBR calls every 90 days",
                supporting_evidence=[
                    "QBR call 90 days ago",
                    "QBR call 180 days ago",
                    "QBR call 270 days ago"
                ],
                metadata={"cycle_days": 90, "consistency_score": 0.9}
            ),
            PatternRecognition(
                pattern_type="risk_pattern",
                pattern_name="activity_decline",
                confidence=0.75,
                description="Decreasing engagement over last quarter",
                supporting_evidence=[
                    "33% activity decline in last 30 days",
                    "Support tickets increasing"
                ],
                metadata={"trend": "declining", "severity": "medium"}
            )
        ],
        sentiment_trend=SentimentTrend.DECLINING,
        relationship_strength=RelationshipStrength.MODERATE,
        risk_level=RiskLevel.MEDIUM,
        key_insights=[
            "Strong quarterly engagement pattern",
            "Recent activity decline indicates potential risk",
            "Support ticket volume increasing"
        ],
        metadata={
            "analyst_version": "1.0.0",
            "execution_time_ms": 350,
            "data_sources": ["cognee_memory", "zoho_activities"]
        }
    )


@pytest_asyncio.fixture
async def mock_zoho_scout(mock_account_snapshot):
    """Create mock ZohoDataScout with realistic responses."""
    scout = MagicMock(spec=ZohoDataScout)
    scout.get_account_snapshot = AsyncMock(return_value=mock_account_snapshot)
    return scout


@pytest_asyncio.fixture
async def mock_memory_analyst(mock_historical_context):
    """Create mock MemoryAnalyst with realistic responses."""
    analyst = MagicMock(spec=MemoryAnalyst)
    analyst.get_historical_context = AsyncMock(return_value=mock_historical_context)
    return analyst


@pytest_asyncio.fixture
async def approval_manager():
    """Create real ApprovalManager instance."""
    return ApprovalManager()


@pytest_asyncio.fixture
async def orchestrator(mock_zoho_scout, mock_memory_analyst, approval_manager):
    """Create OrchestratorAgent with mocked dependencies."""
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    return OrchestratorAgent(
        session_id=session_id,
        zoho_scout=mock_zoho_scout,
        memory_analyst=mock_memory_analyst,
        approval_manager=approval_manager
    )


# ============================================================================
# COMPLETE WORKFLOW TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_multi_agent_workflow(orchestrator, approval_manager):
    """Test complete workflow: Zoho → Memory → Recommendation → Approval.

    Validates:
    - All agents execute in sequence
    - Context passes between agents
    - Events stream in correct order
    - Approval workflow completes
    - Final output contains all results
    """
    account_id = "acc_test_001"

    # Collect all events
    events = []

    # Execute workflow
    async for event in orchestrator.execute_with_events({
        "account_id": account_id,
        "workflow": "account_analysis",
        "timeout_seconds": 5  # Fast timeout for testing
    }):
        events.append(event)

        # Auto-approve when approval requested
        if event.get("event") == "approval_required":
            approval_data = event.get("data", {})
            rec_id = approval_data.get("recommendation", {}).get("recommendation_id")

            # Find approval request
            for approval_id, approval in approval_manager._active_approvals.items():
                if approval.recommendation_id == rec_id:
                    await approval_manager.respond_to_approval(
                        approval_id=approval_id,
                        action="approve",
                        approved_by="test_user"
                    )
                    break

    # Validate event sequence
    event_types = [e.get("event") for e in events]

    assert "workflow_started" in event_types
    assert "agent_started" in event_types  # At least one agent
    assert "agent_completed" in event_types  # At least one completion
    assert "approval_required" in event_types
    assert "workflow_completed" in event_types

    # Validate workflow_started
    workflow_started = next(e for e in events if e.get("event") == "workflow_started")
    assert workflow_started["data"]["workflow"] == "account_analysis"
    assert workflow_started["data"]["account_id"] == account_id

    # Validate agent execution
    agent_started_events = [e for e in events if e.get("event") == "agent_started"]
    assert len(agent_started_events) >= 2  # At least Zoho and Memory

    # Check Zoho scout executed
    zoho_started = next(
        (e for e in agent_started_events if e["data"]["agent"] == "zoho_scout"),
        None
    )
    assert zoho_started is not None
    assert zoho_started["data"]["step"] == 1

    # Check Memory analyst executed
    memory_started = next(
        (e for e in agent_started_events if e["data"]["agent"] == "memory_analyst"),
        None
    )
    assert memory_started is not None
    assert memory_started["data"]["step"] == 2

    # Validate agent_stream events
    agent_stream_events = [e for e in events if e.get("event") == "agent_stream"]
    assert len(agent_stream_events) >= 2  # Multiple progress updates

    # Validate approval workflow
    approval_required = next(e for e in events if e.get("event") == "approval_required")
    assert "recommendation" in approval_required["data"]
    assert approval_required["data"]["timeout_hours"] > 0

    # Validate workflow completion
    workflow_completed = next(e for e in events if e.get("event") == "workflow_completed")
    final_output = workflow_completed["data"]["final_output"]

    assert final_output["status"] == "completed"
    assert final_output["account_id"] == account_id
    assert "approval" in final_output
    assert final_output["approval"]["status"] == "approved"
    assert "execution_summary" in final_output

    # Validate execution summary
    summary = final_output["execution_summary"]
    assert summary["zoho_data_fetched"] is True
    assert summary["historical_context_retrieved"] is True
    assert summary["recommendations_generated"] > 0
    assert summary["risk_level"] in ["low", "medium", "high", "critical"]
    assert summary["sentiment_trend"] in ["improving", "stable", "declining", "critical"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_with_rejection(orchestrator, approval_manager):
    """Test workflow when user rejects recommendation."""
    account_id = "acc_test_002"

    events = []

    async for event in orchestrator.execute_with_events({
        "account_id": account_id,
        "workflow": "account_analysis",
        "timeout_seconds": 5
    }):
        events.append(event)

        # Reject approval when requested
        if event.get("event") == "approval_required":
            approval_data = event.get("data", {})
            rec_id = approval_data.get("recommendation", {}).get("recommendation_id")

            for approval_id, approval in approval_manager._active_approvals.items():
                if approval.recommendation_id == rec_id:
                    await approval_manager.respond_to_approval(
                        approval_id=approval_id,
                        action="reject",
                        reason="Not the right time for this action",
                        approved_by="test_user"
                    )
                    break

    # Validate rejection handled
    workflow_completed = next(e for e in events if e.get("event") == "workflow_completed")
    final_output = workflow_completed["data"]["final_output"]

    assert final_output["status"] == "rejected"
    assert final_output["approval"]["status"] == "rejected"
    assert final_output["approval"]["reason"] == "Not the right time for this action"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_approval_timeout(orchestrator, approval_manager):
    """Test workflow when approval request times out."""
    account_id = "acc_test_003"

    events = []

    # Don't respond to approval - let it timeout
    async for event in orchestrator.execute_with_events({
        "account_id": account_id,
        "workflow": "account_analysis",
        "timeout_seconds": 1  # Very short timeout
    }):
        events.append(event)

    # Validate timeout handled
    workflow_completed = next(e for e in events if e.get("event") == "workflow_completed")
    final_output = workflow_completed["data"]["final_output"]

    assert final_output["status"] == "timeout"
    assert "timeout" in final_output["message"].lower()


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_zoho_scout_error_handling(mock_memory_analyst, approval_manager):
    """Test error handling when ZohoDataScout fails."""
    # Create scout that raises error
    failing_scout = MagicMock(spec=ZohoDataScout)
    failing_scout.get_account_snapshot = AsyncMock(
        side_effect=Exception("Zoho API connection timeout")
    )

    orchestrator = OrchestratorAgent(
        session_id=f"test_session_{uuid.uuid4().hex[:8]}",
        zoho_scout=failing_scout,
        memory_analyst=mock_memory_analyst,
        approval_manager=approval_manager
    )

    events = []

    with pytest.raises(Exception) as exc_info:
        async for event in orchestrator.execute_with_events({
            "account_id": "acc_test_004",
            "workflow": "account_analysis"
        }):
            events.append(event)

    assert "Zoho API connection timeout" in str(exc_info.value)

    # Validate error event emitted
    error_events = [e for e in events if e.get("event") == "agent_error"]
    assert len(error_events) > 0

    zoho_error = next(
        (e for e in error_events if e["data"]["agent"] == "zoho_scout"),
        None
    )
    assert zoho_error is not None
    assert zoho_error["data"]["error_type"] == "data_fetch_error"
    assert "Zoho API connection timeout" in zoho_error["data"]["error_message"]

    # Workflow should still emit completion event with error status
    workflow_completed = next(
        (e for e in events if e.get("event") == "workflow_completed"),
        None
    )
    assert workflow_completed is not None
    assert workflow_completed["data"]["final_output"]["status"] == "error"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_memory_analyst_error_handling(mock_zoho_scout, approval_manager):
    """Test error handling when MemoryAnalyst fails."""
    # Create analyst that raises error
    failing_analyst = MagicMock(spec=MemoryAnalyst)
    failing_analyst.get_historical_context = AsyncMock(
        side_effect=Exception("Cognee connection lost")
    )

    orchestrator = OrchestratorAgent(
        session_id=f"test_session_{uuid.uuid4().hex[:8]}",
        zoho_scout=mock_zoho_scout,
        memory_analyst=failing_analyst,
        approval_manager=approval_manager
    )

    events = []

    with pytest.raises(Exception) as exc_info:
        async for event in orchestrator.execute_with_events({
            "account_id": "acc_test_005",
            "workflow": "account_analysis"
        }):
            events.append(event)

    assert "Cognee connection lost" in str(exc_info.value)

    # Validate error event
    error_events = [e for e in events if e.get("event") == "agent_error"]
    memory_error = next(
        (e for e in error_events if e["data"]["agent"] == "memory_analyst"),
        None
    )
    assert memory_error is not None
    assert memory_error["data"]["error_type"] == "memory_retrieval_error"


# ============================================================================
# CONTEXT PASSING TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_context_passing_between_agents(orchestrator, approval_manager):
    """Test that context is properly passed between agents."""
    account_id = "acc_test_006"

    events = []

    async for event in orchestrator.execute_with_events({
        "account_id": account_id,
        "workflow": "account_analysis",
        "timeout_seconds": 5
    }):
        events.append(event)

        if event.get("event") == "approval_required":
            approval_data = event.get("data", {})
            rec_id = approval_data.get("recommendation", {}).get("recommendation_id")

            for approval_id, approval in approval_manager._active_approvals.items():
                if approval.recommendation_id == rec_id:
                    await approval_manager.respond_to_approval(
                        approval_id=approval_id,
                        action="approve",
                        approved_by="test_user"
                    )
                    break

    # Extract agent outputs
    zoho_completed = next(
        (e for e in events if e.get("event") == "agent_completed" and e["data"]["agent"] == "zoho_scout"),
        None
    )

    memory_completed = next(
        (e for e in events if e.get("event") == "agent_completed" and e["data"]["agent"] == "memory_analyst"),
        None
    )

    workflow_completed = next(e for e in events if e.get("event") == "workflow_completed")

    # Validate context accumulation
    assert zoho_completed is not None
    assert zoho_completed["data"]["output"]["status"] == "success"
    assert "risk_level" in zoho_completed["data"]["output"]

    assert memory_completed is not None
    assert memory_completed["data"]["output"]["status"] == "success"
    assert "sentiment_trend" in memory_completed["data"]["output"]

    # Final output should contain data from all agents
    final_output = workflow_completed["data"]["final_output"]
    summary = final_output["execution_summary"]

    assert summary["risk_level"] is not None
    assert summary["sentiment_trend"] is not None


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_workflow_performance(orchestrator, approval_manager):
    """Test that complete workflow executes within performance targets.

    Performance Requirements:
    - Complete workflow < 10 seconds (with mocks)
    - Event streaming latency < 200ms
    """
    import time

    account_id = "acc_test_007"

    start_time = time.time()
    event_timestamps = []

    async for event in orchestrator.execute_with_events({
        "account_id": account_id,
        "workflow": "account_analysis",
        "timeout_seconds": 5
    }):
        event_timestamps.append(time.time())

        # Auto-approve
        if event.get("event") == "approval_required":
            approval_data = event.get("data", {})
            rec_id = approval_data.get("recommendation", {}).get("recommendation_id")

            for approval_id, approval in approval_manager._active_approvals.items():
                if approval.recommendation_id == rec_id:
                    await approval_manager.respond_to_approval(
                        approval_id=approval_id,
                        action="approve",
                        approved_by="test_user"
                    )
                    break

    end_time = time.time()
    total_duration = end_time - start_time

    # Validate total workflow time
    assert total_duration < 10.0, f"Workflow took {total_duration:.2f}s, expected <10s"

    # Validate event streaming latency
    if len(event_timestamps) > 1:
        max_gap = max(
            event_timestamps[i+1] - event_timestamps[i]
            for i in range(len(event_timestamps) - 1)
        )
        assert max_gap < 0.2, f"Event gap {max_gap:.3f}s exceeds 200ms latency target"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_concurrent_workflows(mock_zoho_scout, mock_memory_analyst, approval_manager):
    """Test multiple concurrent workflows execute correctly."""
    account_ids = [f"acc_concurrent_{i}" for i in range(5)]

    async def run_workflow(account_id: str):
        """Run single workflow."""
        orchestrator = OrchestratorAgent(
            session_id=f"session_{account_id}",
            zoho_scout=mock_zoho_scout,
            memory_analyst=mock_memory_analyst,
            approval_manager=approval_manager
        )

        events = []
        async for event in orchestrator.execute_with_events({
            "account_id": account_id,
            "workflow": "account_analysis",
            "timeout_seconds": 5
        }):
            events.append(event)

            if event.get("event") == "approval_required":
                approval_data = event.get("data", {})
                rec_id = approval_data.get("recommendation", {}).get("recommendation_id")

                for approval_id, approval in approval_manager._active_approvals.items():
                    if approval.recommendation_id == rec_id:
                        await approval_manager.respond_to_approval(
                            approval_id=approval_id,
                            action="approve",
                            approved_by="test_user"
                        )
                        break

        return events

    # Run all workflows concurrently
    import time
    start = time.time()

    results = await asyncio.gather(
        *[run_workflow(acc_id) for acc_id in account_ids],
        return_exceptions=True
    )

    elapsed = time.time() - start

    # Validate all workflows completed
    assert len(results) == 5
    assert all(not isinstance(r, Exception) for r in results)

    # Validate each workflow produced events
    for events in results:
        assert len(events) > 0
        assert any(e.get("event") == "workflow_completed" for e in events)

    # Concurrent execution should be faster than sequential
    # (5 workflows * ~2s each = ~10s sequential, should be <5s concurrent)
    assert elapsed < 8.0, f"Concurrent workflows took {elapsed:.2f}s, expected <8s"


# ============================================================================
# MISSING ACCOUNT ID TEST
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_missing_account_id_error(orchestrator):
    """Test that missing account_id raises appropriate error."""
    with pytest.raises(ValueError) as exc_info:
        async for event in orchestrator.execute_with_events({
            "workflow": "account_analysis"
            # Missing account_id
        }):
            pass

    assert "account_id is required" in str(exc_info.value)


# ============================================================================
# EVENT SCHEMA VALIDATION
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_event_schema_validation(orchestrator, approval_manager):
    """Test that all emitted events conform to AG UI Protocol schema."""
    account_id = "acc_test_008"

    events = []

    async for event in orchestrator.execute_with_events({
        "account_id": account_id,
        "workflow": "account_analysis",
        "timeout_seconds": 5
    }):
        events.append(event)

        # Validate event structure
        assert "event" in event, "Event missing 'event' field"
        assert "data" in event, "Event missing 'data' field"
        assert "timestamp" in event, "Event missing 'timestamp' field"

        # Validate event-specific schemas
        event_type = event["event"]
        data = event["data"]

        if event_type == "workflow_started":
            assert "workflow" in data
            assert "account_id" in data
            assert "session_id" in data

        elif event_type == "agent_started":
            assert "agent" in data
            assert "step" in data

        elif event_type == "agent_stream":
            assert "agent" in data
            assert "content" in data
            assert "content_type" in data

        elif event_type == "agent_completed":
            assert "agent" in data
            assert "step" in data
            assert "duration_ms" in data

        elif event_type == "agent_error":
            assert "agent" in data
            assert "step" in data
            assert "error_type" in data
            assert "error_message" in data

        elif event_type == "approval_required":
            assert "recommendation" in data
            assert "timeout_hours" in data

            # Auto-approve
            rec_id = data["recommendation"]["recommendation_id"]
            for approval_id, approval in approval_manager._active_approvals.items():
                if approval.recommendation_id == rec_id:
                    await approval_manager.respond_to_approval(
                        approval_id=approval_id,
                        action="approve",
                        approved_by="test_user"
                    )
                    break

        elif event_type == "workflow_completed":
            assert "workflow" in data
            assert "account_id" in data
            assert "final_output" in data
            assert "total_duration_ms" in data

    assert len(events) >= 5, "Should emit multiple events"
