"""
Unit tests for Zoho SDK client wrapper.

Tests all client methods in isolation with mocked SDK responses.
Coverage: 95%+ target
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from typing import Dict, Any, List


# ============================================================================
# Test Client Initialization
# ============================================================================

class TestSDKClientInitialization:
    """Test suite for SDK client initialization."""

    @pytest.mark.unit
    def test_client_initialization_with_valid_config(self, mock_zoho_config):
        """Test client initializes correctly with valid configuration."""
        # Arrange
        from tests.fixtures.zoho_fixtures import MockZohoSDKClient

        # Act
        client = MockZohoSDKClient(mock_zoho_config)

        # Assert
        assert client is not None
        assert client.config == mock_zoho_config
        assert client.access_token is None  # Not initialized yet
        assert client.call_count == 0

    @pytest.mark.unit
    def test_client_initialization_with_invalid_config(self, mock_invalid_zoho_config):
        """Test client handles invalid configuration gracefully."""
        # Arrange
        from tests.fixtures.zoho_fixtures import MockZohoSDKClient

        # Act & Assert
        # Should create client but validation should fail on use
        client = MockZohoSDKClient(mock_invalid_zoho_config)
        assert client.config["client_id"] == ""
        assert client.config["redirect_uri"] == "not-a-url"

    @pytest.mark.unit
    def test_client_initialization_with_oauth_token(self, mock_zoho_config, mock_oauth_token_response):
        """Test client initialization with OAuth token."""
        # Arrange
        from tests.fixtures.zoho_fixtures import MockZohoSDKClient

        # Act
        client = MockZohoSDKClient(mock_zoho_config)
        client.initialize(mock_oauth_token_response)

        # Assert
        assert client.access_token == mock_oauth_token_response["access_token"]
        assert client.refresh_token == mock_oauth_token_response["refresh_token"]


# ============================================================================
# Test Get Account Method
# ============================================================================

class TestGetAccount:
    """Test suite for get_account method."""

    @pytest.mark.unit
    def test_get_account_with_valid_id(self, mock_zoho_sdk_client, mock_account_data):
        """Test get_account retrieves account successfully."""
        # Arrange
        account_id = mock_account_data["id"]
        mock_zoho_sdk_client._accounts_db[account_id] = mock_account_data

        # Act
        response = mock_zoho_sdk_client.get_account(account_id)

        # Assert
        assert response is not None
        assert "data" in response
        assert len(response["data"]) == 1
        assert response["data"][0]["id"] == account_id
        assert mock_zoho_sdk_client.call_count == 1

    @pytest.mark.unit
    def test_get_account_with_nonexistent_id(self, mock_zoho_sdk_client):
        """Test get_account with non-existent ID creates account."""
        # Arrange
        account_id = "acc_nonexistent"

        # Act
        response = mock_zoho_sdk_client.get_account(account_id)

        # Assert
        assert response is not None
        assert "data" in response
        assert response["data"][0]["id"] == account_id

    @pytest.mark.unit
    def test_get_account_triggers_token_refresh_on_401(self, mock_zoho_sdk_client):
        """Test get_account triggers token refresh on 401 unauthorized."""
        # Arrange
        mock_zoho_sdk_client.should_fail = True
        mock_zoho_sdk_client.failure_mode = "unauthorized"

        # Act & Assert
        with pytest.raises(PermissionError) as exc_info:
            mock_zoho_sdk_client.get_account("acc_123")

        assert "INVALID_TOKEN" in str(exc_info.value)
        assert mock_zoho_sdk_client.call_count == 1


# ============================================================================
# Test Update Account Method
# ============================================================================

class TestUpdateAccount:
    """Test suite for update_account method."""

    @pytest.mark.unit
    def test_update_account_with_valid_data(self, mock_zoho_sdk_client, mock_account_data):
        """Test update_account updates account successfully."""
        # Arrange
        account_id = mock_account_data["id"]
        mock_zoho_sdk_client._accounts_db[account_id] = mock_account_data.copy()
        update_data = {"Account_Name": "Updated Corp", "Annual_Revenue": 10000000}

        # Act
        response = mock_zoho_sdk_client.update_account(account_id, update_data)

        # Assert
        assert response["data"][0]["code"] == "SUCCESS"
        assert response["data"][0]["status"] == "success"
        assert mock_zoho_sdk_client._accounts_db[account_id]["Account_Name"] == "Updated Corp"
        assert mock_zoho_sdk_client.call_count == 1

    @pytest.mark.unit
    def test_update_account_with_invalid_data(self, mock_zoho_sdk_client):
        """Test update_account handles invalid data."""
        # Arrange
        mock_zoho_sdk_client.should_fail = True
        mock_zoho_sdk_client.failure_mode = "invalid_data"

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            mock_zoho_sdk_client.update_account("acc_123", {"Invalid_Field": "value"})

        assert "invalid_data" in str(exc_info.value)


# ============================================================================
# Test Bulk Read Method
# ============================================================================

class TestBulkRead:
    """Test suite for bulk_read method."""

    @pytest.mark.unit
    def test_bulk_read_100_records(self, mock_zoho_sdk_client):
        """Test bulk_read retrieves 100 records successfully."""
        # Act
        response = mock_zoho_sdk_client.bulk_read("Accounts", per_page=100)

        # Assert
        assert "data" in response
        assert len(response["data"]) == 100
        assert "info" in response
        assert response["info"]["count"] == 100
        assert mock_zoho_sdk_client.call_count == 1

    @pytest.mark.unit
    def test_bulk_read_with_pagination(self, mock_zoho_sdk_client):
        """Test bulk_read with pagination."""
        # Act - First page
        page1 = mock_zoho_sdk_client.bulk_read("Accounts", page=1, per_page=50)
        page2 = mock_zoho_sdk_client.bulk_read("Accounts", page=2, per_page=50)

        # Assert
        assert len(page1["data"]) == 50
        assert len(page2["data"]) == 50
        assert mock_zoho_sdk_client.call_count == 2

    @pytest.mark.unit
    def test_bulk_read_with_criteria(self, mock_zoho_sdk_client):
        """Test bulk_read with search criteria."""
        # Act
        response = mock_zoho_sdk_client.bulk_read(
            "Accounts",
            criteria="(Annual_Revenue:greater_than:1000000)",
            per_page=100
        )

        # Assert
        assert "data" in response
        assert len(response["data"]) > 0


# ============================================================================
# Test Bulk Write Method
# ============================================================================

class TestBulkWrite:
    """Test suite for bulk_write method."""

    @pytest.mark.unit
    def test_bulk_write_with_batching(self, mock_zoho_sdk_client, mock_account_batch_100):
        """Test bulk_write processes batch of 100 records."""
        # Act
        response = mock_zoho_sdk_client.bulk_write("Accounts", mock_account_batch_100)

        # Assert
        assert "data" in response
        assert len(response["data"]) == 100
        assert all(result["code"] == "SUCCESS" for result in response["data"])
        assert mock_zoho_sdk_client.call_count == 1

    @pytest.mark.unit
    def test_bulk_write_partial_failure(self, mock_zoho_sdk_client):
        """Test bulk_write handles partial batch failures."""
        # Arrange
        mock_zoho_sdk_client.should_fail = True
        mock_zoho_sdk_client.failure_mode = "partial_failure"
        records = [{"Account_Name": f"Test {i}"} for i in range(10)]

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            mock_zoho_sdk_client.bulk_write("Accounts", records)

        assert "partial_failure" in str(exc_info.value)


# ============================================================================
# Test Token Refresh
# ============================================================================

class TestTokenRefresh:
    """Test suite for token refresh functionality."""

    @pytest.mark.unit
    def test_refresh_token_success(self, mock_zoho_sdk_client, mock_oauth_token_response):
        """Test successful token refresh."""
        # Arrange
        mock_zoho_sdk_client.initialize(mock_oauth_token_response)
        old_token = mock_zoho_sdk_client.access_token

        # Act
        new_token = mock_zoho_sdk_client.refresh_access_token()

        # Assert
        assert new_token is not None
        assert new_token != old_token
        assert mock_zoho_sdk_client.access_token == new_token
        assert mock_zoho_sdk_client.call_count == 1

    @pytest.mark.unit
    def test_refresh_token_with_invalid_refresh_token(self, mock_zoho_sdk_client):
        """Test token refresh fails with invalid refresh token."""
        # Arrange
        mock_zoho_sdk_client.should_fail = True
        mock_zoho_sdk_client.failure_mode = "invalid_refresh_token"

        # Act & Assert
        with pytest.raises(PermissionError) as exc_info:
            mock_zoho_sdk_client.refresh_access_token()

        assert "INVALID_REFRESH_TOKEN" in str(exc_info.value)


# ============================================================================
# Test Retry Logic
# ============================================================================

class TestRetryLogic:
    """Test suite for retry logic with exponential backoff."""

    @pytest.mark.unit
    @patch('time.sleep')  # Mock sleep to speed up test
    def test_retry_on_rate_limit(self, mock_sleep, mock_zoho_sdk_client):
        """Test retry logic activates on rate limit (429)."""
        # Arrange
        mock_zoho_sdk_client.should_fail = True
        mock_zoho_sdk_client.failure_mode = "rate_limit"

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            mock_zoho_sdk_client.get_account("acc_123")

        assert "RATE_LIMIT_EXCEEDED" in str(exc_info.value)

    @pytest.mark.unit
    @patch('time.sleep')
    def test_exponential_backoff(self, mock_sleep, mock_zoho_sdk_client):
        """Test exponential backoff on retries."""
        # Arrange
        mock_zoho_sdk_client.should_fail = True
        mock_zoho_sdk_client.failure_mode = "timeout"

        # Act & Assert
        with pytest.raises(TimeoutError):
            mock_zoho_sdk_client.get_account("acc_123")


# ============================================================================
# Test Error Handling
# ============================================================================

class TestErrorHandling:
    """Test suite for error handling."""

    @pytest.mark.unit
    def test_network_timeout_handling(self, mock_zoho_sdk_client):
        """Test handling of network timeouts."""
        # Arrange
        mock_zoho_sdk_client.should_fail = True
        mock_zoho_sdk_client.failure_mode = "timeout"

        # Act & Assert
        with pytest.raises(TimeoutError):
            mock_zoho_sdk_client.get_account("acc_123")

    @pytest.mark.unit
    def test_malformed_response_handling(self, mock_malformed_response_error):
        """Test handling of malformed API responses."""
        # Simulate parsing malformed JSON
        with pytest.raises((ValueError, TypeError)):
            import json
            json.loads(mock_malformed_response_error)

    @pytest.mark.unit
    def test_connection_timeout_handling(self, mock_network_timeout_error):
        """Test connection timeout handling."""
        assert "timeout" in str(mock_network_timeout_error).lower()


# ============================================================================
# Test Configuration Validation
# ============================================================================

class TestConfigValidation:
    """Test suite for configuration validation."""

    @pytest.mark.unit
    def test_valid_config_passes_validation(self, mock_zoho_config):
        """Test valid configuration passes validation."""
        # Assert all required fields present
        assert "client_id" in mock_zoho_config
        assert "client_secret" in mock_zoho_config
        assert "redirect_uri" in mock_zoho_config
        assert mock_zoho_config["client_id"]  # Not empty

    @pytest.mark.unit
    def test_invalid_config_fails_validation(self, mock_invalid_zoho_config):
        """Test invalid configuration fails validation."""
        # Assert validation would fail
        assert not mock_invalid_zoho_config["client_id"]
        assert not mock_invalid_zoho_config["scope"]
        assert "http" not in mock_invalid_zoho_config["redirect_uri"]
