"""RecommendationAuthor agent - generates actionable account recommendations.

Part of Week 6: Recommendation Author Implementation.
Follows SPARC Refinement Phase specification (MASTER_SPARC_PLAN_V3.md lines 605-625).
"""

from typing import Dict, Any, List, AsyncGenerator
from datetime import datetime, timedelta
import structlog

from src.agents.base_agent import BaseAgent
from src.events.ag_ui_emitter import AGUIEventEmitter

logger = structlog.get_logger(__name__)


class RecommendationAuthor(BaseAgent):
    """Generates actionable account recommendations with confidence scoring.

    This agent analyzes account data and historical insights to generate
    data-driven recommendations across four categories:
    - Engagement: Maintaining customer contact and relationships
    - Expansion: Upsell and cross-sell opportunities
    - Retention: Contract renewal and churn prevention
    - Risk Mitigation: Addressing account health issues

    Each recommendation includes:
    - Confidence score (0-100) based on data quality
    - Priority level (critical, high, medium, low)
    - Estimated impact
    - Next steps for execution

    Example:
        author = RecommendationAuthor()
        context = {
            "account_data": {...},
            "historical_insights": [...]
        }
        async for event in author.execute_with_events(context):
            if event.get("type") == "agent_completed":
                recommendations = event.get("data", {}).get("output", {}).get("recommendations", [])
    """

    # Recommendation categories
    CATEGORY_ENGAGEMENT = "engagement"
    CATEGORY_EXPANSION = "expansion"
    CATEGORY_RETENTION = "retention"
    CATEGORY_RISK_MITIGATION = "risk_mitigation"

    # Priority levels
    PRIORITY_CRITICAL = "critical"
    PRIORITY_HIGH = "high"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_LOW = "low"

    # Thresholds
    ENGAGEMENT_THRESHOLD_DAYS = 30
    ENGAGEMENT_CRITICAL_DAYS = 60
    HEALTH_CRITICAL_THRESHOLD = 50
    HEALTH_EXPANSION_THRESHOLD = 70
    EXPANSION_REVENUE_THRESHOLD = 50000
    RENEWAL_WARNING_DAYS = 90

    def __init__(self):
        """Initialize RecommendationAuthor agent."""
        super().__init__(
            agent_id="recommendation-author",
            system_prompt=(
                "You are a RecommendationAuthor agent that generates actionable "
                "account recommendations based on data analysis. Your recommendations "
                "must be specific, data-driven, and include confidence scores."
            ),
            allowed_tools=[],  # This agent doesn't use external tools
            permission_mode="default"
        )

        self.logger.info("recommendation_author_initialized")

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy execute method - calls execute_with_events().

        Args:
            context: Execution context with account_data and historical_insights

        Returns:
            Dictionary with recommendations list
        """
        recommendations = []
        async for event in self.execute_with_events(context):
            if event.get("type") == "agent_completed":
                recommendations = event.get("data", {}).get("output", {}).get("recommendations", [])

        return {"recommendations": recommendations}

    async def execute_with_events(self, context: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate recommendations with AG UI event streaming.

        Args:
            context: Execution context containing:
                - account_data: Account metrics and information
                - historical_insights: Historical patterns and insights
                - session_id: Optional session identifier

        Yields:
            AG UI Protocol events documenting recommendation generation
        """
        # Initialize AG UI event emitter
        session_id = context.get("session_id", f"rec-{datetime.utcnow().isoformat()}")
        emitter = AGUIEventEmitter(session_id=session_id)

        try:
            # Emit agent started event
            yield emitter.emit_agent_started(
                agent="recommendation_author",
                step=3,  # Step 3 in workflow (after scout and analyst)
                task="Generate actionable account recommendations"
            )

            # Stream progress
            yield emitter.emit_agent_stream(
                agent="recommendation_author",
                content="Analyzing account data for recommendation opportunities..."
            )

            # Extract input data
            account_data = context.get("account_data", {})
            historical_insights = context.get("historical_insights", [])

            if not account_data:
                raise ValueError("account_data is required in context")

            # Generate recommendations
            self.logger.info(
                "generating_recommendations",
                account_id=account_data.get("account_id"),
                insights_count=len(historical_insights)
            )

            recommendations = await self._generate_recommendations(
                account_data,
                historical_insights,
                emitter
            )

            # Stream each recommendation
            for i, rec in enumerate(recommendations, 1):
                yield emitter.emit_agent_stream(
                    agent="recommendation_author",
                    content=(
                        f"✓ {rec['title']} "
                        f"(confidence: {rec['confidence_score']}%, "
                        f"priority: {rec['priority']})"
                    )
                )

            # Store recommendations in context
            context["recommendations"] = recommendations

            self.logger.info(
                "recommendations_generated",
                count=len(recommendations),
                account_id=account_data.get("account_id")
            )

            # Emit agent completed event
            yield emitter.emit_agent_completed(
                agent="recommendation_author",
                step=3,
                output={"recommendations": recommendations}
            )

        except Exception as e:
            self.logger.error(
                "recommendation_generation_error",
                error=str(e),
                account_id=context.get("account_data", {}).get("account_id")
            )

            yield emitter.emit_agent_error(
                agent="recommendation_author",
                step=3,
                error_type="RecommendationGenerationError",
                error_message=str(e)
            )

            raise

    async def _generate_recommendations(
        self,
        account_data: Dict[str, Any],
        historical_insights: List[Dict[str, Any]],
        emitter: AGUIEventEmitter
    ) -> List[Dict[str, Any]]:
        """Generate data-driven recommendations based on account analysis.

        Args:
            account_data: Account metrics and information
            historical_insights: Historical patterns from MemoryAnalyst
            emitter: Event emitter for progress streaming

        Returns:
            List of recommendation dictionaries with confidence scores
        """
        recommendations = []

        # Extract key metrics
        account_id = account_data.get("account_id", "unknown")
        last_engagement_days = self._get_days_since_last_engagement(account_data)
        account_health = account_data.get("health_score", 50)
        revenue = account_data.get("annual_revenue", 0)
        contract_expiry_days = self._get_days_until_contract_expiry(account_data)

        # Generate engagement recommendations
        engagement_rec = self._generate_engagement_recommendation(
            account_id,
            last_engagement_days,
            account_data
        )
        if engagement_rec:
            recommendations.append(engagement_rec)

        # Generate expansion recommendations
        expansion_rec = self._generate_expansion_recommendation(
            account_id,
            account_health,
            revenue,
            account_data
        )
        if expansion_rec:
            recommendations.append(expansion_rec)

        # Generate risk mitigation recommendations
        risk_rec = self._generate_risk_recommendation(
            account_id,
            account_health,
            account_data
        )
        if risk_rec:
            recommendations.append(risk_rec)

        # Generate retention recommendations
        retention_rec = self._generate_retention_recommendation(
            account_id,
            contract_expiry_days,
            account_data
        )
        if retention_rec:
            recommendations.append(retention_rec)

        # Incorporate historical insights
        if historical_insights:
            insight_rec = self._generate_insight_based_recommendation(
                account_id,
                historical_insights,
                account_data
            )
            if insight_rec:
                recommendations.append(insight_rec)

        return recommendations

    def _generate_engagement_recommendation(
        self,
        account_id: str,
        days_since_engagement: int,
        account_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate engagement recommendation if needed."""
        if days_since_engagement < self.ENGAGEMENT_THRESHOLD_DAYS:
            return None

        is_critical = days_since_engagement > self.ENGAGEMENT_CRITICAL_DAYS

        return {
            "recommendation_id": f"{account_id}-eng-001",
            "account_id": account_id,
            "category": self.CATEGORY_ENGAGEMENT,
            "title": "Schedule Executive Business Review",
            "description": (
                f"Account has not been contacted in {days_since_engagement} days. "
                "Schedule EBR to maintain relationship and discuss business outcomes."
            ),
            "rationale": (
                f"Last engagement was {days_since_engagement} days ago, "
                f"exceeding {self.ENGAGEMENT_THRESHOLD_DAYS}-day threshold. "
                "Regular touchpoints are critical for relationship health."
            ),
            "confidence_score": self._calculate_confidence(
                data_recency=100 - min(days_since_engagement, 100),
                pattern_strength=80,
                data_completeness=90
            ),
            "priority": self.PRIORITY_CRITICAL if is_critical else self.PRIORITY_HIGH,
            "estimated_impact": (
                "Reduce churn risk by 25%" if is_critical
                else "Maintain relationship momentum"
            ),
            "next_steps": [
                "Review account history and recent activity",
                "Prepare executive summary with key metrics",
                "Send EBR invitation with proposed agenda",
                "Coordinate with CSM for stakeholder alignment"
            ],
            "created_at": datetime.utcnow().isoformat()
        }

    def _generate_expansion_recommendation(
        self,
        account_id: str,
        health_score: int,
        revenue: float,
        account_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate expansion recommendation if account is healthy."""
        if health_score < self.HEALTH_EXPANSION_THRESHOLD or revenue < self.EXPANSION_REVENUE_THRESHOLD:
            return None

        expansion_potential = revenue * 0.3

        return {
            "recommendation_id": f"{account_id}-exp-001",
            "account_id": account_id,
            "category": self.CATEGORY_EXPANSION,
            "title": "Present Upsell Opportunity",
            "description": (
                "Account is healthy and engaged. Present advanced features "
                "or additional licenses to drive expansion revenue."
            ),
            "rationale": (
                f"Health score of {health_score}% indicates strong satisfaction "
                "and readiness for expansion conversation. Current revenue level "
                f"(${revenue:,.0f}) suggests expansion capacity."
            ),
            "confidence_score": self._calculate_confidence(
                data_recency=90,
                pattern_strength=health_score,
                data_completeness=85
            ),
            "priority": self.PRIORITY_MEDIUM,
            "estimated_impact": f"Potential revenue increase of ${expansion_potential:,.0f}",
            "next_steps": [
                "Identify feature usage gaps and opportunities",
                "Prepare ROI presentation with customer success stories",
                "Schedule demo of advanced features",
                "Develop customized expansion proposal"
            ],
            "created_at": datetime.utcnow().isoformat()
        }

    def _generate_risk_recommendation(
        self,
        account_id: str,
        health_score: int,
        account_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate risk mitigation recommendation if health is poor."""
        if health_score >= self.HEALTH_CRITICAL_THRESHOLD:
            return None

        return {
            "recommendation_id": f"{account_id}-risk-001",
            "account_id": account_id,
            "category": self.CATEGORY_RISK_MITIGATION,
            "title": "Initiate Churn Prevention Protocol",
            "description": (
                "Account health is below critical threshold. "
                "Immediate intervention required to prevent churn."
            ),
            "rationale": (
                f"Health score of {health_score}% indicates high churn risk. "
                "Proactive intervention can improve retention probability by 60%."
            ),
            "confidence_score": self._calculate_confidence(
                data_recency=95,
                pattern_strength=100 - health_score,
                data_completeness=80
            ),
            "priority": self.PRIORITY_CRITICAL,
            "estimated_impact": "Prevent potential revenue loss and improve retention",
            "next_steps": [
                "Schedule immediate call with account owner",
                "Review all support tickets and pain points",
                "Prepare comprehensive recovery action plan",
                "Escalate to executive sponsor if needed"
            ],
            "created_at": datetime.utcnow().isoformat()
        }

    def _generate_retention_recommendation(
        self,
        account_id: str,
        days_until_expiry: int,
        account_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate retention recommendation based on contract timing."""
        if days_until_expiry <= 0 or days_until_expiry > self.RENEWAL_WARNING_DAYS:
            return None

        return {
            "recommendation_id": f"{account_id}-ret-001",
            "account_id": account_id,
            "category": self.CATEGORY_RETENTION,
            "title": "Initiate Renewal Discussion",
            "description": (
                f"Contract expires in {days_until_expiry} days. "
                "Begin renewal conversation to secure continuation."
            ),
            "rationale": (
                "Proactive renewal discussion 60-90 days before expiry "
                "improves retention and provides time for negotiation."
            ),
            "confidence_score": self._calculate_confidence(
                data_recency=100,
                pattern_strength=85,
                data_completeness=95
            ),
            "priority": self.PRIORITY_HIGH,
            "estimated_impact": "Increase renewal probability by 40%",
            "next_steps": [
                "Prepare renewal proposal with usage metrics",
                "Review pricing and contract terms",
                "Schedule renewal discussion meeting",
                "Identify and address any renewal blockers"
            ],
            "created_at": datetime.utcnow().isoformat()
        }

    def _generate_insight_based_recommendation(
        self,
        account_id: str,
        insights: List[Dict[str, Any]],
        account_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate recommendation based on historical insights."""
        if not insights:
            return None

        # Find most relevant insight
        sorted_insights = sorted(
            insights,
            key=lambda x: x.get("confidence_score", 0),
            reverse=True
        )

        top_insight = sorted_insights[0]

        return {
            "recommendation_id": f"{account_id}-ins-001",
            "account_id": account_id,
            "category": "data_driven",
            "title": f"Act on Pattern: {top_insight.get('pattern_type', 'Unknown')}",
            "description": (
                f"Historical analysis identified: {top_insight.get('insight', 'Pattern detected')}. "
                "Take action based on this recurring pattern."
            ),
            "rationale": (
                f"Pattern detected with {top_insight.get('confidence_score', 0)}% confidence "
                f"based on {top_insight.get('occurrence_count', 0)} similar cases."
            ),
            "confidence_score": top_insight.get("confidence_score", 50),
            "priority": self.PRIORITY_MEDIUM,
            "estimated_impact": "Leverage proven successful pattern",
            "next_steps": [
                "Review historical context and outcomes",
                "Adapt proven approach to current situation",
                "Monitor results against historical benchmarks"
            ],
            "created_at": datetime.utcnow().isoformat()
        }

    def _calculate_confidence(
        self,
        data_recency: int,
        pattern_strength: int,
        data_completeness: int
    ) -> int:
        """Calculate confidence score (0-100) for recommendation.

        Args:
            data_recency: How recent/fresh the data is (0-100)
            pattern_strength: Strength of the pattern/signal (0-100)
            data_completeness: Completeness of available data (0-100)

        Returns:
            Confidence score as integer (0-100)
        """
        # Weighted average: recency 30%, pattern 40%, completeness 30%
        confidence = (
            data_recency * 0.3 +
            pattern_strength * 0.4 +
            data_completeness * 0.3
        )
        return int(min(max(confidence, 0), 100))

    def _get_days_since_last_engagement(self, account_data: Dict[str, Any]) -> int:
        """Calculate days since last engagement.

        Args:
            account_data: Account information

        Returns:
            Number of days since last engagement
        """
        last_activity_date = account_data.get("last_activity_date")

        if not last_activity_date:
            # No activity date recorded - assume very old
            return 999

        try:
            # Parse ISO format date
            if isinstance(last_activity_date, str):
                last_date = datetime.fromisoformat(last_activity_date.replace("Z", "+00:00"))
            elif isinstance(last_activity_date, datetime):
                last_date = last_activity_date
            else:
                return 999

            # Calculate difference
            delta = datetime.utcnow() - last_date.replace(tzinfo=None)
            return delta.days

        except Exception as e:
            self.logger.warning(
                "date_parse_error",
                error=str(e),
                date_value=last_activity_date
            )
            return 999

    def _get_days_until_contract_expiry(self, account_data: Dict[str, Any]) -> int:
        """Calculate days until contract expiry.

        Args:
            account_data: Account information

        Returns:
            Number of days until contract expires (-1 if unknown)
        """
        contract_end_date = account_data.get("contract_end_date")

        if not contract_end_date:
            return -1

        try:
            # Parse ISO format date
            if isinstance(contract_end_date, str):
                end_date = datetime.fromisoformat(contract_end_date.replace("Z", "+00:00"))
            elif isinstance(contract_end_date, datetime):
                end_date = contract_end_date
            else:
                return -1

            # Calculate difference
            delta = end_date.replace(tzinfo=None) - datetime.utcnow()
            return delta.days

        except Exception as e:
            self.logger.warning(
                "date_parse_error",
                error=str(e),
                date_value=contract_end_date
            )
            return -1
