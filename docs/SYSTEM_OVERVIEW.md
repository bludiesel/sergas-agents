# System Overview - Sergas Super Account Manager

**Version:** 1.0.0
**Last Updated:** 2025-10-19
**Document Type:** Technical Architecture Overview

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [High-Level Architecture](#high-level-architecture)
3. [Three-Layer Architecture](#three-layer-architecture)
4. [Component Responsibilities](#component-responsibilities)
5. [Data Flow Diagrams](#data-flow-diagrams)
6. [Technology Stack](#technology-stack)
7. [Integration Points](#integration-points)

---

## Executive Summary

The Sergas Super Account Manager is an AI-powered system that automates CRM account management through intelligent multi-agent orchestration. It reduces account review time by 60% while maintaining human-in-the-loop safety controls.

### Key Capabilities

- **Automated Monitoring**: Real-time detection of account changes and risk factors
- **Intelligent Analysis**: Historical context synthesis using knowledge graphs
- **Smart Recommendations**: AI-generated actionable insights with confidence scoring
- **Human Control**: All CRM modifications require explicit approval
- **Enterprise Security**: Zero-trust architecture with comprehensive audit trails

### Business Impact

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Account Review Time | 8+ minutes | <3 minutes | 60% reduction |
| Proactive Alerts | Manual | Automatic | 100% coverage |
| Context Retrieval | 5 minutes | Instant | 95% faster |
| Audit Trail | Partial | Complete | 100% visibility |
| User Adoption | N/A | Target 80% | New capability |

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                          │
│                                                                 │
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │   Web UI         │              │   CLI Interface  │        │
│  │  (CopilotKit)    │              │   (Python)       │        │
│  │  - React         │              │   - Click        │        │
│  │  - TypeScript    │              │   - Rich         │        │
│  └─────────┬────────┘              └─────────┬────────┘        │
│            │                                  │                 │
└────────────┼──────────────────────────────────┼─────────────────┘
             │                                  │
             │  AG UI Protocol (SSE)            │  Direct API
             │                                  │
┌────────────▼──────────────────────────────────▼─────────────────┐
│                   APPLICATION LAYER                              │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI Backend                                          │  │
│  │  • /copilotkit endpoint (SSE streaming)                   │  │
│  │  • /approval/respond (approval workflow)                  │  │
│  │  • /health (service status)                               │  │
│  │  • CORS middleware, JWT auth, rate limiting               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  AG UI Protocol Bridge                                    │  │
│  │  • Event emitter (16 event types)                         │  │
│  │  • SSE encoder                                            │  │
│  │  • State synchronization                                  │  │
│  │  • Approval coordination                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────┬────────────────────────────────────────────────────┘
             │
             │  Agent Orchestration
             │
┌────────────▼────────────────────────────────────────────────────┐
│              ORCHESTRATION LAYER                                 │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  OrchestratorAgent                                        │  │
│  │  • Workflow coordination                                  │  │
│  │  • Subagent delegation                                    │  │
│  │  │  • Approval gates                                       │  │
│  │  • Session management                                     │  │
│  └─────────┬────────────────────────────────────────────────┘  │
│            │                                                    │
│  ┌─────────┼────────────────────────────────────────────────┐  │
│  │         ▼                                                 │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐ │  │
│  │  │ ZohoDataScout│  │ MemoryAnalyst│  │ Recommendation │ │  │
│  │  │              │  │              │  │ Author         │ │  │
│  │  │ • CRM data   │  │ • Historical │  │ • Generate     │ │  │
│  │  │   retrieval  │  │   context    │  │   insights     │ │  │
│  │  │ • Change     │  │ • Pattern    │  │ • Confidence   │ │  │
│  │  │   detection  │  │   analysis   │  │   scoring      │ │  │
│  │  └──────┬───────┘  └──────┬───────┘  └────────┬───────┘ │  │
│  │         │                  │                   │         │  │
│  └─────────┼──────────────────┼───────────────────┼─────────┘  │
│            │                  │                   │             │
└────────────┼──────────────────┼───────────────────┼─────────────┘
             │                  │                   │
             │  Tool Calls      │  Memory Queries   │  Recommendations
             │                  │                   │
┌────────────▼──────────────────▼───────────────────▼─────────────┐
│                   INTEGRATION LAYER                              │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  Zoho MCP        │  │  Cognee MCP      │  │  Claude SDK  │ │
│  │  Server          │  │  Server          │  │  Client      │ │
│  │  • Primary       │  │  • Knowledge     │  │  • LLM calls │ │
│  │    CRM access    │  │    graph         │  │  • Streaming │ │
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬───────┘ │
│           │                     │                     │         │
└───────────┼─────────────────────┼─────────────────────┼─────────┘
            │                     │                     │
            │  API Calls          │  GraphQL/REST       │  HTTPS
            │                     │                     │
┌───────────▼─────────────────────▼─────────────────────▼─────────┐
│                      DATA LAYER                                  │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  Zoho CRM API    │  │  Cognee System   │  │  PostgreSQL  │ │
│  │  • Accounts      │  │  • Knowledge     │  │  • Audit     │ │
│  │  • Contacts      │  │    graph         │  │    logs      │ │
│  │  • Deals         │  │  • Vector DB     │  │  • Sessions  │ │
│  │  • Activities    │  │    (Qdrant)      │  │  • Metrics   │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Three-Layer Architecture

### Layer 1: Presentation (CopilotKit UI)

**Purpose**: Professional user interface with pre-built components

**Components:**
- React/Next.js application
- CopilotKit UI components
- Real-time event rendering
- Approval workflow interface
- Tool call visualization

**Key Features:**
- Server-Sent Events (SSE) for real-time updates
- Automatic reconnection handling
- State persistence across page reloads
- Responsive design for mobile/desktop

**Benefits:**
- Saves 4-8 weeks of frontend development
- Professional, battle-tested components
- Built-in generative UI support
- Tool visualization out-of-the-box

### Layer 2: Protocol Bridge (AG UI Protocol)

**Purpose**: Open standard for agent-frontend communication

**Components:**
- FastAPI SSE endpoint (`/copilotkit`)
- Event emitter (16 AG UI event types)
- SSE encoder (Server-Sent Events format)
- State synchronization manager
- Approval coordination system

**Key Features:**
- Framework-agnostic protocol
- Real-time event streaming
- Bidirectional state sync
- Tool call transparency
- Human-in-the-loop approval

**Benefits:**
- No vendor lock-in
- Works with any backend
- Industry standard (CopilotKit, LangGraph, CrewAI)
- Simple HTTP/SSE transport

### Layer 3: Orchestration (Claude Agent SDK)

**Purpose**: Multi-agent coordination and business logic

**Components:**
- OrchestratorAgent (main coordinator)
- Specialist agents (Scout, Analyst, Author)
- Claude SDK client integration
- Hook system (audit, metrics, permissions)
- Three-tier Zoho integration

**Key Features:**
- Multi-agent orchestration
- MCP server integration
- Tool execution with permissions
- Session and state management
- Comprehensive logging

**Benefits:**
- Full control over agent behavior
- Existing investment protected
- Perfect for multi-agent workflows
- Native MCP support

---

## Component Responsibilities

### Frontend Components

#### CopilotChat Component
```typescript
// Responsibilities:
// - Render chat interface
// - Handle user input
// - Display streaming responses
// - Manage conversation state

<CopilotChat
  labels={{ title: "Account Analysis Agent" }}
  makeSystemMessage={customEventRenderer}
/>
```

#### ApprovalModal Component
```typescript
// Responsibilities:
// - Display pending approvals
// - Collect user decision
// - Support modification workflow
// - Handle timeout warnings

<ApprovalModal
  request={approvalRequest}
  onApprove={handleApprove}
  onReject={handleReject}
/>
```

#### ToolCallCard Component
```typescript
// Responsibilities:
// - Visualize tool executions
// - Show input/output data
// - Indicate success/failure
// - Provide debugging information

<ToolCallCard
  toolCall={toolCallData}
  expandable={true}
/>
```

### Backend Components

#### FastAPI Application
```python
# Responsibilities:
# - HTTP server
# - CORS configuration
# - Authentication middleware
# - Rate limiting
# - Health checks

app = FastAPI(title="Sergas Account Manager")
app.add_middleware(CORSMiddleware, ...)
```

#### AG UI Event Emitter
```python
# Responsibilities:
# - Generate AG UI events
# - Maintain event sequence
# - Handle timestamps
# - Support all 16 event types

class AGUIEventEmitter:
    def emit_run_started(self) -> Dict[str, Any]: ...
    def emit_text_message_content(self, ...): ...
    def emit_tool_call_start(self, ...): ...
```

#### Approval Manager
```python
# Responsibilities:
# - Track pending approvals
# - Coordinate request/response
# - Handle timeouts
# - Store approval history

class ApprovalManager:
    async def request_approval(self, run_id, data, timeout): ...
    def respond_to_approval(self, run_id, response): ...
```

### Agent Components

#### OrchestratorAgent
```python
# Responsibilities:
# - Coordinate specialist agents
# - Manage workflow execution
# - Handle approval gates
# - Aggregate results
# - Error recovery

class OrchestratorAgent(BaseAgent):
    async def execute_workflow(self, context): ...
```

#### ZohoDataScout
```python
# Responsibilities:
# - Retrieve CRM data
# - Detect changes
# - Map account owners
# - Three-tier integration fallback

class ZohoDataScout(BaseAgent):
    async def get_account(self, account_id): ...
```

#### MemoryAnalyst
```python
# Responsibilities:
# - Query knowledge graph
# - Identify patterns
# - Synthesize historical context
# - Relevance ranking

class MemoryAnalyst(BaseAgent):
    async def analyze_history(self, account_id): ...
```

#### RecommendationAuthor
```python
# Responsibilities:
# - Generate actionable insights
# - Calculate confidence scores
# - Apply templates
# - Priority ranking

class RecommendationAuthor(BaseAgent):
    async def create_recommendations(self, data, history): ...
```

---

## Data Flow Diagrams

### Request Flow: User → Backend

```
User Input
    ↓
┌──────────────────┐
│ CopilotChat UI   │
│ - Collect input  │
│ - Generate run_id│
└────────┬─────────┘
         │
         │ HTTP POST /copilotkit
         ▼
┌──────────────────┐
│ FastAPI Endpoint │
│ - Auth check     │
│ - Parse input    │
│ - Validate       │
└────────┬─────────┘
         │
         │ Initialize
         ▼
┌──────────────────┐
│ OrchestratorAgent│
│ - Create session │
│ - Start workflow │
└────────┬─────────┘
         │
         │ SSE stream begins
         ▼
```

### Response Flow: Backend → User

```
Agent Execution
    ↓
┌──────────────────┐
│ Generate Events  │
│ - RUN_STARTED    │
│ - TEXT_MESSAGE   │
│ - TOOL_CALL      │
│ - STATE_SNAPSHOT │
│ - APPROVAL_REQ   │
│ - RUN_FINISHED   │
└────────┬─────────┘
         │
         │ Encode to SSE
         ▼
┌──────────────────┐
│ EventEncoder     │
│ - to_sse()       │
│ - JSON serialize │
└────────┬─────────┘
         │
         │ Stream
         ▼
┌──────────────────┐
│ StreamingResponse│
│ - media_type:    │
│   event-stream   │
└────────┬─────────┘
         │
         │ SSE
         ▼
┌──────────────────┐
│ EventSource API  │
│ (Browser)        │
└────────┬─────────┘
         │
         │ Render
         ▼
┌──────────────────┐
│ CopilotChat UI   │
│ - Update state   │
│ - Show messages  │
│ - Display tools  │
└──────────────────┘
```

### Tool Execution Flow

```
Agent needs data
    ↓
┌──────────────────┐
│ TOOL_CALL_START  │
│ - tool_name      │
│ - tool_call_id   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ TOOL_CALL_ARGS   │
│ - args (JSON)    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Execute Tool     │
│ Tier 1: Zoho MCP │
│ Tier 2: Python SDK
│ Tier 3: REST API │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ TOOL_CALL_RESULT │
│ - result (data)  │
│ - error (if any) │
└────────┬─────────┘
         │
         ▼
Agent continues...
```

---

## Technology Stack

### Frontend

| Technology | Purpose | Version |
|------------|---------|---------|
| **Next.js** | React framework | 14.x |
| **TypeScript** | Type safety | 5.x |
| **CopilotKit** | AI UI components | 0.1.39+ |
| **TailwindCSS** | Styling | 3.x |
| **React Query** | Data fetching | 5.x |

### Backend

| Technology | Purpose | Version |
|------------|---------|---------|
| **Python** | Primary language | 3.14 |
| **FastAPI** | Web framework | 0.104+ |
| **Claude Agent SDK** | LLM orchestration | Latest |
| **Pydantic** | Data validation | 2.x |
| **Structlog** | Logging | 23.x |

### Integration

| Technology | Purpose | Version |
|------------|---------|---------|
| **AG UI Protocol** | Agent-UI standard | 0.1.0+ |
| **Zoho MCP Server** | CRM integration | Latest |
| **Cognee** | Knowledge graph | Latest |
| **PostgreSQL** | Primary database | 15.x |
| **Qdrant** | Vector database | 1.7+ |

### DevOps

| Technology | Purpose | Version |
|------------|---------|---------|
| **Docker** | Containerization | 24.x |
| **Kubernetes** | Orchestration | 1.28+ |
| **Prometheus** | Metrics | 2.x |
| **Grafana** | Visualization | 10.x |
| **GitHub Actions** | CI/CD | Latest |

---

## Integration Points

### Zoho CRM Integration (Three-Tier)

**Tier 1: Zoho MCP Server (Primary)**
```python
# Fastest, most reliable
# Direct MCP protocol
tools = ["zoho_get_account", "zoho_search_contacts", ...]
```

**Tier 2: Zoho Python SDK (Secondary)**
```python
# Fallback if MCP unavailable
from zcrmsdk import ZCRMRestClient
client = ZCRMRestClient.get_instance()
```

**Tier 3: Zoho REST API (Tertiary)**
```python
# Final fallback
requests.get(
    "https://www.zohoapis.com/crm/v2/Accounts",
    headers={"Authorization": f"Bearer {token}"}
)
```

### Cognee Knowledge Graph

**GraphQL API:**
```graphql
query GetAccountHistory($accountId: String!) {
  accountHistory(id: $accountId) {
    interactions {
      date
      type
      outcome
    }
    patterns {
      name
      confidence
    }
  }
}
```

### Claude Agent SDK

**Streaming API:**
```python
async for chunk in client.query(task):
    if chunk["type"] == "text":
        content = chunk["content"]
    elif chunk["type"] == "tool_use":
        tool_call = chunk
```

---

**Document Revision History:**

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-19 | Initial system overview |

**Related Documents:**
- [Master SPARC Plan V3](MASTER_SPARC_PLAN_V3.md)
- [AG UI Protocol Research](research/AG_UI_PROTOCOL_Complete_Research.md)
- [Claude SDK Integration](integrations/CLAUDE_SDK_AG_UI_Integration_Guide.md)
