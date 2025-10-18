"""Orchestrator module - Main coordination layer for account reviews.

Main Orchestrator Agent implementation for Week 5 of the SPARC development plan.

Components:
- MainOrchestrator: Central coordination agent
- WorkflowEngine: Review cycle execution engine
- ApprovalGate: Human-in-the-loop approval workflow
- OrchestratorConfig: Configuration management

Key Features:
- Scheduled review cycles (daily/weekly/on-demand)
- Parallel subagent coordination via Claude SDK
- Approval workflow for all CRM modifications
- Session state persistence and recovery
- Comprehensive audit logging and metrics

Architecture Alignment:
This module implements the specifications from:
- docs/sparc/03_architecture.md lines 104-167 (Main Orchestrator)
- docs/sparc/01_specification.md (Functional requirements)

Example Usage:
    >>> from src.orchestrator import MainOrchestrator, OrchestratorConfig
    >>> from src.services.memory_service import MemoryService
    >>> from src.integrations.zoho.integration_manager import ZohoIntegrationManager
    >>>
    >>> # Initialize configuration
    >>> config = OrchestratorConfig.from_env()
    >>>
    >>> # Create orchestrator
    >>> orchestrator = MainOrchestrator(
    ...     config=config,
    ...     memory_service=memory_service,
    ...     zoho_manager=zoho_manager,
    ... )
    >>>
    >>> # Start orchestrator
    >>> await orchestrator.start()
    >>>
    >>> # Execute review cycle
    >>> briefs = await orchestrator.execute_review_cycle(
    ...     cycle=ReviewCycle.DAILY
    ... )
    >>>
    >>> # Check status
    >>> status = orchestrator.get_status()
    >>> print(f"Status: {status['status']}")
"""

from src.orchestrator.main_orchestrator import (
    MainOrchestrator,
    ReviewCycle,
    OrchestratorStatus,
    OwnerAssignment,
    AccountUpdate,
    OwnerBrief,
    SubagentQuery,
    SubagentResult,
)

from src.orchestrator.workflow_engine import (
    WorkflowEngine,
    WorkflowStatus,
    PriorityLevel,
    WorkflowExecution,
)

from src.orchestrator.approval_gate import (
    ApprovalGate,
    ApprovalStatus,
    ApprovalChannel,
    ApprovalRequest,
    ApprovalConfig,
)

from src.orchestrator.config import (
    OrchestratorConfig,
    PermissionMode,
    MCPProtocol,
    MCPServerConfig,
    HooksConfig,
)


__version__ = "1.0.0"

__all__ = [
    # Main Orchestrator
    "MainOrchestrator",
    "ReviewCycle",
    "OrchestratorStatus",
    "OwnerAssignment",
    "AccountUpdate",
    "OwnerBrief",
    "SubagentQuery",
    "SubagentResult",

    # Workflow Engine
    "WorkflowEngine",
    "WorkflowStatus",
    "PriorityLevel",
    "WorkflowExecution",

    # Approval Gate
    "ApprovalGate",
    "ApprovalStatus",
    "ApprovalChannel",
    "ApprovalRequest",
    "ApprovalConfig",

    # Configuration
    "OrchestratorConfig",
    "PermissionMode",
    "MCPProtocol",
    "MCPServerConfig",
    "HooksConfig",
]


def create_orchestrator(
    memory_service: "MemoryService",
    zoho_manager: "ZohoIntegrationManager",
    config: OrchestratorConfig = None,
) -> MainOrchestrator:
    """Factory function to create Main Orchestrator.

    Convenience function for creating fully initialized orchestrator.

    Args:
        memory_service: Memory coordination service
        zoho_manager: Zoho integration manager
        config: Orchestrator configuration (loads from env if None)

    Returns:
        Initialized MainOrchestrator instance

    Example:
        >>> orchestrator = create_orchestrator(
        ...     memory_service=memory_service,
        ...     zoho_manager=zoho_manager,
        ... )
        >>> await orchestrator.start()
    """
    if config is None:
        config = OrchestratorConfig.from_env()

    return MainOrchestrator(
        config=config,
        memory_service=memory_service,
        zoho_manager=zoho_manager,
    )


def get_version() -> str:
    """Get orchestrator module version.

    Returns:
        Version string
    """
    return __version__
