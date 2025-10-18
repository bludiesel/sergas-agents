"""Zoho MCP endpoint client (Tier 1).

Handles agent operations with tool permissions through MCP endpoints.
"""

import asyncio
from typing import Dict, Any, List, Optional
import httpx
import structlog

from src.integrations.zoho.exceptions import (
    ZohoAuthError,
    ZohoAPIError,
    ZohoRateLimitError,
    ZohoConfigError,
)

logger = structlog.get_logger(__name__)


class ZohoMCPClient:
    """Zoho MCP endpoint client for agent operations.

    This client handles Tier 1 integration using MCP endpoints, which provide:
    - Tool permission handling for agent operations
    - Real-time data access
    - Agent context awareness

    Example:
        >>> client = ZohoMCPClient(
        ...     endpoint_url="https://zoho-mcp2.zohomcp.com/endpoint",
        ...     client_id="your_client_id",
        ...     client_secret="your_secret"
        ... )
        >>> account = await client.get_account("123456")
    """

    def __init__(
        self,
        endpoint_url: str,
        client_id: str,
        client_secret: str,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        """Initialize MCP client.

        Args:
            endpoint_url: MCP endpoint base URL
            client_id: OAuth client ID for MCP
            client_secret: OAuth client secret for MCP
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts

        Raises:
            ZohoConfigError: If configuration is invalid
        """
        if not endpoint_url:
            raise ZohoConfigError("MCP endpoint URL is required")
        if not client_id:
            raise ZohoConfigError("MCP client ID is required")
        if not client_secret:
            raise ZohoConfigError("MCP client secret is required")

        self.endpoint_url = endpoint_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self.max_retries = max_retries

        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None

        self.logger = logger.bind(component="ZohoMCPClient")

        # Create async HTTP client
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        )

        self.logger.info(
            "mcp_client_initialized",
            endpoint=endpoint_url,
            timeout=timeout,
        )

    async def _ensure_authenticated(self) -> None:
        """Ensure client has valid access token.

        Raises:
            ZohoAuthError: If authentication fails
        """
        # For now, we'll use client credentials flow
        # In production, this would involve proper OAuth flow
        if self._access_token is None:
            await self._authenticate()

    async def _authenticate(self) -> None:
        """Authenticate with MCP endpoint.

        Raises:
            ZohoAuthError: If authentication fails
        """
        try:
            # MCP authentication endpoint
            auth_url = f"{self.endpoint_url}/oauth/token"

            response = await self._client.post(
                auth_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )

            if response.status_code != 200:
                raise ZohoAuthError(
                    f"MCP authentication failed: {response.text}",
                    status_code=response.status_code,
                )

            data = response.json()
            self._access_token = data.get("access_token")
            self._token_expires_at = asyncio.get_event_loop().time() + data.get("expires_in", 3600)

            self.logger.info("mcp_authenticated")

        except httpx.HTTPError as e:
            self.logger.error("mcp_auth_failed", error=str(e))
            raise ZohoAuthError(
                f"Failed to authenticate with MCP: {str(e)}",
                details={"endpoint": self.endpoint_url}
            )

    async def _make_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        tools: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Make authenticated request to MCP endpoint.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., /accounts/123)
            data: Request body data
            params: Query parameters
            tools: Tool permissions to request

        Returns:
            Response data

        Raises:
            ZohoAPIError: If request fails
            ZohoRateLimitError: If rate limited
        """
        await self._ensure_authenticated()

        url = f"{self.endpoint_url}{path}"

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        # Add tool permissions to headers
        if tools:
            headers["X-MCP-Tools"] = ",".join(tools)

        try:
            response = await self._client.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise ZohoRateLimitError(
                    "MCP rate limit exceeded",
                    retry_after=retry_after,
                )

            # Handle authentication errors
            if response.status_code == 401:
                self._access_token = None
                raise ZohoAuthError("MCP authentication expired", status_code=401)

            # Handle other errors
            if response.status_code >= 400:
                raise ZohoAPIError(
                    f"MCP request failed: {response.text}",
                    status_code=response.status_code,
                )

            return response.json()

        except httpx.HTTPError as e:
            self.logger.error("mcp_request_failed", error=str(e), path=path)
            raise ZohoAPIError(
                f"MCP request failed: {str(e)}",
                details={"path": path, "method": method}
            )

    async def get_account(
        self,
        account_id: str,
        tools: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get account via MCP endpoint.

        Args:
            account_id: Zoho account ID
            tools: Tool permissions for agent operations

        Returns:
            Account data

        Raises:
            ZohoAPIError: If request fails
        """
        self.logger.info("mcp_get_account", account_id=account_id, tools=tools)

        result = await self._make_request(
            method="GET",
            path=f"/accounts/{account_id}",
            tools=tools,
        )

        self.logger.info("mcp_account_retrieved", account_id=account_id)
        return result

    async def get_accounts(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        tools: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get multiple accounts via MCP endpoint.

        Args:
            filters: Query filters
            limit: Maximum number of results
            tools: Tool permissions

        Returns:
            List of account records

        Raises:
            ZohoAPIError: If request fails
        """
        params = filters or {}
        params["limit"] = limit

        result = await self._make_request(
            method="GET",
            path="/accounts",
            params=params,
            tools=tools,
        )

        accounts = result.get("data", [])
        self.logger.info("mcp_accounts_retrieved", count=len(accounts))
        return accounts

    async def update_account(
        self,
        account_id: str,
        data: Dict[str, Any],
        tools: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Update account via MCP endpoint.

        Args:
            account_id: Zoho account ID
            data: Fields to update
            tools: Tool permissions

        Returns:
            Updated account data

        Raises:
            ZohoAPIError: If request fails
        """
        self.logger.info(
            "mcp_update_account",
            account_id=account_id,
            fields=list(data.keys()),
        )

        result = await self._make_request(
            method="PUT",
            path=f"/accounts/{account_id}",
            data=data,
            tools=tools,
        )

        self.logger.info("mcp_account_updated", account_id=account_id)
        return result

    async def search_accounts(
        self,
        criteria: str,
        tools: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Search accounts via MCP endpoint.

        Args:
            criteria: Search criteria (COQL format)
            tools: Tool permissions
            limit: Maximum results

        Returns:
            List of matching accounts

        Raises:
            ZohoAPIError: If request fails
        """
        result = await self._make_request(
            method="POST",
            path="/accounts/search",
            data={"criteria": criteria, "limit": limit},
            tools=tools,
        )

        accounts = result.get("data", [])
        self.logger.info("mcp_search_completed", count=len(accounts), criteria=criteria)
        return accounts

    async def health_check(self) -> bool:
        """Check MCP endpoint health.

        Returns:
            True if endpoint is healthy

        Raises:
            ZohoAPIError: If health check fails
        """
        try:
            await self._make_request("GET", "/health")
            self.logger.info("mcp_health_check_passed")
            return True

        except Exception as e:
            self.logger.error("mcp_health_check_failed", error=str(e))
            return False

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()
        self.logger.info("mcp_client_closed")

    async def __aenter__(self) -> "ZohoMCPClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
