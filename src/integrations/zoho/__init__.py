"""Zoho CRM integration package.

This package provides three-tier Zoho CRM integration:
- Tier 1: MCP tools (primary, for real-time operations)
- Tier 2: Python SDK (secondary, for bulk operations)
- Tier 3: REST API (fallback, for unsupported operations)
"""

from src.integrations.zoho.exceptions import (
    ZohoAuthError,
    ZohoAPIError,
    ZohoTokenError,
    ZohoRateLimitError,
)
from src.integrations.zoho.sdk_client import ZohoSDKClient
from src.integrations.zoho.token_store import TokenStore

# TODO: Uncomment when implemented
# from .integration_manager import ZohoIntegrationManager

__all__ = [
    "ZohoSDKClient",
    "TokenStore",
    "ZohoAuthError",
    "ZohoAPIError",
    "ZohoTokenError",
    "ZohoRateLimitError",
    # "ZohoIntegrationManager",
]
