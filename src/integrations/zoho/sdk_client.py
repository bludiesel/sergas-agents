"""Zoho SDK client wrapper - TEMPORARY STUB for demonstration.

This is a temporary mock to allow the server to start.
Replace with actual Zoho SDK integration when ready.
"""

import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)


class ZohoSDKClient:
    """Temporary mock Zoho SDK client for demonstration."""

    def __init__(
        self,
        config: Any,
        database_url: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize mock SDK client."""
        self.config = config
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logger.bind(component="ZohoSDKClient (MOCK)")
        self.logger.warning("using_mock_zoho_sdk_client")

    def get_accounts(
        self,
        limit: int = 200,
        page: int = 1,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Return mock account data."""
        return [
            {
                "id": "ACC-MOCK-001",
                "Account_Name": "Demo Account 1",
                "Account_Type": "Customer",
                "Owner": {"name": "Demo User"},
                "Last_Activity_Time": datetime.now().isoformat(),
            },
            {
                "id": "ACC-MOCK-002",
                "Account_Name": "Demo Account 2",
                "Account_Type": "Prospect",
                "Owner": {"name": "Demo User"},
                "Last_Activity_Time": datetime.now().isoformat(),
            },
        ]

    def get_account(self, account_id: str) -> Dict[str, Any]:
        """Return mock single account."""
        return {
            "id": account_id,
            "Account_Name": f"Demo Account {account_id}",
            "Account_Type": "Customer",
            "Owner": {"name": "Demo User"},
            "Last_Activity_Time": datetime.now().isoformat(),
        }

    def update_account(
        self,
        account_id: str,
        field_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Mock account update."""
        self.logger.info("mock_account_update", account_id=account_id, fields=field_data)
        return self.get_account(account_id)

    def bulk_read_accounts(
        self,
        criteria: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Return mock bulk read."""
        return self.get_accounts(limit=100)

    def bulk_update_accounts(
        self,
        records: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Mock bulk update."""
        return {
            "total": len(records),
            "status_code": 200,
            "message": "Mock bulk update successful",
        }

    def search_accounts(
        self,
        criteria: str,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Mock search."""
        return self.get_accounts(limit=limit)
