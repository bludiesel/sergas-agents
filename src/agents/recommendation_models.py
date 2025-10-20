"""Pydantic models for recommendation author agent.

This module defines all data models used by the Recommendation Author subagent
including recommendations, confidence scores, email drafts, and task suggestions.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class RecommendationType(str, Enum):
    """Types of recommendations that can be generated."""

    FOLLOW_UP_EMAIL = "follow_up_email"
    ESCALATION = "escalation"
    SCHEDULE_MEETING = "schedule_meeting"
    UPDATE_ACCOUNT = "update_account"
    CREATE_TASK = "create_task"
    RENEWAL_REMINDER = "renewal_reminder"
    UPSELL_OPPORTUNITY = "upsell_opportunity"
    RISK_MITIGATION = "risk_mitigation"
    EXECUTIVE_ALIGNMENT = "executive_alignment"
    RE_ENGAGEMENT = "re_engagement"


class Priority(str, Enum):
    """Priority levels for recommendations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceLevel(str, Enum):
    """Confidence levels for recommendations."""

    HIGH = "high"      # 0.8-1.0
    MEDIUM = "medium"  # 0.6-0.79
    LOW = "low"        # 0.5-0.59


class EscalationReason(str, Enum):
    """Reasons for escalating an account."""

    DEAL_RISK = "deal_risk"
    CHURN_RISK = "churn_risk"
    STALLED_DEAL = "stalled_deal"
    EXECUTIVE_INTERVENTION = "executive_intervention"
    TECHNICAL_ESCALATION = "technical_escalation"
    PRICING_APPROVAL = "pricing_approval"
    CONTRACTUAL_ISSUE = "contractual_issue"


class DataReference(BaseModel):
    """Reference to data source supporting a recommendation."""

    source_type: str = Field(..., description="Type of data source (zoho, cognee, memory)")
    source_id: str = Field(..., description="Unique identifier for the data source")
    entity_type: str = Field(..., description="Type of entity (account, deal, contact, etc.)")
    entity_id: str = Field(..., description="Entity identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When data was retrieved")
    field_name: Optional[str] = Field(None, description="Specific field referenced")
    field_value: Optional[Any] = Field(None, description="Value of the field")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConfidenceScore(BaseModel):
    """Detailed confidence score breakdown."""

    overall: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    level: ConfidenceLevel = Field(..., description="Confidence level category")
    data_recency: float = Field(..., ge=0.0, le=1.0, description="Score based on data freshness")
    pattern_strength: float = Field(..., ge=0.0, le=1.0, description="Score based on pattern occurrence")
    evidence_quality: float = Field(..., ge=0.0, le=1.0, description="Score based on evidence quality")
    historical_accuracy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Past recommendation success rate")
    rationale: str = Field(..., description="Explanation of confidence score")

    @model_validator(mode='after')
    def validate_confidence_level(self) -> 'ConfidenceScore':
        """Ensure level matches overall score."""
        if self.overall >= 0.8:
            expected_level = ConfidenceLevel.HIGH
        elif self.overall >= 0.6:
            expected_level = ConfidenceLevel.MEDIUM
        else:
            expected_level = ConfidenceLevel.LOW

        if self.level != expected_level:
            self.level = expected_level

        return self


class NextStep(BaseModel):
    """Individual next step in an action plan."""

    description: str = Field(..., description="What should be done")
    timeline: str = Field(..., description="When it should be done (e.g., 'within 48 hours')")
    owner: Optional[str] = Field(None, description="Who should do it")
    dependencies: List[str] = Field(default_factory=list, description="Other steps that must complete first")


class ActionSuggestion(BaseModel):
    """Suggested action with detailed guidance."""

    action_type: str = Field(..., description="Type of action (call, email, meeting, etc.)")
    description: str = Field(..., description="What to do")
    subject: Optional[str] = Field(None, description="Email subject or meeting title")
    draft_body: Optional[str] = Field(None, description="Draft content (email body, notes, etc.)")
    next_steps: List[NextStep] = Field(default_factory=list, description="Subsequent steps")
    estimated_effort_minutes: int = Field(default=15, ge=5, le=480, description="Time required")
    crm_updates: Optional[Dict[str, Any]] = Field(None, description="Suggested CRM field updates")

    @field_validator('estimated_effort_minutes')
    @classmethod
    def validate_effort(cls, v: int) -> int:
        """Round effort to reasonable intervals."""
        if v < 15:
            return 15
        elif v <= 30:
            return 30
        elif v <= 60:
            return 60
        else:
            return ((v + 29) // 30) * 30  # Round to nearest 30 minutes


class EmailDraft(BaseModel):
    """Draft email with personalization."""

    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body content")
    to_contacts: List[str] = Field(..., description="Recipient contact IDs or emails")
    cc_contacts: List[str] = Field(default_factory=list, description="CC contact IDs or emails")
    template_id: Optional[str] = Field(None, description="Template used for generation")
    personalization_fields: Dict[str, str] = Field(default_factory=dict, description="Fields used for personalization")
    tone: str = Field(default="professional", description="Email tone")
    urgency: Priority = Field(default=Priority.MEDIUM, description="Email urgency")

    @field_validator('body')
    @classmethod
    def validate_body_length(cls, v: str) -> str:
        """Ensure email body is reasonable length."""
        if len(v.strip()) < 50:
            raise ValueError("Email body too short (minimum 50 characters)")
        if len(v) > 5000:
            raise ValueError("Email body too long (maximum 5000 characters)")
        return v


class TaskSuggestion(BaseModel):
    """Suggested task for CRM."""

    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    due_date: datetime = Field(..., description="When task is due")
    priority: Priority = Field(default=Priority.MEDIUM, description="Task priority")
    assigned_to: Optional[str] = Field(None, description="User ID to assign to")
    related_to: Dict[str, str] = Field(..., description="Related entities (account_id, deal_id, etc.)")
    task_type: str = Field(default="follow_up", description="Type of task")
    estimated_hours: float = Field(default=1.0, ge=0.25, le=40.0, description="Estimated hours")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Escalation(BaseModel):
    """Escalation details for high-risk situations."""

    escalate_to: str = Field(..., description="Who to escalate to (role or user ID)")
    reason: EscalationReason = Field(..., description="Why escalation is needed")
    severity: Priority = Field(..., description="Escalation severity")
    context: str = Field(..., description="Context for the escalation")
    recommended_actions: List[str] = Field(..., description="What should be done")
    timeline: str = Field(..., description="How quickly action is needed")
    risk_if_ignored: str = Field(..., description="Consequences of not escalating")
    supporting_data: List[DataReference] = Field(default_factory=list, description="Evidence for escalation")

    @field_validator('recommended_actions')
    @classmethod
    def validate_actions(cls, v: List[str]) -> List[str]:
        """Ensure at least one action is recommended."""
        if not v:
            raise ValueError("At least one recommended action is required")
        return v


class InsightsSynthesis(BaseModel):
    """Synthesized insights from data sources."""

    account_id: str = Field(..., description="Account this synthesis is for")
    risk_level: Priority = Field(..., description="Overall risk assessment")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    opportunities: List[str] = Field(default_factory=list, description="Identified opportunities")
    engagement_health: float = Field(..., ge=0.0, le=1.0, description="Engagement health score")
    sentiment_trend: str = Field(..., description="Sentiment direction (improving/stable/declining)")
    key_patterns: List[str] = Field(default_factory=list, description="Important patterns observed")
    data_sources: List[DataReference] = Field(..., description="Sources used for synthesis")
    synthesized_at: datetime = Field(default_factory=datetime.utcnow, description="When synthesis was created")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Recommendation(BaseModel):
    """Complete recommendation with all details."""

    recommendation_id: str = Field(..., description="Unique recommendation identifier")
    account_id: str = Field(..., description="Account this recommendation is for")
    account_name: str = Field(..., description="Account name for display")
    owner_id: str = Field(..., description="Account owner user ID")
    owner_name: str = Field(..., description="Account owner name")

    type: RecommendationType = Field(..., description="Type of recommendation")
    priority: Priority = Field(..., description="Recommendation priority")

    title: str = Field(..., description="Short recommendation title")
    rationale: str = Field(..., description="Why this recommendation is being made")

    confidence: ConfidenceScore = Field(..., description="Confidence score breakdown")

    suggested_action: ActionSuggestion = Field(..., description="Primary action to take")
    email_draft: Optional[EmailDraft] = Field(None, description="Email draft if applicable")
    task_suggestion: Optional[TaskSuggestion] = Field(None, description="Task suggestion if applicable")
    escalation: Optional[Escalation] = Field(None, description="Escalation details if applicable")

    data_references: List[DataReference] = Field(..., description="Supporting data sources")
    insights_used: Optional[InsightsSynthesis] = Field(None, description="Synthesized insights used")

    generated_at: datetime = Field(default_factory=datetime.utcnow, description="When recommendation was generated")
    expires_at: Optional[datetime] = Field(None, description="When recommendation expires")

    status: str = Field(default="pending", description="Recommendation status")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Ensure title is concise."""
        if len(v) > 150:
            raise ValueError("Title too long (maximum 150 characters)")
        return v

    @field_validator('rationale')
    @classmethod
    def validate_rationale(cls, v: str) -> str:
        """Ensure rationale is substantive."""
        if len(v.strip()) < 20:
            raise ValueError("Rationale too short (minimum 20 characters)")
        return v

    @model_validator(mode='after')
    def validate_type_consistency(self) -> 'Recommendation':
        """Ensure fields match recommendation type."""
        if self.type == RecommendationType.FOLLOW_UP_EMAIL and not self.email_draft:
            raise ValueError("Email draft required for follow_up_email type")

        if self.type == RecommendationType.ESCALATION and not self.escalation:
            raise ValueError("Escalation details required for escalation type")

        if self.type == RecommendationType.CREATE_TASK and not self.task_suggestion:
            raise ValueError("Task suggestion required for create_task type")

        return self


class RecommendationBatch(BaseModel):
    """Batch of recommendations for an account."""

    account_id: str = Field(..., description="Account ID")
    recommendations: List[Recommendation] = Field(..., description="All recommendations for this account")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Batch generation time")
    total_count: int = Field(..., description="Total number of recommendations")
    priority_breakdown: Dict[str, int] = Field(default_factory=dict, description="Count by priority")

    @model_validator(mode='after')
    def validate_consistency(self) -> 'RecommendationBatch':
        """Ensure counts match."""
        if self.total_count != len(self.recommendations):
            self.total_count = len(self.recommendations)

        # Calculate priority breakdown
        breakdown: Dict[str, int] = {}
        for rec in self.recommendations:
            priority_str = rec.priority.value
            breakdown[priority_str] = breakdown.get(priority_str, 0) + 1
        self.priority_breakdown = breakdown

        return self

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RecommendationContext(BaseModel):
    """Context needed for generating recommendations."""

    account_data: Dict[str, Any] = Field(..., description="Account data from Zoho Data Scout")
    historical_context: Dict[str, Any] = Field(..., description="Historical context from Memory Analyst")
    run_config: Dict[str, Any] = Field(default_factory=dict, description="Run configuration")
    priority_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "critical": 1.0,
            "high": 0.75,
            "medium": 0.5,
            "low": 0.25
        },
        description="Priority weighting factors"
    )


class RecommendationResult(BaseModel):
    """Result of recommendation generation process."""

    success: bool = Field(..., description="Whether generation succeeded")
    account_id: str = Field(..., description="Account ID")
    recommendations: List[Recommendation] = Field(default_factory=list, description="Generated recommendations")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    processing_time_ms: int = Field(..., description="Time taken to generate")
    data_sources_used: List[str] = Field(default_factory=list, description="Data sources accessed")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
