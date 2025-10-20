"""Pydantic models for Memory Analyst subagent.

Defines all data structures for memory analysis, pattern recognition,
and historical context tracking.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator


class SentimentTrend(str, Enum):
    """Sentiment trend over time."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    UNKNOWN = "unknown"


class PatternType(str, Enum):
    """Types of patterns detected in account history."""
    CHURN_RISK = "churn_risk"
    UPSELL_OPPORTUNITY = "upsell_opportunity"
    RENEWAL_RISK = "renewal_risk"
    ENGAGEMENT_CYCLE = "engagement_cycle"
    EXECUTIVE_CHANGE = "executive_change"
    DEAL_STALL = "deal_stall"
    COMMITMENT_PATTERN = "commitment_pattern"
    SEASONAL_TREND = "seasonal_trend"


class CommitmentStatus(str, Enum):
    """Status of tracked commitments."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class RelationshipStrength(str, Enum):
    """Strength of account relationship."""
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    AT_RISK = "at_risk"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    """Risk level categorization."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EventType(str, Enum):
    """Types of timeline events."""
    MEETING = "meeting"
    EMAIL = "email"
    CALL = "call"
    NOTE = "note"
    DEAL_UPDATE = "deal_update"
    EXECUTIVE_CHANGE = "executive_change"
    STATUS_CHANGE = "status_change"
    RENEWAL = "renewal"
    EXPANSION = "expansion"
    ESCALATION = "escalation"


class TimelineEvent(BaseModel):
    """Single event in account timeline.

    Attributes:
        event_id: Unique event identifier
        account_id: Associated account ID
        timestamp: When event occurred
        event_type: Type of event
        description: Human-readable description
        participants: List of participant names/IDs
        outcome: Result or outcome of event
        impact: Impact level (high/medium/low)
        source_reference: Reference to source system
        metadata: Additional event metadata
    """
    event_id: str = Field(..., description="Unique event identifier")
    account_id: str = Field(..., description="Account identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    event_type: EventType = Field(..., description="Type of event")
    description: str = Field(..., description="Event description")
    participants: List[str] = Field(default_factory=list, description="Participants")
    outcome: Optional[str] = Field(None, description="Event outcome")
    impact: str = Field(default="medium", description="Impact level")
    source_reference: Optional[str] = Field(None, description="Source system reference")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('impact')
    @classmethod
    def validate_impact(cls, v: str) -> str:
        """Validate impact level."""
        if v not in ['high', 'medium', 'low']:
            raise ValueError("Impact must be high, medium, or low")
        return v


class Pattern(BaseModel):
    """Detected pattern in account history.

    Attributes:
        pattern_id: Unique pattern identifier
        pattern_type: Type of pattern detected
        confidence: Confidence score (0.0-1.0)
        description: Pattern description
        evidence: Supporting evidence
        first_detected: When pattern was first detected
        last_detected: Most recent detection
        frequency: How often pattern appears
        risk_score: Associated risk score (0-100)
        recommendations: Suggested actions
    """
    pattern_id: str = Field(..., description="Unique pattern ID")
    pattern_type: PatternType = Field(..., description="Pattern type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    description: str = Field(..., description="Pattern description")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence")
    first_detected: datetime = Field(..., description="First detection time")
    last_detected: datetime = Field(..., description="Last detection time")
    frequency: int = Field(default=1, ge=1, description="Pattern frequency")
    risk_score: int = Field(default=0, ge=0, le=100, description="Risk score")
    recommendations: List[str] = Field(default_factory=list, description="Recommended actions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SentimentAnalysis(BaseModel):
    """Sentiment trend analysis over time.

    Attributes:
        account_id: Account identifier
        overall_sentiment: Overall sentiment score (-1.0 to 1.0)
        trend: Sentiment trend direction
        recent_score: Recent period sentiment
        historical_score: Historical average sentiment
        change_rate: Rate of sentiment change
        analysis_period_days: Analysis period in days
        data_points: Number of data points analyzed
        key_factors: Factors influencing sentiment
        warnings: Sentiment-related warnings
    """
    account_id: str = Field(..., description="Account identifier")
    overall_sentiment: float = Field(..., ge=-1.0, le=1.0, description="Overall sentiment")
    trend: SentimentTrend = Field(..., description="Sentiment trend")
    recent_score: float = Field(..., ge=-1.0, le=1.0, description="Recent sentiment")
    historical_score: float = Field(..., ge=-1.0, le=1.0, description="Historical sentiment")
    change_rate: float = Field(..., description="Sentiment change rate")
    analysis_period_days: int = Field(..., gt=0, description="Analysis period")
    data_points: int = Field(..., ge=0, description="Number of data points")
    key_factors: List[str] = Field(default_factory=list, description="Influencing factors")
    warnings: List[str] = Field(default_factory=list, description="Warnings")


class PriorRecommendation(BaseModel):
    """Previously generated recommendation and outcome.

    Attributes:
        recommendation_id: Unique recommendation ID
        account_id: Account identifier
        generated_date: When recommendation was created
        recommendation: The recommendation text
        priority: Recommendation priority
        action_type: Type of action recommended
        status: Current status
        outcome: Result if completed
        follow_up_date: When follow-up occurred
        effectiveness_score: How effective (0-100)
        notes: Additional notes
    """
    recommendation_id: str = Field(..., description="Recommendation ID")
    account_id: str = Field(..., description="Account identifier")
    generated_date: datetime = Field(..., description="Generation date")
    recommendation: str = Field(..., description="Recommendation text")
    priority: str = Field(..., description="Priority level")
    action_type: str = Field(..., description="Action type")
    status: str = Field(default="pending", description="Current status")
    outcome: Optional[str] = Field(None, description="Outcome if completed")
    follow_up_date: Optional[datetime] = Field(None, description="Follow-up date")
    effectiveness_score: Optional[int] = Field(None, ge=0, le=100, description="Effectiveness")
    notes: str = Field(default="", description="Additional notes")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status value."""
        valid_statuses = ['pending', 'in_progress', 'completed', 'rejected', 'expired']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v


class RelationshipAssessment(BaseModel):
    """Assessment of account relationship strength.

    Attributes:
        account_id: Account identifier
        relationship_strength: Overall strength rating
        engagement_score: Engagement level (0.0-1.0)
        executive_alignment: Executive alignment score
        touchpoint_frequency: Recent touchpoint frequency
        response_rate: Customer response rate
        last_interaction_days: Days since last interaction
        key_contacts_count: Number of key contacts
        executive_sponsor_present: Has executive sponsor
        relationship_health_score: Overall health (0-100)
        improvement_trends: Positive trends
        degradation_risks: Negative trends
    """
    account_id: str = Field(..., description="Account identifier")
    relationship_strength: RelationshipStrength = Field(..., description="Relationship strength")
    engagement_score: float = Field(..., ge=0.0, le=1.0, description="Engagement score")
    executive_alignment: float = Field(..., ge=0.0, le=1.0, description="Executive alignment")
    touchpoint_frequency: float = Field(..., ge=0.0, description="Touchpoint frequency")
    response_rate: float = Field(..., ge=0.0, le=1.0, description="Response rate")
    last_interaction_days: int = Field(..., ge=0, description="Days since last interaction")
    key_contacts_count: int = Field(..., ge=0, description="Key contacts count")
    executive_sponsor_present: bool = Field(..., description="Executive sponsor present")
    relationship_health_score: int = Field(..., ge=0, le=100, description="Health score")
    improvement_trends: List[str] = Field(default_factory=list, description="Positive trends")
    degradation_risks: List[str] = Field(default_factory=list, description="Risk factors")


class Commitment(BaseModel):
    """Tracked commitment or promise.

    Attributes:
        commitment_id: Unique commitment ID
        account_id: Account identifier
        commitment_text: What was committed
        committed_by: Who made commitment
        committed_to: Who commitment was made to
        commitment_date: When commitment was made
        due_date: When commitment is due
        status: Current status
        completion_date: When completed
        follow_up_required: Requires follow-up
        priority: Commitment priority
        notes: Additional notes
    """
    commitment_id: str = Field(..., description="Commitment ID")
    account_id: str = Field(..., description="Account identifier")
    commitment_text: str = Field(..., description="Commitment description")
    committed_by: str = Field(..., description="Who committed")
    committed_to: str = Field(..., description="Recipient")
    commitment_date: datetime = Field(..., description="Commitment date")
    due_date: Optional[datetime] = Field(None, description="Due date")
    status: CommitmentStatus = Field(default=CommitmentStatus.PENDING, description="Status")
    completion_date: Optional[datetime] = Field(None, description="Completion date")
    follow_up_required: bool = Field(default=False, description="Needs follow-up")
    priority: str = Field(default="medium", description="Priority")
    notes: str = Field(default="", description="Notes")

    @model_validator(mode='after')
    def validate_dates(self) -> 'Commitment':
        """Validate date logic."""
        if self.completion_date and self.completion_date < self.commitment_date:
            raise ValueError("Completion date cannot be before commitment date")
        if self.due_date and self.due_date < self.commitment_date:
            raise ValueError("Due date cannot be before commitment date")
        return self


class KeyEvent(BaseModel):
    """Significant event in account history.

    Attributes:
        event_id: Unique event ID
        account_id: Account identifier
        event_date: When event occurred
        event_type: Type of event
        title: Event title
        description: Detailed description
        impact_level: Impact level
        stakeholders: Involved stakeholders
        outcome: Event outcome
        lessons_learned: Key takeaways
    """
    event_id: str = Field(..., description="Event ID")
    account_id: str = Field(..., description="Account identifier")
    event_date: datetime = Field(..., description="Event date")
    event_type: str = Field(..., description="Event type")
    title: str = Field(..., description="Event title")
    description: str = Field(..., description="Event description")
    impact_level: str = Field(default="medium", description="Impact level")
    stakeholders: List[str] = Field(default_factory=list, description="Stakeholders")
    outcome: Optional[str] = Field(None, description="Outcome")
    lessons_learned: List[str] = Field(default_factory=list, description="Lessons learned")


class EngagementMetrics(BaseModel):
    """Account engagement metrics.

    Attributes:
        account_id: Account identifier
        measurement_period_days: Measurement period
        total_interactions: Total interaction count
        meetings_count: Number of meetings
        emails_count: Number of emails
        calls_count: Number of calls
        average_response_time_hours: Avg response time
        interaction_frequency_score: Frequency score (0.0-1.0)
        quality_score: Interaction quality (0.0-1.0)
        trend: Engagement trend
    """
    account_id: str = Field(..., description="Account identifier")
    measurement_period_days: int = Field(..., gt=0, description="Measurement period")
    total_interactions: int = Field(..., ge=0, description="Total interactions")
    meetings_count: int = Field(default=0, ge=0, description="Meetings")
    emails_count: int = Field(default=0, ge=0, description="Emails")
    calls_count: int = Field(default=0, ge=0, description="Calls")
    average_response_time_hours: float = Field(default=0.0, ge=0.0, description="Avg response time")
    interaction_frequency_score: float = Field(..., ge=0.0, le=1.0, description="Frequency score")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score")
    trend: str = Field(default="stable", description="Engagement trend")


class HistoricalContext(BaseModel):
    """Complete historical context for an account.

    Main output structure from Memory Analyst matching SPARC spec.

    Attributes:
        account_id: Account identifier
        key_events: Significant events in history
        sentiment_trend: Overall sentiment trend
        prior_recommendations: Previous recommendations
        relationship_strength: Relationship assessment
        commitment_tracking: Tracked commitments
        patterns: Detected patterns
        timeline: Complete timeline of events
        engagement_metrics: Engagement statistics
        risk_level: Current risk level
        last_updated: When context was generated
    """
    account_id: str = Field(..., description="Account identifier")
    key_events: List[KeyEvent] = Field(default_factory=list, description="Key events")
    sentiment_trend: SentimentTrend = Field(..., description="Sentiment trend")
    prior_recommendations: List[PriorRecommendation] = Field(
        default_factory=list,
        description="Prior recommendations"
    )
    relationship_strength: RelationshipStrength = Field(..., description="Relationship strength")
    commitment_tracking: List[Commitment] = Field(
        default_factory=list,
        description="Tracked commitments"
    )
    patterns: List[Pattern] = Field(default_factory=list, description="Detected patterns")
    timeline: List[TimelineEvent] = Field(default_factory=list, description="Event timeline")
    engagement_metrics: Optional[EngagementMetrics] = Field(None, description="Engagement metrics")
    risk_level: RiskLevel = Field(default=RiskLevel.MEDIUM, description="Risk level")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Update timestamp")

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EngagementCycle(BaseModel):
    """Identified engagement cycle pattern.

    Attributes:
        cycle_id: Unique cycle ID
        account_id: Account identifier
        start_date: Cycle start
        end_date: Cycle end
        cycle_length_days: Cycle duration
        peak_engagement_date: Peak engagement
        low_engagement_date: Lowest engagement
        average_frequency: Average interaction frequency
        cycle_type: Type of cycle (seasonal, quarterly, etc.)
        confidence: Detection confidence
    """
    cycle_id: str = Field(..., description="Cycle ID")
    account_id: str = Field(..., description="Account identifier")
    start_date: datetime = Field(..., description="Cycle start")
    end_date: datetime = Field(..., description="Cycle end")
    cycle_length_days: int = Field(..., gt=0, description="Cycle length")
    peak_engagement_date: Optional[datetime] = Field(None, description="Peak date")
    low_engagement_date: Optional[datetime] = Field(None, description="Low date")
    average_frequency: float = Field(..., ge=0.0, description="Average frequency")
    cycle_type: str = Field(..., description="Cycle type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence")


class CommitmentPattern(BaseModel):
    """Pattern in commitment tracking.

    Attributes:
        pattern_id: Pattern ID
        account_id: Account identifier
        pattern_description: Pattern description
        commitment_count: Total commitments
        completion_rate: Rate of completion
        average_delay_days: Average delay
        common_commitment_types: Common types
        risk_indicators: Risk factors
    """
    pattern_id: str = Field(..., description="Pattern ID")
    account_id: str = Field(..., description="Account identifier")
    pattern_description: str = Field(..., description="Pattern description")
    commitment_count: int = Field(..., ge=0, description="Commitment count")
    completion_rate: float = Field(..., ge=0.0, le=1.0, description="Completion rate")
    average_delay_days: float = Field(..., ge=0.0, description="Average delay")
    common_commitment_types: List[str] = Field(default_factory=list, description="Common types")
    risk_indicators: List[str] = Field(default_factory=list, description="Risk indicators")


class Timeline(BaseModel):
    """Complete account timeline.

    Attributes:
        account_id: Account identifier
        events: All timeline events
        start_date: Timeline start
        end_date: Timeline end
        total_events: Total event count
        event_types: Distribution by type
        milestones: Key milestones
    """
    account_id: str = Field(..., description="Account identifier")
    events: List[TimelineEvent] = Field(default_factory=list, description="Timeline events")
    start_date: datetime = Field(..., description="Timeline start")
    end_date: datetime = Field(..., description="Timeline end")
    total_events: int = Field(..., ge=0, description="Total events")
    event_types: Dict[str, int] = Field(default_factory=dict, description="Event type distribution")
    milestones: List[KeyEvent] = Field(default_factory=list, description="Key milestones")


class Milestone(BaseModel):
    """Key milestone in account journey.

    Attributes:
        milestone_id: Milestone ID
        account_id: Account identifier
        milestone_date: When milestone occurred
        milestone_type: Type of milestone
        title: Milestone title
        description: Detailed description
        significance: Importance level
        impact_on_relationship: Impact assessment
    """
    milestone_id: str = Field(..., description="Milestone ID")
    account_id: str = Field(..., description="Account identifier")
    milestone_date: datetime = Field(..., description="Milestone date")
    milestone_type: str = Field(..., description="Milestone type")
    title: str = Field(..., description="Milestone title")
    description: str = Field(..., description="Description")
    significance: str = Field(default="medium", description="Significance level")
    impact_on_relationship: str = Field(..., description="Impact assessment")


class ToneAnalysis(BaseModel):
    """Communication tone analysis.

    Attributes:
        account_id: Account identifier
        overall_tone: Overall tone assessment
        formality_score: Formality level (0.0-1.0)
        positivity_score: Positivity level (0.0-1.0)
        urgency_score: Urgency level (0.0-1.0)
        confidence_score: Confidence level (0.0-1.0)
        tone_consistency: Consistency score
        notable_tone_shifts: Significant shifts
    """
    account_id: str = Field(..., description="Account identifier")
    overall_tone: str = Field(..., description="Overall tone")
    formality_score: float = Field(..., ge=0.0, le=1.0, description="Formality")
    positivity_score: float = Field(..., ge=0.0, le=1.0, description="Positivity")
    urgency_score: float = Field(..., ge=0.0, le=1.0, description="Urgency")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence")
    tone_consistency: float = Field(..., ge=0.0, le=1.0, description="Consistency")
    notable_tone_shifts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Tone shifts"
    )


class AlignmentScore(BaseModel):
    """Executive alignment assessment.

    Attributes:
        account_id: Account identifier
        overall_alignment: Overall score (0.0-1.0)
        executive_engagement_count: Executive interactions
        decision_maker_accessibility: Access score
        strategic_alignment: Strategy alignment
        sponsorship_strength: Sponsor strength
        alignment_trends: Trend indicators
    """
    account_id: str = Field(..., description="Account identifier")
    overall_alignment: float = Field(..., ge=0.0, le=1.0, description="Overall alignment")
    executive_engagement_count: int = Field(..., ge=0, description="Executive interactions")
    decision_maker_accessibility: float = Field(..., ge=0.0, le=1.0, description="Access score")
    strategic_alignment: float = Field(..., ge=0.0, le=1.0, description="Strategic alignment")
    sponsorship_strength: float = Field(..., ge=0.0, le=1.0, description="Sponsor strength")
    alignment_trends: List[str] = Field(default_factory=list, description="Trends")
