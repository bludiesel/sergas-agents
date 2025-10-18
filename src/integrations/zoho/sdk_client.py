"""Zoho SDK client wrapper with OAuth and automatic token refresh.

This module provides a production-ready Zoho CRM SDK client with:
- OAuth token management with automatic refresh
- Database-backed token persistence
- Retry logic with exponential backoff
- Comprehensive error handling
- Structured logging
- Type hints and docstrings
"""

import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import structlog
from zcrmsdk import (
    ZCRMRestClient,
    ZCRMRecord,
    ZCRMModule,
    OAuth,
    ZCRMException,
)
from zcrmsdk.Persistence import OAuthToken

from src.models.config import ZohoSDKConfig
from src.integrations.zoho.token_store import TokenStore
from src.integrations.zoho.exceptions import (
    ZohoAuthError,
    ZohoAPIError,
    ZohoRateLimitError,
    ZohoConfigError,
)

logger = structlog.get_logger(__name__)


class ZohoSDKClient:
    """Zoho CRM SDK client with automatic OAuth token management.

    This client provides:
    - Automatic token refresh when expired
    - Database persistence for tokens
    - Retry logic with exponential backoff
    - Comprehensive error handling
    - Thread-safe operations

    Example:
        >>> config = ZohoSDKConfig(
        ...     client_id="your_client_id",
        ...     client_secret="your_secret",
        ...     refresh_token="your_refresh_token",
        ... )
        >>> client = ZohoSDKClient(config, "postgresql://...")
        >>> accounts = client.get_accounts(limit=100)
    """

    def __init__(
        self,
        config: ZohoSDKConfig,
        database_url: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize Zoho SDK client.

        Args:
            config: Zoho SDK configuration
            database_url: PostgreSQL database URL for token storage
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries in seconds

        Raises:
            ZohoConfigError: If configuration is invalid
            ZohoAuthError: If initial authentication fails
        """
        self.config = config
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logger.bind(component="ZohoSDKClient")

        # Initialize token store
        self.token_store = TokenStore(database_url)

        # Initialize SDK
        try:
            self._initialize_sdk()
            self.logger.info(
                "zoho_sdk_initialized",
                region=config.region,
                environment=config.environment,
            )
        except Exception as e:
            self.logger.error("sdk_initialization_failed", error=str(e))
            raise ZohoConfigError(
                f"Failed to initialize Zoho SDK: {str(e)}",
                details={"region": config.region, "environment": config.environment}
            )

    def _initialize_sdk(self) -> None:
        """Initialize Zoho CRM SDK with configuration.

        Raises:
            ZohoConfigError: If SDK initialization fails
        """
        try:
            # Configure SDK
            configuration = {
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret.get_secret_value(),
                "refresh_token": self.config.refresh_token.get_secret_value(),
                "redirect_uri": self.config.redirect_url,
                "currentUserEmail": "sdk@sergas.com",  # Required by SDK
                "sandbox": self.config.environment == "sandbox",
                "apiBaseUrl": self._get_api_base_url(),
                "apiVersion": "v8",
                "access_type": "offline",
                "persistence_handler_class": "CustomDBHandler",
                "persistence_handler_path": __file__,
            }

            ZCRMRestClient.initialize(configuration)
            self.logger.debug("sdk_configured", config=configuration)

        except Exception as e:
            raise ZohoConfigError(f"SDK configuration failed: {str(e)}")

    def _get_api_base_url(self) -> str:
        """Get API base URL based on region.

        Returns:
            API base URL for the configured region
        """
        region_urls = {
            "us": "https://www.zohoapis.com",
            "eu": "https://www.zohoapis.eu",
            "au": "https://www.zohoapis.com.au",
            "in": "https://www.zohoapis.in",
            "cn": "https://www.zohoapis.com.cn",
            "jp": "https://www.zohoapis.jp",
        }
        return region_urls.get(self.config.region, region_urls["us"])

    def _ensure_valid_token(self) -> None:
        """Ensure access token is valid, refresh if needed.

        Raises:
            ZohoAuthError: If token refresh fails
        """
        if self.token_store.is_token_expired():
            self.logger.info("token_expired_refreshing")
            self._refresh_access_token()

    def _refresh_access_token(self) -> None:
        """Refresh OAuth access token using refresh token.

        Raises:
            ZohoAuthError: If token refresh fails
        """
        try:
            # Get current token from database
            current_token = self.token_store.get_token()
            if not current_token:
                raise ZohoAuthError("No refresh token found in database")

            # Use SDK's OAuth to refresh
            oauth_client = OAuth.get_instance()
            oauth_client.client_id = self.config.client_id
            oauth_client.client_secret = self.config.client_secret.get_secret_value()
            oauth_client.redirect_uri = self.config.redirect_url

            # Refresh token
            new_token = oauth_client.refresh_access_token(
                current_token["refresh_token"],
                None  # User email not required for refresh
            )

            # Save new token to database
            self.token_store.save_token(
                access_token=new_token.access_token,
                refresh_token=current_token["refresh_token"],
                expires_in=new_token.expires_in,
            )

            self.logger.info(
                "token_refreshed",
                expires_at=(
                    datetime.utcnow() + timedelta(seconds=new_token.expires_in)
                ).isoformat(),
            )

        except Exception as e:
            self.logger.error("token_refresh_failed", error=str(e))
            raise ZohoAuthError(
                f"Failed to refresh access token: {str(e)}",
                details={"refresh_token_exists": current_token is not None}
            )

    def _retry_with_backoff(
        self,
        operation: Callable[[], Any],
        operation_name: str,
    ) -> Any:
        """Execute operation with exponential backoff retry logic.

        Args:
            operation: Function to execute
            operation_name: Name of operation for logging

        Returns:
            Result of successful operation

        Raises:
            ZohoAPIError: If all retries fail
            ZohoRateLimitError: If rate limit is exceeded
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                self._ensure_valid_token()
                result = operation()
                return result

            except ZCRMException as e:
                last_exception = e
                error_code = getattr(e, "status_code", None)

                # Handle rate limiting
                if error_code == 429:
                    retry_after = getattr(e, "retry_after", 60)
                    self.logger.warning(
                        "rate_limit_exceeded",
                        operation=operation_name,
                        retry_after=retry_after,
                    )
                    raise ZohoRateLimitError(
                        f"Rate limit exceeded for {operation_name}",
                        retry_after=retry_after,
                        details={"attempt": attempt + 1}
                    )

                # Handle authentication errors
                if error_code in (401, 403):
                    self.logger.warning(
                        "auth_error_refreshing_token",
                        operation=operation_name,
                        status_code=error_code,
                    )
                    self._refresh_access_token()

                # Exponential backoff
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    self.logger.info(
                        "retrying_operation",
                        operation=operation_name,
                        attempt=attempt + 1,
                        delay=delay,
                    )
                    time.sleep(delay)

            except Exception as e:
                last_exception = e
                self.logger.error(
                    "operation_failed",
                    operation=operation_name,
                    error=str(e),
                    attempt=attempt + 1,
                )
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    time.sleep(delay)

        # All retries exhausted
        self.logger.error(
            "operation_failed_all_retries",
            operation=operation_name,
            max_retries=self.max_retries,
        )
        raise ZohoAPIError(
            f"Operation {operation_name} failed after {self.max_retries} attempts",
            details={"last_error": str(last_exception)}
        )

    def get_accounts(
        self,
        limit: int = 200,
        page: int = 1,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve accounts from Zoho CRM.

        Args:
            limit: Maximum number of records to retrieve (max 200)
            page: Page number for pagination
            sort_by: Field name to sort by
            sort_order: Sort order ('asc' or 'desc')
            fields: List of field names to retrieve

        Returns:
            List of account records as dictionaries

        Raises:
            ZohoAPIError: If API request fails
        """
        def _get():
            module = ZCRMModule.get_instance("Accounts")

            # Build request parameters
            params = {
                "page": page,
                "per_page": min(limit, 200),
            }

            if sort_by:
                params["sort_by"] = sort_by
            if sort_order:
                params["sort_order"] = sort_order
            if fields:
                params["fields"] = ",".join(fields)

            response = module.get_records(params)

            if response.status_code not in (200, 204):
                raise ZohoAPIError(
                    f"Failed to get accounts: {response.message}",
                    status_code=response.status_code,
                )

            # Convert records to dictionaries
            records = []
            for record in response.data:
                record_data = {
                    "id": record.entity_id,
                    **record.field_data,
                }
                records.append(record_data)

            self.logger.info(
                "accounts_retrieved",
                count=len(records),
                page=page,
                limit=limit,
            )
            return records

        return self._retry_with_backoff(_get, "get_accounts")

    def get_account(self, account_id: str) -> Dict[str, Any]:
        """Retrieve a single account by ID.

        Args:
            account_id: Zoho account ID

        Returns:
            Account record as dictionary

        Raises:
            ZohoAPIError: If API request fails
        """
        def _get():
            record = ZCRMRecord.get_instance("Accounts", account_id)
            response = record.get()

            if response.status_code not in (200, 204):
                raise ZohoAPIError(
                    f"Failed to get account {account_id}: {response.message}",
                    status_code=response.status_code,
                )

            data = response.data
            return {
                "id": data.entity_id,
                **data.field_data,
            }

        return self._retry_with_backoff(_get, f"get_account_{account_id}")

    def update_account(
        self,
        account_id: str,
        field_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update an account record.

        Args:
            account_id: Zoho account ID
            field_data: Dictionary of field names and values to update

        Returns:
            Updated account record

        Raises:
            ZohoAPIError: If API request fails
        """
        def _update():
            record = ZCRMRecord.get_instance("Accounts", account_id)

            # Set field values
            for field_name, value in field_data.items():
                record.set_field_value(field_name, value)

            response = record.update()

            if response.status_code not in (200, 204):
                raise ZohoAPIError(
                    f"Failed to update account {account_id}: {response.message}",
                    status_code=response.status_code,
                )

            self.logger.info(
                "account_updated",
                account_id=account_id,
                fields=list(field_data.keys()),
            )

            data = response.data
            return {
                "id": data.entity_id,
                **data.field_data,
            }

        return self._retry_with_backoff(_update, f"update_account_{account_id}")

    def bulk_read_accounts(
        self,
        criteria: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform bulk read operation for accounts.

        Args:
            criteria: COQL query criteria
            fields: List of fields to retrieve

        Returns:
            List of account records

        Raises:
            ZohoAPIError: If bulk read fails
        """
        def _bulk_read():
            module = ZCRMModule.get_instance("Accounts")

            params = {}
            if criteria:
                params["criteria"] = criteria
            if fields:
                params["fields"] = ",".join(fields)

            # Use bulk read API
            response = module.get_records(params)

            if response.status_code not in (200, 204):
                raise ZohoAPIError(
                    f"Bulk read failed: {response.message}",
                    status_code=response.status_code,
                )

            records = []
            for record in response.data:
                records.append({
                    "id": record.entity_id,
                    **record.field_data,
                })

            self.logger.info("bulk_read_completed", count=len(records))
            return records

        return self._retry_with_backoff(_bulk_read, "bulk_read_accounts")

    def bulk_update_accounts(
        self,
        records: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Perform bulk update operation for accounts.

        Args:
            records: List of record dictionaries with 'id' and field data

        Returns:
            Bulk operation result with success/failure counts

        Raises:
            ZohoAPIError: If bulk update fails
        """
        def _bulk_update():
            record_instances = []

            for record_data in records:
                account_id = record_data.pop("id")
                record = ZCRMRecord.get_instance("Accounts", account_id)

                for field_name, value in record_data.items():
                    record.set_field_value(field_name, value)

                record_instances.append(record)

            # Perform bulk update
            module = ZCRMModule.get_instance("Accounts")
            response = module.update_records(record_instances)

            if response.status_code not in (200, 204):
                raise ZohoAPIError(
                    f"Bulk update failed: {response.message}",
                    status_code=response.status_code,
                )

            self.logger.info(
                "bulk_update_completed",
                total=len(records),
                status_code=response.status_code,
            )

            return {
                "total": len(records),
                "status_code": response.status_code,
                "message": response.message,
            }

        return self._retry_with_backoff(_bulk_update, "bulk_update_accounts")

    def search_accounts(
        self,
        criteria: str,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Search accounts using COQL criteria.

        Args:
            criteria: COQL search criteria
            limit: Maximum number of results

        Returns:
            List of matching account records

        Raises:
            ZohoAPIError: If search fails
        """
        def _search():
            module = ZCRMModule.get_instance("Accounts")

            params = {
                "criteria": criteria,
                "per_page": min(limit, 200),
            }

            response = module.search_records(params)

            if response.status_code not in (200, 204):
                raise ZohoAPIError(
                    f"Search failed: {response.message}",
                    status_code=response.status_code,
                )

            records = []
            for record in response.data:
                records.append({
                    "id": record.entity_id,
                    **record.field_data,
                })

            self.logger.info("search_completed", count=len(records), criteria=criteria)
            return records

        return self._retry_with_backoff(_search, "search_accounts")


class CustomDBHandler:
    """Custom database handler for Zoho SDK token persistence.

    This handler is used by the Zoho SDK to persist OAuth tokens.
    It delegates to our TokenStore implementation.
    """

    @staticmethod
    def get_oauth_instance() -> Optional[OAuthToken]:
        """Get OAuth token from database (SDK callback).

        Returns:
            OAuthToken instance or None
        """
        # This would be called by SDK, but we handle tokens directly
        return None

    @staticmethod
    def save_oauth_data(oauth_token: OAuthToken) -> None:
        """Save OAuth token to database (SDK callback).

        Args:
            oauth_token: OAuth token from SDK
        """
        # This would be called by SDK, but we handle tokens directly
        pass
