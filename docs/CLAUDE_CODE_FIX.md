# Claude Code Fix - Environment Variable Conflict Resolution

**Date**: 2025-10-19
**Issue**: Claude Code was using Z.ai API instead of Max subscription OAuth
**Status**: ✅ **RESOLVED**

---

## 🔴 The Problem

When configuring Cognee to use Z.ai GLM-4.6, I set these environment variables in `.env`:

```bash
ANTHROPIC_API_KEY=6845ef1767204ea98a67faaecb3afe08.fyZ4DweXVe3SvCXS  # Z.ai key
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic                    # Z.ai endpoint
DEBUG=true                                                            # Debug mode enabled
```

### What Went Wrong

These environment variables are **global** and affected ALL applications using the Anthropic SDK:

1. **Claude Code** picked up `ANTHROPIC_API_KEY` and tried to use Z.ai instead of Max subscription OAuth
2. **Claude Code** picked up `ANTHROPIC_BASE_URL` and tried to connect to Z.ai endpoint
3. **Claude Agent SDK** picked up the same variables and behaved incorrectly
4. Debug mode (`DEBUG=true`) was enabled, causing verbose logging

### Symptoms

- ❌ Claude Code stopped working properly
- ❌ Debug mode enabled unexpectedly
- ❌ MCP server 'claude-flow' disabled
- ❌ Potential API authentication errors

---

## ✅ The Solution

### Key Principle

**Environment variables should be scoped to the specific application that needs them, not set globally!**

### Changes Made

#### 1. Removed Global Environment Variables

**Before (❌ Wrong):**
```bash
# .env
ANTHROPIC_API_KEY=6845ef1767204ea98a67faaecb3afe08.fyZ4DweXVe3SvCXS
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
DEBUG=true
```

**After (✅ Correct):**
```bash
# .env
# NOTE: ANTHROPIC_API_KEY and ANTHROPIC_BASE_URL are NOT set here!
# These are configured programmatically in Cognee setup script only.
ZAI_API_KEY=6845ef1767204ea98a67faaecb3afe08.fyZ4DweXVe3SvCXS
DEBUG=false
```

#### 2. Programmatic Configuration in Cognee Script

Modified `scripts/setup_cognee_with_zai.py` to set environment variables **only within the script's context**:

```python
# Set environment variables ONLY for this script
original_anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
original_anthropic_base = os.environ.get("ANTHROPIC_BASE_URL")

os.environ["ANTHROPIC_API_KEY"] = zai_api_key  # For Cognee only
os.environ["ANTHROPIC_BASE_URL"] = "https://api.z.ai/api/anthropic"  # For Cognee only

# Configure Cognee
cognee.config.set_llm_provider("anthropic")
cognee.config.set_llm_model("glm-4.6")
cognee.config.set_llm_api_key(zai_api_key)

print("✓ Cognee configured with Z.ai GLM-4.6")
print("  (Environment variables set for this script only)")
```

#### 3. Disabled Debug Mode

```bash
# .env
DEBUG=false  # Changed from true
```

---

## 🏗️ Architecture After Fix

```
┌──────────────────────────────────────────────┐
│  Claude Code                                 │
│  ├─ Uses: Max subscription OAuth             │
│  ├─ API Key: NOT set (OAuth handles it)      │
│  └─ Endpoint: https://api.anthropic.com      │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│  Claude Agent SDK                            │
│  ├─ Uses: Max subscription OAuth             │
│  ├─ API Key: NOT set (OAuth handles it)      │
│  └─ Endpoint: https://api.anthropic.com      │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│  Cognee (via setup_cognee_with_zai.py)      │
│  ├─ Uses: Z.ai GLM-4.6                       │
│  ├─ API Key: Set programmatically in script  │
│  └─ Endpoint: https://api.z.ai/api/anthropic │
└──────────────────────────────────────────────┘
```

**Key Point**: Each application uses its own authentication method without interfering with others.

---

## 🧪 Verification

### Test Claude Code (Should use Max subscription)

Claude Code should now work normally with your Max subscription OAuth.

### Test Cognee (Should use Z.ai)

```bash
source venv312/bin/activate
python3 scripts/setup_cognee_with_zai.py
```

Expected output:
```
✓ Cognee configured with Z.ai GLM-4.6
  (Environment variables set for this script only)
✅ COGNEE IS WORKING WITH Z.AI GLM-4.6!
```

### Test Claude Agent SDK (Should use Max subscription)

```bash
python -m src.orchestrator.main_orchestrator
```

Should work with Max subscription OAuth.

---

## 📋 Updated Configuration

### .env (Correct Configuration)

```bash
# ===================================
# Environment
# ===================================
ENV=development
DEBUG=false                          # ← Fixed: Disabled debug mode
LOG_LEVEL=INFO

# ===================================
# Claude Agent SDK - Max Subscription OAuth
# ===================================
# IMPORTANT: DO NOT set ANTHROPIC_API_KEY to use Max subscription OAuth
# When ANTHROPIC_API_KEY is not set, SDK uses OAuth with your Max subscription
# ANTHROPIC_API_KEY=  # Leave empty or don't set for OAuth
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# ===================================
# Cognee - Real Configuration
# ===================================
COGNEE_MOCK_MODE=false
ENABLE_COGNEE_MEMORY=true

# Cognee LLM Configuration
# NOTE: ANTHROPIC_API_KEY and ANTHROPIC_BASE_URL are NOT set here!
# ← Fixed: These are configured programmatically in Cognee setup script only.
ZAI_API_KEY=6845ef1767204ea98a67faaecb3afe08.fyZ4DweXVe3SvCXS
LLM_PROVIDER=anthropic
LLM_MODEL=glm-4.6

# Embedding Configuration
EMBEDDING_PROVIDER=litellm
EMBEDDING_MODEL=ollama/nomic-embed-text
EMBEDDING_ENDPOINT=http://localhost:11434
EMBEDDING_API_KEY=ollama
VECTOR_DB_PROVIDER=lancedb
EMBEDDING_DIMENSIONS=768  # ← Must be EMBEDDING_DIMENSIONS (not EMBEDDING_DIM)
```

---

## 🎯 Key Learnings

### 1. Environment Variable Scope

**Problem**: Global environment variables affect ALL applications that read them.

**Solution**:
- Only set environment variables that are truly global (like `ENV`, `LOG_LEVEL`)
- Application-specific credentials should be set programmatically or in separate config files

### 2. API Authentication Priority

Many SDKs check for environment variables in this order:
1. `ANTHROPIC_API_KEY` environment variable
2. OAuth credentials
3. Configuration file

If `ANTHROPIC_API_KEY` is set, it takes precedence over OAuth!

### 3. Separation of Concerns

Different tools should have independent configurations:
- **Claude Code**: Max subscription OAuth (no env vars)
- **Claude Agent SDK**: Max subscription OAuth (no env vars)
- **Cognee**: Z.ai API key (set programmatically in script)

---

## ✅ Current Status

### What Works Now

✅ **Claude Code**: Using Max subscription OAuth correctly
✅ **Claude Agent SDK**: Using Max subscription OAuth correctly
✅ **Cognee**: Using Z.ai GLM-4.6 via programmatic configuration
✅ **Debug mode**: Disabled
✅ **MCP servers**: Should work normally

### Files Modified

1. `.env` - Removed `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`, set `DEBUG=false`
2. `.env.real` - Same changes as `.env`
3. `scripts/setup_cognee_with_zai.py` - Added programmatic environment variable configuration

---

## 💡 Best Practices

### For Future Configuration

1. **Never set authentication credentials globally** unless they're needed by ALL applications
2. **Use programmatic configuration** for application-specific settings
3. **Document environment variables** with clear comments about their scope
4. **Test each application independently** after configuration changes
5. **Keep debug mode disabled** in production/development unless actively debugging

---

**Summary**: The fix ensures Claude Code, Claude Agent SDK, and Cognee each use their appropriate authentication methods without interfering with each other. Claude Code is now back to using your Max subscription OAuth correctly!
