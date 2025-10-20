"""Utility functions for recommendation author.

This module provides helper functions for recommendation prioritization,
data reference tracking, and rationale generation.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
import re
import structlog

from .recommendation_models import (
    DataReference,
    Priority,
    Recommendation,
    RecommendationType
)

logger = structlog.get_logger()


def prioritize_recommendations(
    recommendations: List[Recommendation],
    max_count: int = 5
) -> List[Recommendation]:
    """Prioritize and rank recommendations.

    Args:
        recommendations: List of recommendations to prioritize
        max_count: Maximum number to return

    Returns:
        Sorted list of top recommendations
    """
    if not recommendations:
        return []

    # Calculate urgency scores
    scored_recs = [
        (rec, calculate_urgency_score(rec))
        for rec in recommendations
    ]

    # Sort by urgency score (descending)
    scored_recs.sort(key=lambda x: x[1], reverse=True)

    # Take top N
    top_recs = [rec for rec, _ in scored_recs[:max_count]]

    return top_recs


def calculate_urgency_score(recommendation: Recommendation) -> float:
    """Calculate urgency score for a recommendation.

    Combines priority, confidence, and time sensitivity.

    Args:
        recommendation: Recommendation to score

    Returns:
        Urgency score (higher = more urgent)
    """
    # Priority component (40% weight)
    priority_scores = {
        Priority.CRITICAL: 100.0,
        Priority.HIGH: 75.0,
        Priority.MEDIUM: 50.0,
        Priority.LOW: 25.0
    }
    priority_score = priority_scores.get(recommendation.priority, 50.0)

    # Confidence component (30% weight)
    confidence_score = recommendation.confidence.overall * 100.0

    # Time sensitivity component (30% weight)
    time_score = 50.0  # Default
    if recommendation.expires_at:
        time_to_expiry = (recommendation.expires_at - datetime.utcnow()).total_seconds()
        if time_to_expiry <= 86400:  # 1 day
            time_score = 100.0
        elif time_to_expiry <= 259200:  # 3 days
            time_score = 75.0
        elif time_to_expiry <= 604800:  # 1 week
            time_score = 50.0
        else:
            time_score = 25.0

    # Type-specific adjustments
    type_multipliers = {
        RecommendationType.ESCALATION: 1.2,
        RecommendationType.RISK_MITIGATION: 1.15,
        RecommendationType.RENEWAL_REMINDER: 1.1,
        RecommendationType.FOLLOW_UP_EMAIL: 1.0,
        RecommendationType.UPSELL_OPPORTUNITY: 0.95,
        RecommendationType.RE_ENGAGEMENT: 0.9
    }
    multiplier = type_multipliers.get(recommendation.type, 1.0)

    # Calculate weighted score
    urgency = (
        priority_score * 0.4 +
        confidence_score * 0.3 +
        time_score * 0.3
    ) * multiplier

    return urgency


def extract_data_references(
    zoho_data: Dict[str, Any],
    memory_data: Dict[str, Any]
) -> List[DataReference]:
    """Extract data references from data sources.

    Args:
        zoho_data: Data from Zoho Data Scout
        memory_data: Data from Memory Analyst

    Returns:
        List of DataReference objects
    """
    references: List[DataReference] = []

    # Extract from Zoho data
    if zoho_data:
        account_id = zoho_data.get('account_id', '')
        modified_time_str = zoho_data.get('modified_time')
        modified_time = _parse_datetime(modified_time_str) if modified_time_str else datetime.utcnow()

        # Account reference
        references.append(DataReference(
            source_type='zoho',
            source_id=f"account_{account_id}",
            entity_type='account',
            entity_id=account_id,
            timestamp=modified_time
        ))

        # Deal references
        for deal in zoho_data.get('deals', []):
            deal_id = deal.get('id', '')
            references.append(DataReference(
                source_type='zoho',
                source_id=f"deal_{deal_id}",
                entity_type='deal',
                entity_id=deal_id,
                timestamp=_parse_datetime(deal.get('modified_time')) or datetime.utcnow()
            ))

        # Activity references
        for activity in zoho_data.get('activities', []):
            activity_id = activity.get('id', '')
            references.append(DataReference(
                source_type='zoho',
                source_id=f"activity_{activity_id}",
                entity_type='activity',
                entity_id=activity_id,
                timestamp=_parse_datetime(activity.get('created_time')) or datetime.utcnow()
            ))

    # Extract from memory data
    if memory_data:
        account_id = memory_data.get('account_id', '')

        # Timeline events
        for event in memory_data.get('timeline', []):
            event_id = event.get('id', event.get('timestamp', ''))
            references.append(DataReference(
                source_type='cognee',
                source_id=f"event_{event_id}",
                entity_type='timeline_event',
                entity_id=str(event_id),
                timestamp=_parse_datetime(event.get('timestamp')) or datetime.utcnow()
            ))

        # Insights
        for insight in memory_data.get('key_insights', []):
            insight_id = insight.get('id', '')
            references.append(DataReference(
                source_type='cognee',
                source_id=f"insight_{insight_id}",
                entity_type='insight',
                entity_id=str(insight_id),
                timestamp=_parse_datetime(insight.get('generated_at')) or datetime.utcnow()
            ))

    return references


def validate_data_freshness(
    references: List[DataReference],
    max_age_days: int = 30
) -> bool:
    """Validate that data references are fresh enough.

    Args:
        references: Data references to validate
        max_age_days: Maximum acceptable age in days

    Returns:
        True if all references are fresh enough
    """
    if not references:
        return False

    current_time = datetime.utcnow()
    max_age = timedelta(days=max_age_days)

    for ref in references:
        age = current_time - ref.timestamp
        if age > max_age:
            logger.warning(
                "stale_data_reference",
                source=ref.source_id,
                age_days=age.days
            )
            return False

    return True


def generate_rationale(
    recommendation: Recommendation,
    context: Dict[str, Any]
) -> str:
    """Generate detailed rationale for a recommendation.

    Args:
        recommendation: Recommendation to explain
        context: Additional context

    Returns:
        Rationale text
    """
    parts: List[str] = []

    # Start with confidence rationale
    parts.append(recommendation.confidence.rationale)

    # Add context-specific information
    account_data = context.get('account_data', {})
    historical = context.get('historical_context', {})

    # Change flags
    change_flags = account_data.get('change_flags', [])
    if change_flags:
        parts.append(f"Recent changes detected: {', '.join(change_flags)}.")

    # Risk factors
    risk_factors = historical.get('risk_factors', [])
    if risk_factors and recommendation.priority in [Priority.CRITICAL, Priority.HIGH]:
        parts.append(f"Risk indicators: {', '.join(risk_factors[:3])}.")

    # Engagement health
    engagement_score = historical.get('engagement_score')
    if engagement_score is not None:
        if engagement_score < 0.4:
            parts.append(f"Low engagement (score: {engagement_score:.2f}) indicates potential disengagement.")
        elif engagement_score > 0.8:
            parts.append(f"High engagement (score: {engagement_score:.2f}) presents opportunity.")

    # Days since last activity
    last_activity_date = account_data.get('last_activity_date')
    if last_activity_date:
        days_since = (datetime.utcnow() - _parse_datetime(last_activity_date)).days
        if days_since > 14:
            parts.append(f"No activity in {days_since} days suggests follow-up needed.")

    # Pattern matching
    insights_used = recommendation.insights_used
    if insights_used and insights_used.key_patterns:
        pattern_str = insights_used.key_patterns[0] if insights_used.key_patterns else ""
        if pattern_str:
            parts.append(f"Pattern observed: {pattern_str}.")

    return " ".join(parts)


def explain_confidence_score(scores: Dict[str, float]) -> str:
    """Generate explanation for confidence score components.

    Args:
        scores: Component scores dictionary

    Returns:
        Explanation text
    """
    parts: List[str] = []

    # Overall
    overall = scores.get('overall', 0.0)
    if overall >= 0.8:
        parts.append("High confidence")
    elif overall >= 0.6:
        parts.append("Moderate confidence")
    else:
        parts.append("Low confidence")

    # Components
    recency = scores.get('data_recency', 0.0)
    pattern = scores.get('pattern_strength', 0.0)
    evidence = scores.get('evidence_quality', 0.0)

    components: List[str] = []
    if recency >= 0.7:
        components.append("fresh data")
    if pattern >= 0.7:
        components.append("strong patterns")
    if evidence >= 0.7:
        components.append("quality evidence")

    if components:
        parts.append(f"based on {', '.join(components)}")

    # Weaknesses
    weak_components: List[str] = []
    if recency < 0.5:
        weak_components.append("dated data")
    if pattern < 0.5:
        weak_components.append("weak patterns")
    if evidence < 0.5:
        weak_components.append("limited evidence")

    if weak_components:
        parts.append(f"but limited by {', '.join(weak_components)}")

    return " ".join(parts) + "."


def group_recommendations_by_account(
    recommendations: List[Recommendation]
) -> Dict[str, List[Recommendation]]:
    """Group recommendations by account ID.

    Args:
        recommendations: List of recommendations

    Returns:
        Dictionary mapping account_id to recommendations
    """
    groups: Dict[str, List[Recommendation]] = {}

    for rec in recommendations:
        account_id = rec.account_id
        if account_id not in groups:
            groups[account_id] = []
        groups[account_id].append(rec)

    return groups


def deduplicate_recommendations(
    recommendations: List[Recommendation]
) -> List[Recommendation]:
    """Remove duplicate recommendations based on similarity.

    Args:
        recommendations: List of recommendations

    Returns:
        Deduplicated list
    """
    if not recommendations:
        return []

    # Track seen combinations
    seen: Set[Tuple[str, str, str]] = set()
    unique: List[Recommendation] = []

    for rec in recommendations:
        # Create signature
        signature = (
            rec.account_id,
            rec.type.value,
            rec.title[:50]  # First 50 chars of title
        )

        if signature not in seen:
            seen.add(signature)
            unique.append(rec)
        else:
            logger.debug(
                "duplicate_recommendation_skipped",
                account_id=rec.account_id,
                type=rec.type.value
            )

    return unique


def filter_expired_recommendations(
    recommendations: List[Recommendation]
) -> List[Recommendation]:
    """Filter out expired recommendations.

    Args:
        recommendations: List of recommendations

    Returns:
        List with only non-expired recommendations
    """
    current_time = datetime.utcnow()

    valid = [
        rec for rec in recommendations
        if rec.expires_at is None or rec.expires_at > current_time
    ]

    expired_count = len(recommendations) - len(valid)
    if expired_count > 0:
        logger.info(
            "expired_recommendations_filtered",
            count=expired_count
        )

    return valid


def enrich_with_account_context(
    recommendation: Recommendation,
    account_data: Dict[str, Any]
) -> Recommendation:
    """Enrich recommendation with account context details.

    Args:
        recommendation: Recommendation to enrich
        account_data: Account data from Zoho

    Returns:
        Enriched recommendation
    """
    # Add account name if missing
    if not recommendation.account_name and 'account_name' in account_data:
        recommendation.account_name = account_data['account_name']

    # Add owner info if missing
    if not recommendation.owner_name and 'owner_name' in account_data:
        recommendation.owner_name = account_data['owner_name']

    # Set expiration if not set
    if not recommendation.expires_at:
        recommendation.expires_at = _calculate_expiration(recommendation.priority)

    return recommendation


def _parse_datetime(value: Any) -> datetime:
    """Parse datetime from various formats.

    Args:
        value: Value to parse

    Returns:
        Parsed datetime
    """
    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        # Try ISO format
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass

        # Try common formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d',
        ]
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

    # Default to now
    return datetime.utcnow()


def _calculate_expiration(priority: Priority) -> datetime:
    """Calculate expiration time based on priority.

    Args:
        priority: Recommendation priority

    Returns:
        Expiration datetime
    """
    now = datetime.utcnow()

    if priority == Priority.CRITICAL:
        return now + timedelta(hours=24)
    elif priority == Priority.HIGH:
        return now + timedelta(days=3)
    elif priority == Priority.MEDIUM:
        return now + timedelta(days=7)
    else:  # LOW
        return now + timedelta(days=14)


def extract_key_entities(text: str) -> Dict[str, List[str]]:
    """Extract key entities from text (simple pattern-based).

    Args:
        text: Text to analyze

    Returns:
        Dictionary of entity types to values
    """
    entities: Dict[str, List[str]] = {
        'emails': [],
        'phones': [],
        'dates': [],
        'dollar_amounts': []
    }

    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    entities['emails'] = re.findall(email_pattern, text)

    # Phone pattern (simple)
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    entities['phones'] = re.findall(phone_pattern, text)

    # Dollar amounts
    dollar_pattern = r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?(?:K|M|B)?'
    entities['dollar_amounts'] = re.findall(dollar_pattern, text, re.IGNORECASE)

    return entities


def calculate_recommendation_impact(
    recommendation: Recommendation,
    account_value: Optional[float] = None
) -> Dict[str, Any]:
    """Calculate potential impact of a recommendation.

    Args:
        recommendation: Recommendation to evaluate
        account_value: Total account value if available

    Returns:
        Impact metrics
    """
    impact: Dict[str, Any] = {
        'risk_reduction': 0.0,
        'revenue_potential': 0.0,
        'time_savings': 0.0,
        'relationship_improvement': 0.0
    }

    # Risk reduction for critical/high priority
    if recommendation.priority in [Priority.CRITICAL, Priority.HIGH]:
        if account_value:
            # Estimate risk as percentage of account value
            risk_percentage = 0.3 if recommendation.priority == Priority.CRITICAL else 0.15
            impact['risk_reduction'] = account_value * risk_percentage

    # Revenue potential for upsell/renewal
    if recommendation.type in [RecommendationType.UPSELL_OPPORTUNITY, RecommendationType.RENEWAL_REMINDER]:
        if account_value:
            # Estimate 10-25% expansion potential
            impact['revenue_potential'] = account_value * 0.175

    # Time savings from recommended action
    effort_minutes = recommendation.suggested_action.estimated_effort_minutes
    impact['time_savings'] = effort_minutes / 60.0  # Convert to hours

    # Relationship improvement (qualitative score 0-1)
    if recommendation.type in [RecommendationType.EXECUTIVE_ALIGNMENT, RecommendationType.RE_ENGAGEMENT]:
        impact['relationship_improvement'] = 0.8
    elif recommendation.type == RecommendationType.FOLLOW_UP_EMAIL:
        impact['relationship_improvement'] = 0.5

    return impact
