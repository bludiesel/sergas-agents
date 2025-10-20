# Quick Start: Launch CopilotKit Interface

## 🚀 5-Minute Setup

### Prerequisites

Make sure you have:
- Python 3.12+ installed
- Node.js 18+ and npm installed
- Environment variables configured

---

## Step 1: Start the Backend (FastAPI)

### Option A: Using Virtual Environment (Recommended)

```bash
# Navigate to project root
cd /Users/mohammadabdelrahman/Projects/sergas_agents

# Activate virtual environment (if you have one)
source venv/bin/activate  # On macOS/Linux
# OR
.\venv\Scripts\activate   # On Windows

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Start FastAPI server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Option B: Direct Python

```bash
# Navigate to project root
cd /Users/mohammadabdelrahman/Projects/sergas_agents

# Install dependencies
pip3 install fastapi uvicorn httpx structlog pydantic anthropic

# Start server
python3 -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Test Backend**:
```bash
# In a new terminal
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

---

## Step 2: Start the Frontend (Next.js)

### First Time Setup

```bash
# Navigate to frontend directory
cd /Users/mohammadabdelrahman/Projects/sergas_agents/frontend

# Install dependencies
npm install

# Configure environment
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_TOKEN=your-auth-token-here
EOF
```

### Launch Frontend

```bash
# Still in /frontend directory
npm run dev
```

**Expected Output**:
```
  ▲ Next.js 15.5.6
  - Local:        http://localhost:3000
  - Network:      http://192.168.1.x:3000

 ✓ Starting...
 ✓ Ready in 2.3s
```

---

## Step 3: Access the Interface

### Open Your Browser

```
http://localhost:3000
```

You should see:
- **Header**: "Sergas Account Manager" title
- **Sidebar**: Agent Status panel (Zoho Scout, Memory Analyst, Recommendation Author)
- **Main Area**: CopilotKit chat interface with greeting message

---

## Step 4: Test the Interface

### Try These Commands in the Chat

1. **Simple Test**:
   ```
   Hello, can you help me analyze an account?
   ```

2. **Analyze Account** (if you have Zoho configured):
   ```
   Analyze account ACC-001
   ```

3. **What You'll See**:
   - Live agent status updates in the sidebar
   - Real-time messages streaming in the chat
   - Tool calls displayed as cards
   - Approval modal popup for recommendations

---

## 📱 What the Interface Looks Like

### Layout

```
┌─────────────────────────────────────────────────┐
│ Sergas Account Manager                          │
│ AI-powered account analysis and recommendations │
├──────────────┬──────────────────────────────────┤
│              │                                   │
│ Agent Status │    CopilotKit Chat Interface     │
│              │                                   │
│ ○ Zoho Scout │    [Chat messages here]          │
│ ○ Memory     │                                   │
│ ○ Recommend  │    [User input box at bottom]    │
│              │                                   │
└──────────────┴──────────────────────────────────┘
```

### Features You'll See

1. **Agent Status Panel** (Left Sidebar):
   - Gray circle = Idle
   - Blue spinning circle = Running
   - Green check = Completed

2. **Chat Interface** (Main Area):
   - Your messages on the right
   - Agent responses on the left
   - Tool call cards showing API operations
   - Status messages ("Retrieving account data...")

3. **Approval Modal** (Popup):
   - Table of recommendations
   - Priority badges (Critical, High, Medium, Low)
   - Confidence scores (0-100%)
   - Next steps for each recommendation
   - Approve/Reject buttons

---

## 🔧 Troubleshooting

### Backend Not Starting?

**Error: ModuleNotFoundError**
```bash
# Install missing dependencies
pip install -r requirements.txt
```

**Error: Port 8000 already in use**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn src.main:app --reload --port 8001
# Then update frontend .env.local to use port 8001
```

**Error: ImportError for src.main**
```bash
# Make sure you're in the project root
cd /Users/mohammadabdelrahman/Projects/sergas_agents

# Try with PYTHONPATH
PYTHONPATH=. uvicorn src.main:app --reload
```

### Frontend Not Starting?

**Error: Cannot find module**
```bash
# Clean install
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Error: Port 3000 already in use**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use different port
PORT=3001 npm run dev
```

**Error: CORS issues**
```bash
# Check backend CORS configuration in src/main.py
# Should include http://localhost:3000
```

### Connection Issues?

**Frontend can't connect to backend**
```bash
# 1. Check backend is running
curl http://localhost:8000/health

# 2. Check .env.local in frontend
cat frontend/.env.local
# Should have: NEXT_PUBLIC_API_URL=http://localhost:8000

# 3. Check browser console for errors
# Open browser DevTools (F12) → Console tab
```

**No events streaming**
```bash
# Check SSE endpoint
curl -N http://localhost:8000/copilotkit \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"thread_id":"test","run_id":"test","account_id":"ACC-001"}'

# Should see streaming events starting with "data:"
```

---

## 🎯 Quick Commands Reference

### Terminal 1: Backend
```bash
cd /Users/mohammadabdelrahman/Projects/sergas_agents
source venv/bin/activate
uvicorn src.main:app --reload --port 8000
```

### Terminal 2: Frontend
```bash
cd /Users/mohammadabdelrahman/Projects/sergas_agents/frontend
npm run dev
```

### Terminal 3: Testing
```bash
# Health check
curl http://localhost:8000/health

# Test SSE endpoint
curl -N http://localhost:8000/copilotkit \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"thread_id":"test-1","run_id":"run-1","account_id":"ACC-001"}'
```

---

## 🎨 Customization

### Change Theme

Edit `frontend/app/page.tsx`:
```typescript
// Change background color
<div className="flex h-screen bg-gray-50">  // Change to bg-blue-50, etc.
```

### Change Title

Edit `frontend/app/page.tsx`:
```typescript
<h1 className="text-2xl font-bold text-gray-900">
  Your Custom Title Here  // Change this
</h1>
```

### Add Custom Greeting

Edit `frontend/app/page.tsx`:
```typescript
<CopilotChat
  labels={{
    title: 'Your Custom Title',
    initial: 'Your custom greeting message here!',
  }}
/>
```

---

## 📚 Next Steps

Once you have the interface running:

1. **Try the CLI** (alternative interface):
   ```bash
   python -m src.cli.agent_cli analyze --account-id ACC-001
   ```

2. **Run Tests**:
   ```bash
   pytest tests/integration/ -v
   ```

3. **Check Performance**:
   ```bash
   ./scripts/run_benchmarks.sh
   ```

4. **Read User Guides**:
   - `/docs/guides/CLI_USAGE.md`
   - `/docs/frontend/FRONTEND_SETUP_COMPLETE.md`

---

## 🆘 Need Help?

### Check Logs

**Backend Logs**:
- Visible in Terminal 1 (where uvicorn is running)
- Look for errors after making requests

**Frontend Logs**:
- Visible in Terminal 2 (where npm run dev is running)
- Also check browser DevTools Console (F12)

### Common Issues

1. **"Cannot connect to backend"**
   - Ensure backend is running on port 8000
   - Check .env.local has correct URL

2. **"No events streaming"**
   - Check browser Network tab for SSE connection
   - Ensure CORS is configured correctly

3. **"Approval modal not showing"**
   - Check browser console for JavaScript errors
   - Ensure ApprovalModal component is imported correctly

### Get More Help

- **Documentation**: Check `/docs/guides/` directory
- **Examples**: Check `/examples/` directory
- **Issues**: File an issue with error logs

---

## ✅ Success Checklist

- [ ] Backend running on http://localhost:8000
- [ ] Backend health check returns `{"status":"healthy"}`
- [ ] Frontend running on http://localhost:3000
- [ ] Browser shows CopilotKit interface
- [ ] Agent status panel visible on left
- [ ] Chat interface responsive
- [ ] Can type messages in chat

**Once all checked, you're ready to analyze accounts!** 🎉
