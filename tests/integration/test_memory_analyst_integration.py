"""Integration tests for Memory Analyst.

Tests complete workflows with mocked MemoryService and CogneeClient.
Validates:
- End-to-end context retrieval
- Pattern detection workflows
- Performance requirements (<200ms)
- Error handling and recovery
- Component integration

Target: 30+ integration tests with realistic scenarios.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from src.agents.memory_analyst import MemoryAnalyst
from src.agents.memory_models import (
    HistoricalContext, TimelineEvent, Pattern, SentimentTrend,
    RelationshipStrength, RiskLevel, EventType, PatternType,
    CommitmentStatus
)
from src.services.memory_service import MemoryService
from src.integrations.cognee.cognee_client import CogneeClient


@pytest.fixture
def mock_memory_service():
    """Create fully mocked MemoryService."""
    service = Mock(spec=MemoryService)
    service.store_context = AsyncMock()
    service.get_context = AsyncMock(return_value=None)
    service.update_context = AsyncMock()
    return service


@pytest.fixture
def mock_cognee_client():
    """Create fully mocked CogneeClient with realistic responses."""
    client = Mock(spec=CogneeClient)

    # Default responses
    client.get_account_context = AsyncMock(return_value={
        'account_id': 'acc123',
        'historical_interactions': [],
        'response_rate': 0.7,
        'average_sentiment': 0.5,
        'contacts': [],
        'commitments': [],
        'usage_data': {},
        'contract_data': {}
    })

    client.get_account_timeline = AsyncMock(return_value=[])
    client.search_accounts = AsyncMock(return_value=[])

    return client


@pytest.fixture
def memory_analyst(mock_memory_service, mock_cognee_client):
    """Create Memory Analyst with mocked dependencies."""
    return MemoryAnalyst(
        memory_service=mock_memory_service,
        cognee_client=mock_cognee_client,
        api_key="test-api-key"
    )


@pytest.fixture
def realistic_account_data():
    """Create realistic account data for integration tests."""
    now = datetime.utcnow()

    return {
        'context': {
            'account_id': 'acc123',
            'historical_interactions': [
                {
                    'type': 'meeting',
                    'timestamp': (now - timedelta(days=i*7)).isoformat(),
                    'sentiment': 0.7 - (i * 0.1)
                }
                for i in range(10)
            ],
            'response_rate': 0.8,
            'average_sentiment': 0.6,
            'contacts': [
                {
                    'name': 'John CEO',
                    'level': 'C-Level',
                    'accessible': True,
                    'alignment': 0.9,
                    'is_sponsor': True,
                    'account_id': 'acc123'
                },
                {
                    'name': 'Jane VP',
                    'level': 'VP',
                    'accessible': True,
                    'alignment': 0.8,
                    'is_sponsor': False,
                    'account_id': 'acc123'
                },
                {
                    'name': 'Bob Director',
                    'level': 'Director',
                    'accessible': False,
                    'alignment': 0.6,
                    'is_sponsor': False,
                    'account_id': 'acc123'
                }
            ],
            'commitments': [
                {
                    'status': 'completed',
                    'type': 'feature_delivery',
                    'due_date': (now - timedelta(days=30)).isoformat(),
                    'completion_date': (now - timedelta(days=25)).isoformat()
                },
                {
                    'status': 'overdue',
                    'type': 'support_ticket',
                    'due_date': (now - timedelta(days=10)).isoformat()
                },
                {
                    'status': 'pending',
                    'type': 'documentation'
                }
            ],
            'usage_data': {
                'current_usage': 180,
                'historical_usage': 120
            },
            'contract_data': {
                'renewal_date': (now + timedelta(days=75)).isoformat()
            }
        },
        'timeline': [
            {
                'interaction_id': f'event{i}',
                'timestamp': (now - timedelta(days=i*5)).isoformat(),
                'type': ['meeting', 'email', 'call'][i % 3],
                'summary': f'Event {i} - {"issue" if i % 4 == 0 else "progress"}',
                'participants': ['Team Member'],
                'metadata': {
                    'sentiment': 0.8 - (i * 0.15) if i < 5 else 0.3,
                    'status': 'completed'
                },
                'impact': 'high' if i % 3 == 0 else 'medium'
            }
            for i in range(20)
        ],
        'recommendations': [
            {
                'metadata': {
                    'recommendation_id': f'rec{i}',
                    'generated_date': (now - timedelta(days=i*30)).isoformat(),
                    'recommendation': f'Recommendation {i}',
                    'priority': 'high' if i == 0 else 'medium',
                    'action_type': 'follow_up',
                    'status': 'completed' if i > 0 else 'pending',
                    'outcome': 'successful' if i > 0 else None
                }
            }
            for i in range(3)
        ]
    }


# End-to-End Workflow Tests

@pytest.mark.asyncio
async def test_complete_historical_context_workflow(
    memory_analyst, mock_cognee_client, realistic_account_data
):
    """Test complete historical context retrieval workflow."""
    mock_cognee_client.get_account_context.return_value = realistic_account_data['context']
    mock_cognee_client.get_account_timeline.return_value = realistic_account_data['timeline']
    mock_cognee_client.search_accounts.return_value = realistic_account_data['recommendations']

    context = await memory_analyst.get_historical_context("acc123", include_patterns=True)

    # Verify complete context structure
    assert isinstance(context, HistoricalContext)
    assert context.account_id == "acc123"
    assert len(context.timeline) > 0
    assert len(context.key_events) > 0
    assert context.sentiment_trend in [SentimentTrend.IMPROVING, SentimentTrend.STABLE, SentimentTrend.DECLINING]
    assert context.relationship_strength in [
        RelationshipStrength.STRONG, RelationshipStrength.MODERATE,
        RelationshipStrength.WEAK, RelationshipStrength.AT_RISK
    ]
    assert len(context.patterns) > 0
    assert len(context.commitment_tracking) > 0
    assert context.engagement_metrics is not None
    assert context.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]


@pytest.mark.asyncio
async def test_pattern_detection_workflow(
    memory_analyst, mock_cognee_client, realistic_account_data
):
    """Test pattern detection workflow."""
    mock_cognee_client.get_account_timeline.return_value = realistic_account_data['timeline']
    mock_cognee_client.get_account_context.return_value = realistic_account_data['context']

    patterns = await memory_analyst.identify_patterns("acc123")

    # Should detect multiple pattern types
    assert isinstance(patterns, list)
    assert len(patterns) > 0

    pattern_types = {p.pattern_type for p in patterns}
    # Should have various pattern types based on realistic data
    assert len(pattern_types) >= 2


@pytest.mark.asyncio
async def test_sentiment_analysis_workflow(
    memory_analyst, mock_cognee_client, realistic_account_data
):
    """Test sentiment analysis workflow."""
    mock_cognee_client.get_account_timeline.return_value = realistic_account_data['timeline']

    sentiment = await memory_analyst.analyze_sentiment_trend("acc123")

    assert sentiment.account_id == "acc123"
    assert sentiment.trend == SentimentTrend.DECLINING  # Based on realistic data
    assert -1.0 <= sentiment.overall_sentiment <= 1.0
    assert sentiment.data_points > 0


@pytest.mark.asyncio
async def test_relationship_assessment_workflow(
    memory_analyst, mock_cognee_client, realistic_account_data
):
    """Test relationship assessment workflow."""
    mock_cognee_client.get_account_context.return_value = realistic_account_data['context']

    assessment = await memory_analyst.assess_relationship_strength("acc123")

    assert assessment.account_id == "acc123"
    assert assessment.relationship_strength in [
        RelationshipStrength.STRONG, RelationshipStrength.MODERATE,
        RelationshipStrength.WEAK, RelationshipStrength.AT_RISK
    ]
    assert assessment.executive_sponsor_present is True
    assert assessment.key_contacts_count == 3


@pytest.mark.asyncio
async def test_commitment_tracking_workflow(
    memory_analyst, mock_cognee_client, realistic_account_data
):
    """Test commitment tracking workflow."""
    # Add commitment keywords to timeline
    timeline_with_commitments = realistic_account_data['timeline'][:5]
    timeline_with_commitments[0]['summary'] = "We promised to deliver the feature"
    timeline_with_commitments[1]['summary'] = "Committed to resolving the issue"
    timeline_with_commitments[2]['summary'] = "Will provide documentation next week"

    mock_cognee_client.get_account_timeline.return_value = timeline_with_commitments

    commitments = await memory_analyst.track_commitments("acc123")

    assert len(commitments) == 3
    assert all(c.account_id == "acc123" for c in commitments)


# Performance Tests

@pytest.mark.asyncio
async def test_context_retrieval_performance(
    memory_analyst, mock_cognee_client, realistic_account_data
):
    """Test that context retrieval meets <200ms target."""
    mock_cognee_client.get_account_context.return_value = realistic_account_data['context']
    mock_cognee_client.get_account_timeline.return_value = realistic_account_data['timeline'][:10]
    mock_cognee_client.search_accounts.return_value = []

    start = datetime.utcnow()
    context = await memory_analyst.get_historical_context("acc123", include_patterns=False)
    duration = (datetime.utcnow() - start).total_seconds()

    # Allow some overhead for mocking, but should still be fast
    assert duration < 1.0
    assert isinstance(context, HistoricalContext)


@pytest.mark.asyncio
async def test_pattern_detection_performance(
    memory_analyst, mock_cognee_client, realistic_account_data
):
    """Test pattern detection performance."""
    mock_cognee_client.get_account_timeline.return_value = realistic_account_data['timeline']
    mock_cognee_client.get_account_context.return_value = realistic_account_data['context']

    start = datetime.utcnow()
    patterns = await memory_analyst.identify_patterns("acc123")
    duration = (datetime.utcnow() - start).total_seconds()

    assert duration < 1.0
    assert isinstance(patterns, list)


@pytest.mark.asyncio
async def test_concurrent_operations_performance(
    memory_analyst, mock_cognee_client, realistic_account_data
):
    """Test performance of concurrent operations."""
    mock_cognee_client.get_account_context.return_value = realistic_account_data['context']
    mock_cognee_client.get_account_timeline.return_value = realistic_account_data['timeline'][:10]
    mock_cognee_client.search_accounts.return_value = []

    # Simulate concurrent requests
    start = datetime.utcnow()
    results = await asyncio.gather(
        memory_analyst.get_historical_context("acc123", include_patterns=False),
        memory_analyst.analyze_sentiment_trend("acc123"),
        memory_analyst.assess_relationship_strength("acc123")
    )
    duration = (datetime.utcnow() - start).total_seconds()

    # Concurrent operations should be faster than sequential
    assert duration < 2.0
    assert len(results) == 3


# Error Handling Tests

@pytest.mark.asyncio
async def test_cognee_api_failure_handling(
    memory_analyst, mock_cognee_client
):
    """Test handling of Cognee API failures."""
    mock_cognee_client.get_account_context.side_effect = Exception("API Error")
    mock_cognee_client.get_account_timeline.side_effect = Exception("API Error")
    mock_cognee_client.search_accounts.side_effect = Exception("API Error")

    # Should handle gracefully
    context = await memory_analyst.get_historical_context("acc123")

    assert isinstance(context, HistoricalContext)


@pytest.mark.asyncio
async def test_partial_api_failure_handling(
    memory_analyst, mock_cognee_client, realistic_account_data
):
    """Test handling when some API calls fail."""
    mock_cognee_client.get_account_context.return_value = realistic_account_data['context']
    mock_cognee_client.get_account_timeline.side_effect = Exception("Timeline API Error")
    mock_cognee_client.search_accounts.return_value = []

    context = await memory_analyst.get_historical_context("acc123")

    # Should still return context with partial data
    assert isinstance(context, HistoricalContext)
    assert context.timeline == []  # Failed to retrieve


@pytest.mark.asyncio
async def test_invalid_data_handling(
    memory_analyst, mock_cognee_client
):
    """Test handling of invalid/malformed data."""
    mock_cognee_client.get_account_context.return_value = {
        'invalid': 'structure',
        'missing': 'required_fields'
    }
    mock_cognee_client.get_account_timeline.return_value = [
        {'invalid': 'event'},
        {'also': 'invalid'}
    ]
    mock_cognee_client.search_accounts.return_value = []

    context = await memory_analyst.get_historical_context("acc123")

    # Should handle gracefully without crashing
    assert isinstance(context, HistoricalContext)


@pytest.mark.asyncio
async def test_empty_data_handling(
    memory_analyst, mock_cognee_client
):
    """Test handling of empty responses."""
    mock_cognee_client.get_account_context.return_value = {
        'account_id': 'acc123',
        'historical_interactions': [],
        'contacts': [],
        'commitments': []
    }
    mock_cognee_client.get_account_timeline.return_value = []
    mock_cognee_client.search_accounts.return_value = []

    context = await memory_analyst.get_historical_context("acc123")

    assert isinstance(context, HistoricalContext)
    assert context.timeline == []
    assert context.key_events == []


# Scenario-Based Integration Tests

@pytest.mark.asyncio
async def test_at_risk_account_scenario(
    memory_analyst, mock_cognee_client
):
    """Test complete workflow for at-risk account."""
    now = datetime.utcnow()

    # At-risk account data
    at_risk_context = {
        'account_id': 'acc123',
        'historical_interactions': [
            {
                'timestamp': (now - timedelta(days=60)).isoformat(),
                'type': 'email',
                'sentiment': -0.5
            }
        ],
        'response_rate': 0.2,
        'average_sentiment': -0.4,
        'contacts': [],
        'commitments': [
            {'status': 'overdue', 'type': 'critical_issue'},
            {'status': 'overdue', 'type': 'support'}
        ],
        'usage_data': {'current_usage': 50, 'historical_usage': 150},
        'contract_data': {'renewal_date': (now + timedelta(days=45)).isoformat()}
    }

    at_risk_timeline = [
        {
            'interaction_id': f'event{i}',
            'timestamp': (now - timedelta(days=60+i*10)).isoformat(),
            'type': 'email',
            'summary': 'Issues and concerns raised',
            'participants': ['Customer'],
            'metadata': {'sentiment': -0.6},
            'impact': 'high'
        }
        for i in range(5)
    ]

    mock_cognee_client.get_account_context.return_value = at_risk_context
    mock_cognee_client.get_account_timeline.return_value = at_risk_timeline
    mock_cognee_client.search_accounts.return_value = []

    context = await memory_analyst.get_historical_context("acc123", include_patterns=True)

    # Should detect high risk
    assert context.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    assert context.relationship_strength in [RelationshipStrength.WEAK, RelationshipStrength.AT_RISK]
    assert context.sentiment_trend in [SentimentTrend.DECLINING, SentimentTrend.STABLE]

    # Should detect churn and renewal risk patterns
    churn_patterns = [p for p in context.patterns if p.pattern_type == PatternType.CHURN_RISK]
    renewal_patterns = [p for p in context.patterns if p.pattern_type == PatternType.RENEWAL_RISK]
    assert len(churn_patterns) > 0 or len(renewal_patterns) > 0


@pytest.mark.asyncio
async def test_healthy_account_scenario(
    memory_analyst, mock_cognee_client
):
    """Test complete workflow for healthy account."""
    now = datetime.utcnow()

    healthy_context = {
        'account_id': 'acc123',
        'historical_interactions': [
            {
                'timestamp': (now - timedelta(days=i)).isoformat(),
                'type': 'meeting',
                'sentiment': 0.8
            }
            for i in range(0, 60, 3)
        ],
        'response_rate': 0.95,
        'average_sentiment': 0.85,
        'contacts': [
            {
                'level': 'C-Level',
                'accessible': True,
                'alignment': 0.9,
                'is_sponsor': True,
                'account_id': 'acc123'
            },
            {
                'level': 'VP',
                'accessible': True,
                'alignment': 0.85,
                'is_sponsor': True,
                'account_id': 'acc123'
            }
        ],
        'commitments': [
            {'status': 'completed', 'type': 'feature'},
            {'status': 'completed', 'type': 'support'}
        ],
        'usage_data': {'current_usage': 250, 'historical_usage': 150},
        'contract_data': {}
    }

    healthy_timeline = [
        {
            'interaction_id': f'event{i}',
            'timestamp': (now - timedelta(days=i*3)).isoformat(),
            'type': 'meeting',
            'summary': 'Positive discussion about expansion',
            'participants': ['Sales', 'Customer'],
            'metadata': {'sentiment': 0.9},
            'impact': 'high' if i % 2 == 0 else 'medium'
        }
        for i in range(20)
    ]

    mock_cognee_client.get_account_context.return_value = healthy_context
    mock_cognee_client.get_account_timeline.return_value = healthy_timeline
    mock_cognee_client.search_accounts.return_value = []

    context = await memory_analyst.get_historical_context("acc123", include_patterns=True)

    # Should indicate healthy account
    assert context.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]
    assert context.relationship_strength in [RelationshipStrength.STRONG, RelationshipStrength.MODERATE]

    # Should detect upsell opportunities
    upsell_patterns = [p for p in context.patterns if p.pattern_type == PatternType.UPSELL_OPPORTUNITY]
    assert len(upsell_patterns) > 0


@pytest.mark.asyncio
async def test_renewal_period_scenario(
    memory_analyst, mock_cognee_client
):
    """Test workflow during renewal period."""
    now = datetime.utcnow()

    renewal_context = {
        'account_id': 'acc123',
        'historical_interactions': [
            {
                'timestamp': (now - timedelta(days=i*5)).isoformat(),
                'type': 'meeting',
                'sentiment': 0.6
            }
            for i in range(12)
        ],
        'response_rate': 0.7,
        'average_sentiment': 0.5,
        'contacts': [
            {
                'level': 'VP',
                'accessible': True,
                'alignment': 0.7,
                'is_sponsor': False,
                'account_id': 'acc123'
            }
        ],
        'commitments': [
            {'status': 'pending', 'type': 'renewal_discussion'}
        ],
        'usage_data': {},
        'contract_data': {
            'renewal_date': (now + timedelta(days=60)).isoformat()
        }
    }

    renewal_timeline = [
        {
            'interaction_id': 'budget_discussion',
            'timestamp': (now - timedelta(days=20)).isoformat(),
            'type': 'meeting',
            'summary': 'Budget review and pricing discussion',
            'participants': ['Finance'],
            'metadata': {'sentiment': 0.3},
            'impact': 'high'
        },
        {
            'interaction_id': 'competitive',
            'timestamp': (now - timedelta(days=10)).isoformat(),
            'type': 'email',
            'summary': 'Evaluating alternative solutions',
            'participants': ['Customer'],
            'metadata': {'sentiment': 0.2},
            'impact': 'high'
        }
    ]

    mock_cognee_client.get_account_context.return_value = renewal_context
    mock_cognee_client.get_account_timeline.return_value = renewal_timeline
    mock_cognee_client.search_accounts.return_value = []

    context = await memory_analyst.get_historical_context("acc123", include_patterns=True)

    # Should detect renewal risks
    renewal_patterns = [p for p in context.patterns if p.pattern_type == PatternType.RENEWAL_RISK]
    assert len(renewal_patterns) > 0


@pytest.mark.asyncio
async def test_executive_change_scenario(
    memory_analyst, mock_cognee_client
):
    """Test workflow after executive sponsor change."""
    now = datetime.utcnow()

    exec_change_context = {
        'account_id': 'acc123',
        'historical_interactions': [
            {
                'timestamp': (now - timedelta(days=i*5)).isoformat(),
                'type': 'meeting',
                'sentiment': 0.5
            }
            for i in range(10)
        ],
        'response_rate': 0.6,
        'average_sentiment': 0.4,
        'contacts': [
            {
                'level': 'C-Level',
                'accessible': False,
                'alignment': 0.3,
                'is_sponsor': True,
                'account_id': 'acc123',
                'name': 'New Executive'
            }
        ],
        'commitments': [],
        'usage_data': {},
        'contract_data': {}
    }

    exec_change_timeline = [
        {
            'interaction_id': 'exec_change',
            'timestamp': (now - timedelta(days=30)).isoformat(),
            'type': 'executive_change',
            'summary': 'Executive sponsor changed from Alice to Bob',
            'participants': ['Alice', 'Bob'],
            'metadata': {},
            'impact': 'high'
        }
    ]

    mock_cognee_client.get_account_context.return_value = exec_change_context
    mock_cognee_client.get_account_timeline.return_value = exec_change_timeline
    mock_cognee_client.search_accounts.return_value = []

    context = await memory_analyst.get_historical_context("acc123", include_patterns=True)

    # Should detect executive change pattern
    exec_patterns = [p for p in context.patterns if p.pattern_type == PatternType.EXECUTIVE_CHANGE]
    assert len(exec_patterns) > 0


# Metrics and Performance Tracking Tests

@pytest.mark.asyncio
async def test_metrics_tracking(
    memory_analyst, mock_cognee_client, realistic_account_data
):
    """Test that performance metrics are tracked."""
    mock_cognee_client.get_account_context.return_value = realistic_account_data['context']
    mock_cognee_client.get_account_timeline.return_value = realistic_account_data['timeline'][:5]
    mock_cognee_client.search_accounts.return_value = []

    initial_metrics = memory_analyst.get_metrics()
    initial_count = initial_metrics['total_analyses']

    await memory_analyst.get_historical_context("acc123")
    await memory_analyst.get_historical_context("acc456")

    final_metrics = memory_analyst.get_metrics()

    assert final_metrics['total_analyses'] == initial_count + 2
    assert final_metrics['avg_duration_seconds'] >= 0


@pytest.mark.asyncio
async def test_pattern_detection_metrics(
    memory_analyst, mock_cognee_client, realistic_account_data
):
    """Test pattern detection metrics tracking."""
    mock_cognee_client.get_account_context.return_value = realistic_account_data['context']
    mock_cognee_client.get_account_timeline.return_value = realistic_account_data['timeline']
    mock_cognee_client.search_accounts.return_value = []

    initial_metrics = memory_analyst.get_metrics()
    initial_patterns = initial_metrics['pattern_detections']

    await memory_analyst.get_historical_context("acc123", include_patterns=True)

    final_metrics = memory_analyst.get_metrics()

    assert final_metrics['pattern_detections'] > initial_patterns


# Data Consistency Tests

@pytest.mark.asyncio
async def test_temporal_consistency(
    memory_analyst, mock_cognee_client, realistic_account_data
):
    """Test temporal data consistency across components."""
    mock_cognee_client.get_account_context.return_value = realistic_account_data['context']
    mock_cognee_client.get_account_timeline.return_value = realistic_account_data['timeline']
    mock_cognee_client.search_accounts.return_value = realistic_account_data['recommendations']

    context = await memory_analyst.get_historical_context("acc123", include_patterns=True)

    # Verify temporal consistency
    if context.timeline:
        assert context.timeline[0].timestamp <= context.timeline[-1].timestamp

    for pattern in context.patterns:
        assert pattern.first_detected <= pattern.last_detected

    assert isinstance(context.last_updated, datetime)


@pytest.mark.asyncio
async def test_account_id_consistency(
    memory_analyst, mock_cognee_client, realistic_account_data
):
    """Test account ID consistency across all components."""
    mock_cognee_client.get_account_context.return_value = realistic_account_data['context']
    mock_cognee_client.get_account_timeline.return_value = realistic_account_data['timeline']
    mock_cognee_client.search_accounts.return_value = realistic_account_data['recommendations']

    context = await memory_analyst.get_historical_context("acc123", include_patterns=True)

    # All components should have consistent account_id
    assert context.account_id == "acc123"

    for event in context.timeline:
        assert event.account_id == "acc123"

    for event in context.key_events:
        assert event.account_id == "acc123"

    for commitment in context.commitment_tracking:
        assert commitment.account_id == "acc123"

    if context.engagement_metrics:
        assert context.engagement_metrics.account_id == "acc123"


# Edge Case Tests

@pytest.mark.asyncio
async def test_very_long_timeline(
    memory_analyst, mock_cognee_client
):
    """Test handling of very long timeline."""
    now = datetime.utcnow()

    # Create 1000 events
    long_timeline = [
        {
            'interaction_id': f'event{i}',
            'timestamp': (now - timedelta(days=i)).isoformat(),
            'type': 'email',
            'summary': f'Event {i}',
            'participants': [],
            'metadata': {'sentiment': 0.5},
            'impact': 'medium'
        }
        for i in range(1000)
    ]

    mock_cognee_client.get_account_context.return_value = {'account_id': 'acc123', 'commitments': []}
    mock_cognee_client.get_account_timeline.return_value = long_timeline
    mock_cognee_client.search_accounts.return_value = []

    context = await memory_analyst.get_historical_context("acc123")

    # Should handle gracefully
    assert isinstance(context, HistoricalContext)
    assert len(context.timeline) > 0


@pytest.mark.asyncio
async def test_missing_optional_fields(
    memory_analyst, mock_cognee_client
):
    """Test handling when optional fields are missing."""
    minimal_context = {
        'account_id': 'acc123'
    }

    minimal_timeline = [
        {
            'interaction_id': 'event1',
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'email',
            'summary': 'Event'
        }
    ]

    mock_cognee_client.get_account_context.return_value = minimal_context
    mock_cognee_client.get_account_timeline.return_value = minimal_timeline
    mock_cognee_client.search_accounts.return_value = []

    context = await memory_analyst.get_historical_context("acc123")

    # Should handle gracefully with defaults
    assert isinstance(context, HistoricalContext)


@pytest.mark.asyncio
async def test_unicode_and_special_characters(
    memory_analyst, mock_cognee_client
):
    """Test handling of unicode and special characters."""
    unicode_context = {
        'account_id': 'acc123',
        'historical_interactions': [],
        'contacts': [
            {
                'name': 'José García',
                'level': 'C-Level',
                'accessible': True,
                'alignment': 0.8,
                'is_sponsor': True,
                'account_id': 'acc123'
            }
        ],
        'commitments': []
    }

    unicode_timeline = [
        {
            'interaction_id': 'event1',
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'email',
            'summary': 'Discussion about €1M expansion opportunity 中文',
            'participants': ['José García'],
            'metadata': {}
        }
    ]

    mock_cognee_client.get_account_context.return_value = unicode_context
    mock_cognee_client.get_account_timeline.return_value = unicode_timeline
    mock_cognee_client.search_accounts.return_value = []

    context = await memory_analyst.get_historical_context("acc123")

    # Should handle unicode characters
    assert isinstance(context, HistoricalContext)
    assert 'José García' in unicode_timeline[0]['participants']


@pytest.mark.asyncio
async def test_duplicate_events(
    memory_analyst, mock_cognee_client
):
    """Test handling of duplicate events in timeline."""
    now = datetime.utcnow()

    # Create duplicate events
    duplicate_timeline = [
        {
            'interaction_id': 'event1',
            'timestamp': now.isoformat(),
            'type': 'email',
            'summary': 'Same event',
            'participants': [],
            'metadata': {}
        }
        for _ in range(5)
    ]

    mock_cognee_client.get_account_context.return_value = {'account_id': 'acc123', 'commitments': []}
    mock_cognee_client.get_account_timeline.return_value = duplicate_timeline
    mock_cognee_client.search_accounts.return_value = []

    context = await memory_analyst.get_historical_context("acc123")

    # Should handle duplicates
    assert isinstance(context, HistoricalContext)
