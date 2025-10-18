"""
MCP Client Test Suite (Tier 1)
Tests Zoho CRM MCP tool integration for agent-based operations.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import json


class TestMCPClientInitialization:
    """Test MCP client initialization."""

    def test_client_initialization_with_valid_credentials(self):
        """Client should initialize with valid credentials."""
        from src.integrations.mcp_client import MCPClient

        client = MCPClient(
            client_id="test_client_id",
            client_secret="test_secret",
            refresh_token="test_token"
        )

        assert client.client_id == "test_client_id"
        assert client.is_initialized

    def test_client_initialization_missing_credentials_raises_error(self):
        """Missing credentials should raise ValueError."""
        from src.integrations.mcp_client import MCPClient

        with pytest.raises(ValueError):
            MCPClient(client_id="", client_secret="", refresh_token="")

    def test_client_initialization_with_environment_variables(self, monkeypatch):
        """Client should initialize from environment variables."""
        from src.integrations.mcp_client import MCPClient

        monkeypatch.setenv("ZOHO_CLIENT_ID", "env_client_id")
        monkeypatch.setenv("ZOHO_CLIENT_SECRET", "env_secret")
        monkeypatch.setenv("ZOHO_REFRESH_TOKEN", "env_token")

        client = MCPClient.from_env()

        assert client.client_id == "env_client_id"


class TestMCPClientAccountOperations:
    """Test MCP client account CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_account_with_tool_permissions(self, mcp_client, mock_mcp_server):
        """Get account should work with tool permissions."""
        mock_mcp_server.call_tool.return_value = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "id": "123",
                        "name": "Test Account",
                        "status": "Active"
                    })
                }
            ]
        }

        result = await mcp_client.get_account("123")

        assert result["id"] == "123"
        assert result["name"] == "Test Account"
        mock_mcp_server.call_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_account_not_found(self, mcp_client, mock_mcp_server):
        """Get account with invalid ID should raise NotFoundError."""
        from src.integrations.mcp_client import NotFoundError

        mock_mcp_server.call_tool.return_value = {
            "content": [{"type": "error", "error": "Account not found"}],
            "isError": True
        }

        with pytest.raises(NotFoundError):
            await mcp_client.get_account("INVALID")

    @pytest.mark.asyncio
    async def test_update_account_via_mcp_endpoint(self, mcp_client, mock_mcp_server):
        """Update account should use MCP endpoint."""
        mock_mcp_server.call_tool.return_value = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "id": "456",
                        "name": "Updated Name",
                        "updated_at": datetime.now().isoformat()
                    })
                }
            ]
        }

        result = await mcp_client.update_account(
            "456",
            {"name": "Updated Name"}
        )

        assert result["name"] == "Updated Name"
        assert "updated_at" in result

    @pytest.mark.asyncio
    async def test_search_accounts_with_criteria(self, mcp_client, mock_mcp_server):
        """Search accounts should use MCP search tool."""
        mock_mcp_server.call_tool.return_value = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "results": [
                            {"id": "A1", "status": "Active"},
                            {"id": "A2", "status": "Active"}
                        ],
                        "total": 2
                    })
                }
            ]
        }

        result = await mcp_client.search_accounts({"status": "Active"})

        assert len(result["results"]) == 2
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_create_account_operation(self, mcp_client, mock_mcp_server):
        """Create account should work via MCP."""
        mock_mcp_server.call_tool.return_value = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "id": "NEW123",
                        "name": "New Account",
                        "created_at": datetime.now().isoformat()
                    })
                }
            ]
        }

        result = await mcp_client.create_account({"name": "New Account"})

        assert result["id"] == "NEW123"
        assert result["name"] == "New Account"


class TestMCPClientAuthentication:
    """Test OAuth token handling."""

    @pytest.mark.asyncio
    async def test_oauth_token_obtained_on_first_call(self, mcp_client, mock_oauth_server):
        """OAuth token should be obtained on first API call."""
        mock_oauth_server.post.return_value = Mock(
            status_code=200,
            json=Mock(return_value={
                "access_token": "test_access_token",
                "expires_in": 3600
            })
        )

        await mcp_client._ensure_token()

        assert mcp_client.access_token == "test_access_token"

    @pytest.mark.asyncio
    async def test_expired_token_auto_refreshed(self, mcp_client, mock_oauth_server):
        """Expired token should be automatically refreshed."""
        # Set expired token
        mcp_client.access_token = "expired_token"
        mcp_client.token_expires_at = datetime.now()

        mock_oauth_server.post.return_value = Mock(
            status_code=200,
            json=Mock(return_value={
                "access_token": "new_token",
                "expires_in": 3600
            })
        )

        await mcp_client._ensure_token()

        assert mcp_client.access_token == "new_token"

    @pytest.mark.asyncio
    async def test_token_refresh_failure_raises_error(self, mcp_client, mock_oauth_server):
        """Token refresh failure should raise AuthenticationError."""
        from src.integrations.mcp_client import AuthenticationError

        mock_oauth_server.post.return_value = Mock(
            status_code=401,
            json=Mock(return_value={"error": "invalid_grant"})
        )

        with pytest.raises(AuthenticationError):
            await mcp_client._ensure_token()


class TestMCPClientErrorHandling:
    """Test error handling for MCP client."""

    @pytest.mark.asyncio
    async def test_request_timeout_handling(self, mcp_client, mock_mcp_server):
        """Request timeout should be handled correctly."""
        from src.integrations.mcp_client import TimeoutError

        mock_mcp_server.call_tool.side_effect = asyncio.TimeoutError()

        with pytest.raises(TimeoutError):
            await mcp_client.get_account("T001", timeout=1)

    @pytest.mark.asyncio
    async def test_malformed_mcp_response_handled(self, mcp_client, mock_mcp_server):
        """Malformed MCP response should be handled."""
        from src.integrations.mcp_client import InvalidResponseError

        mock_mcp_server.call_tool.return_value = {
            "content": "not a list"  # Invalid format
        }

        with pytest.raises(InvalidResponseError):
            await mcp_client.get_account("BAD001")

    @pytest.mark.asyncio
    async def test_server_error_500_handled(self, mcp_client, mock_mcp_server):
        """Server error 500 should be handled correctly."""
        from src.integrations.mcp_client import ServerError

        mock_mcp_server.call_tool.return_value = {
            "content": [{"type": "error", "error": "Internal server error"}],
            "isError": True,
            "status_code": 500
        }

        with pytest.raises(ServerError):
            await mcp_client.get_account("ERR500")

    @pytest.mark.asyncio
    async def test_rate_limit_error_with_retry(self, mcp_client, mock_mcp_server):
        """Rate limit error should trigger retry."""
        mock_mcp_server.call_tool.side_effect = [
            {"content": [{"type": "error", "error": "Rate limit exceeded"}], "isError": True},
            {
                "content": [
                    {"type": "text", "text": json.dumps({"id": "RL001", "name": "Success"})}
                ]
            }
        ]

        result = await mcp_client.get_account("RL001")

        assert result["id"] == "RL001"
        assert mock_mcp_server.call_tool.call_count == 2


class TestMCPClientHealthCheck:
    """Test health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, mcp_client, mock_mcp_server):
        """Health check should return healthy status."""
        mock_mcp_server.ping.return_value = {"status": "ok"}

        health = await mcp_client.health_check()

        assert health["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_failure(self, mcp_client, mock_mcp_server):
        """Health check failure should return unhealthy status."""
        mock_mcp_server.ping.side_effect = Exception("Connection failed")

        health = await mcp_client.health_check()

        assert health["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_health_check_includes_latency(self, mcp_client, mock_mcp_server):
        """Health check should include latency measurement."""
        mock_mcp_server.ping.return_value = {"status": "ok"}

        health = await mcp_client.health_check()

        assert "latency_ms" in health
        assert health["latency_ms"] >= 0


class TestMCPClientToolManagement:
    """Test MCP tool management."""

    @pytest.mark.asyncio
    async def test_list_available_tools(self, mcp_client, mock_mcp_server):
        """Should list available Zoho CRM tools."""
        mock_mcp_server.list_tools.return_value = {
            "tools": [
                {"name": "get_account", "description": "Get account by ID"},
                {"name": "update_account", "description": "Update account"},
                {"name": "search_accounts", "description": "Search accounts"}
            ]
        }

        tools = await mcp_client.list_tools()

        assert len(tools) == 3
        assert any(t["name"] == "get_account" for t in tools)

    @pytest.mark.asyncio
    async def test_tool_permission_validation(self, mcp_client):
        """Should validate tool permissions before calling."""
        mcp_client.allowed_tools = ["get_account", "search_accounts"]

        # Allowed tool
        assert mcp_client._validate_tool_permission("get_account")

        # Disallowed tool
        with pytest.raises(PermissionError):
            mcp_client._validate_tool_permission("delete_account")


class TestMCPClientMetrics:
    """Test metrics collection."""

    @pytest.mark.asyncio
    async def test_request_metrics_collected(self, mcp_client, mock_mcp_server):
        """Request metrics should be collected."""
        mock_mcp_server.call_tool.return_value = {
            "content": [{"type": "text", "text": json.dumps({"id": "M001"})}]
        }

        await mcp_client.get_account("M001")

        metrics = mcp_client.get_metrics()
        assert metrics["total_requests"] > 0

    @pytest.mark.asyncio
    async def test_response_time_tracking(self, mcp_client, mock_mcp_server):
        """Response times should be tracked."""
        mock_mcp_server.call_tool.return_value = {
            "content": [{"type": "text", "text": json.dumps({"id": "RT001"})}]
        }

        await mcp_client.get_account("RT001")

        metrics = mcp_client.get_metrics()
        assert "avg_response_time" in metrics
