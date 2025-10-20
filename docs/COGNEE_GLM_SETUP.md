# Using Cognee with Z.ai Coding Plan (GLM-4.6 Models)

**Status**: ⚠️ **REQUIRES SEPARATE API ACCESS**

## 🚨 CRITICAL: Z.ai Coding Plan vs API Access

**Z.ai Coding Plan** ($3-15/month):
- ✅ Works with: Claude Code, Cline, OpenCode, Roo Code, Windsurf, Cursor
- ❌ Does NOT work with: Direct API calls, Python scripts, Cognee
- Quota: Only consumed when using supported coding tools
- Endpoint: `https://api.z.ai/api/coding/paas/v4` (coding tools only)

**Z.ai API Access** (pay-per-token):
- ✅ Works with: Cognee, Python scripts, any application
- ❌ Separate billing from coding plan subscription
- Endpoint: `https://api.z.ai/api/anthropic` (Anthropic-compatible)
- Cost: ~$14 per 1M tokens (glm-4-plus)

**For Cognee**: You MUST use Z.ai API access (separate from coding plan)

---

## Option 1: Z.ai API Access (For Cognee)

### Configuration

```bash
# In .env.real or .env

# Use Anthropic-compatible endpoint
LLM_PROVIDER=openai  # Uses OpenAI SDK format
LLM_MODEL=glm-4-plus  # or glm-4-flash, glm-4-air
LLM_ENDPOINT=https://api.z.ai/api/anthropic
LLM_API_KEY=your-z-ai-api-key-here

# Alternative: Custom provider
# LLM_PROVIDER=custom
# LLM_MODEL=glm-4-plus
# LLM_ENDPOINT=https://api.z.ai/api/anthropic
# LLM_API_KEY=your-z-ai-api-key-here
```

### Where to Get API Key

1. Go to: https://z.ai/
2. Login to your account
3. Navigate to API Keys section (separate from coding plan)
4. Generate new API key for programmatic access
5. Note: This is separate billing from your coding plan subscription

---

## Option 2: Alternative LLM Providers (If Z.ai API is too expensive)

If you want to avoid separate Z.ai API billing, consider these alternatives:

### Anthropic API (Recommended - Works with Your Max Subscription)

```bash
# Use your Claude Max subscription API access
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_API_KEY=sk-ant-...  # Get from console.anthropic.com
# Note: This is separate from Max subscription OAuth used by Claude SDK
```

**Cost**: $15 per 1M tokens (similar to Z.ai glm-4-plus)

### OpenAI API

```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo
LLM_API_KEY=sk-...  # Get from platform.openai.com
```

**Cost**: $30 per 1M tokens (more expensive)

### Local Ollama (FREE)

```bash
# Install Ollama: brew install ollama
# Pull model: ollama pull llama3.2

LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
LLM_ENDPOINT=http://localhost:11434
LLM_API_KEY=ollama
```

**Cost**: FREE (runs locally, slower but no API charges)

---

## Configuration Methods

### Method 1: Environment Variables (.env file)

```bash
# .env or .env.real
LLM_PROVIDER=custom
LLM_MODEL=glm-4-plus
LLM_ENDPOINT=https://open.bigmodel.cn/api/paas/v4
LLM_API_KEY=your-api-key
```

### Method 2: Programmatic Configuration

```python
import cognee

# Configure Zhipu AI GLM
cognee.config.set_llm_provider("custom")
cognee.config.set_llm_model("glm-4-plus")
cognee.config.set_llm_endpoint("https://open.bigmodel.cn/api/paas/v4")
cognee.config.set_llm_api_key("your-api-key")
```

### Method 3: LLM Config Object

```python
from cognee.infrastructure.llm.config import LLMConfig

config = LLMConfig(
    llm_provider="custom",
    llm_model="glm-4-plus",
    llm_endpoint="https://open.bigmodel.cn/api/paas/v4",
    llm_api_key="your-api-key"
)
```

---

## Available GLM Models

| Model | Context | Best For | Cost |
|-------|---------|----------|------|
| **glm-4-plus** | 128K | General tasks, high quality | ~¥0.1/1K tokens |
| **glm-4-flash** | 128K | Fast responses, cost-effective | ~¥0.01/1K tokens |
| **glm-4-9b-chat** | 200K | Long context, open-source | Free (self-hosted) |
| **glm-4-air** | 128K | Balanced performance/cost | ~¥0.001/1K tokens |

---

## Test Configuration

```python
import asyncio
import cognee

# Configure GLM-4
cognee.config.set_llm_provider("custom")
cognee.config.set_llm_model("glm-4-plus")
cognee.config.set_llm_endpoint("https://open.bigmodel.cn/api/paas/v4")
cognee.config.set_llm_api_key("your-zhipu-api-key")

async def test_glm():
    # Test with sample data
    text = "Cognee is a knowledge graph system for AI agents."

    await cognee.add(text, dataset_name="test-glm")
    await cognee.cognify()

    results = await cognee.search(
        cognee.SearchType.INSIGHTS,
        query_text="What is Cognee?"
    )

    for result in results:
        print(result)

# Run test
asyncio.run(test_glm())
```

---

## Embedding Models

Cognee also needs an embedding model. Options:

### Option 1: Zhipu AI Embeddings
```bash
EMBEDDING_PROVIDER=custom
EMBEDDING_MODEL=embedding-3  # Zhipu's embedding model
EMBEDDING_ENDPOINT=https://open.bigmodel.cn/api/paas/v4
EMBEDDING_API_KEY=your-zhipu-api-key
```

### Option 2: Local Ollama Embeddings (Free)
```bash
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_ENDPOINT=http://localhost:11434
EMBEDDING_API_KEY=ollama
```

### Option 3: OpenAI Embeddings (If you have access)
```bash
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=your-openai-key
```

---

## Complete .env Configuration Example

```bash
# Cognee with Z.ai API (GLM-4.6 Models)

# ⚠️ IMPORTANT: This uses Z.ai API access (pay-per-token)
# Your Z.ai coding plan quota is NOT used for this configuration
# Coding plan quota only works in coding tools (Claude Code, Cline, etc.)

# LLM Configuration - Z.ai API
LLM_PROVIDER=openai  # Uses OpenAI-compatible format
LLM_MODEL=glm-4-plus  # or glm-4-flash (cheaper), glm-4-air (fastest)
LLM_ENDPOINT=https://api.z.ai/api/anthropic
LLM_API_KEY=your-z-ai-api-key-here

# Embedding Configuration (Choose one)

# Option 1: Z.ai embeddings (if available)
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=embedding-3
EMBEDDING_ENDPOINT=https://api.z.ai/api/anthropic
EMBEDDING_API_KEY=your-z-ai-api-key-here

# Option 2: Local Ollama (FREE - recommended to save costs)
# EMBEDDING_PROVIDER=ollama
# EMBEDDING_MODEL=nomic-embed-text
# EMBEDDING_ENDPOINT=http://localhost:11434
# EMBEDDING_API_KEY=ollama

# Cognee Settings
COGNEE_MOCK_MODE=false
ENABLE_COGNEE_MEMORY=true
COGNEE_WORKSPACE=sergas-accounts
```

---

## Advantages of Using GLM-4.6

✅ **Lower Cost**: Significantly cheaper than OpenAI/Anthropic
✅ **Long Context**: 128K-200K tokens context window
✅ **Chinese+English**: Excellent bilingual support
✅ **Tool Calling**: Supports function/tool calling like OpenAI
✅ **Fast**: glm-4-flash is very quick and cost-effective

---

## Troubleshooting

### Issue: "Connection failed"
**Solution**: Check if you're using the correct endpoint:
- China users: `https://open.bigmodel.cn/api/paas/v4`
- Global users: Check z.ai documentation for global endpoint

### Issue: "Invalid API key"
**Solution**:
1. Verify API key from Zhipu dashboard
2. Check if key has proper permissions
3. Ensure billing is active

### Issue: "Model not found"
**Solution**: Use exact model names:
- `glm-4-plus` (not `glm-4.6`)
- `glm-4-flash`
- `glm-4-air`

### Issue: "Embedding errors"
**Solution**: Make sure embedding provider matches LLM provider or use local Ollama:
```bash
# Install Ollama
brew install ollama  # macOS
ollama pull nomic-embed-text
ollama serve
```

---

## Migration from Mock to GLM-4.6

```bash
# 1. Edit .env.real with GLM configuration above

# 2. Copy to .env
cp .env.real .env

# 3. Update Cognee mock mode
sed -i '' 's/COGNEE_MOCK_MODE=true/COGNEE_MOCK_MODE=false/' .env

# 4. Test setup
source venv312/bin/activate
python scripts/setup_real_cognee.py
```

---

## Cost Comparison

| Provider | Model | Cost per 1M tokens | Notes |
|----------|-------|-------------------|-------|
| **Zhipu GLM-4-plus** | glm-4-plus | ~$14 | High quality |
| **Zhipu GLM-4-flash** | glm-4-flash | ~$1.4 | Fast, cheap |
| **Anthropic** | claude-3-5-sonnet | $15 | Claude Max free tier |
| **OpenAI** | gpt-4-turbo | $30 | Expensive |

**Recommendation**: Use **glm-4-flash** for development, **glm-4-plus** for production.

---

## Next Steps

1. Get Zhipu AI API key from https://open.bigmodel.cn/
2. Configure .env.real with GLM settings above
3. Copy to .env: `cp .env.real .env`
4. Test: `python scripts/setup_real_cognee.py`
5. Run agents: `python -m src.orchestrator.main_orchestrator`

---

## 🚨 Z.ai Coding Plan - Key Clarifications

**What IS included in your Z.ai coding plan:**
- ✅ Claude Code tool integration (this session right now!)
- ✅ Cline, OpenCode, Roo Code, Windsurf, Cursor
- ✅ GLM-4.6 model access within supported tools
- ✅ Quota resets based on your plan tier ($3/15/50 per month)

**What is NOT included in your Z.ai coding plan:**
- ❌ Direct API calls from Python scripts
- ❌ Cognee integration (requires API access)
- ❌ Custom applications or services
- ❌ Server-to-server integrations

**For Cognee specifically:**
- You'll need **Z.ai API access** (separate billing)
- OR use **Anthropic API** ($15/1M tokens, same as Z.ai)
- OR use **local Ollama** (FREE but slower)

**Recommendation**:
- Keep your Z.ai coding plan for Claude Code (you're using it right now!)
- For Cognee, use Anthropic API or Ollama to avoid separate Z.ai API billing
- Total cost: $0-15/month for Cognee if using Anthropic API

---

**Summary**: Z.ai coding plan quota cannot be used with Cognee. You need separate Z.ai API access OR use Anthropic/Ollama instead.
