"""Comprehensive tests for recommendation utility functions.

Tests prioritization, data reference tracking, rationale generation, and helper utilities.
"""

import pytest
from datetime import datetime, timedelta
from typing import Any, Dict, List

from src.agents.recommendation_utils import (
    calculate_recommendation_impact,
    calculate_urgency_score,
    deduplicate_recommendations,
    enrich_with_account_context,
    explain_confidence_score,
    extract_data_references,
    extract_key_entities,
    filter_expired_recommendations,
    generate_rationale,
    group_recommendations_by_account,
    prioritize_recommendations,
    validate_data_freshness,
)
from src.agents.recommendation_models import (
    ActionSuggestion,
    ConfidenceLevel,
    ConfidenceScore,
    DataReference,
    EmailDraft,
    InsightsSynthesis,
    Priority,
    Recommendation,
    RecommendationType,
)


class TestPrioritizeRecommendations:
    """Tests for recommendation prioritization."""

    def create_recommendation(
        self,
        rec_id: str,
        priority: Priority = Priority.MEDIUM,
        confidence: float = 0.7,
        rec_type: RecommendationType = RecommendationType.FOLLOW_UP_EMAIL,
        expires_days: int = 7
    ) -> Recommendation:
        """Helper to create test recommendation."""
        return Recommendation(
            recommendation_id=rec_id,
            account_id="123",
            account_name="Test Account",
            owner_id="owner_1",
            owner_name="Test Owner",
            type=rec_type,
            priority=priority,
            title=f"Test Recommendation {rec_id}",
            rationale="Test rationale for recommendation",
            confidence=ConfidenceScore(
                overall=confidence,
                level=ConfidenceLevel.HIGH if confidence >= 0.8 else ConfidenceLevel.MEDIUM,
                data_recency=confidence,
                pattern_strength=confidence,
                evidence_quality=confidence,
                rationale="Test"
            ),
            suggested_action=ActionSuggestion(
                action_type="email",
                description="Test action"
            ),
            email_draft=EmailDraft(
                subject="Test",
                body="This is a valid test email body with enough characters.",
                to_contacts=["test@example.com"]
            ),
            data_references=[
                DataReference(
                    source_type="zoho",
                    source_id="test_123",
                    entity_type="account",
                    entity_id="123"
                )
            ],
            expires_at=datetime.utcnow() + timedelta(days=expires_days)
        )

    def test_prioritize_empty_list(self):
        """Test prioritizing empty list returns empty."""
        result = prioritize_recommendations([])
        assert result == []

    def test_prioritize_single_recommendation(self):
        """Test prioritizing single recommendation."""
        rec = self.create_recommendation("rec1")
        result = prioritize_recommendations([rec])
        assert len(result) == 1
        assert result[0].recommendation_id == "rec1"

    def test_prioritize_by_priority_level(self):
        """Test prioritization favors higher priority."""
        recs = [
            self.create_recommendation("low", Priority.LOW),
            self.create_recommendation("critical", Priority.CRITICAL),
            self.create_recommendation("medium", Priority.MEDIUM),
            self.create_recommendation("high", Priority.HIGH),
        ]

        result = prioritize_recommendations(recs, max_count=10)

        assert result[0].recommendation_id == "critical"
        assert result[1].recommendation_id == "high"
        assert result[2].recommendation_id == "medium"
        assert result[3].recommendation_id == "low"

    def test_prioritize_by_confidence(self):
        """Test prioritization considers confidence."""
        recs = [
            self.create_recommendation("low_conf", Priority.HIGH, confidence=0.6),
            self.create_recommendation("high_conf", Priority.HIGH, confidence=0.9),
        ]

        result = prioritize_recommendations(recs)

        assert result[0].recommendation_id == "high_conf"

    def test_prioritize_max_count_limit(self):
        """Test max_count limits results."""
        recs = [
            self.create_recommendation(f"rec{i}", Priority.HIGH)
            for i in range(10)
        ]

        result = prioritize_recommendations(recs, max_count=3)

        assert len(result) == 3

    def test_prioritize_urgency_with_expiration(self):
        """Test prioritization considers expiration time."""
        recs = [
            self.create_recommendation("expires_week", Priority.HIGH, expires_days=7),
            self.create_recommendation("expires_day", Priority.HIGH, expires_days=1),
        ]

        result = prioritize_recommendations(recs)

        # More urgent due to earlier expiration
        assert result[0].recommendation_id == "expires_day"


class TestCalculateUrgencyScore:
    """Tests for urgency score calculation."""

    def create_recommendation(
        self,
        priority: Priority = Priority.MEDIUM,
        confidence: float = 0.7,
        rec_type: RecommendationType = RecommendationType.FOLLOW_UP_EMAIL,
        expires_at: datetime = None
    ) -> Recommendation:
        """Helper to create test recommendation."""
        if expires_at is None:
            expires_at = datetime.utcnow() + timedelta(days=7)

        return Recommendation(
            recommendation_id="test_rec",
            account_id="123",
            account_name="Test",
            owner_id="owner_1",
            owner_name="Owner",
            type=rec_type,
            priority=priority,
            title="Test",
            rationale="Test rationale here",
            confidence=ConfidenceScore(
                overall=confidence,
                level=ConfidenceLevel.HIGH if confidence >= 0.8 else ConfidenceLevel.MEDIUM,
                data_recency=confidence,
                pattern_strength=confidence,
                evidence_quality=confidence,
                rationale="Test"
            ),
            suggested_action=ActionSuggestion(
                action_type="email",
                description="Test"
            ),
            email_draft=EmailDraft(
                subject="Test",
                body="Valid email body with enough characters to pass validation.",
                to_contacts=["test@example.com"]
            ),
            data_references=[
                DataReference(
                    source_type="zoho",
                    source_id="test",
                    entity_type="account",
                    entity_id="123"
                )
            ],
            expires_at=expires_at
        )

    def test_urgency_score_critical_priority(self):
        """Test urgency score for critical priority."""
        rec = self.create_recommendation(priority=Priority.CRITICAL, confidence=0.9)
        score = calculate_urgency_score(rec)
        assert score > 90  # Should be very high

    def test_urgency_score_low_priority(self):
        """Test urgency score for low priority."""
        rec = self.create_recommendation(priority=Priority.LOW, confidence=0.6)
        score = calculate_urgency_score(rec)
        assert score < 50  # Should be low

    def test_urgency_score_high_confidence(self):
        """Test urgency score increases with confidence."""
        rec_low = self.create_recommendation(priority=Priority.MEDIUM, confidence=0.5)
        rec_high = self.create_recommendation(priority=Priority.MEDIUM, confidence=0.9)

        score_low = calculate_urgency_score(rec_low)
        score_high = calculate_urgency_score(rec_high)

        assert score_high > score_low

    def test_urgency_score_expiring_soon(self):
        """Test urgency score for soon-expiring recommendation."""
        expires_soon = datetime.utcnow() + timedelta(hours=12)
        rec = self.create_recommendation(
            priority=Priority.MEDIUM,
            expires_at=expires_soon
        )
        score = calculate_urgency_score(rec)
        assert score > 60  # Time component should boost score

    def test_urgency_score_type_multiplier_escalation(self):
        """Test escalation type gets urgency multiplier."""
        rec_escalation = self.create_recommendation(
            priority=Priority.HIGH,
            rec_type=RecommendationType.ESCALATION
        )
        rec_normal = self.create_recommendation(
            priority=Priority.HIGH,
            rec_type=RecommendationType.FOLLOW_UP_EMAIL
        )

        score_escalation = calculate_urgency_score(rec_escalation)
        score_normal = calculate_urgency_score(rec_normal)

        assert score_escalation > score_normal  # Escalation multiplier


class TestExtractDataReferences:
    """Tests for extracting data references from sources."""

    def test_extract_from_zoho_account(self):
        """Test extracting references from Zoho account data."""
        zoho_data = {
            "account_id": "123",
            "modified_time": "2024-01-15T10:30:00Z"
        }

        refs = extract_data_references(zoho_data, {})

        assert len(refs) >= 1
        assert any(ref.entity_type == "account" for ref in refs)
        assert any(ref.entity_id == "123" for ref in refs)

    def test_extract_from_zoho_deals(self):
        """Test extracting references from deals."""
        zoho_data = {
            "account_id": "123",
            "deals": [
                {"id": "deal_1", "modified_time": "2024-01-15T10:00:00Z"},
                {"id": "deal_2", "modified_time": "2024-01-16T11:00:00Z"}
            ]
        }

        refs = extract_data_references(zoho_data, {})

        deal_refs = [ref for ref in refs if ref.entity_type == "deal"]
        assert len(deal_refs) == 2

    def test_extract_from_zoho_activities(self):
        """Test extracting references from activities."""
        zoho_data = {
            "account_id": "123",
            "activities": [
                {"id": "act_1", "created_time": "2024-01-15T09:00:00Z"}
            ]
        }

        refs = extract_data_references(zoho_data, {})

        activity_refs = [ref for ref in refs if ref.entity_type == "activity"]
        assert len(activity_refs) == 1

    def test_extract_from_memory_timeline(self):
        """Test extracting references from memory timeline."""
        memory_data = {
            "account_id": "123",
            "timeline": [
                {"id": "event_1", "timestamp": "2024-01-15T10:00:00Z"},
                {"id": "event_2", "timestamp": "2024-01-16T10:00:00Z"}
            ]
        }

        refs = extract_data_references({}, memory_data)

        event_refs = [ref for ref in refs if ref.entity_type == "timeline_event"]
        assert len(event_refs) == 2

    def test_extract_from_memory_insights(self):
        """Test extracting references from insights."""
        memory_data = {
            "account_id": "123",
            "key_insights": [
                {"id": "insight_1", "generated_at": "2024-01-15T10:00:00Z"}
            ]
        }

        refs = extract_data_references({}, memory_data)

        insight_refs = [ref for ref in refs if ref.entity_type == "insight"]
        assert len(insight_refs) == 1

    def test_extract_from_both_sources(self):
        """Test extracting from both Zoho and memory data."""
        zoho_data = {
            "account_id": "123",
            "deals": [{"id": "deal_1"}]
        }
        memory_data = {
            "account_id": "123",
            "timeline": [{"id": "event_1", "timestamp": "2024-01-15T10:00:00Z"}]
        }

        refs = extract_data_references(zoho_data, memory_data)

        assert len(refs) >= 3  # account + deal + event

    def test_extract_empty_data(self):
        """Test extracting from empty data sources."""
        refs = extract_data_references({}, {})
        assert refs == []


class TestValidateDataFreshness:
    """Tests for data freshness validation."""

    def test_validate_fresh_data(self):
        """Test validation passes for fresh data."""
        refs = [
            DataReference(
                source_type="zoho",
                source_id="test_1",
                entity_type="account",
                entity_id="1",
                timestamp=datetime.utcnow() - timedelta(days=5)
            )
        ]

        assert validate_data_freshness(refs, max_age_days=30) is True

    def test_validate_stale_data(self):
        """Test validation fails for stale data."""
        refs = [
            DataReference(
                source_type="zoho",
                source_id="test_1",
                entity_type="account",
                entity_id="1",
                timestamp=datetime.utcnow() - timedelta(days=60)
            )
        ]

        assert validate_data_freshness(refs, max_age_days=30) is False

    def test_validate_mixed_freshness(self):
        """Test validation with mixed data ages."""
        refs = [
            DataReference(
                source_type="zoho",
                source_id="fresh",
                entity_type="account",
                entity_id="1",
                timestamp=datetime.utcnow() - timedelta(days=5)
            ),
            DataReference(
                source_type="cognee",
                source_id="stale",
                entity_type="insight",
                entity_id="2",
                timestamp=datetime.utcnow() - timedelta(days=60)
            )
        ]

        assert validate_data_freshness(refs, max_age_days=30) is False

    def test_validate_empty_references(self):
        """Test validation fails for empty references."""
        assert validate_data_freshness([], max_age_days=30) is False


class TestGenerateRationale:
    """Tests for rationale generation."""

    def create_recommendation_with_insights(
        self,
        risk_factors: List[str] = None,
        engagement_score: float = None
    ) -> Recommendation:
        """Helper to create recommendation with insights."""
        ref = DataReference(
            source_type="zoho",
            source_id="test",
            entity_type="account",
            entity_id="123"
        )

        insights = None
        if risk_factors is not None or engagement_score is not None:
            insights = InsightsSynthesis(
                account_id="123",
                risk_level=Priority.MEDIUM,
                risk_factors=risk_factors or [],
                engagement_health=engagement_score if engagement_score is not None else 0.7,
                sentiment_trend="stable",
                key_patterns=["Regular check-ins"],
                data_sources=[ref]
            )

        return Recommendation(
            recommendation_id="test",
            account_id="123",
            account_name="Test Account",
            owner_id="owner_1",
            owner_name="Owner",
            type=RecommendationType.FOLLOW_UP_EMAIL,
            priority=Priority.MEDIUM,
            title="Test",
            rationale="Base rationale",
            confidence=ConfidenceScore(
                overall=0.7,
                level=ConfidenceLevel.MEDIUM,
                data_recency=0.7,
                pattern_strength=0.7,
                evidence_quality=0.7,
                rationale="Test confidence rationale"
            ),
            suggested_action=ActionSuggestion(
                action_type="email",
                description="Test"
            ),
            email_draft=EmailDraft(
                subject="Test",
                body="Valid email body with enough characters.",
                to_contacts=["test@example.com"]
            ),
            data_references=[ref],
            insights_used=insights
        )

    def test_generate_rationale_includes_confidence(self):
        """Test rationale includes confidence rationale."""
        rec = self.create_recommendation_with_insights()
        context = {"account_data": {}, "historical_context": {}}

        rationale = generate_rationale(rec, context)

        assert "Test confidence rationale" in rationale

    def test_generate_rationale_with_risk_factors(self):
        """Test rationale includes risk factors."""
        rec = self.create_recommendation_with_insights(
            risk_factors=["Low engagement", "Payment delay"]
        )
        rec.priority = Priority.CRITICAL
        context = {"account_data": {}, "historical_context": {"risk_factors": ["Low engagement"]}}

        rationale = generate_rationale(rec, context)

        assert "Risk indicators" in rationale

    def test_generate_rationale_low_engagement(self):
        """Test rationale mentions low engagement."""
        rec = self.create_recommendation_with_insights(engagement_score=0.3)
        context = {"account_data": {}, "historical_context": {"engagement_score": 0.3}}

        rationale = generate_rationale(rec, context)

        assert "Low engagement" in rationale

    def test_generate_rationale_high_engagement(self):
        """Test rationale mentions high engagement opportunity."""
        rec = self.create_recommendation_with_insights(engagement_score=0.9)
        context = {"account_data": {}, "historical_context": {"engagement_score": 0.9}}

        rationale = generate_rationale(rec, context)

        assert "High engagement" in rationale or "opportunity" in rationale


class TestHelperFunctions:
    """Tests for various helper functions."""

    def test_explain_confidence_score_high(self):
        """Test confidence score explanation for high confidence."""
        scores = {
            "overall": 0.85,
            "data_recency": 0.9,
            "pattern_strength": 0.8,
            "evidence_quality": 0.85
        }

        explanation = explain_confidence_score(scores)

        assert "High confidence" in explanation
        assert "fresh data" in explanation

    def test_explain_confidence_score_low(self):
        """Test confidence score explanation for low confidence."""
        scores = {
            "overall": 0.45,
            "data_recency": 0.4,
            "pattern_strength": 0.4,
            "evidence_quality": 0.4
        }

        explanation = explain_confidence_score(scores)

        assert "Low confidence" in explanation
        assert "limited by" in explanation

    def test_group_recommendations_by_account(self):
        """Test grouping recommendations by account."""
        recs = [
            Recommendation(
                recommendation_id="rec1",
                account_id="123",
                account_name="Account 1",
                owner_id="owner_1",
                owner_name="Owner",
                type=RecommendationType.FOLLOW_UP_EMAIL,
                priority=Priority.MEDIUM,
                title="Test 1",
                rationale="Rationale for test 1",
                confidence=ConfidenceScore(
                    overall=0.7, level=ConfidenceLevel.MEDIUM,
                    data_recency=0.7, pattern_strength=0.7,
                    evidence_quality=0.7, rationale="Test"
                ),
                suggested_action=ActionSuggestion(action_type="email", description="Test"),
                email_draft=EmailDraft(subject="Test", body="Valid body for test email.",
                                       to_contacts=["test@example.com"]),
                data_references=[DataReference(source_type="zoho", source_id="test",
                                                entity_type="account", entity_id="123")]
            ),
            Recommendation(
                recommendation_id="rec2",
                account_id="456",
                account_name="Account 2",
                owner_id="owner_2",
                owner_name="Owner",
                type=RecommendationType.FOLLOW_UP_EMAIL,
                priority=Priority.MEDIUM,
                title="Test 2",
                rationale="Rationale for test 2",
                confidence=ConfidenceScore(
                    overall=0.7, level=ConfidenceLevel.MEDIUM,
                    data_recency=0.7, pattern_strength=0.7,
                    evidence_quality=0.7, rationale="Test"
                ),
                suggested_action=ActionSuggestion(action_type="email", description="Test"),
                email_draft=EmailDraft(subject="Test", body="Valid body for test email.",
                                       to_contacts=["test@example.com"]),
                data_references=[DataReference(source_type="zoho", source_id="test",
                                                entity_type="account", entity_id="456")]
            )
        ]

        groups = group_recommendations_by_account(recs)

        assert len(groups) == 2
        assert "123" in groups
        assert "456" in groups
        assert len(groups["123"]) == 1
        assert len(groups["456"]) == 1

    def test_deduplicate_recommendations(self):
        """Test deduplication of similar recommendations."""
        base_rec = Recommendation(
            recommendation_id="rec1",
            account_id="123",
            account_name="Test",
            owner_id="owner_1",
            owner_name="Owner",
            type=RecommendationType.FOLLOW_UP_EMAIL,
            priority=Priority.MEDIUM,
            title="Follow up with contact",
            rationale="Valid rationale for this recommendation",
            confidence=ConfidenceScore(
                overall=0.7, level=ConfidenceLevel.MEDIUM,
                data_recency=0.7, pattern_strength=0.7,
                evidence_quality=0.7, rationale="Test"
            ),
            suggested_action=ActionSuggestion(action_type="email", description="Test"),
            email_draft=EmailDraft(subject="Test", body="Valid email body.",
                                   to_contacts=["test@example.com"]),
            data_references=[DataReference(source_type="zoho", source_id="test",
                                            entity_type="account", entity_id="123")]
        )

        # Create duplicate
        duplicate = base_rec.model_copy(update={"recommendation_id": "rec2"})

        recs = [base_rec, duplicate]
        unique = deduplicate_recommendations(recs)

        assert len(unique) == 1

    def test_filter_expired_recommendations(self):
        """Test filtering expired recommendations."""
        valid_rec = Recommendation(
            recommendation_id="valid",
            account_id="123",
            account_name="Test",
            owner_id="owner_1",
            owner_name="Owner",
            type=RecommendationType.FOLLOW_UP_EMAIL,
            priority=Priority.MEDIUM,
            title="Valid",
            rationale="Valid rationale",
            confidence=ConfidenceScore(
                overall=0.7, level=ConfidenceLevel.MEDIUM,
                data_recency=0.7, pattern_strength=0.7,
                evidence_quality=0.7, rationale="Test"
            ),
            suggested_action=ActionSuggestion(action_type="email", description="Test"),
            email_draft=EmailDraft(subject="Test", body="Valid email body.",
                                   to_contacts=["test@example.com"]),
            data_references=[DataReference(source_type="zoho", source_id="test",
                                            entity_type="account", entity_id="123")],
            expires_at=datetime.utcnow() + timedelta(days=1)
        )

        expired_rec = valid_rec.model_copy(update={
            "recommendation_id": "expired",
            "expires_at": datetime.utcnow() - timedelta(days=1)
        })

        recs = [valid_rec, expired_rec]
        valid_recs = filter_expired_recommendations(recs)

        assert len(valid_recs) == 1
        assert valid_recs[0].recommendation_id == "valid"

    def test_extract_key_entities_emails(self):
        """Test extracting email addresses."""
        text = "Contact john@example.com or sarah.smith@company.co.uk"
        entities = extract_key_entities(text)

        assert len(entities["emails"]) == 2
        assert "john@example.com" in entities["emails"]

    def test_extract_key_entities_phones(self):
        """Test extracting phone numbers."""
        text = "Call 555-123-4567 or 800.555.0199"
        entities = extract_key_entities(text)

        assert len(entities["phones"]) >= 1

    def test_extract_key_entities_dollar_amounts(self):
        """Test extracting dollar amounts."""
        text = "Deal worth $150,000 or potentially $2.5M"
        entities = extract_key_entities(text)

        assert len(entities["dollar_amounts"]) >= 1

    def test_calculate_recommendation_impact(self):
        """Test calculating recommendation impact metrics."""
        rec = Recommendation(
            recommendation_id="test",
            account_id="123",
            account_name="Test",
            owner_id="owner_1",
            owner_name="Owner",
            type=RecommendationType.UPSELL_OPPORTUNITY,
            priority=Priority.HIGH,
            title="Upsell opportunity",
            rationale="Valid rationale",
            confidence=ConfidenceScore(
                overall=0.8, level=ConfidenceLevel.HIGH,
                data_recency=0.8, pattern_strength=0.8,
                evidence_quality=0.8, rationale="Test"
            ),
            suggested_action=ActionSuggestion(
                action_type="email",
                description="Test",
                estimated_effort_minutes=30
            ),
            email_draft=EmailDraft(subject="Test", body="Valid email body.",
                                   to_contacts=["test@example.com"]),
            data_references=[DataReference(source_type="zoho", source_id="test",
                                            entity_type="account", entity_id="123")]
        )

        impact = calculate_recommendation_impact(rec, account_value=100000.0)

        assert "revenue_potential" in impact
        assert impact["revenue_potential"] > 0
        assert "time_savings" in impact

    def test_enrich_with_account_context(self):
        """Test enriching recommendation with account context."""
        rec = Recommendation(
            recommendation_id="test",
            account_id="123",
            account_name="",  # Empty
            owner_id="owner_1",
            owner_name="",  # Empty
            type=RecommendationType.FOLLOW_UP_EMAIL,
            priority=Priority.MEDIUM,
            title="Test",
            rationale="Valid rationale",
            confidence=ConfidenceScore(
                overall=0.7, level=ConfidenceLevel.MEDIUM,
                data_recency=0.7, pattern_strength=0.7,
                evidence_quality=0.7, rationale="Test"
            ),
            suggested_action=ActionSuggestion(action_type="email", description="Test"),
            email_draft=EmailDraft(subject="Test", body="Valid email body.",
                                   to_contacts=["test@example.com"]),
            data_references=[DataReference(source_type="zoho", source_id="test",
                                            entity_type="account", entity_id="123")]
        )

        account_data = {
            "account_name": "Acme Corp",
            "owner_name": "Jane Smith"
        }

        enriched = enrich_with_account_context(rec, account_data)

        assert enriched.account_name == "Acme Corp"
        assert enriched.owner_name == "Jane Smith"
        assert enriched.expires_at is not None
