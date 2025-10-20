"""
CopilotKit Backend Setup Template

This module demonstrates how to set up the CopilotKit Python SDK with FastAPI
for the Sergas Account Manager backend.

Key Integrations:
- CopilotKit Python SDK
- LangGraph for agent workflows
- FastAPI for HTTP endpoints
- Claude Agent SDK integration

Usage:
    from docs.sparc.templates.backend_setup import setup_copilotkit

    app = FastAPI()
    setup_copilotkit(app)
"""

import os
from typing import Dict, Any, Optional
from fastapi import FastAPI
from copilotkit import CopilotKit
from copilotkit.integrations.fastapi import add_fastapi_endpoint
import structlog

logger = structlog.get_logger(__name__)


def setup_copilotkit(
    app: FastAPI,
    config: Optional[Dict[str, Any]] = None
) -> CopilotKit:
    """
    Configure and initialize CopilotKit with FastAPI application.

    This function:
    1. Initializes the CopilotKit SDK
    2. Registers all agent wrappers (LangGraph nodes)
    3. Adds the FastAPI endpoint for CopilotKit communication
    4. Configures CORS for frontend integration

    Args:
        app: FastAPI application instance
        config: Optional configuration dictionary overriding environment variables

    Returns:
        Configured CopilotKit instance

    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> copilot_kit = setup_copilotkit(app)
        >>> # Server now has /copilotkit endpoint available
    """

    # Load configuration from environment with defaults
    default_config = {
        "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "allowed_origins": os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://localhost:3001"
        ).split(",")
    }

    # Merge with provided config
    final_config = {**default_config, **(config or {})}

    # Validate required configuration
    if not final_config["api_key"]:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable must be set. "
            "See .env_copilotkit.example for configuration."
        )

    logger.info(
        "initializing_copilotkit",
        model=final_config["model"],
        debug=final_config["debug"]
    )

    try:
        # Initialize CopilotKit
        copilot_kit = CopilotKit(
            model=final_config["model"],
            api_key=final_config["api_key"],
            # Optional: Add cloud features if using CopilotKit Cloud
            # cloud_api_key=os.getenv("COPILOTKIT_PUBLIC_API_KEY"),
        )

        # Register agent wrappers (LangGraph graphs)
        # These will be imported from separate wrapper modules
        from docs.sparc.templates.orchestrator_wrapper import create_orchestrator_graph
        from docs.sparc.templates.zoho_scout_wrapper import create_zoho_scout_graph

        # Create LangGraph instances for each agent
        orchestrator_graph = create_orchestrator_graph()
        zoho_scout_graph = create_zoho_scout_graph()

        # Register graphs with CopilotKit
        copilot_kit.add_agent("orchestrator", orchestrator_graph)
        copilot_kit.add_agent("zoho_scout", zoho_scout_graph)

        # Add FastAPI endpoint for CopilotKit communication
        # This creates POST /copilotkit endpoint that handles:
        # - Agent execution requests
        # - Streaming responses
        # - State management
        add_fastapi_endpoint(
            app=app,
            copilot_kit=copilot_kit,
            endpoint="/copilotkit",
            # Optional: Custom request validation
            # request_validator=custom_validator,
        )

        logger.info(
            "copilotkit_initialized",
            endpoint="/copilotkit",
            agents=["orchestrator", "zoho_scout"]
        )

        return copilot_kit

    except Exception as e:
        logger.error(
            "copilotkit_initialization_failed",
            error=str(e)
        )
        raise


def configure_cors(app: FastAPI, allowed_origins: list[str]) -> None:
    """
    Configure CORS middleware for CopilotKit frontend integration.

    CopilotKit requires CORS to be properly configured for browser-based
    requests from the React frontend.

    Args:
        app: FastAPI application
        allowed_origins: List of allowed origin URLs

    Example:
        >>> configure_cors(app, ["http://localhost:3000"])
    """
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Content-Type", "Authorization"]
    )

    logger.info(
        "cors_configured",
        allowed_origins=allowed_origins
    )


# Example: Complete FastAPI application setup
def create_app() -> FastAPI:
    """
    Create and configure the complete FastAPI application with CopilotKit.

    Returns:
        Configured FastAPI application ready to serve

    Example:
        >>> app = create_app()
        >>> # Run with: uvicorn backend_setup:app --reload
    """

    # Create FastAPI app
    app = FastAPI(
        title="Sergas Account Manager API",
        description="Backend API for Sergas Super Account Manager with CopilotKit",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Configure CORS
    allowed_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000"
    ).split(",")
    configure_cors(app, allowed_origins)

    # Setup CopilotKit
    copilot_kit = setup_copilotkit(app)

    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint for monitoring."""
        return {
            "status": "healthy",
            "service": "sergas-account-manager",
            "copilotkit": "enabled"
        }

    # Add additional custom endpoints here
    # Example: Account list endpoint
    @app.get("/api/accounts")
    async def list_accounts():
        """List available accounts (example endpoint)."""
        return {
            "accounts": [
                {"id": "ACC-001", "name": "Acme Corp"},
                {"id": "ACC-002", "name": "TechStart Inc"}
            ]
        }

    logger.info(
        "fastapi_app_created",
        docs_url="/docs",
        copilotkit_endpoint="/copilotkit"
    )

    return app


# For direct execution
if __name__ == "__main__":
    import uvicorn

    app = create_app()

    # Run the server
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )
