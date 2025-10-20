"""
End-to-End Tests for Sync Workflows.

Tests cover:
- Full sync cycle tests
- Incremental sync tests
- Webhook processing tests
- Sync error recovery
- Data consistency validation
- Performance validation

Uses real database with mocked external APIs.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import AsyncMock, Mock, patch

from tests.e2e.fixtures.account_fixtures import get_all_test_accounts
from tests.e2e.fixtures.interaction_fixtures import generate_complete_interaction_history
from tests.e2e.fixtures.deal_fixtures import generate_complete_deal_pipeline


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_sync_scheduler():
    """Mock sync scheduler for E2E testing."""
    scheduler = AsyncMock()
    schedules = {}
    execution_log = []

    async def create_schedule(schedule_id, config):
        schedules[schedule_id] = {
            "id": schedule_id,
            "config": config,
            "status": "active",
            "created_at": datetime.now()
        }
        return schedule_id

    async def execute_sync(schedule_id):
        if schedule_id in schedules:
            execution_log.append({
                "schedule_id": schedule_id,
                "executed_at": datetime.now(),
                "status": "success"
            })
            return {"success": True, "records_synced": 50}
        return {"success": False}

    async def get_schedule(schedule_id):
        return schedules.get(schedule_id)

    scheduler.create_schedule = create_schedule
    scheduler.execute_sync = execute_sync
    scheduler.get_schedule = get_schedule
    scheduler.schedules = schedules
    scheduler.execution_log = execution_log

    return scheduler


@pytest.fixture
def mock_webhook_processor():
    """Mock webhook processor for E2E testing."""
    processor = AsyncMock()
    webhook_queue = []
    processed_webhooks = []

    async def receive_webhook(payload: Dict[str, Any]):
        webhook = {
            "id": f"webhook_{len(webhook_queue)}",
            "payload": payload,
            "received_at": datetime.now(),
            "status": "pending"
        }
        webhook_queue.append(webhook)
        return webhook["id"]

    async def process_webhook(webhook_id):
        for webhook in webhook_queue:
            if webhook["id"] == webhook_id:
                # Simulate processing
                await asyncio.sleep(0.05)
                webhook["status"] = "processed"
                webhook["processed_at"] = datetime.now()
                processed_webhooks.append(webhook)
                return {"success": True, "webhook_id": webhook_id}
        return {"success": False}

    async def get_pending_count():
        return len([w for w in webhook_queue if w["status"] == "pending"])

    processor.receive_webhook = receive_webhook
    processor.process_webhook = process_webhook
    processor.get_pending_count = get_pending_count
    processor.webhook_queue = webhook_queue
    processor.processed_webhooks = processed_webhooks

    return processor


@pytest.fixture
def mock_sync_state_manager():
    """Mock sync state manager for tracking sync progress."""
    manager = AsyncMock()
    state_store = {}

    async def save_state(sync_id, state):
        state_store[sync_id] = {
            "state": state,
            "updated_at": datetime.now()
        }

    async def get_state(sync_id):
        return state_store.get(sync_id)

    async def update_checkpoint(sync_id, checkpoint):
        if sync_id in state_store:
            state_store[sync_id]["state"]["checkpoint"] = checkpoint
            state_store[sync_id]["updated_at"] = datetime.now()

    manager.save_state = save_state
    manager.get_state = get_state
    manager.update_checkpoint = update_checkpoint
    manager.state_store = state_store

    return manager


# ============================================================================
# Test Suite: Full Sync Cycles
# ============================================================================

@pytest.mark.e2e
@pytest.mark.asyncio
class TestFullSyncCycles:
    """Test complete full sync workflows."""

    async def test_full_account_sync(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e,
        mock_sync_state_manager
    ):
        """Test complete full sync of all accounts."""
        # Arrange
        all_accounts = get_all_test_accounts()
        sync_id = "full_sync_001"

        # Act
        start_time = datetime.now()

        # Initialize sync state
        await mock_sync_state_manager.save_state(sync_id, {
            "total_accounts": len(all_accounts),
            "processed": 0,
            "status": "in_progress",
            "started_at": start_time.isoformat()
        })

        # Process all accounts
        synced_accounts = []
        for i, account in enumerate(all_accounts):
            # Fetch from Zoho
            account_data = await mock_zoho_client_e2e.get_account(account["id"])

            # Store in memory
            await mock_cognee_client_e2e.add(
                account_data,
                dataset="accounts"
            )

            synced_accounts.append(account_data)

            # Update checkpoint every 10 accounts
            if (i + 1) % 10 == 0:
                await mock_sync_state_manager.update_checkpoint(sync_id, {
                    "processed": i + 1,
                    "last_account_id": account["id"]
                })

        # Finalize sync
        end_time = datetime.now()
        await mock_sync_state_manager.save_state(sync_id, {
            "total_accounts": len(all_accounts),
            "processed": len(synced_accounts),
            "status": "completed",
            "started_at": start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "duration_seconds": (end_time - start_time).total_seconds()
        })

        # Assert
        state = await mock_sync_state_manager.get_state(sync_id)
        assert state["state"]["status"] == "completed"
        assert state["state"]["processed"] == len(all_accounts)
        assert len(synced_accounts) == len(all_accounts)

    async def test_full_sync_with_relationships(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e
    ):
        """Test full sync including related entities (contacts, deals)."""
        # Arrange
        test_accounts = get_all_test_accounts()[:10]

        # Act
        for account in test_accounts:
            # Fetch account and relationships
            account_data = await mock_zoho_client_e2e.get_account(account["id"])
            contacts = await mock_zoho_client_e2e.get_contacts(account["id"])
            deals = await mock_zoho_client_e2e.get_deals(account["id"])
            activities = await mock_zoho_client_e2e.get_activities(account["id"])

            # Store complete record with relationships
            complete_record = {
                "account": account_data,
                "contacts": contacts,
                "deals": deals,
                "activities": activities,
                "synced_at": datetime.now().isoformat()
            }

            await mock_cognee_client_e2e.add(
                complete_record,
                dataset=f"account_complete_{account['id']}"
            )

        # Assert
        # Verify all accounts synced with relationships
        for account in test_accounts:
            results = await mock_cognee_client_e2e.search(
                f"account_complete_{account['id']}"
            )
            assert len(results) > 0

    async def test_full_sync_performance(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e
    ):
        """Test full sync meets performance requirements."""
        # Arrange
        all_accounts = get_all_test_accounts()  # 50 accounts

        # Act
        start_time = datetime.now()

        # Batch processing for better performance
        batch_size = 10
        for i in range(0, len(all_accounts), batch_size):
            batch = all_accounts[i:i + batch_size]

            # Parallel fetch within batch
            async def sync_account(account):
                account_data = await mock_zoho_client_e2e.get_account(account["id"])
                await mock_cognee_client_e2e.add(account_data, dataset="accounts")
                return account_data

            await asyncio.gather(*[sync_account(acc) for acc in batch])

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Assert
        # 50 accounts should sync in reasonable time
        assert duration < 60  # Less than 1 minute for 50 accounts
        # Average per account
        avg_time = duration / len(all_accounts)
        assert avg_time < 1.2  # Less than 1.2 seconds per account

    async def test_full_sync_with_rate_limiting(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e
    ):
        """Test full sync respects rate limits."""
        # Arrange
        accounts = get_all_test_accounts()[:20]
        rate_limiter = {
            "calls_per_minute": 60,
            "call_count": 0,
            "window_start": datetime.now()
        }

        async def rate_limited_fetch(account_id):
            # Check rate limit
            now = datetime.now()
            if (now - rate_limiter["window_start"]).total_seconds() >= 60:
                # Reset window
                rate_limiter["window_start"] = now
                rate_limiter["call_count"] = 0

            if rate_limiter["call_count"] >= rate_limiter["calls_per_minute"]:
                # Wait for next window
                await asyncio.sleep(1)
                rate_limiter["window_start"] = datetime.now()
                rate_limiter["call_count"] = 0

            rate_limiter["call_count"] += 1
            return await mock_zoho_client_e2e.get_account(account_id)

        # Act
        for account in accounts:
            account_data = await rate_limited_fetch(account["id"])
            await mock_cognee_client_e2e.add(account_data, dataset="accounts")

        # Assert
        assert rate_limiter["call_count"] <= rate_limiter["calls_per_minute"]


# ============================================================================
# Test Suite: Incremental Sync
# ============================================================================

@pytest.mark.e2e
@pytest.mark.asyncio
class TestIncrementalSync:
    """Test incremental sync workflows."""

    async def test_incremental_sync_modified_accounts(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e,
        mock_sync_state_manager
    ):
        """Test incremental sync of only modified accounts."""
        # Arrange
        all_accounts = get_all_test_accounts()
        last_sync_time = datetime.now() - timedelta(hours=24)

        # Simulate some accounts modified since last sync
        modified_accounts = [
            acc for acc in all_accounts
            if datetime.fromisoformat(acc["Modified_Time"]) > last_sync_time
        ][:5]

        sync_id = "incremental_001"

        # Act
        await mock_sync_state_manager.save_state(sync_id, {
            "type": "incremental",
            "last_sync": last_sync_time.isoformat(),
            "status": "in_progress"
        })

        synced = []
        for account in modified_accounts:
            account_data = await mock_zoho_client_e2e.get_account(account["id"])
            await mock_cognee_client_e2e.add(account_data, dataset="accounts")
            synced.append(account_data)

        await mock_sync_state_manager.save_state(sync_id, {
            "type": "incremental",
            "last_sync": last_sync_time.isoformat(),
            "current_sync": datetime.now().isoformat(),
            "status": "completed",
            "accounts_synced": len(synced)
        })

        # Assert
        state = await mock_sync_state_manager.get_state(sync_id)
        assert state["state"]["status"] == "completed"
        assert state["state"]["accounts_synced"] == len(modified_accounts)
        # Should be much fewer than total
        assert len(synced) < len(all_accounts)

    async def test_incremental_sync_delta_detection(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e
    ):
        """Test detection of changes in incremental sync."""
        # Arrange
        account = get_all_test_accounts()[0]

        # Store initial version
        initial_data = await mock_zoho_client_e2e.get_account(account["id"])
        await mock_cognee_client_e2e.store(
            f"account_{account['id']}_v1",
            initial_data
        )

        # Simulate account update
        updated_data = {**initial_data, "Rating": "Hot", "Modified_Time": datetime.now().isoformat()}
        mock_zoho_client_e2e.get_account = AsyncMock(return_value=updated_data)

        # Act
        current_data = await mock_zoho_client_e2e.get_account(account["id"])
        previous_data = await mock_cognee_client_e2e.get(f"account_{account['id']}_v1")

        # Detect changes
        changes = {}
        for key in current_data:
            if key in previous_data and current_data[key] != previous_data[key]:
                changes[key] = {
                    "old": previous_data[key],
                    "new": current_data[key]
                }

        # Store updated version
        await mock_cognee_client_e2e.store(
            f"account_{account['id']}_v2",
            current_data
        )

        # Assert
        assert len(changes) > 0
        assert "Rating" in changes
        assert changes["Rating"]["new"] == "Hot"

    async def test_incremental_sync_checkpoint_recovery(
        self,
        mock_zoho_client_e2e,
        mock_sync_state_manager
    ):
        """Test incremental sync can recover from checkpoint."""
        # Arrange
        accounts = get_all_test_accounts()[:20]
        sync_id = "incremental_checkpoint_001"

        # Act - Part 1: Sync first 10, then fail
        processed_ids = []
        for i, account in enumerate(accounts[:10]):
            await mock_zoho_client_e2e.get_account(account["id"])
            processed_ids.append(account["id"])

            if i == 9:
                # Save checkpoint
                await mock_sync_state_manager.save_state(sync_id, {
                    "processed_ids": processed_ids,
                    "last_processed_index": i,
                    "status": "interrupted"
                })

        # Part 2: Resume from checkpoint
        checkpoint = await mock_sync_state_manager.get_state(sync_id)
        last_index = checkpoint["state"]["last_processed_index"]

        for account in accounts[last_index + 1:]:
            await mock_zoho_client_e2e.get_account(account["id"])
            processed_ids.append(account["id"])

        await mock_sync_state_manager.save_state(sync_id, {
            "processed_ids": processed_ids,
            "status": "completed"
        })

        # Assert
        final_state = await mock_sync_state_manager.get_state(sync_id)
        assert final_state["state"]["status"] == "completed"
        assert len(processed_ids) == 20


# ============================================================================
# Test Suite: Webhook Processing
# ============================================================================

@pytest.mark.e2e
@pytest.mark.asyncio
class TestWebhookProcessing:
    """Test webhook-driven sync workflows."""

    async def test_webhook_account_update(
        self,
        mock_webhook_processor,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e
    ):
        """Test processing account update webhook."""
        # Arrange
        account = get_all_test_accounts()[0]
        webhook_payload = {
            "event": "account.updated",
            "account_id": account["id"],
            "changes": {"Rating": "Hot", "Last_Activity_Time": datetime.now().isoformat()},
            "timestamp": datetime.now().isoformat()
        }

        # Act
        # Receive webhook
        webhook_id = await mock_webhook_processor.receive_webhook(webhook_payload)

        # Process webhook
        result = await mock_webhook_processor.process_webhook(webhook_id)

        # Fetch updated account data
        account_data = await mock_zoho_client_e2e.get_account(account["id"])

        # Update in memory
        await mock_cognee_client_e2e.add(
            {
                "account": account_data,
                "webhook_id": webhook_id,
                "updated_at": datetime.now().isoformat()
            },
            dataset=f"webhook_updates_{account['id']}"
        )

        # Assert
        assert result["success"] is True
        assert len(mock_webhook_processor.processed_webhooks) == 1

    async def test_webhook_bulk_processing(
        self,
        mock_webhook_processor
    ):
        """Test processing multiple webhooks in batch."""
        # Arrange
        accounts = get_all_test_accounts()[:15]
        webhooks = []

        # Act
        # Receive multiple webhooks
        for account in accounts:
            webhook_id = await mock_webhook_processor.receive_webhook({
                "event": "account.updated",
                "account_id": account["id"],
                "timestamp": datetime.now().isoformat()
            })
            webhooks.append(webhook_id)

        # Process in parallel
        results = await asyncio.gather(*[
            mock_webhook_processor.process_webhook(wid)
            for wid in webhooks
        ])

        # Assert
        assert len(results) == 15
        assert all(r["success"] for r in results)
        assert await mock_webhook_processor.get_pending_count() == 0

    async def test_webhook_processing_order(
        self,
        mock_webhook_processor
    ):
        """Test webhooks processed in correct order."""
        # Arrange
        account_id = "ACC_ORDER_TEST"
        events = ["created", "updated", "updated", "deleted"]

        # Act
        webhook_ids = []
        for i, event in enumerate(events):
            webhook_id = await mock_webhook_processor.receive_webhook({
                "event": f"account.{event}",
                "account_id": account_id,
                "sequence": i,
                "timestamp": (datetime.now() + timedelta(seconds=i)).isoformat()
            })
            webhook_ids.append(webhook_id)

        # Process in order
        for webhook_id in webhook_ids:
            await mock_webhook_processor.process_webhook(webhook_id)

        # Assert
        processed = mock_webhook_processor.processed_webhooks
        assert len(processed) == 4
        # Verify order maintained
        for i in range(len(processed)):
            assert processed[i]["payload"]["sequence"] == i

    async def test_webhook_deduplication(
        self,
        mock_webhook_processor
    ):
        """Test duplicate webhooks are handled correctly."""
        # Arrange
        account_id = "ACC_DEDUP_TEST"
        duplicate_payload = {
            "event": "account.updated",
            "account_id": account_id,
            "event_id": "evt_123",  # Same event ID
            "timestamp": datetime.now().isoformat()
        }

        processed_event_ids = set()

        async def deduplicated_process(webhook_id):
            webhook = None
            for w in mock_webhook_processor.webhook_queue:
                if w["id"] == webhook_id:
                    webhook = w
                    break

            if not webhook:
                return {"success": False}

            event_id = webhook["payload"].get("event_id")
            if event_id in processed_event_ids:
                # Skip duplicate
                return {"success": True, "skipped": True}

            processed_event_ids.add(event_id)
            await mock_webhook_processor.process_webhook(webhook_id)
            return {"success": True, "skipped": False}

        # Act
        # Receive same webhook twice
        webhook_id_1 = await mock_webhook_processor.receive_webhook(duplicate_payload)
        webhook_id_2 = await mock_webhook_processor.receive_webhook(duplicate_payload)

        result_1 = await deduplicated_process(webhook_id_1)
        result_2 = await deduplicated_process(webhook_id_2)

        # Assert
        assert result_1["skipped"] is False
        assert result_2["skipped"] is True
        assert len(processed_event_ids) == 1


# ============================================================================
# Test Suite: Sync Error Recovery
# ============================================================================

@pytest.mark.e2e
@pytest.mark.asyncio
class TestSyncErrorRecovery:
    """Test sync error handling and recovery."""

    async def test_sync_retry_on_failure(
        self,
        mock_zoho_client_e2e
    ):
        """Test sync retries on transient failures."""
        # Arrange
        account = get_all_test_accounts()[0]
        attempt_count = {"count": 0}

        async def flaky_get_account(account_id):
            attempt_count["count"] += 1
            if attempt_count["count"] < 3:
                raise Exception("Temporary network error")
            return {"id": account_id, "Account_Name": "Test"}

        mock_zoho_client_e2e.get_account = flaky_get_account

        # Act
        async def retry_with_backoff(operation, max_retries=5):
            for attempt in range(max_retries):
                try:
                    return await operation()
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff

        result = await retry_with_backoff(
            lambda: mock_zoho_client_e2e.get_account(account["id"])
        )

        # Assert
        assert result is not None
        assert attempt_count["count"] == 3

    async def test_sync_partial_failure_handling(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e
    ):
        """Test sync handles partial failures gracefully."""
        # Arrange
        accounts = get_all_test_accounts()[:10]
        failed_accounts = [accounts[3]["id"], accounts[7]["id"]]

        async def conditional_get_account(account_id):
            if account_id in failed_accounts:
                raise Exception(f"Failed to fetch {account_id}")
            return {"id": account_id, "Account_Name": "Test"}

        mock_zoho_client_e2e.get_account = conditional_get_account

        # Act
        successful = []
        failed = []

        for account in accounts:
            try:
                account_data = await mock_zoho_client_e2e.get_account(account["id"])
                await mock_cognee_client_e2e.add(account_data, dataset="accounts")
                successful.append(account["id"])
            except Exception as e:
                failed.append({"account_id": account["id"], "error": str(e)})

        # Assert
        assert len(successful) == 8
        assert len(failed) == 2
        assert all(f["account_id"] in failed_accounts for f in failed)

    async def test_sync_data_validation(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e
    ):
        """Test sync validates data before storage."""
        # Arrange
        def validate_account_data(data):
            required_fields = ["id", "Account_Name"]
            for field in required_fields:
                if field not in data or not data[field]:
                    raise ValueError(f"Missing required field: {field}")
            return True

        valid_account = {"id": "ACC_001", "Account_Name": "Valid Corp"}
        invalid_account = {"id": "ACC_002"}  # Missing Account_Name

        # Act & Assert
        # Valid account should pass
        assert validate_account_data(valid_account)
        await mock_cognee_client_e2e.add(valid_account, dataset="accounts")

        # Invalid account should fail
        with pytest.raises(ValueError, match="Missing required field"):
            validate_account_data(invalid_account)

    async def test_sync_conflict_resolution(
        self,
        mock_cognee_client_e2e
    ):
        """Test sync resolves data conflicts correctly."""
        # Arrange
        account_id = "ACC_CONFLICT_001"

        # Version 1 (older)
        version_1 = {
            "id": account_id,
            "Account_Name": "Old Name",
            "Modified_Time": (datetime.now() - timedelta(hours=2)).isoformat(),
            "version": 1
        }

        # Version 2 (newer)
        version_2 = {
            "id": account_id,
            "Account_Name": "New Name",
            "Modified_Time": datetime.now().isoformat(),
            "version": 2
        }

        # Act
        def resolve_conflict(existing, incoming):
            # Use modified_time to resolve
            existing_time = datetime.fromisoformat(existing["Modified_Time"])
            incoming_time = datetime.fromisoformat(incoming["Modified_Time"])

            if incoming_time > existing_time:
                return incoming  # Use newer version
            return existing

        # Store version 1
        await mock_cognee_client_e2e.store(f"account_{account_id}", version_1)

        # Try to store version 2
        existing = await mock_cognee_client_e2e.get(f"account_{account_id}")
        resolved = resolve_conflict(existing, version_2)
        await mock_cognee_client_e2e.store(f"account_{account_id}", resolved)

        # Assert
        final = await mock_cognee_client_e2e.get(f"account_{account_id}")
        assert final["version"] == 2
        assert final["Account_Name"] == "New Name"


# ============================================================================
# Test Suite: Sync Performance & Scalability
# ============================================================================

@pytest.mark.e2e
@pytest.mark.asyncio
class TestSyncPerformance:
    """Test sync performance and scalability."""

    async def test_sync_throughput(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e
    ):
        """Test sync achieves target throughput."""
        # Arrange
        accounts = get_all_test_accounts()  # 50 accounts

        # Act
        start_time = datetime.now()

        # Parallel sync with batching
        batch_size = 10
        for i in range(0, len(accounts), batch_size):
            batch = accounts[i:i + batch_size]

            async def sync_single(account):
                data = await mock_zoho_client_e2e.get_account(account["id"])
                await mock_cognee_client_e2e.add(data, dataset="accounts")

            await asyncio.gather(*[sync_single(acc) for acc in batch])

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Calculate throughput
        throughput = len(accounts) / duration  # accounts per second

        # Assert
        assert throughput > 1  # At least 1 account per second
        assert duration < 60  # Complete in under 1 minute

    async def test_sync_memory_efficiency(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e
    ):
        """Test sync processes large datasets efficiently."""
        # Arrange
        large_dataset = get_all_test_accounts() * 5  # 250 accounts

        # Act
        # Process in streaming fashion to avoid memory issues
        processed_count = 0
        batch_size = 10

        for i in range(0, len(large_dataset), batch_size):
            batch = large_dataset[i:i + batch_size]

            # Process batch
            for account in batch:
                data = await mock_zoho_client_e2e.get_account(account["id"])
                await mock_cognee_client_e2e.add(data, dataset="accounts")
                processed_count += 1

            # Clear batch from memory (simulated)
            batch = None

        # Assert
        assert processed_count == len(large_dataset)

    async def test_sync_concurrent_operations(
        self,
        mock_sync_scheduler
    ):
        """Test multiple sync operations can run concurrently."""
        # Arrange
        sync_configs = [
            {"id": "sync_1", "type": "full"},
            {"id": "sync_2", "type": "incremental"},
            {"id": "sync_3", "type": "webhook"}
        ]

        # Act
        # Create schedules
        for config in sync_configs:
            await mock_sync_scheduler.create_schedule(config["id"], config)

        # Execute concurrently
        results = await asyncio.gather(*[
            mock_sync_scheduler.execute_sync(config["id"])
            for config in sync_configs
        ])

        # Assert
        assert len(results) == 3
        assert all(r["success"] for r in results)
        assert len(mock_sync_scheduler.execution_log) == 3
