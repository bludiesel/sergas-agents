# AG-UI Protocol Technical Specification

**Research Date**: 2025-10-19
**Protocol Version**: Latest (as of October 2025)
**Repository**: https://github.com/ag-ui-protocol/ag-ui
**Official Documentation**: https://docs.ag-ui.com

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Core Protocol Specification](#core-protocol-specification)
3. [Complete Event Reference](#complete-event-reference)
4. [API Reference](#api-reference)
5. [Authentication & Security](#authentication--security)
6. [Integration Patterns](#integration-patterns)
7. [Python Implementation](#python-implementation)
8. [FastAPI Integration](#fastapi-integration)
9. [TypeScript SDK](#typescript-sdk)
10. [Dependencies & Requirements](#dependencies--requirements)
11. [Best Practices](#best-practices)
12. [Error Handling & Retry Strategies](#error-handling--retry-strategies)
13. [Code Examples](#code-examples)
14. [Resources & References](#resources--references)

---

## Executive Summary

**AG-UI (Agent-User Interaction Protocol)** is an open, lightweight, event-based protocol developed by CopilotKit in partnership with LangGraph and CrewAI. It standardizes how AI agents communicate with frontend applications through streaming JSON events over HTTP/SSE or WebSocket.

### Key Features
- **16 Standardized Event Types** - Comprehensive coverage of agent interactions
- **Real-Time Streaming** - SSE/WebSocket support for live updates
- **Framework Agnostic** - Works with OpenAI, LangGraph, CrewAI, Pydantic AI, and more
- **Bidirectional Communication** - Supports both agent → UI and UI → agent flows
- **State Management** - Built-in state synchronization between frontend and backend
- **Tool Call Support** - Structured tool invocation and result handling
- **Type Safety** - Pydantic-based validation for Python, TypeScript definitions for JS

### Use Cases
- Agentic chat interfaces
- Real-time agent status updates
- Tool call visualization
- State-driven UI updates
- Multi-agent collaboration interfaces
- Human-in-the-loop workflows

---

## Core Protocol Specification

### Protocol Architecture

AG-UI uses a **single HTTP POST request** followed by a **persistent streaming connection** (SSE or WebSocket) to deliver events from the agent to the frontend.

```
┌─────────────┐                    ┌──────────────┐
│             │  HTTP POST         │              │
│  Frontend   │─────────────────>  │  Agent API   │
│  (Client)   │                    │  (Server)    │
│             │  SSE/WebSocket     │              │
│             │<─────────────────  │              │
└─────────────┘    Event Stream    └──────────────┘
```

### Communication Flow

1. **Request Phase**: Client sends HTTP POST with user input and context
2. **Connection Phase**: Server establishes SSE or WebSocket stream
3. **Streaming Phase**: Agent emits events as they occur
4. **Completion Phase**: RunFinished or RunError event closes the stream

### Transport Layers

#### Server-Sent Events (SSE) - Recommended
- **Protocol**: HTTP/HTTPS
- **Direction**: Unidirectional (Server → Client)
- **Advantages**:
  - Works through standard infrastructure (firewalls, proxies, CDNs)
  - Automatic reconnection handling by browser
  - Simpler to implement
  - Native browser support via EventSource API
- **Use Case**: 99% of AG-UI implementations

#### WebSocket - Optional
- **Protocol**: WS/WSS
- **Direction**: Bidirectional
- **Advantages**:
  - Full-duplex communication
  - Lower latency
  - More control over connection lifecycle
- **Use Case**: High-frequency bidirectional updates

### Message Format

All events follow a standard JSON structure:

```typescript
interface BaseEvent {
  type: EventType;
  // Event-specific fields
}
```

Events are serialized with **camelCase** field names for JavaScript/TypeScript compatibility.

---

## Complete Event Reference

AG-UI defines **16 standardized event types** across 5 categories:

### 1. Lifecycle Events (Mandatory)

#### RunStarted
```typescript
interface RunStartedEvent {
  type: EventType.RUN_STARTED;
  threadId: string;
  runId: string;
}
```
- **When**: First event emitted when agent begins processing
- **Purpose**: Establishes execution context with unique runId
- **Required**: Yes

#### RunFinished
```typescript
interface RunFinishedEvent {
  type: EventType.RUN_FINISHED;
  threadId: string;
  runId: string;
}
```
- **When**: Agent successfully completes all work
- **Purpose**: Signals successful completion
- **Required**: Yes (or RunError)

#### RunError
```typescript
interface RunErrorEvent {
  type: EventType.RUN_ERROR;
  threadId: string;
  runId: string;
  error: {
    message: string;
    code?: string;
    details?: any;
  };
}
```
- **When**: Agent encounters unrecoverable error
- **Purpose**: Signals failure and provides error context
- **Required**: Yes (if RunFinished not emitted)

#### StepStarted / StepFinished (Optional)
```typescript
interface StepStartedEvent {
  type: EventType.STEP_STARTED;
  stepId: string;
  stepName?: string;
  parentMessageId?: string;
}

interface StepFinishedEvent {
  type: EventType.STEP_FINISHED;
  stepId: string;
}
```
- **When**: During multi-step agent processes
- **Purpose**: Track granular progress within a run
- **Required**: No (optional for structured workflows)

### 2. Text Message Events

#### TextMessageStart
```typescript
interface TextMessageStartEvent {
  type: EventType.TEXT_MESSAGE_START;
  messageId: string;
  role: string; // 'assistant', 'user', 'system'
}
```
- **When**: Agent begins generating a text response
- **Purpose**: Initialize message container with ID

#### TextMessageContent
```typescript
interface TextMessageContentEvent {
  type: EventType.TEXT_MESSAGE_CONTENT;
  messageId: string;
  delta: string; // Text chunk to append
}
```
- **When**: Each chunk of streaming text is generated
- **Purpose**: Stream text incrementally for real-time display
- **Pattern**: Can be emitted multiple times per message

#### TextMessageEnd
```typescript
interface TextMessageEndEvent {
  type: EventType.TEXT_MESSAGE_END;
  messageId: string;
}
```
- **When**: Message generation completes
- **Purpose**: Signal message finalization

### 3. Tool Call Events

Tool calls follow a **streaming pattern**: START → ARGS (multiple) → END

#### ToolCallStart
```typescript
interface ToolCallStartEvent {
  type: EventType.TOOL_CALL_START;
  toolCallId: string;
  toolCallName: string;
  parentMessageId?: string;
}
```
- **When**: Agent decides to invoke a tool
- **Purpose**: Initialize tool call with unique ID and name

#### ToolCallArgs
```typescript
interface ToolCallArgsEvent {
  type: EventType.TOOL_CALL_ARGS;
  toolCallId: string;
  argsJson: string; // JSON string of partial/complete arguments
}
```
- **When**: Tool arguments are generated (streaming)
- **Purpose**: Stream tool arguments as they're constructed
- **Pattern**: Multiple events may be emitted for complex arguments

#### ToolCallEnd
```typescript
interface ToolCallEndEvent {
  type: EventType.TOOL_CALL_END;
  toolCallId: string;
}
```
- **When**: Tool invocation completes
- **Purpose**: Signal end of tool call definition

#### ToolCallResult
```typescript
interface ToolCallResultEvent {
  type: EventType.TOOL_CALL_RESULT;
  toolCallId: string;
  result: any; // Tool execution result
  error?: {
    message: string;
    code?: string;
  };
}
```
- **When**: Tool execution completes (success or failure)
- **Purpose**: Deliver tool output back to UI

### 4. State Management Events

#### StateSnapshot
```typescript
interface StateSnapshotEvent {
  type: EventType.STATE_SNAPSHOT;
  state: Record<string, any>; // Complete state object
}
```
- **When**: Full state needs to be synchronized
- **Purpose**: Initialize or reset UI state to match agent state

#### StateDelta
```typescript
interface StateDeltaEvent {
  type: EventType.STATE_DELTA;
  delta: Record<string, any>; // Partial state update
}
```
- **When**: Incremental state changes occur
- **Purpose**: Update specific state fields without full replacement

#### MessagesSnapshot
```typescript
interface MessagesSnapshotEvent {
  type: EventType.MESSAGES_SNAPSHOT;
  messages: Array<{
    messageId: string;
    role: string;
    content: string;
    toolCalls?: any[];
  }>;
}
```
- **When**: Complete message history needed
- **Purpose**: Provide full conversation context

### 5. Special Events

#### Raw Event
```typescript
interface RawEvent {
  type: EventType.RAW;
  source: string; // External system identifier
  data: any; // Original event data
}
```
- **When**: Events from external systems need passthrough
- **Purpose**: Container for non-AG-UI events

#### Custom Event
```typescript
interface CustomEvent {
  type: EventType.CUSTOM;
  name: string;
  data: any;
}
```
- **When**: Application-specific events needed
- **Purpose**: Extension mechanism for custom functionality

---

## API Reference

### Python API

#### Core Types (ag_ui.core)

```python
from ag_ui.core import (
    # Input/Output
    RunAgentInput,

    # Event Types
    EventType,

    # Lifecycle Events
    RunStartedEvent,
    RunFinishedEvent,
    RunErrorEvent,
    StepStartedEvent,
    StepFinishedEvent,

    # Message Events
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,

    # Tool Events
    ToolCallStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,

    # State Events
    StateSnapshotEvent,
    StateDeltaEvent,
    MessagesSnapshotEvent,

    # Special Events
    RawEvent,
    CustomEvent,
)
```

#### RunAgentInput Schema

```python
class RunAgentInput(BaseModel):
    """Input schema for AG-UI agent runs"""

    thread_id: str
    """Unique thread identifier for conversation continuity"""

    run_id: str
    """Unique run identifier for this execution"""

    messages: List[Message]
    """Conversation history"""

    state: Optional[Dict[str, Any]] = None
    """Current application state"""

    tools: Optional[List[ToolDefinition]] = None
    """Available tools for this run"""

    metadata: Optional[Dict[str, Any]] = None
    """Additional run metadata"""
```

#### EventEncoder

```python
from ag_ui.encoder import EventEncoder

encoder = EventEncoder()

# Encode single event for SSE
sse_string = encoder.encode(event)
# Returns: "data: {\"type\":\"...\",\"messageId\":\"...\"}\n\n"

# Encode for WebSocket (JSON)
json_string = encoder.encode_json(event)
# Returns: "{\"type\":\"...\",\"messageId\":\"...\"}"
```

### TypeScript API

#### Client SDK (@ag-ui/client)

```typescript
import { HttpAgent, AgentMessage } from '@ag-ui/client';

// Create agent client
const agent = new HttpAgent({
  url: 'https://api.example.com/agent',
  headers: {
    Authorization: 'Bearer YOUR_TOKEN',
  },
});

// Run agent with streaming
const stream = await agent.run({
  threadId: 'thread_123',
  runId: 'run_456',
  messages: [
    { role: 'user', content: 'Hello!' }
  ],
});

// Subscribe to events
for await (const event of stream) {
  switch (event.type) {
    case 'TEXT_MESSAGE_CONTENT':
      console.log(event.delta);
      break;
    case 'TOOL_CALL_START':
      console.log(`Calling tool: ${event.toolCallName}`);
      break;
  }
}
```

---

## Authentication & Security

### Authentication Mechanisms

#### 1. Bearer Token (Recommended)
```python
# FastAPI Example
from fastapi import Header, HTTPException

async def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Unauthorized')

    token = authorization.split(' ')[1]
    # Validate token (JWT, database lookup, etc.)
    return token
```

#### 2. OAuth2 Flow
```typescript
// Client-side
const agent = new HttpAgent({
  url: 'https://api.example.com/agent',
  headers: {
    Authorization: `Bearer ${await getAccessToken()}`,
  },
});
```

### Security Best Practices

1. **Transport Security**
   - Always use HTTPS/WSS in production
   - TLS 1.2+ required
   - Optional: Message-level encryption using JOSE

2. **Authorization**
   - Role-based access control (RBAC) on component actions
   - Validate thread_id ownership
   - Implement rate limiting per user/token

3. **Audit Logging**
   - Log all RunStarted/RunFinished events
   - Track tool invocations
   - Immutable audit trail for compliance

4. **Token Management**
   - Short-lived access tokens (15-60 minutes)
   - Refresh token rotation
   - Secure token storage (HTTP-only cookies, secure storage)

5. **Input Validation**
   - Validate all RunAgentInput fields
   - Sanitize user messages
   - Limit message/state size to prevent DoS

---

## Integration Patterns

### Pattern 1: Simple Streaming Agent

**Backend (FastAPI + Pydantic AI)**
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from ag_ui.core import RunAgentInput
from pydantic_ai import Agent
from pydantic_ai.ag_ui import run_ag_ui, SSE_CONTENT_TYPE

app = FastAPI()
agent = Agent('openai:gpt-4', instructions='Be helpful!')

@app.post('/agent')
async def run_agent(input_data: RunAgentInput):
    event_stream = run_ag_ui(agent, input_data, accept=SSE_CONTENT_TYPE)
    return StreamingResponse(event_stream, media_type=SSE_CONTENT_TYPE)
```

**Frontend (React)**
```typescript
import { HttpAgent } from '@ag-ui/client';

const agent = new HttpAgent({ url: '/agent' });

async function chat(message: string) {
  const stream = await agent.run({
    threadId: 'thread_123',
    runId: crypto.randomUUID(),
    messages: [{ role: 'user', content: message }],
  });

  for await (const event of stream) {
    if (event.type === 'TEXT_MESSAGE_CONTENT') {
      updateUI(event.delta);
    }
  }
}
```

### Pattern 2: Tool-Enabled Agent

**Backend**
```python
from pydantic_ai import Agent, RunContext, ToolReturn
from ag_ui.core import CustomEvent, EventType

agent = Agent('openai:gpt-4')

@agent.tool
async def fetch_weather(ctx: RunContext[None], city: str) -> ToolReturn[str]:
    # Emit custom event during tool execution
    custom_event = CustomEvent(
        type=EventType.CUSTOM,
        name='weather_api_call',
        data={'city': city, 'status': 'fetching'}
    )

    weather_data = await call_weather_api(city)

    return ToolReturn(
        result=f"Weather in {city}: {weather_data}",
        metadata=[custom_event]  # Include custom events
    )

@app.post('/agent')
async def run_agent(input_data: RunAgentInput):
    event_stream = run_ag_ui(agent, input_data)
    return StreamingResponse(event_stream, media_type='text/event-stream')
```

### Pattern 3: State-Driven UI

**Backend**
```python
from ag_ui.encoder import EventEncoder
from ag_ui.core import StateDeltaEvent, EventType

async def agent_with_state(input_data: RunAgentInput):
    encoder = EventEncoder()

    # Initial state
    yield encoder.encode(StateSnapshotEvent(
        type=EventType.STATE_SNAPSHOT,
        state={'step': 'thinking', 'progress': 0}
    ))

    # Update state as agent progresses
    yield encoder.encode(StateDeltaEvent(
        type=EventType.STATE_DELTA,
        delta={'progress': 50}
    ))

    # Final state
    yield encoder.encode(StateDeltaEvent(
        type=EventType.STATE_DELTA,
        delta={'step': 'complete', 'progress': 100}
    ))
```

**Frontend State Management**
```typescript
const [agentState, setAgentState] = useState({});

for await (const event of stream) {
  switch (event.type) {
    case 'STATE_SNAPSHOT':
      setAgentState(event.state);
      break;
    case 'STATE_DELTA':
      setAgentState(prev => ({ ...prev, ...event.delta }));
      break;
  }
}
```

### Pattern 4: Multi-Framework Integration

**LangGraph**
```python
# Install: pip install ag-ui-langgraph
from ag_ui_langgraph import LangGraphAdapter
from langgraph.graph import StateGraph

graph = StateGraph(...)
# Build your LangGraph...

adapter = LangGraphAdapter(graph)

@app.post('/agent')
async def run_agent(input_data: RunAgentInput):
    return StreamingResponse(
        adapter.stream(input_data),
        media_type='text/event-stream'
    )
```

**CrewAI**
```python
# Install: pip install ag-ui-crewai
from ag_ui_crewai import CrewAIAdapter
from crewai import Crew, Agent, Task

crew = Crew(agents=[...], tasks=[...])
adapter = CrewAIAdapter(crew)

@app.post('/agent')
async def run_agent(input_data: RunAgentInput):
    return StreamingResponse(
        adapter.stream(input_data),
        media_type='text/event-stream'
    )
```

---

## Python Implementation

### Installation

```bash
# Core protocol
pip install ag-ui-protocol

# Framework integrations (optional)
pip install ag-ui-langgraph
pip install ag-ui-crewai
pip install llama-index-protocols-ag-ui

# With Pydantic AI
pip install pydantic-ai[ag-ui]

# For FastAPI servers
pip install fastapi uvicorn
```

### Minimal Python Server

```python
import json
from http import HTTPStatus
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from ag_ui.core import RunAgentInput, EventType
from ag_ui.core import RunStartedEvent, TextMessageStartEvent
from ag_ui.core import TextMessageContentEvent, TextMessageEndEvent
from ag_ui.core import RunFinishedEvent
from ag_ui.encoder import EventEncoder

app = FastAPI(title='AG-UI Agent')

@app.post('/agent')
async def run_agent(request: Request) -> Response:
    # Parse input
    try:
        run_input = RunAgentInput.model_validate(await request.json())
    except ValidationError as e:
        return Response(
            content=json.dumps(e.json()),
            media_type='application/json',
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    # Generate event stream
    async def event_generator():
        encoder = EventEncoder()

        # Start run
        yield encoder.encode(RunStartedEvent(
            type=EventType.RUN_STARTED,
            thread_id=run_input.thread_id,
            run_id=run_input.run_id
        ))

        # Generate message
        message_id = 'msg_123'
        yield encoder.encode(TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role='assistant'
        ))

        # Stream text chunks
        response_text = "Hello! How can I help you today?"
        for chunk in response_text.split():
            yield encoder.encode(TextMessageContentEvent(
                type=EventType.TEXT_MESSAGE_CONTENT,
                message_id=message_id,
                delta=chunk + ' '
            ))

        yield encoder.encode(TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        ))

        # Finish run
        yield encoder.encode(RunFinishedEvent(
            type=EventType.RUN_FINISHED,
            thread_id=run_input.thread_id,
            run_id=run_input.run_id
        ))

    return StreamingResponse(
        event_generator(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
    )
```

### Python Type Safety

All AG-UI events are Pydantic models with automatic validation:

```python
from ag_ui.core import TextMessageContentEvent, EventType

# Valid event
event = TextMessageContentEvent(
    type=EventType.TEXT_MESSAGE_CONTENT,
    message_id='msg_123',
    delta='Hello'
)

# Invalid event (raises ValidationError)
try:
    bad_event = TextMessageContentEvent(
        type=EventType.RUN_STARTED,  # Wrong type!
        message_id='msg_123',
        delta='Hello'
    )
except ValidationError as e:
    print(e)
```

### Automatic camelCase Serialization

```python
event = TextMessageContentEvent(
    type=EventType.TEXT_MESSAGE_CONTENT,
    message_id='msg_123',  # Python snake_case
    delta='Hello'
)

json_output = event.model_dump_json()
# Output: {"type":"TEXT_MESSAGE_CONTENT","messageId":"msg_123","delta":"Hello"}
#         ^^^ Automatically converted to camelCase for JavaScript
```

---

## FastAPI Integration

### Complete FastAPI Server Example

```python
from typing import AsyncGenerator
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse
from ag_ui.core import (
    RunAgentInput,
    EventType,
    RunStartedEvent,
    RunFinishedEvent,
    RunErrorEvent,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    ToolCallStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
)
from ag_ui.encoder import EventEncoder
from pydantic_ai import Agent

app = FastAPI(
    title='AG-UI Agent Server',
    description='Production-ready AG-UI protocol implementation',
    version='1.0.0'
)

# Initialize agent
agent = Agent(
    'openai:gpt-4',
    system_prompt='You are a helpful assistant.',
)

# Add tools
@agent.tool
async def search_web(query: str) -> str:
    """Search the web for information"""
    # Implement web search
    return f"Search results for: {query}"

@app.post('/agent', response_class=StreamingResponse)
async def run_agent(
    input_data: RunAgentInput,
    authorization: str = Header(None)
) -> StreamingResponse:
    """
    AG-UI protocol endpoint.

    Accepts RunAgentInput and streams AG-UI events via SSE.
    """
    # Authentication
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Unauthorized')

    # Generate events
    async def event_generator() -> AsyncGenerator[str, None]:
        encoder = EventEncoder()

        try:
            # Start run
            yield encoder.encode(RunStartedEvent(
                type=EventType.RUN_STARTED,
                thread_id=input_data.thread_id,
                run_id=input_data.run_id
            ))

            # Run agent with AG-UI support
            from pydantic_ai.ag_ui import run_ag_ui

            async for event in run_ag_ui(agent, input_data):
                yield encoder.encode(event)

        except Exception as e:
            # Error handling
            yield encoder.encode(RunErrorEvent(
                type=EventType.RUN_ERROR,
                thread_id=input_data.thread_id,
                run_id=input_data.run_id,
                error={
                    'message': str(e),
                    'code': 'AGENT_ERROR',
                }
            ))

    return StreamingResponse(
        event_generator(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',  # Disable nginx buffering
        }
    )

@app.get('/health')
async def health_check():
    """Health check endpoint"""
    return {'status': 'healthy'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
```

### FastAPI Middleware for Logging

```python
from fastapi import Request
import time
import logging

logger = logging.getLogger(__name__)

@app.middleware('http')
async def log_requests(request: Request, call_next):
    """Log all AG-UI requests"""
    start_time = time.time()

    # Log request
    logger.info(f'AG-UI Request: {request.method} {request.url}')

    response = await call_next(request)

    # Log response
    duration = time.time() - start_time
    logger.info(f'AG-UI Response: {response.status_code} ({duration:.2f}s)')

    return response
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],  # Frontend origin
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
```

---

## TypeScript SDK

### Installation

```bash
npm install @ag-ui/client
# or
yarn add @ag-ui/client
# or
pnpm add @ag-ui/client
```

### Client Usage

```typescript
import { HttpAgent } from '@ag-ui/client';

// Create agent client
const agent = new HttpAgent({
  url: 'https://api.example.com/agent',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
  },
});

// Run agent with streaming
const stream = await agent.run({
  threadId: 'thread_' + crypto.randomUUID(),
  runId: 'run_' + crypto.randomUUID(),
  messages: [
    { role: 'user', content: 'What is the weather in San Francisco?' }
  ],
  state: { timezone: 'America/Los_Angeles' },
});

// Process events
for await (const event of stream) {
  console.log('Event:', event);
}
```

### React Integration

```typescript
import { HttpAgent } from '@ag-ui/client';
import { useState, useCallback } from 'react';

function useAgent() {
  const [messages, setMessages] = useState<string[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const agent = new HttpAgent({ url: '/agent' });

  const runAgent = useCallback(async (userMessage: string) => {
    setIsRunning(true);
    setMessages(prev => [...prev, `User: ${userMessage}`]);

    const stream = await agent.run({
      threadId: 'thread_123',
      runId: crypto.randomUUID(),
      messages: [{ role: 'user', content: userMessage }],
    });

    let currentMessage = '';

    for await (const event of stream) {
      switch (event.type) {
        case 'TEXT_MESSAGE_START':
          currentMessage = '';
          break;

        case 'TEXT_MESSAGE_CONTENT':
          currentMessage += event.delta;
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1] = `Agent: ${currentMessage}`;
            return newMessages;
          });
          break;

        case 'TEXT_MESSAGE_END':
          // Message complete
          break;

        case 'TOOL_CALL_START':
          console.log(`Calling tool: ${event.toolCallName}`);
          break;

        case 'RUN_FINISHED':
          setIsRunning(false);
          break;
      }
    }
  }, []);

  return { messages, isRunning, runAgent };
}
```

---

## Dependencies & Requirements

### Python Dependencies

#### Core Protocol
```toml
[tool.poetry.dependencies]
python = "^3.9"
pydantic = "^2.0"
ag-ui-protocol = "^0.1.0"
```

#### FastAPI Server
```toml
[tool.poetry.dependencies]
fastapi = "^0.100.0"
uvicorn = { extras = ["standard"], version = "^0.23.0" }
```

#### Pydantic AI Integration
```toml
[tool.poetry.dependencies]
pydantic-ai = { extras = ["ag-ui"], version = "^0.0.14" }
openai = "^1.0.0"  # For OpenAI models
```

#### Framework Integrations
```toml
[tool.poetry.dependencies]
# LangGraph
ag-ui-langgraph = "^0.1.0"
langgraph = "^0.2.0"

# CrewAI
ag-ui-crewai = "^0.1.0"
crewai = "^0.1.0"

# LlamaIndex
llama-index-protocols-ag-ui = "^0.1.0"
llama-index = "^0.10.0"
```

### TypeScript Dependencies

```json
{
  "dependencies": {
    "@ag-ui/client": "^0.1.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0"
  }
}
```

### Peer Dependencies

AG-UI works with any LLM provider:
- OpenAI API (`openai` package)
- Anthropic Claude (`anthropic` package)
- Google Gemini (`google-generativeai` package)
- Ollama (local models, `ollama` package)
- Azure OpenAI
- Custom LLM implementations

---

## Best Practices

### 1. Event Ordering

**Always emit events in the correct order:**

✅ **Correct:**
```
RunStarted → TextMessageStart → TextMessageContent* → TextMessageEnd → RunFinished
```

❌ **Incorrect:**
```
TextMessageStart → RunStarted  # RunStarted must be first!
```

### 2. Message IDs

**Generate unique IDs for each message:**

```python
import uuid

message_id = f"msg_{uuid.uuid4().hex[:8]}"
```

### 3. Tool Call Patterns

**Complete tool call sequences:**

```python
# Always emit all three events
yield ToolCallStartEvent(...)
yield ToolCallArgsEvent(...)  # Can emit multiple for streaming args
yield ToolCallEndEvent(...)
```

### 4. Error Handling

**Always emit RunFinished or RunError:**

```python
try:
    # Agent logic
    yield RunFinishedEvent(...)
except Exception as e:
    yield RunErrorEvent(
        type=EventType.RUN_ERROR,
        thread_id=thread_id,
        run_id=run_id,
        error={'message': str(e)}
    )
```

### 5. State Management

**Use StateDelta for incremental updates:**

```python
# Don't send full state on every update
yield StateSnapshotEvent(state={'step': 1, 'progress': 0, 'data': {...}})

# Do use deltas for changes
yield StateDeltaEvent(delta={'progress': 50})  # Only changed fields
```

### 6. SSE Headers

**Set proper headers for SSE streaming:**

```python
headers = {
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'X-Accel-Buffering': 'no',  # Disable nginx buffering
    'Content-Type': 'text/event-stream',
}
```

### 7. Connection Management

**Handle client disconnections gracefully:**

```python
from starlette.requests import Request

async def event_generator(request: Request):
    try:
        while not await request.is_disconnected():
            yield event
    except Exception:
        # Cleanup resources
        pass
```

### 8. Thread and Run ID Management

**Use consistent ID schemes:**

```python
# Thread ID: Persistent across multiple runs
thread_id = f"thread_{user_id}_{conversation_id}"

# Run ID: Unique per execution
run_id = f"run_{uuid.uuid4()}"
```

### 9. Tool Result Timing

**Emit ToolCallResult after tool execution completes:**

```python
# 1. Emit tool call definition
yield ToolCallStartEvent(tool_call_id='tc_123', tool_call_name='search')
yield ToolCallArgsEvent(tool_call_id='tc_123', args_json='{"query":"..."}')
yield ToolCallEndEvent(tool_call_id='tc_123')

# 2. Execute tool
result = await execute_tool(...)

# 3. Emit result
yield ToolCallResultEvent(tool_call_id='tc_123', result=result)
```

### 10. Frontend State Synchronization

**Use STATE_SNAPSHOT initially, STATE_DELTA for updates:**

```python
# On first connection
yield StateSnapshotEvent(state={...})

# On subsequent updates
yield StateDeltaEvent(delta={...})
```

---

## Error Handling & Retry Strategies

### Client-Side Error Handling

#### SSE Reconnection

Browser EventSource API automatically reconnects on connection loss:

```typescript
const eventSource = new EventSource('/agent');

eventSource.addEventListener('open', () => {
  console.log('Connection opened');
});

eventSource.addEventListener('error', (e) => {
  console.error('Connection error:', e);
  // Browser automatically retries
});

// Manual reconnection with exponential backoff
let retryCount = 0;
const maxRetries = 5;

eventSource.addEventListener('error', (e) => {
  if (retryCount < maxRetries) {
    const delay = Math.min(1000 * Math.pow(2, retryCount), 30000);
    retryCount++;

    setTimeout(() => {
      // Recreate connection
      connectToAgent();
    }, delay);
  }
});
```

#### HTTP Client Retry

```typescript
async function runAgentWithRetry(
  input: RunAgentInput,
  maxRetries: number = 3
) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await agent.run(input);
    } catch (error) {
      if (i === maxRetries - 1) throw error;

      // Exponential backoff
      const delay = Math.min(1000 * Math.pow(2, i), 10000);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
```

### Server-Side Error Handling

#### Graceful Degradation

```python
async def event_generator(run_input: RunAgentInput):
    encoder = EventEncoder()

    yield encoder.encode(RunStartedEvent(...))

    try:
        # Agent execution
        async for event in agent.run(run_input):
            yield encoder.encode(event)

        yield encoder.encode(RunFinishedEvent(...))

    except OpenAIError as e:
        # LLM provider error
        yield encoder.encode(RunErrorEvent(
            ...,
            error={
                'message': 'LLM provider error',
                'code': 'LLM_ERROR',
                'details': {'provider': 'openai', 'original': str(e)}
            }
        ))

    except ToolExecutionError as e:
        # Tool failure - continue with degraded functionality
        yield encoder.encode(ToolCallResultEvent(
            tool_call_id=e.tool_call_id,
            error={'message': str(e), 'code': 'TOOL_ERROR'}
        ))

        # Continue with other operations
        yield encoder.encode(RunFinishedEvent(...))

    except Exception as e:
        # Unknown error
        logger.exception('Agent execution failed')
        yield encoder.encode(RunErrorEvent(
            ...,
            error={'message': 'Internal server error', 'code': 'INTERNAL_ERROR'}
        ))
```

#### Timeout Handling

```python
import asyncio

async def event_generator_with_timeout(run_input: RunAgentInput):
    try:
        async with asyncio.timeout(300):  # 5 minute timeout
            async for event in event_generator(run_input):
                yield event
    except asyncio.TimeoutError:
        yield encoder.encode(RunErrorEvent(
            ...,
            error={'message': 'Agent execution timeout', 'code': 'TIMEOUT'}
        ))
```

### Retry Best Practices

1. **Exponential Backoff**: Increase delay between retries
2. **Jitter**: Add randomness to prevent thundering herd
3. **Max Retries**: Limit retry attempts (3-5 typical)
4. **Idempotency**: Ensure retries don't cause duplicate operations
5. **Circuit Breaker**: Stop retrying after sustained failures

```python
import random
import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise

                    # Exponential backoff with jitter
                    delay = base_delay * (2 ** attempt)
                    jitter = random.uniform(0, delay * 0.1)
                    await asyncio.sleep(delay + jitter)

        return wrapper
    return decorator

@retry_with_backoff(max_retries=3)
async def call_llm_api(...):
    # API call
    pass
```

---

## Code Examples

### Example 1: Simple Chat Agent

**Backend (FastAPI + OpenAI)**
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from ag_ui.core import RunAgentInput
from ag_ui.encoder import EventEncoder
from ag_ui.core import (
    EventType, RunStartedEvent, TextMessageStartEvent,
    TextMessageContentEvent, TextMessageEndEvent, RunFinishedEvent
)
import openai
import uuid

app = FastAPI()
openai.api_key = 'your-api-key'

@app.post('/chat')
async def chat(input_data: RunAgentInput):
    async def event_generator():
        encoder = EventEncoder()

        # Start run
        yield encoder.encode(RunStartedEvent(
            type=EventType.RUN_STARTED,
            thread_id=input_data.thread_id,
            run_id=input_data.run_id
        ))

        # Prepare messages
        messages = [
            {'role': msg.role, 'content': msg.content}
            for msg in input_data.messages
        ]

        # Stream OpenAI response
        message_id = f"msg_{uuid.uuid4().hex[:8]}"

        yield encoder.encode(TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role='assistant'
        ))

        response = await openai.ChatCompletion.acreate(
            model='gpt-4',
            messages=messages,
            stream=True
        )

        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield encoder.encode(TextMessageContentEvent(
                    type=EventType.TEXT_MESSAGE_CONTENT,
                    message_id=message_id,
                    delta=chunk.choices[0].delta.content
                ))

        yield encoder.encode(TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        ))

        # Finish run
        yield encoder.encode(RunFinishedEvent(
            type=EventType.RUN_FINISHED,
            thread_id=input_data.thread_id,
            run_id=input_data.run_id
        ))

    return StreamingResponse(
        event_generator(),
        media_type='text/event-stream'
    )
```

### Example 2: Research Agent with Tools

**Backend (Pydantic AI)**
```python
from pydantic_ai import Agent, RunContext, ToolReturn
from ag_ui.core import CustomEvent, EventType

agent = Agent('openai:gpt-4', system_prompt='You are a research assistant.')

@agent.tool
async def search_web(ctx: RunContext[None], query: str) -> ToolReturn[str]:
    """Search the web for information"""
    # Emit custom event
    search_event = CustomEvent(
        type=EventType.CUSTOM,
        name='search_started',
        data={'query': query, 'source': 'google'}
    )

    # Simulate search
    results = f"Found 10 results for: {query}"

    return ToolReturn(
        result=results,
        metadata=[search_event]
    )

@agent.tool
async def summarize_text(ctx: RunContext[None], text: str) -> str:
    """Summarize text content"""
    # Use LLM to summarize
    summary = await openai_summarize(text)
    return summary

@app.post('/research')
async def research(input_data: RunAgentInput):
    from pydantic_ai.ag_ui import run_ag_ui, SSE_CONTENT_TYPE

    event_stream = run_ag_ui(agent, input_data, accept=SSE_CONTENT_TYPE)
    return StreamingResponse(event_stream, media_type=SSE_CONTENT_TYPE)
```

### Example 3: Multi-Step Workflow

**Backend**
```python
from ag_ui.core import StepStartedEvent, StepFinishedEvent

async def multi_step_workflow(input_data: RunAgentInput):
    encoder = EventEncoder()

    yield encoder.encode(RunStartedEvent(...))

    # Step 1: Analyze request
    step1_id = 'step_analyze'
    yield encoder.encode(StepStartedEvent(
        type=EventType.STEP_STARTED,
        step_id=step1_id,
        step_name='Analyzing request'
    ))

    # Perform analysis
    analysis = await analyze_request(input_data)

    yield encoder.encode(StepFinishedEvent(
        type=EventType.STEP_FINISHED,
        step_id=step1_id
    ))

    # Step 2: Generate plan
    step2_id = 'step_plan'
    yield encoder.encode(StepStartedEvent(
        type=EventType.STEP_STARTED,
        step_id=step2_id,
        step_name='Creating execution plan'
    ))

    plan = await create_plan(analysis)

    yield encoder.encode(StepFinishedEvent(
        type=EventType.STEP_FINISHED,
        step_id=step2_id
    ))

    # Step 3: Execute plan
    step3_id = 'step_execute'
    yield encoder.encode(StepStartedEvent(
        type=EventType.STEP_STARTED,
        step_id=step3_id,
        step_name='Executing plan'
    ))

    result = await execute_plan(plan)

    # Stream result as message
    message_id = 'msg_result'
    yield encoder.encode(TextMessageStartEvent(...))
    yield encoder.encode(TextMessageContentEvent(
        message_id=message_id,
        delta=result
    ))
    yield encoder.encode(TextMessageEndEvent(...))

    yield encoder.encode(StepFinishedEvent(
        type=EventType.STEP_FINISHED,
        step_id=step3_id
    ))

    yield encoder.encode(RunFinishedEvent(...))
```

### Example 4: Frontend React Component

**Complete Chat Component**
```typescript
import React, { useState, useCallback } from 'react';
import { HttpAgent } from '@ag-ui/client';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  isComplete: boolean;
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [currentState, setCurrentState] = useState<any>({});

  const agent = new HttpAgent({
    url: 'http://localhost:8000/agent',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  const sendMessage = useCallback(async () => {
    if (!input.trim() || isRunning) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input,
      isComplete: true,
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsRunning(true);

    const assistantMessage: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      isComplete: false,
    };

    setMessages(prev => [...prev, assistantMessage]);

    try {
      const stream = await agent.run({
        threadId: 'thread_123',
        runId: crypto.randomUUID(),
        messages: [
          ...messages.map(m => ({ role: m.role, content: m.content })),
          { role: 'user', content: input },
        ],
      });

      for await (const event of stream) {
        switch (event.type) {
          case 'TEXT_MESSAGE_CONTENT':
            setMessages(prev => {
              const updated = [...prev];
              const lastMessage = updated[updated.length - 1];
              lastMessage.content += event.delta;
              return updated;
            });
            break;

          case 'TEXT_MESSAGE_END':
            setMessages(prev => {
              const updated = [...prev];
              const lastMessage = updated[updated.length - 1];
              lastMessage.isComplete = true;
              return updated;
            });
            break;

          case 'STATE_SNAPSHOT':
            setCurrentState(event.state);
            break;

          case 'STATE_DELTA':
            setCurrentState(prev => ({ ...prev, ...event.delta }));
            break;

          case 'TOOL_CALL_START':
            console.log(`Calling tool: ${event.toolCallName}`);
            break;

          case 'RUN_FINISHED':
            setIsRunning(false);
            break;

          case 'RUN_ERROR':
            console.error('Agent error:', event.error);
            setIsRunning(false);
            break;
        }
      }
    } catch (error) {
      console.error('Connection error:', error);
      setIsRunning(false);
    }
  }, [input, messages, isRunning]);

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map(msg => (
          <div key={msg.id} className={`message ${msg.role}`}>
            <strong>{msg.role}:</strong> {msg.content}
            {!msg.isComplete && <span className="cursor">▊</span>}
          </div>
        ))}
      </div>

      {currentState.step && (
        <div className="status">
          Step: {currentState.step} ({currentState.progress}%)
        </div>
      )}

      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && sendMessage()}
          disabled={isRunning}
          placeholder="Type a message..."
        />
        <button onClick={sendMessage} disabled={isRunning || !input.trim()}>
          {isRunning ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;
```

---

## Resources & References

### Official Documentation
- **AG-UI Docs**: https://docs.ag-ui.com
- **GitHub Repository**: https://github.com/ag-ui-protocol/ag-ui
- **TypeScript SDK**: https://github.com/ag-ui-protocol/typescript-sdk

### Python Packages
- **ag-ui-protocol**: https://pypi.org/project/ag-ui-protocol/
- **ag-ui-langgraph**: https://pypi.org/project/ag-ui-langgraph/
- **ag-ui-crewai**: https://pypi.org/project/ag-ui-crewai/
- **llama-index-protocols-ag-ui**: https://pypi.org/project/llama-index-protocols-ag-ui/
- **pydantic-ai**: https://ai.pydantic.dev/ag-ui/

### TypeScript Packages
- **@ag-ui/client**: https://www.npmjs.com/package/@ag-ui/client

### Framework Integrations
- **LangGraph**: https://www.copilotkit.ai/blog/how-to-add-a-frontend-to-any-langgraph-agent-using-ag-ui-protocol
- **CrewAI**: https://www.copilotkit.ai/blog/how-to-add-a-frontend-to-any-crewai-agent-using-ag-ui-protocol
- **Mastra**: https://www.copilotkit.ai/blog/how-to-add-a-frontend-to-any-mastra-agent-using-ag-ui-protocol
- **Agno**: https://www.copilotkit.ai/blog/build-your-own-ai-stock-portfolio-agent-with-agno-ag-ui

### Technical Articles
- **Introducing AG-UI**: https://webflow.copilotkit.ai/blog/introducing-ag-ui-the-protocol-where-agents-meet-users
- **AG-UI Protocol Guide**: https://zediot.com/blog/ag-ui-protocol/
- **Why LangGraph and CrewAI Are Betting on AG-UI**: https://prajnaaiwisdom.medium.com/why-langgraph-and-crewai-are-betting-on-ag-ui-03ed00ffd193

### Community Resources
- **GitHub Issues**: https://github.com/ag-ui-protocol/ag-ui/issues
- **GitHub Discussions**: https://github.com/ag-ui-protocol/ag-ui/discussions

### Related Protocols
- **Server-Sent Events (SSE) Spec**: https://html.spec.whatwg.org/multipage/server-sent-events.html
- **WebSocket Protocol**: https://datatracker.ietf.org/doc/html/rfc6455

---

## Appendix: Quick Reference

### Event Type Enum

```python
class EventType:
    # Lifecycle
    RUN_STARTED = 'RUN_STARTED'
    RUN_FINISHED = 'RUN_FINISHED'
    RUN_ERROR = 'RUN_ERROR'
    STEP_STARTED = 'STEP_STARTED'
    STEP_FINISHED = 'STEP_FINISHED'

    # Messages
    TEXT_MESSAGE_START = 'TEXT_MESSAGE_START'
    TEXT_MESSAGE_CONTENT = 'TEXT_MESSAGE_CONTENT'
    TEXT_MESSAGE_END = 'TEXT_MESSAGE_END'

    # Tools
    TOOL_CALL_START = 'TOOL_CALL_START'
    TOOL_CALL_ARGS = 'TOOL_CALL_ARGS'
    TOOL_CALL_END = 'TOOL_CALL_END'
    TOOL_CALL_RESULT = 'TOOL_CALL_RESULT'

    # State
    STATE_SNAPSHOT = 'STATE_SNAPSHOT'
    STATE_DELTA = 'STATE_DELTA'
    MESSAGES_SNAPSHOT = 'MESSAGES_SNAPSHOT'

    # Special
    RAW = 'RAW'
    CUSTOM = 'CUSTOM'
```

### Common Patterns

**Complete Message Sequence**:
```
TextMessageStart → TextMessageContent (×N) → TextMessageEnd
```

**Complete Tool Call Sequence**:
```
ToolCallStart → ToolCallArgs (×N) → ToolCallEnd → ToolCallResult
```

**Complete Run Sequence**:
```
RunStarted → [Events...] → (RunFinished | RunError)
```

**Multi-Step Run**:
```
RunStarted → StepStarted → [Events...] → StepFinished → ... → RunFinished
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-19
**Research Conducted By**: Research Agent
**Repository Status**: Active Development
**Protocol Maturity**: Production-Ready (v0.1.x)

---

## Notes on ai16z

Based on research, **ai16z** and **AG-UI Protocol** are separate projects:

- **ai16z**: AI-driven investment DAO platform with ElizaOS framework for building autonomous agents on Solana blockchain ($2.3B valuation)
- **AG-UI Protocol**: Agent-UI interaction protocol developed by CopilotKit, LangGraph, and CrewAI

The original request mentioned "ai16z/ag-ui-protocol" but this appears to be a misidentification. The AG-UI protocol is maintained by the `ag-ui-protocol` GitHub organization, not ai16z.

If ai16z has adopted or forked AG-UI protocol, that information was not available in the research conducted on 2025-10-19.
