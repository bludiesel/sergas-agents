"""CopilotKit integration module for Sergas Account Manager.

This module provides CopilotKit SDK integration for FastAPI,
enabling real-time agent communication with frontend clients.

Includes:
- FastAPI endpoint setup for CopilotKit
- LangGraph agent wrappers
- AG UI Protocol bridge
"""

from .fastapi_integration import (
    setup_copilotkit_endpoint,
    setup_copilotkit_with_agents,
    CopilotKitIntegration
)

__version__ = "0.1.0"

__all__ = [
    "setup_copilotkit_endpoint",
    "setup_copilotkit_with_agents",
    "CopilotKitIntegration"
]
