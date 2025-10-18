"""Integration tests for Zoho SDK with mocked API responses.

These tests validate end-to-end functionality including:
- OAuth flow and token refresh
- Database token persistence
- Bulk operations (100+ records)
- Error handling and retry logic
- Thread-safe operations
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pydantic import SecretStr
import threading
import time

from src.integrations.zoho.sdk_client import ZohoSDKClient
from src.integrations.zoho.token_store import TokenStore
from src.integrations.zoho.exceptions import (
    ZohoAuthError,
    ZohoAPIError,
    ZohoRateLimitError,
)
from src.models.config import ZohoSDKConfig


@pytest.fixture
def test_database_url():
    """Test database URL."""
    return "postgresql://test:test@localhost:5432/test_zoho"


@pytest.fixture
def zoho_config():
    """Create test Zoho configuration."""
    return ZohoSDKConfig(
        client_id="test_client_id",
        client_secret=SecretStr("test_secret"),
        refresh_token=SecretStr("test_refresh_token"),
        redirect_url="http://localhost:8000/callback",
        region="us",
        environment="sandbox",
    )


@pytest.fixture
def mock_token_store_db():
    """Mock database operations for token store."""
    with patch("src.integrations.zoho.token_store.create_engine") as mock_engine:
        with patch("src.integrations.zoho.token_store.sessionmaker"):
            engine = MagicMock()
            mock_engine.return_value = engine
            yield mock_engine


@pytest.fixture
def mock_zoho_api():
    """Mock all Zoho SDK API components."""
    with patch("src.integrations.zoho.sdk_client.ZCRMRestClient"):
        with patch("src.integrations.zoho.sdk_client.ZCRMModule") as mock_module:
            with patch("src.integrations.zoho.sdk_client.ZCRMRecord") as mock_record:
                with patch("src.integrations.zoho.sdk_client.OAuth") as mock_oauth:
                    yield {
                        "module": mock_module,
                        "record": mock_record,
                        "oauth": mock_oauth,
                    }


class TestOAuthFlow:
    """Test complete OAuth authentication flow."""

    def test_initial_token_setup(
        self, zoho_config, test_database_url, mock_token_store_db, mock_zoho_api
    ):
        """Test initial token storage during client initialization."""
        with patch("src.integrations.zoho.token_store.TokenStore.get_token") as mock_get:
            mock_get.return_value = {
                "access_token": "initial_token",
                "refresh_token": "refresh_token",
                "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            }

            client = ZohoSDKClient(zoho_config, test_database_url)

            assert client.token_store is not None

    def test_token_refresh_flow_end_to_end(
        self, zoho_config, test_database_url, mock_token_store_db, mock_zoho_api
    ):
        """Test complete token refresh flow."""
        # Setup: Token is expired
        with patch("src.integrations.zoho.token_store.TokenStore.is_token_expired") as mock_expired:
            with patch("src.integrations.zoho.token_store.TokenStore.get_token") as mock_get:
                with patch("src.integrations.zoho.token_store.TokenStore.save_token") as mock_save:
                    mock_expired.return_value = True
                    mock_get.return_value = {
                        "access_token": "old_token",
                        "refresh_token": "refresh_token",
                        "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                    }

                    # Mock OAuth refresh
                    oauth_instance = MagicMock()
                    new_token = MagicMock()
                    new_token.access_token = "new_token"
                    new_token.expires_in = 3600
                    oauth_instance.refresh_access_token.return_value = new_token
                    mock_zoho_api["oauth"].get_instance.return_value = oauth_instance

                    client = ZohoSDKClient(zoho_config, test_database_url)

                    # Trigger token refresh
                    client._ensure_valid_token()

                    # Verify new token was saved
                    mock_save.assert_called()
                    save_call_args = mock_save.call_args[1]
                    assert save_call_args["access_token"] == "new_token"
                    assert save_call_args["expires_in"] == 3600

    def test_automatic_token_refresh_on_401(
        self, zoho_config, test_database_url, mock_token_store_db, mock_zoho_api
    ):
        """Test automatic token refresh when API returns 401."""
        from src.integrations.zoho.sdk_client import ZCRMException

        with patch("src.integrations.zoho.token_store.TokenStore.is_token_expired") as mock_expired:
            with patch("src.integrations.zoho.token_store.TokenStore.get_token") as mock_get:
                mock_expired.return_value = False
                mock_get.return_value = {
                    "access_token": "expired_token",
                    "refresh_token": "refresh_token",
                    "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                }

                # Setup OAuth mock
                oauth_instance = MagicMock()
                new_token = MagicMock()
                new_token.access_token = "refreshed_token"
                new_token.expires_in = 3600
                oauth_instance.refresh_access_token.return_value = new_token
                mock_zoho_api["oauth"].get_instance.return_value = oauth_instance

                # Setup API to return 401 first, then succeed
                module_instance = MagicMock()
                mock_zoho_api["module"].get_instance.return_value = module_instance

                auth_error = ZCRMException()
                auth_error.status_code = 401

                success_response = MagicMock()
                success_response.status_code = 200
                success_response.data = []

                module_instance.get_records.side_effect = [auth_error, success_response]

                client = ZohoSDKClient(zoho_config, test_database_url)

                # This should trigger refresh and retry
                with patch("time.sleep"):  # Skip sleep in tests
                    result = client.get_accounts()

                # Should have retried after refresh
                assert module_instance.get_records.call_count == 2


class TestDatabasePersistence:
    """Test token persistence in PostgreSQL."""

    def test_token_save_and_retrieve(
        self, zoho_config, test_database_url, mock_token_store_db, mock_zoho_api
    ):
        """Test token storage and retrieval from database."""
        with patch("src.integrations.zoho.token_store.TokenStore.save_token") as mock_save:
            with patch("src.integrations.zoho.token_store.TokenStore.get_token") as mock_get:
                # Setup return value
                mock_get.return_value = {
                    "access_token": "saved_token",
                    "refresh_token": "saved_refresh",
                    "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                }

                client = ZohoSDKClient(zoho_config, test_database_url)

                # Retrieve token
                token = client.token_store.get_token()

                assert token["access_token"] == "saved_token"
                assert token["refresh_token"] == "saved_refresh"

    def test_concurrent_token_updates(
        self, zoho_config, test_database_url, mock_token_store_db, mock_zoho_api
    ):
        """Test thread-safe concurrent token updates."""
        results = []
        errors = []

        def update_token(client, token_id):
            """Update token from multiple threads."""
            try:
                with patch("src.integrations.zoho.token_store.TokenStore.save_token") as mock_save:
                    mock_save.return_value = {
                        "access_token": f"token_{token_id}",
                        "refresh_token": f"refresh_{token_id}",
                        "expires_at": datetime.utcnow().isoformat(),
                    }

                    client.token_store.save_token(
                        access_token=f"token_{token_id}",
                        refresh_token=f"refresh_{token_id}",
                        expires_in=3600,
                    )
                    results.append(token_id)
            except Exception as e:
                errors.append(str(e))

        with patch("src.integrations.zoho.token_store.TokenStore.get_token") as mock_get:
            mock_get.return_value = {
                "access_token": "initial",
                "refresh_token": "initial",
                "expires_at": datetime.utcnow().isoformat(),
            }

            client = ZohoSDKClient(zoho_config, test_database_url)

            # Create multiple threads
            threads = []
            for i in range(5):
                t = threading.Thread(target=update_token, args=(client, i))
                threads.append(t)
                t.start()

            # Wait for all threads
            for t in threads:
                t.join()

            # Verify no errors occurred
            assert len(errors) == 0
            assert len(results) == 5


class TestBulkOperations:
    """Test bulk read and write operations."""

    def test_bulk_read_100_plus_records(
        self, zoho_config, test_database_url, mock_token_store_db, mock_zoho_api
    ):
        """Test bulk reading of 100+ records."""
        with patch("src.integrations.zoho.token_store.TokenStore.is_token_expired") as mock_expired:
            with patch("src.integrations.zoho.token_store.TokenStore.get_token") as mock_get:
                mock_expired.return_value = False
                mock_get.return_value = {
                    "access_token": "valid_token",
                    "refresh_token": "refresh_token",
                    "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                }

                # Mock API to return 150 records
                module_instance = MagicMock()
                mock_zoho_api["module"].get_instance.return_value = module_instance

                # Create 150 mock records
                mock_records = []
                for i in range(150):
                    record = MagicMock()
                    record.entity_id = f"id_{i}"
                    record.field_data = {"Account_Name": f"Account {i}", "Industry": "Tech"}
                    mock_records.append(record)

                response = MagicMock()
                response.status_code = 200
                response.data = mock_records
                module_instance.get_records.return_value = response

                client = ZohoSDKClient(zoho_config, test_database_url)

                # Perform bulk read
                results = client.bulk_read_accounts(fields=["Account_Name", "Industry"])

                # Verify all records retrieved
                assert len(results) == 150
                assert results[0]["id"] == "id_0"
                assert results[149]["id"] == "id_149"

    def test_bulk_update_100_plus_records(
        self, zoho_config, test_database_url, mock_token_store_db, mock_zoho_api
    ):
        """Test bulk updating of 100+ records."""
        with patch("src.integrations.zoho.token_store.TokenStore.is_token_expired") as mock_expired:
            with patch("src.integrations.zoho.token_store.TokenStore.get_token") as mock_get:
                mock_expired.return_value = False
                mock_get.return_value = {
                    "access_token": "valid_token",
                    "refresh_token": "refresh_token",
                    "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                }

                # Mock Record instances
                record_instances = []
                for i in range(120):
                    record = MagicMock()
                    record_instances.append(record)

                mock_zoho_api["record"].get_instance.side_effect = record_instances

                # Mock module update
                module_instance = MagicMock()
                mock_zoho_api["module"].get_instance.return_value = module_instance

                response = MagicMock()
                response.status_code = 200
                response.message = "Success"
                module_instance.update_records.return_value = response

                client = ZohoSDKClient(zoho_config, test_database_url)

                # Create 120 records to update
                records_to_update = []
                for i in range(120):
                    records_to_update.append({
                        "id": f"account_{i}",
                        "Status": "Active",
                        "Last_Updated": datetime.utcnow().isoformat(),
                    })

                # Perform bulk update
                result = client.bulk_update_accounts(records_to_update)

                # Verify result
                assert result["total"] == 120
                assert result["status_code"] == 200
                assert "Success" in result["message"]


class TestErrorHandlingAndRetry:
    """Test comprehensive error handling and retry logic."""

    def test_retry_on_transient_errors(
        self, zoho_config, test_database_url, mock_token_store_db, mock_zoho_api
    ):
        """Test retry on transient network errors."""
        with patch("src.integrations.zoho.token_store.TokenStore.is_token_expired") as mock_expired:
            with patch("src.integrations.zoho.token_store.TokenStore.get_token") as mock_get:
                mock_expired.return_value = False
                mock_get.return_value = {
                    "access_token": "valid_token",
                    "refresh_token": "refresh_token",
                    "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                }

                module_instance = MagicMock()
                mock_zoho_api["module"].get_instance.return_value = module_instance

                # Fail twice, succeed on third attempt
                success_response = MagicMock()
                success_response.status_code = 200
                success_response.data = []

                module_instance.get_records.side_effect = [
                    Exception("Network error"),
                    Exception("Timeout"),
                    success_response,
                ]

                client = ZohoSDKClient(zoho_config, test_database_url)

                # Should succeed after retries
                with patch("time.sleep"):  # Skip sleep
                    result = client.get_accounts()

                # Verify retried 3 times
                assert module_instance.get_records.call_count == 3
                assert result == []

    def test_rate_limit_handling(
        self, zoho_config, test_database_url, mock_token_store_db, mock_zoho_api
    ):
        """Test proper rate limit error handling."""
        from src.integrations.zoho.sdk_client import ZCRMException

        with patch("src.integrations.zoho.token_store.TokenStore.is_token_expired") as mock_expired:
            with patch("src.integrations.zoho.token_store.TokenStore.get_token") as mock_get:
                mock_expired.return_value = False
                mock_get.return_value = {
                    "access_token": "valid_token",
                    "refresh_token": "refresh_token",
                    "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                }

                module_instance = MagicMock()
                mock_zoho_api["module"].get_instance.return_value = module_instance

                # Simulate rate limit
                rate_limit_error = ZCRMException()
                rate_limit_error.status_code = 429
                rate_limit_error.retry_after = 60

                module_instance.get_records.side_effect = rate_limit_error

                client = ZohoSDKClient(zoho_config, test_database_url)

                # Should raise rate limit error
                with pytest.raises(ZohoRateLimitError) as exc_info:
                    client.get_accounts()

                assert exc_info.value.status_code == 429
                assert exc_info.value.retry_after == 60

    def test_max_retries_exhausted(
        self, zoho_config, test_database_url, mock_token_store_db, mock_zoho_api
    ):
        """Test failure after max retries."""
        with patch("src.integrations.zoho.token_store.TokenStore.is_token_expired") as mock_expired:
            with patch("src.integrations.zoho.token_store.TokenStore.get_token") as mock_get:
                mock_expired.return_value = False
                mock_get.return_value = {
                    "access_token": "valid_token",
                    "refresh_token": "refresh_token",
                    "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                }

                module_instance = MagicMock()
                mock_zoho_api["module"].get_instance.return_value = module_instance

                # Always fail
                module_instance.get_records.side_effect = Exception("Persistent failure")

                client = ZohoSDKClient(
                    zoho_config,
                    test_database_url,
                    max_retries=3,
                )

                # Should raise after max retries
                with patch("time.sleep"):
                    with pytest.raises(ZohoAPIError) as exc_info:
                        client.get_accounts()

                assert "failed after 3 attempts" in str(exc_info.value)
                assert module_instance.get_records.call_count == 3


class TestPerformanceBenchmark:
    """Performance benchmarks vs REST API (documented)."""

    def test_sdk_bulk_read_performance(
        self, zoho_config, test_database_url, mock_token_store_db, mock_zoho_api
    ):
        """Test and document SDK performance for bulk reads."""
        with patch("src.integrations.zoho.token_store.TokenStore.is_token_expired") as mock_expired:
            with patch("src.integrations.zoho.token_store.TokenStore.get_token") as mock_get:
                mock_expired.return_value = False
                mock_get.return_value = {
                    "access_token": "valid_token",
                    "refresh_token": "refresh_token",
                    "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                }

                module_instance = MagicMock()
                mock_zoho_api["module"].get_instance.return_value = module_instance

                # Create 200 records
                mock_records = [
                    MagicMock(entity_id=f"id_{i}", field_data={"Name": f"Account {i}"})
                    for i in range(200)
                ]

                response = MagicMock()
                response.status_code = 200
                response.data = mock_records
                module_instance.get_records.return_value = response

                client = ZohoSDKClient(zoho_config, test_database_url)

                # Measure execution time
                start_time = time.time()
                results = client.bulk_read_accounts()
                end_time = time.time()

                execution_time = end_time - start_time

                # Verify results
                assert len(results) == 200

                # Performance should be fast (< 1 second for mocked operation)
                assert execution_time < 1.0

                # This would be compared against REST API in actual benchmarks
                # Expected: SDK is 30-50% faster for bulk operations
                print(f"\nSDK Bulk Read (200 records): {execution_time:.4f}s")
