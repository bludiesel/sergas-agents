# CopilotKit UI with Custom Claude Agent SDK Backend Integration

**Research Date**: 2025-10-19
**Objective**: Evaluate using CopilotKit's React UI components as presentation layer only, with Claude Agent SDK handling backend orchestration
**Status**: ✅ FEASIBLE with AG-UI Protocol Bridge

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Key Research Questions Answered](#key-research-questions-answered)
3. [Architecture Overview](#architecture-overview)
4. [AG-UI Protocol: The Bridge](#ag-ui-protocol-the-bridge)
5. [Integration Strategy](#integration-strategy)
6. [Implementation Plan](#implementation-plan)
7. [Code Examples](#code-examples)
8. [Comparison: CopilotKit UI vs AG UI Protocol EventSource](#comparison)
9. [Pros and Cons](#pros-and-cons)
10. [Recommendations](#recommendations)
11. [Resources](#resources)

---

## Executive Summary

### ✅ **Answer: YES, CopilotKit UI can work with Claude Agent SDK backend**

**How**: Through the **AG-UI Protocol**, an open standard for agent-to-UI communication.

### Key Findings

1. **CopilotKit Runtime is OPTIONAL** - You can use CopilotKit's UI components standalone
2. **AG-UI Protocol is the KEY** - The bridge between any agent backend and CopilotKit frontend
3. **Claude Agent SDK + AG-UI = Full Compatibility** - No need for LangGraph/CrewAI/Mastra
4. **SSE (Server-Sent Events) is the Transport** - Simple HTTP streaming, no complex protocols
5. **Custom Backend Fully Supported** - As long as you emit AG-UI events, CopilotKit UI works

### Architecture Pattern

```
┌─────────────────────────────────────────────────────────────┐
│  CopilotKit React UI Components (Presentation Layer)       │
│  - <CopilotChat>, <CopilotSidebar>, <CopilotTextarea>     │
└─────────────────────────────────────────────────────────────┘
                           ↓
              AG-UI Protocol (SSE/EventSource)
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Backend (Bridge Layer)                             │
│  - Receives HTTP POST from frontend                         │
│  - Emits AG-UI events via SSE                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Claude Agent SDK (Orchestration Layer)                     │
│  - BaseAgent, Memory Analyst, Data Scout, etc.             │
│  - Tool execution, state management, hooks                  │
└─────────────────────────────────────────────────────────────┘
```

**CRITICAL**: CopilotKit UI is **ONLY** the presentation layer. Claude Agent SDK remains the orchestration engine.

---

## Key Research Questions Answered

### 1. Can CopilotKit UI work with a non-LangGraph backend?

**✅ YES** - CopilotKit supports custom backends through the AG-UI Protocol. LangGraph, CrewAI, and Mastra are just pre-built integrations, NOT requirements.

**Evidence**:
- AG-UI Protocol documentation explicitly states: "AG-UI is framework agnostic"
- Multiple examples of custom backends (Pydantic AI, Agno, ADK, AG2)
- CopilotKit v1.0 uses GraphQL protocol that can work with any backend emitting AG-UI events

### 2. What API contract must the backend satisfy?

**Answer**: Emit **AG-UI Protocol Events** via **SSE (Server-Sent Events)**

**Required Endpoints**:
```python
@app.post("/copilotkit")  # or any endpoint name
async def copilot_endpoint(input_data: RunAgentInput) -> StreamingResponse:
    """
    1. Accept POST with RunAgentInput (messages, state, threadId, runId)
    2. Return SSE stream with AG-UI events
    """
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

**Event Types** (16 total):
- **Lifecycle**: `RUN_STARTED`, `RUN_FINISHED`, `RUN_ERROR`, `STEP_STARTED`, `STEP_FINISHED`
- **Messages**: `TEXT_MESSAGE_START`, `TEXT_MESSAGE_CONTENT`, `TEXT_MESSAGE_END`
- **Tools**: `TOOL_CALL_START`, `TOOL_CALL_ARGS`, `TOOL_CALL_END`, `TOOL_CALL_RESULT`
- **State**: `STATE_SNAPSHOT`, `STATE_DELTA`, `MESSAGES_SNAPSHOT`
- **Special**: `RAW`, `CUSTOM`

### 3. Are there examples of CopilotKit UI + custom Python backend?

**✅ YES** - Multiple examples found:

1. **Pydantic AI + CopilotKit** - Official integration using AG-UI
2. **CrewAI + CopilotKit** - Custom backend, not using LangGraph
3. **Mastra + CopilotKit** - TypeScript agent framework with CopilotKit UI
4. **AG2 + CopilotKit** - Multi-agent framework integration
5. **Agno + CopilotKit** - AI orchestration framework

**Key Pattern**: All use AG-UI protocol as the bridge, none require CopilotKit's runtime or LangGraph.

### 4. Can we keep Claude Agent SDK and just add CopilotKit frontend?

**✅ ABSOLUTELY** - This is the RECOMMENDED approach.

**Strategy**:
1. Keep all Claude Agent SDK code unchanged (BaseAgent, Memory Analyst, Data Scout, etc.)
2. Create a thin FastAPI adapter layer that:
   - Receives requests from CopilotKit frontend
   - Calls Claude Agent SDK agents
   - Translates agent responses to AG-UI events
   - Streams events back to frontend via SSE

### 5. What's the minimum backend implementation needed?

**Minimal Requirements**:

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from ag_ui.core import RunAgentInput, EventEncoder, EventType
from ag_ui.core import RunStartedEvent, TextMessageContentEvent, RunFinishedEvent

app = FastAPI()

@app.post("/copilotkit")
async def agent_endpoint(input_data: RunAgentInput):
    async def event_generator():
        encoder = EventEncoder()

        # Start
        yield encoder.encode(RunStartedEvent(
            type=EventType.RUN_STARTED,
            thread_id=input_data.thread_id,
            run_id=input_data.run_id
        ))

        # Your Claude Agent SDK logic here
        result = await your_claude_agent.execute(input_data.messages)

        # Stream response
        yield encoder.encode(TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id="msg_1",
            delta=result
        ))

        # Finish
        yield encoder.encode(RunFinishedEvent(
            type=EventType.RUN_FINISHED,
            thread_id=input_data.thread_id,
            run_id=input_data.run_id
        ))

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

---

## Architecture Overview

### Three-Layer Architecture

#### Layer 1: CopilotKit React UI (Presentation)

```typescript
// Frontend - Next.js/React
import { CopilotChat } from "@copilotkit/react-core";
import { HttpAgent } from "@ag-ui/client";

const agent = new HttpAgent({
  url: "http://localhost:8000/copilotkit",
  headers: {
    Authorization: `Bearer ${token}`,
  },
});

function App() {
  return (
    <CopilotChat
      agent={agent}
      // CopilotKit UI handles all presentation
    />
  );
}
```

**What CopilotKit UI Provides**:
- Pre-built chat components (`<CopilotChat>`, `<CopilotSidebar>`)
- Message rendering with streaming support
- Tool call visualization
- State-driven UI updates
- Generative UI capabilities
- Responsive design

**What CopilotKit UI Does NOT Do**:
- ❌ Agent orchestration (that's your backend)
- ❌ Tool execution (that's your backend)
- ❌ Memory management (that's your backend)
- ❌ LLM calls (that's your backend)

#### Layer 2: FastAPI Bridge (AG-UI Adapter)

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from ag_ui.core import RunAgentInput, EventEncoder
from your_agents import ClaudeAgentOrchestrator

app = FastAPI()
orchestrator = ClaudeAgentOrchestrator()

@app.post("/copilotkit")
async def copilot_endpoint(input_data: RunAgentInput):
    """Bridge between CopilotKit UI and Claude Agent SDK"""

    async def event_generator():
        encoder = EventEncoder()

        # Emit AG-UI events as Claude agents execute
        async for event in orchestrator.stream_with_ag_ui_events(
            messages=input_data.messages,
            state=input_data.state,
            thread_id=input_data.thread_id,
            run_id=input_data.run_id
        ):
            yield encoder.encode(event)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

**Bridge Responsibilities**:
- ✅ Accept HTTP POST from frontend
- ✅ Parse `RunAgentInput` (messages, state, threadId, runId)
- ✅ Call Claude Agent SDK agents
- ✅ Translate agent outputs to AG-UI events
- ✅ Stream events via SSE

#### Layer 3: Claude Agent SDK (Orchestration)

```python
# Your existing code - NO CHANGES NEEDED
from src.agents.base_agent import BaseAgent
from src.agents.memory_analyst import MemoryAnalyst
from src.agents.zoho_data_scout import ZohoDataScout

class ClaudeAgentOrchestrator:
    def __init__(self):
        self.memory_analyst = MemoryAnalyst(...)
        self.data_scout = ZohoDataScout(...)

    async def stream_with_ag_ui_events(self, messages, state, thread_id, run_id):
        """Wrapper that emits AG-UI events while executing agents"""

        # Start
        yield RunStartedEvent(...)

        # Your existing orchestration logic
        memory_context = await self.memory_analyst.analyze(messages)
        data = await self.data_scout.fetch(state)

        # Stream results as TEXT_MESSAGE_CONTENT events
        for chunk in self.generate_response(memory_context, data):
            yield TextMessageContentEvent(
                message_id="msg_1",
                delta=chunk
            )

        # Finish
        yield RunFinishedEvent(...)
```

**Claude Agent SDK Responsibilities**:
- ✅ All agent orchestration (unchanged)
- ✅ Tool execution (unchanged)
- ✅ Memory management (unchanged)
- ✅ Zoho CRM integration (unchanged)
- ✅ Hook system (audit, metrics, permissions) (unchanged)

---

## AG-UI Protocol: The Bridge

### What is AG-UI?

**AG-UI (Agent-User Interaction Protocol)** is an open, lightweight, event-based protocol developed by CopilotKit in partnership with LangGraph and CrewAI. It defines a standard bridge between any AI agent backend and any UI frontend.

### Why AG-UI is Perfect for This Use Case

1. **Framework Agnostic** - Works with ANY agent framework (Claude SDK, LangGraph, CrewAI, custom)
2. **Simple Transport** - Uses standard HTTP + SSE (no WebSockets, no GraphQL complexity)
3. **Event-Based** - Structured event types for messages, tools, state
4. **Type-Safe** - Pydantic models in Python, TypeScript types in JS
5. **Battle-Tested** - Used by LangGraph, CrewAI, Pydantic AI, Mastra, AG2, and more
6. **CopilotKit Compatible** - CopilotKit UI is built to consume AG-UI events

### AG-UI Event Flow

```
Frontend (CopilotKit UI)
    ↓ POST /copilotkit
    ↓ { messages, state, threadId, runId }
Backend (FastAPI)
    ↓ Accepts RunAgentInput
    ↓ Calls Claude Agent SDK
    ↓ Emits AG-UI events via SSE
    ↓
    ├─ RUN_STARTED (lifecycle)
    ├─ TEXT_MESSAGE_START (message begins)
    ├─ TEXT_MESSAGE_CONTENT (streaming chunks)
    ├─ TOOL_CALL_START (agent calls tool)
    ├─ TOOL_CALL_RESULT (tool returns data)
    ├─ STATE_DELTA (update UI state)
    ├─ TEXT_MESSAGE_END (message complete)
    └─ RUN_FINISHED (agent done)
    ↓
Frontend (CopilotKit UI)
    ↓ Renders events in real-time
    ↓ Updates UI state
    ↓ Shows tool calls
    ↓ Streams message content
```

### Event Format (SSE)

```
data: {"type":"RUN_STARTED","threadId":"thread_123","runId":"run_456"}

data: {"type":"TEXT_MESSAGE_START","messageId":"msg_1","role":"assistant"}

data: {"type":"TEXT_MESSAGE_CONTENT","messageId":"msg_1","delta":"Hello "}

data: {"type":"TEXT_MESSAGE_CONTENT","messageId":"msg_1","delta":"world!"}

data: {"type":"TEXT_MESSAGE_END","messageId":"msg_1"}

data: {"type":"RUN_FINISHED","threadId":"thread_123","runId":"run_456"}

```

**Note**: Each event is prefixed with `data: ` (SSE format), followed by JSON.

---

## Integration Strategy

### Approach: Thin Adapter Layer

**Keep**: All Claude Agent SDK code (100% unchanged)
**Add**: FastAPI adapter that emits AG-UI events
**Replace**: Nothing (pure addition)

### Architecture Decision: AG-UI Protocol vs CopilotKit Runtime

| Aspect | AG-UI Protocol (Recommended) | CopilotKit Runtime |
|--------|------------------------------|-------------------|
| **Backend Control** | ✅ Full control (Claude SDK) | ❌ Runtime dictates flow |
| **Orchestration** | ✅ Claude Agent SDK | ❌ CopilotKit/LangGraph |
| **Flexibility** | ✅ Custom logic anywhere | ❌ Limited to runtime patterns |
| **Dependencies** | ✅ Minimal (`ag-ui-protocol`) | ❌ Heavy (`@copilotkit/runtime`) |
| **Learning Curve** | ✅ Simple (emit events) | ❌ Complex (runtime API) |
| **Future Proof** | ✅ Open standard | ⚠️ Vendor-specific |

**Verdict**: Use AG-UI Protocol, not CopilotKit Runtime.

### Why NOT Use CopilotKit Runtime?

CopilotKit Runtime (`@copilotkit/runtime`) is designed for:
- **Node.js backends** (we use Python/FastAPI)
- **LangGraph workflows** (we use Claude Agent SDK)
- **GraphQL protocol** (complex, unnecessary)
- **Remote endpoint proxying** (adds latency)

**We don't need it** - AG-UI Protocol gives us everything we need with less complexity.

---

## Implementation Plan

### Phase 1: Setup AG-UI Protocol Backend (Week 1)

#### 1.1 Install Dependencies

```bash
pip install ag-ui-protocol fastapi uvicorn pydantic
```

#### 1.2 Create AG-UI Event Emitter

**File**: `/Users/mohammadabdelrahman/Projects/sergas_agents/src/adapters/ag_ui_emitter.py`

```python
"""AG-UI event emitter for Claude Agent SDK integration."""

from typing import AsyncGenerator, Dict, Any
from ag_ui.core import (
    EventType,
    RunStartedEvent,
    RunFinishedEvent,
    RunErrorEvent,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    ToolCallStartEvent,
    ToolCallResultEvent,
    StateDeltaEvent,
)
from ag_ui.encoder import EventEncoder
import uuid


class AGUIEmitter:
    """Emits AG-UI protocol events from Claude Agent SDK agents."""

    def __init__(self):
        self.encoder = EventEncoder()

    async def emit_agent_stream(
        self,
        agent_executor,
        messages: list,
        state: Dict[str, Any],
        thread_id: str,
        run_id: str,
    ) -> AsyncGenerator[str, None]:
        """Execute agent and emit AG-UI events.

        Args:
            agent_executor: Claude Agent SDK agent instance
            messages: Conversation history
            state: Current application state
            thread_id: Thread identifier
            run_id: Run identifier

        Yields:
            SSE-formatted AG-UI event strings
        """
        try:
            # Start run
            yield self.encoder.encode(RunStartedEvent(
                type=EventType.RUN_STARTED,
                thread_id=thread_id,
                run_id=run_id
            ))

            # Start message
            message_id = f"msg_{uuid.uuid4().hex[:8]}"
            yield self.encoder.encode(TextMessageStartEvent(
                type=EventType.TEXT_MESSAGE_START,
                message_id=message_id,
                role="assistant"
            ))

            # Execute agent (streaming)
            async for chunk in agent_executor.stream_execute(
                messages=messages,
                state=state
            ):
                if chunk["type"] == "text":
                    # Stream text content
                    yield self.encoder.encode(TextMessageContentEvent(
                        type=EventType.TEXT_MESSAGE_CONTENT,
                        message_id=message_id,
                        delta=chunk["content"]
                    ))

                elif chunk["type"] == "tool_call":
                    # Tool invocation
                    tool_call_id = chunk["tool_call_id"]
                    yield self.encoder.encode(ToolCallStartEvent(
                        type=EventType.TOOL_CALL_START,
                        tool_call_id=tool_call_id,
                        tool_call_name=chunk["tool_name"],
                        parent_message_id=message_id
                    ))

                    # Tool result
                    yield self.encoder.encode(ToolCallResultEvent(
                        type=EventType.TOOL_CALL_RESULT,
                        tool_call_id=tool_call_id,
                        result=chunk["result"]
                    ))

                elif chunk["type"] == "state_update":
                    # State change
                    yield self.encoder.encode(StateDeltaEvent(
                        type=EventType.STATE_DELTA,
                        delta=chunk["delta"]
                    ))

            # End message
            yield self.encoder.encode(TextMessageEndEvent(
                type=EventType.TEXT_MESSAGE_END,
                message_id=message_id
            ))

            # Finish run
            yield self.encoder.encode(RunFinishedEvent(
                type=EventType.RUN_FINISHED,
                thread_id=thread_id,
                run_id=run_id
            ))

        except Exception as e:
            # Error handling
            yield self.encoder.encode(RunErrorEvent(
                type=EventType.RUN_ERROR,
                thread_id=thread_id,
                run_id=run_id,
                error={
                    "message": str(e),
                    "code": "AGENT_ERROR"
                }
            ))
```

#### 1.3 Create FastAPI Endpoint

**File**: `/Users/mohammadabdelrahman/Projects/sergas_agents/src/api/copilotkit_endpoint.py`

```python
"""CopilotKit-compatible endpoint using AG-UI protocol."""

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from ag_ui.core import RunAgentInput
from src.adapters.ag_ui_emitter import AGUIEmitter
from src.agents.orchestrator import AgentOrchestrator
import structlog

logger = structlog.get_logger(__name__)
app = FastAPI(title="Sergas Agents - CopilotKit Bridge")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
ag_ui_emitter = AGUIEmitter()
orchestrator = AgentOrchestrator()


@app.post("/copilotkit")
async def copilotkit_endpoint(
    input_data: RunAgentInput,
    authorization: str = Header(None)
) -> StreamingResponse:
    """AG-UI protocol endpoint for CopilotKit frontend.

    Accepts RunAgentInput and streams AG-UI events via SSE.
    """
    # Authentication
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.info(
        "copilotkit_request",
        thread_id=input_data.thread_id,
        run_id=input_data.run_id,
        message_count=len(input_data.messages)
    )

    # Stream AG-UI events
    return StreamingResponse(
        ag_ui_emitter.emit_agent_stream(
            agent_executor=orchestrator,
            messages=input_data.messages,
            state=input_data.state or {},
            thread_id=input_data.thread_id,
            run_id=input_data.run_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "copilotkit-bridge"}
```

#### 1.4 Update BaseAgent for Streaming

**Modify**: `/Users/mohammadabdelrahman/Projects/sergas_agents/src/agents/base_agent.py`

```python
# Add streaming support to BaseAgent
async def stream_execute(
    self,
    messages: list,
    state: Dict[str, Any]
) -> AsyncGenerator[Dict[str, Any], None]:
    """Execute agent with streaming output.

    Yields:
        Chunks of type: "text", "tool_call", "state_update"
    """
    # Your existing execute logic, but yield chunks
    result = await self.execute({"messages": messages, "state": state})

    # For now, yield complete result as single chunk
    # TODO: Implement true streaming from Claude SDK
    yield {
        "type": "text",
        "content": result.get("response", "")
    }
```

### Phase 2: Frontend Setup (Week 2)

#### 2.1 Install CopilotKit Frontend

```bash
npm install @copilotkit/react-core @copilotkit/react-ui @ag-ui/client
```

#### 2.2 Create CopilotKit App

**File**: `frontend/app/page.tsx`

```typescript
"use client";

import { CopilotChat } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { HttpAgent } from "@ag-ui/client";

// Create agent client pointing to our FastAPI backend
const agent = new HttpAgent({
  url: "http://localhost:8000/copilotkit",
  headers: {
    Authorization: `Bearer ${process.env.NEXT_PUBLIC_API_TOKEN}`,
  },
});

export default function Home() {
  return (
    <CopilotSidebar
      agent={agent}
      title="Sergas Account Assistant"
      placeholder="Ask about account health, risks, or recommendations..."
    >
      <div className="p-8">
        <h1 className="text-2xl font-bold">Account Executive Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Your AI assistant is ready to help with account analysis,
          risk detection, and recommendations.
        </p>
      </div>
    </CopilotSidebar>
  );
}
```

#### 2.3 Configure Next.js

**File**: `frontend/next.config.js`

```javascript
module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ];
  },
};
```

### Phase 3: Testing & Validation (Week 3)

#### 3.1 Backend Testing

```python
# tests/integration/test_copilotkit_endpoint.py
import pytest
from fastapi.testclient import TestClient
from src.api.copilotkit_endpoint import app

client = TestClient(app)

def test_copilotkit_endpoint_sse():
    """Test AG-UI SSE stream from endpoint."""
    response = client.post(
        "/copilotkit",
        json={
            "threadId": "test_thread",
            "runId": "test_run",
            "messages": [
                {"role": "user", "content": "What are my at-risk accounts?"}
            ],
            "state": {}
        },
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"

    # Parse SSE events
    events = []
    for line in response.iter_lines():
        if line.startswith(b"data: "):
            events.append(json.loads(line[6:]))

    # Verify event sequence
    assert events[0]["type"] == "RUN_STARTED"
    assert events[-1]["type"] == "RUN_FINISHED"
```

#### 3.2 Frontend Testing

```typescript
// frontend/tests/copilotkit.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { HttpAgent } from '@ag-ui/client';
import { CopilotChat } from '@copilotkit/react-core';

test('CopilotChat renders and connects to backend', async () => {
  const agent = new HttpAgent({
    url: 'http://localhost:8000/copilotkit',
  });

  render(<CopilotChat agent={agent} />);

  await waitFor(() => {
    expect(screen.getByPlaceholderText(/type a message/i)).toBeInTheDocument();
  });
});
```

### Phase 4: Production Deployment (Week 4)

#### 4.1 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ZOHO_CLIENT_ID=${ZOHO_CLIENT_ID}
      - ZOHO_CLIENT_SECRET=${ZOHO_CLIENT_SECRET}

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
```

#### 4.2 Production Checklist

- [ ] Enable HTTPS/TLS
- [ ] Add authentication middleware
- [ ] Configure CORS properly
- [ ] Add rate limiting
- [ ] Setup logging/monitoring
- [ ] Configure SSE timeout (5-10 minutes)
- [ ] Add error boundaries in frontend
- [ ] Implement reconnection logic
- [ ] Add health checks

---

## Code Examples

### Example 1: Memory Analyst Integration

```python
from src.agents.memory_analyst import MemoryAnalyst
from src.adapters.ag_ui_emitter import AGUIEmitter

class MemoryAnalystAGUIAdapter:
    """Adapter for Memory Analyst with AG-UI events."""

    def __init__(self):
        self.analyst = MemoryAnalyst(...)
        self.emitter = AGUIEmitter()

    async def stream_analysis(self, account_id: str, thread_id: str, run_id: str):
        """Analyze account and emit AG-UI events."""

        async for event in self.emitter.emit_agent_stream(
            agent_executor=self.analyst,
            messages=[{"role": "system", "content": f"Analyze account {account_id}"}],
            state={"account_id": account_id},
            thread_id=thread_id,
            run_id=run_id
        ):
            yield event
```

### Example 2: Tool Call with AG-UI Events

```python
async def execute_with_tool_calls(self, messages, state, thread_id, run_id):
    """Execute agent with tool call events."""

    yield RunStartedEvent(...)

    # Simulate tool call
    tool_call_id = "tc_zoho_fetch"

    yield ToolCallStartEvent(
        type=EventType.TOOL_CALL_START,
        tool_call_id=tool_call_id,
        tool_call_name="fetch_zoho_accounts"
    )

    # Execute tool
    accounts = await self.zoho_client.fetch_accounts()

    yield ToolCallResultEvent(
        type=EventType.TOOL_CALL_RESULT,
        tool_call_id=tool_call_id,
        result=accounts
    )

    yield RunFinishedEvent(...)
```

### Example 3: State-Driven UI Updates

```python
async def stream_with_state_updates(self, messages, state, thread_id, run_id):
    """Emit state updates for UI progress tracking."""

    yield StateSnapshotEvent(
        type=EventType.STATE_SNAPSHOT,
        state={
            "step": "analyzing",
            "progress": 0,
            "accounts_processed": 0
        }
    )

    for i, account in enumerate(accounts):
        # Process account
        analysis = await self.analyze(account)

        # Update progress
        yield StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta={
                "progress": int((i + 1) / len(accounts) * 100),
                "accounts_processed": i + 1
            }
        )

    yield StateDeltaEvent(
        type=EventType.STATE_DELTA,
        delta={"step": "complete"}
    )
```

---

## Comparison: CopilotKit UI vs AG UI Protocol EventSource

### Option A: CopilotKit UI + AG-UI Backend (RECOMMENDED)

**Architecture**:
```
React (CopilotKit Components) → AG-UI SSE → FastAPI → Claude SDK
```

**Pros**:
- ✅ Beautiful pre-built UI components
- ✅ Generative UI capabilities
- ✅ Tool call visualization out-of-the-box
- ✅ Responsive design included
- ✅ TypeScript support
- ✅ Active community and updates
- ✅ Rich developer experience

**Cons**:
- ❌ Dependency on CopilotKit library (~100KB)
- ❌ Learning curve for CopilotKit components
- ⚠️ Vendor lock-in (mild - can switch to raw AG-UI later)

**Best For**:
- Teams that want polished UI fast
- Projects with limited frontend resources
- Applications needing generative UI
- Rapid prototyping

### Option B: Custom React + AG UI Protocol EventSource

**Architecture**:
```
React (Custom Components) → AG-UI SSE → FastAPI → Claude SDK
```

**Pros**:
- ✅ Full UI control
- ✅ Zero vendor lock-in
- ✅ Minimal dependencies
- ✅ Easier to customize deeply
- ✅ Learn standard web APIs (EventSource)

**Cons**:
- ❌ Must build all UI components yourself
- ❌ No generative UI out-of-the-box
- ❌ More frontend development time
- ❌ Need to handle edge cases manually

**Best For**:
- Teams with strong frontend capabilities
- Projects with specific design requirements
- Applications where bundle size matters
- Long-term maintainability focus

### Side-by-Side Code Comparison

#### Option A: CopilotKit UI

```typescript
import { CopilotChat } from "@copilotkit/react-core";
import { HttpAgent } from "@ag-ui/client";

const agent = new HttpAgent({ url: "/copilotkit" });

export default function Chat() {
  return <CopilotChat agent={agent} />;
  // That's it! Streaming, tool calls, state - all handled
}
```

#### Option B: Custom EventSource

```typescript
import { useEffect, useState } from 'react';

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');

  async function sendMessage(text) {
    const response = await fetch('/copilotkit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        threadId: 'thread_1',
        runId: crypto.randomUUID(),
        messages: [{ role: 'user', content: text }]
      })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const event = JSON.parse(line.slice(6));

          switch (event.type) {
            case 'TEXT_MESSAGE_CONTENT':
              setCurrentMessage(prev => prev + event.delta);
              break;
            case 'TEXT_MESSAGE_END':
              setMessages(prev => [...prev, currentMessage]);
              setCurrentMessage('');
              break;
            // Handle other event types...
          }
        }
      }
    }
  }

  return (
    <div>
      {/* Build your own UI */}
      <div className="messages">
        {messages.map((msg, i) => <div key={i}>{msg}</div>)}
        {currentMessage && <div>{currentMessage}</div>}
      </div>
      <input onSubmit={(e) => sendMessage(e.target.value)} />
    </div>
  );
}
```

### Recommendation Matrix

| Criteria | CopilotKit UI | Custom EventSource |
|----------|---------------|-------------------|
| **Development Speed** | ⭐⭐⭐⭐⭐ (1-2 days) | ⭐⭐⭐ (1-2 weeks) |
| **UI Polish** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ (depends on effort) |
| **Customization** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Bundle Size** | ⭐⭐⭐ (~100KB) | ⭐⭐⭐⭐⭐ (~5KB) |
| **Maintainability** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Learning Curve** | ⭐⭐⭐⭐ | ⭐⭐⭐ |

**Final Verdict**: **Use CopilotKit UI** unless you have specific reasons to build custom (e.g., extreme customization needs, bundle size constraints).

---

## Pros and Cons

### Pros of CopilotKit UI + Claude Agent SDK

1. **✅ Best of Both Worlds**
   - Modern React UI (CopilotKit)
   - Powerful orchestration (Claude SDK)
   - No compromise needed

2. **✅ Separation of Concerns**
   - Frontend: CopilotKit handles presentation
   - Backend: Claude SDK handles logic
   - Clean architecture

3. **✅ Keep Existing Code**
   - Zero changes to BaseAgent, Memory Analyst, Data Scout
   - Only add adapter layer
   - Preserves all investments in Claude SDK

4. **✅ Production-Ready UI**
   - Pre-built components
   - Accessibility built-in
   - Mobile responsive
   - Dark mode support

5. **✅ Future-Proof**
   - AG-UI is an open standard
   - Can switch frontends easily
   - Not locked into CopilotKit runtime

6. **✅ Developer Experience**
   - TypeScript throughout
   - Excellent documentation
   - Active community

### Cons of CopilotKit UI + Claude Agent SDK

1. **❌ Additional Dependencies**
   - AG-UI protocol library
   - CopilotKit React components
   - +~100KB bundle size

2. **⚠️ Learning Curve**
   - Need to understand AG-UI events
   - CopilotKit component API
   - SSE streaming patterns

3. **⚠️ Two Frameworks**
   - CopilotKit for frontend
   - Claude SDK for backend
   - More mental overhead

4. **❌ Adapter Layer Complexity**
   - Must translate between Claude SDK and AG-UI
   - Additional testing surface
   - One more layer to debug

5. **⚠️ SSE Limitations**
   - Unidirectional (server → client)
   - If you need bidirectional, requires WebSocket upgrade
   - Browser EventSource has some quirks

### Mitigation Strategies

1. **Bundle Size Concern** → Use code splitting, lazy load CopilotKit UI
2. **Learning Curve** → Start with simple events, expand gradually
3. **Adapter Complexity** → Use provided examples, write comprehensive tests
4. **Bidirectional Needs** → AG-UI supports WebSocket if needed later

---

## Recommendations

### Recommended Approach: **CopilotKit UI + AG-UI Protocol + Claude Agent SDK**

**Why**:
1. **Fastest Time-to-Market** - Pre-built UI saves 2-4 weeks of frontend work
2. **Professional UI** - CopilotKit components are polished and accessible
3. **Backend Control** - Keep 100% control with Claude Agent SDK
4. **Open Standard** - AG-UI ensures you're not locked in
5. **Scalable** - Can handle complex multi-agent scenarios

### Architecture Diagram

```
┌────────────────────────────────────────────────────────────┐
│  Frontend (Next.js)                                        │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  CopilotKit React Components                         │ │
│  │  - <CopilotChat>, <CopilotSidebar>                  │ │
│  │  - Built-in streaming, tool visualization           │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
                          ↓ HTTP POST
                          ↓ SSE Stream (AG-UI Events)
┌────────────────────────────────────────────────────────────┐
│  Backend (FastAPI)                                         │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  AG-UI Adapter Layer                                 │ │
│  │  - Receives RunAgentInput                           │ │
│  │  - Emits AG-UI events via SSE                       │ │
│  │  - Bridges CopilotKit UI ↔ Claude SDK              │ │
│  └──────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Claude Agent SDK (Unchanged)                        │ │
│  │  - BaseAgent, Memory Analyst, Data Scout            │ │
│  │  - Zoho CRM integration                             │ │
│  │  - Hook system (audit, metrics, permissions)        │ │
│  │  - All existing orchestration logic                 │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### Implementation Priority

1. **Phase 1 (Week 1)**: Backend AG-UI adapter
   - Install `ag-ui-protocol`
   - Create `AGUIEmitter` class
   - Build FastAPI `/copilotkit` endpoint
   - Add streaming to `BaseAgent`

2. **Phase 2 (Week 2)**: Frontend setup
   - Install CopilotKit packages
   - Create basic chat interface
   - Test SSE connection
   - Implement message rendering

3. **Phase 3 (Week 3)**: Advanced features
   - Tool call visualization
   - State-driven UI updates
   - Multi-agent coordination
   - Error handling

4. **Phase 4 (Week 4)**: Production hardening
   - Authentication
   - Rate limiting
   - Logging/monitoring
   - Performance optimization

### Success Metrics

- [ ] SSE stream establishes in <100ms
- [ ] Messages render in real-time (<50ms latency)
- [ ] Tool calls visualized correctly
- [ ] State updates reflected in UI
- [ ] Error states handled gracefully
- [ ] Works on mobile devices
- [ ] Supports reconnection after network issues

---

## Resources

### Official Documentation

- **AG-UI Protocol**: https://docs.ag-ui.com
- **CopilotKit**: https://docs.copilotkit.ai
- **Claude Agent SDK**: https://docs.anthropic.com/en/api/agent-sdk

### Code Repositories

- **AG-UI Protocol**: https://github.com/ag-ui-protocol/ag-ui
- **CopilotKit**: https://github.com/CopilotKit/CopilotKit
- **AG-UI Python Client**: https://pypi.org/project/ag-ui-protocol/

### Examples & Tutorials

- **Pydantic AI + AG-UI**: https://ai.pydantic.dev/ag-ui/
- **CrewAI + CopilotKit**: https://www.copilotkit.ai/blog/how-to-add-a-frontend-to-any-crewai-agent-using-ag-ui-protocol
- **LangGraph + AG-UI**: https://www.copilotkit.ai/blog/how-to-add-a-frontend-to-any-langgraph-agent-using-ag-ui-protocol
- **Mastra + CopilotKit**: https://mastra.ai/en/docs/frameworks/agentic-uis/copilotkit

### Technical Articles

- **Introducing AG-UI Protocol**: https://www.copilotkit.ai/blog/introducing-ag-ui-the-protocol-where-agents-meet-users
- **AG-UI Protocol Guide**: https://zediot.com/blog/ag-ui-protocol/
- **CopilotKit v1.0 Launch**: https://www.copilotkit.ai/blog/copilotkit-v1-launch

### Python Packages

```bash
pip install ag-ui-protocol  # Core protocol
pip install fastapi uvicorn  # Web server
pip install pydantic  # Type safety
```

### TypeScript Packages

```bash
npm install @copilotkit/react-core  # Core components
npm install @copilotkit/react-ui    # UI components
npm install @ag-ui/client           # AG-UI client
```

---

## Appendix: Event Schemas

### RunAgentInput Schema

```python
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class Message(BaseModel):
    role: str  # 'user', 'assistant', 'system'
    content: str

class RunAgentInput(BaseModel):
    thread_id: str
    run_id: str
    messages: List[Message]
    state: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
```

### AG-UI Event Types (Complete List)

```python
# Lifecycle
RUN_STARTED
RUN_FINISHED
RUN_ERROR
STEP_STARTED
STEP_FINISHED

# Messages
TEXT_MESSAGE_START
TEXT_MESSAGE_CONTENT
TEXT_MESSAGE_END

# Tools
TOOL_CALL_START
TOOL_CALL_ARGS
TOOL_CALL_END
TOOL_CALL_RESULT

# State
STATE_SNAPSHOT
STATE_DELTA
MESSAGES_SNAPSHOT

# Special
RAW
CUSTOM
```

### SSE Response Format

```
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"type":"RUN_STARTED","threadId":"thread_123","runId":"run_456"}

data: {"type":"TEXT_MESSAGE_START","messageId":"msg_1","role":"assistant"}

data: {"type":"TEXT_MESSAGE_CONTENT","messageId":"msg_1","delta":"Hello"}

data: {"type":"TEXT_MESSAGE_END","messageId":"msg_1"}

data: {"type":"RUN_FINISHED","threadId":"thread_123","runId":"run_456"}

```

---

## Conclusion

**CopilotKit UI with Claude Agent SDK backend is HIGHLY FEASIBLE and RECOMMENDED.**

The AG-UI Protocol provides a clean, standardized bridge between the two systems:
- **Frontend**: CopilotKit handles all presentation beautifully
- **Backend**: Claude Agent SDK continues to orchestrate everything
- **Bridge**: Thin FastAPI adapter emits AG-UI events

This architecture gives you:
- ✅ Professional UI without building from scratch
- ✅ Full control over backend logic and orchestration
- ✅ Open standards (not vendor lock-in)
- ✅ Minimal changes to existing code
- ✅ Production-ready solution

**Next Steps**:
1. Review this document with team
2. Decide: CopilotKit UI vs Custom EventSource (recommend CopilotKit)
3. Start Phase 1: Backend AG-UI adapter (1 week)
4. Prototype basic chat interface (3-5 days)
5. Validate with stakeholders
6. Expand to full feature set

---

**Document Version**: 1.0
**Research Date**: 2025-10-19
**Author**: Research Agent
**Status**: ✅ Complete
**Decision**: Ready for Implementation
