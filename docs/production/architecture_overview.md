# Architecture Overview

## System Architecture

The Sergas Super Account Manager is a multi-agent AI system built on a layered architecture designed for scalability, reliability, and maintainability.

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Component Details](#component-details)
3. [Data Flow](#data-flow)
4. [Integration Architecture](#integration-architecture)
5. [Security Architecture](#security-architecture)
6. [Deployment Architecture](#deployment-architecture)

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Presentation Layer                           │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  CLI Interface  │  REST API (FastAPI)  │  AG UI Protocol SSE   │  │
│  │  • Account queries    • Health checks       • Real-time events │  │
│  │  • Manual actions     • Webhooks            • Agent status     │  │
│  └────────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│                      Orchestration Layer                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Main Orchestrator Agent                          │   │
│  │  • Workflow coordination      • Approval gate management     │   │
│  │  • Subagent delegation        • Session management           │   │
│  │  • Error handling             • Metrics collection           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│                      Multi-Agent Layer                                │
│  ┌────────────┬──────────────┬────────────────┬──────────────────┐  │
│  │  Zoho Data │  Memory      │  Recommendation│  Compliance      │  │
│  │  Scout     │  Analyst     │  Author        │  Reviewer        │  │
│  │            │              │                │                  │  │
│  │  CRM data  │  Historical  │  Action        │  Policy          │  │
│  │  retrieval │  context     │  synthesis     │  validation      │  │
│  └────────────┴──────────────┴────────────────┴──────────────────┘  │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│                      Integration Layer                                │
│  ┌─────────────────────┬───────────────────┬──────────────────────┐ │
│  │  Zoho Integration   │  Cognee Memory    │  Claude Agent SDK    │ │
│  │  (3-Tier Failover)  │  (Knowledge Graph)│  (AI Reasoning)      │ │
│  │                     │                   │                      │ │
│  │  • MCP Server       │  • Vector Search  │  • Agent Runtime     │ │
│  │  • Python SDK       │  • Graph Queries  │  • Tool Execution    │ │
│  │  • REST API         │  • Memory Sync    │  • Context Mgmt      │ │
│  └─────────────────────┴───────────────────┴──────────────────────┘ │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│                      Data Layer                                       │
│  ┌──────────────┬────────────────┬──────────────┬─────────────────┐ │
│  │ PostgreSQL   │ Qdrant         │ Redis        │ S3/Storage      │ │
│  │              │ (Vectors)      │ (Cache)      │ (Files/Logs)    │ │
│  │ • Accounts   │ • Embeddings   │ • Sessions   │ • Audit Logs    │ │
│  │ • Activities │ • Semantic     │ • Rate Limit │ • Backups       │ │
│  │ • Audit Logs │   Search       │ • Dedup      │ • Reports       │ │
│  └──────────────┴────────────────┴──────────────┴─────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│                      Cross-Cutting Concerns                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Monitoring  │  Security    │  Resilience  │  Observability  │   │
│  │  • Prometheus│  • OAuth 2.0 │  • Retries   │  • Logging      │   │
│  │  • Grafana   │  • Secrets   │  • Circuit   │  • Tracing      │   │
│  │  • Alerts    │  • Audit     │    Breaker   │  • Metrics      │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Presentation Layer

#### REST API (FastAPI)

**Responsibilities:**
- HTTP request handling
- Input validation
- Authentication/authorization
- Response formatting
- Webhook endpoints

**Key Features:**
- OpenAPI documentation
- Async request handling
- CORS support
- Rate limiting
- Health checks

**Endpoints:**
```python
POST   /api/v1/accounts/{id}/analyze    # Trigger account analysis
GET    /api/v1/accounts/{id}/status     # Get analysis status
GET    /api/v1/recommendations/{id}     # Get recommendations
POST   /api/v1/recommendations/{id}/approve  # Approve recommendation
GET    /api/v1/health                   # Health check
POST   /api/webhooks/zoho              # Zoho webhook receiver
```

#### CLI Interface

**Responsibilities:**
- Command-line operations
- Admin tasks
- Scripting support
- Batch operations

**Key Commands:**
```bash
sergas analyze <account-id>           # Analyze single account
sergas batch analyze <account-list>   # Batch analysis
sergas sync --full                    # Full CRM sync
sergas user create --admin            # Create admin user
sergas db migrate                     # Run migrations
```

#### AG UI Protocol (SSE)

**Responsibilities:**
- Real-time event streaming
- Agent status updates
- Progress notifications
- Approval workflows

**Event Types:**
```javascript
{
  "type": "agent_started",
  "agent": "ZohoDataScout",
  "timestamp": "2024-10-19T10:00:00Z",
  "data": {}
}

{
  "type": "agent_progress",
  "agent": "MemoryAnalyst",
  "progress": 0.65,
  "message": "Analyzing historical patterns..."
}

{
  "type": "approval_required",
  "recommendation_id": "rec_123",
  "action": "update_account_status",
  "confidence": 0.87
}
```

---

### 2. Orchestration Layer

#### Main Orchestrator Agent

**Class:** `AccountOrchestrator`
**Location:** `/src/agents/orchestrator.py`

**Responsibilities:**
1. Workflow coordination across subagents
2. Session lifecycle management
3. Approval gate enforcement
4. Error handling and recovery
5. Metrics collection

**Workflow:**
```python
async def analyze_account(account_id: str) -> AnalysisResult:
    """
    Main workflow orchestration.

    Steps:
    1. Initialize session
    2. Invoke Zoho Data Scout (retrieve account data)
    3. Invoke Memory Analyst (get historical context)
    4. Invoke Recommendation Author (generate actions)
    5. Invoke Compliance Reviewer (validate recommendations)
    6. Wait for human approval
    7. Execute approved actions
    8. Close session and log results
    """
```

**State Machine:**
```
IDLE → INITIALIZING → DATA_RETRIEVAL → MEMORY_ANALYSIS →
RECOMMENDATION → COMPLIANCE_CHECK → AWAITING_APPROVAL →
EXECUTING → COMPLETED | FAILED
```

---

### 3. Multi-Agent Layer

#### Zoho Data Scout Agent

**Class:** `ZohoDataScout`
**Location:** `/src/agents/zoho_data_scout.py`

**Responsibilities:**
- Retrieve account data from Zoho CRM
- Detect changes since last sync
- Map account ownership
- Monitor activity patterns

**Tools:**
- `zoho_get_account` - Fetch account details
- `zoho_list_activities` - Get recent activities
- `zoho_search_accounts` - Query accounts
- `zoho_get_notes` - Retrieve notes/comments

**Output Schema:**
```python
class AccountData(BaseModel):
    account_id: str
    name: str
    status: AccountStatus
    owner_id: str
    owner_name: str
    last_activity: datetime
    deal_value: float
    payment_status: PaymentStatus
    activities: List[Activity]
    recent_changes: List[Change]
```

---

#### Memory Analyst Agent

**Class:** `MemoryAnalyst`
**Location:** `/src/agents/memory_analyst.py`

**Responsibilities:**
- Query Cognee knowledge graph
- Identify historical patterns
- Provide temporal context
- Surface similar past cases

**Tools:**
- `cognee_query` - Semantic search
- `cognee_get_related` - Find related entities
- `cognee_get_timeline` - Temporal analysis
- `cognee_pattern_match` - Pattern recognition

**Output Schema:**
```python
class HistoricalContext(BaseModel):
    account_history: List[HistoricalEvent]
    similar_accounts: List[SimilarAccount]
    patterns_detected: List[Pattern]
    risk_indicators: List[RiskIndicator]
    success_factors: List[SuccessFactor]
```

---

#### Recommendation Author Agent

**Class:** `RecommendationAuthor`
**Location:** `/src/agents/recommendation_author.py`

**Responsibilities:**
- Synthesize account data and context
- Generate actionable recommendations
- Calculate confidence scores
- Prioritize actions

**Tools:**
- `template_renderer` - Apply action templates
- `confidence_scorer` - Calculate confidence
- `priority_ranker` - Prioritize actions
- `draft_writer` - Generate communication drafts

**Output Schema:**
```python
class Recommendation(BaseModel):
    id: str
    type: RecommendationType  # FOLLOW_UP, UPDATE_STATUS, ESCALATE, etc.
    priority: Priority  # HIGH, MEDIUM, LOW
    confidence: float  # 0.0-1.0
    action: str
    rationale: str
    draft_content: Optional[str]
    estimated_impact: str
    requires_approval: bool
```

---

#### Compliance Reviewer Agent

**Class:** `ComplianceReviewer`
**Location:** `/src/agents/compliance_reviewer.py`

**Responsibilities:**
- Validate recommendations against policies
- Detect PII in outputs
- Check approval requirements
- Sanitize sensitive data

**Tools:**
- `policy_validator` - Check compliance rules
- `pii_detector` - Identify sensitive data
- `data_sanitizer` - Mask/encrypt PII
- `approval_checker` - Verify authorization

**Output Schema:**
```python
class ComplianceReport(BaseModel):
    approved: bool
    policy_violations: List[PolicyViolation]
    pii_detected: List[PIIInstance]
    sanitized_content: str
    approval_required: bool
    risk_level: RiskLevel
```

---

### 4. Integration Layer

#### Zoho CRM Integration (3-Tier Failover)

**Tier 1: Zoho MCP Server** (Primary)
- Direct MCP protocol integration
- Fastest performance
- Limited by MCP availability

**Tier 2: Zoho Python SDK** (Secondary)
- Official Zoho SDK
- Comprehensive API coverage
- Handles OAuth automatically

**Tier 3: REST API** (Fallback)
- Direct HTTP requests
- Maximum flexibility
- Manual token management

**Failover Logic:**
```python
async def get_account(account_id: str) -> Account:
    """
    3-tier failover implementation.

    1. Try Zoho MCP server
    2. If failed, try Python SDK
    3. If failed, try REST API
    4. If all failed, raise IntegrationError
    """
    try:
        return await zoho_mcp_client.get_account(account_id)
    except MCPError:
        try:
            return await zoho_sdk_client.get_account(account_id)
        except SDKError:
            return await zoho_rest_client.get_account(account_id)
```

---

#### Cognee Memory Integration

**Architecture:**
```
┌─────────────────────────────────────────┐
│          Application Layer              │
│  ┌───────────────────────────────────┐  │
│  │  Memory Sync Scheduler            │  │
│  │  • Periodic sync (hourly)         │  │
│  │  • Real-time updates (webhook)    │  │
│  └───────────────────────────────────┘  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          Cognee MCP Tools               │
│  • add_knowledge(text, metadata)        │
│  • search(query, filters)               │
│  • get_related(entity_id)               │
│  • get_graph_neighbors(node_id)         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          Cognee Core                    │
│  ┌──────────────┬──────────────────┐   │
│  │  PostgreSQL  │  Qdrant Vector   │   │
│  │  (Graph)     │  (Embeddings)    │   │
│  └──────────────┴──────────────────┘   │
└─────────────────────────────────────────┘
```

**Data Sync Strategy:**
- **Full Sync**: Daily at 2 AM (all accounts)
- **Incremental Sync**: Hourly (changed accounts)
- **Real-Time Sync**: Webhook-triggered (immediate)

---

### 5. Data Layer

#### PostgreSQL Database

**Schema Overview:**
```sql
-- Accounts (synced from Zoho)
CREATE TABLE accounts (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50),
    owner_id VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    sync_hash VARCHAR(64)  -- For change detection
);

-- Activities (synced from Zoho)
CREATE TABLE activities (
    id VARCHAR(50) PRIMARY KEY,
    account_id VARCHAR(50) REFERENCES accounts(id),
    type VARCHAR(50),
    description TEXT,
    created_by VARCHAR(50),
    created_at TIMESTAMP
);

-- Recommendations (generated by agents)
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id VARCHAR(50) REFERENCES accounts(id),
    type VARCHAR(50) NOT NULL,
    priority VARCHAR(20),
    confidence DECIMAL(3, 2),
    action TEXT NOT NULL,
    rationale TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    approved_by VARCHAR(50),
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Audit Logs (all system actions)
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    agent_id VARCHAR(50),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(50),
    details JSONB,
    ip_address INET,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent Sessions (workflow tracking)
CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id VARCHAR(50),
    orchestrator_id VARCHAR(50),
    status VARCHAR(20),
    start_time TIMESTAMP DEFAULT NOW(),
    end_time TIMESTAMP,
    error_message TEXT,
    metrics JSONB
);
```

**Indexes:**
```sql
CREATE INDEX idx_accounts_owner_id ON accounts(owner_id);
CREATE INDEX idx_accounts_status ON accounts(status);
CREATE INDEX idx_activities_account_id ON activities(account_id);
CREATE INDEX idx_recommendations_account_id ON recommendations(account_id);
CREATE INDEX idx_recommendations_status ON recommendations(status);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_agent_sessions_account_id ON agent_sessions(account_id);
```

---

#### Redis Cache

**Use Cases:**
1. **Session Management**: User sessions, agent sessions
2. **Rate Limiting**: API request tracking
3. **Deduplication**: Webhook event dedup
4. **Query Cache**: Expensive query results
5. **Token Cache**: OAuth access tokens

**Key Patterns:**
```python
# Sessions
session:{user_id}:{session_id} -> {session_data}

# Rate limiting
ratelimit:{ip}:{endpoint}:{window} -> {count}

# Deduplication
webhook:event:{event_id} -> {processed_timestamp}

# Query cache
cache:account:{account_id} -> {account_data}

# Tokens
zoho:access_token -> {token_value}
```

**TTL Configuration:**
```python
SESSION_TTL = 3600  # 1 hour
RATE_LIMIT_WINDOW = 60  # 1 minute
DEDUP_TTL = 3600  # 1 hour
QUERY_CACHE_TTL = 300  # 5 minutes
TOKEN_TTL = 3000  # 50 minutes (refresh before expiry)
```

---

## Data Flow

### Account Analysis Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. REQUEST: POST /api/v1/accounts/{id}/analyze                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. ORCHESTRATOR: Initialize session, validate permissions      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. ZOHO DATA SCOUT: Retrieve account data (3-tier failover)    │
│    Output: AccountData (status, activities, changes)           │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. MEMORY ANALYST: Query Cognee for historical context         │
│    Output: HistoricalContext (patterns, similar accounts)      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. RECOMMENDATION AUTHOR: Generate actionable recommendations  │
│    Input: AccountData + HistoricalContext                      │
│    Output: List[Recommendation] (with confidence scores)       │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. COMPLIANCE REVIEWER: Validate recommendations               │
│    Output: ComplianceReport (approved, violations, sanitized)  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. APPROVAL GATE: Wait for human approval (async)              │
│    Notification: Email/Slack to account owner                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. EXECUTION: Apply approved recommendations to Zoho CRM       │
│    Log: Audit trail of all changes                             │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. MEMORY SYNC: Update Cognee with new knowledge               │
│    Store: Recommendation outcomes for future learning          │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 10. RESPONSE: Return AnalysisResult to client                  │
│     Status: success/failed, recommendations, next_review       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────────┐
│                       Perimeter Security                         │
│  • Firewall (only 80/443 exposed)                              │
│  • DDoS protection                                              │
│  • Geographic restrictions                                      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                   Network Security (TLS Layer)                   │
│  • TLS 1.3 encryption                                           │
│  • Certificate pinning                                          │
│  • Perfect forward secrecy                                      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│              Application Security (API Layer)                    │
│  • OAuth 2.0 authentication                                     │
│  • JWT token validation                                         │
│  • Rate limiting (60 req/min)                                   │
│  • CORS policies                                                │
│  • Input validation                                             │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│              Agent Security (Business Logic)                     │
│  • Read-only tools by default                                   │
│  • Approval gates for writes                                    │
│  • PII detection and masking                                    │
│  • Compliance validation                                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                   Data Security (Storage)                        │
│  • Encryption at rest (AES-256)                                 │
│  • Column-level encryption (PII)                                │
│  • Database access controls                                     │
│  • Audit logging                                                │
└─────────────────────────────────────────────────────────────────┘
```

### Secrets Management

```
┌─────────────────────────────────────────────────────────────────┐
│                   AWS Secrets Manager                            │
│  • Automatic rotation                                           │
│  • Encryption with KMS                                          │
│  • Audit logging                                                │
│  • Version history                                              │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│              Application Secrets Loader                          │
│  • Lazy loading                                                 │
│  • In-memory cache (encrypted)                                  │
│  • Automatic refresh                                            │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                  Application Runtime                             │
│  • No secrets in code                                           │
│  • No secrets in logs                                           │
│  • No secrets in environment dumps                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

### Production Deployment (Kubernetes)

```
┌───────────────────────────────────────────────────────────────────┐
│                      Load Balancer (AWS ALB/GCP LB)               │
│  • SSL termination                                                │
│  • Health checks                                                  │
│  • Request routing                                                │
└────────────────────────┬──────────────────────────────────────────┘
                         │
┌────────────────────────▼──────────────────────────────────────────┐
│                  Kubernetes Cluster                                │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              Ingress Controller (Nginx)                       │ │
│  │  • Path-based routing                                        │ │
│  │  • Rate limiting                                             │ │
│  └────────────────────┬─────────────────────────────────────────┘ │
│                       │                                            │
│  ┌────────────────────▼─────────────────────────────────────────┐ │
│  │         Application Pods (Deployment)                        │ │
│  │  ┌──────────┬──────────┬──────────┬──────────┬──────────┐   │ │
│  │  │  Pod 1   │  Pod 2   │  Pod 3   │  Pod 4   │  Pod 5   │   │ │
│  │  │  FastAPI │  FastAPI │  FastAPI │  FastAPI │  FastAPI │   │ │
│  │  │  + Agents│  + Agents│  + Agents│  + Agents│  + Agents│   │ │
│  │  └──────────┴──────────┴──────────┴──────────┴──────────┘   │ │
│  │  • Auto-scaling (HPA): 2-10 replicas                         │ │
│  │  • Resource limits: 2 CPU, 4Gi memory                        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │         Database (StatefulSet)                               │ │
│  │  ┌──────────────────┬──────────────────────────────────────┐│ │
│  │  │  PostgreSQL      │  Redis                               ││ │
│  │  │  Primary/Replica │  Sentinel HA                         ││ │
│  │  └──────────────────┴──────────────────────────────────────┘│ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │         Monitoring (StatefulSet)                             │ │
│  │  ┌──────────────────┬──────────────────┬──────────────────┐ │ │
│  │  │  Prometheus      │  Grafana         │  AlertManager    │ │ │
│  │  └──────────────────┴──────────────────┴──────────────────┘ │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

### Scaling Strategy

**Horizontal Pod Autoscaler (HPA):**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sergas-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sergas-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Database Scaling:**
- Vertical: Increase instance size
- Horizontal: Read replicas for queries
- Partitioning: Time-based partitioning for audit logs

---

## Technology Stack

### Backend
- **Language**: Python 3.14
- **Framework**: FastAPI
- **Agent SDK**: Claude Agent SDK (Anthropic)
- **Async Runtime**: uvloop
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic

### Integrations
- **CRM**: Zoho CRM (MCP + SDK + REST)
- **Memory**: Cognee (Knowledge Graph)
- **Vector DB**: Qdrant
- **Cache**: Redis

### Data Layer
- **Database**: PostgreSQL 14+
- **Cache**: Redis 6+
- **Object Storage**: S3/MinIO
- **Vector Search**: Qdrant

### Infrastructure
- **Containers**: Docker
- **Orchestration**: Kubernetes
- **Monitoring**: Prometheus + Grafana
- **Logging**: Structured logging (JSON)
- **Tracing**: OpenTelemetry

### Security
- **Secrets**: AWS Secrets Manager
- **Auth**: OAuth 2.0 + JWT
- **Encryption**: TLS 1.3, AES-256-GCM
- **Compliance**: SOC 2, GDPR

---

## Performance Characteristics

### Throughput
- **Accounts/hour**: 5,000+
- **Concurrent users**: 50+
- **API requests/sec**: 100+
- **Agent sessions/min**: 20+

### Latency
- **API response time**: <200ms (p95)
- **Account analysis**: <30s (full workflow)
- **Database queries**: <50ms (p95)
- **Zoho API calls**: <1s (p95)

### Availability
- **Target uptime**: 99.9%
- **RTO** (Recovery Time Objective): <15 minutes
- **RPO** (Recovery Point Objective): <1 hour

---

**Last Updated**: 2025-10-19
**Version**: 1.0.0
**Maintained by**: Sergas Architecture Team
