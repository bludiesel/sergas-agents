# System Requirements Specification
## Sergas Super Account Manager Agent

**Project**: Sergas Super Account Manager Agent
**Version**: 1.0.0
**Status**: Draft
**Date**: 2025-10-18
**Authors**: SPARC Specification Team
**SPARC Phase**: Specification

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [User Personas & Needs](#2-user-personas--needs)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Success Metrics](#5-success-metrics)
6. [Use Cases & User Stories](#6-use-cases--user-stories)
7. [System Boundaries & Constraints](#7-system-boundaries--constraints)
8. [Integration Requirements](#8-integration-requirements)
9. [Data Model Specification](#9-data-model-specification)
10. [Acceptance Criteria](#10-acceptance-criteria)

---

## 1. Executive Summary

### 1.1 Purpose

The Sergas Super Account Manager Agent is an AI-powered automation system built on Claude Agent SDK (Python 3.14) that transforms how account executives manage their Zoho CRM portfolios. The system performs automated account reviews, synthesizes historical context, and generates actionable recommendations while maintaining human oversight through approval workflows.

### 1.2 Scope

**In Scope:**
- Multi-agent orchestration system with specialized subagents
- Zoho CRM integration via official MCP endpoint
- Persistent memory layer using Cognee knowledge graph
- Account change detection and risk analysis
- Automated recommendation generation
- Human-in-the-loop approval workflows
- Comprehensive audit trails and logging
- Daily/weekly account briefings per owner

**Out of Scope:**
- Fully autonomous CRM updates without approval
- Real-time notifications (Phase 1)
- Email/calendar API integration (Phase 1)
- BI dashboard creation (Phase 1)
- Mobile application interface
- Multi-CRM platform support

### 1.3 Problem Statement

Sergas account executives manage large portfolios in Zoho CRM manually, resulting in:
- Missed account updates and delayed follow-ups
- Average 8+ minutes per account review
- Inconsistent monitoring practices
- Lost context across account history
- Reactive rather than proactive engagement

### 1.4 Solution Overview

A multi-agent AI system that:
- Automatically monitors account changes across portfolio
- Synthesizes historical context from knowledge graph
- Generates prioritized action recommendations
- Reduces review time by 60% (target <3 minutes)
- Maintains audit compliance and human control

---

## 2. User Personas & Needs

### 2.1 Account Executive (Primary Persona)

**Profile:**
- Name: Sarah Chen
- Role: Senior Account Executive
- Portfolio: 50-80 active accounts
- Experience: 3-5 years in B2B sales
- Technical Comfort: Moderate

**Needs:**
- **Concise Insights**: Quick-scan briefs highlighting critical changes
- **Trustworthy Data**: Accurate account status with source references
- **Fast Triage**: Clear risk signals and priority rankings
- **Actionable Guidance**: Draft follow-ups and next steps
- **Time Efficiency**: Sub-3-minute account reviews

**Pain Points:**
- Missing deal stage changes buried in activity feeds
- Losing context on multi-month account histories
- Manual tracking of follow-up commitments
- Uncertainty about prioritization across portfolio

**Success Criteria:**
- Can review entire portfolio in <2 hours weekly
- Identifies at-risk accounts within 24 hours of status change
- Accepts 50%+ of system recommendations
- Maintains confidence in data accuracy

### 2.2 Sales Manager (Secondary Persona)

**Profile:**
- Name: Marcus Rodriguez
- Role: Regional Sales Manager
- Team Size: 8-12 account executives
- Responsibilities: Team performance, process adherence, forecasting

**Needs:**
- **Team Visibility**: Overview of workload distribution
- **Process Adherence**: Verification of follow-up discipline
- **Audit Trails**: Record of recommendations vs. actions taken
- **Performance Insights**: Recommendation acceptance rates per rep
- **Compliance Assurance**: Policy adherence in automated outputs

**Pain Points:**
- Lack of visibility into account coverage gaps
- Difficulty tracking whether reps act on insights
- Manual reporting on team activity
- Compliance risk from inconsistent documentation

**Success Criteria:**
- Can identify coverage gaps across team portfolio
- Tracks recommendation uptake per team member
- Demonstrates audit compliance in reviews
- Reduces team admin time by 40%+

### 2.3 Operations Admin (Tertiary Persona)

**Profile:**
- Name: Priya Patel
- Role: Sales Operations Administrator
- Responsibilities: System configuration, security, data governance

**Needs:**
- **Security Control**: Manage API credentials and access scopes
- **Compliance Management**: Configure data retention and redaction rules
- **System Configuration**: Define review cadence and account segments
- **Audit Capabilities**: Access logs of all system actions
- **Integration Management**: Control MCP endpoints and tool permissions

**Pain Points:**
- Credential sprawl across multiple integrations
- Lack of granular permission controls
- Manual compliance report generation
- Difficulty diagnosing integration failures

**Success Criteria:**
- Centralized secrets management for all credentials
- Granular tool permissions per subagent
- Automated compliance report generation
- Sub-10-minute mean time to diagnose issues

---

## 3. Functional Requirements

### 3.1 Account Review Orchestration

#### FR-3.1.1: Scheduled Review Execution
**Priority**: High
**Description**: System shall execute account reviews on configurable schedules (daily, weekly, on-demand)

**Acceptance Criteria:**
- Supports cron-style schedule configuration
- Executes reviews for all accounts in segment
- Handles interruptions with resume capability
- Logs start/end times and execution status

#### FR-3.1.2: Owner-Based Segmentation
**Priority**: High
**Description**: System shall group accounts by owner and generate owner-specific briefs

**Acceptance Criteria:**
- Retrieves owner assignments from Zoho CRM
- Groups accounts by owner ID
- Generates consolidated brief per owner
- Supports manual owner override

#### FR-3.1.3: On-Demand Review Trigger
**Priority**: Medium
**Description**: Users shall trigger immediate review for specific accounts

**Acceptance Criteria:**
- CLI command accepts account ID(s)
- Executes full review workflow for specified accounts
- Returns results within 30 seconds for single account
- Supports batch mode for multiple accounts

### 3.2 Account Change Detection

#### FR-3.2.1: Field-Level Change Tracking
**Priority**: High
**Description**: System shall detect changes in critical account fields since last review

**Critical Fields:**
- Account Status/Stage
- Deal Stage and Close Date
- Account Owner
- Last Activity Date
- Revenue/ARR values
- Health Score (if available)

**Acceptance Criteria:**
- Compares current state to last-known state in memory
- Identifies all changed fields with old/new values
- Timestamps change detection
- Flags changes meeting alert thresholds

#### FR-3.2.2: Inactivity Detection
**Priority**: High
**Description**: System shall identify accounts with no activity beyond threshold

**Acceptance Criteria:**
- Configurable inactivity thresholds (default: 30 days)
- Checks last activity date across modules (Accounts, Deals, Notes, Tasks)
- Calculates days since last touch
- Surfaces accounts exceeding threshold in priority list

#### FR-3.2.3: Deal Stall Detection
**Priority**: Medium
**Description**: System shall detect deals stalled in stage beyond expected duration

**Acceptance Criteria:**
- Configurable stage duration limits per pipeline stage
- Calculates time in current stage
- Flags deals exceeding threshold
- Includes stage history in context

#### FR-3.2.4: Risk Signal Aggregation
**Priority**: Medium
**Description**: System shall compute composite risk score from multiple signals

**Risk Signals:**
- Inactivity duration
- Missed follow-up commitments
- Deal stage regression
- Negative sentiment in notes
- Support ticket escalations

**Acceptance Criteria:**
- Weighted risk score (0-100 scale)
- Explains contributing factors
- Ranks accounts by risk descending
- Surfaces top 10 at-risk accounts per owner

### 3.3 Historical Context Retrieval

#### FR-3.3.1: Memory Layer Integration
**Priority**: High
**Description**: System shall query Cognee knowledge graph for account context

**Acceptance Criteria:**
- Connects to Cognee MCP server
- Retrieves account timeline (meetings, notes, commitments)
- Pulls related entities (contacts, deals, tasks)
- Returns context within 5 seconds per account

#### FR-3.3.2: Key Event Extraction
**Priority**: Medium
**Description**: System shall identify significant events in account history

**Key Events:**
- Contract renewals/expirations
- Executive meetings
- Product adoption milestones
- Escalations or support issues
- Previous commitments made

**Acceptance Criteria:**
- Extracts events from Cognee knowledge graph
- Ranks events by significance to current context
- Timestamps events chronologically
- Links events to source documents

#### FR-3.3.3: Sentiment Trend Analysis
**Priority**: Low
**Description**: System shall track sentiment trends across account interactions

**Acceptance Criteria:**
- Analyzes sentiment in notes and meeting summaries
- Tracks sentiment over time (positive/neutral/negative)
- Identifies sentiment shifts (improving/declining)
- Includes sentiment in risk assessment

#### FR-3.3.4: Commitment Tracking
**Priority**: Medium
**Description**: System shall track follow-up commitments and completion status

**Acceptance Criteria:**
- Identifies commitments in historical notes
- Tracks commitment due dates
- Flags overdue commitments
- Surfaces unfulfilled commitments in briefs

### 3.4 Recommendation Generation

#### FR-3.4.1: Action Recommendation Templates
**Priority**: High
**Description**: System shall generate structured recommendations using templates

**Recommendation Types:**
- Follow-up email draft
- Task creation suggestion
- Meeting scheduling prompt
- Escalation alert
- Account health check

**Acceptance Criteria:**
- Populates template fields from account context
- Includes rationale for recommendation
- Provides confidence score (0-100)
- Cites supporting data references

#### FR-3.4.2: Recommendation Prioritization
**Priority**: High
**Description**: System shall rank recommendations by urgency and impact

**Prioritization Factors:**
- Account risk score
- Revenue opportunity
- Time sensitivity
- Effort required
- Historical response effectiveness

**Acceptance Criteria:**
- Assigns priority level (Critical/High/Medium/Low)
- Sorts recommendations by priority descending
- Explains prioritization rationale
- Surfaces top 3 actions per account

#### FR-3.4.3: Draft Communication Generation
**Priority**: Medium
**Description**: System shall generate draft emails and messages

**Acceptance Criteria:**
- Generates context-aware email drafts
- Includes subject line and body
- References specific account history
- Maintains professional tone
- Requires human review before sending

#### FR-3.4.4: Confidence Scoring
**Priority**: Medium
**Description**: System shall assess confidence level for each recommendation

**Confidence Factors:**
- Data completeness
- Pattern match to successful past actions
- Recency of supporting data
- Ambiguity in context

**Acceptance Criteria:**
- Numeric confidence score (0-100)
- Textual confidence level (High/Medium/Low)
- Explanation of confidence assessment
- Flags low-confidence items for review

### 3.5 Human-in-the-Loop Approval

#### FR-3.5.1: Approval Workflow Interface
**Priority**: High
**Description**: System shall present recommendations for human approval before execution

**Acceptance Criteria:**
- Displays recommendation with context
- Provides approve/adjust/reject options
- Allows inline editing of drafts
- Captures approval timestamp and user

#### FR-3.5.2: CRM Write Protection
**Priority**: High
**Description**: System shall gate all CRM write operations through approval

**Protected Operations:**
- Account field updates
- Task creation
- Note creation
- Deal stage changes
- Owner reassignments

**Acceptance Criteria:**
- Blocks direct CRM writes without approval
- Prompts for approval before execution
- Logs approval decisions
- Supports batch approval for multiple actions

#### FR-3.5.3: Notification Gating
**Priority**: High
**Description**: System shall require approval before sending owner notifications

**Acceptance Criteria:**
- Previews notification content
- Identifies recipients
- Requires explicit send approval
- Logs notification delivery

#### FR-3.5.4: Feedback Capture
**Priority**: Medium
**Description**: System shall capture user feedback on recommendations

**Feedback Types:**
- Acceptance (approved as-is)
- Adjustment (modified before approval)
- Rejection (declined with reason)
- Deferral (postponed to later)

**Acceptance Criteria:**
- Records feedback type and timestamp
- Captures rejection reasons
- Stores modified versions
- Uses feedback to improve future recommendations

### 3.6 Logging & Audit Trail

#### FR-3.6.1: Operation Logging
**Priority**: High
**Description**: System shall log all operations with sufficient detail for audit

**Logged Events:**
- Review execution (start/end/status)
- Data retrieval (source/timestamp/records)
- Recommendation generation (input/output/confidence)
- Approval decisions (user/timestamp/action)
- CRM modifications (field/old/new/user)

**Acceptance Criteria:**
- Structured log format (JSON)
- Immutable log storage
- Searchable by account/user/date
- Retained per compliance policy

#### FR-3.6.2: Source Data References
**Priority**: High
**Description**: System shall cite source data for all claims and recommendations

**Acceptance Criteria:**
- Links to source CRM records
- Timestamps data retrieval
- Preserves data snapshots for audit
- Supports drill-down to raw data

#### FR-3.6.3: Tool Usage Recording
**Priority**: Medium
**Description**: System shall record all MCP tool invocations

**Acceptance Criteria:**
- Logs tool name and parameters
- Records response data
- Tracks latency and errors
- Associates tools with subagent

#### FR-3.6.4: Decision Audit Trail
**Priority**: High
**Description**: System shall maintain trail of recommendations vs. actions taken

**Acceptance Criteria:**
- Links recommendations to approvals
- Tracks execution of approved actions
- Records deviations from recommendations
- Supports compliance reporting

---

## 4. Non-Functional Requirements

### 4.1 Security Requirements

#### NFR-4.1.1: Credential Management
**Priority**: Critical
**Description**: System shall store and access credentials securely

**Requirements:**
- Integration with secrets manager (AWS Secrets Manager/HashiCorp Vault)
- No plaintext credentials in code or logs
- Credential rotation support
- Separate credentials for staging/production

**Validation:**
- Security audit passes
- No credentials in version control
- Automated rotation succeeds
- Staging/production isolation verified

#### NFR-4.1.2: Data Encryption
**Priority**: Critical
**Description**: System shall encrypt sensitive data at rest and in transit

**Requirements:**
- TLS 1.3 for all API communications
- AES-256 encryption for stored memory
- Encrypted log storage
- Encrypted backup files

**Validation:**
- SSL Labs A+ rating
- Encryption verification tests pass
- Compliance audit confirms encryption

#### NFR-4.1.3: Access Control
**Priority**: Critical
**Description**: System shall enforce least privilege access

**Requirements:**
- Zoho OAuth scopes limited to required modules
- Subagent tool permissions deny-by-default
- Role-based access for admin functions
- Audit log access restricted

**Validation:**
- Scope enumeration matches requirements
- Unauthorized tool usage blocked
- Role-based tests pass
- Access violations logged

#### NFR-4.1.4: Sensitive Data Redaction
**Priority**: High
**Description**: System shall redact sensitive fields from logs and outputs

**Sensitive Fields:**
- Social Security Numbers
- Credit card numbers
- Personal health information
- Financial account numbers

**Requirements:**
- Pattern-based redaction in logs
- Configurable redaction rules
- Audit trail of redactions
- Preserves data for authorized access

**Validation:**
- Redaction tests for all sensitive patterns
- Log review confirms no leakage
- Compliance review passes

#### NFR-4.1.5: Compliance Adherence
**Priority**: Critical
**Description**: System shall comply with Sergas data policies

**Requirements:**
- GDPR compliance for EU accounts
- SOC2 audit controls
- Data residency requirements
- Retention policy enforcement

**Validation:**
- Compliance audit passes
- Data residency verified
- Retention policy tests pass

### 4.2 Scalability Requirements

#### NFR-4.2.1: Account Volume
**Priority**: High
**Description**: System shall handle up to 5,000 accounts without manual tuning

**Requirements:**
- Supports 5,000 accounts
- Serves 50 account owners
- Processes 500 accounts per hour
- Handles 10,000 Zoho API calls per day

**Validation:**
- Load testing with 5,000 accounts succeeds
- Performance acceptable at scale
- No resource exhaustion
- Monitoring shows healthy metrics

#### NFR-4.2.2: Horizontal Scaling
**Priority**: Medium
**Description**: System shall support horizontal scaling for increased load

**Requirements:**
- Stateless orchestrator design
- Distributed task queue
- Shared memory layer
- Load balancing capable

**Validation:**
- Multiple orchestrator instances run concurrently
- Work distributes across instances
- No race conditions
- Linear scaling observed

#### NFR-4.2.3: Data Growth
**Priority**: Medium
**Description**: System shall handle growing knowledge base efficiently

**Requirements:**
- Cognee supports 1M+ document chunks
- Query performance <5 seconds at scale
- Efficient incremental updates
- Archival strategy for old data

**Validation:**
- Performance testing with 1M chunks
- Query latency within limits
- Update efficiency measured
- Archival process tested

### 4.3 Performance Requirements

#### NFR-4.3.1: Review Latency
**Priority**: High
**Description**: System shall complete owner brief within 10 minutes of scheduled run

**Requirements:**
- Owner brief generation: <10 minutes
- Single account analysis: <30 seconds
- Cognee query: <5 seconds per account
- Zoho API calls: <2 seconds per call

**Validation:**
- Performance testing confirms targets
- Monitoring tracks latency percentiles
- Alerts trigger on degradation

#### NFR-4.3.2: API Response Time
**Priority**: High
**Description**: System shall minimize API latency through optimization

**Requirements:**
- Caching of static metadata
- Batch API calls where possible
- Connection pooling
- Retry with exponential backoff

**Validation:**
- P95 latency <3 seconds
- Cache hit rate >70%
- Batch efficiency measured
- Retry logic tested

#### NFR-4.3.3: Resource Efficiency
**Priority**: Medium
**Description**: System shall optimize resource usage

**Requirements:**
- Memory usage <4GB per orchestrator instance
- CPU usage <60% average
- Token usage optimized via context management
- Storage growth <10GB per month

**Validation:**
- Resource monitoring within limits
- Token usage reports reviewed
- Storage growth tracked

#### NFR-4.3.4: Bulk Operation Performance
**Priority**: High
**Description**: Bulk operations SHALL utilize Zoho Python SDK for optimal performance

**Requirements:**
- Bulk read operations: 100 records per API call (vs. individual REST calls)
- Cognee nightly sync: 5,000 accounts in <15 minutes
- Background reconciliation: Process 1,000 records in <5 minutes
- Parallel operation support for multiple bulk operations

**Validation:**
- Performance benchmarks meet targets
- SDK bulk operations verified at 100 records/call
- Nightly sync duration monitored
- Parallel execution efficiency measured

### 4.4 Reliability Requirements

#### NFR-4.4.1: System Uptime
**Priority**: High
**Description**: System shall achieve 99% successful run rate

**Requirements:**
- Successful execution rate ≥99%
- Graceful degradation when dependencies unavailable
- Automatic recovery from transient failures
- Manual intervention only for critical failures

**Validation:**
- Uptime monitoring shows ≥99%
- Chaos engineering tests pass
- Recovery time measured
- Incident count tracked

#### NFR-4.4.2: Fault Tolerance
**Priority**: High
**Description**: System shall handle dependency failures gracefully

**Failure Scenarios:**
- Zoho CRM API unavailable
- Cognee memory layer unreachable
- MCP server timeout
- Network interruption

**Requirements:**
- Retry with exponential backoff (max 3 attempts)
- Fallback to cached data when available
- Partial results if some subagents fail
- Clear error messages for manual recovery

**Validation:**
- Fault injection tests pass
- Fallback behaviors verified
- Error messages actionable
- Recovery procedures documented

#### NFR-4.4.3: Data Consistency
**Priority**: High
**Description**: System shall maintain consistency between CRM and memory

**Requirements:**
- Eventual consistency acceptable (24-hour window)
- Detects and reports inconsistencies
- Reconciliation process available
- Audit trail for all changes

**Validation:**
- Consistency checks automated
- Reconciliation tested
- Audit trail complete

#### NFR-4.4.4: Idempotency
**Priority**: Medium
**Description**: System shall support safe retry of operations

**Requirements:**
- Review operations idempotent
- CRM writes use upsert semantics
- Duplicate detection for recommendations
- Transaction-like semantics where possible

**Validation:**
- Retry tests produce identical results
- No duplicate records created
- Transaction rollback tested

### 4.5 Observability Requirements

#### NFR-4.5.1: Metrics Collection
**Priority**: High
**Description**: System shall collect operational metrics

**Metrics:**
- Run success rate
- Latency percentiles (P50/P95/P99)
- Token usage per run
- API call volume and errors
- Recommendation acceptance rate
- User engagement metrics

**Requirements:**
- Metrics exported to monitoring system
- Real-time dashboards available
- Historical trend analysis
- Alerting on anomalies

**Validation:**
- Dashboard shows all key metrics
- Alerts fire on test conditions
- Historical data retained
- SLO tracking automated

#### NFR-4.5.2: Error Reporting
**Priority**: High
**Description**: System shall provide actionable error diagnostics

**Requirements:**
- Structured error messages
- Stack traces for exceptions
- Context captured (account, operation, state)
- Error aggregation and deduplication

**Validation:**
- Errors include actionable guidance
- Context sufficient for diagnosis
- Aggregation reduces noise
- Incident tracking integrated

#### NFR-4.5.3: Performance Tracing
**Priority**: Medium
**Description**: System shall support distributed tracing

**Requirements:**
- Trace ID propagated across subagents
- Span timing for each operation
- Critical path identification
- Bottleneck detection

**Validation:**
- Traces viewable in tracing UI
- Timing accurate
- Bottlenecks identified correctly

#### NFR-4.5.4: Audit Logging
**Priority**: Critical
**Description**: System shall maintain comprehensive audit logs

**Requirements:**
- All user actions logged
- All CRM modifications logged
- All approval decisions logged
- Logs immutable and searchable

**Validation:**
- Audit log completeness verified
- Tampering detection works
- Search performance acceptable
- Compliance review passes

---

## 5. Success Metrics

### 5.1 Adoption Metrics

#### SM-5.1.1: User Adoption Rate
**Target**: ≥80% of target reps review agent-generated briefs weekly
**Measurement**: Weekly active users / Total eligible users
**Frequency**: Weekly tracking
**Success Threshold**: 80% for 4 consecutive weeks

#### SM-5.1.2: Engagement Depth
**Target**: Average 3+ briefs reviewed per user per week
**Measurement**: Brief views per user per week
**Frequency**: Weekly tracking
**Success Threshold**: Maintained for 8 weeks post-launch

### 5.2 Effectiveness Metrics

#### SM-5.2.1: Recommendation Uptake
**Target**: ≥50% of suggested actions accepted or scheduled
**Measurement**: (Approved recommendations / Total recommendations) × 100
**Frequency**: Daily aggregation, weekly review
**Success Threshold**: 50% average over 30-day period

#### SM-5.2.2: Time Savings
**Target**: Average account review time <3 minutes (baseline >8 minutes)
**Measurement**: Median review duration per account
**Frequency**: Continuous tracking
**Success Threshold**: 62.5% reduction from baseline

#### SM-5.2.3: Risk Detection Accuracy
**Target**: 80% of flagged at-risk accounts require action
**Measurement**: True positives / Total flagged accounts
**Frequency**: Monthly validation
**Success Threshold**: 80% precision

### 5.3 Quality Metrics

#### SM-5.3.1: Data Accuracy
**Target**: <2% error rate in surfaced account status or owner assignments
**Measurement**: Errors reported / Total data points surfaced
**Frequency**: Weekly spot checks + user reports
**Success Threshold**: <2% sustained for 4 weeks

#### SM-5.3.2: Recommendation Quality
**Target**: <10% of recommendations rejected as inappropriate
**Measurement**: Rejected recommendations / Total recommendations
**Frequency**: Daily tracking
**Success Threshold**: <10% rejection rate

#### SM-5.3.3: Context Relevance
**Target**: ≥90% of historical context rated as relevant by users
**Measurement**: User feedback on context helpfulness
**Frequency**: Monthly survey
**Success Threshold**: 90% "helpful" or "very helpful" ratings

### 5.4 Reliability Metrics

#### SM-5.4.1: System Reliability
**Target**: 99% successful run rate across scheduled cycles
**Measurement**: Successful runs / Total scheduled runs
**Frequency**: Daily tracking
**Success Threshold**: 99% over 30-day rolling window

#### SM-5.4.2: Mean Time to Recovery
**Target**: <30 minutes MTTR for system failures
**Measurement**: Time from failure detection to restoration
**Frequency**: Per-incident tracking
**Success Threshold**: 95% of incidents <30 minutes

#### SM-5.4.3: API Availability
**Target**: 99.5% availability for Zoho and Cognee integrations
**Measurement**: Uptime monitoring of dependencies
**Frequency**: Continuous tracking
**Success Threshold**: 99.5% monthly availability

### 5.5 Efficiency Metrics

#### SM-5.5.1: Token Usage Efficiency
**Target**: <$0.10 per account review (Claude API costs)
**Measurement**: Total token costs / Accounts reviewed
**Frequency**: Daily aggregation
**Success Threshold**: Sustained below $0.10

#### SM-5.5.2: API Call Efficiency
**Target**: <20 Zoho API calls per account review
**Measurement**: API calls / Accounts reviewed
**Frequency**: Daily tracking
**Success Threshold**: <20 calls average

#### SM-5.5.3: Processing Throughput
**Target**: ≥500 accounts processed per hour
**Measurement**: Accounts completed / Execution time
**Frequency**: Per-run tracking
**Success Threshold**: 500 accounts/hour at scale

---

## 6. Use Cases & User Stories

### 6.1 Core Use Cases

#### UC-6.1.1: Daily Account Review

**Actor**: Account Executive
**Preconditions**:
- User has active Zoho CRM account
- User manages ≥10 accounts
- System has completed initial data sync
- Review schedule configured

**Main Flow**:
1. System executes scheduled daily review (5:00 AM)
2. Zoho Data Scout retrieves account updates for user's portfolio
3. Memory Analyst queries Cognee for historical context
4. Recommendation Author generates prioritized action list
5. Orchestrator compiles owner-specific brief
6. User receives brief notification (email/Slack)
7. User reviews brief in web interface or CLI
8. User approves/modifies/rejects recommendations
9. System logs decisions and executes approved actions
10. System updates memory with new context

**Postconditions**:
- Owner brief generated and delivered
- User reviews brief within 24 hours
- Approved actions executed in CRM
- Audit trail complete

**Exceptions**:
- **E1**: Zoho API unavailable → Use cached data, flag as stale
- **E2**: Cognee unreachable → Generate brief without historical context
- **E3**: No account changes → Brief indicates "no updates"
- **E4**: User doesn't review within 48 hours → Send reminder

**Acceptance Criteria**:
- Brief delivered within 10 minutes of scheduled time
- Contains all accounts with changes
- Prioritizes by risk score
- Requires <3 minutes to review
- Actions execute within 5 minutes of approval

---

#### UC-6.1.2: At-Risk Account Detection

**Actor**: Account Executive
**Preconditions**:
- Account inactive for >30 days
- No follow-up tasks scheduled
- Previous meeting commitments on record

**Main Flow**:
1. System detects account exceeds inactivity threshold
2. Memory Analyst retrieves last interaction and commitments
3. System calculates risk score based on signals
4. Recommendation Author generates alert with context
5. Alert surfaces in priority section of daily brief
6. User reviews account details and historical timeline
7. User approves suggested follow-up email draft
8. System creates follow-up task in CRM
9. System sends approved email to account contact
10. System updates memory with outreach details

**Postconditions**:
- At-risk account flagged
- Follow-up action taken within 24 hours
- Account moved to "re-engagement" status
- Outreach logged in CRM and memory

**Exceptions**:
- **E1**: Account closed but not marked → Flag for manual review
- **E2**: Contact no longer valid → Suggest owner reassignment
- **E3**: User rejects recommendation → Capture reason, learn pattern

**Acceptance Criteria**:
- Risk score >70 surfaces in priority list
- Historical context includes last 3 interactions
- Email draft references specific past commitments
- Follow-up task auto-created upon approval
- Memory updated within 1 minute

---

#### UC-6.1.3: Deal Stage Change Response

**Actor**: Account Executive
**Preconditions**:
- Deal progressed to "Contract Review" stage
- Previous stage was "Proposal Sent"
- Stage change occurred within last 24 hours

**Main Flow**:
1. Zoho Data Scout detects deal stage advancement
2. Memory Analyst retrieves proposal details and timeline
3. Recommendation Author suggests next actions:
   - Schedule contract review call
   - Prepare contract documentation
   - Update forecast in CRM
4. System generates brief section with deal update
5. User reviews deal details and suggestions
6. User approves task creation and scheduling
7. System creates tasks in CRM with due dates
8. System updates deal notes with action plan
9. System stores decision pattern for future deals

**Postconditions**:
- Deal stage change acknowledged
- Next-step tasks created
- Forecast updated
- Deal notes current

**Exceptions**:
- **E1**: Stage regressed (moved backward) → Flag as high priority alert
- **E2**: Deal stalled in stage >30 days → Suggest escalation
- **E3**: Contract review overdue → Highlight in critical section

**Acceptance Criteria**:
- Stage change detected within 1 hour
- Suggestions align with sales process
- Tasks include realistic due dates
- Notes include stage progression timeline

---

### 6.2 User Stories

#### Epic: Account Monitoring

**US-6.2.1**: As an Account Executive, I want to receive a daily digest of account changes so I can prioritize my follow-ups efficiently.

**Acceptance Criteria**:
- Digest delivered by 6:00 AM local time
- Includes all accounts with changes in last 24 hours
- Sorted by priority (risk score descending)
- Contains max 3 recommended actions per account
- Indicates time required to review (<3 min target)

**Definition of Done**:
- Digest generated successfully for 10 test users
- Delivery within SLA 99% of runs
- User survey shows 80% find digest helpful
- Time tracking confirms <3 min average review time

---

**US-6.2.2**: As an Account Executive, I want to see historical context for each account so I understand the relationship trajectory.

**Acceptance Criteria**:
- Timeline view shows last 6 months of activity
- Includes meetings, notes, deal changes, support tickets
- Highlights key events (renewals, escalations, wins)
- Links to source documents in CRM
- Loads in <5 seconds

**Definition of Done**:
- Timeline retrieval succeeds for all test accounts
- Accuracy validated against CRM data
- Performance meets <5 second target
- Users rate context as "relevant" (90%+ in survey)

---

**US-6.2.3**: As an Account Executive, I want the system to flag at-risk accounts so I can intervene proactively.

**Acceptance Criteria**:
- Risk score computed from multiple signals
- Accounts >70 risk score highlighted in digest
- Includes explanation of risk factors
- Suggests specific remediation actions
- Updates risk score after intervention

**Definition of Done**:
- Risk scoring algorithm validated with historical data
- Precision ≥80% (true positives)
- Risk factors clearly explained in UI
- Interventions tracked and correlated with outcomes

---

#### Epic: Recommendation Generation

**US-6.2.4**: As an Account Executive, I want the system to draft follow-up emails so I save time on routine outreach.

**Acceptance Criteria**:
- Email draft includes subject and body
- References specific account history
- Maintains professional tone
- Requires human review before sending
- Supports inline editing before approval

**Definition of Done**:
- Email generation tested with 50 accounts
- Tone validated by sales leadership
- Editing interface functional
- Send approval workflow complete
- Acceptance rate ≥60% (minimal edits)

---

**US-6.2.5**: As an Account Executive, I want recommendations prioritized by urgency and impact so I focus on what matters most.

**Acceptance Criteria**:
- Recommendations tagged as Critical/High/Medium/Low
- Sorting by priority descending
- Priority rationale explained
- Top 3 actions per account highlighted
- Deferral option for lower priority items

**Definition of Done**:
- Prioritization algorithm tested with historical data
- User feedback confirms priority accuracy (80%+ agreement)
- Deferral workflow functional
- Deferred items resurface appropriately

---

#### Epic: Approval & Control

**US-6.2.6**: As an Account Executive, I want to approve/reject recommendations before CRM changes so I maintain control.

**Acceptance Criteria**:
- All CRM write operations gated by approval
- Approval interface shows before/after state
- Reject option includes reason capture
- Adjust option allows inline modification
- Batch approval for multiple actions

**Definition of Done**:
- Approval workflow blocks writes until confirmed
- Interface tested with 20 test users
- Reason capture functional
- Batch approval tested with 10+ items
- Audit log complete for all decisions

---

**US-6.2.7**: As a Sales Manager, I want to see team-wide recommendation acceptance rates so I understand system adoption.

**Acceptance Criteria**:
- Dashboard shows acceptance rate per team member
- Aggregated metrics for team
- Trend over time (last 30 days)
- Breakdown by recommendation type
- Exportable report

**Definition of Done**:
- Dashboard tested with sample data
- Metrics accurate against audit logs
- Export format validated with manager
- Refresh interval <5 minutes

---

#### Epic: Compliance & Audit

**US-6.2.8**: As an Operations Admin, I want comprehensive audit logs so I can demonstrate compliance.

**Acceptance Criteria**:
- All system actions logged immutably
- Logs include user, timestamp, action, result
- Searchable by account/user/date range
- Exportable for compliance reports
- Retained per policy (default 7 years)

**Definition of Done**:
- Logging tested for all action types
- Search performance <2 seconds
- Export format meets compliance requirements
- Retention policy automated
- Audit log completeness validated

---

**US-6.2.9**: As an Operations Admin, I want granular permission controls so I enforce least privilege.

**Acceptance Criteria**:
- Tool permissions configurable per subagent
- Deny-by-default permission model
- Override capability for admin emergencies
- Permission changes logged
- Permission violation alerts

**Definition of Done**:
- Permission system tested with all subagents
- Violations blocked and logged
- Admin override functional
- Configuration interface validated
- Security review passed

---

## 7. System Boundaries & Constraints

### 7.1 System Boundaries

#### 7.1.1 In-Scope Systems
- Zoho CRM (Accounts, Contacts, Deals, Notes, Tasks, Activities modules)
- Cognee knowledge graph memory layer
- Claude Agent SDK orchestration
- MCP servers (Zoho, Cognee, analytics)
- Secrets management system
- Monitoring and observability platform

#### 7.1.2 Out-of-Scope Systems (Phase 1)
- Email/calendar APIs (future integration)
- BI dashboards (read-only access if needed)
- Support ticketing systems (future integration)
- Document management systems (future integration)
- Real-time notification systems (future)
- Mobile applications (future)

#### 7.1.3 Integration Boundaries
- **Zoho CRM**: Read/write via MCP endpoint + REST API fallback
- **Cognee**: Read/write via MCP endpoint
- **Secrets**: Read-only via secrets manager API
- **Monitoring**: Write-only metrics and logs
- **Email**: Outbound only via SMTP (future)

### 7.2 Technical Constraints

#### 7.2.1 Platform Constraints
- **Runtime**: Python 3.14 required for Claude Agent SDK
- **Dependencies**: Claude Agent SDK, Cognee SDK, MCP client libraries
- **Deployment**: Linux-based container environment
- **Execution**: Single-tenant deployment per customer

#### 7.2.2 API Constraints
- **Zoho Rate Limits**: 200 calls/day (free tier), 1,500-5,000/day (paid)
- **Claude Token Limits**: 200K tokens per request (Sonnet 4)
- **MCP Timeout**: 30 seconds default per tool invocation
- **Cognee Query**: 5 second target, 10 second max

#### 7.2.3 Data Constraints
- **Account Volume**: 5,000 accounts maximum (Phase 1)
- **Owner Count**: 50 account owners maximum
- **Memory Size**: 1M document chunks in Cognee
- **Log Retention**: 7 years (compliance requirement)
- **Backup Frequency**: Daily incremental, weekly full

#### 7.2.4 Performance Constraints
- **Review Latency**: 10 minutes max for full owner brief
- **Account Analysis**: 30 seconds max per account
- **Memory Query**: 5 seconds target per account
- **Approval Wait**: No timeout (human-in-the-loop)

### 7.3 Business Constraints

#### 7.3.1 Timeline Constraints
- **Phase 1 (Foundation)**: 6 weeks from kickoff
- **Phase 2 (Pilot)**: 4 weeks after Phase 1
- **Phase 3 (Production)**: 4 weeks after successful pilot
- **Total**: 14 weeks to production

#### 7.3.2 Resource Constraints
- **Team Size**: 3 engineers (backend, AI/ML, DevOps)
- **Budget**: TBD (include API costs, infrastructure, tooling)
- **Compute**: Container-based, auto-scaling to 10 instances max
- **Storage**: 1TB initial allocation

#### 7.3.3 Compliance Constraints
- **Data Residency**: US-based hosting for Sergas data
- **Certifications**: SOC2 Type II required
- **GDPR**: Compliance required for EU accounts
- **Audit**: Quarterly compliance audits
- **Retention**: 7-year retention for audit logs

### 7.4 Operational Constraints

#### 7.4.1 Availability Constraints
- **Uptime Target**: 99% successful execution rate
- **Maintenance Window**: Sundays 2:00-4:00 AM PST
- **Downtime Tolerance**: <1 hour per month
- **Disaster Recovery**: 24-hour RTO, 4-hour RPO

#### 7.4.2 Security Constraints
- **Authentication**: OAuth2 for Zoho, API keys for MCP
- **Authorization**: Role-based access control (RBAC)
- **Encryption**: TLS 1.3 in transit, AES-256 at rest
- **Secrets**: Managed secrets service (no plaintext)

#### 7.4.3 Support Constraints
- **Business Hours**: 9 AM - 5 PM PST, M-F
- **Response Time**: 4 hours for critical issues
- **Escalation**: On-call engineer for P0 incidents
- **Documentation**: Runbooks for all operational procedures

---

## 8. Integration Requirements

### 8.1 Zoho CRM Integration

#### IR-8.1.1: Zoho MCP Endpoint Integration
**Priority**: Critical
**Description**: Integrate with provisioned Zoho MCP endpoint for primary CRM access

**Requirements**:
- Configure Claude to use remote MCP: `npx mcp-remote https://zoho-mcp2-900114980.zohomcp.com/...`
- Enumerate all available tools at initialization
- Validate required tools present (contact search, deal read, account read, notes CRUD)
- Implement tool usage logging
- Handle MCP timeout (30s) with retry logic

**Required Tools**:
- `search_contacts`: Query contacts by criteria
- `create_contact`: Add new contact records
- `update_contact`: Modify contact fields
- `search_deals`: Query deals by status, owner, date
- `create_deal`: Create new deal records
- `list_deals`: Retrieve deal lists
- `get_user_info`: Fetch user/owner metadata
- `read_account`: Retrieve account details
- `update_account`: Modify account fields
- `create_note`: Add notes to records
- `read_notes`: Retrieve notes by record

**Acceptance Criteria**:
- MCP endpoint connection succeeds
- All required tools enumerate successfully
- Test invocation of each tool succeeds
- Timeout handling tested with 35s mock delay
- Logging captures tool name, params, response, latency

**Phase**: Foundation (Week 1-2)

---

#### IR-8.1.2: Zoho REST API Fallback
**Priority**: High
**Description**: Implement direct Zoho REST API client for operations not in MCP

**Requirements**:
- OAuth2 Server-based Applications flow
- API version V6+ endpoints
- Modules: Accounts, Contacts, Deals, Notes, Activities, Tasks
- Scopes: `ZohoCRM.modules.ALL`, `ZohoCRM.users.READ`, `ZohoCRM.notifications.READ`
- Rate limit tracking and backoff
- Batch operations for bulk reads

**Key Endpoints**:
- `GET /crm/v6/Accounts` - List accounts with filters
- `GET /crm/v6/Accounts/{id}` - Retrieve account details
- `PUT /crm/v6/Accounts/{id}` - Update account fields
- `POST /crm/v6/coql` - COQL query for complex filters
- `GET /crm/v6/Notes` - Retrieve notes by module/record
- `POST /crm/v6/Notes` - Create notes
- `GET /crm/v6/users` - Fetch user/owner list

**Acceptance Criteria**:
- OAuth2 flow completes successfully
- All endpoints tested with sample data
- Rate limit tracking functional (200/day free tier)
- Batch read retrieves 100 records in single call
- Error handling for 401, 429, 500 responses

**Phase**: Foundation (Week 2-3)

---

#### IR-8.1.3: Zoho Change Detection
**Priority**: High
**Description**: Detect account/deal changes since last review

**Approach**:
- **Option 1**: Use Zoho Notification API (webhooks) for real-time changes
- **Option 2**: Scheduled diff via `Modified_Time` field filter

**Requirements**:
- Query accounts modified since last review timestamp
- COQL query: `SELECT * FROM Accounts WHERE Modified_Time > '2025-01-01T00:00:00Z' AND Owner = '{user_id}'`
- Store last review timestamp per account in memory
- Detect field-level changes (compare snapshots)
- Surface changed fields in brief

**Acceptance Criteria**:
- Change detection identifies all modified accounts
- Field-level diff accurate (old vs. new values)
- Performance <2 seconds for 100 accounts
- Last review timestamp persists across runs
- Zero false positives in test data

**Phase**: Agent Orchestration (Week 3-4)

---

#### IR-8.1.4: Zoho Write Operations with Approval
**Priority**: Critical
**Description**: Gate all Zoho CRM write operations through approval workflow

**Protected Operations**:
- Account field updates (`PUT /crm/v6/Accounts/{id}`)
- Deal stage changes (`PUT /crm/v6/Deals/{id}`)
- Task creation (`POST /crm/v6/Tasks`)
- Note creation (`POST /crm/v6/Notes`)
- Contact updates (`PUT /crm/v6/Contacts/{id}`)

**Requirements**:
- Implement `PreToolUse` hook to intercept writes
- Present operation details to user (before/after state)
- Capture approval decision (approve/adjust/reject)
- Log decision with timestamp and user
- Execute write only after approval
- Rollback capability for failed writes

**Acceptance Criteria**:
- All write operations blocked without approval
- Approval prompt shows clear before/after comparison
- User can modify parameters before approval
- Rejection reason captured
- Approved writes execute successfully
- Failed writes logged with error details

**Phase**: Agent Orchestration (Week 4-5)

---

#### 8.2 Zoho Python SDK Integration

**FR-8.2.1**: System SHALL integrate official Zoho Python SDK v8 (`zohocrmsdk8-0`) as secondary integration tier for bulk operations and background jobs.

**FR-8.2.2**: SDK client SHALL implement database-backed token persistence with automatic refresh.

**FR-8.2.3**: ZohoIntegrationManager SHALL route operations to optimal tier:
- Agent-driven operations → Zoho MCP (primary)
- Bulk operations (>50 records) → Zoho Python SDK (secondary)
- Fallback → REST API (tertiary)

**FR-8.2.4**: SDK SHALL be used for:
- Nightly Cognee sync (5,000 accounts bulk ingestion)
- File upload/download operations
- Custom module access not available via MCP
- Background data reconciliation jobs

**FR-8.2.5**: System SHALL maintain separate OAuth clients for MCP and SDK integrations.

**Acceptance Criteria**:
- Zoho Python SDK v8 installed and configured
- Database token persistence operational
- ZohoIntegrationManager routing verified in tests
- Bulk operations use SDK (100 records/call)
- Separate OAuth credentials for MCP and SDK
- Token refresh automation functional

**Phase**: Foundation (Week 2-4)

---

### 8.3 Cognee Memory Integration

#### IR-8.2.1: Cognee MCP Server Setup
**Priority**: High
**Description**: Deploy and configure Cognee MCP server for memory access

**Requirements**:
- Deploy Cognee instance (self-hosted or managed)
- Create MCP server wrapping Cognee SDK
- Implement MCP tools: `add_context`, `search_context`, `get_timeline`, `upsert_account`
- Configure workspace isolation per customer
- Set up authentication (API key or OAuth)
- Define data ingestion pipeline

**MCP Tools**:
- `add_context(content, metadata)`: Ingest document/note into Cognee
- `search_context(query, filters)`: Semantic search across memory
- `get_timeline(account_id, start_date, end_date)`: Retrieve account history
- `upsert_account(account_id, snapshot)`: Store current account state

**Acceptance Criteria**:
- MCP server deploys successfully
- All tools callable from Claude agent
- Workspace isolation verified (no cross-customer leakage)
- Authentication functional
- Performance <5 seconds per search query

**Phase**: Foundation (Week 2-3)

---

#### IR-8.2.2: Historical Data Ingestion
**Priority**: High
**Description**: Ingest Zoho CRM historical data into Cognee

**Data Sources**:
- Account records (all fields, owner, status)
- Deal records (stage, value, timeline)
- Notes (activity history, meeting summaries)
- Tasks (completed, overdue)
- Custom fields (health score, segment, etc.)

**Ingestion Process**:
1. Export data from Zoho via Bulk Read API
2. Normalize and enrich (map IDs to names, compute metrics)
3. Chunk documents for Cognee ingestion
4. Add metadata (account_id, owner, date, type)
5. Ingest via Cognee SDK or MCP tool
6. Validate ingestion (spot check retrieval)

**Requirements**:
- Handles up to 5,000 accounts × 2 years history
- Ingestion performance ~1GB in 40 minutes
- Deduplication of identical records
- Entity extraction (accounts, contacts, deals)
- Relationship mapping (account→contacts→deals)

**Acceptance Criteria**:
- All test account history ingested successfully
- Retrieval returns expected records
- No duplicate records (verified with checksums)
- Entity relationships correct
- Performance within targets

**Phase**: Foundation (Week 3-4)

---

#### IR-8.2.3: Incremental Memory Updates
**Priority**: Medium
**Description**: Sync new Zoho changes to Cognee incrementally

**Approaches**:
- **Scheduled Sync**: Nightly batch job pulling last 24 hours of changes
- **Event-Driven**: Zoho webhook triggers Cognee upsert
- **Hybrid**: Nightly sync + on-demand refresh for recent accounts

**Requirements**:
- Detects new/modified records in Zoho
- Upserts changes to Cognee (add or update)
- Handles deletions (soft delete or archival)
- Monitors sync lag (should be <24 hours)
- Alerts on sync failures

**Acceptance Criteria**:
- Sync completes within 2 hours for daily changes
- Modified records reflected in Cognee within 24 hours
- Deletion handling tested (archived, not lost)
- Sync lag monitoring functional
- Failure alerts trigger correctly

**Phase**: Pilot Experience (Week 7-8)

---

#### IR-8.2.4: Memory Query Optimization
**Priority**: Medium
**Description**: Optimize Cognee queries for sub-5-second performance

**Optimization Strategies**:
- Index frequently queried fields (account_id, owner, date)
- Cache recent query results (TTL 1 hour)
- Pre-aggregate common patterns (last 6 months timeline)
- Limit result size (top 20 events)
- Parallelize multiple queries

**Requirements**:
- Query latency P95 <5 seconds
- Cache hit rate >70%
- Parallel query speedup 2-3x
- Result relevance maintained (no quality degradation)

**Acceptance Criteria**:
- Performance testing confirms <5s P95
- Cache metrics show >70% hit rate
- Parallel queries tested with 5 concurrent requests
- User feedback confirms result quality

**Phase**: Production Hardening (Week 9-10)

---

### 8.3 Secrets Management Integration

#### IR-8.3.1: Secrets Manager Setup
**Priority**: Critical
**Description**: Integrate with secrets manager for credential storage

**Supported Services**:
- AWS Secrets Manager (preferred)
- HashiCorp Vault
- Azure Key Vault

**Secrets to Store**:
- Zoho OAuth client ID and secret
- Zoho access and refresh tokens
- Cognee API key
- MCP endpoint authentication tokens
- SMTP credentials (future)

**Requirements**:
- Secrets retrieved at runtime (never hardcoded)
- Automatic refresh for expiring secrets (OAuth tokens)
- Separate secrets for staging/production
- Audit log of secret access
- Emergency secret rotation capability

**Acceptance Criteria**:
- All secrets stored in manager (zero plaintext)
- Application retrieves secrets successfully
- Token refresh automated (tested with expired token)
- Staging/production isolation verified
- Rotation tested without downtime

**Phase**: Foundation (Week 1-2)

---

### 8.4 Monitoring & Observability Integration

#### IR-8.4.1: Metrics Exporter
**Priority**: High
**Description**: Export operational metrics to monitoring platform

**Metrics to Export**:
- Run success rate (%)
- Latency percentiles (P50, P95, P99) - seconds
- Token usage per run - integer
- API call volume per endpoint - integer
- Error rate by type - percentage
- Recommendation acceptance rate - percentage
- User engagement (briefs viewed) - count

**Target Platform**:
- Prometheus + Grafana (preferred)
- Datadog
- CloudWatch

**Requirements**:
- Metrics endpoint exposed (/metrics)
- Metrics updated real-time (<1 minute lag)
- Historical retention 90 days
- Dashboards for key metrics
- Alerting rules configured

**Acceptance Criteria**:
- Metrics endpoint accessible
- All key metrics present
- Dashboard displays live data
- Historical data retained 90 days
- Alerts fire on test conditions

**Phase**: Agent Orchestration (Week 4-5)

---

#### IR-8.4.2: Structured Logging
**Priority**: High
**Description**: Implement structured logging for observability

**Log Levels**:
- ERROR: System failures, exceptions
- WARN: Degraded performance, retries
- INFO: Operational events (run start/end)
- DEBUG: Detailed execution traces

**Log Format**:
```json
{
  "timestamp": "2025-10-18T12:00:00Z",
  "level": "INFO",
  "message": "Account review completed",
  "context": {
    "account_id": "12345",
    "owner": "user@sergas.com",
    "duration_seconds": 28,
    "recommendations_generated": 3,
    "trace_id": "abc-def-ghi"
  }
}
```

**Requirements**:
- JSON-formatted logs
- Trace ID propagation across subagents
- Sensitive data redaction
- Log aggregation to central platform
- Searchable and filterable

**Acceptance Criteria**:
- All logs in JSON format
- Trace ID present in all log entries
- No sensitive data in logs (verified)
- Logs searchable in platform
- Query performance <2 seconds

**Phase**: Agent Orchestration (Week 4-5)

---

#### IR-8.4.3: Distributed Tracing
**Priority**: Medium
**Description**: Implement distributed tracing for performance analysis

**Tracing Platform**:
- Jaeger (preferred)
- Zipkin
- Datadog APM

**Spans to Trace**:
- Full review execution (root span)
- Subagent invocations (child spans)
- MCP tool calls (child spans)
- Database/API calls (child spans)

**Requirements**:
- Trace ID generated per review run
- Trace ID propagated to all subagents
- Span timing accurate to millisecond
- Critical path identification
- Trace retention 30 days

**Acceptance Criteria**:
- Traces viewable in UI
- All spans present with accurate timing
- Critical path correctly identified
- Trace retention verified
- Performance bottlenecks detectable

**Phase**: Production Hardening (Week 10-11)

---

## 9. Data Model Specification

### 9.1 Core Entities

#### 9.1.1 Account

**Source**: Zoho CRM Accounts module
**Purpose**: Represents customer organization

**Attributes**:
```yaml
Account:
  id: string (UUID, primary key)
  zoho_account_id: string (Zoho record ID, unique)
  account_name: string (required)
  owner_id: string (Zoho user ID)
  owner_name: string (computed)
  status: enum [Active, Inactive, At-Risk, Churned]
  health_score: integer (0-100, computed)
  annual_revenue: decimal (ARR/contract value)
  industry: string
  account_segment: enum [Enterprise, Mid-Market, SMB]
  created_date: timestamp
  modified_date: timestamp
  last_activity_date: timestamp
  inactivity_days: integer (computed)
  risk_score: integer (0-100, computed)

relationships:
  has_many: Deals
  has_many: Contacts
  has_many: Notes
  has_many: Tasks
  belongs_to: Owner (User)
```

**Computed Fields**:
- `health_score`: Weighted score from activity, deal stage, support tickets
- `inactivity_days`: Days since `last_activity_date`
- `risk_score`: Composite risk from inactivity, stalled deals, negative sentiment

---

#### 9.1.2 Deal

**Source**: Zoho CRM Deals module
**Purpose**: Represents sales opportunity

**Attributes**:
```yaml
Deal:
  id: string (UUID, primary key)
  zoho_deal_id: string (Zoho record ID, unique)
  deal_name: string (required)
  account_id: string (foreign key to Account)
  owner_id: string (Zoho user ID)
  stage: enum [Prospecting, Qualification, Proposal, Negotiation, Closed-Won, Closed-Lost]
  amount: decimal (deal value)
  close_date: date
  probability: integer (0-100)
  created_date: timestamp
  modified_date: timestamp
  stage_changed_date: timestamp
  days_in_stage: integer (computed)
  is_stalled: boolean (computed)

relationships:
  belongs_to: Account
  has_many: Notes
  has_many: Tasks
```

**Computed Fields**:
- `days_in_stage`: Days since `stage_changed_date`
- `is_stalled`: True if `days_in_stage` exceeds threshold for stage

---

#### 9.1.3 Contact

**Source**: Zoho CRM Contacts module
**Purpose**: Represents individual at customer organization

**Attributes**:
```yaml
Contact:
  id: string (UUID, primary key)
  zoho_contact_id: string (Zoho record ID, unique)
  first_name: string
  last_name: string
  email: string (required, validated)
  phone: string
  title: string
  account_id: string (foreign key to Account)
  is_primary: boolean (default false)
  created_date: timestamp
  modified_date: timestamp

relationships:
  belongs_to: Account
  has_many: Notes
```

---

#### 9.1.4 Note

**Source**: Zoho CRM Notes module
**Purpose**: Activity history, meeting summaries, system recommendations

**Attributes**:
```yaml
Note:
  id: string (UUID, primary key)
  zoho_note_id: string (Zoho record ID, unique, nullable)
  related_to_id: string (Account/Deal/Contact ID)
  related_to_type: enum [Account, Deal, Contact]
  title: string
  content: text (markdown supported)
  created_by: string (user ID or "system")
  created_date: timestamp
  note_type: enum [Meeting, Call, Email, System-Recommendation, System-Analysis]
  sentiment: enum [Positive, Neutral, Negative, Mixed] (computed for non-system notes)

relationships:
  belongs_to: Account | Deal | Contact (polymorphic)
```

**Note Types**:
- **Meeting/Call/Email**: User-entered activity notes
- **System-Recommendation**: AI-generated action suggestions
- **System-Analysis**: AI-generated account analysis

---

#### 9.1.5 Task

**Source**: Zoho CRM Tasks module
**Purpose**: Follow-up actions and commitments

**Attributes**:
```yaml
Task:
  id: string (UUID, primary key)
  zoho_task_id: string (Zoho record ID, unique)
  subject: string (required)
  description: text
  related_to_id: string (Account/Deal/Contact ID)
  related_to_type: enum [Account, Deal, Contact]
  owner_id: string (Zoho user ID)
  status: enum [Not-Started, In-Progress, Completed, Deferred]
  priority: enum [Low, Medium, High, Critical]
  due_date: date
  created_date: timestamp
  completed_date: timestamp (nullable)
  is_overdue: boolean (computed)
  created_by_system: boolean (default false)

relationships:
  belongs_to: Account | Deal | Contact (polymorphic)
  belongs_to: Owner (User)
```

**Computed Fields**:
- `is_overdue`: True if `status != Completed` and `due_date < today`

---

#### 9.1.6 Owner (User)

**Source**: Zoho CRM Users module
**Purpose**: Account executive or sales rep

**Attributes**:
```yaml
Owner:
  id: string (UUID, primary key)
  zoho_user_id: string (Zoho user ID, unique)
  email: string (required)
  full_name: string
  role: enum [Account-Executive, Sales-Manager, Admin]
  is_active: boolean (default true)
  portfolio_size: integer (computed: count of assigned accounts)

relationships:
  has_many: Accounts
  has_many: Deals
  has_many: Tasks
```

---

#### 9.1.7 Recommendation

**Source**: System-generated (stored in Cognee + Zoho Notes)
**Purpose**: AI-generated action suggestion

**Attributes**:
```yaml
Recommendation:
  id: string (UUID, primary key)
  account_id: string (foreign key to Account)
  generated_date: timestamp
  recommendation_type: enum [Follow-Up-Email, Task-Creation, Meeting-Schedule, Escalation, Health-Check]
  priority: enum [Critical, High, Medium, Low]
  title: string (brief description)
  rationale: text (explanation with supporting data)
  suggested_action: text (specific next step)
  confidence_score: integer (0-100)
  status: enum [Pending, Approved, Adjusted, Rejected, Executed]
  reviewed_by: string (user ID, nullable)
  reviewed_date: timestamp (nullable)
  executed_date: timestamp (nullable)
  feedback: text (user comments on recommendation, nullable)

relationships:
  belongs_to: Account
  references: supporting_data (array of Note/Deal/Task IDs)
```

---

#### 9.1.8 OwnerBrief

**Source**: System-generated (not stored in Zoho, ephemeral or in Cognee)
**Purpose**: Daily/weekly account digest per owner

**Attributes**:
```yaml
OwnerBrief:
  id: string (UUID, primary key)
  owner_id: string (foreign key to Owner)
  generated_date: timestamp
  period: enum [Daily, Weekly]
  accounts_reviewed: integer (count)
  accounts_with_changes: integer (count)
  high_priority_accounts: array[Account IDs]
  total_recommendations: integer (count)
  critical_recommendations: integer (count)
  estimated_review_time_minutes: integer
  status: enum [Generated, Delivered, Reviewed, Archived]
  reviewed_date: timestamp (nullable)

relationships:
  belongs_to: Owner
  has_many: Recommendations
```

---

### 9.2 Memory Layer Schema (Cognee)

#### 9.2.1 Account Snapshot

**Purpose**: Historical point-in-time account state for comparison

**Structure**:
```yaml
AccountSnapshot:
  account_id: string
  snapshot_date: timestamp
  account_data: json (full account record at time)
  deals_data: json (array of deal records)
  contacts_data: json (array of contact records)
  health_score: integer
  risk_score: integer
  last_activity: timestamp

stored_in: Cognee as enriched document chunk
indexed_by: [account_id, snapshot_date]
```

---

#### 9.2.2 Timeline Event

**Purpose**: Significant events in account history (meetings, milestones, escalations)

**Structure**:
```yaml
TimelineEvent:
  event_id: string (UUID)
  account_id: string
  event_date: timestamp
  event_type: enum [Meeting, Call, Email, Deal-Stage-Change, Contract-Renewal, Escalation, Product-Adoption, Support-Ticket]
  description: text (summary of event)
  participants: array[Contact IDs]
  sentiment: enum [Positive, Neutral, Negative]
  source_note_id: string (reference to Zoho Note, nullable)

stored_in: Cognee as entity with relationships
indexed_by: [account_id, event_date, event_type]
relationships: Account → TimelineEvent → Contacts
```

---

#### 9.2.3 Commitment

**Purpose**: Tracked promises made to customers (follow-ups, deliverables)

**Structure**:
```yaml
Commitment:
  commitment_id: string (UUID)
  account_id: string
  committed_date: timestamp
  due_date: date
  description: text
  committed_by: string (owner name)
  status: enum [Pending, Fulfilled, Overdue, Cancelled]
  fulfilled_date: timestamp (nullable)
  source_note_id: string (reference to Zoho Note)

stored_in: Cognee as entity
indexed_by: [account_id, due_date, status]
relationships: Account → Commitment
```

---

### 9.3 Data Relationships

#### 9.3.1 Entity Relationship Diagram

```
Owner (User)
  ├── has_many: Accounts
  ├── has_many: Deals
  └── has_many: Tasks

Account
  ├── belongs_to: Owner
  ├── has_many: Deals
  ├── has_many: Contacts
  ├── has_many: Notes
  ├── has_many: Tasks
  ├── has_many: Recommendations
  └── has_many: AccountSnapshots (in Cognee)

Deal
  ├── belongs_to: Account
  ├── belongs_to: Owner
  ├── has_many: Notes
  └── has_many: Tasks

Contact
  ├── belongs_to: Account
  └── has_many: Notes

Note
  └── belongs_to: Account | Deal | Contact (polymorphic)

Task
  ├── belongs_to: Account | Deal | Contact (polymorphic)
  └── belongs_to: Owner

Recommendation
  ├── belongs_to: Account
  └── references: supporting_data (Notes/Deals/Tasks)

OwnerBrief
  ├── belongs_to: Owner
  └── has_many: Recommendations

AccountSnapshot (Cognee)
  └── belongs_to: Account

TimelineEvent (Cognee)
  ├── belongs_to: Account
  └── has_many: Contacts (participants)

Commitment (Cognee)
  └── belongs_to: Account
```

---

### 9.4 Data Flow

#### 9.4.1 Data Ingestion Flow

```
Zoho CRM → Bulk Export API
           ↓
       Normalize & Enrich
           ↓
       Cognee Ingestion
           ↓
   Knowledge Graph Storage
           ↓
      Entity Extraction
           ↓
   Relationship Mapping
```

---

#### 9.4.2 Review Workflow Data Flow

```
1. Orchestrator triggers review
           ↓
2. Zoho Data Scout: Fetch current account state (via MCP/API)
           ↓
3. Compare with last snapshot (from Cognee)
           ↓
4. Detect changes → Store as ChangeDetection entity
           ↓
5. Memory Analyst: Query Cognee for timeline, commitments, sentiment
           ↓
6. Aggregate context → Store as ContextSummary entity
           ↓
7. Recommendation Author: Generate actions → Store as Recommendation entities
           ↓
8. Orchestrator: Compile OwnerBrief
           ↓
9. Present to user for approval
           ↓
10. Upon approval: Execute CRM writes, update Cognee, log audit trail
```

---

#### 9.4.3 Incremental Sync Flow

```
Daily/Event-Driven:
  Zoho Change → Notification/Poll
         ↓
    Fetch changed records
         ↓
    Create/Update AccountSnapshot
         ↓
    Update Cognee entities
         ↓
    Reindex for search
         ↓
    Log sync status
```

---

## 10. Acceptance Criteria

### 10.1 Feature Acceptance Criteria

#### AC-10.1.1: Account Review Execution

**Given**: System configured with 50 test accounts for user@sergas.com
**When**: Daily review scheduled for 5:00 AM PST
**Then**:
- [ ] Review executes automatically at scheduled time
- [ ] All 50 accounts processed within 10 minutes
- [ ] Owner brief generated with account changes
- [ ] Brief delivered via email by 5:15 AM PST
- [ ] Execution logged with success status
- [ ] Zero errors or exceptions

**Validation Method**: Automated test with scheduler + monitoring verification

---

#### AC-10.1.2: Change Detection Accuracy

**Given**: 10 test accounts with known field changes in last 24 hours
**When**: Review executes
**Then**:
- [ ] All 10 accounts identified as changed
- [ ] Changed fields correctly identified (name, stage, owner, etc.)
- [ ] Old and new values captured accurately
- [ ] Change timestamps within 1 minute of actual Zoho modification
- [ ] No false positives (unchanged accounts flagged)
- [ ] No false negatives (changed accounts missed)

**Validation Method**: Ground truth comparison with Zoho audit logs

---

#### AC-10.1.3: At-Risk Account Detection

**Given**: 5 accounts inactive for 31+ days, 3 with stalled deals, 2 with negative sentiment
**When**: Risk analysis executes
**Then**:
- [ ] All 5 inactive accounts flagged with risk score ≥70
- [ ] 3 stalled deals identified and included in risk calculation
- [ ] 2 negative sentiment accounts highlighted
- [ ] Risk factors explained in brief (e.g., "31 days inactive, stalled deal")
- [ ] Accounts ranked by risk descending
- [ ] Top 3 at-risk accounts surfaced prominently in brief

**Validation Method**: Manual review of flagged accounts + user feedback survey

---

#### AC-10.1.4: Historical Context Retrieval

**Given**: Account with 18 months of history (12 meetings, 25 notes, 3 deals)
**When**: Memory Analyst queries Cognee for context
**Then**:
- [ ] Timeline retrieved with all 12 meetings
- [ ] Key events identified (contract renewal, exec meeting, escalation)
- [ ] Related contacts and deals linked
- [ ] Query completes in <5 seconds
- [ ] Context relevance rated ≥90% by user
- [ ] No missing critical events

**Validation Method**: Performance testing + user survey on relevance

---

#### AC-10.1.5: Recommendation Quality

**Given**: At-risk account with overdue commitment and 45 days inactivity
**When**: Recommendation Author generates actions
**Then**:
- [ ] At least 1 recommendation generated
- [ ] Recommendation type appropriate (Follow-Up-Email)
- [ ] Rationale references inactivity and overdue commitment
- [ ] Draft email includes account-specific context
- [ ] Confidence score ≥60 (Medium or High)
- [ ] Priority marked as High or Critical
- [ ] Supporting data references included (note IDs, deal IDs)

**Validation Method**: Human review of 50 test recommendations + acceptance rate tracking

---

#### AC-10.1.6: Approval Workflow Enforcement

**Given**: Recommendation to create task in Zoho CRM
**When**: System attempts to execute task creation
**Then**:
- [ ] Execution blocked until user approval
- [ ] Approval prompt displays task details (subject, description, due date)
- [ ] User can approve, adjust, or reject
- [ ] Upon approval: task created in Zoho within 5 seconds
- [ ] Upon rejection: task not created, reason captured
- [ ] Upon adjustment: modified parameters used, original logged
- [ ] All decisions logged in audit trail

**Validation Method**: End-to-end approval workflow testing with 20 scenarios

---

#### AC-10.1.7: Audit Trail Completeness

**Given**: Full review cycle with 5 recommendations (3 approved, 1 adjusted, 1 rejected)
**When**: Audit log queried
**Then**:
- [ ] All 5 recommendations logged with generation timestamp
- [ ] 3 approved recommendations logged with approval timestamp and user
- [ ] 1 adjusted recommendation logged with original + modified parameters
- [ ] 1 rejected recommendation logged with rejection reason
- [ ] All CRM writes logged with field changes (old/new values)
- [ ] Data source references preserved (Zoho record IDs, Cognee document IDs)
- [ ] Logs immutable (hash verification passes)
- [ ] Logs searchable by account ID

**Validation Method**: Compliance audit of log completeness + tamper detection test

---

### 10.2 Non-Functional Acceptance Criteria

#### AC-10.2.1: Performance - Review Latency

**Given**: 50 accounts for single owner
**When**: Review executes
**Then**:
- [ ] Total execution time <10 minutes (600 seconds)
- [ ] Average time per account <30 seconds
- [ ] P95 time per account <45 seconds
- [ ] No timeout errors
- [ ] Performance consistent across 10 test runs

**Validation Method**: Performance testing with 50-account portfolio, 10 iterations

---

#### AC-10.2.2: Performance - Memory Query Speed

**Given**: Cognee with 100K document chunks, 5K accounts
**When**: Memory Analyst queries account history
**Then**:
- [ ] Query response time P95 <5 seconds
- [ ] Query response time P99 <8 seconds
- [ ] No query timeouts
- [ ] Cache hit rate >70% for repeat queries
- [ ] Performance stable under 10 concurrent queries

**Validation Method**: Load testing with realistic data volume

---

#### AC-10.2.3: Scalability - Account Volume

**Given**: System configured with 5,000 accounts across 50 owners
**When**: Full portfolio review scheduled
**Then**:
- [ ] All 5,000 accounts processed successfully
- [ ] Execution completes within 10 hours (500 accounts/hour)
- [ ] Memory usage <4GB per orchestrator instance
- [ ] CPU usage <60% average
- [ ] No resource exhaustion errors
- [ ] All owner briefs delivered

**Validation Method**: Load testing with 5K account dataset

---

#### AC-10.2.4: Reliability - System Uptime

**Given**: 30-day production run
**When**: Monitoring data analyzed
**Then**:
- [ ] Successful execution rate ≥99%
- [ ] <3 failed runs due to system errors
- [ ] All failures recovered automatically or within 30 minutes
- [ ] No data loss or corruption
- [ ] Uptime SLA met (99%)

**Validation Method**: 30-day pilot monitoring + incident tracking

---

#### AC-10.2.5: Security - Credential Protection

**Given**: System deployed to production
**When**: Security audit conducted
**Then**:
- [ ] Zero plaintext credentials in code, configs, or logs
- [ ] All credentials stored in secrets manager
- [ ] Credential access logged
- [ ] Separate credentials for staging/production
- [ ] Token rotation tested and functional
- [ ] No credentials in version control (git history scan)

**Validation Method**: Security audit + automated credential scanning

---

#### AC-10.2.6: Security - Data Encryption

**Given**: System handling customer data
**When**: Encryption verification performed
**Then**:
- [ ] All API calls use TLS 1.3
- [ ] Cognee storage encrypted at rest (AES-256)
- [ ] Logs encrypted at rest
- [ ] Backup files encrypted
- [ ] SSL Labs rating A or A+
- [ ] Encryption verified with automated tests

**Validation Method**: SSL Labs scan + encryption configuration audit

---

#### AC-10.2.7: Compliance - Audit Log Retention

**Given**: System running for 7 years
**When**: Compliance audit conducted
**Then**:
- [ ] All audit logs retained for 7 years
- [ ] Logs accessible and searchable
- [ ] No data loss or corruption over time
- [ ] Retention policy automated
- [ ] Archival strategy tested (mock 7-year data)

**Validation Method**: Compliance review + retention policy verification

---

### 10.3 Integration Acceptance Criteria

#### AC-10.3.1: Zoho MCP Integration

**Given**: Zoho MCP endpoint configured
**When**: System initializes
**Then**:
- [ ] MCP connection established successfully
- [ ] All required tools enumerate (search_contacts, search_deals, read_account, etc.)
- [ ] Test invocation of each tool succeeds
- [ ] Responses parsed correctly
- [ ] Timeout handling functional (tested with 35s delay)
- [ ] Error handling functional (tested with invalid parameters)

**Validation Method**: Integration testing with Zoho MCP sandbox

---

#### AC-10.3.2: Cognee MCP Integration

**Given**: Cognee MCP server deployed
**When**: System initializes
**Then**:
- [ ] MCP connection established successfully
- [ ] All tools callable (add_context, search_context, get_timeline, upsert_account)
- [ ] Test data ingested successfully
- [ ] Query returns expected results
- [ ] Performance within targets (<5 seconds)
- [ ] Error handling functional

**Validation Method**: Integration testing with Cognee test instance

---

#### AC-10.3.3: Secrets Manager Integration

**Given**: Secrets manager configured with test credentials
**When**: System retrieves secrets
**Then**:
- [ ] All secrets retrieved successfully
- [ ] Token refresh automated (tested with expired token)
- [ ] Staging/production isolation verified (separate secrets)
- [ ] Secret access logged
- [ ] Emergency rotation tested without downtime

**Validation Method**: Integration testing + rotation drill

---

#### AC-10.3.4: Monitoring Integration

**Given**: Monitoring platform configured
**When**: System runs and exports metrics
**Then**:
- [ ] All key metrics exported (run success, latency, token usage, etc.)
- [ ] Metrics visible in dashboard within 1 minute
- [ ] Historical data retained 90 days
- [ ] Alerts trigger on test conditions (simulate failure)
- [ ] Logs searchable in platform

**Validation Method**: End-to-end monitoring validation + alert testing

---

### 10.4 User Acceptance Criteria

#### AC-10.4.1: User Experience - Brief Clarity

**Given**: 10 account executives review generated briefs
**When**: User survey conducted
**Then**:
- [ ] ≥80% rate brief as "clear and easy to understand"
- [ ] ≥70% complete review in <3 minutes
- [ ] ≥60% accept at least 1 recommendation without modification
- [ ] <10% report confusion or missing context
- [ ] ≥90% find priority ranking helpful

**Validation Method**: User survey + time tracking + usability testing

---

#### AC-10.4.2: User Experience - Approval Workflow Usability

**Given**: 10 account executives use approval interface
**When**: Usability testing conducted
**Then**:
- [ ] ≥80% rate interface as "easy to use"
- [ ] Average time to approve/reject <30 seconds
- [ ] <5% errors in approving wrong action
- [ ] ≥70% find batch approval helpful
- [ ] <10% require support to use interface

**Validation Method**: Usability testing + survey

---

#### AC-10.4.3: User Acceptance - Recommendation Quality

**Given**: 100 recommendations generated across 10 users
**When**: User feedback collected
**Then**:
- [ ] ≥50% acceptance rate (approved or approved with minor edits)
- [ ] <10% rejection rate as "inappropriate"
- [ ] ≥80% rated as "helpful" or "very helpful"
- [ ] ≥70% confidence scores align with user perception
- [ ] <5% reported as "inaccurate or misleading"

**Validation Method**: Acceptance tracking + user survey

---

### 10.5 System Acceptance Criteria

#### AC-10.5.1: System Deployment

**Given**: Production environment prepared
**When**: System deployed
**Then**:
- [ ] Deployment completes without errors
- [ ] All services start successfully
- [ ] Health checks pass
- [ ] MCP integrations functional
- [ ] Monitoring active and reporting
- [ ] Rollback capability verified

**Validation Method**: Deployment runbook execution + smoke tests

---

#### AC-10.5.2: System Recovery

**Given**: System failure simulated (e.g., database crash)
**When**: Recovery procedure executed
**Then**:
- [ ] System restores from backup within 24 hours (RTO)
- [ ] Data loss <4 hours (RPO)
- [ ] No data corruption detected
- [ ] System resumes normal operation
- [ ] Incident logged and postmortem completed

**Validation Method**: Disaster recovery drill

---

#### AC-10.5.3: System Documentation

**Given**: System deployed to production
**When**: Documentation review conducted
**Then**:
- [ ] User guide complete and accurate
- [ ] Admin guide complete with runbooks
- [ ] API documentation complete
- [ ] Architecture diagrams current
- [ ] Troubleshooting guides available
- [ ] ≥80% of users find documentation helpful

**Validation Method**: Documentation review + user feedback

---

## Appendix A: Glossary

- **Account Executive (AE)**: Sales representative managing customer accounts
- **At-Risk Account**: Account with high probability of churn based on signals (inactivity, negative sentiment, stalled deals)
- **Brief**: Daily or weekly digest summarizing account changes and recommendations for an owner
- **Cognee**: Knowledge graph memory system for persistent context storage
- **MCP (Model Context Protocol)**: Standardized interface for Claude agents to call external services
- **Owner**: Zoho CRM user assigned to manage account (typically Account Executive)
- **Recommendation**: AI-generated action suggestion with rationale and confidence score
- **Risk Score**: Computed metric (0-100) indicating account churn probability
- **Subagent**: Specialized Claude agent with specific tools and prompts (e.g., Zoho Data Scout, Memory Analyst)
- **SPARC**: Specification, Pseudocode, Architecture, Refinement, Completion methodology

---

## Appendix B: References

- **Claude Agent SDK Documentation**: Anthropic official docs
- **Zoho CRM API v6 Reference**: https://www.zoho.com/crm/developer/docs/api/v6/
- **Cognee Documentation**: https://docs.cognee.ai
- **MCP Specification**: https://spec.modelcontextprotocol.io
- **PubNub Subagent Case Study**: August 2025 (Claude Agent SDK best practices)

---

## Appendix C: Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-10-18 | SPARC Specification Team | Initial specification document |

---

**END OF SPECIFICATION DOCUMENT**
