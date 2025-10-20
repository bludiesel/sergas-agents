"""Utility functions for memory analysis and pattern recognition.

Provides reusable utilities for:
- Pattern detection in historical data
- Sentiment analysis
- Timeline construction
- Relationship scoring
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re
import structlog

from src.agents.memory_models import (
    TimelineEvent, Pattern, PatternType, SentimentTrend,
    EngagementCycle, CommitmentPattern, Timeline, Milestone,
    ToneAnalysis, AlignmentScore, EventType, Commitment,
    CommitmentStatus
)

logger = structlog.get_logger(__name__)


# Pattern Detection Utilities

def detect_churn_patterns(events: List[TimelineEvent]) -> List[Pattern]:
    """Detect churn risk patterns in timeline events.

    Analyzes:
    - Declining engagement frequency
    - Negative sentiment trends
    - Executive sponsor changes
    - Deal stagnation
    - Missed commitments

    Args:
        events: Timeline events to analyze

    Returns:
        List of detected churn patterns
    """
    patterns: List[Pattern] = []
    now = datetime.utcnow()

    if not events:
        return patterns

    # Sort events by timestamp
    sorted_events = sorted(events, key=lambda x: x.timestamp)

    # Pattern 1: Engagement drop
    recent_events = [e for e in sorted_events if (now - e.timestamp).days <= 30]
    historical_events = [e for e in sorted_events if 30 < (now - e.timestamp).days <= 90]

    if len(historical_events) > 0:
        recent_rate = len(recent_events) / 30
        historical_rate = len(historical_events) / 60

        if historical_rate > 0 and recent_rate / historical_rate < 0.5:
            patterns.append(Pattern(
                pattern_id=f"churn_engagement_drop_{events[0].account_id}",
                pattern_type=PatternType.CHURN_RISK,
                confidence=0.7,
                description="Significant drop in engagement frequency detected",
                evidence=[
                    f"Recent activity rate: {recent_rate:.2f} events/day",
                    f"Historical rate: {historical_rate:.2f} events/day",
                    f"Drop: {(1 - recent_rate/historical_rate) * 100:.1f}%"
                ],
                first_detected=now - timedelta(days=30),
                last_detected=now,
                frequency=1,
                risk_score=70,
                recommendations=[
                    "Schedule urgent check-in call",
                    "Review recent interactions for issues",
                    "Engage executive sponsor"
                ]
            ))

    # Pattern 2: Executive changes
    exec_changes = [e for e in sorted_events if e.event_type == EventType.EXECUTIVE_CHANGE]
    if exec_changes and (now - exec_changes[-1].timestamp).days <= 60:
        patterns.append(Pattern(
            pattern_id=f"churn_exec_change_{events[0].account_id}",
            pattern_type=PatternType.EXECUTIVE_CHANGE,
            confidence=0.8,
            description="Recent executive sponsor change detected",
            evidence=[
                f"Executive change on {exec_changes[-1].timestamp.date()}",
                f"Total changes in 6 months: {len([e for e in exec_changes if (now - e.timestamp).days <= 180])}"
            ],
            first_detected=exec_changes[0].timestamp,
            last_detected=exec_changes[-1].timestamp,
            frequency=len(exec_changes),
            risk_score=60,
            recommendations=[
                "Rebuild relationship with new executive",
                "Schedule introduction meeting",
                "Review account strategy"
            ]
        ))

    # Pattern 3: Negative sentiment in communications
    negative_events = [e for e in sorted_events if _is_negative_sentiment(e)]
    if len(negative_events) >= 3 and (now - negative_events[-1].timestamp).days <= 30:
        patterns.append(Pattern(
            pattern_id=f"churn_negative_sentiment_{events[0].account_id}",
            pattern_type=PatternType.CHURN_RISK,
            confidence=0.75,
            description="Pattern of negative sentiment in communications",
            evidence=[
                f"Negative interactions: {len(negative_events)}",
                f"Recent negative event: {negative_events[-1].description[:100]}"
            ],
            first_detected=negative_events[0].timestamp,
            last_detected=negative_events[-1].timestamp,
            frequency=len(negative_events),
            risk_score=75,
            recommendations=[
                "Address concerns immediately",
                "Review satisfaction levels",
                "Consider escalation to management"
            ]
        ))

    return patterns


def identify_engagement_cycles(interactions: List[Dict[str, Any]]) -> List[EngagementCycle]:
    """Identify recurring engagement patterns.

    Detects:
    - Seasonal patterns
    - Quarterly cycles
    - Monthly rhythms
    - Weekly patterns

    Args:
        interactions: List of interaction dictionaries

    Returns:
        List of identified engagement cycles
    """
    cycles: List[EngagementCycle] = []

    if not interactions or len(interactions) < 10:
        return cycles

    # Sort by timestamp
    sorted_interactions = sorted(
        interactions,
        key=lambda x: datetime.fromisoformat(x.get('timestamp', '2000-01-01'))
    )

    account_id = interactions[0].get('account_id', 'unknown')

    # Analyze monthly patterns
    monthly_counts = defaultdict(int)
    for interaction in sorted_interactions:
        ts = datetime.fromisoformat(interaction.get('timestamp', '2000-01-01'))
        month_key = f"{ts.year}-{ts.month:02d}"
        monthly_counts[month_key] += 1

    if len(monthly_counts) >= 3:
        avg_monthly = sum(monthly_counts.values()) / len(monthly_counts)
        std_dev = _calculate_std_dev(list(monthly_counts.values()))

        if std_dev / avg_monthly > 0.3:  # High variability indicates cycles
            cycles.append(EngagementCycle(
                cycle_id=f"monthly_{account_id}",
                account_id=account_id,
                start_date=sorted_interactions[0]['timestamp'] if isinstance(
                    sorted_interactions[0]['timestamp'], datetime
                ) else datetime.fromisoformat(sorted_interactions[0]['timestamp']),
                end_date=sorted_interactions[-1]['timestamp'] if isinstance(
                    sorted_interactions[-1]['timestamp'], datetime
                ) else datetime.fromisoformat(sorted_interactions[-1]['timestamp']),
                cycle_length_days=30,
                average_frequency=avg_monthly,
                cycle_type="monthly",
                confidence=0.7
            ))

    # Analyze quarterly patterns
    quarterly_counts = defaultdict(int)
    for interaction in sorted_interactions:
        ts = datetime.fromisoformat(interaction.get('timestamp', '2000-01-01'))
        quarter = (ts.month - 1) // 3 + 1
        quarter_key = f"{ts.year}-Q{quarter}"
        quarterly_counts[quarter_key] += 1

    if len(quarterly_counts) >= 2:
        avg_quarterly = sum(quarterly_counts.values()) / len(quarterly_counts)

        cycles.append(EngagementCycle(
            cycle_id=f"quarterly_{account_id}",
            account_id=account_id,
            start_date=sorted_interactions[0]['timestamp'] if isinstance(
                sorted_interactions[0]['timestamp'], datetime
            ) else datetime.fromisoformat(sorted_interactions[0]['timestamp']),
            end_date=sorted_interactions[-1]['timestamp'] if isinstance(
                sorted_interactions[-1]['timestamp'], datetime
            ) else datetime.fromisoformat(sorted_interactions[-1]['timestamp']),
            cycle_length_days=90,
            average_frequency=avg_quarterly,
            cycle_type="quarterly",
            confidence=0.65
        ))

    return cycles


def find_commitment_patterns(history: Dict[str, Any]) -> List[CommitmentPattern]:
    """Analyze commitment tracking patterns.

    Identifies:
    - Completion rate trends
    - Delay patterns
    - Common commitment types
    - Risk indicators

    Args:
        history: Account history data

    Returns:
        List of commitment patterns
    """
    patterns: List[CommitmentPattern] = []

    commitments = history.get('commitments', [])
    if not commitments:
        return patterns

    account_id = history.get('account_id', 'unknown')

    # Calculate metrics
    total_commitments = len(commitments)
    completed = [c for c in commitments if c.get('status') == 'completed']
    overdue = [c for c in commitments if c.get('status') == 'overdue']
    pending = [c for c in commitments if c.get('status') == 'pending']

    completion_rate = len(completed) / total_commitments if total_commitments > 0 else 0.0

    # Calculate average delay
    delays = []
    for commitment in completed:
        if commitment.get('due_date') and commitment.get('completion_date'):
            due = datetime.fromisoformat(commitment['due_date'])
            completed_at = datetime.fromisoformat(commitment['completion_date'])
            delay = (completed_at - due).days
            if delay > 0:
                delays.append(delay)

    avg_delay = sum(delays) / len(delays) if delays else 0.0

    # Identify common types
    commitment_types = [c.get('type', 'unknown') for c in commitments]
    type_counts = Counter(commitment_types)
    common_types = [t for t, _ in type_counts.most_common(3)]

    # Identify risk indicators
    risk_indicators = []
    if completion_rate < 0.6:
        risk_indicators.append(f"Low completion rate: {completion_rate:.1%}")
    if len(overdue) > 0:
        risk_indicators.append(f"{len(overdue)} overdue commitments")
    if avg_delay > 7:
        risk_indicators.append(f"Average delay: {avg_delay:.1f} days")

    pattern = CommitmentPattern(
        pattern_id=f"commitment_pattern_{account_id}",
        account_id=account_id,
        pattern_description=f"Commitment tracking for {total_commitments} commitments",
        commitment_count=total_commitments,
        completion_rate=completion_rate,
        average_delay_days=avg_delay,
        common_commitment_types=common_types,
        risk_indicators=risk_indicators
    )

    patterns.append(pattern)
    return patterns


# Sentiment Analysis Utilities

def calculate_sentiment_trend(interactions: List[Dict[str, Any]]) -> SentimentTrend:
    """Calculate overall sentiment trend.

    Args:
        interactions: List of interactions

    Returns:
        Sentiment trend classification
    """
    if not interactions or len(interactions) < 3:
        return SentimentTrend.UNKNOWN

    # Sort by timestamp
    sorted_interactions = sorted(
        interactions,
        key=lambda x: datetime.fromisoformat(x.get('timestamp', '2000-01-01'))
    )

    # Split into recent and historical
    midpoint = len(sorted_interactions) // 2
    historical = sorted_interactions[:midpoint]
    recent = sorted_interactions[midpoint:]

    # Calculate average sentiment for each period
    historical_sentiment = _calculate_average_sentiment(historical)
    recent_sentiment = _calculate_average_sentiment(recent)

    # Determine trend
    delta = recent_sentiment - historical_sentiment

    if delta > 0.2:
        return SentimentTrend.IMPROVING
    elif delta < -0.2:
        return SentimentTrend.DECLINING
    else:
        return SentimentTrend.STABLE


def analyze_communication_tone(notes: List[str]) -> ToneAnalysis:
    """Analyze tone of communications.

    Args:
        notes: List of communication text

    Returns:
        Tone analysis result
    """
    if not notes:
        return ToneAnalysis(
            account_id="unknown",
            overall_tone="neutral",
            formality_score=0.5,
            positivity_score=0.5,
            urgency_score=0.5,
            confidence_score=0.5,
            tone_consistency=0.5
        )

    # Analyze formality
    formality_score = _calculate_formality_score(notes)

    # Analyze positivity
    positivity_score = _calculate_positivity_score(notes)

    # Analyze urgency
    urgency_score = _calculate_urgency_score(notes)

    # Analyze confidence
    confidence_score = _calculate_confidence_score(notes)

    # Calculate consistency
    tone_consistency = _calculate_tone_consistency(notes)

    # Determine overall tone
    if positivity_score > 0.6:
        overall_tone = "positive"
    elif positivity_score < 0.4:
        overall_tone = "negative"
    else:
        overall_tone = "neutral"

    return ToneAnalysis(
        account_id="unknown",
        overall_tone=overall_tone,
        formality_score=formality_score,
        positivity_score=positivity_score,
        urgency_score=urgency_score,
        confidence_score=confidence_score,
        tone_consistency=tone_consistency
    )


# Timeline Construction Utilities

def build_account_timeline(events: List[Dict[str, Any]]) -> Timeline:
    """Build complete timeline from events.

    Args:
        events: List of event dictionaries

    Returns:
        Structured timeline
    """
    if not events:
        return Timeline(
            account_id="unknown",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow(),
            total_events=0
        )

    # Convert to TimelineEvent objects
    timeline_events = []
    for event in events:
        try:
            timeline_event = TimelineEvent(
                event_id=event.get('id', f"event_{len(timeline_events)}"),
                account_id=event.get('account_id', 'unknown'),
                timestamp=datetime.fromisoformat(event.get('timestamp', datetime.utcnow().isoformat())),
                event_type=EventType(event.get('type', 'note')),
                description=event.get('description', ''),
                participants=event.get('participants', []),
                outcome=event.get('outcome'),
                impact=event.get('impact', 'medium')
            )
            timeline_events.append(timeline_event)
        except Exception as e:
            logger.warning("failed_to_parse_event", error=str(e), event=event)
            continue

    if not timeline_events:
        return Timeline(
            account_id="unknown",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow(),
            total_events=0
        )

    # Sort by timestamp
    timeline_events.sort(key=lambda x: x.timestamp)

    # Calculate event type distribution
    event_types = {}
    for event in timeline_events:
        event_type = event.event_type.value
        event_types[event_type] = event_types.get(event_type, 0) + 1

    return Timeline(
        account_id=timeline_events[0].account_id,
        events=timeline_events,
        start_date=timeline_events[0].timestamp,
        end_date=timeline_events[-1].timestamp,
        total_events=len(timeline_events),
        event_types=event_types,
        milestones=[]
    )


def identify_key_milestones(timeline: Timeline) -> List[Milestone]:
    """Identify key milestones in timeline.

    Args:
        timeline: Account timeline

    Returns:
        List of key milestones
    """
    milestones: List[Milestone] = []

    high_impact_events = [e for e in timeline.events if e.impact == 'high']

    for event in high_impact_events:
        milestone = Milestone(
            milestone_id=f"milestone_{event.event_id}",
            account_id=event.account_id,
            milestone_date=event.timestamp,
            milestone_type=event.event_type.value,
            title=event.description[:100],
            description=event.description,
            significance="high",
            impact_on_relationship=event.outcome or "Significant event in account journey"
        )
        milestones.append(milestone)

    return milestones


# Relationship Scoring Utilities

def calculate_relationship_score(interactions: Dict[str, Any]) -> float:
    """Calculate overall relationship score.

    Args:
        interactions: Interaction data

    Returns:
        Relationship score (0.0-1.0)
    """
    score = 0.5  # Base score

    # Factor 1: Interaction frequency (30% weight)
    interaction_count = interactions.get('total_interactions', 0)
    frequency_score = min(1.0, interaction_count / 50)  # Normalize to 50 interactions
    score += frequency_score * 0.3

    # Factor 2: Recency (25% weight)
    last_interaction_days = interactions.get('days_since_last_interaction', 90)
    recency_score = max(0.0, 1.0 - (last_interaction_days / 90))
    score += recency_score * 0.25

    # Factor 3: Response rate (20% weight)
    response_rate = interactions.get('response_rate', 0.5)
    score += response_rate * 0.2

    # Factor 4: Sentiment (15% weight)
    avg_sentiment = interactions.get('average_sentiment', 0.0)
    sentiment_score = (avg_sentiment + 1.0) / 2.0  # Convert -1 to 1 range to 0 to 1
    score += sentiment_score * 0.15

    # Factor 5: Executive engagement (10% weight)
    executive_engagement = interactions.get('executive_engagement', 0)
    exec_score = min(1.0, executive_engagement / 10)
    score += exec_score * 0.1

    return min(1.0, max(0.0, score))


def assess_executive_alignment(contacts: List[Dict[str, Any]]) -> AlignmentScore:
    """Assess executive alignment.

    Args:
        contacts: List of contact dictionaries

    Returns:
        Executive alignment assessment
    """
    if not contacts:
        return AlignmentScore(
            account_id="unknown",
            overall_alignment=0.0,
            executive_engagement_count=0,
            decision_maker_accessibility=0.0,
            strategic_alignment=0.0,
            sponsorship_strength=0.0
        )

    # Count executive contacts
    executives = [c for c in contacts if c.get('level') in ['C-Level', 'VP', 'Director']]
    executive_count = len(executives)

    # Calculate accessibility
    accessible_execs = [e for e in executives if e.get('accessible', False)]
    accessibility = len(accessible_execs) / executive_count if executive_count > 0 else 0.0

    # Calculate strategic alignment
    aligned_execs = [e for e in executives if e.get('alignment', 0) > 0.7]
    strategic_alignment = len(aligned_execs) / executive_count if executive_count > 0 else 0.0

    # Calculate sponsorship strength
    sponsors = [e for e in executives if e.get('is_sponsor', False)]
    sponsorship_strength = min(1.0, len(sponsors) / 2)  # Ideal is 2+ sponsors

    # Overall alignment
    overall = (accessibility + strategic_alignment + sponsorship_strength) / 3

    return AlignmentScore(
        account_id=contacts[0].get('account_id', 'unknown'),
        overall_alignment=overall,
        executive_engagement_count=executive_count,
        decision_maker_accessibility=accessibility,
        strategic_alignment=strategic_alignment,
        sponsorship_strength=sponsorship_strength
    )


# Helper Functions

def _is_negative_sentiment(event: TimelineEvent) -> bool:
    """Check if event has negative sentiment."""
    negative_keywords = [
        'issue', 'problem', 'concern', 'delay', 'frustrated',
        'unhappy', 'disappointed', 'escalation', 'complaint'
    ]
    description_lower = event.description.lower()
    return any(keyword in description_lower for keyword in negative_keywords)


def _calculate_std_dev(values: List[float]) -> float:
    """Calculate standard deviation."""
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance ** 0.5


def _calculate_average_sentiment(interactions: List[Dict[str, Any]]) -> float:
    """Calculate average sentiment from interactions."""
    sentiments = []
    for interaction in interactions:
        sentiment = interaction.get('sentiment', 0.0)
        if isinstance(sentiment, (int, float)):
            sentiments.append(sentiment)

    return sum(sentiments) / len(sentiments) if sentiments else 0.0


def _calculate_formality_score(notes: List[str]) -> float:
    """Calculate formality score from text."""
    formal_indicators = ['please', 'kindly', 'regarding', 'pursuant', 'hereby']
    informal_indicators = ['hey', 'thanks', 'cool', 'awesome', 'yeah']

    formal_count = 0
    informal_count = 0

    for note in notes:
        note_lower = note.lower()
        formal_count += sum(1 for indicator in formal_indicators if indicator in note_lower)
        informal_count += sum(1 for indicator in informal_indicators if indicator in note_lower)

    total = formal_count + informal_count
    if total == 0:
        return 0.5

    return formal_count / total


def _calculate_positivity_score(notes: List[str]) -> float:
    """Calculate positivity score from text."""
    positive_words = ['great', 'excellent', 'wonderful', 'perfect', 'love', 'appreciate']
    negative_words = ['issue', 'problem', 'concern', 'unfortunately', 'disappointed']

    positive_count = 0
    negative_count = 0

    for note in notes:
        note_lower = note.lower()
        positive_count += sum(1 for word in positive_words if word in note_lower)
        negative_count += sum(1 for word in negative_words if word in note_lower)

    total = positive_count + negative_count
    if total == 0:
        return 0.5

    return positive_count / total


def _calculate_urgency_score(notes: List[str]) -> float:
    """Calculate urgency score from text."""
    urgent_indicators = ['asap', 'urgent', 'immediately', 'critical', 'emergency']

    urgent_count = 0
    for note in notes:
        note_lower = note.lower()
        urgent_count += sum(1 for indicator in urgent_indicators if indicator in note_lower)

    # Normalize by total notes
    return min(1.0, urgent_count / len(notes)) if notes else 0.0


def _calculate_confidence_score(notes: List[str]) -> float:
    """Calculate confidence score from text."""
    confident_words = ['will', 'definitely', 'certainly', 'confident', 'sure']
    uncertain_words = ['maybe', 'perhaps', 'possibly', 'might', 'uncertain']

    confident_count = 0
    uncertain_count = 0

    for note in notes:
        note_lower = note.lower()
        confident_count += sum(1 for word in confident_words if word in note_lower)
        uncertain_count += sum(1 for word in uncertain_words if word in note_lower)

    total = confident_count + uncertain_count
    if total == 0:
        return 0.5

    return confident_count / total


def _calculate_tone_consistency(notes: List[str]) -> float:
    """Calculate tone consistency across communications."""
    if len(notes) < 2:
        return 1.0

    # Calculate formality for each note
    formality_scores = []
    for note in notes:
        score = _calculate_formality_score([note])
        formality_scores.append(score)

    # Calculate variance
    mean_formality = sum(formality_scores) / len(formality_scores)
    variance = sum((score - mean_formality) ** 2 for score in formality_scores) / len(formality_scores)
    std_dev = variance ** 0.5

    # Convert to consistency score (lower variance = higher consistency)
    consistency = 1.0 - min(1.0, std_dev * 2)
    return consistency
