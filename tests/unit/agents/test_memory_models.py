"""Unit tests for memory analyst models.

Tests all Pydantic models, enums, and validation logic.
Target: 30+ tests covering all model functionality.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from src.agents.memory_models import (
    SentimentTrend, PatternType, CommitmentStatus, RelationshipStrength,
    RiskLevel, EventType, TimelineEvent, Pattern, SentimentAnalysis,
    PriorRecommendation, RelationshipAssessment, Commitment, KeyEvent,
    EngagementMetrics, HistoricalContext, EngagementCycle, CommitmentPattern,
    Timeline, Milestone, ToneAnalysis, AlignmentScore
)


class TestEnums:
    """Test enum definitions."""

    def test_sentiment_trend_values(self):
        assert SentimentTrend.IMPROVING == "improving"
        assert SentimentTrend.STABLE == "stable"
        assert SentimentTrend.DECLINING == "declining"
        assert SentimentTrend.UNKNOWN == "unknown"

    def test_pattern_type_values(self):
        assert PatternType.CHURN_RISK == "churn_risk"
        assert PatternType.UPSELL_OPPORTUNITY == "upsell_opportunity"
        assert PatternType.RENEWAL_RISK == "renewal_risk"

    def test_commitment_status_values(self):
        assert CommitmentStatus.PENDING == "pending"
        assert CommitmentStatus.COMPLETED == "completed"
        assert CommitmentStatus.OVERDUE == "overdue"

    def test_relationship_strength_values(self):
        assert RelationshipStrength.STRONG == "strong"
        assert RelationshipStrength.MODERATE == "moderate"
        assert RelationshipStrength.AT_RISK == "at_risk"


class TestTimelineEvent:
    """Test TimelineEvent model."""

    def test_create_valid_timeline_event(self):
        event = TimelineEvent(
            event_id="evt_123",
            account_id="acc_456",
            timestamp=datetime.utcnow(),
            event_type=EventType.MEETING,
            description="Quarterly business review",
            participants=["John Doe", "Jane Smith"],
            impact="high"
        )
        assert event.event_id == "evt_123"
        assert event.event_type == EventType.MEETING
        assert len(event.participants) == 2

    def test_timeline_event_default_values(self):
        event = TimelineEvent(
            event_id="evt_123",
            account_id="acc_456",
            timestamp=datetime.utcnow(),
            event_type=EventType.NOTE,
            description="Test note"
        )
        assert event.participants == []
        assert event.impact == "medium"
        assert event.metadata == {}

    def test_timeline_event_impact_validation(self):
        with pytest.raises(ValidationError):
            TimelineEvent(
                event_id="evt_123",
                account_id="acc_456",
                timestamp=datetime.utcnow(),
                event_type=EventType.NOTE,
                description="Test",
                impact="invalid"
            )

    def test_timeline_event_json_serialization(self):
        event = TimelineEvent(
            event_id="evt_123",
            account_id="acc_456",
            timestamp=datetime.utcnow(),
            event_type=EventType.CALL,
            description="Follow-up call"
        )
        json_data = event.model_dump()
        assert json_data["event_id"] == "evt_123"
        assert json_data["event_type"] == "call"


class TestPattern:
    """Test Pattern model."""

    def test_create_valid_pattern(self):
        pattern = Pattern(
            pattern_id="pat_123",
            pattern_type=PatternType.CHURN_RISK,
            confidence=0.85,
            description="Engagement drop detected",
            evidence=["50% reduction in activity"],
            first_detected=datetime.utcnow(),
            last_detected=datetime.utcnow(),
            risk_score=75
        )
        assert pattern.confidence == 0.85
        assert pattern.risk_score == 75
        assert len(pattern.evidence) == 1

    def test_pattern_confidence_validation(self):
        with pytest.raises(ValidationError):
            Pattern(
                pattern_id="pat_123",
                pattern_type=PatternType.CHURN_RISK,
                confidence=1.5,  # Invalid: > 1.0
                description="Test",
                first_detected=datetime.utcnow(),
                last_detected=datetime.utcnow()
            )

    def test_pattern_risk_score_validation(self):
        with pytest.raises(ValidationError):
            Pattern(
                pattern_id="pat_123",
                pattern_type=PatternType.CHURN_RISK,
                confidence=0.8,
                description="Test",
                first_detected=datetime.utcnow(),
                last_detected=datetime.utcnow(),
                risk_score=150  # Invalid: > 100
            )


class TestSentimentAnalysis:
    """Test SentimentAnalysis model."""

    def test_create_sentiment_analysis(self):
        analysis = SentimentAnalysis(
            account_id="acc_123",
            overall_sentiment=0.6,
            trend=SentimentTrend.IMPROVING,
            recent_score=0.8,
            historical_score=0.4,
            change_rate=0.4,
            analysis_period_days=90,
            data_points=25
        )
        assert analysis.trend == SentimentTrend.IMPROVING
        assert analysis.change_rate == 0.4

    def test_sentiment_score_bounds(self):
        with pytest.raises(ValidationError):
            SentimentAnalysis(
                account_id="acc_123",
                overall_sentiment=1.5,  # Invalid
                trend=SentimentTrend.STABLE,
                recent_score=0.5,
                historical_score=0.5,
                change_rate=0.0,
                analysis_period_days=90,
                data_points=10
            )


class TestPriorRecommendation:
    """Test PriorRecommendation model."""

    def test_create_prior_recommendation(self):
        rec = PriorRecommendation(
            recommendation_id="rec_123",
            account_id="acc_456",
            generated_date=datetime.utcnow(),
            recommendation="Schedule executive briefing",
            priority="high",
            action_type="engagement",
            status="completed",
            effectiveness_score=85
        )
        assert rec.status == "completed"
        assert rec.effectiveness_score == 85

    def test_recommendation_status_validation(self):
        with pytest.raises(ValidationError):
            PriorRecommendation(
                recommendation_id="rec_123",
                account_id="acc_456",
                generated_date=datetime.utcnow(),
                recommendation="Test",
                priority="high",
                action_type="test",
                status="invalid_status"
            )


class TestRelationshipAssessment:
    """Test RelationshipAssessment model."""

    def test_create_relationship_assessment(self):
        assessment = RelationshipAssessment(
            account_id="acc_123",
            relationship_strength=RelationshipStrength.STRONG,
            engagement_score=0.85,
            executive_alignment=0.9,
            touchpoint_frequency=2.5,
            response_rate=0.95,
            last_interaction_days=5,
            key_contacts_count=8,
            executive_sponsor_present=True,
            relationship_health_score=88
        )
        assert assessment.relationship_strength == RelationshipStrength.STRONG
        assert assessment.executive_sponsor_present is True


class TestCommitment:
    """Test Commitment model."""

    def test_create_commitment(self):
        commitment = Commitment(
            commitment_id="comm_123",
            account_id="acc_456",
            commitment_text="Deliver feature by Q3",
            committed_by="Account Manager",
            committed_to="Customer CTO",
            commitment_date=datetime.utcnow(),
            status=CommitmentStatus.IN_PROGRESS
        )
        assert commitment.status == CommitmentStatus.IN_PROGRESS

    def test_commitment_date_validation(self):
        commitment_date = datetime.utcnow()
        with pytest.raises(ValidationError):
            Commitment(
                commitment_id="comm_123",
                account_id="acc_456",
                commitment_text="Test",
                committed_by="Manager",
                committed_to="Customer",
                commitment_date=commitment_date,
                completion_date=commitment_date - timedelta(days=1)  # Before commitment
            )


class TestHistoricalContext:
    """Test HistoricalContext model."""

    def test_create_historical_context(self):
        context = HistoricalContext(
            account_id="acc_123",
            sentiment_trend=SentimentTrend.STABLE,
            relationship_strength=RelationshipStrength.MODERATE,
            risk_level=RiskLevel.LOW
        )
        assert context.account_id == "acc_123"
        assert context.key_events == []
        assert context.patterns == []

    def test_historical_context_with_data(self):
        context = HistoricalContext(
            account_id="acc_123",
            key_events=[
                KeyEvent(
                    event_id="ke_1",
                    account_id="acc_123",
                    event_date=datetime.utcnow(),
                    event_type="meeting",
                    title="Executive Review",
                    description="Quarterly review meeting",
                    impact_on_relationship="Positive engagement"
                )
            ],
            sentiment_trend=SentimentTrend.IMPROVING,
            relationship_strength=RelationshipStrength.STRONG,
            risk_level=RiskLevel.LOW
        )
        assert len(context.key_events) == 1
        assert context.sentiment_trend == SentimentTrend.IMPROVING


class TestEngagementMetrics:
    """Test EngagementMetrics model."""

    def test_create_engagement_metrics(self):
        metrics = EngagementMetrics(
            account_id="acc_123",
            measurement_period_days=30,
            total_interactions=15,
            meetings_count=5,
            emails_count=8,
            calls_count=2,
            interaction_frequency_score=0.75,
            quality_score=0.85
        )
        assert metrics.total_interactions == 15
        assert metrics.meetings_count == 5


class TestEngagementCycle:
    """Test EngagementCycle model."""

    def test_create_engagement_cycle(self):
        start = datetime.utcnow() - timedelta(days=90)
        end = datetime.utcnow()

        cycle = EngagementCycle(
            cycle_id="cycle_123",
            account_id="acc_456",
            start_date=start,
            end_date=end,
            cycle_length_days=90,
            average_frequency=2.5,
            cycle_type="quarterly",
            confidence=0.7
        )
        assert cycle.cycle_length_days == 90
        assert cycle.cycle_type == "quarterly"


class TestCommitmentPattern:
    """Test CommitmentPattern model."""

    def test_create_commitment_pattern(self):
        pattern = CommitmentPattern(
            pattern_id="cp_123",
            account_id="acc_456",
            pattern_description="High completion rate",
            commitment_count=20,
            completion_rate=0.9,
            average_delay_days=2.5
        )
        assert pattern.completion_rate == 0.9
        assert pattern.commitment_count == 20


class TestToneAnalysis:
    """Test ToneAnalysis model."""

    def test_create_tone_analysis(self):
        tone = ToneAnalysis(
            account_id="acc_123",
            overall_tone="positive",
            formality_score=0.7,
            positivity_score=0.8,
            urgency_score=0.3,
            confidence_score=0.9,
            tone_consistency=0.85
        )
        assert tone.overall_tone == "positive"
        assert tone.positivity_score == 0.8
