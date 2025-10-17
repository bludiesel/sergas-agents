# Product Requirements Document (PRD)
## Title: Sergas Super Account Manager Agent

### 1. Background & Opportunity
- Sergas account executives manage a large portfolio in Zoho CRM; manual monitoring leads to missed updates and delayed follow-ups.
- Claude Agent SDK (Python 3.14) enables a multi-agent system that automates account review, synthesizes history, and recommends owner actions while keeping humans in control.
- Integrating Zoho CRM data with a persistent memory layer (e.g., Cognee) promises higher situational awareness and better prioritization for account teams.

### 2. Product Goals
1. Provide daily/weekly account briefs highlighting changes, risks, and recommended actions per owner.
2. Reduce manual CRM auditing time for Sergas reps by ≥60% while improving follow-up adherence.
3. Maintain auditable, policy-compliant automation with human approval gates before CRM updates or owner notifications.

### 3. Success Metrics
- **Adoption**: ≥80% of target reps review agent-generated briefs weekly.
- **Recommendation Uptake**: ≥50% of suggested actions accepted or scheduled.
- **Time Savings**: Average account review time <3 minutes (baseline >8 min).
- **Data Quality**: <2% error rate in surfaced account status or owner assignments.
- **System Reliability**: 99% successful run rate across scheduled cycles.

### 4. User Personas & Needs
- **Account Executive (Primary)**: Wants concise, trustworthy insights, fast triage of high-risk accounts, and draft follow-up actions.
- **Sales Manager**: Requires visibility into team workload, adherence to process, and audit trails for recommendations vs. actions taken.
- **Operations Admin**: Needs control over API credentials, security compliance, and ability to configure scopes/data retention.

### 5. Functional Requirements
#### 5.1 Core Workflow
1. Orchestrator schedules account reviews (daily/weekly) or runs on demand.
2. Zoho Data Scout agent retrieves account updates, owner info, recent activities via Zoho CRM MCP server.
3. Memory Analyst agent queries Cognee (or alternative) for historical context (past notes, meeting summaries, prior recommendations).
4. Recommendation Author agent drafts actionable guidance with rationale, confidence, and supporting data references.
5. Orchestrator compiles a brief per account owner, awaiting human approval for any CRM changes or outbound communications.

#### 5.2 Key Features
- Account change detection (modified fields, stalled deals, inactivity thresholds).
- Historical insight aggregation (key events, sentiment trends, prior commitments).
- Action recommendation templates (follow-up email draft, task creation suggestion, escalation alert).
- Human-in-the-loop confirmation workflow (approve/adjust/reject suggestions).
- Logging & audit trail (source data references, tool usage records, final decisions).

#### 5.3 Integrations
- **Zoho CRM (Phase 1)**: use the provisioned Zoho MCP endpoint via Claude (`npx mcp-remote https://zoho-mcp2-900114980...`), catalog available tools, and gate write operations through approval hooks.
- **Zoho CRM (Phase 2)**: build supplemental REST/SDK services for operations not exposed by the MCP (bulk read/write, custom modules, analytics feeds).
- **Memory Layer**: Cognee MCP server (or equivalent) for persistent account context.
- Optional connectors (future): email/calendar APIs, BI dashboards.

#### 5.4 Administration & Configuration
- UI or config files to manage review cadence, account segments, risk rules, output targets.
- Secrets management for Zoho credentials and Cognee tokens.
- Tool permissions per agent to enforce least privilege.

### 6. Non-Functional Requirements
- **Security**: Compliance with Sergas data policies; encrypt credentials and stored memory; redact sensitive fields in outputs.
- **Scalability**: Handle up to 5k accounts, 50 account owners without manual tuning.
- **Performance**: Generate owner brief within 10 minutes of scheduled run; individual account analysis <30 seconds.
- **Reliability**: Graceful degradation when Zoho or Cognee unavailable; retry/backoff strategies.
- **Observability**: Metrics for run success, API latency, token usage; error reporting with actionable logs.

### 7. Implementation Milestones
1. **Foundation**
   - Set up Python 3.14 environment; install Claude Agent SDK.
   - Register existing Zoho MCP endpoint in Claude config; enumerate tools and validate required scopes.
   - Deploy Cognee sandbox; ingest pilot dataset.
2. **Agent Orchestration**
   - Implement orchestrator client with scheduling hooks and logging.
   - Define subagent prompts/config (Data Scout, Memory Analyst, Recommendation Author); enforce tool permissions.
   - Build hooks for audit logging and approval gating.
3. **Pilot Experience**
   - Run limited account set; validate data accuracy, recommendation quality.
   - Add human approval interface (CLI, Slack, or lightweight UI) capturing feedback.
   - Iterate prompts and scoring heuristics based on pilot feedback.
4. **Production Hardening**
   - Integrate secrets manager; add monitoring & alerting.
   - Implement retry/backoff, fallback flows when memory or MCP unavailable; introduce REST/SDK service for gap operations.
   - Conduct security/privacy review; finalize compliance documentation.

### 8. Risks & Mitigations
- **Data Quality Issues**: align with Ops to validate mappings; include manual spot-check workflows.
- **API Rate Limits**: cache metadata, leverage Zoho notifications for incremental sync.
- **Compliance Concerns**: maintain approval workflows; mask sensitive fields in logs; store recommendations separate from CRM modifications.
- **Memory Drift**: schedule periodic Cognee re-ingestion; evaluate deduplication heuristics; maintain evaluation suite.

### 9. Dependencies & Open Questions
- Availability of Zoho sandbox and OAuth client registration.
- Confirmation on Cognee hosting preference (self-hosted vs. managed) and infrastructure ownership.
- Clarify required modules beyond standard Accounts/Deals (custom fields, support tickets, finance data).
- Define approval UX (existing tool vs. new interface) and notification channels for owners.
- Determine long-term storage of recommendations (CRM Notes vs. separate knowledge base).

---
*Prepared to guide planning and execution of the Sergas Super Account Manager agent.*
