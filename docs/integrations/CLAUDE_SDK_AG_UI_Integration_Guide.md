# Claude Agent SDK + CopilotKit Integration Guide

**Status**: Research & Architecture Document
**Created**: 2025-10-19
**Author**: Sergas Engineering Team
**Version**: 1.0.0

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Compatibility Analysis](#compatibility-analysis)
4. [Integration Patterns](#integration-patterns)
5. [Implementation Guide](#implementation-guide)
6. [Code Examples](#code-examples)
7. [State Synchronization](#state-synchronization)
8. [Compatibility Issues & Workarounds](#compatibility-issues--workarounds)
9. [Migration Path](#migration-path)
10. [Best Practices](#best-practices)

---

## Executive Summary

### Key Findings

**Direct Compatibility**: Claude Agent SDK does NOT directly integrate with CopilotKit's CoAgent system as CopilotKit is designed primarily for LangGraph-based agents.

**Integration Strategy**: We must use CopilotKit's **AG-UI Protocol** (Agent-User Interaction Protocol) to create a custom bridge between Claude SDK and CopilotKit's frontend components.

**Recommended Approach**: Wrap our `BaseAgent` (Claude SDK) as an AG-UI-compatible backend, allowing CopilotKit's React components to communicate with Claude agents via the standardized AG-UI protocol.

### Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                       Frontend (React)                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CopilotChat Component                                    │  │
│  │  - useCoAgent() hook                                      │  │
│  │  - State management                                       │  │
│  │  - UI rendering                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │ AG-UI Protocol (SSE/HTTP)
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                   Backend (FastAPI)                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  AG-UI Bridge                                             │  │
│  │  - /copilotkit endpoint                                   │  │
│  │  - SSE stream handler                                     │  │
│  │  - AG-UI event emitter                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                         │                                       │
│  ┌──────────────────────▼───────────────────────────────────┐  │
│  │  BaseAgent Wrapper                                        │  │
│  │  - ClaudeSDKClient integration                            │  │
│  │  - Hook system (audit, metrics, permissions)             │  │
│  │  - Session management                                     │  │
│  │  - Tool execution                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                         │                                       │
│  ┌──────────────────────▼───────────────────────────────────┐  │
│  │  Claude Agent SDK (ClaudeSDKClient)                       │  │
│  │  - Streaming responses                                    │  │
│  │  - Tool calling                                           │  │
│  │  - Permission enforcement                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Overview

### 1. Claude SDK Compatibility Analysis

**Question**: Does Claude Agent SDK work with CopilotKit directly?
**Answer**: **NO** - CopilotKit is designed for LangGraph agents, not Claude SDK.

**Why Not?**
- CopilotKit's `LangGraphAgent` expects a LangGraph `StateGraph` instance
- Claude SDK uses `ClaudeSDKClient`, a fundamentally different architecture
- No built-in adapter exists between the two systems

**Solution**: Use the **AG-UI Protocol** as a bridge.

### 2. AG-UI Protocol: The Bridge

**What is AG-UI?**
- Open-source protocol by CopilotKit for agent-frontend communication
- Framework-agnostic (supports LangGraph, CrewAI, PydanticAI, ADK, and custom backends)
- Uses Server-Sent Events (SSE) for real-time streaming
- Standardizes event formats, state synchronization, and tool execution

**Why AG-UI?**
- Decouples agent framework from frontend components
- Enables M frameworks + N clients instead of M * N integrations
- Provides standard patterns for streaming, state, and tool calls

### 3. Integration Layers

Our integration requires **three layers**:

1. **Frontend Layer**: CopilotKit React components
2. **Bridge Layer**: AG-UI protocol implementation
3. **Backend Layer**: Claude SDK BaseAgent wrapper

---

## Compatibility Analysis

### Claude SDK vs CopilotKit Feature Matrix

| Feature | Claude SDK | CopilotKit (LangGraph) | AG-UI Bridge |
|---------|-----------|------------------------|--------------|
| Streaming Responses | ✅ AsyncGenerator | ✅ StateGraph events | ✅ SSE streams |
| Tool Execution | ✅ Custom tools | ✅ LangChain tools | ✅ AG-UI tool protocol |
| State Management | ❌ Manual | ✅ StateGraph | ✅ AG-UI state events |
| Session Management | ✅ session_id | ✅ thread_id | ✅ session mapping |
| Hooks System | ✅ Pre/Post hooks | ✅ LangGraph callbacks | ✅ Event translation |
| Permission Control | ✅ permission_mode | ❌ N/A | ✅ Hook integration |
| Frontend Integration | ❌ No built-in | ✅ React components | ✅ Via AG-UI |

### Key Compatibility Issues

1. **State Model Mismatch**
   - Claude SDK: No built-in state model
   - CopilotKit: Expects TypedDict state with `messages` field
   - **Workaround**: Create custom state wrapper

2. **Streaming Format Differences**
   - Claude SDK: Custom chunk format from `ClaudeSDKClient.query()`
   - AG-UI: Expects specific event types (StateSnapshotEvent, ToolCallEvent, etc.)
   - **Workaround**: Event translation layer

3. **Tool Calling Protocol**
   - Claude SDK: Hook-based tool execution
   - AG-UI: Declarative tool definitions with results
   - **Workaround**: Tool adapter pattern

4. **Session Management**
   - Claude SDK: `session_id` (string)
   - CopilotKit: `thread_id` (string) + runnable state
   - **Workaround**: Session mapping layer

---

## Integration Patterns

### Pattern 1: Wrapper Pattern (Recommended)

Wrap `BaseAgent` as an AG-UI-compatible backend without modifying the core agent.

**Pros**:
- Non-invasive to existing BaseAgent code
- Easy to maintain and update
- Clear separation of concerns

**Cons**:
- Additional translation layer
- Slight performance overhead

### Pattern 2: Direct Inheritance Pattern

Create `CoAgentBaseAgent` that inherits from `BaseAgent` and implements AG-UI protocol.

**Pros**:
- More integrated solution
- Potentially better performance

**Cons**:
- Modifies BaseAgent architecture
- Tighter coupling to CopilotKit

**Recommendation**: Use **Pattern 1** (Wrapper) for flexibility and maintainability.

---

## Implementation Guide

### Step 1: Install Dependencies

```bash
# Add to requirements.txt
copilotkit>=0.1.39
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
sse-starlette>=1.6.5

# Install
pip install copilotkit fastapi uvicorn[standard] sse-starlette
```

### Step 2: Create AG-UI Events

Create event classes for AG-UI protocol:

```python
# src/integrations/copilotkit/events.py

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class AGUIEvent(BaseModel):
    """Base class for all AG-UI events."""
    event: str

    def to_sse(self) -> str:
        """Convert to SSE format."""
        return f"data: {self.model_dump_json()}\n\n"


class StateSnapshotEvent(AGUIEvent):
    """State snapshot event for frontend state sync."""
    event: Literal["state_snapshot"] = "state_snapshot"
    state: Dict[str, Any]
    timestamp: float


class TextChunkEvent(AGUIEvent):
    """Text chunk event for streaming responses."""
    event: Literal["text_chunk"] = "text_chunk"
    chunk: str
    message_id: str


class ToolCallEvent(AGUIEvent):
    """Tool call event when agent invokes a tool."""
    event: Literal["tool_call"] = "tool_call"
    tool_name: str
    tool_input: Dict[str, Any]
    tool_call_id: str


class ToolResultEvent(AGUIEvent):
    """Tool result event after tool execution."""
    event: Literal["tool_result"] = "tool_result"
    tool_call_id: str
    result: Any
    error: Optional[str] = None


class SessionStartEvent(AGUIEvent):
    """Session start event."""
    event: Literal["session_start"] = "session_start"
    session_id: str
    agent_id: str


class SessionEndEvent(AGUIEvent):
    """Session end event."""
    event: Literal["session_end"] = "session_end"
    session_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### Step 3: Create BaseAgent Wrapper

Create wrapper that translates between Claude SDK and AG-UI:

```python
# src/integrations/copilotkit/base_agent_wrapper.py

import asyncio
import time
from typing import Any, AsyncGenerator, Dict, Optional
import structlog

from src.agents.base_agent import BaseAgent
from src.integrations.copilotkit.events import (
    AGUIEvent,
    StateSnapshotEvent,
    TextChunkEvent,
    ToolCallEvent,
    ToolResultEvent,
    SessionStartEvent,
    SessionEndEvent,
)

logger = structlog.get_logger(__name__)


class BaseAgentAGUIWrapper:
    """
    Wrapper that adapts BaseAgent (Claude SDK) to AG-UI protocol.

    This allows CopilotKit frontend components to communicate with
    Claude SDK agents via the standardized AG-UI protocol.
    """

    def __init__(self, agent: BaseAgent):
        """
        Initialize wrapper with a BaseAgent instance.

        Args:
            agent: BaseAgent instance to wrap
        """
        self.agent = agent
        self.logger = logger.bind(
            agent_id=agent.agent_id,
            wrapper="ag-ui"
        )

        # State management
        self.state: Dict[str, Any] = {
            "messages": [],
            "agent_id": agent.agent_id,
            "session_id": None,
        }

        # Tool execution tracking
        self.pending_tools: Dict[str, Dict[str, Any]] = {}

    async def stream_query(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[AGUIEvent, None]:
        """
        Stream AG-UI events for a given task.

        This method:
        1. Starts a session
        2. Emits state snapshots
        3. Streams text chunks from Claude SDK
        4. Handles tool calls
        5. Ends the session

        Args:
            task: Task description
            context: Optional context

        Yields:
            AG-UI events for frontend consumption
        """
        # Initialize agent if needed
        if not self.agent.session_id:
            await self.agent.initialize()

        # Emit session start event
        self.state["session_id"] = self.agent.session_id
        yield SessionStartEvent(
            session_id=self.agent.session_id,
            agent_id=self.agent.agent_id,
        )

        # Emit initial state snapshot
        yield StateSnapshotEvent(
            state=self.state.copy(),
            timestamp=time.time(),
        )

        # Add user message to state
        user_message = {"role": "user", "content": task}
        self.state["messages"].append(user_message)

        # Emit state update
        yield StateSnapshotEvent(
            state=self.state.copy(),
            timestamp=time.time(),
        )

        try:
            # Stream from Claude SDK
            message_id = f"msg-{int(time.time() * 1000)}"
            full_response = ""

            async for chunk in self.agent.query(task, context):
                chunk_type = chunk.get("type")

                if chunk_type == "text":
                    # Text chunk
                    content = chunk.get("content", "")
                    full_response += content

                    yield TextChunkEvent(
                        chunk=content,
                        message_id=message_id,
                    )

                elif chunk_type == "tool_use":
                    # Tool call
                    tool_name = chunk.get("name")
                    tool_input = chunk.get("input", {})
                    tool_call_id = chunk.get("id", f"tool-{int(time.time() * 1000)}")

                    self.pending_tools[tool_call_id] = {
                        "name": tool_name,
                        "input": tool_input,
                    }

                    yield ToolCallEvent(
                        tool_name=tool_name,
                        tool_input=tool_input,
                        tool_call_id=tool_call_id,
                    )

                elif chunk_type == "tool_result":
                    # Tool result
                    tool_call_id = chunk.get("tool_use_id")
                    result = chunk.get("content")
                    error = chunk.get("error")

                    yield ToolResultEvent(
                        tool_call_id=tool_call_id,
                        result=result,
                        error=error,
                    )

                    # Remove from pending
                    self.pending_tools.pop(tool_call_id, None)

            # Add assistant message to state
            assistant_message = {
                "role": "assistant",
                "content": full_response,
                "message_id": message_id,
            }
            self.state["messages"].append(assistant_message)

            # Emit final state snapshot
            yield StateSnapshotEvent(
                state=self.state.copy(),
                timestamp=time.time(),
            )

        finally:
            # Emit session end event
            await self.agent.cleanup()

            yield SessionEndEvent(
                session_id=self.agent.session_id,
                metadata={
                    "message_count": len(self.state["messages"]),
                    "task": task,
                },
            )

    def get_state(self) -> Dict[str, Any]:
        """Get current state."""
        return self.state.copy()

    def update_state(self, updates: Dict[str, Any]) -> None:
        """Update state from frontend."""
        self.state.update(updates)
        self.logger.info("state_updated", updates=list(updates.keys()))
```

### Step 4: Create FastAPI Endpoint

Create FastAPI endpoint that serves AG-UI protocol:

```python
# src/integrations/copilotkit/fastapi_endpoint.py

from typing import Any, Dict, Optional
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import structlog

from src.agents.base_agent import BaseAgent
from src.integrations.copilotkit.base_agent_wrapper import BaseAgentAGUIWrapper

logger = structlog.get_logger(__name__)


class CopilotKitEndpoint:
    """
    FastAPI endpoint for CopilotKit integration.

    Provides AG-UI protocol endpoint at /copilotkit.
    """

    def __init__(self, app: FastAPI):
        """
        Initialize endpoint.

        Args:
            app: FastAPI application instance
        """
        self.app = app
        self.agents: Dict[str, BaseAgent] = {}

        # Register routes
        self._register_routes()

    def _register_routes(self) -> None:
        """Register FastAPI routes."""

        @self.app.get("/copilotkit/info")
        async def get_info():
            """Get agent information."""
            return {
                "agents": [
                    {
                        "id": agent_id,
                        "name": agent.agent_id,
                        "tools": agent.allowed_tools,
                    }
                    for agent_id, agent in self.agents.items()
                ],
                "protocol": "ag-ui",
                "version": "1.0.0",
            }

        @self.app.post("/copilotkit")
        async def copilotkit_endpoint(request: Request):
            """
            Main CopilotKit endpoint.

            Accepts AG-UI requests and streams responses via SSE.
            """
            # Parse request
            body = await request.json()

            agent_id = body.get("agent_id")
            task = body.get("task")
            context = body.get("context", {})

            # Get agent
            agent = self.agents.get(agent_id)
            if not agent:
                return {"error": f"Agent {agent_id} not found"}

            # Create wrapper
            wrapper = BaseAgentAGUIWrapper(agent)

            # Stream events
            async def event_generator():
                async for event in wrapper.stream_query(task, context):
                    yield event.to_sse()

            return EventSourceResponse(event_generator())

    def register_agent(self, agent: BaseAgent, agent_id: Optional[str] = None) -> None:
        """
        Register a BaseAgent for CopilotKit access.

        Args:
            agent: BaseAgent instance
            agent_id: Optional custom agent ID (defaults to agent.agent_id)
        """
        agent_id = agent_id or agent.agent_id
        self.agents[agent_id] = agent

        logger.info(
            "agent_registered_for_copilotkit",
            agent_id=agent_id,
            tools=len(agent.allowed_tools),
        )


def add_copilotkit_endpoint(app: FastAPI, agents: list[BaseAgent]) -> CopilotKitEndpoint:
    """
    Helper function to add CopilotKit endpoint to FastAPI app.

    Args:
        app: FastAPI application
        agents: List of BaseAgent instances to expose

    Returns:
        CopilotKitEndpoint instance
    """
    endpoint = CopilotKitEndpoint(app)

    for agent in agents:
        endpoint.register_agent(agent)

    return endpoint
```

### Step 5: Frontend Integration

React component using CopilotKit:

```typescript
// frontend/src/components/ClaudeAgentChat.tsx

import { CopilotChat } from "@copilotkit/react-ui";
import { CopilotKitProvider, useCoAgent } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";

interface ClaudeAgentChatProps {
  agentId: string;
  runtimeUrl?: string;
}

export function ClaudeAgentChat({
  agentId,
  runtimeUrl = "http://localhost:8000/copilotkit"
}: ClaudeAgentChatProps) {
  return (
    <CopilotKitProvider runtimeUrl={runtimeUrl}>
      <AgentChatContent agentId={agentId} />
    </CopilotKitProvider>
  );
}

function AgentChatContent({ agentId }: { agentId: string }) {
  // Use CoAgent hook for state management
  const { state, setState } = useCoAgent({
    name: agentId,
    initialState: {
      messages: [],
      agent_id: agentId,
      session_id: null,
    },
  });

  return (
    <div className="claude-agent-chat">
      <h2>Claude Agent: {agentId}</h2>

      {/* CopilotKit Chat UI */}
      <CopilotChat
        labels={{
          title: "Chat with Claude Agent",
          placeholder: "Ask me anything about your accounts...",
        }}
        className="custom-chat"
      />

      {/* Display agent state */}
      <div className="agent-state">
        <h3>Agent State</h3>
        <pre>{JSON.stringify(state, null, 2)}</pre>
      </div>
    </div>
  );
}
```

---

## Code Examples

### Complete Backend Example

```python
# examples/copilotkit_integration.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.agents.base_agent import BaseAgent
from src.integrations.copilotkit.fastapi_endpoint import add_copilotkit_endpoint


# Define a custom agent
class AccountAnalysisAgent(BaseAgent):
    """Agent for analyzing Zoho CRM accounts."""

    async def execute(self, context):
        account_id = context.get("account_id")
        # Implementation...
        return {"status": "success", "account_id": account_id}


# Create FastAPI app
app = FastAPI(title="Claude Agent CopilotKit Integration")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create agent instance
account_agent = AccountAnalysisAgent(
    agent_id="account-analyzer",
    system_prompt="You are an expert at analyzing CRM account data.",
    allowed_tools=["zoho_get_account", "zoho_search_contacts"],
    permission_mode="default",
)

# Register with CopilotKit
copilot_endpoint = add_copilotkit_endpoint(
    app=app,
    agents=[account_agent],
)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "agents": len(copilot_endpoint.agents)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Running the Integration

```bash
# Terminal 1: Start FastAPI backend
python examples/copilotkit_integration.py

# Terminal 2: Start React frontend (in frontend/)
npm run dev
```

---

## State Synchronization

### State Flow Diagram

```
Frontend State (React)          Backend State (BaseAgent)
┌──────────────────┐            ┌──────────────────┐
│ messages: []     │◄──────────►│ messages: []     │
│ agent_id: "..."  │  AG-UI     │ agent_id: "..."  │
│ session_id: null │  Protocol  │ session_id: "X"  │
│ custom_data: {}  │            │ hooks_data: {}   │
└──────────────────┘            └──────────────────┘
         │                               │
         │ StateSnapshotEvent            │
         │◄──────────────────────────────┤
         │                               │
         │ User Input                    │
         ├──────────────────────────────►│
         │                               │
         │ TextChunkEvent                │
         │◄──────────────────────────────┤
         │                               │
         │ Final StateSnapshotEvent      │
         │◄──────────────────────────────┤
```

### State Synchronization Strategy

1. **Initial Sync**: Backend sends `StateSnapshotEvent` on session start
2. **Incremental Updates**: Backend emits `TextChunkEvent` for streaming content
3. **Tool Execution**: `ToolCallEvent` → `ToolResultEvent` cycle
4. **Final Sync**: Backend sends final `StateSnapshotEvent` on completion

### Hook Integration for State Updates

Map Claude SDK hooks to AG-UI state events:

```python
# src/integrations/copilotkit/hook_adapters.py

from typing import Any, Dict, Callable
import structlog

logger = structlog.get_logger(__name__)


class HookToAGUIAdapter:
    """
    Adapter that converts Claude SDK hooks to AG-UI state events.
    """

    def __init__(self, state_callback: Callable[[Dict[str, Any]], None]):
        """
        Initialize adapter.

        Args:
            state_callback: Callback to emit state updates
        """
        self.state_callback = state_callback
        self.logger = logger.bind(adapter="hook-to-agui")

    async def pre_tool_hook(self, context: Dict[str, Any]) -> None:
        """
        Pre-tool hook that emits AG-UI tool call event.
        """
        tool_name = context.get("tool_name")
        tool_input = context.get("tool_input", {})

        # Emit tool call via state callback
        self.state_callback({
            "event": "tool_call",
            "tool_name": tool_name,
            "tool_input": tool_input,
        })

        self.logger.info("pre_tool_hook_called", tool=tool_name)

    async def post_tool_hook(self, context: Dict[str, Any]) -> None:
        """
        Post-tool hook that emits AG-UI tool result event.
        """
        tool_call_id = context.get("tool_call_id")
        result = context.get("result")
        error = context.get("error")

        # Emit tool result via state callback
        self.state_callback({
            "event": "tool_result",
            "tool_call_id": tool_call_id,
            "result": result,
            "error": error,
        })

        self.logger.info("post_tool_hook_called", tool_call_id=tool_call_id)

    async def on_session_start(self, context: Dict[str, Any]) -> None:
        """
        Session start hook.
        """
        # Emit session start
        self.state_callback({
            "event": "session_start",
            "session_id": context.get("session_id"),
            "agent_id": context.get("agent_id"),
        })

    async def on_session_end(self, context: Dict[str, Any]) -> None:
        """
        Session end hook.
        """
        # Emit session end
        self.state_callback({
            "event": "session_end",
            "session_id": context.get("session_id"),
        })
```

---

## Compatibility Issues & Workarounds

### Issue 1: No Native LangGraph Support

**Problem**: CopilotKit expects `LangGraphAgent` with `StateGraph`, but we use `ClaudeSDKClient`.

**Workaround**:
- Use AG-UI Protocol instead of LangGraph integration
- Create custom AG-UI wrapper (see `BaseAgentAGUIWrapper`)

**Impact**: Medium - Requires additional wrapper code but provides more flexibility

---

### Issue 2: Streaming Format Mismatch

**Problem**: Claude SDK streams chunks in custom format; AG-UI expects specific event types.

**Workaround**:
- Translate Claude SDK chunks to AG-UI events in wrapper
- Map `{"type": "text", "content": "..."}` → `TextChunkEvent`
- Map `{"type": "tool_use", ...}` → `ToolCallEvent`

**Impact**: Low - Straightforward translation layer

---

### Issue 3: State Model Differences

**Problem**:
- Claude SDK has no built-in state model
- CopilotKit expects TypedDict with `messages` field

**Workaround**:
- Maintain state dictionary in wrapper
- Sync state via `StateSnapshotEvent`
- Store conversation history manually

**Impact**: Medium - Requires manual state management

---

### Issue 4: Tool Calling Protocol Mismatch

**Problem**:
- Claude SDK uses hooks for tool execution
- AG-UI uses declarative tool definitions

**Workaround**:
- Use hook adapter to translate tool calls to AG-UI events
- Emit `ToolCallEvent` in pre_tool hook
- Emit `ToolResultEvent` in post_tool hook

**Impact**: Low - Hooks already provide necessary interception points

---

### Issue 5: Session Management Alignment

**Problem**:
- Claude SDK uses `session_id` (string)
- CopilotKit uses `thread_id` for conversation threads

**Workaround**:
- Map `session_id` to AG-UI session events
- Emit `SessionStartEvent` and `SessionEndEvent`
- Store session mapping in wrapper

**Impact**: Low - Simple ID mapping

---

### Issue 6: Frontend State Persistence

**Problem**: CopilotKit expects persistent state across page reloads.

**Workaround**:
- Store session state in browser localStorage
- Restore state on component mount
- Sync with backend via state snapshot events

**Impact**: Medium - Requires frontend state persistence logic

**Example**:
```typescript
// frontend/src/hooks/usePersistedAgentState.ts

import { useState, useEffect } from 'react';

export function usePersistedAgentState(agentId: string) {
  const storageKey = `claude-agent-${agentId}`;

  const [state, setState] = useState(() => {
    const saved = localStorage.getItem(storageKey);
    return saved ? JSON.parse(saved) : {
      messages: [],
      agent_id: agentId,
      session_id: null,
    };
  });

  useEffect(() => {
    localStorage.setItem(storageKey, JSON.stringify(state));
  }, [state, storageKey]);

  return [state, setState];
}
```

---

### Issue 7: Error Boundary Handling

**Problem**: Claude SDK errors need to be surfaced in CopilotKit UI.

**Workaround**:
- Catch exceptions in wrapper
- Emit error events via AG-UI protocol
- Display errors in frontend with React error boundaries

**Example**:
```python
# In BaseAgentAGUIWrapper
try:
    async for chunk in self.agent.query(task, context):
        # Process chunks...
        pass
except Exception as e:
    # Emit error event
    yield ErrorEvent(
        error_type=type(e).__name__,
        error_message=str(e),
        session_id=self.agent.session_id,
    )
```

---

## Migration Path

### Phase 1: Proof of Concept (Week 1)

**Goals**:
- ✅ Research AG-UI protocol
- ✅ Create basic wrapper for single agent
- ✅ Test streaming with CopilotKit UI
- ✅ Document findings

**Deliverables**:
- This integration guide
- Basic wrapper implementation
- Example FastAPI endpoint

---

### Phase 2: Core Integration (Week 2-3)

**Goals**:
- Implement full AG-UI event system
- Create hook adapters
- Add state synchronization
- Build React components

**Deliverables**:
- Production-ready wrapper
- FastAPI endpoint with all features
- React component library
- Integration tests

---

### Phase 3: Advanced Features (Week 4-5)

**Goals**:
- Add tool execution visualization
- Implement state persistence
- Create error boundaries
- Add performance monitoring

**Deliverables**:
- Enhanced UI components
- Metrics dashboard
- Performance benchmarks
- User documentation

---

### Phase 4: Production Deployment (Week 6)

**Goals**:
- Deploy to production
- Monitor performance
- Gather user feedback
- Iterate based on usage

**Deliverables**:
- Production deployment
- Monitoring dashboards
- User training materials
- Post-deployment report

---

## Best Practices

### 1. Wrapper Design

✅ **DO**:
- Keep wrapper logic separate from BaseAgent
- Use composition over inheritance
- Implement clear interfaces

❌ **DON'T**:
- Modify BaseAgent core code
- Mix AG-UI logic with agent logic
- Create tight coupling

---

### 2. State Management

✅ **DO**:
- Emit state snapshots at key points
- Keep state minimal and focused
- Version state schema

❌ **DON'T**:
- Send full state on every update
- Store sensitive data in frontend state
- Break state schema compatibility

---

### 3. Error Handling

✅ **DO**:
- Catch and translate all errors
- Provide user-friendly error messages
- Log errors for debugging

❌ **DON'T**:
- Let exceptions crash the stream
- Expose internal error details
- Ignore error recovery

---

### 4. Performance Optimization

✅ **DO**:
- Stream responses incrementally
- Batch state updates when possible
- Monitor performance metrics

❌ **DON'T**:
- Buffer entire response before sending
- Emit too many state snapshots
- Ignore latency issues

---

### 5. Security Considerations

✅ **DO**:
- Validate all frontend inputs
- Use CORS properly
- Implement rate limiting
- Sanitize error messages

❌ **DON'T**:
- Trust frontend data blindly
- Expose API keys or secrets
- Allow unrestricted access

---

## Conclusion

### Summary

The integration of Claude Agent SDK with CopilotKit requires using the **AG-UI Protocol** as a bridge layer. While not natively supported, this approach provides:

1. **Framework Independence**: No tight coupling to LangGraph
2. **Flexibility**: Full control over agent behavior
3. **Compatibility**: Works with CopilotKit's React components
4. **Extensibility**: Easy to add features and customize

### Key Takeaways

- **No Direct Integration**: Claude SDK doesn't work with CopilotKit out-of-the-box
- **AG-UI Bridge**: Use AG-UI protocol for communication
- **Wrapper Pattern**: Wrap BaseAgent without modification
- **State Sync**: Manual state management required
- **Hook Adapters**: Translate hooks to AG-UI events

### Next Steps

1. ✅ Review this integration guide
2. Implement basic wrapper (Phase 1)
3. Test with single agent
4. Expand to multiple agents
5. Deploy to production

### Resources

- [CopilotKit Documentation](https://docs.copilotkit.ai/)
- [AG-UI Protocol Spec](https://docs.copilotkit.ai/coagents/ag-ui-protocol)
- [Claude Agent SDK Docs](https://docs.claude.com/en/api/agent-sdk/overview)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SSE Starlette](https://github.com/sysid/sse-starlette)

---

**Document Version**: 1.0.0
**Last Updated**: 2025-10-19
**Maintained By**: Sergas Engineering Team
