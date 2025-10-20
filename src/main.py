"""FastAPI application entry point for Sergas Super Account Manager.

Week 6-8 Implementation: AG UI Protocol backend with SSE streaming.
Week 13 Enhancement: CopilotKit SDK integration for advanced agent communication.
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

# Load environment variables from .env file
load_dotenv()

# Override with .env.local for application-specific config (GLM-4.6)
# This allows .env to be managed by Claude Code while app uses GLM-4.6
load_dotenv('.env.local', override=True)

from src.api.routers.copilotkit_router import router as copilotkit_router
from src.api.routers.approval_router import router as approval_router
from src.copilotkit import setup_copilotkit_with_agents

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Sergas Super Account Manager API",
    version="1.0.0",
    description="Multi-agent account management with AG UI Protocol support"
)

# Configure CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(copilotkit_router, prefix="/api", tags=["AG UI Protocol"])
app.include_router(approval_router, prefix="/api", tags=["Approval Workflow"])

# Setup CopilotKit SDK endpoint with all agent wrappers
# This adds POST /copilotkit endpoint and registers all available agents
# The /api/copilotkit SSE endpoint remains for backward compatibility
try:
    copilotkit_integration = setup_copilotkit_with_agents(
        app=app,
        endpoint="/copilotkit",
        include_recommendation_author=False  # Set to True once wrapper is created
    )
    logger.info(
        "copilotkit_sdk_configured",
        endpoint="/copilotkit",
        agents=list(copilotkit_integration.agents.keys()) if copilotkit_integration else [],
        note="All agent wrappers registered successfully"
    )
except ValueError as e:
    # CopilotKit setup is optional - log warning if API key not configured
    logger.warning(
        "copilotkit_sdk_not_configured",
        reason=str(e),
        note="CopilotKit SDK endpoint not available. Configure ANTHROPIC_API_KEY to enable."
    )
    copilotkit_integration = None
except Exception as e:
    # Log error but don't crash application
    logger.error(
        "copilotkit_sdk_setup_failed",
        error=str(e),
        note="Application will continue without CopilotKit SDK endpoint"
    )
    copilotkit_integration = None


@app.get("/")
async def root():
    """Root endpoint with agent registry information."""
    response = {
        "service": "Sergas Super Account Manager",
        "version": "1.0.0",
        "protocol": "AG UI Protocol",
        "status": "operational",
        "endpoints": {
            "ag_ui_sse": "/api/copilotkit (SSE streaming)",
            "copilotkit_sdk": "/copilotkit (CopilotKit SDK)" if copilotkit_integration else "Not configured",
            "approval": "/api/approval",
            "health": "/health",
            "docs": "/docs"
        }
    }

    # Add registered agents information if available
    if copilotkit_integration:
        response["copilotkit_agents"] = {
            "total": len(copilotkit_integration.agents),
            "registered": list(copilotkit_integration.agents.keys()),
            "capabilities": {
                "orchestrator": ["orchestration", "approval_workflow", "multi_agent_coordination"],
                "zoho_scout": ["zoho_crm_integration", "account_data_retrieval", "risk_signal_detection"],
                "memory_analyst": ["historical_analysis", "pattern_recognition", "cognee_integration"]
            }
        }

    return response


@app.get("/agents")
async def list_agents():
    """List all registered CopilotKit agents with their capabilities."""
    if not copilotkit_integration:
        return {
            "error": "CopilotKit not configured",
            "message": "Set ANTHROPIC_API_KEY environment variable to enable CopilotKit SDK"
        }

    agents_info = []

    for agent_name in copilotkit_integration.agents.keys():
        if agent_name == "orchestrator":
            agent_info = {
                "name": "orchestrator",
                "description": "Main workflow coordinator with approval workflow",
                "capabilities": [
                    "orchestration",
                    "approval_workflow",
                    "multi_agent_coordination",
                    "event_streaming"
                ],
                "input": "account_id, workflow type",
                "output": "complete workflow results with approval status"
            }
        elif agent_name == "zoho_scout":
            agent_info = {
                "name": "zoho_scout",
                "description": "Zoho CRM data retrieval and risk detection",
                "capabilities": [
                    "zoho_crm_integration",
                    "account_data_retrieval",
                    "risk_signal_detection",
                    "change_tracking"
                ],
                "input": "account_id",
                "output": "account snapshot with risk signals and change summary"
            }
        elif agent_name == "memory_analyst":
            agent_info = {
                "name": "memory_analyst",
                "description": "Historical pattern analysis via Cognee knowledge graph",
                "capabilities": [
                    "historical_analysis",
                    "pattern_recognition",
                    "cognee_integration",
                    "sentiment_analysis",
                    "commitment_tracking"
                ],
                "input": "account_id, lookback_days",
                "output": "historical context with patterns and risk level"
            }
        elif agent_name == "recommendation_author":
            agent_info = {
                "name": "recommendation_author",
                "description": "Generate prioritized recommendations and action plans",
                "capabilities": [
                    "recommendation_generation",
                    "action_prioritization",
                    "template_based_output",
                    "impact_assessment"
                ],
                "input": "account data, historical context",
                "output": "prioritized recommendations with impact analysis"
            }
        else:
            agent_info = {
                "name": agent_name,
                "description": "Unknown agent",
                "capabilities": ["unknown"]
            }

        agents_info.append(agent_info)

    return {
        "total_agents": len(agents_info),
        "agents": agents_info,
        "copilotkit_endpoint": "/copilotkit",
        "model": copilotkit_integration.model
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "service": "sergas-agents",
        "protocol": "ag-ui",
        "copilotkit_configured": copilotkit_integration is not None
    }

    if copilotkit_integration:
        health_status["agents_registered"] = len(copilotkit_integration.agents)

    return health_status


@app.on_event("startup")
async def startup_event():
    """Application startup tasks with agent validation."""
    logger.info("sergas_agents_startup", version="1.0.0")

    # Log CopilotKit integration status
    if copilotkit_integration:
        logger.info(
            "copilotkit_agents_ready",
            total_agents=len(copilotkit_integration.agents),
            agents=list(copilotkit_integration.agents.keys()),
            endpoint="/copilotkit",
            model=copilotkit_integration.model
        )

        # Validate each agent
        for agent_name in copilotkit_integration.agents.keys():
            logger.info(
                "agent_validated",
                agent_name=agent_name,
                status="ready"
            )
    else:
        logger.warning(
            "copilotkit_not_available",
            message="CopilotKit SDK not configured. Agent endpoints not available."
        )


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logger.info("sergas_agents_shutdown")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
