"""Memory Analyst Subagent for Sergas Account Manager.

Implements the Memory Analyst as specified in SPARC Architecture (lines 229-282).
Queries Cognee memory for historical context, patterns, and recommendations.

Architecture Alignment:
- Tool allowlist: cognee_search_memory, cognee_retrieve_history,
  cognee_aggregate_insights, cognee_get_relationship_graph, Read
- Permission mode: default (read-only)
- Output format: Historical context matching SPARC spec

Integration:
- Cognee knowledge graph for historical data
- Memory Service for coordination
- Pattern Recognition for advanced analysis
"""

from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime, timedelta
import asyncio
import structlog

from anthropic import Anthropic
from anthropic.types import Message, MessageParam, TextBlock

from src.services.memory_service import MemoryService
from src.integrations.cognee.cognee_client import CogneeClient
from src.memory.cognee_mcp_tools import CogneeMCPTools
from src.agents.memory_models import (
    HistoricalContext, TimelineEvent, Pattern, SentimentAnalysis,
    PriorRecommendation, RelationshipAssessment, Commitment,
    KeyEvent, EngagementMetrics, SentimentTrend, RelationshipStrength,
    RiskLevel, PatternType, EventType, CommitmentStatus
)
from src.agents.memory_utils import (
    detect_churn_patterns, identify_engagement_cycles,
    find_commitment_patterns, calculate_sentiment_trend,
    analyze_communication_tone, build_account_timeline,
    identify_key_milestones, calculate_relationship_score,
    assess_executive_alignment
)
from src.agents.pattern_recognition import PatternRecognizer
from src.events.ag_ui_emitter import AGUIEventEmitter

logger = structlog.get_logger(__name__)


class MemoryAnalyst:
    """Memory Analyst Subagent for account history analysis.

    Responsibilities (SPARC PRD):
    1. Search Cognee memory for historical account context
    2. Identify patterns in past interactions and deals
    3. Aggregate sentiment trends and commitment tracking
    4. Surface relevant prior recommendations and outcomes

    Tool Allowlist:
    - cognee_search_memory
    - cognee_retrieve_history
    - cognee_aggregate_insights
    - cognee_get_relationship_graph
    - Read (for templates)

    Permission Mode: default (read-only)

    Output Format (lines 258-273):
    {
      "account_id": "123456789",
      "historical_context": {
        "key_events": [...],
        "sentiment_trend": "declining",
        "prior_recommendations": [...],
        "relationship_strength": "strong",
        "commitment_tracking": [...]
      }
    }
    """

    # System prompt from SPARC architecture (lines 249-277)
    SYSTEM_PROMPT = """You are the Memory Analyst for Sergas Account Manager.

Your responsibilities:
1. Search Cognee memory for historical account context
2. Identify patterns in past interactions, deals, and recommendations
3. Aggregate sentiment trends and commitment tracking
4. Surface relevant prior recommendations and their outcomes

Output Format:
{
  "account_id": "123456789",
  "historical_context": {
    "key_events": [
      {"date": "2025-09-01", "event": "Executive sponsor changed",
       "impact": "Delayed Q3 renewal"}
    ],
    "sentiment_trend": "declining",
    "prior_recommendations": [
      {"date": "2025-08-15", "recommendation": "Schedule exec briefing",
       "status": "completed", "outcome": "positive"}
    ],
    "relationship_strength": "strong",
    "commitment_tracking": ["Q4 renewal intent confirmed", "Budget approved"]
  }
}

Prioritize insights relevant to current account status.
If memory is stale, flag for re-ingestion.
"""

    def __init__(
        self,
        memory_service: MemoryService,
        cognee_client: CogneeClient,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022"
    ):
        """Initialize Memory Analyst.

        Args:
            memory_service: Memory service for coordination
            cognee_client: Cognee client for knowledge graph
            api_key: Anthropic API key for Claude
            model: Claude model to use
        """
        self.memory_service = memory_service
        self.cognee = cognee_client
        self.cognee_tools = CogneeMCPTools(cognee_client)
        self.pattern_recognizer = PatternRecognizer()

        # Initialize Anthropic client with optional base_url (for GLM-4.6 via Z.ai)
        base_url = os.getenv("ANTHROPIC_BASE_URL")
        if base_url:
            self.client = Anthropic(api_key=api_key, base_url=base_url)
        else:
            self.client = Anthropic(api_key=api_key)
        self.model = model

        self.logger = logger.bind(
            component="memory_analyst",
            model=model
        )

        # Performance metrics
        self._metrics = {
            "total_analyses": 0,
            "avg_duration_seconds": 0.0,
            "cache_hits": 0,
            "pattern_detections": 0
        }

    async def get_historical_context(
        self,
        account_id: str,
        lookback_days: int = 365,
        include_patterns: bool = True
    ) -> HistoricalContext:
        """Get complete historical context for account.

        Main function for retrieving comprehensive account history.
        Target: < 200ms (SPARC PRD metric)

        Args:
            account_id: Account identifier
            lookback_days: How far back to analyze
            include_patterns: Include pattern detection

        Returns:
            Complete historical context matching SPARC output format
        """
        start_time = datetime.utcnow()

        self.logger.info(
            "getting_historical_context",
            account_id=account_id,
            lookback_days=lookback_days
        )

        try:
            # Parallel retrieval of context components
            context_data, timeline_data, recommendations_data = await asyncio.gather(
                self.cognee.get_account_context(account_id),
                self.cognee.get_account_timeline(account_id, limit=50),
                self._get_prior_recommendations(account_id, lookback_days),
                return_exceptions=True
            )

            # Handle exceptions from parallel tasks
            context = context_data if not isinstance(context_data, Exception) else {}
            timeline_raw = timeline_data if not isinstance(timeline_data, Exception) else []
            prior_recs = recommendations_data if not isinstance(recommendations_data, Exception) else []

            # Build timeline events
            timeline_events = self._build_timeline_events(account_id, timeline_raw)

            # Identify key events
            key_events = self._extract_key_events(timeline_events)

            # Analyze sentiment
            sentiment = await self.analyze_sentiment_trend(account_id, timeline_events)

            # Assess relationship
            relationship = await self.assess_relationship_strength(account_id, context)

            # Track commitments
            commitments = await self.track_commitments(account_id, timeline_events)

            # Detect patterns if requested
            patterns = []
            if include_patterns:
                patterns = await self.identify_patterns(account_id, timeline_events, context)

            # Determine risk level
            risk_level = self._calculate_risk_level(sentiment, relationship, patterns)

            # Build historical context
            historical_context = HistoricalContext(
                account_id=account_id,
                key_events=key_events,
                sentiment_trend=sentiment.trend,
                prior_recommendations=prior_recs,
                relationship_strength=relationship.relationship_strength,
                commitment_tracking=commitments,
                patterns=patterns,
                timeline=timeline_events,
                engagement_metrics=self._build_engagement_metrics(
                    account_id, timeline_events, lookback_days
                ),
                risk_level=risk_level,
                last_updated=datetime.utcnow()
            )

            duration = (datetime.utcnow() - start_time).total_seconds()

            # Update metrics
            self._metrics["total_analyses"] += 1
            self._metrics["avg_duration_seconds"] = (
                (self._metrics["avg_duration_seconds"] * (self._metrics["total_analyses"] - 1) + duration)
                / self._metrics["total_analyses"]
            )
            if include_patterns:
                self._metrics["pattern_detections"] += len(patterns)

            self.logger.info(
                "historical_context_retrieved",
                account_id=account_id,
                duration_seconds=duration,
                within_target=duration < 0.2,
                key_events_count=len(key_events),
                patterns_count=len(patterns)
            )

            return historical_context

        except Exception as e:
            self.logger.error(
                "historical_context_retrieval_failed",
                account_id=account_id,
                error=str(e)
            )
            raise

    async def identify_patterns(
        self,
        account_id: str,
        timeline_events: Optional[List[TimelineEvent]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Pattern]:
        """Identify patterns in account history.

        Detects:
        - Churn risk patterns
        - Engagement cycles
        - Commitment patterns
        - Upsell opportunities
        - Renewal risks

        Args:
            account_id: Account identifier
            timeline_events: Timeline events (fetched if not provided)
            context: Account context (fetched if not provided)

        Returns:
            List of detected patterns
        """
        self.logger.info("identifying_patterns", account_id=account_id)

        try:
            # Fetch data if not provided
            if timeline_events is None:
                timeline_raw = await self.cognee.get_account_timeline(account_id, limit=50)
                timeline_events = self._build_timeline_events(account_id, timeline_raw)

            if context is None:
                context = await self.cognee.get_account_context(account_id)

            patterns: List[Pattern] = []

            # Detect churn patterns
            churn_patterns = detect_churn_patterns(timeline_events)
            patterns.extend(churn_patterns)

            # Detect engagement cycles
            interactions_data = [
                {
                    'account_id': event.account_id,
                    'timestamp': event.timestamp.isoformat(),
                    'type': event.event_type.value
                }
                for event in timeline_events
            ]
            engagement_cycles = identify_engagement_cycles(interactions_data)

            # Convert cycles to patterns
            for cycle in engagement_cycles:
                patterns.append(Pattern(
                    pattern_id=cycle.cycle_id,
                    pattern_type=PatternType.ENGAGEMENT_CYCLE,
                    confidence=cycle.confidence,
                    description=f"{cycle.cycle_type} engagement cycle detected",
                    evidence=[
                        f"Cycle length: {cycle.cycle_length_days} days",
                        f"Average frequency: {cycle.average_frequency:.2f}"
                    ],
                    first_detected=cycle.start_date,
                    last_detected=cycle.end_date,
                    frequency=1,
                    risk_score=0
                ))

            # Detect commitment patterns
            commitment_history = {
                'account_id': account_id,
                'commitments': context.get('commitments', [])
            }
            commitment_patterns = find_commitment_patterns(commitment_history)

            for cp in commitment_patterns:
                patterns.append(Pattern(
                    pattern_id=cp.pattern_id,
                    pattern_type=PatternType.COMMITMENT_PATTERN,
                    confidence=0.7,
                    description=cp.pattern_description,
                    evidence=[
                        f"Completion rate: {cp.completion_rate:.1%}",
                        f"Average delay: {cp.average_delay_days:.1f} days"
                    ],
                    first_detected=datetime.utcnow() - timedelta(days=90),
                    last_detected=datetime.utcnow(),
                    frequency=cp.commitment_count,
                    risk_score=50 if cp.completion_rate < 0.7 else 20,
                    recommendations=["Review commitment tracking", "Improve delivery process"]
                ))

            # Use pattern recognizer for advanced patterns
            engagement_data = {
                'total_interactions': len(timeline_events),
                'days_since_last_interaction': (
                    datetime.utcnow() - timeline_events[-1].timestamp
                ).days if timeline_events else 90
            }

            advanced_churn = self.pattern_recognizer.detect_churn_risk_patterns(
                account_id, timeline_events, engagement_data
            )
            patterns.extend(advanced_churn)

            usage_data = context.get('usage_data', {})
            upsell_patterns = self.pattern_recognizer.detect_upsell_opportunities(
                account_id, timeline_events, usage_data
            )
            patterns.extend(upsell_patterns)

            contract_data = context.get('contract_data', {})
            renewal_patterns = self.pattern_recognizer.detect_renewal_risk_patterns(
                account_id, timeline_events, contract_data
            )
            patterns.extend(renewal_patterns)

            self.logger.info(
                "patterns_identified",
                account_id=account_id,
                pattern_count=len(patterns)
            )

            return patterns

        except Exception as e:
            self.logger.error(
                "pattern_identification_failed",
                account_id=account_id,
                error=str(e)
            )
            return []

    async def analyze_sentiment_trend(
        self,
        account_id: str,
        timeline_events: Optional[List[TimelineEvent]] = None
    ) -> SentimentAnalysis:
        """Analyze sentiment trend over time.

        Args:
            account_id: Account identifier
            timeline_events: Timeline events (fetched if not provided)

        Returns:
            Sentiment analysis with trend
        """
        self.logger.info("analyzing_sentiment_trend", account_id=account_id)

        try:
            if timeline_events is None:
                timeline_raw = await self.cognee.get_account_timeline(account_id, limit=50)
                timeline_events = self._build_timeline_events(account_id, timeline_raw)

            if not timeline_events:
                return SentimentAnalysis(
                    account_id=account_id,
                    overall_sentiment=0.0,
                    trend=SentimentTrend.UNKNOWN,
                    recent_score=0.0,
                    historical_score=0.0,
                    change_rate=0.0,
                    analysis_period_days=365,
                    data_points=0
                )

            # Calculate sentiment from interactions
            interactions = [
                {
                    'account_id': event.account_id,
                    'timestamp': event.timestamp.isoformat(),
                    'sentiment': event.metadata.get('sentiment', 0.0)
                }
                for event in timeline_events
            ]

            trend = calculate_sentiment_trend(interactions)

            # Calculate scores
            recent_events = [e for e in timeline_events if (
                datetime.utcnow() - e.timestamp
            ).days <= 30]
            historical_events = [e for e in timeline_events if 30 < (
                datetime.utcnow() - e.timestamp
            ).days <= 90]

            recent_score = self._calculate_avg_sentiment(recent_events)
            historical_score = self._calculate_avg_sentiment(historical_events)
            overall_sentiment = self._calculate_avg_sentiment(timeline_events)

            change_rate = recent_score - historical_score if historical_events else 0.0

            # Extract key factors
            key_factors = []
            if change_rate < -0.3:
                key_factors.append("Significant negative shift detected")
            elif change_rate > 0.3:
                key_factors.append("Significant positive improvement")

            negative_events = [e for e in recent_events if e.metadata.get('sentiment', 0) < -0.5]
            if len(negative_events) > 2:
                key_factors.append(f"{len(negative_events)} highly negative interactions")

            # Generate warnings
            warnings = []
            if trend == SentimentTrend.DECLINING:
                warnings.append("Sentiment trend is declining - immediate attention needed")
            if overall_sentiment < -0.3:
                warnings.append("Overall sentiment is negative - review account health")

            return SentimentAnalysis(
                account_id=account_id,
                overall_sentiment=overall_sentiment,
                trend=trend,
                recent_score=recent_score,
                historical_score=historical_score,
                change_rate=change_rate,
                analysis_period_days=365,
                data_points=len(timeline_events),
                key_factors=key_factors,
                warnings=warnings
            )

        except Exception as e:
            self.logger.error(
                "sentiment_analysis_failed",
                account_id=account_id,
                error=str(e)
            )
            raise

    async def get_prior_recommendations(
        self,
        account_id: str,
        lookback_days: int = 180
    ) -> List[PriorRecommendation]:
        """Get prior recommendations and their outcomes.

        Args:
            account_id: Account identifier
            lookback_days: How far back to look

        Returns:
            List of prior recommendations
        """
        return await self._get_prior_recommendations(account_id, lookback_days)

    async def assess_relationship_strength(
        self,
        account_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RelationshipAssessment:
        """Assess account relationship strength.

        Args:
            account_id: Account identifier
            context: Account context (fetched if not provided)

        Returns:
            Relationship assessment
        """
        self.logger.info("assessing_relationship_strength", account_id=account_id)

        try:
            if context is None:
                context = await self.cognee.get_account_context(account_id)

            # Extract interaction data
            interactions = {
                'total_interactions': len(context.get('historical_interactions', [])),
                'days_since_last_interaction': self._calculate_days_since_last(
                    context.get('historical_interactions', [])
                ),
                'response_rate': context.get('response_rate', 0.5),
                'average_sentiment': context.get('average_sentiment', 0.0),
                'executive_engagement': len([
                    i for i in context.get('historical_interactions', [])
                    if i.get('type') == 'executive_meeting'
                ])
            }

            # Calculate relationship score
            relationship_score = calculate_relationship_score(interactions)

            # Assess executive alignment
            contacts = context.get('contacts', [])
            exec_alignment = assess_executive_alignment(contacts)

            # Determine relationship strength
            if relationship_score >= 0.8:
                strength = RelationshipStrength.STRONG
            elif relationship_score >= 0.6:
                strength = RelationshipStrength.MODERATE
            elif relationship_score >= 0.4:
                strength = RelationshipStrength.WEAK
            else:
                strength = RelationshipStrength.AT_RISK

            # Calculate metrics
            engagement_score = min(1.0, interactions['total_interactions'] / 50)
            touchpoint_frequency = interactions['total_interactions'] / 30  # per month
            response_rate = interactions['response_rate']

            # Identify trends
            improvement_trends = []
            degradation_risks = []

            if relationship_score > 0.7:
                improvement_trends.append("Strong relationship foundation")
            if exec_alignment.overall_alignment > 0.7:
                improvement_trends.append("Excellent executive alignment")

            if interactions['days_since_last_interaction'] > 14:
                degradation_risks.append("Infrequent recent contact")
            if response_rate < 0.5:
                degradation_risks.append("Low response rate")

            return RelationshipAssessment(
                account_id=account_id,
                relationship_strength=strength,
                engagement_score=engagement_score,
                executive_alignment=exec_alignment.overall_alignment,
                touchpoint_frequency=touchpoint_frequency,
                response_rate=response_rate,
                last_interaction_days=interactions['days_since_last_interaction'],
                key_contacts_count=len(contacts),
                executive_sponsor_present=exec_alignment.executive_engagement_count > 0,
                relationship_health_score=int(relationship_score * 100),
                improvement_trends=improvement_trends,
                degradation_risks=degradation_risks
            )

        except Exception as e:
            self.logger.error(
                "relationship_assessment_failed",
                account_id=account_id,
                error=str(e)
            )
            raise

    async def track_commitments(
        self,
        account_id: str,
        timeline_events: Optional[List[TimelineEvent]] = None
    ) -> List[Commitment]:
        """Track commitments and promises.

        Args:
            account_id: Account identifier
            timeline_events: Timeline events (fetched if not provided)

        Returns:
            List of tracked commitments
        """
        self.logger.info("tracking_commitments", account_id=account_id)

        try:
            if timeline_events is None:
                timeline_raw = await self.cognee.get_account_timeline(account_id, limit=50)
                timeline_events = self._build_timeline_events(account_id, timeline_raw)

            commitments: List[Commitment] = []

            # Extract commitments from events
            commitment_keywords = ['promised', 'committed', 'will deliver', 'agreed to']

            for event in timeline_events:
                description_lower = event.description.lower()
                is_commitment = any(kw in description_lower for kw in commitment_keywords)

                if is_commitment:
                    commitment = Commitment(
                        commitment_id=f"{event.event_id}_commitment",
                        account_id=account_id,
                        commitment_text=event.description,
                        committed_by=event.participants[0] if event.participants else "unknown",
                        committed_to=event.participants[1] if len(event.participants) > 1 else "customer",
                        commitment_date=event.timestamp,
                        due_date=event.metadata.get('due_date'),
                        status=CommitmentStatus(event.metadata.get('status', 'pending')),
                        completion_date=event.metadata.get('completion_date'),
                        priority=event.impact
                    )
                    commitments.append(commitment)

            self.logger.info(
                "commitments_tracked",
                account_id=account_id,
                commitment_count=len(commitments)
            )

            return commitments

        except Exception as e:
            self.logger.error(
                "commitment_tracking_failed",
                account_id=account_id,
                error=str(e)
            )
            return []

    # Helper methods

    def _build_timeline_events(
        self,
        account_id: str,
        timeline_raw: List[Dict[str, Any]]
    ) -> List[TimelineEvent]:
        """Build TimelineEvent objects from raw data."""
        events: List[TimelineEvent] = []

        for item in timeline_raw:
            try:
                event = TimelineEvent(
                    event_id=item.get('interaction_id', f"event_{len(events)}"),
                    account_id=account_id,
                    timestamp=datetime.fromisoformat(
                        item.get('timestamp', datetime.utcnow().isoformat())
                    ),
                    event_type=EventType(item.get('type', 'note')),
                    description=item.get('summary', ''),
                    participants=item.get('participants', []),
                    metadata=item.get('metadata', {})
                )
                events.append(event)
            except Exception as e:
                self.logger.warning("failed_to_parse_event", error=str(e))
                continue

        return events

    def _extract_key_events(
        self,
        timeline_events: List[TimelineEvent]
    ) -> List[KeyEvent]:
        """Extract key events from timeline."""
        key_events: List[KeyEvent] = []

        high_impact = [e for e in timeline_events if e.impact == 'high']

        for event in high_impact[:10]:  # Limit to top 10
            key_event = KeyEvent(
                event_id=event.event_id,
                account_id=event.account_id,
                event_date=event.timestamp,
                event_type=event.event_type.value,
                title=event.description[:100],
                description=event.description,
                impact_level=event.impact,
                stakeholders=event.participants,
                outcome=event.outcome
            )
            key_events.append(key_event)

        return key_events

    async def _get_prior_recommendations(
        self,
        account_id: str,
        lookback_days: int
    ) -> List[PriorRecommendation]:
        """Retrieve prior recommendations from memory."""
        try:
            # Query Cognee for prior recommendations
            search_result = await self.cognee.search_accounts(
                f"recommendations for account {account_id}",
                limit=20
            )

            recommendations: List[PriorRecommendation] = []

            # Parse results (simplified - would integrate with recommendation storage)
            cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

            for result in search_result:
                metadata = result.get('metadata', {})
                generated_date = metadata.get('generated_date')

                if generated_date:
                    gen_dt = datetime.fromisoformat(generated_date)
                    if gen_dt >= cutoff_date:
                        rec = PriorRecommendation(
                            recommendation_id=metadata.get('recommendation_id', 'unknown'),
                            account_id=account_id,
                            generated_date=gen_dt,
                            recommendation=metadata.get('recommendation', ''),
                            priority=metadata.get('priority', 'medium'),
                            action_type=metadata.get('action_type', 'follow_up'),
                            status=metadata.get('status', 'pending'),
                            outcome=metadata.get('outcome')
                        )
                        recommendations.append(rec)

            return recommendations

        except Exception as e:
            self.logger.error(
                "prior_recommendations_retrieval_failed",
                error=str(e)
            )
            return []

    def _build_engagement_metrics(
        self,
        account_id: str,
        timeline_events: List[TimelineEvent],
        period_days: int
    ) -> EngagementMetrics:
        """Build engagement metrics from timeline."""
        cutoff = datetime.utcnow() - timedelta(days=period_days)
        period_events = [e for e in timeline_events if e.timestamp >= cutoff]

        meetings = len([e for e in period_events if e.event_type == EventType.MEETING])
        emails = len([e for e in period_events if e.event_type == EventType.EMAIL])
        calls = len([e for e in period_events if e.event_type == EventType.CALL])

        frequency_score = min(1.0, len(period_events) / (period_days / 7))  # Target: 1/week
        quality_score = 0.7  # Placeholder - would analyze interaction quality

        return EngagementMetrics(
            account_id=account_id,
            measurement_period_days=period_days,
            total_interactions=len(period_events),
            meetings_count=meetings,
            emails_count=emails,
            calls_count=calls,
            interaction_frequency_score=frequency_score,
            quality_score=quality_score,
            trend="stable"
        )

    def _calculate_risk_level(
        self,
        sentiment: SentimentAnalysis,
        relationship: RelationshipAssessment,
        patterns: List[Pattern]
    ) -> RiskLevel:
        """Calculate overall risk level."""
        risk_score = 0

        # Sentiment factors
        if sentiment.trend == SentimentTrend.DECLINING:
            risk_score += 30
        if sentiment.overall_sentiment < -0.3:
            risk_score += 20

        # Relationship factors
        if relationship.relationship_strength == RelationshipStrength.AT_RISK:
            risk_score += 40
        elif relationship.relationship_strength == RelationshipStrength.WEAK:
            risk_score += 25

        # Pattern factors
        churn_patterns = [p for p in patterns if p.pattern_type == PatternType.CHURN_RISK]
        risk_score += len(churn_patterns) * 15

        # Classify
        if risk_score >= 70:
            return RiskLevel.CRITICAL
        elif risk_score >= 50:
            return RiskLevel.HIGH
        elif risk_score >= 30:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _calculate_avg_sentiment(self, events: List[TimelineEvent]) -> float:
        """Calculate average sentiment from events."""
        sentiments = [e.metadata.get('sentiment', 0.0) for e in events]
        return sum(sentiments) / len(sentiments) if sentiments else 0.0

    def _calculate_days_since_last(self, interactions: List[Dict[str, Any]]) -> int:
        """Calculate days since last interaction."""
        if not interactions:
            return 90

        latest = max(
            interactions,
            key=lambda x: datetime.fromisoformat(x.get('timestamp', '2000-01-01'))
        )

        last_time = datetime.fromisoformat(latest.get('timestamp', '2000-01-01'))
        return (datetime.utcnow() - last_time).days

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self._metrics.copy()

    async def execute_with_events(
        self,
        context: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute historical analysis with AG UI event streaming.

        Emits tool calls for Cognee memory operations and streams results.

        Args:
            context: Execution context with account_id

        Yields:
            AG UI Protocol events
        """
        session_id = context.get("session_id", "default")
        emitter = AGUIEventEmitter(session_id=session_id)

        account_id = context.get("account_id")
        step = context.get("step", 2)
        lookback_days = context.get("lookback_days", 365)
        include_patterns = context.get("include_patterns", True)

        try:
            # Emit agent started
            yield emitter.emit_agent_started(
                agent="memory_analyst",
                step=step,
                task=f"Analyze historical context for account {account_id}"
            )

            # Stream progress message
            yield emitter.emit_agent_stream(
                agent="memory_analyst",
                content="Analyzing historical patterns and retrieving account context...",
                content_type="text"
            )

            # Tool call: Query Cognee for account context
            tool_call_id_1 = "cognee-get-context"
            yield emitter.emit_tool_call(
                tool_name="cognee_get_account_context",
                tool_args={"account_id": account_id},
                tool_call_id=tool_call_id_1
            )

            # Execute historical context retrieval
            historical_context = await self.get_historical_context(
                account_id=account_id,
                lookback_days=lookback_days,
                include_patterns=include_patterns
            )

            # Emit tool result
            yield emitter.emit_tool_result(
                tool_call_id=tool_call_id_1,
                tool_name="cognee_get_account_context",
                result={
                    "account_id": account_id,
                    "key_events_count": len(historical_context.key_events),
                    "sentiment_trend": historical_context.sentiment_trend.value,
                    "relationship_strength": historical_context.relationship_strength.value,
                    "risk_level": historical_context.risk_level.value,
                    "patterns_detected": len(historical_context.patterns)
                },
                success=True
            )

            # Stream analysis results
            yield emitter.emit_agent_stream(
                agent="memory_analyst",
                content=f"Found {len(historical_context.key_events)} key events, "
                        f"{len(historical_context.patterns)} patterns detected. "
                        f"Sentiment trend: {historical_context.sentiment_trend.value}",
                content_type="text"
            )

            # If patterns detected, emit another tool call
            if historical_context.patterns:
                tool_call_id_2 = "cognee-pattern-analysis"
                yield emitter.emit_tool_call(
                    tool_name="cognee_analyze_patterns",
                    tool_args={
                        "account_id": account_id,
                        "pattern_types": [p.pattern_type.value for p in historical_context.patterns]
                    },
                    tool_call_id=tool_call_id_2
                )

                # Emit pattern analysis result
                yield emitter.emit_tool_result(
                    tool_call_id=tool_call_id_2,
                    tool_name="cognee_analyze_patterns",
                    result={
                        "patterns": [
                            {
                                "type": p.pattern_type.value,
                                "confidence": p.confidence,
                                "description": p.description
                            }
                            for p in historical_context.patterns[:5]  # Top 5 patterns
                        ]
                    },
                    success=True
                )

            # Store in context for next agent
            context["historical_context"] = historical_context

            # Emit agent completed
            yield emitter.emit_agent_completed(
                agent="memory_analyst",
                step=step,
                output={
                    "account_id": account_id,
                    "risk_level": historical_context.risk_level.value,
                    "sentiment_trend": historical_context.sentiment_trend.value,
                    "relationship_strength": historical_context.relationship_strength.value,
                    "key_events_count": len(historical_context.key_events),
                    "patterns_count": len(historical_context.patterns)
                }
            )

        except Exception as e:
            self.logger.error("memory_analyst_execution_error", error=str(e))
            yield emitter.emit_agent_error(
                agent="memory_analyst",
                step=step,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise
