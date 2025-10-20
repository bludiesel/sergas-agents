# Proxy Solutions for Cognee with Z.ai

**Date**: 2025-10-19
**Status**: Research in progress

---

## 🎯 Goal: Use Proxies to Optimize Cognee LLM Access

Proxy solutions can help with:
- ✅ Cost optimization (route to cheapest provider)
- ✅ Fallback/redundancy (switch providers on failure)
- ✅ Rate limiting and caching
- ✅ Single configuration for multiple backends
- ❌ **Cannot convert Z.ai coding plan quota to API access**

---

## 🔧 Proxy Options

### Option 1: LiteLLM Proxy (Self-hosted, FREE)

**Best for**: Full control, cost optimization, local deployment

#### Setup

```bash
# Install LiteLLM
pip install litellm[proxy]

# Create config file: litellm_config.yaml
model_list:
  - model_name: smart-llm
    litellm_params:
      model: zhipuai/glm-4-plus
      api_key: your-z-ai-api-key
      api_base: https://api.z.ai/api/anthropic
  - model_name: smart-llm
    litellm_params:
      model: anthropic/claude-3-5-sonnet-20241022
      api_key: sk-ant-...
  - model_name: local-llm
    litellm_params:
      model: ollama/llama3.2
      api_base: http://localhost:11434

# Advanced: Cost-based routing
router_settings:
  routing_strategy: usage-based-routing  # Routes to cheapest available
  fallback_models: ["smart-llm"]

# Start proxy
litellm --config litellm_config.yaml --port 8000
```

#### Cognee Configuration

```bash
# .env
LLM_PROVIDER=openai  # LiteLLM provides OpenAI-compatible API
LLM_MODEL=smart-llm  # Virtual model name from config
LLM_ENDPOINT=http://localhost:8000
LLM_API_KEY=anything  # LiteLLM handles real keys
```

**Pros**:
- ✅ FREE (self-hosted)
- ✅ Automatic failover between providers
- ✅ Cost tracking and optimization
- ✅ Caching to reduce API calls
- ✅ Can mix Z.ai, Anthropic, OpenAI, Ollama

**Cons**:
- ⚠️ Still requires Z.ai API access (not coding plan quota)
- ⚠️ Need to run proxy server locally or on VPS

---

### Option 2: Portkey (Cloud-hosted, FREE tier)

**Best for**: Managed service, analytics, no server management

#### Setup

```bash
# Sign up at https://portkey.ai (free tier available)
# Get Portkey API key from dashboard
# Add your Z.ai API key as a "virtual key" in Portkey

# Portkey automatically handles routing and failover
```

#### Cognee Configuration

```bash
# .env
LLM_PROVIDER=openai
LLM_MODEL=glm-4-plus
LLM_ENDPOINT=https://api.portkey.ai/v1
LLM_API_KEY=your-portkey-api-key
# Add Portkey-Virtual-Key header with Z.ai credentials
```

**Pros**:
- ✅ No server management
- ✅ Free tier available
- ✅ Analytics dashboard
- ✅ Automatic fallback
- ✅ Request caching

**Cons**:
- ⚠️ Still requires Z.ai API access
- ⚠️ Adds another service dependency
- ⚠️ Potential privacy concerns (traffic goes through Portkey)

---

### Option 3: OpenRouter (Pay-per-token, Unified Access)

**Best for**: Access to 100+ models with single API key

#### Setup

```bash
# Sign up at https://openrouter.ai
# Add credits to account (~$5 minimum)
# Get API key
```

#### Cognee Configuration

```bash
# .env
LLM_PROVIDER=openai
LLM_MODEL=zhipuai/glm-4-plus
LLM_ENDPOINT=https://openrouter.ai/api/v1
LLM_API_KEY=your-openrouter-api-key
```

**Pros**:
- ✅ 100+ models with one API key
- ✅ Includes GLM-4, Claude, GPT-4, Llama, etc.
- ✅ Pay-as-you-go (no subscription)
- ✅ Automatic model fallback

**Cons**:
- ⚠️ Markup on top of provider costs (~10-20%)
- ⚠️ Still pay-per-token (not using Z.ai coding plan)
- ⚠️ Need to maintain credit balance

---

### Option 4: Hybrid Approach (LiteLLM + Ollama)

**Best for**: Minimize costs, maximum flexibility

#### Architecture

```
┌─────────────┐
│   Cognee    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  LiteLLM Proxy      │
│  (localhost:8000)   │
└──────┬──────────────┘
       │
       ├─► Ollama (local) ─────► FREE (80% of requests)
       ├─► Z.ai API ───────────► $14/1M tokens (complex queries)
       └─► Anthropic API ──────► $15/1M tokens (fallback)
```

#### Configuration

```yaml
# litellm_config.yaml
model_list:
  # Primary: Free local model
  - model_name: cognee-llm
    litellm_params:
      model: ollama/llama3.2
      api_base: http://localhost:11434
    model_info:
      mode: embedding  # Use for embeddings

  # Secondary: Z.ai for complex queries
  - model_name: cognee-llm-complex
    litellm_params:
      model: zhipuai/glm-4-plus
      api_key: your-z-ai-api-key
      api_base: https://api.z.ai/api/anthropic

  # Fallback: Anthropic
  - model_name: cognee-llm-fallback
    litellm_params:
      model: anthropic/claude-3-5-sonnet-20241022
      api_key: sk-ant-...

router_settings:
  routing_strategy: simple-shuffle  # Distribute load
  num_retries: 2
  fallback_models: ["cognee-llm-complex", "cognee-llm-fallback"]

# Cache settings (reduce API calls by 30-50%)
cache:
  type: redis
  host: localhost
  port: 6379
  ttl: 3600  # 1 hour cache
```

**Cost Savings**:
- Ollama (local): 80% of requests = $0
- Z.ai API: 15% of requests = ~$2-5/month
- Anthropic: 5% fallback = ~$1/month
- **Total**: $3-6/month instead of $10-30/month

---

## 🚨 Critical Limitation

**ALL proxy solutions still require Z.ai API access, not coding plan quota.**

**Why?**
- Z.ai coding plan uses OAuth authentication specific to coding tools
- Coding tools have embedded authentication flows
- Proxies cannot intercept/reuse this authentication for general API calls
- Z.ai's coding plan endpoint (`/api/coding/paas/v4`) is locked to tool usage

**Bottom line**: Proxies can optimize cost/performance but cannot convert coding plan quota to API access.

---

## 💡 Recommended Setup

### For Development/Testing
```yaml
# Use LiteLLM with Ollama (100% free)
LiteLLM Proxy
  └─► Ollama (local, free)
```

### For Production (Cost-optimized)
```yaml
# Use LiteLLM with hybrid approach
LiteLLM Proxy
  ├─► Ollama (80% of requests, free)
  ├─► Z.ai API (15% complex queries, ~$3/month)
  └─► Anthropic API (5% fallback, ~$1/month)
Total: ~$4-7/month
```

### For Simplicity (Managed)
```yaml
# Use Portkey with single provider
Portkey
  └─► Anthropic API (~$10-30/month)
```

---

## 📦 Quick Start: LiteLLM + Ollama

### Step 1: Install Dependencies

```bash
# Activate virtual environment
source venv312/bin/activate

# Install LiteLLM
pip install 'litellm[proxy]'

# Install Ollama (macOS)
brew install ollama

# Pull model
ollama pull llama3.2
ollama pull nomic-embed-text  # For embeddings

# Start Ollama server
ollama serve
```

### Step 2: Create LiteLLM Config

```bash
# Create config/litellm_config.yaml
mkdir -p config
cat > config/litellm_config.yaml <<'EOF'
model_list:
  - model_name: cognee-llm
    litellm_params:
      model: ollama/llama3.2
      api_base: http://localhost:11434

general_settings:
  master_key: sk-cognee-local-key  # Simple auth for local use

litellm_settings:
  success_callback: ["langfuse"]  # Optional: track usage
  cache: true
  cache_params:
    type: local
    ttl: 3600
EOF
```

### Step 3: Start LiteLLM Proxy

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start LiteLLM proxy
litellm --config config/litellm_config.yaml --port 8000
```

### Step 4: Configure Cognee

```bash
# Update .env.real
cat >> .env.real <<'EOF'

# LiteLLM Proxy Configuration (FREE with Ollama)
LLM_PROVIDER=openai
LLM_MODEL=cognee-llm
LLM_ENDPOINT=http://localhost:8000
LLM_API_KEY=sk-cognee-local-key

# Embeddings via Ollama
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_ENDPOINT=http://localhost:11434
EMBEDDING_API_KEY=ollama
EOF

# Copy to .env
cp .env.real .env
```

### Step 5: Test

```bash
source venv312/bin/activate
python scripts/setup_real_cognee.py
```

**Expected result**: Cognee working with 100% free local models via LiteLLM proxy!

---

## 📊 Cost Comparison with Proxies

| Setup | Monthly Cost | Speed | Setup Complexity |
|-------|--------------|-------|------------------|
| **Z.ai API (direct)** | $10-30 | Fast | Low |
| **Anthropic API (direct)** | $10-30 | Fast | Low |
| **LiteLLM + Ollama** | $0 | Medium | Medium |
| **LiteLLM + Hybrid** | $4-7 | Fast | High |
| **Portkey + Anthropic** | $10-30 | Fast | Low |
| **OpenRouter** | $12-35 | Fast | Low |

---

## 🎯 Final Recommendation

**For your specific case:**

1. **Start with LiteLLM + Ollama** (FREE)
   - Perfect for development and testing
   - No API costs
   - Learn Cognee behavior

2. **Add Z.ai API to LiteLLM config** when needed
   - Keep Ollama as primary (free)
   - Use Z.ai API for complex queries only
   - Total cost: ~$4-7/month instead of $10-30

3. **Keep Z.ai coding plan for Claude Code**
   - You're already using it successfully!
   - No changes needed there

**Total setup cost**: $3-15/month (Z.ai coding plan) + $0-7/month (Cognee via LiteLLM)

---

## 🔗 Resources

- LiteLLM Proxy: https://docs.litellm.ai/docs/proxy/quick_start
- Portkey: https://portkey.ai/
- OpenRouter: https://openrouter.ai/
- Ollama: https://ollama.ai/

---

**Summary**: Proxies can optimize costs but cannot use Z.ai coding plan quota. Best approach: Use LiteLLM proxy with Ollama (free) + Z.ai API for complex queries only (~$4-7/month total).
