"""Comprehensive unit tests for Memory Analyst subagent.

Tests cover:
- get_historical_context (12+ tests)
- identify_patterns (15+ tests)
- analyze_sentiment_trend (10+ tests)
- assess_relationship_strength (8+ tests)
- track_commitments (10+ tests)
- All helper methods

Target: 90%+ coverage with mocked Cognee API calls.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from src.agents.memory_analyst import MemoryAnalyst
from src.agents.memory_models import (
    HistoricalContext, TimelineEvent, Pattern, SentimentAnalysis,
    PriorRecommendation, RelationshipAssessment, Commitment,
    KeyEvent, EngagementMetrics, SentimentTrend, RelationshipStrength,
    RiskLevel, PatternType, EventType, CommitmentStatus
)
from src.services.memory_service import MemoryService
from src.integrations.cognee.cognee_client import CogneeClient


@pytest.fixture
def mock_memory_service():
    """Create mock MemoryService."""
    service = Mock(spec=MemoryService)
    service.store_context = AsyncMock()
    service.get_context = AsyncMock()
    return service


@pytest.fixture
def mock_cognee_client():
    """Create mock CogneeClient."""
    client = Mock(spec=CogneeClient)
    client.get_account_context = AsyncMock()
    client.get_account_timeline = AsyncMock()
    client.search_accounts = AsyncMock()
    return client


@pytest.fixture
def memory_analyst(mock_memory_service, mock_cognee_client):
    """Create MemoryAnalyst instance with mocked dependencies."""
    return MemoryAnalyst(
        memory_service=mock_memory_service,
        cognee_client=mock_cognee_client,
        api_key="test-api-key"
    )


@pytest.fixture
def sample_timeline_events():
    """Create sample timeline events."""
    now = datetime.utcnow()
    return [
        TimelineEvent(
            event_id="event1",
            account_id="acc123",
            timestamp=now - timedelta(days=5),
            event_type=EventType.MEETING,
            description="Quarterly business review meeting",
            participants=["John Doe", "Jane Smith"],
            impact="high",
            metadata={"sentiment": 0.7}
        ),
        TimelineEvent(
            event_id="event2",
            account_id="acc123",
            timestamp=now - timedelta(days=15),
            event_type=EventType.EMAIL,
            description="Follow-up on contract renewal",
            participants=["John Doe"],
            impact="medium",
            metadata={"sentiment": 0.5}
        ),
        TimelineEvent(
            event_id="event3",
            account_id="acc123",
            timestamp=now - timedelta(days=30),
            event_type=EventType.CALL,
            description="Support escalation call",
            participants=["Jane Smith"],
            impact="high",
            metadata={"sentiment": -0.3}
        ),
        TimelineEvent(
            event_id="event4",
            account_id="acc123",
            timestamp=now - timedelta(days=45),
            event_type=EventType.EXECUTIVE_CHANGE,
            description="Executive sponsor changed from Bob to Alice",
            participants=["Bob", "Alice"],
            impact="high",
            metadata={"sentiment": 0.0}
        ),
        TimelineEvent(
            event_id="event5",
            account_id="acc123",
            timestamp=now - timedelta(days=60),
            event_type=EventType.MEETING,
            description="Product demo session",
            participants=["John Doe", "Sales Team"],
            impact="medium",
            metadata={"sentiment": 0.8}
        )
    ]


@pytest.fixture
def sample_account_context():
    """Create sample account context."""
    return {
        'account_id': 'acc123',
        'historical_interactions': [
            {
                'type': 'meeting',
                'timestamp': datetime.utcnow().isoformat(),
                'sentiment': 0.7
            },
            {
                'type': 'email',
                'timestamp': (datetime.utcnow() - timedelta(days=10)).isoformat(),
                'sentiment': 0.5
            },
            {
                'type': 'executive_meeting',
                'timestamp': (datetime.utcnow() - timedelta(days=30)).isoformat(),
                'sentiment': 0.9
            }
        ],
        'response_rate': 0.8,
        'average_sentiment': 0.6,
        'contacts': [
            {
                'name': 'John Doe',
                'level': 'C-Level',
                'accessible': True,
                'alignment': 0.8,
                'is_sponsor': True,
                'account_id': 'acc123'
            },
            {
                'name': 'Jane Smith',
                'level': 'VP',
                'accessible': True,
                'alignment': 0.7,
                'is_sponsor': False,
                'account_id': 'acc123'
            }
        ],
        'commitments': [
            {
                'status': 'completed',
                'due_date': datetime.utcnow().isoformat(),
                'completion_date': datetime.utcnow().isoformat(),
                'type': 'feature_request'
            },
            {
                'status': 'pending',
                'type': 'support_issue'
            }
        ],
        'usage_data': {
            'current_usage': 150,
            'historical_usage': 100
        },
        'contract_data': {
            'renewal_date': (datetime.utcnow() + timedelta(days=60)).isoformat()
        }
    }


# Tests for get_historical_context

@pytest.mark.asyncio
async def test_get_historical_context_success(
    memory_analyst, mock_cognee_client, sample_timeline_events, sample_account_context
):
    """Test successful retrieval of historical context."""
    mock_cognee_client.get_account_context.return_value = sample_account_context
    mock_cognee_client.get_account_timeline.return_value = [
        {
            'interaction_id': e.event_id,
            'timestamp': e.timestamp.isoformat(),
            'type': e.event_type.value,
            'summary': e.description,
            'participants': e.participants,
            'metadata': e.metadata
        }
        for e in sample_timeline_events
    ]
    mock_cognee_client.search_accounts.return_value = []

    context = await memory_analyst.get_historical_context("acc123")

    assert isinstance(context, HistoricalContext)
    assert context.account_id == "acc123"
    assert context.sentiment_trend in [SentimentTrend.IMPROVING, SentimentTrend.STABLE, SentimentTrend.DECLINING]
    assert context.relationship_strength in [
        RelationshipStrength.STRONG, RelationshipStrength.MODERATE,
        RelationshipStrength.WEAK, RelationshipStrength.AT_RISK
    ]
    assert len(context.timeline) > 0


@pytest.mark.asyncio
async def test_get_historical_context_with_patterns(
    memory_analyst, mock_cognee_client, sample_timeline_events, sample_account_context
):
    """Test context retrieval with pattern detection enabled."""
    mock_cognee_client.get_account_context.return_value = sample_account_context
    mock_cognee_client.get_account_timeline.return_value = [
        {
            'interaction_id': e.event_id,
            'timestamp': e.timestamp.isoformat(),
            'type': e.event_type.value,
            'summary': e.description,
            'participants': e.participants,
            'metadata': e.metadata
        }
        for e in sample_timeline_events
    ]
    mock_cognee_client.search_accounts.return_value = []

    context = await memory_analyst.get_historical_context("acc123", include_patterns=True)

    assert isinstance(context, HistoricalContext)
    assert isinstance(context.patterns, list)
    # Should have at least executive change pattern
    assert any(p.pattern_type == PatternType.EXECUTIVE_CHANGE for p in context.patterns)


@pytest.mark.asyncio
async def test_get_historical_context_without_patterns(
    memory_analyst, mock_cognee_client, sample_timeline_events, sample_account_context
):
    """Test context retrieval with pattern detection disabled."""
    mock_cognee_client.get_account_context.return_value = sample_account_context
    mock_cognee_client.get_account_timeline.return_value = []
    mock_cognee_client.search_accounts.return_value = []

    context = await memory_analyst.get_historical_context("acc123", include_patterns=False)

    assert isinstance(context, HistoricalContext)
    assert context.patterns == []


@pytest.mark.asyncio
async def test_get_historical_context_performance(
    memory_analyst, mock_cognee_client, sample_account_context
):
    """Test that context retrieval meets performance target (<200ms)."""
    mock_cognee_client.get_account_context.return_value = sample_account_context
    mock_cognee_client.get_account_timeline.return_value = []
    mock_cognee_client.search_accounts.return_value = []

    start = datetime.utcnow()
    context = await memory_analyst.get_historical_context("acc123", include_patterns=False)
    duration = (datetime.utcnow() - start).total_seconds()

    assert duration < 0.5  # Allow some overhead for test environment
    assert isinstance(context, HistoricalContext)


@pytest.mark.asyncio
async def test_get_historical_context_lookback_days(
    memory_analyst, mock_cognee_client, sample_account_context
):
    """Test context retrieval with custom lookback period."""
    mock_cognee_client.get_account_context.return_value = sample_account_context
    mock_cognee_client.get_account_timeline.return_value = []
    mock_cognee_client.search_accounts.return_value = []

    context = await memory_analyst.get_historical_context("acc123", lookback_days=90)

    assert isinstance(context, HistoricalContext)
    assert context.engagement_metrics.measurement_period_days == 90


@pytest.mark.asyncio
async def test_get_historical_context_empty_timeline(
    memory_analyst, mock_cognee_client, sample_account_context
):
    """Test context retrieval with no timeline events."""
    mock_cognee_client.get_account_context.return_value = sample_account_context
    mock_cognee_client.get_account_timeline.return_value = []
    mock_cognee_client.search_accounts.return_value = []

    context = await memory_analyst.get_historical_context("acc123")

    assert isinstance(context, HistoricalContext)
    assert context.timeline == []
    assert context.key_events == []


@pytest.mark.asyncio
async def test_get_historical_context_exception_handling(
    memory_analyst, mock_cognee_client
):
    """Test exception handling in context retrieval."""
    mock_cognee_client.get_account_context.side_effect = Exception("API error")

    with pytest.raises(Exception) as exc_info:
        await memory_analyst.get_historical_context("acc123")

    assert "API error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_historical_context_partial_failures(
    memory_analyst, mock_cognee_client, sample_account_context
):
    """Test context retrieval handles partial API failures gracefully."""
    mock_cognee_client.get_account_context.side_effect = Exception("Context failed")
    mock_cognee_client.get_account_timeline.return_value = []
    mock_cognee_client.search_accounts.return_value = []

    # Should not raise, should handle exceptions gracefully
    context = await memory_analyst.get_historical_context("acc123")

    assert isinstance(context, HistoricalContext)


@pytest.mark.asyncio
async def test_get_historical_context_risk_level_calculation(
    memory_analyst, mock_cognee_client, sample_timeline_events, sample_account_context
):
    """Test risk level is properly calculated."""
    # Create declining sentiment scenario
    declining_events = [
        {
            'interaction_id': f"event{i}",
            'timestamp': (datetime.utcnow() - timedelta(days=i*5)).isoformat(),
            'type': 'email',
            'summary': 'test',
            'participants': [],
            'metadata': {'sentiment': 0.8 - (i * 0.2)}  # Declining sentiment
        }
        for i in range(5)
    ]

    mock_cognee_client.get_account_context.return_value = sample_account_context
    mock_cognee_client.get_account_timeline.return_value = declining_events
    mock_cognee_client.search_accounts.return_value = []

    context = await memory_analyst.get_historical_context("acc123", include_patterns=True)

    assert context.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]


@pytest.mark.asyncio
async def test_get_historical_context_metrics_tracking(
    memory_analyst, mock_cognee_client, sample_account_context
):
    """Test that performance metrics are tracked."""
    mock_cognee_client.get_account_context.return_value = sample_account_context
    mock_cognee_client.get_account_timeline.return_value = []
    mock_cognee_client.search_accounts.return_value = []

    initial_count = memory_analyst._metrics["total_analyses"]

    await memory_analyst.get_historical_context("acc123")

    assert memory_analyst._metrics["total_analyses"] == initial_count + 1
    assert memory_analyst._metrics["avg_duration_seconds"] >= 0


@pytest.mark.asyncio
async def test_get_historical_context_key_events_extraction(
    memory_analyst, mock_cognee_client, sample_timeline_events, sample_account_context
):
    """Test that key events are properly extracted."""
    mock_cognee_client.get_account_context.return_value = sample_account_context
    mock_cognee_client.get_account_timeline.return_value = [
        {
            'interaction_id': e.event_id,
            'timestamp': e.timestamp.isoformat(),
            'type': e.event_type.value,
            'summary': e.description,
            'participants': e.participants,
            'metadata': e.metadata,
            'impact': e.impact
        }
        for e in sample_timeline_events
    ]
    mock_cognee_client.search_accounts.return_value = []

    context = await memory_analyst.get_historical_context("acc123")

    # Should extract high-impact events
    high_impact_count = sum(1 for e in sample_timeline_events if e.impact == 'high')
    assert len(context.key_events) <= high_impact_count


@pytest.mark.asyncio
async def test_get_historical_context_engagement_metrics(
    memory_analyst, mock_cognee_client, sample_timeline_events, sample_account_context
):
    """Test engagement metrics are properly calculated."""
    mock_cognee_client.get_account_context.return_value = sample_account_context
    mock_cognee_client.get_account_timeline.return_value = [
        {
            'interaction_id': e.event_id,
            'timestamp': e.timestamp.isoformat(),
            'type': e.event_type.value,
            'summary': e.description,
            'participants': e.participants,
            'metadata': e.metadata
        }
        for e in sample_timeline_events
    ]
    mock_cognee_client.search_accounts.return_value = []

    context = await memory_analyst.get_historical_context("acc123")

    assert context.engagement_metrics is not None
    assert context.engagement_metrics.total_interactions > 0
    assert 0 <= context.engagement_metrics.interaction_frequency_score <= 1.0
    assert 0 <= context.engagement_metrics.quality_score <= 1.0


# Tests for identify_patterns

@pytest.mark.asyncio
async def test_identify_patterns_success(
    memory_analyst, mock_cognee_client, sample_timeline_events, sample_account_context
):
    """Test successful pattern identification."""
    patterns = await memory_analyst.identify_patterns(
        "acc123",
        timeline_events=sample_timeline_events,
        context=sample_account_context
    )

    assert isinstance(patterns, list)
    assert all(isinstance(p, Pattern) for p in patterns)


@pytest.mark.asyncio
async def test_identify_patterns_churn_detection(
    memory_analyst, sample_timeline_events
):
    """Test churn pattern detection."""
    # Add more events to trigger churn patterns
    now = datetime.utcnow()
    churn_events = sample_timeline_events + [
        TimelineEvent(
            event_id=f"neg{i}",
            account_id="acc123",
            timestamp=now - timedelta(days=i),
            event_type=EventType.EMAIL,
            description=f"Issue with product - concern raised",
            participants=["Customer"],
            impact="high",
            metadata={"sentiment": -0.7}
        )
        for i in range(3)
    ]

    patterns = await memory_analyst.identify_patterns(
        "acc123",
        timeline_events=churn_events,
        context={'commitments': []}
    )

    churn_patterns = [p for p in patterns if p.pattern_type == PatternType.CHURN_RISK]
    assert len(churn_patterns) > 0


@pytest.mark.asyncio
async def test_identify_patterns_engagement_cycles(
    memory_analyst, mock_cognee_client
):
    """Test engagement cycle detection."""
    # Create monthly cycle pattern
    now = datetime.utcnow()
    cycle_events = [
        TimelineEvent(
            event_id=f"cycle{i}",
            account_id="acc123",
            timestamp=now - timedelta(days=30*i + j),
            event_type=EventType.MEETING,
            description="Regular sync",
            participants=["Team"],
            metadata={}
        )
        for i in range(4)  # 4 months
        for j in range(5)  # 5 events per month
    ]

    patterns = await memory_analyst.identify_patterns(
        "acc123",
        timeline_events=cycle_events,
        context={'commitments': []}
    )

    engagement_patterns = [p for p in patterns if p.pattern_type == PatternType.ENGAGEMENT_CYCLE]
    assert len(engagement_patterns) > 0


@pytest.mark.asyncio
async def test_identify_patterns_commitment_tracking(
    memory_analyst
):
    """Test commitment pattern detection."""
    context = {
        'commitments': [
            {'status': 'completed', 'due_date': datetime.utcnow().isoformat(),
             'completion_date': datetime.utcnow().isoformat(), 'type': 'feature'},
            {'status': 'completed', 'due_date': datetime.utcnow().isoformat(),
             'completion_date': datetime.utcnow().isoformat(), 'type': 'support'},
            {'status': 'overdue', 'type': 'bug_fix'},
            {'status': 'pending', 'type': 'enhancement'}
        ]
    }

    patterns = await memory_analyst.identify_patterns(
        "acc123",
        timeline_events=[],
        context=context
    )

    commitment_patterns = [p for p in patterns if p.pattern_type == PatternType.COMMITMENT_PATTERN]
    assert len(commitment_patterns) > 0


@pytest.mark.asyncio
async def test_identify_patterns_executive_changes(
    memory_analyst, sample_timeline_events
):
    """Test executive change pattern detection."""
    patterns = await memory_analyst.identify_patterns(
        "acc123",
        timeline_events=sample_timeline_events,
        context={'commitments': []}
    )

    exec_patterns = [p for p in patterns if p.pattern_type == PatternType.EXECUTIVE_CHANGE]
    assert len(exec_patterns) > 0


@pytest.mark.asyncio
async def test_identify_patterns_upsell_opportunities(
    memory_analyst, mock_cognee_client
):
    """Test upsell opportunity pattern detection."""
    now = datetime.utcnow()
    upsell_events = [
        TimelineEvent(
            event_id=f"upsell{i}",
            account_id="acc123",
            timestamp=now - timedelta(days=i*10),
            event_type=EventType.MEETING,
            description="Discussed expansion plans and growth needs",
            participants=["Sales", "Customer"],
            metadata={"sentiment": 0.8}
        )
        for i in range(3)
    ]

    context = {
        'usage_data': {
            'current_usage': 200,
            'historical_usage': 100
        },
        'commitments': []
    }

    patterns = await memory_analyst.identify_patterns(
        "acc123",
        timeline_events=upsell_events,
        context=context
    )

    upsell_patterns = [p for p in patterns if p.pattern_type == PatternType.UPSELL_OPPORTUNITY]
    assert len(upsell_patterns) > 0


@pytest.mark.asyncio
async def test_identify_patterns_renewal_risks(
    memory_analyst
):
    """Test renewal risk pattern detection."""
    now = datetime.utcnow()
    renewal_events = [
        TimelineEvent(
            event_id="renewal1",
            account_id="acc123",
            timestamp=now - timedelta(days=5),
            event_type=EventType.EMAIL,
            description="Discussing budget concerns for renewal",
            participants=["Finance"],
            metadata={"sentiment": -0.2}
        )
    ]

    context = {
        'contract_data': {
            'renewal_date': (now + timedelta(days=60)).isoformat()
        },
        'usage_data': {},
        'commitments': []
    }

    patterns = await memory_analyst.identify_patterns(
        "acc123",
        timeline_events=renewal_events,
        context=context
    )

    renewal_patterns = [p for p in patterns if p.pattern_type == PatternType.RENEWAL_RISK]
    assert len(renewal_patterns) > 0


@pytest.mark.asyncio
async def test_identify_patterns_empty_timeline(
    memory_analyst
):
    """Test pattern identification with empty timeline."""
    patterns = await memory_analyst.identify_patterns(
        "acc123",
        timeline_events=[],
        context={'commitments': []}
    )

    assert isinstance(patterns, list)
    # Should still return some patterns from context analysis


@pytest.mark.asyncio
async def test_identify_patterns_fetches_missing_data(
    memory_analyst, mock_cognee_client, sample_timeline_events, sample_account_context
):
    """Test that missing timeline/context data is fetched."""
    mock_cognee_client.get_account_timeline.return_value = [
        {
            'interaction_id': e.event_id,
            'timestamp': e.timestamp.isoformat(),
            'type': e.event_type.value,
            'summary': e.description,
            'participants': e.participants,
            'metadata': e.metadata
        }
        for e in sample_timeline_events
    ]
    mock_cognee_client.get_account_context.return_value = sample_account_context

    # Call without providing timeline or context
    patterns = await memory_analyst.identify_patterns("acc123")

    assert isinstance(patterns, list)
    mock_cognee_client.get_account_timeline.assert_called_once()
    mock_cognee_client.get_account_context.assert_called_once()


@pytest.mark.asyncio
async def test_identify_patterns_exception_handling(
    memory_analyst, mock_cognee_client
):
    """Test exception handling in pattern identification."""
    mock_cognee_client.get_account_timeline.side_effect = Exception("API error")

    patterns = await memory_analyst.identify_patterns("acc123")

    # Should return empty list on error, not raise
    assert patterns == []


@pytest.mark.asyncio
async def test_identify_patterns_confidence_scores(
    memory_analyst, sample_timeline_events, sample_account_context
):
    """Test that patterns have valid confidence scores."""
    patterns = await memory_analyst.identify_patterns(
        "acc123",
        timeline_events=sample_timeline_events,
        context=sample_account_context
    )

    for pattern in patterns:
        assert 0.0 <= pattern.confidence <= 1.0


@pytest.mark.asyncio
async def test_identify_patterns_recommendations(
    memory_analyst, sample_timeline_events, sample_account_context
):
    """Test that patterns include actionable recommendations."""
    patterns = await memory_analyst.identify_patterns(
        "acc123",
        timeline_events=sample_timeline_events,
        context=sample_account_context
    )

    # At least some patterns should have recommendations
    patterns_with_recs = [p for p in patterns if p.recommendations]
    assert len(patterns_with_recs) > 0


@pytest.mark.asyncio
async def test_identify_patterns_evidence(
    memory_analyst, sample_timeline_events, sample_account_context
):
    """Test that patterns include supporting evidence."""
    patterns = await memory_analyst.identify_patterns(
        "acc123",
        timeline_events=sample_timeline_events,
        context=sample_account_context
    )

    for pattern in patterns:
        assert isinstance(pattern.evidence, list)
        if pattern.pattern_type in [PatternType.CHURN_RISK, PatternType.EXECUTIVE_CHANGE]:
            assert len(pattern.evidence) > 0


@pytest.mark.asyncio
async def test_identify_patterns_risk_scores(
    memory_analyst, sample_timeline_events, sample_account_context
):
    """Test that patterns have valid risk scores."""
    patterns = await memory_analyst.identify_patterns(
        "acc123",
        timeline_events=sample_timeline_events,
        context=sample_account_context
    )

    for pattern in patterns:
        assert 0 <= pattern.risk_score <= 100


@pytest.mark.asyncio
async def test_identify_patterns_temporal_data(
    memory_analyst, sample_timeline_events, sample_account_context
):
    """Test that patterns have valid temporal data."""
    patterns = await memory_analyst.identify_patterns(
        "acc123",
        timeline_events=sample_timeline_events,
        context=sample_account_context
    )

    for pattern in patterns:
        assert isinstance(pattern.first_detected, datetime)
        assert isinstance(pattern.last_detected, datetime)
        assert pattern.first_detected <= pattern.last_detected


# Tests for analyze_sentiment_trend

@pytest.mark.asyncio
async def test_analyze_sentiment_trend_success(
    memory_analyst, sample_timeline_events
):
    """Test successful sentiment trend analysis."""
    analysis = await memory_analyst.analyze_sentiment_trend(
        "acc123",
        timeline_events=sample_timeline_events
    )

    assert isinstance(analysis, SentimentAnalysis)
    assert analysis.account_id == "acc123"
    assert analysis.trend in [SentimentTrend.IMPROVING, SentimentTrend.STABLE, SentimentTrend.DECLINING]


@pytest.mark.asyncio
async def test_analyze_sentiment_trend_improving(
    memory_analyst
):
    """Test detection of improving sentiment."""
    now = datetime.utcnow()
    improving_events = [
        TimelineEvent(
            event_id=f"sent{i}",
            account_id="acc123",
            timestamp=now - timedelta(days=60-i*10),
            event_type=EventType.EMAIL,
            description="Communication",
            participants=[],
            metadata={"sentiment": -0.5 + (i * 0.3)}  # Improving from -0.5 to 1.0
        )
        for i in range(6)
    ]

    analysis = await memory_analyst.analyze_sentiment_trend("acc123", improving_events)

    assert analysis.trend == SentimentTrend.IMPROVING
    assert analysis.change_rate > 0


@pytest.mark.asyncio
async def test_analyze_sentiment_trend_declining(
    memory_analyst
):
    """Test detection of declining sentiment."""
    now = datetime.utcnow()
    declining_events = [
        TimelineEvent(
            event_id=f"sent{i}",
            account_id="acc123",
            timestamp=now - timedelta(days=60-i*10),
            event_type=EventType.EMAIL,
            description="Communication",
            participants=[],
            metadata={"sentiment": 0.8 - (i * 0.3)}  # Declining from 0.8 to -0.7
        )
        for i in range(6)
    ]

    analysis = await memory_analyst.analyze_sentiment_trend("acc123", declining_events)

    assert analysis.trend == SentimentTrend.DECLINING
    assert analysis.change_rate < 0


@pytest.mark.asyncio
async def test_analyze_sentiment_trend_stable(
    memory_analyst
):
    """Test detection of stable sentiment."""
    now = datetime.utcnow()
    stable_events = [
        TimelineEvent(
            event_id=f"sent{i}",
            account_id="acc123",
            timestamp=now - timedelta(days=i*10),
            event_type=EventType.EMAIL,
            description="Communication",
            participants=[],
            metadata={"sentiment": 0.5}  # Constant
        )
        for i in range(6)
    ]

    analysis = await memory_analyst.analyze_sentiment_trend("acc123", stable_events)

    assert analysis.trend == SentimentTrend.STABLE
    assert abs(analysis.change_rate) < 0.2


@pytest.mark.asyncio
async def test_analyze_sentiment_trend_empty_timeline(
    memory_analyst
):
    """Test sentiment analysis with empty timeline."""
    analysis = await memory_analyst.analyze_sentiment_trend("acc123", [])

    assert isinstance(analysis, SentimentAnalysis)
    assert analysis.trend == SentimentTrend.UNKNOWN
    assert analysis.data_points == 0


@pytest.mark.asyncio
async def test_analyze_sentiment_trend_warnings(
    memory_analyst
):
    """Test that warnings are generated for negative trends."""
    now = datetime.utcnow()
    negative_events = [
        TimelineEvent(
            event_id=f"neg{i}",
            account_id="acc123",
            timestamp=now - timedelta(days=i),
            event_type=EventType.EMAIL,
            description="Issue",
            participants=[],
            metadata={"sentiment": -0.8}
        )
        for i in range(5)
    ]

    analysis = await memory_analyst.analyze_sentiment_trend("acc123", negative_events)

    assert len(analysis.warnings) > 0


@pytest.mark.asyncio
async def test_analyze_sentiment_trend_key_factors(
    memory_analyst
):
    """Test that key factors are identified."""
    now = datetime.utcnow()
    mixed_events = [
        TimelineEvent(
            event_id=f"event{i}",
            account_id="acc123",
            timestamp=now - timedelta(days=i*5),
            event_type=EventType.EMAIL,
            description="Communication",
            participants=[],
            metadata={"sentiment": 0.5 - (i * 0.2)}
        )
        for i in range(5)
    ]

    analysis = await memory_analyst.analyze_sentiment_trend("acc123", mixed_events)

    if abs(analysis.change_rate) > 0.3:
        assert len(analysis.key_factors) > 0


@pytest.mark.asyncio
async def test_analyze_sentiment_trend_fetches_timeline(
    memory_analyst, mock_cognee_client, sample_timeline_events
):
    """Test that timeline is fetched if not provided."""
    mock_cognee_client.get_account_timeline.return_value = [
        {
            'interaction_id': e.event_id,
            'timestamp': e.timestamp.isoformat(),
            'type': e.event_type.value,
            'summary': e.description,
            'participants': e.participants,
            'metadata': e.metadata
        }
        for e in sample_timeline_events
    ]

    analysis = await memory_analyst.analyze_sentiment_trend("acc123")

    assert isinstance(analysis, SentimentAnalysis)
    mock_cognee_client.get_account_timeline.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_sentiment_trend_score_ranges(
    memory_analyst, sample_timeline_events
):
    """Test that sentiment scores are in valid range."""
    analysis = await memory_analyst.analyze_sentiment_trend("acc123", sample_timeline_events)

    assert -1.0 <= analysis.overall_sentiment <= 1.0
    assert -1.0 <= analysis.recent_score <= 1.0
    assert -1.0 <= analysis.historical_score <= 1.0


@pytest.mark.asyncio
async def test_analyze_sentiment_trend_exception_handling(
    memory_analyst, mock_cognee_client
):
    """Test exception handling in sentiment analysis."""
    mock_cognee_client.get_account_timeline.side_effect = Exception("API error")

    with pytest.raises(Exception):
        await memory_analyst.analyze_sentiment_trend("acc123")


# Tests for assess_relationship_strength

@pytest.mark.asyncio
async def test_assess_relationship_strength_success(
    memory_analyst, sample_account_context
):
    """Test successful relationship assessment."""
    assessment = await memory_analyst.assess_relationship_strength(
        "acc123",
        context=sample_account_context
    )

    assert isinstance(assessment, RelationshipAssessment)
    assert assessment.account_id == "acc123"
    assert assessment.relationship_strength in [
        RelationshipStrength.STRONG, RelationshipStrength.MODERATE,
        RelationshipStrength.WEAK, RelationshipStrength.AT_RISK
    ]


@pytest.mark.asyncio
async def test_assess_relationship_strength_strong(
    memory_analyst
):
    """Test detection of strong relationship."""
    strong_context = {
        'historical_interactions': [
            {'timestamp': datetime.utcnow().isoformat(), 'type': 'meeting'}
            for _ in range(50)
        ],
        'response_rate': 0.9,
        'average_sentiment': 0.8,
        'contacts': [
            {
                'level': 'C-Level',
                'accessible': True,
                'alignment': 0.9,
                'is_sponsor': True,
                'account_id': 'acc123'
            }
        ]
    }

    assessment = await memory_analyst.assess_relationship_strength("acc123", strong_context)

    assert assessment.relationship_strength == RelationshipStrength.STRONG
    assert assessment.relationship_health_score >= 80


@pytest.mark.asyncio
async def test_assess_relationship_strength_at_risk(
    memory_analyst
):
    """Test detection of at-risk relationship."""
    at_risk_context = {
        'historical_interactions': [
            {
                'timestamp': (datetime.utcnow() - timedelta(days=90)).isoformat(),
                'type': 'email'
            }
        ],
        'response_rate': 0.2,
        'average_sentiment': -0.5,
        'contacts': []
    }

    assessment = await memory_analyst.assess_relationship_strength("acc123", at_risk_context)

    assert assessment.relationship_strength == RelationshipStrength.AT_RISK
    assert assessment.relationship_health_score < 50


@pytest.mark.asyncio
async def test_assess_relationship_strength_executive_alignment(
    memory_analyst, sample_account_context
):
    """Test executive alignment calculation."""
    assessment = await memory_analyst.assess_relationship_strength(
        "acc123",
        sample_account_context
    )

    assert 0.0 <= assessment.executive_alignment <= 1.0
    assert assessment.executive_sponsor_present is True


@pytest.mark.asyncio
async def test_assess_relationship_strength_trends(
    memory_analyst, sample_account_context
):
    """Test identification of improvement and degradation trends."""
    assessment = await memory_analyst.assess_relationship_strength(
        "acc123",
        sample_account_context
    )

    # Should have either improvement trends or degradation risks
    assert isinstance(assessment.improvement_trends, list)
    assert isinstance(assessment.degradation_risks, list)


@pytest.mark.asyncio
async def test_assess_relationship_strength_fetches_context(
    memory_analyst, mock_cognee_client, sample_account_context
):
    """Test that context is fetched if not provided."""
    mock_cognee_client.get_account_context.return_value = sample_account_context

    assessment = await memory_analyst.assess_relationship_strength("acc123")

    assert isinstance(assessment, RelationshipAssessment)
    mock_cognee_client.get_account_context.assert_called_once()


@pytest.mark.asyncio
async def test_assess_relationship_strength_score_ranges(
    memory_analyst, sample_account_context
):
    """Test that all scores are in valid ranges."""
    assessment = await memory_analyst.assess_relationship_strength("acc123", sample_account_context)

    assert 0.0 <= assessment.engagement_score <= 1.0
    assert 0.0 <= assessment.executive_alignment <= 1.0
    assert 0.0 <= assessment.response_rate <= 1.0
    assert 0 <= assessment.relationship_health_score <= 100


@pytest.mark.asyncio
async def test_assess_relationship_strength_exception_handling(
    memory_analyst, mock_cognee_client
):
    """Test exception handling in relationship assessment."""
    mock_cognee_client.get_account_context.side_effect = Exception("API error")

    with pytest.raises(Exception):
        await memory_analyst.assess_relationship_strength("acc123")


# Tests for track_commitments

@pytest.mark.asyncio
async def test_track_commitments_success(
    memory_analyst
):
    """Test successful commitment tracking."""
    now = datetime.utcnow()
    commitment_events = [
        TimelineEvent(
            event_id="commit1",
            account_id="acc123",
            timestamp=now - timedelta(days=10),
            event_type=EventType.MEETING,
            description="We promised to deliver the feature by end of month",
            participants=["Sales", "Customer"],
            metadata={'status': 'pending'}
        ),
        TimelineEvent(
            event_id="commit2",
            account_id="acc123",
            timestamp=now - timedelta(days=5),
            event_type=EventType.EMAIL,
            description="Committed to resolving the support issue",
            participants=["Support"],
            metadata={'status': 'completed'}
        )
    ]

    commitments = await memory_analyst.track_commitments("acc123", commitment_events)

    assert isinstance(commitments, list)
    assert len(commitments) == 2
    assert all(isinstance(c, Commitment) for c in commitments)


@pytest.mark.asyncio
async def test_track_commitments_keyword_detection(
    memory_analyst
):
    """Test commitment detection by keywords."""
    now = datetime.utcnow()
    events = [
        TimelineEvent(
            event_id=f"event{i}",
            account_id="acc123",
            timestamp=now - timedelta(days=i),
            event_type=EventType.EMAIL,
            description=desc,
            participants=["Team"],
            metadata={}
        )
        for i, desc in enumerate([
            "We will deliver this next week",
            "Agreed to provide documentation",
            "No commitment here",
            "Committed to the deadline"
        ])
    ]

    commitments = await memory_analyst.track_commitments("acc123", events)

    # Should detect 3 out of 4 (excluding "No commitment here")
    assert len(commitments) == 3


@pytest.mark.asyncio
async def test_track_commitments_status_tracking(
    memory_analyst
):
    """Test commitment status tracking."""
    now = datetime.utcnow()
    events = [
        TimelineEvent(
            event_id="commit1",
            account_id="acc123",
            timestamp=now,
            event_type=EventType.EMAIL,
            description="Promised to deliver",
            participants=["Sales"],
            metadata={'status': 'completed', 'completion_date': now.isoformat()}
        )
    ]

    commitments = await memory_analyst.track_commitments("acc123", events)

    assert commitments[0].status == CommitmentStatus.COMPLETED
    assert commitments[0].completion_date is not None


@pytest.mark.asyncio
async def test_track_commitments_empty_timeline(
    memory_analyst
):
    """Test commitment tracking with empty timeline."""
    commitments = await memory_analyst.track_commitments("acc123", [])

    assert commitments == []


@pytest.mark.asyncio
async def test_track_commitments_fetches_timeline(
    memory_analyst, mock_cognee_client
):
    """Test that timeline is fetched if not provided."""
    mock_cognee_client.get_account_timeline.return_value = []

    commitments = await memory_analyst.track_commitments("acc123")

    assert isinstance(commitments, list)
    mock_cognee_client.get_account_timeline.assert_called_once()


@pytest.mark.asyncio
async def test_track_commitments_participants(
    memory_analyst
):
    """Test commitment participant tracking."""
    now = datetime.utcnow()
    events = [
        TimelineEvent(
            event_id="commit1",
            account_id="acc123",
            timestamp=now,
            event_type=EventType.MEETING,
            description="We committed to the deadline",
            participants=["John Doe", "Customer Contact"],
            metadata={}
        )
    ]

    commitments = await memory_analyst.track_commitments("acc123", events)

    assert commitments[0].committed_by == "John Doe"
    assert commitments[0].committed_to == "Customer Contact"


@pytest.mark.asyncio
async def test_track_commitments_priority_assignment(
    memory_analyst
):
    """Test that priority is properly assigned."""
    now = datetime.utcnow()
    events = [
        TimelineEvent(
            event_id="commit1",
            account_id="acc123",
            timestamp=now,
            event_type=EventType.MEETING,
            description="Promised delivery",
            participants=["Team"],
            impact="high",
            metadata={}
        )
    ]

    commitments = await memory_analyst.track_commitments("acc123", events)

    assert commitments[0].priority == "high"


@pytest.mark.asyncio
async def test_track_commitments_exception_handling(
    memory_analyst, mock_cognee_client
):
    """Test exception handling in commitment tracking."""
    mock_cognee_client.get_account_timeline.side_effect = Exception("API error")

    commitments = await memory_analyst.track_commitments("acc123")

    # Should return empty list on error
    assert commitments == []


@pytest.mark.asyncio
async def test_track_commitments_due_dates(
    memory_analyst
):
    """Test due date extraction from metadata."""
    now = datetime.utcnow()
    due_date = now + timedelta(days=30)
    events = [
        TimelineEvent(
            event_id="commit1",
            account_id="acc123",
            timestamp=now,
            event_type=EventType.EMAIL,
            description="Committed to delivery",
            participants=["Team"],
            metadata={'due_date': due_date}
        )
    ]

    commitments = await memory_analyst.track_commitments("acc123", events)

    assert commitments[0].due_date == due_date


@pytest.mark.asyncio
async def test_track_commitments_text_preservation(
    memory_analyst
):
    """Test that commitment text is preserved."""
    now = datetime.utcnow()
    commitment_text = "We will deliver the feature integration by Q3 deadline"
    events = [
        TimelineEvent(
            event_id="commit1",
            account_id="acc123",
            timestamp=now,
            event_type=EventType.MEETING,
            description=commitment_text,
            participants=["Team"],
            metadata={}
        )
    ]

    commitments = await memory_analyst.track_commitments("acc123", events)

    assert commitments[0].commitment_text == commitment_text


# Test helper methods

def test_calculate_risk_level_critical(memory_analyst):
    """Test critical risk level calculation."""
    sentiment = SentimentAnalysis(
        account_id="acc123",
        overall_sentiment=-0.5,
        trend=SentimentTrend.DECLINING,
        recent_score=-0.6,
        historical_score=0.2,
        change_rate=-0.8,
        analysis_period_days=90,
        data_points=10
    )

    relationship = RelationshipAssessment(
        account_id="acc123",
        relationship_strength=RelationshipStrength.AT_RISK,
        engagement_score=0.2,
        executive_alignment=0.1,
        touchpoint_frequency=0.5,
        response_rate=0.3,
        last_interaction_days=45,
        key_contacts_count=1,
        executive_sponsor_present=False,
        relationship_health_score=20
    )

    patterns = [
        Pattern(
            pattern_id="p1",
            pattern_type=PatternType.CHURN_RISK,
            confidence=0.8,
            description="Test",
            evidence=[],
            first_detected=datetime.utcnow(),
            last_detected=datetime.utcnow(),
            risk_score=80
        ),
        Pattern(
            pattern_id="p2",
            pattern_type=PatternType.CHURN_RISK,
            confidence=0.7,
            description="Test",
            evidence=[],
            first_detected=datetime.utcnow(),
            last_detected=datetime.utcnow(),
            risk_score=70
        )
    ]

    risk = memory_analyst._calculate_risk_level(sentiment, relationship, patterns)

    assert risk == RiskLevel.CRITICAL


def test_calculate_risk_level_low(memory_analyst):
    """Test low risk level calculation."""
    sentiment = SentimentAnalysis(
        account_id="acc123",
        overall_sentiment=0.7,
        trend=SentimentTrend.IMPROVING,
        recent_score=0.8,
        historical_score=0.6,
        change_rate=0.2,
        analysis_period_days=90,
        data_points=10
    )

    relationship = RelationshipAssessment(
        account_id="acc123",
        relationship_strength=RelationshipStrength.STRONG,
        engagement_score=0.9,
        executive_alignment=0.8,
        touchpoint_frequency=5.0,
        response_rate=0.9,
        last_interaction_days=2,
        key_contacts_count=5,
        executive_sponsor_present=True,
        relationship_health_score=95
    )

    patterns = []

    risk = memory_analyst._calculate_risk_level(sentiment, relationship, patterns)

    assert risk == RiskLevel.LOW


def test_get_metrics(memory_analyst):
    """Test metrics retrieval."""
    metrics = memory_analyst.get_metrics()

    assert isinstance(metrics, dict)
    assert "total_analyses" in metrics
    assert "avg_duration_seconds" in metrics
    assert "cache_hits" in metrics
    assert "pattern_detections" in metrics
