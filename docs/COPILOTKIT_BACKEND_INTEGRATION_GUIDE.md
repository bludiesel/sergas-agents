# CopilotKit Backend Integration Guide

## Overview

This document describes the enhanced CopilotKit backend integration with GLM-4.6 agent orchestration system. The integration replaces mock responses with real multi-agent workflows powered by GLM-4.6 via Z.ai proxy.

## Architecture

### Frontend (Next.js)
- **File**: `/frontend/app/api/copilotkit/route.ts`
- **Purpose**: CopilotKit API proxy with Server-Sent Events support
- **Features**:
  - GraphQL operation routing
  - SSE streaming for real-time updates
  - Proper error handling and fallbacks
  - Account ID extraction and session management

### Backend (FastAPI)
- **File**: `/src/api/routers/copilotkit_router_enhanced.py`
- **Purpose**: Real agent orchestration with GLM-4.6
- **Features**:
  - OrchestratorAgent coordination
  - Server-Sent Events streaming
  - AG UI Protocol event emission
  - Multi-agent workflow execution

### Agent System
- **OrchestratorAgent**: Coordinates specialist agents
- **ZohoDataScout**: CRM data retrieval and risk analysis
- **MemoryAnalyst**: Historical context and pattern recognition
- **RecommendationAuthor**: Actionable recommendation generation

## Integration Features

### 1. Real GLM-4.6 Model Integration
- Uses GLM-4.6 via Z.ai proxy
- Configurable model selection
- Proper authentication with API keys

### 2. Server-Sent Events Streaming
```typescript
// Frontend SSE streaming
const response = await fetch('/api/copilotkit', {
  headers: {
    'Accept': 'text/event-stream'
  }
});

const reader = response.body?.getReader();
// Process real-time agent events
```

```python
# Backend SSE streaming
@router.post("/copilotkit/stream")
async def handle_generate_response_streaming(body):
    async def event_stream_generator():
        async for event in orchestrator.execute_with_events(context):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream_generator())
```

### 3. Agent Orchestration Workflow
```
User Request → OrchestratorAgent → Specialist Agents → Response
    ↓                 ↓                ↓
  Extract Account   ZohoDataScout    MemoryAnalyst
    ↓                 ↓                ↓
  Analyze Risk    Get Data         Get History
    ↓                 ↓                ↓
  Generate        Risk Analysis     Pattern Recognition
  Recommendations   ↓                ↓
    ↓                 ↓                ↓
  Approval         Combine Results   Recommendations
  Workflow
```

## API Endpoints

### Frontend Proxy (`/api/copilotkit`)
- **POST**: Main CopilotKit endpoint
- **Accept**: JSON/GraphQL requests
- **Response**: JSON or SSE stream

### Backend Agent System (`/api/copilotkit`)
- **POST**: Agent orchestration requests
- **Operations**:
  - `loadAgentState`: Initialize agent session
  - `generateCopilotResponse`: Execute agent workflow

### Backend Streaming (`/api/copilotkit/stream`)
- **POST**: Server-Sent Events streaming
- **Accept**: `text/event-stream`
- **Response**: Real-time agent execution events

### Health & Discovery
- `GET /health`: Backend health status
- `GET /api/copilotkit/health`: CopilotKit service status
- `GET /agents`: List available agents with capabilities

## Configuration

### Environment Variables
```bash
# GLM-4.6 Configuration
ANTHROPIC_API_KEY=your_api_key
ANTHROPIC_BASE_URL=https://api.z.ai/v1
GLM_MODEL=glm-4.6

# Backend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
GLM_PROVIDER=z.ai
```

### Frontend Configuration
```typescript
// /frontend/app/api/copilotkit/route.ts
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const GLM_MODEL = process.env.GLM_MODEL || 'glm-4.6';
const GLM_PROVIDER = process.env.GLM_PROVIDER || 'z.ai';
```

## Request/Response Format

### GraphQL Request Example
```json
{
  "operationName": "generateCopilotResponse",
  "variables": {
    "messages": [
      {
        "role": "user",
        "content": "Analyze account ACC-001 for risks"
      }
    ],
    "accountId": "ACC-001"
  },
  "agent": "orchestrator",
  "workflow": "account_analysis",
  "stream": true
}
```

### Response Format
```json
{
  "data": {
    "generateCopilotResponse": {
      "response": "✅ GLM-4.6 Analysis Complete for ACC-001...",
      "threadId": "thread_abc123",
      "timestamp": "2024-01-01T12:00:00Z",
      "agent": "orchestrator",
      "executionStatus": "completed",
      "agentCount": 3,
      "metadata": {
        "model": "glm-4.6",
        "provider": "z.ai",
        "accountId": "ACC-001",
        "sessionId": "session_xyz789",
        "orchestrationComplete": true
      }
    }
  }
}
```

## Server-Sent Events Format

### Event Types
```javascript
// Connection established
{
  "event": "connection_established",
  "data": {
    "message": "Connected to GLM-4.6 agent orchestration system",
    "model": "glm-4.6",
    "sessionId": "session_123"
  }
}

// Agent progress
{
  "event": "agent_stream",
  "data": {
    "agent": "zoho_scout",
    "content": "Retrieving account data...",
    "content_type": "text"
  }
}

// Agent completed
{
  "event": "agent_completed",
  "data": {
    "agent": "zoho_scout",
    "step": 1,
    "output": {
      "status": "success",
      "risk_level": "medium"
    }
  }
}

// Workflow completed
{
  "event": "workflow_completed",
  "data": {
    "workflow": "account_analysis",
    "final_output": {
      "status": "completed",
      "recommendations": [...]
    }
  }
}
```

## Testing

### Automated Testing
```bash
# Run comprehensive backend integration tests
python test_copilotkit_backend_integration.py
```

### Manual Testing
```bash
# 1. Start backend server
cd /Users/mohammadabdelrahman/Projects/sergas_agents
python -m src.main

# 2. Test health endpoint
curl http://localhost:8000/api/copilotkit/health

# 3. Test agent listing
curl http://localhost:8000/agents

# 4. Test loadAgentState
curl -X POST http://localhost:8000/api/copilotkit \
  -H "Content-Type: application/json" \
  -d '{
    "operationName": "loadAgentState",
    "variables": {"data": {"threadId": "test_thread"}}
  }'

# 5. Test streaming
curl -X POST http://localhost:8000/api/copilotkit/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "operationName": "generateCopilotResponse",
    "variables": {
      "messages": [{"role": "user", "content": "Test analysis"}],
      "accountId": "ACC-TEST"
    }
  }'
```

## Integration Benefits

### 1. Real Agent System
- **Before**: Mock GLM-4.6 responses
- **After**: Actual multi-agent orchestration
- **Benefits**: Account data, historical context, recommendations

### 2. Real-time Updates
- **Before**: Static responses
- **After**: Streaming agent progress
- **Benefits**: Better UX, visible processing, interruptible workflows

### 3. Production Ready
- **Before**: Demo/simple responses
- **After**: Full workflow with approval
- **Benefits**: Real business value, actionable insights

## Troubleshooting

### Common Issues
1. **Backend Connection Failed**
   - Verify backend is running on port 8000
   - Check CORS configuration
   - Confirm API URL in frontend

2. **Agent Initialization Error**
   - Check GLM-4.6 API credentials
   - Verify environment variables
   - Review orchestration dependencies

3. **Streaming Not Working**
   - Check Accept header: `text/event-stream`
   - Verify SSE endpoint routing
   - Review frontend SSE handling

4. **GraphQL Operations Failing**
   - Verify operationName spelling
   - Check variables structure
   - Review GraphQL response format

### Debug Logging
```bash
# Backend logs
tail -f logs/backend.log

# Frontend logs (Next.js dev)
npm run dev

# Check agent status
curl http://localhost:8000/api/copilotkit/health
```

## Next Steps

1. **Complete Zoho Integration**: Replace simplified agents with full CRM integration
2. **Add LangGraph Integration**: Use LangGraph wrapper for advanced workflows
3. **Enhance Memory System**: Connect to Cognee for persistent memory
4. **Add Approval UI**: Implement interactive approval workflow in frontend
5. **Monitoring**: Add metrics and performance monitoring

## Files Changed

### Frontend
- `/frontend/app/api/copilotkit/route.ts` - Enhanced with SSE and real agent integration

### Backend
- `/src/api/routers/copilotkit_router_enhanced.py` - New enhanced router
- `/src/main.py` - Updated to use enhanced router

### Testing
- `/test_copilotkit_backend_integration.py` - Comprehensive test suite

### Documentation
- `/docs/COPILOTKIT_BACKEND_INTEGRATION_GUIDE.md` - This guide

## Support

For issues or questions:
1. Check this integration guide
2. Run the automated test suite
3. Review server logs for specific errors
4. Verify environment configuration
5. Test individual components in isolation