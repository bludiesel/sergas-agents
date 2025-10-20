# CopilotKit Integration Quick Reference

## Installation

```bash
# Activate virtual environment
source venv312/bin/activate

# Install CopilotKit SDK and dependencies
pip install copilotkit langgraph langchain langchain-anthropic

# Or install from requirements.txt (already includes these)
pip install -r requirements.txt
```

## Configuration

### Environment Variables (.env)
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional (has defaults)
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Usage

### Basic Setup (Already Done in src/main.py)
```python
from fastapi import FastAPI
from src.copilotkit import setup_copilotkit_endpoint

app = FastAPI()

# Setup CopilotKit endpoint
copilotkit = setup_copilotkit_endpoint(app, endpoint="/copilotkit")
```

### Register Agents (Future)
```python
# After agent wrappers are created
from docs.sparc.templates.orchestrator_wrapper import create_orchestrator_graph
from docs.sparc.templates.zoho_scout_wrapper import create_zoho_scout_graph

# Create agent graphs
orchestrator = create_orchestrator_graph()
zoho_scout = create_zoho_scout_graph()

# Register with CopilotKit
copilotkit.register_agent("orchestrator", orchestrator)
copilotkit.register_agent("zoho_scout", zoho_scout)
```

## API Endpoints

### Existing Endpoints (Unchanged)
- `POST /api/copilotkit` - AG UI Protocol SSE streaming
- `GET /api/copilotkit/health` - Health check
- `POST /api/approval/respond` - Approval workflow

### New CopilotKit Endpoint
- `POST /copilotkit` - CopilotKit SDK agent communication
  - Requires: CopilotKit SDK installed + API key configured
  - Format: Standard CopilotKit message format

## Testing

### Automated Test
```bash
python scripts/test_fastapi_startup.py
```

### Start Development Server
```bash
uvicorn src.main:app --reload --port 8000
```

### Manual Tests
```bash
# Check root endpoint
curl http://localhost:8000/

# Check health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs
```

## File Locations

### Integration Code
- `/src/copilotkit/__init__.py` - Module exports
- `/src/copilotkit/fastapi_integration.py` - Main integration logic

### Main Application
- `/src/main.py` - FastAPI app with CopilotKit setup

### Testing
- `/scripts/test_fastapi_startup.py` - Validation script

### Documentation
- `/docs/sparc/integration/copilotkit_integration_report.md` - Full report
- `/docs/sparc/integration/copilotkit_quick_reference.md` - This file

## Integration Status

### ✅ Complete
- FastAPI integration module
- Graceful degradation (optional SDK)
- Endpoint registration
- Error handling
- Testing framework
- Documentation

### ⏳ Pending (Next Phase)
- Agent wrapper implementations
- Agent registration in main.py
- Frontend CopilotKit React integration

## Common Issues

### "No module named 'copilotkit'"
**Solution**: Install CopilotKit SDK
```bash
pip install copilotkit
```

### "ANTHROPIC_API_KEY must be provided"
**Solution**: Configure API key in .env
```bash
echo "ANTHROPIC_API_KEY=sk-ant-your-key" >> .env
```

### CopilotKit endpoint not appearing
**Expected**: CopilotKit SDK not installed or not configured
**Check logs for**:
- `copilotkit_sdk_not_configured`
- `copilotkit_sdk_setup_failed`

## Logging

### Success Messages
```json
{"event": "copilotkit_sdk_initialized", "model": "claude-3-5-sonnet-20241022"}
{"event": "copilotkit_agent_registered", "agent_name": "orchestrator"}
{"event": "copilotkit_endpoint_added", "endpoint": "/copilotkit"}
```

### Warning Messages
```json
{"event": "copilotkit_sdk_not_configured", "note": "..."}
```

### Error Messages
```json
{"event": "copilotkit_sdk_setup_failed", "error": "..."}
```

## Architecture

```
┌─────────────────────────────────────────────┐
│           FastAPI Application               │
├─────────────────────────────────────────────┤
│  Existing Routes:                           │
│  • POST /api/copilotkit (AG UI SSE)        │
│  • POST /api/approval/respond               │
│  • GET  /health                             │
├─────────────────────────────────────────────┤
│  New CopilotKit Route:                      │
│  • POST /copilotkit (CopilotKit SDK)       │
│    └─> CopilotKitIntegration               │
│         ├─> CopilotKit SDK                  │
│         ├─> Agent Registry                  │
│         └─> LangGraph Agents                │
└─────────────────────────────────────────────┘
```

## Next Steps

1. **Install Dependencies**
   ```bash
   pip install copilotkit langgraph langchain langchain-anthropic
   ```

2. **Configure API Key**
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-your-key
   ```

3. **Start Server**
   ```bash
   uvicorn src.main:app --reload
   ```

4. **Verify Integration**
   ```bash
   python scripts/test_fastapi_startup.py
   ```

5. **Wait for Agent Wrappers**
   - Once wrappers are created, register them in main.py
   - Test end-to-end agent communication

## Support

- **Documentation**: `/docs/sparc/integration/`
- **Templates**: `/docs/sparc/templates/`
- **Main App**: `/src/main.py`
- **Integration Module**: `/src/copilotkit/`

---

**Status**: Ready for agent wrapper integration
**Last Updated**: 2025-10-19
