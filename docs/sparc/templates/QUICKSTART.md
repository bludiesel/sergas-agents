# CopilotKit Integration - Quick Start Guide

## 🎯 Goal

Get CopilotKit working with Sergas Account Manager in under 30 minutes.

---

## ⚡ 5-Minute Setup

### 1. Install Dependencies (2 minutes)

```bash
# Backend
pip install copilotkit langgraph langchain langchain-core langchain-anthropic

# Frontend (in your Next.js project)
npm install @copilotkit/react-core @copilotkit/react-ui @copilotkit/react-textarea
```

### 2. Configure Environment (1 minute)

```bash
# Copy example
cp docs/sparc/templates/.env_copilotkit.example .env

# Edit .env - ONLY these are required for quick start:
ANTHROPIC_API_KEY=sk-ant-...your-key-here
ZOHO_CLIENT_ID=your-zoho-client-id
ZOHO_CLIENT_SECRET=your-zoho-client-secret
```

### 3. Start Backend (1 minute)

```bash
# Run the complete backend
python docs/sparc/templates/main_copilotkit.py

# Should see:
# INFO: Application starting...
# INFO: CopilotKit initialized at /copilotkit
# INFO: Uvicorn running on http://0.0.0.0:8000
```

### 4. Add Frontend API Route (30 seconds)

```bash
# Create directory
mkdir -p app/api/copilotkit

# Copy route file
cp docs/sparc/templates/route.ts app/api/copilotkit/route.ts
```

### 5. Test It (30 seconds)

```bash
# In another terminal
curl http://localhost:8000/health

# Should return:
# {"status": "healthy", "service": "sergas-account-manager"}
```

---

## 🧪 First Working Example (15 minutes)

### Create a Test Page

```tsx
// app/page.tsx
'use client';

import { CopilotKit } from '@copilotkit/react-core';
import { CopilotSidebar } from '@copilotkit/react-ui';
import '@copilotkit/react-ui/styles.css';

export default function Home() {
  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      agent="zoho_scout"
    >
      <div className="flex h-screen">
        {/* Your content */}
        <div className="flex-1 p-8">
          <h1 className="text-3xl font-bold">Account Manager</h1>
          <p className="mt-4">
            Ask the AI assistant to fetch account information!
          </p>
        </div>

        {/* CopilotKit Sidebar */}
        <CopilotSidebar
          defaultOpen={true}
          labels={{
            title: 'Account Assistant',
            initial: 'Try: "Fetch account ACC-001"',
          }}
        />
      </div>
    </CopilotKit>
  );
}
```

### Run Frontend

```bash
npm run dev
```

### Test Interaction

1. Open http://localhost:3000
2. Type in chat: "Fetch account ACC-001"
3. Watch the AI stream the response!

---

## 🚀 Next Steps (10 minutes)

### Add Account Analysis

Use the full template:

```bash
# Copy the demo component
cp docs/sparc/templates/CopilotKitDemo.tsx components/CopilotKitDemo.tsx

# Use in your page
# app/page.tsx
import { CopilotKitDemo } from '@/components/CopilotKitDemo';

export default function Home() {
  return <CopilotKitDemo />;
}
```

Now you have:
- ✅ Real-time account analysis
- ✅ Risk signal detection
- ✅ Historical context retrieval
- ✅ Interactive UI updates

---

## 📊 Verify Everything Works

### Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Can access http://localhost:8000/health
- [ ] Can access http://localhost:3000
- [ ] Chat interface appears in browser
- [ ] Typing "Fetch account ACC-001" returns data
- [ ] No CORS errors in browser console

### Troubleshooting

**Problem: "ANTHROPIC_API_KEY not set"**
```bash
# Check .env file exists
cat .env | grep ANTHROPIC_API_KEY

# Should show your API key
```

**Problem: "Backend unavailable"**
```bash
# Check backend is running
curl http://localhost:8000/health

# If not, start it:
python docs/sparc/templates/main_copilotkit.py
```

**Problem: "CORS error"**
```bash
# Add to .env:
ALLOWED_ORIGINS=http://localhost:3000

# Restart backend
```

---

## 🎓 Understanding the Flow

### What Happens When User Types?

```
1. User types: "Analyze account ACC-001"
   ↓
2. Frontend sends to: /api/copilotkit (Next.js route)
   ↓
3. Next.js forwards to: http://localhost:8000/copilotkit
   ↓
4. FastAPI receives request
   ↓
5. CopilotKit routes to ZohoDataScout agent
   ↓
6. LangGraph executes workflow:
   - fetch_account_node
   - analyze_risk_signals_node
   ↓
7. Results stream back through:
   Backend → Next.js → Frontend
   ↓
8. User sees real-time updates
```

### Files Involved

```
Frontend:
  app/page.tsx                  → User interface
  app/api/copilotkit/route.ts   → API proxy

Backend:
  main_copilotkit.py            → FastAPI app
  backend_setup.py              → CopilotKit setup
  zoho_scout_wrapper.py         → LangGraph agent

Existing:
  src/agents/zoho_data_scout.py → Original agent
```

---

## 🛠 Customization

### Change the Agent

```tsx
// Use orchestrator instead of zoho_scout
<CopilotKit
  runtimeUrl="/api/copilotkit"
  agent="orchestrator"  // ← Change here
>
```

### Add Custom Action

```tsx
import { useCopilotAction } from '@copilotkit/react-core';

function MyComponent() {
  useCopilotAction({
    name: 'getAccountList',
    description: 'Get list of all accounts',
    parameters: [],
    handler: async () => {
      const res = await fetch('/api/accounts');
      const data = await res.json();
      return data;
    },
  });

  return <div>My component</div>;
}
```

### Share Context with AI

```tsx
import { useCopilotReadable } from '@copilotkit/react-core';

function MyComponent() {
  const [accountId, setAccountId] = useState('ACC-001');

  // Make this available to AI
  useCopilotReadable({
    description: 'Currently selected account ID',
    value: accountId,
  });

  return <div>Account: {accountId}</div>;
}
```

---

## 📚 What to Read Next

1. **Full Integration Guide**: See `README.md` in this directory
2. **Template Files**: Review each template with detailed comments
3. **Agent Wrappers**: Study `orchestrator_wrapper.py` and `zoho_scout_wrapper.py`
4. **Frontend Examples**: Check `CopilotKitDemo.tsx` for advanced patterns

---

## 🎯 Common Use Cases

### Use Case 1: Quick Account Lookup

```
User: "Show me account ACC-001"
→ Uses: zoho_scout agent
→ Returns: Account snapshot with risk level
```

### Use Case 2: Full Analysis

```
User: "Analyze account ACC-001"
→ Uses: orchestrator agent
→ Executes: ZohoScout → MemoryAnalyst → Recommendations
→ Returns: Complete analysis with recommendations
```

### Use Case 3: Historical Context

```
User: "What's the history for ACC-001?"
→ Uses: memory_analyst agent
→ Returns: Timeline, patterns, sentiment analysis
```

---

## ✅ Success Criteria

You've successfully integrated CopilotKit when:

1. ✅ Backend starts without errors
2. ✅ Frontend connects to backend
3. ✅ Chat interface appears
4. ✅ Typing messages gets AI responses
5. ✅ Account data loads from Zoho
6. ✅ Responses stream in real-time
7. ✅ No errors in browser console
8. ✅ No errors in backend logs

---

## 🚀 Going to Production

### Before Production Deployment

1. **Security**
   - [ ] Use proper authentication
   - [ ] Secure API keys (not in code)
   - [ ] Enable HTTPS
   - [ ] Validate all inputs

2. **Performance**
   - [ ] Enable caching
   - [ ] Use connection pooling
   - [ ] Optimize database queries
   - [ ] Monitor response times

3. **Reliability**
   - [ ] Add error handling
   - [ ] Implement retries
   - [ ] Set up health checks
   - [ ] Configure logging

4. **Monitoring**
   - [ ] Add application metrics
   - [ ] Set up error tracking
   - [ ] Configure alerts
   - [ ] Track user interactions

---

## 💡 Tips & Best Practices

### Tip 1: Start Simple

Begin with `http_agent_wrapper.ts` for simple cases, graduate to LangGraph for complex workflows.

### Tip 2: Test Incrementally

Test each component independently:
1. Backend health check
2. Single agent execution
3. Frontend-backend connection
4. Full end-to-end flow

### Tip 3: Use Debug Mode

```bash
# Backend
DEBUG=true python main_copilotkit.py

# Frontend (browser console)
localStorage.debug = 'copilotkit:*'
```

### Tip 4: Read Error Messages

CopilotKit provides detailed error messages. Read them carefully - they usually point to the exact issue.

### Tip 5: Check the Examples

All template files have complete working examples. Copy and adapt them rather than starting from scratch.

---

## 🆘 Getting Help

### If Stuck

1. Check this QUICKSTART.md
2. Review README.md
3. Read template file comments
4. Check official CopilotKit docs: https://docs.copilotkit.ai
5. Review existing agent code in `/src/agents/`

### Common Gotchas

- **Forgetting to start backend**: Always check `http://localhost:8000/health`
- **Wrong API route path**: Must be `app/api/copilotkit/route.ts`
- **Missing CORS config**: Add frontend URL to `ALLOWED_ORIGINS`
- **Wrong agent name**: Check agent name in `backend_setup.py`

---

## 🎉 You're Ready!

You now have:
- ✅ Working CopilotKit integration
- ✅ Backend with multiple agents
- ✅ Frontend with AI chat interface
- ✅ Real-time streaming responses
- ✅ Complete code templates

**Next:** Customize the templates for your specific needs!
