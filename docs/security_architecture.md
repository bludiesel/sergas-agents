# Security Architecture - Sergas Super Account Manager

## 1. Executive Summary

This document defines the security architecture for the Sergas Super Account Manager multi-agent system. The architecture enforces defense-in-depth principles across authentication, authorization, secrets management, data protection, and audit logging to protect Zoho CRM data and ensure compliance with Sergas data policies.

**Security Posture**: Zero-trust, least-privilege, human-in-the-loop enforcement.

**Key Risk Areas**:
- Unauthorized access to Zoho CRM data containing PII
- Credential theft or misuse of OAuth tokens
- Unauthorized CRM modifications by agents
- Data leakage through logs or memory systems
- Insufficient audit trails for compliance

---

## 2. Authentication Model

### 2.1 Human Users (Account Executives, Managers, Admins)

**Primary Authentication**:
- SSO integration with Sergas identity provider (SAML 2.0/OIDC) for web UI access
- Multi-factor authentication (MFA) required for all users accessing system administration functions
- Session tokens with 8-hour expiry; re-authentication required for sensitive operations

**Role-Based Access Control (RBAC)**:
- **Account Executive**: Read own account briefs, approve/reject recommendations, view audit logs for own actions
- **Sales Manager**: Read team briefs, view aggregated metrics, access audit reports
- **Operations Admin**: Full system configuration, credential management, agent permissions, global audit access

**Password Requirements** (if local auth fallback):
- Minimum 16 characters, complexity requirements enforced
- Hashed with Argon2id (memory-hard algorithm)
- Password rotation every 90 days for admin accounts

### 2.2 Agent Authentication

**Agent Identity**:
- Each agent instance assigned unique service account with immutable identity
- Agent credentials stored in secrets manager (AWS Secrets Manager, HashiCorp Vault, or Azure Key Vault)
- No shared credentials between agents; each subagent has isolated identity

**Inter-Agent Communication**:
- Agents communicate through orchestrator only; no direct peer-to-peer connections
- Message authenticity verified via HMAC signatures using per-agent keys
- Session tokens for agent-to-orchestrator communication expire after 1 hour

### 2.3 External System Authentication

**Zoho CRM OAuth 2.0 Implementation**:
- Server-based OAuth flow with authorization code grant
- Separate OAuth clients for staging/production environments
- Client credentials stored in secrets manager with automatic rotation

**OAuth Token Management**:
```
Access Token:
  - Lifetime: 1 hour
  - Scope: Minimum required (ZohoCRM.modules.Accounts.READ, etc.)
  - Storage: In-memory only, never persisted to disk
  - Transmission: HTTPS only

Refresh Token:
  - Lifetime: 90 days (rotated at 60 days)
  - Storage: Encrypted at rest in secrets manager
  - Access: Restricted to token refresh service only
  - Rotation: Automatic via scheduled job with alert on failure
```

**Cognee Memory System**:
- API key authentication for Cognee API access
- Keys rotated every 30 days via automated process
- Separate keys for production vs. staging workspaces

---

## 3. Authorization Model

### 3.1 Principle of Least Privilege

**Agent Tool Permissions** (Claude Agent SDK permission modes):

```yaml
Orchestrator Agent:
  permission_mode: default
  allowed_tools:
    - SubagentCall
    - Read (config files only)
    - SessionManager
  denied_tools:
    - Write (to CRM)
    - Bash
    - WebFetch
  mcp_servers:
    - none (orchestrator delegates only)

Zoho Data Scout:
  permission_mode: default
  allowed_tools:
    - Read (local cache)
  mcp_servers:
    - zoho-crm (read-only tools)
  allowed_mcp_tools:
    - search_accounts
    - get_account_details
    - list_deals
    - get_user_info
  denied_mcp_tools:
    - update_account
    - create_deal
    - delete_*

Memory Analyst:
  permission_mode: default
  allowed_tools:
    - Read
  mcp_servers:
    - cognee-memory (read-only)
  allowed_mcp_tools:
    - search_context
    - get_account_timeline
    - retrieve_similar_accounts
  denied_mcp_tools:
    - add_context (write operations)
    - delete_context

Recommendation Author:
  permission_mode: default
  allowed_tools:
    - Write (local draft files in /tmp/recommendations/)
  mcp_servers:
    - none (writes to filesystem only)
  denied_mcp_tools:
    - All Zoho CRM write operations

Compliance Reviewer:
  permission_mode: default
  allowed_tools:
    - Read
    - Write (redacted output files)
  mcp_servers:
    - none
```

**Human-in-the-Loop Gates**:
- All CRM write operations (update_account, create_task, add_note) require explicit human approval
- Approval workflow enforced via pre-tool-use hooks with timeout (24 hours)
- Rejected recommendations logged with rationale for audit

### 3.2 Zoho CRM Scopes

**Minimum Required Scopes** (OAuth registration):
```
Production:
  - ZohoCRM.modules.Accounts.READ
  - ZohoCRM.modules.Contacts.READ
  - ZohoCRM.modules.Deals.READ
  - ZohoCRM.modules.Notes.READ
  - ZohoCRM.modules.Activities.READ
  - ZohoCRM.users.READ

Write Operations (post-approval):
  - ZohoCRM.modules.Notes.CREATE
  - ZohoCRM.modules.Tasks.CREATE
  - ZohoCRM.modules.Activities.CREATE
```

**Scope Escalation Policy**:
- Any new scope addition requires Operations Admin approval + security review
- Write scopes enabled only after pilot validation and compliance sign-off
- Quarterly review of active scopes to enforce least privilege

### 3.3 Data Access Controls

**Account Data Segregation**:
- Account Executives access only accounts assigned to them (owner field match)
- Sales Managers access accounts for direct reports only
- Filtering enforced at API query level (COQL WHERE owner IN ...)

**Sensitive Field Masking**:
```
Always Masked in Logs:
  - Social Security Numbers
  - Credit Card Numbers
  - Bank Account Details
  - Personal Health Information

Masked in Non-Production:
  - Customer Email Addresses
  - Phone Numbers
  - Physical Addresses
  - Contract Values (>$100k)
```

---

## 4. Secrets Management

### 4.1 Secrets Storage Architecture

**Primary Secrets Manager**: AWS Secrets Manager (or HashiCorp Vault for on-premises)

**Secret Categories**:
```
zoho/oauth/production:
  - client_id
  - client_secret
  - refresh_token
  Rotation: Every 90 days (automated)
  Access: Token refresh service only

zoho/oauth/staging:
  - client_id
  - client_secret
  - refresh_token
  Rotation: Every 90 days
  Access: Staging environment services

cognee/api_keys/production:
  - api_key
  - workspace_id
  Rotation: Every 30 days
  Access: Memory Analyst agent + sync service

agent/service_accounts:
  - orchestrator_key
  - scout_key
  - analyst_key
  - recommender_key
  Rotation: Every 60 days
  Access: Respective agent process only

database/credentials:
  - audit_db_password
  - metrics_db_password
  Rotation: Every 60 days
  Access: Application services only
```

### 4.2 Secret Access Patterns

**Retrieval Protocol**:
1. Agent requests secret via service account credentials
2. Secrets manager validates IAM role/service principal
3. Access logged with agent identity, timestamp, secret name
4. Secret returned in-memory only (never written to disk)
5. Secret cached for maximum 15 minutes in process memory

**Prohibited Practices**:
- No secrets in environment variables (except local development)
- No secrets in configuration files committed to version control
- No secrets in container images
- No secrets in log files or error messages

### 4.3 Secret Rotation

**Automated Rotation Schedule**:
```bash
# Zoho OAuth tokens
0 2 * * 0 /usr/local/bin/rotate-zoho-tokens.sh --env production

# Cognee API keys
0 3 1 * * /usr/local/bin/rotate-cognee-keys.sh --env production

# Agent service account keys
0 4 1 */2 * /usr/local/bin/rotate-agent-keys.sh
```

**Rotation Failure Alerts**:
- PagerDuty alert to Operations Admin on rotation failure
- Automatic rollback to previous valid secret
- 72-hour grace period for manual intervention before system lockout

### 4.4 Emergency Secret Revocation

**Compromise Response**:
1. Immediately revoke suspected secret via secrets manager API
2. Force re-authentication of all agents using that secret
3. Generate new secret and deploy via emergency rotation pipeline
4. Audit all API calls made with compromised secret (past 90 days)
5. Notify security team and affected stakeholders

---

## 5. Data Encryption

### 5.1 Encryption at Rest

**Zoho CRM Data**:
- Controlled by Zoho infrastructure (AES-256)
- Regional data residency configured per Sergas policy (EU/US/APAC)

**Cognee Memory System**:
```
Storage Layer: LanceDB with encryption enabled
  - Algorithm: AES-256-GCM
  - Key Management: AWS KMS (Customer Managed Keys)
  - Key Rotation: Automatic annual rotation

Account Context Snapshots:
  - Encrypted before storage in Cognee
  - Decryption keys stored in secrets manager
  - Field-level encryption for PII (SSN, payment info)
```

**Local Storage**:
- Recommendation drafts encrypted with per-session keys
- Audit logs encrypted before archival to S3/Azure Blob
- Database backups encrypted with separate KMS key

**Filesystem Encryption**:
- Full disk encryption (LUKS/BitLocker) on all agent host systems
- Temporary files in /tmp encrypted via filesystem-level encryption
- Swap/page files encrypted to prevent memory dumps

### 5.2 Encryption in Transit

**All Network Communication**:
```
Claude API: TLS 1.3 only
Zoho CRM API: TLS 1.2+ with certificate pinning
Cognee API: TLS 1.2+ with mutual TLS (mTLS) for production
MCP Servers: HTTPS/WSS with TLS 1.2+ (stdio for local only)
Internal Services: mTLS with client certificate validation
```

**Certificate Management**:
- Certificates issued by internal PKI or trusted CA
- Automatic renewal 30 days before expiry
- Certificate revocation list (CRL) checked on each connection

### 5.3 Key Management

**Key Hierarchy**:
```
Root Key (AWS KMS):
  └─ Data Encryption Keys (per environment)
      ├─ Cognee workspace encryption key
      ├─ Audit log encryption key
      ├─ Backup encryption key
      └─ Session encryption keys (ephemeral)
```

**Key Access Controls**:
- Root key accessible only via KMS API with IAM policies
- Data keys never exposed to application code
- Key usage logged to CloudTrail/Azure Monitor

---

## 6. PII Handling and Data Privacy

### 6.1 PII Classification

**PII Categories in Zoho CRM**:
```
Tier 1 - Highly Sensitive:
  - Government IDs (SSN, passport numbers)
  - Financial account numbers
  - Health information
  Treatment: Encrypt at rest, mask in logs, restrict access

Tier 2 - Sensitive:
  - Full names
  - Email addresses
  - Phone numbers
  - Physical addresses
  Treatment: Mask in non-production, audit access

Tier 3 - Business Identifiers:
  - Company names
  - Job titles
  - Account numbers
  Treatment: Standard access controls, audit logging
```

### 6.2 Data Processing Rules

**Collection**:
- Retrieve only fields necessary for account review
- Filter out Tier 1 PII unless explicitly required for recommendation
- Justify PII collection in audit logs (purpose, legal basis)

**Storage**:
- PII in Cognee tagged with retention period (90 days for recommendations)
- Automatic deletion after retention expiry
- Right to erasure honored within 72 hours of request

**Usage**:
- PII never included in agent prompts unless anonymized
- Recommendation outputs sanitized before storage
- No PII in system metrics or telemetry

**Sharing**:
- PII never transmitted to third parties (except Zoho/Cognee per DPA)
- Agent-to-agent communication excludes PII; use account IDs only
- Email drafts reviewed for PII leakage before sending

### 6.3 Data Residency and Sovereignty

**Regional Compliance**:
```
EU Accounts:
  - Zoho CRM: EU datacenter (dc.zoho.eu)
  - Cognee: AWS eu-west-1 (Ireland)
  - Audit logs: S3 bucket with EU residency constraint

US Accounts:
  - Zoho CRM: US datacenter (zoho.com)
  - Cognee: AWS us-east-1 (Virginia)
  - Audit logs: S3 bucket us-east-1

APAC Accounts:
  - Zoho CRM: APAC datacenter (zoho.com.au)
  - Cognee: AWS ap-southeast-1 (Singapore)
  - Audit logs: S3 bucket ap-southeast-1
```

**Cross-Border Transfers**:
- Standard Contractual Clauses (SCCs) in place with Zoho/Cognee
- Transfer Impact Assessments completed for each region
- No storage of EU/UK data in US systems

---

## 7. Audit Logging Requirements

### 7.1 Audit Event Categories

**Authentication Events**:
```json
{
  "event_type": "authentication",
  "timestamp": "2025-10-18T00:00:00Z",
  "user_id": "exec@sergas.com",
  "action": "login_success",
  "ip_address": "203.0.113.42",
  "mfa_used": true,
  "session_id": "sess_abc123"
}
```

**Authorization Events**:
```json
{
  "event_type": "authorization",
  "timestamp": "2025-10-18T00:05:00Z",
  "agent_id": "zoho-scout-001",
  "action": "mcp_tool_call",
  "tool_name": "search_accounts",
  "permission_check": "allowed",
  "resource": "accounts/owner:exec@sergas.com"
}
```

**Data Access Events**:
```json
{
  "event_type": "data_access",
  "timestamp": "2025-10-18T00:10:00Z",
  "agent_id": "memory-analyst-001",
  "action": "retrieve_account_context",
  "account_id": "zoho_acc_12345",
  "fields_accessed": ["name", "industry", "last_activity"],
  "pii_accessed": false,
  "justification": "recommendation_generation"
}
```

**Recommendation Events**:
```json
{
  "event_type": "recommendation",
  "timestamp": "2025-10-18T00:15:00Z",
  "agent_id": "recommender-001",
  "account_id": "zoho_acc_12345",
  "recommendation_type": "follow_up_task",
  "confidence_score": 0.87,
  "approval_status": "pending",
  "approver_id": null,
  "data_sources": ["zoho_activity_log", "cognee_timeline"]
}
```

**CRM Modification Events**:
```json
{
  "event_type": "crm_write",
  "timestamp": "2025-10-18T00:20:00Z",
  "approver_id": "exec@sergas.com",
  "agent_id": "orchestrator-001",
  "action": "create_task",
  "account_id": "zoho_acc_12345",
  "approval_timestamp": "2025-10-18T00:18:00Z",
  "zoho_response": {"success": true, "task_id": "task_67890"}
}
```

### 7.2 Audit Log Storage and Retention

**Storage Architecture**:
- Primary: PostgreSQL audit database (encrypted, replicated)
- Archive: S3/Azure Blob with lifecycle policy (transition to Glacier after 90 days)
- Retention: 7 years for compliance (CRM modifications), 1 year for access logs

**Log Integrity**:
- Write-once storage with append-only permissions
- Cryptographic hash chain for tamper detection
- Daily integrity verification via automated job

**Access Controls**:
- Read access: Operations Admin, Compliance Officer
- No modification or deletion of audit logs (except automated retention policy)
- Access to audit logs is itself audited

### 7.3 Audit Monitoring and Alerting

**Real-Time Alerts**:
```
Critical:
  - Unauthorized access attempts (3 failures in 5 minutes)
  - CRM write operation without approval
  - PII access outside normal hours
  - Secret rotation failure
  - Encryption key usage anomaly

Warning:
  - High volume of API calls from single agent (>100/min)
  - Recommendation rejection rate >50% for single agent
  - Zoho rate limit approaching (>80% consumed)
  - MCP server connection failures
```

**Alert Destinations**:
- PagerDuty for critical security events
- Slack #security-alerts for warnings
- Email to Operations Admin for daily digest

---

## 8. Compliance Controls

### 8.1 Sergas Data Policy Compliance

**Policy Requirements** (assumed based on enterprise standards):

1. **Data Minimization**: Collect only necessary account data
   - Control: Zoho API queries filtered by required fields only
   - Validation: Quarterly audit of data collection patterns

2. **Purpose Limitation**: Use account data solely for account management
   - Control: Agent prompts explicitly scope usage
   - Validation: Audit log analysis for out-of-scope access

3. **Accuracy**: Ensure recommendations based on current data
   - Control: Cache invalidation after 1 hour; real-time Zoho queries
   - Validation: Spot checks comparing recommendations to CRM state

4. **Storage Limitation**: Retain data only as long as necessary
   - Control: 90-day retention in Cognee, immediate deletion on request
   - Validation: Monthly retention policy enforcement reports

5. **Integrity and Confidentiality**: Protect data from unauthorized access
   - Control: Encryption, RBAC, audit logging (see sections 3, 5, 7)
   - Validation: Annual penetration testing, quarterly access reviews

### 8.2 GDPR and Privacy Considerations

**GDPR Compliance (for EU accounts)**:

**Lawful Basis**: Legitimate interest (account management); consent for marketing recommendations

**Data Subject Rights**:
- Right to access: API endpoint to retrieve all data for account owner
- Right to rectification: Human approver corrects inaccurate recommendations
- Right to erasure: Delete account context from Cognee within 72 hours
- Right to restrict processing: Flag accounts as "do not process" in system
- Right to data portability: Export account timeline in JSON/CSV format

**Privacy by Design**:
- Default to minimal data collection (accounts, contacts, deals only)
- Pseudonymization where possible (use account IDs in agent communication)
- Privacy Impact Assessment (PIA) completed before production launch

**Data Protection Officer (DPO)**:
- Designated contact for privacy inquiries: dpo@sergas.com
- DPO notified of all PII access incidents within 24 hours

### 8.3 Audit Trail for Compliance

**Compliance Reporting**:
- Monthly report: Data access by user/agent, PII processing justifications
- Quarterly report: Recommendation approval rates, policy violations, security incidents
- Annual report: Comprehensive compliance posture, third-party audit findings

**Regulatory Audit Support**:
- Immutable audit logs available for regulator inspection
- Documentation package: architecture diagrams, DPA agreements, PIAs, access control matrices
- On-demand audit log exports with chain-of-custody verification

---

## 9. Human-in-the-Loop Controls

### 9.1 Approval Workflow Architecture

**Recommendation Approval Flow**:
```
1. Agent generates recommendation → stored in pending queue
2. Notification sent to account owner (email + Slack)
3. Owner reviews recommendation via web UI or CLI
4. Owner actions:
   - Approve: Execute CRM operation, log approval
   - Modify: Edit recommendation, re-submit for execution
   - Reject: Log rejection reason, train agent feedback loop
5. Timeout (24 hours): Auto-reject with alert to manager
```

**Approval UI Requirements**:
- Display recommendation with confidence score, data sources, rationale
- Show diff of proposed CRM changes (before/after)
- Require explicit confirmation ("I approve this action")
- Prevent accidental approval (no default selection)

### 9.2 Escalation Policies

**Automatic Escalation**:
- High-risk recommendations (confidence <60%) → escalate to Sales Manager
- Large CRM updates (>10 records) → require Manager + Admin approval
- PII-related actions → require Compliance Officer approval

**Manual Escalation**:
- Account Executive can escalate any recommendation for second opinion
- Escalation logged with reason and reviewers notified within 15 minutes

### 9.3 Override and Emergency Stop

**Emergency Stop Mechanism**:
- Global kill switch accessible to Operations Admin
- Immediately halts all agent operations and CRM write attempts
- Requires manual review and approval to restart system

**Override Authority**:
- Operations Admin can override RBAC for emergency access (logged and time-limited)
- Overrides expire after 1 hour; require re-authorization
- All overrides reviewed by Security Officer within 48 hours

---

## 10. Security Monitoring and Alerting

### 10.1 Security Metrics

**Real-Time Dashboards**:
- Failed authentication attempts (by user, IP, agent)
- Unauthorized access attempts (denied MCP tool calls)
- PII access patterns (anomaly detection)
- Encryption key usage (volume, latency)
- API rate limit consumption (Zoho, Cognee)

**Threat Intelligence**:
- IP reputation checks for user logins
- Known attack patterns (SQL injection, XSS in inputs)
- Leaked credential monitoring (via HaveIBeenPwned API)

### 10.2 Security Information and Event Management (SIEM)

**SIEM Integration**:
- Forward audit logs to centralized SIEM (Splunk, Datadog, Elastic Security)
- Correlation rules for multi-stage attacks
- Automated playbooks for common incidents (brute force, privilege escalation)

**Use Cases**:
- Detect account takeover attempts (unusual IP, failed MFA)
- Identify insider threats (bulk data exfiltration, off-hours access)
- Monitor agent behavior anomalies (high error rates, permission denials)

### 10.3 Incident Response Procedures

**Security Incident Classification**:
```
P0 - Critical:
  - Confirmed data breach (PII exposed)
  - Credential compromise with active exploitation
  - Unauthorized CRM modifications at scale
  Response: Immediate, 24/7 on-call

P1 - High:
  - Suspected credential theft (no confirmed misuse)
  - Repeated unauthorized access attempts
  - Encryption key access anomaly
  Response: Within 1 hour during business hours

P2 - Medium:
  - Individual account access violation
  - Non-critical configuration drift
  - Secret rotation failure (with fallback active)
  Response: Within 4 hours during business hours

P3 - Low:
  - Routine policy violations (logged, no impact)
  - Low-confidence anomaly detections
  Response: Weekly review cycle
```

**Incident Response Playbook**:
1. **Detection**: Alert triggered via monitoring system
2. **Containment**: Isolate affected systems, revoke compromised credentials
3. **Investigation**: Analyze audit logs, identify root cause and scope
4. **Eradication**: Patch vulnerabilities, remove attacker access
5. **Recovery**: Restore systems from clean backups, validate integrity
6. **Post-Incident**: Document findings, update security controls, train team

**Communication Protocol**:
- Security Officer notified of all P0/P1 incidents within 15 minutes
- Legal/Compliance notified of PII breaches within 1 hour
- Affected users notified within 72 hours (GDPR requirement)
- Public disclosure only if required by regulation (coordinated with Legal)

---

## 11. Security Testing and Validation

### 11.1 Continuous Security Testing

**Automated Security Scans**:
- SAST (Static Application Security Testing): SonarQube, Semgrep
- DAST (Dynamic Application Security Testing): OWASP ZAP, Burp Suite
- Dependency vulnerability scanning: Snyk, Dependabot
- Container image scanning: Trivy, Clair
- Secrets scanning: Gitleaks, TruffleHog

**Frequency**:
- SAST: On every commit (CI/CD pipeline)
- DAST: Weekly against staging environment
- Dependency scans: Daily
- Container scans: On every image build
- Secrets scans: Pre-commit hooks + daily repo scans

### 11.2 Penetration Testing

**Annual Penetration Test**:
- Conducted by independent third-party firm
- Scope: Web UI, API endpoints, MCP servers, agent infrastructure
- Deliverable: Report with CVSS-scored findings and remediation recommendations
- Remediation: P0/P1 findings resolved within 30 days

**Red Team Exercise** (biennial):
- Simulate advanced persistent threat (APT) scenario
- Test detection and response capabilities
- Validate backup/recovery procedures

### 11.3 Security Validation Checklist

**Pre-Production Release**:
- [ ] All secrets migrated to secrets manager (no .env files)
- [ ] RBAC configured per least privilege matrix
- [ ] Encryption enabled for data at rest and in transit
- [ ] Audit logging active and tested
- [ ] Human approval workflow enforced for CRM writes
- [ ] PII masking validated in logs and outputs
- [ ] Rate limiting configured for Zoho API
- [ ] Backup and recovery procedures tested
- [ ] Incident response playbook reviewed with team
- [ ] Security scanning passed (no P0/P1 findings)
- [ ] Penetration test completed with acceptable risk posture
- [ ] Compliance review approved (Sergas policy, GDPR)

---

## 12. Security Architecture Diagrams

### 12.1 Authentication and Authorization Flow

```
┌─────────────┐
│   User      │
│ (Exec/Mgr)  │
└──────┬──────┘
       │ 1. Login (SSO + MFA)
       ▼
┌─────────────────┐
│  Identity       │
│  Provider       │──────────┐
│  (Okta/Azure)   │          │ 2. SAML/OIDC token
└─────────────────┘          │
                             ▼
                    ┌────────────────┐
                    │  Web UI        │
                    │  (Frontend)    │
                    └────────┬───────┘
                             │ 3. JWT session token
                             ▼
                    ┌────────────────┐
                    │  API Gateway   │
                    │  + RBAC Check  │
                    └────────┬───────┘
                             │ 4. Authorized request
                             ▼
                    ┌────────────────┐
                    │  Orchestrator  │
                    │     Agent      │
                    └────────┬───────┘
                             │ 5. Delegate to subagent
                             ▼
              ┌──────────────┴──────────────┐
              │                             │
    ┌─────────▼─────────┐         ┌────────▼────────┐
    │  Zoho Data Scout  │         │ Memory Analyst  │
    │  (Service Acct)   │         │ (Service Acct)  │
    └─────────┬─────────┘         └────────┬────────┘
              │                             │
              │ 6a. OAuth token             │ 6b. API key
              │ (from Secrets Mgr)          │ (from Secrets Mgr)
              ▼                             ▼
    ┌─────────────────┐         ┌─────────────────┐
    │  Zoho CRM API   │         │  Cognee API     │
    │  (OAuth 2.0)    │         │  (API Key Auth) │
    └─────────────────┘         └─────────────────┘
```

### 12.2 Data Flow with Security Controls

```
┌──────────────────────────────────────────────────────────┐
│                    USER APPROVAL LAYER                   │
│  (Human-in-the-loop for all CRM write operations)        │
└──────────────┬──────────────────────────────┬────────────┘
               │                              │
               │ Approve                      │ Reject
               ▼                              ▼
┌─────────────────────────┐        ┌─────────────────────┐
│   CRM Write Operation   │        │   Audit Log Only    │
│   (with approval proof) │        │ (train feedback)    │
└──────────┬──────────────┘        └─────────────────────┘
           │
           │ Encrypted HTTPS + mTLS
           ▼
┌─────────────────────────┐
│      Zoho CRM API       │
│  (TLS 1.2+, Cert Pin)   │
└──────────┬──────────────┘
           │
           │ Encrypted response
           ▼
┌─────────────────────────┐
│   Recommendation Author │
│  (Sanitize PII in logs) │
└──────────┬──────────────┘
           │
           │ Recommendation draft (encrypted at rest)
           ▼
┌─────────────────────────┐
│   Cognee Memory Store   │
│  (AES-256, field-level  │
│   encryption for PII)   │
└──────────┬──────────────┘
           │
           │ Retention: 90 days → Auto-delete
           ▼
┌─────────────────────────┐
│   Audit Log Archive     │
│ (S3 Glacier, encrypted, │
│  7-year retention)      │
└─────────────────────────┘
```

### 12.3 Secrets Management Architecture

```
┌─────────────────┐
│  Agent Process  │
│   (Runtime)     │
└────────┬────────┘
         │ 1. Request secret with service account creds
         ▼
┌──────────────────────────┐
│   Secrets Manager        │
│ (AWS Secrets Manager /   │
│  HashiCorp Vault)        │
└────────┬─────────────────┘
         │ 2. IAM/RBAC validation
         │ 3. Audit log (who, what, when)
         │ 4. Return encrypted secret
         ▼
┌──────────────────────────┐
│  Agent Memory (RAM only) │
│  Secret cached 15 min    │
└────────┬─────────────────┘
         │ 5. Use secret for API call
         ▼
┌──────────────────────────┐
│  External API            │
│  (Zoho CRM / Cognee)     │
└────────┬─────────────────┘
         │ 6. Secret auto-rotated every 30-90 days
         ▼
┌──────────────────────────┐
│  Rotation Service        │
│  (Scheduled job +        │
│   failure alerting)      │
└──────────────────────────┘
```

---

## 13. Security Roles and Responsibilities

**Security Officer**:
- Own security architecture and policy
- Approve high-risk changes (new scopes, data access patterns)
- Lead incident response for P0/P1 events
- Conduct quarterly access reviews

**Operations Admin**:
- Manage secrets rotation and credential lifecycle
- Configure agent RBAC and tool permissions
- Monitor security alerts and respond to P2/P3 incidents
- Execute backup and recovery procedures

**Compliance Officer**:
- Ensure GDPR and Sergas policy adherence
- Review audit logs for compliance violations
- Approve PII processing requests
- Coordinate regulatory audits

**Development Team**:
- Implement security controls in code
- Fix security vulnerabilities per SLA (P0: 7 days, P1: 30 days)
- Participate in security training (annual)
- Perform peer code reviews with security checklist

---

## 14. Security Roadmap

**Phase 1 - Foundation (Pre-Pilot)**:
- OAuth 2.0 implementation with secrets manager
- RBAC configuration for all agents
- Audit logging infrastructure
- PII masking in logs
- Human approval workflow (CLI-based)

**Phase 2 - Hardening (Pre-Production)**:
- Encryption at rest for Cognee
- mTLS for internal services
- SIEM integration
- Automated security scanning in CI/CD
- Penetration testing

**Phase 3 - Advanced Controls (Post-Launch)**:
- Behavioral anomaly detection for agents
- Automated incident response playbooks
- Field-level encryption for Tier 1 PII
- Secrets rotation automation
- Red team exercise

**Phase 4 - Continuous Improvement**:
- Quarterly threat modeling updates
- Annual security architecture review
- Agent security training (reinforcement learning from incidents)
- Zero-trust network segmentation

---

## 15. References and Standards

**Standards Compliance**:
- OWASP Top 10 (2021): Web application security
- NIST Cybersecurity Framework: Risk management
- CIS Controls v8: Baseline security controls
- ISO 27001: Information security management
- SOC 2 Type II: Trust services criteria

**Zoho Security Documentation**:
- Zoho CRM Security Whitepaper (2025)
- OAuth 2.0 Implementation Guide (Zoho Developer Docs)
- Zoho API Rate Limits and Best Practices

**Claude Agent SDK**:
- Security Considerations (Anthropic Docs)
- MCP Security Best Practices
- Permission Modes Reference

**Regulatory Frameworks**:
- GDPR (General Data Protection Regulation)
- CCPA (California Consumer Privacy Act)
- HIPAA (if healthcare accounts processed)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-18
**Owner**: Security Engineering Team
**Review Cycle**: Quarterly
**Next Review**: 2026-01-18
