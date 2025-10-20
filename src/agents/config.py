"""Data Scout Agent - Configuration Management.

Subagent configuration loader following SPARC architecture
specifications (lines 193-226).

Features:
- Tool permission definitions
- System prompt templates
- Environment variable validation
- Cache configuration
- Read-only enforcement
"""

import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator
from pathlib import Path


class CacheConfig(BaseModel):
    """Cache configuration for Data Scout."""
    enabled: bool = Field(default=True, description="Enable caching")
    ttl_seconds: int = Field(default=21600, ge=60, description="Cache TTL (6 hours default)")
    max_size: int = Field(default=1000, ge=10, description="Max cache entries")
    cache_dir: Path = Field(default=Path(".cache/data_scout"), description="Cache directory")

    def __init__(self, **data):
        """Initialize cache config."""
        super().__init__(**data)
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)


class ToolPermissions(BaseModel):
    """Tool allowlist for Data Scout subagent."""
    # Zoho CRM MCP Tools (Read-Only)
    zoho_tools: List[str] = Field(
        default=[
            "zoho_get_accounts",
            "zoho_get_account_details",
            "zoho_search_accounts",
            "zoho_get_deals",
            "zoho_list_open_deals",
            "zoho_get_activities",
            "zoho_get_notes",
            "zoho_get_user_info",
        ],
        description="Allowed Zoho MCP tools"
    )

    # Utility tools
    utility_tools: List[str] = Field(
        default=["Read", "Write"],
        description="Utility tools (Write requires approval)"
    )

    # Write operations require approval
    write_approval_required: bool = Field(
        default=True,
        description="Require approval for Write operations"
    )

    def get_all_tools(self) -> List[str]:
        """Get complete tool allowlist.

        Returns:
            All allowed tools
        """
        return self.zoho_tools + self.utility_tools

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Check if tool is allowed.

        Args:
            tool_name: Tool to check

        Returns:
            True if tool allowed
        """
        return tool_name in self.get_all_tools()

    def is_write_operation(self, tool_name: str) -> bool:
        """Check if tool is a write operation.

        Args:
            tool_name: Tool to check

        Returns:
            True if write operation
        """
        return tool_name == "Write"


class SystemPromptTemplate:
    """System prompt templates for Data Scout."""

    MAIN_PROMPT = """You are the Zoho Data Scout for Sergas Account Manager.

Your responsibilities:
1. Fetch accounts assigned to specified owners from Zoho CRM
2. Detect changes since last sync (modified fields, new activities, stalled deals)
3. Aggregate related records (deals, tasks, notes, activities)
4. Return structured data with change flags and metadata

Output Format:
{
  "account_id": "123456789",
  "account_name": "Acme Corp",
  "owner": "john.doe@sergas.com",
  "last_modified": "2025-10-15T14:30:00Z",
  "changes_detected": true,
  "changes": [
    {"field": "Deal_Stage", "old": "Negotiation", "new": "Closed Won",
     "timestamp": "2025-10-15T10:00:00Z"}
  ],
  "open_deals": [...],
  "recent_activities": [...],
  "notes_count": 15,
  "risk_signals": ["No activity in 30 days", "Deal stalled in stage"]
}

Never write to CRM. If asked to modify data, respond: "I can only read data.
Contact the Orchestrator to request approved modifications."
"""

    CHANGE_DETECTION_PROMPT = """Analyze account changes since last sync.

Focus on:
- Owner changes (requires immediate notification)
- Status changes (Active → At Risk)
- Deal stage progression or stalls (>30 days in stage)
- Inactivity thresholds (no activity >14 days)
- High-value activities (demos, executive meetings, contract reviews)
- Custom field modifications

Return structured change detection results with:
- Field-level diff tracking
- Change timestamps
- Change type classification
- Priority assessment
"""

    RISK_ASSESSMENT_PROMPT = """Identify risk signals for account.

Risk indicators:
1. CRITICAL: No activity in 30+ days
2. HIGH: Deal stalled >30 days in stage
3. HIGH: Owner change without transition plan
4. MEDIUM: Decreasing engagement (fewer activities month-over-month)
5. MEDIUM: Overdue commitments or tasks
6. LOW: Minor field changes

Return risk signals with:
- Signal type and severity
- Description and details
- Actionable recommendations
- Data sources for each signal
"""

    AGGREGATION_PROMPT = """Aggregate related account data.

Fetch and consolidate:
1. Open deals (all stages except Closed Won/Lost)
2. Recent activities (last 90 days)
3. Notes and communications (last 90 days)
4. Related contacts

Calculate summaries:
- Total deal pipeline value
- Stalled deal count
- High-value activity count
- Activity frequency trends
- Last interaction date
"""

    @classmethod
    def get_prompt(
        cls,
        prompt_type: str = "main",
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Get system prompt by type.

        Args:
            prompt_type: Prompt type (main, change_detection, risk_assessment, aggregation)
            context: Additional context for prompt customization

        Returns:
            Formatted system prompt
        """
        prompts = {
            "main": cls.MAIN_PROMPT,
            "change_detection": cls.CHANGE_DETECTION_PROMPT,
            "risk_assessment": cls.RISK_ASSESSMENT_PROMPT,
            "aggregation": cls.AGGREGATION_PROMPT,
        }

        prompt = prompts.get(prompt_type, cls.MAIN_PROMPT)

        # Inject context if provided
        if context:
            prompt = prompt.format(**context)

        return prompt


class DataScoutConfig(BaseModel):
    """Complete configuration for Zoho Data Scout subagent."""

    # Agent identification
    agent_name: str = Field(default="zoho_data_scout", description="Agent identifier")
    agent_version: str = Field(default="1.0.0", description="Agent version")

    # Tool permissions
    tool_permissions: ToolPermissions = Field(
        default_factory=ToolPermissions,
        description="Tool allowlist"
    )

    # Permission mode (read-only)
    permission_mode: str = Field(default="plan", description="Claude SDK permission mode")
    read_only: bool = Field(default=True, description="Read-only enforcement")

    # Cache configuration
    cache: CacheConfig = Field(default_factory=CacheConfig, description="Cache settings")

    # Change detection thresholds
    inactivity_threshold_days: int = Field(default=30, ge=1, description="Inactivity threshold")
    deal_stalled_threshold_days: int = Field(default=30, ge=1, description="Deal stalled threshold")
    high_value_activity_types: List[str] = Field(
        default=["Demo", "Contract Review", "Executive Meeting"],
        description="High-value activity types"
    )

    # Data fetching limits
    max_activities_per_account: int = Field(default=100, ge=10, description="Max activities to fetch")
    max_notes_per_account: int = Field(default=50, ge=5, description="Max notes to fetch")
    max_deals_per_account: int = Field(default=20, ge=5, description="Max deals to fetch")
    activity_lookback_days: int = Field(default=90, ge=1, description="Activity lookback period")
    notes_lookback_days: int = Field(default=90, ge=1, description="Notes lookback period")

    # Execution timeouts
    default_timeout_seconds: int = Field(default=300, ge=30, description="Default operation timeout")
    batch_timeout_seconds: int = Field(default=600, ge=60, description="Batch operation timeout")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    structured_logging: bool = Field(default=True, description="Enable structured logging")

    # Environment variables
    zoho_api_timeout: int = Field(default=30, ge=5, description="Zoho API timeout")

    @field_validator("permission_mode")
    @classmethod
    def validate_permission_mode(cls, v: str) -> str:
        """Validate permission mode is read-only.

        Args:
            v: Permission mode value

        Returns:
            Validated permission mode

        Raises:
            ValueError: If not read-only mode
        """
        allowed_modes = ["plan"]
        if v not in allowed_modes:
            raise ValueError(
                f"Data Scout must use read-only permission mode: {allowed_modes}"
            )
        return v

    @classmethod
    def from_env(cls) -> "DataScoutConfig":
        """Load configuration from environment variables.

        Returns:
            Configuration instance
        """
        return cls(
            agent_name=os.getenv("DATA_SCOUT_AGENT_NAME", "zoho_data_scout"),
            agent_version=os.getenv("DATA_SCOUT_VERSION", "1.0.0"),
            inactivity_threshold_days=int(os.getenv("INACTIVITY_THRESHOLD_DAYS", "30")),
            deal_stalled_threshold_days=int(os.getenv("DEAL_STALLED_THRESHOLD_DAYS", "30")),
            max_activities_per_account=int(os.getenv("MAX_ACTIVITIES_PER_ACCOUNT", "100")),
            max_notes_per_account=int(os.getenv("MAX_NOTES_PER_ACCOUNT", "50")),
            max_deals_per_account=int(os.getenv("MAX_DEALS_PER_ACCOUNT", "20")),
            activity_lookback_days=int(os.getenv("ACTIVITY_LOOKBACK_DAYS", "90")),
            notes_lookback_days=int(os.getenv("NOTES_LOOKBACK_DAYS", "90")),
            default_timeout_seconds=int(os.getenv("DATA_SCOUT_TIMEOUT", "300")),
            log_level=os.getenv("DATA_SCOUT_LOG_LEVEL", "INFO"),
            zoho_api_timeout=int(os.getenv("ZOHO_API_TIMEOUT", "30")),
        )

    def get_system_prompt(self, prompt_type: str = "main") -> str:
        """Get system prompt for agent.

        Args:
            prompt_type: Type of prompt to retrieve

        Returns:
            System prompt string
        """
        return SystemPromptTemplate.get_prompt(prompt_type)

    def validate_environment(self) -> Dict[str, bool]:
        """Validate required environment variables and settings.

        Returns:
            Validation results
        """
        results = {
            "read_only_mode": self.read_only,
            "permission_mode_valid": self.permission_mode == "plan",
            "cache_configured": self.cache.enabled,
            "thresholds_valid": (
                self.inactivity_threshold_days > 0 and
                self.deal_stalled_threshold_days > 0
            ),
            "limits_valid": (
                self.max_activities_per_account > 0 and
                self.max_notes_per_account > 0
            ),
        }

        all_valid = all(results.values())
        results["all_valid"] = all_valid

        return results

    def get_tool_allowlist(self) -> List[str]:
        """Get complete tool allowlist.

        Returns:
            List of allowed tools
        """
        return self.tool_permissions.get_all_tools()

    def is_write_allowed(self) -> bool:
        """Check if write operations are allowed.

        Returns:
            False (Data Scout is read-only)
        """
        return False

    class Config:
        """Pydantic configuration."""
        validate_assignment = True
