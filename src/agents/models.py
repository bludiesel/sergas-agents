"""Data Scout Agent - Pydantic Models.

Complete data structures for Zoho Data Scout subagent following
SPARC architecture specifications (lines 170-227).

All models with:
- 100% type hints
- Validation logic
- JSON serialization support
- Immutable where appropriate
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
from decimal import Decimal


class ChangeType(str, Enum):
    """Types of account changes detected."""
    OWNER_CHANGE = "owner_change"
    STATUS_CHANGE = "status_change"
    DEAL_STALLED = "deal_stalled"
    HIGH_VALUE_ACTIVITY = "high_value_activity"
    INACTIVITY_THRESHOLD = "inactivity_threshold"
    CONTACT_ADDED = "contact_added"
    CUSTOM_FIELD_MODIFIED = "custom_field_modified"
    NEW_ACCOUNT = "new_account"
    DEAL_STAGE_CHANGE = "deal_stage_change"
    REVENUE_CHANGE = "revenue_change"


class AccountStatus(str, Enum):
    """Account status values."""
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    AT_RISK = "At Risk"
    CLOSED = "Closed"
    PENDING = "Pending"
    ONBOARDING = "Onboarding"


class DealStage(str, Enum):
    """Deal pipeline stages."""
    QUALIFICATION = "Qualification"
    NEEDS_ANALYSIS = "Needs Analysis"
    VALUE_PROPOSITION = "Value Proposition"
    PROPOSAL = "Proposal"
    NEGOTIATION = "Negotiation"
    CLOSED_WON = "Closed Won"
    CLOSED_LOST = "Closed Lost"
    STALLED = "Stalled"


class RiskLevel(str, Enum):
    """Account risk assessment levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class ActivityType(str, Enum):
    """CRM activity types."""
    CALL = "Call"
    EMAIL = "Email"
    MEETING = "Meeting"
    TASK = "Task"
    DEMO = "Demo"
    CONTRACT_REVIEW = "Contract Review"
    EXECUTIVE_MEETING = "Executive Meeting"
    NOTE = "Note"


class FieldChange(BaseModel):
    """Individual field change detection."""
    model_config = ConfigDict(frozen=True)

    field_name: str = Field(..., description="Field that changed")
    old_value: Any = Field(None, description="Previous value")
    new_value: Any = Field(..., description="New value")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When change occurred")
    change_type: ChangeType = Field(..., description="Type of change")

    def __hash__(self) -> int:
        """Make hashable for use in sets."""
        return hash((self.field_name, str(self.old_value), str(self.new_value)))


class DealRecord(BaseModel):
    """Deal/opportunity record from Zoho CRM."""
    deal_id: str = Field(..., description="Zoho deal ID")
    deal_name: str = Field(..., description="Deal name")
    account_id: str = Field(..., description="Associated account ID")
    stage: DealStage = Field(..., description="Current pipeline stage")
    amount: Decimal = Field(default=Decimal("0"), description="Deal value")
    probability: int = Field(default=0, ge=0, le=100, description="Win probability %")
    closing_date: Optional[datetime] = Field(None, description="Expected close date")
    created_time: datetime = Field(default_factory=datetime.utcnow, description="Created timestamp")
    modified_time: datetime = Field(default_factory=datetime.utcnow, description="Last modified")
    stage_changed_date: Optional[datetime] = Field(None, description="Last stage change")
    owner_id: str = Field(..., description="Deal owner ID")
    owner_name: str = Field("", description="Deal owner name")
    is_stalled: bool = Field(default=False, description="Deal stalled in stage >30 days")
    days_in_stage: int = Field(default=0, ge=0, description="Days in current stage")

    @field_validator("amount", mode="before")
    @classmethod
    def convert_amount(cls, v: Any) -> Decimal:
        """Convert amount to Decimal."""
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v

    def calculate_stalled_status(self, threshold_days: int = 30) -> bool:
        """Calculate if deal is stalled.

        Args:
            threshold_days: Days threshold for stalled status

        Returns:
            True if deal is stalled
        """
        if not self.stage_changed_date:
            return False

        days_in_stage = (datetime.utcnow() - self.stage_changed_date).days
        return days_in_stage > threshold_days


class ActivityRecord(BaseModel):
    """CRM activity record."""
    activity_id: str = Field(..., description="Activity ID")
    account_id: str = Field(..., description="Associated account ID")
    activity_type: ActivityType = Field(..., description="Activity type")
    subject: str = Field("", description="Activity subject")
    description: str = Field("", description="Activity description")
    created_time: datetime = Field(default_factory=datetime.utcnow, description="Created timestamp")
    modified_time: datetime = Field(default_factory=datetime.utcnow, description="Last modified")
    owner_id: str = Field(..., description="Activity owner ID")
    owner_name: str = Field("", description="Activity owner name")
    participants: List[str] = Field(default_factory=list, description="Participant names")
    is_high_value: bool = Field(default=False, description="High-value activity")
    outcome: Optional[str] = Field(None, description="Activity outcome")

    def is_recent(self, days: int = 30) -> bool:
        """Check if activity is recent.

        Args:
            days: Number of days to consider recent

        Returns:
            True if activity within threshold
        """
        age = (datetime.utcnow() - self.created_time).days
        return age <= days


class NoteRecord(BaseModel):
    """CRM note record."""
    note_id: str = Field(..., description="Note ID")
    account_id: str = Field(..., description="Associated account ID")
    title: str = Field("", description="Note title")
    content: str = Field(..., description="Note content")
    created_time: datetime = Field(default_factory=datetime.utcnow, description="Created timestamp")
    modified_time: datetime = Field(default_factory=datetime.utcnow, description="Last modified")
    created_by_id: str = Field(..., description="Creator ID")
    created_by_name: str = Field("", description="Creator name")
    is_private: bool = Field(default=False, description="Private note flag")


class RiskSignal(BaseModel):
    """Risk indicator for account."""
    signal_type: str = Field(..., description="Type of risk signal")
    description: str = Field(..., description="Human-readable description")
    severity: RiskLevel = Field(..., description="Risk severity level")
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="Detection timestamp")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    requires_action: bool = Field(default=False, description="Immediate action needed")

    @field_validator("signal_type")
    @classmethod
    def validate_signal_type(cls, v: str) -> str:
        """Validate signal type is not empty."""
        if not v or not v.strip():
            raise ValueError("signal_type cannot be empty")
        return v.strip()


class AccountRecord(BaseModel):
    """Core account record from Zoho CRM."""
    account_id: str = Field(..., description="Zoho account ID")
    account_name: str = Field(..., description="Account name")
    owner_id: str = Field(..., description="Account owner ID")
    owner_name: str = Field("", description="Account owner name")
    status: AccountStatus = Field(default=AccountStatus.ACTIVE, description="Account status")
    last_modified: datetime = Field(default_factory=datetime.utcnow, description="Last modified timestamp")
    last_activity_date: Optional[datetime] = Field(None, description="Most recent activity")
    created_time: datetime = Field(default_factory=datetime.utcnow, description="Created timestamp")

    # Business metrics
    deal_count: int = Field(default=0, ge=0, description="Number of open deals")
    total_value: Decimal = Field(default=Decimal("0"), description="Total deal value")
    annual_revenue: Decimal = Field(default=Decimal("0"), description="Annual revenue")

    # Metadata
    industry: str = Field("", description="Industry sector")
    website: str = Field("", description="Company website")
    phone: str = Field("", description="Primary phone")
    billing_city: str = Field("", description="Billing city")
    billing_country: str = Field("", description="Billing country")

    # Custom fields
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom field data")

    # Change tracking
    change_flags: Set[ChangeType] = Field(default_factory=set, description="Detected changes")

    @field_validator("total_value", "annual_revenue", mode="before")
    @classmethod
    def convert_currency(cls, v: Any) -> Decimal:
        """Convert currency values to Decimal."""
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v

    def days_since_activity(self) -> int:
        """Calculate days since last activity.

        Returns:
            Number of days since last activity (0 if never)
        """
        if not self.last_activity_date:
            return 0
        return (datetime.utcnow() - self.last_activity_date).days

    def has_change(self, change_type: ChangeType) -> bool:
        """Check if specific change type detected.

        Args:
            change_type: Change type to check

        Returns:
            True if change detected
        """
        return change_type in self.change_flags

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
            set: list,
        }


class AggregatedData(BaseModel):
    """Aggregated related data for account."""
    account_id: str = Field(..., description="Account identifier")

    # Related records
    deals: List[DealRecord] = Field(default_factory=list, description="Open deals")
    activities: List[ActivityRecord] = Field(default_factory=list, description="Recent activities")
    notes: List[NoteRecord] = Field(default_factory=list, description="Recent notes")

    # Summaries
    total_deal_value: Decimal = Field(default=Decimal("0"), description="Sum of deal values")
    stalled_deal_count: int = Field(default=0, ge=0, description="Number of stalled deals")
    high_value_activity_count: int = Field(default=0, ge=0, description="High-value activities")
    recent_activity_count: int = Field(default=0, ge=0, description="Activities last 30 days")

    # Timestamps
    aggregated_at: datetime = Field(default_factory=datetime.utcnow, description="Aggregation timestamp")
    data_freshness: int = Field(default=0, ge=0, description="Data age in seconds")

    def calculate_summaries(self) -> None:
        """Calculate aggregate summaries from records."""
        # Sum deal values
        self.total_deal_value = sum(
            (deal.amount for deal in self.deals),
            Decimal("0")
        )

        # Count stalled deals
        self.stalled_deal_count = sum(1 for deal in self.deals if deal.is_stalled)

        # Count high-value activities
        self.high_value_activity_count = sum(
            1 for activity in self.activities if activity.is_high_value
        )

        # Count recent activities (30 days)
        self.recent_activity_count = sum(
            1 for activity in self.activities if activity.is_recent(30)
        )


class ChangeDetectionResult(BaseModel):
    """Result of change detection analysis."""
    account_id: str = Field(..., description="Account identifier")
    changes_detected: bool = Field(default=False, description="Any changes detected")
    field_changes: List[FieldChange] = Field(default_factory=list, description="Field-level changes")
    change_types: Set[ChangeType] = Field(default_factory=set, description="Types of changes")
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="Detection timestamp")
    comparison_baseline: Optional[datetime] = Field(None, description="Last sync timestamp")
    requires_attention: bool = Field(default=False, description="Needs review flag")

    def add_change(
        self,
        field_name: str,
        old_value: Any,
        new_value: Any,
        change_type: ChangeType,
    ) -> None:
        """Add field change to result.

        Args:
            field_name: Field that changed
            old_value: Previous value
            new_value: New value
            change_type: Type of change
        """
        change = FieldChange(
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            timestamp=datetime.utcnow(),
            change_type=change_type,
        )
        self.field_changes.append(change)
        self.change_types.add(change_type)
        self.changes_detected = True

        # Mark for attention if critical change
        if change_type in {
            ChangeType.OWNER_CHANGE,
            ChangeType.STATUS_CHANGE,
            ChangeType.DEAL_STALLED,
        }:
            self.requires_attention = True

    def get_critical_changes(self) -> List[FieldChange]:
        """Get critical changes requiring attention.

        Returns:
            List of critical field changes
        """
        critical_types = {
            ChangeType.OWNER_CHANGE,
            ChangeType.STATUS_CHANGE,
            ChangeType.DEAL_STALLED,
            ChangeType.INACTIVITY_THRESHOLD,
        }
        return [
            change for change in self.field_changes
            if change.change_type in critical_types
        ]

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            set: list,
        }


class AccountSnapshot(BaseModel):
    """Complete account snapshot with all data and analysis."""
    # Core data
    account: AccountRecord = Field(..., description="Core account record")
    aggregated_data: AggregatedData = Field(..., description="Related records")
    changes: ChangeDetectionResult = Field(..., description="Change detection results")
    risk_signals: List[RiskSignal] = Field(default_factory=list, description="Risk indicators")

    # Metadata
    snapshot_id: str = Field(..., description="Unique snapshot ID")
    snapshot_time: datetime = Field(default_factory=datetime.utcnow, description="Snapshot timestamp")
    data_sources: List[str] = Field(default_factory=list, description="Data source references")

    # Analysis flags
    needs_review: bool = Field(default=False, description="Requires owner review")
    risk_level: RiskLevel = Field(default=RiskLevel.NONE, description="Overall risk level")
    priority_score: int = Field(default=0, ge=0, le=100, description="Priority score (0-100)")

    def calculate_risk_level(self) -> RiskLevel:
        """Calculate overall risk level from signals.

        Returns:
            Calculated risk level
        """
        if not self.risk_signals:
            return RiskLevel.NONE

        # Find highest severity
        severities = [signal.severity for signal in self.risk_signals]

        if RiskLevel.CRITICAL in severities:
            return RiskLevel.CRITICAL
        elif RiskLevel.HIGH in severities:
            return RiskLevel.HIGH
        elif RiskLevel.MEDIUM in severities:
            return RiskLevel.MEDIUM
        elif RiskLevel.LOW in severities:
            return RiskLevel.LOW

        return RiskLevel.NONE

    def calculate_priority_score(self) -> int:
        """Calculate priority score (0-100).

        Factors:
        - Risk level (40 points)
        - Change count (30 points)
        - Deal value (20 points)
        - Recent activity (10 points)

        Returns:
            Priority score 0-100
        """
        score = 0

        # Risk level contribution (40 points)
        risk_weights = {
            RiskLevel.CRITICAL: 40,
            RiskLevel.HIGH: 30,
            RiskLevel.MEDIUM: 20,
            RiskLevel.LOW: 10,
            RiskLevel.NONE: 0,
        }
        score += risk_weights.get(self.risk_level, 0)

        # Changes contribution (30 points)
        if self.changes.changes_detected:
            change_count = len(self.changes.field_changes)
            score += min(30, change_count * 5)

        # Deal value contribution (20 points)
        deal_value = float(self.aggregated_data.total_deal_value)
        if deal_value > 100000:
            score += 20
        elif deal_value > 50000:
            score += 15
        elif deal_value > 10000:
            score += 10

        # Recent activity contribution (10 points)
        if self.aggregated_data.recent_activity_count > 5:
            score += 10
        elif self.aggregated_data.recent_activity_count > 2:
            score += 5

        return min(100, score)

    def update_analysis_flags(self) -> None:
        """Update analysis flags based on data."""
        self.risk_level = self.calculate_risk_level()
        self.priority_score = self.calculate_priority_score()
        self.needs_review = (
            self.changes.requires_attention or
            self.risk_level in {RiskLevel.CRITICAL, RiskLevel.HIGH} or
            self.priority_score > 60
        )

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
            set: list,
        }
