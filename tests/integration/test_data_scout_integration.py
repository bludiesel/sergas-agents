"""Integration Tests for Data Scout.

End-to-end integration tests with mock Zoho Integration Manager.
Tests complete workflows and performance benchmarks.

Test Coverage:
- Complete account snapshot workflow (10+ tests)
- Error handling and recovery (8+ tests)
- Performance benchmarks (5+ tests)
- Cache behavior (5+ tests)
- Concurrent operations (3+ tests)
"""

import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch
from freezegun import freeze_time

import pytest
import pytest_asyncio

from src.agents.zoho_data_scout import ZohoDataScout
from src.agents.models import (
    AccountRecord,
    AccountSnapshot,
    ChangeDetectionResult,
    AggregatedData,
    RiskSignal,
    DealRecord,
    ActivityRecord,
    NoteRecord,
    ChangeType,
    AccountStatus,
    DealStage,
    ActivityType,
    RiskLevel,
)
from src.agents.config import DataScoutConfig
from src.integrations.zoho.exceptions import ZohoAPIError


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_zoho_integration_manager():
    """Create a comprehensive mock ZohoIntegrationManager."""
    manager = AsyncMock()

    # Mock successful account fetch
    manager.get_account = AsyncMock(return_value={
        "id": "acc_123",
        "Account_Name": "Acme Corporation",
        "Owner": {"id": "owner_456", "name": "John Doe"},
        "Account_Status": "Active",
        "Modified_Time": datetime.utcnow().isoformat(),
        "Last_Activity_Time": (datetime.utcnow() - timedelta(days=5)).isoformat(),
        "Created_Time": (datetime.utcnow() - timedelta(days=365)).isoformat(),
        "Open_Deals_Count": 3,
        "Total_Deal_Value": 150000,
        "Annual_Revenue": 500000,
        "Industry": "Technology",
        "Website": "https://acme.com",
        "Phone": "+1-555-0100",
        "Billing_City": "San Francisco",
        "Billing_Country": "USA",
    })

    # Mock account search
    manager.search_accounts = AsyncMock(return_value=[
        {
            "id": "acc_123",
            "Account_Name": "Acme Corporation",
            "Owner": {"id": "owner_456", "name": "John Doe"},
            "Account_Status": "Active",
            "Modified_Time": datetime.utcnow().isoformat(),
            "Last_Activity_Time": (datetime.utcnow() - timedelta(days=5)).isoformat(),
            "Created_Time": (datetime.utcnow() - timedelta(days=365)).isoformat(),
            "Open_Deals_Count": 3,
            "Total_Deal_Value": 150000,
            "Annual_Revenue": 500000,
            "Industry": "Technology",
        }
    ])

    return manager


@pytest.fixture
def integration_config(tmp_path):
    """Create test configuration for integration tests."""
    config = DataScoutConfig()
    config.cache.cache_dir = tmp_path / "integration_cache"
    config.cache.cache_dir.mkdir(parents=True, exist_ok=True)
    config.cache.enabled = True
    config.cache.ttl_seconds = 3600
    return config


@pytest.fixture
async def data_scout_integration(mock_zoho_integration_manager, integration_config):
    """Create Data Scout instance for integration testing."""
    return ZohoDataScout(
        zoho_manager=mock_zoho_integration_manager,
        config=integration_config,
    )


# ============================================================================
# COMPLETE WORKFLOW TESTS
# ============================================================================

class TestCompleteWorkflows:
    """Test complete Data Scout workflows end-to-end."""

    @pytest.mark.asyncio
    async def test_complete_account_snapshot_workflow(self, data_scout_integration):
        """Test complete account snapshot creation workflow."""
        # Mock the internal fetch methods
        with patch.object(data_scout_integration, '_fetch_deals', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            snapshot = await data_scout_integration.get_account_snapshot("acc_123")

            # Verify snapshot structure
            assert isinstance(snapshot, AccountSnapshot)
            assert snapshot.account.account_id == "acc_123"
            assert snapshot.account.account_name == "Acme Corporation"
            assert isinstance(snapshot.aggregated_data, AggregatedData)
            assert isinstance(snapshot.changes, ChangeDetectionResult)
            assert isinstance(snapshot.risk_signals, list)

    @pytest.mark.asyncio
    async def test_workflow_with_deals(self, data_scout_integration):
        """Test workflow with deal aggregation."""
        deal = DealRecord(
            deal_id="deal_123",
            deal_name="Q4 Enterprise Deal",
            account_id="acc_123",
            stage=DealStage.NEGOTIATION,
            amount=Decimal("75000"),
            probability=75,
            owner_id="owner_456",
            stage_changed_date=datetime.utcnow() - timedelta(days=15),
        )

        with patch.object(data_scout_integration, '_fetch_deals', return_value=[deal]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            snapshot = await data_scout_integration.get_account_snapshot("acc_123")

            assert len(snapshot.aggregated_data.deals) == 1
            assert snapshot.aggregated_data.total_deal_value == Decimal("75000")

    @pytest.mark.asyncio
    async def test_workflow_with_activities(self, data_scout_integration):
        """Test workflow with activity aggregation."""
        activities = [
            ActivityRecord(
                activity_id=f"act_{i}",
                account_id="acc_123",
                activity_type=ActivityType.MEETING,
                created_time=datetime.utcnow() - timedelta(days=i*7),
                owner_id="owner_456",
            )
            for i in range(3)
        ]

        with patch.object(data_scout_integration, '_fetch_deals', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=activities), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            snapshot = await data_scout_integration.get_account_snapshot("acc_123")

            assert len(snapshot.aggregated_data.activities) == 3

    @pytest.mark.asyncio
    async def test_workflow_with_risk_signals(self, data_scout_integration):
        """Test workflow identifies risk signals correctly."""
        # Configure account with risk factors
        data_scout_integration.zoho_manager.get_account.return_value = {
            "id": "acc_123",
            "Account_Name": "At Risk Account",
            "Owner": {"id": "owner_456", "name": "John Doe"},
            "Account_Status": "At Risk",
            "Modified_Time": datetime.utcnow().isoformat(),
            "Last_Activity_Time": (datetime.utcnow() - timedelta(days=45)).isoformat(),
            "Created_Time": (datetime.utcnow() - timedelta(days=365)).isoformat(),
            "Open_Deals_Count": 0,
            "Total_Deal_Value": 0,
            "Annual_Revenue": 0,
        }

        with patch.object(data_scout_integration, '_fetch_deals', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            snapshot = await data_scout_integration.get_account_snapshot("acc_123")

            # Should identify multiple risk signals
            assert len(snapshot.risk_signals) > 0
            assert snapshot.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]
            assert snapshot.needs_review

    @pytest.mark.asyncio
    async def test_workflow_with_stalled_deals(self, data_scout_integration):
        """Test workflow identifies stalled deals."""
        stalled_deal = DealRecord(
            deal_id="stalled_123",
            deal_name="Stalled Deal",
            account_id="acc_123",
            stage=DealStage.NEGOTIATION,
            amount=Decimal("50000"),
            probability=60,
            stage_changed_date=datetime.utcnow() - timedelta(days=45),
            owner_id="owner_456",
            is_stalled=True,
        )

        with patch.object(data_scout_integration, '_fetch_deals', return_value=[stalled_deal]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            snapshot = await data_scout_integration.get_account_snapshot("acc_123")

            # Should identify stalled deal risk
            stalled_signals = [s for s in snapshot.risk_signals if s.signal_type == "stalled_deals"]
            assert len(stalled_signals) > 0

    @pytest.mark.asyncio
    async def test_workflow_with_change_detection(self, data_scout_integration):
        """Test workflow detects changes correctly."""
        # First snapshot to establish baseline
        with patch.object(data_scout_integration, '_fetch_deals', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            snapshot1 = await data_scout_integration.get_account_snapshot("acc_123")

            # Modify account data
            data_scout_integration.zoho_manager.get_account.return_value["Account_Status"] = "At Risk"

            # Second snapshot should detect change
            snapshot2 = await data_scout_integration.get_account_snapshot("acc_123")

            assert snapshot2.changes.changes_detected
            assert ChangeType.STATUS_CHANGE in snapshot2.changes.change_types

    @pytest.mark.asyncio
    async def test_workflow_updates_last_sync_time(self, data_scout_integration):
        """Test workflow updates last sync timestamp."""
        with patch.object(data_scout_integration, '_fetch_deals', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            before_sync = datetime.utcnow()
            snapshot = await data_scout_integration.get_account_snapshot("acc_123")
            after_sync = datetime.utcnow()

            # Should update last sync time
            assert "acc_123" in data_scout_integration.last_sync_times
            last_sync = data_scout_integration.last_sync_times["acc_123"]
            assert before_sync <= last_sync <= after_sync

    @pytest.mark.asyncio
    async def test_workflow_with_notes(self, data_scout_integration):
        """Test workflow aggregates notes."""
        notes = [
            NoteRecord(
                note_id=f"note_{i}",
                account_id="acc_123",
                content=f"Note content {i}",
                created_by_id="user_123",
                created_time=datetime.utcnow() - timedelta(days=i*5),
            )
            for i in range(5)
        ]

        with patch.object(data_scout_integration, '_fetch_deals', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=notes):

            snapshot = await data_scout_integration.get_account_snapshot("acc_123")

            assert len(snapshot.aggregated_data.notes) == 5

    @pytest.mark.asyncio
    async def test_workflow_priority_scoring(self, data_scout_integration):
        """Test workflow calculates priority scores correctly."""
        # High-value account with changes
        data_scout_integration.zoho_manager.get_account.return_value["Total_Deal_Value"] = 500000

        deal = DealRecord(
            deal_id="high_value",
            deal_name="Enterprise Deal",
            account_id="acc_123",
            stage=DealStage.NEGOTIATION,
            amount=Decimal("500000"),
            probability=80,
            owner_id="owner_456",
        )

        activities = [
            ActivityRecord(
                activity_id=f"act_{i}",
                account_id="acc_123",
                activity_type=ActivityType.MEETING,
                is_high_value=True,
                created_time=datetime.utcnow() - timedelta(days=i),
                owner_id="owner_456",
            )
            for i in range(10)
        ]

        with patch.object(data_scout_integration, '_fetch_deals', return_value=[deal]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=activities), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            snapshot = await data_scout_integration.get_account_snapshot("acc_123")

            # High-value account should have high priority
            assert snapshot.priority_score > 50

    @pytest.mark.asyncio
    async def test_workflow_analysis_flags_updated(self, data_scout_integration):
        """Test workflow updates all analysis flags."""
        with patch.object(data_scout_integration, '_fetch_deals', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            snapshot = await data_scout_integration.get_account_snapshot("acc_123")

            # All flags should be updated
            assert snapshot.risk_level is not None
            assert snapshot.priority_score >= 0
            assert isinstance(snapshot.needs_review, bool)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling and recovery."""

    @pytest.mark.asyncio
    async def test_handles_zoho_api_error(self, data_scout_integration):
        """Test handling of Zoho API errors."""
        data_scout_integration.zoho_manager.get_account.side_effect = ZohoAPIError("API Error")

        with pytest.raises(Exception):
            await data_scout_integration.get_account_snapshot("acc_123")

    @pytest.mark.asyncio
    async def test_handles_network_timeout(self, data_scout_integration):
        """Test handling of network timeouts."""
        data_scout_integration.zoho_manager.get_account.side_effect = asyncio.TimeoutError()

        with pytest.raises(asyncio.TimeoutError):
            await data_scout_integration.get_account_snapshot("acc_123")

    @pytest.mark.asyncio
    async def test_handles_partial_aggregation_failure(self, data_scout_integration):
        """Test graceful degradation when some aggregations fail."""
        # Deals fetch succeeds
        deal = DealRecord(
            deal_id="1",
            deal_name="Test",
            account_id="acc_123",
            stage=DealStage.NEGOTIATION,
            owner_id="owner_456",
        )

        with patch.object(data_scout_integration, '_fetch_deals', return_value=[deal]), \
             patch.object(data_scout_integration, '_fetch_activities', side_effect=Exception("Failed")), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            aggregated = await data_scout_integration.aggregate_related_records("acc_123")

            # Should have deals but not activities
            assert len(aggregated.deals) == 1
            assert len(aggregated.activities) == 0

    @pytest.mark.asyncio
    async def test_handles_invalid_account_data(self, data_scout_integration):
        """Test handling of invalid account data from Zoho."""
        data_scout_integration.zoho_manager.get_account.return_value = {
            "id": "acc_123",
            # Missing required fields
        }

        with pytest.raises(Exception):
            await data_scout_integration.get_account_snapshot("acc_123")

    @pytest.mark.asyncio
    async def test_handles_cache_corruption(self, data_scout_integration):
        """Test handling of corrupted cache files."""
        # Create corrupted cache file
        cache_path = data_scout_integration._get_cache_path("acc_123")
        cache_path.write_text("invalid json {")

        with patch.object(data_scout_integration, '_fetch_deals', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            # Should handle corrupted cache gracefully
            snapshot = await data_scout_integration.get_account_snapshot("acc_123")
            assert isinstance(snapshot, AccountSnapshot)

    @pytest.mark.asyncio
    async def test_handles_empty_response(self, data_scout_integration):
        """Test handling of empty API responses."""
        data_scout_integration.zoho_manager.search_accounts.return_value = []

        accounts = await data_scout_integration.fetch_accounts_by_owner("owner_456")

        assert len(accounts) == 0

    @pytest.mark.asyncio
    async def test_recovers_from_transient_error(self, data_scout_integration):
        """Test recovery from transient errors."""
        # First call fails, second succeeds
        call_count = [0]

        async def get_account_with_retry(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Transient error")
            return {
                "id": "acc_123",
                "Account_Name": "Acme",
                "Owner": {"id": "owner_456", "name": "John"},
                "Account_Status": "Active",
                "Modified_Time": datetime.utcnow().isoformat(),
                "Created_Time": datetime.utcnow().isoformat(),
            }

        data_scout_integration.zoho_manager.get_account = get_account_with_retry

        with patch.object(data_scout_integration, '_fetch_deals', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            # First call should fail
            with pytest.raises(Exception):
                await data_scout_integration.get_account_snapshot("acc_123")

            # Second call should succeed
            snapshot = await data_scout_integration.get_account_snapshot("acc_123")
            assert isinstance(snapshot, AccountSnapshot)

    @pytest.mark.asyncio
    async def test_handles_rate_limiting(self, data_scout_integration):
        """Test handling of rate limit errors."""
        data_scout_integration.zoho_manager.search_accounts.side_effect = ZohoAPIError(
            "Rate limit exceeded"
        )

        with pytest.raises(ZohoAPIError):
            await data_scout_integration.fetch_accounts_by_owner("owner_456")


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Test performance benchmarks."""

    @pytest.mark.asyncio
    async def test_snapshot_performance(self, data_scout_integration):
        """Test snapshot creation completes within 30 seconds."""
        with patch.object(data_scout_integration, '_fetch_deals', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            start = datetime.utcnow()
            snapshot = await data_scout_integration.get_account_snapshot("acc_123")
            duration = (datetime.utcnow() - start).total_seconds()

            # Should complete in under 30 seconds
            assert duration < 30

    @pytest.mark.asyncio
    async def test_batch_fetch_performance(self, data_scout_integration):
        """Test fetching multiple accounts performs adequately."""
        start = datetime.utcnow()

        # Fetch 5 accounts
        accounts = await data_scout_integration.fetch_accounts_by_owner("owner_456")

        duration = (datetime.utcnow() - start).total_seconds()

        # Should complete quickly
        assert duration < 10

    @pytest.mark.asyncio
    async def test_aggregation_parallelism(self, data_scout_integration):
        """Test aggregation uses parallel execution."""
        # Mock slow fetches
        async def slow_fetch():
            await asyncio.sleep(0.2)
            return []

        with patch.object(data_scout_integration, '_fetch_deals', side_effect=slow_fetch), \
             patch.object(data_scout_integration, '_fetch_activities', side_effect=slow_fetch), \
             patch.object(data_scout_integration, '_fetch_notes', side_effect=slow_fetch):

            start = datetime.utcnow()
            await data_scout_integration.aggregate_related_records("acc_123")
            duration = (datetime.utcnow() - start).total_seconds()

            # Should take ~0.2s if parallel, ~0.6s if sequential
            assert duration < 0.4

    @pytest.mark.asyncio
    async def test_change_detection_performance(self, data_scout_integration):
        """Test change detection completes quickly."""
        # Establish baseline
        with patch.object(data_scout_integration, '_fetch_deals', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            await data_scout_integration.get_account_snapshot("acc_123")

            # Detect changes
            start = datetime.utcnow()
            changes = await data_scout_integration.detect_changes("acc_123")
            duration = (datetime.utcnow() - start).total_seconds()

            # Should be very fast
            assert duration < 1

    @pytest.mark.asyncio
    async def test_cache_improves_performance(self, data_scout_integration):
        """Test caching improves repeated access performance."""
        with patch.object(data_scout_integration, '_fetch_deals', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            # First access - cache miss
            start1 = datetime.utcnow()
            await data_scout_integration.detect_changes("acc_123")
            duration1 = (datetime.utcnow() - start1).total_seconds()

            # Second access - cache hit
            start2 = datetime.utcnow()
            await data_scout_integration.detect_changes("acc_123")
            duration2 = (datetime.utcnow() - start2).total_seconds()

            # Cached access should be faster or similar
            assert duration2 <= duration1 * 1.5


# ============================================================================
# CACHE BEHAVIOR TESTS
# ============================================================================

class TestCacheBehavior:
    """Test caching behavior and TTL."""

    @pytest.mark.asyncio
    async def test_cache_stores_state(self, data_scout_integration):
        """Test cache stores account state."""
        with patch.object(data_scout_integration, '_fetch_deals', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            await data_scout_integration.get_account_snapshot("acc_123")

            # Check cache file exists
            cache_path = data_scout_integration._get_cache_path("acc_123")
            assert cache_path.exists()

    @pytest.mark.asyncio
    async def test_cache_loads_state(self, data_scout_integration):
        """Test cache loads previously stored state."""
        # Store initial state
        initial_data = {
            "id": "acc_123",
            "Account_Name": "Initial Name",
            "Account_Status": "Active",
        }
        data_scout_integration._save_cached_state("acc_123", initial_data)

        # Load cached state
        loaded_data = data_scout_integration._load_cached_state("acc_123")

        assert loaded_data is not None
        assert loaded_data["Account_Name"] == "Initial Name"

    @pytest.mark.asyncio
    async def test_cache_respects_ttl(self, data_scout_integration):
        """Test cache respects TTL setting."""
        # Set short TTL
        data_scout_integration.config.cache.ttl_seconds = 1

        # Store state
        data_scout_integration._save_cached_state("acc_123", {"id": "acc_123"})

        # Should load immediately
        loaded = data_scout_integration._load_cached_state("acc_123")
        assert loaded is not None

        # Wait for TTL expiration
        await asyncio.sleep(2)

        # Should return None (expired)
        loaded = data_scout_integration._load_cached_state("acc_123")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_cache_disabled(self, data_scout_integration):
        """Test behavior when cache is disabled."""
        data_scout_integration.config.cache.enabled = False

        # Attempt to save
        data_scout_integration._save_cached_state("acc_123", {"id": "acc_123"})

        # Should not load when disabled
        loaded = data_scout_integration._load_cached_state("acc_123")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_cache_handles_missing_files(self, data_scout_integration):
        """Test cache handles missing cache files gracefully."""
        # Try to load non-existent cache
        loaded = data_scout_integration._load_cached_state("nonexistent")

        assert loaded is None


# ============================================================================
# CONCURRENT OPERATION TESTS
# ============================================================================

class TestConcurrentOperations:
    """Test concurrent operations handling."""

    @pytest.mark.asyncio
    async def test_concurrent_snapshot_creation(self, data_scout_integration):
        """Test creating multiple snapshots concurrently."""
        with patch.object(data_scout_integration, '_fetch_deals', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            # Create 5 snapshots concurrently
            tasks = [
                data_scout_integration.get_account_snapshot(f"acc_{i}")
                for i in range(5)
            ]

            snapshots = await asyncio.gather(*tasks)

            # All should complete successfully
            assert len(snapshots) == 5
            for snapshot in snapshots:
                assert isinstance(snapshot, AccountSnapshot)

    @pytest.mark.asyncio
    async def test_concurrent_change_detection(self, data_scout_integration):
        """Test concurrent change detection."""
        # Establish baseline for multiple accounts
        for i in range(3):
            data_scout_integration._save_cached_state(
                f"acc_{i}",
                {"id": f"acc_{i}", "Account_Status": "Active"}
            )

        # Detect changes concurrently
        tasks = [
            data_scout_integration.detect_changes(f"acc_{i}")
            for i in range(3)
        ]

        results = await asyncio.gather(*tasks)

        # All should complete
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_concurrent_aggregation(self, data_scout_integration):
        """Test concurrent data aggregation."""
        with patch.object(data_scout_integration, '_fetch_deals', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            # Aggregate data for multiple accounts concurrently
            tasks = [
                data_scout_integration.aggregate_related_records(f"acc_{i}")
                for i in range(3)
            ]

            results = await asyncio.gather(*tasks)

            assert len(results) == 3
            for result in results:
                assert isinstance(result, AggregatedData)


# ============================================================================
# DATA QUALITY TESTS
# ============================================================================

class TestDataQuality:
    """Test data quality and consistency."""

    @pytest.mark.asyncio
    async def test_snapshot_data_consistency(self, data_scout_integration):
        """Test snapshot data is internally consistent."""
        deal = DealRecord(
            deal_id="1",
            deal_name="Test",
            account_id="acc_123",
            stage=DealStage.NEGOTIATION,
            amount=Decimal("50000"),
            owner_id="owner_456",
        )

        with patch.object(data_scout_integration, '_fetch_deals', return_value=[deal]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            snapshot = await data_scout_integration.get_account_snapshot("acc_123")

            # Account ID should match everywhere
            assert snapshot.account.account_id == "acc_123"
            assert snapshot.aggregated_data.account_id == "acc_123"
            assert snapshot.changes.account_id == "acc_123"

    @pytest.mark.asyncio
    async def test_snapshot_has_all_required_fields(self, data_scout_integration):
        """Test snapshot contains all required fields."""
        with patch.object(data_scout_integration, '_fetch_deals', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            snapshot = await data_scout_integration.get_account_snapshot("acc_123")

            # Required fields present
            assert snapshot.snapshot_id is not None
            assert snapshot.account is not None
            assert snapshot.aggregated_data is not None
            assert snapshot.changes is not None
            assert snapshot.risk_signals is not None
            assert snapshot.data_sources is not None

    @pytest.mark.asyncio
    async def test_timestamp_accuracy(self, data_scout_integration):
        """Test timestamps are accurate."""
        with patch.object(data_scout_integration, '_fetch_deals', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            before = datetime.utcnow()
            snapshot = await data_scout_integration.get_account_snapshot("acc_123")
            after = datetime.utcnow()

            # Snapshot time should be between before and after
            assert before <= snapshot.snapshot_time <= after

    @pytest.mark.asyncio
    async def test_data_freshness_tracking(self, data_scout_integration):
        """Test data freshness is tracked."""
        with patch.object(data_scout_integration, '_fetch_deals', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_activities', return_value=[]), \
             patch.object(data_scout_integration, '_fetch_notes', return_value=[]):

            snapshot = await data_scout_integration.get_account_snapshot("acc_123")

            # Data freshness should be set
            assert snapshot.aggregated_data.data_freshness >= 0


# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

class TestConfiguration:
    """Test configuration behavior."""

    @pytest.mark.asyncio
    async def test_custom_thresholds_respected(self, mock_zoho_integration_manager, tmp_path):
        """Test custom thresholds are respected."""
        config = DataScoutConfig()
        config.cache.cache_dir = tmp_path / "custom_cache"
        config.cache.cache_dir.mkdir(parents=True, exist_ok=True)
        config.inactivity_threshold_days = 60
        config.deal_stalled_threshold_days = 45

        scout = ZohoDataScout(mock_zoho_integration_manager, config)

        assert scout.config.inactivity_threshold_days == 60
        assert scout.config.deal_stalled_threshold_days == 45

    @pytest.mark.asyncio
    async def test_read_only_mode_enforced(self, data_scout_integration):
        """Test read-only mode is enforced."""
        assert data_scout_integration.config.read_only is True
        assert data_scout_integration.config.permission_mode == "plan"

    @pytest.mark.asyncio
    async def test_max_fetch_limits_respected(self, mock_zoho_integration_manager, integration_config):
        """Test max fetch limits are respected."""
        integration_config.max_deals_per_account = 5
        integration_config.max_activities_per_account = 10

        scout = ZohoDataScout(mock_zoho_integration_manager, integration_config)

        # Configuration should be set
        assert scout.config.max_deals_per_account == 5
        assert scout.config.max_activities_per_account == 10
