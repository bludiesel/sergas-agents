"""Zoho Data Scout Subagent - Week 7 Implementation.

Read-only subagent for fetching and analyzing Zoho CRM data.
Following SPARC architecture specifications (lines 170-227).

Features:
- Fetch accounts by owner with filters
- Detect changes since last sync
- Aggregate related records (deals, activities, notes)
- Identify risk signals
- Field-level diff tracking
- Caching with last-sync timestamps
- Integration with ZohoIntegrationManager

Permission Mode: plan (read-only execution)
Tool Allowlist: Zoho read-only tools + Read/Write (approval required)
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, AsyncGenerator
from decimal import Decimal
import structlog
import json
from pathlib import Path

from src.agents.models import (
    AccountRecord,
    AccountSnapshot,
    ChangeDetectionResult,
    AggregatedData,
    RiskSignal,
    DealRecord,
    ActivityRecord,
    NoteRecord,
    ChangeType,
    AccountStatus,
    DealStage,
    ActivityType,
    RiskLevel,
)
from src.agents.config import DataScoutConfig, SystemPromptTemplate
from src.agents.utils import (
    calculate_field_diff,
    detect_stalled_deals,
    calculate_inactivity_days,
    assess_account_risk,
    generate_risk_signals,
    aggregate_deal_pipeline,
    summarize_activities,
    calculate_engagement_score,
)
from src.integrations.zoho.integration_manager import ZohoIntegrationManager
from src.integrations.zoho.exceptions import ZohoAPIError
from src.events.ag_ui_emitter import AGUIEventEmitter

logger = structlog.get_logger(__name__)


class ZohoDataScout:
    """Zoho Data Scout Subagent for Sergas Account Manager.

    System Prompt (from architecture lines 195-222):
    You are the Zoho Data Scout for Sergas Account Manager.

    Your responsibilities:
    1. Fetch accounts assigned to specified owners from Zoho CRM
    2. Detect changes since last sync (modified fields, new activities, stalled deals)
    3. Aggregate related records (deals, tasks, notes, activities)
    4. Return structured data with change flags and metadata

    Never write to CRM. If asked to modify data, respond: "I can only read data.
    Contact the Orchestrator to request approved modifications."

    Features:
    - Account fetching with owner filters
    - Change detection with field-level diffs
    - Activity aggregation (deals, tasks, notes, activities)
    - Risk signal identification
    - Caching with TTL

    Example:
        >>> config = DataScoutConfig.from_env()
        >>> scout = ZohoDataScout(
        ...     zoho_manager=zoho_manager,
        ...     config=config
        ... )
        >>> accounts = await scout.fetch_accounts_by_owner(
        ...     owner_id="owner_123",
        ...     filters={"status": "Active"}
        ... )
        >>> snapshot = await scout.get_account_snapshot("account_456")
    """

    def __init__(
        self,
        zoho_manager: ZohoIntegrationManager,
        config: Optional[DataScoutConfig] = None,
    ) -> None:
        """Initialize Zoho Data Scout.

        Args:
            zoho_manager: Zoho integration manager
            config: Data Scout configuration (loads from env if None)
        """
        self.zoho_manager = zoho_manager
        self.config = config or DataScoutConfig.from_env()

        # Initialize cache
        self.cache_dir = self.config.cache.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Last sync timestamps (account_id -> datetime)
        self.last_sync_times: Dict[str, datetime] = {}

        # System prompt
        self.system_prompt = self.config.get_system_prompt("main")

        self.logger = logger.bind(
            component="zoho_data_scout",
            version=self.config.agent_version,
        )
        self.logger.info(
            "data_scout_initialized",
            read_only=self.config.read_only,
            permission_mode=self.config.permission_mode,
        )

    async def fetch_accounts_by_owner(
        self,
        owner_id: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[AccountRecord]:
        """Fetch accounts assigned to specific owner.

        Algorithm from pseudocode lines 686-718.

        Args:
            owner_id: Zoho owner/user ID
            filters: Additional filter criteria

        Returns:
            List of account records

        Raises:
            ZohoAPIError: If fetch fails
        """
        self.logger.info(
            "fetching_accounts_by_owner",
            owner_id=owner_id,
            has_filters=filters is not None,
        )

        try:
            # Build search criteria
            search_criteria = f"Owner.id:equals:{owner_id}"

            if filters:
                if "status" in filters:
                    search_criteria += f" and Account_Status:equals:{filters['status']}"
                if "modified_since" in filters:
                    modified_date = filters["modified_since"].strftime("%Y-%m-%d")
                    search_criteria += f" and Modified_Time:greater_than:{modified_date}"

            # Fetch from Zoho
            zoho_accounts = await self.zoho_manager.search_accounts(
                criteria=search_criteria,
                limit=1000,
                context={"agent_context": True},
            )

            # Convert to AccountRecord models
            accounts: List[AccountRecord] = []
            for zoho_account in zoho_accounts:
                account = self._convert_to_account_record(zoho_account)
                accounts.append(account)

            self.logger.info(
                "accounts_fetched",
                owner_id=owner_id,
                account_count=len(accounts),
            )

            return accounts

        except Exception as e:
            self.logger.error(
                "fetch_accounts_failed",
                owner_id=owner_id,
                error=str(e),
            )
            raise ZohoAPIError(f"Failed to fetch accounts for owner {owner_id}: {str(e)}")

    async def detect_changes(
        self,
        account_id: str,
        last_sync: Optional[datetime] = None,
    ) -> ChangeDetectionResult:
        """Detect changes since last sync with field-level diff tracking.

        Algorithm from pseudocode lines 574-629.

        Args:
            account_id: Account to check
            last_sync: Last sync timestamp (uses cached if None)

        Returns:
            Change detection result with field diffs
        """
        self.logger.info(
            "detecting_changes",
            account_id=account_id,
            last_sync=last_sync.isoformat() if last_sync else None,
        )

        result = ChangeDetectionResult(
            account_id=account_id,
            comparison_baseline=last_sync or self.last_sync_times.get(account_id),
        )

        try:
            # Fetch current state
            current_data = await self.zoho_manager.get_account(
                account_id,
                context={"agent_context": True},
            )

            # Load cached previous state
            cached_state = self._load_cached_state(account_id)

            if not cached_state:
                # First time seeing this account
                result.change_types.add(ChangeType.NEW_ACCOUNT)
                result.changes_detected = True
                self.logger.info(
                    "new_account_detected",
                    account_id=account_id,
                )
                # Save current state
                self._save_cached_state(account_id, current_data)
                return result

            # Calculate field differences
            field_changes = calculate_field_diff(
                old_data=cached_state,
                new_data=current_data,
            )

            for change in field_changes:
                result.add_change(
                    field_name=change.field_name,
                    old_value=change.old_value,
                    new_value=change.new_value,
                    change_type=change.change_type,
                )

            # Save current state to cache
            self._save_cached_state(account_id, current_data)

            self.logger.info(
                "changes_detected",
                account_id=account_id,
                change_count=len(result.field_changes),
                requires_attention=result.requires_attention,
            )

            return result

        except Exception as e:
            self.logger.error(
                "change_detection_failed",
                account_id=account_id,
                error=str(e),
            )
            raise

    async def aggregate_related_records(
        self,
        account_id: str,
    ) -> AggregatedData:
        """Aggregate related records (deals, activities, notes).

        Algorithm from pseudocode lines 553-572.

        Args:
            account_id: Account to aggregate data for

        Returns:
            Aggregated data with summaries
        """
        self.logger.info(
            "aggregating_related_records",
            account_id=account_id,
        )

        aggregated = AggregatedData(account_id=account_id)
        start_time = datetime.utcnow()

        try:
            # Fetch related data in parallel
            deals_task = self._fetch_deals(account_id)
            activities_task = self._fetch_activities(account_id)
            notes_task = self._fetch_notes(account_id)

            deals, activities, notes = await asyncio.gather(
                deals_task,
                activities_task,
                notes_task,
                return_exceptions=True,
            )

            # Handle exceptions
            if isinstance(deals, Exception):
                self.logger.warning("deals_fetch_failed", error=str(deals))
                deals = []
            if isinstance(activities, Exception):
                self.logger.warning("activities_fetch_failed", error=str(activities))
                activities = []
            if isinstance(notes, Exception):
                self.logger.warning("notes_fetch_failed", error=str(notes))
                notes = []

            # Populate aggregated data
            aggregated.deals = deals
            aggregated.activities = activities
            aggregated.notes = notes

            # Calculate summaries
            aggregated.calculate_summaries()

            # Calculate data freshness
            duration = (datetime.utcnow() - start_time).total_seconds()
            aggregated.data_freshness = int(duration)

            self.logger.info(
                "aggregation_complete",
                account_id=account_id,
                deals=len(deals),
                activities=len(activities),
                notes=len(notes),
                duration_seconds=duration,
            )

            return aggregated

        except Exception as e:
            self.logger.error(
                "aggregation_failed",
                account_id=account_id,
                error=str(e),
            )
            raise

    async def identify_risk_signals(
        self,
        account_data: AccountRecord,
        aggregated_data: Optional[AggregatedData] = None,
    ) -> List[RiskSignal]:
        """Identify risk signals for account.

        Algorithm combines multiple risk detection patterns.

        Args:
            account_data: Account record
            aggregated_data: Aggregated related data (fetched if None)

        Returns:
            List of identified risk signals
        """
        self.logger.info(
            "identifying_risk_signals",
            account_id=account_data.account_id,
        )

        # Fetch aggregated data if not provided
        if not aggregated_data:
            aggregated_data = await self.aggregate_related_records(
                account_data.account_id
            )

        # Generate risk signals using utilities
        signals = generate_risk_signals(
            account=account_data,
            deals=aggregated_data.deals,
            activities=aggregated_data.activities,
            inactivity_threshold=self.config.inactivity_threshold_days,
            deal_stalled_threshold=self.config.deal_stalled_threshold_days,
        )

        self.logger.info(
            "risk_signals_identified",
            account_id=account_data.account_id,
            signal_count=len(signals),
        )

        return signals

    async def get_account_snapshot(
        self,
        account_id: str,
    ) -> AccountSnapshot:
        """Get complete account snapshot with all analysis.

        Main integration point - combines all Data Scout capabilities.

        Args:
            account_id: Account to snapshot

        Returns:
            Complete account snapshot

        Raises:
            ZohoAPIError: If fetch fails
        """
        snapshot_id = f"{account_id}_{datetime.utcnow().isoformat()}"

        self.logger.info(
            "creating_account_snapshot",
            account_id=account_id,
            snapshot_id=snapshot_id,
        )

        try:
            # Fetch account data
            zoho_account = await self.zoho_manager.get_account(
                account_id,
                context={"agent_context": True},
            )
            account = self._convert_to_account_record(zoho_account)

            # Detect changes
            changes = await self.detect_changes(account_id)

            # Add change flags to account
            account.change_flags = changes.change_types

            # Aggregate related data
            aggregated_data = await self.aggregate_related_records(account_id)

            # Identify risk signals
            risk_signals = await self.identify_risk_signals(account, aggregated_data)

            # Create snapshot
            snapshot = AccountSnapshot(
                snapshot_id=snapshot_id,
                account=account,
                aggregated_data=aggregated_data,
                changes=changes,
                risk_signals=risk_signals,
                data_sources=[
                    "zoho_crm_mcp",
                    "zoho_deals_api",
                    "zoho_activities_api",
                    "zoho_notes_api",
                ],
            )

            # Update analysis flags
            snapshot.update_analysis_flags()

            # Update last sync time
            self.last_sync_times[account_id] = datetime.utcnow()

            self.logger.info(
                "snapshot_created",
                account_id=account_id,
                snapshot_id=snapshot_id,
                risk_level=snapshot.risk_level.value,
                priority_score=snapshot.priority_score,
                needs_review=snapshot.needs_review,
            )

            return snapshot

        except Exception as e:
            self.logger.error(
                "snapshot_creation_failed",
                account_id=account_id,
                error=str(e),
            )
            raise

    async def execute_with_events(
        self,
        context: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute Zoho data retrieval with AG UI event streaming.

        Emits tool calls for Zoho API operations and streams results.

        Args:
            context: Execution context with account_id

        Yields:
            AG UI Protocol events
        """
        session_id = context.get("session_id", "default")
        emitter = AGUIEventEmitter(session_id=session_id)

        account_id = context.get("account_id")
        step = context.get("step", 1)

        try:
            # Emit agent started
            yield emitter.emit_agent_started(
                agent="zoho_data_scout",
                step=step,
                task=f"Retrieve account {account_id} from Zoho CRM"
            )

            # Stream progress message
            yield emitter.emit_agent_stream(
                agent="zoho_data_scout",
                content=f"Retrieving account {account_id} from Zoho CRM...",
                content_type="text"
            )

            # Tool call: Get account snapshot
            tool_call_id = "zoho-get-snapshot"
            yield emitter.emit_tool_call(
                tool_name="zoho_get_account_snapshot",
                tool_args={"account_id": account_id},
                tool_call_id=tool_call_id
            )

            # Execute snapshot retrieval
            snapshot = await self.get_account_snapshot(account_id)

            # Emit tool result
            yield emitter.emit_tool_result(
                tool_call_id=tool_call_id,
                tool_name="zoho_get_account_snapshot",
                result={
                    "account_id": snapshot.account.account_id,
                    "account_name": snapshot.account.account_name,
                    "risk_level": snapshot.risk_level.value,
                    "priority_score": snapshot.priority_score,
                    "needs_review": snapshot.needs_review,
                    "change_count": len(snapshot.changes.field_changes)
                },
                success=True
            )

            # Stream success message
            yield emitter.emit_agent_stream(
                agent="zoho_data_scout",
                content=f"Account snapshot retrieved successfully. Risk level: {snapshot.risk_level.value}",
                content_type="text"
            )

            # Store in context for next agent
            context["account_snapshot"] = snapshot

            # Emit agent completed
            yield emitter.emit_agent_completed(
                agent="zoho_data_scout",
                step=step,
                output={
                    "account_id": account_id,
                    "snapshot_id": snapshot.snapshot_id,
                    "risk_level": snapshot.risk_level.value,
                    "priority_score": snapshot.priority_score
                }
            )

        except Exception as e:
            self.logger.error("zoho_scout_execution_error", error=str(e))
            yield emitter.emit_agent_error(
                agent="zoho_data_scout",
                step=step,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise

    # ========================================================================
    # INTERNAL HELPER METHODS
    # ========================================================================

    def _convert_to_account_record(
        self,
        zoho_data: Dict[str, Any],
    ) -> AccountRecord:
        """Convert Zoho API response to AccountRecord.

        Args:
            zoho_data: Raw Zoho account data

        Returns:
            AccountRecord instance
        """
        owner = zoho_data.get("Owner", {})

        return AccountRecord(
            account_id=zoho_data.get("id", ""),
            account_name=zoho_data.get("Account_Name", ""),
            owner_id=owner.get("id", ""),
            owner_name=owner.get("name", ""),
            status=AccountStatus(zoho_data.get("Account_Status", "Active")),
            last_modified=self._parse_datetime(zoho_data.get("Modified_Time")),
            last_activity_date=self._parse_datetime(zoho_data.get("Last_Activity_Time")),
            created_time=self._parse_datetime(zoho_data.get("Created_Time")),
            deal_count=int(zoho_data.get("Open_Deals_Count", 0)),
            total_value=Decimal(str(zoho_data.get("Total_Deal_Value", 0))),
            annual_revenue=Decimal(str(zoho_data.get("Annual_Revenue", 0))),
            industry=zoho_data.get("Industry", ""),
            website=zoho_data.get("Website", ""),
            phone=zoho_data.get("Phone", ""),
            billing_city=zoho_data.get("Billing_City", ""),
            billing_country=zoho_data.get("Billing_Country", ""),
            custom_fields={
                k: v for k, v in zoho_data.items()
                if k.startswith("Custom_") or k.startswith("cf_")
            },
        )

    async def _fetch_deals(
        self,
        account_id: str,
    ) -> List[DealRecord]:
        """Fetch deals for account.

        Args:
            account_id: Account identifier

        Returns:
            List of deal records
        """
        try:
            # Use Zoho MCP tool to get deals
            criteria = f"Account_Name.id:equals:{account_id}"
            zoho_deals = await self.zoho_manager.search_accounts(
                criteria=criteria,
                limit=self.config.max_deals_per_account,
                context={"agent_context": True},
            )

            deals: List[DealRecord] = []
            for zoho_deal in zoho_deals:
                deal = self._convert_to_deal_record(zoho_deal)
                deals.append(deal)

            return deals

        except Exception as e:
            self.logger.warning(
                "deals_fetch_failed",
                account_id=account_id,
                error=str(e),
            )
            return []

    async def _fetch_activities(
        self,
        account_id: str,
    ) -> List[ActivityRecord]:
        """Fetch activities for account.

        Args:
            account_id: Account identifier

        Returns:
            List of activity records
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=self.config.activity_lookback_days)

            # Fetch activities (placeholder - would use Zoho Activities API)
            # In production: zoho_manager.get_activities(account_id, modified_since=cutoff)

            activities: List[ActivityRecord] = []
            # TODO: Implement actual Zoho Activities API call

            return activities

        except Exception as e:
            self.logger.warning(
                "activities_fetch_failed",
                account_id=account_id,
                error=str(e),
            )
            return []

    async def _fetch_notes(
        self,
        account_id: str,
    ) -> List[NoteRecord]:
        """Fetch notes for account.

        Args:
            account_id: Account identifier

        Returns:
            List of note records
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=self.config.notes_lookback_days)

            # Fetch notes (placeholder - would use Zoho Notes API)
            # In production: zoho_manager.get_notes(account_id, modified_since=cutoff)

            notes: List[NoteRecord] = []
            # TODO: Implement actual Zoho Notes API call

            return notes

        except Exception as e:
            self.logger.warning(
                "notes_fetch_failed",
                account_id=account_id,
                error=str(e),
            )
            return []

    def _convert_to_deal_record(
        self,
        zoho_data: Dict[str, Any],
    ) -> DealRecord:
        """Convert Zoho deal data to DealRecord.

        Args:
            zoho_data: Raw Zoho deal data

        Returns:
            DealRecord instance
        """
        owner = zoho_data.get("Owner", {})

        return DealRecord(
            deal_id=zoho_data.get("id", ""),
            deal_name=zoho_data.get("Deal_Name", ""),
            account_id=zoho_data.get("Account_Name", {}).get("id", ""),
            stage=DealStage(zoho_data.get("Stage", "Qualification")),
            amount=Decimal(str(zoho_data.get("Amount", 0))),
            probability=int(zoho_data.get("Probability", 0)),
            closing_date=self._parse_datetime(zoho_data.get("Closing_Date")),
            created_time=self._parse_datetime(zoho_data.get("Created_Time")),
            modified_time=self._parse_datetime(zoho_data.get("Modified_Time")),
            stage_changed_date=self._parse_datetime(zoho_data.get("Stage_History", {}).get("last_changed")),
            owner_id=owner.get("id", ""),
            owner_name=owner.get("name", ""),
        )

    def _parse_datetime(
        self,
        value: Any,
    ) -> datetime:
        """Parse datetime from various formats.

        Args:
            value: Datetime value (string, datetime, or None)

        Returns:
            Parsed datetime (defaults to utcnow if None)
        """
        if not value:
            return datetime.utcnow()

        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except Exception:
                return datetime.utcnow()

        return datetime.utcnow()

    def _get_cache_path(
        self,
        account_id: str,
    ) -> Path:
        """Get cache file path for account.

        Args:
            account_id: Account identifier

        Returns:
            Cache file path
        """
        return self.cache_dir / f"{account_id}.json"

    def _load_cached_state(
        self,
        account_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Load cached account state.

        Args:
            account_id: Account identifier

        Returns:
            Cached state or None
        """
        if not self.config.cache.enabled:
            return None

        cache_path = self._get_cache_path(account_id)

        if not cache_path.exists():
            return None

        try:
            # Check cache age
            cache_age = datetime.utcnow() - datetime.fromtimestamp(
                cache_path.stat().st_mtime
            )

            if cache_age.total_seconds() > self.config.cache.ttl_seconds:
                self.logger.debug(
                    "cache_expired",
                    account_id=account_id,
                    age_seconds=cache_age.total_seconds(),
                )
                return None

            # Load cache
            with cache_path.open("r") as f:
                return json.load(f)

        except Exception as e:
            self.logger.warning(
                "cache_load_failed",
                account_id=account_id,
                error=str(e),
            )
            return None

    def _save_cached_state(
        self,
        account_id: str,
        data: Dict[str, Any],
    ) -> None:
        """Save account state to cache.

        Args:
            account_id: Account identifier
            data: Account data to cache
        """
        if not self.config.cache.enabled:
            return

        cache_path = self._get_cache_path(account_id)

        try:
            with cache_path.open("w") as f:
                json.dump(data, f, default=str, indent=2)

            self.logger.debug(
                "state_cached",
                account_id=account_id,
            )

        except Exception as e:
            self.logger.warning(
                "cache_save_failed",
                account_id=account_id,
                error=str(e),
            )
