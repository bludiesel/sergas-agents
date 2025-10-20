# CopilotKit Integration Templates

## Overview

This directory contains production-ready templates for integrating CopilotKit with the Sergas Account Manager backend. These templates provide complete, working code that can be adapted for your specific needs.

## 📁 Template Files

### Backend (Python/FastAPI)

1. **`requirements_copilotkit.txt`**
   - Additional Python dependencies for CopilotKit
   - Add these to your existing `requirements.txt`
   - Includes: CopilotKit SDK, LangGraph, LangChain

2. **`.env_copilotkit.example`**
   - Environment variables configuration
   - Copy to `.env` and fill in values
   - Includes: API keys, database URLs, configuration

3. **`backend_setup.py`**
   - FastAPI application setup with CopilotKit
   - Functions: `setup_copilotkit()`, `configure_cors()`, `create_app()`
   - Ready to run: `python backend_setup.py`

4. **`orchestrator_wrapper.py`**
   - LangGraph wrapper for OrchestratorAgent
   - State management with TypedDict
   - Multi-agent workflow coordination
   - Approval workflow integration

5. **`zoho_scout_wrapper.py`**
   - LangGraph wrapper for ZohoDataScout
   - Account data retrieval from Zoho CRM
   - Risk signal analysis
   - Change detection

6. **`main_copilotkit.py`**
   - Complete FastAPI application
   - All agents registered
   - Health checks and monitoring
   - Custom endpoints for account management
   - Production-ready with lifecycle management

### Frontend (Next.js/TypeScript/React)

7. **`package.json`**
   - Node.js dependencies for frontend
   - CopilotKit React libraries
   - Next.js configuration

8. **`route.ts`**
   - Next.js API route for CopilotKit
   - Proxies requests to FastAPI backend
   - Handles streaming responses (SSE)
   - Location: `app/api/copilotkit/route.ts`

9. **`CopilotKitDemo.tsx`**
   - Complete React component with CopilotKit integration
   - Hooks: `useCopilotChat`, `useCopilotAction`, `useCopilotReadable`
   - UI components: Sidebar and Popup variants
   - Account analysis interface

10. **`http_agent_wrapper.ts`**
    - Alternative to LangGraph for simpler patterns
    - Direct HTTP communication
    - Lighter weight for basic operations
    - Comparison guide: HttpAgent vs LangGraph

11. **`a2a_middleware.ts`**
    - Agent-to-Agent communication patterns
    - Multi-agent coordination
    - Workflow patterns: Sequential, Parallel, Conditional
    - Advanced collaboration patterns

---

## 🚀 Quick Start

### 1. Backend Setup

```bash
# Navigate to project root
cd /Users/mohammadabdelrahman/Projects/sergas_agents

# Install additional dependencies
pip install -r docs/sparc/templates/requirements_copilotkit.txt

# Configure environment
cp docs/sparc/templates/.env_copilotkit.example .env
# Edit .env with your credentials

# Run the backend
python docs/sparc/templates/main_copilotkit.py

# Backend now running at http://localhost:8000
# CopilotKit endpoint: http://localhost:8000/copilotkit
```

### 2. Frontend Setup

```bash
# Create Next.js application (if not exists)
npx create-next-app@latest sergas-frontend --typescript --tailwind --app

# Navigate to frontend
cd sergas-frontend

# Copy package.json dependencies
# Merge with your existing package.json

# Install dependencies
npm install

# Copy template files:
# - route.ts → app/api/copilotkit/route.ts
# - CopilotKitDemo.tsx → components/CopilotKitDemo.tsx

# Run frontend
npm run dev

# Frontend now running at http://localhost:3000
```

### 3. Integration

In your Next.js app:

```tsx
// app/page.tsx
import { CopilotKitDemo } from '@/components/CopilotKitDemo';

export default function Home() {
  return <CopilotKitDemo />;
}
```

---

## 📚 Architecture

### Backend Architecture

```
FastAPI App (main_copilotkit.py)
    ↓
CopilotKit SDK
    ↓
LangGraph Wrappers
    ↓ ↓ ↓
┌──────────────┬─────────────────┬────────────────────┐
│ Orchestrator │ ZohoDataScout   │ MemoryAnalyst      │
└──────────────┴─────────────────┴────────────────────┘
    ↓              ↓                   ↓
Existing Agent  Zoho Integration  Cognee Integration
```

### Frontend Architecture

```
React Component (CopilotKitDemo.tsx)
    ↓
CopilotKit Hooks
    ↓
Next.js API Route (route.ts)
    ↓
FastAPI Backend (/copilotkit)
```

---

## 🔧 Configuration

### Environment Variables

**Required:**
- `ANTHROPIC_API_KEY`: Claude API key
- `ZOHO_CLIENT_ID`, `ZOHO_CLIENT_SECRET`: Zoho CRM credentials
- `COGNEE_API_KEY`: Cognee memory service

**Optional:**
- `COPILOTKIT_PUBLIC_API_KEY`: For CopilotKit Cloud features
- `DEBUG`: Enable debug mode (true/false)
- `ALLOWED_ORIGINS`: CORS origins (comma-separated)

See `.env_copilotkit.example` for complete list.

---

## 📖 Usage Examples

### Example 1: Basic Account Analysis

**User:** "Analyze account ACC-001"

**Backend Flow:**
1. Orchestrator receives request
2. Calls ZohoDataScout to fetch data
3. Calls MemoryAnalyst for historical context
4. Returns combined analysis
5. Streams results to frontend

**Frontend:**
```tsx
// Component automatically handles streaming
<CopilotKitDemo />

// User types in chat: "Analyze account ACC-001"
// Results stream in real-time
```

### Example 2: Custom Actions

```tsx
// In your React component
useCopilotAction({
  name: 'analyzeAccount',
  description: 'Analyze a specific account',
  parameters: [
    {
      name: 'accountId',
      type: 'string',
      description: 'Account ID (ACC-XXX)',
      required: true,
    },
  ],
  handler: async ({ accountId }) => {
    const response = await fetch(`/api/accounts/${accountId}`);
    const data = await response.json();
    return { success: true, data };
  },
});
```

### Example 3: Share Context with AI

```tsx
// Make UI state available to AI
useCopilotReadable({
  description: 'Currently selected account',
  value: selectedAccount,
});

// Now AI can reference this in responses
// User: "What's the risk level?"
// AI: "The current account (ACC-001) has a high risk level..."
```

---

## 🎯 Integration Patterns

### Pattern 1: LangGraph (Recommended for Complex Workflows)

**Use when:**
- Multi-step workflows
- State management needed
- Agent coordination required
- Approval workflows

**Files:**
- `orchestrator_wrapper.py`
- `zoho_scout_wrapper.py`

**Example:**
```python
from docs.sparc.templates.orchestrator_wrapper import create_orchestrator_graph

graph = create_orchestrator_graph()
copilot_kit.add_agent("orchestrator", graph)
```

### Pattern 2: HttpAgent (Simple Operations)

**Use when:**
- Single API calls
- Stateless operations
- Quick data retrieval
- Prototyping

**Files:**
- `http_agent_wrapper.ts`

**Example:**
```typescript
const agent = createHttpAgent();
runtime.agent(agent);
```

### Pattern 3: a2a Middleware (Multi-Agent Coordination)

**Use when:**
- Multiple agents need to collaborate
- Complex routing logic
- Agent handoffs required
- Parallel agent execution

**Files:**
- `a2a_middleware.ts`

**Example:**
```typescript
const middleware = createA2AMiddleware();
runtime.agent(middleware);
```

---

## 🔍 Debugging

### Backend Debugging

```python
# Enable debug logging
import structlog
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ]
)

# Run with debug mode
DEBUG=true python main_copilotkit.py
```

### Frontend Debugging

```tsx
// Check CopilotKit state
const { isLoading, messages } = useCopilotChat();

console.log('CopilotKit state:', { isLoading, messages });

// Monitor API calls
// Open Network tab in browser DevTools
// Look for calls to /api/copilotkit
```

### Common Issues

**Issue: "ANTHROPIC_API_KEY not set"**
- Solution: Copy `.env_copilotkit.example` to `.env` and fill in API key

**Issue: "Backend unavailable"**
- Solution: Check backend is running on port 8000
- Verify `NEXT_PUBLIC_BACKEND_URL` in frontend .env

**Issue: "CORS error"**
- Solution: Add frontend URL to `ALLOWED_ORIGINS` in backend .env

**Issue: "Agent not found"**
- Solution: Verify agent is registered in `backend_setup.py`

---

## 🧪 Testing

### Test Backend

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test CopilotKit endpoint
curl -X POST http://localhost:8000/copilotkit \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Analyze account ACC-001"}]}'
```

### Test Frontend

```bash
# Run development server
npm run dev

# Open http://localhost:3000
# Type in chat: "Analyze account ACC-001"
# Verify streaming response
```

### Integration Test

```bash
# Start backend
python main_copilotkit.py &

# Start frontend
cd sergas-frontend && npm run dev &

# Test end-to-end
# 1. Open http://localhost:3000
# 2. Type "Analyze account ACC-001"
# 3. Verify response streams correctly
# 4. Check backend logs for agent execution
```

---

## 📝 Customization Guide

### Add New Agent

**Backend:**

```python
# 1. Create LangGraph wrapper
# docs/sparc/templates/my_agent_wrapper.py
from langgraph.graph import StateGraph

def create_my_agent_graph():
    workflow = StateGraph(MyAgentState)
    workflow.add_node("my_node", my_node_function)
    return workflow.compile()

# 2. Register in backend_setup.py
my_agent_graph = create_my_agent_graph()
copilot_kit.add_agent("my_agent", my_agent_graph)
```

**Frontend:**

```tsx
// Use with specific agent
<CopilotKit
  runtimeUrl="/api/copilotkit"
  agent="my_agent"
>
  <YourComponent />
</CopilotKit>
```

### Add Custom Action

```tsx
useCopilotAction({
  name: 'myCustomAction',
  description: 'Description for AI to understand when to use this',
  parameters: [
    {
      name: 'paramName',
      type: 'string',
      description: 'Parameter description',
      required: true,
    },
  ],
  handler: async ({ paramName }) => {
    // Your custom logic
    const result = await myCustomFunction(paramName);
    return { success: true, result };
  },
});
```

---

## 🚀 Production Deployment

### Backend Production

```bash
# Install production dependencies
pip install gunicorn

# Run with gunicorn
gunicorn docs.sparc.templates.main_copilotkit:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000

# Or use Docker (create Dockerfile):
# FROM python:3.13
# COPY . /app
# RUN pip install -r requirements.txt
# CMD ["gunicorn", "main_copilotkit:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker"]
```

### Frontend Production

```bash
# Build Next.js app
npm run build

# Start production server
npm start

# Or deploy to Vercel
vercel deploy
```

---

## 📚 Additional Resources

### Documentation

- **CopilotKit Docs**: https://docs.copilotkit.ai
- **LangGraph Guide**: https://langchain-ai.github.io/langgraph/
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Next.js Docs**: https://nextjs.org/docs

### Related Files

- **Project PRD**: `/Users/mohammadabdelrahman/Projects/sergas_agents/docs/requirements/PRD_SuperAccountManager_V3.md`
- **Architecture**: `/Users/mohammadabdelrahman/Projects/sergas_agents/docs/architecture/`
- **Existing Agents**: `/Users/mohammadabdelrahman/Projects/sergas_agents/src/agents/`

---

## ✅ Checklist

Before deploying, ensure:

- [ ] All environment variables configured
- [ ] Backend starts without errors
- [ ] Frontend connects to backend
- [ ] Account analysis works end-to-end
- [ ] Streaming responses working
- [ ] Error handling tested
- [ ] CORS configured correctly
- [ ] Authentication implemented (if needed)
- [ ] Monitoring/logging enabled
- [ ] Production secrets secured

---

## 🤝 Support

For issues or questions:

1. Check this README
2. Review template code comments
3. Check official CopilotKit docs
4. Review existing agent implementations in `/src/agents/`

---

## 📄 License

These templates are part of the Sergas Account Manager project.
