# Per-Project LLM Configuration Guide

## Overview

This guide shows you how to configure Claude Code to use different LLM providers (GLM-4.6, Claude Max subscription, etc.) on a **per-project basis** while maintaining global defaults.

**Cost Optimization Strategy:**
- **GLM-4.6 via Z.ai**: $3-15/month (85-94% cheaper than Claude)
- **Claude Max Subscription**: $200/month (unlimited usage)
- **Use GLM-4.6 for**: Development, testing, coding tasks
- **Use Max subscription for**: Complex reasoning, production tasks

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Understanding Authentication Variables](#understanding-authentication-variables)
3. [Setup for New Projects](#setup-for-new-projects)
4. [Switching Between Providers](#switching-between-providers)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Configurations](#advanced-configurations)

---

## Quick Start

### Option 1: Use GLM-4.6 for This Project Only

```bash
# 1. Navigate to your project
cd /path/to/your/project

# 2. Create .env file
cat > .env << 'EOF'
# GLM-4.6 Configuration (Claude Code)
ANTHROPIC_AUTH_TOKEN=your-zai-api-key-here
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4.6
ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air
ANTHROPIC_DEFAULT_OPUS_MODEL=glm-4.6

# GLM-4.6 Configuration (Python SDK)
ANTHROPIC_API_KEY=your-zai-api-key-here
CLAUDE_MODEL=glm-4.6
EOF

# 3. Create switching scripts (see below)
mkdir -p scripts
# Copy scripts from this guide

# 4. Start Claude Code
source scripts/switch_to_glm46.sh
claude
```

### Option 2: Use Max Subscription Globally, GLM-4.6 Per-Project

```bash
# 1. Keep shell environment clean (use subscription globally)
# Don't set any ANTHROPIC_* variables in ~/.bashrc or ~/.zshrc

# 2. Per-project: Create switching scripts
# When you want GLM-4.6 for a specific project:
cd /path/to/project
source scripts/switch_to_glm46.sh
claude

# When you want Max subscription:
cd /path/to/project
source scripts/switch_to_subscription.sh
claude
```

---

## Understanding Authentication Variables

### Critical Distinction: Claude Code vs Python SDK

| Purpose | Claude Code Variable | Python SDK Variable |
|---------|---------------------|---------------------|
| **API Key** | `ANTHROPIC_AUTH_TOKEN` | `ANTHROPIC_API_KEY` |
| **Base URL** | `ANTHROPIC_BASE_URL` | `ANTHROPIC_BASE_URL` |
| **Model Selection** | `ANTHROPIC_DEFAULT_SONNET_MODEL` | `CLAUDE_MODEL` |

### Why Different Variables?

**Claude Code:**
- Uses `ANTHROPIC_AUTH_TOKEN` for custom endpoints (like Z.ai)
- Uses model tier mapping (`SONNET`, `HAIKU`, `OPUS`)
- Requires variables to be set **before** launching `claude` command

**Python SDK (Anthropic library):**
- Uses `ANTHROPIC_API_KEY` for authentication
- Uses direct model names via `CLAUDE_MODEL` or in code

### Authentication Priority Order

```
Claude Code:
1. ANTHROPIC_AUTH_TOKEN (custom endpoints)
2. ANTHROPIC_API_KEY (official API)
3. OAuth token (subscription)

Python SDK:
1. ANTHROPIC_API_KEY environment variable
2. API key passed in code
3. No fallback (will error)
```

---

## Setup for New Projects

### Step 1: Create Project Structure

```bash
# Create new project
mkdir my-new-project
cd my-new-project

# Create scripts directory
mkdir -p scripts docs
```

### Step 2: Create `.env` File

```bash
cat > .env << 'EOF'
# ===================================
# LLM Provider Configuration
# ===================================
# Current: Using GLM-4.6 via Z.ai
# To switch: Comment these out and use Max subscription

# GLM-4.6 Configuration (Claude Code)
ANTHROPIC_AUTH_TOKEN=your-zai-api-key-here
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4.6
ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air
ANTHROPIC_DEFAULT_OPUS_MODEL=glm-4.6

# GLM-4.6 Configuration (Python SDK)
ANTHROPIC_API_KEY=your-zai-api-key-here
CLAUDE_MODEL=glm-4.6

# ===================================
# TO USE MAX SUBSCRIPTION INSTEAD:
# ===================================
# 1. Comment out all ANTHROPIC_* variables above
# 2. Run: source scripts/switch_to_subscription.sh
# 3. Start: claude
EOF
```

### Step 3: Create Switching Scripts

**Script 1: Switch to GLM-4.6**

```bash
cat > scripts/switch_to_glm46.sh << 'EOF'
#!/bin/bash
# Switch Claude Code to use GLM-4.6 via Z.ai

echo "🔄 Switching to GLM-4.6 via Z.ai..."

# Export environment variables for current session
export ANTHROPIC_AUTH_TOKEN="your-zai-api-key-here"
export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"
export ANTHROPIC_DEFAULT_SONNET_MODEL="glm-4.6"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="glm-4.5-air"
export ANTHROPIC_DEFAULT_OPUS_MODEL="glm-4.6"

# Unset conflicting variables
unset ANTHROPIC_API_KEY

echo "✅ Environment configured for GLM-4.6"
echo ""
echo "   Provider: Z.ai"
echo "   Model: GLM-4.6"
echo "   Cost: $3-15/month"
echo ""
echo "📝 Now start Claude Code in THIS SAME TERMINAL:"
echo "   claude"
echo ""
echo "💡 Verify with: /status inside Claude Code"
EOF

chmod +x scripts/switch_to_glm46.sh
```

**Script 2: Switch to Max Subscription**

```bash
cat > scripts/switch_to_subscription.sh << 'EOF'
#!/bin/bash
# Switch Claude Code to use Max subscription

echo "🔄 Switching to Max Subscription..."

# Unset all ANTHROPIC variables to use subscription OAuth
unset ANTHROPIC_AUTH_TOKEN
unset ANTHROPIC_API_KEY
unset ANTHROPIC_BASE_URL
unset ANTHROPIC_DEFAULT_SONNET_MODEL
unset ANTHROPIC_DEFAULT_HAIKU_MODEL
unset ANTHROPIC_DEFAULT_OPUS_MODEL
unset CLAUDE_MODEL

echo "✅ Environment configured for Max Subscription"
echo ""
echo "   Provider: Anthropic (Official)"
echo "   Model: Claude 3.5 Sonnet"
echo "   Cost: $200/month (unlimited)"
echo ""
echo "📝 Now start Claude Code in THIS SAME TERMINAL:"
echo "   claude"
echo ""
echo "💡 Verify with: /status inside Claude Code"
echo ""
echo "⚠️  Note: Your Python app will still use .env for configuration"
EOF

chmod +x scripts/switch_to_subscription.sh
```

### Step 4: Create `.gitignore`

```bash
cat > .gitignore << 'EOF'
# Environment files with secrets
.env
.env.local
.env.*.local

# Don't ignore example files
!.env.example
EOF
```

### Step 5: Create `.env.example` Template

```bash
cat > .env.example << 'EOF'
# ===================================
# LLM Provider Configuration - EXAMPLE
# ===================================
# Copy this to .env and fill in your API keys

# GLM-4.6 Configuration (Claude Code)
ANTHROPIC_AUTH_TOKEN=your-zai-api-key-here
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4.6
ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air
ANTHROPIC_DEFAULT_OPUS_MODEL=glm-4.6

# GLM-4.6 Configuration (Python SDK)
ANTHROPIC_API_KEY=your-zai-api-key-here
CLAUDE_MODEL=glm-4.6
EOF
```

---

## Switching Between Providers

### Daily Workflow

**Morning: Start with GLM-4.6 (Cost-Effective)**

```bash
cd ~/Projects/my-project
source scripts/switch_to_glm46.sh
claude
```

**When You Need More Power: Switch to Max**

```bash
# In another terminal tab/window
cd ~/Projects/my-project
source scripts/switch_to_subscription.sh
claude
```

### Verification Commands

**Inside Claude Code, run:**

```
/status
```

Expected output for GLM-4.6:
```
Model: glm-4.6
Provider: z.ai
Base URL: https://api.z.ai/api/anthropic
```

Expected output for Max subscription:
```
Model: claude-3-5-sonnet-20241022
Provider: anthropic
Authentication: Subscription OAuth
```

---

## Troubleshooting

### Issue 1: New Session Not Using GLM-4.6

**Symptom:** After running `switch_to_glm46.sh`, Claude Code still uses subscription

**Diagnosis:**
```bash
# Check environment variables are set
env | grep ANTHROPIC
```

**Expected output:**
```
ANTHROPIC_AUTH_TOKEN=6845ef...
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4.6
```

**Fix:**
```bash
# Make sure you're using 'source' not 'sh'
source scripts/switch_to_glm46.sh  # ✅ Correct
sh scripts/switch_to_glm46.sh      # ❌ Wrong - doesn't export to parent shell

# Then start Claude Code in SAME terminal
claude
```

### Issue 2: "Authentication Failed" Error

**Symptom:** `401 Unauthorized` or `Authentication failed`

**Diagnosis:**
```bash
# Check if using wrong variable
echo "AUTH_TOKEN: $ANTHROPIC_AUTH_TOKEN"
echo "API_KEY: $ANTHROPIC_API_KEY"
echo "BASE_URL: $ANTHROPIC_BASE_URL"
```

**Fix:**
```bash
# For Claude Code with Z.ai, you need AUTH_TOKEN, not API_KEY
export ANTHROPIC_AUTH_TOKEN="your-key"  # ✅ Correct
export ANTHROPIC_API_KEY="your-key"     # ❌ Wrong for custom endpoints

# Unset the wrong one
unset ANTHROPIC_API_KEY
```

### Issue 3: Using Wrong Model Despite Configuration

**Symptom:** Claude Code uses Claude 3.5 Sonnet instead of GLM-4.6

**Diagnosis:**
```bash
echo "Model: $ANTHROPIC_DEFAULT_SONNET_MODEL"
```

**Fix:**
```bash
# Make sure model mapping is set
export ANTHROPIC_DEFAULT_SONNET_MODEL="glm-4.6"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="glm-4.5-air"
export ANTHROPIC_DEFAULT_OPUS_MODEL="glm-4.6"

# Restart Claude Code
claude
```

### Issue 4: Python App Not Using GLM-4.6

**Symptom:** Your Python application errors or uses wrong model

**Diagnosis:**
```python
import os
print(f"API_KEY: {os.getenv('ANTHROPIC_API_KEY')}")
print(f"BASE_URL: {os.getenv('ANTHROPIC_BASE_URL')}")
print(f"MODEL: {os.getenv('CLAUDE_MODEL')}")
```

**Fix:**
```python
# Ensure .env is loaded in your app
from dotenv import load_dotenv
load_dotenv()  # Loads .env file

# Verify it's set
import os
assert os.getenv('ANTHROPIC_API_KEY'), "API key not set!"
assert os.getenv('ANTHROPIC_BASE_URL') == "https://api.z.ai/api/anthropic"
```

### Issue 5: Variables Not Persisting Between Terminal Sessions

**Symptom:** Have to run `switch_to_glm46.sh` every time you open a terminal

**Solution A: Make Permanent for This Project**

```bash
# Add to project-specific shell script
cat > .envrc << 'EOF'
# Automatically load when entering this directory
# Requires direnv: brew install direnv

export ANTHROPIC_AUTH_TOKEN="your-key"
export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"
export ANTHROPIC_DEFAULT_SONNET_MODEL="glm-4.6"
EOF

# Enable direnv
direnv allow
```

**Solution B: Make Permanent Globally (Not Recommended)**

```bash
# Add to ~/.bashrc or ~/.zshrc (but loses per-project flexibility)
echo 'export ANTHROPIC_AUTH_TOKEN="your-key"' >> ~/.bashrc
echo 'export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"' >> ~/.bashrc
echo 'export ANTHROPIC_DEFAULT_SONNET_MODEL="glm-4.6"' >> ~/.bashrc

# Reload shell
source ~/.bashrc
```

---

## Advanced Configurations

### Configuration 1: Different Models for Different Tasks

```bash
# switch_to_fast.sh - Use GLM-4.5-air for simple tasks
export ANTHROPIC_DEFAULT_SONNET_MODEL="glm-4.5-air"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="glm-4.5-air"
export ANTHROPIC_DEFAULT_OPUS_MODEL="glm-4.5-air"

# switch_to_powerful.sh - Use GLM-4.6 for complex tasks
export ANTHROPIC_DEFAULT_SONNET_MODEL="glm-4.6"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="glm-4.5-air"
export ANTHROPIC_DEFAULT_OPUS_MODEL="glm-4.6"
```

### Configuration 2: Hybrid Approach (GLM + Max)

```bash
# Use GLM-4.6 for most work, Max for specific needs
# Default: GLM-4.6
source scripts/switch_to_glm46.sh
claude

# When you need Max: Open new terminal tab
source scripts/switch_to_subscription.sh
claude
```

### Configuration 3: Cost Tracking

```bash
cat > scripts/track_usage.sh << 'EOF'
#!/bin/bash
# Track which provider you're using

PROVIDER=$([ -n "$ANTHROPIC_AUTH_TOKEN" ] && echo "GLM-4.6 (Z.ai)" || echo "Max Subscription")
MODEL=$([ -n "$ANTHROPIC_DEFAULT_SONNET_MODEL" ] && echo "$ANTHROPIC_DEFAULT_SONNET_MODEL" || echo "claude-3-5-sonnet")

echo "$(date '+%Y-%m-%d %H:%M:%S') - Provider: $PROVIDER, Model: $MODEL" >> ~/claude_usage.log
EOF
```

### Configuration 4: Team Collaboration

```bash
# .env.example - Safe to commit
ANTHROPIC_AUTH_TOKEN=ask-team-lead-for-key
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4.6

# README.md - Document for team
cat > README.md << 'EOF'
## Setup LLM Provider

1. Get Z.ai API key from [team lead]
2. Copy `.env.example` to `.env`
3. Fill in your API key
4. Run: `source scripts/switch_to_glm46.sh`
5. Start: `claude`
EOF
```

---

## Cost Comparison

### Monthly Costs

| Provider | Model | Cost | Best For |
|----------|-------|------|----------|
| **Z.ai** | GLM-4.6 | $3-15/mo | Development, testing, coding |
| **Z.ai** | GLM-4.5-air | $1-5/mo | Simple tasks, drafts |
| **Anthropic** | Max Subscription | $200/mo | Unlimited usage, complex reasoning |
| **Anthropic** | API Pay-as-you-go | Variable | Production, specific use cases |

### Savings Calculator

```bash
# Example: 1000 requests/month
GLM-4.6: ~$10/month
Claude Max: $200/month (unlimited)
Savings: $190/month (95% reduction)

# Break-even point: ~50 requests/day
If you use <50 requests/day: Use GLM-4.6
If you use >50 requests/day: Use Max subscription
```

---

## Quick Reference Commands

```bash
# Setup new project
mkdir my-project && cd my-project
curl -O https://raw.githubusercontent.com/[your-repo]/scripts/switch_to_glm46.sh
curl -O https://raw.githubusercontent.com/[your-repo]/scripts/switch_to_subscription.sh
chmod +x scripts/*.sh

# Use GLM-4.6
source scripts/switch_to_glm46.sh && claude

# Use Max subscription
source scripts/switch_to_subscription.sh && claude

# Check current configuration
env | grep ANTHROPIC

# Verify inside Claude Code
/status

# Reset everything
unset ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL ANTHROPIC_DEFAULT_SONNET_MODEL
```

---

## Security Best Practices

1. **Never commit API keys**: Always use `.gitignore` for `.env` files
2. **Use `.env.example`**: Provide templates without real keys
3. **Rotate keys regularly**: Change API keys every 3-6 months
4. **Use project-specific keys**: Different keys for different projects
5. **Monitor usage**: Track costs and usage patterns
6. **Team access**: Use shared team keys, not personal ones

---

## Summary

**Key Takeaways:**

1. ✅ **Claude Code uses `ANTHROPIC_AUTH_TOKEN`**, not `ANTHROPIC_API_KEY`
2. ✅ **Python SDK uses `ANTHROPIC_API_KEY`**
3. ✅ **Set variables BEFORE launching `claude` command**
4. ✅ **Use `source scripts/switch_*.sh`** for per-session configuration
5. ✅ **Verify with `/status`** inside Claude Code
6. ✅ **GLM-4.6 saves 85-94%** compared to Claude API costs
7. ✅ **Keep `.env` for app config**, switching scripts for Claude Code

**Next Steps:**

1. Copy this guide to your new project: `docs/PER_PROJECT_LLM_CONFIGURATION.md`
2. Create switching scripts in `scripts/` directory
3. Set up `.env.example` for team collaboration
4. Test both providers to verify configuration
5. Choose default provider based on usage patterns

**Need Help?**

- Check `/status` inside Claude Code to see active configuration
- Run `env | grep ANTHROPIC` to verify environment variables
- Review troubleshooting section above
- Test with simple prompts first before complex tasks
