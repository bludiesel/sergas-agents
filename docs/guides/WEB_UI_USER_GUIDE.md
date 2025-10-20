# Web UI User Guide - Sergas Super Account Manager

**Version:** 1.0.0
**Last Updated:** 2025-10-19
**Target Audience:** Account Executives, Sales Managers, Business Users

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Accessing the Interface](#accessing-the-interface)
3. [Analyzing an Account](#analyzing-an-account)
4. [Understanding Recommendations](#understanding-recommendations)
5. [Approval Workflow](#approval-workflow)
6. [Viewing Tool Calls](#viewing-tool-calls)
7. [Dashboard Features](#dashboard-features)
8. [Tips and Best Practices](#tips-and-best-practices)

---

## Getting Started

### What is Sergas Super Account Manager?

Sergas is an AI-powered assistant that helps you manage your CRM accounts more efficiently. It:

- **Monitors** your accounts for important changes
- **Analyzes** historical context and patterns
- **Recommends** actions to improve account health
- **Streamlines** CRM updates with intelligent automation

### Key Benefits

- **60% Time Savings**: Reduce account review time from 8+ minutes to <3 minutes
- **Proactive Insights**: Never miss important account changes
- **Smart Recommendations**: AI-generated actions with confidence scores
- **Safe Updates**: All CRM modifications require your approval

---

## Accessing the Interface

### Login

1. Navigate to `https://app.sergas.com`
2. Click **Sign In**
3. Authenticate with your company credentials
4. You'll be redirected to your dashboard

### Initial Setup

On first login, you'll need to connect your Zoho CRM account:

1. Click **Settings** → **Integrations**
2. Click **Connect Zoho CRM**
3. Authorize Sergas to access your CRM data
4. Verify connection (green checkmark appears)

---

## Analyzing an Account

### Quick Analysis

**Step 1:** Navigate to the analysis page

- Click **Analyze Account** in the sidebar
- Or use the quick search bar (press `/`)

**Step 2:** Enter account information

```
┌───────────────────────────────────────┐
│  Which account should I analyze?      │
│                                       │
│  ┌─────────────────────────────────┐ │
│  │ ACC-001  🔍 Search...           │ │
│  └─────────────────────────────────┘ │
│                                       │
│  Recent accounts:                     │
│  • Acme Corporation (ACC-001)         │
│  • TechCorp Ltd (ACC-002)             │
│  • Global Industries (ACC-003)        │
└───────────────────────────────────────┘
```

**Step 3:** Click **Analyze** or press Enter

### What Happens During Analysis?

You'll see real-time progress as the AI:

1. **Retrieves Data** 📥
   - Fetches account details from Zoho CRM
   - Shows account name, status, and key metrics

2. **Analyzes History** 🧠
   - Searches historical context
   - Identifies patterns and trends

3. **Generates Recommendations** 💡
   - Creates actionable insights
   - Calculates confidence scores

### Example Analysis Screen

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 Acme Corporation (ACC-001)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Account Overview
────────────────────────────────────────────────
Status: Active              Owner: Jane Doe
Health: 78/100 🟢           Last Contact: 45 days ago
Revenue: $125,000           Industry: Technology
Open Deals: 2 ($50,000)     Risk Level: Low

🔄 Recent Activity (Loading...)
  ✓ Retrieved account data
  ✓ Analyzed 24 historical interactions
  ✓ Identified 3 opportunities

💡 AI is generating recommendations...
```

---

## Understanding Recommendations

### Recommendation Cards

Each recommendation is displayed as a card:

```
┌─────────────────────────────────────────────────┐
│ 🔴 HIGH PRIORITY • Confidence: 92%              │
├─────────────────────────────────────────────────┤
│ Follow-up Required                              │
│                                                 │
│ 📝 Details:                                     │
│ Last contact was 45 days ago, which exceeds     │
│ the recommended 30-day cadence for active       │
│ accounts.                                       │
│                                                 │
│ 🎯 Recommended Action:                          │
│ Schedule a check-in call within 3 business days │
│                                                 │
│ 💭 Reasoning:                                   │
│ • Long gap since last interaction               │
│ • Account shows high engagement historically    │
│ • Similar accounts at this stage need attention │
│                                                 │
│ ┌──────────────┐  ┌──────────────┐             │
│ │   Approve    │  │    Reject    │             │
│ └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────┘
```

### Priority Levels

| Priority | Color | When to Act | Example |
|----------|-------|-------------|---------|
| **HIGH** | 🔴 Red | Within 1-3 days | Follow-ups, urgent updates |
| **MEDIUM** | 🟡 Yellow | Within 1 week | Status changes, tasks |
| **LOW** | 🟢 Green | Within 2 weeks | Campaign additions, notes |

### Confidence Scores

Confidence indicates how certain the AI is about the recommendation:

- **90-100%**: Very confident (based on strong patterns)
- **75-89%**: Confident (good historical match)
- **60-74%**: Moderate (some uncertainty)
- **<60%**: Low confidence (review carefully)

💡 **Tip:** You can safely approve recommendations with 80%+ confidence in most cases.

---

## Approval Workflow

### Why Approval is Required

Sergas follows a **human-in-the-loop** approach for safety:

- All CRM updates require your explicit approval
- You can modify recommendations before approving
- Rejected recommendations are logged for learning

### Approving Recommendations

**Option 1: Approve All**

```
┌─────────────────────────────────────┐
│ ✅ 3 recommendations ready          │
│                                     │
│ [ Approve All ]  [ Review Each ]   │
└─────────────────────────────────────┘
```

**Option 2: Review Each**

Step through recommendations one by one:

```
┌─────────────────────────────────────┐
│ Recommendation 1 of 3               │
│                                     │
│ [Content shown above]               │
│                                     │
│ ✓ Approve  ✗ Reject  ✏️ Modify     │
│                                     │
│ [←  Previous]      [Next  →]       │
└─────────────────────────────────────┘
```

### Modifying Recommendations

Click **✏️ Modify** to edit before approval:

```
┌─────────────────────────────────────┐
│ Modify Recommendation               │
│                                     │
│ Action:                             │
│ ┌─────────────────────────────────┐ │
│ │ Update Account Status           │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Field:                              │
│ ┌─────────────────────────────────┐ │
│ │ Account_Status                  │ │
│ └─────────────────────────────────┘ │
│                                     │
│ New Value:                          │
│ ┌─────────────────────────────────┐ │
│ │ Warm Lead ▼                     │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Reason for change:                  │
│ ┌─────────────────────────────────┐ │
│ │ Changed to Warm instead of Hot  │ │
│ └─────────────────────────────────┘ │
│                                     │
│    [Cancel]    [Save & Approve]     │
└─────────────────────────────────────┘
```

### Rejecting Recommendations

When you reject a recommendation, provide feedback:

```
┌─────────────────────────────────────┐
│ Why are you rejecting this?         │
│                                     │
│ ○ Not relevant                      │
│ ○ Incorrect information             │
│ ○ Already handled manually          │
│ ● Need more context                 │
│ ○ Other (please specify)            │
│                                     │
│ Additional notes:                   │
│ ┌─────────────────────────────────┐ │
│ │ Need to verify with account     │ │
│ │ owner before making changes     │ │
│ └─────────────────────────────────┘ │
│                                     │
│    [Cancel]        [Submit]         │
└─────────────────────────────────────┘
```

---

## Viewing Tool Calls

### What are Tool Calls?

Tool calls show you exactly what the AI is doing behind the scenes. This transparency helps you:

- Understand how recommendations were generated
- Verify data sources
- Trust the AI's reasoning

### Tool Call Display

During analysis, you'll see expandable tool call cards:

```
┌─────────────────────────────────────────────────┐
│ 🔧 Tool Call: zoho_get_account                  │
│ Status: ✓ Completed in 1.2s                     │
├─────────────────────────────────────────────────┤
│ ▼ Show Details                                  │
│                                                 │
│ Input:                                          │
│ {                                               │
│   "account_id": "ACC-001"                       │
│ }                                               │
│                                                 │
│ Output:                                         │
│ {                                               │
│   "name": "Acme Corporation",                   │
│   "status": "Active",                           │
│   "owner": "Jane Doe",                          │
│   "health_score": 78,                           │
│   "last_contact": "2025-09-04T10:30:00Z"        │
│ }                                               │
└─────────────────────────────────────────────────┘
```

### Common Tools

| Tool Name | Purpose | Example Use |
|-----------|---------|-------------|
| `zoho_get_account` | Retrieve account details | Get current status, owner, etc. |
| `zoho_search_contacts` | Find related contacts | Identify key stakeholders |
| `cognee_search` | Query historical data | Find past interactions |
| `zoho_update_account` | Update CRM fields | Change status, add notes |
| `zoho_create_task` | Create follow-up tasks | Schedule calls, emails |

---

## Dashboard Features

### Overview Dashboard

Your main dashboard shows:

```
┌────────────────────────────────────────────────┐
│  📊 My Accounts Overview                       │
├────────────────────────────────────────────────┤
│                                                │
│  Total Accounts: 127                           │
│  Avg Health Score: 74/100                      │
│  Pending Actions: 12                           │
│  Last Analyzed: 2 hours ago                    │
│                                                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                │
│  🔴 High Priority (3)                          │
│  • ACC-001: Follow-up overdue                  │
│  • ACC-045: Payment issue detected             │
│  • ACC-089: Engagement drop-off                │
│                                                │
│  🟡 Medium Priority (5)                        │
│  🟢 Low Priority (4)                           │
│                                                │
│  [Analyze All]  [View Details]                 │
└────────────────────────────────────────────────┘
```

### Account Health Trends

View health score trends over time:

```
Account Health Trend (90 days)

100 ┤                            ╭─────
 90 ┤                     ╭──────╯
 80 ┤            ╭────────╯
 70 ┤     ╭──────╯
 60 ┤─────╯
    └─┬────┬────┬────┬────┬────┬────┬──
     Jul  Aug  Sep  Oct  Nov  Dec  Jan

📈 +15 points since last quarter
```

### Activity Feed

See recent AI actions and approvals:

```
┌────────────────────────────────────────────────┐
│  📜 Recent Activity                            │
├────────────────────────────────────────────────┤
│                                                │
│  ✓ 10:30 AM - Approved status update (ACC-001)│
│  ✗ 10:25 AM - Rejected task creation (ACC-002)│
│  ✓ 10:15 AM - Approved 3 recommendations       │
│  🔄 10:00 AM - Analysis completed (5 accounts) │
│  ✓ 09:45 AM - Approved campaign add (ACC-012)  │
│                                                │
│  [View All Activity]                           │
└────────────────────────────────────────────────┘
```

---

## Tips and Best Practices

### ✅ Do's

1. **Review High-Confidence Recommendations First**
   - Start with 90%+ confidence scores
   - These are safest to approve quickly

2. **Provide Feedback on Rejections**
   - Helps the AI learn your preferences
   - Improves future recommendations

3. **Use Batch Analysis for Efficiency**
   - Analyze multiple accounts at once
   - Review all recommendations together

4. **Check Tool Calls for Transparency**
   - Verify data sources
   - Understand AI reasoning

5. **Set Up Regular Analysis Schedules**
   - Daily for high-priority accounts
   - Weekly for standard accounts

### ❌ Don'ts

1. **Don't Auto-Approve Everything**
   - Always review recommendations
   - Check for context accuracy

2. **Don't Ignore Low-Confidence Recommendations**
   - May contain valuable insights
   - Review carefully before rejecting

3. **Don't Skip Providing Rejection Reasons**
   - Feedback improves AI performance
   - Helps team understand patterns

4. **Don't Modify Without Understanding**
   - Read full recommendation details
   - Check supporting evidence

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `/` | Focus search bar |
| `A` | Approve current recommendation |
| `R` | Reject current recommendation |
| `→` | Next recommendation |
| `←` | Previous recommendation |
| `Esc` | Close modal/dialog |
| `?` | Show all shortcuts |

### Common Workflows

**Morning Account Review (5 minutes):**

1. Open dashboard
2. Click "Analyze All"
3. Review high-priority recommendations
4. Approve/modify/reject each
5. Check activity feed for updates

**End-of-Week Cleanup (15 minutes):**

1. Filter by "Low Priority"
2. Batch review all recommendations
3. Approve standard updates
4. Reject non-applicable items
5. Export weekly report

---

## Getting Help

### In-App Support

- Click **?** icon in top-right corner
- Access help articles and videos
- Start live chat with support

### Reporting Issues

If something doesn't work correctly:

1. Click **Report Issue** in the help menu
2. Describe what happened
3. Include screenshot if possible
4. Submit report

### Training Resources

- **Video Tutorials**: `https://training.sergas.com/videos`
- **Interactive Guide**: Click "Take Tour" on first login
- **Knowledge Base**: `https://docs.sergas.com`

---

**Questions?** Contact support@sergas.com or use the in-app chat!
