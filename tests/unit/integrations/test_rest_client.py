"""
REST Client Test Suite (Tier 3)
Tests Zoho CRM REST API client for fallback operations.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import json


class TestRESTClientInitialization:
    """Test REST client initialization."""

    def test_client_initialization_with_credentials(self):
        """Client should initialize with valid credentials."""
        from src.integrations.rest_client import RESTClient

        client = RESTClient(
            client_id="rest_client_id",
            client_secret="rest_secret",
            refresh_token="rest_token",
            api_domain="https://www.zohoapis.com"
        )

        assert client.client_id == "rest_client_id"
        assert client.api_domain == "https://www.zohoapis.com"

    def test_client_initialization_default_domain(self):
        """Client should use default API domain."""
        from src.integrations.rest_client import RESTClient

        client = RESTClient(
            client_id="id",
            client_secret="secret",
            refresh_token="token"
        )

        assert client.api_domain.startswith("https://")

    def test_initialization_from_config(self):
        """Client should initialize from config object."""
        from src.integrations.rest_client import RESTClient

        config = {
            "client_id": "config_id",
            "client_secret": "config_secret",
            "refresh_token": "config_token"
        }

        client = RESTClient.from_config(config)

        assert client.client_id == "config_id"


class TestRESTClientAccountOperations:
    """Test REST API account operations."""

    @pytest.mark.asyncio
    async def test_get_single_account(self, rest_client, mock_http_client):
        """Get single account should return correct data."""
        mock_http_client.get.return_value = AsyncMock(
            status=200,
            json=AsyncMock(return_value={
                "data": [{
                    "id": "REST001",
                    "Account_Name": "REST Account",
                    "Account_Number": "12345"
                }]
            })
        )

        result = await rest_client.get_account("REST001")

        assert result["id"] == "REST001"
        assert result["Account_Name"] == "REST Account"

    @pytest.mark.asyncio
    async def test_get_multiple_accounts_with_pagination(self, rest_client, mock_http_client):
        """Get multiple accounts should handle pagination."""
        mock_http_client.get.return_value = AsyncMock(
            status=200,
            json=AsyncMock(return_value={
                "data": [
                    {"id": f"A{i}", "Account_Name": f"Account {i}"} for i in range(200)
                ],
                "info": {
                    "page": 1,
                    "per_page": 200,
                    "count": 200,
                    "more_records": True
                }
            })
        )

        result = await rest_client.get_accounts(page=1, per_page=200)

        assert len(result["data"]) == 200
        assert result["info"]["more_records"] is True

    @pytest.mark.asyncio
    async def test_update_account_success(self, rest_client, mock_http_client):
        """Update account should work correctly."""
        mock_http_client.put.return_value = AsyncMock(
            status=200,
            json=AsyncMock(return_value={
                "data": [{
                    "code": "SUCCESS",
                    "details": {
                        "id": "UPD001",
                        "Modified_Time": datetime.now().isoformat()
                    }
                }]
            })
        )

        result = await rest_client.update_account(
            "UPD001",
            {"Account_Name": "Updated"}
        )

        assert result["code"] == "SUCCESS"

    @pytest.mark.asyncio
    async def test_search_accounts_with_criteria(self, rest_client, mock_http_client):
        """Search accounts should use COQL."""
        mock_http_client.get.return_value = AsyncMock(
            status=200,
            json=AsyncMock(return_value={
                "data": [
                    {"id": "S001", "Annual_Revenue": 1000000},
                    {"id": "S002", "Annual_Revenue": 2000000}
                ],
                "info": {"count": 2}
            })
        )

        result = await rest_client.search_accounts(
            criteria={"Annual_Revenue": {"$gt": 500000}}
        )

        assert len(result["data"]) == 2

    @pytest.mark.asyncio
    async def test_create_account_operation(self, rest_client, mock_http_client):
        """Create account should work correctly."""
        mock_http_client.post.return_value = AsyncMock(
            status=201,
            json=AsyncMock(return_value={
                "data": [{
                    "code": "SUCCESS",
                    "details": {
                        "id": "NEW_REST",
                        "Created_Time": datetime.now().isoformat()
                    }
                }]
            })
        )

        result = await rest_client.create_account({"Account_Name": "New REST Account"})

        assert result["code"] == "SUCCESS"
        assert result["details"]["id"] == "NEW_REST"

    @pytest.mark.asyncio
    async def test_delete_account_operation(self, rest_client, mock_http_client):
        """Delete account should work correctly."""
        mock_http_client.delete.return_value = AsyncMock(
            status=200,
            json=AsyncMock(return_value={
                "data": [{
                    "code": "SUCCESS",
                    "details": {"id": "DEL001"}
                }]
            })
        )

        result = await rest_client.delete_account("DEL001")

        assert result["code"] == "SUCCESS"


class TestRESTClientRateLimiting:
    """Test rate limit handling (5000 requests/day)."""

    @pytest.mark.asyncio
    async def test_rate_limit_tracking(self, rest_client, mock_http_client):
        """Rate limit usage should be tracked."""
        mock_http_client.get.return_value = AsyncMock(
            status=200,
            headers={"X-RateLimit-Remaining": "4999", "X-RateLimit-Limit": "5000"},
            json=AsyncMock(return_value={"data": [{"id": "RL001"}]})
        )

        await rest_client.get_account("RL001")

        assert rest_client.rate_limit_remaining == 4999
        assert rest_client.rate_limit_total == 5000

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_raises_error(self, rest_client, mock_http_client):
        """Exceeding rate limit should raise error."""
        from src.integrations.rest_client import RateLimitError

        mock_http_client.get.return_value = AsyncMock(
            status=429,
            json=AsyncMock(return_value={
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Rate limit exceeded"
            })
        )

        with pytest.raises(RateLimitError):
            await rest_client.get_account("RL_EXCEEDED")

    @pytest.mark.asyncio
    async def test_rate_limit_warning_at_90_percent(self, rest_client, mock_http_client):
        """Warning should be logged at 90% rate limit."""
        mock_http_client.get.return_value = AsyncMock(
            status=200,
            headers={"X-RateLimit-Remaining": "500", "X-RateLimit-Limit": "5000"},
            json=AsyncMock(return_value={"data": [{"id": "RL90"}]})
        )

        with patch('logging.warning') as mock_warning:
            await rest_client.get_account("RL90")

            # Should warn when remaining < 10%
            assert mock_warning.called

    @pytest.mark.asyncio
    async def test_rate_limit_reset_time(self, rest_client, mock_http_client):
        """Rate limit reset time should be tracked."""
        reset_time = datetime.now() + timedelta(hours=1)
        mock_http_client.get.return_value = AsyncMock(
            status=200,
            headers={
                "X-RateLimit-Remaining": "4000",
                "X-RateLimit-Reset": str(int(reset_time.timestamp()))
            },
            json=AsyncMock(return_value={"data": [{"id": "RLR001"}]})
        )

        await rest_client.get_account("RLR001")

        assert rest_client.rate_limit_reset is not None


class TestRESTClientTokenManagement:
    """Test OAuth token refresh."""

    @pytest.mark.asyncio
    async def test_token_auto_refresh_on_expiry(self, rest_client, mock_oauth_client):
        """Expired token should auto-refresh."""
        # Set expired token
        rest_client.access_token = "expired"
        rest_client.token_expires_at = datetime.now() - timedelta(hours=1)

        mock_oauth_client.post.return_value = AsyncMock(
            status=200,
            json=AsyncMock(return_value={
                "access_token": "refreshed_token",
                "expires_in": 3600
            })
        )

        await rest_client._ensure_valid_token()

        assert rest_client.access_token == "refreshed_token"

    @pytest.mark.asyncio
    async def test_token_refresh_failure_raises_error(self, rest_client, mock_oauth_client):
        """Token refresh failure should raise error."""
        from src.integrations.rest_client import AuthenticationError

        mock_oauth_client.post.return_value = AsyncMock(
            status=400,
            json=AsyncMock(return_value={"error": "invalid_grant"})
        )

        with pytest.raises(AuthenticationError):
            await rest_client._refresh_token()

    @pytest.mark.asyncio
    async def test_token_included_in_requests(self, rest_client, mock_http_client):
        """Access token should be included in requests."""
        rest_client.access_token = "valid_token"
        rest_client.token_expires_at = datetime.now() + timedelta(hours=1)

        mock_http_client.get.return_value = AsyncMock(
            status=200,
            json=AsyncMock(return_value={"data": [{"id": "T001"}]})
        )

        await rest_client.get_account("T001")

        # Verify Authorization header was set
        call_kwargs = mock_http_client.get.call_args[1]
        assert "headers" in call_kwargs
        assert call_kwargs["headers"].get("Authorization") == "Zoho-oauthtoken valid_token"


class TestRESTClientErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_404_not_found_handled(self, rest_client, mock_http_client):
        """404 errors should raise NotFoundError."""
        from src.integrations.rest_client import NotFoundError

        mock_http_client.get.return_value = AsyncMock(
            status=404,
            json=AsyncMock(return_value={
                "code": "INVALID_MODULE",
                "message": "Record not found"
            })
        )

        with pytest.raises(NotFoundError):
            await rest_client.get_account("NOTFOUND")

    @pytest.mark.asyncio
    async def test_500_server_error_handled(self, rest_client, mock_http_client):
        """500 errors should raise ServerError."""
        from src.integrations.rest_client import ServerError

        mock_http_client.get.return_value = AsyncMock(
            status=500,
            json=AsyncMock(return_value={
                "code": "INTERNAL_ERROR",
                "message": "Internal server error"
            })
        )

        with pytest.raises(ServerError):
            await rest_client.get_account("ERROR500")

    @pytest.mark.asyncio
    async def test_network_timeout_handled(self, rest_client, mock_http_client):
        """Network timeouts should raise TimeoutError."""
        from src.integrations.rest_client import TimeoutError
        import asyncio as aio

        mock_http_client.get.side_effect = aio.TimeoutError()

        with pytest.raises(TimeoutError):
            await rest_client.get_account("TIMEOUT", timeout=1)

    @pytest.mark.asyncio
    async def test_invalid_json_response_handled(self, rest_client, mock_http_client):
        """Invalid JSON should be handled."""
        from src.integrations.rest_client import InvalidResponseError

        mock_http_client.get.return_value = AsyncMock(
            status=200,
            json=AsyncMock(side_effect=json.JSONDecodeError("Invalid", "", 0))
        )

        with pytest.raises(InvalidResponseError):
            await rest_client.get_account("BADJSON")


class TestRESTClientHealthCheck:
    """Test health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, rest_client, mock_http_client):
        """Successful health check should return healthy."""
        mock_http_client.get.return_value = AsyncMock(
            status=200,
            json=AsyncMock(return_value={"users": []})
        )

        health = await rest_client.health_check()

        assert health["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_failure(self, rest_client, mock_http_client):
        """Failed health check should return unhealthy."""
        mock_http_client.get.side_effect = Exception("Connection failed")

        health = await rest_client.health_check()

        assert health["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_health_check_includes_metrics(self, rest_client, mock_http_client):
        """Health check should include metrics."""
        mock_http_client.get.return_value = AsyncMock(
            status=200,
            headers={"X-RateLimit-Remaining": "4500"},
            json=AsyncMock(return_value={"users": []})
        )

        health = await rest_client.health_check()

        assert "latency_ms" in health
        assert "rate_limit_remaining" in health


class TestRESTClientBulkOperations:
    """Test bulk operations."""

    @pytest.mark.asyncio
    async def test_bulk_create_accounts(self, rest_client, mock_http_client):
        """Bulk create should batch correctly."""
        mock_http_client.post.return_value = AsyncMock(
            status=200,
            json=AsyncMock(return_value={
                "data": [
                    {"code": "SUCCESS", "details": {"id": f"BULK{i}"}}
                    for i in range(100)
                ]
            })
        )

        accounts = [{"Account_Name": f"Bulk {i}"} for i in range(100)]
        result = await rest_client.create_accounts_bulk(accounts)

        assert len(result["data"]) == 100

    @pytest.mark.asyncio
    async def test_bulk_update_accounts(self, rest_client, mock_http_client):
        """Bulk update should work correctly."""
        mock_http_client.put.return_value = AsyncMock(
            status=200,
            json=AsyncMock(return_value={
                "data": [
                    {"code": "SUCCESS", "details": {"id": f"UPD{i}"}}
                    for i in range(50)
                ]
            })
        )

        updates = [{"id": f"UPD{i}", "Status": "Active"} for i in range(50)]
        result = await rest_client.update_accounts_bulk(updates)

        assert len(result["data"]) == 50
