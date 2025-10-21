# Quick Setup Guide: LLM Configuration for New Projects

## 5-Minute Setup

Copy-paste these commands to set up a new project with GLM-4.6/Max subscription switching:

### 1. Create Project Structure

```bash
# Navigate to your new project
cd /path/to/your/new/project

# Create directories
mkdir -p scripts docs
```

### 2. Copy Switching Scripts

```bash
# Download or copy switch_to_glm46.sh
curl -o scripts/switch_to_glm46.sh https://raw.githubusercontent.com/YOUR_REPO/main/scripts/switch_to_glm46.sh

# Or create manually:
cat > scripts/switch_to_glm46.sh << 'SCRIPT'
#!/bin/bash
echo "🔄 Switching to GLM-4.6 via Z.ai..."

export ANTHROPIC_AUTH_TOKEN="YOUR_ZAI_API_KEY_HERE"
export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"
export ANTHROPIC_DEFAULT_SONNET_MODEL="glm-4.6"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="glm-4.5-air"
export ANTHROPIC_DEFAULT_OPUS_MODEL="glm-4.6"
unset ANTHROPIC_API_KEY

echo "✅ Configured for GLM-4.6"
echo "Now run: claude"
SCRIPT

chmod +x scripts/switch_to_glm46.sh
```

```bash
# Download or copy switch_to_subscription.sh
curl -o scripts/switch_to_subscription.sh https://raw.githubusercontent.com/YOUR_REPO/main/scripts/switch_to_subscription.sh

# Or create manually:
cat > scripts/switch_to_subscription.sh << 'SCRIPT'
#!/bin/bash
echo "🔄 Switching to Max Subscription..."

unset ANTHROPIC_AUTH_TOKEN
unset ANTHROPIC_API_KEY
unset ANTHROPIC_BASE_URL
unset ANTHROPIC_DEFAULT_SONNET_MODEL
unset ANTHROPIC_DEFAULT_HAIKU_MODEL
unset ANTHROPIC_DEFAULT_OPUS_MODEL

echo "✅ Configured for Max Subscription"
echo "Now run: claude"
SCRIPT

chmod +x scripts/switch_to_subscription.sh
```

### 3. Create Environment Files

```bash
# .env - Your actual configuration (DO NOT COMMIT)
cat > .env << 'ENV'
# GLM-4.6 Configuration
ANTHROPIC_AUTH_TOKEN=your-zai-api-key-here
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4.6
ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air
ANTHROPIC_DEFAULT_OPUS_MODEL=glm-4.6

# For Python SDK
ANTHROPIC_API_KEY=your-zai-api-key-here
CLAUDE_MODEL=glm-4.6
ENV

# .env.example - Template for team (SAFE TO COMMIT)
cat > .env.example << 'EXAMPLE'
# GLM-4.6 Configuration
ANTHROPIC_AUTH_TOKEN=get-from-z.ai
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4.6
ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air
ANTHROPIC_DEFAULT_OPUS_MODEL=glm-4.6

# For Python SDK
ANTHROPIC_API_KEY=same-as-auth-token
CLAUDE_MODEL=glm-4.6
EXAMPLE

# .gitignore
cat > .gitignore << 'IGNORE'
.env
.env.local
.env.*.local
!.env.example
IGNORE
```

### 4. Update Scripts with Your API Key

```bash
# Edit the switching script with your actual Z.ai API key
nano scripts/switch_to_glm46.sh
# Replace: YOUR_ZAI_API_KEY_HERE
# With: your actual key from https://z.ai
```

### 5. Test the Setup

```bash
# Test GLM-4.6
source scripts/switch_to_glm46.sh
env | grep ANTHROPIC  # Verify variables are set
claude

# Inside Claude Code, run:
/status
# Should show: Model: glm-4.6, Provider: z.ai

# Test Max Subscription (in new terminal)
source scripts/switch_to_subscription.sh
env | grep ANTHROPIC  # Should be empty or show no custom values
claude

# Inside Claude Code, run:
/status
# Should show: Claude 3.5 Sonnet, Subscription OAuth
```

---

## Daily Usage

### Use GLM-4.6 (Cost-Effective)

```bash
cd /path/to/project
source scripts/switch_to_glm46.sh
claude
```

### Use Max Subscription (Powerful)

```bash
cd /path/to/project
source scripts/switch_to_subscription.sh
claude
```

---

## Troubleshooting

### Variables Not Set?

```bash
# Check if you used 'source' not 'sh'
source scripts/switch_to_glm46.sh  # ✅ Correct
sh scripts/switch_to_glm46.sh      # ❌ Wrong

# Verify
env | grep ANTHROPIC
```

### Still Using Wrong Provider?

```bash
# Make sure Claude Code was started AFTER setting variables
source scripts/switch_to_glm46.sh  # First
claude                              # Then
```

### Authentication Failed?

```bash
# Check your API key is valid
echo $ANTHROPIC_AUTH_TOKEN
# Should show your Z.ai key

# Test the API key
curl -X POST https://api.z.ai/api/anthropic/v1/messages \
  -H "x-api-key: $ANTHROPIC_AUTH_TOKEN" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"glm-4.6","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'
```

---

## One-Line Setup for New Projects

```bash
cd /path/to/new/project && \
mkdir -p scripts docs && \
curl -o scripts/switch_to_glm46.sh https://YOUR_REPO/scripts/switch_to_glm46.sh && \
curl -o scripts/switch_to_subscription.sh https://YOUR_REPO/scripts/switch_to_subscription.sh && \
chmod +x scripts/*.sh && \
echo "✅ Setup complete! Edit scripts/switch_to_glm46.sh with your API key"
```

---

## What Gets Created

```
your-project/
├── scripts/
│   ├── switch_to_glm46.sh          # Switch to GLM-4.6
│   └── switch_to_subscription.sh    # Switch to Max subscription
├── docs/
│   └── PER_PROJECT_LLM_CONFIGURATION.md  # Full documentation
├── .env                              # Your actual config (gitignored)
├── .env.example                      # Template (committed)
└── .gitignore                        # Protects .env
```

---

## Cost Savings

| Provider | Monthly Cost | Best For |
|----------|-------------|----------|
| GLM-4.6 | $3-15 | Development, testing |
| Max Subscription | $200 | Unlimited, complex tasks |
| **Savings** | **$185-197/mo** | **Use GLM-4.6 by default** |

---

## Next Steps

1. ✅ Complete this 5-minute setup
2. ✅ Test both providers
3. ✅ Choose default based on your usage
4. ✅ Share `.env.example` with team
5. ✅ Read full guide: `docs/PER_PROJECT_LLM_CONFIGURATION.md`

**Questions?** Check the full documentation or run `/help` inside Claude Code.
