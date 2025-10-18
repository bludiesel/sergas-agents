"""Tier configuration models for three-tier Zoho integration strategy.

This module defines configuration for:
- Tier 1: MCP Endpoint (agent operations with tool permissions)
- Tier 2: Python SDK (bulk operations)
- Tier 3: REST API (emergency fallback)
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class TierConfig:
    """Configuration for a single integration tier.

    Attributes:
        name: Tier name for logging and identification
        enabled: Whether this tier is enabled
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts on failure
        priority: Priority level (1=highest, 3=lowest)
        health_check_interval: Seconds between health checks
    """

    name: str
    enabled: bool = True
    timeout: int = 30
    max_retries: int = 3
    priority: int = 1
    health_check_interval: int = 60

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.timeout <= 0:
            raise ValueError(f"Timeout must be positive, got {self.timeout}")
        if self.max_retries < 0:
            raise ValueError(f"Max retries must be non-negative, got {self.max_retries}")
        if self.priority not in (1, 2, 3):
            raise ValueError(f"Priority must be 1-3, got {self.priority}")
        if self.health_check_interval <= 0:
            raise ValueError(f"Health check interval must be positive, got {self.health_check_interval}")


@dataclass
class IntegrationConfig:
    """Complete three-tier integration configuration.

    Defines configuration for all three tiers and circuit breaker settings.

    Attributes:
        tier1_mcp: MCP endpoint configuration
        tier2_sdk: Python SDK configuration
        tier3_rest: REST API configuration
        circuit_breaker_threshold: Failures before circuit opens
        circuit_breaker_timeout: Seconds to wait before retry
        enable_metrics: Whether to collect metrics
        enable_failover: Whether to enable automatic failover
    """

    # Tier configurations
    tier1_mcp: TierConfig = field(default_factory=lambda: TierConfig(
        name="MCP",
        enabled=True,
        timeout=30,
        max_retries=3,
        priority=1,  # Highest priority for agent operations
        health_check_interval=60,
    ))

    tier2_sdk: TierConfig = field(default_factory=lambda: TierConfig(
        name="SDK",
        enabled=True,
        timeout=60,  # Longer timeout for bulk operations
        max_retries=3,
        priority=2,  # Secondary priority
        health_check_interval=60,
    ))

    tier3_rest: TierConfig = field(default_factory=lambda: TierConfig(
        name="REST",
        enabled=True,
        timeout=45,
        max_retries=2,  # Fewer retries for fallback
        priority=3,  # Lowest priority (fallback only)
        health_check_interval=120,
    ))

    # Circuit breaker settings
    circuit_breaker_threshold: int = 5  # Open circuit after 5 failures
    circuit_breaker_timeout: int = 60  # Wait 60s before retry

    # Feature flags
    enable_metrics: bool = True
    enable_failover: bool = True

    def __post_init__(self) -> None:
        """Validate integration configuration."""
        if self.circuit_breaker_threshold <= 0:
            raise ValueError(f"Circuit breaker threshold must be positive, got {self.circuit_breaker_threshold}")
        if self.circuit_breaker_timeout <= 0:
            raise ValueError(f"Circuit breaker timeout must be positive, got {self.circuit_breaker_timeout}")

        # Ensure at least one tier is enabled
        if not any([self.tier1_mcp.enabled, self.tier2_sdk.enabled, self.tier3_rest.enabled]):
            raise ValueError("At least one tier must be enabled")

    def get_enabled_tiers(self) -> list[TierConfig]:
        """Get list of enabled tiers sorted by priority.

        Returns:
            List of enabled tier configurations, highest priority first
        """
        tiers = []
        if self.tier1_mcp.enabled:
            tiers.append(self.tier1_mcp)
        if self.tier2_sdk.enabled:
            tiers.append(self.tier2_sdk)
        if self.tier3_rest.enabled:
            tiers.append(self.tier3_rest)

        # Sort by priority (1=highest)
        return sorted(tiers, key=lambda t: t.priority)

    def get_tier_by_name(self, name: str) -> TierConfig | None:
        """Get tier configuration by name.

        Args:
            name: Tier name (MCP, SDK, or REST)

        Returns:
            Tier configuration or None if not found
        """
        tier_map = {
            "MCP": self.tier1_mcp,
            "SDK": self.tier2_sdk,
            "REST": self.tier3_rest,
        }
        return tier_map.get(name.upper())


@dataclass
class RoutingContext:
    """Context for routing decisions.

    Contains information to help integration manager choose the right tier.

    Attributes:
        operation_type: Type of operation (read, write, search, bulk_read, bulk_write)
        agent_context: Whether this is an agent operation requiring tool permissions
        record_count: Number of records involved (for bulk operations)
        requires_realtime: Whether real-time data is required
        timeout_override: Optional timeout override in seconds
        preferred_tier: Optional tier to prefer if available
    """

    operation_type: Literal["read", "write", "search", "bulk_read", "bulk_write"]
    agent_context: bool = False
    record_count: int = 1
    requires_realtime: bool = False
    timeout_override: int | None = None
    preferred_tier: str | None = None

    def should_use_tier1(self) -> bool:
        """Determine if Tier 1 (MCP) should be used.

        Returns:
            True if MCP tier is recommended
        """
        # Use MCP for agent operations or real-time requirements
        return self.agent_context or self.requires_realtime

    def should_use_tier2(self) -> bool:
        """Determine if Tier 2 (SDK) should be used.

        Returns:
            True if SDK tier is recommended
        """
        # Use SDK for bulk operations (10+ records)
        return self.record_count >= 10 or self.operation_type in ("bulk_read", "bulk_write")

    def get_recommended_tier(self) -> str:
        """Get recommended tier based on context.

        Returns:
            Recommended tier name (MCP, SDK, or REST)
        """
        if self.preferred_tier:
            return self.preferred_tier.upper()

        if self.should_use_tier1():
            return "MCP"
        elif self.should_use_tier2():
            return "SDK"
        else:
            return "MCP"  # Default to MCP for single operations
