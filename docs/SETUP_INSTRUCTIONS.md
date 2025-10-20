# Setup Instructions - Dual Authentication Strategy

## Overview

This project uses a **dual authentication strategy** to allow:
- **Claude Code** to use your Max subscription ($200/month) for development
- **Your Python application** to use GLM-4.6 via Z.ai ($3/month) for production

## Quick Setup

### 1. Verify Files Exist

```bash
ls -la .env .env.local .env.example
```

You should see:
- `.env` - Base configuration (NO API keys)
- `.env.local` - Application runtime config (HAS GLM-4.6 API keys)
- `.env.example` - Template for team

### 2. Verify .env is Clean

```bash
./scripts/check_auth_config.sh
```

**Expected output:**
```
✅ Authentication configuration looks good!
   Claude Code will use your Max subscription.
```

If you see warnings, run:
```bash
# Comment out API keys in .env
sed -i.bak '/^ANTHROPIC_API_KEY=/s/^/# /' .env
sed -i.bak '/^ANTHROPIC_BASE_URL=/s/^/# /' .env

# Verify fix
./scripts/check_auth_config.sh
```

### 3. Update Your Python Application

Ensure your application loads **both** environment files:

**Option A: Update main.py** (Recommended)
```python
# src/main.py
from dotenv import load_dotenv

# Load .env first (base configuration)
load_dotenv()

# Load .env.local (overrides for GLM-4.6)
load_dotenv('.env.local', override=True)

# Now your application uses GLM-4.6 while Claude Code uses Max subscription
```

**Option B: Environment Variable**
```bash
# Set this before running your app
export DOTENV_OVERRIDE=.env.local

# Then run your app
python src/main.py
```

### 4. Test Both Modes

**Test Claude Code (Should use subscription):**
```bash
# This should show: "✅ Claude Code will use your Max subscription"
./scripts/check_auth_config.sh

# Ask Claude Code to do something
# It should use claude-3-5-sonnet-20241022 via Max subscription
```

**Test Your Application (Should use GLM-4.6):**
```python
# scripts/test_app_auth.py
from dotenv import load_dotenv
import os

load_dotenv()
load_dotenv('.env.local', override=True)

print(f"ANTHROPIC_BASE_URL: {os.getenv('ANTHROPIC_BASE_URL')}")
print(f"CLAUDE_MODEL: {os.getenv('CLAUDE_MODEL')}")

# Expected output:
# ANTHROPIC_BASE_URL: https://api.z.ai/api/anthropic
# CLAUDE_MODEL: glm-4.6
```

## File Structure Explained

```
.
├── .env                    # Base config (NO API keys) - Git tracked
├── .env.local             # App overrides (HAS GLM-4.6) - Gitignored
├── .env.claude-code       # Claude Code specific - Gitignored
├── .env.example           # Team template - Git tracked
├── .env.local.example     # App override template - Git tracked
└── docs/
    ├── AUTHENTICATION_GUIDE.md
    ├── QUICK_AUTH_REFERENCE.md
    ├── FILE_SEPARATION_STRATEGY.md
    └── CLAUDE_SDK_MAX_SUBSCRIPTION_GUIDE.md
```

## How It Works

### Claude Code Development Session

1. You open Claude Code
2. Claude Code reads `.env` 
3. `.env` has NO `ANTHROPIC_API_KEY` or `ANTHROPIC_BASE_URL`
4. Claude Code falls back to your Max subscription OAuth
5. **Result:** Uses your $200/month subscription ✅

### Your Python Application Runtime

1. You run `python src/main.py`
2. Application loads `.env` (base configuration)
3. Application loads `.env.local` (overrides with GLM-4.6)
4. `.env.local` sets `ANTHROPIC_BASE_URL` and `ANTHROPIC_API_KEY`
5. **Result:** Uses GLM-4.6 via Z.ai ($3/month) ✅

## Common Issues

### Issue: Claude Code using GLM-4.6

**Symptom:** You see "Using glm-4.6" in Claude Code responses

**Diagnosis:**
```bash
./scripts/check_auth_config.sh
```

**Fix:**
```bash
# Comment out API keys in .env
vim .env  # or use your editor
# Comment out lines with ANTHROPIC_API_KEY and ANTHROPIC_BASE_URL

# Verify
./scripts/check_auth_config.sh
```

### Issue: Application NOT using GLM-4.6

**Symptom:** Application errors or unexpected costs

**Diagnosis:**
```bash
# Check if .env.local exists
cat .env.local

# Should show:
# ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
# ANTHROPIC_API_KEY=6845ef1767204ea98a67faaecb3afe08.fyZ4DweXVe3SvCXS
```

**Fix:**
```python
# Update your application to load .env.local
from dotenv import load_dotenv

load_dotenv()  # Load .env
load_dotenv('.env.local', override=True)  # Override with .env.local
```

### Issue: Both using the same configuration

**Root Cause:** Application not loading `.env.local`

**Fix:** See "Update Your Python Application" section above

## Switching Modes

### Switch Application to Claude API

Edit `.env.local`:
```bash
# Comment out GLM-4.6
# ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
# ANTHROPIC_API_KEY=6845ef1767204ea98a67faaecb3afe08.fyZ4DweXVe3SvCXS

# Add Claude API key
ANTHROPIC_API_KEY=sk-ant-your-key-from-console
CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

### Temporarily test Claude Code with API key

**Not recommended**, but if you need to test:

1. Temporarily add API key to .env
2. Test your scenario
3. **IMMEDIATELY remove** the API key from .env
4. Run `./scripts/check_auth_config.sh` to verify

## Security Checklist

- [ ] `.env` has NO active API keys (all commented)
- [ ] `.env.local` has your GLM-4.6 API key
- [ ] `.env.local` is in `.gitignore`
- [ ] `.env.example` and `.env.local.example` are safe templates
- [ ] Validation script passes: `./scripts/check_auth_config.sh`
- [ ] Application loads `.env.local` with override
- [ ] Never commit `.env.local` to git

## Summary

✅ **Claude Code**: Reads `.env` → No API keys → Uses Max subscription
✅ **Your App**: Reads `.env` + `.env.local` → Has GLM-4.6 → Uses Z.ai
✅ **No conflicts**: Each tool has separate authentication
✅ **Git safe**: Secrets in `.env.local` (gitignored)
✅ **Cost effective**: Dev uses subscription, production uses GLM-4.6

## Support

See comprehensive guides:
- `/docs/AUTHENTICATION_GUIDE.md` - Full technical details
- `/docs/QUICK_AUTH_REFERENCE.md` - Quick reference card
- `/docs/FILE_SEPARATION_STRATEGY.md` - File organization explained
- `/docs/CLAUDE_SDK_MAX_SUBSCRIPTION_GUIDE.md` - SDK + subscription usage
