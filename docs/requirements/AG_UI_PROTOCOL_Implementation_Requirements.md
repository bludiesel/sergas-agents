# Implementation Requirements Document
## Sergas Super Account Manager - AG UI Protocol & CopilotKit Integration

**Project**: Sergas Super Account Manager
**Date**: 2025-10-19
**Version**: 1.0
**Status**: Complete Implementation Checklist

---

## Executive Summary

This document extracts all implementation requirements from AG UI Protocol and CopilotKit research for the Sergas Super Account Manager project. Based on comprehensive analysis, **AG UI Protocol (direct implementation)** is recommended over CopilotKit due to superior architecture alignment (93% vs 27.5%).

**Key Decision**: Use AG UI Protocol directly with existing FastAPI + Claude Agent SDK stack. CopilotKit avoided due to:
- React framework lock-in (project has no frontend specified)
- LangGraph paradigm mismatch with Claude Agent SDK
- 12-19 week integration effort vs 2-3 weeks for AG UI Protocol
- Multi-layer state synchronization complexity

---

## 1. Dependencies & Versions

### 1.1 Python Backend Dependencies

#### Core Framework (Already in requirements.txt)
```txt
# Python Version
python>=3.14

# Claude Agent SDK
claude-agent-sdk>=0.1.4

# FastAPI & Web Framework
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6

# Async HTTP
aiohttp>=3.9.0
httpx>=0.25.0
```

#### AG UI Protocol (NEW - ADD TO requirements.txt)
```txt
# AG UI Protocol Support
ag-ui-protocol>=0.1.0  # Official Python SDK
pydantic>=2.5.0  # Already present - for event schema validation
```

#### SSE/WebSocket Support (Already Present)
```txt
# Real-time Streaming
sse-starlette>=1.6.5  # Server-Sent Events for FastAPI
python-socketio>=5.10.0  # Optional: WebSocket fallback
```

#### State Management (Already Present)
```txt
# Database
sqlalchemy>=2.0.23
alembic>=1.12.1
asyncpg>=0.29.0  # PostgreSQL async driver
redis>=5.0.1  # Caching

# Memory Layer
cognee>=0.3.0
lancedb>=0.3.0
```

### 1.2 Frontend Dependencies (If Building Web UI)

**Note**: Frontend is **optional** since AG UI Protocol is framework-agnostic.

#### Option A: React (If Needed)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@mui/material": "^5.14.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "axios": "^1.6.0",
    "date-fns": "^2.30.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.2.0",
    "vite": "^5.0.0"
  }
}
```

**Do NOT Install CopilotKit** (not recommended):
```json
// ❌ AVOID - Not aligned with architecture
{
  "@copilotkit/react-core": "^1.0.0",
  "@copilotkit/react-ui": "^1.0.0",
  "@copilotkit/runtime": "^1.0.0"
}
```

#### Option B: Vue/Svelte/Plain JS
AG UI Protocol works with **any framework** - no specific dependencies required beyond standard HTTP client.

### 1.3 System Requirements

```yaml
# Development Environment
OS: macOS/Linux/WSL2
Python: 3.14+
Node.js: 18+ (if building frontend)
Docker: 24+ (for Cognee, Redis, PostgreSQL)

# Production Environment
CPU: 2+ cores
RAM: 4GB minimum (8GB recommended)
Storage: 20GB (10GB for database, 10GB for logs/cache)
Network: Stable connection to Zoho CRM API
```

### 1.4 Environment Variables

```bash
# .env file structure

# ===================================
# Anthropic Claude
# ===================================
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929

# ===================================
# Zoho CRM Integration
# ===================================
# Tier 1: MCP Server
ZOHO_MCP_ENDPOINT=https://zoho-mcp2-900114980...
ZOHO_MCP_API_KEY=...

# Tier 2: Python SDK OAuth
ZOHO_CLIENT_ID=...
ZOHO_CLIENT_SECRET=...
ZOHO_REDIRECT_URI=http://localhost:8080/callback
ZOHO_REFRESH_TOKEN=...  # Generated during OAuth flow
ZOHO_ACCESS_TOKEN=...  # Auto-refreshed by SDK
ZOHO_DOMAIN=com  # or eu, in, com.au, jp
ZOHO_ENVIRONMENT=production  # or sandbox

# ===================================
# Cognee Memory Layer
# ===================================
COGNEE_API_KEY=...
COGNEE_ENDPOINT=http://localhost:8000  # or managed endpoint
COGNEE_MCP_ENDPOINT=...

# ===================================
# Database
# ===================================
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/sergas_agents
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis Cache
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# ===================================
# AG UI Protocol Configuration
# ===================================
AG_UI_STREAM_ENDPOINT=/api/agent/stream
AG_UI_APPROVAL_ENDPOINT=/api/approval/respond
AG_UI_SSE_KEEPALIVE=15  # seconds
AG_UI_MAX_EVENT_SIZE=10485760  # 10MB

# ===================================
# Security
# ===================================
JWT_SECRET_KEY=...  # Generate with: openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440  # 24 hours

# AWS Secrets Manager (Optional)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
SECRETS_MANAGER_NAME=sergas-agents-prod

# ===================================
# Monitoring
# ===================================
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
SENTRY_DSN=...  # Optional error tracking

# ===================================
# Application Settings
# ===================================
ENVIRONMENT=development  # or staging, production
DEBUG=true
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
MAX_CONCURRENT_AGENTS=10
AGENT_TIMEOUT_SECONDS=300
```

---

## 2. Configuration Requirements

### 2.1 FastAPI Application Setup

#### File: `src/api/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from src.api.routers import ag_ui_router, approval_router
from src.config import settings

# FastAPI app with AG UI Protocol support
app = FastAPI(
    title="Sergas Super Account Manager API",
    version="1.0.0",
    description="Multi-agent account management with AG UI Protocol",
)

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ag_ui_router.router, prefix="/api", tags=["AG UI"])
app.include_router(approval_router.router, prefix="/api", tags=["Approvals"])

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "protocol": "AG UI"}
```

### 2.2 AG UI Protocol Endpoint Configuration

#### File: `src/api/routers/ag_ui_router.py`
```python
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from src.events.ag_ui_emitter import AGUIEventEmitter
from src.agents.orchestrator import Orchestrator
import json

router = APIRouter()

@router.post("/agent/stream")
async def stream_agent_execution(request: Request):
    """
    Stream agent execution via AG UI Protocol (SSE)

    Request Body:
    {
        "account_id": "ACC-123",
        "workflow": "account_analysis"  # or "daily_review", "risk_assessment"
    }

    Response: Server-Sent Events (text/event-stream)
    """
    data = await request.json()
    account_id = data.get("account_id")
    workflow = data.get("workflow", "account_analysis")

    async def event_generator():
        """Generate AG UI Protocol events"""
        orchestrator = Orchestrator()
        emitter = AGUIEventEmitter()

        # Execute workflow with event streaming
        async for event in orchestrator.execute_with_events(
            workflow=workflow,
            account_id=account_id
        ):
            # Format as SSE
            event_data = json.dumps(event)
            yield f"data: {event_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
```

### 2.3 CORS Settings (Already Configured)

```python
# src/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # AG UI Protocol Settings
    ag_ui_stream_endpoint: str = "/api/agent/stream"
    ag_ui_approval_endpoint: str = "/api/approval/respond"
    ag_ui_sse_keepalive: int = 15  # seconds
    ag_ui_max_event_size: int = 10485760  # 10MB

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### 2.4 WebSocket Configuration (Optional Fallback)

```python
# src/api/websocket_handler.py (OPTIONAL)
from fastapi import WebSocket, WebSocketDisconnect
from src.agents.orchestrator import Orchestrator
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

# WebSocket endpoint
@app.websocket("/ws/agent/{account_id}")
async def websocket_endpoint(websocket: WebSocket, account_id: str):
    manager = WebSocketManager()
    await manager.connect(websocket)

    try:
        orchestrator = Orchestrator()
        async for event in orchestrator.execute_with_events("account_analysis", account_id):
            await websocket.send_json(event)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### 2.5 Environment-Specific Configs

```yaml
# config/development.yaml
environment: development
debug: true
log_level: DEBUG
database_pool_size: 5
max_concurrent_agents: 3

# config/production.yaml
environment: production
debug: false
log_level: INFO
database_pool_size: 20
max_concurrent_agents: 10
enable_metrics: true
```

---

## 3. Code Structure Requirements

### 3.1 Directory Organization

```
sergas_agents/
├── src/
│   ├── agents/                    # Agent implementations
│   │   ├── base_agent.py          # BaseAgent with AG UI event emission
│   │   ├── orchestrator.py        # Main orchestrator
│   │   ├── zoho_data_scout.py
│   │   ├── memory_analyst.py
│   │   └── recommendation_author.py
│   ├── api/                       # FastAPI routes
│   │   ├── main.py                # App entry point
│   │   ├── routers/
│   │   │   ├── ag_ui_router.py    # AG UI Protocol endpoints
│   │   │   ├── approval_router.py # Approval workflow endpoints
│   │   │   └── health_router.py
│   │   └── middleware/
│   │       ├── auth.py
│   │       └── rate_limit.py
│   ├── events/                    # AG UI Protocol event handling
│   │   ├── ag_ui_emitter.py       # Event formatter and emitter
│   │   ├── event_schemas.py       # Pydantic models for events
│   │   └── approval_manager.py    # Approval workflow state machine
│   ├── integrations/              # External service integrations
│   │   ├── zoho/
│   │   │   ├── mcp_client.py      # Tier 1: MCP integration
│   │   │   ├── sdk_client.py      # Tier 2: Python SDK
│   │   │   ├── rest_client.py     # Tier 3: REST fallback
│   │   │   └── integration_manager.py  # Three-tier router
│   │   └── cognee/
│   │       └── memory_client.py
│   ├── models/                    # Database models
│   │   ├── base.py
│   │   ├── audit_log.py
│   │   ├── recommendations.py
│   │   └── approvals.py
│   ├── config.py                  # Application configuration
│   └── utils/
│       ├── logging.py
│       └── retry.py
├── frontend/                      # Optional frontend (React/Vue/etc)
│   ├── src/
│   │   ├── components/
│   │   │   ├── ApprovalCard.tsx
│   │   │   ├── AgentMonitor.tsx
│   │   │   └── RecommendationList.tsx
│   │   ├── services/
│   │   │   └── ag_ui_client.ts    # EventSource wrapper
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
├── tests/
│   ├── unit/
│   │   ├── test_ag_ui_emitter.py
│   │   ├── test_approval_workflow.py
│   │   └── test_orchestrator.py
│   ├── integration/
│   │   └── test_ag_ui_stream.py
│   └── e2e/
│       └── test_approval_flow.py
├── migrations/                    # Alembic database migrations
├── docs/
│   ├── requirements/
│   │   └── implementation_requirements.md  # THIS FILE
│   ├── api/
│   │   └── ag_ui_protocol_spec.md
│   └── guides/
│       └── frontend_integration.md
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```

### 3.2 Module Dependencies Graph

```
┌─────────────────────────────────────────────────────┐
│                   main.py                           │
│              (FastAPI Application)                  │
└───────────────────┬─────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
┌───────▼──────┐    │    ┌──────▼──────┐
│ AG UI Router │    │    │ Approval    │
│              │    │    │ Router      │
└───────┬──────┘    │    └──────┬──────┘
        │           │           │
        └───────────┼───────────┘
                    │
        ┌───────────▼───────────┐
        │   Orchestrator        │
        │ (execute_with_events) │
        └───────────┬───────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
┌───────▼──────┐    │    ┌──────▼──────────┐
│ Zoho Data    │    │    │ Memory Analyst  │
│ Scout        │    │    │                 │
└───────┬──────┘    │    └──────┬──────────┘
        │           │           │
        └───────────┼───────────┘
                    │
        ┌───────────▼───────────┐
        │ Recommendation Author │
        └───────────┬───────────┘
                    │
        ┌───────────▼───────────┐
        │  AG UI Event Emitter  │
        └───────────┬───────────┘
                    │
        ┌───────────▼───────────┐
        │   SSE Stream Response │
        │   (to Frontend)       │
        └───────────────────────┘
```

### 3.3 Import Patterns

```python
# Standard library
import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Optional

# Third-party
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
import structlog

# Local absolute imports
from src.agents.base_agent import BaseAgent
from src.events.ag_ui_emitter import AGUIEventEmitter
from src.config import settings
from src.integrations.zoho.integration_manager import ZohoIntegrationManager
from src.models.recommendations import Recommendation
```

### 3.4 Naming Conventions

- **Files**: `snake_case.py` (e.g., `ag_ui_router.py`)
- **Classes**: `PascalCase` (e.g., `AGUIEventEmitter`)
- **Functions**: `snake_case` (e.g., `execute_with_events`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_CONCURRENT_AGENTS`)
- **Environment Variables**: `UPPER_SNAKE_CASE` (e.g., `ZOHO_CLIENT_ID`)
- **Event Types**: `lower_snake_case` (e.g., `agent_started`, `approval_required`)

---

## 4. API Requirements

### 4.1 REST Endpoints Needed

```python
# AG UI Protocol Endpoints
POST   /api/agent/stream           # Start agent execution (SSE response)
POST   /api/approval/respond       # Submit approval decision
GET    /api/agent/status/{id}      # Check agent status
GET    /api/recommendations/{id}   # Get recommendation details
GET    /api/audit-log              # Retrieve audit trail

# Health & Monitoring
GET    /health                     # Health check
GET    /metrics                    # Prometheus metrics
GET    /api/version                # API version info

# Admin (Optional)
POST   /api/admin/workflows/trigger  # Manual workflow trigger
GET    /api/admin/agents/list        # List active agents
POST   /api/admin/agents/stop/{id}   # Stop running agent
```

### 4.2 WebSocket Endpoints (Optional)

```python
# Real-time bidirectional communication
WS     /ws/agent/{account_id}      # WebSocket stream for agent execution
WS     /ws/approvals               # Real-time approval notifications
```

### 4.3 Request/Response Schemas

#### Agent Execution Request
```typescript
// POST /api/agent/stream
{
  "account_id": "ACC-123",
  "workflow": "account_analysis",  // or "daily_review", "risk_assessment"
  "options": {
    "include_history": true,
    "max_recommendations": 5,
    "confidence_threshold": 0.7
  }
}
```

#### AG UI Event Stream Response
```typescript
// SSE events (text/event-stream)
data: {"type": "workflow_started", "data": {"workflow": "account_analysis", "account_id": "ACC-123"}}

data: {"type": "agent_started", "data": {"agent": "zoho_scout", "step": 1}}

data: {"type": "agent_stream", "data": {"agent": "zoho_scout", "content": "Fetching account updates..."}}

data: {"type": "agent_completed", "data": {"agent": "zoho_scout", "step": 1, "duration_ms": 1234}}

data: {"type": "approval_required", "data": {"recommendation_id": "REC-456", "recommendation": {...}}}

data: {"type": "workflow_completed", "data": {"workflow": "account_analysis", "total_duration_ms": 5678}}
```

#### Approval Response Request
```typescript
// POST /api/approval/respond
{
  "recommendation_id": "REC-456",
  "action": "approve",  // or "reject", "modify"
  "modified_data": {  // optional, only if action="modify"
    "follow_up_date": "2025-10-25",
    "priority": "high"
  },
  "reason": "Account shows strong engagement signals"
}
```

#### Approval Response
```typescript
// 200 OK
{
  "status": "success",
  "recommendation_id": "REC-456",
  "action": "approve",
  "applied": true,
  "audit_log_id": "AUDIT-789"
}
```

### 4.4 Error Response Formats

```typescript
// 4xx/5xx errors
{
  "error": {
    "code": "AGENT_TIMEOUT",
    "message": "Agent execution exceeded 300 second timeout",
    "details": {
      "agent_id": "zoho_scout_12345",
      "duration_ms": 300000,
      "account_id": "ACC-123"
    },
    "timestamp": "2025-10-19T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

---

## 5. Frontend Requirements (Optional)

**Note**: Frontend is **completely optional** since AG UI Protocol is framework-agnostic. Can use CLI, Slack bot, or any HTTP client.

### 5.1 React Version Compatibility

```json
{
  "react": "^18.2.0",  // Minimum version
  "react-dom": "^18.2.0"
}
```

### 5.2 Required Components (If Building React UI)

```typescript
// src/components/AgentMonitor.tsx
export function AgentMonitor() {
  // Display real-time agent status
  // Shows: zoho_scout, memory_analyst, recommendation_author
  // Status: idle, running, completed, error
}

// src/components/ApprovalCard.tsx
export function ApprovalCard({ recommendation }) {
  // Display recommendation with approve/reject/modify actions
  // Inline editing for modification
  // Confidence badge
  // Rationale display
}

// src/components/RecommendationList.tsx
export function RecommendationList({ accountId }) {
  // List of recommendations for account
  // Filters: date, confidence, status
  // Pagination
}

// src/components/AuditLogTable.tsx
export function AuditLogTable() {
  // Display approval history
  // Export to CSV
  // Search and filter
}
```

### 5.3 Styling Approach

```typescript
// Option A: Material-UI (Recommended)
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Container } from '@mui/material';

const theme = createTheme({
  palette: {
    primary: { main: '#1976d2' },
    secondary: { main: '#dc004e' },
  },
});

// Option B: Tailwind CSS
// tailwind.config.js
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
};

// Option C: Plain CSS Modules
// Component.module.css with scoped styles
```

### 5.4 Build Configuration

```javascript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
```

---

## 6. Testing Requirements

### 6.1 Unit Test Patterns for AG UI Events

```python
# tests/unit/test_ag_ui_emitter.py
import pytest
from src.events.ag_ui_emitter import AGUIEventEmitter

@pytest.mark.asyncio
async def test_workflow_started_event():
    """Test workflow_started event formatting"""
    emitter = AGUIEventEmitter()
    event = emitter.format_workflow_started("account_analysis", "ACC-123")

    assert event["type"] == "workflow_started"
    assert event["data"]["workflow"] == "account_analysis"
    assert event["data"]["account_id"] == "ACC-123"
    assert "timestamp" in event["data"]

@pytest.mark.asyncio
async def test_agent_stream_event():
    """Test agent_stream event with content"""
    emitter = AGUIEventEmitter()
    event = emitter.format_agent_stream("zoho_scout", "Fetching account data...")

    assert event["type"] == "agent_stream"
    assert event["data"]["agent"] == "zoho_scout"
    assert event["data"]["content"] == "Fetching account data..."
```

### 6.2 Integration Test Setup

```python
# tests/integration/test_ag_ui_stream.py
import pytest
from httpx import AsyncClient
from src.api.main import app

@pytest.mark.asyncio
async def test_agent_stream_endpoint():
    """Test SSE stream from /api/agent/stream"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/agent/stream",
            json={"account_id": "ACC-123", "workflow": "account_analysis"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"

        # Read events
        events = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                event_data = json.loads(line[6:])
                events.append(event_data)

        # Verify event sequence
        assert events[0]["type"] == "workflow_started"
        assert any(e["type"] == "agent_started" for e in events)
        assert any(e["type"] == "agent_completed" for e in events)
        assert events[-1]["type"] == "workflow_completed"
```

### 6.3 E2E Test Requirements

```python
# tests/e2e/test_approval_flow.py
import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_full_approval_workflow():
    """
    End-to-end test: Agent execution → Approval → CRM update
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # 1. Navigate to dashboard
        await page.goto("http://localhost:5173")

        # 2. Trigger account analysis
        await page.click("#analyze-account-btn")

        # 3. Wait for recommendation
        await page.wait_for_selector(".approval-card")

        # 4. Click approve
        await page.click(".approve-btn")

        # 5. Verify success message
        success = await page.text_content(".success-message")
        assert "Recommendation approved" in success

        await browser.close()
```

### 6.4 Mock/Stub Patterns

```python
# tests/fixtures/ag_ui_fixtures.py
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator for testing"""
    async def mock_execute_with_events(workflow, account_id):
        yield {"type": "workflow_started", "data": {"workflow": workflow}}
        yield {"type": "agent_started", "data": {"agent": "zoho_scout"}}
        yield {"type": "agent_stream", "data": {"agent": "zoho_scout", "content": "Test"}}
        yield {"type": "agent_completed", "data": {"agent": "zoho_scout"}}
        yield {"type": "workflow_completed", "data": {"workflow": workflow}}

    orchestrator = AsyncMock()
    orchestrator.execute_with_events = mock_execute_with_events
    return orchestrator

@pytest.fixture
def mock_zoho_client():
    """Mock Zoho client for testing"""
    client = AsyncMock()
    client.get_account = AsyncMock(return_value={
        "id": "ACC-123",
        "name": "Acme Corp",
        "status": "Active"
    })
    return client
```

---

## 7. Deployment Requirements

### 7.1 Docker Configuration

#### Dockerfile
```dockerfile
# Dockerfile
FROM python:3.14-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini .

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD alembic upgrade head && uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/sergas
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
      - cognee
    volumes:
      - ./src:/app/src

  db:
    image: postgres:16
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=sergas
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  cognee:
    image: cognee/cognee:latest
    ports:
      - "8001:8000"
    environment:
      - COGNEE_DB_URL=postgresql://postgres:password@db:5432/cognee

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  postgres_data:
  redis_data:
  grafana_data:
```

### 7.2 Vercel/Hosting Setup (If Deploying Frontend)

```json
// vercel.json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/static-build",
      "config": { "distDir": "dist" }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "https://api.sergas-agents.com/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/frontend/$1"
    }
  ]
}
```

### 7.3 Environment Variables (Production)

```bash
# Production .env (AWS Secrets Manager or equivalent)
ANTHROPIC_API_KEY={{resolve:secretsmanager:sergas/anthropic:SecretString:api_key}}
ZOHO_CLIENT_ID={{resolve:secretsmanager:sergas/zoho:SecretString:client_id}}
ZOHO_CLIENT_SECRET={{resolve:secretsmanager:sergas/zoho:SecretString:client_secret}}
DATABASE_URL={{resolve:secretsmanager:sergas/database:SecretString:url}}
REDIS_URL={{resolve:secretsmanager:sergas/redis:SecretString:url}}
```

### 7.4 Secrets Management

```python
# src/config/secrets.py
import boto3
from botocore.exceptions import ClientError

class SecretsManager:
    def __init__(self, region_name="us-east-1"):
        self.client = boto3.client("secretsmanager", region_name=region_name)

    def get_secret(self, secret_name: str) -> dict:
        """Retrieve secret from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return json.loads(response["SecretString"])
        except ClientError as e:
            raise Exception(f"Failed to retrieve secret: {e}")

    def get_zoho_credentials(self) -> dict:
        """Get Zoho OAuth credentials"""
        return self.get_secret("sergas-agents/zoho")

    def get_database_credentials(self) -> dict:
        """Get database connection details"""
        return self.get_secret("sergas-agents/database")
```

---

## 8. Migration Path

### 8.1 From Current BaseAgent to AG UI Event Emission

#### Step 1: Update BaseAgent Class

**Before** (Current):
```python
# src/agents/base_agent.py
class BaseAgent:
    async def execute(self, task: str) -> str:
        """Execute task and return final result"""
        async for chunk in self.client.query(task):
            # Stream chunks internally
            pass
        return final_result
```

**After** (With AG UI Events):
```python
# src/agents/base_agent.py
from typing import AsyncGenerator, Dict, Any

class BaseAgent:
    async def execute(self, task: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute task and emit AG UI events"""
        # Emit agent start
        yield {
            "type": "agent_started",
            "data": {
                "agent": self.agent_id,
                "task": task,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        # Stream Claude SDK responses
        async for chunk in self.client.query(task):
            yield {
                "type": "agent_stream",
                "data": {
                    "agent": self.agent_id,
                    "content": chunk,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

        # Emit agent completion
        yield {
            "type": "agent_completed",
            "data": {
                "agent": self.agent_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
```

#### Step 2: Update Orchestrator

**Before**:
```python
async def execute(self, task: str) -> Recommendation:
    zoho_data = await self.zoho_scout.execute(task)
    memory_data = await self.memory_analyst.execute(zoho_data)
    recommendation = await self.recommendation_author.execute(memory_data)
    return recommendation
```

**After**:
```python
async def execute_with_events(self, workflow: str, account_id: str):
    """Execute with AG UI event streaming"""
    # Workflow start
    yield {"type": "workflow_started", "data": {"workflow": workflow}}

    # Agent 1: Zoho Scout
    async for event in self.zoho_scout.execute(f"Analyze {account_id}"):
        yield event

    # Agent 2: Memory Analyst
    async for event in self.memory_analyst.execute(zoho_data):
        yield event

    # Agent 3: Recommendation Author
    async for event in self.recommendation_author.execute(memory_data):
        yield event

    # Workflow completion
    yield {"type": "workflow_completed", "data": {"workflow": workflow}}
```

### 8.2 Database Migrations Needed

```python
# migrations/versions/20251019_ag_ui_events.py
"""Add AG UI event tracking

Revision ID: 20251019_0001
Revises: 20241018_0100
Create Date: 2025-10-19 10:00:00
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add event_stream table
    op.create_table(
        'ag_ui_event_stream',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_data', sa.JSON, nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('agent_id', sa.String(255), nullable=True),
        sa.Index('idx_session_id', 'session_id'),
        sa.Index('idx_timestamp', 'timestamp')
    )

    # Add approval_workflow table
    op.create_table(
        'approval_workflow',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('recommendation_id', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),  # pending, approved, rejected
        sa.Column('action', sa.String(50), nullable=True),
        sa.Column('modified_data', sa.JSON, nullable=True),
        sa.Column('reason', sa.Text, nullable=True),
        sa.Column('approved_by', sa.String(255), nullable=True),
        sa.Column('approved_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Index('idx_recommendation_id', 'recommendation_id'),
        sa.Index('idx_status', 'status')
    )

def downgrade():
    op.drop_table('approval_workflow')
    op.drop_table('ag_ui_event_stream')
```

### 8.3 Configuration Changes

```diff
# .env
+ # AG UI Protocol Settings
+ AG_UI_STREAM_ENDPOINT=/api/agent/stream
+ AG_UI_APPROVAL_ENDPOINT=/api/approval/respond
+ AG_UI_SSE_KEEPALIVE=15
+ AG_UI_MAX_EVENT_SIZE=10485760

# requirements.txt
+ ag-ui-protocol>=0.1.0
+ sse-starlette>=1.6.5
```

### 8.4 Breaking Changes to Handle

#### Breaking Change 1: Return Type Changed from `str` to `AsyncGenerator`

**Impact**: All agent calls must now use `async for` instead of `await`.

**Migration**:
```python
# Before
result = await agent.execute(task)

# After
async for event in agent.execute(task):
    if event["type"] == "agent_completed":
        result = event["data"].get("result")
```

#### Breaking Change 2: Approval Workflow Moved to Separate Endpoint

**Impact**: Approval logic no longer inline - now event-driven.

**Migration**:
```python
# Before
recommendation = await author.execute(data)
if user_approves(recommendation):
    apply_to_zoho(recommendation)

# After
# Backend emits approval_required event
yield {"type": "approval_required", "data": {"recommendation": recommendation}}

# Frontend/CLI sends POST /api/approval/respond
# Backend listens for approval response and applies
```

---

## 9. Complete Implementation Checklist

### Phase 1: Backend AG UI Integration (Week 1)

#### Day 1-2: Dependencies & Configuration
- [ ] Add `ag-ui-protocol>=0.1.0` to requirements.txt
- [ ] Add `sse-starlette>=1.6.5` to requirements.txt
- [ ] Create `src/events/` directory
- [ ] Create `src/events/ag_ui_emitter.py`
- [ ] Create `src/events/event_schemas.py` (Pydantic models)
- [ ] Update `src/config.py` with AG UI settings
- [ ] Add AG UI environment variables to `.env.example`

#### Day 3-4: Event Emission
- [ ] Update `src/agents/base_agent.py` to emit events
- [ ] Modify `async def execute()` to return `AsyncGenerator[Dict, None]`
- [ ] Implement `agent_started` event emission
- [ ] Implement `agent_stream` event emission
- [ ] Implement `agent_completed` event emission
- [ ] Add error event handling (`agent_error`)

#### Day 5-6: API Endpoints
- [ ] Create `src/api/routers/ag_ui_router.py`
- [ ] Implement `POST /api/agent/stream` (SSE endpoint)
- [ ] Create `src/api/routers/approval_router.py`
- [ ] Implement `POST /api/approval/respond`
- [ ] Implement `GET /api/recommendations/{id}`
- [ ] Add CORS middleware configuration
- [ ] Test SSE streaming with curl/Postman

#### Day 7: Orchestrator Integration
- [ ] Update `src/agents/orchestrator.py`
- [ ] Implement `async def execute_with_events()`
- [ ] Add workflow start/completion events
- [ ] Add agent coordination events
- [ ] Implement approval workflow state machine
- [ ] Add timeout handling (300 seconds default)

### Phase 2: Approval Workflow (Week 1-2)

#### Day 8-9: Approval State Machine
- [ ] Create `src/events/approval_manager.py`
- [ ] Implement approval request event
- [ ] Implement approval response handling
- [ ] Add database persistence (approval_workflow table)
- [ ] Create Alembic migration for approval tables
- [ ] Run migration: `alembic upgrade head`

#### Day 10: Testing Backend
- [ ] Write unit tests for AGUIEventEmitter
- [ ] Write integration tests for /api/agent/stream
- [ ] Write tests for approval workflow
- [ ] Test SSE streaming with multiple clients
- [ ] Load test with 10 concurrent agents
- [ ] Verify event ordering and consistency

### Phase 3: Frontend Client (Week 2 - Optional)

#### Day 11-12: EventSource Client
- [ ] Create `frontend/src/services/ag_ui_client.ts`
- [ ] Implement EventSource wrapper
- [ ] Add automatic reconnection logic
- [ ] Handle event parsing and validation
- [ ] Create React hooks: `useAgentStream`, `useApproval`

#### Day 13-14: UI Components
- [ ] Create `ApprovalCard.tsx` component
- [ ] Create `AgentMonitor.tsx` component
- [ ] Create `RecommendationList.tsx` component
- [ ] Add approval action handlers (approve/reject/modify)
- [ ] Style with Material-UI or Tailwind

#### Day 15: Frontend Testing
- [ ] Write component tests (React Testing Library)
- [ ] Test EventSource connection/reconnection
- [ ] E2E tests with Playwright
- [ ] Test approval workflow end-to-end
- [ ] Verify SSE event handling in browser

### Phase 4: Documentation & Deployment (Week 3)

#### Day 16-17: Documentation
- [ ] Write API documentation (OpenAPI/Swagger)
- [ ] Create frontend integration guide
- [ ] Document AG UI event schema
- [ ] Write approval workflow guide
- [ ] Create deployment runbook

#### Day 18-19: Docker & Deployment
- [ ] Create Dockerfile
- [ ] Create docker-compose.yml
- [ ] Test local Docker deployment
- [ ] Configure Prometheus metrics
- [ ] Set up Grafana dashboards
- [ ] Deploy to staging environment

#### Day 20-21: Production Hardening
- [ ] Load testing (50+ concurrent users)
- [ ] Security review (authentication, authorization)
- [ ] Configure AWS Secrets Manager
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Deploy to production
- [ ] Monitor for 24 hours

---

## 10. Key Takeaways & Decision Summary

### 10.1 Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Protocol** | AG UI Protocol (direct) | 93% architecture alignment vs CopilotKit's 27.5% |
| **Frontend Framework** | Framework-agnostic (optional React) | Maximum flexibility, no forced dependencies |
| **Backend Framework** | FastAPI (existing) | No changes needed, native async support |
| **Agent Framework** | Claude Agent SDK (existing) | Direct integration, no LangGraph conversion |
| **State Management** | SQLite/Redis (existing) | No duplicate state layers |
| **Streaming** | Server-Sent Events (SSE) | Standard, widely supported, simpler than WebSocket |
| **Approval Workflow** | Event-driven state machine | Framework-agnostic, works with CLI/Web/Slack |

### 10.2 Why NOT CopilotKit?

**Critical Blockers**:
1. **React Lock-in**: Requires React frontend (project has none specified)
2. **Agent Rewrite**: Requires LangGraph (current: Claude Agent SDK)
3. **State Duplication**: React Context + GraphQL + Claude SDK + SQLite/Redis
4. **Integration Effort**: 12-19 weeks vs 2-3 weeks for AG UI Protocol
5. **Maintenance Burden**: Multiple frameworks vs single Python stack

### 10.3 Implementation Timeline

```
Week 1: Backend AG UI Integration
├─ Day 1-2: Dependencies & configuration
├─ Day 3-4: Event emission in agents
├─ Day 5-6: API endpoints (SSE streaming)
└─ Day 7: Orchestrator integration

Week 2: Approval Workflow & Testing
├─ Day 8-9: Approval state machine
├─ Day 10: Backend testing
├─ Day 11-14: Frontend (optional)
└─ Day 15: Frontend testing

Week 3: Documentation & Deployment
├─ Day 16-17: Documentation
├─ Day 18-19: Docker & deployment
└─ Day 20-21: Production hardening

Total: 3 weeks (vs 12-19 weeks for CopilotKit)
```

### 10.4 Success Criteria

- [ ] **Backend**: SSE stream working with 50+ concurrent users
- [ ] **Events**: All 6 event types (workflow_started, agent_started, agent_stream, agent_completed, approval_required, workflow_completed) functioning
- [ ] **Approval**: End-to-end approval workflow (request → response → CRM update) < 2 seconds
- [ ] **Testing**: >80% code coverage
- [ ] **Performance**: <2 second latency for event streaming
- [ ] **Reliability**: 99% uptime during pilot phase

---

## 11. References & Resources

### Official Documentation
- **AG UI Protocol Spec**: https://www.copilotkit.ai/ag-ui
- **AG UI GitHub**: https://github.com/ag-ui-protocol/ag-ui
- **CopilotKit Docs** (reference only): https://docs.copilotkit.ai
- **Claude Agent SDK**: https://github.com/anthropics/claude-agent-sdk
- **FastAPI SSE**: https://github.com/sysid/sse-starlette

### Internal Project Docs
- **AG UI Research Report**: `/docs/research/ag_ui_research_report.md`
- **CopilotKit Analysis**: `/docs/research/copilotkit_comprehensive_analysis.md`
- **Architecture Assessment**: `/docs/copilotkit_architecture_assessment.md`
- **PRD**: `/prd_super_account_manager.md`
- **Implementation Plan**: `/docs/implementation_plan.md`

### Code Examples
- **AG UI Python Example**: See Section 4.2 (AG UI Event Flow)
- **FastAPI SSE Example**: See Section 2.2 (AG UI Endpoint Configuration)
- **React EventSource Client**: See Section 5.4 (Frontend Client Example)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-19
**Author**: Requirements Analyst
**Status**: Complete Implementation Checklist

**Next Steps**:
1. Review with stakeholders
2. Obtain approval for AG UI Protocol approach
3. Begin Phase 1 implementation (Week 1)
4. Update project roadmap with revised timeline

---

*This document serves as the complete implementation checklist for integrating AG UI Protocol with the Sergas Super Account Manager project. All requirements extracted from AG UI and CopilotKit research.*
