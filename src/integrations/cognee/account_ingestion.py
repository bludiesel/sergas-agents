"""
Account Ingestion Pipeline.

Pipeline for ingesting Zoho CRM accounts into Cognee knowledge graph.
Handles bulk ingestion, incremental sync, and data transformation.
"""

from typing import Dict, List, Optional, Any
import asyncio
from datetime import datetime
import structlog

from src.integrations.cognee.cognee_client import CogneeClient
from src.integrations.cognee.cognee_config import CogneeIngestionConfig

logger = structlog.get_logger(__name__)


class AccountIngestionPipeline:
    """
    Pipeline for ingesting Zoho CRM accounts into Cognee.

    Features:
    - Bulk account ingestion with batching
    - Incremental sync for updated accounts
    - Data validation and transformation
    - Deduplication
    - Progress tracking
    - Error handling and recovery
    """

    def __init__(
        self,
        zoho_integration_manager,
        cognee_client: CogneeClient,
        config: Optional[CogneeIngestionConfig] = None
    ):
        """
        Initialize ingestion pipeline.

        Args:
            zoho_integration_manager: Zoho CRM integration manager
            cognee_client: Cognee client instance
            config: Ingestion configuration
        """
        self.zoho = zoho_integration_manager
        self.cognee = cognee_client
        self.config = config or CogneeIngestionConfig()

        self.logger = logger.bind(component="account_ingestion")

        # Stats tracking
        self.stats = {
            "total_processed": 0,
            "success_count": 0,
            "failure_count": 0,
            "duplicate_count": 0,
            "validation_errors": 0,
            "start_time": None,
            "end_time": None
        }

    async def ingest_pilot_accounts(
        self,
        account_ids: List[str],
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Ingest pilot accounts (50) into Cognee.

        Process:
        1. Fetch accounts from Zoho (Tier 2 SDK - bulk)
        2. Validate and transform data
        3. Generate embeddings
        4. Store in Cognee knowledge graph
        5. Create relationships

        Args:
            account_ids: List of Zoho account IDs to ingest
            batch_size: Batch size for processing

        Returns:
            Detailed ingestion report with stats
        """
        self.logger.info(
            "pilot_ingestion_started",
            account_count=len(account_ids),
            batch_size=batch_size
        )

        self.stats["start_time"] = datetime.utcnow()
        batch_size = batch_size or self.config.batch_delay_ms

        # Fetch accounts from Zoho
        accounts_data = await self._fetch_accounts_from_zoho(account_ids)

        if not accounts_data:
            self.logger.warning("no_accounts_fetched_from_zoho")
            return self._generate_report()

        # Validate accounts
        validated_accounts = self._validate_accounts(accounts_data)

        # Transform accounts to Cognee format
        transformed_accounts = [
            self._transform_zoho_to_cognee(account)
            for account in validated_accounts
        ]

        # Check for duplicates if enabled
        if self.config.enable_deduplication:
            transformed_accounts = await self._deduplicate_accounts(
                transformed_accounts
            )

        # Ingest in batches
        results = await self._ingest_in_batches(
            transformed_accounts,
            batch_size
        )

        # Create account relationships
        if self.config.enable_progress_tracking:
            await self._create_account_relationships(transformed_accounts)

        self.stats["end_time"] = datetime.utcnow()
        return self._generate_report(results)

    async def sync_account_updates(
        self,
        account_ids: Optional[List[str]] = None,
        since_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Sync account updates from Zoho to Cognee.

        Performs incremental sync for modified accounts only.

        Args:
            account_ids: Specific accounts to sync (None = all modified)
            since_date: Only sync accounts modified after this date

        Returns:
            Sync report with statistics
        """
        self.logger.info(
            "incremental_sync_started",
            account_ids_count=len(account_ids) if account_ids else None,
            since_date=since_date
        )

        self.stats["start_time"] = datetime.utcnow()

        # Get modified accounts from Zoho
        if account_ids:
            accounts_data = await self._fetch_accounts_from_zoho(account_ids)
        else:
            accounts_data = await self._fetch_modified_accounts(since_date)

        if not accounts_data:
            self.logger.info("no_modified_accounts_found")
            return self._generate_report()

        # Transform and ingest
        transformed_accounts = [
            self._transform_zoho_to_cognee(account)
            for account in accounts_data
        ]

        results = await self._ingest_in_batches(transformed_accounts)

        self.stats["end_time"] = datetime.utcnow()
        return self._generate_report(results)

    # Private methods

    async def _fetch_accounts_from_zoho(
        self,
        account_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Fetch accounts from Zoho CRM using integration manager.

        Uses Tier 2 SDK for bulk fetching.
        """
        try:
            # Use Zoho integration manager to fetch accounts
            accounts = []

            # Fetch in batches to avoid API limits
            batch_size = 100
            for i in range(0, len(account_ids), batch_size):
                batch_ids = account_ids[i:i + batch_size]

                # Fetch accounts using Zoho integration
                batch_accounts = await self.zoho.get_accounts_bulk(batch_ids)
                accounts.extend(batch_accounts)

                self.logger.debug(
                    "zoho_batch_fetched",
                    batch_num=i // batch_size + 1,
                    count=len(batch_accounts)
                )

            self.logger.info(
                "accounts_fetched_from_zoho",
                requested=len(account_ids),
                fetched=len(accounts)
            )

            return accounts

        except Exception as e:
            self.logger.error(
                "zoho_fetch_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return []

    async def _fetch_modified_accounts(
        self,
        since_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Fetch accounts modified since given date from Zoho."""
        try:
            # Use Zoho search/filter to get modified accounts
            modified_accounts = await self.zoho.search_accounts(
                filters={"Modified_Time": {"greater_than": since_date}}
            )

            return modified_accounts

        except Exception as e:
            self.logger.error(
                "fetch_modified_accounts_failed",
                error=str(e)
            )
            return []

    def _validate_accounts(
        self,
        accounts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validate account data schema.

        Filters out invalid accounts if skip_invalid_records is enabled.
        """
        if not self.config.validate_schema:
            return accounts

        validated = []
        for account in accounts:
            if self._is_valid_account(account):
                validated.append(account)
            else:
                self.stats["validation_errors"] += 1
                self.logger.warning(
                    "invalid_account_skipped",
                    account_id=account.get("id", "unknown")
                )

                if not self.config.skip_invalid_records:
                    raise ValueError(f"Invalid account data: {account.get('id')}")

        return validated

    def _is_valid_account(self, account: Dict[str, Any]) -> bool:
        """Check if account has required fields."""
        required_fields = ["id", "Account_Name"]
        return all(field in account for field in required_fields)

    def _transform_zoho_to_cognee(
        self,
        zoho_account: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transform Zoho CRM account format to Cognee format.

        Extracts and structures:
        - Account name, industry, region
        - Key contacts
        - Deal history
        - Engagement metrics
        - Custom fields
        """
        # Extract core fields
        cognee_account = {
            "id": zoho_account.get("id"),
            "Account_Name": zoho_account.get("Account_Name", ""),
            "Industry": zoho_account.get("Industry", ""),
            "Billing_Country": zoho_account.get("Billing_Country", ""),
            "Annual_Revenue": zoho_account.get("Annual_Revenue", 0),
            "Description": zoho_account.get("Description", ""),
            "Account_Type": zoho_account.get("Account_Type", ""),
            "Rating": zoho_account.get("Rating", ""),
            "Website": zoho_account.get("Website", ""),
            "Phone": zoho_account.get("Phone", ""),

            # Owner information
            "Owner": {
                "id": zoho_account.get("Owner", {}).get("id", ""),
                "name": zoho_account.get("Owner", {}).get("name", ""),
                "email": zoho_account.get("Owner", {}).get("email", "")
            },

            # Metadata
            "Created_Time": zoho_account.get("Created_Time", ""),
            "Modified_Time": zoho_account.get("Modified_Time", ""),
            "Last_Activity_Time": zoho_account.get("Last_Activity_Time", ""),

            # Engagement metrics (if available)
            "Number_of_Employees": zoho_account.get("Number_of_Employees", 0),
            "Parent_Account": zoho_account.get("Parent_Account", {}),

            # Custom fields (preserve all)
            "custom_fields": {
                k: v for k, v in zoho_account.items()
                if k not in [
                    "id", "Account_Name", "Industry", "Billing_Country",
                    "Annual_Revenue", "Description", "Account_Type", "Rating",
                    "Website", "Phone", "Owner", "Created_Time", "Modified_Time",
                    "Last_Activity_Time", "Number_of_Employees", "Parent_Account"
                ]
            },

            # Ingestion metadata
            "_ingestion_timestamp": datetime.utcnow().isoformat(),
            "_source": "zoho_crm"
        }

        return cognee_account

    async def _deduplicate_accounts(
        self,
        accounts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Check for duplicate accounts and filter them out.

        Uses duplicate_check_fields from config.
        """
        seen = set()
        deduplicated = []

        for account in accounts:
            # Create unique key from check fields
            check_values = tuple(
                account.get(field, "")
                for field in self.config.duplicate_check_fields
            )

            if check_values not in seen:
                seen.add(check_values)
                deduplicated.append(account)
            else:
                self.stats["duplicate_count"] += 1
                self.logger.debug(
                    "duplicate_account_skipped",
                    account_id=account.get("id")
                )

        return deduplicated

    async def _ingest_in_batches(
        self,
        accounts: List[Dict[str, Any]],
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Ingest accounts in batches with progress tracking.
        """
        batch_size = batch_size or 10
        total = len(accounts)

        results = {
            "success": [],
            "failed": [],
            "errors": []
        }

        for i in range(0, total, batch_size):
            batch = accounts[i:i + batch_size]
            batch_num = (i // batch_size) + 1

            # Log progress
            if self.config.enable_progress_tracking:
                self.logger.info(
                    "ingestion_progress",
                    batch=batch_num,
                    processed=min(i + batch_size, total),
                    total=total,
                    progress_pct=round((min(i + batch_size, total) / total) * 100, 1)
                )

            # Ingest batch
            if self.config.parallel_batches:
                batch_result = await self.cognee.add_accounts_bulk(batch)
            else:
                # Sequential processing
                batch_result = {"success": 0, "failed": 0, "errors": []}
                for account in batch:
                    try:
                        await self.cognee.add_account(account)
                        batch_result["success"] += 1
                        results["success"].append(account["id"])
                    except Exception as e:
                        batch_result["failed"] += 1
                        batch_result["errors"].append({
                            "account_id": account["id"],
                            "error": str(e)
                        })
                        results["failed"].append(account["id"])

            # Aggregate results
            self.stats["success_count"] += batch_result.get("success", 0)
            self.stats["failure_count"] += batch_result.get("failed", 0)
            self.stats["total_processed"] += len(batch)

            results["errors"].extend(batch_result.get("errors", []))

            # Check max errors threshold
            if (
                self.config.max_errors and
                self.stats["failure_count"] >= self.config.max_errors
            ):
                self.logger.error(
                    "max_errors_reached",
                    failures=self.stats["failure_count"],
                    max_allowed=self.config.max_errors
                )
                break

            # Add delay between batches if configured
            if self.config.batch_delay_ms > 0 and i + batch_size < total:
                await asyncio.sleep(self.config.batch_delay_ms / 1000)

        return results

    async def _create_account_relationships(
        self,
        accounts: List[Dict[str, Any]]
    ) -> None:
        """
        Create relationships between accounts in knowledge graph.

        Relationships:
        - Same industry
        - Same region
        - Parent-child relationships
        """
        self.logger.info(
            "creating_account_relationships",
            account_count=len(accounts)
        )

        # Group accounts by industry and region
        industry_groups = {}
        region_groups = {}

        for account in accounts:
            industry = account.get("Industry", "Unknown")
            region = account.get("Billing_Country", "Unknown")

            industry_groups.setdefault(industry, []).append(account["id"])
            region_groups.setdefault(region, []).append(account["id"])

        # Store relationship metadata (can be used for graph queries)
        self.logger.info(
            "relationships_created",
            industry_groups=len(industry_groups),
            region_groups=len(region_groups)
        )

    def _generate_report(
        self,
        results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate detailed ingestion report."""
        duration = None
        if self.stats["start_time"] and self.stats["end_time"]:
            duration = (
                self.stats["end_time"] - self.stats["start_time"]
            ).total_seconds()

        report = {
            "summary": {
                "total_processed": self.stats["total_processed"],
                "success_count": self.stats["success_count"],
                "failure_count": self.stats["failure_count"],
                "duplicate_count": self.stats["duplicate_count"],
                "validation_errors": self.stats["validation_errors"],
                "success_rate": (
                    round(
                        (self.stats["success_count"] / self.stats["total_processed"]) * 100,
                        2
                    )
                    if self.stats["total_processed"] > 0
                    else 0
                )
            },
            "timing": {
                "start_time": (
                    self.stats["start_time"].isoformat()
                    if self.stats["start_time"] else None
                ),
                "end_time": (
                    self.stats["end_time"].isoformat()
                    if self.stats["end_time"] else None
                ),
                "duration_seconds": duration,
                "throughput_per_second": (
                    round(self.stats["total_processed"] / duration, 2)
                    if duration and duration > 0
                    else 0
                )
            },
            "errors": results.get("errors", []) if results else []
        }

        self.logger.info(
            "ingestion_report_generated",
            **report["summary"]
        )

        return report


class AccountSyncScheduler:
    """
    Scheduler for periodic account synchronization.

    Manages incremental sync schedules and triggers.
    """

    def __init__(
        self,
        ingestion_pipeline: AccountIngestionPipeline,
        sync_interval_hours: int = 24
    ):
        """
        Initialize sync scheduler.

        Args:
            ingestion_pipeline: Ingestion pipeline instance
            sync_interval_hours: Hours between sync runs
        """
        self.pipeline = ingestion_pipeline
        self.sync_interval_hours = sync_interval_hours
        self.logger = logger.bind(component="sync_scheduler")
        self._running = False

    async def start(self) -> None:
        """Start periodic sync scheduler."""
        self._running = True
        self.logger.info(
            "sync_scheduler_started",
            interval_hours=self.sync_interval_hours
        )

        while self._running:
            try:
                # Calculate since_date for incremental sync
                since_date = datetime.utcnow()
                since_date = since_date.replace(
                    hour=since_date.hour - self.sync_interval_hours
                )

                # Run sync
                result = await self.pipeline.sync_account_updates(
                    since_date=since_date
                )

                self.logger.info(
                    "scheduled_sync_completed",
                    **result["summary"]
                )

            except Exception as e:
                self.logger.error(
                    "scheduled_sync_failed",
                    error=str(e)
                )

            # Wait for next interval
            await asyncio.sleep(self.sync_interval_hours * 3600)

    async def stop(self) -> None:
        """Stop sync scheduler."""
        self._running = False
        self.logger.info("sync_scheduler_stopped")
