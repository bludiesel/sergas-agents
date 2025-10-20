# Backend Developer Guide

**Version:** 1.0.0
**Last Updated:** 2025-10-19
**Target Audience:** Backend Engineers, System Architects

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Adding New Agents](#adding-new-agents)
3. [AG UI Event Streaming](#ag-ui-event-streaming)
4. [Testing Guidelines](#testing-guidelines)
5. [Deployment Process](#deployment-process)
6. [Architecture Patterns](#architecture-patterns)

---

## Project Structure

```
sergas_agents/
├── src/
│   ├── agents/             # Agent implementations
│   │   ├── base_agent.py   # Base agent class (Claude SDK)
│   │   ├── orchestrator.py # Main coordinator
│   │   ├── zoho_data_scout.py
│   │   ├── memory_analyst.py
│   │   └── recommendation_author.py
│   │
│   ├── api/                # FastAPI application
│   │   ├── main.py         # App entry point
│   │   └── routers/
│   │       ├── copilotkit_router.py  # AG UI endpoint
│   │       └── approval_router.py    # Approval workflow
│   │
│   ├── events/             # AG UI Protocol implementation
│   │   ├── ag_ui_emitter.py   # Event emitter
│   │   ├── ag_ui_encoder.py   # SSE encoder
│   │   └── approval_manager.py
│   │
│   ├── hooks/              # Hook system
│   │   ├── audit_hooks.py
│   │   ├── permission_hooks.py
│   │   └── metrics_hooks.py
│   │
│   ├── models/             # Data models
│   ├── database/           # Database layer
│   └── utils/              # Utilities
│
├── tests/                  # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/                   # Documentation
├── scripts/                # Utility scripts
└── config/                 # Configuration files
```

---

## Adding New Agents

### Step 1: Define Agent Class

Create a new file in `src/agents/`:

```python
# src/agents/my_new_agent.py

from typing import Dict, Any, AsyncGenerator
import structlog

from src.agents.base_agent import BaseAgent
from src.events.ag_ui_emitter import AGUIEventEmitter
from ag_ui.core import EventType

logger = structlog.get_logger(__name__)


class MyNewAgent(BaseAgent):
    """
    Custom agent for [specific purpose].

    This agent:
    - [Capability 1]
    - [Capability 2]
    - [Capability 3]
    """

    def __init__(self):
        super().__init__(
            agent_id="my-new-agent",
            system_prompt="""
            You are an expert at [domain].
            Your role is to [primary function].
            Always provide [specific output format].
            """,
            allowed_tools=[
                "tool_1",
                "tool_2",
                "tool_3"
            ],
            permission_mode="default",  # or "acceptEdits", "bypassPermissions"
        )

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent task.

        Args:
            context: {
                "input_field": "value",
                "thread_id": "...",
                "run_id": "..."
            }

        Returns:
            {
                "status": "success",
                "result": {...}
            }
        """
        # Implementation
        input_value = context.get("input_field")

        # Initialize agent
        await self.initialize()

        try:
            # Your agent logic here
            result = await self._process(input_value)

            return {
                "status": "success",
                "result": result,
                "agent_id": self.agent_id,
            }

        finally:
            await self.cleanup()

    async def execute_with_events(
        self,
        context: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute with AG UI event streaming.

        Yields:
            AG UI Protocol events
        """
        emitter = AGUIEventEmitter(
            thread_id=context.get("thread_id"),
            run_id=context.get("run_id"),
            agent_id=self.agent_id,
        )

        try:
            # Emit start event
            yield emitter.emit_run_started()

            # Emit progress message
            yield emitter.emit_text_message_start(message_id="msg-1")
            yield emitter.emit_text_message_content(
                message_id="msg-1",
                content="Processing your request..."
            )

            # Execute main logic
            result = await self.execute(context)

            # Emit result
            yield emitter.emit_text_message_content(
                message_id="msg-1",
                content=f"Result: {result}"
            )
            yield emitter.emit_text_message_end(message_id="msg-1")

            # Emit finish event
            yield emitter.emit_run_finished(final_output=result)

        except Exception as e:
            logger.error("agent_error", error=str(e), agent_id=self.agent_id)
            yield emitter.emit_run_error(error=str(e))

    async def _process(self, input_value: str) -> Dict[str, Any]:
        """Private helper method for processing."""
        # Your implementation
        return {"processed": input_value}
```

### Step 2: Register Agent in Orchestrator

Update `src/agents/orchestrator.py`:

```python
from src.agents.my_new_agent import MyNewAgent

class OrchestratorAgent(BaseAgent):
    def __init__(self, ...):
        super().__init__(...)

        # Add new agent
        self.my_new_agent = MyNewAgent()

    async def execute_workflow(self, context: Dict[str, Any]):
        # Use new agent in workflow
        result = await self.my_new_agent.execute(context)
        # ...
```

### Step 3: Write Tests

Create test file in `tests/unit/agents/`:

```python
# tests/unit/agents/test_my_new_agent.py

import pytest
from src.agents.my_new_agent import MyNewAgent


@pytest.mark.asyncio
async def test_my_new_agent_execute():
    """Test basic agent execution."""
    agent = MyNewAgent()

    context = {
        "input_field": "test_value",
        "thread_id": "test-thread",
        "run_id": "test-run"
    }

    result = await agent.execute(context)

    assert result["status"] == "success"
    assert "result" in result


@pytest.mark.asyncio
async def test_my_new_agent_with_events():
    """Test agent with AG UI event streaming."""
    agent = MyNewAgent()

    context = {
        "input_field": "test_value",
        "thread_id": "test-thread",
        "run_id": "test-run"
    }

    events = []
    async for event in agent.execute_with_events(context):
        events.append(event)

    # Verify event sequence
    assert events[0]["type"] == "RUN_STARTED"
    assert events[-1]["type"] == "RUN_FINISHED"
```

---

## AG UI Event Streaming

### Event Flow Architecture

```
Request → FastAPI → Orchestrator → Agent → Events → SSE → Client
                                     ↓
                              Tool Executions
                                     ↓
                              AG UI Events
```

### Implementing Event Streaming

#### 1. Basic Event Emission

```python
from src.events.ag_ui_emitter import AGUIEventEmitter
from ag_ui.core import EventType

# Initialize emitter
emitter = AGUIEventEmitter(
    thread_id="thread-123",
    run_id="run-456",
    agent_id="my-agent"
)

# Emit lifecycle events
yield emitter.emit_run_started()
yield emitter.emit_run_finished(final_output={"status": "success"})
yield emitter.emit_run_error(error="Error message")
```

#### 2. Streaming Text Messages

```python
# Start message
message_id = "msg-1"
yield emitter.emit_text_message_start(message_id=message_id)

# Stream content chunks
for chunk in response_chunks:
    yield emitter.emit_text_message_content(
        message_id=message_id,
        content=chunk
    )

# End message
yield emitter.emit_text_message_end(message_id=message_id)
```

#### 3. Tool Call Events

```python
# Start tool call
tool_call_id = "tc-1"
yield emitter.emit_tool_call_start(
    tool_call_id=tool_call_id,
    tool_name="zoho_get_account"
)

# Emit arguments
yield emitter.emit_tool_call_args(
    tool_call_id=tool_call_id,
    args={"account_id": "ACC-001"}
)

# Execute tool
result = await execute_tool(...)

# Emit result
yield emitter.emit_tool_call_result(
    tool_call_id=tool_call_id,
    result=result
)
```

#### 4. State Management

```python
# Emit state snapshot
yield emitter.emit_state_snapshot(state={
    "stage": "processing",
    "progress": 50,
    "data": {...}
})

# Emit state delta (incremental update)
yield emitter.emit_state_delta(delta={
    "progress": 75
})
```

### FastAPI Endpoint Pattern

```python
# src/api/routers/copilotkit_router.py

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from ag_ui.core import RunAgentInput
from src.agents.orchestrator import OrchestratorAgent

router = APIRouter(prefix="/copilotkit", tags=["CopilotKit"])


@router.post("")
async def copilotkit_endpoint(request: Request):
    """Main CopilotKit SSE endpoint."""
    # Parse input
    input_data: RunAgentInput = await request.json()

    # Initialize orchestrator
    orchestrator = OrchestratorAgent(
        thread_id=input_data.thread_id,
        run_id=input_data.run_id
    )

    # Stream events
    async def event_generator():
        async for event in orchestrator.execute_with_events(input_data):
            # Encode to SSE format
            yield f"data: {event.to_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

---

## Testing Guidelines

### Unit Testing

```python
# tests/unit/test_example.py

import pytest
from src.agents.base_agent import BaseAgent


class TestAgent(BaseAgent):
    async def execute(self, context):
        return {"status": "success"}


@pytest.mark.asyncio
async def test_agent_initialization():
    """Test agent initializes correctly."""
    agent = TestAgent(
        agent_id="test-agent",
        system_prompt="Test prompt",
        allowed_tools=["tool1"],
        permission_mode="default"
    )

    assert agent.agent_id == "test-agent"
    assert len(agent.allowed_tools) == 1


@pytest.mark.asyncio
async def test_agent_session_lifecycle():
    """Test session start/end lifecycle."""
    agent = TestAgent(...)

    # Initialize
    await agent.initialize()
    assert agent.session_id is not None

    # Cleanup
    await agent.cleanup()
    assert agent.session_id is None
```

### Integration Testing

```python
# tests/integration/test_multi_agent.py

import pytest
from httpx import AsyncClient
from src.api.main import app


@pytest.mark.asyncio
async def test_full_workflow():
    """Test complete orchestrator workflow."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Start analysis
        response = await client.post(
            "/copilotkit",
            json={
                "thread_id": "test-thread",
                "run_id": "test-run",
                "messages": [
                    {"role": "user", "content": "Analyze ACC-001"}
                ],
                "state": {"account_id": "ACC-001"}
            },
            headers={"Accept": "text/event-stream"}
        )

        events = []
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[5:]))

        # Verify event sequence
        assert events[0]["type"] == "RUN_STARTED"
        assert events[-1]["type"] == "RUN_FINISHED"
```

### E2E Testing

```python
# tests/e2e/test_account_analysis.py

import pytest


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_account_analysis():
    """Test end-to-end account analysis flow."""
    # 1. Start analysis via API
    # 2. Verify data retrieval from Zoho
    # 3. Verify memory queries
    # 4. Verify recommendations generated
    # 5. Test approval workflow
    # 6. Verify CRM updates
    pass
```

### Test Coverage Requirements

- **Unit Tests**: 80% minimum coverage
- **Integration Tests**: All API endpoints
- **E2E Tests**: Critical workflows

Run coverage:
```bash
pytest --cov=src --cov-report=html --cov-report=term
```

---

## Deployment Process

### Local Development

```bash
# 1. Setup environment
python3.14 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 3. Start services
docker-compose up -d cognee

# 4. Run application
uvicorn src.api.main:app --reload --port 8000
```

### Staging Deployment

```bash
# 1. Build Docker image
docker build -t sergas-agents:staging .

# 2. Push to registry
docker tag sergas-agents:staging registry.sergas.com/sergas-agents:staging
docker push registry.sergas.com/sergas-agents:staging

# 3. Deploy to staging
kubectl apply -f k8s/staging/

# 4. Verify deployment
kubectl get pods -n staging
kubectl logs -f deployment/sergas-agents -n staging
```

### Production Deployment

```bash
# 1. Tag release
git tag v1.0.0
git push origin v1.0.0

# 2. Build production image
docker build -t sergas-agents:1.0.0 -f Dockerfile.prod .

# 3. Push to registry
docker push registry.sergas.com/sergas-agents:1.0.0

# 4. Deploy with zero-downtime
kubectl set image deployment/sergas-agents \
  sergas-agents=registry.sergas.com/sergas-agents:1.0.0 \
  --record -n production

# 5. Monitor rollout
kubectl rollout status deployment/sergas-agents -n production
```

---

## Architecture Patterns

### 1. Agent Pattern

All agents inherit from `BaseAgent` and implement:
- `execute()`: Core business logic
- `execute_with_events()`: AG UI streaming support

### 2. Hook System

Agents use hooks for cross-cutting concerns:
```python
hooks = {
    "pre_tool": audit_hook.pre_tool,
    "post_tool": audit_hook.post_tool,
    "on_session_start": metrics_hook.on_session_start,
    "on_session_end": metrics_hook.on_session_end
}
```

### 3. Event-Driven Architecture

AG UI Protocol enables decoupled frontend/backend:
- Backend emits events
- Frontend consumes via SSE
- No tight coupling between layers

### 4. Three-Tier Integration

Zoho CRM access with fallback:
1. **Tier 1**: Zoho MCP (primary)
2. **Tier 2**: Python SDK (secondary)
3. **Tier 3**: REST API (fallback)

---

**Next Steps:**
- Review [Testing Strategy](../testing_strategy.md)
- Check [API Documentation](../api/openapi.yml)
- See [Frontend Guide](FRONTEND_GUIDE.md)
