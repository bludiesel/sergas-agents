"""Zoho REST API client (Tier 3 - Emergency Fallback).

Direct REST API calls for emergency fallback when SDK and MCP are unavailable.
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


class ZohoRESTClient:
    """Zoho REST API client for emergency fallback operations.

    This client provides Tier 3 integration using direct REST API calls.
    Used as a last resort when SDK and MCP endpoints are unavailable.

    Features:
    - Direct REST API calls (no SDK dependency)
    - Rate limit handling (Zoho: 5000/day per org)
    - Manual token refresh
    - Comprehensive error handling

    Example:
        >>> client = ZohoRESTClient(
        ...     api_domain="https://www.zohoapis.com",
        ...     access_token="your_access_token",
        ...     refresh_token="your_refresh_token"
        ... )
        >>> account = await client.get_account("123456")
    """

    def __init__(
        self,
        api_domain: str,
        access_token: str,
        refresh_token: str,
        client_id: str,
        client_secret: str,
        timeout: int = 45,
        max_retries: int = 2,
    ) -> None:
        """Initialize REST API client.

        Args:
            api_domain: Zoho API domain (e.g., https://www.zohoapis.com)
            access_token: OAuth access token
            refresh_token: OAuth refresh token for token renewal
            client_id: OAuth client ID
            client_secret: OAuth client secret
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts

        Raises:
            ZohoConfigError: If configuration is invalid
        """
        if not api_domain:
            raise ZohoConfigError("API domain is required")
        if not access_token:
            raise ZohoConfigError("Access token is required")

        self.api_domain = api_domain.rstrip("/")
        self._access_token = access_token
        self._refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self.max_retries = max_retries

        self.logger = logger.bind(component="ZohoRESTClient")

        # Create async HTTP client
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        )

        self.logger.info(
            "rest_client_initialized",
            api_domain=api_domain,
            timeout=timeout,
        )

    async def _refresh_access_token(self) -> None:
        """Refresh OAuth access token.

        Raises:
            ZohoAuthError: If token refresh fails
        """
        try:
            # Use accounts server for token refresh
            token_url = "https://accounts.zoho.com/oauth/v2/token"

            response = await self._client.post(
                token_url,
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self._refresh_token,
                },
            )

            if response.status_code != 200:
                raise ZohoAuthError(
                    f"Token refresh failed: {response.text}",
                    status_code=response.status_code,
                )

            data = response.json()
            self._access_token = data.get("access_token")

            self.logger.info("rest_token_refreshed")

        except httpx.HTTPError as e:
            self.logger.error("rest_token_refresh_failed", error=str(e))
            raise ZohoAuthError(
                f"Failed to refresh access token: {str(e)}",
                details={"api_domain": self.api_domain}
            )

    async def _make_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make authenticated request to Zoho REST API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., /crm/v8/Accounts/123)
            data: Request body data
            params: Query parameters

        Returns:
            Response data

        Raises:
            ZohoAPIError: If request fails
            ZohoRateLimitError: If rate limited
        """
        url = f"{self.api_domain}{path}"

        headers = {
            "Authorization": f"Zoho-oauthtoken {self._access_token}",
            "Content-Type": "application/json",
        }

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
                self.logger.warning("rest_rate_limited", retry_after=retry_after)
                raise ZohoRateLimitError(
                    "REST API rate limit exceeded",
                    retry_after=retry_after,
                )

            # Handle authentication errors (try refresh)
            if response.status_code == 401:
                self.logger.info("rest_auth_expired_refreshing")
                await self._refresh_access_token()

                # Retry request with new token
                headers["Authorization"] = f"Zoho-oauthtoken {self._access_token}"
                response = await self._client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers,
                )

            # Handle other errors
            if response.status_code >= 400:
                raise ZohoAPIError(
                    f"REST API request failed: {response.text}",
                    status_code=response.status_code,
                )

            return response.json()

        except httpx.HTTPError as e:
            self.logger.error("rest_request_failed", error=str(e), path=path)
            raise ZohoAPIError(
                f"REST API request failed: {str(e)}",
                details={"path": path, "method": method}
            )

    async def get_account(self, account_id: str) -> Dict[str, Any]:
        """Get account via REST API.

        Args:
            account_id: Zoho account ID

        Returns:
            Account data

        Raises:
            ZohoAPIError: If request fails
        """
        self.logger.info("rest_get_account", account_id=account_id)

        result = await self._make_request(
            method="GET",
            path=f"/crm/v8/Accounts/{account_id}",
        )

        # Extract account data from response
        account = result.get("data", [{}])[0]
        self.logger.info("rest_account_retrieved", account_id=account_id)
        return account

    async def get_accounts(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get multiple accounts via REST API.

        Args:
            filters: Query filters
            limit: Maximum number of results (max 200)

        Returns:
            List of account records

        Raises:
            ZohoAPIError: If request fails
        """
        params = filters or {}
        params["per_page"] = min(limit, 200)

        result = await self._make_request(
            method="GET",
            path="/crm/v8/Accounts",
            params=params,
        )

        accounts = result.get("data", [])
        self.logger.info("rest_accounts_retrieved", count=len(accounts))
        return accounts

    async def update_account(
        self,
        account_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update account via REST API.

        Args:
            account_id: Zoho account ID
            data: Fields to update

        Returns:
            Updated account data

        Raises:
            ZohoAPIError: If request fails
        """
        self.logger.info(
            "rest_update_account",
            account_id=account_id,
            fields=list(data.keys()),
        )

        # Zoho expects data in specific format
        payload = {
            "data": [data]
        }

        result = await self._make_request(
            method="PUT",
            path=f"/crm/v8/Accounts/{account_id}",
            data=payload,
        )

        account = result.get("data", [{}])[0]
        self.logger.info("rest_account_updated", account_id=account_id)
        return account

    async def search_accounts(
        self,
        criteria: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Search accounts using COQL criteria via REST API.

        Args:
            criteria: COQL search criteria
            limit: Maximum results (max 200)

        Returns:
            List of matching accounts

        Raises:
            ZohoAPIError: If request fails
        """
        # Use COQL API for search
        payload = {
            "select_query": f"select * from Accounts where {criteria} limit {min(limit, 200)}"
        }

        result = await self._make_request(
            method="POST",
            path="/crm/v8/coql",
            data=payload,
        )

        accounts = result.get("data", [])
        self.logger.info("rest_search_completed", count=len(accounts), criteria=criteria)
        return accounts

    async def bulk_read_accounts(
        self,
        account_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """Bulk read accounts via REST API.

        Args:
            account_ids: List of account IDs

        Returns:
            List of account records

        Raises:
            ZohoAPIError: If request fails
        """
        # Use comma-separated IDs parameter
        params = {
            "ids": ",".join(account_ids)
        }

        result = await self._make_request(
            method="GET",
            path="/crm/v8/Accounts",
            params=params,
        )

        accounts = result.get("data", [])
        self.logger.info("rest_bulk_read_completed", count=len(accounts))
        return accounts

    async def bulk_update_accounts(
        self,
        updates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Bulk update accounts via REST API.

        Args:
            updates: List of account updates (must include 'id' field)

        Returns:
            Bulk operation result

        Raises:
            ZohoAPIError: If request fails
        """
        # Zoho allows up to 100 records per bulk update
        batch_size = 100
        results = []

        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]

            payload = {"data": batch}

            result = await self._make_request(
                method="PUT",
                path="/crm/v8/Accounts",
                data=payload,
            )

            results.extend(result.get("data", []))

        self.logger.info("rest_bulk_update_completed", total=len(updates))
        return {
            "total": len(updates),
            "results": results,
        }

    async def health_check(self) -> bool:
        """Check REST API health.

        Returns:
            True if API is healthy

        Raises:
            ZohoAPIError: If health check fails
        """
        try:
            # Try to get user info as health check
            await self._make_request("GET", "/crm/v8/users?type=CurrentUser")
            self.logger.info("rest_health_check_passed")
            return True

        except Exception as e:
            self.logger.error("rest_health_check_failed", error=str(e))
            return False

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()
        self.logger.info("rest_client_closed")

    async def __aenter__(self) -> "ZohoRESTClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
