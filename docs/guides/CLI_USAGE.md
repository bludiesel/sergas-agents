# CLI User Guide

Production-ready command-line interface for Sergas Account Manager with live event streaming and interactive workflows.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Commands](#commands)
- [Event Types](#event-types)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)
- [Examples](#examples)

## Installation

### Automated Setup

Run the setup script to automatically install dependencies and configure the CLI:

```bash
chmod +x scripts/cli_setup.sh
./scripts/cli_setup.sh
```

The setup script will:
- Install required Python packages (click, rich, httpx)
- Create a `sergas` alias in your shell configuration
- Validate Python installation

### Manual Installation

If you prefer manual installation:

```bash
# Install dependencies
pip install click rich httpx

# Add alias to your shell configuration
echo 'alias sergas="python3 -m src.cli.agent_cli"' >> ~/.bashrc  # or ~/.zshrc

# Reload shell
source ~/.bashrc  # or ~/.zshrc
```

### Verify Installation

Check that the CLI is properly installed:

```bash
sergas --version
sergas --help
```

## Quick Start

### 1. Start the Backend

Ensure the backend API is running:

```bash
# In a separate terminal
python -m src.main
```

The backend should be accessible at `http://localhost:8000` by default.

### 2. Check Health

Verify backend connectivity:

```bash
sergas health
```

Expected output:
```
✓ Backend is healthy
```

### 3. Analyze an Account

Run your first account analysis:

```bash
sergas analyze --account-id ACC-001
```

The CLI will:
1. Connect to the backend
2. Stream real-time agent progress
3. Display recommendations in a table
4. Prompt for approval
5. Show final workflow summary

## Commands

### `analyze`

Analyze an account with AI agents and live event streaming.

**Usage:**
```bash
sergas analyze [OPTIONS]
```

**Required Options:**
- `--account-id TEXT`: Zoho CRM account ID to analyze (e.g., ACC-001)

**Optional Flags:**
- `--api-url TEXT`: Backend API URL (default: `http://localhost:8000`)
- `--auto-approve`: Automatically approve all recommendations
- `--workflow TEXT`: Workflow type (default: `account_analysis`)
- `--timeout INTEGER`: Request timeout in seconds (default: 300)
- `--verbose`: Enable verbose output with detailed event data

**Examples:**

```bash
# Basic interactive analysis
sergas analyze --account-id ACC-001

# Auto-approve recommendations (for automation)
sergas analyze --account-id ACC-001 --auto-approve

# Custom backend URL
sergas analyze --account-id ACC-001 --api-url https://api.production.com

# Verbose output for debugging
sergas analyze --account-id ACC-001 --verbose

# Custom workflow with timeout
sergas analyze --account-id ACC-001 --workflow risk_assessment --timeout 600
```

### `health`

Check backend health status and connectivity.

**Usage:**
```bash
sergas health [OPTIONS]
```

**Optional Flags:**
- `--api-url TEXT`: Backend API URL (default: `http://localhost:8000`)
- `--verbose`: Show detailed health information

**Examples:**

```bash
# Basic health check
sergas health

# Check production backend
sergas health --api-url https://api.production.com

# Detailed health info
sergas health --verbose
```

## Event Types

The CLI displays real-time events during workflow execution:

### Workflow Events

**`workflow_started`**
- **Display:** `✓ Workflow started: account_analysis`
- **Description:** Workflow has begun executing

**`workflow_completed`**
- **Display:** `✓ WORKFLOW COMPLETED` + summary panel
- **Description:** Workflow finished successfully

**`workflow_error`**
- **Display:** `✗ ERROR: WorkflowError`
- **Description:** Critical workflow failure

### Agent Events

**`agent_started`**
- **Display:** `→ Step 1: zoho_scout`
- **Description:** An agent has started executing

**`agent_stream`**
- **Display:** `  → Retrieved account snapshot for Acme Corp`
- **Description:** Real-time progress updates from agent

**`agent_completed`**
- **Display:** `✓ zoho_scout completed`
- **Description:** Agent finished execution

**`agent_error`**
- **Display:** `✗ ERROR: AgentError`
- **Description:** Agent encountered an error

### Tool Events

**`tool_call`**
- **Display:** `  🔧 Tool: get_account_snapshot`
- **Description:** Agent is calling a tool

**`tool_result`**
- **Display:** `  ✓ Tool completed`
- **Description:** Tool execution finished

### Approval Events

**`approval_required`**
- **Display:** Table of recommendations + approval prompt
- **Description:** User approval needed to proceed

## Advanced Usage

### Automation Scripts

Use the CLI in automation scripts with `--auto-approve`:

```bash
#!/bin/bash
# Automated daily account analysis

ACCOUNTS=("ACC-001" "ACC-002" "ACC-003")

for account in "${ACCOUNTS[@]}"; do
    echo "Analyzing $account..."
    sergas analyze --account-id "$account" --auto-approve
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
done
```

### CI/CD Integration

Integrate into continuous integration pipelines:

```yaml
# GitHub Actions example
name: Account Analysis
on:
  schedule:
    - cron: '0 9 * * *'  # Daily at 9 AM

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install CLI
        run: |
          pip install click rich httpx

      - name: Run Analysis
        run: |
          python -m src.cli.agent_cli analyze \
            --account-id ${{ secrets.ACCOUNT_ID }} \
            --api-url ${{ secrets.API_URL }} \
            --auto-approve \
            --verbose
```

### Custom API URLs

Connect to different environments:

```bash
# Development
sergas analyze --account-id ACC-001 --api-url http://localhost:8000

# Staging
sergas analyze --account-id ACC-001 --api-url https://staging-api.sergas.com

# Production
sergas analyze --account-id ACC-001 --api-url https://api.sergas.com
```

### Verbose Debugging

Enable detailed output for troubleshooting:

```bash
sergas analyze --account-id ACC-001 --verbose
```

Verbose mode shows:
- Raw event data
- Agent output details
- Complete workflow output JSON
- Stack traces for errors

## Troubleshooting

### Connection Errors

**Problem:** `Cannot connect to backend`

**Solutions:**
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check URL is correct: `sergas health --api-url http://localhost:8000`
3. Verify firewall settings allow connections
4. Check for proxy/VPN interference

### Timeout Errors

**Problem:** `Request timeout after 300s`

**Solutions:**
1. Increase timeout: `--timeout 600`
2. Check backend logs for slow queries
3. Verify network connectivity is stable
4. Consider breaking into smaller workflows

### Approval Not Received

**Problem:** Workflow times out waiting for approval

**Solutions:**
1. Respond to approval prompt within timeout period
2. Use `--auto-approve` for automated workflows
3. Increase approval timeout in backend configuration

### Invalid Events

**Problem:** `Warning: Invalid JSON event`

**Solutions:**
1. Update CLI to latest version
2. Verify backend is using compatible AG UI Protocol
3. Check network is not corrupting SSE stream
4. Enable `--verbose` to inspect event data

## Examples

### Basic Account Analysis

```bash
sergas analyze --account-id ACC-001
```

**Output:**
```
╭───────────────────────────────────────╮
│ Sergas Account Analysis               │
│ Account ID: ACC-001                   │
│ Workflow: account_analysis            │
│ API URL: http://localhost:8000        │
╰───────────────────────────────────────╯

✓ Workflow started: account_analysis

→ Step 1: zoho_scout
  Fetching account data from Zoho CRM
  → Retrieved account snapshot for Acme Corp
  → Detected 3 risk signals
✓ zoho_scout completed

→ Step 2: memory_analyst
  Analyzing historical patterns and context
  → Analyzed 47 historical events
  → Detected 5 patterns
  → Sentiment trend: improving
✓ memory_analyst completed

⚠ APPROVAL REQUIRED

╭────────────── Generated Recommendations ──────────────╮
│ ID          Category    Title                Priority │
├─────────────────────────────────────────────────────────┤
│ rec_a1b2c3  engagement  Schedule follow-up   HIGH     │
│ rec_d4e5f6  revenue     Upsell opportunity   MEDIUM   │
╰─────────────────────────────────────────────────────────╯

Do you approve these recommendations? [Y/n]: y

✓ Recommendations approved

✓ WORKFLOW COMPLETED

╭──────────── Workflow Summary ────────────╮
│ Status: COMPLETED                        │
│ Account ID: ACC-001                      │
│ Duration: 12.3s                          │
│                                          │
│ Execution Summary:                       │
│ - Agents completed: 2                    │
│ - Tool calls: 5                          │
│ - Approvals: 1                           │
│                                          │
│ Results:                                 │
│ - Zoho data fetched: ✓                   │
│ - Historical context: ✓                  │
│ - Recommendations: 2                     │
│ - Risk level: medium                     │
╰──────────────────────────────────────────╯
```

### Automated Analysis with Auto-Approve

```bash
sergas analyze --account-id ACC-002 --auto-approve
```

**Use Case:** Scheduled batch processing, CI/CD pipelines

### Production Backend Analysis

```bash
sergas analyze \
  --account-id ACC-003 \
  --api-url https://api.production.com \
  --timeout 600 \
  --verbose
```

**Use Case:** Production monitoring, detailed diagnostics

### Health Check Before Analysis

```bash
# Check health first
sergas health || exit 1

# Run analysis if healthy
sergas analyze --account-id ACC-004
```

**Use Case:** Robust automation scripts

---

## Additional Resources

- **Backend Documentation:** `docs/architecture/AG_UI_PROTOCOL.md`
- **Orchestrator Implementation:** `src/agents/orchestrator.py`
- **Event Schema:** `src/events/ag_ui_emitter.py`
- **API Reference:** `docs/api/COPILOTKIT_ROUTER.md`

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review backend logs: `tail -f logs/app.log`
3. Enable verbose mode: `--verbose`
4. Check event stream with curl: `curl -N http://localhost:8000/api/copilotkit`
