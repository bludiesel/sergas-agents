# CLI User Guide - Sergas Super Account Manager

**Version:** 1.0.0
**Last Updated:** 2025-10-19
**Target Audience:** Power users, developers, automation engineers

---

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Basic Commands](#basic-commands)
5. [Advanced Usage](#advanced-usage)
6. [Troubleshooting](#troubleshooting)
7. [Examples](#examples)

---

## Introduction

The Sergas CLI provides command-line access to the AI-powered account management system. It's ideal for:

- **Automation**: Integrate with scripts and CI/CD pipelines
- **Batch Processing**: Analyze multiple accounts efficiently
- **Development**: Test agent behavior during development
- **Power Users**: Advanced users who prefer terminal interfaces

### Key Features

- Real-time streaming output with progress indicators
- Interactive approval workflow
- JSON output for programmatic consumption
- Comprehensive error reporting
- Session management and history

---

## Installation

### Prerequisites

- Python 3.14 or higher
- Zoho CRM account with API access
- Anthropic API key (Claude Agent SDK)

### Install from Source

```bash
# Clone repository
git clone https://github.com/mohammadabdelrahman/sergas-agents.git
cd sergas-agents

# Create virtual environment
python3.14 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install CLI in development mode
pip install -e .
```

### Verify Installation

```bash
sergas --version
# Output: Sergas CLI v1.0.0

sergas --help
# Output: Usage information
```

---

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# Anthropic API Configuration
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Zoho CRM Configuration
ZOHO_CLIENT_ID=1000.ABC123...
ZOHO_CLIENT_SECRET=abc123def456...
ZOHO_REFRESH_TOKEN=1000.abc123...
ZOHO_DOMAIN=https://www.zohoapis.com

# Cognee Configuration
COGNEE_API_URL=http://localhost:8000
COGNEE_API_KEY=optional_api_key

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Configuration File

Alternatively, use a YAML configuration file:

```bash
sergas config init
# Creates ~/.sergas/config.yml
```

Edit `~/.sergas/config.yml`:

```yaml
anthropic:
  api_key: ${ANTHROPIC_API_KEY}
  model: claude-3-5-sonnet-20241022

zoho:
  client_id: ${ZOHO_CLIENT_ID}
  client_secret: ${ZOHO_CLIENT_SECRET}
  refresh_token: ${ZOHO_REFRESH_TOKEN}
  domain: https://www.zohoapis.com

cognee:
  api_url: http://localhost:8000
  api_key: optional_key

preferences:
  auto_approve: false
  output_format: pretty
  color_output: true
```

---

## Basic Commands

### 1. Analyze an Account

Analyze a single account and get AI-generated recommendations:

```bash
sergas analyze ACC-001
```

**Output:**
```
🔍 Analyzing account ACC-001...

✓ Retrieving account data from Zoho CRM
✓ Querying historical context from Cognee
✓ Generating recommendations

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Account: Acme Corporation (ACC-001)
Status: Active
Health Score: 78/100
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 RECOMMENDATIONS (3):

1. [HIGH PRIORITY] Follow-up Required
   • Last contact: 45 days ago
   • Confidence: 92%
   • Action: Schedule check-in call
   • Reason: Long gap since last interaction

2. [MEDIUM] Update Account Status
   • Current: Active → Hot Lead
   • Confidence: 85%
   • Action: Change status in CRM
   • Reason: Recent engagement spike detected

3. [LOW] Add to Nurture Campaign
   • Campaign: Q4 Upsell Campaign
   • Confidence: 72%
   • Action: Add to campaign
   • Reason: Fits target profile

🔒 Approve recommendations to update CRM? [y/N]:
```

### 2. Batch Analysis

Analyze multiple accounts:

```bash
# From account list
sergas analyze ACC-001 ACC-002 ACC-003

# From file
sergas analyze --from-file accounts.txt

# All accounts (with filters)
sergas analyze --all --status Active --owner "John Doe"
```

### 3. View Recommendations

Display recommendations without updating CRM:

```bash
sergas analyze ACC-001 --dry-run

# Output as JSON
sergas analyze ACC-001 --format json > recommendations.json
```

### 4. History and Sessions

View past analyses:

```bash
# List recent sessions
sergas history

# View specific session
sergas history show session-123

# Export session data
sergas history export session-123 --format json
```

---

## Advanced Usage

### Approval Workflow

#### Interactive Approval

```bash
sergas analyze ACC-001
# Prompts for approval after showing recommendations
```

#### Auto-Approve (Use with caution!)

```bash
sergas analyze ACC-001 --auto-approve

# Or set in config
sergas config set preferences.auto_approve true
```

#### Selective Approval

```bash
sergas analyze ACC-001 --interactive
# Allows approving/rejecting individual recommendations
```

### Filtering and Queries

```bash
# Analyze high-risk accounts only
sergas analyze --all --health-score "<60"

# Accounts with recent changes
sergas analyze --all --changed-since "7 days ago"

# By account owner
sergas analyze --all --owner "jane@example.com"
```

### Output Formats

```bash
# Pretty print (default)
sergas analyze ACC-001

# JSON output
sergas analyze ACC-001 --format json

# CSV export
sergas analyze --all --format csv > accounts_report.csv

# Markdown report
sergas analyze ACC-001 --format markdown > report.md
```

### Custom Agent Configuration

```bash
# Use specific system prompt
sergas analyze ACC-001 --prompt "Focus on upsell opportunities"

# Limit tools available
sergas analyze ACC-001 --tools zoho_get_account,cognee_search

# Set permission mode
sergas analyze ACC-001 --permission-mode bypassPermissions
```

### Debugging

```bash
# Verbose output
sergas analyze ACC-001 --verbose

# Debug mode with full traces
sergas analyze ACC-001 --debug

# Show tool calls
sergas analyze ACC-001 --show-tools
```

---

## Troubleshooting

### Common Issues

#### 1. Authentication Errors

**Symptom:** `Unauthorized: Invalid API key`

**Solution:**
```bash
# Verify API key is set
echo $ANTHROPIC_API_KEY

# Re-initialize config
sergas config init

# Test connection
sergas test-connection
```

#### 2. Zoho CRM Connection Failed

**Symptom:** `Failed to connect to Zoho CRM`

**Solution:**
```bash
# Refresh Zoho token
sergas zoho refresh-token

# Verify credentials
sergas zoho test-connection

# Check MCP server status
sergas mcp status zoho
```

#### 3. Slow Performance

**Symptom:** Analysis takes >2 minutes

**Solutions:**
```bash
# Check service status
sergas health

# View metrics
sergas metrics

# Clear cache
sergas cache clear
```

#### 4. Tool Permission Errors

**Symptom:** `Permission denied for tool: zoho_update_account`

**Solution:**
```bash
# Check allowed tools
sergas config get agents.zoho_data_scout.allowed_tools

# Update tool permissions
sergas config set agents.zoho_data_scout.permission_mode acceptEdits
```

### Getting Help

```bash
# General help
sergas --help

# Command-specific help
sergas analyze --help

# Show current configuration
sergas config show

# Run diagnostics
sergas diagnose
```

---

## Examples

### Example 1: Daily Account Review

```bash
#!/bin/bash
# daily_review.sh - Review all active accounts

sergas analyze --all \
  --status Active \
  --changed-since "24 hours ago" \
  --format json \
  --output daily_report_$(date +%Y%m%d).json

echo "Daily review complete!"
```

### Example 2: High-Risk Account Alert

```bash
#!/bin/bash
# alert_high_risk.sh - Alert on high-risk accounts

HIGH_RISK=$(sergas analyze --all \
  --health-score "<50" \
  --format json \
  | jq -r '.accounts[].id')

if [ -n "$HIGH_RISK" ]; then
  echo "High-risk accounts found: $HIGH_RISK"
  # Send alert email
  sergas analyze $HIGH_RISK --format markdown \
    | mail -s "High-Risk Account Alert" team@example.com
fi
```

### Example 3: Interactive Batch Processing

```bash
#!/bin/bash
# interactive_batch.sh - Process accounts with approval

while IFS= read -r account_id; do
  echo "Processing $account_id..."
  sergas analyze "$account_id" --interactive

  read -p "Continue to next account? [y/N] " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    break
  fi
done < accounts_to_review.txt
```

### Example 4: Export Recommendations

```bash
# Export all recommendations to CSV
sergas analyze --all \
  --format csv \
  --fields "account_id,recommendation,confidence,action" \
  > recommendations_$(date +%Y%m%d).csv

# Upload to Google Sheets (using gsheet CLI)
gsheet upload recommendations_$(date +%Y%m%d).csv \
  --spreadsheet "Account Recommendations"
```

### Example 5: Scheduled Analysis with Cron

```bash
# Add to crontab (crontab -e)

# Run every weekday at 9 AM
0 9 * * 1-5 /path/to/sergas analyze --all --auto-approve >> /var/log/sergas_daily.log 2>&1

# Weekly summary on Friday at 5 PM
0 17 * * 5 /path/to/sergas analyze --all --format markdown | mail -s "Weekly Account Summary" team@example.com
```

---

## Appendix

### Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `sergas analyze <id>` | Analyze single account | `sergas analyze ACC-001` |
| `sergas analyze --all` | Analyze all accounts | `sergas analyze --all --status Active` |
| `sergas history` | View session history | `sergas history --limit 10` |
| `sergas config` | Manage configuration | `sergas config show` |
| `sergas test-connection` | Test API connections | `sergas test-connection` |
| `sergas health` | Service health check | `sergas health --verbose` |
| `sergas zoho` | Zoho CRM utilities | `sergas zoho refresh-token` |
| `sergas mcp` | MCP server management | `sergas mcp status` |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | Required |
| `ANTHROPIC_MODEL` | Claude model version | `claude-3-5-sonnet-20241022` |
| `ZOHO_CLIENT_ID` | Zoho OAuth client ID | Required |
| `ZOHO_CLIENT_SECRET` | Zoho OAuth secret | Required |
| `ZOHO_REFRESH_TOKEN` | Zoho refresh token | Required |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `SERGAS_CONFIG` | Config file path | `~/.sergas/config.yml` |

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error |
| `2` | Configuration error |
| `3` | Authentication error |
| `4` | API error |
| `5` | Permission denied |

---

**Need Help?**

- 📚 [Full Documentation](https://docs.sergas.com)
- 🐛 [Report Issues](https://github.com/mohammadabdelrahman/sergas-agents/issues)
- 💬 [Discussions](https://github.com/mohammadabdelrahman/sergas-agents/discussions)
- 📧 Email: support@sergas.com
