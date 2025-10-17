# Agent Specifications - Sergas Super Account Manager

## 1. Overview

This document provides detailed implementation specifications for all agents in the Sergas Super Account Manager system, including configuration, tool permissions, system prompts, hooks, and interaction patterns.

---

## 2. Main Orchestrator Agent

### 2.1 Core Configuration

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, MCPServer

orchestrator_options = ClaudeAgentOptions(
    # Model Configuration
    model="claude-sonnet-4-5",
    max_tokens=8192,
    temperature=0.7,

    # System Prompt
    system_prompt="""You are the Sergas Account Manager Orchestrator.

Your mission: Coordinate specialized subagents to analyze account portfolios,
synthesize insights, and generate actionable recommendations for account executives.

## Core Responsibilities
1. Schedule and trigger account review cycles (daily/weekly/on-demand)
2. Coordinate parallel subagent execution via query() API
3. Aggregate subagent outputs into owner-specific briefs
4. Manage human approval workflows for CRM modifications
5. Execute approved actions and log outcomes
6. Maintain session state and audit trails

## Workflow Pattern
For each review cycle:
1. Load account-owner assignments from config
2. Spawn subagents in parallel for each owner segment:
   - Zoho Data Scout: Fetch account data and detect changes
   - Memory Analyst: Query historical context from Cognee
   - Recommendation Author: Synthesize insights into actions
3. Compile results into owner briefs with priority ranking
4. Present recommendations for human approval
5. Execute approved actions (task creation, notes, etc.)
6. Store decisions and outcomes in Cognee for future context

## Safety & Security Rules
- **Never modify CRM data without explicit human approval**
- Always provide data source references for recommendations
- Prioritize high-risk accounts (stalled deals, inactivity, churn signals)
- Redact sensitive fields (SSN, financials, personal data) in all outputs
- Log every tool invocation, recommendation, and decision with timestamps
- Fail gracefully when Zoho or Cognee unavailable (retry + fallback)

## Output Format
Generate owner briefs in this structure:
```json
{
  "owner_email": "john.doe@sergas.com",
  "generated_at": "2025-10-18T06:00:00Z",
  "review_period": "2025-10-11 to 2025-10-18",
  "accounts_reviewed": 23,
  "high_priority_accounts": [
    {"account_id": "123", "account_name": "Acme Corp", "risk_level": "high"}
  ],
  "summary": "3 accounts require immediate attention due to inactivity...",
  "recommendations": [...],
  "metrics": {
    "accounts_with_changes": 8,
    "stalled_deals": 2,
    "overdue_follow_ups": 5
  }
}
```

## Error Handling
- If Zoho API fails: Retry 3x with exponential backoff, then skip account
- If Cognee unavailable: Proceed without historical context, flag degraded mode
- If subagent times out: Log error, continue with remaining subagents
- Never let failures block entire review cycle
""",

    # Tool Permissions
    allowed_tools=[
        # Session Management
        "create_session",
        "fork_session",
        "resume_session",

        # File System (for config and logging)
        "Read",
        "Write",  # Requires approval via permission_mode
        "Glob",

        # Task Management
        "TodoWrite",

        # Bash (limited for system operations)
        "Bash"
    ],

    disallowed_tools=[
        # No direct CRM access (delegates to subagents)
        "*zoho*",

        # No memory access (delegates to subagents)
        "*cognee*",

        # No web access
        "WebFetch",
        "WebSearch"
    ],

    # Permission Mode
    permission_mode="acceptEdits",  # Require approval for file writes

    # Settings
    setting_sources=["project"],  # Load .claude/CLAUDE.md

    # MCP Servers (for subagents to use)
    mcp_servers=[
        MCPServer(
            name="zoho-crm",
            protocol="remote",
            endpoint=os.environ["ZOHO_MCP_ENDPOINT"],
            config={
                "oauth_token_source": "secrets_manager",
                "secret_id": "sergas/zoho-crm/oauth-token",
                "rate_limit_rpm": 120
            }
        ),
        MCPServer(
            name="cognee",
            protocol="stdio",
            command=["npx", "cognee-mcp"],
            env={
                "COGNEE_API_URL": os.environ["COGNEE_API_URL"],
                "COGNEE_API_KEY": os.environ["COGNEE_API_KEY"]
            }
        )
    ],

    # Hooks
    hooks={
        "pre_tool": pre_tool_hook,
        "post_tool": post_tool_hook,
        "pre_prompt": pre_prompt_hook,
        "post_compaction": post_compaction_hook,
        "session_end": session_end_hook
    }
)
```

---

### 2.2 Hook Implementations

```python
import structlog
import time
from datetime import datetime

logger = structlog.get_logger()
audit_logger = AuditLogger()  # Custom audit logger

async def pre_tool_hook(tool_name: str, tool_input: dict, context: dict):
    """Log tool invocations before execution"""
    session_id = context.get("session_id")
    account_id = tool_input.get("account_id")

    logger.info(
        "tool_invocation_start",
        session_id=session_id,
        tool_name=tool_name,
        tool_input=tool_input,
        account_id=account_id,
        timestamp=datetime.utcnow().isoformat()
    )

    audit_logger.log_tool_invocation(
        session_id=session_id,
        agent_name="orchestrator",
        tool_name=tool_name,
        tool_inputs=tool_input
    )

    context["tool_start_time"] = time.time()


async def post_tool_hook(tool_name: str, tool_output: dict, context: dict):
    """Log tool results and execution time"""
    session_id = context.get("session_id")
    start_time = context.get("tool_start_time", time.time())
    execution_time_ms = int((time.time() - start_time) * 1000)

    logger.info(
        "tool_invocation_complete",
        session_id=session_id,
        tool_name=tool_name,
        execution_time_ms=execution_time_ms,
        success=tool_output.get("success", True),
        timestamp=datetime.utcnow().isoformat()
    )

    audit_logger.log_tool_result(
        session_id=session_id,
        agent_name="orchestrator",
        tool_name=tool_name,
        tool_outputs=tool_output,
        execution_time_ms=execution_time_ms
    )

    # Track Zoho API usage for rate limiting
    if "zoho" in tool_name:
        rate_limiter.record_request(tool_name, execution_time_ms)


async def pre_prompt_hook(prompt: str, context: dict):
    """Log prompt submissions"""
    session_id = context.get("session_id")

    logger.info(
        "prompt_submitted",
        session_id=session_id,
        prompt_length=len(prompt),
        timestamp=datetime.utcnow().isoformat()
    )


async def post_compaction_hook(messages_before: int, messages_after: int, context: dict):
    """Log context compaction events"""
    session_id = context.get("session_id")

    logger.info(
        "context_compacted",
        session_id=session_id,
        messages_before=messages_before,
        messages_after=messages_after,
        compression_ratio=messages_after / messages_before,
        timestamp=datetime.utcnow().isoformat()
    )


async def session_end_hook(session_id: str, metrics: dict):
    """Export session audit trail and metrics"""
    logger.info(
        "session_ended",
        session_id=session_id,
        metrics=metrics,
        timestamp=datetime.utcnow().isoformat()
    )

    # Export audit trail to PostgreSQL
    audit_logger.finalize_session(session_id, metrics)

    # Store session outcomes in Cognee for future reference
    cognee_client.store_session_summary(
        session_id=session_id,
        summary=metrics.get("summary"),
        recommendations_count=metrics.get("recommendations_count"),
        approvals_count=metrics.get("approvals_count")
    )
```

---

### 2.3 Subagent Spawning Pattern

```python
from claude_agent_sdk import query

async def process_owner_accounts(owner_email: str, account_ids: list[str]):
    """Spawn subagents in parallel to analyze accounts"""

    # Spawn Zoho Data Scout
    zoho_scout_task = query(
        messages=[{
            "role": "user",
            "content": f"""Fetch account data for the following accounts:
{json.dumps(account_ids, indent=2)}

For each account, detect changes since last sync and aggregate:
- Account details (name, owner, status, last_modified)
- Open deals with stages and amounts
- Recent activities (calls, meetings, emails)
- Notes from the last 30 days
- Risk signals (inactivity, stalled deals, overdue tasks)

Return structured JSON output."""
        }],
        options=zoho_scout_options  # Defined below
    )

    # Spawn Memory Analyst
    memory_analyst_task = query(
        messages=[{
            "role": "user",
            "content": f"""Retrieve historical context for these accounts:
{json.dumps(account_ids, indent=2)}

Query Cognee memory for:
- Key events from the last 90 days
- Sentiment trends and relationship strength
- Prior recommendations and their outcomes
- Commitment tracking and renewal timelines
- Executive sponsor changes

Return structured JSON output."""
        }],
        options=memory_analyst_options
    )

    # Execute subagents in parallel
    zoho_data, memory_insights = await asyncio.gather(
        zoho_scout_task,
        memory_analyst_task
    )

    # Spawn Recommendation Author (depends on above outputs)
    recommendation_task = query(
        messages=[{
            "role": "user",
            "content": f"""Synthesize account data and historical context
into actionable recommendations.

Account Data:
{json.dumps(zoho_data, indent=2)}

Historical Context:
{json.dumps(memory_insights, indent=2)}

Generate recommendations with:
- Type (follow_up_email, task_creation, escalation)
- Priority (low/medium/high)
- Confidence (low/medium/high) with rationale
- Suggested action with draft content
- Data references for auditability

Return structured JSON output."""
        }],
        options=recommendation_author_options
    )

    recommendations = await recommendation_task

    # Compile owner brief
    owner_brief = {
        "owner_email": owner_email,
        "generated_at": datetime.utcnow().isoformat(),
        "accounts_reviewed": len(account_ids),
        "account_data": zoho_data,
        "historical_insights": memory_insights,
        "recommendations": recommendations
    }

    return owner_brief
```

---

## 3. Zoho Data Scout Subagent

### 3.1 Configuration

```python
zoho_scout_options = ClaudeAgentOptions(
    model="claude-sonnet-4-5",
    max_tokens=4096,
    temperature=0.3,  # Lower temperature for factual data retrieval

    system_prompt="""You are the Zoho Data Scout for Sergas Account Manager.

Your mission: Retrieve account data from Zoho CRM with change detection
and activity aggregation.

## Responsibilities
1. Fetch accounts by owner from Zoho CRM via MCP tools
2. Detect changes since last sync (field modifications, new activities)
3. Aggregate related records (deals, tasks, notes, activities)
4. Identify risk signals (inactivity thresholds, stalled deals)
5. Return structured data with change flags and metadata

## Available Tools
- zoho_get_accounts: List accounts by owner
- zoho_get_account_details: Fetch single account with full details
- zoho_search_accounts: Query accounts by criteria (last_modified, status)
- zoho_get_deals: List deals for an account
- zoho_list_open_deals: Filter open deals by stage
- zoho_get_activities: Fetch calls, meetings, emails for account
- zoho_get_notes: Retrieve notes from last N days

## Change Detection Strategy
1. Compare last_modified timestamps with last sync timestamp
2. Flag new activities added since last sync
3. Identify deal stage changes (forward or backward movement)
4. Detect inactivity (no activities in 30 days = high risk)
5. Check for overdue tasks or past-due follow-ups

## Risk Signals to Detect
- No activity in 30+ days (high risk)
- Deal stalled in same stage for 45+ days (medium risk)
- Executive sponsor changed (medium risk)
- Negative sentiment in recent notes (medium risk)
- Overdue renewal or contract expiration (high risk)

## Output Format
Return JSON array:
```json
[
  {
    "account_id": "123456789",
    "account_name": "Acme Corp",
    "owner": "john.doe@sergas.com",
    "last_modified": "2025-10-15T14:30:00Z",
    "changes_detected": true,
    "changes": [
      {
        "field": "Deal_Stage",
        "old": "Negotiation",
        "new": "Closed Won",
        "timestamp": "2025-10-15T10:00:00Z",
        "deal_id": "deal_001"
      }
    ],
    "open_deals": [
      {
        "deal_id": "deal_002",
        "deal_name": "Q4 Expansion",
        "stage": "Proposal",
        "amount": 75000,
        "close_date": "2025-12-15",
        "days_in_stage": 20
      }
    ],
    "recent_activities": [
      {
        "activity_type": "Call",
        "subject": "Q4 planning discussion",
        "date": "2025-10-12",
        "owner": "john.doe@sergas.com"
      }
    ],
    "notes_count": 15,
    "last_activity_date": "2025-10-12",
    "days_since_last_activity": 6,
    "risk_signals": []
  }
]
```

## Safety Rules
- **Never modify CRM data** (read-only access)
- If asked to update/create/delete: Respond "I can only read data"
- Always include data_source references (tool_name + record_id)
- Redact sensitive fields: SSN, Tax_ID, Credit_Card, Bank_Account
- If Zoho API fails, return error with retry suggestion
""",

    allowed_tools=[
        # Zoho CRM MCP Tools (Read-Only)
        "zoho_get_accounts",
        "zoho_get_account_details",
        "zoho_search_accounts",
        "zoho_get_deals",
        "zoho_list_open_deals",
        "zoho_get_activities",
        "zoho_get_notes",
        "zoho_get_user_info",

        # Utility Tools
        "Read"  # For loading last-sync timestamps
    ],

    disallowed_tools=[
        # No write operations
        "zoho_update_account",
        "zoho_create_task",
        "zoho_add_note",
        "zoho_delete_*",

        # No file writes
        "Write",
        "Edit",

        # No bash/web access
        "Bash",
        "WebFetch",
        "WebSearch"
    ],

    permission_mode="plan",  # Read-only, no approvals needed

    setting_sources=[],  # Isolated from project settings

    mcp_servers=[
        MCPServer(
            name="zoho-crm",
            protocol="remote",
            endpoint=os.environ["ZOHO_MCP_ENDPOINT"]
        )
    ],

    hooks={
        "pre_tool": zoho_scout_pre_tool_hook,
        "post_tool": zoho_scout_post_tool_hook
    }
)
```

---

### 3.2 Hook Implementations

```python
async def zoho_scout_pre_tool_hook(tool_name: str, tool_input: dict, context: dict):
    """Enforce rate limiting and log Zoho API calls"""
    if "zoho" in tool_name:
        # Check rate limit
        if not rate_limiter.can_request(tool_name):
            raise RateLimitExceeded(f"Zoho API rate limit exceeded for {tool_name}")

        logger.info(
            "zoho_api_call",
            tool_name=tool_name,
            account_id=tool_input.get("account_id"),
            owner=tool_input.get("owner"),
            timestamp=datetime.utcnow().isoformat()
        )


async def zoho_scout_post_tool_hook(tool_name: str, tool_output: dict, context: dict):
    """Cache Zoho API responses and track usage"""
    if "zoho" in tool_name and tool_output.get("success"):
        # Cache response for 15 minutes
        cache_key = f"{tool_name}:{hash(json.dumps(tool_input))}"
        redis_client.setex(cache_key, 900, json.dumps(tool_output))

        # Track API usage
        metrics.zoho_api_requests_total.labels(tool_name=tool_name).inc()
        metrics.zoho_api_latency_seconds.labels(tool_name=tool_name).observe(
            context.get("execution_time_ms", 0) / 1000
        )
```

---

## 4. Memory Analyst Subagent

### 4.1 Configuration

```python
memory_analyst_options = ClaudeAgentOptions(
    model="claude-sonnet-4-5",
    max_tokens=4096,
    temperature=0.5,  # Moderate temperature for pattern analysis

    system_prompt="""You are the Memory Analyst for Sergas Account Manager.

Your mission: Query Cognee memory layer for historical account context,
patterns, and insights to inform recommendations.

## Responsibilities
1. Search Cognee memory for historical account context
2. Identify patterns in past interactions, deals, and outcomes
3. Aggregate sentiment trends and commitment tracking
4. Surface relevant prior recommendations and their effectiveness
5. Map relationship graphs (contacts, deals, parent accounts)

## Available Tools
- cognee_search_memory: Semantic search for account context
- cognee_retrieve_history: Get temporal account events
- cognee_aggregate_insights: Pattern analysis over time periods
- cognee_get_relationship_graph: Fetch connected entities

## Analysis Focus Areas
1. **Key Events**: Executive changes, contract renewals, major wins/losses
2. **Sentiment Trends**: Analyze note tone over time (positive/negative shift)
3. **Engagement Patterns**: Activity frequency, response times, meeting cadence
4. **Commitment Tracking**: Promises made vs. kept, renewal intent signals
5. **Recommendation Effectiveness**: Prior suggestions and their outcomes
6. **Relationship Strength**: Contact stability, escalation history

## Output Format
Return JSON:
```json
{
  "account_id": "123456789",
  "account_name": "Acme Corp",
  "memory_query_timestamp": "2025-10-18T06:00:00Z",
  "historical_context": {
    "key_events": [
      {
        "date": "2025-09-01",
        "event": "Executive sponsor changed from Jane Smith to Bob Johnson",
        "impact": "Delayed Q3 renewal discussion by 3 weeks",
        "source": "cognee_memory_ref_456"
      }
    ],
    "sentiment_trend": {
      "current": "neutral",
      "90_day_trend": "declining",
      "analysis": "Sentiment shifted from positive to neutral after sponsor change"
    },
    "engagement_patterns": {
      "activity_frequency": "bi-weekly",
      "response_time_avg_days": 2.5,
      "last_executive_meeting": "2025-09-15",
      "days_since_exec_meeting": 33
    },
    "prior_recommendations": [
      {
        "date": "2025-08-15",
        "recommendation": "Schedule executive briefing on Q4 roadmap",
        "status": "completed",
        "outcome": "positive",
        "effectiveness_score": 0.85,
        "outcome_note": "Resulted in Q4 expansion deal"
      }
    ],
    "relationship_strength": {
      "score": "strong",
      "factors": [
        "5+ year customer",
        "Multiple successful renewals",
        "Executive sponsor engaged"
      ],
      "risk_factors": [
        "Recent sponsor change",
        "Reduced meeting frequency"
      ]
    },
    "commitment_tracking": [
      "Q4 renewal intent confirmed (2025-08-20)",
      "Budget approved for expansion (2025-09-10)",
      "Technical evaluation pending (overdue)"
    ]
  },
  "data_references": [
    "cognee_memory_ref_456",
    "cognee_memory_ref_789"
  ]
}
```

## Safety Rules
- Query memory read-only (no writes from this agent)
- If memory is stale (>7 days old), flag for re-ingestion
- If no historical data found, return empty context (don't fabricate)
- Always include data_references for audit trail
""",

    allowed_tools=[
        # Cognee MCP Tools (Read-Only)
        "cognee_search_memory",
        "cognee_retrieve_history",
        "cognee_aggregate_insights",
        "cognee_get_relationship_graph",

        # Utility Tools
        "Read"  # For loading analysis templates
    ],

    disallowed_tools=[
        # No memory writes
        "cognee_store_context",
        "cognee_update_*",
        "cognee_delete_*",

        # No file writes
        "Write",
        "Edit",

        # No CRM/bash/web access
        "zoho_*",
        "Bash",
        "WebFetch",
        "WebSearch"
    ],

    permission_mode="default",  # Read-only

    setting_sources=[],  # Isolated

    mcp_servers=[
        MCPServer(
            name="cognee",
            protocol="stdio",
            command=["npx", "cognee-mcp"]
        )
    ],

    hooks={
        "post_tool": memory_analyst_post_tool_hook
    }
)
```

---

### 4.2 Hook Implementations

```python
async def memory_analyst_post_tool_hook(tool_name: str, tool_output: dict, context: dict):
    """Track memory staleness and cache results"""
    if "cognee" in tool_name and tool_output.get("success"):
        # Check memory freshness
        last_ingestion = tool_output.get("metadata", {}).get("last_ingestion")
        if last_ingestion:
            days_stale = (datetime.utcnow() - datetime.fromisoformat(last_ingestion)).days
            if days_stale > 7:
                logger.warning(
                    "stale_memory_detected",
                    account_id=tool_output.get("account_id"),
                    days_stale=days_stale,
                    recommendation="Re-ingest account data"
                )

        # Track Cognee query performance
        metrics.cognee_queries_total.inc()
        metrics.cognee_latency_seconds.observe(
            context.get("execution_time_ms", 0) / 1000
        )
```

---

## 5. Recommendation Author Subagent

### 5.1 Configuration

```python
recommendation_author_options = ClaudeAgentOptions(
    model="claude-sonnet-4-5",
    max_tokens=8192,  # Larger for detailed recommendations
    temperature=0.7,  # Higher temperature for creative suggestions

    system_prompt="""You are the Recommendation Author for Sergas Account Manager.

Your mission: Synthesize account data and historical context into actionable
recommendations with confidence scores and rationale.

## Responsibilities
1. Analyze account data (from Zoho Data Scout) and historical context (from Memory Analyst)
2. Generate prioritized, actionable recommendations
3. Assign confidence scores (low/medium/high) with supporting rationale
4. Draft follow-up email templates and task suggestions
5. Flag high-risk accounts for escalation
6. Provide data references for auditability

## Recommendation Types
1. **Follow-Up Email**: Draft email to re-engage contact
2. **Task Creation**: Suggest task with deadline and owner
3. **Escalation**: Flag for manager intervention
4. **Meeting Request**: Propose executive briefing or strategy session
5. **Deal Acceleration**: Suggest actions to move deal forward
6. **Renewal Reminder**: Proactive outreach for upcoming renewals

## Confidence Scoring
- **High**: Strong data signals, clear pattern, recent context
- **Medium**: Moderate signals, some uncertainty, older context
- **Low**: Weak signals, speculative, missing key data

## Priority Levels
- **Critical**: Immediate action required (churn risk, expired contract)
- **High**: Action within 5 days (stalled deal, overdue follow-up)
- **Medium**: Action within 2 weeks (routine check-in, opportunity)
- **Low**: Informational or future planning

## Output Format
Return JSON:
```json
{
  "account_id": "123456789",
  "account_name": "Acme Corp",
  "owner": "john.doe@sergas.com",
  "generated_at": "2025-10-18T06:00:00Z",
  "overall_risk_level": "medium",
  "recommendations": [
    {
      "recommendation_id": "rec_001",
      "type": "follow_up_email",
      "priority": "high",
      "confidence": "high",
      "rationale": "No activity in 35 days. Historical pattern shows engagement drops before churn. Executive sponsor change increases risk. Prior outreach was effective (0.85 score).",
      "suggested_action": {
        "subject": "Checking in on Q4 renewal timeline and technical evaluation",
        "draft_body": "Hi Bob,\\n\\nI wanted to follow up on our September conversation about Q4 renewal and the pending technical evaluation. I understand there was a leadership transition, and I'd love to ensure we're aligned on timeline and next steps.\\n\\nWould you have 30 minutes next week for a quick sync?\\n\\nBest,\\nJohn",
        "next_steps": [
          "Schedule call within 5 days",
          "Confirm budget status",
          "Get technical evaluation timeline"
        ],
        "deadline": "2025-10-23"
      },
      "data_references": [
        "zoho_account_123456789",
        "cognee_memory_ref_456",
        "zoho_activity_last_30_days"
      ]
    },
    {
      "recommendation_id": "rec_002",
      "type": "escalation",
      "priority": "high",
      "confidence": "medium",
      "rationale": "Deal stalled in Negotiation stage for 45 days. Historical pattern shows 60-day threshold before loss. Sentiment trend declining. Technical evaluation overdue.",
      "suggested_action": {
        "escalate_to": "sales_manager",
        "reason": "Potential deal risk requires manager intervention and executive alignment",
        "proposed_actions": [
          "Manager to join next customer call",
          "Propose executive sponsor briefing",
          "Consider pricing flexibility if needed"
        ]
      },
      "data_references": [
        "zoho_deal_002",
        "cognee_sentiment_trend",
        "zoho_deal_stage_history"
      ]
    }
  ],
  "summary": "Account requires immediate attention due to inactivity and stalled deal. Recommend re-engagement within 5 days and manager escalation for deal risk.",
  "metadata": {
    "recommendations_count": 2,
    "high_priority_count": 2,
    "data_sources_used": ["zoho_crm", "cognee_memory"]
  }
}
```

## Safety Rules
- Never recommend actions without supporting data references
- Assign confidence based on data recency and pattern strength
- If conflicting signals, note uncertainty and recommend validation
- Always draft email templates (never send automatically)
- For escalations, explain risk clearly with evidence
- Redact sensitive fields in draft communications
""",

    allowed_tools=[
        # Utility Tools
        "Read",  # For loading recommendation templates
        "Write"  # For drafting outputs (approval required)
    ],

    disallowed_tools=[
        # No CRM/memory access (works with inputs only)
        "zoho_*",
        "cognee_*",

        # No bash/web access
        "Bash",
        "WebFetch",
        "WebSearch"
    ],

    permission_mode="acceptEdits",  # Require approval for file writes

    setting_sources=[],  # Isolated

    mcp_servers=[],  # No MCP access (works with provided data)

    hooks={
        "post_tool": recommendation_author_post_tool_hook
    }
)
```

---

### 5.2 Hook Implementations

```python
async def recommendation_author_post_tool_hook(tool_name: str, tool_output: dict, context: dict):
    """Track recommendation generation and validate output"""
    if tool_name == "Write" and "recommendation" in tool_output.get("file_path", ""):
        # Validate recommendation structure
        try:
            recommendations = json.loads(tool_output.get("content", "{}"))
            validate_recommendation_schema(recommendations)

            # Track metrics
            rec_count = len(recommendations.get("recommendations", []))
            metrics.recommendations_generated_total.labels(
                type="all"
            ).inc(rec_count)

            logger.info(
                "recommendations_generated",
                account_id=recommendations.get("account_id"),
                count=rec_count,
                high_priority_count=recommendations.get("metadata", {}).get("high_priority_count", 0)
            )
        except Exception as e:
            logger.error(
                "invalid_recommendation_output",
                error=str(e),
                file_path=tool_output.get("file_path")
            )


def validate_recommendation_schema(data: dict):
    """Ensure recommendation output matches expected schema"""
    required_fields = ["account_id", "account_name", "owner", "recommendations"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    for rec in data.get("recommendations", []):
        rec_required = ["recommendation_id", "type", "priority", "confidence", "rationale", "suggested_action", "data_references"]
        for field in rec_required:
            if field not in rec:
                raise ValueError(f"Missing required field in recommendation: {field}")
```

---

## 6. Tool Allowlists Summary

### 6.1 Tool Permission Matrix

| Tool Name | Orchestrator | Zoho Scout | Memory Analyst | Recommendation Author |
|-----------|-------------|------------|----------------|----------------------|
| **Claude SDK Tools** ||||
| Read | ✅ | ✅ | ✅ | ✅ |
| Write | ✅ (approved) | ❌ | ❌ | ✅ (approved) |
| Edit | ❌ | ❌ | ❌ | ❌ |
| Glob | ✅ | ❌ | ❌ | ❌ |
| Bash | ✅ (limited) | ❌ | ❌ | ❌ |
| TodoWrite | ✅ | ❌ | ❌ | ❌ |
| WebFetch | ❌ | ❌ | ❌ | ❌ |
| WebSearch | ❌ | ❌ | ❌ | ❌ |
| **Zoho CRM MCP Tools** ||||
| zoho_get_accounts | ❌ | ✅ | ❌ | ❌ |
| zoho_get_account_details | ❌ | ✅ | ❌ | ❌ |
| zoho_search_accounts | ❌ | ✅ | ❌ | ❌ |
| zoho_get_deals | ❌ | ✅ | ❌ | ❌ |
| zoho_list_open_deals | ❌ | ✅ | ❌ | ❌ |
| zoho_get_activities | ❌ | ✅ | ❌ | ❌ |
| zoho_get_notes | ❌ | ✅ | ❌ | ❌ |
| zoho_update_account | ❌ | ❌ | ❌ | ❌ |
| zoho_create_task | ❌ | ❌ | ❌ | ❌ |
| zoho_add_note | ❌ | ❌ | ❌ | ❌ |
| **Cognee MCP Tools** ||||
| cognee_search_memory | ❌ | ❌ | ✅ | ❌ |
| cognee_retrieve_history | ❌ | ❌ | ✅ | ❌ |
| cognee_aggregate_insights | ❌ | ❌ | ✅ | ❌ |
| cognee_get_relationship_graph | ❌ | ❌ | ✅ | ❌ |
| cognee_store_context | ❌ | ❌ | ❌ | ❌ |
| **Session Management** ||||
| create_session | ✅ | ❌ | ❌ | ❌ |
| fork_session | ✅ | ❌ | ❌ | ❌ |
| resume_session | ✅ | ❌ | ❌ | ❌ |

**Legend:**
- ✅ Allowed
- ❌ Disallowed
- ✅ (approved) Allowed but requires human approval

---

## 7. Session Management Patterns

### 7.1 Orchestrator Session Lifecycle

```python
from claude_agent_sdk import ClaudeSDKClient

# Initialize orchestrator client
orchestrator = ClaudeSDKClient(orchestrator_options)

# Create session for review cycle
session = orchestrator.create_session(
    session_id=f"review_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
    metadata={
        "trigger": "scheduled",
        "schedule": "daily",
        "start_time": datetime.utcnow().isoformat()
    }
)

try:
    # Run review cycle
    results = await run_review_cycle(orchestrator, session)

    # Store session outcomes in Cognee
    cognee_client.store_context(
        namespace="session_history",
        key=session.session_id,
        value=json.dumps(results)
    )

except Exception as e:
    logger.error(f"Review cycle failed: {e}", session_id=session.session_id)
    # Session can be resumed later
    save_session_state(session)

finally:
    # Finalize session
    orchestrator.end_session(
        session_id=session.session_id,
        export_metrics=True
    )
```

---

### 7.2 Subagent Session Isolation

```python
async def spawn_isolated_subagent(agent_options: ClaudeAgentOptions, task: str):
    """Spawn subagent with isolated session context"""

    # Create subagent session (forked from orchestrator)
    subagent_session_id = f"{orchestrator_session_id}_subagent_{uuid.uuid4()}"

    result = await query(
        messages=[{
            "role": "user",
            "content": task
        }],
        options=agent_options,
        session_id=subagent_session_id,
        fork_session=True  # Isolated context
    )

    return result
```

---

## 8. Error Handling & Resilience

### 8.1 Retry Strategies

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry_error_callback=lambda retry_state: log_retry_failure(retry_state)
)
async def call_zoho_tool_with_retry(tool_name: str, tool_input: dict):
    """Call Zoho MCP tool with automatic retry"""
    try:
        result = await zoho_scout.use_tool(tool_name, tool_input)
        return result
    except ZohoAPIError as e:
        if e.status_code in [429, 503]:  # Rate limit or service unavailable
            logger.warning(f"Zoho API error {e.status_code}, retrying...")
            raise  # Trigger retry
        else:
            logger.error(f"Zoho API error {e.status_code}, not retrying")
            raise StopRetry()  # Don't retry client errors


def log_retry_failure(retry_state):
    """Log final failure after all retries exhausted"""
    logger.error(
        "zoho_api_retry_failed",
        tool_name=retry_state.args[0],
        attempt_number=retry_state.attempt_number,
        error=str(retry_state.outcome.exception())
    )
```

---

### 8.2 Graceful Degradation

```python
async def process_owner_accounts_with_fallback(owner_email: str, account_ids: list[str]):
    """Process accounts with graceful degradation if services unavailable"""

    # Try full workflow
    try:
        zoho_data = await fetch_zoho_data(account_ids)
    except ZohoUnavailable:
        logger.warning("Zoho CRM unavailable, using cached data")
        zoho_data = load_cached_zoho_data(account_ids)

    try:
        memory_insights = await fetch_cognee_insights(account_ids)
    except CogneeUnavailable:
        logger.warning("Cognee unavailable, proceeding without historical context")
        memory_insights = {"degraded_mode": True, "context": {}}

    # Generate recommendations (works with partial data)
    recommendations = await generate_recommendations(
        zoho_data=zoho_data,
        memory_insights=memory_insights
    )

    # Flag degraded mode in output
    if memory_insights.get("degraded_mode"):
        recommendations["metadata"]["degraded_mode"] = True
        recommendations["metadata"]["warning"] = "Historical context unavailable"

    return recommendations
```

---

## 9. Configuration Files

### 9.1 Agent Registry

**config/agents.yaml**
```yaml
agents:
  orchestrator:
    name: "Main Orchestrator"
    model: "claude-sonnet-4-5"
    max_tokens: 8192
    temperature: 0.7
    permission_mode: "acceptEdits"
    system_prompt_path: "config/prompts/orchestrator.md"

  zoho_scout:
    name: "Zoho Data Scout"
    model: "claude-sonnet-4-5"
    max_tokens: 4096
    temperature: 0.3
    permission_mode: "plan"
    system_prompt_path: "config/prompts/zoho_scout.md"

  memory_analyst:
    name: "Memory Analyst"
    model: "claude-sonnet-4-5"
    max_tokens: 4096
    temperature: 0.5
    permission_mode: "default"
    system_prompt_path: "config/prompts/memory_analyst.md"

  recommendation_author:
    name: "Recommendation Author"
    model: "claude-sonnet-4-5"
    max_tokens: 8192
    temperature: 0.7
    permission_mode: "acceptEdits"
    system_prompt_path: "config/prompts/recommendation_author.md"
```

---

### 9.2 Tool Configuration

**config/tools.yaml**
```yaml
tool_permissions:
  orchestrator:
    allowed:
      - Read
      - Write
      - Glob
      - Bash
      - TodoWrite
      - create_session
      - fork_session
      - resume_session
    disallowed:
      - "zoho_*"
      - "cognee_*"
      - WebFetch
      - WebSearch

  zoho_scout:
    allowed:
      - Read
      - zoho_get_accounts
      - zoho_get_account_details
      - zoho_search_accounts
      - zoho_get_deals
      - zoho_list_open_deals
      - zoho_get_activities
      - zoho_get_notes
      - zoho_get_user_info
    disallowed:
      - "zoho_*update*"
      - "zoho_*create*"
      - "zoho_*delete*"
      - Write
      - Edit
      - Bash

  memory_analyst:
    allowed:
      - Read
      - cognee_search_memory
      - cognee_retrieve_history
      - cognee_aggregate_insights
      - cognee_get_relationship_graph
    disallowed:
      - "cognee_store_*"
      - "cognee_update_*"
      - "cognee_delete_*"
      - Write
      - Edit
      - "zoho_*"

  recommendation_author:
    allowed:
      - Read
      - Write
    disallowed:
      - "zoho_*"
      - "cognee_*"
      - Bash
      - WebFetch
      - WebSearch
```

---

## 10. Next Steps

1. **Implement Orchestrator**: Build main orchestration logic with subagent spawning
2. **Configure Subagents**: Set up tool permissions and system prompts
3. **Integrate MCP Servers**: Connect Zoho CRM and Cognee MCP endpoints
4. **Build Hooks**: Implement audit logging and metrics tracking
5. **Test Isolation**: Validate subagent tool restrictions
6. **Pilot Run**: Execute with 10 accounts to validate workflow
7. **Iterate Prompts**: Refine based on output quality and approval feedback

---

**Document Version:** 1.0
**Last Updated:** 2025-10-18
**Next Review:** After pilot implementation
