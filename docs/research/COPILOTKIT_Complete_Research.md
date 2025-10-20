# CopilotKit Technical Specification

## Repository Information
- **Repository**: https://github.com/CopilotKit/CopilotKit
- **Version**: v1.10.6
- **Commit**: ba1dc6d80535c7c18542b2d147619c3977ce48aa
- **Date**: 2025-10-17 10:25:06 -0700
- **Research Date**: 2025-10-19

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

CopilotKit is a full-stack framework for building AI copilots into React applications. It consists of:

1. **Frontend SDK** (`@copilotkit/react-core`, `@copilotkit/react-ui`)
2. **Backend SDK** (Python `copilotkit` package, Node.js `@copilotkit/runtime`)
3. **AG-UI Protocol** - Agent-User Interaction Protocol (underlying communication layer)
4. **Runtime/Adapter Layer** - Connects to LLM providers (OpenAI, Anthropic, etc.)

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend                           │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │ CopilotChat    │  │ useCoAgent   │  │ useCopilotAction│ │
│  │ Component      │  │ Hook         │  │ Hook            │ │
│  └────────────────┘  └──────────────┘  └─────────────────┘ │
│           │                  │                    │          │
│           └──────────────────┴────────────────────┘          │
│                              │                               │
│                    ┌─────────▼─────────┐                     │
│                    │  CopilotProvider  │                     │
│                    │  (Context/State)  │                     │
│                    └─────────┬─────────┘                     │
└──────────────────────────────┼───────────────────────────────┘
                               │ GraphQL/HTTP
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                   CopilotKit Runtime                          │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │ AG-UI Protocol │  │  Adapters    │  │ Remote Endpoints│ │
│  │  (Events)      │  │  (LLM)       │  │  (Agents)       │ │
│  └────────────────┘  └──────────────┘  └─────────────────┘ │
└───────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
        ┌───────▼──────┐  ┌───▼────┐  ┌─────▼──────┐
        │ LangGraph    │  │ OpenAI │  │ Anthropic  │
        │ Python Agent │  │        │  │            │
        └──────────────┘  └────────┘  └────────────┘
```

### 1.2 AG-UI Protocol

CopilotKit uses the **AG-UI (Agent-User Interaction) Protocol** underneath. This is a standardized protocol for agent-to-UI communication supporting:

- **Text streaming** (TextMessageStart, TextMessageContent, TextMessageEnd)
- **Tool/Action execution** (ActionExecutionStart, ActionExecutionArgs, ActionExecutionEnd)
- **State synchronization** (AgentStateMessage, StateSnapshotEvent)
- **Meta-events** (Interrupts, PredictState, Exit)
- **Lifecycle events** (RunStarted, RunFinished, NodeStarted, NodeFinished)

**Event Types** (from `sdk-python/copilotkit/protocol.py`):
```python
class RuntimeEventTypes(Enum):
    TEXT_MESSAGE_START = "TextMessageStart"
    TEXT_MESSAGE_CONTENT = "TextMessageContent"
    TEXT_MESSAGE_END = "TextMessageEnd"
    ACTION_EXECUTION_START = "ActionExecutionStart"
    ACTION_EXECUTION_ARGS = "ActionExecutionArgs"
    ACTION_EXECUTION_END = "ActionExecutionEnd"
    ACTION_EXECUTION_RESULT = "ActionExecutionResult"
    AGENT_STATE_MESSAGE = "AgentStateMessage"
    META_EVENT = "MetaEvent"
    RUN_STARTED = "RunStarted"
    RUN_FINISHED = "RunFinished"
    RUN_ERROR = "RunError"
    NODE_STARTED = "NodeStarted"
    NODE_FINISHED = "NodeFinished"
```

---

## 2. Backend SDK (Python)

### 2.1 Package Structure

```
copilotkit/
├── __init__.py
├── sdk.py                        # Core SDK classes
├── integrations/
│   └── fastapi.py               # FastAPI integration
├── agent.py                     # Base Agent class
├── langgraph_agent.py          # LangGraph integration
├── langgraph_agui_agent.py     # AG-UI LangGraph adapter
├── action.py                    # Action definitions
├── parameter.py                 # Parameter schemas
├── types.py                     # Type definitions
├── protocol.py                  # AG-UI protocol events
├── langgraph.py                 # LangGraph utilities
├── langchain.py                 # LangChain utilities
└── exc.py                       # Exception classes
```

### 2.2 Core Classes

#### 2.2.1 CopilotKitRemoteEndpoint

**File**: `sdk-python/copilotkit/sdk.py`

Main SDK class for serving actions and agents.

```python
from copilotkit import CopilotKitRemoteEndpoint, Action, LangGraphAGUIAgent

sdk = CopilotKitRemoteEndpoint(
    actions=[
        Action(
            name="greet_user",
            handler=greet_user_handler,
            description="Greet the user",
            parameters=[
                {
                    "name": "name",
                    "type": "string",
                    "description": "The name of the user"
                }
            ]
        )
    ],
    agents=[
        LangGraphAGUIAgent(
            name="email_agent",
            description="This agent sends emails",
            graph=graph,
        )
    ]
)
```

**Methods**:
- `info(context: CopilotKitContext) -> InfoDict` - Returns available actions/agents
- `execute_action(context, name, arguments) -> ActionResultDict` - Executes an action
- `execute_agent(context, name, thread_id, state, messages, actions, ...)` - Runs agent
- `get_agent_state(context, thread_id, name)` - Retrieves agent state

**Dynamic Actions/Agents** (context-based):
```python
sdk = CopilotKitRemoteEndpoint(
    actions=lambda context: [
        Action(
            name="greet_user",
            handler=make_handler(context["properties"]["user_id"]),
            description="Greet the user"
        )
    ],
    agents=lambda context: (
        [admin_agent, user_agent]
        if is_admin(context["properties"]["token"])
        else [user_agent]
    )
)
```

#### 2.2.2 Action

**File**: `sdk-python/copilotkit/action.py`

```python
from copilotkit import Action

action = Action(
    name="send_email",
    handler=send_email_handler,
    description="Send an email to a recipient",
    parameters=[
        {
            "name": "to",
            "type": "string",
            "description": "Email recipient",
            "required": True
        },
        {
            "name": "subject",
            "type": "string",
            "description": "Email subject"
        },
        {
            "name": "body",
            "type": "string",
            "description": "Email body"
        }
    ]
)
```

**Handler Signature**:
```python
async def send_email_handler(to: str, subject: str, body: str) -> Any:
    # Sync or async handler
    result = await send_email(to, subject, body)
    return result  # Returned as ActionResultDict
```

#### 2.2.3 Agent Base Class

**File**: `sdk-python/copilotkit/agent.py`

```python
from copilotkit import Agent
from abc import ABC, abstractmethod

class Agent(ABC):
    def __init__(self, name: str, description: Optional[str] = None):
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, state, config, messages, thread_id, actions, **kwargs):
        """Execute the agent"""

    @abstractmethod
    async def get_state(self, thread_id: str):
        """Get agent state"""
```

#### 2.2.4 LangGraphAGUIAgent

**File**: `sdk-python/copilotkit/langgraph_agui_agent.py`

Wraps a LangGraph CompiledStateGraph for use with CopilotKit.

```python
from copilotkit import LangGraphAGUIAgent
from langgraph.graph.state import CompiledStateGraph

agent = LangGraphAGUIAgent(
    name="research_agent",
    description="AI research assistant",
    graph=compiled_graph,
    config={
        "configurable": {
            "model": "gpt-4o",
            "temperature": 0.7
        }
    }
)
```

**Key Features**:
- **State streaming**: Emits `StateSnapshotEvent` for real-time UI updates
- **Custom events**: Handles `copilotkit_manually_emit_message`, `copilotkit_manually_emit_tool_call`, `copilotkit_manually_emit_intermediate_state`
- **Event filtering**: Supports `copilotkit:emit-tool-calls`, `copilotkit:emit-messages` metadata
- **PredictState**: Streams intermediate state from tool calls via `copilotkit:emit-intermediate-state`

**Custom Event Names**:
```python
class CustomEventNames(Enum):
    ManuallyEmitMessage = "copilotkit_manually_emit_message"
    ManuallyEmitToolCall = "copilotkit_manually_emit_tool_call"
    ManuallyEmitState = "copilotkit_manually_emit_intermediate_state"
```

#### 2.2.5 LangGraphAgent (Legacy)

**File**: `sdk-python/copilotkit/langgraph_agent.py`

**Note**: Use `LangGraphAGUIAgent` instead for new projects. `LangGraphAgent` is the older implementation.

```python
from copilotkit import LangGraphAgent

agent = LangGraphAgent(
    name="email_agent",
    graph=graph,
    description="This agent sends emails",
    langgraph_config=config,
    copilotkit_config={
        "merge_state": custom_merge_function,
        "convert_messages": custom_convert_function
    }
)
```

**CopilotKitConfig Options**:
- `merge_state`: Custom function to merge CopilotKit state into LangGraph state
- `convert_messages`: Custom function to convert CopilotKit messages to LangChain messages

**Default Merge State**:
```python
def langgraph_default_merge_state(
    state: dict,
    messages: List[BaseMessage],
    actions: List[Any],
    agent_name: str
):
    if len(messages) > 0 and isinstance(messages[0], SystemMessage):
        messages = messages[1:]

    existing_messages = state.get("messages", [])
    existing_message_ids = {message.id for message in existing_messages}
    new_messages = [msg for msg in messages if msg.id not in existing_message_ids]

    return {
        **state,
        "messages": new_messages,
        "copilotkit": {
            "actions": actions
        }
    }
```

**State Streaming**:
- Emits `on_copilotkit_state_sync` events
- Filters state by input/output schema keys
- Supports `interrupt_after` for human-in-the-loop
- Handles regeneration via message checkpoints

**Error Handling**:
```python
# Emits error events in both formats for compatibility
yield langchain_dumps({
    "event": "error",
    "data": {
        "message": f"{error_type}: {error_message}",
        "error_details": error_details,
        "thread_id": thread_id,
        "agent_name": self.name,
        "node_name": node_name or "unknown"
    }
}) + "\n"

yield langchain_dumps({
    "event": "on_copilotkit_error",
    "data": {
        "error": error_details,
        "thread_id": thread_id,
        "agent_name": self.name,
        "node_name": node_name or "unknown"
    }
}) + "\n"
```

### 2.3 FastAPI Integration

#### 2.3.1 add_fastapi_endpoint()

**File**: `sdk-python/copilotkit/integrations/fastapi.py`

```python
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from fastapi import FastAPI

app = FastAPI()
sdk = CopilotKitRemoteEndpoint(...)

add_fastapi_endpoint(
    fastapi_app=app,
    sdk=sdk,
    prefix="/copilotkit"
)
```

**Parameters**:
- `fastapi_app`: FastAPI application instance
- `sdk`: CopilotKitRemoteEndpoint instance
- `prefix`: URL prefix for the endpoint (e.g., "/copilotkit")
- `use_thread_pool` (deprecated): Whether to use ThreadPoolExecutor
- `max_workers` (deprecated): Maximum worker threads

**Endpoints Created**:
1. **GET/POST `/prefix/`** - Info endpoint (returns available actions/agents)
2. **POST `/prefix/agent/{name}`** - Execute agent
3. **POST `/prefix/agent/{name}/state`** - Get agent state
4. **POST `/prefix/action/{name}`** - Execute action

**Backward Compatibility Routes** (v1):
- **POST `/prefix/info`** - Info endpoint
- **POST `/prefix/actions/execute`** - Execute action
- **POST `/prefix/agents/execute`** - Execute agent
- **POST `/prefix/agents/state`** - Get agent state

#### 2.3.2 CopilotKitContext

**File**: `sdk-python/copilotkit/sdk.py`

Context object passed to all handlers:

```python
class CopilotKitContext(TypedDict):
    properties: Any                    # From frontend <CopilotKit properties={...} />
    frontend_url: Optional[str]        # Current frontend URL
    headers: Mapping[str, str]         # HTTP request headers
```

**Usage in Handlers**:
```python
sdk = CopilotKitRemoteEndpoint(
    actions=lambda context: [
        Action(
            name="user_action",
            handler=lambda **kwargs: process_with_context(
                context["properties"]["user_id"],
                **kwargs
            )
        )
    ]
)
```

### 2.4 Complete FastAPI Example

**File**: Based on `examples/coagents-wait-user-input/agent/`

```python
# agent.py - LangGraph agent definition
from langgraph.graph import MessagesState, START, END, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from copilotkit.langgraph import copilotkit_customize_config
from pydantic import BaseModel

# Define tools
@tool
def search(query: str):
    """Search the web."""
    return f"Search results for: {query}"

tools = [search]
tool_node = ToolNode(tools)

# Model
model = ChatOpenAI(model="gpt-4o")

# Human-in-the-loop tool
class AskHuman(BaseModel):
    """Ask the human a question"""
    question: str

model = model.bind_tools(tools + [AskHuman])

# Agent logic
def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return "end"
    elif last_message.tool_calls[0]["name"] == "AskHuman":
        return "ask_human"
    else:
        return "continue"

def call_model(state, config):
    config = copilotkit_customize_config(
        config,
        emit_tool_calls="AskHuman",  # Don't show AskHuman in chat
    )
    messages = state["messages"]
    response = model.invoke(messages, config=config)
    return {"messages": [response]}

def ask_human(state):
    pass  # Placeholder for interrupt

# Build graph
workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)
workflow.add_node("ask_human", ask_human)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "action",
        "ask_human": "ask_human",
        "end": END,
    },
)
workflow.add_edge("action", "agent")
workflow.add_edge("ask_human", "agent")

memory = MemorySaver()
graph = workflow.compile(
    checkpointer=memory,
    interrupt_after=["ask_human"]  # Pause for user input
)

# server.py - FastAPI server
from fastapi import FastAPI
import uvicorn
from copilotkit import CopilotKitRemoteEndpoint, LangGraphAGUIAgent
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from agent import graph

app = FastAPI()

sdk = CopilotKitRemoteEndpoint(
    agents=[
        LangGraphAGUIAgent(
            name="weather_agent",
            description="Agent that searches and asks questions",
            graph=graph
        )
    ]
)

add_fastapi_endpoint(app, sdk, "/copilotkit")

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
```

### 2.5 LangGraph Utilities

**File**: `sdk-python/copilotkit/langgraph.py`

```python
from copilotkit.langgraph import (
    copilotkit_customize_config,
    copilotkit_emit_state,
    copilotkit_emit_message,
    copilotkit_emit_tool_call
)

# Customize config to control what's emitted
def my_node(state, config):
    config = copilotkit_customize_config(
        config,
        emit_messages=False,         # Don't emit LLM messages
        emit_tool_calls="ToolName",  # Only emit specific tool calls
        emit_intermediate_state=[    # Stream state updates
            {
                "stateKey": "outline",
                "tool": "set_outline",
                "toolArgument": "outline"
            }
        ]
    )
    response = model.invoke(state["messages"], config)
    return {"messages": [response]}

# Manually emit state updates
def processing_node(state, config):
    copilotkit_emit_state(
        config,
        {"progress": 50, "status": "processing"}
    )
    # ... do work ...
    copilotkit_emit_state(
        config,
        {"progress": 100, "status": "complete"}
    )
    return state

# Manually emit messages
def notification_node(state, config):
    copilotkit_emit_message(
        config,
        "Processing your request..."
    )
    return state
```

---

## 3. Frontend SDK (React)

### 3.1 Package Structure

```
@copilotkit/react-core/
├── components/
│   ├── copilot-provider/         # Main provider
│   └── error-boundary/           # Error handling
├── context/
│   ├── copilot-context.tsx       # Core context
│   └── copilot-messages-context.tsx
├── hooks/
│   ├── use-coagent.ts            # CoAgent integration
│   ├── use-copilot-action.ts     # Action hook
│   ├── use-copilot-chat.ts       # Chat functionality
│   ├── use-coagent-state-render.ts
│   └── use-langgraph-interrupt.ts
├── types/
│   ├── frontend-action.ts
│   ├── coagent-state.ts
│   └── interrupt-action.ts
└── index.tsx

@copilotkit/react-ui/
├── components/
│   ├── chat/                     # Chat UI components
│   │   ├── index.tsx             # CopilotChat
│   │   ├── messages/
│   │   └── Suggestions.tsx
│   └── popup/                    # CopilotPopup
└── index.tsx

@copilotkit/runtime/
├── service-adapters/             # LLM adapters
│   ├── openai/
│   ├── anthropic/
│   └── google-genai/
└── runtime.ts                    # CopilotRuntime
```

### 3.2 CopilotKit Provider

**File**: `CopilotKit/packages/react-core/src/components/copilot-provider/`

```tsx
import { CopilotKit } from "@copilotkit/react-core";

function App() {
  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      agent="research_agent"
      properties={{
        userId: "user123",
        context: "research_mode"
      }}
    >
      <YourApp />
    </CopilotKit>
  );
}
```

**Props**:
- `runtimeUrl`: Backend endpoint URL
- `agent`: Default agent name (optional)
- `properties`: Context data passed to backend
- `publicApiKey`: API key for Copilot Cloud
- `headers`: Custom HTTP headers
- `credentials`: CORS credentials mode
- `showDevConsole`: Enable debug logging

### 3.3 useCoAgent Hook

**File**: `CopilotKit/packages/react-core/src/hooks/use-coagent.ts`

Primary hook for integrating LangGraph agents with shared state.

#### 3.3.1 Basic Usage

```tsx
import { useCoAgent } from "@copilotkit/react-core";

type AgentState = {
  count: number;
  items: string[];
};

function MyComponent() {
  const {
    name,           // Agent name
    nodeName,       // Current LangGraph node
    threadId,       // Thread ID
    running,        // Is agent running
    state,          // Current agent state
    setState,       // Update state
    start,          // Start agent
    stop,           // Stop agent
    run             // Re-run agent
  } = useCoAgent<AgentState>({
    name: "my-agent",
    initialState: {
      count: 0,
      items: []
    }
  });

  return (
    <div>
      <p>Count: {state.count}</p>
      <button onClick={() => setState({ count: state.count + 1 })}>
        Increment
      </button>
      <button onClick={start}>Start Agent</button>
      <button onClick={stop}>Stop Agent</button>
      <button onClick={() => run()}>Re-run</button>
    </div>
  );
}
```

#### 3.3.2 External State Management

```tsx
import { useState } from "react";
import { useCoAgent } from "@copilotkit/react-core";

function MyComponent() {
  const [agentState, setAgentState] = useState<AgentState>({
    count: 0,
    items: []
  });

  useCoAgent<AgentState>({
    name: "my-agent",
    state: agentState,
    setState: setAgentState
  });

  // State is managed externally
  return <div>Count: {agentState.count}</div>;
}
```

#### 3.3.3 LangGraph Config

```tsx
useCoAgent({
  name: "email-agent",
  initialState: {},
  config: {
    configurable: {
      model: "gpt-4o",
      temperature: 0.7,
      userId: "user123"
    }
  }
});
```

#### 3.3.4 Re-running with Hints

```tsx
const { run, state } = useCoAgent({
  name: "my-agent",
  initialState: { query: "" }
});

// Provide hint about why re-running
await run(({ previousState, currentState }) => {
  if (currentState.query !== previousState.query) {
    return {
      id: randomId(),
      role: "user",
      content: `The query changed from "${previousState.query}" to "${currentState.query}". Please update the results.`
    };
  }
});
```

#### 3.3.5 State Persistence

The hook automatically loads state from the backend when `threadId` changes:

```tsx
// Backend endpoint: POST /copilotkit/agent/{name}/state
const result = await runtimeClient.loadAgentState({
  threadId,
  agentName: name,
});

if (result.data?.loadAgentState?.threadExists && newState) {
  const fetchedState = parseJson(newState, {});
  setState(fetchedState);
}
```

### 3.4 useCoAgentStateRender Hook

**File**: `CopilotKit/packages/react-core/src/hooks/use-coagent-state-render.ts`

Render UI based on agent state changes.

```tsx
import { useCoAgentStateRender } from "@copilotkit/react-core";

type ResearchState = {
  outline: string[];
  currentStep: string;
  progress: number;
};

function ResearchUI() {
  useCoAgentStateRender<ResearchState>({
    name: "research_agent",
    render: ({ state }) => {
      if (!state.outline) return null;

      return (
        <div>
          <h3>Research Progress: {state.progress}%</h3>
          <p>Current: {state.currentStep}</p>
          <ul>
            {state.outline.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      );
    }
  });

  return <div>Research Assistant</div>;
}
```

### 3.5 useCopilotAction Hook

**File**: `CopilotKit/packages/react-core/src/hooks/use-copilot-action.ts`

Define actions the AI can execute.

#### 3.5.1 Simple Action

```tsx
import { useCopilotAction } from "@copilotkit/react-core";

useCopilotAction({
  name: "sayHello",
  description: "Say hello to someone",
  parameters: [
    {
      name: "name",
      type: "string",
      description: "Name of the person",
      required: true
    }
  ],
  handler: async ({ name }) => {
    alert(`Hello, ${name}!`);
  }
});
```

#### 3.5.2 Complex Parameters

```tsx
useCopilotAction({
  name: "createTask",
  parameters: [
    {
      name: "title",
      type: "string",
      required: true
    },
    {
      name: "priority",
      type: "string",
      enum: ["low", "medium", "high"]
    },
    {
      name: "tags",
      type: "string[]"
    },
    {
      name: "metadata",
      type: "object",
      attributes: [
        { name: "category", type: "string" },
        { name: "dueDate", type: "string" }
      ]
    }
  ],
  handler: async ({ title, priority, tags, metadata }) => {
    await createTask({
      title,
      priority,
      tags,
      category: metadata.category,
      dueDate: metadata.dueDate
    });
  }
});
```

#### 3.5.3 Generative UI (render)

```tsx
useCopilotAction({
  name: "appendToSpreadsheet",
  description: "Append rows to spreadsheet",
  parameters: [
    {
      name: "rows",
      type: "object[]",
      attributes: [
        {
          name: "cells",
          type: "object[]",
          attributes: [
            { name: "value", type: "string" }
          ]
        }
      ]
    }
  ],
  render: ({ status, args }) => {
    if (status === "executing") {
      return <Spinner />;
    }
    return <Spreadsheet data={args.rows} />;
  },
  handler: ({ rows }) => {
    setSpreadsheet(prev => ({
      ...prev,
      rows: [...prev.rows, ...rows]
    }));
  }
});
```

#### 3.5.4 Approval Workflow (renderAndWaitForResponse)

```tsx
useCopilotAction({
  name: "sendEmail",
  description: "Send an email (requires approval)",
  parameters: [
    {
      name: "to",
      type: "string",
      required: true
    },
    {
      name: "subject",
      type: "string"
    },
    {
      name: "body",
      type: "string"
    }
  ],
  renderAndWaitForResponse: ({ args, status, respond }) => {
    return (
      <EmailApproval
        to={args.to}
        subject={args.subject}
        body={args.body}
        isExecuting={status === "executing"}
        onApprove={() => respond?.({
          approved: true,
          metadata: { sentAt: new Date().toISOString() }
        })}
        onReject={() => respond?.({ approved: false })}
      />
    );
  }
});
```

**Status Values**:
- `"inProgress"` - Action is being prepared
- `"executing"` - Waiting for user response
- `"complete"` - Action completed

#### 3.5.5 Remote Actions

```tsx
// Frontend only defines the UI, backend implements handler
useCopilotAction({
  name: "AskHuman",
  available: "remote",  // Implemented on backend
  parameters: [
    {
      name: "question",
      type: "string"
    }
  ],
  handler: async ({ question }) => {
    return window.prompt(question);
  }
});
```

#### 3.5.6 Catch-All Action

```tsx
// Render actions not defined in frontend
useCopilotAction({
  name: "*",
  render: ({ name, args, status, result }) => {
    return (
      <div>
        <h4>Action: {name}</h4>
        <pre>{JSON.stringify(args, null, 2)}</pre>
        {status === "complete" && <p>Result: {result}</p>}
      </div>
    );
  }
});
```

### 3.6 useCopilotChat Hook

**File**: `CopilotKit/packages/react-core/src/hooks/use-copilot-chat.ts`

Headless chat functionality.

```tsx
import { useCopilotChat } from "@copilotkit/react-core";

function CustomChat() {
  const {
    visibleMessages,      // Messages to display
    appendMessage,        // Add message
    setMessages,          // Set all messages
    deleteMessage,        // Remove message
    reloadMessages,       // Reload from ID
    stopGeneration,       // Stop current generation
    isLoading             // Loading state
  } = useCopilotChat();

  return (
    <div>
      {visibleMessages.map(msg => (
        <div key={msg.id}>
          <strong>{msg.role}:</strong> {msg.content}
        </div>
      ))}
      <button onClick={() => appendMessage({
        id: randomId(),
        role: "user",
        content: "Hello"
      })}>
        Send
      </button>
    </div>
  );
}
```

### 3.7 useLangGraphInterrupt Hook

**File**: `CopilotKit/packages/react-core/src/hooks/use-langgraph-interrupt.ts`

Handle LangGraph interrupts (human-in-the-loop).

```tsx
import { useLangGraphInterrupt } from "@copilotkit/react-core";

useLangGraphInterrupt({
  render: ({ value, respond }) => {
    const question = JSON.parse(value);

    return (
      <InterruptDialog
        question={question.text}
        onRespond={(answer) => {
          respond(JSON.stringify({ answer }));
        }}
      />
    );
  }
});
```

### 3.8 CopilotChat Component

**File**: `CopilotKit/packages/react-ui/src/components/chat/`

Pre-built chat UI component.

```tsx
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

function App() {
  return (
    <CopilotChat
      instructions="You are a helpful assistant."
      labels={{
        title: "AI Assistant",
        initial: "How can I help you?"
      }}
      makeSystemMessage={(context) =>
        `Current page: ${context.documentTitle}`
      }
      onSubmitMessage={(message) => {
        console.log("User said:", message);
      }}
      icons={{
        openIcon: <CustomIcon />,
        closeIcon: <CustomIcon />
      }}
    />
  );
}
```

**Props**:
- `instructions`: System prompt
- `labels`: UI text customization
- `makeSystemMessage`: Dynamic system message function
- `onSubmitMessage`: Message submission callback
- `icons`: Custom icon components
- `className`: CSS class names
- `hitl`: Human-in-the-loop configuration

### 3.9 CopilotPopup Component

```tsx
import { CopilotPopup } from "@copilotkit/react-ui";

function App() {
  return (
    <CopilotPopup
      defaultOpen={true}
      clickOutsideToClose={false}
      labels={{
        title: "Help",
        initial: "Need assistance?"
      }}
    />
  );
}
```

---

## 4. Runtime (Next.js Integration)

### 4.1 CopilotRuntime

**File**: `CopilotKit/packages/runtime/src/runtime.ts`

```tsx
// app/api/copilotkit/route.ts
import { NextRequest } from "next/server";
import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import OpenAI from "openai";

const openai = new OpenAI();
const serviceAdapter = new OpenAIAdapter({ openai });

const runtime = new CopilotRuntime({
  remoteEndpoints: [
    {
      url: process.env.REMOTE_ACTION_URL || "http://localhost:8000/copilotkit",
    },
  ],
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
```

### 4.2 Service Adapters

```tsx
// OpenAI
import { OpenAIAdapter } from "@copilotkit/runtime";
const adapter = new OpenAIAdapter({
  openai,
  model: "gpt-4o"
});

// Anthropic
import { AnthropicAdapter } from "@copilotkit/runtime";
const adapter = new AnthropicAdapter({
  anthropic,
  model: "claude-3-5-sonnet-20241022"
});

// Google Gemini
import { GoogleGenerativeAIAdapter } from "@copilotkit/runtime";
const adapter = new GoogleGenerativeAIAdapter({
  model: "gemini-1.5-pro"
});
```

---

## 5. Multi-Agent Coordination

### 5.1 Multiple Agents in Frontend

```tsx
import { useCoAgent } from "@copilotkit/react-core";

function Dashboard() {
  // Research agent
  const research = useCoAgent({
    name: "research_agent",
    initialState: { query: "", results: [] }
  });

  // Email agent
  const email = useCoAgent({
    name: "email_agent",
    initialState: { drafts: [] }
  });

  // Data agent
  const data = useCoAgent({
    name: "data_agent",
    initialState: { charts: [] }
  });

  return (
    <div>
      <ResearchPanel agent={research} />
      <EmailPanel agent={email} />
      <DataPanel agent={data} />
    </div>
  );
}
```

### 5.2 Multiple Agents in Backend

```python
from copilotkit import CopilotKitRemoteEndpoint, LangGraphAGUIAgent

sdk = CopilotKitRemoteEndpoint(
    agents=[
        LangGraphAGUIAgent(
            name="research_agent",
            description="Research and analysis",
            graph=research_graph
        ),
        LangGraphAGUIAgent(
            name="email_agent",
            description="Email composition",
            graph=email_graph
        ),
        LangGraphAGUIAgent(
            name="data_agent",
            description="Data visualization",
            graph=data_graph
        )
    ]
)
```

### 5.3 Agent-to-Agent Communication

Agents communicate via shared state in CopilotKit context:

```python
# Agent 1: Research Agent
def research_node(state, config):
    results = perform_research(state["query"])

    # Store in copilotkit context
    state["copilotkit"]["research_results"] = results

    return state

# Agent 2: Email Agent (can access research results)
def email_node(state, config):
    # Access results from research agent
    research_data = state.get("copilotkit", {}).get("research_results", [])

    email_draft = compose_email(research_data)
    return {"draft": email_draft}
```

---

## 6. Production Deployment

### 6.1 Environment Variables

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Remote agent endpoint
REMOTE_ACTION_URL=http://localhost:8000/copilotkit

# Copilot Cloud (optional)
COPILOT_CLOUD_API_KEY=ck_...
```

### 6.2 Docker Deployment

**Dockerfile** (Python Backend):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

**requirements.txt**:
```
copilotkit
fastapi
uvicorn[standard]
langchain
langchain-openai
langgraph
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  frontend:
    build: ./ui
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_COPILOT_URL=http://localhost:3000/api/copilotkit
      - REMOTE_ACTION_URL=http://backend:8000/copilotkit
    depends_on:
      - backend

  backend:
    build: ./agent
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

### 6.3 Vercel Deployment

**vercel.json**:
```json
{
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "env": {
    "OPENAI_API_KEY": "@openai-api-key",
    "REMOTE_ACTION_URL": "@remote-action-url"
  }
}
```

**Next.js Configuration**:
```ts
// next.config.js
module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/copilotkit/:path*',
        destination: '/api/copilotkit/:path*',
      },
    ];
  },
};
```

### 6.4 Error Handling & Retry Logic

**Backend** (from `sdk-python/copilotkit/exc.py`):
```python
from copilotkit.exc import (
    ActionNotFoundException,
    ActionExecutionException,
    AgentNotFoundException,
    AgentExecutionException
)

# Exceptions are caught in FastAPI handler
try:
    result = await sdk.execute_action(...)
    return JSONResponse(content=jsonable_encoder(result))
except ActionNotFoundException as exc:
    logger.error("Action not found: %s", exc)
    return JSONResponse(content={"error": str(exc)}, status_code=404)
except ActionExecutionException as exc:
    logger.error("Action execution error: %s", exc)
    return JSONResponse(content={"error": str(exc)}, status_code=500)
```

**Frontend**:
```tsx
import { CopilotKit } from "@copilotkit/react-core";

function App() {
  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      onError={(error) => {
        console.error("CopilotKit error:", error);
        // Show user-friendly error
        toast.error("AI assistant encountered an error");
      }}
    >
      <YourApp />
    </CopilotKit>
  );
}
```

**Retry Logic** (Agent Execution):
```tsx
const { run } = useCoAgent({
  name: "my-agent",
  initialState: {}
});

async function retryAgent(maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      await run();
      break;
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}
```

### 6.5 Token & Cost Tracking

**Backend Integration**:
```python
from copilotkit import CopilotKitRemoteEndpoint

class TokenTracker:
    def __init__(self):
        self.total_tokens = 0
        self.total_cost = 0

    def track(self, usage):
        self.total_tokens += usage.total_tokens
        self.total_cost += calculate_cost(usage)

tracker = TokenTracker()

def action_handler_with_tracking(**kwargs):
    result = process_action(**kwargs)

    # Track usage
    if hasattr(result, "usage"):
        tracker.track(result.usage)

    return result

sdk = CopilotKitRemoteEndpoint(
    actions=[
        Action(
            name="tracked_action",
            handler=action_handler_with_tracking
        )
    ]
)
```

**LangGraph Callback**:
```python
from langchain.callbacks import get_openai_callback

def call_model(state, config):
    with get_openai_callback() as cb:
        response = model.invoke(state["messages"], config)

        # Log token usage
        print(f"Tokens: {cb.total_tokens}, Cost: ${cb.total_cost}")

    return {"messages": [response]}
```

---

## 7. Complete Example: Research Assistant

### 7.1 Backend (Python + LangGraph)

**state.py**:
```python
from typing import TypedDict, List

class AgentState(TypedDict):
    messages: List
    query: str
    outline: List[str]
    research_results: List[dict]
    summary: str
```

**agent.py**:
```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from copilotkit.langgraph import copilotkit_emit_state

model = ChatOpenAI(model="gpt-4o")

@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # Implement actual search
    return f"Results for: {query}"

# Nodes
def create_outline(state, config):
    """Create research outline"""
    response = model.invoke([
        SystemMessage(content="Create a research outline"),
        HumanMessage(content=state["query"])
    ])

    outline = parse_outline(response.content)

    # Emit state for frontend
    copilotkit_emit_state(config, {
        "outline": outline,
        "progress": 25
    })

    return {"outline": outline}

def research_topics(state, config):
    """Research each topic"""
    results = []
    total = len(state["outline"])

    for i, topic in enumerate(state["outline"]):
        result = search_web.invoke({"query": topic})
        results.append(result)

        # Stream progress
        copilotkit_emit_state(config, {
            "research_results": results,
            "progress": 25 + (50 * (i + 1) / total)
        })

    return {"research_results": results}

def summarize(state, config):
    """Create final summary"""
    response = model.invoke([
        SystemMessage(content="Summarize research results"),
        HumanMessage(content=str(state["research_results"]))
    ])

    copilotkit_emit_state(config, {
        "summary": response.content,
        "progress": 100
    })

    return {"summary": response.content}

# Build graph
workflow = StateGraph(AgentState)
workflow.add_node("outline", create_outline)
workflow.add_node("research", research_topics)
workflow.add_node("summarize", summarize)

workflow.set_entry_point("outline")
workflow.add_edge("outline", "research")
workflow.add_edge("research", "summarize")
workflow.add_edge("summarize", END)

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
```

**server.py**:
```python
from fastapi import FastAPI
import uvicorn
from copilotkit import CopilotKitRemoteEndpoint, LangGraphAGUIAgent
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from agent import graph

app = FastAPI()

sdk = CopilotKitRemoteEndpoint(
    agents=[
        LangGraphAGUIAgent(
            name="research_agent",
            description="AI research assistant",
            graph=graph
        )
    ]
)

add_fastapi_endpoint(app, sdk, "/copilotkit")

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
```

### 7.2 Frontend (React + Next.js)

**app/api/copilotkit/route.ts**:
```tsx
import { NextRequest } from "next/server";
import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import OpenAI from "openai";

const openai = new OpenAI();
const serviceAdapter = new OpenAIAdapter({ openai });

const runtime = new CopilotRuntime({
  remoteEndpoints: [
    {
      url: process.env.REMOTE_ACTION_URL || "http://localhost:8000/copilotkit",
    },
  ],
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
```

**app/research/page.tsx**:
```tsx
"use client";

import { useCoAgent, useCoAgentStateRender } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

type ResearchState = {
  query: string;
  outline: string[];
  research_results: Array<{ topic: string; content: string }>;
  summary: string;
  progress: number;
};

function ResearchAssistant() {
  const { state, setState, running } = useCoAgent<ResearchState>({
    name: "research_agent",
    initialState: {
      query: "",
      outline: [],
      research_results: [],
      summary: "",
      progress: 0
    }
  });

  useCoAgentStateRender<ResearchState>({
    name: "research_agent",
    render: ({ state }) => {
      if (!state.outline || state.outline.length === 0) return null;

      return (
        <div className="research-progress">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${state.progress}%` }}
            />
          </div>

          <h3>Research Outline</h3>
          <ul>
            {state.outline.map((topic, i) => (
              <li key={i} className={
                i < state.research_results.length ? "completed" : ""
              }>
                {topic}
              </li>
            ))}
          </ul>

          {state.summary && (
            <div className="summary">
              <h3>Summary</h3>
              <p>{state.summary}</p>
            </div>
          )}
        </div>
      );
    }
  });

  return (
    <div className="container">
      <h1>AI Research Assistant</h1>

      <div className="research-ui">
        <input
          type="text"
          value={state.query}
          onChange={(e) => setState({ query: e.target.value })}
          placeholder="Enter research topic..."
          disabled={running}
        />
      </div>

      <CopilotChat
        instructions="You are an AI research assistant. Help users research topics thoroughly."
        labels={{
          title: "Research Assistant",
          initial: "What would you like to research?"
        }}
      />
    </div>
  );
}

export default ResearchAssistant;
```

**app/layout.tsx**:
```tsx
import { CopilotKit } from "@copilotkit/react-core";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <CopilotKit
          runtimeUrl="/api/copilotkit"
          agent="research_agent"
        >
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
```

---

## 8. Key Patterns & Best Practices

### 8.1 State Management

**Use External State for Complex UIs**:
```tsx
// Redux/Zustand integration
const agentState = useSelector(state => state.agent);
const dispatch = useDispatch();

useCoAgent({
  name: "my-agent",
  state: agentState,
  setState: (newState) => dispatch(setAgentState(newState))
});
```

### 8.2 Error Boundaries

```tsx
import { ErrorBoundary } from "@copilotkit/react-core";

function App() {
  return (
    <ErrorBoundary
      fallback={<ErrorMessage />}
      onError={(error) => {
        console.error(error);
        reportToSentry(error);
      }}
    >
      <CopilotKit>
        <YourApp />
      </CopilotKit>
    </ErrorBoundary>
  );
}
```

### 8.3 Testing

**Frontend**:
```tsx
import { render, screen } from "@testing-library/react";
import { CopilotKit } from "@copilotkit/react-core";

test("renders agent UI", () => {
  render(
    <CopilotKit runtimeUrl="/api/copilotkit">
      <MyComponent />
    </CopilotKit>
  );

  expect(screen.getByText("AI Assistant")).toBeInTheDocument();
});
```

**Backend**:
```python
import pytest
from copilotkit import CopilotKitRemoteEndpoint, Action

def test_action_execution():
    sdk = CopilotKitRemoteEndpoint(
        actions=[
            Action(
                name="test_action",
                handler=lambda x: x * 2
            )
        ]
    )

    context = {"properties": {}, "headers": {}}
    result = await sdk.execute_action(
        context=context,
        name="test_action",
        arguments={"x": 5}
    )

    assert result["result"] == 10
```

### 8.4 Security

**Validate Context Properties**:
```python
sdk = CopilotKitRemoteEndpoint(
    agents=lambda context: (
        [admin_agent]
        if verify_token(context["properties"]["token"])
        else []
    )
)
```

**Rate Limiting** (FastAPI):
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/copilotkit/{path:path}")
@limiter.limit("10/minute")
async def copilotkit_endpoint(request: Request):
    return await handler(request, sdk)
```

---

## 9. Implementation Checklist for Our Project

### Phase 1: Backend Integration
- [ ] Install `copilotkit` package
- [ ] Create `LangGraphAGUIAgent` wrapper for Claude agent
- [ ] Implement `add_fastapi_endpoint` in FastAPI app
- [ ] Add error handling and logging
- [ ] Test agent execution endpoint

### Phase 2: Frontend Setup
- [ ] Install `@copilotkit/react-core`, `@copilotkit/react-ui`
- [ ] Setup `CopilotKit` provider
- [ ] Create Next.js API route with `CopilotRuntime`
- [ ] Configure Anthropic adapter

### Phase 3: Agent Integration
- [ ] Implement `useCoAgent` for account analysis state
- [ ] Create `useCoAgentStateRender` for real-time insights
- [ ] Add approval workflows with `renderAndWaitForResponse`
- [ ] Implement multi-agent coordination

### Phase 4: Production
- [ ] Add error boundaries
- [ ] Implement retry logic
- [ ] Setup token tracking
- [ ] Configure environment variables
- [ ] Docker deployment setup

---

## 10. Resources

- **Documentation**: https://docs.copilotkit.ai
- **GitHub**: https://github.com/CopilotKit/CopilotKit
- **Discord**: https://discord.gg/6dffbvGU3D
- **Examples**: https://github.com/CopilotKit/CopilotKit/tree/main/examples
- **AG-UI Protocol**: https://github.com/ag-ui-protocol/ag-ui

---

*Research completed: 2025-10-19*
*CopilotKit Version: v1.10.6*
*Commit: ba1dc6d80535c7c18542b2d147619c3977ce48aa*
