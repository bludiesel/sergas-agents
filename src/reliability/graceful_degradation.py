"""
Graceful degradation system for handling partial failures.

Provides fallback strategies, feature flags, circuit breaker enhancements,
and partial failure handling to maintain service availability.
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, TypeVar, Generic
from dataclasses import dataclass, field
import structlog
import json
from pathlib import Path

logger = structlog.get_logger()

T = TypeVar('T')


class DegradationLevel(Enum):
    """Service degradation levels."""
    FULL = "full"              # Full functionality
    DEGRADED = "degraded"      # Reduced functionality
    MINIMAL = "minimal"        # Minimal functionality
    MAINTENANCE = "maintenance"  # Maintenance mode


@dataclass
class FeatureFlag:
    """Feature flag configuration."""
    name: str
    enabled: bool
    description: str = ""
    rollout_percentage: float = 100.0
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "description": self.description,
            "rollout_percentage": self.rollout_percentage,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class FeatureFlags:
    """
    Feature flag management system.

    Enables/disables features dynamically for graceful degradation.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize feature flags.

        Args:
            config_path: Optional path to feature flag configuration file
        """
        self.flags: Dict[str, FeatureFlag] = {}
        self.config_path = config_path
        self.logger = logger.bind(component="feature_flags")

        if config_path and config_path.exists():
            self._load_from_file()

    def register(
        self,
        name: str,
        enabled: bool = True,
        description: str = "",
        rollout_percentage: float = 100.0,
        dependencies: Optional[List[str]] = None
    ):
        """
        Register a feature flag.

        Args:
            name: Feature name
            enabled: Initial state
            description: Feature description
            rollout_percentage: Percentage of users to enable for (0-100)
            dependencies: List of dependent feature flags
        """
        flag = FeatureFlag(
            name=name,
            enabled=enabled,
            description=description,
            rollout_percentage=rollout_percentage,
            dependencies=dependencies or []
        )
        self.flags[name] = flag

        self.logger.info(
            "feature_flag_registered",
            name=name,
            enabled=enabled,
            rollout_percentage=rollout_percentage
        )

    def is_enabled(self, name: str, user_id: Optional[str] = None) -> bool:
        """
        Check if feature is enabled.

        Args:
            name: Feature name
            user_id: Optional user ID for rollout percentage

        Returns:
            True if feature is enabled
        """
        flag = self.flags.get(name)
        if not flag:
            self.logger.warning("feature_flag_not_found", name=name)
            return False

        # Check base enabled state
        if not flag.enabled:
            return False

        # Check dependencies
        for dep in flag.dependencies:
            if not self.is_enabled(dep, user_id):
                self.logger.debug(
                    "feature_disabled_by_dependency",
                    name=name,
                    dependency=dep
                )
                return False

        # Check rollout percentage
        if flag.rollout_percentage < 100.0 and user_id:
            # Use hash of user_id for consistent rollout
            user_hash = hash(user_id) % 100
            if user_hash >= flag.rollout_percentage:
                return False

        return True

    def enable(self, name: str):
        """Enable a feature flag."""
        if name in self.flags:
            self.flags[name].enabled = True
            self.flags[name].updated_at = datetime.now()
            self.logger.info("feature_flag_enabled", name=name)

            if self.config_path:
                self._save_to_file()

    def disable(self, name: str):
        """Disable a feature flag."""
        if name in self.flags:
            self.flags[name].enabled = False
            self.flags[name].updated_at = datetime.now()
            self.logger.info("feature_flag_disabled", name=name)

            if self.config_path:
                self._save_to_file()

    def set_rollout_percentage(self, name: str, percentage: float):
        """
        Set rollout percentage for gradual feature rollout.

        Args:
            name: Feature name
            percentage: Rollout percentage (0-100)
        """
        if name in self.flags:
            self.flags[name].rollout_percentage = max(0.0, min(100.0, percentage))
            self.flags[name].updated_at = datetime.now()

            self.logger.info(
                "feature_rollout_updated",
                name=name,
                percentage=percentage
            )

            if self.config_path:
                self._save_to_file()

    def get_all(self) -> Dict[str, FeatureFlag]:
        """Get all feature flags."""
        return self.flags.copy()

    def _load_from_file(self):
        """Load feature flags from configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)

            for flag_data in data.get("flags", []):
                flag = FeatureFlag(
                    name=flag_data["name"],
                    enabled=flag_data["enabled"],
                    description=flag_data.get("description", ""),
                    rollout_percentage=flag_data.get("rollout_percentage", 100.0),
                    dependencies=flag_data.get("dependencies", []),
                    metadata=flag_data.get("metadata", {}),
                    created_at=datetime.fromisoformat(flag_data.get("created_at", datetime.now().isoformat())),
                    updated_at=datetime.fromisoformat(flag_data.get("updated_at", datetime.now().isoformat()))
                )
                self.flags[flag.name] = flag

            self.logger.info("feature_flags_loaded", count=len(self.flags))

        except Exception as e:
            self.logger.error("feature_flags_load_failed", error=str(e))

    def _save_to_file(self):
        """Save feature flags to configuration file."""
        try:
            data = {
                "flags": [flag.to_dict() for flag in self.flags.values()]
            }

            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)

            self.logger.debug("feature_flags_saved")

        except Exception as e:
            self.logger.error("feature_flags_save_failed", error=str(e))


class FallbackStrategy(ABC, Generic[T]):
    """Base class for fallback strategies."""

    def __init__(self, name: str):
        """
        Initialize fallback strategy.

        Args:
            name: Strategy identifier
        """
        self.name = name
        self.logger = logger.bind(fallback_strategy=name)

    @abstractmethod
    async def execute(self, *args, **kwargs) -> T:
        """
        Execute fallback strategy.

        Returns:
            Fallback result
        """
        pass


class CachedFallback(FallbackStrategy[T]):
    """Fallback to cached data."""

    def __init__(self, name: str, cache_ttl: int = 300):
        """
        Initialize cached fallback.

        Args:
            name: Strategy name
            cache_ttl: Cache time-to-live in seconds
        """
        super().__init__(name)
        self.cache: Dict[str, tuple[T, datetime]] = {}
        self.cache_ttl = cache_ttl

    def cache_result(self, key: str, result: T):
        """
        Cache a result.

        Args:
            key: Cache key
            result: Result to cache
        """
        self.cache[key] = (result, datetime.now())
        self.logger.debug("result_cached", key=key)

    async def execute(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """
        Get cached result or default.

        Args:
            key: Cache key
            default: Default value if not cached

        Returns:
            Cached result or default
        """
        if key in self.cache:
            result, cached_at = self.cache[key]
            age = (datetime.now() - cached_at).total_seconds()

            if age < self.cache_ttl:
                self.logger.info("cache_hit", key=key, age_seconds=age)
                return result
            else:
                # Cache expired
                del self.cache[key]
                self.logger.debug("cache_expired", key=key)

        self.logger.info("cache_miss", key=key)
        return default


class StaticFallback(FallbackStrategy[T]):
    """Fallback to static data."""

    def __init__(self, name: str, fallback_data: T):
        """
        Initialize static fallback.

        Args:
            name: Strategy name
            fallback_data: Static fallback data
        """
        super().__init__(name)
        self.fallback_data = fallback_data

    async def execute(self) -> T:
        """
        Return static fallback data.

        Returns:
            Static fallback data
        """
        self.logger.info("static_fallback_used")
        return self.fallback_data


class ServiceFallback(FallbackStrategy[T]):
    """Fallback to alternative service."""

    def __init__(
        self,
        name: str,
        primary_func: Callable,
        fallback_func: Callable
    ):
        """
        Initialize service fallback.

        Args:
            name: Strategy name
            primary_func: Primary service function
            fallback_func: Fallback service function
        """
        super().__init__(name)
        self.primary_func = primary_func
        self.fallback_func = fallback_func

    async def execute(self, *args, **kwargs) -> T:
        """
        Try primary service, fallback on failure.

        Returns:
            Result from primary or fallback service
        """
        try:
            result = await self.primary_func(*args, **kwargs)
            self.logger.debug("primary_service_success")
            return result
        except Exception as e:
            self.logger.warning(
                "primary_service_failed_using_fallback",
                error=str(e)
            )
            return await self.fallback_func(*args, **kwargs)


class PartialFailureHandler:
    """
    Handles partial failures in multi-step operations.

    Allows operations to continue even if some steps fail.
    """

    def __init__(self, name: str, min_success_rate: float = 0.5):
        """
        Initialize partial failure handler.

        Args:
            name: Handler identifier
            min_success_rate: Minimum success rate to consider operation successful
        """
        self.name = name
        self.min_success_rate = min_success_rate
        self.logger = logger.bind(partial_failure_handler=name)

    async def execute_all(
        self,
        tasks: List[Callable],
        continue_on_failure: bool = True
    ) -> Dict[str, Any]:
        """
        Execute multiple tasks with partial failure handling.

        Args:
            tasks: List of async callable tasks
            continue_on_failure: Continue executing remaining tasks on failure

        Returns:
            Dictionary with results and statistics
        """
        results = []
        failures = []
        start_time = datetime.now()

        for i, task in enumerate(tasks):
            try:
                result = await task()
                results.append({
                    "index": i,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                failure = {
                    "index": i,
                    "status": "failed",
                    "error": str(e),
                    "error_type": type(e).__name__
                }
                failures.append(failure)
                results.append(failure)

                if not continue_on_failure:
                    self.logger.error(
                        "task_failed_stopping",
                        index=i,
                        error=str(e)
                    )
                    break

        execution_time = (datetime.now() - start_time).total_seconds()

        success_count = len([r for r in results if r["status"] == "success"])
        total_count = len(results)
        success_rate = success_count / total_count if total_count > 0 else 0.0

        overall_success = success_rate >= self.min_success_rate

        summary = {
            "overall_success": overall_success,
            "success_count": success_count,
            "failure_count": len(failures),
            "total_count": total_count,
            "success_rate": success_rate,
            "min_success_rate": self.min_success_rate,
            "execution_time_seconds": execution_time,
            "results": results,
            "failures": failures
        }

        self.logger.info(
            "partial_failure_execution_complete",
            overall_success=overall_success,
            success_rate=success_rate,
            failures=len(failures)
        )

        return summary


class DegradationManager:
    """
    Central manager for graceful degradation.

    Coordinates feature flags, fallback strategies, and circuit breakers
    to maintain service availability during failures.
    """

    def __init__(
        self,
        feature_flags: Optional[FeatureFlags] = None,
        circuit_breaker_manager: Optional[Any] = None
    ):
        """
        Initialize degradation manager.

        Args:
            feature_flags: Feature flags instance
            circuit_breaker_manager: Circuit breaker manager instance
        """
        self.feature_flags = feature_flags or FeatureFlags()
        self.circuit_breaker_manager = circuit_breaker_manager
        self.fallback_strategies: Dict[str, FallbackStrategy] = {}
        self.degradation_level = DegradationLevel.FULL
        self.logger = logger.bind(component="degradation_manager")

    def register_fallback(self, name: str, strategy: FallbackStrategy):
        """
        Register a fallback strategy.

        Args:
            name: Strategy identifier
            strategy: Fallback strategy instance
        """
        self.fallback_strategies[name] = strategy
        self.logger.info("fallback_strategy_registered", name=name)

    async def execute_with_fallback(
        self,
        name: str,
        primary_func: Callable,
        fallback_strategy: Optional[str] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with fallback handling.

        Args:
            name: Operation name
            primary_func: Primary function to execute
            fallback_strategy: Name of fallback strategy to use
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result from primary function or fallback
        """
        try:
            # Check if feature is enabled
            if name in self.feature_flags.flags:
                if not self.feature_flags.is_enabled(name):
                    self.logger.info("feature_disabled_using_fallback", name=name)
                    return await self._execute_fallback(fallback_strategy, *args, **kwargs)

            # Execute with circuit breaker if available
            if self.circuit_breaker_manager and name in self.circuit_breaker_manager.breakers:
                result = await self.circuit_breaker_manager.call(
                    name,
                    primary_func,
                    *args,
                    **kwargs
                )
            else:
                result = await primary_func(*args, **kwargs)

            return result

        except Exception as e:
            self.logger.warning(
                "primary_execution_failed",
                name=name,
                error=str(e),
                using_fallback=fallback_strategy is not None
            )

            if fallback_strategy:
                return await self._execute_fallback(fallback_strategy, *args, **kwargs)
            else:
                raise

    async def _execute_fallback(
        self,
        strategy_name: Optional[str],
        *args,
        **kwargs
    ) -> Any:
        """Execute fallback strategy."""
        if not strategy_name or strategy_name not in self.fallback_strategies:
            self.logger.error(
                "fallback_strategy_not_found",
                strategy=strategy_name
            )
            return None

        strategy = self.fallback_strategies[strategy_name]
        return await strategy.execute(*args, **kwargs)

    def set_degradation_level(self, level: DegradationLevel):
        """
        Set system degradation level.

        Args:
            level: Degradation level
        """
        old_level = self.degradation_level
        self.degradation_level = level

        self.logger.warning(
            "degradation_level_changed",
            old_level=old_level.value,
            new_level=level.value
        )

        # Automatically disable features based on level
        if level == DegradationLevel.MINIMAL:
            self._apply_minimal_mode()
        elif level == DegradationLevel.MAINTENANCE:
            self._apply_maintenance_mode()

    def _apply_minimal_mode(self):
        """Apply minimal degradation mode."""
        # Disable non-essential features
        non_essential = [
            "analytics",
            "recommendations",
            "notifications",
            "search_suggestions"
        ]

        for feature in non_essential:
            if feature in self.feature_flags.flags:
                self.feature_flags.disable(feature)

        self.logger.warning("minimal_mode_applied")

    def _apply_maintenance_mode(self):
        """Apply maintenance mode."""
        # Disable all features except health checks
        for feature_name in self.feature_flags.flags.keys():
            if feature_name != "health_checks":
                self.feature_flags.disable(feature_name)

        self.logger.warning("maintenance_mode_applied")

    def get_status(self) -> Dict[str, Any]:
        """
        Get degradation status.

        Returns:
            Status dictionary
        """
        enabled_features = sum(
            1 for flag in self.feature_flags.flags.values() if flag.enabled
        )
        total_features = len(self.feature_flags.flags)

        return {
            "degradation_level": self.degradation_level.value,
            "enabled_features": enabled_features,
            "total_features": total_features,
            "feature_availability": enabled_features / total_features if total_features > 0 else 0.0,
            "registered_fallbacks": len(self.fallback_strategies),
            "timestamp": datetime.now().isoformat()
        }
