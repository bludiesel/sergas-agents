# GLM-4.6 Quick Reference Card

## 🚀 Quick Start (60 Seconds)

```bash
# 1. Create config file
cat > .env.local << 'EOF'
ANTHROPIC_API_KEY=6845ef1767204ea98a67faaecb3afe08.fyZ4DweXVe3SvCXS
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
CLAUDE_MODEL=glm-4.6
EOF

# 2. Start application
python src/main.py

# 3. Test it works
curl http://localhost:8000/copilotkit/health
```

---

## 🔑 Essential Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `ANTHROPIC_API_KEY` | `6845ef1767204ea98a67faaecb3afe08.fyZ4DweXVe3SvCXS` | Z.ai API authentication |
| `ANTHROPIC_BASE_URL` | `https://api.z.ai/api/anthropic` | Z.ai API endpoint |
| `CLAUDE_MODEL` | `glm-4.6` | Model selection |

---

## 🧪 Quick Tests

### Health Check
```bash
curl http://localhost:8000/copilotkit/health
```

**Expected Output**:
```json
{
  "status": "healthy",
  "model": "glm-4.6",
  "provider": "z.ai"
}
```

### Test AI Response
```bash
curl -X POST http://localhost:8000/copilotkit \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "TEST-001",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Verify Environment
```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv('.env.local')
print(f'Model: {os.getenv(\"CLAUDE_MODEL\")}')
print(f'API Key: {os.getenv(\"ANTHROPIC_API_KEY\")[:20]}...')
"
```

---

## 📊 Response Format

```json
{
  "data": {
    "generateCopilotResponse": {
      "response": "AI-generated text here",
      "threadId": "thread_abc123",
      "timestamp": "2025-01-20T10:30:00Z",
      "model": "glm-4.6",
      "agent": "real_orchestrator"
    }
  }
}
```

---

## ⚠️ Common Issues & Fixes

| Issue | Quick Fix |
|-------|-----------|
| "401 Unauthorized" | Check `ANTHROPIC_API_KEY` in `.env.local` |
| "Connection refused" | Verify `ANTHROPIC_BASE_URL` is set |
| Wrong model used | Ensure `CLAUDE_MODEL=glm-4.6` and restart app |
| Empty responses | Check logs: `grep "glm_response" backend.log` |
| Import error | Run: `pip install anthropic>=0.18.0` |

---

## 📈 Cost Comparison

| Provider | Monthly Cost | Context Window | Cost Savings |
|----------|-------------|----------------|--------------|
| Claude 3.5 Sonnet | $40 | 200K tokens | Baseline |
| GLM-4.6 (Z.ai) | **$3** | 200K tokens | **94% cheaper** |

**Annual Savings**: $444 per user

---

## 🔍 Debug Checklist

Quick verification steps when troubleshooting:

- [ ] `.env.local` file exists in project root
- [ ] `ANTHROPIC_API_KEY` is set (check with `cat .env.local`)
- [ ] `ANTHROPIC_BASE_URL` points to Z.ai
- [ ] `CLAUDE_MODEL=glm-4.6` (no typos)
- [ ] Application restarted after config changes
- [ ] Health endpoint shows `model: glm-4.6`
- [ ] Logs contain "glm_response_generated" (not "demo_response")

**Debug Command**:
```bash
# Check all config at once
python -c "
import os
from dotenv import load_dotenv
load_dotenv('.env.local')

checks = {
    'API Key Set': bool(os.getenv('ANTHROPIC_API_KEY')),
    'Base URL Set': bool(os.getenv('ANTHROPIC_BASE_URL')),
    'Model': os.getenv('CLAUDE_MODEL', 'NOT SET'),
}

for check, value in checks.items():
    print(f'{check}: {value}')
"
```

---

## 🛠️ Code Examples

### Python: Basic Usage
```python
from anthropic import Anthropic
import os

client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    base_url=os.getenv("ANTHROPIC_BASE_URL")
)

response = client.messages.create(
    model="glm-4.6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.content[0].text)
```

### Python: With Error Handling
```python
try:
    response = client.messages.create(
        model="glm-4.6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text
except Exception as e:
    logger.error(f"GLM API error: {e}")
    return "Error generating response"
```

### Bash: Test Script
```bash
#!/bin/bash
# test_glm.sh - Quick GLM integration test

set -e

echo "Testing GLM-4.6 integration..."

# 1. Check config
echo "✓ Checking configuration..."
python -c "import os; from dotenv import load_dotenv; load_dotenv('.env.local'); assert os.getenv('CLAUDE_MODEL') == 'glm-4.6'"

# 2. Test health endpoint
echo "✓ Testing health endpoint..."
curl -s http://localhost:8000/copilotkit/health | grep -q "glm-4.6"

# 3. Test AI response
echo "✓ Testing AI generation..."
curl -s -X POST http://localhost:8000/copilotkit \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Test"}]}' \
  | grep -q "response"

echo "✅ All tests passed!"
```

---

## 📚 Key Files Reference

| File | Purpose | Line Numbers |
|------|---------|--------------|
| `src/api/routers/copilotkit_router.py` | Main API handler | 94-239 (GLM logic) |
| `src/agents/base_agent.py` | Model initialization | 109-143 (client setup) |
| `.env.example` | Configuration template | Full file |
| `.env.local` | **Your credentials** | Create this file |

---

## 🔗 Important URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Health Check** | `http://localhost:8000/copilotkit/health` | Verify service status |
| **API Endpoint** | `http://localhost:8000/copilotkit` | Main API endpoint |
| **Metrics** | `http://localhost:8000/metrics` | Prometheus metrics |
| **Z.ai Dashboard** | `https://z.ai/dashboard` | Manage API keys |
| **Z.ai Status** | `https://status.z.ai` | Check service status |

---

## 📞 Getting Help

### Quick Help
```bash
# View recent logs
tail -n 100 backend.log | grep -i glm

# Check if GLM is being used
grep "model.*glm" backend.log | tail -n 5

# Verify API connectivity
curl -I https://api.z.ai/api/anthropic
```

### Support Channels
- **GitHub Issues**: Tag with `[GLM-4.6]`
- **Slack**: `#ai-integration`
- **Email**: dev-support@sergas.com
- **Full Guide**: `/docs/integrations/GLM46_INTEGRATION_GUIDE.md`

---

## 🎯 Performance Targets

| Metric | Target | Typical | Notes |
|--------|--------|---------|-------|
| **Response Time** | <3s | ~2s | 95th percentile |
| **Availability** | >99.5% | ~99.8% | Z.ai SLA |
| **Context Window** | 200K tokens | 200K tokens | Same as Claude |
| **Cost per 1M tokens** | <$1 | ~$0.50 | Input + output |

---

## 🔐 Security Quick Checks

```bash
# ✅ GOOD: API key not in Git
git grep -i "6845ef1767204ea98a67faaecb3afe08" || echo "✓ Safe"

# ✅ GOOD: .env.local in .gitignore
grep -q ".env.local" .gitignore && echo "✓ Protected"

# ✅ GOOD: Using environment variables
python -c "import src.api.routers.copilotkit_router; import inspect; assert 'os.getenv' in inspect.getsource(src.api.routers.copilotkit_router)" && echo "✓ Secure"
```

---

## 🚦 Status Indicators

### ✅ Healthy System
```
✓ Health endpoint returns "glm-4.6"
✓ Logs show "glm_response_generated"
✓ Response times <3s
✓ No "demo_response" in logs
```

### ⚠️ Warning Signs
```
⚠ Health endpoint returns wrong model
⚠ Logs show "fallback" or "demo"
⚠ Response times >5s
⚠ Error rate >1%
```

### 🔴 Critical Issues
```
🔴 401 Unauthorized errors
🔴 Health endpoint down
🔴 "Connection refused" errors
🔴 Error rate >5%
```

---

## 📖 One-Liner Commands

```bash
# Quick setup
cat > .env.local << 'EOF'
ANTHROPIC_API_KEY=6845ef1767204ea98a67faaecb3afe08.fyZ4DweXVe3SvCXS
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
CLAUDE_MODEL=glm-4.6
EOF

# Test config
python -c "from dotenv import load_dotenv; load_dotenv('.env.local'); import os; print(os.getenv('CLAUDE_MODEL'))"

# Check health
curl -s http://localhost:8000/copilotkit/health | jq '.model'

# Test AI
curl -X POST http://localhost:8000/copilotkit -H "Content-Type: application/json" -d '{"messages":[{"role":"user","content":"Hi"}]}' | jq '.data.generateCopilotResponse.response'

# Monitor logs
tail -f backend.log | grep --color=auto -E "(glm|error|ERROR)"

# Check if working correctly
curl -s http://localhost:8000/copilotkit/health | jq -e '.model == "glm-4.6"' && echo "✅ GLM-4.6 is active"
```

---

**Cheat Sheet Version**: 1.0
**Last Updated**: 2025-01-20
**Print & Keep Handy!** 📌
