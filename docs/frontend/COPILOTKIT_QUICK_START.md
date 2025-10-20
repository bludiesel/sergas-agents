# CopilotKit Integration - Quick Start Guide

## Verify the Integration

Run the validation script to confirm everything is working:

```bash
bash scripts/validate_copilotkit.sh
```

Expected output:
```
All tests passed! ✅
CopilotKit integration is working correctly.
```

## Access the Application

### Frontend
- **URL**: http://localhost:7007
- **Port**: 7007
- **Framework**: Next.js 15.5.6 with Turbopack

### Backend
- **URL**: http://localhost:8008
- **Port**: 8008
- **Framework**: FastAPI with CopilotKit

## Test the Integration

### 1. Open the Frontend
```bash
open http://localhost:7007
```

### 2. Verify CopilotKit Sidebar
- Look for the chat sidebar on the right side
- Should show: "Account Analysis Assistant"
- Initial message: "Hello! I can help you analyze accounts..."

### 3. Test API Route
```bash
curl http://localhost:7007/api/copilotkit | jq '.'
```

Expected response:
```json
{
  "status": "ok",
  "backend": {
    "status": "healthy",
    "service": "sergas-agents",
    "protocol": "ag-ui",
    "copilotkit_configured": true,
    "agents_registered": 3
  }
}
```

### 4. Test Backend Health
```bash
curl http://localhost:8008/health | jq '.'
```

Expected response:
```json
{
  "status": "healthy",
  "service": "sergas-agents",
  "protocol": "ag-ui",
  "copilotkit_configured": true,
  "agents_registered": 3
}
```

## Configuration Files

### Environment Variables (.env.local)
Located at: `frontend/.env.local`

```env
NEXT_PUBLIC_COPILOTKIT_API_KEY=ck_pub_e406823a48472880c136f49a521e5cf6
NEXT_PUBLIC_API_URL=http://localhost:8008
NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL=/api/copilotkit
```

### Key Files

1. **Layout** - `frontend/app/layout.tsx`
   - Contains `<CopilotProvider>` wrapper
   - Configures agent and authentication

2. **Main Page** - `frontend/app/page.tsx`
   - Contains `<CopilotSidebar>` component
   - Handles UI and interactions

3. **API Route** - `frontend/app/api/copilotkit/route.ts`
   - Proxies requests to backend
   - Handles SSE streaming

4. **Provider** - `frontend/components/copilot/CopilotProvider.tsx`
   - Configures CopilotKit
   - Manages authentication

## Architecture

```
Frontend (Next.js)           Backend (FastAPI)
Port: 7007                   Port: 8008
    │                            │
    ├─ CopilotProvider           │
    │   └─ CopilotSidebar        │
    │                            │
    └─ API Route                 │
        /api/copilotkit ────────▶│─ /copilotkit
                                 │
                                 ├─ orchestrator
                                 ├─ zoho_scout
                                 └─ memory_analyst
```

## Troubleshooting

### Frontend not loading?
```bash
# Check if process is running
lsof -ti:7007

# Restart frontend
cd frontend
npm run dev
```

### Backend not responding?
```bash
# Check if process is running
lsof -ti:8008

# Test health endpoint
curl http://localhost:8008/health
```

### CopilotKit UI not appearing?
1. Open browser console (F12)
2. Check for JavaScript errors
3. Verify CopilotProvider is in layout.tsx
4. Ensure no duplicate CopilotKit wrappers

### API route failing?
1. Check environment variables in `.env.local`
2. Verify backend is running
3. Test backend endpoint directly:
   ```bash
   curl http://localhost:8008/copilotkit
   ```

## Next Steps

### Test End-to-End Flow
1. Open frontend at http://localhost:7007
2. Click in the CopilotKit sidebar
3. Type a message
4. Verify response from GLM-4.6 model

### Explore Features
- **Account Analysis**: Click "Account Analysis" tab
- **Agent Dashboard**: Click "Agent Dashboard" tab
- **Approval Workflow**: Test recommendation approvals

### Development
- Frontend code: `frontend/`
- Components: `frontend/components/copilot/`
- API routes: `frontend/app/api/`
- Tests: `frontend/__tests__/`

## Support

### Documentation
- Fix Report: `docs/frontend/COPILOTKIT_INTEGRATION_FIX_REPORT.md`
- This Guide: `docs/frontend/COPILOTKIT_QUICK_START.md`

### Validation
Run comprehensive validation:
```bash
bash scripts/validate_copilotkit.sh
```

### Logs
Frontend logs:
```bash
# If using PM2 or background process
tail -f frontend.log

# If using npm run dev
# Logs appear in terminal
```

Backend logs:
```bash
tail -f backend.log
```

## Success Indicators

All these should be true:
- ✅ Frontend running on port 7007
- ✅ Backend running on port 8008
- ✅ CopilotKit sidebar visible in UI
- ✅ API route returns healthy status
- ✅ Backend health check passes
- ✅ No console errors in browser
- ✅ Validation script passes all tests

If all indicators are green, your CopilotKit integration is working correctly!
