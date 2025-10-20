# Using Claude Agent SDK with Claude Max Subscription

## ⚠️ Critical Disclaimer

**Anthropic's Official Stance:**
> "Third-party developers are **not allowed** to apply Claude.ai rate limits for their products, including agents built on the Claude Agent SDK. Please use API key authentication methods instead."

**What This Means:**
- ✅ **Personal use**: You can use your Max subscription with Claude Code CLI
- ❌ **Third-party apps**: You cannot deploy apps that use Max subscription for end users
- ⚠️ **Gray area**: Personal automation scripts and tools (use at your own discretion)

**This guide covers:**
1. Official methods (fully supported)
2. Community solutions (use with caution)
3. Workarounds (ToS unclear)

---

## Table of Contents

1. [Official Method: Claude Code CLI](#official-method-claude-code-cli)
2. [Community Solutions](#community-solutions)
3. [Session Token Extraction](#session-token-extraction-advanced)
4. [Containerized Deployment](#containerized-deployment)
5. [Usage Limits & Rate Limits](#usage-limits--rate-limits)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Official Method: Claude Code CLI

### ✅ Fully Supported by Anthropic

The official way to use your Max subscription is through **Claude Code CLI**:

### Installation

```bash
# macOS/Linux
curl -LsSf https://install.claude.ai | sh

# Or using Homebrew (macOS)
brew install anthropics/claude/claude

# Verify installation
claude --version
```

### Authentication

```bash
# Login with your Max subscription
claude login

# This opens a browser to authenticate
# Choose "Log in with your subscription account"
# DO NOT add Console API credentials
```

**Important**: When logging in:
- ✅ Use only your Max plan credentials (email/password or SSO)
- ❌ Do NOT add API keys from console.anthropic.com
- ✅ This ensures usage comes from your subscription quota

### Verification

```bash
# Check authentication status
claude auth status

# Expected output:
# ✓ Authenticated with Claude Max subscription
# Rate limits: Max 20x tier
# Usage resets: Every 5 hours
```

### Using with Code

**Python:**
```python
from claude import Claude

# No API key needed - uses subscription via CLI authentication
client = Claude()

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

**TypeScript:**
```typescript
import { Claude } from '@anthropic-ai/claude-agent-sdk';

// Uses CLI authentication automatically
const claude = new Claude();

const response = await claude.messages.create({
    model: 'claude-3-5-sonnet-20241022',
    max_tokens: 1024,
    messages: [{ role: 'user', content: 'Hello!' }]
});
```

### Supported Tools

These tools integrate with Claude Code CLI and use your subscription:

| Tool | Description | Integration |
|------|-------------|-------------|
| **Cline** | VS Code extension for AI agents | Uses `claude` CLI |
| **Repo Prompt** | Codebase analysis tool | Reads CLI session |
| **Zed Editor** | AI-powered code editor | Native integration |
| **Cursor** | AI code editor | Optional CLI integration |

**Setup for VS Code/Cline:**
1. Install Cline extension
2. Configure to use Claude Code
3. Cline automatically uses your subscription

---

## Community Solutions

### ⚠️ Use at Your Own Risk

These are **community-created** solutions. Anthropic does not officially endorse them.

### 1. Vercel AI SDK Provider

**Repository**: [ben-vargas/ai-sdk-provider-claude-code](https://github.com/ben-vargas/ai-sdk-provider-claude-code)

**What it does**: Enables Vercel AI SDK to use your Max subscription

**Installation:**
```bash
npm install ai-sdk-provider-claude-code
```

**Usage:**
```typescript
import { createClaudeCode } from 'ai-sdk-provider-claude-code';
import { streamText } from 'ai';

const claudeCode = createClaudeCode();

const result = await streamText({
  model: claudeCode('claude-3-5-sonnet-20241022'),
  prompt: 'Write a hello world function',
});

for await (const chunk of result.textStream) {
  process.stdout.write(chunk);
}
```

**How it works**: Wraps the CLI authentication and uses it programmatically

**Limitations**:
- Requires `claude` CLI installed and authenticated
- Only works where CLI is available (local machine)
- Not suitable for server deployment

---

### 2. claude_max Package

**What it does**: Direct programmatic access to Max subscription (deprecated/unofficial)

**Status**: ⚠️ **Use with extreme caution** - May violate ToS

**Original approach:**
- Extracted OAuth tokens from Claude Code
- Used them directly via HTTP requests
- Bypassed official SDK

**Why it's problematic:**
- Violates Anthropic's stated policy
- OAuth tokens can expire/be revoked
- No official support if it breaks
- Potential account suspension risk

**Recommendation**: **Do not use** - Use official methods instead

---

## Session Token Extraction (Advanced)

### ⚠️ Experimental - ToS Unclear

Some developers extract session tokens for automation. This is **not officially supported**.

### Method 1: Using Built-in Command

```bash
# Extract session token
claude auth token

# Output: session_token_value_here
# COPY IT IMMEDIATELY - cannot retrieve again
```

**Usage:**
```python
import os
from anthropic import Anthropic

# Use extracted token
os.environ['ANTHROPIC_SESSION_TOKEN'] = 'your_token_here'

client = Anthropic()  # Uses session token instead of API key
```

**Limitations:**
- Tokens expire (typically 24-48 hours)
- Need to re-extract periodically
- Not suitable for long-running services
- Unclear if this violates ToS

### Method 2: Programmatic Token Extraction

```python
import subprocess
import os

def get_claude_session_token():
    """Extract Claude Code session token."""
    try:
        result = subprocess.run(
            ['claude', 'auth', 'token'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        raise Exception("Not authenticated. Run: claude login")

# Use in your code
session_token = get_claude_session_token()
os.environ['ANTHROPIC_SESSION_TOKEN'] = session_token
```

**When to use:**
- Personal automation scripts
- Local development only
- Not for production/deployment

**When NOT to use:**
- Third-party applications
- Server-side deployment
- Any app with external users

---

## Containerized Deployment

### ⚠️ Advanced - Personal Use Only

Deploy Claude Agent SDK with your Max subscription to cloud providers.

### Solution: claude-agent-sdk-container

**Repository**: [receipting/claude-agent-sdk-container](https://github.com/receipting/claude-agent-sdk-container)

**What it provides:**
- Containerized Claude Agent SDK
- Uses Max plan tokens instead of API tokens
- Web-based CLI and REST API
- OAuth security layer
- Multi-agent support

**Architecture:**
```
┌─────────────┐
│   Docker    │
│  Container  │
├─────────────┤
│ Claude Agent│  ← Uses session token
│     SDK     │     from volume mount
├─────────────┤
│   OAuth     │  ← Protects access
│  Security   │
├─────────────┤
│  REST API   │  ← Your apps connect here
└─────────────┘
```

### Setup

**1. Clone Repository:**
```bash
git clone https://github.com/receipting/claude-agent-sdk-container.git
cd claude-agent-sdk-container
```

**2. Authenticate Locally:**
```bash
# Must have Claude Code CLI installed
claude login
```

**3. Extract Session Token:**
```bash
# Extract and save to file
claude auth token > .claude-token

# Verify
cat .claude-token
```

**4. Configure Docker:**
```dockerfile
# docker-compose.yml
version: '3.8'
services:
  claude-agent:
    build: .
    volumes:
      - ./.claude-token:/app/.claude-token:ro
    environment:
      - CLAUDE_SESSION_TOKEN_FILE=/app/.claude-token
      - OAUTH_CLIENT_ID=your-oauth-client-id
      - OAUTH_CLIENT_SECRET=your-oauth-secret
    ports:
      - "8080:8080"
```

**5. Deploy:**
```bash
# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f
```

**6. Use REST API:**
```bash
# Health check
curl http://localhost:8080/health

# Send message
curl -X POST http://localhost:8080/api/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-oauth-token" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Cloud Deployment

**AWS ECS:**
```bash
# Use secrets manager for token
aws secretsmanager create-secret \
  --name claude-session-token \
  --secret-string "$(claude auth token)"

# Update task definition to use secret
# Deploy to ECS
```

**Google Cloud Run:**
```bash
# Store token in Secret Manager
echo -n "$(claude auth token)" | \
  gcloud secrets create claude-session-token --data-file=-

# Deploy container with secret
gcloud run deploy claude-agent \
  --image gcr.io/your-project/claude-agent \
  --update-secrets CLAUDE_SESSION_TOKEN=claude-session-token:latest
```

**Cloudflare Workers:**

Use [receipting/claude-agent-sdk-cloudflare](https://github.com/receipting/claude-agent-sdk-cloudflare):
- Each accountId gets its own Durable Object
- Isolated container per user
- Serialized execution
- No shared state

### Limitations of Containerized Approach

**Token Management:**
- Session tokens expire (24-48 hours)
- Need automated refresh mechanism
- Risk of downtime when token expires

**ToS Concerns:**
- Unclear if allowed for multi-tenant deployment
- Anthropic explicitly discourages third-party use
- Could result in account suspension

**Recommended For:**
- Personal projects only
- Internal tools (not public-facing)
- Development/testing environments

**NOT Recommended For:**
- Commercial SaaS products
- Public APIs
- Customer-facing applications

---

## Usage Limits & Rate Limits

### Max 5x ($100/month)

**Every 5 hours:**
- ~225 messages on claude.ai (web/mobile)
- ~50-200 prompts via Claude Code CLI

**OR** (not both - shared quota):
- Emphasis on "OR" - using Claude Code reduces web quota and vice versa

### Max 20x ($200/month)

**Every 5 hours:**
- ~900 messages on claude.ai
- ~200-800 prompts via Claude Code CLI

**Benefits:**
- 4x more usage than Max 5x
- Early access to new features
- Higher output limits per request

### Rate Limit Behavior

**When you hit limits:**
```json
{
  "error": {
    "type": "rate_limit_error",
    "message": "Usage limit exceeded. Resets at 2025-10-19T22:00:00Z"
  }
}
```

**Handling in Code:**
```python
from anthropic import Anthropic, RateLimitError
import time

client = Anthropic()

def chat_with_retry(message, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": message}]
            )
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            # Check when quota resets
            reset_time = e.response.headers.get('x-ratelimit-reset')
            wait_seconds = calculate_wait(reset_time)
            print(f"Rate limited. Waiting {wait_seconds}s...")
            time.sleep(wait_seconds)
```

### Monitoring Usage

**CLI Command:**
```bash
# Check current usage
claude usage

# Output:
# Period: 2025-10-19 17:00 - 22:00
# Used: 150 / 800 prompts
# Remaining: 650 prompts
# Resets: in 2h 15m
```

**Programmatic Monitoring:**

Install: [Claude-Code-Usage-Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor)

```bash
# Real-time usage dashboard
npm install -g claude-code-usage-monitor
claude-usage-monitor --dashboard
```

**Features:**
- Real-time usage tracking
- Predictions based on usage patterns
- Warnings before hitting limits
- macOS toolbar widget available

---

## Best Practices

### ✅ DO

1. **Use Official CLI for Personal Dev**
   ```bash
   # Authenticate once
   claude login

   # All tools use this authentication
   # No need to extract tokens
   ```

2. **Respect Rate Limits**
   ```python
   # Implement exponential backoff
   # Monitor usage regularly
   # Plan batch operations during off-peak usage
   ```

3. **Separate Dev from Production**
   ```
   Development: Max subscription (fixed cost)
   Production: API keys (pay-per-use, scalable)
   ```

4. **Keep Tokens Secure**
   ```bash
   # If you must extract tokens:
   chmod 600 .claude-token
   # Add to .gitignore
   # Never commit to version control
   ```

5. **Monitor Usage**
   ```bash
   # Daily check
   claude usage

   # Set up alerts
   claude-usage-monitor --alert-threshold 80
   ```

### ❌ DON'T

1. **Don't Build Public SaaS on Max Subscription**
   ```
   ❌ Multi-tenant app using your Max quota
   ✅ Personal tools using your Max quota
   ✅ Public app using customers' API keys
   ```

2. **Don't Share Session Tokens**
   ```
   ❌ Hardcode in source code
   ❌ Share in environment files
   ❌ Give to team members (they need own subscription)
   ```

3. **Don't Assume Unlimited Usage**
   ```
   Even Max 20x has limits:
   - 800 prompts per 5 hours
   - NOT unlimited
   - Plan accordingly
   ```

4. **Don't Bypass Official Methods**
   ```
   ❌ Reverse engineering auth flows
   ❌ Extracting tokens via browser devtools
   ❌ Using undocumented APIs
   ```

---

## Troubleshooting

### Issue: "Not authenticated" Error

**Symptoms:**
```
Error: Not authenticated with Claude
```

**Solutions:**
```bash
# 1. Check authentication status
claude auth status

# 2. If not authenticated, login again
claude login

# 3. Verify credentials
claude whoami
# Should show your Max subscription email
```

### Issue: Token Expired in Containerized Setup

**Symptoms:**
```json
{"error": "invalid_session_token"}
```

**Solutions:**
```bash
# 1. Extract new token
claude auth token > .claude-token

# 2. Restart container
docker-compose restart

# 3. Automated refresh (add to cron):
# Run every 24 hours
0 */24 * * * claude auth token > /path/to/.claude-token && docker-compose restart
```

### Issue: Rate Limit Errors

**Symptoms:**
```
RateLimitError: Usage limit exceeded
```

**Solutions:**
```python
# Check usage first
import subprocess
result = subprocess.run(['claude', 'usage'], capture_output=True, text=True)
print(result.stdout)

# Wait until quota resets (shown in output)

# Implement queue system for batch operations
from queue import Queue
import time

class ClaudeQueue:
    def __init__(self):
        self.queue = Queue()

    def add_request(self, message):
        self.queue.put(message)

    def process(self):
        while not self.queue.empty():
            try:
                message = self.queue.get()
                # Process message
                response = chat_with_retry(message)
                self.queue.task_done()
            except RateLimitError:
                # Re-queue and wait
                self.queue.put(message)
                time.sleep(3600)  # Wait 1 hour
```

### Issue: "Third-party application detected"

**Symptoms:**
```
Error: This application cannot use subscription credentials
```

**Cause**: Anthropic detects usage outside approved tools

**Solutions:**
1. Use official API keys for production apps
2. Keep personal automation local only
3. Don't distribute apps using Max subscription

### Issue: Environment Variable Conflicts

**Symptoms**: Claude Code uses API key instead of subscription

**Check:**
```bash
# Look for conflicting variables
env | grep ANTHROPIC

# Should NOT see:
# ANTHROPIC_API_KEY=...
# ANTHROPIC_BASE_URL=...
```

**Fix:**
```bash
# Unset conflicts
unset ANTHROPIC_API_KEY
unset ANTHROPIC_BASE_URL

# Verify subscription usage
./scripts/check_auth_config.sh
```

---

## Summary: Decision Matrix

| Use Case | Recommended Method | Reasoning |
|----------|-------------------|-----------|
| **Local development** | Claude Code CLI + `claude login` | ✅ Official, supported, easy |
| **Personal automation** | CLI + session token extraction | ⚠️ Works but ToS unclear |
| **Team collaboration** | Each person: own subscription | ✅ Proper licensing |
| **Production SaaS** | Anthropic API with API keys | ✅ Only supported method |
| **Internal tools** | Containerized with session tokens | ⚠️ Personal use okay, commercial unclear |
| **Open source tool** | Support both subscription AND API keys | ✅ Give users choice |
| **Customer-facing app** | API keys (customers provide their own) | ✅ Proper model |

---

## Additional Resources

**Official Documentation:**
- [Claude Code Overview](https://docs.claude.com/en/docs/claude-code)
- [Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk/overview)
- [Using Pro/Max with Claude Code](https://support.claude.com/en/articles/11145838)

**Community Projects:**
- [claude-agent-sdk-container](https://github.com/receipting/claude-agent-sdk-container)
- [ai-sdk-provider-claude-code](https://github.com/ben-vargas/ai-sdk-provider-claude-code)
- [Claude Code Usage Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor)

**Tools Integration:**
- [Cline](https://cline.bot/) - VS Code AI agent
- [Cursor](https://cursor.sh/) - AI code editor
- [Zed](https://zed.dev/) - Collaborative code editor

---

## Legal & Ethical Considerations

**From Anthropic's Terms:**
> Third-party developers are not allowed to apply Claude.ai rate limits for their products.

**Interpretation:**
- ✅ **Allowed**: Personal use of Max subscription with Claude Code
- ✅ **Allowed**: Using subscription for your own development
- ⚠️ **Unclear**: Personal automation scripts (not explicitly forbidden)
- ❌ **Forbidden**: Building SaaS products on Max subscription
- ❌ **Forbidden**: Reselling Max subscription access

**Best Practice:**
- When in doubt, use API keys for production
- Max subscription = personal productivity tool
- API = programmatic/commercial access

**Contact Anthropic** for clarification on specific use cases:
- Email: support@anthropic.com
- Specify your use case clearly
- Get written confirmation if building commercial product

---

**Last Updated**: 2025-10-19
**Claude Code Version**: Latest
**Max Subscription**: 20x tier ($200/month)
