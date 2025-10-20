# Frontend Quick Start Guide

Get the Sergas Account Manager frontend up and running in 5 minutes.

## Prerequisites

- Node.js 18+ installed
- Backend running on `http://localhost:8000`

## Quick Setup

```bash
# 1. Navigate to frontend directory
cd /Users/mohammadabdelrahman/Projects/sergas_agents/frontend

# 2. Install dependencies (first time only)
npm install

# 3. Configure environment
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_TOKEN=your-auth-token-here
EOF

# 4. Start development server
npm run dev
```

Open browser: http://localhost:3000

## Verify Installation

You should see:
- Sergas Account Manager header
- Agent Status sidebar (Zoho Scout, Memory Analyst, Recommendation Author)
- CopilotKit chat interface
- "Hello! I can help you analyze accounts..." initial message

## Test Backend Connection

1. Type a message in chat: "Analyze account ACC-123"
2. Watch the Agent Status panel for updates
3. Review any approval requests in modal dialogs

## Troubleshooting

### "Cannot connect to backend"

```bash
# Check if backend is running
curl http://localhost:8000/health

# If not, start backend:
cd /Users/mohammadabdelrahman/Projects/sergas_agents
uvicorn src.api.main:app --reload --port 8000
```

### "Module not found" errors

```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Build errors

```bash
# Clear build cache
rm -rf .next
npm run build
```

## Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## File Structure

```
frontend/
├── app/page.tsx              # Main application
├── components/
│   ├── ApprovalModal.tsx     # Approval workflow
│   ├── AgentStatusPanel.tsx  # Agent tracking
│   └── ToolCallCard.tsx      # Tool display
└── .env.local                # Configuration
```

## Next Steps

1. Review `/frontend/README.md` for detailed documentation
2. Check `/docs/frontend/FRONTEND_SETUP_COMPLETE.md` for implementation details
3. Test approval workflow with backend
4. Customize components as needed

## Support

- **Documentation**: `/frontend/README.md`
- **Implementation Guide**: `/docs/frontend/FRONTEND_SETUP_COMPLETE.md`
- **Backend Docs**: `/docs/research/COPILOTKIT_UI_Custom_Backend_Integration.md`
