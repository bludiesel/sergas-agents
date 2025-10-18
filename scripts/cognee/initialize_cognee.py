#!/usr/bin/env python3
"""
Initialize Cognee Workspace.

Sets up Cognee workspace and configuration for Sergas Super Account Manager.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.integrations.cognee.cognee_client import CogneeClient
from src.integrations.cognee.cognee_config import CogneeConfig
import structlog

logger = structlog.get_logger(__name__)


async def initialize_cognee() -> None:
    """Initialize Cognee workspace and configuration."""

    print("🔧 Initializing Cognee workspace...")

    try:
        # Load configuration from environment
        config = CogneeConfig(
            base_url="http://localhost:8000",
            workspace="sergas-accounts",
            vector_store_type="lancedb",
            vector_store_path="./cognee_data/vectors",
            graph_db_type="networkx",
            enable_embeddings=True,
            enable_search=True,
            enable_graph=True
        )

        # Create client
        client = CogneeClient(config=config)

        # Initialize connection
        await client.initialize()

        print("✅ Cognee workspace initialized successfully")
        print(f"   - Workspace: {config.workspace}")
        print(f"   - Base URL: {config.base_url}")
        print(f"   - Vector Store: {config.vector_store_type}")
        print(f"   - Graph DB: {config.graph_db_type}")
        print(f"   - Embeddings: {'Enabled' if config.enable_embeddings else 'Disabled'}")
        print(f"   - Search: {'Enabled' if config.enable_search else 'Disabled'}")

        # Close client
        await client.close()

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        logger.error("cognee_initialization_failed", error=str(e))
        sys.exit(1)


async def verify_cognee_connection() -> bool:
    """Verify Cognee is accessible and responding."""

    print("\n🔍 Verifying Cognee connection...")

    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health") as response:
                if response.status == 200:
                    print("✅ Cognee is accessible")
                    return True
                else:
                    print(f"⚠️  Cognee returned status {response.status}")
                    return False

    except Exception as e:
        print(f"❌ Cannot connect to Cognee: {e}")
        return False


async def main():
    """Main initialization routine."""

    print("=" * 60)
    print("Cognee Workspace Initialization")
    print("=" * 60)
    print()

    # Verify connection
    is_connected = await verify_cognee_connection()

    if not is_connected:
        print("\n❌ Cannot connect to Cognee.")
        print("   Make sure Cognee is running:")
        print("   docker-compose -f docker/cognee/docker-compose.yml up -d")
        sys.exit(1)

    # Initialize workspace
    await initialize_cognee()

    print()
    print("=" * 60)
    print("✅ Initialization Complete!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    asyncio.run(main())
