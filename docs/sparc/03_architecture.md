# System Architecture - Sergas Super Account Manager Agent

## 1. Executive Summary

This document specifies the complete system architecture for the Sergas Super Account Manager Agent, a multi-agent system built on Claude Agent SDK (Python 3.14) that automates account review workflows by integrating Zoho CRM data with persistent memory (Cognee) to deliver actionable insights to account executives.

**Architecture Principles:**
- **Multi-Agent Pattern**: Orchestrator + specialized subagents with isolated contexts
- **Human-in-the-Loop**: All CRM modifications and outbound actions require approval
- **Security-First**: Least-privilege tool access, encrypted credentials, audit trails
- **Scalability**: Support 5,000 accounts and 50 owners without manual tuning
- **Integration-Centric**: MCP-based connections to Zoho CRM and Cognee memory layer

---

## 2. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SERGAS ACCOUNT MANAGER                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATION LAYER                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │           Main Orchestrator Agent (Python 3.14)              │   │
│  │  - Scheduling & workflow management                          │   │
│  │  - Subagent coordination via query()                         │   │
│  │  - Human approval gate orchestration                         │   │
│  │  - Session management & context preservation                 │   │
│  │  - Audit logging & metrics collection                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            ▼                    ▼                    ▼
┌─────────────────────┐ ┌─────────────────┐ ┌──────────────────────┐
│  Zoho Data Scout    │ │ Memory Analyst  │ │ Recommendation       │
│     Subagent        │ │    Subagent     │ │ Author Subagent      │
│                     │ │                 │ │                      │
│ • Account queries   │ │ • Historical    │ │ • Draft actions      │
│ • Change detection  │ │   context       │ │ • Confidence scoring │
│ • Owner mapping     │ │ • Pattern       │ │ • Rationale synthesis│
│ • Activity sync     │ │   analysis      │ │ • Template rendering │
│                     │ │ • Trend insights│ │                      │
└──────────┬──────────┘ └────────┬────────┘ └──────────┬───────────┘
           │                     │                      │
           │                     │                      │
           ▼                     ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       INTEGRATION LAYER (MCP)                        │
│  ┌───────────────────────┐         ┌──────────────────────────┐    │
│  │   Zoho CRM MCP Server │         │  Cognee Memory MCP Server│    │
│  │  (Remote/Self-hosted) │         │     (Self-hosted)        │    │
│  │                       │         │                          │    │
│  │ Tools:                │         │ Tools:                   │    │
│  │ • get_accounts        │         │ • store_context          │    │
│  │ • get_account_details │         │ • search_memory          │    │
│  │ • search_accounts     │         │ • retrieve_history       │    │
│  │ • get_deals           │         │ • aggregate_insights     │    │
│  │ • get_activities      │         │ • deduplicate_records    │    │
│  │ • get_notes           │         │                          │    │
│  │ • update_account*     │         └──────────────────────────┘    │
│  │ • create_task*        │                                          │
│  │ • add_note*           │    (*requires approval)                  │
│  └───────────────────────┘                                          │
└─────────────────────────────────────────────────────────────────────┘
           │                                            │
           ▼                                            ▼
┌─────────────────────┐                    ┌──────────────────────────┐
│   Zoho CRM API      │                    │  Cognee Storage Backend  │
│   (OAuth 2.0)       │                    │  (Vector DB + Graph)     │
│                     │                    │                          │
│ • Accounts          │                    │ • Account embeddings     │
│ • Deals             │                    │ • Historical notes       │
│ • Activities        │                    │ • Meeting summaries      │
│ • Notes             │                    │ • Recommendation history │
│ • Tasks             │                    │ • Relationship graph     │
└─────────────────────┘                    └──────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       SECURITY & SUPPORT LAYER                       │
│                                                                       │
│  ┌──────────────────┐  ┌───────────────┐  ┌─────────────────────┐  │
│  │ Secrets Manager  │  │ Audit Logger  │  │ Monitoring System   │  │
│  │ (AWS/Azure/Vault)│  │ (Structured)  │  │ (Prometheus/Cloud)  │  │
│  └──────────────────┘  └───────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      HUMAN INTERACTION LAYER                         │
│                                                                       │
│  ┌──────────────────┐  ┌───────────────┐  ┌─────────────────────┐  │
│  │ Approval UI      │  │ Email/Slack   │  │ Dashboard (Future)  │  │
│  │ (CLI/Web)        │  │ Notifications │  │                     │  │
│  └──────────────────┘  └───────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Agent Architecture

### 3.1 Main Orchestrator Agent

**Responsibilities:**
- Schedule and trigger account review cycles (daily/weekly/on-demand)
- Coordinate parallel subagent execution via Claude SDK `query()` API
- Aggregate subagent outputs into consolidated owner briefs
- Manage approval workflow for suggested actions
- Persist session state and enable resume capability
- Emit audit logs and performance metrics

**Configuration:**
```python
orchestrator_config = ClaudeAgentOptions(
    system_prompt="""You are the Sergas Account Manager Orchestrator.
    Your role is to:
    1. Coordinate subagents to review account portfolios
    2. Compile actionable briefs for account owners
    3. Gate all CRM modifications through human approval
    4. Maintain audit trails of all recommendations and decisions

    Never modify CRM data without explicit user approval.
    Always provide data sources for recommendations.
    Prioritize high-risk accounts first.""",

    allowed_tools=[
        "Read", "Write", "Bash",  # For config/logging
        "TodoWrite",  # For workflow tracking
        "create_session", "fork_session"  # Session management
    ],

    disallowed_tools=[
        "*zoho*update*", "*zoho*create*", "*zoho*delete*"  # No direct CRM writes
    ],

    permission_mode="acceptEdits",  # Require approval for file writes

    setting_sources=["project"],  # Load .claude/CLAUDE.md

    mcp_servers=[
        MCPServer(name="zoho-crm", protocol="remote",
                  endpoint=os.environ["ZOHO_MCP_ENDPOINT"]),
        MCPServer(name="cognee", protocol="stdio",
                  command=["npx", "cognee-mcp"])
    ],

    hooks={
        "pre_tool": log_tool_invocation,
        "post_tool": record_tool_result,
        "session_end": export_audit_trail
    }
)
```

**Workflow Logic:**
1. Load account owner assignments from config/database
2. For each owner segment, spawn parallel subagent queries:
   - Zoho Data Scout: Fetch account updates
   - Memory Analyst: Retrieve historical context
   - Recommendation Author: Generate action suggestions
3. Compile results into structured owner brief
4. Present to owner via notification/UI with approval buttons
5. Execute approved actions (task creation, note addition)
6. Store recommendations and decisions in Cognee for future context

---

### 3.2 Zoho Data Scout Subagent

**Purpose:** Retrieve account data from Zoho CRM with change detection and activity aggregation.

**Tool Allowlist:**
```python
zoho_scout_tools = [
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
    "Read",  # For loading last-sync timestamps
    "Write"  # For caching metadata (approval required)
]
```

**System Prompt:**
```python
zoho_scout_prompt = """You are the Zoho Data Scout for Sergas Account Manager.

Your responsibilities:
1. Fetch accounts assigned to specified owners from Zoho CRM
2. Detect changes since last sync (modified fields, new activities, stalled deals)
3. Aggregate related records (deals, tasks, notes, activities)
4. Return structured data with change flags and metadata

Output Format:
{
  "account_id": "123456789",
  "account_name": "Acme Corp",
  "owner": "john.doe@sergas.com",
  "last_modified": "2025-10-15T14:30:00Z",
  "changes_detected": true,
  "changes": [
    {"field": "Deal_Stage", "old": "Negotiation", "new": "Closed Won",
     "timestamp": "2025-10-15T10:00:00Z"}
  ],
  "open_deals": [...],
  "recent_activities": [...],
  "notes_count": 15,
  "risk_signals": ["No activity in 30 days", "Deal stalled in stage"]
}

Never write to CRM. If asked to modify data, respond: "I can only read data.
Contact the Orchestrator to request approved modifications."
"""
```

**Permission Mode:** `plan` (read-only execution)

---

### 3.3 Memory Analyst Subagent

**Purpose:** Query Cognee memory layer for historical account context, patterns, and prior recommendations.

**Tool Allowlist:**
```python
memory_analyst_tools = [
    # Cognee MCP Tools
    "cognee_search_memory",
    "cognee_retrieve_history",
    "cognee_aggregate_insights",
    "cognee_get_relationship_graph",

    # Analysis Utilities
    "Read"  # For loading analysis templates
]
```

**System Prompt:**
```python
memory_analyst_prompt = """You are the Memory Analyst for Sergas Account Manager.

Your responsibilities:
1. Search Cognee memory for historical account context
2. Identify patterns in past interactions, deals, and recommendations
3. Aggregate sentiment trends and commitment tracking
4. Surface relevant prior recommendations and their outcomes

Output Format:
{
  "account_id": "123456789",
  "historical_context": {
    "key_events": [
      {"date": "2025-09-01", "event": "Executive sponsor changed",
       "impact": "Delayed Q3 renewal"}
    ],
    "sentiment_trend": "declining",
    "prior_recommendations": [
      {"date": "2025-08-15", "recommendation": "Schedule exec briefing",
       "status": "completed", "outcome": "positive"}
    ],
    "relationship_strength": "strong",
    "commitment_tracking": ["Q4 renewal intent confirmed", "Budget approved"]
  }
}

Prioritize insights relevant to current account status.
If memory is stale, flag for re-ingestion.
"""
```

**Permission Mode:** `default` (read-only)

---

### 3.4 Recommendation Author Subagent

**Purpose:** Synthesize data from Data Scout and Memory Analyst to generate actionable recommendations with confidence scores and rationale.

**Tool Allowlist:**
```python
recommendation_author_tools = [
    "Read",  # For loading recommendation templates
    "Write"  # For drafting outputs (approval required)
]
```

**System Prompt:**
```python
recommendation_author_prompt = """You are the Recommendation Author for Sergas Account Manager.

Your responsibilities:
1. Synthesize account data and historical context into actionable recommendations
2. Assign confidence scores (low/medium/high) with supporting rationale
3. Draft follow-up email templates and task creation suggestions
4. Flag high-risk accounts for escalation

Output Format:
{
  "account_id": "123456789",
  "recommendations": [
    {
      "type": "follow_up_email",
      "priority": "high",
      "confidence": "high",
      "rationale": "No activity in 35 days; prior pattern shows engagement
                    drops before churn. Executive sponsor change increases risk.",
      "suggested_action": {
        "subject": "Checking in on Q4 renewal timeline",
        "draft_body": "Hi [Contact], I wanted to follow up on our Q3 conversation...",
        "next_steps": ["Schedule call within 5 days", "Confirm budget status"]
      },
      "data_references": ["zoho_account_123", "cognee_memory_ref_456"]
    },
    {
      "type": "escalation",
      "priority": "critical",
      "confidence": "medium",
      "rationale": "Deal stalled in Negotiation stage for 45 days; historical
                    pattern shows 60-day threshold before loss.",
      "suggested_action": {
        "escalate_to": "sales_manager",
        "reason": "Potential deal risk requires manager intervention"
      }
    }
  ]
}

Always provide data references. Never recommend actions without supporting evidence.
Assign confidence based on data recency and pattern strength.
"""
```

**Permission Mode:** `acceptEdits` (require approval for drafts)

---

## 4. Integration Architecture

### 4.1 Zoho CRM MCP Integration

**Connection Method:** Model Context Protocol (MCP) remote endpoint

**Configuration:**
```json
{
  "mcpServers": {
    "zoho-crm": {
      "protocol": "remote",
      "endpoint": "https://zoho-mcp2-900114980.us-east-1.elb.amazonaws.com",
      "authentication": {
        "type": "oauth2",
        "token_source": "secrets_manager",
        "secret_id": "sergas/zoho-crm/oauth-token",
        "refresh_endpoint": "https://accounts.zoho.com/oauth/v2/token"
      },
      "rate_limits": {
        "requests_per_minute": 120,
        "concurrent_requests": 5
      },
      "retry_policy": {
        "max_retries": 3,
        "backoff": "exponential",
        "initial_delay_ms": 1000
      }
    }
  }
}
```

**Available Tools:**
| Tool Name | Operation | Approval Required | Scope |
|-----------|-----------|-------------------|-------|
| `zoho_get_accounts` | List accounts by owner | No | READ |
| `zoho_get_account_details` | Fetch single account | No | READ |
| `zoho_search_accounts` | Query accounts by criteria | No | READ |
| `zoho_get_deals` | List deals for account | No | READ |
| `zoho_list_open_deals` | Filter open deals | No | READ |
| `zoho_get_activities` | Fetch activities | No | READ |
| `zoho_get_notes` | Retrieve notes | No | READ |
| `zoho_update_account` | Modify account fields | **YES** | WRITE |
| `zoho_create_task` | Create follow-up task | **YES** | CREATE |
| `zoho_add_note` | Add account note | **YES** | CREATE |

**Fallback REST Service:**
For operations not exposed by MCP (bulk sync, custom modules, analytics), a supplemental REST service will be built in Phase 2:
```python
# REST service for bulk operations
class ZohoRESTService:
    def __init__(self, oauth_credentials):
        self.client = ZohoCRMClient(oauth_credentials)

    def bulk_fetch_accounts(self, owner_ids, modified_since):
        """Batch fetch accounts for multiple owners"""
        pass

    def sync_account_metadata(self, account_ids):
        """Cache field metadata for offline analysis"""
        pass

    def get_analytics_feed(self, module, filters):
        """Fetch aggregated analytics from Zoho Analytics"""
        pass
```

---

### 4.2 Cognee Memory MCP Integration

**Connection Method:** MCP stdio server (self-hosted)

**Configuration:**
```json
{
  "mcpServers": {
    "cognee": {
      "protocol": "stdio",
      "command": ["npx", "cognee-mcp"],
      "env": {
        "COGNEE_API_URL": "http://localhost:8000",
        "COGNEE_API_KEY": "${COGNEE_API_KEY}"
      },
      "working_directory": "/opt/sergas/cognee"
    }
  }
}
```

**Storage Backend:**
- **Vector Database:** Qdrant (for semantic search of account context)
- **Graph Database:** Neo4j (for relationship mapping)
- **Relational Store:** PostgreSQL (for structured recommendation history)

**Data Model:**
```python
# Account Context in Cognee
{
  "account_id": "123456789",
  "account_name": "Acme Corp",
  "ingestion_timestamp": "2025-10-15T00:00:00Z",
  "embeddings": {
    "summary": [...],  # 1536-dim vector
    "notes": [...],
    "activities": [...]
  },
  "relationships": {
    "contacts": ["contact_001", "contact_002"],
    "deals": ["deal_001"],
    "parent_accounts": []
  },
  "metadata": {
    "last_analysis": "2025-10-14T12:00:00Z",
    "sentiment_score": 0.75,
    "engagement_level": "high"
  }
}

# Recommendation History
{
  "recommendation_id": "rec_12345",
  "account_id": "123456789",
  "created_at": "2025-10-15T10:00:00Z",
  "recommendation_type": "follow_up_email",
  "status": "approved",
  "outcome": "completed",
  "effectiveness_score": 0.85
}
```

**Tools:**
| Tool Name | Purpose | Usage |
|-----------|---------|-------|
| `cognee_search_memory` | Semantic search for context | Query: "executive sponsor changes affecting renewal" |
| `cognee_retrieve_history` | Get temporal account history | Fetch events from last 90 days |
| `cognee_aggregate_insights` | Pattern analysis | Identify churn risk signals |
| `cognee_store_context` | Persist new information | Save recommendation outcomes |
| `cognee_deduplicate_records` | Cleanup stale data | Remove outdated entries |

---

## 5. Data Architecture

### 5.1 Data Flow Diagram

```
┌──────────────┐
│ Zoho CRM API │ (Source of Truth)
└──────┬───────┘
       │ 1. Initial fetch via MCP
       ▼
┌────────────────────────────┐
│ Zoho Data Scout Subagent   │
│ • Query accounts by owner  │
│ • Detect changes           │
│ • Aggregate activities     │
└────────────┬───────────────┘
             │ 2. Structured account data
             ▼
┌─────────────────────────────┐
│ Main Orchestrator           │
│ • Enrich with owner context │
│ • Trigger memory lookup     │
└────────────┬────────────────┘
             │ 3. Account IDs + context request
             ▼
┌──────────────────────────────┐
│ Memory Analyst Subagent      │
│ • Search Cognee              │
│ • Retrieve historical events │
│ • Identify patterns          │
└────────────┬─────────────────┘
             │ 4. Historical insights
             ▼
┌─────────────────────────────────┐
│ Recommendation Author Subagent  │
│ • Synthesize data + context     │
│ • Generate recommendations      │
│ • Assign confidence scores      │
└────────────┬────────────────────┘
             │ 5. Actionable recommendations
             ▼
┌──────────────────────────────┐
│ Main Orchestrator            │
│ • Compile owner brief        │
│ • Present for approval       │
└────────────┬─────────────────┘
             │ 6. Approval request
             ▼
┌────────────────────────────┐
│ Human (Account Owner)      │
│ • Review recommendations   │
│ • Approve/Reject/Adjust    │
└────────────┬───────────────┘
             │ 7. Decision
             ▼
┌──────────────────────────────┐
│ Main Orchestrator            │
│ • Execute approved actions   │
│ • Store decisions in Cognee  │
│ • Emit audit logs            │
└────────────┬─────────────────┘
             │ 8. CRM updates (if approved)
             ▼
┌──────────────┐
│ Zoho CRM API │ (Updated)
└──────────────┘
```

### 5.2 Storage Layers

**1. Transient (Session-scoped):**
- Agent conversation context (Claude SDK manages)
- Subagent outputs cached during orchestrator workflow
- Temporary files for draft recommendations

**2. Short-Term Cache (Redis/Local):**
- Last sync timestamps per account
- Owner-to-account mappings
- Recent API responses (15-minute TTL)

**3. Long-Term Persistence (Cognee + PostgreSQL):**
- **Cognee:** Account embeddings, historical notes, relationship graphs
- **PostgreSQL:** Recommendation history, approval decisions, audit logs

**4. External Source (Zoho CRM):**
- Authoritative account, deal, contact, activity data
- Fetched on-demand via MCP; never cached longer than 1 hour

---

### 5.3 Audit Logging Schema

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,  -- 'orchestrator', 'zoho_scout', etc.
    action_type VARCHAR(50) NOT NULL,  -- 'tool_invocation', 'recommendation_generated', 'approval_requested', 'action_executed'

    -- Context
    account_id VARCHAR(50),
    owner_email VARCHAR(255),

    -- Tool/Action Details
    tool_name VARCHAR(100),
    tool_inputs JSONB,
    tool_outputs JSONB,

    -- Human Decision (for approval actions)
    decision VARCHAR(20),  -- 'approved', 'rejected', 'adjusted'
    decision_rationale TEXT,

    -- Metadata
    execution_time_ms INTEGER,
    error_message TEXT,

    INDEX idx_session (session_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_account (account_id)
);

CREATE TABLE recommendation_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recommendation_id UUID NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    recommendation_type VARCHAR(50) NOT NULL,

    -- Decision Tracking
    status VARCHAR(20) NOT NULL,  -- 'pending', 'approved', 'rejected', 'completed'
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,

    -- Effectiveness Tracking (populated post-execution)
    executed_at TIMESTAMP,
    outcome VARCHAR(50),  -- 'successful', 'unsuccessful', 'partial'
    effectiveness_score FLOAT,  -- 0.0-1.0 based on follow-up actions

    -- Data References
    data_sources JSONB,  -- ['zoho_account_123', 'cognee_memory_456']

    INDEX idx_account (account_id),
    INDEX idx_status (status),
    INDEX idx_created (created_at)
);
```

---

## 6. Security Architecture

### 6.1 Authentication & Authorization

**External Systems:**
```yaml
zoho_crm:
  auth_method: OAuth 2.0
  grant_type: authorization_code
  token_storage: AWS Secrets Manager (encrypted at rest)
  refresh_strategy: Automatic refresh 5 minutes before expiry
  scopes:
    - ZohoCRM.modules.accounts.READ
    - ZohoCRM.modules.deals.READ
    - ZohoCRM.modules.contacts.READ
    - ZohoCRM.modules.activities.READ
    - ZohoCRM.modules.notes.READ
    - ZohoCRM.modules.accounts.UPDATE  # Gated via approval
    - ZohoCRM.modules.tasks.CREATE     # Gated via approval

cognee:
  auth_method: API Key (internal service)
  key_storage: AWS Secrets Manager
  network_access: Localhost only (no external exposure)

anthropic_api:
  auth_method: API Key
  key_storage: AWS Secrets Manager
  usage_tracking: Enabled (cost monitoring)
```

**Agent-Level Authorization:**
| Agent | Zoho Tools | Cognee Tools | File System | Bash |
|-------|-----------|--------------|-------------|------|
| Orchestrator | None (delegates) | None (delegates) | Read/Write (approved) | Limited |
| Zoho Scout | Read-only | None | Read (cache) | No |
| Memory Analyst | None | Read-only | Read | No |
| Recommendation Author | None | None | Read/Write (approved) | No |

---

### 6.2 Encryption

**At Rest:**
- **Secrets:** AES-256 via AWS Secrets Manager/Azure Key Vault
- **Cognee Storage:** AES-256 for vector/graph databases
- **Audit Logs:** Encrypted PostgreSQL volumes
- **Local Cache:** Encrypted filesystem (LUKS/BitLocker)

**In Transit:**
- **Zoho API:** TLS 1.3
- **Cognee MCP:** Localhost only (no network encryption)
- **Anthropic API:** TLS 1.3
- **Internal Agent Communication:** In-memory (no network)

---

### 6.3 Data Privacy & Compliance

**GDPR/CCPA Considerations:**
- **Data Minimization:** Fetch only fields required for analysis
- **Right to Forget:** Implement account data purge in Cognee
- **Data Portability:** Export account context on request
- **Audit Trails:** Retain logs for 2 years (configurable)

**Sensitive Field Redaction:**
```python
REDACTED_FIELDS = [
    "SSN", "Tax_ID", "Credit_Card", "Bank_Account",
    "Personal_Email", "Home_Address", "Date_of_Birth"
]

def redact_sensitive_fields(data: dict) -> dict:
    """Remove sensitive fields from agent outputs"""
    for field in REDACTED_FIELDS:
        if field in data:
            data[field] = "[REDACTED]"
    return data
```

**Access Control:**
- Account owners can only view briefs for their assigned accounts
- Sales managers have cross-team visibility
- Operations admins control system configuration
- All access logged with user ID and timestamp

---

### 6.4 Approval Workflow Security

**Approval Gate Design:**
```python
class ApprovalGate:
    def __init__(self, notifier: Notifier, audit_logger: AuditLogger):
        self.notifier = notifier
        self.audit_logger = audit_logger

    async def request_approval(self, recommendation: dict, owner_email: str) -> dict:
        """Present recommendation to owner and await decision"""
        approval_id = generate_uuid()

        # Log approval request
        self.audit_logger.log_approval_request(
            approval_id=approval_id,
            recommendation=recommendation,
            owner=owner_email
        )

        # Send notification (email/Slack)
        await self.notifier.send(
            to=owner_email,
            subject=f"Action Required: {recommendation['account_name']}",
            body=self.render_approval_template(recommendation),
            actions=[
                {"label": "Approve", "callback": f"approve/{approval_id}"},
                {"label": "Reject", "callback": f"reject/{approval_id}"},
                {"label": "Adjust", "callback": f"adjust/{approval_id}"}
            ]
        )

        # Wait for decision (timeout: 72 hours)
        decision = await self.wait_for_decision(approval_id, timeout=72*3600)

        # Log decision
        self.audit_logger.log_approval_decision(
            approval_id=approval_id,
            decision=decision,
            timestamp=datetime.utcnow()
        )

        return decision
```

**Security Properties:**
- Approval links expire after 72 hours
- Single-use tokens prevent replay attacks
- Decisions logged with IP address and user agent
- No automated approvals (always require human input)

---

## 7. Deployment Architecture

### 7.1 Hosting Options

**Option 1: Cloud VM (AWS EC2/Azure VM)**
```
┌─────────────────────────────────────────┐
│      AWS EC2 Instance (t3.large)        │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Main Orchestrator Process        │ │
│  │  (Python 3.14 + Claude SDK)       │ │
│  │                                   │ │
│  │  ┌─────────────────────────────┐ │ │
│  │  │ Cognee MCP Server (stdio)   │ │ │
│  │  │ - Qdrant (vector DB)        │ │ │
│  │  │ - Neo4j (graph DB)          │ │ │
│  │  │ - PostgreSQL (relational)   │ │ │
│  │  └─────────────────────────────┘ │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Secrets Manager Integration            │
│  CloudWatch Logging                     │
│  Auto-scaling disabled (stateful)       │
└─────────────────────────────────────────┘
```

**Option 2: Container (Docker/Kubernetes)**
```yaml
# docker-compose.yml
services:
  orchestrator:
    image: sergas/account-manager:latest
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ZOHO_MCP_ENDPOINT=${ZOHO_MCP_ENDPOINT}
      - COGNEE_API_URL=http://cognee:8000
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    depends_on:
      - cognee
      - postgres

  cognee:
    image: cognee/server:latest
    ports:
      - "8000:8000"
    environment:
      - QDRANT_URL=http://qdrant:6333
      - NEO4J_URL=bolt://neo4j:7687
    depends_on:
      - qdrant
      - neo4j

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant-data:/qdrant/storage

  neo4j:
    image: neo4j:latest
    environment:
      - NEO4J_AUTH=neo4j/password
    volumes:
      - neo4j-data:/data

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=sergas_audit
      - POSTGRES_USER=sergas
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
```

**Recommendation:** Start with cloud VM (simpler for stateful orchestrator), migrate to Kubernetes for production scalability.

---

### 7.2 Scalability Design

**Current Scale:** 5,000 accounts, 50 owners

**Scalability Approach:**

1. **Horizontal Scaling (Future):**
   - Partition accounts by owner segments
   - Run multiple orchestrator instances (one per segment)
   - Load balance via account hash

2. **Vertical Scaling (Phase 1):**
   - t3.large (2 vCPU, 8 GB RAM) for orchestrator
   - Cognee on separate m5.xlarge (4 vCPU, 16 GB RAM)
   - PostgreSQL on RDS (db.t3.medium)

3. **Caching Strategy:**
   - Account metadata cached for 1 hour (Redis)
   - Owner assignments cached until midnight (refresh daily)
   - Zoho API responses cached per request (15 min TTL)

4. **Batch Processing:**
   - Process 50 accounts in parallel (10 owners × 5 accounts avg)
   - Queue remaining accounts for next cycle
   - Prioritize accounts with detected changes

**Performance Targets:**
| Metric | Target | Measurement |
|--------|--------|-------------|
| Owner brief generation | <10 minutes | End-to-end cycle time |
| Single account analysis | <30 seconds | Subagent execution time |
| Zoho API latency | <500ms p95 | MCP tool response time |
| Cognee query latency | <200ms p95 | Memory search time |
| Daily throughput | 5,000 accounts | Scheduled run completion |

---

### 7.3 Monitoring & Observability

**Metrics to Track:**
```python
# Prometheus metrics
metrics = {
    # System Health
    "orchestrator_runs_total": Counter("Total orchestrator runs"),
    "orchestrator_run_duration_seconds": Histogram("Run duration"),
    "orchestrator_run_failures_total": Counter("Failed runs"),

    # Agent Performance
    "subagent_invocations_total": Counter("Subagent calls", ["agent_name"]),
    "subagent_duration_seconds": Histogram("Subagent duration", ["agent_name"]),
    "subagent_errors_total": Counter("Subagent errors", ["agent_name"]),

    # Integration Health
    "zoho_api_requests_total": Counter("Zoho API calls", ["tool_name"]),
    "zoho_api_latency_seconds": Histogram("Zoho latency", ["tool_name"]),
    "zoho_api_errors_total": Counter("Zoho errors", ["error_code"]),
    "cognee_queries_total": Counter("Cognee queries"),
    "cognee_latency_seconds": Histogram("Cognee latency"),

    # Business Metrics
    "accounts_processed_total": Counter("Accounts analyzed"),
    "recommendations_generated_total": Counter("Recommendations", ["type"]),
    "recommendations_approved_total": Counter("Approved actions"),
    "recommendations_rejected_total": Counter("Rejected actions"),

    # Cost Tracking
    "anthropic_tokens_used_total": Counter("Claude API tokens", ["model"]),
    "anthropic_api_cost_usd": Counter("API cost estimate")
}
```

**Alerting Rules:**
```yaml
alerts:
  - name: HighErrorRate
    condition: zoho_api_errors_total > 10 in 5m
    severity: warning
    action: Notify on-call engineer

  - name: SlowOrchestrator
    condition: orchestrator_run_duration_seconds > 600
    severity: warning
    action: Investigate performance bottleneck

  - name: ApprovalBacklog
    condition: pending_approvals_count > 50
    severity: info
    action: Notify account managers

  - name: CogneeDown
    condition: cognee_queries_total == 0 for 10m
    severity: critical
    action: Restart Cognee service + notify
```

**Logging Strategy:**
```python
import structlog

logger = structlog.get_logger()

# Structured logging example
logger.info(
    "recommendation_generated",
    account_id="123456789",
    owner="john.doe@sergas.com",
    recommendation_type="follow_up_email",
    confidence="high",
    session_id="sess_abc123",
    duration_ms=1234
)
```

---

## 8. Configuration Management

### 8.1 Environment Configuration

**config/environments/production.yaml**
```yaml
environment: production

anthropic:
  api_key_source: aws_secrets_manager
  secret_id: sergas/anthropic-api-key
  model: claude-sonnet-4-5
  max_tokens: 8192
  temperature: 0.7

zoho_crm:
  mcp_endpoint: https://zoho-mcp2-900114980.us-east-1.elb.amazonaws.com
  oauth_token_source: aws_secrets_manager
  secret_id: sergas/zoho-crm/oauth-token
  rate_limit_requests_per_minute: 120
  retry_max_attempts: 3

cognee:
  api_url: http://localhost:8000
  api_key_source: aws_secrets_manager
  secret_id: sergas/cognee-api-key
  vector_db_url: http://qdrant:6333
  graph_db_url: bolt://neo4j:7687

orchestrator:
  schedule_cron: "0 6 * * *"  # Daily at 6 AM UTC
  max_parallel_subagents: 10
  session_timeout_minutes: 30
  approval_timeout_hours: 72

auditing:
  log_level: INFO
  log_destination: cloudwatch
  audit_db_url: postgresql://sergas:${POSTGRES_PASSWORD}@postgres:5432/sergas_audit
  retention_days: 730

monitoring:
  prometheus_port: 9090
  metrics_enabled: true
  tracing_enabled: true
  cost_tracking_enabled: true
```

---

### 8.2 Agent Prompt Configuration

**config/prompts/orchestrator.md**
```markdown
# Sergas Account Manager Orchestrator

You are the main orchestrator for Sergas Account Manager, coordinating subagents to analyze account portfolios and generate actionable insights.

## Core Responsibilities
1. Schedule and trigger account review cycles
2. Coordinate parallel subagent execution
3. Compile owner-specific briefs
4. Manage human approval workflows
5. Execute approved actions
6. Maintain audit trails

## Workflow
For each scheduled run:
1. Load account-owner assignments
2. Spawn subagents in parallel:
   - Zoho Data Scout: Fetch account updates
   - Memory Analyst: Retrieve historical context
   - Recommendation Author: Generate action suggestions
3. Aggregate results by owner
4. Present recommendations for approval
5. Execute approved actions
6. Log outcomes

## Safety Rules
- Never modify CRM data without explicit approval
- Always provide data source references
- Prioritize high-risk accounts
- Redact sensitive fields in outputs
- Log all decisions with timestamps

## Output Format
Generate owner briefs in this structure:
```json
{
  "owner_email": "john.doe@sergas.com",
  "generated_at": "2025-10-18T06:00:00Z",
  "accounts_reviewed": 23,
  "high_priority_accounts": 3,
  "recommendations": [...]
}
```
```

---

## 9. Technology Stack Rationale

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Agent Framework** | Claude Agent SDK (Python 3.14) | Native Claude Code integration, MCP support, session management, hooks |
| **Orchestrator Runtime** | Python 3.14 | SDK native support, async/await for subagents, rich ecosystem |
| **Zoho Integration** | MCP Remote Endpoint | OAuth handled by MCP server, fine-grained tool permissions, retry/backoff |
| **Memory Layer** | Cognee MCP | Purpose-built for LLM memory, vector + graph storage, deduplication |
| **Vector Database** | Qdrant | High-performance semantic search, Python SDK, easy deployment |
| **Graph Database** | Neo4j | Relationship mapping, Cypher queries, mature tooling |
| **Relational Database** | PostgreSQL | Audit logs, recommendation history, JSONB support |
| **Secrets Management** | AWS Secrets Manager / Azure Key Vault | Encryption at rest, automatic rotation, IAM integration |
| **Monitoring** | Prometheus + CloudWatch | Metrics collection, alerting, cost tracking |
| **Logging** | structlog + CloudWatch Logs | Structured JSON logs, queryable, retained 2 years |
| **Deployment** | Docker Compose → Kubernetes | Initial simplicity, future scalability |

---

## 10. Scalability Considerations

### 10.1 Current Capacity Analysis

**5,000 accounts, 50 owners:**
- Average accounts per owner: 100
- Orchestrator processes 10 owners in parallel (10 minutes each)
- Total cycle time: ~50 minutes (within 10-minute target per owner segment)

**Bottlenecks:**
1. **Zoho API rate limits:** 120 req/min = 7,200 req/hour
   - 5,000 accounts × 3 API calls avg = 15,000 calls
   - Requires 2+ hours without batching
   - **Mitigation:** Batch requests, cache metadata, use change detection

2. **Cognee memory queries:** 5,000 searches × 200ms = 16.7 minutes
   - **Mitigation:** Parallelize queries, cache recent results

3. **Claude API latency:** 5,000 recommendations × 3 seconds = 4.2 hours
   - **Mitigation:** Batch subagent calls, use Haiku for simple cases

---

### 10.2 Scaling Strategy (Future)

**10,000 accounts, 100 owners:**
- Horizontal scaling: Deploy 2 orchestrator instances
- Partition accounts by owner ID hash
- Shared Cognee cluster with read replicas

**50,000 accounts, 500 owners:**
- Kubernetes cluster with 10 orchestrator pods
- Dedicated Zoho MCP servers per region
- Cognee sharding by account segment
- PostgreSQL read replicas for audit logs

---

## 11. Next Steps

1. **Phase 1 (Foundation):**
   - Implement orchestrator with session management
   - Configure Zoho MCP and test tool catalog
   - Deploy Cognee sandbox and ingest pilot data
   - Build approval workflow (CLI-based)

2. **Phase 2 (Agent Development):**
   - Develop and test three subagents
   - Implement hooks for audit logging
   - Create recommendation templates
   - Run pilot with 50 accounts

3. **Phase 3 (Production Hardening):**
   - Integrate secrets manager
   - Add Prometheus metrics and alerting
   - Build REST fallback service for Zoho
   - Conduct security review

4. **Phase 4 (Scaling):**
   - Implement batch processing
   - Add horizontal scaling support
   - Build admin UI for configuration
   - Deploy to production

---

**Document Version:** 1.0
**Last Updated:** 2025-10-18
**Next Review:** After Phase 1 completion
