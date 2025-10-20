# 🔐 Authentication Quick Reference

## TL;DR - Avoid Subscription Override

```bash
# ✅ DO THIS (Claude Code uses your Max subscription)
# Keep these UNSET or COMMENTED in .env:
# ANTHROPIC_API_KEY=
# ANTHROPIC_BASE_URL=

# ❌ DON'T DO THIS (Overrides subscription, charges API)
ANTHROPIC_API_KEY=sk-ant-...  # Will bypass subscription!
ANTHROPIC_BASE_URL=https://...  # Will route elsewhere!
```

## Quick Check

Run this before coding:
```bash
./scripts/check_auth_config.sh
```

Expected output:
```
✅ Authentication configuration looks good!
   Claude Code will use your Max subscription.
```

## File Separation Strategy

| File | Purpose | Read By | Should Include API Keys? | Git Tracked? |
|------|---------|---------|--------------------------|--------------|
| `.env` | Base configuration | Both | ❌ **NO** | ✅ Yes (template) |
| `.env.local` | Application runtime overrides | Application only | ✅ Yes (for SDK) | ❌ No (gitignored) |
| `.env.claude-code` | Claude Code specific | Claude Code (optional) | ❌ **NO** | ❌ No (gitignored) |
| `.env.example` | Team template | Documentation | Commented examples only | ✅ Yes |

## Authentication Modes

### Mode 1: Claude Code (This IDE) - Subscription ✅
**When**: Developing, debugging, coding
**Auth**: Max subscription OAuth
**Cost**: $200/month (fixed)
**Setup**: Don't set `ANTHROPIC_API_KEY`

```bash
# .env.claude-code
CLAUDE_MODEL=claude-3-5-sonnet-20241022
# ANTHROPIC_API_KEY=  ← Leave unset!
```

### Mode 2: Your Application - API Key 🔑
**When**: Deploying agents, production use
**Auth**: Anthropic API key
**Cost**: Pay-per-token
**Setup**: Set `ANTHROPIC_API_KEY` in `.env` (not `.env.claude-code`)

```bash
# .env (for your app, NOT Claude Code)
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
```

### Mode 3: GLM-4.6 via Z.ai (Alternative) 🌐
**When**: Testing GLM-4.6, cost optimization
**Auth**: Z.ai API key
**Cost**: Z.ai billing
**Setup**: Both API key and base URL

```bash
# .env (for your app)
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
ANTHROPIC_API_KEY=6845ef1767204ea98a67faaecb3afe08.fyZ4DweXVe3SvCXS
CLAUDE_MODEL=glm-4.6
```

## Common Mistakes

### ❌ Mistake 1: Global API Key
```bash
# ~/.zshrc or ~/.bashrc
export ANTHROPIC_API_KEY="sk-ant-..."  # BAD!
```
**Problem**: All terminal sessions use API key forever
**Fix**: Remove from shell profile, restart terminal

### ❌ Mistake 2: Single .env for Everything
```bash
# .env (both Claude Code AND app read this)
ANTHROPIC_API_KEY=sk-ant-...  # Overrides subscription!
```
**Problem**: Claude Code uses API key instead of subscription
**Fix**: Use separate `.env.claude-code` for Claude Code

### ❌ Mistake 3: Forgetting to Check
```bash
# Making changes without validation
git add .
git commit -m "updates"
```
**Problem**: May commit active API keys or wrong config
**Fix**: Run `./scripts/check_auth_config.sh` first

## Emergency Reset

If Claude Code suddenly starts using API/GLM-4.6:

```bash
# 1. Unset environment variables
unset ANTHROPIC_API_KEY
unset ANTHROPIC_BASE_URL

# 2. Comment out in .env
sed -i.bak '/^ANTHROPIC_API_KEY=/d' .env
sed -i.bak '/^ANTHROPIC_BASE_URL=/d' .env

# 3. Verify
./scripts/check_auth_config.sh

# 4. Restart Claude Code
# (Kill terminal, reopen, or restart IDE)
```

## Validation Checklist

Before starting work:
- [ ] Run `./scripts/check_auth_config.sh`
- [ ] Verify output shows "Subscription OAuth"
- [ ] Check no `ANTHROPIC_API_KEY` in environment: `env | grep ANTHROPIC`
- [ ] Confirm `.env` has API keys commented out

## Resources

- **Full Guide**: `/docs/AUTHENTICATION_GUIDE.md`
- **Checker Script**: `/scripts/check_auth_config.sh`
- **Example Config**: `.env.claude-code.example`
