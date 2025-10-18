"""Zoho Integration Manager - Intelligent three-tier routing system.

Manages routing across three tiers with automatic failover:
- Tier 1 (MCP): Agent operations with tool permissions
- Tier 2 (SDK): Bulk operations (100+ records/call)
- Tier 3 (REST): Emergency fallback

Features:
- Intelligent routing based on operation type and context
- Automatic failover on tier failure
- Circuit breaker integration for fault tolerance
- Comprehensive metrics collection
- Health monitoring for all tiers
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from enum import Enum
import structlog

from src.integrations.zoho.mcp_client import ZohoMCPClient
from src.integrations.zoho.sdk_client import ZohoSDKClient
from src.integrations.zoho.rest_client import ZohoRESTClient
from src.integrations.zoho.tier_config import (
    IntegrationConfig,
    TierConfig,
    RoutingContext,
)
from src.integrations.zoho.metrics import IntegrationMetrics
from src.integrations.zoho.exceptions import (
    ZohoAPIError,
    ZohoRateLimitError,
    ZohoAuthError,
)
from src.utils.circuit_breaker import CircuitBreaker, CircuitBreakerError

logger = structlog.get_logger(__name__)


class TierName(Enum):
    """Tier identifiers."""
    MCP = "MCP"
    SDK = "SDK"
    REST = "REST"


class ZohoIntegrationManager:
    """Intelligent three-tier integration manager for Zoho CRM.

    Routing Logic:
    - Agent operations (with tool calls) → Tier 1 (MCP)
    - Bulk operations (100+ records) → Tier 2 (SDK)
    - Fallback on failure → Tier 3 (REST)

    Example:
        >>> config = IntegrationConfig()
        >>> manager = ZohoIntegrationManager(
        ...     mcp_client=mcp_client,
        ...     sdk_client=sdk_client,
        ...     rest_client=rest_client,
        ...     config=config
        ... )
        >>> # Agent operation - routes to MCP
        >>> account = await manager.get_account(
        ...     "123456",
        ...     context={"agent_context": True}
        ... )
        >>> # Bulk operation - routes to SDK
        >>> accounts = await manager.bulk_read_accounts(account_ids)
    """

    def __init__(
        self,
        mcp_client: ZohoMCPClient,
        sdk_client: ZohoSDKClient,
        rest_client: ZohoRESTClient,
        config: Optional[IntegrationConfig] = None,
    ) -> None:
        """Initialize integration manager.

        Args:
            mcp_client: Tier 1 MCP endpoint client
            sdk_client: Tier 2 Python SDK client
            rest_client: Tier 3 REST API client
            config: Integration configuration (uses defaults if None)
        """
        self.mcp_client = mcp_client
        self.sdk_client = sdk_client
        self.rest_client = rest_client
        self.config = config or IntegrationConfig()

        # Initialize metrics collector
        self.metrics = IntegrationMetrics()

        # Initialize circuit breakers for each tier
        self.circuit_breakers: Dict[TierName, CircuitBreaker] = {
            TierName.MCP: CircuitBreaker(
                failure_threshold=self.config.circuit_breaker_threshold,
                timeout=self.config.circuit_breaker_timeout,
                name="MCP",
            ),
            TierName.SDK: CircuitBreaker(
                failure_threshold=self.config.circuit_breaker_threshold,
                timeout=self.config.circuit_breaker_timeout,
                name="SDK",
            ),
            TierName.REST: CircuitBreaker(
                failure_threshold=self.config.circuit_breaker_threshold,
                timeout=self.config.circuit_breaker_timeout,
                name="REST",
            ),
        }

        self.logger = logger.bind(component="ZohoIntegrationManager")
        self.logger.info(
            "integration_manager_initialized",
            tiers_enabled=[t.name for t in self.config.get_enabled_tiers()],
        )

    def _select_tier(self, context: RoutingContext) -> TierName:
        """Select appropriate tier based on routing context.

        Args:
            context: Routing context with operation details

        Returns:
            Selected tier name

        Routing Rules:
        - Agent context → MCP (Tier 1)
        - Bulk operations (10+ records) → SDK (Tier 2)
        - Real-time required → MCP (Tier 1)
        - Default → MCP (Tier 1)
        """
        # Check preferred tier first
        if context.preferred_tier:
            tier_name = context.preferred_tier.upper()
            if tier_name == "MCP" and self.config.tier1_mcp.enabled:
                return TierName.MCP
            elif tier_name == "SDK" and self.config.tier2_sdk.enabled:
                return TierName.SDK
            elif tier_name == "REST" and self.config.tier3_rest.enabled:
                return TierName.REST

        # Agent operations always use MCP (if available)
        if context.agent_context and self.config.tier1_mcp.enabled:
            self.logger.debug("tier_selected_agent_context", tier="MCP")
            return TierName.MCP

        # Bulk operations use SDK (if available)
        if context.should_use_tier2() and self.config.tier2_sdk.enabled:
            self.logger.debug("tier_selected_bulk_operation", tier="SDK", record_count=context.record_count)
            return TierName.SDK

        # Real-time operations use MCP (if available)
        if context.requires_realtime and self.config.tier1_mcp.enabled:
            self.logger.debug("tier_selected_realtime", tier="MCP")
            return TierName.MCP

        # Default to MCP for single operations
        if self.config.tier1_mcp.enabled:
            return TierName.MCP

        # Fallback to SDK if MCP not available
        if self.config.tier2_sdk.enabled:
            return TierName.SDK

        # Last resort: REST
        return TierName.REST

    def _get_failover_tiers(self, primary_tier: TierName) -> List[TierName]:
        """Get failover tier sequence.

        Args:
            primary_tier: Primary tier that failed

        Returns:
            List of failover tiers in priority order
        """
        all_tiers = [TierName.MCP, TierName.SDK, TierName.REST]

        # Remove primary tier
        all_tiers.remove(primary_tier)

        # Filter to enabled tiers only
        enabled_tiers = []
        for tier in all_tiers:
            tier_config = self._get_tier_config(tier)
            if tier_config and tier_config.enabled:
                enabled_tiers.append(tier)

        return enabled_tiers

    def _get_tier_config(self, tier: TierName) -> Optional[TierConfig]:
        """Get configuration for specific tier.

        Args:
            tier: Tier name

        Returns:
            Tier configuration or None
        """
        if tier == TierName.MCP:
            return self.config.tier1_mcp
        elif tier == TierName.SDK:
            return self.config.tier2_sdk
        elif tier == TierName.REST:
            return self.config.tier3_rest
        return None

    async def _execute_with_tier(
        self,
        tier: TierName,
        operation: str,
        **kwargs
    ) -> Any:
        """Execute operation with specific tier.

        Args:
            tier: Tier to use
            operation: Operation name (get_account, update_account, etc.)
            **kwargs: Operation arguments

        Returns:
            Operation result

        Raises:
            ZohoAPIError: If operation fails
        """
        start_time = time.time()
        success = False
        error_msg = None

        try:
            # Get tier client and execute
            if tier == TierName.MCP:
                result = await self._execute_mcp(operation, **kwargs)
            elif tier == TierName.SDK:
                result = await self._execute_sdk(operation, **kwargs)
            elif tier == TierName.REST:
                result = await self._execute_rest(operation, **kwargs)
            else:
                raise ValueError(f"Unknown tier: {tier}")

            success = True
            return result

        except Exception as e:
            error_msg = str(e)
            raise

        finally:
            # Record metrics
            duration = time.time() - start_time
            self.metrics.record_request(
                tier=tier.value,
                operation=operation,
                duration=duration,
                success=success,
                error=error_msg,
            )

    async def _execute_mcp(self, operation: str, **kwargs) -> Any:
        """Execute operation via MCP client."""
        if operation == "get_account":
            return await self.mcp_client.get_account(
                kwargs["account_id"],
                tools=kwargs.get("tools"),
            )
        elif operation == "get_accounts":
            return await self.mcp_client.get_accounts(
                filters=kwargs.get("filters"),
                limit=kwargs.get("limit", 100),
                tools=kwargs.get("tools"),
            )
        elif operation == "update_account":
            return await self.mcp_client.update_account(
                kwargs["account_id"],
                kwargs["data"],
                tools=kwargs.get("tools"),
            )
        elif operation == "search_accounts":
            return await self.mcp_client.search_accounts(
                kwargs["criteria"],
                tools=kwargs.get("tools"),
                limit=kwargs.get("limit", 100),
            )
        else:
            raise ValueError(f"Operation {operation} not supported by MCP client")

    def _execute_sdk(self, operation: str, **kwargs) -> Any:
        """Execute operation via SDK client (sync)."""
        if operation == "get_account":
            return self.sdk_client.get_account(kwargs["account_id"])
        elif operation == "get_accounts":
            return self.sdk_client.get_accounts(
                limit=kwargs.get("limit", 100),
                fields=kwargs.get("fields"),
            )
        elif operation == "update_account":
            return self.sdk_client.update_account(
                kwargs["account_id"],
                kwargs["data"],
            )
        elif operation == "search_accounts":
            return self.sdk_client.search_accounts(
                kwargs["criteria"],
                limit=kwargs.get("limit", 100),
            )
        elif operation == "bulk_read_accounts":
            return self.sdk_client.bulk_read_accounts(
                criteria=kwargs.get("criteria"),
                fields=kwargs.get("fields"),
            )
        elif operation == "bulk_update_accounts":
            return self.sdk_client.bulk_update_accounts(kwargs["records"])
        else:
            raise ValueError(f"Operation {operation} not supported by SDK client")

    async def _execute_rest(self, operation: str, **kwargs) -> Any:
        """Execute operation via REST client."""
        if operation == "get_account":
            return await self.rest_client.get_account(kwargs["account_id"])
        elif operation == "get_accounts":
            return await self.rest_client.get_accounts(
                filters=kwargs.get("filters"),
                limit=kwargs.get("limit", 100),
            )
        elif operation == "update_account":
            return await self.rest_client.update_account(
                kwargs["account_id"],
                kwargs["data"],
            )
        elif operation == "search_accounts":
            return await self.rest_client.search_accounts(
                kwargs["criteria"],
                limit=kwargs.get("limit", 100),
            )
        elif operation == "bulk_read_accounts":
            return await self.rest_client.bulk_read_accounts(kwargs["account_ids"])
        elif operation == "bulk_update_accounts":
            return await self.rest_client.bulk_update_accounts(kwargs["updates"])
        else:
            raise ValueError(f"Operation {operation} not supported by REST client")

    async def _execute_with_failover(
        self,
        operation: str,
        context: RoutingContext,
        **kwargs
    ) -> Any:
        """Execute operation with automatic failover.

        Args:
            operation: Operation name
            context: Routing context
            **kwargs: Operation arguments

        Returns:
            Operation result

        Raises:
            ZohoAPIError: If all tiers fail
        """
        # Select primary tier
        primary_tier = self._select_tier(context)

        # Try primary tier with circuit breaker
        try:
            self.logger.info(
                "executing_operation",
                operation=operation,
                tier=primary_tier.value,
                context=context.operation_type,
            )

            circuit_breaker = self.circuit_breakers[primary_tier]
            result = circuit_breaker.call(
                self._execute_with_tier,
                primary_tier,
                operation,
                **kwargs
            )

            # Handle async result if needed
            if asyncio.iscoroutine(result):
                result = await result

            self.logger.info(
                "operation_succeeded",
                operation=operation,
                tier=primary_tier.value,
            )
            return result

        except (CircuitBreakerError, ZohoAPIError, ZohoRateLimitError, ZohoAuthError) as e:
            self.logger.warning(
                "tier_failed_attempting_failover",
                operation=operation,
                tier=primary_tier.value,
                error=str(e),
            )

            # Try failover tiers if enabled
            if not self.config.enable_failover:
                raise

            failover_tiers = self._get_failover_tiers(primary_tier)

            for failover_tier in failover_tiers:
                try:
                    self.logger.info(
                        "attempting_failover",
                        operation=operation,
                        from_tier=primary_tier.value,
                        to_tier=failover_tier.value,
                    )

                    circuit_breaker = self.circuit_breakers[failover_tier]
                    result = circuit_breaker.call(
                        self._execute_with_tier,
                        failover_tier,
                        operation,
                        **kwargs
                    )

                    if asyncio.iscoroutine(result):
                        result = await result

                    self.logger.info(
                        "failover_succeeded",
                        operation=operation,
                        tier=failover_tier.value,
                    )
                    return result

                except Exception as failover_error:
                    self.logger.warning(
                        "failover_tier_failed",
                        tier=failover_tier.value,
                        error=str(failover_error),
                    )
                    continue

            # All tiers failed
            self.logger.error(
                "all_tiers_failed",
                operation=operation,
                primary_tier=primary_tier.value,
            )
            raise ZohoAPIError(
                f"Operation {operation} failed on all tiers",
                details={
                    "primary_tier": primary_tier.value,
                    "failover_attempts": len(failover_tiers),
                }
            )

    # Public API methods

    async def get_account(
        self,
        account_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Get single account with intelligent tier routing.

        Args:
            account_id: Zoho account ID
            context: Routing context (optional)

        Returns:
            Account data

        Raises:
            ZohoAPIError: If operation fails on all tiers
        """
        routing_context = RoutingContext(
            operation_type="read",
            agent_context=context.get("agent_context", False) if context else False,
            requires_realtime=context.get("requires_realtime", False) if context else False,
        )

        return await self._execute_with_failover(
            "get_account",
            routing_context,
            account_id=account_id,
            tools=context.get("tools") if context else None,
        )

    async def get_accounts(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Get multiple accounts with tier selection based on limit.

        Args:
            filters: Query filters
            limit: Maximum results
            context: Routing context

        Returns:
            List of account records

        Raises:
            ZohoAPIError: If operation fails on all tiers
        """
        routing_context = RoutingContext(
            operation_type="read",
            agent_context=context.get("agent_context", False) if context else False,
            record_count=limit,
        )

        return await self._execute_with_failover(
            "get_accounts",
            routing_context,
            filters=filters,
            limit=limit,
            tools=context.get("tools") if context else None,
        )

    async def update_account(
        self,
        account_id: str,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update account with tier routing.

        Args:
            account_id: Zoho account ID
            data: Fields to update
            context: Routing context

        Returns:
            Updated account data

        Raises:
            ZohoAPIError: If operation fails on all tiers
        """
        routing_context = RoutingContext(
            operation_type="write",
            agent_context=context.get("agent_context", False) if context else False,
        )

        return await self._execute_with_failover(
            "update_account",
            routing_context,
            account_id=account_id,
            data=data,
            tools=context.get("tools") if context else None,
        )

    async def bulk_read_accounts(
        self,
        account_ids: Optional[List[str]] = None,
        criteria: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Bulk read - always use Tier 2 (SDK) for performance.

        Args:
            account_ids: List of account IDs (for REST fallback)
            criteria: COQL criteria (for SDK)

        Returns:
            List of account records

        Raises:
            ZohoAPIError: If operation fails
        """
        record_count = len(account_ids) if account_ids else 100

        routing_context = RoutingContext(
            operation_type="bulk_read",
            record_count=record_count,
            preferred_tier="SDK",  # Always prefer SDK for bulk
        )

        return await self._execute_with_failover(
            "bulk_read_accounts",
            routing_context,
            account_ids=account_ids,
            criteria=criteria,
        )

    async def bulk_update_accounts(
        self,
        updates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Bulk update - always use Tier 2 (SDK) for performance.

        Args:
            updates: List of account updates

        Returns:
            Bulk operation result

        Raises:
            ZohoAPIError: If operation fails
        """
        routing_context = RoutingContext(
            operation_type="bulk_write",
            record_count=len(updates),
            preferred_tier="SDK",
        )

        return await self._execute_with_failover(
            "bulk_update_accounts",
            routing_context,
            records=updates,
            updates=updates,
        )

    async def search_accounts(
        self,
        criteria: str,
        limit: int = 100,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search accounts with intelligent routing.

        Args:
            criteria: Search criteria (COQL format)
            limit: Maximum results
            context: Routing context

        Returns:
            List of matching accounts

        Raises:
            ZohoAPIError: If operation fails
        """
        routing_context = RoutingContext(
            operation_type="search",
            agent_context=context.get("agent_context", False) if context else False,
            record_count=limit,
        )

        return await self._execute_with_failover(
            "search_accounts",
            routing_context,
            criteria=criteria,
            limit=limit,
            tools=context.get("tools") if context else None,
        )

    def get_tier_health(self) -> Dict[str, Any]:
        """Get health status of all tiers.

        Returns:
            Health status for each tier
        """
        return {
            "MCP": {
                "enabled": self.config.tier1_mcp.enabled,
                "circuit_breaker": self.circuit_breakers[TierName.MCP].get_status(),
            },
            "SDK": {
                "enabled": self.config.tier2_sdk.enabled,
                "circuit_breaker": self.circuit_breakers[TierName.SDK].get_status(),
            },
            "REST": {
                "enabled": self.config.tier3_rest.enabled,
                "circuit_breaker": self.circuit_breakers[TierName.REST].get_status(),
            },
        }

    def get_tier_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all tiers.

        Returns:
            Comprehensive metrics for all tiers
        """
        return self.metrics.get_overall_stats()

    def reset_circuit_breakers(self) -> None:
        """Reset all circuit breakers."""
        for breaker in self.circuit_breakers.values():
            breaker.reset()
        self.logger.info("circuit_breakers_reset")
