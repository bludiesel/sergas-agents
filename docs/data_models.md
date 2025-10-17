# Data Models Specification

## 1. Overview

This document defines all data models used in the Sergas Agents system. Models are implemented using Pydantic v2 for validation, serialization, and type safety.

## 2. Base Models

### 2.1 BaseModel Configuration

```python
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

class SerGasBaseModel(BaseModel):
    """Base model with common configuration for all data models."""

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {}
        }
    )

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    def update_timestamp(self):
        """Update the updated_at field."""
        self.updated_at = datetime.utcnow()
```

## 3. Account Data Models

### 3.1 Account Core Model

```python
from pydantic import EmailStr, HttpUrl, validator
from typing import List, Dict, Any, Optional
from enum import Enum

class AccountStatus(str, Enum):
    """Account status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    CLOSED = "closed"

class AccountType(str, Enum):
    """Account type enumeration."""
    CUSTOMER = "customer"
    VENDOR = "vendor"
    PARTNER = "partner"
    INTERNAL = "internal"

class Account(SerGasBaseModel):
    """Core account data model."""

    # Zoho CRM Fields
    zoho_account_id: str = Field(..., description="Zoho CRM account ID")
    account_name: str = Field(..., min_length=1, max_length=255)
    account_number: Optional[str] = Field(None, description="Internal account number")
    account_type: AccountType = Field(default=AccountType.CUSTOMER)
    status: AccountStatus = Field(default=AccountStatus.ACTIVE)

    # Contact Information
    primary_email: Optional[EmailStr] = None
    secondary_email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r'^\+?[\d\s\-\(\)]+$')
    website: Optional[HttpUrl] = None

    # Address Information
    billing_address: Optional["Address"] = None
    shipping_address: Optional["Address"] = None

    # Financial Information
    annual_revenue: Optional[float] = Field(None, ge=0)
    credit_limit: Optional[float] = Field(None, ge=0)
    payment_terms: Optional[str] = None
    currency: str = Field(default="USD")

    # Business Information
    industry: Optional[str] = None
    employee_count: Optional[int] = Field(None, ge=0)
    tax_id: Optional[str] = None

    # Relationship Management
    account_owner: Optional[str] = None
    parent_account_id: Optional[str] = None

    # Metadata
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    # Analytics
    health_score: Optional[float] = Field(None, ge=0, le=100)
    risk_level: Optional[str] = None
    last_activity_date: Optional[datetime] = None

    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v and len(v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) < 10:
            raise ValueError('Phone number must have at least 10 digits')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "zoho_account_id": "123456789",
                "account_name": "Acme Corporation",
                "account_number": "ACC-001",
                "account_type": "customer",
                "status": "active",
                "primary_email": "contact@acme.com",
                "phone": "+1-555-123-4567",
                "annual_revenue": 1000000.00,
                "industry": "Technology",
                "health_score": 85.5
            }
        }
    )

class Address(BaseModel):
    """Address model for billing and shipping."""

    street: str = Field(..., description="Street address")
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str
    address_type: Optional[str] = Field(None, description="billing or shipping")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "street": "123 Main Street",
                "city": "San Francisco",
                "state": "CA",
                "postal_code": "94105",
                "country": "USA",
                "address_type": "billing"
            }
        }
    )
```

### 3.2 Account Metrics Model

```python
class AccountMetrics(SerGasBaseModel):
    """Account performance metrics and analytics."""

    account_id: str = Field(..., description="Reference to Account.zoho_account_id")

    # Financial Metrics
    total_revenue: float = Field(default=0.0, ge=0)
    ytd_revenue: float = Field(default=0.0, ge=0)
    avg_transaction_value: float = Field(default=0.0, ge=0)
    outstanding_balance: float = Field(default=0.0)
    days_sales_outstanding: Optional[int] = Field(None, ge=0)

    # Engagement Metrics
    total_transactions: int = Field(default=0, ge=0)
    transaction_frequency: Optional[float] = Field(None, ge=0, description="Transactions per month")
    last_transaction_date: Optional[datetime] = None
    days_since_last_transaction: Optional[int] = Field(None, ge=0)

    # Support Metrics
    support_tickets_total: int = Field(default=0, ge=0)
    support_tickets_open: int = Field(default=0, ge=0)
    avg_resolution_time_hours: Optional[float] = Field(None, ge=0)
    satisfaction_score: Optional[float] = Field(None, ge=0, le=5)

    # Behavioral Metrics
    email_open_rate: Optional[float] = Field(None, ge=0, le=1)
    email_click_rate: Optional[float] = Field(None, ge=0, le=1)
    portal_login_count: int = Field(default=0, ge=0)
    last_portal_login: Optional[datetime] = None

    # Predictive Metrics
    churn_risk_score: Optional[float] = Field(None, ge=0, le=1, description="0=low risk, 1=high risk")
    upsell_likelihood: Optional[float] = Field(None, ge=0, le=1)
    next_purchase_predicted_date: Optional[datetime] = None

    # Calculated Fields
    health_score: float = Field(default=0.0, ge=0, le=100)
    engagement_level: Optional[str] = Field(None, description="high, medium, low")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "account_id": "123456789",
                "total_revenue": 50000.00,
                "ytd_revenue": 15000.00,
                "total_transactions": 24,
                "transaction_frequency": 2.5,
                "health_score": 85.0,
                "churn_risk_score": 0.15
            }
        }
    )
```

### 3.3 Transaction Model

```python
class TransactionType(str, Enum):
    """Transaction type enumeration."""
    INVOICE = "invoice"
    PAYMENT = "payment"
    CREDIT_NOTE = "credit_note"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"

class TransactionStatus(str, Enum):
    """Transaction status enumeration."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class Transaction(SerGasBaseModel):
    """Financial transaction model."""

    # References
    zoho_transaction_id: str = Field(..., description="Zoho Books transaction ID")
    account_id: str = Field(..., description="Reference to Account")

    # Transaction Details
    transaction_type: TransactionType
    transaction_number: str
    transaction_date: datetime
    due_date: Optional[datetime] = None

    # Financial Details
    subtotal: float = Field(..., ge=0)
    tax_amount: float = Field(default=0.0, ge=0)
    discount_amount: float = Field(default=0.0, ge=0)
    total_amount: float = Field(..., ge=0)
    currency: str = Field(default="USD")

    # Status
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    payment_status: Optional[str] = None

    # Line Items
    line_items: List["LineItem"] = Field(default_factory=list)

    # Metadata
    description: Optional[str] = None
    notes: Optional[str] = None
    reference_number: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    @validator('total_amount')
    def validate_total(cls, v, values):
        """Validate total amount calculation."""
        if 'subtotal' in values and 'tax_amount' in values and 'discount_amount' in values:
            expected_total = values['subtotal'] + values['tax_amount'] - values['discount_amount']
            if abs(v - expected_total) > 0.01:
                raise ValueError(f'Total amount {v} does not match calculated total {expected_total}')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "zoho_transaction_id": "TXN-123456",
                "account_id": "123456789",
                "transaction_type": "invoice",
                "transaction_number": "INV-2024-001",
                "transaction_date": "2024-01-15T10:00:00Z",
                "subtotal": 1000.00,
                "tax_amount": 80.00,
                "total_amount": 1080.00,
                "status": "completed"
            }
        }
    )

class LineItem(BaseModel):
    """Transaction line item model."""

    item_id: Optional[str] = None
    item_name: str
    description: Optional[str] = None
    quantity: float = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)
    discount_percent: float = Field(default=0.0, ge=0, le=100)
    tax_percent: float = Field(default=0.0, ge=0, le=100)
    line_total: float = Field(..., ge=0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "item_name": "Professional Services",
                "quantity": 10.0,
                "unit_price": 100.00,
                "line_total": 1000.00
            }
        }
    )
```

## 4. Recommendation Data Models

### 4.1 Recommendation Model

```python
class RecommendationType(str, Enum):
    """Recommendation type enumeration."""
    UPSELL = "upsell"
    CROSS_SELL = "cross_sell"
    RETENTION = "retention"
    ENGAGEMENT = "engagement"
    PAYMENT_TERMS = "payment_terms"
    CREDIT_ADJUSTMENT = "credit_adjustment"
    CUSTOM = "custom"

class RecommendationPriority(str, Enum):
    """Recommendation priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class RecommendationStatus(str, Enum):
    """Recommendation status."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    EXPIRED = "expired"

class Recommendation(SerGasBaseModel):
    """Recommendation model for account actions."""

    # References
    account_id: str = Field(..., description="Target account ID")
    generated_by_agent: str = Field(..., description="Agent that generated recommendation")

    # Recommendation Details
    recommendation_type: RecommendationType
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)

    # Priority and Timing
    priority: RecommendationPriority = Field(default=RecommendationPriority.MEDIUM)
    confidence_score: float = Field(..., ge=0, le=1, description="Model confidence in recommendation")
    expected_impact: Optional[str] = None

    # Status
    status: RecommendationStatus = Field(default=RecommendationStatus.PENDING)
    valid_until: Optional[datetime] = Field(None, description="Expiration date")

    # Action Details
    suggested_actions: List["ActionItem"] = Field(default_factory=list)
    required_resources: List[str] = Field(default_factory=list)
    estimated_time: Optional[str] = None

    # Financial Impact
    estimated_revenue_impact: Optional[float] = None
    estimated_cost: Optional[float] = None
    estimated_roi: Optional[float] = None

    # Context and Reasoning
    reasoning: str = Field(..., description="Why this recommendation was generated")
    supporting_data: Dict[str, Any] = Field(default_factory=dict)
    similar_cases: List[str] = Field(default_factory=list, description="Similar successful cases")

    # Implementation Tracking
    implemented_at: Optional[datetime] = None
    implemented_by: Optional[str] = None
    actual_impact: Optional[str] = None
    feedback: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "account_id": "123456789",
                "generated_by_agent": "recommendation_agent",
                "recommendation_type": "upsell",
                "title": "Upgrade to Premium Plan",
                "description": "Customer usage patterns indicate they would benefit from premium features",
                "priority": "high",
                "confidence_score": 0.85,
                "status": "pending",
                "estimated_revenue_impact": 5000.00,
                "reasoning": "Usage data shows 90% utilization of current plan limits"
            }
        }
    )

class ActionItem(BaseModel):
    """Individual action item within a recommendation."""

    action_id: str = Field(default_factory=lambda: str(uuid4()))
    action_type: str
    description: str
    priority: int = Field(..., ge=1, le=5)
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str = Field(default="pending")
    completion_notes: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "action_type": "send_email",
                "description": "Send premium plan upgrade offer to customer",
                "priority": 1,
                "status": "pending"
            }
        }
    )
```

### 4.2 Recommendation Context Model

```python
class RecommendationContext(SerGasBaseModel):
    """Context data used to generate recommendations."""

    account_id: str
    recommendation_id: Optional[str] = None

    # Account Context
    account_metrics: Optional[AccountMetrics] = None
    recent_transactions: List[Transaction] = Field(default_factory=list)

    # Historical Patterns
    historical_patterns: Dict[str, Any] = Field(default_factory=dict)
    seasonal_trends: Dict[str, Any] = Field(default_factory=dict)

    # Comparative Analysis
    peer_group_metrics: Optional[Dict[str, Any]] = None
    industry_benchmarks: Optional[Dict[str, Any]] = None

    # Knowledge Graph Data
    cognee_insights: List[Dict[str, Any]] = Field(default_factory=list)
    related_accounts: List[str] = Field(default_factory=list)

    # External Factors
    market_conditions: Optional[Dict[str, Any]] = None
    seasonal_factors: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "account_id": "123456789",
                "historical_patterns": {
                    "avg_monthly_spend": 2500.00,
                    "purchase_frequency": "monthly",
                    "preferred_payment_method": "credit_card"
                },
                "peer_group_metrics": {
                    "avg_revenue": 3000.00,
                    "avg_transaction_size": 500.00
                }
            }
        }
    )
```

## 5. Audit Trail Models

### 5.1 Audit Event Model

```python
class AuditEventType(str, Enum):
    """Audit event type enumeration."""
    AGENT_SESSION_START = "agent_session_start"
    AGENT_SESSION_END = "agent_session_end"
    TOOL_EXECUTION = "tool_execution"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    RECOMMENDATION_GENERATED = "recommendation_generated"
    RECOMMENDATION_IMPLEMENTED = "recommendation_implemented"
    PERMISSION_DENIED = "permission_denied"
    ERROR_OCCURRED = "error_occurred"
    CONFIGURATION_CHANGED = "configuration_changed"

class AuditSeverity(str, Enum):
    """Audit event severity."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AuditEvent(SerGasBaseModel):
    """Comprehensive audit event model."""

    # Event Identification
    event_id: UUID = Field(default_factory=uuid4)
    event_type: AuditEventType
    event_timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Context
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None

    # Event Details
    event_description: str
    severity: AuditSeverity = Field(default=AuditSeverity.INFO)

    # Action Details
    action_taken: Optional[str] = None
    resource_affected: Optional[str] = None
    resource_type: Optional[str] = None

    # Data Changes
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    changes: Optional[Dict[str, Any]] = None

    # Tool/Operation Details
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Any] = None
    tool_duration_ms: Optional[int] = Field(None, ge=0)

    # Status
    status: str = Field(default="completed")
    error_message: Optional[str] = None
    error_trace: Optional[str] = None

    # Metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    additional_context: Dict[str, Any] = Field(default_factory=dict)

    # Compliance
    compliance_tags: List[str] = Field(default_factory=list)
    data_classification: Optional[str] = None
    retention_period_days: int = Field(default=365)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_type": "tool_execution",
                "event_description": "Executed zoho_query_accounts tool",
                "agent_id": "account_agent",
                "session_id": "session-123",
                "tool_name": "zoho_query_accounts",
                "tool_input": {"query": "status:active", "limit": 10},
                "tool_duration_ms": 1250,
                "status": "completed",
                "severity": "info"
            }
        }
    )
```

### 5.2 Audit Trail Query Model

```python
class AuditTrailQuery(BaseModel):
    """Query parameters for audit trail search."""

    # Time Range
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Filters
    event_types: Optional[List[AuditEventType]] = None
    agent_ids: Optional[List[str]] = None
    session_ids: Optional[List[str]] = None
    severities: Optional[List[AuditSeverity]] = None
    resource_types: Optional[List[str]] = None

    # Search
    search_term: Optional[str] = None
    tags: Optional[List[str]] = None

    # Pagination
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=1000)

    # Sorting
    sort_by: str = Field(default="event_timestamp")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-31T23:59:59Z",
                "event_types": ["tool_execution", "data_modification"],
                "agent_ids": ["account_agent"],
                "page": 1,
                "page_size": 50
            }
        }
    )

class AuditTrailResponse(BaseModel):
    """Response model for audit trail queries."""

    total_count: int
    page: int
    page_size: int
    total_pages: int
    events: List[AuditEvent]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_count": 150,
                "page": 1,
                "page_size": 50,
                "total_pages": 3,
                "events": []
            }
        }
    )
```

## 6. Agent Context Models

### 6.1 Agent Session Model

```python
class AgentSessionStatus(str, Enum):
    """Agent session status."""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class AgentSession(SerGasBaseModel):
    """Agent execution session tracking."""

    session_id: str = Field(..., description="Unique session identifier")
    agent_id: str = Field(..., description="Agent identifier")
    agent_type: str = Field(..., description="Type of agent")

    # Session Lifecycle
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    status: AgentSessionStatus = Field(default=AgentSessionStatus.ACTIVE)

    # Task Information
    task_description: str
    task_context: Dict[str, Any] = Field(default_factory=dict)

    # Execution Metrics
    iterations_completed: int = Field(default=0, ge=0)
    tools_called: List[str] = Field(default_factory=list)
    tool_call_count: int = Field(default=0, ge=0)
    tokens_used: Optional[int] = Field(None, ge=0)

    # Results
    output: Optional[str] = None
    structured_results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    # Resource Usage
    memory_usage_mb: Optional[float] = None
    cpu_time_seconds: Optional[float] = None
    api_calls_made: int = Field(default=0, ge=0)

    # Quality Metrics
    success: bool = Field(default=False)
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    quality_score: Optional[float] = Field(None, ge=0, le=1)

    # Metadata
    parent_session_id: Optional[str] = None
    child_session_ids: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "session-abc123",
                "agent_id": "account_agent",
                "agent_type": "AccountAgent",
                "task_description": "Analyze account ACC-12345",
                "status": "completed",
                "iterations_completed": 5,
                "tool_call_count": 12,
                "success": True
            }
        }
    )
```

### 6.2 Agent Memory Model

```python
class MemoryType(str, Enum):
    """Memory storage type."""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"

class AgentMemory(SerGasBaseModel):
    """Agent memory storage for context retention."""

    memory_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    session_id: Optional[str] = None

    # Memory Classification
    memory_type: MemoryType
    memory_key: str = Field(..., description="Unique key for retrieval")

    # Content
    content: Dict[str, Any] = Field(..., description="Memory content")
    content_summary: Optional[str] = None

    # Metadata
    importance_score: float = Field(default=0.5, ge=0, le=1)
    access_count: int = Field(default=0, ge=0)
    last_accessed: Optional[datetime] = None

    # Temporal
    expires_at: Optional[datetime] = None
    is_expired: bool = Field(default=False)

    # Relationships
    related_memory_ids: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

    # Vector Embedding (for semantic search)
    embedding: Optional[List[float]] = None

    def mark_accessed(self):
        """Update access tracking."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()

    def check_expiration(self) -> bool:
        """Check if memory has expired."""
        if self.expires_at and datetime.utcnow() > self.expires_at:
            self.is_expired = True
        return self.is_expired

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "agent_id": "account_agent",
                "session_id": "session-abc123",
                "memory_type": "episodic",
                "memory_key": "account_analysis_ACC-12345",
                "content": {
                    "account_id": "ACC-12345",
                    "analysis_result": "High-value customer with growth potential"
                },
                "importance_score": 0.8
            }
        }
    )
```

## 7. Configuration Models

### 7.1 Agent Configuration Model

```python
class AgentConfig(BaseModel):
    """Configuration for individual agent."""

    agent_id: str
    agent_name: str
    agent_type: str

    # System Prompt
    system_prompt: str
    system_prompt_template: Optional[str] = None

    # Permissions
    allowed_tools: List[str] = Field(default_factory=list)
    disallowed_tools: List[str] = Field(default_factory=list)
    permission_mode: str = Field(default="default")

    # Behavior
    max_iterations: int = Field(default=10, ge=1)
    timeout_seconds: int = Field(default=300, ge=1)
    enable_memory: bool = Field(default=True)
    enable_audit: bool = Field(default=True)

    # MCP Servers
    mcp_servers: List[str] = Field(default_factory=list)

    # Model Configuration
    model_name: str = Field(default="claude-sonnet-4-5-20250929")
    temperature: float = Field(default=0.7, ge=0, le=1)
    max_tokens: int = Field(default=8192, ge=1)

    # Hooks
    enable_hooks: bool = Field(default=True)
    custom_hooks: Dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "agent_id": "account_agent",
                "agent_name": "Account Management Agent",
                "agent_type": "AccountAgent",
                "system_prompt": "You are an expert account manager...",
                "allowed_tools": ["read", "write", "zoho_query_accounts"],
                "max_iterations": 10,
                "timeout_seconds": 300
            }
        }
    )
```

### 7.2 System Configuration Model

```python
class SystemConfig(BaseModel):
    """Global system configuration."""

    # Environment
    environment: str = Field(default="development")
    debug_mode: bool = Field(default=False)

    # API Keys
    anthropic_api_key: str
    zoho_client_id: str
    zoho_client_secret: str
    cognee_api_key: str

    # Database
    database_url: str
    redis_url: Optional[str] = None

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    # Agent Defaults
    default_max_iterations: int = Field(default=10)
    default_timeout_seconds: int = Field(default=300)
    default_permission_mode: str = Field(default="default")

    # Performance
    max_concurrent_agents: int = Field(default=5, ge=1)
    max_tool_retries: int = Field(default=3, ge=0)
    tool_timeout_seconds: int = Field(default=60, ge=1)

    # Monitoring
    enable_metrics: bool = Field(default=True)
    metrics_port: int = Field(default=9090)
    enable_tracing: bool = Field(default=False)

    # Security
    enable_audit_logging: bool = Field(default=True)
    audit_retention_days: int = Field(default=365, ge=1)
    enable_encryption: bool = Field(default=True)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "environment": "production",
                "log_level": "INFO",
                "max_concurrent_agents": 5,
                "enable_metrics": True
            }
        }
    )
```

## 8. Response Models

### 8.1 API Response Wrapper

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    success: bool
    message: str
    data: Optional[T] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {},
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }
    )

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response."""

    items: List[T]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total_count": 100,
                "page": 1,
                "page_size": 10,
                "total_pages": 10,
                "has_next": True,
                "has_previous": False
            }
        }
    )
```

---

## Summary

This data models specification provides comprehensive type-safe models for:

- **Account Management**: Core account data, metrics, and transactions
- **Recommendations**: AI-generated recommendations with context
- **Audit Trails**: Comprehensive event tracking and compliance
- **Agent Context**: Session tracking and memory management
- **Configuration**: Agent and system configuration
- **API Responses**: Standardized response formats

All models use Pydantic v2 for:
- Automatic validation
- Type safety
- JSON serialization/deserialization
- OpenAPI schema generation
- Clear documentation with examples

These models serve as the foundation for the entire Sergas Agents system, ensuring data consistency, type safety, and clear contracts between all components.
