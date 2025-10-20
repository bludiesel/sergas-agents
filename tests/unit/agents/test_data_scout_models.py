"""Comprehensive Unit Tests for Data Scout Models.

Tests all 9 Pydantic models with validators, serialization, and edge cases:
- FieldChange (5+ tests)
- DealRecord (8+ tests)
- ActivityRecord (6+ tests)
- NoteRecord (4+ tests)
- RiskSignal (6+ tests)
- AccountRecord (10+ tests)
- AggregatedData (8+ tests)
- ChangeDetectionResult (8+ tests)
- AccountSnapshot (10+ tests)
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any

import pytest
from pydantic import ValidationError

from src.agents.models import (
    FieldChange,
    DealRecord,
    ActivityRecord,
    NoteRecord,
    RiskSignal,
    AccountRecord,
    AggregatedData,
    ChangeDetectionResult,
    AccountSnapshot,
    ChangeType,
    AccountStatus,
    DealStage,
    ActivityType,
    RiskLevel,
)


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestEnums:
    """Test enum definitions and values."""

    def test_change_type_enum_values(self):
        """Test ChangeType enum has expected values."""
        assert ChangeType.OWNER_CHANGE == "owner_change"
        assert ChangeType.STATUS_CHANGE == "status_change"
        assert ChangeType.DEAL_STALLED == "deal_stalled"
        assert ChangeType.NEW_ACCOUNT == "new_account"

    def test_account_status_enum_values(self):
        """Test AccountStatus enum values."""
        assert AccountStatus.ACTIVE == "Active"
        assert AccountStatus.AT_RISK == "At Risk"
        assert AccountStatus.INACTIVE == "Inactive"

    def test_deal_stage_enum_values(self):
        """Test DealStage enum values."""
        assert DealStage.QUALIFICATION == "Qualification"
        assert DealStage.NEGOTIATION == "Negotiation"
        assert DealStage.CLOSED_WON == "Closed Won"

    def test_risk_level_enum_values(self):
        """Test RiskLevel enum values."""
        assert RiskLevel.CRITICAL == "critical"
        assert RiskLevel.HIGH == "high"
        assert RiskLevel.MEDIUM == "medium"
        assert RiskLevel.LOW == "low"
        assert RiskLevel.NONE == "none"

    def test_activity_type_enum_values(self):
        """Test ActivityType enum values."""
        assert ActivityType.CALL == "Call"
        assert ActivityType.MEETING == "Meeting"
        assert ActivityType.DEMO == "Demo"


# ============================================================================
# FIELD_CHANGE TESTS
# ============================================================================

class TestFieldChange:
    """Test FieldChange model."""

    def test_field_change_creation(self):
        """Test basic FieldChange creation."""
        change = FieldChange(
            field_name="Account_Status",
            old_value="Active",
            new_value="At Risk",
            change_type=ChangeType.STATUS_CHANGE,
        )

        assert change.field_name == "Account_Status"
        assert change.old_value == "Active"
        assert change.new_value == "At Risk"
        assert change.change_type == ChangeType.STATUS_CHANGE
        assert isinstance(change.timestamp, datetime)

    def test_field_change_is_frozen(self):
        """Test FieldChange is immutable."""
        change = FieldChange(
            field_name="test",
            new_value="new",
            change_type=ChangeType.CUSTOM_FIELD_MODIFIED,
        )

        with pytest.raises(ValidationError):
            change.field_name = "modified"

    def test_field_change_hashable(self):
        """Test FieldChange is hashable for use in sets."""
        change1 = FieldChange(
            field_name="test",
            old_value="old",
            new_value="new",
            change_type=ChangeType.CUSTOM_FIELD_MODIFIED,
        )
        change2 = FieldChange(
            field_name="test",
            old_value="old",
            new_value="new",
            change_type=ChangeType.CUSTOM_FIELD_MODIFIED,
        )

        # Should be hashable
        change_set = {change1, change2}
        assert len(change_set) >= 1

    def test_field_change_with_none_old_value(self):
        """Test FieldChange with None old_value (new field)."""
        change = FieldChange(
            field_name="new_field",
            old_value=None,
            new_value="value",
            change_type=ChangeType.CUSTOM_FIELD_MODIFIED,
        )

        assert change.old_value is None
        assert change.new_value == "value"

    def test_field_change_custom_timestamp(self):
        """Test FieldChange with custom timestamp."""
        custom_time = datetime(2025, 10, 15, 12, 0, 0)
        change = FieldChange(
            field_name="test",
            new_value="new",
            timestamp=custom_time,
            change_type=ChangeType.CUSTOM_FIELD_MODIFIED,
        )

        assert change.timestamp == custom_time


# ============================================================================
# DEAL_RECORD TESTS
# ============================================================================

class TestDealRecord:
    """Test DealRecord model."""

    def test_deal_record_creation(self):
        """Test basic DealRecord creation."""
        deal = DealRecord(
            deal_id="deal_123",
            deal_name="Enterprise Deal",
            account_id="account_456",
            stage=DealStage.NEGOTIATION,
            amount=Decimal("50000"),
            probability=75,
            owner_id="owner_789",
        )

        assert deal.deal_id == "deal_123"
        assert deal.deal_name == "Enterprise Deal"
        assert deal.stage == DealStage.NEGOTIATION
        assert deal.amount == Decimal("50000")
        assert deal.probability == 75

    def test_deal_record_amount_conversion(self):
        """Test amount is converted to Decimal."""
        # From int
        deal1 = DealRecord(
            deal_id="1",
            deal_name="Test",
            account_id="acc",
            stage=DealStage.QUALIFICATION,
            amount=50000,
            owner_id="owner",
        )
        assert isinstance(deal1.amount, Decimal)
        assert deal1.amount == Decimal("50000")

        # From float
        deal2 = DealRecord(
            deal_id="2",
            deal_name="Test",
            account_id="acc",
            stage=DealStage.QUALIFICATION,
            amount=50000.50,
            owner_id="owner",
        )
        assert isinstance(deal2.amount, Decimal)

        # From string
        deal3 = DealRecord(
            deal_id="3",
            deal_name="Test",
            account_id="acc",
            stage=DealStage.QUALIFICATION,
            amount="50000",
            owner_id="owner",
        )
        assert isinstance(deal3.amount, Decimal)

    def test_deal_record_probability_validation(self):
        """Test probability must be 0-100."""
        # Valid
        deal = DealRecord(
            deal_id="1",
            deal_name="Test",
            account_id="acc",
            stage=DealStage.QUALIFICATION,
            probability=50,
            owner_id="owner",
        )
        assert deal.probability == 50

        # Invalid - too high
        with pytest.raises(ValidationError):
            DealRecord(
                deal_id="1",
                deal_name="Test",
                account_id="acc",
                stage=DealStage.QUALIFICATION,
                probability=150,
                owner_id="owner",
            )

        # Invalid - negative
        with pytest.raises(ValidationError):
            DealRecord(
                deal_id="1",
                deal_name="Test",
                account_id="acc",
                stage=DealStage.QUALIFICATION,
                probability=-10,
                owner_id="owner",
            )

    def test_deal_record_defaults(self):
        """Test DealRecord default values."""
        deal = DealRecord(
            deal_id="1",
            deal_name="Test",
            account_id="acc",
            stage=DealStage.QUALIFICATION,
            owner_id="owner",
        )

        assert deal.amount == Decimal("0")
        assert deal.probability == 0
        assert deal.is_stalled is False
        assert deal.days_in_stage == 0
        assert deal.owner_name == ""

    def test_deal_record_calculate_stalled_status(self):
        """Test calculate_stalled_status method."""
        # Not stalled - recent stage change
        deal1 = DealRecord(
            deal_id="1",
            deal_name="Test",
            account_id="acc",
            stage=DealStage.NEGOTIATION,
            stage_changed_date=datetime.utcnow() - timedelta(days=15),
            owner_id="owner",
        )
        assert not deal1.calculate_stalled_status(threshold_days=30)

        # Stalled - old stage change
        deal2 = DealRecord(
            deal_id="2",
            deal_name="Test",
            account_id="acc",
            stage=DealStage.NEGOTIATION,
            stage_changed_date=datetime.utcnow() - timedelta(days=45),
            owner_id="owner",
        )
        assert deal2.calculate_stalled_status(threshold_days=30)

        # No stage change date
        deal3 = DealRecord(
            deal_id="3",
            deal_name="Test",
            account_id="acc",
            stage=DealStage.NEGOTIATION,
            owner_id="owner",
        )
        assert not deal3.calculate_stalled_status()

    def test_deal_record_optional_fields(self):
        """Test optional fields can be None."""
        deal = DealRecord(
            deal_id="1",
            deal_name="Test",
            account_id="acc",
            stage=DealStage.QUALIFICATION,
            owner_id="owner",
            closing_date=None,
            stage_changed_date=None,
        )

        assert deal.closing_date is None
        assert deal.stage_changed_date is None

    def test_deal_record_with_all_fields(self):
        """Test DealRecord with all fields populated."""
        closing = datetime(2025, 12, 31)
        created = datetime(2025, 9, 1)
        modified = datetime(2025, 10, 15)
        stage_changed = datetime(2025, 10, 1)

        deal = DealRecord(
            deal_id="deal_123",
            deal_name="Full Deal",
            account_id="account_456",
            stage=DealStage.PROPOSAL,
            amount=Decimal("75000"),
            probability=80,
            closing_date=closing,
            created_time=created,
            modified_time=modified,
            stage_changed_date=stage_changed,
            owner_id="owner_789",
            owner_name="Jane Doe",
            is_stalled=False,
            days_in_stage=14,
        )

        assert deal.deal_id == "deal_123"
        assert deal.closing_date == closing
        assert deal.owner_name == "Jane Doe"
        assert deal.days_in_stage == 14


# ============================================================================
# ACTIVITY_RECORD TESTS
# ============================================================================

class TestActivityRecord:
    """Test ActivityRecord model."""

    def test_activity_record_creation(self):
        """Test basic ActivityRecord creation."""
        activity = ActivityRecord(
            activity_id="act_123",
            account_id="acc_456",
            activity_type=ActivityType.MEETING,
            subject="Strategy Discussion",
            owner_id="owner_789",
        )

        assert activity.activity_id == "act_123"
        assert activity.account_id == "acc_456"
        assert activity.activity_type == ActivityType.MEETING
        assert activity.subject == "Strategy Discussion"

    def test_activity_record_defaults(self):
        """Test ActivityRecord default values."""
        activity = ActivityRecord(
            activity_id="1",
            account_id="acc",
            activity_type=ActivityType.CALL,
            owner_id="owner",
        )

        assert activity.subject == ""
        assert activity.description == ""
        assert activity.owner_name == ""
        assert activity.participants == []
        assert activity.is_high_value is False
        assert activity.outcome is None

    def test_activity_record_is_recent_method(self):
        """Test is_recent method."""
        # Recent activity (5 days ago)
        recent = ActivityRecord(
            activity_id="1",
            account_id="acc",
            activity_type=ActivityType.CALL,
            created_time=datetime.utcnow() - timedelta(days=5),
            owner_id="owner",
        )
        assert recent.is_recent(days=30)
        assert recent.is_recent(days=7)

        # Not recent (45 days ago)
        old = ActivityRecord(
            activity_id="2",
            account_id="acc",
            activity_type=ActivityType.EMAIL,
            created_time=datetime.utcnow() - timedelta(days=45),
            owner_id="owner",
        )
        assert not old.is_recent(days=30)
        assert old.is_recent(days=60)

    def test_activity_record_participants_list(self):
        """Test participants list field."""
        activity = ActivityRecord(
            activity_id="1",
            account_id="acc",
            activity_type=ActivityType.MEETING,
            participants=["John Doe", "Jane Smith", "Bob Johnson"],
            owner_id="owner",
        )

        assert len(activity.participants) == 3
        assert "John Doe" in activity.participants

    def test_activity_record_high_value_flag(self):
        """Test is_high_value flag."""
        high_value_activity = ActivityRecord(
            activity_id="1",
            account_id="acc",
            activity_type=ActivityType.DEMO,
            is_high_value=True,
            owner_id="owner",
        )

        assert high_value_activity.is_high_value

    def test_activity_record_with_outcome(self):
        """Test activity with outcome."""
        activity = ActivityRecord(
            activity_id="1",
            account_id="acc",
            activity_type=ActivityType.CALL,
            outcome="Scheduled follow-up meeting",
            owner_id="owner",
        )

        assert activity.outcome == "Scheduled follow-up meeting"


# ============================================================================
# NOTE_RECORD TESTS
# ============================================================================

class TestNoteRecord:
    """Test NoteRecord model."""

    def test_note_record_creation(self):
        """Test basic NoteRecord creation."""
        note = NoteRecord(
            note_id="note_123",
            account_id="acc_456",
            title="Meeting Notes",
            content="Discussion about Q4 strategy",
            created_by_id="user_789",
        )

        assert note.note_id == "note_123"
        assert note.account_id == "acc_456"
        assert note.title == "Meeting Notes"
        assert note.content == "Discussion about Q4 strategy"

    def test_note_record_defaults(self):
        """Test NoteRecord default values."""
        note = NoteRecord(
            note_id="1",
            account_id="acc",
            content="Test content",
            created_by_id="user",
        )

        assert note.title == ""
        assert note.created_by_name == ""
        assert note.is_private is False

    def test_note_record_private_flag(self):
        """Test private note flag."""
        private_note = NoteRecord(
            note_id="1",
            account_id="acc",
            content="Private info",
            created_by_id="user",
            is_private=True,
        )

        assert private_note.is_private

    def test_note_record_timestamps(self):
        """Test note timestamps."""
        created = datetime(2025, 10, 1)
        modified = datetime(2025, 10, 15)

        note = NoteRecord(
            note_id="1",
            account_id="acc",
            content="Test",
            created_time=created,
            modified_time=modified,
            created_by_id="user",
        )

        assert note.created_time == created
        assert note.modified_time == modified


# ============================================================================
# RISK_SIGNAL TESTS
# ============================================================================

class TestRiskSignal:
    """Test RiskSignal model."""

    def test_risk_signal_creation(self):
        """Test basic RiskSignal creation."""
        signal = RiskSignal(
            signal_type="inactivity",
            description="No activity in 30 days",
            severity=RiskLevel.HIGH,
        )

        assert signal.signal_type == "inactivity"
        assert signal.description == "No activity in 30 days"
        assert signal.severity == RiskLevel.HIGH

    def test_risk_signal_defaults(self):
        """Test RiskSignal default values."""
        signal = RiskSignal(
            signal_type="test",
            description="Test signal",
            severity=RiskLevel.LOW,
        )

        assert signal.details == {}
        assert signal.requires_action is False
        assert isinstance(signal.detected_at, datetime)

    def test_risk_signal_with_details(self):
        """Test RiskSignal with details."""
        signal = RiskSignal(
            signal_type="stalled_deals",
            description="2 deals stalled",
            severity=RiskLevel.MEDIUM,
            details={
                "deal_ids": ["deal1", "deal2"],
                "days_stalled": 35,
            },
        )

        assert "deal_ids" in signal.details
        assert len(signal.details["deal_ids"]) == 2

    def test_risk_signal_requires_action(self):
        """Test requires_action flag."""
        signal = RiskSignal(
            signal_type="critical_issue",
            description="Immediate action needed",
            severity=RiskLevel.CRITICAL,
            requires_action=True,
        )

        assert signal.requires_action

    def test_risk_signal_type_validation(self):
        """Test signal_type cannot be empty."""
        with pytest.raises(ValidationError):
            RiskSignal(
                signal_type="",
                description="Test",
                severity=RiskLevel.LOW,
            )

        with pytest.raises(ValidationError):
            RiskSignal(
                signal_type="   ",
                description="Test",
                severity=RiskLevel.LOW,
            )

    def test_risk_signal_type_stripped(self):
        """Test signal_type is stripped of whitespace."""
        signal = RiskSignal(
            signal_type="  test_signal  ",
            description="Test",
            severity=RiskLevel.LOW,
        )

        assert signal.signal_type == "test_signal"


# ============================================================================
# ACCOUNT_RECORD TESTS
# ============================================================================

class TestAccountRecord:
    """Test AccountRecord model."""

    def test_account_record_creation(self):
        """Test basic AccountRecord creation."""
        account = AccountRecord(
            account_id="acc_123",
            account_name="Acme Corp",
            owner_id="owner_456",
        )

        assert account.account_id == "acc_123"
        assert account.account_name == "Acme Corp"
        assert account.owner_id == "owner_456"

    def test_account_record_defaults(self):
        """Test AccountRecord default values."""
        account = AccountRecord(
            account_id="1",
            account_name="Test",
            owner_id="owner",
        )

        assert account.status == AccountStatus.ACTIVE
        assert account.owner_name == ""
        assert account.deal_count == 0
        assert account.total_value == Decimal("0")
        assert account.annual_revenue == Decimal("0")
        assert account.custom_fields == {}
        assert account.change_flags == set()

    def test_account_record_currency_conversion(self):
        """Test currency values are converted to Decimal."""
        # From int
        account1 = AccountRecord(
            account_id="1",
            account_name="Test",
            owner_id="owner",
            total_value=100000,
            annual_revenue=500000,
        )
        assert isinstance(account1.total_value, Decimal)
        assert isinstance(account1.annual_revenue, Decimal)

        # From float
        account2 = AccountRecord(
            account_id="2",
            account_name="Test",
            owner_id="owner",
            total_value=100000.50,
            annual_revenue=500000.75,
        )
        assert isinstance(account2.total_value, Decimal)
        assert isinstance(account2.annual_revenue, Decimal)

        # From string
        account3 = AccountRecord(
            account_id="3",
            account_name="Test",
            owner_id="owner",
            total_value="100000",
            annual_revenue="500000",
        )
        assert isinstance(account3.total_value, Decimal)

    def test_account_record_deal_count_validation(self):
        """Test deal_count must be non-negative."""
        # Valid
        account = AccountRecord(
            account_id="1",
            account_name="Test",
            owner_id="owner",
            deal_count=5,
        )
        assert account.deal_count == 5

        # Invalid - negative
        with pytest.raises(ValidationError):
            AccountRecord(
                account_id="1",
                account_name="Test",
                owner_id="owner",
                deal_count=-1,
            )

    def test_account_record_days_since_activity(self):
        """Test days_since_activity method."""
        # Recent activity
        account1 = AccountRecord(
            account_id="1",
            account_name="Test",
            owner_id="owner",
            last_activity_date=datetime.utcnow() - timedelta(days=10),
        )
        assert account1.days_since_activity() == 10

        # No activity
        account2 = AccountRecord(
            account_id="2",
            account_name="Test",
            owner_id="owner",
            last_activity_date=None,
        )
        assert account2.days_since_activity() == 0

    def test_account_record_has_change_method(self):
        """Test has_change method."""
        account = AccountRecord(
            account_id="1",
            account_name="Test",
            owner_id="owner",
            change_flags={ChangeType.OWNER_CHANGE, ChangeType.STATUS_CHANGE},
        )

        assert account.has_change(ChangeType.OWNER_CHANGE)
        assert account.has_change(ChangeType.STATUS_CHANGE)
        assert not account.has_change(ChangeType.DEAL_STALLED)

    def test_account_record_custom_fields(self):
        """Test custom_fields storage."""
        account = AccountRecord(
            account_id="1",
            account_name="Test",
            owner_id="owner",
            custom_fields={
                "Custom_Field_1": "value1",
                "cf_field_2": "value2",
            },
        )

        assert account.custom_fields["Custom_Field_1"] == "value1"
        assert account.custom_fields["cf_field_2"] == "value2"

    def test_account_record_json_serialization(self):
        """Test AccountRecord JSON serialization."""
        account = AccountRecord(
            account_id="1",
            account_name="Test",
            owner_id="owner",
            total_value=Decimal("100000"),
            last_modified=datetime(2025, 10, 15, 12, 0, 0),
            change_flags={ChangeType.OWNER_CHANGE},
        )

        # Should serialize to JSON
        json_str = account.model_dump_json()
        assert isinstance(json_str, str)

        # Decimal should be string
        data = json.loads(json_str)
        assert isinstance(data["total_value"], str)

    def test_account_record_with_all_fields(self):
        """Test AccountRecord with all fields populated."""
        account = AccountRecord(
            account_id="acc_123",
            account_name="Acme Corporation",
            owner_id="owner_456",
            owner_name="John Doe",
            status=AccountStatus.ACTIVE,
            last_modified=datetime(2025, 10, 15),
            last_activity_date=datetime(2025, 10, 10),
            created_time=datetime(2024, 1, 1),
            deal_count=5,
            total_value=Decimal("150000"),
            annual_revenue=Decimal("500000"),
            industry="Technology",
            website="https://acme.com",
            phone="+1-555-0100",
            billing_city="San Francisco",
            billing_country="USA",
            custom_fields={"tier": "enterprise"},
            change_flags={ChangeType.OWNER_CHANGE},
        )

        assert account.account_name == "Acme Corporation"
        assert account.industry == "Technology"
        assert account.billing_city == "San Francisco"
        assert len(account.change_flags) == 1


# ============================================================================
# AGGREGATED_DATA TESTS
# ============================================================================

class TestAggregatedData:
    """Test AggregatedData model."""

    def test_aggregated_data_creation(self):
        """Test basic AggregatedData creation."""
        aggregated = AggregatedData(account_id="acc_123")

        assert aggregated.account_id == "acc_123"
        assert aggregated.deals == []
        assert aggregated.activities == []
        assert aggregated.notes == []

    def test_aggregated_data_defaults(self):
        """Test AggregatedData default values."""
        aggregated = AggregatedData(account_id="acc_123")

        assert aggregated.total_deal_value == Decimal("0")
        assert aggregated.stalled_deal_count == 0
        assert aggregated.high_value_activity_count == 0
        assert aggregated.recent_activity_count == 0
        assert aggregated.data_freshness == 0

    def test_aggregated_data_calculate_summaries_deals(self):
        """Test calculate_summaries with deals."""
        deal1 = DealRecord(
            deal_id="1",
            deal_name="Deal 1",
            account_id="acc",
            stage=DealStage.NEGOTIATION,
            amount=Decimal("50000"),
            owner_id="owner",
        )
        deal2 = DealRecord(
            deal_id="2",
            deal_name="Deal 2",
            account_id="acc",
            stage=DealStage.PROPOSAL,
            amount=Decimal("75000"),
            owner_id="owner",
        )

        aggregated = AggregatedData(
            account_id="acc",
            deals=[deal1, deal2],
        )
        aggregated.calculate_summaries()

        assert aggregated.total_deal_value == Decimal("125000")

    def test_aggregated_data_calculate_summaries_stalled_deals(self):
        """Test calculate_summaries counts stalled deals."""
        stalled_deal = DealRecord(
            deal_id="1",
            deal_name="Stalled",
            account_id="acc",
            stage=DealStage.NEGOTIATION,
            is_stalled=True,
            owner_id="owner",
        )
        active_deal = DealRecord(
            deal_id="2",
            deal_name="Active",
            account_id="acc",
            stage=DealStage.PROPOSAL,
            is_stalled=False,
            owner_id="owner",
        )

        aggregated = AggregatedData(
            account_id="acc",
            deals=[stalled_deal, active_deal],
        )
        aggregated.calculate_summaries()

        assert aggregated.stalled_deal_count == 1

    def test_aggregated_data_calculate_summaries_high_value_activities(self):
        """Test calculate_summaries counts high-value activities."""
        high_value = ActivityRecord(
            activity_id="1",
            account_id="acc",
            activity_type=ActivityType.DEMO,
            is_high_value=True,
            owner_id="owner",
        )
        normal = ActivityRecord(
            activity_id="2",
            account_id="acc",
            activity_type=ActivityType.CALL,
            is_high_value=False,
            owner_id="owner",
        )

        aggregated = AggregatedData(
            account_id="acc",
            activities=[high_value, normal],
        )
        aggregated.calculate_summaries()

        assert aggregated.high_value_activity_count == 1

    def test_aggregated_data_calculate_summaries_recent_activities(self):
        """Test calculate_summaries counts recent activities."""
        recent = ActivityRecord(
            activity_id="1",
            account_id="acc",
            activity_type=ActivityType.MEETING,
            created_time=datetime.utcnow() - timedelta(days=5),
            owner_id="owner",
        )
        old = ActivityRecord(
            activity_id="2",
            account_id="acc",
            activity_type=ActivityType.EMAIL,
            created_time=datetime.utcnow() - timedelta(days=45),
            owner_id="owner",
        )

        aggregated = AggregatedData(
            account_id="acc",
            activities=[recent, old],
        )
        aggregated.calculate_summaries()

        assert aggregated.recent_activity_count == 1

    def test_aggregated_data_with_notes(self):
        """Test AggregatedData with notes."""
        note = NoteRecord(
            note_id="1",
            account_id="acc",
            content="Test note",
            created_by_id="user",
        )

        aggregated = AggregatedData(
            account_id="acc",
            notes=[note],
        )

        assert len(aggregated.notes) == 1

    def test_aggregated_data_empty_summaries(self):
        """Test calculate_summaries with empty data."""
        aggregated = AggregatedData(account_id="acc")
        aggregated.calculate_summaries()

        assert aggregated.total_deal_value == Decimal("0")
        assert aggregated.stalled_deal_count == 0
        assert aggregated.high_value_activity_count == 0

    def test_aggregated_data_data_freshness(self):
        """Test data_freshness field."""
        aggregated = AggregatedData(
            account_id="acc",
            data_freshness=150,
        )

        assert aggregated.data_freshness == 150


# ============================================================================
# CHANGE_DETECTION_RESULT TESTS
# ============================================================================

class TestChangeDetectionResult:
    """Test ChangeDetectionResult model."""

    def test_change_detection_result_creation(self):
        """Test basic ChangeDetectionResult creation."""
        result = ChangeDetectionResult(account_id="acc_123")

        assert result.account_id == "acc_123"
        assert result.changes_detected is False
        assert result.field_changes == []
        assert result.change_types == set()

    def test_change_detection_result_add_change(self):
        """Test add_change method."""
        result = ChangeDetectionResult(account_id="acc_123")

        result.add_change(
            field_name="Account_Status",
            old_value="Active",
            new_value="At Risk",
            change_type=ChangeType.STATUS_CHANGE,
        )

        assert result.changes_detected
        assert len(result.field_changes) == 1
        assert ChangeType.STATUS_CHANGE in result.change_types

    def test_change_detection_result_multiple_changes(self):
        """Test adding multiple changes."""
        result = ChangeDetectionResult(account_id="acc_123")

        result.add_change("field1", "old1", "new1", ChangeType.CUSTOM_FIELD_MODIFIED)
        result.add_change("field2", "old2", "new2", ChangeType.REVENUE_CHANGE)

        assert len(result.field_changes) == 2
        assert len(result.change_types) == 2

    def test_change_detection_result_requires_attention_critical(self):
        """Test requires_attention flag for critical changes."""
        result = ChangeDetectionResult(account_id="acc_123")

        result.add_change(
            "Owner",
            "old_owner",
            "new_owner",
            ChangeType.OWNER_CHANGE,
        )

        assert result.requires_attention

    def test_change_detection_result_requires_attention_non_critical(self):
        """Test requires_attention flag for non-critical changes."""
        result = ChangeDetectionResult(account_id="acc_123")

        result.add_change(
            "Website",
            "old_url",
            "new_url",
            ChangeType.CUSTOM_FIELD_MODIFIED,
        )

        # Should not require attention for custom field changes
        assert not result.requires_attention

    def test_change_detection_result_get_critical_changes(self):
        """Test get_critical_changes method."""
        result = ChangeDetectionResult(account_id="acc_123")

        # Add critical changes
        result.add_change("Owner", "old", "new", ChangeType.OWNER_CHANGE)
        result.add_change("Status", "Active", "At Risk", ChangeType.STATUS_CHANGE)

        # Add non-critical change
        result.add_change("Website", "old", "new", ChangeType.CUSTOM_FIELD_MODIFIED)

        critical = result.get_critical_changes()
        assert len(critical) == 2

    def test_change_detection_result_comparison_baseline(self):
        """Test comparison_baseline field."""
        baseline = datetime(2025, 10, 1)
        result = ChangeDetectionResult(
            account_id="acc_123",
            comparison_baseline=baseline,
        )

        assert result.comparison_baseline == baseline

    def test_change_detection_result_json_serialization(self):
        """Test JSON serialization."""
        result = ChangeDetectionResult(account_id="acc_123")
        result.add_change("test", "old", "new", ChangeType.CUSTOM_FIELD_MODIFIED)

        # Should serialize
        json_str = result.model_dump_json()
        assert isinstance(json_str, str)

        # Sets should be serialized as lists
        data = json.loads(json_str)
        assert isinstance(data["change_types"], list)


# ============================================================================
# ACCOUNT_SNAPSHOT TESTS
# ============================================================================

class TestAccountSnapshot:
    """Test AccountSnapshot model."""

    def test_account_snapshot_creation(self):
        """Test basic AccountSnapshot creation."""
        account = AccountRecord(
            account_id="acc_123",
            account_name="Test",
            owner_id="owner_456",
        )
        aggregated = AggregatedData(account_id="acc_123")
        changes = ChangeDetectionResult(account_id="acc_123")

        snapshot = AccountSnapshot(
            snapshot_id="snap_123",
            account=account,
            aggregated_data=aggregated,
            changes=changes,
        )

        assert snapshot.snapshot_id == "snap_123"
        assert snapshot.account.account_id == "acc_123"
        assert snapshot.needs_review is False
        assert snapshot.risk_level == RiskLevel.NONE

    def test_account_snapshot_calculate_risk_level(self):
        """Test calculate_risk_level method."""
        account = AccountRecord(account_id="acc", account_name="Test", owner_id="owner")
        aggregated = AggregatedData(account_id="acc")
        changes = ChangeDetectionResult(account_id="acc")

        # No signals
        snapshot1 = AccountSnapshot(
            snapshot_id="1",
            account=account,
            aggregated_data=aggregated,
            changes=changes,
        )
        assert snapshot1.calculate_risk_level() == RiskLevel.NONE

        # With critical signal
        snapshot2 = AccountSnapshot(
            snapshot_id="2",
            account=account,
            aggregated_data=aggregated,
            changes=changes,
            risk_signals=[
                RiskSignal(
                    signal_type="test",
                    description="Critical issue",
                    severity=RiskLevel.CRITICAL,
                )
            ],
        )
        assert snapshot2.calculate_risk_level() == RiskLevel.CRITICAL

        # With mixed signals
        snapshot3 = AccountSnapshot(
            snapshot_id="3",
            account=account,
            aggregated_data=aggregated,
            changes=changes,
            risk_signals=[
                RiskSignal(signal_type="t1", description="Low", severity=RiskLevel.LOW),
                RiskSignal(signal_type="t2", description="High", severity=RiskLevel.HIGH),
                RiskSignal(signal_type="t3", description="Medium", severity=RiskLevel.MEDIUM),
            ],
        )
        # Should return highest severity
        assert snapshot3.calculate_risk_level() == RiskLevel.HIGH

    def test_account_snapshot_calculate_priority_score(self):
        """Test calculate_priority_score method."""
        account = AccountRecord(account_id="acc", account_name="Test", owner_id="owner")
        aggregated = AggregatedData(account_id="acc")
        changes = ChangeDetectionResult(account_id="acc")

        snapshot = AccountSnapshot(
            snapshot_id="1",
            account=account,
            aggregated_data=aggregated,
            changes=changes,
            risk_level=RiskLevel.HIGH,
        )

        score = snapshot.calculate_priority_score()
        assert 0 <= score <= 100

    def test_account_snapshot_priority_score_risk_contribution(self):
        """Test priority score risk level contribution."""
        account = AccountRecord(account_id="acc", account_name="Test", owner_id="owner")
        aggregated = AggregatedData(account_id="acc")
        changes = ChangeDetectionResult(account_id="acc")

        # Critical risk should contribute 40 points
        snapshot_critical = AccountSnapshot(
            snapshot_id="1",
            account=account,
            aggregated_data=aggregated,
            changes=changes,
            risk_level=RiskLevel.CRITICAL,
        )
        assert snapshot_critical.calculate_priority_score() >= 40

    def test_account_snapshot_priority_score_changes_contribution(self):
        """Test priority score changes contribution."""
        account = AccountRecord(account_id="acc", account_name="Test", owner_id="owner")
        aggregated = AggregatedData(account_id="acc")
        changes = ChangeDetectionResult(account_id="acc")

        # Add multiple changes
        for i in range(6):
            changes.add_change(f"field{i}", "old", "new", ChangeType.CUSTOM_FIELD_MODIFIED)

        snapshot = AccountSnapshot(
            snapshot_id="1",
            account=account,
            aggregated_data=aggregated,
            changes=changes,
            risk_level=RiskLevel.NONE,
        )

        score = snapshot.calculate_priority_score()
        # Should have points from changes (6 changes * 5 points = 30 points)
        assert score >= 30

    def test_account_snapshot_priority_score_deal_value_contribution(self):
        """Test priority score deal value contribution."""
        account = AccountRecord(account_id="acc", account_name="Test", owner_id="owner")
        aggregated = AggregatedData(
            account_id="acc",
            total_deal_value=Decimal("150000"),  # > $100k
        )
        changes = ChangeDetectionResult(account_id="acc")

        snapshot = AccountSnapshot(
            snapshot_id="1",
            account=account,
            aggregated_data=aggregated,
            changes=changes,
            risk_level=RiskLevel.NONE,
        )

        score = snapshot.calculate_priority_score()
        # Should get 20 points for high deal value
        assert score >= 20

    def test_account_snapshot_priority_score_activity_contribution(self):
        """Test priority score activity contribution."""
        account = AccountRecord(account_id="acc", account_name="Test", owner_id="owner")
        aggregated = AggregatedData(
            account_id="acc",
            recent_activity_count=10,  # > 5 activities
        )
        changes = ChangeDetectionResult(account_id="acc")

        snapshot = AccountSnapshot(
            snapshot_id="1",
            account=account,
            aggregated_data=aggregated,
            changes=changes,
            risk_level=RiskLevel.NONE,
        )

        score = snapshot.calculate_priority_score()
        # Should get 10 points for high activity
        assert score >= 10

    def test_account_snapshot_update_analysis_flags(self):
        """Test update_analysis_flags method."""
        account = AccountRecord(account_id="acc", account_name="Test", owner_id="owner")
        aggregated = AggregatedData(account_id="acc")
        changes = ChangeDetectionResult(account_id="acc")

        snapshot = AccountSnapshot(
            snapshot_id="1",
            account=account,
            aggregated_data=aggregated,
            changes=changes,
            risk_signals=[
                RiskSignal(
                    signal_type="test",
                    description="High risk",
                    severity=RiskLevel.HIGH,
                )
            ],
        )

        snapshot.update_analysis_flags()

        assert snapshot.risk_level == RiskLevel.HIGH
        assert snapshot.priority_score > 0
        assert snapshot.needs_review

    def test_account_snapshot_needs_review_high_risk(self):
        """Test needs_review flag for high risk."""
        account = AccountRecord(account_id="acc", account_name="Test", owner_id="owner")
        aggregated = AggregatedData(account_id="acc")
        changes = ChangeDetectionResult(account_id="acc")

        snapshot = AccountSnapshot(
            snapshot_id="1",
            account=account,
            aggregated_data=aggregated,
            changes=changes,
            risk_level=RiskLevel.HIGH,
        )

        snapshot.update_analysis_flags()
        assert snapshot.needs_review

    def test_account_snapshot_needs_review_changes(self):
        """Test needs_review flag for changes requiring attention."""
        account = AccountRecord(account_id="acc", account_name="Test", owner_id="owner")
        aggregated = AggregatedData(account_id="acc")
        changes = ChangeDetectionResult(account_id="acc")
        changes.add_change("Owner", "old", "new", ChangeType.OWNER_CHANGE)

        snapshot = AccountSnapshot(
            snapshot_id="1",
            account=account,
            aggregated_data=aggregated,
            changes=changes,
        )

        snapshot.update_analysis_flags()
        assert snapshot.needs_review

    def test_account_snapshot_data_sources(self):
        """Test data_sources field."""
        account = AccountRecord(account_id="acc", account_name="Test", owner_id="owner")
        aggregated = AggregatedData(account_id="acc")
        changes = ChangeDetectionResult(account_id="acc")

        snapshot = AccountSnapshot(
            snapshot_id="1",
            account=account,
            aggregated_data=aggregated,
            changes=changes,
            data_sources=["zoho_crm", "zoho_deals", "zoho_activities"],
        )

        assert len(snapshot.data_sources) == 3
        assert "zoho_crm" in snapshot.data_sources
