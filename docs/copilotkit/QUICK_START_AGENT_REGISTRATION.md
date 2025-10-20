# Quick Start: CopilotKit Agent Registration

## TL;DR

3 agents are automatically registered on server startup:
- `orchestrator` - Workflow coordinator
- `zoho_scout` - Zoho CRM data retrieval
- `memory_analyst` - Historical pattern analysis

## Start Server

```bash
# Set required environment variable
export ANTHROPIC_API_KEY=sk-ant-...

# Start server
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## Test Agent Registration

```bash
# List all registered agents
curl http://localhost:8000/agents | jq

# Check health
curl http://localhost:8000/health | jq

# View root info
curl http://localhost:8000/ | jq
```

## Use from Frontend

```typescript
// In your React/Next.js app with CopilotKit
import { CopilotKit } from "@copilotkit/react-core";

function App() {
  return (
    <CopilotKit
      runtimeUrl="http://localhost:8000/copilotkit"
      agent="orchestrator"  // or "zoho_scout", "memory_analyst"
    >
      <YourApp />
    </CopilotKit>
  );
}
```

## Expected Response from `/agents`

```json
{
  "total_agents": 3,
  "agents": [
    {
      "name": "orchestrator",
      "capabilities": ["orchestration", "approval_workflow"]
    },
    {
      "name": "zoho_scout",
      "capabilities": ["zoho_crm_integration", "risk_signal_detection"]
    },
    {
      "name": "memory_analyst",
      "capabilities": ["historical_analysis", "pattern_recognition"]
    }
  ]
}
```

## Add New Agent

1. Create wrapper in `/src/copilotkit/agents/your_agent_wrapper.py`:
```python
def create_your_agent_graph() -> StateGraph:
    # Your LangGraph implementation
    pass
```

2. Update `/src/copilotkit/agents/__init__.py`:
```python
from .your_agent_wrapper import create_your_agent_graph
```

3. Register in `/src/copilotkit/fastapi_integration.py`:
```python
# In setup_copilotkit_with_agents()
your_agent_graph = create_your_agent_graph()
integration.register_agent("your_agent", your_agent_graph)
```

4. Server automatically picks it up on restart!

## Troubleshooting

### CopilotKit not configured
```bash
# Make sure ANTHROPIC_API_KEY is set
export ANTHROPIC_API_KEY=sk-ant-...
```

### Agent not showing up
```bash
# Check startup logs for errors
uvicorn src.main:app --log-level debug

# Verify wrapper exists
ls -la src/copilotkit/agents/

# Check imports
python3 -c "from src.copilotkit.agents import create_orchestrator_graph; print('OK')"
```

### Import errors
```bash
# Install dependencies
pip install -r requirements.txt

# Check Python path
python3 -c "import sys; print(sys.path)"
```

## Architecture

```
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│                                         │
│  setup_copilotkit_with_agents()         │
│         │                               │
│         ├── Register orchestrator       │
│         ├── Register zoho_scout         │
│         └── Register memory_analyst     │
│                                         │
│  POST /copilotkit ← CopilotKit SDK      │
│  GET  /agents     ← Registry info       │
└─────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────┐
│       LangGraph Agent Wrappers          │
│                                         │
│  • orchestrator_wrapper.py              │
│  • zoho_scout_wrapper.py                │
│  • memory_analyst_wrapper.py            │
└─────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────┐
│      Original Sergas Agents             │
│                                         │
│  • OrchestratorAgent (Claude SDK)       │
│  • ZohoDataScout                        │
│  • MemoryAnalyst                        │
└─────────────────────────────────────────┘
```

## Key Files

| File | Purpose |
|------|---------|
| `/src/main.py` | FastAPI app with agent registration |
| `/src/copilotkit/fastapi_integration.py` | Registration logic |
| `/src/copilotkit/agents/__init__.py` | Agent exports |
| `/src/copilotkit/agents/*.py` | LangGraph wrappers |

## Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CORS_ORIGINS=http://localhost:3000
```

## Next Steps

1. ✅ Server starts with 3 agents registered
2. ✅ Test endpoints work
3. ⏳ Add recommendation_author wrapper (in progress)
4. 🚀 Connect frontend CopilotKit client
5. 🎯 Build multi-agent workflows
