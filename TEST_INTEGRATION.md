# CopilotKit Integration - Live Testing Guide

**Date**: 2025-10-19
**Status**: ✅ Services Running

---

## 🚀 Running Services

### Backend (FastAPI)
- **URL**: http://localhost:8008
- **Status**: ✅ Running
- **PID**: Check `.backend_copilotkit.pid`
- **Logs**: `tail -f backend_copilotkit.log`

**Endpoints**:
- Root: http://localhost:8008/
- Health: http://localhost:8008/health
- Agents: http://localhost:8008/agents
- OpenAPI Docs: http://localhost:8008/docs
- CopilotKit SDK: http://localhost:8008/copilotkit

### Frontend (Next.js)
- **URL**: http://localhost:7007
- **Status**: ✅ Running
- **PID**: Check `.frontend_copilotkit.pid`
- **Logs**: `tail -f frontend_copilotkit.log`

**Endpoints**:
- Home: http://localhost:7007/
- CopilotKit API Route: http://localhost:7007/api/copilotkit

---

## 🧪 Manual Testing Steps

### 1. Test Backend Directly

#### Check Health
```bash
curl http://localhost:8008/health | jq
```

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "sergas-agents",
  "protocol": "ag-ui",
  "copilotkit_configured": true,
  "agents_registered": 3
}
```

#### List Registered Agents
```bash
curl http://localhost:8008/agents | jq
```

**Expected Response**:
```json
{
  "total_agents": 3,
  "agents": [
    {
      "name": "orchestrator",
      "capabilities": ["orchestration", "approval_workflow", "multi_agent_coordination"],
      "description": "Main workflow coordinator"
    },
    {
      "name": "zoho_scout",
      "capabilities": ["zoho_crm_integration", "account_data_retrieval", "risk_signal_detection"],
      "description": "Account data retrieval from Zoho CRM"
    },
    {
      "name": "memory_analyst",
      "capabilities": ["historical_analysis", "pattern_recognition", "cognee_integration"],
      "description": "Historical context and pattern analysis"
    }
  ]
}
```

#### Test CopilotKit Endpoint
```bash
curl -X POST http://localhost:8008/copilotkit \
  -H "Content-Type: application/json" \
  -d '{"agent": "orchestrator", "message": "Test message"}'
```

### 2. Test Frontend

#### Open in Browser
1. Navigate to: http://localhost:7007
2. You should see the Sergas Account Manager UI with CopilotKit integration

#### Test CopilotKit API Route
```bash
curl http://localhost:7007/api/copilotkit
```

**Expected Response**: Health check from Next.js API route

### 3. Test Complete Integration Flow

#### Option A: Using the UI
1. Open http://localhost:7007 in browser
2. Look for CopilotKit sidebar or popup
3. Try typing a command like "Analyze account ACC-001"
4. Watch for:
   - SSE streaming events
   - Agent status updates
   - Real-time responses

#### Option B: Using curl (API Route → Backend)
```bash
curl -X POST http://localhost:7007/api/copilotkit \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "zoho_scout",
    "account_id": "ACC-001",
    "action": "fetchAccountData"
  }'
```

### 4. Test Agent Actions

#### Analyze Account (Full Workflow)
Use the browser console:
```javascript
// This would be triggered from the UI
fetch('/api/copilotkit', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    agent: 'orchestrator',
    workflow: 'account_analysis',
    account_id: 'ACC-001'
  })
})
```

### 5. Test HITL Approval Workflow

1. Trigger recommendation generation from UI
2. Watch for approval modal to appear
3. Approve or reject recommendations
4. Verify workflow resumes/cancels correctly

---

## 🔍 Validation Checklist

### Backend Validation
- [ ] Backend starts without errors
- [ ] Health endpoint returns healthy status
- [ ] 3 agents registered (orchestrator, zoho_scout, memory_analyst)
- [ ] /copilotkit endpoint responds
- [ ] OpenAPI docs accessible at /docs

### Frontend Validation
- [ ] Frontend builds successfully
- [ ] Home page loads at port 7007
- [ ] CopilotKit provider initialized
- [ ] No console errors in browser
- [ ] API route proxies requests correctly

### Integration Validation
- [ ] Frontend can reach backend via API route
- [ ] SSE streaming works (check Network tab)
- [ ] Agent actions can be triggered
- [ ] State updates happen in real-time
- [ ] HITL approval modal appears when needed

### Component Validation
- [ ] CopilotSidebar or CopilotPopup visible
- [ ] AccountAnalysisAgent actions work
- [ ] useCopilotAction hooks trigger correctly
- [ ] useCopilotReadable provides context
- [ ] useCoAgent shares state bidirectionally

---

## 🐛 Troubleshooting

### Backend Issues

**Backend won't start:**
```bash
# Check if port is already in use
lsof -ti:8008 | xargs kill -9

# Check logs
tail -50 backend_copilotkit.log

# Check for Python errors
source venv/bin/activate
python -c "from src.main import app; print('✅ Import successful')"
```

**No agents registered:**
```bash
# Check if LangGraph is installed
pip list | grep langgraph

# Install if missing
pip install langgraph langchain-anthropic langchain-core
```

### Frontend Issues

**Frontend won't start:**
```bash
# Check if port is already in use
lsof -ti:7007 | xargs kill -9

# Check logs
tail -50 frontend_copilotkit.log

# Rebuild
cd frontend
npm run build
```

**TypeScript errors:**
```bash
cd frontend
npx tsc --noEmit
```

### Integration Issues

**API route can't reach backend:**
- Verify backend is running: `curl http://localhost:8008/health`
- Check CORS configuration in backend
- Verify API route proxy URL is correct

**SSE streaming not working:**
- Check browser Network tab for event-stream
- Verify Content-Type headers
- Check for connection timeouts

**Agents not responding:**
- Check backend logs for errors
- Verify agent registration: `curl http://localhost:8008/agents`
- Test agents directly: `curl http://localhost:8008/copilotkit`

---

## 📊 Expected Behavior

### On Startup

**Backend**:
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8008
```

**Frontend**:
```
 ▲ Next.js 15.5.6
 - Local:        http://localhost:7007
 - Network:      http://0.0.0.0:7007

 ✓ Ready in 2.5s
```

### On Agent Request

**Backend Logs**:
```
INFO: Agent request received: orchestrator
INFO: Executing workflow: account_analysis
INFO: ZohoDataScout: Fetching account ACC-001
INFO: MemoryAnalyst: Analyzing historical context
INFO: RecommendationAuthor: Generating recommendations
INFO: HITL: Approval required for 3 recommendations
```

**Browser Network Tab**:
```
POST /api/copilotkit
Status: 200 OK
Content-Type: text/event-stream

data: {"type":"agent_started","agent":"orchestrator"}
data: {"type":"agent_stream","content":"Analyzing account..."}
data: {"type":"workflow_interrupted","reason":"approval_required"}
```

---

## 🎯 Test Scenarios

### Scenario 1: Simple Account Query
1. Open frontend: http://localhost:7007
2. Type: "Show me account ACC-001"
3. Expect: ZohoDataScout retrieves account data
4. Verify: Account details displayed

### Scenario 2: Full Analysis Workflow
1. Type: "Analyze account ACC-001"
2. Expect: Orchestrator triggers all agents sequentially
3. Watch: ZohoScout → MemoryAnalyst → RecommendationAuthor
4. Verify: Approval modal appears for high-priority recommendations

### Scenario 3: HITL Approval
1. Trigger recommendation generation
2. Wait for approval modal
3. Click "Approve" or "Reject"
4. Verify: Workflow resumes/cancels appropriately
5. Check: Recommendations execute or are discarded

### Scenario 4: Real-Time Streaming
1. Start a long-running analysis
2. Watch browser Network tab
3. Verify: SSE events stream in real-time
4. Check: Progress updates appear continuously

---

## 📝 Notes

- Backend uses port **8008** (not 8000)
- Frontend uses port **7007** (not 3000)
- All agents are LangGraph wrappers (non-invasive)
- Original agents remain unchanged
- HITL workflow interrupts at approval points

---

## 🛑 Stopping Services

### Quick Stop
```bash
./scripts/stop_all.sh
```

### Manual Stop
```bash
# Kill by PID
kill $(cat .backend_copilotkit.pid)
kill $(cat .frontend_copilotkit.pid)

# Or by port
lsof -ti:8008 | xargs kill -9
lsof -ti:7007 | xargs kill -9

# Clean up PID files
rm -f .backend_copilotkit.pid .frontend_copilotkit.pid
```

---

## 🎉 Success Criteria

All tests pass if:
- ✅ Backend starts and registers 3 agents
- ✅ Frontend builds and serves on port 7007
- ✅ API route proxies to backend successfully
- ✅ SSE streaming works in browser
- ✅ Agent actions can be triggered from UI
- ✅ HITL approval workflow functions correctly
- ✅ No console errors in browser or backend logs

**Ready to test the complete CopilotKit integration!** 🚀
