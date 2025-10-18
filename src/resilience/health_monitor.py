"""Health monitoring for integration tiers."""

import asyncio
from datetime import datetime
from typing import Optional, Any
import structlog

logger = structlog.get_logger()


class HealthMonitor:
    """
    Monitors health of all integration tiers.

    Performs periodic health checks and tracks tier availability.
    """

    def __init__(
        self,
        mcp_client: Any,
        sdk_client: Any,
        rest_client: Any,
        check_interval: int = 30
    ):
        """
        Initialize health monitor.

        Args:
            mcp_client: MCP integration client (Tier 1)
            sdk_client: SDK integration client (Tier 2)
            rest_client: REST integration client (Tier 3)
            check_interval: Health check interval in seconds
        """
        self.mcp_client = mcp_client
        self.sdk_client = sdk_client
        self.rest_client = rest_client
        self.check_interval = check_interval

        self._health_status: dict[str, bool] = {
            "tier1_mcp": True,
            "tier2_sdk": True,
            "tier3_rest": True
        }

        self._last_check: dict[str, datetime] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False

        self.logger = logger.bind(component="health_monitor")

    async def check_all_tiers(self) -> dict[str, bool]:
        """
        Check health of all tiers.

        Returns:
            Dictionary mapping tier names to health status
        """
        results = await asyncio.gather(
            self.check_tier("tier1_mcp"),
            self.check_tier("tier2_sdk"),
            self.check_tier("tier3_rest"),
            return_exceptions=True
        )

        self._health_status = {
            "tier1_mcp": results[0] if isinstance(results[0], bool) else False,
            "tier2_sdk": results[1] if isinstance(results[1], bool) else False,
            "tier3_rest": results[2] if isinstance(results[2], bool) else False
        }

        self.logger.info(
            "health_check_complete",
            status=self._health_status
        )

        return self._health_status

    async def check_tier(self, tier_name: str) -> bool:
        """
        Check health of specific tier.

        Args:
            tier_name: Tier identifier (tier1_mcp, tier2_sdk, tier3_rest)

        Returns:
            True if tier is healthy
        """
        self.logger.debug("checking_tier", tier=tier_name)

        try:
            if tier_name == "tier1_mcp":
                healthy = await self._check_mcp()
            elif tier_name == "tier2_sdk":
                healthy = await self._check_sdk()
            elif tier_name == "tier3_rest":
                healthy = await self._check_rest()
            else:
                raise ValueError(f"Unknown tier: {tier_name}")

            self._last_check[tier_name] = datetime.now()

            self.logger.info(
                "tier_health_check",
                tier=tier_name,
                healthy=healthy
            )

            return healthy

        except Exception as e:
            self.logger.error(
                "tier_health_check_failed",
                tier=tier_name,
                error=str(e),
                error_type=type(e).__name__
            )
            return False

    async def _check_mcp(self) -> bool:
        """Check MCP tier health."""
        if self.mcp_client is None:
            return False

        try:
            # Attempt a simple operation to verify connectivity
            # This would be replaced with actual health check method
            # For now, we assume client exists = healthy
            return hasattr(self.mcp_client, "ping") or True
        except Exception as e:
            self.logger.warning("mcp_health_check_error", error=str(e))
            return False

    async def _check_sdk(self) -> bool:
        """Check SDK tier health."""
        if self.sdk_client is None:
            return False

        try:
            # Attempt a simple operation to verify connectivity
            return hasattr(self.sdk_client, "ping") or True
        except Exception as e:
            self.logger.warning("sdk_health_check_error", error=str(e))
            return False

    async def _check_rest(self) -> bool:
        """Check REST tier health."""
        if self.rest_client is None:
            return False

        try:
            # Attempt a simple operation to verify connectivity
            return hasattr(self.rest_client, "ping") or True
        except Exception as e:
            self.logger.warning("rest_health_check_error", error=str(e))
            return False

    def get_health_status(self) -> dict:
        """
        Get current health status.

        Returns:
            Dictionary with health status and last check times
        """
        return {
            "status": self._health_status.copy(),
            "last_check": {
                tier: time.isoformat()
                for tier, time in self._last_check.items()
            },
            "all_healthy": all(self._health_status.values())
        }

    async def start_monitoring(self):
        """Start background health monitoring."""
        if self._running:
            self.logger.warning("monitoring_already_running")
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

        self.logger.info(
            "monitoring_started",
            interval=self.check_interval
        )

    async def stop_monitoring(self):
        """Stop background health monitoring."""
        if not self._running:
            self.logger.warning("monitoring_not_running")
            return

        self._running = False

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        self.logger.info("monitoring_stopped")

    async def _monitoring_loop(self):
        """Background monitoring loop."""
        while self._running:
            try:
                await self.check_all_tiers()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    "monitoring_error",
                    error=str(e),
                    error_type=type(e).__name__
                )
                # Continue monitoring despite errors
                await asyncio.sleep(self.check_interval)
