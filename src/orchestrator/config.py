"""Orchestrator Configuration - Settings and environment management.

Manages:
- Environment variable loading
- Configuration validation
- MCP server settings
- Hook function registration
- Permission modes
"""

import os
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings
import structlog

logger = structlog.get_logger(__name__)


class PermissionMode(str, Enum):
    """Agent permission modes."""
    ACCEPT_EDITS = "acceptEdits"  # Require approval for file writes
    AUTO_APPROVE = "autoApprove"  # Auto-approve operations
    STRICT = "strict"  # Maximum validation


class MCPProtocol(str, Enum):
    """MCP server protocols."""
    STDIO = "stdio"
    REMOTE = "remote"
    HTTP = "http"


class MCPServerConfig(BaseModel):
    """MCP server configuration."""
    name: str
    protocol: MCPProtocol
    endpoint: Optional[str] = None  # For remote protocol
    command: Optional[List[str]] = None  # For stdio protocol
    env: Dict[str, str] = Field(default_factory=dict)
    enabled: bool = True


class HooksConfig(BaseModel):
    """Hooks configuration."""
    pre_tool_enabled: bool = True
    post_tool_enabled: bool = True
    session_end_enabled: bool = True

    # Hook function names (would be actual functions in production)
    pre_tool_hook: str = "log_tool_invocation"
    post_tool_hook: str = "record_tool_result"
    session_end_hook: str = "export_audit_trail"


class OrchestratorConfig(BaseSettings):
    """Main orchestrator configuration.

    Loads settings from environment variables and provides
    validated configuration for the orchestrator system.

    Environment Variables:
    - ZOHO_MCP_ENDPOINT: Zoho CRM MCP endpoint URL
    - COGNEE_MCP_COMMAND: Cognee MCP command
    - CLAUDE_API_KEY: Claude API key
    - MAX_CONCURRENT_SUBAGENTS: Maximum parallel subagents
    - CIRCUIT_BREAKER_THRESHOLD: Failure threshold
    - CIRCUIT_BREAKER_TIMEOUT: Recovery timeout seconds

    Example:
        >>> config = OrchestratorConfig.from_env()
        >>> orchestrator = MainOrchestrator(config)
    """

    # System prompt (from SPARC Architecture)
    system_prompt: str = """You are the Sergas Account Manager Orchestrator.
Your role is to:
1. Coordinate subagents to review account portfolios
2. Compile actionable briefs for account owners
3. Gate all CRM modifications through human approval
4. Maintain audit trails of all recommendations and decisions

Never modify CRM data without explicit user approval.
Always provide data sources for recommendations.
Prioritize high-risk accounts first."""

    # Tool permissions
    allowed_tools: List[str] = Field(
        default_factory=lambda: [
            "Read",
            "Write",
            "Bash",
            "TodoWrite",
            "create_session",
            "fork_session",
        ]
    )

    disallowed_tools: List[str] = Field(
        default_factory=lambda: [
            "*zoho*update*",
            "*zoho*create*",
            "*zoho*delete*",
        ]
    )

    # Permission settings
    permission_mode: PermissionMode = PermissionMode.ACCEPT_EDITS
    setting_sources: List[str] = Field(default_factory=lambda: ["project"])

    # MCP server configurations
    zoho_mcp_endpoint: str = Field(
        default="",
        description="Zoho CRM MCP endpoint URL",
    )
    cognee_mcp_command: List[str] = Field(
        default_factory=lambda: ["npx", "cognee-mcp"],
        description="Cognee MCP command",
    )

    # Subagent execution
    max_concurrent_subagents: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum concurrent subagent queries",
    )
    subagent_timeout_seconds: int = Field(
        default=300,
        ge=30,
        le=600,
        description="Subagent query timeout",
    )

    # Circuit breaker settings
    circuit_breaker_threshold: int = Field(
        default=5,
        ge=3,
        le=10,
        description="Circuit breaker failure threshold",
    )
    circuit_breaker_timeout: int = Field(
        default=60,
        ge=30,
        le=300,
        description="Circuit breaker recovery timeout seconds",
    )

    # Hooks configuration
    hooks_config: HooksConfig = Field(default_factory=HooksConfig)

    # Approval configuration
    approval_config: "ApprovalConfig" = Field(
        default_factory=lambda: __import__('src.orchestrator.approval_gate',
                                           fromlist=['ApprovalConfig']).ApprovalConfig()
    )

    # Scheduling
    daily_review_time: str = Field(
        default="05:00",
        description="Daily review execution time (HH:MM)",
    )
    weekly_review_day: int = Field(
        default=1,  # Monday
        ge=0,
        le=6,
        description="Weekly review day (0=Monday, 6=Sunday)",
    )

    # Performance targets (from SPARC PRD)
    target_brief_generation_minutes: int = Field(
        default=10,
        description="Target time for owner brief generation",
    )
    target_account_analysis_seconds: int = Field(
        default=30,
        description="Target time per account analysis",
    )

    # Logging and audit
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    audit_retention_days: int = Field(
        default=2555,  # 7 years
        description="Audit log retention in days",
    )

    class Config:
        """Pydantic configuration."""
        env_prefix = ""
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"

    @field_validator("zoho_mcp_endpoint")
    @classmethod
    def validate_zoho_endpoint(cls, v: str) -> str:
        """Validate Zoho MCP endpoint."""
        if not v:
            # Try to get from environment
            v = os.environ.get("ZOHO_MCP_ENDPOINT", "")

        if not v:
            logger.warning("zoho_mcp_endpoint_not_configured")

        return v

    @field_validator("daily_review_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Validate time format."""
        try:
            hour, minute = v.split(":")
            hour_int = int(hour)
            minute_int = int(minute)

            if not (0 <= hour_int <= 23 and 0 <= minute_int <= 59):
                raise ValueError("Invalid time range")

            return v
        except Exception:
            raise ValueError(f"Invalid time format: {v}. Expected HH:MM")

    def get_mcp_servers(self) -> List[MCPServerConfig]:
        """Get configured MCP servers.

        Returns:
            List of MCP server configurations
        """
        servers = []

        # Zoho CRM MCP
        if self.zoho_mcp_endpoint:
            servers.append(MCPServerConfig(
                name="zoho-crm",
                protocol=MCPProtocol.REMOTE,
                endpoint=self.zoho_mcp_endpoint,
            ))

        # Cognee MCP
        servers.append(MCPServerConfig(
            name="cognee",
            protocol=MCPProtocol.STDIO,
            command=self.cognee_mcp_command,
        ))

        return servers

    def get_hook_functions(self) -> Dict[str, Callable]:
        """Get registered hook functions.

        In production, these would be actual function references.
        For now, returns placeholders.

        Returns:
            Dictionary mapping hook names to functions
        """
        hooks = {}

        if self.hooks_config.pre_tool_enabled:
            hooks["pre_tool"] = self._log_tool_invocation

        if self.hooks_config.post_tool_enabled:
            hooks["post_tool"] = self._record_tool_result

        if self.hooks_config.session_end_enabled:
            hooks["session_end"] = self._export_audit_trail

        return hooks

    def _log_tool_invocation(self, tool_name: str, params: Dict[str, Any]) -> None:
        """Hook: Log tool invocation."""
        logger.info(
            "tool_invoked",
            tool=tool_name,
            params=params,
        )

    def _record_tool_result(
        self,
        tool_name: str,
        result: Any,
        duration: float,
    ) -> None:
        """Hook: Record tool result."""
        logger.info(
            "tool_completed",
            tool=tool_name,
            duration_seconds=duration,
        )

    def _export_audit_trail(self, session_data: Dict[str, Any]) -> None:
        """Hook: Export audit trail."""
        logger.info(
            "session_ended",
            session_id=session_data.get("session_id"),
        )

    @classmethod
    def from_env(cls) -> "OrchestratorConfig":
        """Create configuration from environment variables.

        Returns:
            Orchestrator configuration
        """
        return cls()

    def to_claude_agent_options(self) -> Dict[str, Any]:
        """Convert to Claude Agent SDK options format.

        This would create ClaudeAgentOptions in production.

        Returns:
            Configuration dictionary
        """
        return {
            "system_prompt": self.system_prompt,
            "allowed_tools": self.allowed_tools,
            "disallowed_tools": self.disallowed_tools,
            "permission_mode": self.permission_mode.value,
            "setting_sources": self.setting_sources,
            "mcp_servers": [s.dict() for s in self.get_mcp_servers()],
            "hooks": self.get_hook_functions(),
        }

    def validate_configuration(self) -> bool:
        """Validate configuration completeness.

        Returns:
            True if configuration is valid
        """
        errors = []

        # Check critical settings
        if not self.zoho_mcp_endpoint:
            errors.append("ZOHO_MCP_ENDPOINT not configured")

        if self.max_concurrent_subagents < 1:
            errors.append("max_concurrent_subagents must be >= 1")

        if errors:
            logger.error("configuration_validation_failed", errors=errors)
            return False

        logger.info("configuration_validated")
        return True

    def get_summary(self) -> Dict[str, Any]:
        """Get configuration summary.

        Returns:
            Configuration summary
        """
        return {
            "permission_mode": self.permission_mode.value,
            "max_concurrent_subagents": self.max_concurrent_subagents,
            "circuit_breaker_threshold": self.circuit_breaker_threshold,
            "mcp_servers": [s.name for s in self.get_mcp_servers()],
            "allowed_tools_count": len(self.allowed_tools),
            "disallowed_tools_count": len(self.disallowed_tools),
            "hooks_enabled": {
                "pre_tool": self.hooks_config.pre_tool_enabled,
                "post_tool": self.hooks_config.post_tool_enabled,
                "session_end": self.hooks_config.session_end_enabled,
            },
        }
