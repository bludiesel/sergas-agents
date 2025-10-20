"""Confidence scoring algorithms for recommendations.

This module implements confidence scoring logic based on data recency,
pattern strength, evidence quality, and historical accuracy.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import structlog

from .recommendation_models import (
    ConfidenceLevel,
    ConfidenceScore,
    DataReference,
    Priority
)

logger = structlog.get_logger()


class ConfidenceScorer:
    """Calculates confidence scores for recommendations."""

    def __init__(
        self,
        recency_half_life_days: int = 14,
        min_pattern_occurrences: int = 2,
        min_evidence_sources: int = 2
    ) -> None:
        """Initialize confidence scorer.

        Args:
            recency_half_life_days: Days after which data freshness score halves
            min_pattern_occurrences: Minimum occurrences for high pattern confidence
            min_evidence_sources: Minimum sources for high evidence quality
        """
        self.recency_half_life_days = recency_half_life_days
        self.min_pattern_occurrences = min_pattern_occurrences
        self.min_evidence_sources = min_evidence_sources
        self.logger = logger.bind(component="confidence_scorer")

    def calculate_data_recency_score(
        self,
        data_timestamp: datetime,
        current_time: Optional[datetime] = None
    ) -> float:
        """Calculate confidence score based on data recency.

        Uses exponential decay: score = 2^(-days_old / half_life)

        Args:
            data_timestamp: When the data was collected
            current_time: Current time (defaults to now)

        Returns:
            Recency score between 0.0 and 1.0
        """
        if current_time is None:
            current_time = datetime.utcnow()

        days_old = (current_time - data_timestamp).total_seconds() / 86400

        if days_old < 0:
            self.logger.warning(
                "future_timestamp_detected",
                data_timestamp=data_timestamp,
                current_time=current_time
            )
            return 1.0

        # Exponential decay
        score = 2 ** (-days_old / self.recency_half_life_days)

        # Clamp to [0, 1]
        return max(0.0, min(1.0, score))

    def calculate_pattern_strength_score(
        self,
        pattern: Dict[str, Any]
    ) -> float:
        """Calculate confidence based on pattern strength.

        Considers:
        - Number of occurrences
        - Consistency of pattern
        - Statistical significance

        Args:
            pattern: Pattern dictionary with occurrence data

        Returns:
            Pattern strength score between 0.0 and 1.0
        """
        occurrences = pattern.get("occurrences", 0)
        consistency = pattern.get("consistency", 0.0)  # 0.0-1.0
        confidence_from_pattern = pattern.get("confidence", 0.5)

        # Base score from occurrences (logarithmic scaling)
        if occurrences == 0:
            occurrence_score = 0.0
        elif occurrences >= self.min_pattern_occurrences * 3:
            occurrence_score = 1.0
        else:
            # Logarithmic scale between 0 and 1
            import math
            occurrence_score = min(
                1.0,
                math.log(occurrences + 1) / math.log(self.min_pattern_occurrences * 3 + 1)
            )

        # Weighted combination
        score = (
            occurrence_score * 0.4 +
            consistency * 0.3 +
            confidence_from_pattern * 0.3
        )

        return max(0.0, min(1.0, score))

    def calculate_evidence_quality_score(
        self,
        references: List[DataReference]
    ) -> float:
        """Calculate confidence based on evidence quality.

        Considers:
        - Number of independent data sources
        - Recency of each source
        - Diversity of source types

        Args:
            references: List of data references supporting the recommendation

        Returns:
            Evidence quality score between 0.0 and 1.0
        """
        if not references:
            return 0.0

        # Count unique sources
        unique_sources = len(set(ref.source_id for ref in references))

        # Source diversity (different source types)
        unique_source_types = len(set(ref.source_type for ref in references))

        # Average recency of references
        current_time = datetime.utcnow()
        recency_scores = [
            self.calculate_data_recency_score(ref.timestamp, current_time)
            for ref in references
        ]
        avg_recency = sum(recency_scores) / len(recency_scores) if recency_scores else 0.0

        # Score components
        source_count_score = min(1.0, unique_sources / self.min_evidence_sources)
        diversity_score = min(1.0, unique_source_types / 3.0)  # Expect up to 3 types

        # Weighted combination
        score = (
            source_count_score * 0.4 +
            diversity_score * 0.2 +
            avg_recency * 0.4
        )

        return max(0.0, min(1.0, score))

    def calculate_historical_accuracy_score(
        self,
        past_recommendations: List[Dict[str, Any]],
        recommendation_type: str
    ) -> Optional[float]:
        """Calculate confidence based on historical recommendation accuracy.

        Args:
            past_recommendations: Previous recommendations with outcomes
            recommendation_type: Type of current recommendation

        Returns:
            Historical accuracy score between 0.0 and 1.0, or None if no history
        """
        # Filter to same type
        relevant_recs = [
            rec for rec in past_recommendations
            if rec.get("type") == recommendation_type
        ]

        if not relevant_recs:
            return None

        # Count successful outcomes
        successful = sum(
            1 for rec in relevant_recs
            if rec.get("outcome") == "successful" or rec.get("status") == "approved"
        )

        # Calculate success rate
        success_rate = successful / len(relevant_recs)

        # Apply credibility interval adjustment for small samples
        if len(relevant_recs) < 5:
            # Wilson score interval lower bound (conservative estimate)
            import math
            n = len(relevant_recs)
            p = success_rate
            z = 1.645  # 90% confidence
            denominator = 1 + z**2 / n
            center = (p + z**2 / (2*n)) / denominator
            adjustment = z * math.sqrt((p * (1-p) + z**2/(4*n)) / n) / denominator
            success_rate = max(0.0, center - adjustment)

        return success_rate

    def assign_overall_confidence(
        self,
        scores: Dict[str, float]
    ) -> ConfidenceLevel:
        """Assign confidence level based on component scores.

        Args:
            scores: Dictionary with component scores

        Returns:
            ConfidenceLevel enum value
        """
        # Calculate weighted average
        weights = {
            "data_recency": 0.25,
            "pattern_strength": 0.25,
            "evidence_quality": 0.30,
            "historical_accuracy": 0.20
        }

        total_weight = 0.0
        weighted_sum = 0.0

        for key, weight in weights.items():
            if key in scores and scores[key] is not None:
                weighted_sum += scores[key] * weight
                total_weight += weight

        if total_weight == 0:
            return ConfidenceLevel.LOW

        overall_score = weighted_sum / total_weight

        # Assign level
        if overall_score >= 0.8:
            return ConfidenceLevel.HIGH
        elif overall_score >= 0.6:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def calculate_confidence_score(
        self,
        data_references: List[DataReference],
        pattern: Optional[Dict[str, Any]] = None,
        past_recommendations: Optional[List[Dict[str, Any]]] = None,
        recommendation_type: Optional[str] = None
    ) -> ConfidenceScore:
        """Calculate complete confidence score for a recommendation.

        Args:
            data_references: Data sources supporting the recommendation
            pattern: Pattern data if pattern-based recommendation
            past_recommendations: Historical recommendations for accuracy calculation
            recommendation_type: Type of recommendation for historical matching

        Returns:
            Complete ConfidenceScore object
        """
        # Calculate component scores
        scores: Dict[str, float] = {}

        # Data recency
        if data_references:
            recency_scores = [
                self.calculate_data_recency_score(ref.timestamp)
                for ref in data_references
            ]
            scores["data_recency"] = sum(recency_scores) / len(recency_scores)
        else:
            scores["data_recency"] = 0.0

        # Pattern strength
        if pattern:
            scores["pattern_strength"] = self.calculate_pattern_strength_score(pattern)
        else:
            scores["pattern_strength"] = 0.5  # Neutral if no pattern

        # Evidence quality
        scores["evidence_quality"] = self.calculate_evidence_quality_score(data_references)

        # Historical accuracy
        if past_recommendations and recommendation_type:
            historical = self.calculate_historical_accuracy_score(
                past_recommendations,
                recommendation_type
            )
            scores["historical_accuracy"] = historical if historical is not None else 0.5
        else:
            scores["historical_accuracy"] = 0.5  # Neutral if no history

        # Calculate overall
        level = self.assign_overall_confidence(scores)

        # Determine overall score
        weights = {
            "data_recency": 0.25,
            "pattern_strength": 0.25,
            "evidence_quality": 0.30,
            "historical_accuracy": 0.20
        }

        overall = sum(
            scores[key] * weights[key]
            for key in weights.keys()
        )

        # Generate rationale
        rationale = self._generate_rationale(scores, level)

        return ConfidenceScore(
            overall=overall,
            level=level,
            data_recency=scores["data_recency"],
            pattern_strength=scores["pattern_strength"],
            evidence_quality=scores["evidence_quality"],
            historical_accuracy=scores.get("historical_accuracy"),
            rationale=rationale
        )

    def _generate_rationale(
        self,
        scores: Dict[str, float],
        level: ConfidenceLevel
    ) -> str:
        """Generate human-readable rationale for confidence score.

        Args:
            scores: Component scores
            level: Overall confidence level

        Returns:
            Rationale text
        """
        parts = [f"Confidence: {level.value}."]

        # Data recency
        recency = scores.get("data_recency", 0.0)
        if recency >= 0.9:
            parts.append("Data is very fresh (recent).")
        elif recency >= 0.7:
            parts.append("Data is reasonably fresh.")
        elif recency >= 0.5:
            parts.append("Data is moderately dated.")
        else:
            parts.append("Data may be outdated.")

        # Pattern strength
        pattern = scores.get("pattern_strength", 0.0)
        if pattern >= 0.8:
            parts.append("Strong historical pattern observed.")
        elif pattern >= 0.6:
            parts.append("Moderate pattern evidence.")
        elif pattern >= 0.4:
            parts.append("Weak pattern support.")
        else:
            parts.append("No clear pattern.")

        # Evidence quality
        evidence = scores.get("evidence_quality", 0.0)
        if evidence >= 0.8:
            parts.append("High-quality, diverse evidence from multiple sources.")
        elif evidence >= 0.6:
            parts.append("Adequate evidence from multiple sources.")
        elif evidence >= 0.4:
            parts.append("Limited evidence sources.")
        else:
            parts.append("Minimal supporting evidence.")

        # Historical accuracy
        historical = scores.get("historical_accuracy")
        if historical is not None:
            if historical >= 0.8:
                parts.append("Similar recommendations have been highly successful.")
            elif historical >= 0.6:
                parts.append("Similar recommendations have had moderate success.")
            elif historical >= 0.4:
                parts.append("Mixed historical results for this type.")
            else:
                parts.append("Limited historical success for this type.")

        return " ".join(parts)


def create_threshold_config() -> Dict[str, Any]:
    """Create default threshold configuration for confidence scoring.

    Returns:
        Configuration dictionary
    """
    return {
        "recency_half_life_days": 14,
        "min_pattern_occurrences": 2,
        "min_evidence_sources": 2,
        "confidence_thresholds": {
            "high": 0.8,
            "medium": 0.6,
            "low": 0.5
        },
        "weights": {
            "data_recency": 0.25,
            "pattern_strength": 0.25,
            "evidence_quality": 0.30,
            "historical_accuracy": 0.20
        }
    }


def adjust_confidence_for_priority(
    confidence: ConfidenceScore,
    priority: Priority
) -> ConfidenceScore:
    """Adjust confidence score based on recommendation priority.

    Critical priorities require higher confidence; lower priorities can tolerate
    more uncertainty.

    Args:
        confidence: Original confidence score
        priority: Recommendation priority

    Returns:
        Adjusted confidence score
    """
    # Critical recommendations need higher confidence threshold
    if priority == Priority.CRITICAL and confidence.level != ConfidenceLevel.HIGH:
        # Add disclaimer to rationale
        confidence.rationale += " Note: Critical priority recommendation may require additional validation."

    # Low priority can accept lower confidence
    if priority == Priority.LOW and confidence.level == ConfidenceLevel.LOW:
        confidence.rationale += " Low priority allows for exploratory action."

    return confidence


def validate_minimum_confidence(
    confidence: ConfidenceScore,
    min_threshold: float = 0.5
) -> bool:
    """Check if confidence meets minimum threshold.

    Args:
        confidence: Confidence score to validate
        min_threshold: Minimum acceptable confidence

    Returns:
        True if confidence meets threshold
    """
    return confidence.overall >= min_threshold


def compare_confidence_scores(
    score1: ConfidenceScore,
    score2: ConfidenceScore
) -> int:
    """Compare two confidence scores for sorting.

    Args:
        score1: First confidence score
        score2: Second confidence score

    Returns:
        -1 if score1 < score2, 0 if equal, 1 if score1 > score2
    """
    if score1.overall < score2.overall:
        return -1
    elif score1.overall > score2.overall:
        return 1
    else:
        # If overall scores equal, compare by evidence quality
        if score1.evidence_quality < score2.evidence_quality:
            return -1
        elif score1.evidence_quality > score2.evidence_quality:
            return 1
        else:
            return 0
