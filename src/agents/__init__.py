"""Agent implementations for the Super Account Manager system.

This module provides all subagent implementations:
- ZohoDataScout: Read-only Zoho CRM data fetching and analysis
- MemoryAnalyst: Historical context retrieval and timeline analysis
- RecommendationAuthor: Actionable recommendation generation

Week 7 Deliverables:
- Complete Zoho Data Scout implementation
- All data models and utilities
- Configuration management
"""

from typing import Optional

# Week 7: Zoho Data Scout implementation
from src.agents.zoho_data_scout import ZohoDataScout
from src.agents.config import DataScoutConfig, ToolPermissions, CacheConfig
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
    RiskLevel,
    FieldChange,
)
from src.agents.utils import (
    calculate_field_diff,
    detect_stalled_deals,
    calculate_inactivity_days,
    assess_account_risk,
    identify_engagement_drop,
    generate_risk_signals,
    aggregate_deal_pipeline,
    summarize_activities,
    calculate_engagement_score,
)

# Future implementations
# from .orchestrator import MainOrchestrator
# from .memory_analyst import MemoryAnalyst
# from .recommendation_author import RecommendationAuthor


def create_data_scout(
    zoho_manager,
    config: Optional[DataScoutConfig] = None,
) -> ZohoDataScout:
    """Factory function to create Zoho Data Scout instance.

    Args:
        zoho_manager: ZohoIntegrationManager instance
        config: Optional configuration (loads from env if None)

    Returns:
        Configured ZohoDataScout instance

    Example:
        >>> from src.integrations.zoho.integration_manager import ZohoIntegrationManager
        >>> from src.agents import create_data_scout
        >>>
        >>> zoho_manager = ZohoIntegrationManager(...)
        >>> data_scout = create_data_scout(zoho_manager)
        >>> snapshot = await data_scout.get_account_snapshot("account_123")
    """
    return ZohoDataScout(
        zoho_manager=zoho_manager,
        config=config or DataScoutConfig.from_env(),
    )


__all__ = [
    # Main subagent
    "ZohoDataScout",
    # Factory functions
    "create_data_scout",
    # Configuration
    "DataScoutConfig",
    "ToolPermissions",
    "CacheConfig",
    # Data models
    "AccountRecord",
    "AccountSnapshot",
    "ChangeDetectionResult",
    "AggregatedData",
    "RiskSignal",
    "DealRecord",
    "ActivityRecord",
    "NoteRecord",
    "FieldChange",
    # Enums
    "ChangeType",
    "AccountStatus",
    "DealStage",
    "RiskLevel",
    # Utilities
    "calculate_field_diff",
    "detect_stalled_deals",
    "calculate_inactivity_days",
    "assess_account_risk",
    "identify_engagement_drop",
    "generate_risk_signals",
    "aggregate_deal_pipeline",
    "summarize_activities",
    "calculate_engagement_score",
]
