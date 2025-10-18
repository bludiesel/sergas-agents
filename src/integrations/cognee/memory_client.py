"""Cognee memory client - DEPRECATED.

This module is deprecated. Use cognee_client.py instead.
Kept for backwards compatibility.
"""

# Re-export from new location
from src.integrations.cognee.cognee_client import CogneeClient

__all__ = ["CogneeClient"]
