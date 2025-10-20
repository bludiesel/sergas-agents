"""
Complete FastAPI Application with CopilotKit Integration

This is the main entry point for the Sergas Account Manager backend
with full CopilotKit integration.

Features:
- FastAPI server with CopilotKit endpoint
- All agent wrappers registered
- CORS configuration for frontend
- Health checks and monitoring
- SSE (Server-Sent Events) streaming

Usage:
    # Development
    python docs/sparc/templates/main_copilotkit.py

    # Production with uvicorn
    uvicorn docs.sparc.templates.main_copilotkit:app --host 0.0.0.0 --port 8000

    # Production with gunicorn
    gunicorn docs.sparc.templates.main_copilotkit:app -k uvicorn.workers.UvicornWorker
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from copilotkit import CopilotKit
from copilotkit.integrations.fastapi import add_fastapi_endpoint

# Import agent wrappers
from docs.sparc.templates.orchestrator_wrapper import create_orchestrator_graph
from docs.sparc.templates.zoho_scout_wrapper import create_zoho_scout_graph

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ]
)

logger = structlog.get_logger(__name__)


# ============================================================================
# Application Lifecycle Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle (startup/shutdown).

    This context manager handles:
    - Database connections
    - Cache initialization
    - Resource cleanup

    Args:
        app: FastAPI application instance

    Yields:
        None (but manages resources)
    """

    logger.info("application_starting")

    # Startup tasks
    try:
        # Initialize database connections
        # await init_database()

        # Initialize Redis cache
        # await init_cache()

        # Warm up agent dependencies
        logger.info("warming_up_agent_dependencies")

        logger.info("application_startup_complete")

    except Exception as e:
        logger.error("application_startup_failed", error=str(e))
        raise

    yield  # Application runs here

    # Shutdown tasks
    logger.info("application_shutting_down")

    # Close database connections
    # await close_database()

    # Close cache connections
    # await close_cache()

    logger.info("application_shutdown_complete")


# ============================================================================
# FastAPI Application Creation
# ============================================================================

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application

    Configuration:
        - Title, description, version
        - CORS middleware
        - CopilotKit integration
        - Custom endpoints
        - Error handlers
    """

    # Create FastAPI app with lifecycle management
    app = FastAPI(
        title="Sergas Account Manager API",
        description=(
            "Backend API for Sergas Super Account Manager with CopilotKit. "
            "Provides AI-powered account analysis and recommendations."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # ========================================================================
    # CORS Configuration
    # ========================================================================

    allowed_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:3001"
    ).split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Content-Type", "Authorization"]
    )

    logger.info("cors_configured", allowed_origins=allowed_origins)

    # ========================================================================
    # CopilotKit Integration
    # ========================================================================

    try:
        # Validate environment
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable must be set. "
                "See .env_copilotkit.example"
            )

        # Initialize CopilotKit
        copilot_kit = CopilotKit(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            api_key=api_key
        )

        # Create and register agent graphs
        orchestrator_graph = create_orchestrator_graph()
        zoho_scout_graph = create_zoho_scout_graph()

        copilot_kit.add_agent("orchestrator", orchestrator_graph)
        copilot_kit.add_agent("zoho_scout", zoho_scout_graph)

        # Add CopilotKit endpoint
        # This creates POST /copilotkit for agent communication
        add_fastapi_endpoint(
            app=app,
            copilot_kit=copilot_kit,
            endpoint="/copilotkit"
        )

        logger.info(
            "copilotkit_initialized",
            endpoint="/copilotkit",
            agents=["orchestrator", "zoho_scout"]
        )

    except Exception as e:
        logger.error("copilotkit_initialization_failed", error=str(e))
        raise

    # ========================================================================
    # Custom Endpoints
    # ========================================================================

    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "service": "Sergas Account Manager API",
            "version": "1.0.0",
            "status": "operational",
            "endpoints": {
                "copilotkit": "/copilotkit",
                "docs": "/docs",
                "health": "/health",
                "accounts": "/api/accounts"
            }
        }

    @app.get("/health")
    async def health_check():
        """
        Health check endpoint for monitoring.

        Returns:
            Health status and component availability
        """

        # Check components
        components = {
            "api": "healthy",
            "copilotkit": "healthy",
            "zoho": "healthy",  # TODO: Actually check Zoho connection
            "cognee": "healthy",  # TODO: Actually check Cognee connection
        }

        all_healthy = all(status == "healthy" for status in components.values())

        return {
            "status": "healthy" if all_healthy else "degraded",
            "service": "sergas-account-manager",
            "version": "1.0.0",
            "components": components
        }

    @app.get("/api/accounts")
    async def list_accounts(
        owner_id: str = None,
        status: str = None,
        limit: int = 50
    ):
        """
        List accounts with optional filtering.

        Args:
            owner_id: Filter by account owner
            status: Filter by status (Active, Inactive, etc.)
            limit: Maximum number of accounts to return

        Returns:
            List of accounts
        """

        # TODO: Implement actual account listing
        # This is a placeholder for demonstration

        return {
            "accounts": [
                {
                    "id": "ACC-001",
                    "name": "Acme Corporation",
                    "owner": "John Doe",
                    "status": "Active",
                    "risk_level": "low"
                },
                {
                    "id": "ACC-002",
                    "name": "TechStart Inc",
                    "owner": "Jane Smith",
                    "status": "Active",
                    "risk_level": "medium"
                }
            ],
            "total": 2,
            "limit": limit
        }

    @app.get("/api/accounts/{account_id}")
    async def get_account(account_id: str):
        """
        Get detailed account information.

        Args:
            account_id: Account identifier

        Returns:
            Account details
        """

        # This could use the zoho_scout_wrapper directly
        from docs.sparc.templates.zoho_scout_wrapper import fetch_account_data

        try:
            account_data = await fetch_account_data(account_id)
            return account_data

        except Exception as e:
            logger.error(
                "account_fetch_failed",
                account_id=account_id,
                error=str(e)
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch account: {str(e)}"
            )

    @app.post("/api/accounts/{account_id}/analyze")
    async def analyze_account(account_id: str):
        """
        Trigger full account analysis (orchestrator workflow).

        This endpoint starts the complete analysis workflow:
        1. Fetch Zoho data
        2. Retrieve historical context
        3. Generate recommendations
        4. Request approval

        Args:
            account_id: Account to analyze

        Returns:
            Analysis results
        """

        # TODO: Implement orchestrator invocation
        # This would typically be done through CopilotKit, but can also
        # be triggered via direct API call

        return {
            "status": "analysis_started",
            "account_id": account_id,
            "message": "Use CopilotKit frontend for interactive analysis"
        }

    # ========================================================================
    # Error Handlers
    # ========================================================================

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle validation errors."""
        logger.warning("validation_error", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=400,
            content={"error": "validation_error", "message": str(exc)}
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        """Handle unexpected errors."""
        logger.error(
            "unexpected_error",
            error=str(exc),
            path=request.url.path,
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred"
            }
        )

    logger.info("fastapi_app_created")

    return app


# ============================================================================
# Application Instance
# ============================================================================

# Create the app instance (used by uvicorn/gunicorn)
app = create_app()


# ============================================================================
# Development Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Load environment
    from dotenv import load_dotenv
    load_dotenv()

    # Server configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    logger.info(
        "starting_development_server",
        host=host,
        port=port,
        debug=debug
    )

    # Run server
    uvicorn.run(
        "main_copilotkit:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )
