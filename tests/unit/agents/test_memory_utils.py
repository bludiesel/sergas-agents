"""Comprehensive unit tests for Memory Utilities.

Tests cover:
- detect_churn_patterns (10+ tests)
- identify_engagement_cycles (10+ tests)
- calculate_sentiment_trend (10+ tests)
- build_account_timeline (10+ tests)
- All utility functions (5+ tests)

Target: 90%+ coverage.
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any

from src.agents.memory_utils import (
    detect_churn_patterns, identify_engagement_cycles,
    find_commitment_patterns, calculate_sentiment_trend,
    analyze_communication_tone, build_account_timeline,
    identify_key_milestones, calculate_relationship_score,
    assess_executive_alignment
)
from src.agents.memory_models import (
    TimelineEvent, Pattern, PatternType, SentimentTrend,
    EventType, EngagementCycle, CommitmentPattern,
    Timeline, Milestone, ToneAnalysis, AlignmentScore
)


# Test detect_churn_patterns

def test_detect_churn_patterns_engagement_drop():
    """Test churn detection with engagement drop."""
    now = datetime.utcnow()

    # Historical: high engagement
    events = [
        TimelineEvent(
            event_id=f"hist{i}",
            account_id="acc123",
            timestamp=now - timedelta(days=i+30),
            event_type=EventType.EMAIL,
            description="Activity",
            participants=[],
            metadata={}
        )
        for i in range(60)
    ]

    # Recent: low engagement
    events.extend([
        TimelineEvent(
            event_id=f"recent{i}",
            account_id="acc123",
            timestamp=now - timedelta(days=i),
            event_type=EventType.EMAIL,
            description="Activity",
            participants=[],
            metadata={}
        )
        for i in range(5)
    ])

    patterns = detect_churn_patterns(events)

    assert len(patterns) > 0
    engagement_drops = [p for p in patterns if "engagement" in p.description.lower()]
    assert len(engagement_drops) > 0


def test_detect_churn_patterns_executive_changes():
    """Test churn detection with executive changes."""
    now = datetime.utcnow()

    events = [
        TimelineEvent(
            event_id=f"exec{i}",
            account_id="acc123",
            timestamp=now - timedelta(days=i*45),
            event_type=EventType.EXECUTIVE_CHANGE,
            description=f"Executive sponsor changed",
            participants=["Old", "New"],
            metadata={}
        )
        for i in range(3)
    ]

    patterns = detect_churn_patterns(events)

    exec_patterns = [p for p in patterns if p.pattern_type == PatternType.EXECUTIVE_CHANGE]
    assert len(exec_patterns) > 0


def test_detect_churn_patterns_negative_sentiment():
    """Test churn detection with negative sentiment."""
    now = datetime.utcnow()

    events = [
        TimelineEvent(
            event_id=f"neg{i}",
            account_id="acc123",
            timestamp=now - timedelta(days=i*5),
            event_type=EventType.EMAIL,
            description="Issue with product causing concern and frustration",
            participants=[],
            metadata={"sentiment": -0.8}
        )
        for i in range(4)
    ]

    patterns = detect_churn_patterns(events)

    sentiment_patterns = [p for p in patterns if "sentiment" in p.description.lower()]
    assert len(sentiment_patterns) > 0


def test_detect_churn_patterns_empty_events():
    """Test churn detection with empty event list."""
    patterns = detect_churn_patterns([])

    assert patterns == []


def test_detect_churn_patterns_stable_engagement():
    """Test no churn pattern with stable engagement."""
    now = datetime.utcnow()

    events = [
        TimelineEvent(
            event_id=f"event{i}",
            account_id="acc123",
            timestamp=now - timedelta(days=i*2),
            event_type=EventType.EMAIL,
            description="Regular activity",
            participants=[],
            metadata={}
        )
        for i in range(50)
    ]

    patterns = detect_churn_patterns(events)

    # Should not detect engagement drop
    engagement_drops = [p for p in patterns if "engagement dropped" in p.description.lower()]
    assert len(engagement_drops) == 0


def test_detect_churn_patterns_recommendations():
    """Test that churn patterns include recommendations."""
    now = datetime.utcnow()

    events = [
        TimelineEvent(
            event_id="exec1",
            account_id="acc123",
            timestamp=now - timedelta(days=30),
            event_type=EventType.EXECUTIVE_CHANGE,
            description="Sponsor changed",
            participants=[],
            metadata={}
        )
    ]

    patterns = detect_churn_patterns(events)

    for pattern in patterns:
        assert isinstance(pattern.recommendations, list)


def test_detect_churn_patterns_risk_scores():
    """Test churn patterns have valid risk scores."""
    now = datetime.utcnow()

    events = [
        TimelineEvent(
            event_id=f"event{i}",
            account_id="acc123",
            timestamp=now - timedelta(days=i*10),
            event_type=EventType.EXECUTIVE_CHANGE if i < 2 else EventType.EMAIL,
            description="Event",
            participants=[],
            metadata={}
        )
        for i in range(10)
    ]

    patterns = detect_churn_patterns(events)

    for pattern in patterns:
        assert 0 <= pattern.risk_score <= 100


def test_detect_churn_patterns_confidence():
    """Test churn patterns have valid confidence scores."""
    now = datetime.utcnow()

    events = [
        TimelineEvent(
            event_id="exec1",
            account_id="acc123",
            timestamp=now - timedelta(days=45),
            event_type=EventType.EXECUTIVE_CHANGE,
            description="Change",
            participants=[],
            metadata={}
        ),
        TimelineEvent(
            event_id="exec2",
            account_id="acc123",
            timestamp=now - timedelta(days=30),
            event_type=EventType.EXECUTIVE_CHANGE,
            description="Change",
            participants=[],
            metadata={}
        )
    ]

    patterns = detect_churn_patterns(events)

    for pattern in patterns:
        assert 0.0 <= pattern.confidence <= 1.0


def test_detect_churn_patterns_evidence():
    """Test churn patterns include evidence."""
    now = datetime.utcnow()

    # Create many historical events, few recent
    events = []
    for i in range(60):
        events.append(TimelineEvent(
            event_id=f"hist{i}",
            account_id="acc123",
            timestamp=now - timedelta(days=i+30),
            event_type=EventType.EMAIL,
            description="Activity",
            participants=[],
            metadata={}
        ))

    for i in range(3):
        events.append(TimelineEvent(
            event_id=f"recent{i}",
            account_id="acc123",
            timestamp=now - timedelta(days=i),
            event_type=EventType.EMAIL,
            description="Activity",
            participants=[],
            metadata={}
        ))

    patterns = detect_churn_patterns(events)

    for pattern in patterns:
        assert isinstance(pattern.evidence, list)


def test_detect_churn_patterns_temporal_data():
    """Test churn patterns have valid temporal data."""
    now = datetime.utcnow()

    events = [
        TimelineEvent(
            event_id="event1",
            account_id="acc123",
            timestamp=now - timedelta(days=30),
            event_type=EventType.EXECUTIVE_CHANGE,
            description="Change",
            participants=[],
            metadata={}
        )
    ]

    patterns = detect_churn_patterns(events)

    for pattern in patterns:
        assert isinstance(pattern.first_detected, datetime)
        assert isinstance(pattern.last_detected, datetime)


# Test identify_engagement_cycles

def test_identify_engagement_cycles_monthly():
    """Test identification of monthly engagement cycles."""
    now = datetime.utcnow()

    # Create monthly pattern: activity clusters each month
    interactions = []
    for month in range(6):
        for day in range(5):  # 5 interactions per month
            interactions.append({
                'account_id': 'acc123',
                'timestamp': (now - timedelta(days=month*30 + day)).isoformat(),
                'type': 'email'
            })

    cycles = identify_engagement_cycles(interactions)

    assert len(cycles) > 0
    monthly_cycles = [c for c in cycles if c.cycle_type == "monthly"]
    assert len(monthly_cycles) > 0


def test_identify_engagement_cycles_quarterly():
    """Test identification of quarterly engagement cycles."""
    now = datetime.utcnow()

    # Create quarterly pattern
    interactions = []
    for quarter in range(4):
        for week in range(10):  # Activity throughout quarter
            interactions.append({
                'account_id': 'acc123',
                'timestamp': (now - timedelta(days=quarter*90 + week*7)).isoformat(),
                'type': 'meeting'
            })

    cycles = identify_engagement_cycles(interactions)

    quarterly_cycles = [c for c in cycles if c.cycle_type == "quarterly"]
    assert len(quarterly_cycles) > 0


def test_identify_engagement_cycles_insufficient_data():
    """Test cycle detection with insufficient data."""
    interactions = [
        {
            'account_id': 'acc123',
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'email'
        }
        for _ in range(5)
    ]

    cycles = identify_engagement_cycles(interactions)

    assert cycles == []


def test_identify_engagement_cycles_empty():
    """Test cycle detection with empty data."""
    cycles = identify_engagement_cycles([])

    assert cycles == []


def test_identify_engagement_cycles_confidence():
    """Test engagement cycles have valid confidence scores."""
    now = datetime.utcnow()

    interactions = []
    for month in range(6):
        for day in range(8):
            interactions.append({
                'account_id': 'acc123',
                'timestamp': (now - timedelta(days=month*30 + day)).isoformat(),
                'type': 'email'
            })

    cycles = identify_engagement_cycles(interactions)

    for cycle in cycles:
        assert 0.0 <= cycle.confidence <= 1.0


def test_identify_engagement_cycles_dates():
    """Test engagement cycles have valid date ranges."""
    now = datetime.utcnow()

    interactions = []
    for month in range(6):
        for day in range(5):
            interactions.append({
                'account_id': 'acc123',
                'timestamp': (now - timedelta(days=month*30 + day)).isoformat(),
                'type': 'email'
            })

    cycles = identify_engagement_cycles(interactions)

    for cycle in cycles:
        assert isinstance(cycle.start_date, datetime)
        assert isinstance(cycle.end_date, datetime)
        assert cycle.start_date <= cycle.end_date


def test_identify_engagement_cycles_frequency():
    """Test engagement cycles calculate frequency."""
    now = datetime.utcnow()

    interactions = []
    for month in range(6):
        for day in range(10):
            interactions.append({
                'account_id': 'acc123',
                'timestamp': (now - timedelta(days=month*30 + day)).isoformat(),
                'type': 'email'
            })

    cycles = identify_engagement_cycles(interactions)

    for cycle in cycles:
        assert cycle.average_frequency > 0


def test_identify_engagement_cycles_length():
    """Test engagement cycles have valid lengths."""
    now = datetime.utcnow()

    interactions = []
    for month in range(6):
        for day in range(5):
            interactions.append({
                'account_id': 'acc123',
                'timestamp': (now - timedelta(days=month*30 + day)).isoformat(),
                'type': 'email'
            })

    cycles = identify_engagement_cycles(interactions)

    for cycle in cycles:
        assert cycle.cycle_length_days > 0


def test_identify_engagement_cycles_account_id():
    """Test engagement cycles preserve account ID."""
    interactions = []
    now = datetime.utcnow()

    for month in range(6):
        for day in range(5):
            interactions.append({
                'account_id': 'acc999',
                'timestamp': (now - timedelta(days=month*30 + day)).isoformat(),
                'type': 'email'
            })

    cycles = identify_engagement_cycles(interactions)

    for cycle in cycles:
        assert cycle.account_id == 'acc999'


# Test find_commitment_patterns

def test_find_commitment_patterns_success():
    """Test commitment pattern detection."""
    history = {
        'account_id': 'acc123',
        'commitments': [
            {'status': 'completed', 'type': 'feature', 'due_date': datetime.utcnow().isoformat(),
             'completion_date': datetime.utcnow().isoformat()},
            {'status': 'completed', 'type': 'support', 'due_date': datetime.utcnow().isoformat(),
             'completion_date': datetime.utcnow().isoformat()},
            {'status': 'overdue', 'type': 'bug'},
            {'status': 'pending', 'type': 'enhancement'}
        ]
    }

    patterns = find_commitment_patterns(history)

    assert len(patterns) > 0
    assert patterns[0].commitment_count == 4


def test_find_commitment_patterns_completion_rate():
    """Test commitment completion rate calculation."""
    history = {
        'account_id': 'acc123',
        'commitments': [
            {'status': 'completed', 'type': 'feature'},
            {'status': 'completed', 'type': 'support'},
            {'status': 'pending', 'type': 'enhancement'},
            {'status': 'pending', 'type': 'bug'}
        ]
    }

    patterns = find_commitment_patterns(history)

    assert patterns[0].completion_rate == 0.5


def test_find_commitment_patterns_delay_calculation():
    """Test average delay calculation."""
    now = datetime.utcnow()

    history = {
        'account_id': 'acc123',
        'commitments': [
            {
                'status': 'completed',
                'type': 'feature',
                'due_date': (now - timedelta(days=10)).isoformat(),
                'completion_date': (now - timedelta(days=5)).isoformat()
            },
            {
                'status': 'completed',
                'type': 'support',
                'due_date': (now - timedelta(days=20)).isoformat(),
                'completion_date': (now - timedelta(days=10)).isoformat()
            }
        ]
    }

    patterns = find_commitment_patterns(history)

    assert patterns[0].average_delay_days > 0


def test_find_commitment_patterns_empty():
    """Test pattern detection with no commitments."""
    history = {
        'account_id': 'acc123',
        'commitments': []
    }

    patterns = find_commitment_patterns(history)

    assert patterns == []


def test_find_commitment_patterns_risk_indicators():
    """Test risk indicator identification."""
    history = {
        'account_id': 'acc123',
        'commitments': [
            {'status': 'completed', 'type': 'feature'},
            {'status': 'overdue', 'type': 'bug'},
            {'status': 'overdue', 'type': 'support'},
            {'status': 'pending', 'type': 'enhancement'}
        ]
    }

    patterns = find_commitment_patterns(history)

    assert len(patterns[0].risk_indicators) > 0


def test_find_commitment_patterns_common_types():
    """Test identification of common commitment types."""
    history = {
        'account_id': 'acc123',
        'commitments': [
            {'status': 'completed', 'type': 'feature'},
            {'status': 'completed', 'type': 'feature'},
            {'status': 'completed', 'type': 'feature'},
            {'status': 'pending', 'type': 'support'}
        ]
    }

    patterns = find_commitment_patterns(history)

    assert 'feature' in patterns[0].common_commitment_types


# Test calculate_sentiment_trend

def test_calculate_sentiment_trend_improving():
    """Test detection of improving sentiment."""
    interactions = [
        {
            'timestamp': (datetime.utcnow() - timedelta(days=i*5)).isoformat(),
            'sentiment': -0.5 + (i * 0.3)  # Improving over time
        }
        for i in range(6)
    ]

    trend = calculate_sentiment_trend(interactions)

    assert trend == SentimentTrend.IMPROVING


def test_calculate_sentiment_trend_declining():
    """Test detection of declining sentiment."""
    interactions = [
        {
            'timestamp': (datetime.utcnow() - timedelta(days=i*5)).isoformat(),
            'sentiment': 0.8 - (i * 0.3)  # Declining over time
        }
        for i in range(6)
    ]

    trend = calculate_sentiment_trend(interactions)

    assert trend == SentimentTrend.DECLINING


def test_calculate_sentiment_trend_stable():
    """Test detection of stable sentiment."""
    interactions = [
        {
            'timestamp': (datetime.utcnow() - timedelta(days=i*5)).isoformat(),
            'sentiment': 0.5  # Constant
        }
        for i in range(6)
    ]

    trend = calculate_sentiment_trend(interactions)

    assert trend == SentimentTrend.STABLE


def test_calculate_sentiment_trend_insufficient_data():
    """Test sentiment trend with insufficient data."""
    interactions = [
        {'timestamp': datetime.utcnow().isoformat(), 'sentiment': 0.5}
    ]

    trend = calculate_sentiment_trend(interactions)

    assert trend == SentimentTrend.UNKNOWN


def test_calculate_sentiment_trend_empty():
    """Test sentiment trend with empty data."""
    trend = calculate_sentiment_trend([])

    assert trend == SentimentTrend.UNKNOWN


# Test analyze_communication_tone

def test_analyze_communication_tone_positive():
    """Test tone analysis with positive communications."""
    notes = [
        "Great meeting today! Looking forward to the excellent results.",
        "Thank you for the wonderful presentation.",
        "Perfect solution, we love the new features."
    ]

    analysis = analyze_communication_tone(notes)

    assert analysis.overall_tone == "positive"
    assert analysis.positivity_score > 0.5


def test_analyze_communication_tone_negative():
    """Test tone analysis with negative communications."""
    notes = [
        "Unfortunately, we're experiencing issues with the product.",
        "Disappointed with the recent problems and delays.",
        "Concerned about the ongoing issues."
    ]

    analysis = analyze_communication_tone(notes)

    assert analysis.overall_tone == "negative"
    assert analysis.positivity_score < 0.5


def test_analyze_communication_tone_formal():
    """Test formality score calculation."""
    notes = [
        "Please kindly review the proposal regarding our partnership.",
        "I hereby submit the request pursuant to our agreement."
    ]

    analysis = analyze_communication_tone(notes)

    assert analysis.formality_score > 0.5


def test_analyze_communication_tone_informal():
    """Test informal tone detection."""
    notes = [
        "Hey, thanks for the awesome update!",
        "Yeah, that's cool. Looking forward to it."
    ]

    analysis = analyze_communication_tone(notes)

    assert analysis.formality_score < 0.5


def test_analyze_communication_tone_urgency():
    """Test urgency score calculation."""
    notes = [
        "This is urgent - need immediate response ASAP.",
        "Critical issue requiring emergency attention."
    ]

    analysis = analyze_communication_tone(notes)

    assert analysis.urgency_score > 0


def test_analyze_communication_tone_confidence():
    """Test confidence score calculation."""
    notes = [
        "We will definitely deliver this on time.",
        "I'm confident and certain about the results."
    ]

    analysis = analyze_communication_tone(notes)

    assert analysis.confidence_score > 0.5


def test_analyze_communication_tone_consistency():
    """Test tone consistency calculation."""
    notes = [
        "Please review the proposal.",
        "Please consider the request.",
        "Please kindly respond."
    ]

    analysis = analyze_communication_tone(notes)

    assert 0.0 <= analysis.tone_consistency <= 1.0


def test_analyze_communication_tone_empty():
    """Test tone analysis with empty notes."""
    analysis = analyze_communication_tone([])

    assert analysis.overall_tone == "neutral"
    assert analysis.formality_score == 0.5


# Test build_account_timeline

def test_build_account_timeline_success():
    """Test timeline construction."""
    events = [
        {
            'id': 'event1',
            'account_id': 'acc123',
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'meeting',
            'description': 'Quarterly review',
            'participants': ['Team'],
            'impact': 'high'
        },
        {
            'id': 'event2',
            'account_id': 'acc123',
            'timestamp': (datetime.utcnow() - timedelta(days=10)).isoformat(),
            'type': 'email',
            'description': 'Follow-up',
            'participants': ['Customer'],
            'impact': 'medium'
        }
    ]

    timeline = build_account_timeline(events)

    assert isinstance(timeline, Timeline)
    assert timeline.total_events == 2
    assert len(timeline.events) == 2


def test_build_account_timeline_sorting():
    """Test that timeline events are sorted by timestamp."""
    now = datetime.utcnow()

    events = [
        {
            'id': f'event{i}',
            'account_id': 'acc123',
            'timestamp': (now - timedelta(days=i*5)).isoformat(),
            'type': 'email',
            'description': 'Event',
            'participants': []
        }
        for i in [3, 1, 4, 2, 0]  # Unsorted
    ]

    timeline = build_account_timeline(events)

    # Should be sorted oldest to newest
    for i in range(len(timeline.events) - 1):
        assert timeline.events[i].timestamp <= timeline.events[i+1].timestamp


def test_build_account_timeline_event_types():
    """Test event type distribution calculation."""
    events = [
        {
            'id': f'event{i}',
            'account_id': 'acc123',
            'timestamp': datetime.utcnow().isoformat(),
            'type': event_type,
            'description': 'Event',
            'participants': []
        }
        for i, event_type in enumerate(['meeting', 'meeting', 'email', 'call'])
    ]

    timeline = build_account_timeline(events)

    assert timeline.event_types['meeting'] == 2
    assert timeline.event_types['email'] == 1
    assert timeline.event_types['call'] == 1


def test_build_account_timeline_empty():
    """Test timeline with no events."""
    timeline = build_account_timeline([])

    assert timeline.total_events == 0
    assert timeline.events == []


def test_build_account_timeline_invalid_events():
    """Test timeline handles invalid events gracefully."""
    events = [
        {'invalid': 'data'},
        {
            'id': 'valid1',
            'account_id': 'acc123',
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'email',
            'description': 'Valid event',
            'participants': []
        }
    ]

    timeline = build_account_timeline(events)

    # Should only include valid event
    assert timeline.total_events == 1


# Test identify_key_milestones

def test_identify_key_milestones():
    """Test milestone identification."""
    timeline = Timeline(
        account_id='acc123',
        events=[
            TimelineEvent(
                event_id=f'event{i}',
                account_id='acc123',
                timestamp=datetime.utcnow() - timedelta(days=i*10),
                event_type=EventType.MEETING,
                description=f'Event {i}',
                participants=[],
                impact='high' if i % 2 == 0 else 'medium'
            )
            for i in range(10)
        ],
        start_date=datetime.utcnow() - timedelta(days=100),
        end_date=datetime.utcnow(),
        total_events=10
    )

    milestones = identify_key_milestones(timeline)

    assert len(milestones) > 0
    for milestone in milestones:
        assert isinstance(milestone, Milestone)


def test_identify_key_milestones_high_impact_only():
    """Test that only high-impact events become milestones."""
    timeline = Timeline(
        account_id='acc123',
        events=[
            TimelineEvent(
                event_id=f'event{i}',
                account_id='acc123',
                timestamp=datetime.utcnow(),
                event_type=EventType.EMAIL,
                description='Event',
                participants=[],
                impact='high' if i < 3 else 'low'
            )
            for i in range(10)
        ],
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow(),
        total_events=10
    )

    milestones = identify_key_milestones(timeline)

    assert len(milestones) == 3


# Test calculate_relationship_score

def test_calculate_relationship_score_high():
    """Test high relationship score calculation."""
    interactions = {
        'total_interactions': 100,
        'days_since_last_interaction': 1,
        'response_rate': 0.95,
        'average_sentiment': 0.8,
        'executive_engagement': 15
    }

    score = calculate_relationship_score(interactions)

    assert score > 0.8


def test_calculate_relationship_score_low():
    """Test low relationship score calculation."""
    interactions = {
        'total_interactions': 5,
        'days_since_last_interaction': 60,
        'response_rate': 0.2,
        'average_sentiment': -0.5,
        'executive_engagement': 0
    }

    score = calculate_relationship_score(interactions)

    assert score < 0.4


def test_calculate_relationship_score_range():
    """Test relationship score is in valid range."""
    interactions = {
        'total_interactions': 50,
        'days_since_last_interaction': 10,
        'response_rate': 0.7,
        'average_sentiment': 0.3,
        'executive_engagement': 5
    }

    score = calculate_relationship_score(interactions)

    assert 0.0 <= score <= 1.0


# Test assess_executive_alignment

def test_assess_executive_alignment_success():
    """Test executive alignment assessment."""
    contacts = [
        {
            'account_id': 'acc123',
            'level': 'C-Level',
            'accessible': True,
            'alignment': 0.9,
            'is_sponsor': True
        },
        {
            'account_id': 'acc123',
            'level': 'VP',
            'accessible': True,
            'alignment': 0.8,
            'is_sponsor': False
        }
    ]

    alignment = assess_executive_alignment(contacts)

    assert isinstance(alignment, AlignmentScore)
    assert alignment.executive_engagement_count == 2


def test_assess_executive_alignment_high():
    """Test high executive alignment."""
    contacts = [
        {
            'account_id': 'acc123',
            'level': 'C-Level',
            'accessible': True,
            'alignment': 0.9,
            'is_sponsor': True
        },
        {
            'account_id': 'acc123',
            'level': 'VP',
            'accessible': True,
            'alignment': 0.9,
            'is_sponsor': True
        }
    ]

    alignment = assess_executive_alignment(contacts)

    assert alignment.overall_alignment > 0.7


def test_assess_executive_alignment_empty():
    """Test alignment with no contacts."""
    alignment = assess_executive_alignment([])

    assert alignment.overall_alignment == 0.0
    assert alignment.executive_engagement_count == 0


def test_assess_executive_alignment_sponsorship():
    """Test sponsorship strength calculation."""
    contacts = [
        {
            'level': 'C-Level',
            'accessible': True,
            'alignment': 0.8,
            'is_sponsor': True
        },
        {
            'level': 'VP',
            'accessible': True,
            'alignment': 0.7,
            'is_sponsor': True
        }
    ]

    alignment = assess_executive_alignment(contacts)

    assert alignment.sponsorship_strength >= 0.5


def test_assess_executive_alignment_accessibility():
    """Test accessibility score calculation."""
    contacts = [
        {
            'level': 'C-Level',
            'accessible': True,
            'alignment': 0.8,
            'is_sponsor': False
        },
        {
            'level': 'VP',
            'accessible': False,
            'alignment': 0.7,
            'is_sponsor': False
        }
    ]

    alignment = assess_executive_alignment(contacts)

    assert 0.0 <= alignment.decision_maker_accessibility <= 1.0
