# CopilotKit Integration Architecture

**Document Version**: 1.0
**Date**: 2025-10-19
**Phase**: SPARC Architecture
**Status**: Design Phase

---

## Executive Summary

This document defines the complete system architecture for proper CopilotKit integration with the Sergas Account Manager multi-agent system. It addresses the current architectural gap where agents communicate directly with the frontend via SSE, instead of using the official CopilotKit flow.

**Current Problem**: Direct React → FastAPI SSE endpoint bypass
**Required Flow**: React → Next.js API Route → FastAPI with `add_fastapi_endpoint()` → LangGraph agents
**Impact**: Enables proper UI integration with CopilotKit's chat interface and AG UI Protocol

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Component Architecture](#2-component-architecture)
3. [Data Flow Architecture](#3-data-flow-architecture)
4. [Agent Architecture](#4-agent-architecture)
5. [Folder Structure](#5-folder-structure)
6. [API Architecture](#6-api-architecture)
7. [Deployment Architecture](#7-deployment-architecture)
8. [Integration Points](#8-integration-points)
9. [Security Architecture](#9-security-architecture)
10. [Performance Considerations](#10-performance-considerations)

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                 │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    React Frontend (Next.js)                    │  │
│  │                                                                 │  │
│  │  ┌──────────────────┐  ┌──────────────────┐                  │  │
│  │  │ CopilotKit Chat  │  │  Account Manager  │                  │  │
│  │  │    Interface     │  │   Dashboard UI    │                  │  │
│  │  └────────┬─────────┘  └──────────────────┘                  │  │
│  │           │                                                     │  │
│  │           │ useCopilotAction()                                 │  │
│  │           │ useCopilotReadable()                               │  │
│  │           │                                                     │  │
│  └───────────┼─────────────────────────────────────────────────────┘  │
│              │                                                        │
└──────────────┼────────────────────────────────────────────────────────┘
               │
               │ HTTP POST (JSON)
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      NEXT.JS API LAYER                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │         /app/api/copilotkit/route.ts (Proxy Route)            │  │
│  │                                                                 │  │
│  │  • Forward CopilotKit requests to FastAPI backend             │  │
│  │  • Handle authentication headers                               │  │
│  │  • Stream responses back to frontend                           │  │
│  │  • Convert between CopilotKit and AG UI formats               │  │
│  └────────────────────────┬──────────────────────────────────────┘  │
│                           │                                          │
└───────────────────────────┼──────────────────────────────────────────┘
                            │
                            │ HTTP POST (/copilotkit)
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       FASTAPI BACKEND                                │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              CopilotKit SDK Integration Layer                  │  │
│  │                                                                 │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │         CopilotKitSDK (Python)                           │ │  │
│  │  │  • add_fastapi_endpoint(app, sdk, "/copilotkit")        │ │  │
│  │  │  • LangGraphAgent wrapper for each specialist           │ │  │
│  │  │  • AG UI Protocol event transformation                  │ │  │
│  │  └──────────────────────┬───────────────────────────────────┘ │  │
│  └─────────────────────────┼─────────────────────────────────────┘  │
│                            │                                          │
│                            ▼                                          │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                   AGENT ORCHESTRATION LAYER                    │  │
│  │                                                                 │  │
│  │  ┌──────────────────┐   ┌──────────────────┐                 │  │
│  │  │  OrchestratorAgent │   │  HttpAgent       │                 │  │
│  │  │  (LangGraph)      │   │  (HTTP caller)   │                 │  │
│  │  └────────┬──────────┘   └──────────────────┘                 │  │
│  │           │                                                     │  │
│  │           │ Coordinates Specialist Agents                      │  │
│  │           │                                                     │  │
│  │  ┌────────▼─────────┬──────────────────┬────────────────────┐ │  │
│  │  │                  │                  │                    │ │  │
│  │  │ ZohoDataScout    │ MemoryAnalyst    │ Recommendation-    │ │  │
│  │  │ (LangGraph)      │ (LangGraph)      │ Author (LangGraph) │ │  │
│  │  │                  │                  │                    │ │  │
│  │  │ • Fetch accounts │ • Query Cognee   │ • Generate recs    │ │  │
│  │  │ • Detect changes │ • Pattern detect │ • Template render  │ │  │
│  │  │ • Risk signals   │ • Sentiment      │ • Confidence score │ │  │
│  │  └──────────────────┴──────────────────┴────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                      INTEGRATION LAYER                         │  │
│  │                                                                 │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐│  │
│  │  │ Zoho CRM MCP   │  │ Cognee Memory  │  │ Approval Manager ││  │
│  │  │ Integration    │  │ Service        │  │ (AG UI Protocol) ││  │
│  │  └────────────────┘  └────────────────┘  └──────────────────┘│  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Architecture Layers

| Layer | Purpose | Technologies | Communication |
|-------|---------|-------------|---------------|
| **Client Layer** | User interface | React, Next.js, CopilotKit | HTTP, WebSocket |
| **Next.js API Layer** | Proxy and routing | Next.js API Routes | HTTP POST |
| **CopilotKit SDK Layer** | Integration glue | CopilotKit Python SDK | LangGraph protocol |
| **Agent Orchestration** | Multi-agent coordination | LangGraph, Claude Agent SDK | Internal events |
| **Integration Layer** | External services | MCP, REST APIs | Various protocols |

### 1.3 Current vs. Required Architecture

```
CURRENT (WRONG):
React → FastAPI SSE /events → Agents
  ❌ Bypasses CopilotKit
  ❌ No standardized protocol
  ❌ Custom SSE implementation

REQUIRED (CORRECT):
React → Next.js /api/copilotkit → FastAPI /copilotkit → LangGraph Agents
  ✅ Uses CopilotKit SDK
  ✅ LangGraph integration
  ✅ AG UI Protocol support
  ✅ Standardized streaming
```

---

## 2. Component Architecture

### 2.1 CopilotKit SDK Integration Component

```python
# /src/copilotkit/sdk_integration.py

"""
CopilotKit SDK Integration for Sergas Account Manager.

Initializes CopilotKitSDK and registers LangGraph-wrapped agents.
"""

from copilotkit import CopilotKitSDK, LangGraphAgent
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from fastapi import FastAPI

class CopilotKitIntegration:
    """CopilotKit SDK integration manager."""

    def __init__(self, app: FastAPI):
        self.app = app
        self.sdk = CopilotKitSDK()
        self.agents = {}

    def register_agent(
        self,
        agent_name: str,
        agent_callable: callable,
        description: str
    ):
        """Register LangGraph agent with CopilotKit.

        Args:
            agent_name: Unique agent identifier
            agent_callable: Agent execution function
            description: Agent description for UI
        """
        langgraph_agent = LangGraphAgent(
            name=agent_name,
            description=description,
            agent_callable=agent_callable
        )
        self.agents[agent_name] = langgraph_agent
        self.sdk.add_agent(langgraph_agent)

    def setup_endpoint(self, path: str = "/copilotkit"):
        """Setup FastAPI endpoint for CopilotKit.

        Args:
            path: Endpoint path (default: /copilotkit)
        """
        add_fastapi_endpoint(
            app=self.app,
            sdk=self.sdk,
            endpoint=path
        )

# Component Responsibilities:
# 1. Initialize CopilotKitSDK instance
# 2. Register all specialist agents as LangGraph agents
# 3. Setup FastAPI endpoint integration
# 4. Handle agent discovery and metadata
```

### 2.2 LangGraph Agent Wrapper Component

```python
# /src/copilotkit/agents/langgraph_wrapper.py

"""
LangGraph wrapper for existing Sergas agents.

Wraps ZohoDataScout, MemoryAnalyst, RecommendationAuthor in LangGraph interface.
"""

from typing import Dict, Any, AsyncGenerator
from langgraph.graph import StateGraph, END
from src.agents.zoho_data_scout import ZohoDataScout
from src.agents.memory_analyst import MemoryAnalyst
from src.agents.recommendation_author import RecommendationAuthor

class LangGraphAgentWrapper:
    """Wraps Sergas agents in LangGraph state machine."""

    def __init__(
        self,
        zoho_scout: ZohoDataScout,
        memory_analyst: MemoryAnalyst,
        recommendation_author: RecommendationAuthor
    ):
        self.zoho_scout = zoho_scout
        self.memory_analyst = memory_analyst
        self.recommendation_author = recommendation_author

        # Build LangGraph workflow
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build LangGraph state machine for agent coordination."""
        workflow = StateGraph()

        # Define nodes (agents)
        workflow.add_node("zoho_scout", self._zoho_scout_node)
        workflow.add_node("memory_analyst", self._memory_analyst_node)
        workflow.add_node("recommendation_author", self._recommendation_author_node)

        # Define edges (flow)
        workflow.add_edge("zoho_scout", "memory_analyst")
        workflow.add_edge("memory_analyst", "recommendation_author")
        workflow.add_edge("recommendation_author", END)

        # Set entry point
        workflow.set_entry_point("zoho_scout")

        return workflow.compile()

    async def _zoho_scout_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph node for ZohoDataScout."""
        account_id = state.get("account_id")
        snapshot = await self.zoho_scout.get_account_snapshot(account_id)

        state["account_snapshot"] = snapshot.model_dump()
        return state

    async def _memory_analyst_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph node for MemoryAnalyst."""
        account_id = state.get("account_id")
        context = await self.memory_analyst.get_historical_context(
            account_id=account_id,
            lookback_days=365,
            include_patterns=True
        )

        state["historical_context"] = context.model_dump()
        return state

    async def _recommendation_author_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph node for RecommendationAuthor."""
        recommendations = await self.recommendation_author.generate_recommendations(
            account_data=state.get("account_snapshot"),
            historical_context=state.get("historical_context")
        )

        state["recommendations"] = [r.model_dump() for r in recommendations]
        return state

    async def execute(self, input_state: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute LangGraph workflow with streaming."""
        async for event in self.graph.astream(input_state):
            yield event

# Component Responsibilities:
# 1. Wrap existing agents in LangGraph StateGraph
# 2. Define agent execution nodes
# 3. Define data flow between agents
# 4. Stream intermediate results to CopilotKit
```

### 2.3 Next.js API Route Component

```typescript
// /frontend/app/api/copilotkit/route.ts

/**
 * Next.js API Route for CopilotKit integration.
 *
 * Proxies CopilotKit requests to FastAPI backend.
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
const COPILOTKIT_ENDPOINT = '/copilotkit';

export async function POST(request: NextRequest) {
  try {
    // Extract request body and headers
    const body = await request.json();
    const authToken = request.headers.get('authorization');

    // Forward to FastAPI backend
    const response = await fetch(`${BACKEND_URL}${COPILOTKIT_ENDPOINT}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authToken || '',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    // Stream response back to frontend
    const data = await response.json();

    return NextResponse.json(data, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });

  } catch (error) {
    console.error('CopilotKit proxy error:', error);

    return NextResponse.json(
      { error: 'Failed to communicate with backend' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  // Health check for CopilotKit endpoint
  return NextResponse.json(
    { status: 'ok', endpoint: 'copilotkit-proxy' },
    { status: 200 }
  );
}

// Component Responsibilities:
// 1. Accept CopilotKit requests from frontend
// 2. Forward to FastAPI backend
// 3. Handle authentication
// 4. Stream responses back
// 5. Error handling and logging
```

### 2.4 AG UI Protocol Bridge Component

```python
# /src/copilotkit/ag_ui_bridge.py

"""
Bridge between AG UI Protocol and CopilotKit streaming.

Transforms AG UI events into CopilotKit-compatible format.
"""

from typing import Dict, Any, AsyncGenerator
from src.events.ag_ui_emitter import AGUIEventEmitter

class AGUIToCopilotKitBridge:
    """Transforms AG UI Protocol events to CopilotKit format."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.emitter = AGUIEventEmitter(session_id=session_id)

    async def transform_events(
        self,
        ag_ui_stream: AsyncGenerator[Dict[str, Any], None]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Transform AG UI events to CopilotKit format.

        AG UI Protocol Event Types:
        - RUN_STARTED, RUN_FINISHED, RUN_ERROR
        - agent_started, agent_completed, agent_error
        - agent_stream, tool_call, tool_result
        - approval_required, approval_granted

        CopilotKit Event Types:
        - message (text content)
        - action (agent action)
        - state (state update)
        """
        async for event in ag_ui_stream:
            event_type = event.get("event")

            if event_type == "agent_stream":
                # Transform to CopilotKit message
                yield {
                    "type": "message",
                    "content": event.get("data", {}).get("content", ""),
                    "metadata": {
                        "agent": event.get("data", {}).get("agent"),
                        "content_type": event.get("data", {}).get("content_type")
                    }
                }

            elif event_type in ["agent_started", "agent_completed"]:
                # Transform to CopilotKit action
                yield {
                    "type": "action",
                    "action": event.get("data", {}).get("agent"),
                    "status": "running" if event_type == "agent_started" else "completed",
                    "output": event.get("data", {}).get("output")
                }

            elif event_type == "tool_call":
                # Transform to CopilotKit tool usage
                yield {
                    "type": "tool_call",
                    "tool_name": event.get("data", {}).get("tool_name"),
                    "tool_args": event.get("data", {}).get("tool_args"),
                    "tool_call_id": event.get("data", {}).get("tool_call_id")
                }

            elif event_type == "approval_required":
                # Transform to CopilotKit approval request
                yield {
                    "type": "approval",
                    "approval_id": event.get("data", {}).get("approval_id"),
                    "recommendation": event.get("data", {}).get("recommendation"),
                    "timeout_hours": event.get("data", {}).get("timeout_hours")
                }

            else:
                # Pass through unknown events
                yield event

# Component Responsibilities:
# 1. Transform AG UI Protocol events
# 2. Map to CopilotKit event types
# 3. Preserve metadata and context
# 4. Handle streaming efficiently
```

---

## 3. Data Flow Architecture

### 3.1 Request/Response Flow Diagram

```
┌─────────────┐
│   Browser   │
│  (React UI) │
└──────┬──────┘
       │
       │ 1. User sends message via CopilotKit chat
       │    { message: "Analyze account ACC-001", context: {...} }
       │
       ▼
┌──────────────────────┐
│  CopilotKit Provider │
│  (Frontend Component)│
└──────┬───────────────┘
       │
       │ 2. useCopilotAction() hook triggered
       │    POST /api/copilotkit
       │
       ▼
┌──────────────────────┐
│  Next.js API Route   │
│  /api/copilotkit/    │
│      route.ts        │
└──────┬───────────────┘
       │
       │ 3. Proxy to FastAPI backend
       │    POST http://backend:8000/copilotkit
       │    Headers: { Authorization: "Bearer ..." }
       │
       ▼
┌──────────────────────────────┐
│  FastAPI Backend             │
│  CopilotKit SDK Endpoint     │
│  /copilotkit                 │
└──────┬───────────────────────┘
       │
       │ 4. CopilotKitSDK routes to LangGraph agent
       │    agent_callable(input_state)
       │
       ▼
┌──────────────────────────────┐
│  LangGraph Agent Wrapper     │
│  (State Machine)             │
└──────┬───────────────────────┘
       │
       │ 5. Execute agent workflow
       │
       ├─► ZohoDataScout Node
       │   • get_account_snapshot(account_id)
       │   • Emit: agent_started, tool_call, agent_completed
       │
       ├─► MemoryAnalyst Node
       │   • get_historical_context(account_id)
       │   • Emit: agent_started, tool_call, agent_completed
       │
       └─► RecommendationAuthor Node
           • generate_recommendations(...)
           • Emit: agent_started, agent_stream, approval_required

       │
       │ 6. AG UI → CopilotKit event transformation
       │    AGUIToCopilotKitBridge.transform_events()
       │
       ▼
┌──────────────────────────────┐
│  CopilotKit SDK              │
│  (Formats response)          │
└──────┬───────────────────────┘
       │
       │ 7. Stream response back through layers
       │    JSON stream with events
       │
       ▼
┌──────────────────────┐
│  Next.js API Route   │
│  (Proxies response)  │
└──────┬───────────────┘
       │
       │ 8. Stream to frontend
       │    Server-Sent Events (SSE) or JSON chunks
       │
       ▼
┌──────────────────────┐
│  CopilotKit Provider │
│  (Receives events)   │
└──────┬───────────────┘
       │
       │ 9. Update UI with agent responses
       │    • Display messages
       │    • Show tool calls
       │    • Handle approvals
       │
       ▼
┌─────────────┐
│   Browser   │
│ (UI Updated)│
└─────────────┘
```

### 3.2 Event Streaming Flow

```
Timeline: User Action → Agent Execution → UI Update

T=0ms     │ User: "Analyze account ACC-001"
          │
T=10ms    │ → CopilotKit hook triggered
          │ → POST /api/copilotkit
          │
T=50ms    │ → Next.js proxy forwards to FastAPI
          │ → POST http://backend:8000/copilotkit
          │
T=100ms   │ → CopilotKitSDK receives request
          │ → Routes to LangGraph agent
          │
T=150ms   │ → LangGraph workflow starts
          │ → Event: workflow_started
          │   { event: "workflow_started", workflow: "account_analysis" }
          │
T=200ms   │ → ZohoDataScout node executing
          │ → Event: agent_started
          │   { event: "agent_started", agent: "zoho_scout", step: 1 }
          │
T=500ms   │ → Zoho API calls in progress
          │ → Event: agent_stream
          │   { event: "agent_stream", content: "Fetching account data..." }
          │
T=1200ms  │ → ZohoDataScout completed
          │ → Event: agent_completed
          │   { event: "agent_completed", agent: "zoho_scout",
          │     output: { snapshot_id: "...", risk_level: "medium" } }
          │
T=1250ms  │ → MemoryAnalyst node executing
          │ → Event: agent_started
          │   { event: "agent_started", agent: "memory_analyst", step: 2 }
          │
T=1500ms  │ → Cognee memory queries in progress
          │ → Event: tool_call
          │   { event: "tool_call", tool_name: "cognee_search_memory" }
          │
T=2000ms  │ → MemoryAnalyst completed
          │ → Event: agent_completed
          │   { event: "agent_completed", agent: "memory_analyst",
          │     output: { patterns: 3, sentiment: "stable" } }
          │
T=2100ms  │ → RecommendationAuthor node executing
          │ → Event: agent_started
          │   { event: "agent_started", agent: "recommendation_author", step: 3 }
          │
T=3000ms  │ → Recommendations generated
          │ → Event: approval_required
          │   { event: "approval_required", recommendation: {...} }
          │
T=3100ms  │ → Workflow paused awaiting approval
          │ → UI shows approval dialog
          │
T=10000ms │ → User approves recommendation
          │ → POST /api/approvals/{id}/approve
          │
T=10100ms │ → Workflow resumes
          │ → Event: approval_granted
          │   { event: "approval_granted", approval_id: "..." }
          │
T=10200ms │ → Workflow completes
          │ → Event: workflow_completed
          │   { event: "workflow_completed", final_output: {...} }
          │
T=10300ms │ → UI updated with final results
```

### 3.3 State Management Flow

```python
# LangGraph State Schema

class AgentWorkflowState(TypedDict):
    """State passed between agents in LangGraph workflow."""

    # Input
    account_id: str
    workflow: str
    session_id: str

    # ZohoDataScout outputs
    account_snapshot: Optional[Dict[str, Any]]

    # MemoryAnalyst outputs
    historical_context: Optional[Dict[str, Any]]

    # RecommendationAuthor outputs
    recommendations: Optional[List[Dict[str, Any]]]

    # Approval tracking
    approval_status: Optional[str]
    approval_id: Optional[str]

    # Final output
    final_output: Optional[Dict[str, Any]]

    # Error handling
    errors: List[str]

# State transitions:
# 1. Initial state: { account_id, workflow, session_id }
# 2. After ZohoDataScout: + account_snapshot
# 3. After MemoryAnalyst: + historical_context
# 4. After RecommendationAuthor: + recommendations
# 5. After Approval: + approval_status, approval_id
# 6. Final: + final_output
```

---

## 4. Agent Architecture

### 4.1 Agent Wrapper Architecture

```
┌────────────────────────────────────────────────────────────────┐
│              LangGraph Agent Wrapper (StateMachine)            │
│                                                                 │
│  Entry Point → [zoho_scout] → [memory_analyst] →              │
│                [recommendation_author] → END                    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Node: zoho_scout                                         │ │
│  │  ┌────────────────────────────────────────────────────┐  │ │
│  │  │  Existing ZohoDataScout Agent                      │  │ │
│  │  │  • get_account_snapshot()                          │  │ │
│  │  │  • detect_changes()                                │  │ │
│  │  │  • aggregate_related_records()                     │  │ │
│  │  │  • identify_risk_signals()                         │  │ │
│  │  └────────────────────────────────────────────────────┘  │ │
│  │  Input: { account_id }                                    │ │
│  │  Output: { account_snapshot: {...} }                      │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Node: memory_analyst                                     │ │
│  │  ┌────────────────────────────────────────────────────┐  │ │
│  │  │  Existing MemoryAnalyst Agent                      │  │ │
│  │  │  • get_historical_context()                        │  │ │
│  │  │  • identify_patterns()                             │  │ │
│  │  │  • analyze_sentiment_trend()                       │  │ │
│  │  │  • assess_relationship_strength()                  │  │ │
│  │  └────────────────────────────────────────────────────┘  │ │
│  │  Input: { account_id, account_snapshot }                  │ │
│  │  Output: { historical_context: {...} }                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Node: recommendation_author                              │ │
│  │  ┌────────────────────────────────────────────────────┐  │ │
│  │  │  Existing RecommendationAuthor Agent               │  │ │
│  │  │  • generate_recommendations()                      │  │ │
│  │  │  • rank_recommendations()                          │  │ │
│  │  │  • apply_templates()                               │  │ │
│  │  └────────────────────────────────────────────────────┘  │ │
│  │  Input: { account_snapshot, historical_context }          │ │
│  │  Output: { recommendations: [...] }                       │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘

Event Emission at Each Node:
• agent_started: Before node execution
• tool_call: When calling external services (Zoho, Cognee)
• tool_result: After tool completes
• agent_stream: Progress updates
• agent_completed: After node finishes
• agent_error: If node fails
```

### 4.2 Agent Responsibility Matrix

| Agent | Primary Responsibility | Input | Output | External Dependencies |
|-------|----------------------|-------|--------|---------------------|
| **OrchestratorAgent** | Coordinate workflow | `account_id` | `final_output` | None (pure coordination) |
| **ZohoDataScout** | Fetch & analyze CRM data | `account_id` | `account_snapshot` | Zoho CRM MCP |
| **MemoryAnalyst** | Retrieve historical context | `account_id` | `historical_context` | Cognee Memory Service |
| **RecommendationAuthor** | Generate recommendations | `account_snapshot`, `historical_context` | `recommendations` | Claude LLM |
| **HttpAgent** (AG UI) | HTTP tool calls | `url`, `method`, `data` | `response` | External APIs |
| **a2aMiddlewareAgent** (AG UI) | Agent-to-agent messaging | `message`, `target_agent` | `ack` | Internal messaging |

### 4.3 Agent Communication Patterns

```
Pattern 1: Sequential Execution (Current)
┌───────────────┐      ┌────────────────┐      ┌─────────────────────┐
│ ZohoDataScout │ ───► │ MemoryAnalyst  │ ───► │ RecommendationAuthor│
└───────────────┘      └────────────────┘      └─────────────────────┘
      │                        │                          │
      ▼                        ▼                          ▼
  account_snapshot     historical_context         recommendations


Pattern 2: Parallel + Sequential (Future Optimization)
┌───────────────┐
│ ZohoDataScout │ ─┐
└───────────────┘  │
                   │
┌────────────────┐ ├──► Merge Context
│ MemoryAnalyst  │ ─┘          │
└────────────────┘              │
                                ▼
                    ┌─────────────────────┐
                    │ RecommendationAuthor│
                    └─────────────────────┘


Pattern 3: Event-Driven (AG UI Protocol)
┌───────────────┐   emit(agent_started)
│ ZohoDataScout │ ──────────────────────► Event Bus
└───────────────┘                            │
                                             │ subscribe
                                             ▼
                                    ┌────────────────┐
                                    │  UI Components │
                                    └────────────────┘
```

---

## 5. Folder Structure

### 5.1 Complete Directory Tree

```
/Users/mohammadabdelrahman/Projects/sergas_agents/
│
├── src/
│   ├── copilotkit/                          # NEW: CopilotKit integration
│   │   ├── __init__.py
│   │   ├── sdk_integration.py               # CopilotKitSDK initialization
│   │   ├── ag_ui_bridge.py                  # AG UI → CopilotKit transformer
│   │   │
│   │   ├── agents/                          # LangGraph-wrapped agents
│   │   │   ├── __init__.py
│   │   │   ├── langgraph_wrapper.py         # Main LangGraph wrapper
│   │   │   ├── orchestrator_langgraph.py    # Orchestrator as LangGraph
│   │   │   ├── zoho_scout_langgraph.py      # ZohoDataScout wrapper
│   │   │   ├── memory_analyst_langgraph.py  # MemoryAnalyst wrapper
│   │   │   └── recommendation_langgraph.py  # RecommendationAuthor wrapper
│   │   │
│   │   ├── config/                          # CopilotKit configuration
│   │   │   ├── __init__.py
│   │   │   ├── agent_config.py              # Agent metadata for CopilotKit
│   │   │   └── endpoint_config.py           # Endpoint configuration
│   │   │
│   │   └── utils/                           # Utilities
│   │       ├── __init__.py
│   │       ├── event_transformer.py         # Event transformation utilities
│   │       └── state_manager.py             # LangGraph state management
│   │
│   ├── agents/                              # EXISTING: Core agents
│   │   ├── __init__.py
│   │   ├── base_agent.py                    # Base agent with Claude SDK
│   │   ├── orchestrator.py                  # Current orchestrator
│   │   ├── zoho_data_scout.py               # Zoho data retrieval
│   │   ├── memory_analyst.py                # Historical analysis
│   │   ├── recommendation_author.py         # Recommendation generation
│   │   └── ...
│   │
│   ├── api/                                 # EXISTING: FastAPI routes
│   │   ├── __init__.py
│   │   ├── main.py                          # Main FastAPI app
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── accounts.py                  # Account endpoints
│   │   │   ├── copilotkit.py                # NEW: CopilotKit integration route
│   │   │   └── events.py                    # SSE events (legacy)
│   │   └── dependencies/
│   │       └── auth.py                      # Authentication
│   │
│   ├── events/                              # EXISTING: AG UI Protocol
│   │   ├── __init__.py
│   │   ├── ag_ui_emitter.py                 # Event emitter
│   │   └── approval_manager.py              # Approval workflow
│   │
│   └── ...
│
├── frontend/                                # Next.js frontend
│   ├── app/
│   │   ├── api/                             # NEW: Next.js API routes
│   │   │   └── copilotkit/
│   │   │       └── route.ts                 # CopilotKit proxy route
│   │   │
│   │   ├── dashboard/                       # Dashboard pages
│   │   └── ...
│   │
│   ├── components/                          # React components
│   │   ├── copilot/                         # NEW: CopilotKit components
│   │   │   ├── CopilotProvider.tsx          # CopilotKit provider wrapper
│   │   │   ├── AccountAnalysisAction.tsx    # Account analysis action
│   │   │   └── ApprovalDialog.tsx           # Approval UI
│   │   └── ...
│   │
│   └── ...
│
├── tests/                                   # Test suites
│   ├── unit/
│   │   ├── copilotkit/                      # NEW: CopilotKit tests
│   │   │   ├── test_sdk_integration.py
│   │   │   ├── test_langgraph_wrapper.py
│   │   │   └── test_ag_ui_bridge.py
│   │   └── ...
│   │
│   ├── integration/
│   │   ├── test_copilotkit_e2e.py           # NEW: End-to-end CopilotKit test
│   │   └── ...
│   │
│   └── ...
│
└── docs/                                    # Documentation
    ├── sparc/
    │   ├── 02_COPILOTKIT_ARCHITECTURE.md    # This document
    │   └── ...
    │
    └── integrations/
        └── copilotkit_integration_guide.md  # Implementation guide
```

### 5.2 New Files Summary

| File Path | Purpose | Priority |
|-----------|---------|----------|
| `/src/copilotkit/sdk_integration.py` | Initialize CopilotKitSDK | 🔴 Critical |
| `/src/copilotkit/agents/langgraph_wrapper.py` | Wrap agents in LangGraph | 🔴 Critical |
| `/src/copilotkit/ag_ui_bridge.py` | Transform AG UI events | 🟡 Important |
| `/frontend/app/api/copilotkit/route.ts` | Next.js proxy route | 🔴 Critical |
| `/frontend/components/copilot/CopilotProvider.tsx` | Frontend provider | 🔴 Critical |
| `/src/api/routes/copilotkit.py` | FastAPI CopilotKit route | 🟡 Important |
| `/tests/unit/copilotkit/test_langgraph_wrapper.py` | Unit tests | 🟢 Recommended |

---

## 6. API Architecture

### 6.1 CopilotKit API Endpoint Design

```python
# /src/api/routes/copilotkit.py

"""
FastAPI route for CopilotKit integration.

Endpoint: POST /copilotkit
Purpose: Handle CopilotKit SDK requests
"""

from fastapi import APIRouter, Depends, HTTPException
from copilotkit import CopilotKitSDK
from src.copilotkit.sdk_integration import CopilotKitIntegration
from src.api.dependencies.auth import get_current_user

router = APIRouter()

# Initialize CopilotKit integration
copilotkit = CopilotKitIntegration(app)

# Register agents
copilotkit.register_agent(
    agent_name="account_analyzer",
    agent_callable=langgraph_wrapper.execute,
    description="Analyze customer accounts with multi-agent system"
)

# Setup CopilotKit endpoint
copilotkit.setup_endpoint(path="/copilotkit")

# Endpoint Schema:
"""
POST /copilotkit

Request Body (CopilotKit format):
{
  "messages": [
    {
      "role": "user",
      "content": "Analyze account ACC-001"
    }
  ],
  "agent": "account_analyzer",
  "context": {
    "account_id": "ACC-001"
  }
}

Response (Streaming JSON):
{
  "event": "message",
  "content": "Starting account analysis...",
  "metadata": {
    "agent": "zoho_scout",
    "step": 1
  }
}

{
  "event": "action",
  "action": "fetch_account_data",
  "status": "completed",
  "output": {
    "snapshot_id": "snap_123",
    "risk_level": "medium"
  }
}

{
  "event": "approval",
  "approval_id": "appr_456",
  "recommendation": {
    "action_type": "schedule_followup",
    "priority": "high"
  }
}
"""
```

### 6.2 Next.js API Route Specification

```typescript
// /frontend/app/api/copilotkit/route.ts

/**
 * Next.js API Route Specification
 *
 * Endpoint: POST /api/copilotkit
 * Purpose: Proxy CopilotKit requests to FastAPI backend
 */

// Request Interface
interface CopilotKitRequest {
  messages: Array<{
    role: 'user' | 'assistant' | 'system';
    content: string;
  }>;
  agent: string;
  context?: Record<string, any>;
}

// Response Interface
interface CopilotKitResponse {
  event: 'message' | 'action' | 'approval' | 'error';
  content?: string;
  action?: string;
  status?: string;
  output?: Record<string, any>;
  error?: string;
}

// Implementation
export async function POST(request: NextRequest): Promise<NextResponse> {
  // 1. Parse and validate request
  // 2. Extract authentication token
  // 3. Forward to FastAPI backend
  // 4. Stream response back to frontend
  // 5. Handle errors appropriately
}

// Error Handling
// - 400: Invalid request format
// - 401: Unauthorized (missing/invalid token)
// - 500: Backend communication error
// - 504: Backend timeout
```

### 6.3 API Request/Response Examples

```json
// Example 1: Account Analysis Request
POST /api/copilotkit
Content-Type: application/json
Authorization: Bearer eyJhbGc...

{
  "messages": [
    {
      "role": "user",
      "content": "Analyze account ACC-001 and provide recommendations"
    }
  ],
  "agent": "account_analyzer",
  "context": {
    "account_id": "ACC-001",
    "workflow": "account_analysis"
  }
}

// Response (Streamed Events)
{
  "event": "message",
  "content": "Starting account analysis for ACC-001...",
  "metadata": { "agent": "orchestrator", "step": 0 }
}

{
  "event": "action",
  "action": "fetch_account_data",
  "status": "running",
  "metadata": { "agent": "zoho_scout", "step": 1 }
}

{
  "event": "message",
  "content": "Retrieved account snapshot. Risk level: medium",
  "metadata": { "agent": "zoho_scout" }
}

{
  "event": "action",
  "action": "fetch_account_data",
  "status": "completed",
  "output": {
    "snapshot_id": "snap_20251019_001",
    "risk_level": "medium",
    "priority_score": 65
  }
}

{
  "event": "action",
  "action": "analyze_historical_context",
  "status": "running",
  "metadata": { "agent": "memory_analyst", "step": 2 }
}

{
  "event": "message",
  "content": "Detected 3 patterns in account history",
  "metadata": { "agent": "memory_analyst" }
}

{
  "event": "action",
  "action": "analyze_historical_context",
  "status": "completed",
  "output": {
    "patterns": 3,
    "sentiment_trend": "stable",
    "relationship_strength": "strong"
  }
}

{
  "event": "action",
  "action": "generate_recommendations",
  "status": "running",
  "metadata": { "agent": "recommendation_author", "step": 3 }
}

{
  "event": "approval",
  "approval_id": "appr_789",
  "recommendation": {
    "recommendation_id": "rec_456",
    "action_type": "schedule_executive_review",
    "priority": "high",
    "reasoning": "Strong relationship but recent inactivity detected"
  },
  "timeout_hours": 24
}
```

---

## 7. Deployment Architecture

### 7.1 Production Deployment Diagram

```
                        ┌─────────────────────────────────┐
                        │       Load Balancer             │
                        │     (Nginx / CloudFlare)        │
                        └────────────┬────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                  │
                    ▼                                  ▼
        ┌───────────────────────┐        ┌───────────────────────┐
        │   Next.js Frontend    │        │   FastAPI Backend     │
        │   (Vercel / Docker)   │        │   (Docker Compose)    │
        │                       │        │                       │
        │  • React App          │        │  • CopilotKit SDK     │
        │  • API Routes         │        │  • LangGraph Agents   │
        │  • Static Assets      │        │  • AG UI Bridge       │
        └───────────────────────┘        └──────────┬────────────┘
                                                    │
                                    ┌───────────────┼───────────────┐
                                    │               │               │
                                    ▼               ▼               ▼
                        ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
                        │  PostgreSQL  │  │  Redis Cache │  │  Cognee API  │
                        │   Database   │  │              │  │  (Memory)    │
                        └──────────────┘  └──────────────┘  └──────────────┘
                                                    │
                                                    ▼
                                        ┌──────────────────────┐
                                        │  Zoho CRM (External) │
                                        └──────────────────────┘
```

### 7.2 Container Architecture (Docker)

```yaml
# docker-compose.yml

version: '3.8'

services:
  # Next.js Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_BACKEND_URL=http://backend:8000
    depends_on:
      - backend

  # FastAPI Backend with CopilotKit
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/sergas
      - REDIS_URL=redis://redis:6379/0
      - COGNEE_API_URL=http://cognee:8080
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ZOHO_CLIENT_ID=${ZOHO_CLIENT_ID}
      - ZOHO_CLIENT_SECRET=${ZOHO_CLIENT_SECRET}
    volumes:
      - ./src:/app/src
    depends_on:
      - postgres
      - redis
      - cognee

  # PostgreSQL Database
  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=sergas
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis Cache
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  # Cognee Memory Service
  cognee:
    image: cognee/cognee:latest
    ports:
      - "8080:8080"
    environment:
      - NEO4J_URL=bolt://neo4j:7687
    depends_on:
      - neo4j

  # Neo4j Graph Database (for Cognee)
  neo4j:
    image: neo4j:5-community
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
    volumes:
      - neo4j_data:/data

volumes:
  postgres_data:
  redis_data:
  neo4j_data:
```

### 7.3 Scalability Architecture

```
High-Traffic Scenario (1000+ concurrent users)

┌─────────────────────────────────────────────────────────────┐
│                      CDN Layer                               │
│                   (CloudFlare / CloudFront)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│  Frontend Pool   │          │  Backend Pool    │
│  (3-5 instances) │          │  (5-10 instances)│
│                  │          │                  │
│  • Load balanced │          │  • Horizontal    │
│  • Auto-scaling  │          │    scaling       │
│  • Health checks │          │  • Queue-based   │
└──────────────────┘          └────────┬─────────┘
                                       │
                      ┌────────────────┼────────────────┐
                      │                │                │
                      ▼                ▼                ▼
          ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
          │  DB Primary  │   │  Redis       │   │  Task Queue  │
          │  + Replicas  │   │  Cluster     │   │  (Celery)    │
          │  (Read/Write)│   │  (Cache)     │   │  (Async)     │
          └──────────────┘   └──────────────┘   └──────────────┘

Scaling Strategies:
1. Frontend: Auto-scale based on request rate
2. Backend: Scale by CPU/memory usage + queue depth
3. Database: Read replicas for heavy queries
4. Cache: Redis cluster for session/state management
5. Task Queue: Celery workers for async agent execution
```

---

## 8. Integration Points

### 8.1 CopilotKit Frontend Integration

```typescript
// /frontend/components/copilot/CopilotProvider.tsx

import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";

export function CopilotProvider({ children }: { children: React.ReactNode }) {
  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      agent="account_analyzer"
    >
      <CopilotSidebar>
        {children}
      </CopilotSidebar>
    </CopilotKit>
  );
}

// Usage in app
// /frontend/app/layout.tsx
import { CopilotProvider } from '@/components/copilot/CopilotProvider';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <CopilotProvider>
          {children}
        </CopilotProvider>
      </body>
    </html>
  );
}
```

### 8.2 AG UI Protocol Integration

```python
# /src/copilotkit/ag_ui_bridge.py (expanded)

from src.events.ag_ui_emitter import AGUIEventEmitter
from src.events.approval_manager import ApprovalManager

class AGUIIntegration:
    """
    Bridge between AG UI Protocol and CopilotKit.

    AG UI Protocol provides:
    1. HttpAgent - Make HTTP calls from chat
    2. a2aMiddlewareAgent - Agent-to-agent messaging
    3. Event streaming for UI updates
    4. Approval workflows

    Integration Points:
    - Emit AG UI events during agent execution
    - Transform events to CopilotKit format
    - Handle approval requests via AG UI Protocol
    - Enable HttpAgent for external API calls
    """

    def __init__(self, session_id: str, approval_manager: ApprovalManager):
        self.session_id = session_id
        self.emitter = AGUIEventEmitter(session_id=session_id)
        self.approval_manager = approval_manager

    async def handle_approval_required(
        self,
        recommendation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle approval workflow using AG UI Protocol."""

        # Create approval request
        approval_request = await self.approval_manager.create_approval_request(
            recommendation_id=recommendation["recommendation_id"],
            recommendation=recommendation,
            run_id=self.session_id,
            timeout_seconds=86400  # 24 hours
        )

        # Emit AG UI approval event
        approval_event = self.emitter.emit_approval_required(
            recommendation=recommendation,
            timeout_hours=24
        )

        # Transform to CopilotKit format
        copilotkit_event = {
            "type": "approval",
            "approval_id": approval_request.approval_id,
            "recommendation": recommendation,
            "actions": ["approve", "reject", "defer"],
            "timeout": 24
        }

        return copilotkit_event
```

### 8.3 External Service Integration

```python
# Integration Matrix

class ExternalIntegrations:
    """
    External service integrations for agent system.
    """

    # Zoho CRM Integration (via MCP)
    zoho_integration = {
        "service": "Zoho CRM",
        "protocol": "MCP (Model Context Protocol)",
        "tools": [
            "mcp_zoho_get_account",
            "mcp_zoho_search_accounts",
            "mcp_zoho_get_deals",
            "mcp_zoho_get_activities"
        ],
        "authentication": "OAuth 2.0",
        "used_by": ["ZohoDataScout"]
    }

    # Cognee Memory Integration
    cognee_integration = {
        "service": "Cognee Knowledge Graph",
        "protocol": "REST API + MCP Tools",
        "tools": [
            "cognee_search_memory",
            "cognee_retrieve_history",
            "cognee_aggregate_insights",
            "cognee_get_relationship_graph"
        ],
        "authentication": "API Key",
        "used_by": ["MemoryAnalyst"]
    }

    # Claude LLM Integration (via Anthropic SDK)
    claude_integration = {
        "service": "Claude LLM (Anthropic)",
        "protocol": "Anthropic SDK",
        "models": ["claude-3-5-sonnet-20241022"],
        "features": [
            "Multi-turn conversations",
            "Function calling",
            "Streaming responses"
        ],
        "authentication": "API Key",
        "used_by": ["RecommendationAuthor", "All agents via Claude Agent SDK"]
    }

    # PostgreSQL Database
    database_integration = {
        "service": "PostgreSQL",
        "protocol": "SQLAlchemy ORM",
        "tables": [
            "accounts",
            "account_snapshots",
            "recommendations",
            "approval_requests",
            "audit_logs"
        ],
        "authentication": "Username/Password",
        "used_by": ["All agents for persistence"]
    }
```

---

## 9. Security Architecture

### 9.1 Authentication & Authorization Flow

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ 1. User login
       │    POST /api/auth/login
       │    { email, password }
       │
       ▼
┌──────────────────────┐
│  Next.js Auth API    │
│  /api/auth/login     │
└──────┬───────────────┘
       │ 2. Verify credentials
       │    (NextAuth.js)
       │
       ▼
┌──────────────────────┐
│  FastAPI Auth        │
│  POST /api/v1/login  │
└──────┬───────────────┘
       │ 3. Generate JWT token
       │    { access_token, refresh_token }
       │
       ▼
┌──────────────────────┐
│  Browser stores JWT  │
│  (httpOnly cookie)   │
└──────┬───────────────┘
       │ 4. All subsequent requests
       │    include JWT in Authorization header
       │
       ▼
┌──────────────────────┐
│  Next.js API Route   │
│  /api/copilotkit     │
└──────┬───────────────┘
       │ 5. Extract and forward JWT
       │    Authorization: Bearer {token}
       │
       ▼
┌──────────────────────────────┐
│  FastAPI Middleware          │
│  verify_jwt_token()          │
│  check_permissions()         │
└──────┬───────────────────────┘
       │ 6. If valid, allow request
       │    If invalid, return 401
       │
       ▼
┌──────────────────────────────┐
│  CopilotKit SDK Endpoint     │
│  (Protected resource)        │
└──────────────────────────────┘

Security Layers:
1. TLS/HTTPS encryption for all traffic
2. JWT authentication with expiration
3. httpOnly cookies to prevent XSS
4. CORS restrictions on API routes
5. Rate limiting on sensitive endpoints
6. SQL injection prevention (parameterized queries)
7. Input validation and sanitization
```

### 9.2 API Security Controls

```python
# /src/api/middleware/security.py

from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta

security = HTTPBearer()

class SecurityControls:
    """API security controls."""

    @staticmethod
    def verify_jwt_token(
        credentials: HTTPAuthorizationCredentials = Security(security)
    ) -> dict:
        """Verify JWT token and extract user info."""
        token = credentials.credentials

        try:
            payload = jwt.decode(
                token,
                key=settings.JWT_SECRET_KEY,
                algorithms=["HS256"]
            )

            # Check expiration
            if datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )

            return payload

        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    @staticmethod
    def check_permissions(user: dict, required_permissions: list[str]) -> bool:
        """Check if user has required permissions."""
        user_permissions = user.get("permissions", [])

        for permission in required_permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {permission}"
                )

        return True

# Usage in protected endpoints
@router.post("/copilotkit")
async def copilotkit_endpoint(
    request: CopilotKitRequest,
    user: dict = Depends(SecurityControls.verify_jwt_token)
):
    # Verify user has permission to use agents
    SecurityControls.check_permissions(user, ["agents:execute"])

    # Process request
    ...
```

### 9.3 Data Protection

```python
# Data Security Controls

class DataProtection:
    """Data protection and privacy controls."""

    # Sensitive field encryption
    @staticmethod
    def encrypt_sensitive_fields(data: dict) -> dict:
        """Encrypt sensitive fields before storage."""
        sensitive_fields = ["api_key", "password", "token"]

        for field in sensitive_fields:
            if field in data:
                data[field] = encrypt(data[field])

        return data

    # PII masking for logs
    @staticmethod
    def mask_pii(log_message: str) -> str:
        """Mask personally identifiable information in logs."""
        import re

        # Mask email addresses
        log_message = re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '***@***.***',
            log_message
        )

        # Mask phone numbers
        log_message = re.sub(
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            '***-***-****',
            log_message
        )

        return log_message

    # Audit logging
    @staticmethod
    async def audit_log(
        user_id: str,
        action: str,
        resource: str,
        metadata: dict
    ):
        """Log user actions for audit trail."""
        await db.audit_logs.insert({
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "metadata": metadata,
            "timestamp": datetime.utcnow(),
            "ip_address": request.client.host
        })

# Security Best Practices:
# 1. Never log sensitive data (API keys, passwords, tokens)
# 2. Encrypt data at rest (database encryption)
# 3. Encrypt data in transit (TLS 1.3)
# 4. Implement rate limiting to prevent abuse
# 5. Use parameterized queries to prevent SQL injection
# 6. Validate and sanitize all user inputs
# 7. Implement CSRF protection for state-changing operations
# 8. Regular security audits and penetration testing
```

---

## 10. Performance Considerations

### 10.1 Performance Targets

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| **API Response Time** | < 200ms (p95) | < 500ms |
| **Agent Orchestration** | < 5s (complete workflow) | < 10s |
| **Frontend Load Time** | < 2s (FCP) | < 4s |
| **Database Query Time** | < 100ms (p95) | < 250ms |
| **Memory Usage** | < 512MB per agent | < 1GB |
| **Concurrent Users** | 500+ simultaneous | 1000+ peak |

### 10.2 Optimization Strategies

```python
# 1. Caching Strategy

class CacheOptimization:
    """Multi-layer caching for performance."""

    # Redis cache for frequently accessed data
    @staticmethod
    @cache(ttl=300)  # 5 minutes
    async def get_account_snapshot(account_id: str):
        """Cache account snapshots."""
        return await zoho_scout.get_account_snapshot(account_id)

    # In-memory cache for static data
    @staticmethod
    @lru_cache(maxsize=1000)
    def get_recommendation_template(template_id: str):
        """Cache recommendation templates."""
        return recommendation_templates.get(template_id)

    # Database query result cache
    @staticmethod
    async def get_historical_context_cached(account_id: str):
        """Cache historical context queries."""
        cache_key = f"historical_context:{account_id}"

        # Try cache first
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # Fetch from database
        result = await memory_analyst.get_historical_context(account_id)

        # Cache for 1 hour
        await redis.setex(cache_key, 3600, json.dumps(result))

        return result

# 2. Parallel Execution

class ParallelOptimization:
    """Execute independent tasks in parallel."""

    @staticmethod
    async def fetch_all_data(account_id: str):
        """Fetch all data sources in parallel."""

        # Execute in parallel using asyncio.gather
        account_data, historical_data, deals_data = await asyncio.gather(
            zoho_scout.get_account_snapshot(account_id),
            memory_analyst.get_historical_context(account_id),
            zoho_manager.get_deals(account_id),
            return_exceptions=True
        )

        return {
            "account": account_data,
            "history": historical_data,
            "deals": deals_data
        }

# 3. Database Optimization

class DatabaseOptimization:
    """Optimize database queries."""

    # Use indexes on frequently queried columns
    indexes = [
        "accounts(account_id)",
        "accounts(owner_id, status)",
        "audit_logs(timestamp, user_id)",
        "recommendations(account_id, created_at)"
    ]

    # Use connection pooling
    db_pool = create_async_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True
    )

    # Optimize queries with joins
    @staticmethod
    async def get_account_with_related(account_id: str):
        """Fetch account with related data in single query."""

        query = """
        SELECT
            a.*,
            json_agg(d.*) as deals,
            json_agg(n.*) as notes
        FROM accounts a
        LEFT JOIN deals d ON d.account_id = a.account_id
        LEFT JOIN notes n ON n.account_id = a.account_id
        WHERE a.account_id = :account_id
        GROUP BY a.account_id
        """

        return await db.execute(query, {"account_id": account_id})

# 4. LangGraph Optimization

class LangGraphOptimization:
    """Optimize LangGraph agent execution."""

    # Conditional node execution (skip unnecessary nodes)
    workflow = StateGraph()

    def should_analyze_memory(state: dict) -> bool:
        """Only analyze memory if account has activity."""
        return state.get("account_snapshot", {}).get("last_activity_days", 0) < 90

    # Add conditional edge
    workflow.add_conditional_edges(
        "zoho_scout",
        should_analyze_memory,
        {
            True: "memory_analyst",
            False: "recommendation_author"  # Skip memory analysis
        }
    )

    # Checkpoint for long-running workflows
    workflow = workflow.compile(
        checkpointer=MemorySaver()  # Save state at each node
    )
```

### 10.3 Monitoring & Alerting

```python
# Performance monitoring setup

from prometheus_client import Counter, Histogram, Gauge
import structlog

# Metrics
agent_execution_time = Histogram(
    'agent_execution_seconds',
    'Agent execution time',
    ['agent_name', 'status']
)

api_request_count = Counter(
    'api_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status']
)

active_sessions = Gauge(
    'active_sessions',
    'Number of active CopilotKit sessions'
)

# Logging
logger = structlog.get_logger()

# Alert thresholds
ALERTS = {
    "high_response_time": {
        "threshold": 500,  # ms
        "action": "Page on-call engineer"
    },
    "high_error_rate": {
        "threshold": 0.05,  # 5%
        "action": "Send alert to Slack"
    },
    "database_connection_failure": {
        "threshold": 3,  # retries
        "action": "Escalate to DBA team"
    }
}

# Monitoring dashboard (Grafana)
# - Agent execution times (p50, p95, p99)
# - API response times
# - Error rates by endpoint
# - Database query performance
# - Cache hit rates
# - Active user sessions
# - Resource utilization (CPU, memory, disk)
```

---

## Appendix A: Migration Plan

### Phase 1: Foundation (Week 1)
- [ ] Install CopilotKit SDK dependencies
- [ ] Create `/src/copilotkit/` directory structure
- [ ] Implement `sdk_integration.py`
- [ ] Create Next.js API route `/api/copilotkit/route.ts`

### Phase 2: Agent Wrappers (Week 2)
- [ ] Implement `LangGraphAgentWrapper` base class
- [ ] Wrap `ZohoDataScout` in LangGraph
- [ ] Wrap `MemoryAnalyst` in LangGraph
- [ ] Wrap `RecommendationAuthor` in LangGraph
- [ ] Unit tests for each wrapper

### Phase 3: Integration (Week 3)
- [ ] Implement AG UI → CopilotKit bridge
- [ ] Setup FastAPI endpoint with `add_fastapi_endpoint()`
- [ ] Frontend CopilotKit provider integration
- [ ] End-to-end integration testing

### Phase 4: Testing & Optimization (Week 4)
- [ ] Performance benchmarking
- [ ] Load testing (100+ concurrent users)
- [ ] Security audit
- [ ] Documentation updates

### Phase 5: Deployment (Week 5)
- [ ] Staging environment deployment
- [ ] User acceptance testing
- [ ] Production deployment
- [ ] Monitoring and alerting setup

---

## Appendix B: Reference Links

- **CopilotKit Documentation**: https://docs.copilotkit.ai
- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **AG UI Protocol Spec**: https://docs.agui.io/protocol
- **Claude Agent SDK**: https://github.com/anthropics/claude-agent-sdk
- **FastAPI**: https://fastapi.tiangolo.com
- **Next.js API Routes**: https://nextjs.org/docs/app/building-your-application/routing/route-handlers

---

**End of Architecture Document**

**Next Steps**:
1. Review and approve architecture
2. Begin Phase 1 implementation
3. Setup development environment
4. Create task breakdown for SPARC Refinement phase
