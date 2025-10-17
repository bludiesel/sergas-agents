# SPARC Specification Phase - Key Decisions Summary

**Phase**: Specification
**Status**: Complete
**Date**: 2025-10-18
**Document**: /Users/mohammadabdelrahman/Projects/sergas_agents/docs/sparc/01_specification.md

---

## Key Architectural Decisions

### 1. Multi-Agent Architecture
- **Orchestrator**: Main coordinator using ClaudeSDKClient
- **Zoho Data Scout**: Fetch CRM data (read-only MCP tools)
- **Memory Analyst**: Query Cognee for historical context
- **Recommendation Author**: Generate action suggestions (write-gated)
- **Human-in-the-loop**: All CRM writes require approval

### 2. Integration Strategy
- **Primary Zoho Access**: Use provisioned MCP endpoint (`zoho-mcp2-900114980.zohomcp.com`)
- **Fallback**: Direct Zoho REST API v6 for gaps
- **Memory Layer**: Cognee knowledge graph via custom MCP server
- **Secrets**: AWS Secrets Manager or HashiCorp Vault
- **Monitoring**: Prometheus + Grafana (preferred)

### 3. Data Model Core Entities
- **Account**: Primary CRM entity with computed health/risk scores
- **Deal**: Sales opportunities with stage tracking
- **Contact**: Customer contacts linked to accounts
- **Note**: Activity history + system recommendations
- **Task**: Follow-up actions (user or system-created)
- **Recommendation**: AI-generated suggestions with approval workflow
- **OwnerBrief**: Daily/weekly digest per account executive

### 4. Success Metrics (Critical)
- **Adoption**: ≥80% of reps review briefs weekly
- **Recommendation Uptake**: ≥50% accepted or scheduled
- **Time Savings**: <3 minutes per account (from 8+ min baseline)
- **Data Accuracy**: <2% error rate
- **System Reliability**: 99% successful run rate

### 5. Non-Functional Requirements (Priority)
- **Performance**: <10 min owner brief, <30 sec per account, <5 sec Cognee query
- **Scalability**: 5,000 accounts, 50 owners without manual tuning
- **Security**: TLS 1.3, AES-256 encryption, secrets manager, RBAC
- **Compliance**: GDPR, SOC2, 7-year audit log retention

---

## User Personas & Needs

### Account Executive (Primary)
- **Need**: Concise insights, fast triage, actionable guidance
- **Pain**: Missing updates, lost context, manual tracking
- **Success**: <2 hours weekly portfolio review, 50%+ recommendation acceptance

### Sales Manager (Secondary)
- **Need**: Team visibility, process adherence, audit trails
- **Pain**: Coverage gaps, tracking difficulty, manual reporting
- **Success**: Identify gaps, track uptake, demonstrate compliance

### Operations Admin (Tertiary)
- **Need**: Security control, compliance management, system configuration
- **Pain**: Credential sprawl, lack of permissions, manual diagnostics
- **Success**: Centralized secrets, granular permissions, <10 min MTTR

---

## Functional Requirements Summary

### Core Capabilities
1. **Account Review Orchestration**: Scheduled (daily/weekly) + on-demand
2. **Change Detection**: Field-level changes, inactivity, deal stalls, risk scoring
3. **Historical Context**: Cognee timeline, key events, sentiment, commitments
4. **Recommendation Generation**: Templates, prioritization, drafts, confidence scoring
5. **Approval Workflow**: Gate all CRM writes, capture feedback, audit trail
6. **Logging & Audit**: Operation logs, source references, tool usage, decision trail

### Integration Requirements
- **Zoho MCP**: Primary access via provisioned endpoint
- **Zoho REST API**: Fallback for bulk operations and gap coverage
- **Cognee MCP**: Memory layer for historical context
- **Secrets Manager**: Secure credential storage
- **Monitoring**: Metrics, logs, traces, alerts

---

## Acceptance Criteria Highlights

### Feature Acceptance
- Account review executes within 10 minutes for 50 accounts
- Change detection accuracy: zero false positives/negatives
- At-risk detection: risk score ≥70 for inactive accounts
- Historical context query: <5 seconds, ≥90% relevance
- Recommendation quality: ≥50% acceptance rate
- Approval workflow: blocks writes until confirmed

### Performance Acceptance
- Review latency: <10 min owner brief, <30 sec per account
- Memory query: P95 <5 sec, P99 <8 sec
- Scalability: 5,000 accounts in <10 hours
- System uptime: ≥99% over 30 days

### Security Acceptance
- Zero plaintext credentials in code/logs
- All API calls use TLS 1.3
- Cognee storage AES-256 encrypted
- SSL Labs rating A or A+

### User Acceptance
- ≥80% rate brief as "clear and easy to understand"
- ≥70% complete review in <3 minutes
- ≥50% recommendation acceptance rate
- <10% rejection as "inappropriate"

---

## Implementation Phases

### Phase 1: Foundation (Week 1-6)
- Python 3.14 environment + Claude Agent SDK
- Zoho MCP endpoint registration and validation
- Cognee deployment + pilot data ingestion
- Secrets manager integration
- Basic monitoring setup

### Phase 2: Agent Orchestration (Week 3-6)
- Orchestrator client with scheduling
- Subagent definitions (Data Scout, Memory Analyst, Recommendation Author)
- Tool permissions and approval hooks
- Audit logging implementation

### Phase 3: Pilot Experience (Week 7-10)
- Limited account set (50-100 accounts, 5-10 users)
- Human approval interface (CLI or Slack)
- Prompt iteration based on feedback
- Recommendation quality tuning

### Phase 4: Production Hardening (Week 11-14)
- Secrets manager production deployment
- Monitoring and alerting finalization
- Retry/backoff and fallback flows
- Security/privacy review
- Compliance documentation

---

## Critical Constraints

### Technical
- Python 3.14 required
- Zoho rate limits: 200-5,000 calls/day
- Claude token limits: 200K per request
- MCP timeout: 30 seconds default

### Business
- Timeline: 14 weeks to production
- Team: 3 engineers
- Account volume: 5,000 max (Phase 1)
- Owner count: 50 max

### Compliance
- US-based hosting for Sergas data
- SOC2 Type II certification required
- GDPR compliance for EU accounts
- 7-year audit log retention

---

## Next Steps for Pseudocode Phase

1. **Algorithm Design**: Detail core algorithms for change detection, risk scoring, recommendation generation
2. **Workflow Sequences**: Pseudocode for orchestration, subagent coordination, approval workflow
3. **Data Processing**: Logic for Zoho data retrieval, Cognee queries, snapshot comparisons
4. **Error Handling**: Retry strategies, fallback flows, degradation logic
5. **Performance Optimization**: Caching strategies, batch operations, parallel execution

---

**Specification Phase Complete**
Ready for SPARC Pseudocode Phase (02_pseudocode.md)
