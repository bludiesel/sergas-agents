"""Memory service - central coordination for Cognee and agent memory.

Coordinates between:
- Cognee knowledge graph (historical context)
- Zoho Integration Manager (live data)
- Agent operations (memory access)
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

from src.integrations.cognee.cognee_client import CogneeClient
from src.integrations.zoho.integration_manager import ZohoIntegrationManager

logger = structlog.get_logger(__name__)


class MemoryService:
    """Central memory service for the agent system.

    Coordinates between Cognee knowledge graph and agent operations.
    Implements SPARC architecture memory layer.

    Key Responsibilities:
    - Account brief generation (SPARC PRD deliverable)
    - Memory synchronization
    - Agent action recording
    - Pattern-based recommendations

    Performance Targets (SPARC PRD):
    - Account brief generation: < 10 minutes
    - Context retrieval: < 200ms
    - Memory sync: Hourly incremental

    Example:
        >>> service = MemoryService(cognee_client, zoho_manager)
        >>> brief = await service.get_account_brief("account_123")
        >>> # Returns comprehensive brief in < 10 minutes
    """

    def __init__(
        self,
        cognee_client: CogneeClient,
        zoho_manager: ZohoIntegrationManager
    ):
        """Initialize memory service.

        Args:
            cognee_client: Cognee knowledge graph client
            zoho_manager: Zoho integration manager for live data
        """
        self.cognee = cognee_client
        self.zoho = zoho_manager
        self.logger = logger.bind(component="memory_service")

        self._sync_stats = {
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "last_sync": None
        }

    async def get_account_brief(
        self,
        account_id: str,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive account brief for account executive.

        This is the main deliverable from SPARC PRD:
        - Account overview with key metrics
        - Recent activity timeline
        - Health score and risk factors
        - Recommended next actions
        - Historical patterns and trends

        Target: < 10 minutes generation time (SPARC PRD metric)

        Args:
            account_id: Account identifier
            include_recommendations: Include AI-generated recommendations

        Returns:
            Comprehensive account brief
        """
        self.logger.info("generating_account_brief", account_id=account_id)
        start_time = datetime.utcnow()

        try:
            # Get fresh data from Zoho (Tier 1/2 routing)
            current_data = await self.zoho.get_account(account_id)

            # Get historical context from Cognee
            historical_context = await self.cognee.get_account_context(
                account_id,
                include_interactions=True,
                include_health_history=True
            )

            # Analyze health using memory patterns
            health_analysis = await self.cognee.analyze_account_health(account_id)

            # Get timeline of events
            timeline = await self.cognee.get_account_timeline(
                account_id,
                limit=20
            )

            # Combine into comprehensive brief
            brief = {
                "account_id": account_id,
                "account_name": current_data.get("Account_Name"),
                "current_data": current_data,
                "historical_context": historical_context,
                "health_analysis": health_analysis,
                "timeline": timeline,
                "generated_at": datetime.utcnow().isoformat(),
                "generation_time_seconds": (
                    datetime.utcnow() - start_time
                ).total_seconds()
            }

            if include_recommendations:
                # Basic recommendations (enhanced in Week 7 with Memory Analyst)
                brief["recommendations"] = await self._generate_recommendations(
                    account_id,
                    health_analysis
                )

            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.info(
                "account_brief_generated",
                account_id=account_id,
                duration_seconds=duration,
                within_target=duration < 600  # 10 minutes
            )

            return brief

        except Exception as e:
            self.logger.error(
                "account_brief_generation_failed",
                account_id=account_id,
                error=str(e)
            )
            raise

    async def sync_account_to_memory(
        self,
        account_id: str,
        force: bool = False
    ) -> bool:
        """Sync account from Zoho to Cognee memory.

        Args:
            account_id: Account to sync
            force: Force sync even if recently synced

        Returns:
            True if sync successful
        """
        self.logger.info("syncing_account", account_id=account_id, force=force)

        try:
            # Get current data from Zoho
            account_data = await self.zoho.get_account(account_id)

            # Store in Cognee
            await self.cognee.store_account_data(
                account_id=account_id,
                account_data=account_data,
                metadata={
                    "source": "zoho_sync",
                    "synced_at": datetime.utcnow().isoformat(),
                    "forced": force
                }
            )

            # Update sync stats
            self._sync_stats["total_syncs"] += 1
            self._sync_stats["successful_syncs"] += 1
            self._sync_stats["last_sync"] = datetime.utcnow().isoformat()

            self.logger.info("account_synced", account_id=account_id)
            return True

        except Exception as e:
            self._sync_stats["total_syncs"] += 1
            self._sync_stats["failed_syncs"] += 1

            self.logger.error(
                "account_sync_failed",
                account_id=account_id,
                error=str(e)
            )
            return False

    async def record_agent_action(
        self,
        account_id: str,
        agent_name: str,
        action: str,
        result: Dict[str, Any]
    ) -> str:
        """Record agent action in memory for future context.

        Enables agents to learn from past actions.
        Target: < 50ms (SPARC PRD metric)

        Args:
            account_id: Account identifier
            agent_name: Name of agent that performed action
            action: Action type
            result: Action result

        Returns:
            Interaction ID
        """
        start_time = datetime.utcnow()

        interaction_data = {
            "agent": agent_name,
            "action": action,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            interaction_id = await self.cognee.store_interaction(
                account_id,
                interaction_type="agent_action",
                data=interaction_data
            )

            duration_ms = (
                datetime.utcnow() - start_time
            ).total_seconds() * 1000

            self.logger.debug(
                "agent_action_recorded",
                account_id=account_id,
                agent=agent_name,
                duration_ms=duration_ms,
                within_target=duration_ms < 50
            )

            return interaction_id

        except Exception as e:
            self.logger.error("agent_action_recording_failed", error=str(e))
            raise

    async def find_similar_accounts(
        self,
        account_id: str,
        criteria: str = "all"
    ) -> List[Dict[str, Any]]:
        """Find similar accounts using knowledge graph.

        Criteria:
        - all: Similar across all dimensions
        - industry: Same industry vertical
        - region: Geographic proximity
        - size: Similar company size
        - health: Similar health patterns

        Args:
            account_id: Source account
            criteria: Similarity criteria

        Returns:
            List of similar accounts with similarity scores
        """
        self.logger.info(
            "finding_similar_accounts",
            account_id=account_id,
            criteria=criteria
        )

        try:
            # Get source account context
            source_context = await self.cognee.get_account_context(account_id)
            source_data = source_context.get("current_snapshot", {})

            # Build search query based on criteria
            if criteria == "industry":
                industry = source_data.get("data", {}).get("Industry")
                if industry:
                    similar = await self.cognee.search_accounts(
                        f"Industry:{industry}",
                        limit=10
                    )
                else:
                    similar = []

            elif criteria == "health":
                health_analysis = await self.cognee.analyze_account_health(
                    account_id
                )
                risk_level = health_analysis.get("risk_level")
                similar = await self.cognee.search_accounts(
                    f"risk_level:{risk_level}",
                    limit=10
                )

            else:  # all or other criteria
                # Use knowledge graph relations
                similar = await self.cognee.get_related_accounts(
                    account_id,
                    relation_type=criteria,
                    limit=10
                )

            # Filter out the source account
            similar = [
                acc for acc in similar
                if acc.get("account_id") != account_id
            ]

            return similar

        except Exception as e:
            self.logger.error("similar_accounts_search_failed", error=str(e))
            return []

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics.

        Returns:
            System statistics and health metrics
        """
        cognee_stats = await self.cognee.get_stats()

        return {
            "cognee": cognee_stats,
            "sync_stats": self._sync_stats,
            "service_status": "operational"
        }

    async def _generate_recommendations(
        self,
        account_id: str,
        health_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate basic recommendations (enhanced in Week 7 with subagent).

        Args:
            account_id: Account identifier
            health_analysis: Health analysis result

        Returns:
            List of recommendations
        """
        recommendations = []

        health_score = health_analysis.get("health_score", 100)
        risk_factors = health_analysis.get("risk_factors", [])
        trend = health_analysis.get("trend", "stable")

        # Rule-based recommendations (placeholder for Week 7 AI enhancement)
        if health_score < 50:
            recommendations.append({
                "priority": "high",
                "action": "Schedule urgent check-in call",
                "reason": f"Account health score is {health_score} (critical)",
                "type": "engagement"
            })

        if trend == "declining":
            recommendations.append({
                "priority": "high",
                "action": "Investigate recent changes",
                "reason": "Health trend is declining",
                "type": "investigation"
            })

        if "No activity in 30 days" in risk_factors:
            recommendations.append({
                "priority": "medium",
                "action": "Re-engage with value-add content",
                "reason": "Account has been inactive for 30 days",
                "type": "engagement"
            })

        if not recommendations:
            recommendations.append({
                "priority": "low",
                "action": "Continue regular touchpoints",
                "reason": "Account health is good",
                "type": "maintenance"
            })

        return recommendations

    async def batch_sync_accounts(
        self,
        account_ids: List[str],
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """Batch sync multiple accounts.

        Args:
            account_ids: List of account IDs to sync
            max_concurrent: Maximum concurrent syncs

        Returns:
            Sync results summary
        """
        import asyncio

        self.logger.info(
            "batch_sync_started",
            count=len(account_ids),
            max_concurrent=max_concurrent
        )

        results = {
            "total": len(account_ids),
            "successful": 0,
            "failed": 0,
            "failed_accounts": []
        }

        # Process in batches
        for i in range(0, len(account_ids), max_concurrent):
            batch = account_ids[i:i + max_concurrent]

            tasks = [
                self.sync_account_to_memory(account_id)
                for account_id in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for account_id, success in zip(batch, batch_results):
                if isinstance(success, Exception):
                    results["failed"] += 1
                    results["failed_accounts"].append(account_id)
                elif success:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["failed_accounts"].append(account_id)

        self.logger.info("batch_sync_completed", results=results)
        return results
