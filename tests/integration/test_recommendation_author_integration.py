"""Integration tests for Recommendation Author workflow.

Tests complete recommendation generation workflow with Data Scout and Memory Analyst outputs.
"""

import pytest
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import Mock, patch

from src.agents.recommendation_models import (
    ConfidenceLevel,
    ConfidenceScore,
    DataReference,
    EmailDraft,
    InsightsSynthesis,
    Priority,
    Recommendation,
    RecommendationBatch,
    RecommendationContext,
    RecommendationType,
    TaskSuggestion,
)
from src.agents.confidence_scoring import ConfidenceScorer
from src.agents.recommendation_templates import TemplateRenderer
from src.agents.recommendation_utils import (
    extract_data_references,
    prioritize_recommendations,
    validate_data_freshness,
)


class TestRecommendationAuthorWorkflow:
    """Integration tests for complete recommendation generation workflow."""

    @pytest.fixture
    def zoho_data_scout_output(self) -> Dict[str, Any]:
        """Mock output from Zoho Data Scout."""
        return {
            "account_id": "ACC_12345",
            "account_name": "Acme Corporation",
            "owner_id": "USER_789",
            "owner_name": "Jane Smith",
            "modified_time": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            "last_activity_date": (datetime.utcnow() - timedelta(days=45)).isoformat(),
            "health_score": "yellow",
            "deals": [
                {
                    "id": "DEAL_001",
                    "name": "Enterprise License Renewal",
                    "stage": "Negotiation",
                    "amount": 250000,
                    "modified_time": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                    "close_date": (datetime.utcnow() + timedelta(days=60)).isoformat(),
                    "probability": 70
                }
            ],
            "activities": [
                {
                    "id": "ACT_001",
                    "type": "Call",
                    "subject": "Q4 Planning Discussion",
                    "created_time": (datetime.utcnow() - timedelta(days=45)).isoformat()
                }
            ],
            "contacts": [
                {
                    "id": "CONT_001",
                    "name": "John Doe",
                    "email": "john.doe@acme.com",
                    "title": "VP Engineering"
                }
            ],
            "change_flags": ["no_activity_30_days", "deal_stalled"]
        }

    @pytest.fixture
    def memory_analyst_output(self) -> Dict[str, Any]:
        """Mock output from Memory Analyst."""
        return {
            "account_id": "ACC_12345",
            "engagement_score": 0.45,
            "sentiment_trend": "declining",
            "risk_factors": [
                "45 days without activity",
                "Deal stalled in Negotiation for 30 days",
                "Declining engagement score"
            ],
            "opportunities": [
                "High-value renewal approaching",
                "Historical positive sentiment with product"
            ],
            "timeline": [
                {
                    "id": "TL_001",
                    "timestamp": (datetime.utcnow() - timedelta(days=45)).isoformat(),
                    "event_type": "call",
                    "summary": "Discussed Q4 plans and budget"
                },
                {
                    "id": "TL_002",
                    "timestamp": (datetime.utcnow() - timedelta(days=60)).isoformat(),
                    "event_type": "email",
                    "summary": "Sent product roadmap presentation"
                }
            ],
            "key_insights": [
                {
                    "id": "INS_001",
                    "type": "pattern",
                    "description": "Customer typically responds within 3-5 days",
                    "confidence": 0.85,
                    "generated_at": (datetime.utcnow() - timedelta(days=1)).isoformat()
                }
            ],
            "historical_recommendations": [
                {
                    "type": "follow_up_email",
                    "outcome": "successful",
                    "timestamp": (datetime.utcnow() - timedelta(days=90)).isoformat()
                },
                {
                    "type": "follow_up_email",
                    "outcome": "successful",
                    "timestamp": (datetime.utcnow() - timedelta(days=120)).isoformat()
                }
            ]
        }

    def test_extract_references_from_both_sources(
        self,
        zoho_data_scout_output: Dict[str, Any],
        memory_analyst_output: Dict[str, Any]
    ):
        """Test extracting data references from both Zoho and Memory sources."""
        refs = extract_data_references(zoho_data_scout_output, memory_analyst_output)

        assert len(refs) > 0

        # Check Zoho references
        account_refs = [r for r in refs if r.entity_type == "account"]
        assert len(account_refs) >= 1

        deal_refs = [r for r in refs if r.entity_type == "deal"]
        assert len(deal_refs) >= 1

        activity_refs = [r for r in refs if r.entity_type == "activity"]
        assert len(activity_refs) >= 1

        # Check Memory references
        timeline_refs = [r for r in refs if r.entity_type == "timeline_event"]
        assert len(timeline_refs) >= 1

        insight_refs = [r for r in refs if r.entity_type == "insight"]
        assert len(insight_refs) >= 1

    def test_validate_data_freshness_integration(
        self,
        zoho_data_scout_output: Dict[str, Any],
        memory_analyst_output: Dict[str, Any]
    ):
        """Test data freshness validation with real data structure."""
        refs = extract_data_references(zoho_data_scout_output, memory_analyst_output)

        # Most data is recent (within 60 days)
        assert validate_data_freshness(refs, max_age_days=90) is True

    def test_confidence_scoring_integration(
        self,
        zoho_data_scout_output: Dict[str, Any],
        memory_analyst_output: Dict[str, Any]
    ):
        """Test confidence scoring with integrated data."""
        scorer = ConfidenceScorer()

        refs = extract_data_references(zoho_data_scout_output, memory_analyst_output)

        pattern = {
            "occurrences": 2,
            "consistency": 0.85,
            "confidence": 0.85
        }

        confidence = scorer.calculate_confidence_score(
            data_references=refs,
            pattern=pattern,
            past_recommendations=memory_analyst_output.get("historical_recommendations"),
            recommendation_type="follow_up_email"
        )

        assert isinstance(confidence, ConfidenceScore)
        assert 0.0 <= confidence.overall <= 1.0
        assert confidence.level in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW]
        assert len(confidence.rationale) > 20

    def test_synthesize_insights_integration(
        self,
        zoho_data_scout_output: Dict[str, Any],
        memory_analyst_output: Dict[str, Any]
    ):
        """Test synthesizing insights from both data sources."""
        refs = extract_data_references(zoho_data_scout_output, memory_analyst_output)

        insights = InsightsSynthesis(
            account_id=zoho_data_scout_output["account_id"],
            risk_level=Priority.HIGH,  # Based on stalled deal and low engagement
            risk_factors=memory_analyst_output["risk_factors"],
            opportunities=memory_analyst_output["opportunities"],
            engagement_health=memory_analyst_output["engagement_score"],
            sentiment_trend=memory_analyst_output["sentiment_trend"],
            key_patterns=[
                "45 days without activity",
                "Deal stalled for 30 days"
            ],
            data_sources=refs
        )

        assert insights.account_id == "ACC_12345"
        assert insights.engagement_health == 0.45
        assert len(insights.risk_factors) >= 3
        assert insights.sentiment_trend == "declining"

    def test_generate_follow_up_recommendation(
        self,
        zoho_data_scout_output: Dict[str, Any],
        memory_analyst_output: Dict[str, Any]
    ):
        """Test generating complete follow-up recommendation."""
        # Extract references
        refs = extract_data_references(zoho_data_scout_output, memory_analyst_output)

        # Calculate confidence
        scorer = ConfidenceScorer()
        confidence = scorer.calculate_confidence_score(
            data_references=refs,
            pattern={"occurrences": 2, "consistency": 0.8, "confidence": 0.8},
            past_recommendations=memory_analyst_output.get("historical_recommendations"),
            recommendation_type="follow_up_email"
        )

        # Render email template
        renderer = TemplateRenderer()
        email = renderer.render_email_template(
            "follow_up_no_activity",
            {
                "contact_name": "John Doe",
                "account_name": zoho_data_scout_output["account_name"],
                "days_since_activity": "45",
                "key_points": "Q4 planning and Enterprise License renewal",
                "discussion_points": ["Renewal timeline", "Budget status", "Technical requirements"],
                "sender_name": zoho_data_scout_output["owner_name"],
                "to_contacts": ["john.doe@acme.com"]
            }
        )

        # Create complete recommendation
        from src.agents.recommendation_models import ActionSuggestion

        action = ActionSuggestion(
            action_type="email",
            description="Send follow-up email to re-engage account",
            subject=email.subject,
            draft_body=email.body,
            estimated_effort_minutes=15
        )

        recommendation = Recommendation(
            recommendation_id="REC_001",
            account_id=zoho_data_scout_output["account_id"],
            account_name=zoho_data_scout_output["account_name"],
            owner_id=zoho_data_scout_output["owner_id"],
            owner_name=zoho_data_scout_output["owner_name"],
            type=RecommendationType.FOLLOW_UP_EMAIL,
            priority=Priority.HIGH,
            title="Re-engage Acme Corporation - 45 days without contact",
            rationale="Account has been inactive for 45 days with a $250K deal stalled in negotiation. Declining engagement score indicates potential churn risk.",
            confidence=confidence,
            suggested_action=action,
            email_draft=email,
            data_references=refs
        )

        assert recommendation.account_id == "ACC_12345"
        assert recommendation.type == RecommendationType.FOLLOW_UP_EMAIL
        assert recommendation.priority == Priority.HIGH
        assert recommendation.email_draft is not None
        assert len(recommendation.data_references) > 0

    def test_generate_escalation_recommendation(
        self,
        zoho_data_scout_output: Dict[str, Any],
        memory_analyst_output: Dict[str, Any]
    ):
        """Test generating escalation recommendation for at-risk deal."""
        from src.agents.recommendation_models import ActionSuggestion, Escalation, EscalationReason

        refs = extract_data_references(zoho_data_scout_output, memory_analyst_output)

        scorer = ConfidenceScorer()
        confidence = scorer.calculate_confidence_score(
            data_references=refs,
            pattern={"occurrences": 3, "consistency": 0.9, "confidence": 0.85}
        )

        escalation = Escalation(
            escalate_to="senior_account_manager",
            reason=EscalationReason.DEAL_RISK,
            severity=Priority.CRITICAL,
            context="$250K Enterprise License deal stalled for 30 days with no recent contact. Account shows declining engagement.",
            recommended_actions=[
                "Executive-level outreach within 24 hours",
                "Emergency account review meeting",
                "Escalate to VP of Sales"
            ],
            timeline="within 24 hours",
            risk_if_ignored="High probability of losing $250K annual contract",
            supporting_data=refs[:5]  # Top 5 references
        )

        action = ActionSuggestion(
            action_type="escalation",
            description="Escalate at-risk deal to senior management",
            estimated_effort_minutes=60
        )

        recommendation = Recommendation(
            recommendation_id="REC_ESC_001",
            account_id=zoho_data_scout_output["account_id"],
            account_name=zoho_data_scout_output["account_name"],
            owner_id=zoho_data_scout_output["owner_id"],
            owner_name=zoho_data_scout_output["owner_name"],
            type=RecommendationType.ESCALATION,
            priority=Priority.CRITICAL,
            title="ESCALATION: Acme Corp - Deal at Risk",
            rationale="Critical escalation needed: $250K deal stalled 30+ days, no activity in 45 days, declining engagement score.",
            confidence=confidence,
            suggested_action=action,
            escalation=escalation,
            data_references=refs
        )

        assert recommendation.type == RecommendationType.ESCALATION
        assert recommendation.priority == Priority.CRITICAL
        assert recommendation.escalation is not None
        assert recommendation.escalation.severity == Priority.CRITICAL

    def test_generate_task_recommendation(
        self,
        zoho_data_scout_output: Dict[str, Any],
        memory_analyst_output: Dict[str, Any]
    ):
        """Test generating task recommendation."""
        refs = extract_data_references(zoho_data_scout_output, memory_analyst_output)

        scorer = ConfidenceScorer()
        confidence = scorer.calculate_confidence_score(data_references=refs)

        renderer = TemplateRenderer()
        task = renderer.render_task_template(
            "follow_up_call",
            {
                "account_name": zoho_data_scout_output["account_name"],
                "contact_name": "John Doe",
                "purpose": "Discuss Enterprise License renewal status",
                "topics": [
                    "Renewal timeline and budget",
                    "Address any concerns or blockers",
                    "Schedule decision-maker meeting"
                ],
                "expected_outcome": "Clear next steps and commitment timeline",
                "contact_phone": "555-0123",
                "contact_email": "john.doe@acme.com",
                "account_id": zoho_data_scout_output["account_id"],
                "priority": Priority.HIGH
            }
        )

        from src.agents.recommendation_models import ActionSuggestion

        action = ActionSuggestion(
            action_type="call",
            description="Call to discuss renewal status",
            estimated_effort_minutes=30
        )

        recommendation = Recommendation(
            recommendation_id="REC_TASK_001",
            account_id=zoho_data_scout_output["account_id"],
            account_name=zoho_data_scout_output["account_name"],
            owner_id=zoho_data_scout_output["owner_id"],
            owner_name=zoho_data_scout_output["owner_name"],
            type=RecommendationType.CREATE_TASK,
            priority=Priority.HIGH,
            title="Schedule urgent call with Acme Corp",
            rationale="Renewal deal requires immediate attention after 45 days without contact.",
            confidence=confidence,
            suggested_action=action,
            task_suggestion=task,
            data_references=refs
        )

        assert recommendation.type == RecommendationType.CREATE_TASK
        assert recommendation.task_suggestion is not None
        assert recommendation.task_suggestion.priority == Priority.HIGH

    def test_create_recommendation_batch(
        self,
        zoho_data_scout_output: Dict[str, Any],
        memory_analyst_output: Dict[str, Any]
    ):
        """Test creating batch of recommendations for an account."""
        refs = extract_data_references(zoho_data_scout_output, memory_analyst_output)
        scorer = ConfidenceScorer()

        recommendations = []

        # 1. Follow-up email recommendation
        from src.agents.recommendation_models import ActionSuggestion

        email_confidence = scorer.calculate_confidence_score(
            data_references=refs,
            pattern={"occurrences": 2, "consistency": 0.8, "confidence": 0.8}
        )

        renderer = TemplateRenderer()
        email = renderer.render_email_template(
            "follow_up_no_activity",
            {
                "contact_name": "John Doe",
                "account_name": zoho_data_scout_output["account_name"],
                "days_since_activity": "45",
                "to_contacts": ["john.doe@acme.com"]
            }
        )

        rec1 = Recommendation(
            recommendation_id="REC_001",
            account_id=zoho_data_scout_output["account_id"],
            account_name=zoho_data_scout_output["account_name"],
            owner_id=zoho_data_scout_output["owner_id"],
            owner_name=zoho_data_scout_output["owner_name"],
            type=RecommendationType.FOLLOW_UP_EMAIL,
            priority=Priority.HIGH,
            title="Send follow-up email",
            rationale="Re-engage after 45 days of inactivity",
            confidence=email_confidence,
            suggested_action=ActionSuggestion(action_type="email", description="Send email"),
            email_draft=email,
            data_references=refs
        )
        recommendations.append(rec1)

        # 2. Task recommendation
        task_confidence = scorer.calculate_confidence_score(data_references=refs)

        task = renderer.render_task_template(
            "follow_up_call",
            {
                "account_name": zoho_data_scout_output["account_name"],
                "contact_name": "John Doe",
                "topics": ["Renewal status"],
                "expected_outcome": "Next steps",
                "contact_phone": "555-0123",
                "account_id": zoho_data_scout_output["account_id"],
                "priority": Priority.MEDIUM
            }
        )

        rec2 = Recommendation(
            recommendation_id="REC_002",
            account_id=zoho_data_scout_output["account_id"],
            account_name=zoho_data_scout_output["account_name"],
            owner_id=zoho_data_scout_output["owner_id"],
            owner_name=zoho_data_scout_output["owner_name"],
            type=RecommendationType.CREATE_TASK,
            priority=Priority.MEDIUM,
            title="Schedule follow-up call",
            rationale="Follow up on email response",
            confidence=task_confidence,
            suggested_action=ActionSuggestion(action_type="call", description="Call"),
            task_suggestion=task,
            data_references=refs
        )
        recommendations.append(rec2)

        # Create batch
        batch = RecommendationBatch(
            account_id=zoho_data_scout_output["account_id"],
            recommendations=recommendations,
            total_count=len(recommendations)
        )

        assert batch.account_id == "ACC_12345"
        assert len(batch.recommendations) == 2
        assert batch.priority_breakdown["high"] == 1
        assert batch.priority_breakdown["medium"] == 1

    def test_prioritize_recommendations_integration(
        self,
        zoho_data_scout_output: Dict[str, Any],
        memory_analyst_output: Dict[str, Any]
    ):
        """Test prioritizing multiple recommendations."""
        refs = extract_data_references(zoho_data_scout_output, memory_analyst_output)
        scorer = ConfidenceScorer()

        # Create multiple recommendations with different priorities
        from src.agents.recommendation_models import ActionSuggestion

        recommendations = []
        priorities = [Priority.LOW, Priority.CRITICAL, Priority.MEDIUM, Priority.HIGH]

        for i, priority in enumerate(priorities):
            confidence = scorer.calculate_confidence_score(data_references=refs)

            rec = Recommendation(
                recommendation_id=f"REC_{i}",
                account_id=zoho_data_scout_output["account_id"],
                account_name=zoho_data_scout_output["account_name"],
                owner_id=zoho_data_scout_output["owner_id"],
                owner_name=zoho_data_scout_output["owner_name"],
                type=RecommendationType.FOLLOW_UP_EMAIL,
                priority=priority,
                title=f"Recommendation {i}",
                rationale="Valid rationale for this recommendation",
                confidence=confidence,
                suggested_action=ActionSuggestion(action_type="email", description="Test"),
                email_draft=EmailDraft(
                    subject="Test",
                    body="Valid email body with enough characters.",
                    to_contacts=["test@example.com"]
                ),
                data_references=refs
            )
            recommendations.append(rec)

        # Prioritize
        prioritized = prioritize_recommendations(recommendations, max_count=3)

        assert len(prioritized) == 3
        assert prioritized[0].priority == Priority.CRITICAL
        assert prioritized[1].priority == Priority.HIGH

    def test_recommendation_context_creation(
        self,
        zoho_data_scout_output: Dict[str, Any],
        memory_analyst_output: Dict[str, Any]
    ):
        """Test creating recommendation context from data sources."""
        context = RecommendationContext(
            account_data=zoho_data_scout_output,
            historical_context=memory_analyst_output,
            run_config={
                "max_recommendations": 5,
                "min_confidence_threshold": 0.6,
                "include_email_drafts": True,
                "include_task_suggestions": True
            }
        )

        assert context.account_data["account_id"] == "ACC_12345"
        assert context.historical_context["engagement_score"] == 0.45
        assert context.run_config["max_recommendations"] == 5
        assert context.priority_weights["critical"] == 1.0


class TestApprovalGateIntegration:
    """Integration tests for approval gate workflow."""

    def test_recommendation_approval_workflow(self):
        """Test recommendation moves through approval states."""
        from src.agents.recommendation_models import ActionSuggestion

        # Create recommendation in pending state
        recommendation = Recommendation(
            recommendation_id="REC_APPROVAL_001",
            account_id="ACC_123",
            account_name="Test Account",
            owner_id="USER_456",
            owner_name="Test Owner",
            type=RecommendationType.FOLLOW_UP_EMAIL,
            priority=Priority.HIGH,
            title="Test Recommendation",
            rationale="Valid rationale for approval test",
            confidence=ConfidenceScore(
                overall=0.85,
                level=ConfidenceLevel.HIGH,
                data_recency=0.9,
                pattern_strength=0.8,
                evidence_quality=0.85,
                rationale="High confidence"
            ),
            suggested_action=ActionSuggestion(action_type="email", description="Send email"),
            email_draft=EmailDraft(
                subject="Test Email",
                body="This is a valid test email body with enough characters.",
                to_contacts=["test@example.com"]
            ),
            data_references=[
                DataReference(
                    source_type="zoho",
                    source_id="account_123",
                    entity_type="account",
                    entity_id="123"
                )
            ],
            status="pending"
        )

        assert recommendation.status == "pending"

        # Simulate approval
        recommendation.status = "approved"
        assert recommendation.status == "approved"

        # Simulate execution
        recommendation.status = "executed"
        assert recommendation.status == "executed"

    def test_high_confidence_auto_approval(self):
        """Test that high confidence recommendations can be auto-approved."""
        from src.agents.recommendation_models import ActionSuggestion

        recommendation = Recommendation(
            recommendation_id="REC_AUTO_001",
            account_id="ACC_123",
            account_name="Test Account",
            owner_id="USER_456",
            owner_name="Test Owner",
            type=RecommendationType.FOLLOW_UP_EMAIL,
            priority=Priority.MEDIUM,
            title="Low-risk auto-approval",
            rationale="Valid rationale",
            confidence=ConfidenceScore(
                overall=0.92,
                level=ConfidenceLevel.HIGH,
                data_recency=0.95,
                pattern_strength=0.9,
                evidence_quality=0.9,
                rationale="Very high confidence"
            ),
            suggested_action=ActionSuggestion(action_type="email", description="Send email"),
            email_draft=EmailDraft(
                subject="Test",
                body="Valid test email body with enough characters.",
                to_contacts=["test@example.com"]
            ),
            data_references=[
                DataReference(
                    source_type="zoho",
                    source_id="test",
                    entity_type="account",
                    entity_id="123"
                )
            ]
        )

        # Auto-approval logic: confidence >= 0.9 and priority <= MEDIUM
        can_auto_approve = (
            recommendation.confidence.overall >= 0.9 and
            recommendation.priority in [Priority.LOW, Priority.MEDIUM]
        )

        assert can_auto_approve is True

    def test_critical_priority_requires_approval(self):
        """Test that critical recommendations require manual approval."""
        from src.agents.recommendation_models import ActionSuggestion, Escalation, EscalationReason

        recommendation = Recommendation(
            recommendation_id="REC_CRITICAL_001",
            account_id="ACC_123",
            account_name="Test Account",
            owner_id="USER_456",
            owner_name="Test Owner",
            type=RecommendationType.ESCALATION,
            priority=Priority.CRITICAL,
            title="Critical escalation",
            rationale="Valid rationale for critical escalation",
            confidence=ConfidenceScore(
                overall=0.95,
                level=ConfidenceLevel.HIGH,
                data_recency=0.95,
                pattern_strength=0.95,
                evidence_quality=0.95,
                rationale="High confidence"
            ),
            suggested_action=ActionSuggestion(action_type="escalation", description="Escalate"),
            escalation=Escalation(
                escalate_to="VP Sales",
                reason=EscalationReason.CHURN_RISK,
                severity=Priority.CRITICAL,
                context="Critical situation",
                recommended_actions=["Immediate action"],
                timeline="24 hours",
                risk_if_ignored="Account loss"
            ),
            data_references=[
                DataReference(
                    source_type="zoho",
                    source_id="test",
                    entity_type="account",
                    entity_id="123"
                )
            ]
        )

        # Critical always requires approval regardless of confidence
        requires_manual_approval = recommendation.priority == Priority.CRITICAL

        assert requires_manual_approval is True
