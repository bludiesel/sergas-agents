#!/usr/bin/env python3
"""
Ingest Pilot Accounts to Cognee.

Ingests 50 pilot accounts from Zoho CRM into Cognee knowledge graph.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.integrations.cognee.cognee_client import CogneeClient
from src.integrations.cognee.cognee_config import CogneeConfig
from src.integrations.cognee.account_ingestion import AccountIngestionPipeline
import structlog

logger = structlog.get_logger(__name__)


# Mock Zoho integration for testing (replace with actual integration)
class MockZohoIntegration:
    """Mock Zoho integration for testing."""

    async def get_accounts_bulk(self, account_ids):
        """Mock fetching accounts from Zoho."""
        # Return mock account data
        accounts = []
        for account_id in account_ids:
            accounts.append({
                "id": account_id,
                "Account_Name": f"Account {account_id}",
                "Industry": "Technology",
                "Billing_Country": "United States",
                "Annual_Revenue": 1000000,
                "Description": f"Mock account {account_id} for testing",
                "Account_Type": "Customer",
                "Rating": "Hot",
                "Website": f"https://account{account_id}.com",
                "Phone": "+1-555-0100",
                "Owner": {
                    "id": "owner1",
                    "name": "John Doe",
                    "email": "john.doe@sergas.com"
                },
                "Created_Time": "2025-01-01T00:00:00Z",
                "Modified_Time": datetime.utcnow().isoformat() + "Z",
                "Last_Activity_Time": datetime.utcnow().isoformat() + "Z",
                "Number_of_Employees": 100
            })
        return accounts


async def load_pilot_account_ids() -> list:
    """
    Load pilot account IDs.

    In production, this would load from:
    - Configuration file
    - Database query
    - Zoho CRM query for specific criteria

    For now, we'll generate 50 test account IDs.
    """
    # Generate 50 pilot account IDs
    pilot_ids = [f"ACC{str(i).zfill(6)}" for i in range(1, 51)]

    print(f"📋 Loaded {len(pilot_ids)} pilot account IDs")
    return pilot_ids


async def ingest_pilot_accounts():
    """Main ingestion routine."""

    print("=" * 60)
    print("Pilot Account Ingestion to Cognee")
    print("=" * 60)
    print()

    start_time = datetime.utcnow()

    try:
        # Load configuration
        config = CogneeConfig(
            base_url="http://localhost:8000",
            workspace="sergas-accounts",
            batch_size=10,
            max_concurrent_requests=5
        )

        # Create Cognee client
        print("🔧 Initializing Cognee client...")
        cognee_client = CogneeClient(config=config)
        await cognee_client.initialize()
        print("✅ Cognee client initialized")

        # Create mock Zoho integration (replace with actual)
        print("\n🔧 Initializing Zoho integration...")
        zoho_integration = MockZohoIntegration()
        print("✅ Zoho integration initialized (mock)")

        # Create ingestion pipeline
        print("\n🔧 Creating ingestion pipeline...")
        pipeline = AccountIngestionPipeline(
            zoho_integration_manager=zoho_integration,
            cognee_client=cognee_client
        )
        print("✅ Pipeline created")

        # Load pilot account IDs
        print("\n📋 Loading pilot account IDs...")
        pilot_account_ids = await load_pilot_account_ids()

        # Run ingestion
        print(f"\n🚀 Starting ingestion of {len(pilot_account_ids)} accounts...")
        print("-" * 60)

        result = await pipeline.ingest_pilot_accounts(
            account_ids=pilot_account_ids,
            batch_size=10
        )

        # Display results
        print("\n" + "=" * 60)
        print("Ingestion Results")
        print("=" * 60)

        summary = result.get("summary", {})
        timing = result.get("timing", {})

        print(f"\n📊 Summary:")
        print(f"   Total Processed:    {summary.get('total_processed', 0)}")
        print(f"   Successful:         {summary.get('success_count', 0)}")
        print(f"   Failed:             {summary.get('failure_count', 0)}")
        print(f"   Duplicates:         {summary.get('duplicate_count', 0)}")
        print(f"   Validation Errors:  {summary.get('validation_errors', 0)}")
        print(f"   Success Rate:       {summary.get('success_rate', 0)}%")

        print(f"\n⏱️  Timing:")
        print(f"   Duration:           {timing.get('duration_seconds', 0):.2f}s")
        print(f"   Throughput:         {timing.get('throughput_per_second', 0):.2f} accounts/sec")

        # Show errors if any
        errors = result.get("errors", [])
        if errors:
            print(f"\n❌ Errors ({len(errors)}):")
            for error in errors[:5]:  # Show first 5 errors
                print(f"   - Account {error.get('account_id')}: {error.get('error')}")
            if len(errors) > 5:
                print(f"   ... and {len(errors) - 5} more errors")

        # Save detailed report
        report_path = project_root / "docs" / "cognee_ingestion_report.json"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, "w") as f:
            json.dump(result, f, indent=2)

        print(f"\n📝 Detailed report saved to: {report_path}")

        # Close client
        await cognee_client.close()

        # Final summary
        end_time = datetime.utcnow()
        total_duration = (end_time - start_time).total_seconds()

        print("\n" + "=" * 60)
        if summary.get('failure_count', 0) == 0:
            print("✅ Ingestion Completed Successfully!")
        else:
            print("⚠️  Ingestion Completed with Errors")
        print("=" * 60)
        print(f"\n⏱️  Total Duration: {total_duration:.2f}s")
        print()

        return result

    except Exception as e:
        print(f"\n❌ Ingestion failed: {e}")
        logger.error("pilot_ingestion_failed", error=str(e))
        sys.exit(1)


async def verify_ingested_accounts():
    """Verify accounts were successfully ingested."""

    print("\n🔍 Verifying ingested accounts...")

    try:
        config = CogneeConfig(
            base_url="http://localhost:8000",
            workspace="sergas-accounts"
        )

        client = CogneeClient(config=config)
        await client.initialize()

        # Search for accounts
        results = await client.search_accounts(
            query="all accounts",
            limit=5
        )

        print(f"✅ Found {len(results)} accounts in Cognee")

        if results:
            print("\n📋 Sample accounts:")
            for i, account in enumerate(results[:3], 1):
                print(f"   {i}. {account.get('account_name')} ({account.get('account_id')})")

        await client.close()

    except Exception as e:
        print(f"⚠️  Verification failed: {e}")


async def main():
    """Main entry point."""

    # Run ingestion
    result = await ingest_pilot_accounts()

    # Verify if successful
    if result.get("summary", {}).get("success_count", 0) > 0:
        await verify_ingested_accounts()


if __name__ == "__main__":
    asyncio.run(main())
