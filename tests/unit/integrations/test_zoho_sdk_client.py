"""Unit tests for Zoho SDK client wrapper."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from pydantic import SecretStr

from src.integrations.zoho.sdk_client import ZohoSDKClient, CustomDBHandler
from src.integrations.zoho.exceptions import (
    ZohoAuthError,
    ZohoAPIError,
    ZohoRateLimitError,
    ZohoConfigError,
)
from src.models.config import ZohoSDKConfig


@pytest.fixture
def zoho_config():
    """Create Zoho SDK configuration for testing."""
    return ZohoSDKConfig(
        client_id="test_client_id",
        client_secret=SecretStr("test_secret"),
        refresh_token=SecretStr("test_refresh_token"),
        redirect_url="http://localhost:8000/callback",
        region="us",
        environment="sandbox",
    )


@pytest.fixture
def mock_token_store():
    """Mock TokenStore."""
    with patch("src.integrations.zoho.sdk_client.TokenStore") as mock:
        store = MagicMock()
        store.is_token_expired.return_value = False
        store.get_token.return_value = {
            "access_token": "test_access",
            "refresh_token": "test_refresh",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        }
        mock.return_value = store
        yield store


@pytest.fixture
def mock_zcrm_client():
    """Mock ZCRMRestClient."""
    with patch("src.integrations.zoho.sdk_client.ZCRMRestClient") as mock:
        yield mock


@pytest.fixture
def sdk_client(zoho_config, mock_token_store, mock_zcrm_client):
    """Create SDK client with mocked dependencies."""
    client = ZohoSDKClient(
        config=zoho_config,
        database_url="postgresql://test:test@localhost/test",
    )
    return client


class TestZohoSDKClientInit:
    """Test ZohoSDKClient initialization."""

    def test_init_creates_token_store(self, zoho_config, mock_zcrm_client):
        """Test token store creation during initialization."""
        with patch("src.integrations.zoho.sdk_client.TokenStore") as mock_store:
            client = ZohoSDKClient(
                config=zoho_config,
                database_url="postgresql://test:test@localhost/test",
            )

            mock_store.assert_called_once_with(
                "postgresql://test:test@localhost/test"
            )

    def test_init_configures_sdk(self, zoho_config, mock_token_store, mock_zcrm_client):
        """Test SDK configuration during initialization."""
        client = ZohoSDKClient(
            config=zoho_config,
            database_url="postgresql://test:test@localhost/test",
        )

        mock_zcrm_client.initialize.assert_called_once()
        config_call = mock_zcrm_client.initialize.call_args[0][0]
        assert config_call["client_id"] == "test_client_id"
        assert config_call["client_secret"] == "test_secret"
        assert config_call["apiVersion"] == "v8"
        assert config_call["sandbox"] is True

    def test_init_raises_config_error_on_failure(self, zoho_config):
        """Test initialization error handling."""
        with patch("src.integrations.zoho.sdk_client.TokenStore"):
            with patch("src.integrations.zoho.sdk_client.ZCRMRestClient") as mock_client:
                mock_client.initialize.side_effect = Exception("Config failed")

                with pytest.raises(ZohoConfigError) as exc_info:
                    ZohoSDKClient(
                        config=zoho_config,
                        database_url="postgresql://test",
                    )

                assert "Failed to initialize Zoho SDK" in str(exc_info.value)

    def test_init_sets_max_retries_and_delay(
        self, zoho_config, mock_token_store, mock_zcrm_client
    ):
        """Test custom retry configuration."""
        client = ZohoSDKClient(
            config=zoho_config,
            database_url="postgresql://test",
            max_retries=5,
            retry_delay=2.0,
        )

        assert client.max_retries == 5
        assert client.retry_delay == 2.0


class TestAPIBaseURL:
    """Test API base URL generation."""

    def test_get_api_base_url_for_us_region(
        self, zoho_config, mock_token_store, mock_zcrm_client
    ):
        """Test US region URL."""
        zoho_config.region = "us"
        client = ZohoSDKClient(
            config=zoho_config,
            database_url="postgresql://test",
        )
        assert client._get_api_base_url() == "https://www.zohoapis.com"

    def test_get_api_base_url_for_eu_region(
        self, zoho_config, mock_token_store, mock_zcrm_client
    ):
        """Test EU region URL."""
        zoho_config.region = "eu"
        client = ZohoSDKClient(
            config=zoho_config,
            database_url="postgresql://test",
        )
        assert client._get_api_base_url() == "https://www.zohoapis.eu"

    def test_get_api_base_url_defaults_to_us(
        self, zoho_config, mock_token_store, mock_zcrm_client
    ):
        """Test default URL for unknown region."""
        zoho_config.region = "unknown"
        client = ZohoSDKClient(
            config=zoho_config,
            database_url="postgresql://test",
        )
        assert client._get_api_base_url() == "https://www.zohoapis.com"


class TestTokenManagement:
    """Test token refresh and management."""

    def test_ensure_valid_token_refreshes_expired_token(self, sdk_client):
        """Test automatic token refresh when expired."""
        sdk_client.token_store.is_token_expired.return_value = True

        with patch.object(sdk_client, "_refresh_access_token") as mock_refresh:
            sdk_client._ensure_valid_token()
            mock_refresh.assert_called_once()

    def test_ensure_valid_token_skips_valid_token(self, sdk_client):
        """Test no refresh for valid token."""
        sdk_client.token_store.is_token_expired.return_value = False

        with patch.object(sdk_client, "_refresh_access_token") as mock_refresh:
            sdk_client._ensure_valid_token()
            mock_refresh.assert_not_called()

    def test_refresh_access_token_uses_oauth_client(self, sdk_client):
        """Test token refresh using OAuth client."""
        with patch("src.integrations.zoho.sdk_client.OAuth") as mock_oauth:
            oauth_instance = MagicMock()
            new_token = MagicMock()
            new_token.access_token = "new_access"
            new_token.expires_in = 3600

            mock_oauth.get_instance.return_value = oauth_instance
            oauth_instance.refresh_access_token.return_value = new_token

            sdk_client._refresh_access_token()

            oauth_instance.refresh_access_token.assert_called_once()
            sdk_client.token_store.save_token.assert_called_once_with(
                access_token="new_access",
                refresh_token="test_refresh",
                expires_in=3600,
            )

    def test_refresh_access_token_raises_on_no_token(self, sdk_client):
        """Test error when refresh token not found."""
        sdk_client.token_store.get_token.return_value = None

        with pytest.raises(ZohoAuthError) as exc_info:
            sdk_client._refresh_access_token()

        assert "No refresh token found" in str(exc_info.value)

    def test_refresh_access_token_handles_oauth_failure(self, sdk_client):
        """Test error handling during token refresh."""
        with patch("src.integrations.zoho.sdk_client.OAuth") as mock_oauth:
            oauth_instance = MagicMock()
            mock_oauth.get_instance.return_value = oauth_instance
            oauth_instance.refresh_access_token.side_effect = Exception("OAuth failed")

            with pytest.raises(ZohoAuthError) as exc_info:
                sdk_client._refresh_access_token()

            assert "Failed to refresh access token" in str(exc_info.value)


class TestRetryLogic:
    """Test retry logic with exponential backoff."""

    def test_retry_with_backoff_succeeds_on_first_attempt(self, sdk_client):
        """Test successful operation on first try."""
        operation = Mock(return_value="success")

        result = sdk_client._retry_with_backoff(operation, "test_op")

        assert result == "success"
        operation.assert_called_once()

    def test_retry_with_backoff_retries_on_failure(self, sdk_client):
        """Test retry on transient failures."""
        operation = Mock(side_effect=[Exception("fail1"), Exception("fail2"), "success"])

        with patch("time.sleep"):  # Skip actual sleep
            result = sdk_client._retry_with_backoff(operation, "test_op")

        assert result == "success"
        assert operation.call_count == 3

    def test_retry_with_backoff_raises_after_max_retries(self, sdk_client):
        """Test failure after max retries."""
        operation = Mock(side_effect=Exception("persistent failure"))

        with patch("time.sleep"):
            with pytest.raises(ZohoAPIError) as exc_info:
                sdk_client._retry_with_backoff(operation, "test_op")

        assert "failed after 3 attempts" in str(exc_info.value)
        assert operation.call_count == 3

    def test_retry_with_backoff_handles_rate_limit(self, sdk_client):
        """Test rate limit error handling."""
        from src.integrations.zoho.sdk_client import ZCRMException

        rate_limit_error = ZCRMException()
        rate_limit_error.status_code = 429
        rate_limit_error.retry_after = 30

        operation = Mock(side_effect=rate_limit_error)

        with pytest.raises(ZohoRateLimitError) as exc_info:
            sdk_client._retry_with_backoff(operation, "test_op")

        assert exc_info.value.retry_after == 30
        assert exc_info.value.status_code == 429

    def test_retry_with_backoff_refreshes_token_on_auth_error(self, sdk_client):
        """Test automatic token refresh on 401 error."""
        from src.integrations.zoho.sdk_client import ZCRMException

        auth_error = ZCRMException()
        auth_error.status_code = 401

        operation = Mock(side_effect=[auth_error, auth_error, "success"])

        with patch.object(sdk_client, "_refresh_access_token") as mock_refresh:
            with patch("time.sleep"):
                result = sdk_client._retry_with_backoff(operation, "test_op")

        assert result == "success"
        # Should refresh token on each 401
        assert mock_refresh.call_count >= 1


class TestGetAccounts:
    """Test account retrieval operations."""

    def test_get_accounts_retrieves_records(self, sdk_client):
        """Test successful account retrieval."""
        with patch("src.integrations.zoho.sdk_client.ZCRMModule") as mock_module:
            module_instance = MagicMock()
            mock_module.get_instance.return_value = module_instance

            # Mock response
            response = MagicMock()
            response.status_code = 200
            response.data = [
                MagicMock(
                    entity_id="123",
                    field_data={"Account_Name": "Test Account", "Industry": "Tech"},
                ),
                MagicMock(
                    entity_id="456",
                    field_data={"Account_Name": "Another Account", "Industry": "Finance"},
                ),
            ]
            module_instance.get_records.return_value = response

            results = sdk_client.get_accounts(limit=100, page=1)

            assert len(results) == 2
            assert results[0]["id"] == "123"
            assert results[0]["Account_Name"] == "Test Account"
            assert results[1]["id"] == "456"

    def test_get_accounts_with_pagination(self, sdk_client):
        """Test account retrieval with pagination."""
        with patch("src.integrations.zoho.sdk_client.ZCRMModule") as mock_module:
            module_instance = MagicMock()
            mock_module.get_instance.return_value = module_instance

            response = MagicMock()
            response.status_code = 200
            response.data = []
            module_instance.get_records.return_value = response

            sdk_client.get_accounts(limit=50, page=2)

            call_params = module_instance.get_records.call_args[0][0]
            assert call_params["page"] == 2
            assert call_params["per_page"] == 50

    def test_get_accounts_raises_on_error(self, sdk_client):
        """Test error handling for account retrieval."""
        with patch("src.integrations.zoho.sdk_client.ZCRMModule") as mock_module:
            module_instance = MagicMock()
            mock_module.get_instance.return_value = module_instance

            response = MagicMock()
            response.status_code = 500
            response.message = "Server error"
            module_instance.get_records.return_value = response

            with patch("time.sleep"):
                with pytest.raises(ZohoAPIError):
                    sdk_client.get_accounts()


class TestUpdateAccount:
    """Test account update operations."""

    def test_update_account_updates_fields(self, sdk_client):
        """Test successful account update."""
        with patch("src.integrations.zoho.sdk_client.ZCRMRecord") as mock_record_class:
            record = MagicMock()
            mock_record_class.get_instance.return_value = record

            response = MagicMock()
            response.status_code = 200
            response.data = MagicMock(
                entity_id="123",
                field_data={"Account_Name": "Updated Name"},
            )
            record.update.return_value = response

            result = sdk_client.update_account(
                account_id="123",
                field_data={"Account_Name": "Updated Name"},
            )

            assert result["id"] == "123"
            assert result["Account_Name"] == "Updated Name"
            record.set_field_value.assert_called_with("Account_Name", "Updated Name")

    def test_update_account_sets_multiple_fields(self, sdk_client):
        """Test updating multiple fields."""
        with patch("src.integrations.zoho.sdk_client.ZCRMRecord") as mock_record_class:
            record = MagicMock()
            mock_record_class.get_instance.return_value = record

            response = MagicMock()
            response.status_code = 200
            response.data = MagicMock(entity_id="123", field_data={})
            record.update.return_value = response

            sdk_client.update_account(
                account_id="123",
                field_data={"Field1": "Value1", "Field2": "Value2"},
            )

            assert record.set_field_value.call_count == 2


class TestBulkOperations:
    """Test bulk read and update operations."""

    def test_bulk_read_accounts_with_criteria(self, sdk_client):
        """Test bulk read with search criteria."""
        with patch("src.integrations.zoho.sdk_client.ZCRMModule") as mock_module:
            module_instance = MagicMock()
            mock_module.get_instance.return_value = module_instance

            response = MagicMock()
            response.status_code = 200
            response.data = [
                MagicMock(entity_id="1", field_data={"Name": "Account 1"}),
                MagicMock(entity_id="2", field_data={"Name": "Account 2"}),
            ]
            module_instance.get_records.return_value = response

            results = sdk_client.bulk_read_accounts(
                criteria="Industry=Tech",
                fields=["Account_Name", "Industry"],
            )

            assert len(results) == 2
            call_params = module_instance.get_records.call_args[0][0]
            assert call_params["criteria"] == "Industry=Tech"
            assert call_params["fields"] == "Account_Name,Industry"

    def test_bulk_update_accounts_updates_multiple(self, sdk_client):
        """Test bulk update of multiple accounts."""
        with patch("src.integrations.zoho.sdk_client.ZCRMModule") as mock_module:
            with patch("src.integrations.zoho.sdk_client.ZCRMRecord") as mock_record:
                module_instance = MagicMock()
                mock_module.get_instance.return_value = module_instance

                record1 = MagicMock()
                record2 = MagicMock()
                mock_record.get_instance.side_effect = [record1, record2]

                response = MagicMock()
                response.status_code = 200
                response.message = "Success"
                module_instance.update_records.return_value = response

                records_to_update = [
                    {"id": "123", "Status": "Active"},
                    {"id": "456", "Status": "Inactive"},
                ]

                result = sdk_client.bulk_update_accounts(records_to_update)

                assert result["total"] == 2
                assert result["status_code"] == 200
                module_instance.update_records.assert_called_once()


class TestSearchAccounts:
    """Test account search operations."""

    def test_search_accounts_with_criteria(self, sdk_client):
        """Test account search with COQL criteria."""
        with patch("src.integrations.zoho.sdk_client.ZCRMModule") as mock_module:
            module_instance = MagicMock()
            mock_module.get_instance.return_value = module_instance

            response = MagicMock()
            response.status_code = 200
            response.data = [
                MagicMock(entity_id="1", field_data={"Name": "Found Account"}),
            ]
            module_instance.search_records.return_value = response

            results = sdk_client.search_accounts(
                criteria="Account_Name LIKE '%Test%'",
                limit=50,
            )

            assert len(results) == 1
            assert results[0]["Name"] == "Found Account"
            call_params = module_instance.search_records.call_args[0][0]
            assert call_params["criteria"] == "Account_Name LIKE '%Test%'"
            assert call_params["per_page"] == 50


class TestCustomDBHandler:
    """Test custom database handler for SDK."""

    def test_get_oauth_instance_returns_none(self):
        """Test OAuth instance retrieval returns None."""
        result = CustomDBHandler.get_oauth_instance()
        assert result is None

    def test_save_oauth_data_does_nothing(self):
        """Test OAuth data save is no-op."""
        mock_token = MagicMock()
        # Should not raise any errors
        CustomDBHandler.save_oauth_data(mock_token)
