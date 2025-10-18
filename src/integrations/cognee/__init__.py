"""
Cognee Integration Package.

Provides persistent memory and knowledge graph functionality for
the Sergas Super Account Manager.

Main Components:
- CogneeClient: Core client for Cognee knowledge graph operations
- CogneeConfig: Configuration and settings management
- AccountIngestionPipeline: Bulk account ingestion from Zoho CRM
- CogneeMCPTools: MCP tools for agent access

Quick Start:
    from src.integrations.cognee import CogneeClient, CogneeConfig

    config = CogneeConfig(
        base_url="http://localhost:8000",
        workspace="sergas-accounts"
    )

    client = CogneeClient(config=config)
    await client.initialize()

    # Add account
    await client.add_account(account_data)

    # Search accounts
    results = await client.search_accounts("at-risk accounts")
"""

from src.integrations.cognee.cognee_client import CogneeClient
from src.integrations.cognee.cognee_config import (
    CogneeConfig,
    CogneeHealthConfig,
    CogneeIngestionConfig,
    load_config_from_env
)
from src.integrations.cognee.account_ingestion import (
    AccountIngestionPipeline,
    AccountSyncScheduler
)
from src.integrations.cognee.cognee_mcp_tools import (
    CogneeMCPTools,
    create_mcp_tool_definitions
)

__all__ = [
    # Core client
    "CogneeClient",

    # Configuration
    "CogneeConfig",
    "CogneeHealthConfig",
    "CogneeIngestionConfig",
    "load_config_from_env",

    # Ingestion pipeline
    "AccountIngestionPipeline",
    "AccountSyncScheduler",

    # MCP tools
    "CogneeMCPTools",
    "create_mcp_tool_definitions",
]

__version__ = "1.0.0"
