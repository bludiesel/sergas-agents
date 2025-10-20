# SPARC Specification: CopilotKit Integration Rectification Plan

**Document Version:** 1.0
**Date:** 2025-10-19
**Phase:** Specification (SPARC Methodology)
**Status:** Draft for Review
**Author:** SPARC Specification Agent

---

## Executive Summary

This specification document defines the requirements, acceptance criteria, and technical specifications for rectifying the CopilotKit integration in the Sergas Super Account Manager project. The current implementation uses a custom SSE endpoint that bypasses the official CopilotKit SDK architecture, leading to incomplete integration and missing key features.

**Problem Statement:** The existing implementation directly connects the Next.js frontend to a custom FastAPI SSE endpoint (`/api/copilotkit`) without using the official CopilotKit Python SDK or Next.js API route proxy pattern, resulting in improper agent orchestration and missing Human-in-the-Loop (HITL) capabilities.

**Solution Approach:** Implement proper CopilotKit SDK integration following the official architecture: Backend Python SDK → Next.js API Route → Frontend CopilotKit React components.

**Success Criteria:**
- All 4 agents (OrchestratorAgent, ZohoDataScout, MemoryAnalyst, RecommendationAuthor) accessible via CopilotKit
- HITL approval workflows functional with `renderAndWaitForResponse`
- Production-ready monitoring and error handling
- 100% test coverage for new integration code

---

## 1. Current State Assessment

### 1.1 Current Architecture (Incorrect)

```
┌──────────────────────────────────────┐
│    Next.js Frontend (Port 3000)      │
│  ┌────────────────────────────────┐  │
│  │  CopilotKit React Components   │  │
│  │  (Direct SSE connection)       │  │
│  └──────────────┬─────────────────┘  │
└─────────────────┼────────────────────┘
                  │ SSE: http://localhost:8000/api/copilotkit
                  │ ❌ BYPASSES Next.js API Route
┌─────────────────▼────────────────────┐
│   FastAPI Backend (Port 8000)        │
│  ┌────────────────────────────────┐  │
│  │  /api/copilotkit (Custom SSE)  │  │  ❌ No CopilotKit SDK
│  │  OrchestratorAgent             │  │
│  │  (AG UI Protocol manual impl)  │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

### 1.2 Current Implementation Problems

| Component | Issue | Impact | Severity |
|-----------|-------|--------|----------|
| **Backend SDK** | CopilotKit Python SDK not installed | Missing LangGraph integration, manual SSE implementation | 🔴 Critical |
| **Next.js API Route** | No `/app/api/copilotkit/route.ts` | Frontend connects directly to FastAPI (CORS issues, no proxy) | 🔴 Critical |
| **Agent Wrapping** | Agents use custom AG UI emitter | Not compatible with CopilotKit's CoAgent pattern | 🔴 Critical |
| **HITL Workflow** | No `renderAndWaitForResponse` | Approval workflow incomplete | 🟡 High |
| **Frontend Hooks** | No `useCoAgent` or `useCopilotAction` | Manual state management, missing features | 🟡 High |
| **Error Handling** | Basic try-catch only | No retry logic, no circuit breaker | 🟡 High |
| **Monitoring** | Structured logs only | No metrics, no tracing | 🟢 Medium |

### 1.3 Current File Inventory

**Backend Files (Existing):**
- ✅ `/src/agents/orchestrator.py` - OrchestratorAgent (485 lines, needs wrapping)
- ✅ `/src/agents/zoho_data_scout.py` - ZohoDataScout (needs wrapping)
- ✅ `/src/agents/memory_analyst.py` - MemoryAnalyst (needs wrapping)
- ✅ `/src/agents/recommendation_author.py` - RecommendationAuthor (needs wrapping)
- ✅ `/src/api/routers/copilotkit_router.py` - Custom SSE endpoint (167 lines, to be replaced)
- ✅ `/src/events/ag_ui_emitter.py` - AG UI event emitter (to be replaced)
- ❌ No CopilotKit SDK integration files

**Frontend Files (Existing):**
- ✅ `/frontend/package.json` - Has `@copilotkit/react-core`, `@copilotkit/react-ui`, `@copilotkit/react-textarea`
- ✅ `/frontend/app/layout.tsx` - Root layout
- ✅ `/frontend/app/page.tsx` - Main page
- ❌ No `/frontend/app/api/copilotkit/route.ts` (missing Next.js API route)
- ❌ No CopilotKit provider setup
- ❌ No agent-specific React components

**Dependencies:**
- ✅ Frontend: CopilotKit React packages installed (v1.10.6)
- ❌ Backend: `copilotkit` Python SDK not in `requirements.txt`
- ❌ Backend: No LangGraph SDK (`langgraph`)

---

## 2. Desired State Specification

### 2.1 Target Architecture (Correct)

```
┌──────────────────────────────────────────────────────────┐
│         Next.js Frontend (Port 3000)                     │
│  ┌────────────────────────────────────────────────────┐  │
│  │  <CopilotKit runtimeUrl="/api/copilotkit">         │  │
│  │    <CopilotChat />                                  │  │
│  │    <ApprovalInterface />                            │  │
│  │    useCoAgent("orchestrator")                       │  │
│  │    useCopilotAction("approve_recommendation")       │  │
│  │  </CopilotKit>                                      │  │
│  └────────────────┬───────────────────────────────────┘  │
│                   │                                       │
│  ┌────────────────▼───────────────────────────────────┐  │
│  │  /app/api/copilotkit/route.ts                      │  │  ✅ Next.js API Route
│  │  (Proxies to FastAPI backend)                      │  │
│  └────────────────┬───────────────────────────────────┘  │
└───────────────────┼──────────────────────────────────────┘
                    │ HTTP: http://localhost:8000/api/copilotkit
┌───────────────────▼──────────────────────────────────────┐
│      FastAPI Backend (Port 8000)                         │
│  ┌────────────────────────────────────────────────────┐  │
│  │  CopilotKit Python SDK                             │  │  ✅ Official SDK
│  │  from copilotkit.integrations.fastapi import (     │  │
│  │      add_fastapi_endpoint                          │  │
│  │  )                                                 │  │
│  │                                                    │  │
│  │  add_fastapi_endpoint(                            │  │
│  │      app,                                         │  │
│  │      agents=[                                     │  │
│  │          orchestrator_coagent,  ← Wrapped         │  │
│  │          zoho_scout_coagent,    ← Wrapped         │  │
│  │          memory_analyst_coagent,← Wrapped         │  │
│  │          recommendation_coagent ← Wrapped         │  │
│  │      ],                                           │  │
│  │      endpoint="/api/copilotkit"                   │  │
│  │  )                                                │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Existing Agents (Python 3.13+)                    │  │
│  │  • OrchestratorAgent (Claude Agent SDK)           │  │
│  │  • ZohoDataScout (Claude Agent SDK)               │  │
│  │  • MemoryAnalyst (Claude Agent SDK)               │  │
│  │  • RecommendationAuthor (Claude Agent SDK)        │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 2.2 Target Dependencies

**Backend (`requirements.txt`):**
```python
# CopilotKit Integration
copilotkit>=1.1.0
langgraph>=0.2.0
langchain>=0.3.0
langchain-anthropic>=0.3.0  # For Claude integration

# Existing dependencies (keep all)
claude-agent-sdk>=0.1.4
pydantic>=2.5.0
fastapi>=0.104.1
# ... (all existing dependencies)
```

**Frontend (`frontend/package.json`):**
```json
{
  "dependencies": {
    "@copilotkit/react-core": "^1.10.6",
    "@copilotkit/react-ui": "^1.10.6",
    "@copilotkit/react-textarea": "^1.10.6",
    "@copilotkit/runtime-client-gql": "^1.10.6",
    "next": "15.5.6",
    "react": "19.1.0",
    "react-dom": "19.1.0"
  }
}
```

### 2.3 Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| **Agent Accessibility** | 0/4 agents via CopilotKit | 4/4 agents via CopilotKit | `useCoAgent()` returns all agents |
| **HITL Approval Time** | N/A (not implemented) | < 5 seconds response time | Time from `renderAndWaitForResponse` to user action |
| **Integration Test Coverage** | 0% (no tests) | 100% for new code | pytest coverage report |
| **Frontend-Backend Latency** | Direct connection (50ms) | < 150ms via proxy | p95 latency metric |
| **Error Recovery** | Manual restart | Automatic retry (3x) | Retry metrics in logs |
| **Monitoring Coverage** | Logs only | Logs + metrics + traces | OpenTelemetry integration |

---

## 3. Requirement Specifications

### Requirement 1: Refactor Agent Orchestration (Backend FastAPI Endpoints)

**ID:** REQ-001
**Priority:** 🔴 Critical
**Estimated Effort:** 8 hours

#### Current State
- ❌ Single custom SSE endpoint `/api/copilotkit` in `copilotkit_router.py`
- ❌ Manual AG UI Protocol event emission
- ❌ No per-agent endpoints
- ❌ No CopilotKit SDK integration

#### Desired State
- ✅ CopilotKit SDK endpoint via `add_fastapi_endpoint()`
- ✅ Each agent accessible as a CoAgent
- ✅ Automatic SSE streaming via CopilotKit
- ✅ Standard AG UI Protocol compliance

#### Acceptance Criteria
```gherkin
Feature: CopilotKit FastAPI Integration

  Scenario: Backend endpoint responds to CopilotKit runtime client
    Given FastAPI app is running on port 8000
    And CopilotKit SDK is configured
    When Next.js API route proxies request to "/api/copilotkit"
    Then backend responds with SSE stream
    And response contains "text/event-stream" content type
    And events follow CopilotKit protocol format

  Scenario: All 4 agents are registered
    Given CopilotKit endpoint is configured
    When client requests agent list
    Then response includes "orchestrator"
    And response includes "zoho-scout"
    And response includes "memory-analyst"
    And response includes "recommendation-author"

  Scenario: Agent execution streams events
    Given orchestrator agent is available
    When client executes "analyze account ACC-001"
    Then backend streams "agent_started" event
    And backend streams "agent_stream" events with progress
    And backend streams "agent_completed" event
    And stream closes gracefully
```

#### API Contract

**Endpoint:** `POST /api/copilotkit`

**Request Headers:**
```http
Content-Type: application/json
Accept: text/event-stream
```

**Request Body:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Analyze account ACC-001"
    }
  ],
  "agent": "orchestrator",
  "context": {
    "account_id": "ACC-001",
    "workflow": "account_analysis"
  }
}
```

**Response (SSE Stream):**
```
event: agent_started
data: {"agentId":"orchestrator","step":1,"task":"Account analysis"}

event: agent_stream
data: {"agentId":"zoho-scout","content":"Fetching account data..."}

event: agent_stream
data: {"agentId":"memory-analyst","content":"Analyzing patterns..."}

event: approval_required
data: {"recommendationId":"REC-123","action":"update_priority"}

event: agent_completed
data: {"agentId":"orchestrator","output":{"status":"completed"}}
```

#### Implementation Files

**New Files:**
- `/src/api/copilotkit/copilotkit_integration.py` - CopilotKit SDK setup
- `/src/api/copilotkit/agent_wrappers.py` - CoAgent wrapper classes

**Modified Files:**
- `/src/api/main.py` - Add CopilotKit endpoint
- `/src/api/routers/copilotkit_router.py` - Deprecate old endpoint (keep for migration)

---

### Requirement 2: Install CopilotKit LangGraph Python SDK

**ID:** REQ-002
**Priority:** 🔴 Critical
**Estimated Effort:** 2 hours

#### Current State
- ❌ `copilotkit` not in `requirements.txt`
- ❌ No LangGraph SDK (`langgraph`)
- ❌ No LangChain Anthropic integration

#### Desired State
- ✅ `copilotkit>=1.1.0` installed
- ✅ `langgraph>=0.2.0` installed
- ✅ `langchain-anthropic>=0.3.0` installed
- ✅ Compatible with Python 3.13+

#### Acceptance Criteria
```gherkin
Feature: CopilotKit SDK Installation

  Scenario: Dependencies are installed
    Given requirements.txt is updated
    When pip install -r requirements.txt runs
    Then copilotkit package is available
    And langgraph package is available
    And langchain-anthropic package is available
    And no dependency conflicts occur

  Scenario: CopilotKit SDK imports successfully
    Given dependencies are installed
    When Python imports copilotkit modules
    Then "from copilotkit import CoAgent" succeeds
    And "from copilotkit.integrations.fastapi import add_fastapi_endpoint" succeeds
    And "from langgraph.graph import StateGraph" succeeds

  Scenario: SDK version compatibility
    Given copilotkit>=1.1.0 is installed
    When checking version compatibility
    Then SDK is compatible with Python 3.13+
    And SDK supports Claude API (Anthropic)
```

#### Dependencies Matrix

| Package | Version | Purpose | Compatibility |
|---------|---------|---------|---------------|
| `copilotkit` | >=1.1.0 | Core CopilotKit SDK | Python 3.13+ ✅ |
| `langgraph` | >=0.2.0 | Agent graph orchestration | Python 3.13+ ✅ |
| `langchain` | >=0.3.0 | LangChain base (transitive) | Python 3.13+ ✅ |
| `langchain-anthropic` | >=0.3.0 | Claude model integration | Python 3.13+ ✅ |

#### Installation Script

**File:** `/scripts/install_copilotkit.sh`
```bash
#!/bin/bash
set -e

echo "Installing CopilotKit SDK..."

# Add to requirements.txt
cat >> requirements.txt << EOF

# ===================================
# CopilotKit Integration
# ===================================
copilotkit>=1.1.0
langgraph>=0.2.0
langchain>=0.3.0
langchain-anthropic>=0.3.0
EOF

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import copilotkit; print(f'✅ CopilotKit {copilotkit.__version__} installed')"
python -c "import langgraph; print(f'✅ LangGraph {langgraph.__version__} installed')"

echo "✅ CopilotKit SDK installation complete"
```

---

### Requirement 3: Wrap Agents with LangGraph/Pydantic AI Integration

**ID:** REQ-003
**Priority:** 🔴 Critical
**Estimated Effort:** 12 hours

#### Current State
- ❌ Agents inherit from `BaseAgent` (Claude Agent SDK)
- ❌ No CoAgent wrapper pattern
- ❌ No LangGraph StateGraph integration
- ❌ Manual AG UI event emission

#### Desired State
- ✅ Each agent wrapped as a CoAgent
- ✅ LangGraph StateGraph for orchestration
- ✅ Automatic state management
- ✅ CopilotKit protocol compliance

#### Acceptance Criteria
```gherkin
Feature: Agent LangGraph Integration

  Scenario: OrchestratorAgent wrapped as CoAgent
    Given OrchestratorAgent class exists
    When wrapped with CoAgent decorator
    Then agent is accessible via CopilotKit
    And agent state is renderable
    And agent supports streaming

  Scenario: CoAgent state is observable
    Given orchestrator CoAgent is running
    When agent processes account
    Then state updates are emitted as SSE events
    And frontend receives state updates in real-time
    And state includes {"accounts_processed": N, "current_step": "..."}

  Scenario: Multi-agent coordination works
    Given all 4 agents are wrapped as CoAgents
    When orchestrator spawns zoho-scout
    Then zoho-scout receives context from orchestrator
    And zoho-scout returns results to orchestrator
    And state transitions are tracked
```

#### Agent Wrapper Pattern

**File:** `/src/api/copilotkit/agent_wrappers.py`

```python
"""CopilotKit CoAgent wrappers for existing Claude SDK agents."""

from typing import Any, Dict
from copilotkit import CoAgent
from langgraph.graph import StateGraph, END
from src.agents.orchestrator import OrchestratorAgent
from src.agents.zoho_data_scout import ZohoDataScout
from src.agents.memory_analyst import MemoryAnalyst
from src.agents.recommendation_author import RecommendationAuthor

# ============================================================================
# Orchestrator CoAgent
# ============================================================================

def create_orchestrator_coagent(
    zoho_scout: ZohoDataScout,
    memory_analyst: MemoryAnalyst,
    recommendation_author: RecommendationAuthor,
    approval_manager: Any
) -> CoAgent:
    """Wrap OrchestratorAgent as CopilotKit CoAgent.

    Args:
        zoho_scout: ZohoDataScout agent instance
        memory_analyst: MemoryAnalyst agent instance
        recommendation_author: RecommendationAuthor agent instance
        approval_manager: ApprovalManager instance

    Returns:
        CoAgent instance for orchestrator
    """
    orchestrator = OrchestratorAgent(
        session_id="copilotkit",
        zoho_scout=zoho_scout,
        memory_analyst=memory_analyst,
        recommendation_author=recommendation_author,
        approval_manager=approval_manager
    )

    async def orchestrator_executor(state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute orchestrator with state tracking."""
        context = {
            "account_id": state.get("account_id"),
            "workflow": state.get("workflow", "account_analysis")
        }
        result = await orchestrator.execute(context)
        return {**state, "result": result}

    return CoAgent(
        name="orchestrator",
        description="Coordinates multi-agent account analysis workflow",
        agent=orchestrator_executor,
        state_render=lambda state: {
            "status": state.get("status", "running"),
            "current_step": state.get("current_step", "initializing"),
            "accounts_processed": state.get("accounts_processed", 0),
            "progress": f"{state.get('progress', 0)}%"
        }
    )

# ============================================================================
# Zoho Data Scout CoAgent
# ============================================================================

def create_zoho_scout_coagent(zoho_scout: ZohoDataScout) -> CoAgent:
    """Wrap ZohoDataScout as CopilotKit CoAgent."""

    async def zoho_scout_executor(state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Zoho data fetching with state tracking."""
        account_id = state.get("account_id")
        snapshot = await zoho_scout.get_account_snapshot(account_id)
        return {
            **state,
            "account_data": snapshot.model_dump(),
            "risk_level": snapshot.risk_level.value
        }

    return CoAgent(
        name="zoho-scout",
        description="Fetches and analyzes Zoho CRM account data",
        agent=zoho_scout_executor,
        state_render=lambda state: {
            "status": "fetching" if not state.get("account_data") else "completed",
            "account_id": state.get("account_id"),
            "risk_signals_detected": len(state.get("risk_signals", []))
        }
    )

# ============================================================================
# Memory Analyst CoAgent
# ============================================================================

def create_memory_analyst_coagent(memory_analyst: MemoryAnalyst) -> CoAgent:
    """Wrap MemoryAnalyst as CopilotKit CoAgent."""

    async def memory_analyst_executor(state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute historical context retrieval."""
        account_id = state.get("account_id")
        context = await memory_analyst.get_historical_context(
            account_id=account_id,
            lookback_days=365,
            include_patterns=True
        )
        return {
            **state,
            "historical_context": context.model_dump(),
            "patterns_detected": len(context.patterns)
        }

    return CoAgent(
        name="memory-analyst",
        description="Analyzes historical patterns and account context",
        agent=memory_analyst_executor,
        state_render=lambda state: {
            "status": "analyzing" if not state.get("historical_context") else "completed",
            "patterns_found": state.get("patterns_detected", 0),
            "sentiment_trend": state.get("sentiment_trend", "unknown")
        }
    )

# ============================================================================
# Recommendation Author CoAgent
# ============================================================================

def create_recommendation_author_coagent(
    recommendation_author: RecommendationAuthor
) -> CoAgent:
    """Wrap RecommendationAuthor as CopilotKit CoAgent."""

    async def recommendation_author_executor(state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute recommendation generation."""
        context = {
            "account_id": state.get("account_id"),
            "account_data": state.get("account_data"),
            "historical_context": state.get("historical_context")
        }
        recommendations = await recommendation_author.execute(context)
        return {
            **state,
            "recommendations": recommendations,
            "recommendation_count": len(recommendations.get("recommendations", []))
        }

    return CoAgent(
        name="recommendation-author",
        description="Generates actionable recommendations based on analysis",
        agent=recommendation_author_executor,
        state_render=lambda state: {
            "status": "generating" if not state.get("recommendations") else "completed",
            "recommendations_count": state.get("recommendation_count", 0),
            "priority": state.get("priority", "medium")
        }
    )
```

#### State Graph Definition

**File:** `/src/api/copilotkit/orchestration_graph.py`

```python
"""LangGraph orchestration graph for multi-agent workflow."""

from typing import Dict, Any
from langgraph.graph import StateGraph, END

def create_orchestration_graph(
    orchestrator_coagent,
    zoho_scout_coagent,
    memory_analyst_coagent,
    recommendation_coagent
) -> StateGraph:
    """Create LangGraph state graph for agent orchestration.

    Workflow:
    1. Start → Zoho Scout (fetch data)
    2. Zoho Scout → Memory Analyst (analyze history)
    3. Memory Analyst → Recommendation Author (generate recommendations)
    4. Recommendation Author → Orchestrator (coordinate approval)
    5. Orchestrator → End
    """

    # Define state schema
    state_schema = {
        "account_id": str,
        "workflow": str,
        "account_data": dict,
        "historical_context": dict,
        "recommendations": dict,
        "approval_status": str,
        "current_step": str,
        "progress": int
    }

    # Create graph
    graph = StateGraph(state_schema)

    # Add nodes (agents)
    graph.add_node("zoho_scout", zoho_scout_coagent)
    graph.add_node("memory_analyst", memory_analyst_coagent)
    graph.add_node("recommendation_author", recommendation_coagent)
    graph.add_node("orchestrator", orchestrator_coagent)

    # Define edges (workflow)
    graph.set_entry_point("zoho_scout")
    graph.add_edge("zoho_scout", "memory_analyst")
    graph.add_edge("memory_analyst", "recommendation_author")
    graph.add_edge("recommendation_author", "orchestrator")
    graph.add_edge("orchestrator", END)

    return graph.compile()
```

---

### Requirement 4: Set Up `/agent-orchestrator` Endpoint

**ID:** REQ-004
**Priority:** 🟡 High
**Estimated Effort:** 4 hours

#### Current State
- ❌ No dedicated orchestrator endpoint
- ❌ Generic `/api/copilotkit` only

#### Desired State
- ✅ `/api/agent-orchestrator` endpoint for starting workflows
- ✅ REST API + SSE streaming hybrid
- ✅ Workflow type selection (account_analysis, daily_review, risk_assessment)

#### Acceptance Criteria
```gherkin
Feature: Agent Orchestrator Endpoint

  Scenario: Start account analysis workflow
    Given FastAPI server is running
    When POST to "/api/agent-orchestrator" with body:
      """
      {
        "account_id": "ACC-001",
        "workflow": "account_analysis"
      }
      """
    Then response status is 202 Accepted
    And response includes "run_id"
    And response includes SSE stream URL

  Scenario: Stream workflow progress
    Given workflow "run_abc123" is running
    When client connects to SSE stream
    Then client receives workflow_started event
    And client receives agent progress events
    And client receives approval_required event
    And client receives workflow_completed event
```

#### API Contract

**Endpoint:** `POST /api/agent-orchestrator`

**Request:**
```json
{
  "account_id": "ACC-001",
  "workflow": "account_analysis",
  "options": {
    "timeout_seconds": 300,
    "auto_approve": false
  }
}
```

**Response (202 Accepted):**
```json
{
  "run_id": "run_abc123",
  "status": "started",
  "stream_url": "/api/agent-orchestrator/run_abc123/stream"
}
```

**SSE Stream:** `GET /api/agent-orchestrator/{run_id}/stream`

---

### Requirement 5: Register Endpoints in Frontend (AG-UI Wrappers)

**ID:** REQ-005
**Priority:** 🟡 High
**Estimated Effort:** 6 hours

#### Current State
- ❌ No Next.js API route `/app/api/copilotkit/route.ts`
- ❌ Frontend connects directly to FastAPI (CORS issues)
- ❌ No HttpAgent or a2aMiddlewareAgent wrappers

#### Desired State
- ✅ Next.js API route proxies to FastAPI backend
- ✅ Frontend uses AG-UI wrappers for HTTP agents
- ✅ Proper error handling and retry logic

#### Acceptance Criteria
```gherkin
Feature: Next.js API Route Proxy

  Scenario: API route proxies to FastAPI backend
    Given Next.js dev server is running
    When frontend requests "/api/copilotkit"
    Then Next.js route forwards to "http://localhost:8000/api/copilotkit"
    And response includes CORS headers
    And SSE stream works correctly

  Scenario: HttpAgent wrapper handles errors
    Given backend is temporarily unavailable
    When frontend makes request via HttpAgent
    Then HttpAgent retries 3 times
    And shows user-friendly error message
```

#### Implementation Files

**File:** `/frontend/app/api/copilotkit/route.ts`

```typescript
/**
 * Next.js API Route: CopilotKit Backend Proxy
 *
 * Proxies requests from CopilotKit frontend to FastAPI backend.
 * Handles SSE streaming, error recovery, and CORS.
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
const COPILOTKIT_ENDPOINT = `${BACKEND_URL}/api/copilotkit`;

export async function POST(request: NextRequest) {
  try {
    // Parse incoming request
    const body = await request.json();

    // Forward to FastAPI backend
    const response = await fetch(COPILOTKIT_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(body),
    });

    // Check for errors
    if (!response.ok) {
      return NextResponse.json(
        { error: 'Backend request failed', status: response.status },
        { status: response.status }
      );
    }

    // Stream SSE response
    return new NextResponse(response.body, {
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    console.error('CopilotKit proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  // Health check
  return NextResponse.json({ status: 'healthy', service: 'copilotkit-proxy' });
}
```

---

### Requirement 6: Update React Frontend with Hooks

**ID:** REQ-006
**Priority:** 🟡 High
**Estimated Effort:** 8 hours

#### Current State
- ❌ No `useCopilotAction` hooks
- ❌ No `useCoAgent` hooks
- ❌ No CopilotKit provider setup

#### Desired State
- ✅ `<CopilotKit>` provider wraps app
- ✅ `useCopilotAction` for approval actions
- ✅ `useCoAgent` for agent state tracking
- ✅ `<CopilotChat>` component for main UI

#### Acceptance Criteria
```gherkin
Feature: React CopilotKit Integration

  Scenario: CopilotKit provider is configured
    Given Next.js app is running
    When app mounts
    Then CopilotKit provider connects to "/api/copilotkit"
    And connection is established successfully

  Scenario: Copilot chat interface works
    Given user opens dashboard
    When user types "Analyze account ACC-001"
    Then chat sends request to backend
    And receives streaming response
    And displays agent progress in real-time

  Scenario: Agent state is observable
    Given orchestrator is running
    When using useCoAgent("orchestrator")
    Then hook returns current agent state
    And state updates trigger re-render
```

#### Implementation Files

**File:** `/frontend/app/layout.tsx` (Modified)

```typescript
import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <CopilotKit runtimeUrl="/api/copilotkit">
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
```

**File:** `/frontend/components/ApprovalInterface.tsx` (New)

```typescript
"use client";

import { useCopilotAction, useCoAgent } from "@copilotkit/react-core";
import { useState } from "react";

export function ApprovalInterface() {
  const [recommendations, setRecommendations] = useState([]);

  // Track orchestrator state
  const orchestrator = useCoAgent("orchestrator");

  // Register approval action
  useCopilotAction({
    name: "approve_recommendation",
    description: "Approve a recommendation for execution",
    parameters: [
      {
        name: "recommendation_id",
        type: "string",
        description: "ID of recommendation to approve",
      },
      {
        name: "modified",
        type: "object",
        description: "Optional modifications to recommendation",
      },
    ],
    handler: async ({ recommendation_id, modified }) => {
      const response = await fetch("/api/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ recommendation_id, modified }),
      });

      if (!response.ok) {
        throw new Error("Approval failed");
      }

      return { success: true, recommendation_id };
    },
  });

  return (
    <div className="approval-interface">
      <h2>Pending Approvals</h2>
      <div className="agent-status">
        Orchestrator Status: {orchestrator.state?.status || "idle"}
      </div>
      {/* Approval cards rendered here */}
    </div>
  );
}
```

---

### Requirement 7: Test Agent Orchestration with HITL Workflows

**ID:** REQ-007
**Priority:** 🟡 High
**Estimated Effort:** 12 hours

#### Current State
- ❌ No integration tests for HITL workflows
- ❌ No E2E tests with frontend + backend
- ❌ Manual testing only

#### Desired State
- ✅ Integration tests for each agent
- ✅ E2E tests for HITL approval workflow
- ✅ Performance tests for concurrent users
- ✅ 100% test coverage for new code

#### Acceptance Criteria
```gherkin
Feature: HITL Workflow Testing

  Scenario: End-to-end approval workflow
    Given orchestrator starts account analysis
    When zoho-scout fetches data
    And memory-analyst retrieves context
    And recommendation-author generates recommendations
    And approval-required event is emitted
    And user approves recommendation
    Then workflow completes successfully
    And Zoho CRM is updated

  Scenario: Approval timeout handling
    Given approval-required event is emitted
    When user does not respond within 5 minutes
    Then workflow auto-rejects
    And timeout event is logged

  Scenario: Concurrent user handling
    Given 10 users trigger workflows simultaneously
    When all workflows execute
    Then all workflows complete successfully
    And no race conditions occur
    And response time < 500ms p95
```

#### Test Suite Structure

```
/tests/integration/copilotkit/
├── test_agent_wrappers.py           # Test CoAgent wrappers
├── test_orchestration_graph.py      # Test LangGraph workflow
├── test_copilotkit_endpoint.py      # Test FastAPI endpoint
└── test_hitl_workflow.py            # Test HITL approval

/tests/e2e/copilotkit/
├── test_frontend_backend_integration.py
├── test_approval_workflow_e2e.py
└── test_performance.py

/frontend/tests/
├── components/
│   └── ApprovalInterface.test.tsx
└── hooks/
    └── useCopilotAction.test.tsx
```

---

### Requirement 8: Implement Monitoring and Error Handling

**ID:** REQ-008
**Priority:** 🟢 Medium
**Estimated Effort:** 10 hours

#### Current State
- ❌ Basic try-catch only
- ❌ No retry logic
- ❌ No circuit breaker
- ❌ Logs only (no metrics)

#### Desired State
- ✅ Exponential backoff retry (3 attempts)
- ✅ Circuit breaker for backend failures
- ✅ Prometheus metrics
- ✅ OpenTelemetry tracing
- ✅ Error rate monitoring

#### Acceptance Criteria
```gherkin
Feature: Error Handling and Monitoring

  Scenario: Automatic retry on transient failure
    Given backend returns 503 Service Unavailable
    When frontend makes request
    Then request retries 3 times with exponential backoff
    And succeeds on retry #2

  Scenario: Circuit breaker trips on repeated failures
    Given backend fails 5 times in a row
    When circuit breaker trips
    Then subsequent requests fail fast
    And user sees "Service temporarily unavailable"
    And circuit breaker resets after 30 seconds

  Scenario: Metrics are collected
    Given integration is running
    When users make requests
    Then Prometheus collects metrics:
      - copilotkit_requests_total
      - copilotkit_request_duration_seconds
      - copilotkit_errors_total
      - copilotkit_active_streams
```

#### Monitoring Configuration

**File:** `/src/monitoring/copilotkit_metrics.py`

```python
"""Prometheus metrics for CopilotKit integration."""

from prometheus_client import Counter, Histogram, Gauge

# Request metrics
copilotkit_requests_total = Counter(
    'copilotkit_requests_total',
    'Total CopilotKit requests',
    ['agent', 'status']
)

copilotkit_request_duration = Histogram(
    'copilotkit_request_duration_seconds',
    'CopilotKit request duration',
    ['agent']
)

# Error metrics
copilotkit_errors_total = Counter(
    'copilotkit_errors_total',
    'Total CopilotKit errors',
    ['agent', 'error_type']
)

# Active stream tracking
copilotkit_active_streams = Gauge(
    'copilotkit_active_streams',
    'Number of active SSE streams'
)

# Approval workflow metrics
copilotkit_approvals_total = Counter(
    'copilotkit_approvals_total',
    'Total approval actions',
    ['action']  # approved, rejected, timeout
)

copilotkit_approval_duration = Histogram(
    'copilotkit_approval_duration_seconds',
    'Time from approval_required to user action'
)
```

---

## 4. Technical Dependencies

### 4.1 Backend Dependencies

| Package | Version | Purpose | Status |
|---------|---------|---------|--------|
| `copilotkit` | >=1.1.0 | Core CopilotKit SDK | ❌ To Install |
| `langgraph` | >=0.2.0 | Agent graph orchestration | ❌ To Install |
| `langchain` | >=0.3.0 | LangChain base | ❌ To Install |
| `langchain-anthropic` | >=0.3.0 | Claude integration | ❌ To Install |
| `claude-agent-sdk` | >=0.1.4 | Existing agent framework | ✅ Installed |
| `fastapi` | >=0.104.1 | Web framework | ✅ Installed |
| `pydantic` | >=2.5.0 | Data validation | ✅ Installed |
| `prometheus-client` | >=0.19.0 | Metrics | ✅ Installed |
| `structlog` | >=23.2.0 | Logging | ✅ Installed |

### 4.2 Frontend Dependencies

| Package | Version | Purpose | Status |
|---------|---------|---------|--------|
| `@copilotkit/react-core` | ^1.10.6 | Core React hooks | ✅ Installed |
| `@copilotkit/react-ui` | ^1.10.6 | UI components | ✅ Installed |
| `@copilotkit/react-textarea` | ^1.10.6 | Textarea component | ✅ Installed |
| `@copilotkit/runtime-client-gql` | ^1.10.6 | Runtime client | ❌ To Install |
| `next` | 15.5.6 | React framework | ✅ Installed |
| `react` | 19.1.0 | UI library | ✅ Installed |

### 4.3 Environment Variables

**Backend (`.env`):**
```bash
# CopilotKit Configuration
COPILOTKIT_ENDPOINT=/api/copilotkit
COPILOTKIT_MAX_CONCURRENT_STREAMS=50

# Existing variables
ANTHROPIC_API_KEY=sk-ant-...
ZOHO_CLIENT_ID=...
ZOHO_CLIENT_SECRET=...
DATABASE_URL=postgresql://...
```

**Frontend (`.env.local`):**
```bash
# Backend URL
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# CopilotKit Runtime
NEXT_PUBLIC_COPILOTKIT_RUNTIME=/api/copilotkit
```

---

## 5. Data Models and Schemas

### 5.1 CopilotKit Message Schema

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class CopilotKitMessage(BaseModel):
    """Message format for CopilotKit requests."""
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")

class CopilotKitRequest(BaseModel):
    """Request format for CopilotKit endpoint."""
    messages: List[CopilotKitMessage] = Field(..., description="Conversation messages")
    agent: Optional[str] = Field(default="orchestrator", description="Target agent")
    context: Dict[str, Any] = Field(default_factory=dict, description="Execution context")
```

### 5.2 Agent State Schema

```python
class AgentState(BaseModel):
    """State schema for LangGraph agents."""

    # Input
    account_id: str = Field(..., description="Account ID to analyze")
    workflow: str = Field(default="account_analysis", description="Workflow type")

    # Intermediate state
    account_data: Optional[Dict[str, Any]] = None
    historical_context: Optional[Dict[str, Any]] = None
    recommendations: Optional[Dict[str, Any]] = None

    # Progress tracking
    current_step: str = Field(default="initializing", description="Current workflow step")
    progress: int = Field(default=0, description="Progress percentage (0-100)")
    status: str = Field(default="running", description="Workflow status")

    # Results
    approval_status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
```

---

## 6. Success Metrics

### 6.1 Functional Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Agent Accessibility** | 4/4 agents via CopilotKit | `useCoAgent()` test |
| **HITL Response Time** | < 5 seconds | Timing from `renderAndWaitForResponse` |
| **Workflow Success Rate** | > 95% | Successful completions / Total runs |
| **Approval Acceptance Rate** | > 60% | Approved / Total approvals requested |

### 6.2 Performance Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **End-to-End Latency** | < 500ms (p95) | OpenTelemetry traces |
| **SSE Stream Latency** | < 150ms | Proxy overhead measurement |
| **Concurrent Users** | 50+ without degradation | Load testing |
| **Error Rate** | < 1% | Error count / Total requests |

### 6.3 Quality Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Test Coverage** | 100% for new code | pytest --cov |
| **Code Quality** | Pylint score > 9.0 | pylint src/api/copilotkit/ |
| **Documentation Coverage** | 100% public APIs | pydocstyle |
| **Type Safety** | mypy --strict passes | mypy src/api/copilotkit/ |

---

## 7. Constraints and Assumptions

### 7.1 Technical Constraints

1. **Python Version:** Must support Python 3.13+ (current project version)
2. **React Version:** Next.js 15.5.6, React 19.1.0 (current frontend version)
3. **Backward Compatibility:** Must not break existing AG UI Protocol custom endpoint (for migration period)
4. **Claude Agent SDK:** Must maintain compatibility with existing `BaseAgent` framework

### 7.2 Business Constraints

1. **Timeline:** Complete integration within 2 weeks (per decision document)
2. **Budget:** No additional infrastructure costs beyond existing AWS services
3. **Migration:** Zero downtime migration (gradual rollout via feature flag)

### 7.3 Assumptions

1. **Backend Infrastructure:** FastAPI backend runs on AWS t3.medium or better
2. **Frontend Hosting:** Next.js deployed on Vercel or equivalent
3. **Database:** PostgreSQL for audit logs and approval state
4. **Redis:** Available for caching and session management
5. **User Load:** Up to 50 concurrent users during business hours

---

## 8. Risk Assessment

### 8.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **CopilotKit SDK Breaking Changes** | Low (20%) | High | Pin versions, monitor releases, fork if needed |
| **LangGraph State Management Complexity** | Medium (40%) | Medium | Start with simple state, iterate incrementally |
| **Frontend-Backend Latency** | Low (15%) | Medium | Optimize proxy, cache static data |
| **SSE Connection Stability** | Medium (30%) | High | Implement reconnection logic, heartbeat |
| **Approval Timeout Edge Cases** | Medium (35%) | Medium | Comprehensive timeout testing |

### 8.2 Integration Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Claude SDK ↔ CopilotKit Incompatibility** | Low (10%) | Critical | Test adapter pattern early |
| **Existing Code Regression** | Medium (30%) | High | Comprehensive regression test suite |
| **Data Loss During Migration** | Low (10%) | Critical | Blue-green deployment, rollback plan |

### 8.3 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Increased Infrastructure Costs** | Low (15%) | Low | Monitor metrics, optimize before scaling |
| **User Adoption Issues** | Medium (40%) | Medium | Pilot with 10% of users first |
| **Support Burden** | Medium (35%) | Medium | Comprehensive documentation, training materials |

---

## 9. Validation Checklist

Before marking specification as complete, verify:

- [x] All 8 requirements have clear acceptance criteria
- [x] API contracts defined for all new endpoints
- [x] Data models and schemas specified
- [x] Dependencies identified with version constraints
- [x] Success metrics measurable and realistic
- [x] Constraints and assumptions documented
- [x] Risks assessed with mitigation strategies
- [x] Test strategy defined (unit, integration, E2E)
- [x] Monitoring and observability addressed
- [x] Migration path clear (old → new)

---

## 10. Next Steps (Pseudocode Phase)

After specification approval, the next SPARC phase (Pseudocode) will:

1. **Algorithm Design:** Define step-by-step algorithms for each requirement
2. **Data Flow Diagrams:** Map data flow from frontend → Next.js API → FastAPI → Agents
3. **State Transition Diagrams:** Model LangGraph state machine for orchestration
4. **Error Handling Flowcharts:** Design retry, fallback, and circuit breaker logic
5. **Test Scenarios:** Define specific test cases with input/output examples

---

## 11. Document Metadata

**Created:** 2025-10-19
**Last Updated:** 2025-10-19
**Version:** 1.0
**Status:** Draft for Review
**Approvers:**
- [ ] Technical Lead
- [ ] Product Owner
- [ ] DevOps Engineer
- [ ] QA Lead

**Related Documents:**
- `/docs/sparc/COPILOTKIT_VS_AGUI_DECISION.md` - Architecture decision record
- `/docs/research/COPILOTKIT_Complete_Research.md` - Technical research
- `/docs/integrations/CLAUDE_SDK_AG_UI_Integration_Guide.md` - Integration guide
- `/docs/MASTER_SPARC_PLAN_V2.md` - Overall project plan

**Change Log:**
- 2025-10-19: Initial specification created (v1.0)

---

**END OF SPECIFICATION DOCUMENT**
