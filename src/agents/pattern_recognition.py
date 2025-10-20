"""Advanced pattern recognition for account analysis.

Detects sophisticated patterns including:
- Churn risk indicators
- Upsell opportunities
- Renewal risks
- Engagement anomalies
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import structlog

from src.agents.memory_models import (
    Pattern, PatternType, TimelineEvent, EventType,
    SentimentTrend, RiskLevel
)

logger = structlog.get_logger(__name__)


class PatternRecognizer:
    """Advanced pattern recognition engine.

    Uses configurable thresholds and multiple detection algorithms
    to identify account patterns for ML-ready feature extraction.
    """

    def __init__(
        self,
        churn_threshold: float = 0.7,
        upsell_threshold: float = 0.6,
        renewal_risk_threshold: float = 0.65
    ):
        """Initialize pattern recognizer.

        Args:
            churn_threshold: Confidence threshold for churn patterns
            upsell_threshold: Confidence threshold for upsell patterns
            renewal_risk_threshold: Confidence threshold for renewal risk
        """
        self.churn_threshold = churn_threshold
        self.upsell_threshold = upsell_threshold
        self.renewal_risk_threshold = renewal_risk_threshold
        self.logger = logger.bind(component="pattern_recognizer")

    def detect_churn_risk_patterns(
        self,
        account_id: str,
        events: List[TimelineEvent],
        engagement_data: Dict[str, Any]
    ) -> List[Pattern]:
        """Detect churn risk patterns.

        Patterns detected:
        1. Engagement drop (>50% reduction)
        2. Executive sponsor changes (multiple in 6 months)
        3. Deal stalls (>45 days no movement)
        4. Sentiment decline (negative trend)
        5. Missed meetings (>2 in month)

        Args:
            account_id: Account identifier
            events: Timeline events
            engagement_data: Engagement metrics

        Returns:
            List of churn risk patterns
        """
        patterns: List[Pattern] = []
        now = datetime.utcnow()

        # Pattern 1: Engagement drop
        engagement_pattern = self._detect_engagement_drop(
            account_id, events, engagement_data, now
        )
        if engagement_pattern:
            patterns.append(engagement_pattern)

        # Pattern 2: Executive changes
        exec_pattern = self._detect_executive_changes(account_id, events, now)
        if exec_pattern:
            patterns.append(exec_pattern)

        # Pattern 3: Deal stalls
        deal_patterns = self._detect_deal_stalls(account_id, events, now)
        patterns.extend(deal_patterns)

        # Pattern 4: Sentiment decline
        sentiment_pattern = self._detect_sentiment_decline(account_id, events, now)
        if sentiment_pattern:
            patterns.append(sentiment_pattern)

        # Pattern 5: Missed meetings
        meeting_pattern = self._detect_missed_meetings(account_id, events, now)
        if meeting_pattern:
            patterns.append(meeting_pattern)

        self.logger.info(
            "churn_patterns_detected",
            account_id=account_id,
            pattern_count=len(patterns)
        )

        return patterns

    def detect_upsell_opportunities(
        self,
        account_id: str,
        events: List[TimelineEvent],
        usage_data: Dict[str, Any]
    ) -> List[Pattern]:
        """Detect upsell opportunity patterns.

        Patterns detected:
        1. Usage growth (>30% increase)
        2. Feature adoption (new features used)
        3. Expansion signals (mentions of growth)
        4. Positive sentiment + high engagement
        5. Executive alignment

        Args:
            account_id: Account identifier
            events: Timeline events
            usage_data: Product usage data

        Returns:
            List of upsell opportunity patterns
        """
        patterns: List[Pattern] = []
        now = datetime.utcnow()

        # Pattern 1: Usage growth
        usage_pattern = self._detect_usage_growth(account_id, usage_data, now)
        if usage_pattern:
            patterns.append(usage_pattern)

        # Pattern 2: Feature adoption
        adoption_pattern = self._detect_feature_adoption(account_id, events, now)
        if adoption_pattern:
            patterns.append(adoption_pattern)

        # Pattern 3: Expansion signals
        expansion_patterns = self._detect_expansion_signals(account_id, events, now)
        patterns.extend(expansion_patterns)

        # Pattern 4: High engagement + positive sentiment
        engagement_pattern = self._detect_positive_engagement(account_id, events, now)
        if engagement_pattern:
            patterns.append(engagement_pattern)

        self.logger.info(
            "upsell_patterns_detected",
            account_id=account_id,
            pattern_count=len(patterns)
        )

        return patterns

    def detect_renewal_risk_patterns(
        self,
        account_id: str,
        events: List[TimelineEvent],
        contract_data: Dict[str, Any]
    ) -> List[Pattern]:
        """Detect renewal risk patterns.

        Patterns detected:
        1. Commitment gaps (unfulfilled promises)
        2. Sentiment decline near renewal
        3. Budget concerns mentioned
        4. Competitive mentions
        5. Low engagement in renewal period

        Args:
            account_id: Account identifier
            events: Timeline events
            contract_data: Contract and renewal data

        Returns:
            List of renewal risk patterns
        """
        patterns: List[Pattern] = []
        now = datetime.utcnow()

        renewal_date = contract_data.get('renewal_date')
        if not renewal_date:
            return patterns

        renewal_dt = datetime.fromisoformat(renewal_date) if isinstance(
            renewal_date, str
        ) else renewal_date

        days_to_renewal = (renewal_dt - now).days

        # Only analyze if within renewal window (90 days)
        if days_to_renewal > 90:
            return patterns

        # Pattern 1: Commitment gaps
        commitment_pattern = self._detect_commitment_gaps(
            account_id, events, now, renewal_dt
        )
        if commitment_pattern:
            patterns.append(commitment_pattern)

        # Pattern 2: Sentiment decline
        sentiment_pattern = self._detect_renewal_sentiment_decline(
            account_id, events, now, days_to_renewal
        )
        if sentiment_pattern:
            patterns.append(sentiment_pattern)

        # Pattern 3: Budget concerns
        budget_pattern = self._detect_budget_concerns(account_id, events, now)
        if budget_pattern:
            patterns.append(budget_pattern)

        # Pattern 4: Competitive mentions
        competitive_pattern = self._detect_competitive_mentions(account_id, events, now)
        if competitive_pattern:
            patterns.append(competitive_pattern)

        # Pattern 5: Low engagement
        engagement_pattern = self._detect_renewal_low_engagement(
            account_id, events, now, days_to_renewal
        )
        if engagement_pattern:
            patterns.append(engagement_pattern)

        self.logger.info(
            "renewal_risk_patterns_detected",
            account_id=account_id,
            pattern_count=len(patterns),
            days_to_renewal=days_to_renewal
        )

        return patterns

    # Private helper methods for churn detection

    def _detect_engagement_drop(
        self,
        account_id: str,
        events: List[TimelineEvent],
        engagement_data: Dict[str, Any],
        now: datetime
    ) -> Optional[Pattern]:
        """Detect significant engagement drop."""
        recent_events = [e for e in events if (now - e.timestamp).days <= 30]
        historical_events = [e for e in events if 30 < (now - e.timestamp).days <= 90]

        if not historical_events:
            return None

        recent_rate = len(recent_events) / 30
        historical_rate = len(historical_events) / 60

        if historical_rate == 0:
            return None

        drop_percentage = (1 - recent_rate / historical_rate) * 100

        if drop_percentage >= 50:
            return Pattern(
                pattern_id=f"churn_engagement_drop_{account_id}_{now.timestamp()}",
                pattern_type=PatternType.CHURN_RISK,
                confidence=min(0.95, 0.5 + (drop_percentage / 100)),
                description=f"Engagement dropped {drop_percentage:.1f}% in last 30 days",
                evidence=[
                    f"Recent: {recent_rate:.2f} events/day",
                    f"Historical: {historical_rate:.2f} events/day",
                    f"Drop: {drop_percentage:.1f}%"
                ],
                first_detected=now - timedelta(days=30),
                last_detected=now,
                frequency=1,
                risk_score=min(100, int(drop_percentage)),
                recommendations=[
                    "Schedule urgent check-in call within 48 hours",
                    "Review recent interactions for root cause",
                    "Engage executive sponsor immediately"
                ]
            )

        return None

    def _detect_executive_changes(
        self,
        account_id: str,
        events: List[TimelineEvent],
        now: datetime
    ) -> Optional[Pattern]:
        """Detect executive sponsor changes."""
        exec_changes = [e for e in events if e.event_type == EventType.EXECUTIVE_CHANGE]

        recent_changes = [e for e in exec_changes if (now - e.timestamp).days <= 180]

        if len(recent_changes) >= 2:
            return Pattern(
                pattern_id=f"churn_exec_change_{account_id}_{now.timestamp()}",
                pattern_type=PatternType.EXECUTIVE_CHANGE,
                confidence=0.8,
                description=f"{len(recent_changes)} executive changes in 6 months",
                evidence=[
                    f"Most recent: {recent_changes[-1].timestamp.date()}",
                    f"Total in 6 months: {len(recent_changes)}"
                ],
                first_detected=recent_changes[0].timestamp,
                last_detected=recent_changes[-1].timestamp,
                frequency=len(recent_changes),
                risk_score=60 + (len(recent_changes) * 10),
                recommendations=[
                    "Rebuild relationship with new executives",
                    "Schedule introduction meetings",
                    "Review and update account strategy"
                ]
            )

        return None

    def _detect_deal_stalls(
        self,
        account_id: str,
        events: List[TimelineEvent],
        now: datetime
    ) -> List[Pattern]:
        """Detect stalled deals."""
        patterns: List[Pattern] = []

        deal_updates = [e for e in events if e.event_type == EventType.DEAL_UPDATE]

        # Group by deal
        deals_by_id = defaultdict(list)
        for event in deal_updates:
            deal_id = event.metadata.get('deal_id', 'unknown')
            deals_by_id[deal_id].append(event)

        for deal_id, deal_events in deals_by_id.items():
            if not deal_events:
                continue

            # Sort by timestamp
            deal_events.sort(key=lambda x: x.timestamp)
            last_update = deal_events[-1]

            days_stalled = (now - last_update.timestamp).days

            if days_stalled >= 45:
                patterns.append(Pattern(
                    pattern_id=f"deal_stall_{account_id}_{deal_id}_{now.timestamp()}",
                    pattern_type=PatternType.DEAL_STALL,
                    confidence=0.75,
                    description=f"Deal {deal_id} stalled for {days_stalled} days",
                    evidence=[
                        f"Last update: {last_update.timestamp.date()}",
                        f"Days stalled: {days_stalled}",
                        f"Stage: {last_update.metadata.get('stage', 'unknown')}"
                    ],
                    first_detected=last_update.timestamp,
                    last_detected=now,
                    frequency=1,
                    risk_score=min(100, 50 + days_stalled // 2),
                    recommendations=[
                        "Schedule stakeholder meeting to unblock",
                        "Review deal requirements and timeline",
                        "Consider executive escalation"
                    ]
                ))

        return patterns

    def _detect_sentiment_decline(
        self,
        account_id: str,
        events: List[TimelineEvent],
        now: datetime
    ) -> Optional[Pattern]:
        """Detect sentiment decline."""
        sentiment_events = [e for e in events if e.metadata.get('sentiment')]

        if len(sentiment_events) < 5:
            return None

        # Sort by timestamp
        sentiment_events.sort(key=lambda x: x.timestamp)

        # Split into periods
        midpoint = len(sentiment_events) // 2
        historical = sentiment_events[:midpoint]
        recent = sentiment_events[midpoint:]

        historical_avg = sum(
            e.metadata.get('sentiment', 0) for e in historical
        ) / len(historical)

        recent_avg = sum(
            e.metadata.get('sentiment', 0) for e in recent
        ) / len(recent)

        decline = historical_avg - recent_avg

        if decline >= 0.3:  # Significant decline
            return Pattern(
                pattern_id=f"sentiment_decline_{account_id}_{now.timestamp()}",
                pattern_type=PatternType.CHURN_RISK,
                confidence=0.7,
                description="Sentiment declining in recent communications",
                evidence=[
                    f"Historical sentiment: {historical_avg:.2f}",
                    f"Recent sentiment: {recent_avg:.2f}",
                    f"Decline: {decline:.2f}"
                ],
                first_detected=recent[0].timestamp,
                last_detected=now,
                frequency=1,
                risk_score=min(100, int(decline * 100)),
                recommendations=[
                    "Address concerns immediately",
                    "Review recent interactions for issues",
                    "Consider satisfaction survey"
                ]
            )

        return None

    def _detect_missed_meetings(
        self,
        account_id: str,
        events: List[TimelineEvent],
        now: datetime
    ) -> Optional[Pattern]:
        """Detect pattern of missed meetings."""
        meetings = [e for e in events if e.event_type == EventType.MEETING]
        recent_meetings = [m for m in meetings if (now - m.timestamp).days <= 30]

        missed = [m for m in recent_meetings if m.outcome and 'cancelled' in m.outcome.lower()]

        if len(missed) >= 2:
            return Pattern(
                pattern_id=f"missed_meetings_{account_id}_{now.timestamp()}",
                pattern_type=PatternType.CHURN_RISK,
                confidence=0.65,
                description=f"{len(missed)} missed/cancelled meetings in last 30 days",
                evidence=[
                    f"Missed meetings: {len(missed)}",
                    f"Total meetings: {len(recent_meetings)}"
                ],
                first_detected=missed[0].timestamp,
                last_detected=missed[-1].timestamp,
                frequency=len(missed),
                risk_score=50 + (len(missed) * 10),
                recommendations=[
                    "Reach out to understand availability issues",
                    "Offer flexible meeting times",
                    "Consider asynchronous communication"
                ]
            )

        return None

    # Upsell opportunity detection helpers

    def _detect_usage_growth(
        self,
        account_id: str,
        usage_data: Dict[str, Any],
        now: datetime
    ) -> Optional[Pattern]:
        """Detect usage growth pattern."""
        current_usage = usage_data.get('current_usage', 0)
        historical_usage = usage_data.get('historical_usage', 0)

        if historical_usage == 0:
            return None

        growth_rate = ((current_usage - historical_usage) / historical_usage) * 100

        if growth_rate >= 30:
            return Pattern(
                pattern_id=f"usage_growth_{account_id}_{now.timestamp()}",
                pattern_type=PatternType.UPSELL_OPPORTUNITY,
                confidence=0.7,
                description=f"Usage increased {growth_rate:.1f}% indicating expansion potential",
                evidence=[
                    f"Current usage: {current_usage}",
                    f"Historical usage: {historical_usage}",
                    f"Growth: {growth_rate:.1f}%"
                ],
                first_detected=now - timedelta(days=30),
                last_detected=now,
                frequency=1,
                risk_score=0,
                recommendations=[
                    "Discuss expansion plans",
                    "Present tier upgrade options",
                    "Highlight additional features"
                ]
            )

        return None

    def _detect_feature_adoption(
        self,
        account_id: str,
        events: List[TimelineEvent],
        now: datetime
    ) -> Optional[Pattern]:
        """Detect new feature adoption."""
        feature_events = [
            e for e in events
            if 'feature' in e.description.lower() and (now - e.timestamp).days <= 60
        ]

        if len(feature_events) >= 3:
            return Pattern(
                pattern_id=f"feature_adoption_{account_id}_{now.timestamp()}",
                pattern_type=PatternType.UPSELL_OPPORTUNITY,
                confidence=0.65,
                description="Actively exploring new features",
                evidence=[
                    f"Feature-related events: {len(feature_events)}",
                    f"Recent exploration: {feature_events[-1].timestamp.date()}"
                ],
                first_detected=feature_events[0].timestamp,
                last_detected=feature_events[-1].timestamp,
                frequency=len(feature_events),
                risk_score=0,
                recommendations=[
                    "Offer advanced feature training",
                    "Discuss premium tier benefits",
                    "Share relevant use cases"
                ]
            )

        return None

    def _detect_expansion_signals(
        self,
        account_id: str,
        events: List[TimelineEvent],
        now: datetime
    ) -> List[Pattern]:
        """Detect expansion signals in communications."""
        patterns: List[Pattern] = []

        expansion_keywords = ['expand', 'growth', 'scale', 'additional', 'more users']

        expansion_events = []
        for event in events:
            if any(keyword in event.description.lower() for keyword in expansion_keywords):
                if (now - event.timestamp).days <= 90:
                    expansion_events.append(event)

        if len(expansion_events) >= 2:
            patterns.append(Pattern(
                pattern_id=f"expansion_signals_{account_id}_{now.timestamp()}",
                pattern_type=PatternType.UPSELL_OPPORTUNITY,
                confidence=0.75,
                description="Multiple expansion signals detected",
                evidence=[
                    f"Expansion mentions: {len(expansion_events)}",
                    f"Most recent: {expansion_events[-1].timestamp.date()}"
                ],
                first_detected=expansion_events[0].timestamp,
                last_detected=expansion_events[-1].timestamp,
                frequency=len(expansion_events),
                risk_score=0,
                recommendations=[
                    "Proactively discuss expansion plans",
                    "Prepare expansion proposal",
                    "Schedule strategic planning session"
                ]
            ))

        return patterns

    def _detect_positive_engagement(
        self,
        account_id: str,
        events: List[TimelineEvent],
        now: datetime
    ) -> Optional[Pattern]:
        """Detect high engagement with positive sentiment."""
        recent_events = [e for e in events if (now - e.timestamp).days <= 30]

        if len(recent_events) < 5:
            return None

        positive_events = [
            e for e in recent_events
            if e.metadata.get('sentiment', 0) > 0.5
        ]

        if len(positive_events) / len(recent_events) >= 0.7:
            return Pattern(
                pattern_id=f"positive_engagement_{account_id}_{now.timestamp()}",
                pattern_type=PatternType.UPSELL_OPPORTUNITY,
                confidence=0.7,
                description="High engagement with positive sentiment",
                evidence=[
                    f"Total interactions: {len(recent_events)}",
                    f"Positive interactions: {len(positive_events)}",
                    f"Positivity rate: {len(positive_events)/len(recent_events)*100:.1f}%"
                ],
                first_detected=recent_events[0].timestamp,
                last_detected=now,
                frequency=1,
                risk_score=0,
                recommendations=[
                    "Capitalize on positive momentum",
                    "Request case study or testimonial",
                    "Ask for referrals"
                ]
            )

        return None

    # Renewal risk detection helpers

    def _detect_commitment_gaps(
        self,
        account_id: str,
        events: List[TimelineEvent],
        now: datetime,
        renewal_date: datetime
    ) -> Optional[Pattern]:
        """Detect unfulfilled commitments near renewal."""
        # This would ideally integrate with commitment tracking
        # For now, detect mentions of unfulfilled promises

        commitment_keywords = ['promised', 'committed', 'agreed to', 'will deliver']
        followup_keywords = ['delivered', 'completed', 'fulfilled']

        commitments = []
        fulfillments = []

        for event in events:
            if any(kw in event.description.lower() for kw in commitment_keywords):
                commitments.append(event)
            if any(kw in event.description.lower() for kw in followup_keywords):
                fulfillments.append(event)

        gap = len(commitments) - len(fulfillments)

        if gap >= 2:
            return Pattern(
                pattern_id=f"commitment_gaps_{account_id}_{now.timestamp()}",
                pattern_type=PatternType.RENEWAL_RISK,
                confidence=0.7,
                description=f"{gap} unfulfilled commitments detected",
                evidence=[
                    f"Commitments made: {len(commitments)}",
                    f"Fulfilled: {len(fulfillments)}",
                    f"Gap: {gap}"
                ],
                first_detected=commitments[0].timestamp if commitments else now,
                last_detected=now,
                frequency=1,
                risk_score=70,
                recommendations=[
                    "Review and fulfill outstanding commitments",
                    "Communicate progress on pending items",
                    "Reset expectations if needed"
                ]
            )

        return None

    def _detect_renewal_sentiment_decline(
        self,
        account_id: str,
        events: List[TimelineEvent],
        now: datetime,
        days_to_renewal: int
    ) -> Optional[Pattern]:
        """Detect sentiment decline during renewal period."""
        renewal_period_events = [
            e for e in events
            if e.metadata.get('sentiment') and (now - e.timestamp).days <= 60
        ]

        if len(renewal_period_events) < 3:
            return None

        avg_sentiment = sum(
            e.metadata.get('sentiment', 0) for e in renewal_period_events
        ) / len(renewal_period_events)

        if avg_sentiment < -0.2:  # Negative sentiment
            return Pattern(
                pattern_id=f"renewal_sentiment_{account_id}_{now.timestamp()}",
                pattern_type=PatternType.RENEWAL_RISK,
                confidence=0.75,
                description="Negative sentiment detected during renewal period",
                evidence=[
                    f"Days to renewal: {days_to_renewal}",
                    f"Average sentiment: {avg_sentiment:.2f}",
                    f"Sample size: {len(renewal_period_events)}"
                ],
                first_detected=renewal_period_events[0].timestamp,
                last_detected=now,
                frequency=1,
                risk_score=80,
                recommendations=[
                    "Address concerns before renewal discussion",
                    "Schedule satisfaction review",
                    "Prepare value demonstration"
                ]
            )

        return None

    def _detect_budget_concerns(
        self,
        account_id: str,
        events: List[TimelineEvent],
        now: datetime
    ) -> Optional[Pattern]:
        """Detect mentions of budget concerns."""
        budget_keywords = ['budget', 'cost', 'price', 'expensive', 'cheaper alternative']

        budget_events = []
        for event in events:
            if any(kw in event.description.lower() for kw in budget_keywords):
                if (now - event.timestamp).days <= 90:
                    budget_events.append(event)

        if len(budget_events) >= 2:
            return Pattern(
                pattern_id=f"budget_concerns_{account_id}_{now.timestamp()}",
                pattern_type=PatternType.RENEWAL_RISK,
                confidence=0.7,
                description="Budget concerns mentioned in discussions",
                evidence=[
                    f"Budget-related mentions: {len(budget_events)}",
                    f"Most recent: {budget_events[-1].timestamp.date()}"
                ],
                first_detected=budget_events[0].timestamp,
                last_detected=budget_events[-1].timestamp,
                frequency=len(budget_events),
                risk_score=65,
                recommendations=[
                    "Prepare ROI analysis",
                    "Discuss flexible pricing options",
                    "Demonstrate value delivered"
                ]
            )

        return None

    def _detect_competitive_mentions(
        self,
        account_id: str,
        events: List[TimelineEvent],
        now: datetime
    ) -> Optional[Pattern]:
        """Detect mentions of competitors."""
        competitive_keywords = ['competitor', 'alternative', 'considering', 'evaluating']

        competitive_events = []
        for event in events:
            if any(kw in event.description.lower() for kw in competitive_keywords):
                if (now - event.timestamp).days <= 60:
                    competitive_events.append(event)

        if competitive_events:
            return Pattern(
                pattern_id=f"competitive_risk_{account_id}_{now.timestamp()}",
                pattern_type=PatternType.RENEWAL_RISK,
                confidence=0.8,
                description="Competitive evaluation detected",
                evidence=[
                    f"Competitive mentions: {len(competitive_events)}",
                    f"Most recent: {competitive_events[-1].timestamp.date()}"
                ],
                first_detected=competitive_events[0].timestamp,
                last_detected=competitive_events[-1].timestamp,
                frequency=len(competitive_events),
                risk_score=75,
                recommendations=[
                    "Conduct competitive analysis",
                    "Highlight unique differentiators",
                    "Address specific competitive concerns"
                ]
            )

        return None

    def _detect_renewal_low_engagement(
        self,
        account_id: str,
        events: List[TimelineEvent],
        now: datetime,
        days_to_renewal: int
    ) -> Optional[Pattern]:
        """Detect low engagement during renewal period."""
        renewal_period_events = [
            e for e in events
            if (now - e.timestamp).days <= 60
        ]

        # Expected: at least 1 interaction per week
        expected_interactions = 60 / 7  # ~8-9
        actual_interactions = len(renewal_period_events)

        if actual_interactions < expected_interactions * 0.5:
            return Pattern(
                pattern_id=f"renewal_low_engagement_{account_id}_{now.timestamp()}",
                pattern_type=PatternType.RENEWAL_RISK,
                confidence=0.65,
                description="Low engagement during renewal period",
                evidence=[
                    f"Days to renewal: {days_to_renewal}",
                    f"Interactions in 60 days: {actual_interactions}",
                    f"Expected: ~{expected_interactions:.0f}"
                ],
                first_detected=now - timedelta(days=60),
                last_detected=now,
                frequency=1,
                risk_score=60,
                recommendations=[
                    "Increase touchpoint frequency",
                    "Schedule renewal discussion",
                    "Re-engage key stakeholders"
                ]
            )

        return None
