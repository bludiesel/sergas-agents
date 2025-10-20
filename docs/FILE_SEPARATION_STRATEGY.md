# File Separation Strategy

## Overview

This project uses multiple environment files to separate Claude Code development configuration from application runtime configuration.

## File Structure

| File | Purpose | Read By | Contains API Keys? | Git Tracked? |
|------|---------|---------|-------------------|--------------|
| `.env` | Base configuration | Both | ❌ NO | ✅ Yes (template) |
| `.env.local` | Application runtime overrides | Application only | ✅ YES | ❌ No (gitignored) |
| `.env.claude-code` | Claude Code specific | Claude Code (optional) | ❌ NO | ❌ No (gitignored) |
| `.env.example` | Team template | Documentation | ❌ NO | ✅ Yes |

## How It Works

### 1. Claude Code Development (Uses Subscription)

**Files Read**: `.env` only

**Configuration**:
```bash
# .env (CLEAN - no API keys)
CLAUDE_MODEL=claude-3-5-sonnet-20241022
# ANTHROPIC_API_KEY and ANTHROPIC_BASE_URL are NOT set
```

**Result**: Claude Code uses your Max subscription ($200/month) ✅

### 2. Application Runtime (Uses GLM-4.6)

**Files Read**: `.env` + `.env.local` (with `.env.local` taking precedence)

**Configuration**:
```bash
# .env.local (HAS API keys)
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
ANTHROPIC_API_KEY=6845ef1767204ea98a67faaecb3afe08.fyZ4DweXVe3SvCXS
CLAUDE_MODEL=glm-4.6
```

**Result**: Your application uses GLM-4.6 via Z.ai ($3/month) ✅

## Python Application Setup

Ensure your application loads both files with `.env.local` taking precedence:

```python
from dotenv import load_dotenv

# Load .env first (base configuration)
load_dotenv()

# Load .env.local (overrides for runtime)
load_dotenv('.env.local', override=True)
```

## Validation

Run the validation script to ensure Claude Code will use your subscription:

```bash
./scripts/check_auth_config.sh
```

**Expected Output**:
```
✅ Authentication configuration looks good!
   Claude Code will use your Max subscription.
```

## Quick Reference

### Using Claude Code (Development)
```bash
# Make sure .env has no active ANTHROPIC_API_KEY
grep "^ANTHROPIC_API_KEY" .env
# Should return nothing or commented lines

# Validation
./scripts/check_auth_config.sh
# Should show: "✅ Authentication configuration looks good!"
```

### Running Your Application (Runtime)
```bash
# Your app reads .env.local automatically
python src/main.py

# Verify GLM-4.6 is being used
echo $ANTHROPIC_BASE_URL  # Should show: https://api.z.ai/api/anthropic
```

## Switching Between Modes

### Switch Application to Claude API

Edit `.env.local`:
```bash
# Comment out GLM-4.6
# ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
# ANTHROPIC_API_KEY=6845ef1767204ea98a67faaecb3afe08.fyZ4DweXVe3SvCXS

# Uncomment Claude API
ANTHROPIC_API_KEY=your-claude-api-key-from-console
CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

### Switch Claude Code to API Key (Not Recommended)

**Only do this if you want to test API key behavior:**

Edit `.env` (temporarily):
```bash
ANTHROPIC_API_KEY=your-test-api-key
```

**Remember to revert** when done testing!

## Troubleshooting

### Issue: Claude Code using GLM-4.6 or API key

**Diagnosis**:
```bash
./scripts/check_auth_config.sh
```

**Fix**:
```bash
# Comment out any ANTHROPIC_* variables in .env
sed -i.bak '/^ANTHROPIC_API_KEY=/s/^/# /' .env
sed -i.bak '/^ANTHROPIC_BASE_URL=/s/^/# /' .env

# Verify
./scripts/check_auth_config.sh
```

### Issue: Application not using GLM-4.6

**Diagnosis**:
```bash
# Check if .env.local exists
ls -la .env.local

# Check if it has the right configuration
grep ANTHROPIC .env.local
```

**Fix**:
```bash
# Create .env.local with GLM-4.6 configuration
cp .env.local.example .env.local
# Edit to add your Z.ai API key
```

### Issue: Both Claude Code and App using same config

**Root Cause**: Application not loading `.env.local`

**Fix**: Update your application initialization:
```python
# src/main.py or src/__init__.py
from dotenv import load_dotenv

# CRITICAL: Load both files in correct order
load_dotenv()  # Load .env first
load_dotenv('.env.local', override=True)  # Override with .env.local
```

## Security Best Practices

1. ✅ **Never commit `.env.local`** - Already in `.gitignore`
2. ✅ **Keep `.env` clean** - No active API keys
3. ✅ **Use `.env.local` for secrets** - Runtime-only secrets
4. ✅ **Run validation before commits** - `./scripts/check_auth_config.sh`
5. ✅ **Document team setup** - Share `.env.example` with team

## Summary

- **Claude Code**: Reads `.env` (no API keys) → Uses subscription
- **Your App**: Reads `.env` + `.env.local` → Uses GLM-4.6
- **No conflicts**: Each tool has its own authentication source
- **Git safe**: Secrets only in `.env.local` (gitignored)
