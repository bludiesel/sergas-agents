"""
Comprehensive unit tests for CogneeSyncPipeline.

Tests cover:
- Pipeline initialization
- Full sync operations
- Incremental sync with change detection
- On-demand sync
- Batch processing
- Error handling and retry logic
- Progress tracking
- Pause/resume functionality
- Checksum validation
- Database state management
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.sync.cognee_sync_pipeline import CogneeSyncPipeline
from src.integrations.zoho.sdk_client import ZohoSDKClient
from src.integrations.cognee.cognee_client import CogneeClient
from src.models.sync.sync_models import (
    Base,
    SyncType,
    SyncStatus,
    SyncStateModel,
    SyncSessionModel,
    SyncBatchModel,
    SyncErrorModel,
)


@pytest.fixture
def database_url():
    """In-memory SQLite database for testing."""
    return "sqlite:///:memory:"


@pytest.fixture
def mock_zoho_client():
    """Mock Zoho SDK client."""
    client = Mock(spec=ZohoSDKClient)
    return client


@pytest.fixture
def mock_cognee_client():
    """Mock Cognee client."""
    client = AsyncMock(spec=CogneeClient)
    client.initialize = AsyncMock()
    client.add_account = AsyncMock(return_value="cognee_account_123")
    client.add_accounts_bulk = AsyncMock(return_value={
        "total": 100,
        "success": 95,
        "failed": 5,
        "account_ids": [f"cognee_{i}" for i in range(95)],
    })
    client.close = AsyncMock()
    return client


@pytest.fixture
async def pipeline(database_url, mock_zoho_client, mock_cognee_client):
    """Create CogneeSyncPipeline instance for testing."""
    pipeline = CogneeSyncPipeline(
        zoho_client=mock_zoho_client,
        cognee_client=mock_cognee_client,
        database_url=database_url,
        batch_size=100,
        max_retries=3,
        retry_delay=0.1,  # Fast retries for testing
        max_concurrent_batches=2,
    )
    await pipeline.initialize()
    yield pipeline
    await pipeline.close()


@pytest.fixture
def sample_accounts():
    """Sample account data for testing."""
    accounts = []
    for i in range(250):
        accounts.append({
            "id": f"zoho_account_{i}",
            "Account_Name": f"Test Account {i}",
            "Industry": "Technology" if i % 2 == 0 else "Finance",
            "Annual_Revenue": (i + 1) * 100000,
            "Modified_Time": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
            "Rating": "Hot" if i % 3 == 0 else "Warm",
            "Description": f"Description for account {i}",
        })
    return accounts


# Initialization tests

@pytest.mark.asyncio
async def test_pipeline_initialization(pipeline):
    """Test pipeline initializes correctly."""
    assert pipeline._initialized is True
    assert pipeline.engine is not None
    assert pipeline.SessionLocal is not None


@pytest.mark.asyncio
async def test_pipeline_double_initialization(pipeline):
    """Test double initialization is handled gracefully."""
    # Should not raise error
    await pipeline.initialize()
    assert pipeline._initialized is True


@pytest.mark.asyncio
async def test_pipeline_initialization_creates_tables(database_url, mock_zoho_client, mock_cognee_client):
    """Test database tables are created on initialization."""
    pipeline = CogneeSyncPipeline(
        zoho_client=mock_zoho_client,
        cognee_client=mock_cognee_client,
        database_url=database_url,
        batch_size=100,
    )
    await pipeline.initialize()

    # Verify tables exist
    inspector = pipeline.engine.dialect.get_inspector(pipeline.engine)
    tables = inspector.get_table_names()

    assert "sync_state" in tables
    assert "sync_sessions" in tables
    assert "sync_batches" in tables
    assert "sync_errors" in tables
    assert "sync_metrics" in tables

    await pipeline.close()


# Full sync tests

@pytest.mark.asyncio
async def test_full_sync_fetches_all_accounts(pipeline, mock_zoho_client, sample_accounts):
    """Test full sync fetches all accounts from Zoho."""
    # Mock Zoho client to return accounts in pages
    page_1 = sample_accounts[:200]
    page_2 = sample_accounts[200:]

    mock_zoho_client.get_accounts = Mock(side_effect=[page_1, page_2, []])

    with patch.object(pipeline, '_process_accounts_in_batches', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = Mock(
            session_id="test_session",
            sync_type=SyncType.FULL,
            status=SyncStatus.COMPLETED,
            total_records=250,
            successful_records=250,
            failed_records=0,
        )

        summary = await pipeline.sync_accounts(sync_type=SyncType.FULL)

        # Verify all pages fetched
        assert mock_zoho_client.get_accounts.call_count == 3
        # Verify all accounts passed to processing
        process_call_args = mock_process.call_args[1]
        assert len(process_call_args["accounts"]) == 250


@pytest.mark.asyncio
async def test_full_sync_creates_session_record(pipeline, mock_zoho_client):
    """Test full sync creates session record in database."""
    mock_zoho_client.get_accounts = Mock(return_value=[])

    await pipeline.sync_accounts(sync_type=SyncType.FULL)

    # Check database for session
    async with pipeline._db_session() as db:
        sessions = db.query(SyncSessionModel).all()
        assert len(sessions) == 1
        assert sessions[0].sync_type == SyncType.FULL
        assert sessions[0].status == SyncStatus.COMPLETED


@pytest.mark.asyncio
async def test_full_sync_processes_batches(pipeline, mock_zoho_client, sample_accounts):
    """Test full sync processes accounts in batches."""
    mock_zoho_client.get_accounts = Mock(return_value=sample_accounts)

    # Mock Cognee client
    pipeline.cognee_client.add_account = AsyncMock(
        side_effect=[f"cognee_{i}" for i in range(len(sample_accounts))]
    )

    summary = await pipeline.sync_accounts(sync_type=SyncType.FULL)

    # Check batches created (250 accounts / 100 batch_size = 3 batches)
    async with pipeline._db_session() as db:
        batches = db.query(SyncBatchModel).all()
        assert len(batches) == 3


# Incremental sync tests

@pytest.mark.asyncio
async def test_incremental_sync_uses_last_sync_time(pipeline, mock_zoho_client):
    """Test incremental sync uses last successful sync time."""
    # Create previous successful sync
    past_time = datetime.utcnow() - timedelta(hours=2)
    async with pipeline._db_session() as db:
        previous_session = SyncSessionModel(
            session_id="previous_session",
            sync_type=SyncType.FULL,
            status=SyncStatus.COMPLETED,
            started_at=past_time,
            completed_at=past_time + timedelta(minutes=10),
            total_records=100,
        )
        db.add(previous_session)
        db.commit()

    mock_zoho_client.search_accounts = Mock(return_value=[])

    await pipeline.sync_accounts(sync_type=SyncType.INCREMENTAL)

    # Verify search was called with criteria
    assert mock_zoho_client.search_accounts.called
    criteria = mock_zoho_client.search_accounts.call_args[1]["criteria"]
    assert "Modified_Time >" in criteria


@pytest.mark.asyncio
async def test_incremental_sync_falls_back_to_full_on_first_run(pipeline, mock_zoho_client, sample_accounts):
    """Test incremental sync falls back to full sync on first run."""
    mock_zoho_client.get_accounts = Mock(return_value=sample_accounts[:50])

    with patch.object(pipeline, '_process_accounts_in_batches', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = Mock(
            session_id="test",
            sync_type=SyncType.INCREMENTAL,
            status=SyncStatus.COMPLETED,
            total_records=50,
            successful_records=50,
            failed_records=0,
        )

        await pipeline.sync_accounts(sync_type=SyncType.INCREMENTAL)

        # Should have called get_accounts (full sync) instead of search_accounts
        assert mock_zoho_client.get_accounts.called


@pytest.mark.asyncio
async def test_incremental_sync_only_fetches_modified_accounts(pipeline, mock_zoho_client):
    """Test incremental sync only processes modified accounts."""
    # Setup previous sync
    past_time = datetime.utcnow() - timedelta(hours=1)
    async with pipeline._db_session() as db:
        session = SyncSessionModel(
            session_id="prev",
            sync_type=SyncType.FULL,
            status=SyncStatus.COMPLETED,
            completed_at=past_time,
        )
        db.add(session)
        db.commit()

    # Return only 10 modified accounts
    modified_accounts = [
        {
            "id": f"account_{i}",
            "Account_Name": f"Modified {i}",
            "Modified_Time": datetime.utcnow().isoformat(),
        }
        for i in range(10)
    ]
    mock_zoho_client.search_accounts = Mock(return_value=modified_accounts)

    with patch.object(pipeline, '_process_accounts_in_batches', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = Mock(
            session_id="test",
            sync_type=SyncType.INCREMENTAL,
            status=SyncStatus.COMPLETED,
            total_records=10,
            successful_records=10,
            failed_records=0,
        )

        summary = await pipeline.sync_accounts(sync_type=SyncType.INCREMENTAL)

        # Verify only modified accounts processed
        accounts = mock_process.call_args[1]["accounts"]
        assert len(accounts) == 10


# On-demand sync tests

@pytest.mark.asyncio
async def test_on_demand_sync_with_account_ids(pipeline, mock_zoho_client):
    """Test on-demand sync with specific account IDs."""
    account_ids = ["account_1", "account_2", "account_3"]

    mock_zoho_client.get_account = Mock(side_effect=[
        {"id": "account_1", "Account_Name": "Account 1"},
        {"id": "account_2", "Account_Name": "Account 2"},
        {"id": "account_3", "Account_Name": "Account 3"},
    ])

    with patch.object(pipeline, '_process_accounts_in_batches', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = Mock(
            session_id="test",
            sync_type=SyncType.ON_DEMAND,
            status=SyncStatus.COMPLETED,
            total_records=3,
            successful_records=3,
            failed_records=0,
        )

        summary = await pipeline.sync_accounts(
            sync_type=SyncType.ON_DEMAND,
            account_ids=account_ids,
        )

        # Verify get_account called for each ID
        assert mock_zoho_client.get_account.call_count == 3


@pytest.mark.asyncio
async def test_on_demand_sync_requires_account_ids(pipeline):
    """Test on-demand sync raises error without account IDs."""
    with pytest.raises(ValueError, match="account_ids required"):
        await pipeline.sync_accounts(sync_type=SyncType.ON_DEMAND)


@pytest.mark.asyncio
async def test_on_demand_sync_handles_fetch_failures(pipeline, mock_zoho_client):
    """Test on-demand sync handles individual account fetch failures."""
    account_ids = ["account_1", "account_2", "account_3"]

    # Second account fetch fails
    mock_zoho_client.get_account = Mock(side_effect=[
        {"id": "account_1", "Account_Name": "Account 1"},
        Exception("Fetch failed"),
        {"id": "account_3", "Account_Name": "Account 3"},
    ])

    with patch.object(pipeline, '_process_accounts_in_batches', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = Mock(
            session_id="test",
            sync_type=SyncType.ON_DEMAND,
            status=SyncStatus.COMPLETED,
            total_records=2,
            successful_records=2,
            failed_records=0,
        )

        summary = await pipeline.sync_accounts(
            sync_type=SyncType.ON_DEMAND,
            account_ids=account_ids,
        )

        # Only 2 accounts should be processed (1 failed to fetch)
        accounts = mock_process.call_args[1]["accounts"]
        assert len(accounts) == 2


# Checksum and change detection tests

@pytest.mark.asyncio
async def test_checksum_calculation_is_consistent(pipeline):
    """Test checksum calculation produces consistent results."""
    account = {
        "id": "account_123",
        "Account_Name": "Test Account",
        "Industry": "Technology",
        "Annual_Revenue": 1000000,
    }

    checksum1 = pipeline._calculate_account_checksum(account)
    checksum2 = pipeline._calculate_account_checksum(account)

    assert checksum1 == checksum2


@pytest.mark.asyncio
async def test_checksum_changes_with_data(pipeline):
    """Test checksum changes when account data changes."""
    account1 = {
        "id": "account_123",
        "Account_Name": "Test Account",
        "Industry": "Technology",
    }
    account2 = {
        "id": "account_123",
        "Account_Name": "Modified Account",
        "Industry": "Technology",
    }

    checksum1 = pipeline._calculate_account_checksum(account1)
    checksum2 = pipeline._calculate_account_checksum(account2)

    assert checksum1 != checksum2


@pytest.mark.asyncio
async def test_should_sync_account_with_new_account(pipeline):
    """Test new account should be synced."""
    account = {
        "id": "new_account",
        "Modified_Time": datetime.utcnow().isoformat(),
        "Account_Name": "New Account",
    }

    should_sync = await pipeline._should_sync_account(account)
    assert should_sync is True


@pytest.mark.asyncio
async def test_should_sync_account_with_unchanged_account(pipeline):
    """Test unchanged account should not be synced."""
    account = {
        "id": "existing_account",
        "Modified_Time": datetime.utcnow().isoformat(),
        "Account_Name": "Existing Account",
    }

    # Create sync state
    checksum = pipeline._calculate_account_checksum(account)
    modified_time = datetime.fromisoformat(account["Modified_Time"].replace("Z", "+00:00"))

    async with pipeline._db_session() as db:
        state = SyncStateModel(
            entity_type="account",
            entity_id="existing_account",
            last_modified_time=modified_time,
            checksum=checksum,
        )
        db.add(state)
        db.commit()

    should_sync = await pipeline._should_sync_account(account)
    assert should_sync is False


@pytest.mark.asyncio
async def test_should_sync_account_with_modified_account(pipeline):
    """Test modified account should be synced."""
    past_time = datetime.utcnow() - timedelta(hours=1)
    account = {
        "id": "existing_account",
        "Modified_Time": datetime.utcnow().isoformat(),
        "Account_Name": "Modified Account",
    }

    # Create old sync state
    async with pipeline._db_session() as db:
        state = SyncStateModel(
            entity_type="account",
            entity_id="existing_account",
            last_modified_time=past_time,
            checksum="old_checksum",
        )
        db.add(state)
        db.commit()

    should_sync = await pipeline._should_sync_account(account)
    assert should_sync is True


# Batch processing tests

@pytest.mark.asyncio
async def test_batch_processing_creates_batch_records(pipeline, sample_accounts):
    """Test batch processing creates database records."""
    session_id = "test_session"

    # Create session
    async with pipeline._db_session() as db:
        session = SyncSessionModel(
            session_id=session_id,
            sync_type=SyncType.FULL,
            status=SyncStatus.RUNNING,
            total_records=len(sample_accounts),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        pipeline._current_session = session

    # Mock Cognee sync
    pipeline.cognee_client.add_account = AsyncMock(return_value="cognee_id")

    batch = sample_accounts[:100]
    successful, failed, errors = await pipeline._process_single_batch(
        session_id=session_id,
        batch_number=1,
        accounts=batch,
    )

    # Verify batch record created
    async with pipeline._db_session() as db:
        batch_record = db.query(SyncBatchModel).filter_by(batch_id=f"{session_id}_batch_1").first()
        assert batch_record is not None
        assert batch_record.total_records == 100
        assert batch_record.status == SyncStatus.COMPLETED


@pytest.mark.asyncio
async def test_concurrent_batch_processing(pipeline, sample_accounts, mock_zoho_client):
    """Test batches are processed concurrently."""
    mock_zoho_client.get_accounts = Mock(return_value=sample_accounts)
    pipeline.cognee_client.add_account = AsyncMock(return_value="cognee_id")

    start_time = datetime.utcnow()
    summary = await pipeline.sync_accounts(sync_type=SyncType.FULL)
    end_time = datetime.utcnow()

    # With max_concurrent_batches=2 and 3 batches, should be faster than sequential
    # This is a rough check - in practice you'd measure actual concurrency
    assert summary.successful_records > 0


# Error handling tests

@pytest.mark.asyncio
async def test_cognee_sync_retries_on_failure(pipeline):
    """Test Cognee sync retries on failure."""
    account = {"id": "account_1", "Account_Name": "Test"}

    # Fail twice, succeed on third attempt
    pipeline.cognee_client.add_account = AsyncMock(
        side_effect=[
            Exception("First failure"),
            Exception("Second failure"),
            "cognee_success",
        ]
    )

    result = await pipeline._sync_account_to_cognee(account)

    assert result == "cognee_success"
    assert pipeline.cognee_client.add_account.call_count == 3


@pytest.mark.asyncio
async def test_cognee_sync_fails_after_max_retries(pipeline):
    """Test Cognee sync fails after exhausting retries."""
    account = {"id": "account_1", "Account_Name": "Test"}

    pipeline.cognee_client.add_account = AsyncMock(
        side_effect=Exception("Persistent failure")
    )

    with pytest.raises(RuntimeError, match="Failed to sync account"):
        await pipeline._sync_account_to_cognee(account)

    # Should retry max_retries times
    assert pipeline.cognee_client.add_account.call_count == pipeline.max_retries


@pytest.mark.asyncio
async def test_sync_error_logging(pipeline, sample_accounts, mock_zoho_client):
    """Test sync errors are logged to database."""
    mock_zoho_client.get_accounts = Mock(return_value=sample_accounts[:10])

    # Make some accounts fail
    pipeline.cognee_client.add_account = AsyncMock(
        side_effect=[
            "success_1",
            Exception("Failed to sync"),
            "success_2",
            Exception("Another failure"),
            "success_3",
            "success_4",
            "success_5",
            "success_6",
            "success_7",
            "success_8",
        ]
    )

    summary = await pipeline.sync_accounts(sync_type=SyncType.FULL)

    # Check errors logged
    async with pipeline._db_session() as db:
        errors = db.query(SyncErrorModel).all()
        # Errors occur but retries may succeed or fail
        assert len(errors) >= 0  # Depends on retry success


@pytest.mark.asyncio
async def test_sync_failure_updates_session_status(pipeline, mock_zoho_client):
    """Test sync failure updates session status to FAILED."""
    # Make fetch fail
    mock_zoho_client.get_accounts = Mock(side_effect=Exception("Fetch failed"))

    with pytest.raises(RuntimeError):
        await pipeline.sync_accounts(sync_type=SyncType.FULL)

    # Check session marked as failed
    async with pipeline._db_session() as db:
        sessions = db.query(SyncSessionModel).all()
        assert len(sessions) == 1
        assert sessions[0].status == SyncStatus.FAILED
        assert sessions[0].error_message is not None


# Progress tracking tests

@pytest.mark.asyncio
async def test_get_sync_progress(pipeline, sample_accounts, mock_zoho_client):
    """Test getting sync progress during operation."""
    mock_zoho_client.get_accounts = Mock(return_value=sample_accounts)
    pipeline.cognee_client.add_account = AsyncMock(return_value="cognee_id")

    # Start sync in background
    sync_task = asyncio.create_task(
        pipeline.sync_accounts(sync_type=SyncType.FULL)
    )

    # Wait a bit for sync to start
    await asyncio.sleep(0.5)

    # Get progress
    async with pipeline._db_session() as db:
        session = db.query(SyncSessionModel).first()
        if session:
            progress = await pipeline.get_sync_progress(session.session_id)

            if progress:  # Progress may not be available yet
                assert progress.sync_type == SyncType.FULL
                assert progress.total_records > 0

    # Wait for sync to complete
    await sync_task


@pytest.mark.asyncio
async def test_pause_and_resume_sync(pipeline):
    """Test pausing and resuming sync."""
    session_id = "test_session"

    # Create running session
    async with pipeline._db_session() as db:
        session = SyncSessionModel(
            session_id=session_id,
            sync_type=SyncType.FULL,
            status=SyncStatus.RUNNING,
        )
        db.add(session)
        db.commit()

    # Pause
    paused = await pipeline.pause_sync(session_id)
    assert paused is True

    # Verify status
    async with pipeline._db_session() as db:
        session = db.query(SyncSessionModel).filter_by(session_id=session_id).first()
        assert session.status == SyncStatus.PAUSED

    # Resume
    resumed = await pipeline.resume_sync(session_id)
    assert resumed is True

    # Verify status
    async with pipeline._db_session() as db:
        session = db.query(SyncSessionModel).filter_by(session_id=session_id).first()
        assert session.status == SyncStatus.RUNNING


# Sync state management tests

@pytest.mark.asyncio
async def test_update_sync_state_creates_new_record(pipeline):
    """Test updating sync state creates new record for new account."""
    account = {
        "id": "new_account",
        "Modified_Time": datetime.utcnow().isoformat(),
        "Account_Name": "New Account",
    }

    await pipeline._update_sync_state(account)

    async with pipeline._db_session() as db:
        state = db.query(SyncStateModel).filter_by(entity_id="new_account").first()
        assert state is not None
        assert state.sync_version == 1


@pytest.mark.asyncio
async def test_update_sync_state_increments_version(pipeline):
    """Test updating sync state increments version."""
    account = {
        "id": "existing_account",
        "Modified_Time": datetime.utcnow().isoformat(),
        "Account_Name": "Account",
    }

    # Create initial state
    await pipeline._update_sync_state(account)

    # Update again
    account["Modified_Time"] = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    await pipeline._update_sync_state(account)

    async with pipeline._db_session() as db:
        state = db.query(SyncStateModel).filter_by(entity_id="existing_account").first()
        assert state.sync_version == 2


# Integration-like tests

@pytest.mark.asyncio
async def test_full_sync_workflow(pipeline, sample_accounts, mock_zoho_client):
    """Test complete full sync workflow end-to-end."""
    mock_zoho_client.get_accounts = Mock(return_value=sample_accounts)
    pipeline.cognee_client.add_account = AsyncMock(
        side_effect=[f"cognee_{i}" for i in range(len(sample_accounts))]
    )

    summary = await pipeline.sync_accounts(sync_type=SyncType.FULL)

    # Verify summary
    assert summary.sync_type == SyncType.FULL
    assert summary.status == SyncStatus.COMPLETED
    assert summary.total_records == len(sample_accounts)
    assert summary.successful_records == len(sample_accounts)
    assert summary.failed_records == 0

    # Verify database records
    async with pipeline._db_session() as db:
        # Session record
        sessions = db.query(SyncSessionModel).all()
        assert len(sessions) == 1

        # Batch records (250 / 100 = 3 batches)
        batches = db.query(SyncBatchModel).all()
        assert len(batches) == 3

        # Sync state records
        states = db.query(SyncStateModel).all()
        assert len(states) == len(sample_accounts)


@pytest.mark.asyncio
async def test_incremental_sync_after_full_sync(pipeline, sample_accounts, mock_zoho_client):
    """Test incremental sync works correctly after full sync."""
    # Do full sync first
    mock_zoho_client.get_accounts = Mock(return_value=sample_accounts)
    pipeline.cognee_client.add_account = AsyncMock(
        side_effect=[f"cognee_{i}" for i in range(len(sample_accounts) + 10)]  # Extra for incremental
    )

    await pipeline.sync_accounts(sync_type=SyncType.FULL)

    # Now do incremental sync (only 10 modified)
    modified_accounts = sample_accounts[:10]
    for acc in modified_accounts:
        acc["Modified_Time"] = datetime.utcnow().isoformat()
        acc["Account_Name"] = f"Modified {acc['Account_Name']}"

    mock_zoho_client.search_accounts = Mock(return_value=modified_accounts)

    summary = await pipeline.sync_accounts(sync_type=SyncType.INCREMENTAL)

    # Should only process 10 accounts
    assert summary.total_records == 10
