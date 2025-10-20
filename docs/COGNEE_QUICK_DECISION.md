# Cognee Configuration - Quick Decision Guide

**Last Updated**: 2025-10-19

---

## 🎯 Pick Your Cognee Configuration (30-Second Decision)

### Question 1: Do you want to spend money?

**NO** → **Option A: LiteLLM + Ollama (FREE)**
- Cost: $0/month
- Speed: Medium
- Setup: 5 minutes
- Command: `./scripts/setup_litellm_proxy.sh`

**YES** → Go to Question 2

---

### Question 2: Do you want best quality or best value?

**Best Quality** → **Option B: Anthropic API**
- Cost: $10-30/month
- Speed: Fast
- Quality: Excellent (Claude 3.5 Sonnet)
- Setup: 2 minutes (just add API key)

**Best Value** → **Option C: Hybrid (LiteLLM + API Fallback)**
- Cost: $4-7/month
- Speed: Fast
- Strategy: Free Ollama for 80% of requests, paid API for 20%
- Setup: 10 minutes

---

## 📊 Full Comparison Matrix

| Option | Monthly Cost | Speed | Quality | Setup Time | Privacy | Best For |
|--------|--------------|-------|---------|------------|---------|----------|
| **A. LiteLLM + Ollama** | $0 | Medium | Good | 5 min | Excellent | Testing, learning, budget |
| **B. Anthropic API** | $10-30 | Fast | Excellent | 2 min | Good | Production, quality |
| **C. Hybrid** | $4-7 | Fast | Excellent | 10 min | Excellent | Best value |
| **D. Z.ai API** | $10-30 | Fast | Very Good | 2 min | Good | Want GLM models |
| **E. OpenAI API** | $20-60 | Fast | Excellent | 2 min | Good | Already using GPT-4 |

---

## 🚀 Quick Start Commands

### Option A: FREE (LiteLLM + Ollama)

```bash
# 1. Setup (one time)
./scripts/setup_litellm_proxy.sh

# 2. Start proxy (every time)
./scripts/start_litellm.sh  # Leave running in terminal

# 3. Test
source venv312/bin/activate
python scripts/setup_real_cognee.py
```

**Monthly cost**: $0
**What you get**: Fully functional Cognee with local models

---

### Option B: Anthropic API

```bash
# 1. Get API key from https://console.anthropic.com/

# 2. Edit .env.real
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_API_KEY=sk-ant-your-key-here

# 3. Test
cp .env.real .env
source venv312/bin/activate
python scripts/setup_real_cognee.py
```

**Monthly cost**: ~$10-30
**What you get**: Production-ready Cognee with Claude 3.5

---

### Option C: Hybrid (Best Value)

```bash
# 1. Setup LiteLLM + Ollama
./scripts/setup_litellm_proxy.sh

# 2. Edit config/litellm_config.yaml - add API fallback:
model_list:
  - model_name: cognee-llm
    litellm_params:
      model: ollama/llama3.2
  - model_name: cognee-llm-fallback
    litellm_params:
      model: anthropic/claude-3-5-sonnet-20241022
      api_key: sk-ant-...

# 3. Start and test
./scripts/start_litellm.sh
python scripts/setup_real_cognee.py
```

**Monthly cost**: ~$4-7
**What you get**: Free for most requests, paid API only when needed

---

### Option D: Z.ai API

```bash
# 1. Get Z.ai API key (NOT coding plan, separate API access)
# Visit: https://z.ai/ → API Keys section

# 2. Edit .env.real
LLM_PROVIDER=openai
LLM_MODEL=glm-4-plus
LLM_ENDPOINT=https://api.z.ai/api/anthropic
LLM_API_KEY=your-z-ai-api-key

# 3. Test
cp .env.real .env
source venv312/bin/activate
python scripts/setup_real_cognee.py
```

**Monthly cost**: ~$10-30
**What you get**: GLM-4.6 models (Chinese/English optimized)

---

## ⚠️ Important Notes

### About Z.ai Coding Plan

**Your Z.ai coding plan quota CANNOT be used for Cognee.**

- ✅ Coding plan works with: Claude Code, Cline, Cursor, etc.
- ❌ Coding plan does NOT work with: Cognee, Python scripts, APIs
- 💡 For Cognee: Use separate Z.ai API access OR choose Option A/B/C

See: `docs/ZAI_CODING_PLAN_ANALYSIS.md`

### About Claude SDK

Your Claude SDK is already configured to use **Max subscription via OAuth** (no API charges).
This is completely separate from Cognee's LLM needs.

---

## 💡 Recommendations by Use Case

### "I'm just testing the system"
→ **Option A** (LiteLLM + Ollama, FREE)

### "I need production quality now"
→ **Option B** (Anthropic API, $10-30/month)

### "I want to minimize costs long-term"
→ **Option C** (Hybrid, $4-7/month)

### "I specifically want GLM models"
→ **Option D** (Z.ai API, $10-30/month)

### "I'm already paying for OpenAI"
→ **Option E** (OpenAI API, $20-60/month)

---

## 📚 Detailed Documentation

- **Full proxy guide**: `docs/PROXY_SOLUTIONS_FOR_COGNEE.md`
- **Z.ai analysis**: `docs/ZAI_CODING_PLAN_ANALYSIS.md`
- **Complete setup**: `docs/SETUP_COMPLETE_GUIDE.md`
- **GLM configuration**: `docs/COGNEE_GLM_SETUP.md`

---

## 🆘 Quick Troubleshooting

**Problem**: "LiteLLM proxy won't start"
```bash
# Solution: Start Ollama first
ollama serve
# Then start LiteLLM
./scripts/start_litellm.sh
```

**Problem**: "Cognee still using mocks"
```bash
# Solution: Check COGNEE_MOCK_MODE in .env
grep COGNEE_MOCK_MODE .env
# Should be: COGNEE_MOCK_MODE=false
```

**Problem**: "API key invalid"
```bash
# Solution: Verify you're using correct provider/key combo
# Z.ai coding plan key ≠ Z.ai API key
# Max subscription OAuth ≠ Anthropic API key
```

---

**TL;DR**: Start with Option A (free), upgrade to B/C when needed.
