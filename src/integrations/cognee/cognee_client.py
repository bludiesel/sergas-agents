"""
Cognee Knowledge Graph Client.

Production-ready client for Cognee persistent memory and knowledge graph.
Provides interface to store, retrieve, and analyze account data.
"""

from typing import Dict, List, Optional, Any, Union
import asyncio
from datetime import datetime
import structlog

try:
    from cognee import cognee
    COGNEE_AVAILABLE = True
except ImportError:
    COGNEE_AVAILABLE = False
    cognee = None

from src.integrations.cognee.cognee_config import CogneeConfig

logger = structlog.get_logger(__name__)


class CogneeClient:
    """
    Cognee knowledge graph client for persistent memory.

    Provides interface to store, retrieve, and analyze account data
    in the Cognee knowledge graph with vector embeddings and relationships.

    Features:
    - Account ingestion and storage
    - Semantic search across knowledge graph
    - Historical context retrieval
    - Account health analysis
    - Relationship discovery
    - Interaction timeline tracking
    """

    def __init__(
        self,
        config: Optional[CogneeConfig] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        workspace: Optional[str] = None
    ):
        """
        Initialize Cognee client.

        Args:
            config: CogneeConfig object (takes precedence)
            api_key: Cognee API key (fallback)
            base_url: Cognee API base URL (fallback)
            workspace: Workspace name (fallback)

        Raises:
            ImportError: If cognee library not available
            ValueError: If configuration is invalid
        """
        if not COGNEE_AVAILABLE:
            raise ImportError(
                "Cognee library not available. Install with: pip install cognee>=0.3.0"
            )

        # Use config or fallback to parameters
        self.config = config or CogneeConfig(
            api_key=api_key,
            base_url=base_url or "http://localhost:8000",
            workspace=workspace or "sergas-accounts"
        )

        self.logger = logger.bind(
            component="cognee_client",
            workspace=self.config.workspace
        )

        # Connection state
        self._initialized = False
        self._session = None

        self.logger.info(
            "cognee_client_initialized",
            base_url=self.config.base_url,
            workspace=self.config.workspace
        )

    async def initialize(self) -> None:
        """
        Initialize Cognee connection and workspace.

        Raises:
            ConnectionError: If cannot connect to Cognee
        """
        if self._initialized:
            self.logger.debug("cognee_already_initialized")
            return

        try:
            # Initialize Cognee configuration
            if self.config.api_key:
                cognee.config.set_api_key(self.config.api_key)

            cognee.config.set_base_url(self.config.base_url)

            # Create or connect to workspace
            await cognee.setup_workspace(self.config.workspace)

            self._initialized = True
            self.logger.info(
                "cognee_connection_established",
                workspace=self.config.workspace
            )

        except Exception as e:
            self.logger.error(
                "cognee_initialization_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise ConnectionError(f"Failed to initialize Cognee: {e}") from e

    async def add_account(
        self,
        account_data: Dict[str, Any],
        generate_embeddings: bool = True
    ) -> str:
        """
        Add single account to knowledge graph.

        Args:
            account_data: Account information from Zoho CRM
            generate_embeddings: Whether to generate vector embeddings

        Returns:
            Account ID in knowledge graph

        Raises:
            ValueError: If account_data is invalid
        """
        await self._ensure_initialized()

        # Validate account data
        if not account_data.get("id"):
            raise ValueError("Account data must include 'id' field")

        account_id = account_data["id"]

        try:
            # Prepare account document
            account_text = self._format_account_for_storage(account_data)

            # Store in Cognee
            if generate_embeddings:
                await cognee.add(
                    account_text,
                    dataset_name=f"account_{account_id}",
                    metadata={
                        "account_id": account_id,
                        "account_name": account_data.get("Account_Name", ""),
                        "industry": account_data.get("Industry", ""),
                        "region": account_data.get("Billing_Country", ""),
                        "ingestion_time": datetime.utcnow().isoformat(),
                        "source": "zoho_crm"
                    }
                )

                # Generate embeddings
                await cognee.cognify()
            else:
                # Store without embeddings
                await cognee.add(
                    account_text,
                    dataset_name=f"account_{account_id}"
                )

            self.logger.info(
                "account_added_to_cognee",
                account_id=account_id,
                account_name=account_data.get("Account_Name"),
                embeddings_generated=generate_embeddings
            )

            return account_id

        except Exception as e:
            self.logger.error(
                "account_add_failed",
                account_id=account_id,
                error=str(e)
            )
            raise

    async def add_accounts_bulk(
        self,
        accounts: List[Dict[str, Any]],
        batch_size: Optional[int] = None,
        generate_embeddings: bool = True
    ) -> Dict[str, Any]:
        """
        Bulk add accounts to knowledge graph.

        Args:
            accounts: List of account data dictionaries
            batch_size: Batch size for processing (defaults to config)
            generate_embeddings: Whether to generate embeddings

        Returns:
            Ingestion report with stats
        """
        await self._ensure_initialized()

        batch_size = batch_size or self.config.batch_size
        total_accounts = len(accounts)

        self.logger.info(
            "bulk_ingestion_started",
            total_accounts=total_accounts,
            batch_size=batch_size
        )

        results = {
            "total": total_accounts,
            "success": 0,
            "failed": 0,
            "errors": [],
            "account_ids": []
        }

        # Process in batches
        for i in range(0, total_accounts, batch_size):
            batch = accounts[i:i + batch_size]
            batch_num = (i // batch_size) + 1

            self.logger.debug(
                "processing_batch",
                batch_num=batch_num,
                batch_size=len(batch)
            )

            # Process batch concurrently
            tasks = [
                self.add_account(account, generate_embeddings)
                for account in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Aggregate results
            for account, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    results["failed"] += 1
                    results["errors"].append({
                        "account_id": account.get("id"),
                        "error": str(result)
                    })
                else:
                    results["success"] += 1
                    results["account_ids"].append(result)

        self.logger.info(
            "bulk_ingestion_completed",
            total=results["total"],
            success=results["success"],
            failed=results["failed"]
        )

        return results

    async def get_account_context(
        self,
        account_id: str,
        include_history: bool = True,
        include_relationships: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve account with full context from knowledge graph.

        Args:
            account_id: Zoho CRM account ID
            include_history: Include historical interactions
            include_relationships: Include related accounts

        Returns:
            Complete account context including:
            - Account data
            - Historical interactions
            - Related accounts
            - Identified patterns
            - Risk indicators
        """
        await self._ensure_initialized()

        try:
            # Search for account in knowledge graph
            search_results = await cognee.search(
                f"account {account_id}",
                filter_metadata={"account_id": account_id}
            )

            context = {
                "account_id": account_id,
                "account_data": {},
                "historical_interactions": [],
                "related_accounts": [],
                "patterns": [],
                "risk_indicators": [],
                "last_updated": datetime.utcnow().isoformat()
            }

            if not search_results:
                self.logger.warning(
                    "account_not_found_in_cognee",
                    account_id=account_id
                )
                return context

            # Extract account data from search results
            context["account_data"] = self._parse_search_results(search_results)

            # Get historical interactions if requested
            if include_history:
                context["historical_interactions"] = await self._get_account_history(
                    account_id
                )

            # Get related accounts if requested
            if include_relationships:
                context["related_accounts"] = await self.get_related_accounts(
                    account_id
                )

            # Identify patterns
            context["patterns"] = self._identify_patterns(context)

            # Detect risk indicators
            context["risk_indicators"] = self._detect_risk_indicators(context)

            return context

        except Exception as e:
            self.logger.error(
                "get_account_context_failed",
                account_id=account_id,
                error=str(e)
            )
            raise

    async def search_accounts(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across account knowledge graph.

        Args:
            query: Natural language search query
            limit: Maximum number of results
            filters: Optional metadata filters (industry, region, etc.)

        Returns:
            Ranked list of matching accounts with relevance scores
        """
        await self._ensure_initialized()

        try:
            # Perform semantic search
            search_results = await cognee.search(
                query,
                filter_metadata=filters,
                limit=limit
            )

            accounts = []
            for result in search_results:
                account = {
                    "account_id": result.get("metadata", {}).get("account_id"),
                    "account_name": result.get("metadata", {}).get("account_name"),
                    "relevance_score": result.get("score", 0.0),
                    "summary": result.get("text", "")[:200],
                    "metadata": result.get("metadata", {})
                }
                accounts.append(account)

            self.logger.info(
                "search_completed",
                query=query,
                results_count=len(accounts),
                limit=limit
            )

            return accounts

        except Exception as e:
            self.logger.error(
                "search_accounts_failed",
                query=query,
                error=str(e)
            )
            raise

    async def analyze_account_health(
        self,
        account_id: str
    ) -> Dict[str, Any]:
        """
        Analyze account health using knowledge graph patterns.

        Args:
            account_id: Zoho CRM account ID

        Returns:
            Account health analysis with:
            - Health score (0-100)
            - Risk factors
            - Growth opportunities
            - Recommended actions
        """
        await self._ensure_initialized()

        # Get full account context
        context = await self.get_account_context(account_id)

        # Calculate health score
        health_score = self._calculate_health_score(context)

        # Identify risk factors
        risk_factors = context.get("risk_indicators", [])

        # Identify opportunities
        opportunities = self._identify_opportunities(context)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            context,
            health_score,
            risk_factors,
            opportunities
        )

        analysis = {
            "account_id": account_id,
            "account_name": context["account_data"].get("account_name", ""),
            "health_score": health_score,
            "health_category": self._categorize_health(health_score),
            "risk_factors": risk_factors,
            "opportunities": opportunities,
            "recommendations": recommendations,
            "analysis_date": datetime.utcnow().isoformat()
        }

        self.logger.info(
            "account_health_analyzed",
            account_id=account_id,
            health_score=health_score,
            risk_count=len(risk_factors)
        )

        return analysis

    async def get_related_accounts(
        self,
        account_id: str,
        relationship_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get related accounts from knowledge graph.

        Args:
            account_id: Source account ID
            relationship_type: Type of relationship to filter
                - similar_industry
                - same_region
                - shared_contacts
                - partnership
            limit: Maximum results

        Returns:
            List of related accounts with relationship details
        """
        await self._ensure_initialized()

        # Get account context
        context = await self.get_account_context(account_id, include_relationships=False)
        account_data = context.get("account_data", {})

        # Build search query based on relationship type
        if relationship_type == "similar_industry":
            query = f"accounts in {account_data.get('industry', '')} industry"
        elif relationship_type == "same_region":
            query = f"accounts in {account_data.get('region', '')} region"
        elif relationship_type == "shared_contacts":
            query = f"accounts with shared contacts {account_id}"
        elif relationship_type == "partnership":
            query = f"partner accounts of {account_id}"
        else:
            # Generic similarity search
            query = f"accounts similar to {account_data.get('account_name', account_id)}"

        # Search for related accounts
        related = await self.search_accounts(query, limit=limit + 1)

        # Filter out the source account
        related_accounts = [
            acc for acc in related
            if acc["account_id"] != account_id
        ][:limit]

        return related_accounts

    async def store_interaction(
        self,
        account_id: str,
        interaction_type: str,
        data: Dict[str, Any]
    ) -> str:
        """
        Store account interaction in knowledge graph.

        Args:
            account_id: Account ID
            interaction_type: Type of interaction (email, call, meeting, note, deal_update)
            data: Interaction data

        Returns:
            Interaction ID
        """
        await self._ensure_initialized()

        # Create interaction document
        interaction_id = f"{account_id}_{interaction_type}_{datetime.utcnow().timestamp()}"

        interaction_text = f"""
        Interaction for account {account_id}
        Type: {interaction_type}
        Date: {data.get('date', datetime.utcnow().isoformat())}
        Summary: {data.get('summary', '')}
        Details: {data.get('details', '')}
        """

        try:
            await cognee.add(
                interaction_text,
                dataset_name=f"interaction_{interaction_id}",
                metadata={
                    "account_id": account_id,
                    "interaction_id": interaction_id,
                    "interaction_type": interaction_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    **data.get("metadata", {})
                }
            )

            await cognee.cognify()

            self.logger.info(
                "interaction_stored",
                account_id=account_id,
                interaction_type=interaction_type,
                interaction_id=interaction_id
            )

            return interaction_id

        except Exception as e:
            self.logger.error(
                "store_interaction_failed",
                account_id=account_id,
                error=str(e)
            )
            raise

    async def get_account_timeline(
        self,
        account_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get chronological account interaction timeline.

        Args:
            account_id: Account ID
            limit: Maximum interactions to return

        Returns:
            Sorted list of interactions (newest first)
        """
        await self._ensure_initialized()

        try:
            # Search for all interactions for this account
            interactions = await cognee.search(
                f"interactions for account {account_id}",
                filter_metadata={"account_id": account_id},
                limit=limit
            )

            # Parse and sort by timestamp
            timeline = []
            for interaction in interactions:
                metadata = interaction.get("metadata", {})
                timeline.append({
                    "interaction_id": metadata.get("interaction_id"),
                    "type": metadata.get("interaction_type"),
                    "timestamp": metadata.get("timestamp"),
                    "summary": interaction.get("text", "")[:200]
                })

            # Sort by timestamp (newest first)
            timeline.sort(
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )

            return timeline[:limit]

        except Exception as e:
            self.logger.error(
                "get_timeline_failed",
                account_id=account_id,
                error=str(e)
            )
            raise

    async def close(self) -> None:
        """Close Cognee client and cleanup resources."""
        if self._session:
            await self._session.close()
            self._session = None

        self._initialized = False
        self.logger.info("cognee_client_closed")

    # Helper methods

    async def _ensure_initialized(self) -> None:
        """Ensure client is initialized before operations."""
        if not self._initialized:
            await self.initialize()

    def _format_account_for_storage(self, account_data: Dict[str, Any]) -> str:
        """Format account data as text for Cognee storage."""
        account_name = account_data.get("Account_Name", "Unknown")
        industry = account_data.get("Industry", "Unknown")
        region = account_data.get("Billing_Country", "Unknown")
        revenue = account_data.get("Annual_Revenue", 0)

        text = f"""
        Account: {account_name}
        ID: {account_data.get('id')}
        Industry: {industry}
        Region: {region}
        Annual Revenue: ${revenue}

        Description: {account_data.get('Description', '')}

        Key Information:
        - Owner: {account_data.get('Owner', {}).get('name', 'Unknown')}
        - Type: {account_data.get('Account_Type', 'Unknown')}
        - Rating: {account_data.get('Rating', 'Unknown')}
        - Website: {account_data.get('Website', '')}
        """

        return text.strip()

    def _parse_search_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse Cognee search results into account data."""
        if not results:
            return {}

        # Use first result as primary data
        primary = results[0]
        metadata = primary.get("metadata", {})

        return {
            "account_id": metadata.get("account_id"),
            "account_name": metadata.get("account_name"),
            "industry": metadata.get("industry"),
            "region": metadata.get("region"),
            "raw_text": primary.get("text", "")
        }

    async def _get_account_history(self, account_id: str) -> List[Dict[str, Any]]:
        """Get historical interactions for account."""
        return await self.get_account_timeline(account_id, limit=20)

    def _identify_patterns(self, context: Dict[str, Any]) -> List[str]:
        """Identify patterns in account context."""
        patterns = []

        history = context.get("historical_interactions", [])

        # Check for engagement patterns
        if len(history) == 0:
            patterns.append("No historical interactions recorded")
        elif len(history) > 10:
            patterns.append("Highly engaged account")

        return patterns

    def _detect_risk_indicators(self, context: Dict[str, Any]) -> List[str]:
        """Detect risk indicators from account context."""
        risks = []

        history = context.get("historical_interactions", [])

        # Check for inactivity
        if not history:
            risks.append("No recent activity")

        return risks

    def _calculate_health_score(self, context: Dict[str, Any]) -> int:
        """Calculate account health score (0-100)."""
        score = 50  # Base score

        # Adjust based on activity
        history_count = len(context.get("historical_interactions", []))
        if history_count > 10:
            score += 20
        elif history_count > 5:
            score += 10
        elif history_count == 0:
            score -= 20

        # Adjust based on risks
        risk_count = len(context.get("risk_indicators", []))
        score -= (risk_count * 10)

        # Clamp to 0-100
        return max(0, min(100, score))

    def _categorize_health(self, score: int) -> str:
        """Categorize health score."""
        if score >= 80:
            return "healthy"
        elif score >= 60:
            return "moderate"
        elif score >= 40:
            return "at_risk"
        else:
            return "critical"

    def _identify_opportunities(self, context: Dict[str, Any]) -> List[str]:
        """Identify growth opportunities."""
        opportunities = []

        # Check for upsell potential
        history = context.get("historical_interactions", [])
        if len(history) > 5:
            opportunities.append("Potential for expansion based on engagement")

        return opportunities

    def _generate_recommendations(
        self,
        context: Dict[str, Any],
        health_score: int,
        risk_factors: List[str],
        opportunities: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations."""
        recommendations = []

        # Risk-based recommendations
        if health_score < 60:
            recommendations.append({
                "priority": "high",
                "action": "Schedule check-in call",
                "rationale": "Account health below threshold"
            })

        # Opportunity-based recommendations
        for opportunity in opportunities:
            recommendations.append({
                "priority": "medium",
                "action": "Explore upsell opportunity",
                "rationale": opportunity
            })

        return recommendations
