"""Comprehensive tests for recommendation models.

Tests all Pydantic models, validators, and model logic for the Recommendation Author.
"""

import pytest
from datetime import datetime, timedelta
from typing import Any, Dict, List

from src.agents.recommendation_models import (
    ActionSuggestion,
    ConfidenceLevel,
    ConfidenceScore,
    DataReference,
    EmailDraft,
    Escalation,
    EscalationReason,
    InsightsSynthesis,
    NextStep,
    Priority,
    Recommendation,
    RecommendationBatch,
    RecommendationContext,
    RecommendationResult,
    RecommendationType,
    TaskSuggestion,
)


class TestDataReference:
    """Tests for DataReference model."""

    def test_create_data_reference(self):
        """Test creating a valid DataReference."""
        ref = DataReference(
            source_type="zoho",
            source_id="account_123",
            entity_type="account",
            entity_id="123"
        )
        assert ref.source_type == "zoho"
        assert ref.source_id == "account_123"
        assert ref.entity_type == "account"
        assert ref.entity_id == "123"
        assert isinstance(ref.timestamp, datetime)

    def test_data_reference_with_custom_timestamp(self):
        """Test DataReference with custom timestamp."""
        custom_time = datetime(2024, 1, 15, 10, 30)
        ref = DataReference(
            source_type="cognee",
            source_id="insight_456",
            entity_type="insight",
            entity_id="456",
            timestamp=custom_time
        )
        assert ref.timestamp == custom_time

    def test_data_reference_with_field_data(self):
        """Test DataReference with field name and value."""
        ref = DataReference(
            source_type="zoho",
            source_id="deal_789",
            entity_type="deal",
            entity_id="789",
            field_name="stage",
            field_value="Negotiation"
        )
        assert ref.field_name == "stage"
        assert ref.field_value == "Negotiation"

    def test_data_reference_json_serialization(self):
        """Test JSON serialization of DataReference."""
        ref = DataReference(
            source_type="zoho",
            source_id="account_123",
            entity_type="account",
            entity_id="123"
        )
        data = ref.model_dump(mode='json')
        assert isinstance(data['timestamp'], str)


class TestConfidenceScore:
    """Tests for ConfidenceScore model and validation."""

    def test_high_confidence_score(self):
        """Test creating high confidence score."""
        score = ConfidenceScore(
            overall=0.85,
            level=ConfidenceLevel.HIGH,
            data_recency=0.9,
            pattern_strength=0.8,
            evidence_quality=0.85,
            historical_accuracy=0.9,
            rationale="High confidence based on fresh data and strong patterns."
        )
        assert score.overall == 0.85
        assert score.level == ConfidenceLevel.HIGH
        assert score.data_recency == 0.9

    def test_medium_confidence_score(self):
        """Test creating medium confidence score."""
        score = ConfidenceScore(
            overall=0.7,
            level=ConfidenceLevel.MEDIUM,
            data_recency=0.6,
            pattern_strength=0.7,
            evidence_quality=0.75,
            rationale="Moderate confidence."
        )
        assert score.level == ConfidenceLevel.MEDIUM

    def test_low_confidence_score(self):
        """Test creating low confidence score."""
        score = ConfidenceScore(
            overall=0.55,
            level=ConfidenceLevel.LOW,
            data_recency=0.5,
            pattern_strength=0.6,
            evidence_quality=0.55,
            rationale="Low confidence."
        )
        assert score.level == ConfidenceLevel.LOW

    def test_confidence_level_auto_correction_high(self):
        """Test automatic correction of confidence level to HIGH."""
        score = ConfidenceScore(
            overall=0.9,
            level=ConfidenceLevel.LOW,  # Wrong level
            data_recency=0.9,
            pattern_strength=0.9,
            evidence_quality=0.9,
            rationale="Test"
        )
        assert score.level == ConfidenceLevel.HIGH  # Auto-corrected

    def test_confidence_level_auto_correction_medium(self):
        """Test automatic correction of confidence level to MEDIUM."""
        score = ConfidenceScore(
            overall=0.7,
            level=ConfidenceLevel.LOW,  # Wrong level
            data_recency=0.7,
            pattern_strength=0.7,
            evidence_quality=0.7,
            rationale="Test"
        )
        assert score.level == ConfidenceLevel.MEDIUM  # Auto-corrected

    def test_confidence_level_auto_correction_low(self):
        """Test automatic correction of confidence level to LOW."""
        score = ConfidenceScore(
            overall=0.5,
            level=ConfidenceLevel.HIGH,  # Wrong level
            data_recency=0.5,
            pattern_strength=0.5,
            evidence_quality=0.5,
            rationale="Test"
        )
        assert score.level == ConfidenceLevel.LOW  # Auto-corrected

    def test_confidence_score_validation_bounds(self):
        """Test that confidence scores are within 0-1 bounds."""
        with pytest.raises(ValueError):
            ConfidenceScore(
                overall=1.5,  # Invalid
                level=ConfidenceLevel.HIGH,
                data_recency=0.9,
                pattern_strength=0.9,
                evidence_quality=0.9,
                rationale="Test"
            )

    def test_confidence_score_with_optional_historical(self):
        """Test confidence score without historical accuracy."""
        score = ConfidenceScore(
            overall=0.8,
            level=ConfidenceLevel.HIGH,
            data_recency=0.8,
            pattern_strength=0.8,
            evidence_quality=0.8,
            rationale="No historical data"
        )
        assert score.historical_accuracy is None


class TestNextStep:
    """Tests for NextStep model."""

    def test_create_next_step(self):
        """Test creating a NextStep."""
        step = NextStep(
            description="Send follow-up email",
            timeline="within 24 hours",
            owner="john@example.com",
            dependencies=["approval_received"]
        )
        assert step.description == "Send follow-up email"
        assert step.timeline == "within 24 hours"
        assert step.owner == "john@example.com"
        assert "approval_received" in step.dependencies

    def test_next_step_without_dependencies(self):
        """Test NextStep without dependencies."""
        step = NextStep(
            description="Schedule meeting",
            timeline="this week"
        )
        assert step.dependencies == []
        assert step.owner is None


class TestActionSuggestion:
    """Tests for ActionSuggestion model."""

    def test_create_action_suggestion(self):
        """Test creating an ActionSuggestion."""
        action = ActionSuggestion(
            action_type="email",
            description="Send follow-up email to contact",
            subject="Checking in on progress",
            draft_body="Hi John, ...",
            estimated_effort_minutes=15
        )
        assert action.action_type == "email"
        assert action.estimated_effort_minutes == 15

    def test_action_suggestion_with_next_steps(self):
        """Test ActionSuggestion with next steps."""
        action = ActionSuggestion(
            action_type="call",
            description="Follow-up call",
            next_steps=[
                NextStep(description="Send summary", timeline="same day"),
                NextStep(description="Update CRM", timeline="within 1 hour")
            ],
            estimated_effort_minutes=30
        )
        assert len(action.next_steps) == 2

    def test_effort_validation_minimum(self):
        """Test effort rounds to minimum 15 minutes."""
        action = ActionSuggestion(
            action_type="task",
            description="Quick task",
            estimated_effort_minutes=5  # Below minimum
        )
        assert action.estimated_effort_minutes == 15

    def test_effort_validation_rounding_30(self):
        """Test effort rounds to 30 minutes."""
        action = ActionSuggestion(
            action_type="task",
            description="Task",
            estimated_effort_minutes=25
        )
        assert action.estimated_effort_minutes == 30

    def test_effort_validation_rounding_60(self):
        """Test effort rounds to 60 minutes."""
        action = ActionSuggestion(
            action_type="task",
            description="Task",
            estimated_effort_minutes=50
        )
        assert action.estimated_effort_minutes == 60

    def test_effort_validation_large_values(self):
        """Test effort rounding for large values."""
        action = ActionSuggestion(
            action_type="project",
            description="Large project",
            estimated_effort_minutes=125
        )
        assert action.estimated_effort_minutes == 150  # Rounded to 150

    def test_action_with_crm_updates(self):
        """Test ActionSuggestion with CRM updates."""
        action = ActionSuggestion(
            action_type="update",
            description="Update account status",
            crm_updates={"status": "active", "next_review": "2024-02-01"}
        )
        assert action.crm_updates["status"] == "active"


class TestEmailDraft:
    """Tests for EmailDraft model."""

    def test_create_email_draft(self):
        """Test creating a valid EmailDraft."""
        email = EmailDraft(
            subject="Follow-up on our conversation",
            body="Hi John, I wanted to follow up on our recent conversation about...",
            to_contacts=["john@example.com"],
            cc_contacts=["manager@example.com"]
        )
        assert email.subject == "Follow-up on our conversation"
        assert len(email.to_contacts) == 1
        assert len(email.cc_contacts) == 1

    def test_email_draft_body_too_short(self):
        """Test validation fails for too short email body."""
        with pytest.raises(ValueError, match="Email body too short"):
            EmailDraft(
                subject="Test",
                body="Too short",  # Less than 50 characters
                to_contacts=["test@example.com"]
            )

    def test_email_draft_body_too_long(self):
        """Test validation fails for too long email body."""
        with pytest.raises(ValueError, match="Email body too long"):
            EmailDraft(
                subject="Test",
                body="x" * 6000,  # More than 5000 characters
                to_contacts=["test@example.com"]
            )

    def test_email_draft_with_personalization(self):
        """Test EmailDraft with personalization fields."""
        email = EmailDraft(
            subject="Hello {{name}}",
            body="Dear {{name}}, This email is about {{topic}}. " + "x" * 50,
            to_contacts=["john@example.com"],
            personalization_fields={"name": "John", "topic": "Account Review"}
        )
        assert email.personalization_fields["name"] == "John"

    def test_email_draft_default_values(self):
        """Test EmailDraft default values."""
        email = EmailDraft(
            subject="Test Subject",
            body="This is a valid email body with enough characters to pass validation.",
            to_contacts=["test@example.com"]
        )
        assert email.tone == "professional"
        assert email.urgency == Priority.MEDIUM
        assert email.cc_contacts == []


class TestTaskSuggestion:
    """Tests for TaskSuggestion model."""

    def test_create_task_suggestion(self):
        """Test creating a valid TaskSuggestion."""
        due_date = datetime.utcnow() + timedelta(days=2)
        task = TaskSuggestion(
            title="Follow up with John",
            description="Call John to discuss renewal",
            due_date=due_date,
            priority=Priority.HIGH,
            related_to={"account_id": "123", "deal_id": "456"}
        )
        assert task.title == "Follow up with John"
        assert task.priority == Priority.HIGH
        assert task.related_to["account_id"] == "123"

    def test_task_suggestion_defaults(self):
        """Test TaskSuggestion default values."""
        task = TaskSuggestion(
            title="Test Task",
            description="Test Description",
            due_date=datetime.utcnow(),
            related_to={"account_id": "123"}
        )
        assert task.priority == Priority.MEDIUM
        assert task.task_type == "follow_up"
        assert task.estimated_hours == 1.0

    def test_task_suggestion_estimated_hours_bounds(self):
        """Test estimated hours validation."""
        with pytest.raises(ValueError):
            TaskSuggestion(
                title="Test",
                description="Test",
                due_date=datetime.utcnow(),
                related_to={"account_id": "123"},
                estimated_hours=50  # Above maximum
            )


class TestEscalation:
    """Tests for Escalation model."""

    def test_create_escalation(self):
        """Test creating an Escalation."""
        escalation = Escalation(
            escalate_to="senior_manager",
            reason=EscalationReason.CHURN_RISK,
            severity=Priority.CRITICAL,
            context="Account showing signs of churn",
            recommended_actions=["Executive outreach", "Emergency call"],
            timeline="within 24 hours",
            risk_if_ignored="Potential loss of $500K account"
        )
        assert escalation.reason == EscalationReason.CHURN_RISK
        assert escalation.severity == Priority.CRITICAL
        assert len(escalation.recommended_actions) == 2

    def test_escalation_requires_actions(self):
        """Test that escalation requires at least one action."""
        with pytest.raises(ValueError, match="At least one recommended action"):
            Escalation(
                escalate_to="manager",
                reason=EscalationReason.DEAL_RISK,
                severity=Priority.HIGH,
                context="Test",
                recommended_actions=[],  # Empty
                timeline="urgent",
                risk_if_ignored="Risk"
            )

    def test_escalation_with_supporting_data(self):
        """Test Escalation with supporting data references."""
        ref = DataReference(
            source_type="zoho",
            source_id="deal_123",
            entity_type="deal",
            entity_id="123"
        )
        escalation = Escalation(
            escalate_to="vp_sales",
            reason=EscalationReason.STALLED_DEAL,
            severity=Priority.HIGH,
            context="Deal stalled for 60 days",
            recommended_actions=["Executive intervention"],
            timeline="this week",
            risk_if_ignored="Deal may be lost",
            supporting_data=[ref]
        )
        assert len(escalation.supporting_data) == 1


class TestInsightsSynthesis:
    """Tests for InsightsSynthesis model."""

    def test_create_insights_synthesis(self):
        """Test creating an InsightsSynthesis."""
        ref = DataReference(
            source_type="cognee",
            source_id="insight_1",
            entity_type="insight",
            entity_id="1"
        )
        insights = InsightsSynthesis(
            account_id="123",
            risk_level=Priority.MEDIUM,
            risk_factors=["Low engagement", "No recent activity"],
            opportunities=["Upsell potential", "Executive alignment"],
            engagement_health=0.65,
            sentiment_trend="stable",
            key_patterns=["Regular communication", "Positive feedback"],
            data_sources=[ref]
        )
        assert insights.account_id == "123"
        assert insights.engagement_health == 0.65
        assert len(insights.risk_factors) == 2
        assert len(insights.opportunities) == 2

    def test_insights_synthesis_defaults(self):
        """Test InsightsSynthesis default values."""
        ref = DataReference(
            source_type="zoho",
            source_id="account_123",
            entity_type="account",
            entity_id="123"
        )
        insights = InsightsSynthesis(
            account_id="123",
            risk_level=Priority.LOW,
            engagement_health=0.8,
            sentiment_trend="improving",
            data_sources=[ref]
        )
        assert insights.risk_factors == []
        assert insights.opportunities == []
        assert isinstance(insights.synthesized_at, datetime)


class TestRecommendation:
    """Tests for Recommendation model and complex validation."""

    def create_valid_recommendation(
        self,
        rec_type: RecommendationType = RecommendationType.FOLLOW_UP_EMAIL,
        include_email: bool = True,
        include_escalation: bool = False,
        include_task: bool = False
    ) -> Recommendation:
        """Helper to create valid recommendation."""
        confidence = ConfidenceScore(
            overall=0.8,
            level=ConfidenceLevel.HIGH,
            data_recency=0.9,
            pattern_strength=0.8,
            evidence_quality=0.75,
            rationale="High confidence"
        )

        action = ActionSuggestion(
            action_type="email",
            description="Send follow-up email"
        )

        ref = DataReference(
            source_type="zoho",
            source_id="account_123",
            entity_type="account",
            entity_id="123"
        )

        email = None
        if include_email:
            email = EmailDraft(
                subject="Follow-up",
                body="This is a valid email body with enough characters to pass validation.",
                to_contacts=["john@example.com"]
            )

        escalation = None
        if include_escalation:
            escalation = Escalation(
                escalate_to="manager",
                reason=EscalationReason.DEAL_RISK,
                severity=Priority.HIGH,
                context="Risk detected",
                recommended_actions=["Immediate action"],
                timeline="urgent",
                risk_if_ignored="Account loss"
            )

        task = None
        if include_task:
            task = TaskSuggestion(
                title="Follow up",
                description="Follow up with contact",
                due_date=datetime.utcnow() + timedelta(days=1),
                related_to={"account_id": "123"}
            )

        return Recommendation(
            recommendation_id="rec_001",
            account_id="123",
            account_name="Acme Corp",
            owner_id="user_456",
            owner_name="Jane Smith",
            type=rec_type,
            priority=Priority.HIGH,
            title="Follow up with Acme Corp",
            rationale="No activity in 30 days, engagement score declining",
            confidence=confidence,
            suggested_action=action,
            email_draft=email,
            escalation=escalation,
            task_suggestion=task,
            data_references=[ref]
        )

    def test_create_valid_recommendation(self):
        """Test creating a valid recommendation."""
        rec = self.create_valid_recommendation()
        assert rec.recommendation_id == "rec_001"
        assert rec.account_id == "123"
        assert rec.type == RecommendationType.FOLLOW_UP_EMAIL
        assert rec.email_draft is not None

    def test_recommendation_title_too_long(self):
        """Test that overly long titles are rejected."""
        with pytest.raises(ValueError, match="Title too long"):
            self.create_valid_recommendation().model_copy(
                update={"title": "x" * 200}
            )

    def test_recommendation_rationale_too_short(self):
        """Test that too short rationale is rejected."""
        with pytest.raises(ValueError, match="Rationale too short"):
            self.create_valid_recommendation().model_copy(
                update={"rationale": "Too short"}
            )

    def test_follow_up_email_requires_email_draft(self):
        """Test that FOLLOW_UP_EMAIL type requires email draft."""
        with pytest.raises(ValueError, match="Email draft required"):
            self.create_valid_recommendation(
                rec_type=RecommendationType.FOLLOW_UP_EMAIL,
                include_email=False
            )

    def test_escalation_type_requires_escalation_details(self):
        """Test that ESCALATION type requires escalation details."""
        with pytest.raises(ValueError, match="Escalation details required"):
            self.create_valid_recommendation(
                rec_type=RecommendationType.ESCALATION,
                include_email=False,
                include_escalation=False
            )

    def test_create_task_type_requires_task_suggestion(self):
        """Test that CREATE_TASK type requires task suggestion."""
        with pytest.raises(ValueError, match="Task suggestion required"):
            self.create_valid_recommendation(
                rec_type=RecommendationType.CREATE_TASK,
                include_email=False,
                include_task=False
            )

    def test_recommendation_with_insights(self):
        """Test Recommendation with insights synthesis."""
        ref = DataReference(
            source_type="cognee",
            source_id="insight_1",
            entity_type="insight",
            entity_id="1"
        )
        insights = InsightsSynthesis(
            account_id="123",
            risk_level=Priority.MEDIUM,
            engagement_health=0.7,
            sentiment_trend="stable",
            data_sources=[ref]
        )

        rec = self.create_valid_recommendation()
        rec.insights_used = insights

        assert rec.insights_used.account_id == "123"
        assert rec.insights_used.engagement_health == 0.7

    def test_recommendation_default_status(self):
        """Test Recommendation default status."""
        rec = self.create_valid_recommendation()
        assert rec.status == "pending"

    def test_recommendation_with_expiration(self):
        """Test Recommendation with expiration date."""
        expires = datetime.utcnow() + timedelta(days=3)
        rec = self.create_valid_recommendation()
        rec.expires_at = expires
        assert rec.expires_at == expires


class TestRecommendationBatch:
    """Tests for RecommendationBatch model."""

    def test_create_recommendation_batch(self):
        """Test creating a RecommendationBatch."""
        recs = [
            Recommendation(
                recommendation_id=f"rec_{i}",
                account_id="123",
                account_name="Acme",
                owner_id="user_1",
                owner_name="Jane",
                type=RecommendationType.FOLLOW_UP_EMAIL,
                priority=Priority.HIGH if i == 0 else Priority.MEDIUM,
                title=f"Recommendation {i}",
                rationale="Valid rationale with enough characters",
                confidence=ConfidenceScore(
                    overall=0.8,
                    level=ConfidenceLevel.HIGH,
                    data_recency=0.8,
                    pattern_strength=0.8,
                    evidence_quality=0.8,
                    rationale="Test"
                ),
                suggested_action=ActionSuggestion(
                    action_type="email",
                    description="Send email"
                ),
                email_draft=EmailDraft(
                    subject="Test",
                    body="This is a valid body with enough characters to pass validation.",
                    to_contacts=["test@example.com"]
                ),
                data_references=[
                    DataReference(
                        source_type="zoho",
                        source_id="account_123",
                        entity_type="account",
                        entity_id="123"
                    )
                ]
            )
            for i in range(3)
        ]

        batch = RecommendationBatch(
            account_id="123",
            recommendations=recs,
            total_count=3
        )

        assert batch.account_id == "123"
        assert len(batch.recommendations) == 3
        assert batch.total_count == 3

    def test_batch_auto_corrects_total_count(self):
        """Test that batch auto-corrects total_count."""
        recs = [
            Recommendation(
                recommendation_id=f"rec_{i}",
                account_id="123",
                account_name="Acme",
                owner_id="user_1",
                owner_name="Jane",
                type=RecommendationType.FOLLOW_UP_EMAIL,
                priority=Priority.MEDIUM,
                title=f"Rec {i}",
                rationale="Valid rationale here",
                confidence=ConfidenceScore(
                    overall=0.7,
                    level=ConfidenceLevel.MEDIUM,
                    data_recency=0.7,
                    pattern_strength=0.7,
                    evidence_quality=0.7,
                    rationale="Test"
                ),
                suggested_action=ActionSuggestion(
                    action_type="email",
                    description="Email"
                ),
                email_draft=EmailDraft(
                    subject="Test",
                    body="Valid body with enough characters to pass validation requirements.",
                    to_contacts=["test@example.com"]
                ),
                data_references=[
                    DataReference(
                        source_type="zoho",
                        source_id="account_123",
                        entity_type="account",
                        entity_id="123"
                    )
                ]
            )
            for i in range(5)
        ]

        batch = RecommendationBatch(
            account_id="123",
            recommendations=recs,
            total_count=10  # Wrong count
        )

        assert batch.total_count == 5  # Auto-corrected

    def test_batch_calculates_priority_breakdown(self):
        """Test that batch calculates priority breakdown."""
        recs = []
        for i, priority in enumerate([Priority.HIGH, Priority.HIGH, Priority.MEDIUM, Priority.LOW]):
            recs.append(
                Recommendation(
                    recommendation_id=f"rec_{i}",
                    account_id="123",
                    account_name="Acme",
                    owner_id="user_1",
                    owner_name="Jane",
                    type=RecommendationType.FOLLOW_UP_EMAIL,
                    priority=priority,
                    title=f"Rec {i}",
                    rationale="Valid rationale",
                    confidence=ConfidenceScore(
                        overall=0.7,
                        level=ConfidenceLevel.MEDIUM,
                        data_recency=0.7,
                        pattern_strength=0.7,
                        evidence_quality=0.7,
                        rationale="Test"
                    ),
                    suggested_action=ActionSuggestion(
                        action_type="email",
                        description="Email"
                    ),
                    email_draft=EmailDraft(
                        subject="Test",
                        body="Valid email body with enough characters to pass.",
                        to_contacts=["test@example.com"]
                    ),
                    data_references=[
                        DataReference(
                            source_type="zoho",
                            source_id="account_123",
                            entity_type="account",
                            entity_id="123"
                        )
                    ]
                )
            )

        batch = RecommendationBatch(
            account_id="123",
            recommendations=recs,
            total_count=4
        )

        assert batch.priority_breakdown["high"] == 2
        assert batch.priority_breakdown["medium"] == 1
        assert batch.priority_breakdown["low"] == 1


class TestRecommendationContext:
    """Tests for RecommendationContext model."""

    def test_create_recommendation_context(self):
        """Test creating a RecommendationContext."""
        context = RecommendationContext(
            account_data={"account_id": "123", "name": "Acme"},
            historical_context={"patterns": ["pattern1"]},
            run_config={"max_recommendations": 5}
        )
        assert context.account_data["account_id"] == "123"
        assert context.run_config["max_recommendations"] == 5

    def test_context_default_priority_weights(self):
        """Test default priority weights."""
        context = RecommendationContext(
            account_data={},
            historical_context={}
        )
        assert context.priority_weights["critical"] == 1.0
        assert context.priority_weights["high"] == 0.75
        assert context.priority_weights["medium"] == 0.5
        assert context.priority_weights["low"] == 0.25


class TestRecommendationResult:
    """Tests for RecommendationResult model."""

    def test_successful_result(self):
        """Test successful RecommendationResult."""
        result = RecommendationResult(
            success=True,
            account_id="123",
            recommendations=[],
            processing_time_ms=250,
            data_sources_used=["zoho", "cognee"]
        )
        assert result.success is True
        assert result.processing_time_ms == 250
        assert len(result.data_sources_used) == 2

    def test_failed_result(self):
        """Test failed RecommendationResult."""
        result = RecommendationResult(
            success=False,
            account_id="123",
            error_message="Data source unavailable",
            processing_time_ms=100
        )
        assert result.success is False
        assert result.error_message == "Data source unavailable"
        assert result.recommendations == []
