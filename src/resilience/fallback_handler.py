"""Fallback handler for tier-based fallback with circuit breaker integration."""

from typing import Callable, Any, Optional
import structlog
from .circuit_breaker_manager import CircuitBreakerManager
from .circuit_breaker import CircuitState
from .exceptions import AllTiersFailedError, CircuitBreakerOpenError

logger = structlog.get_logger()


class FallbackHandler:
    """
    Handles tier fallback logic with circuit breaker integration.

    Automatically falls back to lower tiers when higher tiers fail
    or their circuit breakers are open.
    """

    def __init__(
        self,
        circuit_breaker_manager: CircuitBreakerManager
    ):
        """
        Initialize fallback handler.

        Args:
            circuit_breaker_manager: Circuit breaker manager instance
        """
        self.cb_manager = circuit_breaker_manager
        self.logger = logger.bind(component="fallback_handler")

    async def execute_with_fallback(
        self,
        primary: Callable,
        secondary: Callable,
        tertiary: Callable,
        operation_name: str,
        primary_tier: str = "tier1_mcp",
        secondary_tier: str = "tier2_sdk",
        tertiary_tier: str = "tier3_rest"
    ) -> Any:
        """
        Execute with automatic tier fallback.

        Order: primary → secondary → tertiary

        Uses circuit breakers to skip unhealthy tiers.

        Args:
            primary: Primary tier function (Tier 1 - MCP)
            secondary: Secondary tier function (Tier 2 - SDK)
            tertiary: Tertiary tier function (Tier 3 - REST)
            operation_name: Name of the operation for logging
            primary_tier: Circuit breaker name for primary tier
            secondary_tier: Circuit breaker name for secondary tier
            tertiary_tier: Circuit breaker name for tertiary tier

        Returns:
            Result from first successful tier

        Raises:
            AllTiersFailedError: When all tiers have failed
        """
        tiers = [
            (primary, primary_tier, "primary"),
            (secondary, secondary_tier, "secondary"),
            (tertiary, tertiary_tier, "tertiary")
        ]

        attempted_tiers = []
        errors = []

        for tier_func, tier_name, tier_label in tiers:
            # Check if tier should be skipped
            if self._should_skip_tier(tier_name):
                self.logger.info(
                    "tier_skipped",
                    operation=operation_name,
                    tier=tier_label,
                    reason="circuit_open"
                )
                attempted_tiers.append(tier_label)
                continue

            try:
                self.logger.debug(
                    "tier_attempt",
                    operation=operation_name,
                    tier=tier_label
                )

                result = await tier_func()

                self.logger.info(
                    "tier_success",
                    operation=operation_name,
                    tier=tier_label
                )

                return result

            except CircuitBreakerOpenError as e:
                self.logger.warning(
                    "tier_circuit_open",
                    operation=operation_name,
                    tier=tier_label,
                    retry_after=e.retry_after
                )
                attempted_tiers.append(tier_label)
                errors.append(str(e))

            except Exception as e:
                self.logger.warning(
                    "tier_failed",
                    operation=operation_name,
                    tier=tier_label,
                    error=str(e),
                    error_type=type(e).__name__
                )
                attempted_tiers.append(tier_label)
                errors.append(str(e))

        # All tiers failed
        self.logger.error(
            "all_tiers_failed",
            operation=operation_name,
            attempted_tiers=attempted_tiers,
            errors=errors
        )

        raise AllTiersFailedError(attempted_tiers)

    def _should_skip_tier(self, tier_name: str) -> bool:
        """
        Check if tier should be skipped based on circuit state.

        Args:
            tier_name: Circuit breaker name

        Returns:
            True if tier should be skipped
        """
        try:
            breaker = self.cb_manager.get_breaker(tier_name)
            state = breaker.get_state()

            # Skip if circuit is open
            return state == CircuitState.OPEN

        except KeyError:
            # Circuit breaker not registered, don't skip
            self.logger.debug(
                "circuit_not_registered",
                tier=tier_name
            )
            return False

    async def execute_with_custom_fallback(
        self,
        operations: list[tuple[Callable, str, str]],
        operation_name: str
    ) -> Any:
        """
        Execute with custom tier fallback sequence.

        Args:
            operations: List of (function, tier_name, tier_label) tuples
            operation_name: Name of the operation for logging

        Returns:
            Result from first successful operation

        Raises:
            AllTiersFailedError: When all operations have failed
        """
        attempted = []
        errors = []

        for func, tier_name, tier_label in operations:
            if self._should_skip_tier(tier_name):
                self.logger.info(
                    "operation_skipped",
                    operation=operation_name,
                    tier=tier_label,
                    reason="circuit_open"
                )
                attempted.append(tier_label)
                continue

            try:
                self.logger.debug(
                    "operation_attempt",
                    operation=operation_name,
                    tier=tier_label
                )

                result = await func()

                self.logger.info(
                    "operation_success",
                    operation=operation_name,
                    tier=tier_label
                )

                return result

            except CircuitBreakerOpenError as e:
                self.logger.warning(
                    "operation_circuit_open",
                    operation=operation_name,
                    tier=tier_label,
                    retry_after=e.retry_after
                )
                attempted.append(tier_label)
                errors.append(str(e))

            except Exception as e:
                self.logger.warning(
                    "operation_failed",
                    operation=operation_name,
                    tier=tier_label,
                    error=str(e),
                    error_type=type(e).__name__
                )
                attempted.append(tier_label)
                errors.append(str(e))

        self.logger.error(
            "all_operations_failed",
            operation=operation_name,
            attempted=attempted,
            errors=errors
        )

        raise AllTiersFailedError(attempted)
