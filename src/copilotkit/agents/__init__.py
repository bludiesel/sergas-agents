"""CopilotKit agent wrappers for Sergas agents."""

from .orchestrator_wrapper import (
    OrchestratorState,
    create_orchestrator_graph,
    initialize_orchestrator_dependencies
)

from .zoho_scout_wrapper import (
    create_zoho_scout_graph,
    fetch_account_data_direct,
    ZohoScoutState,
)

from .memory_analyst_wrapper import (
    MemoryAnalystState,
    create_memory_analyst_graph,
    initialize_memory_analyst_dependencies,
    memory_analyst_node,
    pattern_analysis_node
)

__all__ = [
    "OrchestratorState",
    "create_orchestrator_graph",
    "initialize_orchestrator_dependencies",
    "create_zoho_scout_graph",
    "fetch_account_data_direct",
    "ZohoScoutState",
    "MemoryAnalystState",
    "create_memory_analyst_graph",
    "initialize_memory_analyst_dependencies",
    "memory_analyst_node",
    "pattern_analysis_node",
]
