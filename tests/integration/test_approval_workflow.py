"""Integration Tests for Approval Workflow.

Tests approval request/response cycle with timeout and state management.

Week 6-9 Critical Implementation - SPARC V3 Compliance

Test Coverage:
- Approval request creation and tracking
- Approval responses (approve/reject/modify)
- Timeout handling (default 300s)
- Concurrent approval requests
- Approval with modified data
- State management and cleanup
- Error conditions (expired/duplicate/invalid)
- Performance (response latency, concurrent requests)

Test Strategy:
- Real ApprovalManager and ApprovalRequest instances
- AsyncIO event-based waiting
- Realistic timeout scenarios
- Thread safety validation
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from src.events.approval_manager import (
    ApprovalManager,
    ApprovalRequest,
    ApprovalStatus
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest_asyncio.fixture
async def approval_manager():
    """Create fresh ApprovalManager instance."""
    return ApprovalManager()


@pytest.fixture
def sample_recommendation():
    """Generate sample recommendation data."""
    return {
        "recommendation_id": f"rec_{uuid.uuid4().hex[:8]}",
        "account_id": "acc_test_001",
        "action_type": "schedule_qbr",
        "priority": "high",
        "recommendation": "Schedule Quarterly Business Review within 2 weeks",
        "reasoning": "Account showing declining engagement (-33% activity). QBR will strengthen relationship.",
        "expected_impact": "Prevent churn, increase engagement by 40%",
        "confidence_score": 0.85,
        "supporting_data": {
            "current_health_score": 65,
            "trend": "declining",
            "last_qbr": "90 days ago"
        }
    }


# ============================================================================
# APPROVAL REQUEST CREATION TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_approval_request(approval_manager, sample_recommendation):
    """Test creating approval request and tracking it."""
    run_id = f"run_{uuid.uuid4().hex[:8]}"

    approval = await approval_manager.create_approval_request(
        recommendation_id=sample_recommendation["recommendation_id"],
        recommendation=sample_recommendation,
        run_id=run_id,
        timeout_seconds=300
    )

    # Validate approval created
    assert approval.approval_id is not None
    assert approval.recommendation_id == sample_recommendation["recommendation_id"]
    assert approval.run_id == run_id
    assert approval.status == ApprovalStatus.PENDING
    assert approval.timeout_seconds == 300

    # Should be tracked in manager
    tracked = await approval_manager.get_approval_request(approval.approval_id)
    assert tracked is not None
    assert tracked.approval_id == approval.approval_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_approval_request_default_timeout(approval_manager, sample_recommendation):
    """Test approval request uses default 300s timeout."""
    approval = await approval_manager.create_approval_request(
        recommendation_id=sample_recommendation["recommendation_id"],
        recommendation=sample_recommendation,
        run_id=f"run_{uuid.uuid4().hex[:8]}"
        # No timeout_seconds specified
    )

    # Should use default
    assert approval.timeout_seconds == 300

    # Expiry should be ~300s from now
    time_until_expiry = (approval.expires_at - approval.created_at).total_seconds()
    assert 299 <= time_until_expiry <= 301


# ============================================================================
# APPROVAL RESPONSE TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_approve_recommendation(approval_manager, sample_recommendation):
    """Test approving a recommendation."""
    approval = await approval_manager.create_approval_request(
        recommendation_id=sample_recommendation["recommendation_id"],
        recommendation=sample_recommendation,
        run_id=f"run_{uuid.uuid4().hex[:8]}",
        timeout_seconds=60
    )

    # Approve
    await approval_manager.respond_to_approval(
        approval_id=approval.approval_id,
        action="approve",
        approved_by="test_user@example.com",
        reason="Good recommendation, proceed"
    )

    # Validate approval state
    assert approval.status == ApprovalStatus.APPROVED
    assert approval.action == "approve"
    assert approval.approved_by == "test_user@example.com"
    assert approval.reason == "Good recommendation, proceed"
    assert approval.responded_at is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_reject_recommendation(approval_manager, sample_recommendation):
    """Test rejecting a recommendation."""
    approval = await approval_manager.create_approval_request(
        recommendation_id=sample_recommendation["recommendation_id"],
        recommendation=sample_recommendation,
        run_id=f"run_{uuid.uuid4().hex[:8]}",
        timeout_seconds=60
    )

    # Reject
    await approval_manager.respond_to_approval(
        approval_id=approval.approval_id,
        action="reject",
        approved_by="test_user@example.com",
        reason="Not the right time for QBR"
    )

    # Validate rejection state
    assert approval.status == ApprovalStatus.REJECTED
    assert approval.action == "reject"
    assert approval.reason == "Not the right time for QBR"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_modify_recommendation(approval_manager, sample_recommendation):
    """Test modifying and approving a recommendation."""
    approval = await approval_manager.create_approval_request(
        recommendation_id=sample_recommendation["recommendation_id"],
        recommendation=sample_recommendation,
        run_id=f"run_{uuid.uuid4().hex[:8]}",
        timeout_seconds=60
    )

    # Modify
    modified_data = sample_recommendation.copy()
    modified_data["action_type"] = "schedule_call"  # Changed from QBR to call
    modified_data["recommendation"] = "Schedule quick check-in call instead"

    await approval_manager.respond_to_approval(
        approval_id=approval.approval_id,
        action="modify",
        modified_data=modified_data,
        approved_by="test_user@example.com",
        reason="Let's start with a call instead of full QBR"
    )

    # Validate modification state
    assert approval.status == ApprovalStatus.MODIFIED
    assert approval.action == "modify"
    assert approval.modified_data is not None
    assert approval.modified_data["action_type"] == "schedule_call"


# ============================================================================
# WAIT FOR RESPONSE TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_wait_for_approval_response(approval_manager, sample_recommendation):
    """Test waiting for approval response."""
    approval = await approval_manager.create_approval_request(
        recommendation_id=sample_recommendation["recommendation_id"],
        recommendation=sample_recommendation,
        run_id=f"run_{uuid.uuid4().hex[:8]}",
        timeout_seconds=60
    )

    # Respond in background after delay
    async def delayed_response():
        await asyncio.sleep(0.1)
        await approval_manager.respond_to_approval(
            approval_id=approval.approval_id,
            action="approve",
            approved_by="test_user"
        )

    # Start background task
    asyncio.create_task(delayed_response())

    # Wait for response
    response_received = await approval.wait_for_response(timeout=5.0)

    # Should receive response
    assert response_received is True
    assert approval.status == ApprovalStatus.APPROVED


@pytest.mark.asyncio
@pytest.mark.integration
async def test_wait_for_response_timeout(approval_manager, sample_recommendation):
    """Test approval timeout when no response received."""
    approval = await approval_manager.create_approval_request(
        recommendation_id=sample_recommendation["recommendation_id"],
        recommendation=sample_recommendation,
        run_id=f"run_{uuid.uuid4().hex[:8]}",
        timeout_seconds=1  # Very short timeout
    )

    # Don't respond - let it timeout
    response_received = await approval.wait_for_response(timeout=1.0)

    # Should timeout
    assert response_received is False
    assert approval.status == ApprovalStatus.TIMEOUT


# ============================================================================
# CONCURRENT APPROVAL TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_concurrent_approval_requests(approval_manager):
    """Test handling multiple concurrent approval requests."""
    num_requests = 10

    # Create multiple approval requests
    approvals = []
    for i in range(num_requests):
        rec = {
            "recommendation_id": f"rec_{i}",
            "account_id": f"acc_{i}",
            "action_type": "review",
            "priority": "medium",
            "recommendation": f"Recommendation {i}",
            "reasoning": f"Reason {i}",
            "expected_impact": f"Impact {i}"
        }

        approval = await approval_manager.create_approval_request(
            recommendation_id=rec["recommendation_id"],
            recommendation=rec,
            run_id=f"run_{i}",
            timeout_seconds=60
        )
        approvals.append(approval)

    # All should be pending
    assert all(a.status == ApprovalStatus.PENDING for a in approvals)

    # Respond to all concurrently
    async def respond_to_approval(idx: int):
        """Respond to single approval."""
        await asyncio.sleep(0.01 * idx)  # Stagger slightly
        await approval_manager.respond_to_approval(
            approval_id=approvals[idx].approval_id,
            action="approve" if idx % 2 == 0 else "reject",
            approved_by=f"user_{idx}"
        )

    # Run all responses concurrently
    await asyncio.gather(
        *[respond_to_approval(i) for i in range(num_requests)]
    )

    # Validate all responded
    assert all(a.status != ApprovalStatus.PENDING for a in approvals)

    # Check split between approve/reject
    approved = sum(1 for a in approvals if a.status == ApprovalStatus.APPROVED)
    rejected = sum(1 for a in approvals if a.status == ApprovalStatus.REJECTED)

    assert approved == 5  # Even indices
    assert rejected == 5  # Odd indices


# ============================================================================
# ERROR CONDITION TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_respond_to_expired_approval(approval_manager, sample_recommendation):
    """Test responding to expired approval raises error."""
    approval = await approval_manager.create_approval_request(
        recommendation_id=sample_recommendation["recommendation_id"],
        recommendation=sample_recommendation,
        run_id=f"run_{uuid.uuid4().hex[:8]}",
        timeout_seconds=1  # Very short
    )

    # Wait for expiry
    await asyncio.sleep(1.5)

    # Try to respond to expired approval
    with pytest.raises(ValueError, match="expired"):
        await approval_manager.respond_to_approval(
            approval_id=approval.approval_id,
            action="approve",
            approved_by="test_user"
        )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_respond_to_nonexistent_approval(approval_manager):
    """Test responding to non-existent approval raises error."""
    fake_approval_id = "approval_nonexistent"

    with pytest.raises(ValueError, match="not found"):
        await approval_manager.respond_to_approval(
            approval_id=fake_approval_id,
            action="approve",
            approved_by="test_user"
        )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_respond_twice_to_same_approval(approval_manager, sample_recommendation):
    """Test responding twice to same approval raises error."""
    approval = await approval_manager.create_approval_request(
        recommendation_id=sample_recommendation["recommendation_id"],
        recommendation=sample_recommendation,
        run_id=f"run_{uuid.uuid4().hex[:8]}",
        timeout_seconds=60
    )

    # First response
    await approval_manager.respond_to_approval(
        approval_id=approval.approval_id,
        action="approve",
        approved_by="test_user"
    )

    # Second response should fail
    with pytest.raises(ValueError, match="already"):
        await approval_manager.respond_to_approval(
            approval_id=approval.approval_id,
            action="reject",
            approved_by="test_user"
        )


# ============================================================================
# CLEANUP TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_cleanup_expired_approvals(approval_manager):
    """Test cleanup of expired approval requests."""
    # Create some approvals with short timeout
    for i in range(5):
        rec = {
            "recommendation_id": f"rec_{i}",
            "account_id": f"acc_{i}",
            "action_type": "review",
            "priority": "medium",
            "recommendation": f"Rec {i}",
            "reasoning": "Test",
            "expected_impact": "Test"
        }

        await approval_manager.create_approval_request(
            recommendation_id=rec["recommendation_id"],
            recommendation=rec,
            run_id=f"run_{i}",
            timeout_seconds=1  # Very short
        )

    # Initial count
    initial_count = await approval_manager.get_active_count()
    assert initial_count == 5

    # Wait for expiry
    await asyncio.sleep(1.5)

    # Cleanup
    await approval_manager.cleanup_expired()

    # Count should be zero (all expired and cleaned)
    final_count = await approval_manager.get_active_count()
    assert final_count == 0


# ============================================================================
# STATE MANAGEMENT TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_approval_to_dict_serialization(approval_manager, sample_recommendation):
    """Test approval serialization to dictionary."""
    approval = await approval_manager.create_approval_request(
        recommendation_id=sample_recommendation["recommendation_id"],
        recommendation=sample_recommendation,
        run_id=f"run_{uuid.uuid4().hex[:8]}",
        timeout_seconds=300
    )

    # Approve
    await approval_manager.respond_to_approval(
        approval_id=approval.approval_id,
        action="approve",
        approved_by="test_user@example.com",
        reason="LGTM"
    )

    # Serialize
    approval_dict = approval.to_dict()

    # Validate structure
    assert approval_dict["approval_id"] == approval.approval_id
    assert approval_dict["recommendation_id"] == sample_recommendation["recommendation_id"]
    assert approval_dict["status"] == "approved"
    assert approval_dict["action"] == "approve"
    assert approval_dict["approved_by"] == "test_user@example.com"
    assert approval_dict["reason"] == "LGTM"
    assert approval_dict["timeout_seconds"] == 300

    # Timestamps should be ISO format
    assert isinstance(approval_dict["created_at"], str)
    assert isinstance(approval_dict["expires_at"], str)
    assert isinstance(approval_dict["responded_at"], str)

    # Should be JSON serializable
    import json
    json_str = json.dumps(approval_dict)
    assert len(json_str) > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_active_count(approval_manager, sample_recommendation):
    """Test tracking active approval count."""
    # Initially zero
    initial_count = await approval_manager.get_active_count()
    assert initial_count == 0

    # Create 3 approvals
    approvals = []
    for i in range(3):
        rec = sample_recommendation.copy()
        rec["recommendation_id"] = f"rec_{i}"

        approval = await approval_manager.create_approval_request(
            recommendation_id=rec["recommendation_id"],
            recommendation=rec,
            run_id=f"run_{i}",
            timeout_seconds=60
        )
        approvals.append(approval)

    # Count should be 3
    count_after_create = await approval_manager.get_active_count()
    assert count_after_create == 3

    # Respond to one
    await approval_manager.respond_to_approval(
        approval_id=approvals[0].approval_id,
        action="approve",
        approved_by="test_user"
    )

    # Count should be 2 (only pending ones)
    count_after_response = await approval_manager.get_active_count()
    assert count_after_response == 2


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_approval_response_latency(approval_manager, sample_recommendation):
    """Test approval response latency."""
    import time

    approval = await approval_manager.create_approval_request(
        recommendation_id=sample_recommendation["recommendation_id"],
        recommendation=sample_recommendation,
        run_id=f"run_{uuid.uuid4().hex[:8]}",
        timeout_seconds=60
    )

    # Respond in background
    async def delayed_response():
        await asyncio.sleep(0.05)  # 50ms delay
        start = time.time()
        await approval_manager.respond_to_approval(
            approval_id=approval.approval_id,
            action="approve",
            approved_by="test_user"
        )
        return time.time() - start

    response_task = asyncio.create_task(delayed_response())

    # Wait for response
    wait_start = time.time()
    response_received = await approval.wait_for_response(timeout=5.0)
    wait_latency = time.time() - wait_start

    response_latency = await response_task

    # Validate latency
    assert response_received is True

    # Wait should complete quickly after response (within 100ms)
    assert wait_latency < 0.2, f"Wait latency {wait_latency:.3f}s too high"

    # Response processing should be fast (<10ms)
    assert response_latency < 0.01, f"Response latency {response_latency:.3f}s too high"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_high_volume_approval_processing(approval_manager):
    """Test processing high volume of approvals."""
    import time

    num_approvals = 100

    start_time = time.time()

    # Create all approvals
    approvals = []
    for i in range(num_approvals):
        rec = {
            "recommendation_id": f"rec_{i}",
            "account_id": f"acc_{i}",
            "action_type": "review",
            "priority": "medium",
            "recommendation": f"Recommendation {i}",
            "reasoning": f"Reason {i}",
            "expected_impact": f"Impact {i}"
        }

        approval = await approval_manager.create_approval_request(
            recommendation_id=rec["recommendation_id"],
            recommendation=rec,
            run_id=f"run_{i}",
            timeout_seconds=60
        )
        approvals.append(approval)

    create_time = time.time() - start_time

    # Respond to all
    respond_start = time.time()

    await asyncio.gather(
        *[
            approval_manager.respond_to_approval(
                approval_id=approvals[i].approval_id,
                action="approve",
                approved_by=f"user_{i}"
            )
            for i in range(num_approvals)
        ]
    )

    respond_time = time.time() - respond_start

    total_time = time.time() - start_time

    # Performance assertions
    # Creating 100 approvals should be fast (<1s)
    assert create_time < 1.0, f"Create time {create_time:.2f}s too slow"

    # Responding to 100 approvals concurrently should be fast (<2s)
    assert respond_time < 2.0, f"Respond time {respond_time:.2f}s too slow"

    # Total time should be reasonable (<3s)
    assert total_time < 3.0, f"Total time {total_time:.2f}s too slow"

    # All should be approved
    assert all(a.status == ApprovalStatus.APPROVED for a in approvals)


# ============================================================================
# TIMEOUT PRECISION TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_timeout_precision(approval_manager, sample_recommendation):
    """Test that timeout occurs at expected time."""
    import time

    timeout_seconds = 2

    approval = await approval_manager.create_approval_request(
        recommendation_id=sample_recommendation["recommendation_id"],
        recommendation=sample_recommendation,
        run_id=f"run_{uuid.uuid4().hex[:8]}",
        timeout_seconds=timeout_seconds
    )

    # Wait for timeout
    start = time.time()
    response_received = await approval.wait_for_response(timeout=timeout_seconds)
    elapsed = time.time() - start

    # Should timeout
    assert response_received is False
    assert approval.status == ApprovalStatus.TIMEOUT

    # Timeout should occur within ±0.5s of expected time
    assert timeout_seconds - 0.5 < elapsed < timeout_seconds + 0.5, \
        f"Timeout at {elapsed:.2f}s, expected ~{timeout_seconds}s"


# ============================================================================
# METADATA TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_approval_metadata_preservation(approval_manager):
    """Test that recommendation metadata is preserved through approval."""
    recommendation = {
        "recommendation_id": f"rec_{uuid.uuid4().hex[:8]}",
        "account_id": "acc_test",
        "action_type": "schedule_qbr",
        "priority": "high",
        "recommendation": "Schedule QBR",
        "reasoning": "Engagement declining",
        "expected_impact": "Prevent churn",
        "metadata": {
            "confidence_score": 0.92,
            "model_version": "v2.1.0",
            "data_sources": ["zoho", "cognee"],
            "execution_time_ms": 450
        }
    }

    approval = await approval_manager.create_approval_request(
        recommendation_id=recommendation["recommendation_id"],
        recommendation=recommendation,
        run_id=f"run_{uuid.uuid4().hex[:8]}",
        timeout_seconds=60
    )

    # Metadata should be preserved
    assert approval.recommendation["metadata"]["confidence_score"] == 0.92
    assert approval.recommendation["metadata"]["model_version"] == "v2.1.0"

    # Approve
    await approval_manager.respond_to_approval(
        approval_id=approval.approval_id,
        action="approve",
        approved_by="test_user"
    )

    # Serialize and check metadata still present
    approval_dict = approval.to_dict()
    assert approval_dict["recommendation"]["metadata"]["confidence_score"] == 0.92
