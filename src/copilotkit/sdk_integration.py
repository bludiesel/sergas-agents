"""
CopilotKit SDK Integration Module.

This module handles the core integration between CopilotKit Python SDK,
FastAPI, and the Sergas agent system. It provides:

1. CopilotKit SDK initialization and configuration
2. FastAPI endpoint registration for agent communication
3. CORS configuration for frontend integration
4. Agent wrapper registration with LangGraph

Reference Implementation:
    Based on /docs/sparc/templates/backend_setup.py

Architecture:
    FastAPI Application
        ├── /copilotkit endpoint (POST)
        ├── /health endpoint (GET)
        ├── /api/* custom endpoints
        └── CORS middleware

    CopilotKit Instance
        ├── Orchestrator Agent (LangGraph)
        ├── Zoho Scout Agent (LangGraph)
        ├── Memory Analyst Agent (LangGraph)
        └── Recommendation Author Agent (LangGraph)

Security:
    - API keys managed via environment variables
    - CORS configured with explicit allowed origins
    - Request validation on all endpoints
    - No sensitive data in logs

Performance:
    - Streaming responses for real-time updates
    - Connection pooling for Zoho API
    - Caching for frequently accessed data
    - Async/await for all I/O operations
"""

import os
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import structlog

logger = structlog.get_logger(__name__)


def setup_copilotkit(
    app: FastAPI,
    config: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Configure and initialize CopilotKit with FastAPI application.

    This function performs the following setup:
    1. Validates required environment variables
    2. Initializes the CopilotKit SDK instance
    3. Registers all agent wrappers (LangGraph nodes)
    4. Adds the /copilotkit FastAPI endpoint
    5. Configures logging and monitoring

    Args:
        app: FastAPI application instance
        config: Optional configuration dictionary. Keys:
            - model: Claude model identifier
            - api_key: Anthropic API key
            - debug: Enable debug logging
            - allowed_origins: List of CORS allowed origins
            - cloud_api_key: Optional CopilotKit Cloud API key

    Returns:
        Configured CopilotKit instance

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set
        ImportError: If CopilotKit SDK is not installed

    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> copilot_kit = setup_copilotkit(app)
        >>> # Server now has /copilotkit endpoint available
        >>> # Start with: uvicorn main:app --reload
    """

    # Load configuration from environment with defaults
    default_config = {
        "model": os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "allowed_origins": os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://localhost:3001"
        ).split(","),
        "cloud_api_key": os.getenv("COPILOTKIT_PUBLIC_API_KEY"),
    }

    # Merge with provided config
    final_config = {**default_config, **(config or {})}

    # Validate required configuration
    if not final_config["api_key"]:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable must be set. "
            "Please set it in your .env file or environment. "
            "See .env.example for reference."
        )

    logger.info(
        "initializing_copilotkit",
        model=final_config["model"],
        debug=final_config["debug"],
        has_cloud_key=bool(final_config["cloud_api_key"])
    )

    try:
        # Import CopilotKit SDK
        # NOTE: This import is deferred to allow installation check
        try:
            from copilotkit import CopilotKit
            from copilotkit.integrations.fastapi import add_fastapi_endpoint
        except ImportError as e:
            logger.error(
                "copilotkit_sdk_not_installed",
                error=str(e)
            )
            raise ImportError(
                "CopilotKit SDK not installed. "
                "Install with: pip install copilotkit"
            ) from e

        # Initialize CopilotKit instance
        copilot_kit_kwargs = {
            "model": final_config["model"],
            "api_key": final_config["api_key"],
        }

        # Add cloud API key if provided
        if final_config["cloud_api_key"]:
            copilot_kit_kwargs["cloud_api_key"] = final_config["cloud_api_key"]

        copilot_kit = CopilotKit(**copilot_kit_kwargs)

        # Register agent wrappers (LangGraph graphs)
        # These wrappers convert our existing agents to LangGraph format
        _register_agent_wrappers(copilot_kit)

        # Add FastAPI endpoint for CopilotKit communication
        # This creates POST /copilotkit endpoint that handles:
        # - Agent execution requests from frontend
        # - Streaming responses for real-time updates
        # - State management and conversation history
        add_fastapi_endpoint(
            app=app,
            copilot_kit=copilot_kit,
            endpoint="/copilotkit",
        )

        logger.info(
            "copilotkit_initialized",
            endpoint="/copilotkit",
            agents=_get_registered_agent_names()
        )

        return copilot_kit

    except Exception as e:
        logger.error(
            "copilotkit_initialization_failed",
            error=str(e),
            error_type=type(e).__name__
        )
        raise


def _register_agent_wrappers(copilot_kit: Any) -> None:
    """
    Register all agent wrappers with CopilotKit.

    This internal function imports and registers LangGraph wrappers
    for each of our agents. Each wrapper converts the agent's interface
    to LangGraph format for CopilotKit compatibility.

    Args:
        copilot_kit: CopilotKit instance to register agents with

    Note:
        Agent wrappers are located in src/copilotkit/agents/
        Each wrapper implements create_*_graph() function
    """

    logger.info("registering_agent_wrappers")

    # TODO: Import and register agent wrappers
    # from src.copilotkit.agents.orchestrator_wrapper import create_orchestrator_graph
    # from src.copilotkit.agents.zoho_scout_wrapper import create_zoho_scout_graph
    # from src.copilotkit.agents.memory_analyst_wrapper import create_memory_analyst_graph
    # from src.copilotkit.agents.recommendation_author_wrapper import create_recommendation_author_graph

    # orchestrator_graph = create_orchestrator_graph()
    # copilot_kit.add_agent("orchestrator", orchestrator_graph)

    # zoho_scout_graph = create_zoho_scout_graph()
    # copilot_kit.add_agent("zoho_scout", zoho_scout_graph)

    # memory_analyst_graph = create_memory_analyst_graph()
    # copilot_kit.add_agent("memory_analyst", memory_analyst_graph)

    # recommendation_author_graph = create_recommendation_author_graph()
    # copilot_kit.add_agent("recommendation_author", recommendation_author_graph)

    logger.warning(
        "agent_wrappers_not_implemented",
        message="Agent wrappers need to be implemented in src/copilotkit/agents/"
    )


def _get_registered_agent_names() -> List[str]:
    """Get list of registered agent names for logging."""
    # TODO: Return actual registered agent names
    return []  # Will be populated when wrappers are implemented


def configure_cors(app: FastAPI, allowed_origins: List[str]) -> None:
    """
    Configure CORS middleware for CopilotKit frontend integration.

    CopilotKit requires CORS to be properly configured for browser-based
    requests from the React frontend. This function adds the necessary
    middleware to allow cross-origin requests.

    Args:
        app: FastAPI application instance
        allowed_origins: List of allowed origin URLs (e.g., ["http://localhost:3000"])

    Security Notes:
        - Never use ["*"] in production
        - Always specify exact origins
        - Use HTTPS in production
        - Consider environment-specific origins

    Example:
        >>> configure_cors(app, ["http://localhost:3000", "https://app.example.com"])
    """

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Content-Type", "Authorization"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )

    logger.info(
        "cors_configured",
        allowed_origins=allowed_origins,
        allow_credentials=True
    )


def create_app() -> FastAPI:
    """
    Create and configure the complete FastAPI application with CopilotKit.

    This is the main application factory that creates a fully configured
    FastAPI instance with:
    - CopilotKit integration
    - CORS middleware
    - Health check endpoint
    - API documentation
    - Custom endpoints

    Returns:
        Configured FastAPI application ready to serve

    Example:
        >>> app = create_app()
        >>> # Run with: uvicorn src.copilotkit.sdk_integration:app --reload
        >>> # Or import in main.py: from src.copilotkit import create_app
    """

    # Create FastAPI app with metadata
    app = FastAPI(
        title="Sergas Account Manager API",
        description=(
            "Backend API for Sergas Super Account Manager with CopilotKit integration. "
            "Provides agent-based account management with real-time collaboration."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=[
            {
                "name": "copilotkit",
                "description": "CopilotKit agent communication endpoints"
            },
            {
                "name": "health",
                "description": "Health check and monitoring endpoints"
            },
            {
                "name": "accounts",
                "description": "Account management endpoints"
            },
        ]
    )

    # Configure CORS
    allowed_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:3001"
    ).split(",")
    configure_cors(app, allowed_origins)

    # Setup CopilotKit
    copilot_kit = setup_copilotkit(app)

    # Add health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """
        Health check endpoint for monitoring and load balancers.

        Returns:
            dict: Service health status and configuration
        """
        return {
            "status": "healthy",
            "service": "sergas-account-manager",
            "version": "1.0.0",
            "copilotkit": "enabled",
            "agents": _get_registered_agent_names(),
        }

    # Add readiness probe
    @app.get("/ready", tags=["health"])
    async def readiness_check():
        """
        Readiness probe for Kubernetes deployments.

        Returns:
            dict: Service readiness status
        """
        # TODO: Add actual readiness checks (DB connection, Zoho API, etc.)
        return {
            "ready": True,
            "checks": {
                "database": "not_implemented",
                "zoho_api": "not_implemented",
                "copilotkit": "ready"
            }
        }

    logger.info(
        "fastapi_app_created",
        docs_url="/docs",
        copilotkit_endpoint="/copilotkit",
        health_endpoint="/health"
    )

    return app


# For direct execution with uvicorn
# Run with: uvicorn src.copilotkit.sdk_integration:app --reload
app = create_app()

if __name__ == "__main__":
    import uvicorn

    # Run the server
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "false").lower() == "true",
        log_level="debug" if os.getenv("DEBUG", "false").lower() == "true" else "info"
    )
