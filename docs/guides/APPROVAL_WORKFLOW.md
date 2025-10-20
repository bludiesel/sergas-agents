# Approval Workflow Guide

**Version:** 1.0.0
**Last Updated:** 2025-10-19
**Target Audience:** All Users

---

## Table of Contents

1. [What is Approval Workflow](#what-is-approval-workflow)
2. [When Approvals are Required](#when-approvals-are-required)
3. [Approval Process](#approval-process)
4. [How to Approve via CLI](#how-to-approve-via-cli)
5. [How to Approve via Web UI](#how-to-approve-via-web-ui)
6. [What Happens After Approval](#what-happens-after-approval)
7. [Best Practices](#best-practices)

---

## What is Approval Workflow

The approval workflow is a **human-in-the-loop** safety mechanism that ensures all CRM modifications are reviewed and explicitly approved by a human before being applied.

### Why We Use Approval Workflow

- **Safety**: Prevents accidental or incorrect CRM updates
- **Control**: Gives you final say over all changes
- **Transparency**: Shows exactly what will be modified
- **Compliance**: Maintains audit trail for all changes
- **Learning**: Allows AI to learn from your feedback

### Core Principles

1. **No Automatic Updates**: The AI never modifies your CRM without permission
2. **Full Transparency**: You see exactly what will change and why
3. **Modification Rights**: You can edit recommendations before approving
4. **Feedback Loop**: Rejections help the AI learn your preferences

---

## When Approvals are Required

### Always Requires Approval

| Operation | Example | Risk Level |
|-----------|---------|------------|
| **Status Updates** | Changing account status from "Active" to "Hot Lead" | High |
| **Data Modifications** | Updating contact information, notes, or fields | High |
| **Task Creation** | Creating follow-up tasks or calendar events | Medium |
| **Campaign Actions** | Adding accounts to marketing campaigns | Medium |
| **Contact Changes** | Modifying or creating contact records | High |

### Never Requires Approval (Read-Only)

| Operation | Example | Risk Level |
|-----------|---------|------------|
| **Data Retrieval** | Reading account details from Zoho CRM | None |
| **Search Operations** | Querying historical context from Cognee | None |
| **Analysis** | Generating recommendations and insights | None |
| **Metrics Collection** | Recording session statistics | None |

---

## Approval Process

### Step-by-Step Flow

```
┌─────────────────────────────────────────────────┐
│ 1. AI Analysis                                  │
│    • Analyzes account data                      │
│    • Identifies opportunities                   │
│    • Generates recommendations                  │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ 2. Recommendation Presentation                  │
│    • Shows proposed changes                     │
│    • Displays confidence scores                 │
│    • Provides reasoning and evidence            │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ 3. Human Review                                 │
│    • You review each recommendation             │
│    • Check accuracy and relevance               │
│    • Decide: Approve, Modify, or Reject         │
└────────────┬────────────────────────────────────┘
             │
       ┌─────┴─────┐
       │           │
       ▼           ▼
┌───────────┐  ┌──────────┐
│ Approved  │  │ Rejected │
└─────┬─────┘  └──────┬───┘
      │               │
      ▼               ▼
┌─────────────┐  ┌──────────────┐
│ 4. Execute  │  │ 4. Log       │
│    Changes  │  │    Feedback  │
└─────────────┘  └──────────────┘
```

### Timeout Handling

**Default Timeout**: 5 minutes (300 seconds)

What happens when timeout is reached:

- **Web UI**: Warning message appears → "Your session will expire in 1 minute"
- **CLI**: Automatic rejection after timeout
- **Backend**: Approval request is cancelled
- **Audit Log**: Timeout event is recorded

You can extend the timeout:
```bash
# CLI
sergas analyze ACC-001 --approval-timeout 600  # 10 minutes

# Config file
approval:
  timeout_seconds: 600
```

---

## How to Approve via CLI

### Interactive Approval (Default)

```bash
$ sergas analyze ACC-001

🔍 Analyzing account ACC-001...

✓ Analysis complete!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOMMENDATIONS (3):

1. [HIGH] Update Account Status
   Current: Active → Proposed: Hot Lead
   Confidence: 85%
   Reason: Recent engagement spike detected

2. [MEDIUM] Create Follow-up Task
   Task: Schedule check-in call
   Due: 2025-10-22
   Confidence: 78%

3. [LOW] Add to Campaign
   Campaign: Q4 Upsell Campaign
   Confidence: 72%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔒 Approve recommendations to update CRM?

  [A] Approve All
  [R] Review Each
  [X] Reject All

Your choice:
```

### Approve All

```bash
Your choice: A

✓ Approving all recommendations...

✓ Updated account status (ACC-001)
✓ Created follow-up task
✓ Added to Q4 Upsell Campaign

3 of 3 recommendations applied successfully!
```

### Review Each Recommendation

```bash
Your choice: R

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Recommendation 1 of 3

Update Account Status
Current: Active → Proposed: Hot Lead
Confidence: 85%

Reasoning:
• 3 email opens in past 7 days
• Attended webinar on 2025-10-15
• Similar accounts converted at this stage

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [Y] Approve
  [N] Reject
  [M] Modify
  [S] Skip (decide later)

Your choice: Y

✓ Recommendation 1 approved

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Recommendation 2 of 3
...
```

### Modify Before Approving

```bash
Your choice: M

Current value: Hot Lead
Enter new value (or press Enter to keep): Warm Lead

Reason for modification (optional):
> Account owner prefers Warm Lead for now

✓ Recommendation modified and approved
```

### Auto-Approve Mode (Use with Caution!)

```bash
# Approve automatically without prompts
$ sergas analyze ACC-001 --auto-approve

⚠️  Auto-approve mode enabled!
✓ Analysis complete
✓ All 3 recommendations applied automatically
```

**Warning**: Auto-approve bypasses human review. Only use for:
- Trusted, high-confidence recommendations (90%+)
- Batch processing reviewed accounts
- Testing and development environments

---

## How to Approve via Web UI

### Visual Approval Interface

**Step 1:** After analysis completes, you'll see the approval modal:

```
┌─────────────────────────────────────────────────────┐
│  ⏳ Approval Required                               │
│                                                     │
│  The AI has generated 3 recommendations.            │
│  Please review and approve or reject each one.      │
│                                                     │
│  Time remaining: 4:32                               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │ 🔴 HIGH PRIORITY • Confidence: 85%            │ │
│  ├───────────────────────────────────────────────┤ │
│  │ Update Account Status                         │ │
│  │                                               │ │
│  │ Current: Active                               │ │
│  │ Proposed: Hot Lead                            │ │
│  │                                               │ │
│  │ 💭 Reasoning:                                 │ │
│  │ Recent engagement spike detected with 3       │ │
│  │ email opens and webinar attendance.           │ │
│  │                                               │ │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐      │ │
│  │ │ Approve  │ │  Modify  │ │  Reject  │      │ │
│  │ └──────────┘ └──────────┘ └──────────┘      │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  [ ← Previous ]  [ 1 of 3 ]  [ Next → ]           │
│                                                     │
│  ┌───────────────────────┐  ┌──────────────────┐  │
│  │  Approve All (3)      │  │  Reject All      │  │
│  └───────────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**Step 2:** Click button to approve/modify/reject each recommendation

**Step 3:** When all reviewed, click **"Submit Decisions"**

### Modify Recommendation

Click **Modify** to edit:

```
┌─────────────────────────────────────────────────┐
│  Modify Recommendation                          │
├─────────────────────────────────────────────────┤
│                                                 │
│  Action: Update Account Status                  │
│                                                 │
│  Current Value:                                 │
│  ┌─────────────────────────────────┐           │
│  │ Active                          │           │
│  └─────────────────────────────────┘           │
│                                                 │
│  New Value:                                     │
│  ┌─────────────────────────────────┐           │
│  │ Warm Lead         ▼             │           │
│  └─────────────────────────────────┘           │
│                                                 │
│  Reason for change (optional):                  │
│  ┌─────────────────────────────────────────┐   │
│  │ Account owner prefers Warm Lead for     │   │
│  │ initial outreach phase                  │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  ┌────────────┐        ┌────────────────┐      │
│  │  Cancel    │        │ Save & Approve │      │
│  └────────────┘        └────────────────┘      │
└─────────────────────────────────────────────────┘
```

### Batch Approval

For multiple accounts:

```
┌─────────────────────────────────────────────────┐
│  Batch Approval (5 accounts)                    │
├─────────────────────────────────────────────────┤
│                                                 │
│  ✓ ACC-001: 3 recommendations (all approved)    │
│  ⏳ ACC-002: 2 recommendations (pending)        │
│  ○ ACC-003: Not yet reviewed                    │
│  ○ ACC-004: Not yet reviewed                    │
│  ○ ACC-005: Not yet reviewed                    │
│                                                 │
│  Progress: 1 of 5 complete                      │
│                                                 │
│  [ Continue to Next Account → ]                 │
└─────────────────────────────────────────────────┘
```

---

## What Happens After Approval

### Immediate Actions

1. **CRM Update** (if approved)
   - Changes are applied to Zoho CRM
   - Update confirmation is displayed
   - Success/failure status is shown

2. **Audit Log Entry**
   - Timestamp of decision
   - User who approved/rejected
   - Original recommendation
   - Any modifications made
   - Reason for rejection (if provided)

3. **AI Learning** (if rejected)
   - Feedback is stored
   - Patterns are analyzed
   - Future recommendations are adjusted

### Verification

After approval, you can verify changes:

**CLI:**
```bash
# View last session details
$ sergas history show --last

Session: session-abc-123
Status: ✓ Complete
Recommendations: 3 approved, 0 rejected
CRM Updates: 3 successful

Details:
✓ Updated ACC-001: Account_Status → Hot Lead
✓ Created task: Schedule check-in call (due 2025-10-22)
✓ Added ACC-001 to Q4 Upsell Campaign
```

**Web UI:**
Activity feed shows:
```
✓ 10:30 AM - Approved status update (ACC-001)
   Changed: Account_Status → Hot Lead
   [View in CRM] [Undo]
```

### Rollback (if needed)

If you need to undo an approved change:

**CLI:**
```bash
# Undo last approved change
$ sergas undo --session session-abc-123 --recommendation 1

⚠️  This will revert: Account_Status (Hot Lead → Active)
Confirm undo? [y/N]: y

✓ Change reverted successfully
```

**Web UI:**
Click **[Undo]** in activity feed

---

## Best Practices

### ✅ Do's

1. **Review High-Impact Changes Carefully**
   - Status updates
   - Contact information
   - Campaign additions

2. **Provide Rejection Feedback**
   - Helps AI learn
   - Improves future recommendations
   - Documents decision rationale

3. **Use Modification Feature**
   - Adjust values while preserving intent
   - Maintain approval workflow benefits

4. **Check Confidence Scores**
   - 90%+: Safe to approve quickly
   - 75-89%: Review carefully
   - <75%: Verify thoroughly

5. **Verify After Approval**
   - Check CRM to confirm changes
   - Review activity log
   - Ensure expected outcome

### ❌ Don'ts

1. **Don't Auto-Approve Everything**
   - Review each recommendation
   - Understand the reasoning
   - Verify accuracy

2. **Don't Ignore Low-Confidence Recommendations**
   - May be valuable but uncertain
   - Provide feedback if rejecting
   - Help AI learn edge cases

3. **Don't Approve Without Understanding**
   - Read full recommendation
   - Check supporting evidence
   - Verify tool call data

4. **Don't Skip Timeout Extensions**
   - If you need more time, extend
   - Better than rushed decisions

### Security Considerations

1. **Never Share Approval Credentials**
   - Each user has unique access
   - Approvals are tied to your identity
   - Audit trail tracks your decisions

2. **Review Before Approval**
   - Even with high confidence scores
   - Verify data accuracy
   - Check for PII/sensitive data

3. **Use Strong Authentication**
   - Enable 2FA if available
   - Don't share sessions
   - Log out when done

---

## Troubleshooting

### Approval Not Responding

**Symptom:** Click approve but nothing happens

**Solutions:**
1. Check your internet connection
2. Refresh the page
3. Check browser console for errors
4. Try CLI if web UI fails

### Timeout Expired

**Symptom:** "Approval timeout expired"

**Solutions:**
```bash
# Increase timeout globally
$ sergas config set approval.timeout_seconds 900  # 15 minutes

# Or per-command
$ sergas analyze ACC-001 --approval-timeout 900
```

### Changes Not Applied to CRM

**Symptom:** Approved but CRM not updated

**Solutions:**
1. Check activity log for error details
2. Verify Zoho CRM connection: `sergas test-connection`
3. Check permissions: `sergas zoho verify-permissions`
4. Retry: `sergas retry --session <session-id>`

### Can't Find Approval Request

**Symptom:** Approval modal not showing

**Solutions:**
1. Check if analysis is still running
2. Look for errors in analysis output
3. Verify account ID is correct
4. Check logs: `sergas logs --level error`

---

## FAQ

**Q: Can I approve changes in bulk?**
A: Yes, use "Approve All" button or `--auto-approve` flag (with caution)

**Q: What if I approve by mistake?**
A: Use the undo feature or manually revert in CRM

**Q: Can I delegate approval to someone else?**
A: Not currently - approvals are tied to your session

**Q: How long are approval decisions stored?**
A: Indefinitely for audit/compliance purposes

**Q: Can the AI learn from my approvals?**
A: Yes, especially from rejections with feedback

**Q: What happens if I don't respond?**
A: Request times out and is rejected automatically

---

**Need Help?** Contact support@sergas.com or check the [Web UI Guide](WEB_UI_USER_GUIDE.md)
