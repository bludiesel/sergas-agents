# SPARC Completion Phase: CopilotKit Integration Implementation Plan
## Sergas Super Account Manager Agent

**Project**: Sergas Super Account Manager Agent
**Version**: 1.0.0
**Status**: Implementation Plan
**Date**: 2025-10-19
**SPARC Phase**: Completion (Phase 5 of 5)
**Author**: SPARC Completion Specialist

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Implementation Task Breakdown](#2-implementation-task-breakdown)
3. [File Manifest](#3-file-manifest)
4. [Validation Checkpoints](#4-validation-checkpoints)
5. [Timeline & Dependencies](#5-timeline--dependencies)
6. [Risk Mitigation](#6-risk-mitigation)
7. [Success Criteria](#7-success-criteria)

---

## 1. Executive Summary

### 1.1 Project Context

This document provides the detailed implementation plan for integrating **CopilotKit LangGraph Python SDK** with the existing Claude Agent SDK-based Sergas Super Account Manager. The goal is to transform our current agents into HTTP-accessible endpoints compatible with CopilotKit's real-time streaming and human-in-the-loop approval workflows.

### 1.2 Core Requirements

**8 User Requirements to Address:**

1. ✅ **Refactor agent orchestration** into HTTP endpoints
2. ✅ **Install CopilotKit LangGraph Python SDK** (`copilotkit-langgraph`)
3. ✅ **Wrap agents with LangGraph** (OrchestratorAgent, ZohoDataScout, MemoryAnalyst, RecommendationAuthor)
4. ✅ **Set up `/agent-orchestrator` endpoint** with CopilotKitSDK
5. ✅ **Register endpoints in frontend** with AG-UI wrappers
6. ✅ **Update React frontend hooks** (useCopilotAction/useCoAgent)
7. ✅ **Test agent orchestration** end-to-end with HITL approval
8. ✅ **Implement monitoring** with logging and dashboards

### 1.3 Implementation Approach

**Strategy**: Incremental integration with parallel development tracks
- **Backend Track**: Python SDK installation, agent wrapping, endpoint creation
- **Frontend Track**: Next.js route setup, AG-UI client integration, React hooks
- **Testing Track**: Concurrent test development with implementation

**Timeline**: 3 weeks (15 working days)
**Risk Level**: Medium (new SDK integration, architectural changes)

---

## 2. Implementation Task Breakdown

### PHASE 1: Backend Foundation (Week 1)

#### Requirement 1: Refactor Agent Orchestration into HTTP Endpoints

**Task 1.1: Create CopilotKit Agent Module Structure**

**Duration**: 2 hours
**Priority**: CRITICAL
**Dependencies**: None

**Steps**:
```bash
# 1.1.1 Create directory structure
mkdir -p src/copilotkit/agents
mkdir -p src/copilotkit/wrappers
mkdir -p src/copilotkit/routes
mkdir -p src/copilotkit/middleware

# 1.1.2 Create __init__.py files
touch src/copilotkit/__init__.py
touch src/copilotkit/agents/__init__.py
touch src/copilotkit/wrappers/__init__.py
touch src/copilotkit/routes/__init__.py
touch src/copilotkit/middleware/__init__.py
```

**Files to Create**:
- `/src/copilotkit/__init__.py` - Package initialization
- `/src/copilotkit/agents/__init__.py` - Agent exports
- `/src/copilotkit/wrappers/__init__.py` - Wrapper exports
- `/src/copilotkit/routes/__init__.py` - Route exports
- `/src/copilotkit/middleware/__init__.py` - Middleware exports

**Validation Checkpoint 1.1**:
```bash
# Verify directory structure exists
test -d src/copilotkit/agents && echo "✅ Structure created"
# Verify imports work
python -c "import src.copilotkit" && echo "✅ Import successful"
```

**Expected Output**: All directories created, no import errors

---

**Task 1.2: Extract Agent Logic into Reusable Functions**

**Duration**: 4 hours
**Priority**: CRITICAL
**Dependencies**: Task 1.1

**Steps**:
```python
# 1.2.1 Create agent endpoint wrappers
# File: src/copilotkit/agents/orchestrator_endpoint.py

from typing import Dict, Any, AsyncGenerator
from src.agents.orchestrator import OrchestratorAgent
from src.agents.zoho_data_scout import ZohoDataScout
from src.agents.memory_analyst import MemoryAnalyst
from src.agents.recommendation_author import RecommendationAuthor

class OrchestratorEndpoint:
    """
    HTTP endpoint wrapper for OrchestratorAgent.

    Converts Claude SDK agent into CopilotKit-compatible interface.
    """

    def __init__(
        self,
        orchestrator: OrchestratorAgent,
        zoho_scout: ZohoDataScout,
        memory_analyst: MemoryAnalyst,
        recommendation_author: RecommendationAuthor
    ):
        self.orchestrator = orchestrator
        self.zoho_scout = zoho_scout
        self.memory_analyst = memory_analyst
        self.recommendation_author = recommendation_author

    async def execute_workflow(
        self,
        account_id: str,
        session_id: str,
        user_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute multi-agent workflow with streaming.

        Yields:
            AG UI Protocol events for CopilotKit consumption
        """
        context = {
            "account_id": account_id,
            "session_id": session_id,
            "user_id": user_id,
            "step": 0
        }

        # Step 1: Zoho Data Scout
        context["step"] = 1
        async for event in self.zoho_scout.execute_with_events(context):
            yield event

        # Step 2: Memory Analyst
        context["step"] = 2
        async for event in self.memory_analyst.execute_with_events(context):
            yield event

        # Step 3: Recommendation Author
        context["step"] = 3
        async for event in self.recommendation_author.execute_with_events(context):
            yield event

        # Final: Return orchestration complete
        yield {
            "type": "workflow_complete",
            "session_id": session_id,
            "account_id": account_id,
            "timestamp": datetime.utcnow().isoformat()
        }
```

**Files to Create**:
- `/src/copilotkit/agents/orchestrator_endpoint.py` - Orchestrator HTTP wrapper
- `/src/copilotkit/agents/zoho_scout_endpoint.py` - Zoho Scout HTTP wrapper
- `/src/copilotkit/agents/memory_analyst_endpoint.py` - Memory Analyst HTTP wrapper
- `/src/copilotkit/agents/recommendation_author_endpoint.py` - Recommendation Author HTTP wrapper

**Validation Checkpoint 1.2**:
```python
# test_endpoint_wrappers.py
import pytest
from src.copilotkit.agents.orchestrator_endpoint import OrchestratorEndpoint

@pytest.mark.asyncio
async def test_orchestrator_endpoint_creation():
    """Verify endpoint wrapper can be instantiated"""
    endpoint = OrchestratorEndpoint(
        orchestrator=mock_orchestrator,
        zoho_scout=mock_scout,
        memory_analyst=mock_analyst,
        recommendation_author=mock_author
    )
    assert endpoint is not None
    assert hasattr(endpoint, 'execute_workflow')

@pytest.mark.asyncio
async def test_workflow_execution_streaming():
    """Verify workflow yields AG UI events"""
    endpoint = OrchestratorEndpoint(...)
    events = []
    async for event in endpoint.execute_workflow("ACC-001", "sess-123", "user-456"):
        events.append(event)

    assert len(events) > 0
    assert events[-1]["type"] == "workflow_complete"
```

**Expected Output**: All tests pass, endpoint wrappers instantiate correctly

---

#### Requirement 2: Install CopilotKit LangGraph Python SDK

**Task 2.1: Install CopilotKit Dependencies**

**Duration**: 1 hour
**Priority**: CRITICAL
**Dependencies**: None (can run in parallel with Task 1.1)

**Steps**:
```bash
# 2.1.1 Update requirements.txt
cat >> requirements.txt <<EOF

# ===================================
# CopilotKit Integration (Week 5)
# ===================================
# CopilotKit LangGraph Python SDK
copilotkit-langgraph>=0.1.0
langgraph>=0.2.0
langchain-core>=0.3.0

# FastAPI integration for CopilotKit
fastapi>=0.104.1  # Already in requirements
uvicorn[standard]>=0.24.0  # Already in requirements

# SSE support for real-time streaming
sse-starlette>=1.6.5  # Already in requirements
EOF

# 2.1.2 Install dependencies
pip install -r requirements.txt

# 2.1.3 Verify installation
python -c "import copilotkit_langgraph; print(copilotkit_langgraph.__version__)"
python -c "import langgraph; print(langgraph.__version__)"
```

**Files to Modify**:
- `/requirements.txt` - Add CopilotKit dependencies

**Validation Checkpoint 2.1**:
```bash
# Verify all packages installed
pip list | grep copilotkit
pip list | grep langgraph
pip list | grep langchain

# Expected output:
# copilotkit-langgraph    0.1.0
# langgraph               0.2.0
# langchain-core          0.3.0
```

**Expected Output**: All packages installed with correct versions

---

**Task 2.2: Configure CopilotKit SDK Client**

**Duration**: 2 hours
**Priority**: CRITICAL
**Dependencies**: Task 2.1

**Steps**:
```python
# 2.2.1 Create CopilotKit configuration module
# File: src/copilotkit/config.py

import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class CopilotKitConfig(BaseSettings):
    """
    CopilotKit SDK configuration.

    Loads from environment variables with CK_ prefix.
    """

    # API Configuration
    api_base_url: str = Field(
        default="http://localhost:8000",
        description="Base URL for CopilotKit API"
    )

    # Agent Configuration
    agent_endpoint: str = Field(
        default="/api/agent-orchestrator",
        description="Endpoint for agent orchestration"
    )

    # Streaming Configuration
    enable_streaming: bool = Field(
        default=True,
        description="Enable SSE streaming for real-time updates"
    )

    stream_timeout: int = Field(
        default=300,
        description="Stream timeout in seconds"
    )

    # Security
    require_auth: bool = Field(
        default=True,
        description="Require authentication for agent endpoints"
    )

    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )

    # Approval Workflow
    approval_timeout: int = Field(
        default=300,
        description="Approval timeout in seconds"
    )

    enable_auto_approve: bool = Field(
        default=False,
        description="Auto-approve low-risk recommendations (dev only)"
    )

    class Config:
        env_prefix = "CK_"
        env_file = ".env"
        env_file_encoding = "utf-8"

def get_copilotkit_config() -> CopilotKitConfig:
    """Get CopilotKit configuration singleton."""
    return CopilotKitConfig()
```

**Files to Create**:
- `/src/copilotkit/config.py` - CopilotKit configuration
- `/.env.example` - Example environment variables (update existing)

**Validation Checkpoint 2.2**:
```python
# test_copilotkit_config.py
def test_copilotkit_config_defaults():
    """Verify config loads with defaults"""
    config = get_copilotkit_config()
    assert config.api_base_url == "http://localhost:8000"
    assert config.enable_streaming is True
    assert config.require_auth is True

def test_copilotkit_config_from_env(monkeypatch):
    """Verify config loads from environment"""
    monkeypatch.setenv("CK_API_BASE_URL", "https://api.sergas.com")
    monkeypatch.setenv("CK_ENABLE_STREAMING", "false")

    config = get_copilotkit_config()
    assert config.api_base_url == "https://api.sergas.com"
    assert config.enable_streaming is False
```

**Expected Output**: Config loads correctly, all tests pass

---

#### Requirement 3: Wrap Agents with LangGraph

**Task 3.1: Create LangGraph Agent Wrappers**

**Duration**: 6 hours
**Priority**: CRITICAL
**Dependencies**: Tasks 1.2, 2.2

**Steps**:
```python
# 3.1.1 Create LangGraph wrapper for OrchestratorAgent
# File: src/copilotkit/wrappers/orchestrator_langgraph.py

from typing import Dict, Any, AsyncGenerator, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, HumanMessage
from copilotkit_langgraph import CopilotKitSDK

from src.agents.orchestrator import OrchestratorAgent
from src.copilotkit.agents.orchestrator_endpoint import OrchestratorEndpoint

class AgentState(TypedDict):
    """State passed between LangGraph nodes"""
    account_id: str
    session_id: str
    user_id: str
    current_step: str
    zoho_snapshot: Optional[Dict[str, Any]]
    historical_context: Optional[Dict[str, Any]]
    recommendations: Optional[list[Dict[str, Any]]]
    messages: list[AIMessage | HumanMessage]
    pending_approvals: list[Dict[str, Any]]

class OrchestratorLangGraph:
    """
    LangGraph wrapper for OrchestratorAgent.

    Converts Claude SDK agent into LangGraph state machine
    for CopilotKit integration.
    """

    def __init__(
        self,
        orchestrator_endpoint: OrchestratorEndpoint,
        copilotkit_sdk: CopilotKitSDK
    ):
        self.endpoint = orchestrator_endpoint
        self.sdk = copilotkit_sdk
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build LangGraph state machine for agent workflow"""

        workflow = StateGraph(AgentState)

        # Define nodes
        workflow.add_node("zoho_scout", self._run_zoho_scout)
        workflow.add_node("memory_analyst", self._run_memory_analyst)
        workflow.add_node("recommendation_author", self._run_recommendation_author)
        workflow.add_node("approval_gate", self._run_approval_gate)

        # Define edges
        workflow.set_entry_point("zoho_scout")
        workflow.add_edge("zoho_scout", "memory_analyst")
        workflow.add_edge("memory_analyst", "recommendation_author")
        workflow.add_edge("recommendation_author", "approval_gate")
        workflow.add_conditional_edges(
            "approval_gate",
            self._check_approval_status,
            {
                "approved": END,
                "rejected": "recommendation_author",  # Retry with feedback
                "timeout": END
            }
        )

        return workflow.compile()

    async def _run_zoho_scout(self, state: AgentState) -> AgentState:
        """Execute Zoho Data Scout node"""
        context = {
            "account_id": state["account_id"],
            "session_id": state["session_id"],
            "step": 1
        }

        # Stream events from agent
        async for event in self.endpoint.zoho_scout.execute_with_events(context):
            # Emit to CopilotKit
            await self.sdk.emit_event(event)

        # Update state with snapshot
        state["zoho_snapshot"] = context.get("account_snapshot")
        state["current_step"] = "zoho_scout_complete"
        state["messages"].append(
            AIMessage(content=f"Retrieved account snapshot for {state['account_id']}")
        )

        return state

    async def _run_memory_analyst(self, state: AgentState) -> AgentState:
        """Execute Memory Analyst node"""
        context = {
            "account_id": state["account_id"],
            "session_id": state["session_id"],
            "step": 2
        }

        async for event in self.endpoint.memory_analyst.execute_with_events(context):
            await self.sdk.emit_event(event)

        state["historical_context"] = context.get("historical_context")
        state["current_step"] = "memory_analyst_complete"
        state["messages"].append(
            AIMessage(content=f"Analyzed historical context")
        )

        return state

    async def _run_recommendation_author(self, state: AgentState) -> AgentState:
        """Execute Recommendation Author node"""
        context = {
            "account_id": state["account_id"],
            "session_id": state["session_id"],
            "account_snapshot": state["zoho_snapshot"],
            "historical_context": state["historical_context"],
            "step": 3
        }

        async for event in self.endpoint.recommendation_author.execute_with_events(context):
            await self.sdk.emit_event(event)

        state["recommendations"] = context.get("recommendations", [])
        state["current_step"] = "recommendations_ready"
        state["messages"].append(
            AIMessage(content=f"Generated {len(state['recommendations'])} recommendations")
        )

        return state

    async def _run_approval_gate(self, state: AgentState) -> AgentState:
        """Human-in-the-loop approval gate"""

        # Request approval from frontend
        approval_request = {
            "type": "approval_request",
            "session_id": state["session_id"],
            "account_id": state["account_id"],
            "recommendations": state["recommendations"],
            "timeout": 300  # 5 minutes
        }

        # Emit approval request via CopilotKit
        await self.sdk.emit_event(approval_request)

        # Wait for approval response
        approval_response = await self.sdk.wait_for_approval(
            session_id=state["session_id"],
            timeout=300
        )

        state["pending_approvals"] = approval_response.get("approvals", [])
        state["current_step"] = f"approval_{approval_response['status']}"

        return state

    def _check_approval_status(self, state: AgentState) -> str:
        """Determine next step based on approval status"""
        if "approval_approved" in state["current_step"]:
            return "approved"
        elif "approval_rejected" in state["current_step"]:
            return "rejected"
        elif "approval_timeout" in state["current_step"]:
            return "timeout"
        return "approved"  # Default

    async def execute(
        self,
        account_id: str,
        session_id: str,
        user_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute LangGraph workflow with streaming.

        Yields AG UI Protocol events for CopilotKit.
        """
        initial_state = AgentState(
            account_id=account_id,
            session_id=session_id,
            user_id=user_id,
            current_step="initialized",
            zoho_snapshot=None,
            historical_context=None,
            recommendations=None,
            messages=[],
            pending_approvals=[]
        )

        # Execute graph with streaming
        async for event in self.graph.astream(initial_state):
            yield event
```

**Files to Create**:
- `/src/copilotkit/wrappers/orchestrator_langgraph.py` - Orchestrator LangGraph wrapper
- `/src/copilotkit/wrappers/base_langgraph_wrapper.py` - Base wrapper class
- `/src/copilotkit/wrappers/approval_handler.py` - Approval workflow handler

**Validation Checkpoint 3.1**:
```python
# test_langgraph_wrappers.py
@pytest.mark.asyncio
async def test_orchestrator_langgraph_creation():
    """Verify LangGraph wrapper can be created"""
    wrapper = OrchestratorLangGraph(
        orchestrator_endpoint=mock_endpoint,
        copilotkit_sdk=mock_sdk
    )
    assert wrapper.graph is not None

@pytest.mark.asyncio
async def test_langgraph_workflow_execution():
    """Verify workflow executes all nodes"""
    wrapper = OrchestratorLangGraph(...)

    events = []
    async for event in wrapper.execute("ACC-001", "sess-123", "user-456"):
        events.append(event)

    # Verify all nodes executed
    node_names = [e.get("node") for e in events if "node" in e]
    assert "zoho_scout" in node_names
    assert "memory_analyst" in node_names
    assert "recommendation_author" in node_names
    assert "approval_gate" in node_names
```

**Expected Output**: LangGraph workflow builds successfully, all nodes execute

---

#### Requirement 4: Set Up `/agent-orchestrator` Endpoint

**Task 4.1: Create FastAPI CopilotKit Route**

**Duration**: 4 hours
**Priority**: CRITICAL
**Dependencies**: Tasks 3.1

**Steps**:
```python
# 4.1.1 Create FastAPI route for agent orchestration
# File: src/copilotkit/routes/agent_orchestrator.py

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json

from src.copilotkit.config import get_copilotkit_config
from src.copilotkit.wrappers.orchestrator_langgraph import OrchestratorLangGraph
from copilotkit_langgraph import CopilotKitSDK

router = APIRouter(prefix="/api", tags=["agent-orchestrator"])

class AgentRequest(BaseModel):
    """Request model for agent orchestration"""
    account_id: str
    session_id: Optional[str] = None
    user_id: str
    options: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    """Response model for agent orchestration"""
    session_id: str
    account_id: str
    status: str
    recommendations: list[Dict[str, Any]]

@router.post("/agent-orchestrator")
async def orchestrate_agents(
    request: AgentRequest,
    config: CopilotKitConfig = Depends(get_copilotkit_config)
):
    """
    Main agent orchestration endpoint for CopilotKit.

    Executes multi-agent workflow with real-time streaming
    and human-in-the-loop approval.

    Args:
        request: Agent orchestration request
        config: CopilotKit configuration

    Returns:
        StreamingResponse with SSE events
    """

    # Initialize CopilotKit SDK
    sdk = CopilotKitSDK(
        api_base_url=config.api_base_url,
        enable_streaming=config.enable_streaming,
        stream_timeout=config.stream_timeout
    )

    # Create LangGraph wrapper
    orchestrator = OrchestratorLangGraph(
        orchestrator_endpoint=get_orchestrator_endpoint(),
        copilotkit_sdk=sdk
    )

    # Generate session ID if not provided
    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:12]}"

    async def event_generator():
        """Generate SSE events from agent execution"""
        try:
            # Execute workflow with streaming
            async for event in orchestrator.execute(
                account_id=request.account_id,
                session_id=session_id,
                user_id=request.user_id
            ):
                # Format as SSE
                yield f"data: {json.dumps(event)}\n\n"

        except Exception as e:
            error_event = {
                "type": "error",
                "session_id": session_id,
                "error": str(e)
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    # Return SSE stream
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )

@router.post("/agent-orchestrator/approval")
async def handle_approval(
    session_id: str,
    approval_response: Dict[str, Any],
    sdk: CopilotKitSDK = Depends(get_copilotkit_sdk)
):
    """
    Handle approval responses from frontend.

    Args:
        session_id: Session identifier
        approval_response: Approval decision from user
        sdk: CopilotKit SDK instance

    Returns:
        Confirmation of approval processing
    """

    # Send approval to waiting agent
    await sdk.send_approval(session_id, approval_response)

    return {"status": "approval_processed", "session_id": session_id}

@router.get("/agent-orchestrator/status/{session_id}")
async def get_session_status(
    session_id: str,
    sdk: CopilotKitSDK = Depends(get_copilotkit_sdk)
):
    """Get current status of agent session"""

    status = await sdk.get_session_status(session_id)

    return {
        "session_id": session_id,
        "status": status.get("current_step", "unknown"),
        "account_id": status.get("account_id"),
        "started_at": status.get("started_at"),
        "updated_at": status.get("updated_at")
    }
```

**Files to Create**:
- `/src/copilotkit/routes/agent_orchestrator.py` - Main FastAPI route
- `/src/copilotkit/routes/approval_routes.py` - Approval handling routes
- `/src/copilotkit/routes/status_routes.py` - Status query routes

**Validation Checkpoint 4.1**:
```python
# test_agent_orchestrator_routes.py
from fastapi.testclient import TestClient

def test_agent_orchestrator_endpoint_exists(client: TestClient):
    """Verify endpoint is registered"""
    response = client.options("/api/agent-orchestrator")
    assert response.status_code != 404

def test_agent_orchestrator_requires_auth(client: TestClient):
    """Verify authentication is required"""
    response = client.post("/api/agent-orchestrator", json={})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_agent_orchestrator_streaming(client: TestClient):
    """Verify SSE streaming works"""
    response = client.post(
        "/api/agent-orchestrator",
        json={
            "account_id": "ACC-001",
            "user_id": "user-123"
        },
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"
```

**Expected Output**: All routes registered, streaming works, auth enforced

---

**Task 4.2: Integrate CopilotKit SDK with FastAPI App**

**Duration**: 2 hours
**Priority**: CRITICAL
**Dependencies**: Task 4.1

**Steps**:
```python
# 4.2.1 Update main FastAPI app to include CopilotKit routes
# File: src/main.py (update existing file)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from copilotkit_langgraph import add_fastapi_endpoint

from src.copilotkit.routes.agent_orchestrator import router as agent_router
from src.copilotkit.config import get_copilotkit_config

# Create FastAPI app
app = FastAPI(
    title="Sergas Super Account Manager API",
    version="1.0.0",
    description="Multi-agent account management with CopilotKit"
)

# Get CopilotKit config
config = get_copilotkit_config()

# Configure CORS for CopilotKit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include CopilotKit routes
app.include_router(agent_router)

# Register CopilotKit endpoint
add_fastapi_endpoint(
    app=app,
    agents=[
        get_orchestrator_langgraph(),
        # Future: individual agent endpoints
    ],
    endpoint="/api/copilotkit"
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "copilotkit_enabled": True,
        "agent_endpoint": config.agent_endpoint
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

**Files to Modify**:
- `/src/main.py` - Update with CopilotKit integration
- `/src/copilotkit/__init__.py` - Export all CopilotKit components

**Validation Checkpoint 4.2**:
```bash
# Start FastAPI server
python -m src.main &

# Wait for startup
sleep 5

# Test health endpoint
curl http://localhost:8000/health | jq .
# Expected: {"status": "healthy", "copilotkit_enabled": true}

# Test CopilotKit endpoint exists
curl http://localhost:8000/api/copilotkit
# Expected: 200 OK

# Test agent orchestrator endpoint
curl -X OPTIONS http://localhost:8000/api/agent-orchestrator
# Expected: 200 OK with CORS headers

# Stop server
pkill -f "python -m src.main"
```

**Expected Output**: Server starts, all endpoints respond, CORS configured

---

### PHASE 2: Frontend Integration (Week 2)

#### Requirement 5: Register Endpoints in Frontend with AG-UI Wrappers

**Task 5.1: Install CopilotKit Client Libraries**

**Duration**: 1 hour
**Priority**: CRITICAL
**Dependencies**: None (can run in parallel with backend tasks)

**Steps**:
```bash
# 5.1.1 Navigate to frontend directory
cd frontend

# 5.1.2 Install CopilotKit React packages
npm install @copilotkit/react-core @copilotkit/react-ui @copilotkit/runtime-client-gql

# 5.1.3 Install AG-UI client library
npm install @ag-ui/react

# 5.1.4 Install additional dependencies
npm install eventsource uuid

# 5.1.5 Update package.json scripts
npm pkg set scripts.dev="next dev"
npm pkg set scripts.build="next build"
npm pkg set scripts.start="next start"

# 5.1.6 Verify installation
npm list @copilotkit/react-core
npm list @ag-ui/react
```

**Files to Modify**:
- `/frontend/package.json` - Update with new dependencies

**Validation Checkpoint 5.1**:
```bash
# Verify packages installed
cd frontend
npm list | grep copilotkit
npm list | grep ag-ui

# Expected output:
# @copilotkit/react-core@1.x.x
# @copilotkit/react-ui@1.x.x
# @ag-ui/react@0.1.x

# Test dev server starts
npm run dev &
sleep 5
curl http://localhost:3000
pkill -f "next dev"
```

**Expected Output**: All packages installed, dev server starts successfully

---

**Task 5.2: Create Next.js API Route for Agent Orchestration**

**Duration**: 3 hours
**Priority**: CRITICAL
**Dependencies**: Task 5.1, Backend Phase 1 complete

**Steps**:
```typescript
// 5.2.1 Create Next.js API route for CopilotKit
// File: frontend/app/api/copilotkit/route.ts

import { CopilotRuntime, OpenAIAdapter } from "@copilotkit/runtime";
import { NextRequest, NextResponse } from "next/server";

export const runtime = "edge";

// Backend API URL (from environment)
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function POST(req: NextRequest) {
  const copilotKit = new CopilotRuntime({
    // Proxy requests to FastAPI backend
    actions: [
      {
        name: "orchestrate_account_analysis",
        description: "Analyze account with multi-agent system",
        parameters: [
          {
            name: "account_id",
            type: "string",
            description: "Zoho account ID",
            required: true
          },
          {
            name: "user_id",
            type: "string",
            description: "Current user ID",
            required: true
          }
        ],
        handler: async ({ account_id, user_id }) => {
          // Forward to FastAPI backend
          const response = await fetch(`${BACKEND_URL}/api/agent-orchestrator`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": req.headers.get("Authorization") || ""
            },
            body: JSON.stringify({
              account_id,
              user_id,
              session_id: crypto.randomUUID()
            })
          });

          if (!response.ok) {
            throw new Error(`Backend error: ${response.statusText}`);
          }

          // Return SSE stream
          return response.body;
        }
      }
    ]
  });

  return copilotKit.response(req);
}
```

```typescript
// 5.2.2 Create AG-UI HTTP agent wrapper
// File: frontend/lib/agents/http-agent-wrapper.ts

import { HttpAgent } from "@ag-ui/react";

export interface AgentConfig {
  name: string;
  endpoint: string;
  description: string;
  backendUrl: string;
}

export class ServasHttpAgent extends HttpAgent {
  constructor(config: AgentConfig) {
    super({
      name: config.name,
      url: `${config.backendUrl}${config.endpoint}`,
      description: config.description,
      headers: {
        "Content-Type": "application/json"
      }
    });
  }

  async execute(input: any): Promise<AsyncIterator<any>> {
    const response = await fetch(this.url, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify(input)
    });

    if (!response.ok) {
      throw new Error(`Agent execution failed: ${response.statusText}`);
    }

    // Parse SSE stream
    return this.parseSSEStream(response.body!);
  }

  private async *parseSSEStream(stream: ReadableStream): AsyncIterator<any> {
    const reader = stream.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            try {
              yield JSON.parse(data);
            } catch (e) {
              console.error("Failed to parse SSE data:", e);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }
}
```

**Files to Create**:
- `/frontend/app/api/copilotkit/route.ts` - Next.js API route
- `/frontend/lib/agents/http-agent-wrapper.ts` - AG-UI HTTP agent wrapper
- `/frontend/lib/agents/orchestrator-agent.ts` - Orchestrator agent client
- `/frontend/lib/agents/agent-factory.ts` - Agent factory

**Validation Checkpoint 5.2**:
```typescript
// test-next-api-route.test.ts
import { POST } from "@/app/api/copilotkit/route";

describe("CopilotKit API Route", () => {
  it("should handle POST requests", async () => {
    const mockRequest = new Request("http://localhost:3000/api/copilotkit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: [{ role: "user", content: "Analyze ACC-001" }]
      })
    });

    const response = await POST(mockRequest);
    expect(response.status).toBe(200);
  });

  it("should proxy to backend", async () => {
    // Test that backend URL is called
    const mockFetch = jest.spyOn(global, "fetch");

    await POST(mockRequest);

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/agent-orchestrator"),
      expect.any(Object)
    );
  });
});
```

**Expected Output**: API route works, proxies to backend, SSE parsing functional

---

**Task 5.3: Implement A2A Middleware Agent**

**Duration**: 4 hours
**Priority**: HIGH
**Dependencies**: Task 5.2

**Steps**:
```typescript
// 5.3.1 Create A2A middleware agent for agent coordination
// File: frontend/lib/agents/a2a-middleware.ts

import { Agent, AgentMessage } from "@ag-ui/react";

export interface A2AMiddlewareConfig {
  orchestratorUrl: string;
  timeout?: number;
  retryAttempts?: number;
}

export class A2AMiddlewareAgent {
  private config: A2AMiddlewareConfig;
  private activeAgents: Map<string, Agent> = new Map();
  private messageQueue: AgentMessage[] = [];

  constructor(config: A2AMiddlewareConfig) {
    this.config = {
      timeout: 60000,
      retryAttempts: 3,
      ...config
    };
  }

  /**
   * Register agent with middleware
   */
  registerAgent(agent: Agent): void {
    this.activeAgents.set(agent.name, agent);
    console.log(`[A2A] Registered agent: ${agent.name}`);
  }

  /**
   * Route message between agents
   */
  async routeMessage(
    fromAgent: string,
    toAgent: string,
    message: AgentMessage
  ): Promise<void> {
    const targetAgent = this.activeAgents.get(toAgent);

    if (!targetAgent) {
      throw new Error(`Agent not found: ${toAgent}`);
    }

    // Add message to queue
    this.messageQueue.push({
      ...message,
      from: fromAgent,
      to: toAgent,
      timestamp: new Date().toISOString()
    });

    // Send to target agent
    await targetAgent.send(message);
  }

  /**
   * Coordinate multi-agent workflow
   */
  async coordinateWorkflow(
    workflow: string[],
    input: any
  ): Promise<any[]> {
    const results: any[] = [];

    for (const agentName of workflow) {
      const agent = this.activeAgents.get(agentName);

      if (!agent) {
        throw new Error(`Agent not found in workflow: ${agentName}`);
      }

      console.log(`[A2A] Executing agent: ${agentName}`);

      // Execute agent with previous results as context
      const result = await agent.execute({
        ...input,
        previousResults: results
      });

      results.push(result);
    }

    return results;
  }

  /**
   * Get agent coordination status
   */
  getCoordinationStatus(): {
    activeAgents: string[];
    messageCount: number;
    lastActivity: string | null;
  } {
    return {
      activeAgents: Array.from(this.activeAgents.keys()),
      messageCount: this.messageQueue.length,
      lastActivity: this.messageQueue[this.messageQueue.length - 1]?.timestamp || null
    };
  }
}
```

**Files to Create**:
- `/frontend/lib/agents/a2a-middleware.ts` - A2A middleware agent
- `/frontend/lib/agents/agent-coordinator.ts` - Agent coordination logic
- `/frontend/lib/agents/message-router.ts` - Message routing between agents

**Validation Checkpoint 5.3**:
```typescript
// test-a2a-middleware.test.ts
describe("A2A Middleware", () => {
  let middleware: A2AMiddlewareAgent;

  beforeEach(() => {
    middleware = new A2AMiddlewareAgent({
      orchestratorUrl: "http://localhost:8000"
    });
  });

  it("should register agents", () => {
    const mockAgent = { name: "test-agent", execute: jest.fn() };
    middleware.registerAgent(mockAgent as any);

    const status = middleware.getCoordinationStatus();
    expect(status.activeAgents).toContain("test-agent");
  });

  it("should route messages between agents", async () => {
    const agent1 = { name: "agent1", send: jest.fn() };
    const agent2 = { name: "agent2", send: jest.fn() };

    middleware.registerAgent(agent1 as any);
    middleware.registerAgent(agent2 as any);

    await middleware.routeMessage("agent1", "agent2", {
      type: "data",
      content: "test message"
    });

    expect(agent2.send).toHaveBeenCalled();
  });

  it("should coordinate multi-agent workflow", async () => {
    const agent1 = { name: "agent1", execute: jest.fn().mockResolvedValue({ data: 1 }) };
    const agent2 = { name: "agent2", execute: jest.fn().mockResolvedValue({ data: 2 }) };

    middleware.registerAgent(agent1 as any);
    middleware.registerAgent(agent2 as any);

    const results = await middleware.coordinateWorkflow(
      ["agent1", "agent2"],
      { input: "test" }
    );

    expect(results).toHaveLength(2);
    expect(agent1.execute).toHaveBeenCalled();
    expect(agent2.execute).toHaveBeenCalled();
  });
});
```

**Expected Output**: A2A middleware routes messages, coordinates workflows

---

#### Requirement 6: Update React Frontend Hooks

**Task 6.1: Create CopilotKit Provider Wrapper**

**Duration**: 2 hours
**Priority**: CRITICAL
**Dependencies**: Task 5.3

**Steps**:
```typescript
// 6.1.1 Create CopilotKit context provider
// File: frontend/components/providers/copilotkit-provider.tsx

"use client";

import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { ReactNode } from "react";

interface CopilotKitProviderProps {
  children: ReactNode;
  runtime?: string;
}

export function CopilotKitProvider({
  children,
  runtime = "/api/copilotkit"
}: CopilotKitProviderProps) {
  return (
    <CopilotKit
      runtimeUrl={runtime}
      agent="orchestrator"
      showDevConsole={process.env.NODE_ENV === "development"}
    >
      <CopilotSidebar
        defaultOpen={false}
        labels={{
          title: "Account Manager Assistant",
          initial: "Hello! I can help analyze accounts and generate recommendations.",
        }}
        instructions="You are an AI account manager assistant. Help analyze Zoho CRM accounts and generate actionable recommendations."
      >
        {children}
      </CopilotSidebar>
    </CopilotKit>
  );
}
```

```typescript
// 6.1.2 Update root layout with provider
// File: frontend/app/layout.tsx (modify existing)

import { CopilotKitProvider } from "@/components/providers/copilotkit-provider";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <CopilotKitProvider>
          {children}
        </CopilotKitProvider>
      </body>
    </html>
  );
}
```

**Files to Create/Modify**:
- `/frontend/components/providers/copilotkit-provider.tsx` - CopilotKit provider
- `/frontend/app/layout.tsx` - Update root layout (modify existing)

**Validation Checkpoint 6.1**:
```typescript
// test-copilotkit-provider.test.tsx
import { render, screen } from "@testing-library/react";
import { CopilotKitProvider } from "@/components/providers/copilotkit-provider";

describe("CopilotKitProvider", () => {
  it("should render children", () => {
    render(
      <CopilotKitProvider>
        <div>Test Content</div>
      </CopilotKitProvider>
    );

    expect(screen.getByText("Test Content")).toBeInTheDocument();
  });

  it("should initialize CopilotKit with correct runtime", () => {
    const { container } = render(
      <CopilotKitProvider runtime="/custom/runtime">
        <div>Test</div>
      </CopilotKitProvider>
    );

    // Verify CopilotKit is initialized
    expect(container.querySelector('[data-copilotkit]')).toBeInTheDocument();
  });
});
```

**Expected Output**: Provider wraps app, CopilotKit initializes correctly

---

**Task 6.2: Implement useCopilotAction Hook**

**Duration**: 3 hours
**Priority**: CRITICAL
**Dependencies**: Task 6.1

**Steps**:
```typescript
// 6.2.1 Create custom hooks for agent actions
// File: frontend/hooks/use-account-analysis.ts

import { useCopilotAction } from "@copilotkit/react-core";
import { useState, useCallback } from "react";

export interface AccountAnalysisResult {
  account_id: string;
  session_id: string;
  zoho_snapshot: any;
  historical_context: any;
  recommendations: any[];
  status: "pending" | "analyzing" | "complete" | "error";
}

export function useAccountAnalysis() {
  const [analysisState, setAnalysisState] = useState<AccountAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  useCopilotAction({
    name: "analyze_account",
    description: "Analyze a Zoho CRM account with multi-agent system",
    parameters: [
      {
        name: "account_id",
        type: "string",
        description: "Zoho account ID to analyze",
        required: true
      }
    ],
    handler: useCallback(async ({ account_id }) => {
      setIsAnalyzing(true);
      setAnalysisState({
        account_id,
        session_id: crypto.randomUUID(),
        zoho_snapshot: null,
        historical_context: null,
        recommendations: [],
        status: "analyzing"
      });

      try {
        // Action will trigger backend agent execution
        // Results will stream back via CopilotKit
        return {
          status: "started",
          account_id,
          message: "Analysis started. Agents are processing..."
        };
      } catch (error) {
        setAnalysisState(prev => prev ? { ...prev, status: "error" } : null);
        throw error;
      } finally {
        setIsAnalyzing(false);
      }
    }, []),

    render: useCallback((props) => {
      // Custom UI rendering for analysis progress
      return (
        <div className="analysis-progress">
          <h3>Analyzing Account: {props.account_id}</h3>
          <div className="progress-bar">
            {/* Show real-time progress */}
          </div>
        </div>
      );
    }, [])
  });

  return {
    analysisState,
    isAnalyzing,
    startAnalysis: (account_id: string) => {
      // Trigger via CopilotKit
      return { action: "analyze_account", args: { account_id } };
    }
  };
}
```

```typescript
// 6.2.2 Create approval action hook
// File: frontend/hooks/use-approval-workflow.ts

import { useCopilotAction } from "@copilotkit/react-core";
import { useState, useCallback } from "react";

export interface ApprovalRequest {
  id: string;
  recommendation: any;
  account_id: string;
  priority: "high" | "medium" | "low";
  status: "pending" | "approved" | "rejected" | "modified";
}

export function useApprovalWorkflow() {
  const [pendingApprovals, setPendingApprovals] = useState<ApprovalRequest[]>([]);

  useCopilotAction({
    name: "approve_recommendation",
    description: "Approve or reject an AI-generated recommendation",
    parameters: [
      {
        name: "approval_id",
        type: "string",
        description: "Approval request ID",
        required: true
      },
      {
        name: "decision",
        type: "string",
        description: "Approval decision: approve, reject, or modify",
        required: true
      },
      {
        name: "modifications",
        type: "object",
        description: "Optional modifications to recommendation"
      }
    ],
    handler: useCallback(async ({ approval_id, decision, modifications }) => {
      // Send approval to backend
      const response = await fetch("/api/agent-orchestrator/approval", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: approval_id,
          decision,
          modifications
        })
      });

      if (!response.ok) {
        throw new Error("Approval failed");
      }

      // Update local state
      setPendingApprovals(prev =>
        prev.map(a =>
          a.id === approval_id
            ? { ...a, status: decision as any }
            : a
        )
      );

      return {
        status: "processed",
        approval_id,
        decision
      };
    }, []),

    render: useCallback((props) => {
      return (
        <div className="approval-card">
          <h4>Approval Request: {props.approval_id}</h4>
          <div className="approval-actions">
            <button onClick={() => props.handler({ decision: "approve" })}>
              Approve
            </button>
            <button onClick={() => props.handler({ decision: "reject" })}>
              Reject
            </button>
            <button onClick={() => props.handler({ decision: "modify" })}>
              Modify
            </button>
          </div>
        </div>
      );
    }, [])
  });

  return {
    pendingApprovals,
    setPendingApprovals
  };
}
```

**Files to Create**:
- `/frontend/hooks/use-account-analysis.ts` - Account analysis hook
- `/frontend/hooks/use-approval-workflow.ts` - Approval workflow hook
- `/frontend/hooks/use-agent-status.ts` - Agent status monitoring hook

**Validation Checkpoint 6.2**:
```typescript
// test-copilot-hooks.test.ts
import { renderHook, act } from "@testing-library/react";
import { useAccountAnalysis } from "@/hooks/use-account-analysis";

describe("useAccountAnalysis", () => {
  it("should initialize with correct state", () => {
    const { result } = renderHook(() => useAccountAnalysis());

    expect(result.current.isAnalyzing).toBe(false);
    expect(result.current.analysisState).toBeNull();
  });

  it("should start analysis", async () => {
    const { result } = renderHook(() => useAccountAnalysis());

    act(() => {
      result.current.startAnalysis("ACC-001");
    });

    expect(result.current.isAnalyzing).toBe(true);
    expect(result.current.analysisState?.account_id).toBe("ACC-001");
  });
});

describe("useApprovalWorkflow", () => {
  it("should handle approval", async () => {
    const { result } = renderHook(() => useApprovalWorkflow());

    // Mock pending approval
    act(() => {
      result.current.setPendingApprovals([
        {
          id: "approval-1",
          recommendation: {},
          account_id: "ACC-001",
          priority: "high",
          status: "pending"
        }
      ]);
    });

    // Approve
    await act(async () => {
      await result.current.approveRecommendation("approval-1", "approve");
    });

    expect(result.current.pendingApprovals[0].status).toBe("approved");
  });
});
```

**Expected Output**: Hooks work, trigger backend actions, handle approvals

---

**Task 6.3: Implement useCoAgent Hook for Multi-Agent Display**

**Duration**: 3 hours
**Priority**: HIGH
**Dependencies**: Task 6.2

**Steps**:
```typescript
// 6.3.1 Create multi-agent monitoring hook
// File: frontend/hooks/use-agent-coordination.ts

import { useCoAgent } from "@copilotkit/react-core";
import { useState, useEffect } from "react";

export interface AgentStatus {
  name: string;
  state: "idle" | "active" | "waiting" | "complete" | "error";
  currentStep: string | null;
  progress: number;
  output: any;
  error: string | null;
}

export function useAgentCoordination(session_id: string) {
  const [agents, setAgents] = useState<Map<string, AgentStatus>>(new Map());

  // Monitor Zoho Data Scout
  const zohoScout = useCoAgent({
    name: "zoho-data-scout",
    description: "Retrieves account data from Zoho CRM",
    onStateChange: (state) => {
      setAgents(prev => {
        const next = new Map(prev);
        next.set("zoho-data-scout", {
          name: "Zoho Data Scout",
          state: state.status as any,
          currentStep: state.current_step,
          progress: state.progress || 0,
          output: state.output,
          error: state.error
        });
        return next;
      });
    }
  });

  // Monitor Memory Analyst
  const memoryAnalyst = useCoAgent({
    name: "memory-analyst",
    description: "Analyzes historical account context",
    onStateChange: (state) => {
      setAgents(prev => {
        const next = new Map(prev);
        next.set("memory-analyst", {
          name: "Memory Analyst",
          state: state.status as any,
          currentStep: state.current_step,
          progress: state.progress || 0,
          output: state.output,
          error: state.error
        });
        return next;
      });
    }
  });

  // Monitor Recommendation Author
  const recommendationAuthor = useCoAgent({
    name: "recommendation-author",
    description: "Generates actionable recommendations",
    onStateChange: (state) => {
      setAgents(prev => {
        const next = new Map(prev);
        next.set("recommendation-author", {
          name: "Recommendation Author",
          state: state.status as any,
          currentStep: state.current_step,
          progress: state.progress || 0,
          output: state.output,
          error: state.error
        });
        return next;
      });
    }
  });

  // Calculate overall progress
  const overallProgress = Array.from(agents.values()).reduce(
    (sum, agent) => sum + agent.progress,
    0
  ) / Math.max(agents.size, 1);

  // Check if any agents have errors
  const hasErrors = Array.from(agents.values()).some(a => a.error !== null);

  // Check if all agents complete
  const allComplete = agents.size > 0 && Array.from(agents.values()).every(
    a => a.state === "complete"
  );

  return {
    agents: Array.from(agents.values()),
    overallProgress,
    hasErrors,
    allComplete,
    activeAgent: Array.from(agents.values()).find(a => a.state === "active")
  };
}
```

**Files to Create**:
- `/frontend/hooks/use-agent-coordination.ts` - Multi-agent coordination hook
- `/frontend/components/agent-monitor/agent-status-card.tsx` - Agent status UI
- `/frontend/components/agent-monitor/agent-progress-bar.tsx` - Progress visualization

**Validation Checkpoint 6.3**:
```typescript
// test-agent-coordination.test.ts
import { renderHook } from "@testing-library/react";
import { useAgentCoordination } from "@/hooks/use-agent-coordination";

describe("useAgentCoordination", () => {
  it("should track multiple agents", () => {
    const { result } = renderHook(() => useAgentCoordination("sess-123"));

    // Initially no agents
    expect(result.current.agents).toHaveLength(0);
    expect(result.current.overallProgress).toBe(0);
  });

  it("should calculate overall progress", () => {
    const { result } = renderHook(() => useAgentCoordination("sess-123"));

    // Mock agent state updates
    act(() => {
      result.current.updateAgentState("zoho-scout", { progress: 100 });
      result.current.updateAgentState("memory-analyst", { progress: 50 });
    });

    expect(result.current.overallProgress).toBe(75); // (100 + 50) / 2
  });

  it("should detect errors", () => {
    const { result } = renderHook(() => useAgentCoordination("sess-123"));

    act(() => {
      result.current.updateAgentState("zoho-scout", { error: "API error" });
    });

    expect(result.current.hasErrors).toBe(true);
  });
});
```

**Expected Output**: Multi-agent monitoring works, progress calculated, errors detected

---

### PHASE 3: Testing & Validation (Week 3)

#### Requirement 7: Test Agent Orchestration

**Task 7.1: Create End-to-End Test Suite**

**Duration**: 8 hours
**Priority**: CRITICAL
**Dependencies**: All Phase 1 & 2 tasks complete

**Steps**:
```python
# 7.1.1 Create comprehensive E2E test suite
# File: tests/e2e/test_copilotkit_integration.py

import pytest
import asyncio
from httpx import AsyncClient
import json

@pytest.mark.asyncio
async def test_full_agent_workflow():
    """
    Test complete agent workflow from frontend to backend.

    Workflow:
    1. Frontend triggers analysis via CopilotKit
    2. Backend agents execute in sequence
    3. Recommendations generated
    4. Approval requested
    5. User approves
    6. Confirmation returned
    """

    async with AsyncClient(base_url="http://localhost:8000") as client:
        # Step 1: Start analysis
        response = await client.post(
            "/api/agent-orchestrator",
            json={
                "account_id": "ACC-TEST-001",
                "user_id": "user-test",
                "session_id": "sess-test-123"
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"

        # Step 2: Parse SSE stream
        events = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                event = json.loads(line[6:])
                events.append(event)

                # Stop at approval request
                if event.get("type") == "approval_request":
                    break

        # Step 3: Verify agent events received
        event_types = [e["type"] for e in events]
        assert "agent_started" in event_types
        assert "tool_call" in event_types
        assert "tool_result" in event_types
        assert "agent_completed" in event_types
        assert "approval_request" in event_types

        # Step 4: Send approval
        approval_event = next(e for e in events if e["type"] == "approval_request")

        approval_response = await client.post(
            "/api/agent-orchestrator/approval",
            json={
                "session_id": "sess-test-123",
                "decision": "approve",
                "modifications": None
            }
        )

        assert approval_response.status_code == 200
        result = approval_response.json()
        assert result["status"] == "approval_processed"

@pytest.mark.asyncio
async def test_zoho_scout_agent_execution():
    """Test Zoho Data Scout agent execution"""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.post(
            "/api/agent-orchestrator",
            json={"account_id": "ACC-001", "user_id": "test"}
        )

        # Collect Zoho Scout events
        zoho_events = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                event = json.loads(line[6:])
                if event.get("agent") == "zoho_data_scout":
                    zoho_events.append(event)

                # Stop after scout completes
                if (event.get("type") == "agent_completed" and
                    event.get("agent") == "zoho_data_scout"):
                    break

        # Verify Zoho Scout events
        assert len(zoho_events) > 0
        assert any(e["type"] == "agent_started" for e in zoho_events)
        assert any(e["type"] == "tool_call" for e in zoho_events)
        assert any(e["type"] == "agent_completed" for e in zoho_events)

@pytest.mark.asyncio
async def test_memory_analyst_agent_execution():
    """Test Memory Analyst agent execution"""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.post(
            "/api/agent-orchestrator",
            json={"account_id": "ACC-001", "user_id": "test"}
        )

        # Collect Memory Analyst events
        memory_events = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                event = json.loads(line[6:])
                if event.get("agent") == "memory_analyst":
                    memory_events.append(event)

                if (event.get("type") == "agent_completed" and
                    event.get("agent") == "memory_analyst"):
                    break

        # Verify Memory Analyst events
        assert len(memory_events) > 0
        assert any("cognee" in e.get("tool_name", "") for e in memory_events)

@pytest.mark.asyncio
async def test_recommendation_author_with_approval():
    """Test Recommendation Author with approval workflow"""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        # Start workflow
        response = await client.post(
            "/api/agent-orchestrator",
            json={"account_id": "ACC-001", "user_id": "test"}
        )

        # Wait for approval request
        approval_id = None
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                event = json.loads(line[6:])

                if event.get("type") == "approval_request":
                    approval_id = event["session_id"]
                    recommendations = event["recommendations"]
                    assert len(recommendations) > 0
                    break

        assert approval_id is not None

        # Approve first recommendation
        approval_response = await client.post(
            f"/api/agent-orchestrator/approval",
            json={
                "session_id": approval_id,
                "decision": "approve",
                "approved_ids": [recommendations[0]["id"]]
            }
        )

        assert approval_response.status_code == 200

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in agent workflow"""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        # Trigger error with invalid account ID
        response = await client.post(
            "/api/agent-orchestrator",
            json={"account_id": "INVALID", "user_id": "test"}
        )

        # Collect events until error
        error_event = None
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                event = json.loads(line[6:])
                if event.get("type") == "error":
                    error_event = event
                    break

        assert error_event is not None
        assert "error_message" in error_event

@pytest.mark.asyncio
async def test_concurrent_sessions():
    """Test multiple concurrent agent sessions"""

    async def run_session(account_id: str):
        async with AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.post(
                "/api/agent-orchestrator",
                json={"account_id": account_id, "user_id": "test"}
            )

            events = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event = json.loads(line[6:])
                    events.append(event)

                    if event.get("type") == "approval_request":
                        break

            return events

    # Run 5 concurrent sessions
    results = await asyncio.gather(
        run_session("ACC-001"),
        run_session("ACC-002"),
        run_session("ACC-003"),
        run_session("ACC-004"),
        run_session("ACC-005")
    )

    # Verify all sessions completed
    for events in results:
        assert len(events) > 0
        assert any(e["type"] == "approval_request" for e in events)
```

**Files to Create**:
- `/tests/e2e/test_copilotkit_integration.py` - E2E test suite
- `/tests/e2e/test_approval_workflow.py` - Approval workflow tests
- `/tests/e2e/test_agent_coordination.py` - Multi-agent coordination tests
- `/tests/e2e/conftest.py` - E2E test fixtures

**Validation Checkpoint 7.1**:
```bash
# Run E2E tests
pytest tests/e2e/test_copilotkit_integration.py -v

# Expected output:
# tests/e2e/test_copilotkit_integration.py::test_full_agent_workflow PASSED
# tests/e2e/test_copilotkit_integration.py::test_zoho_scout_agent_execution PASSED
# tests/e2e/test_copilotkit_integration.py::test_memory_analyst_agent_execution PASSED
# tests/e2e/test_copilotkit_integration.py::test_recommendation_author_with_approval PASSED
# tests/e2e/test_copilotkit_integration.py::test_error_handling PASSED
# tests/e2e/test_copilotkit_integration.py::test_concurrent_sessions PASSED
# ==================== 6 passed in 15.42s ====================
```

**Expected Output**: All E2E tests pass, workflow functions correctly

---

**Task 7.2: Frontend Integration Testing**

**Duration**: 4 hours
**Priority**: HIGH
**Dependencies**: Task 7.1

**Steps**:
```typescript
// 7.2.1 Create frontend integration tests
// File: frontend/__tests__/integration/copilotkit-integration.test.tsx

import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { CopilotKitProvider } from "@/components/providers/copilotkit-provider";
import { AccountAnalysisPage } from "@/app/accounts/[id]/page";

// Mock API
jest.mock("@/lib/api", () => ({
  analyzeAccount: jest.fn(),
  approveRecommendation: jest.fn()
}));

describe("CopilotKit Integration", () => {
  beforeEach(() => {
    // Mock SSE stream
    global.EventSource = jest.fn(() => ({
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      close: jest.fn()
    })) as any;
  });

  it("should display agent analysis in real-time", async () => {
    render(
      <CopilotKitProvider>
        <AccountAnalysisPage params={{ id: "ACC-001" }} />
      </CopilotKitProvider>
    );

    // Click analyze button
    const analyzeButton = screen.getByRole("button", { name: /analyze/i });
    fireEvent.click(analyzeButton);

    // Wait for agents to appear
    await waitFor(() => {
      expect(screen.getByText(/Zoho Data Scout/i)).toBeInTheDocument();
      expect(screen.getByText(/Memory Analyst/i)).toBeInTheDocument();
      expect(screen.getByText(/Recommendation Author/i)).toBeInTheDocument();
    });

    // Verify progress indicators
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("should handle approval workflow", async () => {
    render(
      <CopilotKitProvider>
        <AccountAnalysisPage params={{ id: "ACC-001" }} />
      </CopilotKitProvider>
    );

    // Trigger analysis
    fireEvent.click(screen.getByRole("button", { name: /analyze/i }));

    // Wait for approval request
    await waitFor(() => {
      expect(screen.getByText(/Approve Recommendation/i)).toBeInTheDocument();
    });

    // Approve recommendation
    const approveButton = screen.getByRole("button", { name: /approve/i });
    fireEvent.click(approveButton);

    // Verify approval processed
    await waitFor(() => {
      expect(screen.getByText(/Approved/i)).toBeInTheDocument();
    });
  });

  it("should display agent errors", async () => {
    // Mock API error
    const mockError = new Error("Zoho API error");
    (global.EventSource as any).mockImplementationOnce(() => ({
      addEventListener: (_: string, callback: Function) => {
        callback({
          data: JSON.stringify({
            type: "error",
            error_message: "Zoho API error"
          })
        });
      },
      removeEventListener: jest.fn(),
      close: jest.fn()
    }));

    render(
      <CopilotKitProvider>
        <AccountAnalysisPage params={{ id: "ACC-001" }} />
      </CopilotKitProvider>
    );

    fireEvent.click(screen.getByRole("button", { name: /analyze/i }));

    // Verify error displayed
    await waitFor(() => {
      expect(screen.getByText(/Zoho API error/i)).toBeInTheDocument();
    });
  });

  it("should handle concurrent agent execution", async () => {
    render(
      <CopilotKitProvider>
        <AccountAnalysisPage params={{ id: "ACC-001" }} />
      </CopilotKitProvider>
    );

    fireEvent.click(screen.getByRole("button", { name: /analyze/i }));

    // Wait for all agents to be active
    await waitFor(() => {
      const activeAgents = screen.getAllByTestId("agent-status-active");
      expect(activeAgents.length).toBeGreaterThan(0);
    });
  });
});
```

**Files to Create**:
- `/frontend/__tests__/integration/copilotkit-integration.test.tsx` - Frontend integration tests
- `/frontend/__tests__/integration/approval-workflow.test.tsx` - Approval UI tests
- `/frontend/__tests__/integration/agent-monitoring.test.tsx` - Agent monitoring tests

**Validation Checkpoint 7.2**:
```bash
# Run frontend integration tests
cd frontend
npm run test:integration

# Expected output:
# PASS  __tests__/integration/copilotkit-integration.test.tsx
#   CopilotKit Integration
#     ✓ should display agent analysis in real-time (2154 ms)
#     ✓ should handle approval workflow (1843 ms)
#     ✓ should display agent errors (421 ms)
#     ✓ should handle concurrent agent execution (1932 ms)
#
# Test Suites: 1 passed, 1 total
# Tests:       4 passed, 4 total
```

**Expected Output**: All frontend integration tests pass

---

#### Requirement 8: Implement Monitoring

**Task 8.1: Add Logging and Metrics**

**Duration**: 4 hours
**Priority**: HIGH
**Dependencies**: Task 7.2

**Steps**:
```python
# 8.1.1 Create monitoring module
# File: src/monitoring/copilotkit_metrics.py

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge
import structlog

logger = structlog.get_logger(__name__)

# Prometheus metrics
copilotkit_requests_total = Counter(
    "copilotkit_requests_total",
    "Total CopilotKit agent requests",
    ["agent", "status"]
)

copilotkit_request_duration = Histogram(
    "copilotkit_request_duration_seconds",
    "CopilotKit request duration",
    ["agent"]
)

copilotkit_active_sessions = Gauge(
    "copilotkit_active_sessions",
    "Number of active CopilotKit sessions"
)

copilotkit_approval_requests = Counter(
    "copilotkit_approval_requests_total",
    "Total approval requests",
    ["account_id", "status"]
)

@dataclass
class SessionMetrics:
    """Metrics for a single CopilotKit session"""
    session_id: str
    account_id: str
    user_id: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    agents_executed: list[str] = field(default_factory=list)
    approval_count: int = 0
    error_count: int = 0
    status: str = "active"

class CopilotKitMonitor:
    """
    Monitoring and metrics collection for CopilotKit integration.

    Tracks:
    - Session lifecycle
    - Agent execution
    - Approval workflows
    - Errors and performance
    """

    def __init__(self):
        self.logger = logger.bind(component="copilotkit_monitor")
        self.active_sessions: Dict[str, SessionMetrics] = {}

    def start_session(
        self,
        session_id: str,
        account_id: str,
        user_id: str
    ) -> SessionMetrics:
        """Start tracking a new session"""

        metrics = SessionMetrics(
            session_id=session_id,
            account_id=account_id,
            user_id=user_id
        )

        self.active_sessions[session_id] = metrics
        copilotkit_active_sessions.inc()

        self.logger.info(
            "session_started",
            session_id=session_id,
            account_id=account_id,
            user_id=user_id
        )

        return metrics

    def track_agent_execution(
        self,
        session_id: str,
        agent_name: str,
        duration: float,
        status: str
    ):
        """Track agent execution metrics"""

        if session_id in self.active_sessions:
            self.active_sessions[session_id].agents_executed.append(agent_name)

            if status == "error":
                self.active_sessions[session_id].error_count += 1

        copilotkit_requests_total.labels(agent=agent_name, status=status).inc()
        copilotkit_request_duration.labels(agent=agent_name).observe(duration)

        self.logger.info(
            "agent_executed",
            session_id=session_id,
            agent=agent_name,
            duration_seconds=duration,
            status=status
        )

    def track_approval_request(
        self,
        session_id: str,
        account_id: str,
        decision: str
    ):
        """Track approval request metrics"""

        if session_id in self.active_sessions:
            self.active_sessions[session_id].approval_count += 1

        copilotkit_approval_requests.labels(
            account_id=account_id,
            status=decision
        ).inc()

        self.logger.info(
            "approval_tracked",
            session_id=session_id,
            account_id=account_id,
            decision=decision
        )

    def complete_session(
        self,
        session_id: str,
        status: str = "success"
    ):
        """Complete session tracking"""

        if session_id not in self.active_sessions:
            self.logger.warning("session_not_found", session_id=session_id)
            return

        metrics = self.active_sessions[session_id]
        metrics.completed_at = datetime.utcnow()
        metrics.duration_seconds = (
            metrics.completed_at - metrics.started_at
        ).total_seconds()
        metrics.status = status

        copilotkit_active_sessions.dec()

        self.logger.info(
            "session_completed",
            session_id=session_id,
            duration_seconds=metrics.duration_seconds,
            agents_executed=len(metrics.agents_executed),
            approval_count=metrics.approval_count,
            error_count=metrics.error_count,
            status=status
        )

        # Remove from active sessions
        del self.active_sessions[session_id]

    def get_session_metrics(self, session_id: str) -> Optional[SessionMetrics]:
        """Get metrics for a specific session"""
        return self.active_sessions.get(session_id)

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all monitoring metrics"""
        return {
            "active_sessions": len(self.active_sessions),
            "sessions": [
                {
                    "session_id": m.session_id,
                    "account_id": m.account_id,
                    "duration": m.duration_seconds,
                    "agents": m.agents_executed,
                    "approvals": m.approval_count,
                    "errors": m.error_count,
                    "status": m.status
                }
                for m in self.active_sessions.values()
            ]
        }

# Global monitor instance
_monitor: Optional[CopilotKitMonitor] = None

def get_copilotkit_monitor() -> CopilotKitMonitor:
    """Get CopilotKit monitor singleton"""
    global _monitor
    if _monitor is None:
        _monitor = CopilotKitMonitor()
    return _monitor
```

**Files to Create**:
- `/src/monitoring/copilotkit_metrics.py` - Metrics collection
- `/src/monitoring/copilotkit_logger.py` - Structured logging
- `/src/monitoring/dashboard_exporter.py` - Dashboard data export

**Validation Checkpoint 8.1**:
```python
# test_copilotkit_monitoring.py
def test_session_tracking():
    """Test session metrics tracking"""
    monitor = CopilotKitMonitor()

    metrics = monitor.start_session("sess-1", "ACC-001", "user-1")
    assert metrics.session_id == "sess-1"
    assert len(monitor.active_sessions) == 1

    monitor.track_agent_execution("sess-1", "zoho-scout", 2.5, "success")
    assert "zoho-scout" in metrics.agents_executed

    monitor.complete_session("sess-1", "success")
    assert len(monitor.active_sessions) == 0
    assert metrics.status == "success"

def test_approval_tracking():
    """Test approval metrics tracking"""
    monitor = CopilotKitMonitor()

    monitor.start_session("sess-1", "ACC-001", "user-1")
    monitor.track_approval_request("sess-1", "ACC-001", "approve")

    metrics = monitor.get_session_metrics("sess-1")
    assert metrics.approval_count == 1
```

**Expected Output**: Monitoring tracks all sessions, metrics exported correctly

---

**Task 8.2: Create Monitoring Dashboard**

**Duration**: 4 hours
**Priority**: MEDIUM
**Dependencies**: Task 8.1

**Steps**:
```python
# 8.2.1 Create dashboard API endpoint
# File: src/monitoring/dashboard_api.py

from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from datetime import datetime, timedelta

from src.monitoring.copilotkit_metrics import get_copilotkit_monitor

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

@router.get("/dashboard")
async def get_dashboard_data() -> Dict[str, Any]:
    """
    Get comprehensive monitoring dashboard data.

    Returns:
        Dashboard data with metrics, active sessions, and trends
    """
    monitor = get_copilotkit_monitor()

    metrics = monitor.get_all_metrics()

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "active_sessions": metrics["active_sessions"],
        "sessions": metrics["sessions"],
        "performance": {
            "avg_session_duration": _calculate_avg_duration(metrics["sessions"]),
            "avg_agents_per_session": _calculate_avg_agents(metrics["sessions"]),
            "error_rate": _calculate_error_rate(metrics["sessions"])
        },
        "approvals": {
            "total_requests": sum(s["approvals"] for s in metrics["sessions"]),
            "avg_per_session": _calculate_avg_approvals(metrics["sessions"])
        }
    }

@router.get("/sessions")
async def get_active_sessions() -> List[Dict[str, Any]]:
    """Get all active sessions"""
    monitor = get_copilotkit_monitor()
    metrics = monitor.get_all_metrics()
    return metrics["sessions"]

@router.get("/sessions/{session_id}")
async def get_session_details(session_id: str) -> Dict[str, Any]:
    """Get detailed metrics for specific session"""
    monitor = get_copilotkit_monitor()
    metrics = monitor.get_session_metrics(session_id)

    if not metrics:
        return {"error": "Session not found"}

    return {
        "session_id": metrics.session_id,
        "account_id": metrics.account_id,
        "user_id": metrics.user_id,
        "started_at": metrics.started_at.isoformat(),
        "duration_seconds": metrics.duration_seconds,
        "agents_executed": metrics.agents_executed,
        "approval_count": metrics.approval_count,
        "error_count": metrics.error_count,
        "status": metrics.status
    }

def _calculate_avg_duration(sessions: List[Dict[str, Any]]) -> float:
    if not sessions:
        return 0.0
    return sum(s["duration"] for s in sessions) / len(sessions)

def _calculate_avg_agents(sessions: List[Dict[str, Any]]) -> float:
    if not sessions:
        return 0.0
    return sum(len(s["agents"]) for s in sessions) / len(sessions)

def _calculate_error_rate(sessions: List[Dict[str, Any]]) -> float:
    if not sessions:
        return 0.0
    errors = sum(s["errors"] for s in sessions)
    total = len(sessions)
    return (errors / total) * 100 if total > 0 else 0.0

def _calculate_avg_approvals(sessions: List[Dict[str, Any]]) -> float:
    if not sessions:
        return 0.0
    return sum(s["approvals"] for s in sessions) / len(sessions)
```

```typescript
// 8.2.2 Create frontend monitoring dashboard
// File: frontend/app/monitoring/page.tsx

"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

interface DashboardData {
  active_sessions: number;
  sessions: any[];
  performance: {
    avg_session_duration: number;
    avg_agents_per_session: number;
    error_rate: number;
  };
  approvals: {
    total_requests: number;
    avg_per_session: number;
  };
}

export default function MonitoringDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch dashboard data
    async function fetchData() {
      try {
        const response = await fetch("/api/monitoring/dashboard");
        const json = await response.json();
        setData(json);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();

    // Refresh every 5 seconds
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div>Loading dashboard...</div>;
  }

  if (!data) {
    return <div>No data available</div>;
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">CopilotKit Monitoring</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardHeader>
            <CardTitle>Active Sessions</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">{data.active_sessions}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Avg Duration</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">
              {data.performance.avg_session_duration.toFixed(1)}s
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Error Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">
              {data.performance.error_rate.toFixed(1)}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Total Approvals</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">
              {data.approvals.total_requests}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Active Sessions</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full">
            <thead>
              <tr>
                <th>Session ID</th>
                <th>Account ID</th>
                <th>Duration</th>
                <th>Agents</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.sessions.map((session) => (
                <tr key={session.session_id}>
                  <td>{session.session_id}</td>
                  <td>{session.account_id}</td>
                  <td>{session.duration.toFixed(1)}s</td>
                  <td>{session.agents.length}</td>
                  <td>{session.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
```

**Files to Create**:
- `/src/monitoring/dashboard_api.py` - Dashboard API endpoints
- `/frontend/app/monitoring/page.tsx` - Monitoring dashboard UI
- `/frontend/components/monitoring/session-card.tsx` - Session display component

**Validation Checkpoint 8.2**:
```bash
# Test dashboard API
curl http://localhost:8000/api/monitoring/dashboard | jq .

# Expected output:
# {
#   "timestamp": "2025-10-19T...",
#   "active_sessions": 2,
#   "sessions": [...],
#   "performance": {
#     "avg_session_duration": 15.3,
#     "avg_agents_per_session": 3.0,
#     "error_rate": 0.5
#   },
#   "approvals": {
#     "total_requests": 5,
#     "avg_per_session": 2.5
#   }
# }

# Test frontend dashboard
cd frontend
npm run dev
# Navigate to http://localhost:3000/monitoring
# Verify dashboard displays metrics
```

**Expected Output**: Dashboard displays real-time metrics, updates automatically

---

## 3. File Manifest

### Backend Files (Python)

#### New Files to Create (28 files)

**CopilotKit Core** (src/copilotkit/):
1. `src/copilotkit/__init__.py`
2. `src/copilotkit/config.py`
3. `src/copilotkit/agents/__init__.py`
4. `src/copilotkit/agents/orchestrator_endpoint.py`
5. `src/copilotkit/agents/zoho_scout_endpoint.py`
6. `src/copilotkit/agents/memory_analyst_endpoint.py`
7. `src/copilotkit/agents/recommendation_author_endpoint.py`
8. `src/copilotkit/wrappers/__init__.py`
9. `src/copilotkit/wrappers/base_langgraph_wrapper.py`
10. `src/copilotkit/wrappers/orchestrator_langgraph.py`
11. `src/copilotkit/wrappers/approval_handler.py`
12. `src/copilotkit/routes/__init__.py`
13. `src/copilotkit/routes/agent_orchestrator.py`
14. `src/copilotkit/routes/approval_routes.py`
15. `src/copilotkit/routes/status_routes.py`
16. `src/copilotkit/middleware/__init__.py`

**Monitoring** (src/monitoring/):
17. `src/monitoring/copilotkit_metrics.py`
18. `src/monitoring/copilotkit_logger.py`
19. `src/monitoring/dashboard_api.py`
20. `src/monitoring/dashboard_exporter.py`

**Tests** (tests/):
21. `tests/e2e/test_copilotkit_integration.py`
22. `tests/e2e/test_approval_workflow.py`
23. `tests/e2e/test_agent_coordination.py`
24. `tests/e2e/conftest.py`
25. `tests/unit/test_copilotkit_config.py`
26. `tests/unit/test_endpoint_wrappers.py`
27. `tests/unit/test_langgraph_wrappers.py`
28. `tests/unit/test_copilotkit_monitoring.py`

#### Files to Modify (2 files)

1. `requirements.txt` - Add CopilotKit dependencies
2. `src/main.py` - Integrate CopilotKit routes

### Frontend Files (TypeScript/React)

#### New Files to Create (20 files)

**Next.js API Routes** (frontend/app/api/):
1. `frontend/app/api/copilotkit/route.ts`

**Agent Wrappers** (frontend/lib/agents/):
2. `frontend/lib/agents/http-agent-wrapper.ts`
3. `frontend/lib/agents/orchestrator-agent.ts`
4. `frontend/lib/agents/agent-factory.ts`
5. `frontend/lib/agents/a2a-middleware.ts`
6. `frontend/lib/agents/agent-coordinator.ts`
7. `frontend/lib/agents/message-router.ts`

**React Hooks** (frontend/hooks/):
8. `frontend/hooks/use-account-analysis.ts`
9. `frontend/hooks/use-approval-workflow.ts`
10. `frontend/hooks/use-agent-status.ts`
11. `frontend/hooks/use-agent-coordination.ts`

**Components** (frontend/components/):
12. `frontend/components/providers/copilotkit-provider.tsx`
13. `frontend/components/agent-monitor/agent-status-card.tsx`
14. `frontend/components/agent-monitor/agent-progress-bar.tsx`
15. `frontend/components/monitoring/session-card.tsx`

**Pages** (frontend/app/):
16. `frontend/app/monitoring/page.tsx`

**Tests** (frontend/__tests__/):
17. `frontend/__tests__/integration/copilotkit-integration.test.tsx`
18. `frontend/__tests__/integration/approval-workflow.test.tsx`
19. `frontend/__tests__/integration/agent-monitoring.test.tsx`
20. `frontend/__tests__/unit/test-copilot-hooks.test.ts`

#### Files to Modify (2 files)

1. `frontend/package.json` - Add CopilotKit dependencies
2. `frontend/app/layout.tsx` - Add CopilotKit provider

---

## 4. Validation Checkpoints

### Checkpoint Summary

| Phase | Checkpoint | Validation Method | Success Criteria |
|-------|-----------|-------------------|------------------|
| **Phase 1: Backend Foundation** |
| 1.1 | Directory structure | `ls` + import test | All dirs exist, imports work |
| 1.2 | Endpoint wrappers | Unit tests | All tests pass |
| 2.1 | SDK installation | `pip list` | Packages installed |
| 2.2 | SDK configuration | Unit tests | Config loads correctly |
| 3.1 | LangGraph wrappers | Unit tests | Workflow builds & executes |
| 4.1 | FastAPI routes | Integration tests | Routes respond, SSE works |
| 4.2 | App integration | Health check + curl | Server starts, endpoints work |
| **Phase 2: Frontend Integration** |
| 5.1 | Client libraries | `npm list` | Packages installed |
| 5.2 | Next.js routes | Unit tests | API route proxies to backend |
| 5.3 | A2A middleware | Unit tests | Message routing works |
| 6.1 | CopilotKit provider | Component tests | Provider wraps app |
| 6.2 | useCopilotAction | Hook tests | Actions trigger backend |
| 6.3 | useCoAgent | Hook tests | Multi-agent monitoring works |
| **Phase 3: Testing & Validation** |
| 7.1 | E2E test suite | pytest | All E2E tests pass |
| 7.2 | Frontend integration | Jest | All UI tests pass |
| 8.1 | Monitoring | Metrics check | Metrics exported |
| 8.2 | Dashboard | UI verification | Dashboard displays data |

### Daily Validation Schedule

**Day 1-5 (Week 1 - Backend):**
- End of each day: Run `pytest tests/unit -v`
- Day 5: Run full integration test suite

**Day 6-10 (Week 2 - Frontend):**
- End of each day: Run `npm run test`
- Day 10: Run E2E tests

**Day 11-15 (Week 3 - Testing):**
- Daily: Run full test suite
- Day 15: Production readiness check

---

## 5. Timeline & Dependencies

### Gantt Chart (3 Weeks)

```
Week 1 (Backend Foundation)
├─ Day 1-2: Requirements 1-2 (Structure + SDK)     [CRITICAL PATH]
│   ├─ Task 1.1: Directory structure (2h)
│   ├─ Task 1.2: Endpoint wrappers (4h)
│   ├─ Task 2.1: SDK installation (1h)
│   └─ Task 2.2: SDK configuration (2h)
│
├─ Day 3-4: Requirement 3 (LangGraph Wrappers)     [CRITICAL PATH]
│   └─ Task 3.1: LangGraph wrappers (6h)
│
└─ Day 5: Requirement 4 (FastAPI Endpoint)         [CRITICAL PATH]
    ├─ Task 4.1: FastAPI routes (4h)
    └─ Task 4.2: App integration (2h)

Week 2 (Frontend Integration)
├─ Day 6: Requirement 5 Part 1 (Client Setup)      [CRITICAL PATH]
│   ├─ Task 5.1: Install libraries (1h)
│   └─ Task 5.2: Next.js routes (3h)
│
├─ Day 7-8: Requirement 5 Part 2 (A2A Middleware)  [CRITICAL PATH]
│   └─ Task 5.3: A2A middleware (4h)
│
├─ Day 9-10: Requirement 6 (React Hooks)           [CRITICAL PATH]
    ├─ Task 6.1: CopilotKit provider (2h)
    ├─ Task 6.2: useCopilotAction (3h)
    └─ Task 6.3: useCoAgent (3h)

Week 3 (Testing & Monitoring)
├─ Day 11-13: Requirement 7 (Testing)              [CRITICAL PATH]
│   ├─ Task 7.1: E2E test suite (8h)
│   └─ Task 7.2: Frontend integration tests (4h)
│
└─ Day 14-15: Requirement 8 (Monitoring)           [HIGH PRIORITY]
    ├─ Task 8.1: Logging & metrics (4h)
    └─ Task 8.2: Dashboard (4h)
```

### Dependency Graph

```
START
  │
  ├─→ [1.1 Structure] ─→ [1.2 Endpoints] ─┐
  │                                        │
  ├─→ [2.1 SDK Install] ─→ [2.2 Config] ─┤
  │                                        │
  └─────────────────────────────────────→ [3.1 LangGraph]
                                            │
                                            ↓
                                         [4.1 Routes]
                                            │
                                            ↓
                                         [4.2 App Integration]
                                            │
  ┌─────────────────────────────────────────┘
  │
  ├─→ [5.1 Client Libs] ─→ [5.2 Next.js] ─→ [5.3 A2A]
  │                                            │
  └────────────────────────────────────────────┤
                                               │
                                               ↓
                                         [6.1 Provider]
                                               │
                                               ├─→ [6.2 Actions]
                                               │
                                               └─→ [6.3 CoAgent]
                                                      │
  ┌───────────────────────────────────────────────────┘
  │
  ├─→ [7.1 E2E Tests] ─┐
  │                    │
  ├─→ [7.2 Frontend Tests] ─┤
  │                    │
  └────────────────────┴─→ [8.1 Monitoring] ─→ [8.2 Dashboard]
                                                      │
                                                      ↓
                                                    END
```

### Parallel Execution Opportunities

**Week 1:**
- Tasks 1.1 & 2.1 can run in parallel (structure + SDK install)
- Tasks 1.2 & 2.2 can overlap (endpoints + config)

**Week 2:**
- Tasks 5.1 & backend validation can run in parallel
- Tasks 6.1, 6.2, 6.3 can be developed concurrently by different devs

**Week 3:**
- Tasks 7.1 & 7.2 can run in parallel (backend E2E + frontend tests)
- Task 8.1 can start while tests are running

---

## 6. Risk Mitigation

### Critical Risks

#### Risk 1: CopilotKit SDK Breaking Changes
**Severity**: HIGH
**Probability**: MEDIUM (20%)

**Mitigation**:
- Pin exact versions in requirements.txt
- Monitor CopilotKit release notes
- Maintain fork as backup
- Test SDK updates in staging before production

#### Risk 2: LangGraph Integration Issues
**Severity**: MEDIUM
**Probability**: MEDIUM (30%)

**Mitigation**:
- Start with simple state graph
- Thorough unit testing of LangGraph wrappers
- Fallback: Direct AG-UI Protocol if LangGraph fails
- Allocate 2 extra days buffer for debugging

#### Risk 3: SSE Connection Stability
**Severity**: MEDIUM
**Probability**: LOW (15%)

**Mitigation**:
- Implement connection retry logic
- Add heartbeat messages every 30s
- Client-side reconnection handling
- Fallback to HTTP polling if SSE fails

#### Risk 4: Approval Workflow Timing
**Severity**: LOW
**Probability**: MEDIUM (25%)

**Mitigation**:
- Configurable timeout (default 5 minutes)
- Clear timeout messaging to users
- Resume capability for timed-out sessions
- Approval queue for batch processing

### Risk Register

| Risk | Mitigation Status | Monitoring Plan | Escalation Path |
|------|------------------|-----------------|-----------------|
| SDK breaking changes | ✅ Versions pinned | Weekly release check | Tech lead approval for updates |
| LangGraph issues | ⚠️ Testing in progress | Unit test coverage >90% | Fallback to direct AG-UI |
| SSE stability | ✅ Retry logic added | Monitor connection errors | Switch to WebSocket |
| Approval timeouts | ✅ Config implemented | Track timeout rate | Increase default timeout |

---

## 7. Success Criteria

### Phase 1 Success (Week 1)

**Backend Foundation:**
- ✅ All CopilotKit packages installed (copilotkit-langgraph, langgraph, langchain-core)
- ✅ Agent endpoint wrappers created for all 4 agents
- ✅ LangGraph state machines build successfully
- ✅ `/api/agent-orchestrator` endpoint responds with SSE stream
- ✅ Health check shows `copilotkit_enabled: true`

**Validation**:
```bash
# All these must pass
pip list | grep -E "(copilotkit|langgraph|langchain)" | wc -l  # >= 3
pytest tests/unit/test_endpoint_wrappers.py -v  # 100% pass
pytest tests/unit/test_langgraph_wrappers.py -v  # 100% pass
curl http://localhost:8000/health | jq .copilotkit_enabled  # true
curl -X POST http://localhost:8000/api/agent-orchestrator \
  -H "Content-Type: application/json" \
  -d '{"account_id":"ACC-001","user_id":"test"}' \
  | head -5  # SSE stream starts
```

### Phase 2 Success (Week 2)

**Frontend Integration:**
- ✅ CopilotKit React packages installed (@copilotkit/react-core, @copilotkit/react-ui)
- ✅ Next.js API route `/api/copilotkit` proxies to backend
- ✅ A2A middleware coordinates agent messages
- ✅ useCopilotAction hooks trigger backend agents
- ✅ useCoAgent hooks monitor multi-agent execution
- ✅ CopilotKit sidebar appears in UI

**Validation**:
```bash
# All these must pass
cd frontend
npm list | grep copilotkit | wc -l  # >= 3
npm run test -- use-account-analysis  # Hooks tests pass
npm run test -- copilotkit-provider  # Provider tests pass
npm run dev &  # Server starts
curl http://localhost:3000/api/copilotkit  # 200 OK
# Manual: Open http://localhost:3000, verify sidebar appears
```

### Phase 3 Success (Week 3)

**Testing & Monitoring:**
- ✅ All E2E tests pass (6/6 tests)
- ✅ All frontend integration tests pass (4/4 tests)
- ✅ Monitoring dashboard displays real-time metrics
- ✅ Session tracking works for concurrent sessions
- ✅ Approval workflow completes end-to-end
- ✅ Error handling tested and functional

**Validation**:
```bash
# All these must pass
pytest tests/e2e/test_copilotkit_integration.py -v  # 6 passed
cd frontend && npm run test:integration  # 4 passed
curl http://localhost:8000/api/monitoring/dashboard | jq .  # Valid JSON
# Manual: Open http://localhost:3000/monitoring, verify metrics update
```

### Production Readiness Checklist

**Week 3 Day 15 - Final Validation:**

- [ ] **Backend**
  - [ ] All unit tests pass (>95% coverage)
  - [ ] All integration tests pass
  - [ ] All E2E tests pass
  - [ ] Health endpoint returns healthy status
  - [ ] Monitoring exports Prometheus metrics
  - [ ] Logging captures all agent events

- [ ] **Frontend**
  - [ ] All component tests pass
  - [ ] All integration tests pass
  - [ ] CopilotKit sidebar functions correctly
  - [ ] Agent status updates in real-time
  - [ ] Approval workflow completes successfully
  - [ ] Error messages display correctly

- [ ] **Performance**
  - [ ] Agent orchestration completes in <30 seconds
  - [ ] SSE stream has <100ms latency
  - [ ] Handles 5 concurrent sessions without errors
  - [ ] Approval workflow responds in <2 seconds
  - [ ] Dashboard loads in <1 second

- [ ] **Documentation**
  - [ ] README updated with CopilotKit setup
  - [ ] API documentation includes new endpoints
  - [ ] Developer guide for adding new agents
  - [ ] User guide for approval workflow

- [ ] **Security**
  - [ ] Authentication enforced on all endpoints
  - [ ] CORS configured for production domains
  - [ ] Sensitive data not logged
  - [ ] Rate limiting enabled

---

## Appendix A: Quick Reference Commands

### Backend Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/unit -v
pytest tests/e2e -v

# Start server
python -m src.main

# Check health
curl http://localhost:8000/health

# Test endpoint
curl -X POST http://localhost:8000/api/agent-orchestrator \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{"account_id":"ACC-001","user_id":"test"}'
```

### Frontend Setup

```bash
# Install dependencies
cd frontend
npm install

# Run tests
npm run test
npm run test:integration

# Start dev server
npm run dev

# Build production
npm run build
npm run start
```

### Monitoring

```bash
# View dashboard
curl http://localhost:8000/api/monitoring/dashboard | jq .

# Get active sessions
curl http://localhost:8000/api/monitoring/sessions | jq .

# Get session details
curl http://localhost:8000/api/monitoring/sessions/sess-123 | jq .
```

---

## Appendix B: Environment Variables

### Backend (.env)

```bash
# CopilotKit Configuration
CK_API_BASE_URL=http://localhost:8000
CK_AGENT_ENDPOINT=/api/agent-orchestrator
CK_ENABLE_STREAMING=true
CK_STREAM_TIMEOUT=300
CK_REQUIRE_AUTH=true
CK_CORS_ORIGINS=http://localhost:3000,http://localhost:3001
CK_APPROVAL_TIMEOUT=300
CK_ENABLE_AUTO_APPROVE=false

# Existing variables (from previous setup)
ANTHROPIC_API_KEY=your-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379
```

### Frontend (.env.local)

```bash
# CopilotKit
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_COPILOTKIT_URL=/api/copilotkit
NEXT_PUBLIC_ENABLE_DEV_CONSOLE=true

# Existing variables
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## Appendix C: Troubleshooting Guide

### Common Issues

**Issue 1: SSE Stream Not Working**

**Symptoms**: Frontend doesn't receive agent events

**Solution**:
```bash
# Check if SSE endpoint is accessible
curl -N http://localhost:8000/api/agent-orchestrator \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"account_id":"ACC-001","user_id":"test"}'

# Should see:
# data: {"type":"agent_started",...}

# If not, check:
1. Backend server is running
2. CORS is configured correctly
3. No proxy blocking SSE
```

**Issue 2: LangGraph Workflow Fails**

**Symptoms**: Agent execution stops mid-workflow

**Solution**:
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check LangGraph state
from src.copilotkit.wrappers.orchestrator_langgraph import OrchestratorLangGraph

wrapper = OrchestratorLangGraph(...)
# Inspect graph structure
print(wrapper.graph.get_graph().to_json())
```

**Issue 3: Approval Timeout**

**Symptoms**: Approval requests time out before user responds

**Solution**:
```bash
# Increase timeout in config
CK_APPROVAL_TIMEOUT=600  # 10 minutes instead of 5

# Or implement resume capability
# (Already included in Task 5.3)
```

---

**Document Status**: ✅ COMPLETE
**Last Updated**: 2025-10-19
**Next Review**: After Week 1 completion
**Author**: SPARC Completion Specialist
**Approvals Required**: Technical Lead, Product Manager

---

**Ready for Implementation**: YES
**Estimated Completion**: 2025-11-09 (3 weeks from start)
