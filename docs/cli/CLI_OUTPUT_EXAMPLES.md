# CLI Output Examples

Visual examples of Sergas CLI in action.

## 1. Help Command

```bash
$ sergas --help
```

**Output:**
```
Usage: python -m src.cli.agent_cli [OPTIONS] COMMAND [ARGS]...

  Sergas Account Manager CLI - AI-powered account analysis.

  Features:
  - Live event streaming from AI agents
  - Interactive approval workflows
  - Rich terminal UI with progress tracking
  - Real-time account analysis

  Examples:
      sergas analyze --account-id ACC-001
      sergas analyze --account-id ACC-001 --auto-approve
      sergas health --api-url http://localhost:8000

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  analyze  Analyze account with AI agents and live event streaming.
  health   Check backend health status and connectivity.
```

## 2. Account Analysis (Interactive)

```bash
$ sergas analyze --account-id ACC-001
```

**Output:**

```
╭───────────────────────────────────────────────────────────────╮
│ Sergas Account Analysis                                       │
│ Account ID: ACC-001                                           │
│ Workflow: account_analysis                                    │
│ API URL: http://localhost:8000                                │
╰───────────────────────────────────────────────────────────────╯

✓ Workflow started: account_analysis

→ Step 1: zoho_scout
  Fetching account data from Zoho CRM
  → Retrieved account snapshot for Acme Corporation
  → Detected 3 risk signals
  🔧 Tool: get_account_snapshot
  ✓ Tool completed
✓ zoho_scout completed

→ Step 2: memory_analyst
  Analyzing historical patterns and context
  → Analyzed 47 historical events
  → Detected 5 patterns
  → Sentiment trend: improving
  🔧 Tool: get_historical_context
  ✓ Tool completed
✓ memory_analyst completed

⚠ APPROVAL REQUIRED

╭───────────────── Generated Recommendations ─────────────────╮
│ ID          Category      Title                     Priority│
├──────────────────────────────────────────────────────────────┤
│ rec_a1b2c3  engagement    Schedule follow-up call   HIGH    │
│ rec_d4e5f6  revenue       Upsell opportunity        MEDIUM  │
│ rec_g7h8i9  retention     Review contract terms     LOW     │
╰──────────────────────────────────────────────────────────────╯

**Reasoning:** Account showing decreased engagement over last 30 days

**Expected Impact:** Prevent potential churn and identify growth opportunities

**Next Steps:** Review and implement

Do you approve these recommendations? [Y/n]: y

✓ Recommendations approved

✓ WORKFLOW COMPLETED

╭─────────────────── Workflow Summary ───────────────────╮
│ Status: COMPLETED                                      │
│ Account ID: ACC-001                                    │
│ Workflow: account_analysis                             │
│ Duration: 12.3s                                        │
│                                                        │
│ Execution Summary:                                     │
│ - Agents completed: 2                                  │
│ - Tool calls: 5                                        │
│ - Approvals: 1                                         │
│                                                        │
│ Results:                                               │
│ - Zoho data fetched: ✓                                 │
│ - Historical context: ✓                                │
│ - Recommendations: 3                                   │
│ - Risk level: medium                                   │
│ - Sentiment trend: improving                           │
╰────────────────────────────────────────────────────────╯
```

## 3. Account Analysis (Auto-Approve)

```bash
$ sergas analyze --account-id ACC-002 --auto-approve
```

**Output:**

```
╭───────────────────────────────────────────────────────────────╮
│ Sergas Account Analysis                                       │
│ Account ID: ACC-002                                           │
│ Workflow: account_analysis                                    │
│ API URL: http://localhost:8000                                │
╰───────────────────────────────────────────────────────────────╯

⚠ Auto-approve mode enabled - all recommendations will be approved automatically

✓ Workflow started: account_analysis

→ Step 1: zoho_scout
  Fetching account data from Zoho CRM
  → Retrieved account snapshot for TechStart Inc
  → Detected 1 risk signals
✓ zoho_scout completed

→ Step 2: memory_analyst
  Analyzing historical patterns and context
  → Analyzed 23 historical events
  → Detected 2 patterns
  → Sentiment trend: stable
✓ memory_analyst completed

⚠ APPROVAL REQUIRED

╭───────────────── Generated Recommendations ─────────────────╮
│ ID          Category      Title                     Priority│
├──────────────────────────────────────────────────────────────┤
│ rec_j1k2l3  engagement    Send quarterly review     MEDIUM  │
╰──────────────────────────────────────────────────────────────╯

✓ Auto-approving...

✓ Recommendations approved

✓ WORKFLOW COMPLETED

╭─────────────────── Workflow Summary ───────────────────╮
│ Status: COMPLETED                                      │
│ Account ID: ACC-002                                    │
│ Duration: 8.7s                                         │
│                                                        │
│ Execution Summary:                                     │
│ - Agents completed: 2                                  │
│ - Tool calls: 3                                        │
│ - Approvals: 1 (auto)                                  │
│                                                        │
│ Results:                                               │
│ - Zoho data fetched: ✓                                 │
│ - Historical context: ✓                                │
│ - Recommendations: 1                                   │
│ - Risk level: low                                      │
╰────────────────────────────────────────────────────────╯
```

## 4. Health Check (Success)

```bash
$ sergas health
```

**Output:**

```
Checking health of: http://localhost:8000

✓ Backend is healthy
```

**Verbose:**

```bash
$ sergas health --verbose
```

```
Checking health of: http://localhost:8000

✓ Backend is healthy

┌───────────┬────────────────────────────────────────┐
│ Status    │ healthy                                │
│ Service   │ ag-ui-protocol                         │
│ Timestamp │ 2025-10-19T10:30:45.123456             │
└───────────┴────────────────────────────────────────┘
```

## 5. Health Check (Failure)

```bash
$ sergas health
```

**Output:**

```
Checking health of: http://localhost:8000

✗ Cannot connect to backend
URL: http://localhost:8000

Troubleshooting:
  1. Ensure backend is running
  2. Check URL is correct
  3. Verify firewall settings
```

## 6. Verbose Analysis

```bash
$ sergas analyze --account-id ACC-003 --verbose
```

**Output:**

```
╭───────────────────────────────────────────────────────────────╮
│ Sergas Account Analysis                                       │
│ Account ID: ACC-003                                           │
│ Workflow: account_analysis                                    │
│ API URL: http://localhost:8000                                │
╰───────────────────────────────────────────────────────────────╯

Event: workflow_started
✓ Workflow started: account_analysis

Event: agent_started
→ Step 1: zoho_scout
  Fetching account data from Zoho CRM

Event: agent_stream
  → Retrieved account snapshot for Global Enterprises

Event: tool_call
  🔧 Tool: get_account_snapshot

Event: tool_result
  ✓ Tool completed

Event: agent_completed
✓ zoho_scout completed

╭────────────────── zoho_scout output ──────────────────╮
│ {                                                     │
│   "status": "success",                                │
│   "snapshot_id": "snap_abc123",                       │
│   "risk_level": "medium",                             │
│   "priority_score": 75                                │
│ }                                                     │
╰───────────────────────────────────────────────────────╯

Event: agent_started
→ Step 2: memory_analyst
  Analyzing historical patterns and context

[... more verbose events ...]

✓ WORKFLOW COMPLETED

╭─────────────────── Complete Output ────────────────────╮
│ {                                                      │
│   "status": "completed",                               │
│   "account_id": "ACC-003",                             │
│   "workflow": "account_analysis",                      │
│   "approval": {                                        │
│     "status": "approved",                              │
│     "approved_by": "user",                             │
│     "timestamp": "2025-10-19T10:35:12.456789"          │
│   },                                                   │
│   "recommendations": [                                 │
│     {                                                  │
│       "recommendation_id": "rec_m4n5o6",               │
│       "category": "engagement",                        │
│       "priority": "high",                              │
│       "confidence_score": 87                           │
│     }                                                  │
│   ],                                                   │
│   "execution_summary": {                               │
│     "zoho_data_fetched": true,                         │
│     "historical_context_retrieved": true,              │
│     "recommendations_generated": 1,                    │
│     "risk_level": "medium",                            │
│     "sentiment_trend": "improving"                     │
│   }                                                    │
│ }                                                      │
╰────────────────────────────────────────────────────────╯
```

## 7. Error Handling

### Connection Error

```bash
$ sergas analyze --account-id ACC-004
```

**Output:**

```
╭───────────────────────────────────────────────────────────────╮
│ Sergas Account Analysis                                       │
│ Account ID: ACC-004                                           │
│ Workflow: account_analysis                                    │
│ API URL: http://localhost:8000                                │
╰───────────────────────────────────────────────────────────────╯

✗ Connection failed

Error: Cannot connect to http://localhost:8000
Ensure backend is running and accessible
```

### Workflow Error

```bash
$ sergas analyze --account-id INVALID-ID
```

**Output:**

```
✓ Workflow started: account_analysis

→ Step 1: zoho_scout
  Fetching account data from Zoho CRM

✗ ERROR: DataFetchError
Failed to fetch account data: Account not found

╭──────────────────── Stack Trace ──────────────────────╮
│ Traceback (most recent call last):                   │
│   File "zoho_data_scout.py", line 123                 │
│     snapshot = client.get_account(account_id)         │
│ DataFetchError: Account INVALID-ID not found          │
╰───────────────────────────────────────────────────────╯
```

## 8. Production Backend Analysis

```bash
$ sergas analyze --account-id ACC-005 --api-url https://api.production.com --timeout 600
```

**Output:**

```
╭───────────────────────────────────────────────────────────────╮
│ Sergas Account Analysis                                       │
│ Account ID: ACC-005                                           │
│ Workflow: account_analysis                                    │
│ API URL: https://api.production.com                           │
╰───────────────────────────────────────────────────────────────╯

[... normal workflow output ...]
```

## 9. Timeout Handling

```bash
$ sergas analyze --account-id ACC-006 --timeout 30
```

**Output:**

```
✓ Workflow started: account_analysis

→ Step 1: zoho_scout
  Fetching account data from Zoho CRM
  [... processing ...]

✗ Request timeout

Error: Request timeout after 30s
```

## 10. Live Progress Tracking

**While Running:**

```
╭───────────────────────────────────────────────────────────────╮
│ Sergas Account Analysis                                       │
│ Account ID: ACC-007                                           │
╰───────────────────────────────────────────────────────────────╯

⠋ Running account_analysis...  Duration: 5.2s | Agents: 1/2 | Tools: 3
```

The spinner (⠋) animates while workflow is active, and the status bar updates in real-time.

---

**Note:** All examples show actual CLI output with Rich formatting. Colors and borders appear in terminal but are represented here in plain text.
