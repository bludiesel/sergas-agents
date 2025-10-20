"""FastAPI integration for CopilotKit SDK.

This module provides a clean integration layer between FastAPI and CopilotKit SDK,
managing agent registration and endpoint creation without breaking existing routes.
"""

import os
from typing import Optional, Dict, Any
from fastapi import FastAPI
import structlog

# CopilotKit is optional - handle graceful degradation
try:
    from copilotkit import CopilotKitRemoteEndpoint
    from copilotkit.integrations.fastapi import add_fastapi_endpoint
    COPILOTKIT_AVAILABLE = True
except ImportError:
    COPILOTKIT_AVAILABLE = False
    CopilotKitRemoteEndpoint = None
    add_fastapi_endpoint = None

logger = structlog.get_logger(__name__)


class CopilotKitIntegration:
    """Manages CopilotKit SDK integration with FastAPI.

    This class encapsulates all CopilotKit initialization and configuration,
    providing a clean interface for registering agents and setting up endpoints.

    Attributes:
        sdk: CopilotKit SDK instance
        agents: Dictionary of registered agent names and their graphs
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """Initialize CopilotKit SDK.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use (defaults to CLAUDE_MODEL env var)
            base_url: Base URL for Anthropic API (defaults to ANTHROPIC_BASE_URL env var)

        Raises:
            ImportError: If CopilotKit SDK is not installed
            ValueError: If API key is not provided or found in environment

        Note:
            CopilotKit uses environment variables for model configuration:
            - ANTHROPIC_API_KEY: API key for Claude/GLM-4.6
            - ANTHROPIC_BASE_URL: Custom base URL (for GLM-4.6 via Z.ai)
            - CLAUDE_MODEL: Model identifier (glm-4.6 or claude-*)
        """
        # Check if CopilotKit is available
        if not COPILOTKIT_AVAILABLE:
            raise ImportError(
                "CopilotKit SDK is not installed. "
                "Install with: pip install copilotkit"
            )

        # Get configuration from environment (for logging/validation only)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model or os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
        self.base_url = base_url or os.getenv("ANTHROPIC_BASE_URL")

        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY must be provided or set in environment. "
                "See .env.example for configuration."
            )

        # Initialize CopilotKit RemoteEndpoint
        # Model/API configuration is handled through environment variables
        # by the underlying LangGraph agents
        self.sdk = CopilotKitRemoteEndpoint()

        # Track registered agents
        self.agents: Dict[str, Any] = {}

        logger.info(
            "copilotkit_sdk_initialized",
            model=self.model,
            base_url=self.base_url or "default"
        )

    def register_agent(self, name: str, agent_graph: Any) -> None:
        """Register an agent graph with CopilotKit.

        Args:
            name: Agent identifier (e.g., "orchestrator", "zoho_scout")
            agent_graph: LangGraph compiled graph instance

        Example:
            >>> integration = CopilotKitIntegration()
            >>> integration.register_agent("orchestrator", orchestrator_graph)
        """
        try:
            # Add agent to the SDK's agents list
            # CopilotKitRemoteEndpoint uses a list-based registration system
            agent_entry = {
                "name": name,
                "description": f"{name} agent for account management",
                "graph": agent_graph
            }
            self.sdk.agents.append(agent_entry)
            self.agents[name] = agent_graph

            logger.info(
                "copilotkit_agent_registered",
                agent_name=name,
                total_agents=len(self.agents)
            )

        except Exception as e:
            logger.error(
                "copilotkit_agent_registration_failed",
                agent_name=name,
                error=str(e),
                exc_info=True
            )
            raise

    def add_fastapi_endpoint(
        self,
        app: FastAPI,
        endpoint: str = "/copilotkit"
    ) -> None:
        """Add CopilotKit endpoint to FastAPI application.

        This creates a POST endpoint that handles CopilotKit agent communication.

        Args:
            app: FastAPI application instance
            endpoint: Path for CopilotKit endpoint (default: "/copilotkit")

        Example:
            >>> app = FastAPI()
            >>> integration = CopilotKitIntegration()
            >>> integration.add_fastapi_endpoint(app)
        """
        try:
            add_fastapi_endpoint(
                fastapi_app=app,
                sdk=self.sdk,
                prefix=endpoint
            )

            logger.info(
                "copilotkit_endpoint_added",
                endpoint=endpoint,
                agents=list(self.agents.keys())
            )

        except Exception as e:
            logger.error(
                "copilotkit_endpoint_creation_failed",
                endpoint=endpoint,
                error=str(e),
                exc_info=True
            )
            raise


def setup_copilotkit_endpoint(
    app: FastAPI,
    endpoint: str = "/copilotkit",
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> CopilotKitIntegration:
    """Setup CopilotKit endpoint on FastAPI application.

    This is the main entry point for integrating CopilotKit with FastAPI.
    It handles SDK initialization, agent registration, and endpoint creation.

    Args:
        app: FastAPI application instance
        endpoint: Path for CopilotKit endpoint (default: "/copilotkit")
        api_key: Optional Anthropic API key
        model: Optional Claude model name

    Returns:
        CopilotKitIntegration instance for agent registration

    Raises:
        ValueError: If configuration is invalid

    Example:
        >>> from fastapi import FastAPI
        >>> from src.copilotkit import setup_copilotkit_endpoint
        >>>
        >>> app = FastAPI()
        >>> copilotkit = setup_copilotkit_endpoint(app)
        >>>
        >>> # Register agents
        >>> copilotkit.register_agent("orchestrator", orchestrator_graph)
        >>> copilotkit.register_agent("zoho_scout", zoho_scout_graph)

    Note:
        This function does NOT register any agents by default.
        Agents must be registered after calling this function.
        This design allows for flexible agent registration patterns.
    """
    try:
        # Initialize CopilotKit integration
        integration = CopilotKitIntegration(api_key=api_key, model=model)

        # Note: We do NOT register agents here
        # Agent registration should happen in the caller
        # This allows for proper dependency injection and testing

        # Add FastAPI endpoint
        integration.add_fastapi_endpoint(app, endpoint)

        logger.info(
            "copilotkit_setup_complete",
            endpoint=endpoint,
            model=integration.model
        )

        return integration

    except Exception as e:
        logger.error(
            "copilotkit_setup_failed",
            error=str(e),
            exc_info=True
        )
        raise


def setup_copilotkit_with_agents(
    app: FastAPI,
    endpoint: str = "/copilotkit",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    include_recommendation_author: bool = False
) -> CopilotKitIntegration:
    """Setup CopilotKit endpoint with all agent wrappers registered.

    This is a convenience function that registers all available agents.
    Use this when you want automatic agent registration.

    Args:
        app: FastAPI application instance
        endpoint: Path for CopilotKit endpoint
        api_key: Optional Anthropic API key
        model: Optional Claude model name
        include_recommendation_author: Include recommendation author agent (requires wrapper to be created)

    Returns:
        CopilotKitIntegration instance with agents registered

    Agents registered:
        - orchestrator: Main workflow coordinator with approval workflow
        - zoho_scout: Zoho CRM data retrieval and risk detection
        - memory_analyst: Historical pattern analysis via Cognee
        - recommendation_author: Action generation (if include_recommendation_author=True)
    """
    try:
        # Import agent graph creation functions
        from src.copilotkit.agents import (
            create_orchestrator_graph,
            create_zoho_scout_graph,
            create_memory_analyst_graph,
        )

        # Setup base integration
        integration = setup_copilotkit_endpoint(
            app=app,
            endpoint=endpoint,
            api_key=api_key,
            model=model
        )

        # Register Orchestrator Agent
        logger.info("registering_orchestrator_agent")
        orchestrator_graph = create_orchestrator_graph()
        integration.register_agent(
            name="orchestrator",
            agent_graph=orchestrator_graph
        )
        logger.info(
            "orchestrator_agent_registered",
            capabilities=["orchestration", "approval_workflow", "multi_agent_coordination"]
        )

        # Register ZohoDataScout Agent
        logger.info("registering_zoho_scout_agent")
        zoho_scout_graph = create_zoho_scout_graph()
        integration.register_agent(
            name="zoho_scout",
            agent_graph=zoho_scout_graph
        )
        logger.info(
            "zoho_scout_agent_registered",
            capabilities=["zoho_crm_integration", "account_data_retrieval", "risk_signal_detection"]
        )

        # Register MemoryAnalyst Agent
        logger.info("registering_memory_analyst_agent")
        memory_analyst_graph = create_memory_analyst_graph()
        integration.register_agent(
            name="memory_analyst",
            agent_graph=memory_analyst_graph
        )
        logger.info(
            "memory_analyst_agent_registered",
            capabilities=["historical_analysis", "pattern_recognition", "cognee_integration"]
        )

        # Register RecommendationAuthor Agent (if available and requested)
        if include_recommendation_author:
            try:
                # Dynamic import to handle if wrapper is not yet created
                from src.copilotkit.agents.recommendation_author_wrapper import (
                    create_recommendation_author_graph
                )

                logger.info("registering_recommendation_author_agent")
                recommendation_author_graph = create_recommendation_author_graph()
                integration.register_agent(
                    name="recommendation_author",
                    agent_graph=recommendation_author_graph
                )
                logger.info(
                    "recommendation_author_agent_registered",
                    capabilities=["recommendation_generation", "action_prioritization", "template_based_output"]
                )
            except ImportError as e:
                logger.warning(
                    "recommendation_author_wrapper_not_found",
                    error=str(e),
                    note="Recommendation author agent will not be registered. Create wrapper to enable."
                )

        logger.info(
            "all_agents_registered",
            total_agents=len(integration.agents),
            registered_agents=list(integration.agents.keys())
        )

        return integration

    except Exception as e:
        logger.error(
            "setup_copilotkit_with_agents_failed",
            error=str(e),
            exc_info=True
        )
        raise
