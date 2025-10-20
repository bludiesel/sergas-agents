"""Comprehensive tests for confidence scoring algorithms.

Tests all scoring factors, weighted combinations, and confidence calibration.
"""

import pytest
from datetime import datetime, timedelta
from typing import Any, Dict, List

from src.agents.confidence_scoring import (
    ConfidenceScorer,
    adjust_confidence_for_priority,
    compare_confidence_scores,
    create_threshold_config,
    validate_minimum_confidence,
)
from src.agents.recommendation_models import (
    ConfidenceLevel,
    ConfidenceScore,
    DataReference,
    Priority,
)


class TestConfidenceScorer:
    """Tests for ConfidenceScorer class."""

    @pytest.fixture
    def scorer(self) -> ConfidenceScorer:
        """Create a ConfidenceScorer instance."""
        return ConfidenceScorer(
            recency_half_life_days=14,
            min_pattern_occurrences=2,
            min_evidence_sources=2
        )

    def test_scorer_initialization(self, scorer: ConfidenceScorer):
        """Test ConfidenceScorer initialization."""
        assert scorer.recency_half_life_days == 14
        assert scorer.min_pattern_occurrences == 2
        assert scorer.min_evidence_sources == 2

    # Data Recency Score Tests
    def test_data_recency_score_fresh_data(self, scorer: ConfidenceScorer):
        """Test recency score for fresh data (today)."""
        now = datetime.utcnow()
        score = scorer.calculate_data_recency_score(now, now)
        assert score == 1.0

    def test_data_recency_score_half_life(self, scorer: ConfidenceScorer):
        """Test recency score at half-life point."""
        now = datetime.utcnow()
        half_life_ago = now - timedelta(days=14)
        score = scorer.calculate_data_recency_score(half_life_ago, now)
        assert score == pytest.approx(0.5, rel=0.01)

    def test_data_recency_score_double_half_life(self, scorer: ConfidenceScorer):
        """Test recency score at double half-life."""
        now = datetime.utcnow()
        double_half_life_ago = now - timedelta(days=28)
        score = scorer.calculate_data_recency_score(double_half_life_ago, now)
        assert score == pytest.approx(0.25, rel=0.01)

    def test_data_recency_score_very_old(self, scorer: ConfidenceScorer):
        """Test recency score for very old data."""
        now = datetime.utcnow()
        old_data = now - timedelta(days=90)
        score = scorer.calculate_data_recency_score(old_data, now)
        assert score < 0.1
        assert score >= 0.0

    def test_data_recency_score_future_timestamp(self, scorer: ConfidenceScorer):
        """Test recency score handles future timestamps gracefully."""
        now = datetime.utcnow()
        future = now + timedelta(days=1)
        score = scorer.calculate_data_recency_score(future, now)
        assert score == 1.0  # Should return 1.0 for future timestamps

    def test_data_recency_score_default_current_time(self, scorer: ConfidenceScorer):
        """Test that current_time defaults to now."""
        recent = datetime.utcnow() - timedelta(hours=1)
        score = scorer.calculate_data_recency_score(recent)
        assert score > 0.99

    # Pattern Strength Score Tests
    def test_pattern_strength_score_no_occurrences(self, scorer: ConfidenceScorer):
        """Test pattern strength with no occurrences."""
        pattern = {"occurrences": 0, "consistency": 0.5, "confidence": 0.5}
        score = scorer.calculate_pattern_strength_score(pattern)
        assert score < 0.4

    def test_pattern_strength_score_minimum_occurrences(self, scorer: ConfidenceScorer):
        """Test pattern strength with minimum occurrences."""
        pattern = {"occurrences": 2, "consistency": 0.8, "confidence": 0.7}
        score = scorer.calculate_pattern_strength_score(pattern)
        assert score > 0.5

    def test_pattern_strength_score_high_occurrences(self, scorer: ConfidenceScorer):
        """Test pattern strength with high occurrences."""
        pattern = {"occurrences": 10, "consistency": 0.9, "confidence": 0.85}
        score = scorer.calculate_pattern_strength_score(pattern)
        assert score > 0.8

    def test_pattern_strength_score_high_consistency(self, scorer: ConfidenceScorer):
        """Test pattern strength with high consistency."""
        pattern = {"occurrences": 3, "consistency": 1.0, "confidence": 0.8}
        score = scorer.calculate_pattern_strength_score(pattern)
        assert score > 0.6

    def test_pattern_strength_score_low_consistency(self, scorer: ConfidenceScorer):
        """Test pattern strength with low consistency."""
        pattern = {"occurrences": 3, "consistency": 0.2, "confidence": 0.5}
        score = scorer.calculate_pattern_strength_score(pattern)
        assert score < 0.6

    def test_pattern_strength_score_missing_fields(self, scorer: ConfidenceScorer):
        """Test pattern strength handles missing fields with defaults."""
        pattern = {}  # Empty pattern
        score = scorer.calculate_pattern_strength_score(pattern)
        assert score >= 0.0
        assert score <= 1.0

    def test_pattern_strength_score_balanced(self, scorer: ConfidenceScorer):
        """Test pattern strength with balanced values."""
        pattern = {"occurrences": 5, "consistency": 0.7, "confidence": 0.7}
        score = scorer.calculate_pattern_strength_score(pattern)
        assert 0.6 <= score <= 0.8

    # Evidence Quality Score Tests
    def test_evidence_quality_score_no_references(self, scorer: ConfidenceScorer):
        """Test evidence quality with no references."""
        score = scorer.calculate_evidence_quality_score([])
        assert score == 0.0

    def test_evidence_quality_score_single_reference(self, scorer: ConfidenceScorer):
        """Test evidence quality with single reference."""
        ref = DataReference(
            source_type="zoho",
            source_id="account_123",
            entity_type="account",
            entity_id="123",
            timestamp=datetime.utcnow()
        )
        score = scorer.calculate_evidence_quality_score([ref])
        assert score < 1.0  # Below minimum sources
        assert score > 0.0

    def test_evidence_quality_score_minimum_sources(self, scorer: ConfidenceScorer):
        """Test evidence quality with minimum sources."""
        refs = [
            DataReference(
                source_type="zoho",
                source_id=f"account_{i}",
                entity_type="account",
                entity_id=str(i),
                timestamp=datetime.utcnow()
            )
            for i in range(2)
        ]
        score = scorer.calculate_evidence_quality_score(refs)
        assert score > 0.5

    def test_evidence_quality_score_diverse_sources(self, scorer: ConfidenceScorer):
        """Test evidence quality with diverse source types."""
        refs = [
            DataReference(
                source_type="zoho",
                source_id="account_1",
                entity_type="account",
                entity_id="1",
                timestamp=datetime.utcnow()
            ),
            DataReference(
                source_type="cognee",
                source_id="insight_2",
                entity_type="insight",
                entity_id="2",
                timestamp=datetime.utcnow()
            ),
            DataReference(
                source_type="memory",
                source_id="event_3",
                entity_type="event",
                entity_id="3",
                timestamp=datetime.utcnow()
            )
        ]
        score = scorer.calculate_evidence_quality_score(refs)
        assert score > 0.7  # High diversity

    def test_evidence_quality_score_old_references(self, scorer: ConfidenceScorer):
        """Test evidence quality with old references."""
        old_time = datetime.utcnow() - timedelta(days=60)
        refs = [
            DataReference(
                source_type="zoho",
                source_id=f"account_{i}",
                entity_type="account",
                entity_id=str(i),
                timestamp=old_time
            )
            for i in range(3)
        ]
        score = scorer.calculate_evidence_quality_score(refs)
        assert score < 0.5  # Low recency

    def test_evidence_quality_score_mixed_recency(self, scorer: ConfidenceScorer):
        """Test evidence quality with mixed recency."""
        now = datetime.utcnow()
        refs = [
            DataReference(
                source_type="zoho",
                source_id="account_1",
                entity_type="account",
                entity_id="1",
                timestamp=now
            ),
            DataReference(
                source_type="cognee",
                source_id="insight_2",
                entity_type="insight",
                entity_id="2",
                timestamp=now - timedelta(days=30)
            )
        ]
        score = scorer.calculate_evidence_quality_score(refs)
        assert 0.3 < score < 0.9

    # Historical Accuracy Score Tests
    def test_historical_accuracy_no_history(self, scorer: ConfidenceScorer):
        """Test historical accuracy with no past recommendations."""
        score = scorer.calculate_historical_accuracy_score([], "follow_up")
        assert score is None

    def test_historical_accuracy_different_type(self, scorer: ConfidenceScorer):
        """Test historical accuracy filters by recommendation type."""
        past = [
            {"type": "escalation", "outcome": "successful"},
            {"type": "escalation", "outcome": "successful"}
        ]
        score = scorer.calculate_historical_accuracy_score(past, "follow_up")
        assert score is None  # No matching type

    def test_historical_accuracy_perfect_success(self, scorer: ConfidenceScorer):
        """Test historical accuracy with 100% success rate."""
        past = [
            {"type": "follow_up", "outcome": "successful"},
            {"type": "follow_up", "outcome": "successful"},
            {"type": "follow_up", "status": "approved"},
            {"type": "follow_up", "outcome": "successful"},
            {"type": "follow_up", "outcome": "successful"}
        ]
        score = scorer.calculate_historical_accuracy_score(past, "follow_up")
        assert score > 0.9

    def test_historical_accuracy_mixed_results(self, scorer: ConfidenceScorer):
        """Test historical accuracy with mixed results."""
        past = [
            {"type": "follow_up", "outcome": "successful"},
            {"type": "follow_up", "outcome": "failed"},
            {"type": "follow_up", "outcome": "successful"},
            {"type": "follow_up", "outcome": "successful"},
            {"type": "follow_up", "outcome": "failed"}
        ]
        score = scorer.calculate_historical_accuracy_score(past, "follow_up")
        assert 0.5 < score < 0.7  # 60% success

    def test_historical_accuracy_small_sample_adjustment(self, scorer: ConfidenceScorer):
        """Test Wilson score adjustment for small samples."""
        # Small sample with 100% success should be adjusted down
        past_small = [
            {"type": "follow_up", "outcome": "successful"},
            {"type": "follow_up", "outcome": "successful"}
        ]
        score_small = scorer.calculate_historical_accuracy_score(past_small, "follow_up")

        # Large sample with 100% success
        past_large = [{"type": "follow_up", "outcome": "successful"} for _ in range(20)]
        score_large = scorer.calculate_historical_accuracy_score(past_large, "follow_up")

        assert score_small < score_large  # Small sample adjusted conservatively

    def test_historical_accuracy_uses_status_field(self, scorer: ConfidenceScorer):
        """Test that historical accuracy considers status field."""
        past = [
            {"type": "follow_up", "status": "approved"},
            {"type": "follow_up", "status": "approved"},
            {"type": "follow_up", "status": "rejected"}
        ]
        score = scorer.calculate_historical_accuracy_score(past, "follow_up")
        assert score is not None
        assert score > 0.4  # 2/3 success

    # Overall Confidence Calculation Tests
    def test_calculate_confidence_score_all_components(self, scorer: ConfidenceScorer):
        """Test complete confidence score calculation."""
        refs = [
            DataReference(
                source_type="zoho",
                source_id=f"account_{i}",
                entity_type="account",
                entity_id=str(i),
                timestamp=datetime.utcnow() - timedelta(days=i)
            )
            for i in range(3)
        ]

        pattern = {"occurrences": 5, "consistency": 0.8, "confidence": 0.75}

        past = [{"type": "follow_up", "outcome": "successful"} for _ in range(10)]

        confidence = scorer.calculate_confidence_score(
            data_references=refs,
            pattern=pattern,
            past_recommendations=past,
            recommendation_type="follow_up"
        )

        assert isinstance(confidence, ConfidenceScore)
        assert 0.0 <= confidence.overall <= 1.0
        assert confidence.level in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW]

    def test_calculate_confidence_score_high_confidence(self, scorer: ConfidenceScorer):
        """Test calculation results in high confidence."""
        refs = [
            DataReference(
                source_type="zoho",
                source_id="account_1",
                entity_type="account",
                entity_id="1",
                timestamp=datetime.utcnow()
            ),
            DataReference(
                source_type="cognee",
                source_id="insight_2",
                entity_type="insight",
                entity_id="2",
                timestamp=datetime.utcnow()
            )
        ]

        pattern = {"occurrences": 10, "consistency": 0.95, "confidence": 0.9}
        past = [{"type": "test", "outcome": "successful"} for _ in range(20)]

        confidence = scorer.calculate_confidence_score(
            data_references=refs,
            pattern=pattern,
            past_recommendations=past,
            recommendation_type="test"
        )

        assert confidence.level == ConfidenceLevel.HIGH
        assert confidence.overall >= 0.8

    def test_calculate_confidence_score_low_confidence(self, scorer: ConfidenceScorer):
        """Test calculation results in low confidence."""
        old_time = datetime.utcnow() - timedelta(days=60)
        refs = [
            DataReference(
                source_type="zoho",
                source_id="account_1",
                entity_type="account",
                entity_id="1",
                timestamp=old_time
            )
        ]

        pattern = {"occurrences": 1, "consistency": 0.3, "confidence": 0.4}
        past = [
            {"type": "test", "outcome": "failed"},
            {"type": "test", "outcome": "failed"}
        ]

        confidence = scorer.calculate_confidence_score(
            data_references=refs,
            pattern=pattern,
            past_recommendations=past,
            recommendation_type="test"
        )

        assert confidence.level == ConfidenceLevel.LOW
        assert confidence.overall < 0.6

    def test_calculate_confidence_score_no_pattern(self, scorer: ConfidenceScorer):
        """Test confidence calculation without pattern data."""
        refs = [
            DataReference(
                source_type="zoho",
                source_id="account_1",
                entity_type="account",
                entity_id="1",
                timestamp=datetime.utcnow()
            )
        ]

        confidence = scorer.calculate_confidence_score(
            data_references=refs,
            pattern=None
        )

        assert confidence.pattern_strength == 0.5  # Neutral default

    def test_calculate_confidence_score_no_history(self, scorer: ConfidenceScorer):
        """Test confidence calculation without historical data."""
        refs = [
            DataReference(
                source_type="zoho",
                source_id="account_1",
                entity_type="account",
                entity_id="1",
                timestamp=datetime.utcnow()
            )
        ]

        confidence = scorer.calculate_confidence_score(
            data_references=refs,
            pattern={"occurrences": 3, "consistency": 0.7, "confidence": 0.7}
        )

        assert confidence.historical_accuracy == 0.5  # Neutral default

    def test_calculate_confidence_score_rationale_generation(self, scorer: ConfidenceScorer):
        """Test that rationale is generated properly."""
        refs = [
            DataReference(
                source_type="zoho",
                source_id="account_1",
                entity_type="account",
                entity_id="1",
                timestamp=datetime.utcnow()
            )
        ]

        confidence = scorer.calculate_confidence_score(
            data_references=refs,
            pattern={"occurrences": 5, "consistency": 0.8, "confidence": 0.75}
        )

        assert len(confidence.rationale) > 20
        assert "Confidence:" in confidence.rationale


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_create_threshold_config(self):
        """Test creation of default threshold configuration."""
        config = create_threshold_config()

        assert config["recency_half_life_days"] == 14
        assert config["min_pattern_occurrences"] == 2
        assert config["min_evidence_sources"] == 2
        assert "confidence_thresholds" in config
        assert config["confidence_thresholds"]["high"] == 0.8
        assert "weights" in config

    def test_adjust_confidence_for_priority_critical(self):
        """Test confidence adjustment for critical priority."""
        confidence = ConfidenceScore(
            overall=0.7,
            level=ConfidenceLevel.MEDIUM,
            data_recency=0.7,
            pattern_strength=0.7,
            evidence_quality=0.7,
            rationale="Medium confidence"
        )

        adjusted = adjust_confidence_for_priority(confidence, Priority.CRITICAL)
        assert "Critical priority" in adjusted.rationale
        assert "additional validation" in adjusted.rationale

    def test_adjust_confidence_for_priority_low(self):
        """Test confidence adjustment for low priority."""
        confidence = ConfidenceScore(
            overall=0.55,
            level=ConfidenceLevel.LOW,
            data_recency=0.5,
            pattern_strength=0.6,
            evidence_quality=0.55,
            rationale="Low confidence"
        )

        adjusted = adjust_confidence_for_priority(confidence, Priority.LOW)
        assert "exploratory action" in adjusted.rationale

    def test_adjust_confidence_for_priority_no_change(self):
        """Test no adjustment for high confidence critical."""
        confidence = ConfidenceScore(
            overall=0.9,
            level=ConfidenceLevel.HIGH,
            data_recency=0.9,
            pattern_strength=0.9,
            evidence_quality=0.9,
            rationale="High confidence"
        )

        adjusted = adjust_confidence_for_priority(confidence, Priority.CRITICAL)
        assert "additional validation" not in adjusted.rationale

    def test_validate_minimum_confidence_pass(self):
        """Test confidence validation passes threshold."""
        confidence = ConfidenceScore(
            overall=0.75,
            level=ConfidenceLevel.MEDIUM,
            data_recency=0.7,
            pattern_strength=0.8,
            evidence_quality=0.75,
            rationale="Test"
        )

        assert validate_minimum_confidence(confidence, min_threshold=0.5) is True
        assert validate_minimum_confidence(confidence, min_threshold=0.7) is True

    def test_validate_minimum_confidence_fail(self):
        """Test confidence validation fails threshold."""
        confidence = ConfidenceScore(
            overall=0.45,
            level=ConfidenceLevel.LOW,
            data_recency=0.4,
            pattern_strength=0.5,
            evidence_quality=0.45,
            rationale="Test"
        )

        assert validate_minimum_confidence(confidence, min_threshold=0.5) is False

    def test_compare_confidence_scores_greater(self):
        """Test comparing confidence scores (score1 > score2)."""
        score1 = ConfidenceScore(
            overall=0.9,
            level=ConfidenceLevel.HIGH,
            data_recency=0.9,
            pattern_strength=0.9,
            evidence_quality=0.9,
            rationale="High"
        )

        score2 = ConfidenceScore(
            overall=0.6,
            level=ConfidenceLevel.MEDIUM,
            data_recency=0.6,
            pattern_strength=0.6,
            evidence_quality=0.6,
            rationale="Medium"
        )

        assert compare_confidence_scores(score1, score2) == 1

    def test_compare_confidence_scores_less(self):
        """Test comparing confidence scores (score1 < score2)."""
        score1 = ConfidenceScore(
            overall=0.5,
            level=ConfidenceLevel.LOW,
            data_recency=0.5,
            pattern_strength=0.5,
            evidence_quality=0.5,
            rationale="Low"
        )

        score2 = ConfidenceScore(
            overall=0.8,
            level=ConfidenceLevel.HIGH,
            data_recency=0.8,
            pattern_strength=0.8,
            evidence_quality=0.8,
            rationale="High"
        )

        assert compare_confidence_scores(score1, score2) == -1

    def test_compare_confidence_scores_equal_overall(self):
        """Test comparing equal overall scores uses evidence quality."""
        score1 = ConfidenceScore(
            overall=0.7,
            level=ConfidenceLevel.MEDIUM,
            data_recency=0.7,
            pattern_strength=0.7,
            evidence_quality=0.8,
            rationale="Test1"
        )

        score2 = ConfidenceScore(
            overall=0.7,
            level=ConfidenceLevel.MEDIUM,
            data_recency=0.7,
            pattern_strength=0.7,
            evidence_quality=0.6,
            rationale="Test2"
        )

        assert compare_confidence_scores(score1, score2) == 1  # Higher evidence quality

    def test_compare_confidence_scores_fully_equal(self):
        """Test comparing fully equal scores."""
        score1 = ConfidenceScore(
            overall=0.7,
            level=ConfidenceLevel.MEDIUM,
            data_recency=0.7,
            pattern_strength=0.7,
            evidence_quality=0.7,
            rationale="Test"
        )

        score2 = ConfidenceScore(
            overall=0.7,
            level=ConfidenceLevel.MEDIUM,
            data_recency=0.7,
            pattern_strength=0.7,
            evidence_quality=0.7,
            rationale="Test"
        )

        assert compare_confidence_scores(score1, score2) == 0
