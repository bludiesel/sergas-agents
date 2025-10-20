# Authentication Guide: Claude Code vs Claude Agent SDK

## Critical Findings

### 🔴 Claude Code vs Claude Agent SDK Authentication

| Tool | Subscription Support | API Key Support | Best For |
|------|---------------------|----------------|----------|
| **Claude Code CLI** | ✅ Yes (Pro/Max OAuth) | ✅ Yes | Development, local coding |
| **Claude Agent SDK** | ❌ No (API key only) | ✅ Yes | Production agents, deployed apps |

### 🚨 Critical Issue: Environment Variable Priority

**When `ANTHROPIC_API_KEY` is set in environment variables:**
- Claude Code **ignores** your subscription
- All usage is charged to the API key
- You lose subscription benefits (fixed monthly cost, higher limits)

**Authentication Priority (highest to lowest):**
1. `ANTHROPIC_API_KEY` environment variable ← **Overrides everything**
2. `ANTHROPIC_BASE_URL` environment variable
3. Claude Code subscription OAuth (Pro/Max)
4. Manual API key entry in IDE

---

## Official Stance: Claude Agent SDK

### From Anthropic Documentation

> **Claude Agent SDK requires API key authentication.**
>
> Anthropic does not allow third-party developers to apply Claude.ai rate limits
> for their products, including agents built on the Claude Agent SDK.

**What this means:**
- Your application code (agents using SDK) **must use API keys**
- You cannot use your Max subscription for deployed agents
- SDK applications are billed separately from Claude Code usage

### Why SDK Doesn't Support Subscriptions

**Technical Reasons:**
1. **Rate Limit Isolation**: Subscription limits are personal, not for distributed applications
2. **Usage Tracking**: API usage needs per-application metering
3. **Billing Separation**: Development (subscription) vs production (API) costs
4. **Team Usage**: API keys allow team-based access control

**Business Reasons:**
- Subscriptions are for **individual use** (Claude Code, web interface)
- APIs are for **programmatic/production use** (deployed applications, agents)
- Different pricing models serve different use cases

---

## The Problem in This Project

### What Happened

Your `.env` file contained:
```bash
ANTHROPIC_API_KEY=6845ef1767204ea98a67faaecb3afe08.fyZ4DweXVe3SvCXS  # Z.ai key
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic  # Routes to GLM-4.6
```

**Result:**
- Claude Code used the Z.ai API key instead of your Max subscription
- All Claude Code requests went to GLM-4.6 (not real Claude)
- Your Max subscription was unused

### Why It Happened

The `.env` file serves **two purposes**:
1. **Claude Code** reads it for configuration (should NOT have API keys)
2. **Your application** reads it for runtime configuration (SHOULD have API keys)

**Conflict**: Same file, different needs!

---

## Solutions to Prevent This Issue

### Solution 1: Separate Environment Files (Recommended)

Use **different environment files** for different purposes:

```bash
# Directory structure
.
├── .env                    # For your application (has API keys)
├── .env.claude-code        # For Claude Code only (NO API keys)
├── .env.example            # Template with comments
└── .gitignore              # Ignore both .env files
```

**Step 1: Create `.env.claude-code`** (for Claude Code only):
```bash
# .env.claude-code
# This file is for Claude Code CLI ONLY
# DO NOT add ANTHROPIC_API_KEY or ANTHROPIC_BASE_URL here

# Claude Code will use your subscription when these are unset
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Project-specific settings (safe to include)
ENV=development
DEBUG=true
LOG_LEVEL=INFO
```

**Step 2: Update `.env`** (for your application):
```bash
# .env
# This file is for your APPLICATION code (agents, SDK usage)
# Claude Code should NOT read this file

# Your application needs API keys for Claude Agent SDK
ANTHROPIC_API_KEY=sk-ant-your-api-key-here  # For SDK usage
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Or use GLM-4.6 for your application
# ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
# ANTHROPIC_API_KEY=6845ef1767204ea98a67faaecb3afe08.fyZ4DweXVe3SvCXS
# CLAUDE_MODEL=glm-4.6
```

**Step 3: Configure Claude Code to use `.env.claude-code`**:

Create `.claude/settings.json`:
```json
{
  "env_file": ".env.claude-code"
}
```

**Step 4: Update `.gitignore`**:
```
.env
.env.claude-code
.env.local
.env.*.local
```

---

### Solution 2: Environment Variable Scoping with direnv

Use `direnv` to load different environment variables for different contexts:

**Install direnv:**
```bash
# macOS
brew install direnv

# Add to ~/.zshrc or ~/.bashrc
eval "$(direnv hook zsh)"  # or bash
```

**Create `.envrc`:**
```bash
# .envrc
# Load .env.claude-code for Claude Code
if command -v claude &> /dev/null; then
    dotenv .env.claude-code
else
    # Load .env for application
    dotenv .env
fi
```

**Activate:**
```bash
direnv allow .
```

---

### Solution 3: Validation Script

Create a script to detect and warn about conflicts:

```bash
#!/bin/bash
# scripts/check_auth_config.sh

echo "🔍 Checking authentication configuration..."

# Check if ANTHROPIC_API_KEY is set in environment
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  WARNING: ANTHROPIC_API_KEY is set in your environment!"
    echo "   Claude Code will use this API key instead of your subscription."
    echo "   To use your Max subscription, unset this variable:"
    echo "   unset ANTHROPIC_API_KEY"
    exit 1
fi

# Check if ANTHROPIC_BASE_URL is set
if [ -n "$ANTHROPIC_BASE_URL" ]; then
    echo "⚠️  WARNING: ANTHROPIC_BASE_URL is set to: $ANTHROPIC_BASE_URL"
    echo "   This will route requests to a custom endpoint."
    echo "   To use official Anthropic API, unset this variable:"
    echo "   unset ANTHROPIC_BASE_URL"
    exit 1
fi

# Check .env file
if [ -f ".env" ] && grep -q "^ANTHROPIC_API_KEY=" .env; then
    echo "⚠️  WARNING: .env contains ANTHROPIC_API_KEY!"
    echo "   This may override Claude Code's subscription authentication."
    echo "   Consider moving API keys to a separate .env.app file."
    exit 1
fi

echo "✅ Authentication configuration looks good!"
echo "   Claude Code will use your subscription."
```

**Usage:**
```bash
chmod +x scripts/check_auth_config.sh
./scripts/check_auth_config.sh
```

**Add to pre-commit hook:**
```bash
# .git/hooks/pre-commit
#!/bin/bash
./scripts/check_auth_config.sh
```

---

### Solution 4: Clear Documentation in .env.example

Update `.env.example` with explicit warnings:

```bash
# ===================================
# ⚠️  AUTHENTICATION CRITICAL ⚠️
# ===================================
# READ THIS BEFORE SETTING THESE VARIABLES!
#
# Claude Code Authentication:
#   - Uses your Max/Pro subscription when ANTHROPIC_API_KEY is NOT set
#   - Will use API key if ANTHROPIC_API_KEY IS set (charges API usage)
#
# Claude Agent SDK Authentication:
#   - REQUIRES API key (does not support subscription)
#   - Your deployed agents will use API billing
#
# Recommendation:
#   - Keep ANTHROPIC_API_KEY commented out for Claude Code
#   - Use a separate .env.app file for your application API keys

# ===================================
# For Claude Code (DO NOT UNCOMMENT)
# ===================================
# ANTHROPIC_API_KEY=  # Leave commented for subscription usage
# ANTHROPIC_BASE_URL=  # Leave commented for official API

# ===================================
# For Your Application (uncomment when deploying)
# ===================================
# ANTHROPIC_API_KEY=sk-ant-your-api-key-here  # For SDK/production use
# CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

---

## Best Practices

### ✅ DO

1. **Keep Claude Code environment clean**
   - Do NOT set `ANTHROPIC_API_KEY` in shell profile
   - Do NOT set `ANTHROPIC_BASE_URL` globally
   - Let Claude Code use subscription OAuth

2. **Separate application configuration**
   - Use `.env.app` or similar for application API keys
   - Load different configs in different contexts
   - Document which file is for what purpose

3. **Validate before commits**
   - Run `./scripts/check_auth_config.sh` before committing
   - Add validation to CI/CD pipeline
   - Check for accidental API key exposure

4. **Document clearly**
   - Add comments to .env files
   - Update README with authentication guide
   - Warn team members about conflicts

### ❌ DON'T

1. **Don't mix Claude Code and application configs**
   - Avoid single .env file for both purposes
   - Don't assume one config fits all

2. **Don't set API keys globally**
   - Avoid `export ANTHROPIC_API_KEY` in shell profile
   - Don't set in system-wide environment

3. **Don't commit sensitive keys**
   - Never commit .env with real API keys
   - Use .env.example templates only

4. **Don't assume subscription works for SDK**
   - SDK requires API keys (official stance)
   - Plan for separate billing

---

## Quick Fix Commands

### Reset to Subscription Authentication

```bash
# Unset environment variables
unset ANTHROPIC_API_KEY
unset ANTHROPIC_BASE_URL

# Remove from current .env
sed -i.bak '/^ANTHROPIC_API_KEY=/d' .env
sed -i.bak '/^ANTHROPIC_BASE_URL=/d' .env

# Verify
./scripts/check_auth_config.sh
```

### Switch to API Key Authentication

```bash
# Set for current session only
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Or add to .env.app
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" >> .env.app
```

---

## Summary

| Scenario | Use | Authentication | Billing |
|----------|-----|----------------|---------|
| **Claude Code CLI (development)** | Coding, debugging | Max subscription OAuth | Subscription ($200/mo) |
| **Claude Agent SDK (application)** | Production agents | API key required | Pay-per-token API |
| **GLM-4.6 via Z.ai** | Cost optimization | Z.ai API key | Z.ai billing |

**Golden Rule**:
- Claude Code = Subscription (no ANTHROPIC_API_KEY)
- Your App/SDK = API Key (set ANTHROPIC_API_KEY)

**Never**: Set ANTHROPIC_API_KEY globally or in shared .env if you want Claude Code to use your subscription!

---

## Additional Resources

- **Claude Code Authentication**: https://docs.claude.com/en/docs/claude-code
- **Claude Agent SDK**: https://docs.claude.com/en/api/agent-sdk/overview
- **API Key Management**: https://console.anthropic.com/settings/keys
- **Subscription Plans**: https://claude.ai/settings/billing
