"""
Cognee MCP Tools.

MCP (Model Context Protocol) tools for exposing Cognee functionality
to Claude agents via standardized tool interface.

Provides 5 core tools:
1. cognee_get_account_context - Retrieve complete account context
2. cognee_search_accounts - Semantic search across accounts
3. cognee_analyze_health - Analyze account health
4. cognee_get_related - Find related accounts
5. cognee_store_interaction - Store new interactions
"""

from typing import Dict, List, Optional, Any
import structlog

from src.integrations.cognee.cognee_client import CogneeClient

logger = structlog.get_logger(__name__)


class CogneeMCPTools:
    """
    MCP tools for Cognee knowledge graph access.

    Exposes 5 standardized tools to Claude agents for:
    - Context retrieval
    - Semantic search
    - Health analysis
    - Relationship discovery
    - Interaction storage
    """

    def __init__(self, cognee_client: CogneeClient):
        """
        Initialize MCP tools.

        Args:
            cognee_client: Initialized CogneeClient instance
        """
        self.cognee = cognee_client
        self.logger = logger.bind(component="cognee_mcp_tools")

    async def cognee_get_account_context(
        self,
        account_id: str,
        include_history: bool = True,
        include_relationships: bool = True
    ) -> Dict[str, Any]:
        """
        Tool 1: Get complete account context from memory.

        Returns comprehensive account information including:
        - Current account data
        - Historical interactions and patterns
        - Related accounts and relationships
        - Risk indicators
        - Growth opportunities

        Args:
            account_id: Zoho CRM account ID
            include_history: Include historical interaction timeline
            include_relationships: Include related accounts

        Returns:
            Complete account context dictionary

        Example:
            context = await tools.cognee_get_account_context(
                account_id="123456789",
                include_history=True,
                include_relationships=True
            )
        """
        self.logger.info(
            "mcp_tool_invoked",
            tool="cognee_get_account_context",
            account_id=account_id
        )

        try:
            context = await self.cognee.get_account_context(
                account_id=account_id,
                include_history=include_history,
                include_relationships=include_relationships
            )

            self.logger.info(
                "account_context_retrieved",
                account_id=account_id,
                has_history=len(context.get("historical_interactions", [])) > 0,
                has_relationships=len(context.get("related_accounts", [])) > 0
            )

            return {
                "success": True,
                "account_id": account_id,
                "context": context
            }

        except Exception as e:
            self.logger.error(
                "get_account_context_failed",
                account_id=account_id,
                error=str(e)
            )
            return {
                "success": False,
                "account_id": account_id,
                "error": str(e),
                "error_type": type(e).__name__
            }

    async def cognee_search_accounts(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Tool 2: Semantic search across account knowledge graph.

        Performs natural language search to find relevant accounts.
        Uses vector embeddings for semantic matching.

        Args:
            query: Natural language search query
            limit: Maximum number of results (default: 10)
            filters: Optional metadata filters:
                - industry: Filter by industry
                - region: Filter by billing country
                - owner: Filter by account owner

        Returns:
            Search results with relevance scores

        Examples:
            # Find at-risk accounts
            results = await tools.cognee_search_accounts(
                query="accounts at risk in healthcare industry",
                filters={"industry": "Healthcare"}
            )

            # Find similar accounts
            results = await tools.cognee_search_accounts(
                query="accounts similar to Acme Corp",
                limit=5
            )

            # Find accounts needing attention
            results = await tools.cognee_search_accounts(
                query="accounts with declining engagement"
            )
        """
        self.logger.info(
            "mcp_tool_invoked",
            tool="cognee_search_accounts",
            query=query,
            limit=limit
        )

        try:
            results = await self.cognee.search_accounts(
                query=query,
                limit=limit,
                filters=filters
            )

            self.logger.info(
                "search_completed",
                query=query,
                results_count=len(results)
            )

            return {
                "success": True,
                "query": query,
                "results_count": len(results),
                "results": results,
                "filters": filters
            }

        except Exception as e:
            self.logger.error(
                "search_accounts_failed",
                query=query,
                error=str(e)
            )
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "error_type": type(e).__name__
            }

    async def cognee_analyze_health(
        self,
        account_id: str
    ) -> Dict[str, Any]:
        """
        Tool 3: Analyze account health using historical patterns.

        Calculates comprehensive health score and identifies:
        - Risk factors
        - Growth opportunities
        - Recommended actions

        Args:
            account_id: Zoho CRM account ID

        Returns:
            Health analysis with score, risks, and recommendations

        Example:
            analysis = await tools.cognee_analyze_health(
                account_id="123456789"
            )

            # Returns:
            {
                "health_score": 75,
                "health_category": "moderate",
                "risk_factors": ["No activity in 30 days"],
                "opportunities": ["Potential for upsell"],
                "recommendations": [...]
            }
        """
        self.logger.info(
            "mcp_tool_invoked",
            tool="cognee_analyze_health",
            account_id=account_id
        )

        try:
            analysis = await self.cognee.analyze_account_health(
                account_id=account_id
            )

            self.logger.info(
                "health_analysis_completed",
                account_id=account_id,
                health_score=analysis.get("health_score"),
                health_category=analysis.get("health_category"),
                risk_count=len(analysis.get("risk_factors", []))
            )

            return {
                "success": True,
                "account_id": account_id,
                "analysis": analysis
            }

        except Exception as e:
            self.logger.error(
                "analyze_health_failed",
                account_id=account_id,
                error=str(e)
            )
            return {
                "success": False,
                "account_id": account_id,
                "error": str(e),
                "error_type": type(e).__name__
            }

    async def cognee_get_related(
        self,
        account_id: str,
        relationship_type: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Tool 4: Find related accounts in knowledge graph.

        Discovers accounts with various relationship types:
        - similar_industry: Same industry vertical
        - same_region: Same geographic region
        - shared_contacts: Shared decision makers
        - partnership: Partner/vendor relationships

        Args:
            account_id: Source account ID
            relationship_type: Type of relationship to find (None = all)
            limit: Maximum results

        Returns:
            List of related accounts with relationship details

        Examples:
            # Find similar industry accounts
            related = await tools.cognee_get_related(
                account_id="123456789",
                relationship_type="similar_industry"
            )

            # Find all related accounts
            related = await tools.cognee_get_related(
                account_id="123456789"
            )
        """
        self.logger.info(
            "mcp_tool_invoked",
            tool="cognee_get_related",
            account_id=account_id,
            relationship_type=relationship_type
        )

        try:
            related_accounts = await self.cognee.get_related_accounts(
                account_id=account_id,
                relationship_type=relationship_type,
                limit=limit
            )

            self.logger.info(
                "related_accounts_retrieved",
                account_id=account_id,
                relationship_type=relationship_type,
                count=len(related_accounts)
            )

            return {
                "success": True,
                "account_id": account_id,
                "relationship_type": relationship_type,
                "related_count": len(related_accounts),
                "related_accounts": related_accounts
            }

        except Exception as e:
            self.logger.error(
                "get_related_failed",
                account_id=account_id,
                error=str(e)
            )
            return {
                "success": False,
                "account_id": account_id,
                "error": str(e),
                "error_type": type(e).__name__
            }

    async def cognee_store_interaction(
        self,
        account_id: str,
        interaction_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Tool 5: Store new account interaction in memory.

        Updates knowledge graph with new account activities.
        Triggers re-analysis of account health and patterns.

        Args:
            account_id: Account ID
            interaction_type: Type of interaction:
                - email: Email communication
                - call: Phone call
                - meeting: In-person or virtual meeting
                - note: Account note or update
                - deal_update: Deal stage change or update
            data: Interaction details:
                - date: Interaction date (ISO format)
                - summary: Brief summary
                - details: Full details
                - participants: List of participants
                - outcome: Outcome/result
                - metadata: Additional metadata

        Returns:
            Stored interaction ID and confirmation

        Example:
            result = await tools.cognee_store_interaction(
                account_id="123456789",
                interaction_type="meeting",
                data={
                    "date": "2025-10-18T14:00:00Z",
                    "summary": "Q4 renewal discussion",
                    "details": "Discussed renewal terms and expansion...",
                    "participants": ["John Doe", "Jane Smith"],
                    "outcome": "Positive - moving forward with renewal"
                }
            )
        """
        self.logger.info(
            "mcp_tool_invoked",
            tool="cognee_store_interaction",
            account_id=account_id,
            interaction_type=interaction_type
        )

        try:
            # Validate interaction type
            valid_types = ["email", "call", "meeting", "note", "deal_update"]
            if interaction_type not in valid_types:
                raise ValueError(
                    f"Invalid interaction_type. Must be one of: {valid_types}"
                )

            # Store interaction
            interaction_id = await self.cognee.store_interaction(
                account_id=account_id,
                interaction_type=interaction_type,
                data=data
            )

            self.logger.info(
                "interaction_stored",
                account_id=account_id,
                interaction_type=interaction_type,
                interaction_id=interaction_id
            )

            return {
                "success": True,
                "account_id": account_id,
                "interaction_type": interaction_type,
                "interaction_id": interaction_id,
                "message": "Interaction successfully stored in knowledge graph"
            }

        except Exception as e:
            self.logger.error(
                "store_interaction_failed",
                account_id=account_id,
                interaction_type=interaction_type,
                error=str(e)
            )
            return {
                "success": False,
                "account_id": account_id,
                "error": str(e),
                "error_type": type(e).__name__
            }

    # Additional utility tools

    async def cognee_get_timeline(
        self,
        account_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Bonus Tool: Get chronological interaction timeline.

        Returns sorted timeline of all account interactions.

        Args:
            account_id: Account ID
            limit: Maximum interactions

        Returns:
            Chronological timeline (newest first)
        """
        self.logger.info(
            "mcp_tool_invoked",
            tool="cognee_get_timeline",
            account_id=account_id
        )

        try:
            timeline = await self.cognee.get_account_timeline(
                account_id=account_id,
                limit=limit
            )

            return {
                "success": True,
                "account_id": account_id,
                "timeline_count": len(timeline),
                "timeline": timeline
            }

        except Exception as e:
            self.logger.error(
                "get_timeline_failed",
                account_id=account_id,
                error=str(e)
            )
            return {
                "success": False,
                "account_id": account_id,
                "error": str(e),
                "error_type": type(e).__name__
            }


def create_mcp_tool_definitions() -> List[Dict[str, Any]]:
    """
    Create MCP tool definitions for Claude Agent SDK.

    Returns tool schemas in MCP format for agent configuration.

    Returns:
        List of tool definition dictionaries
    """
    return [
        {
            "name": "cognee_get_account_context",
            "description": (
                "Retrieve complete account context from Cognee memory including "
                "historical interactions, patterns, related accounts, and risk indicators. "
                "Use this to get comprehensive background before making recommendations."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Zoho CRM account ID"
                    },
                    "include_history": {
                        "type": "boolean",
                        "description": "Include historical interaction timeline",
                        "default": True
                    },
                    "include_relationships": {
                        "type": "boolean",
                        "description": "Include related accounts",
                        "default": True
                    }
                },
                "required": ["account_id"]
            }
        },
        {
            "name": "cognee_search_accounts",
            "description": (
                "Semantic search across account knowledge graph using natural language. "
                "Finds accounts matching query using vector embeddings. "
                "Examples: 'at-risk accounts in healthcare', 'accounts needing attention'"
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 10
                    },
                    "filters": {
                        "type": "object",
                        "description": "Optional metadata filters (industry, region, owner)",
                        "properties": {
                            "industry": {"type": "string"},
                            "region": {"type": "string"},
                            "owner": {"type": "string"}
                        }
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "cognee_analyze_health",
            "description": (
                "Analyze account health using historical patterns in knowledge graph. "
                "Returns health score (0-100), risk factors, growth opportunities, "
                "and actionable recommendations."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Zoho CRM account ID"
                    }
                },
                "required": ["account_id"]
            }
        },
        {
            "name": "cognee_get_related",
            "description": (
                "Find related accounts in knowledge graph by relationship type. "
                "Types: similar_industry, same_region, shared_contacts, partnership. "
                "Use to discover cross-sell opportunities or benchmarking."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Source account ID"
                    },
                    "relationship_type": {
                        "type": "string",
                        "enum": [
                            "similar_industry",
                            "same_region",
                            "shared_contacts",
                            "partnership"
                        ],
                        "description": "Type of relationship to find (optional)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results",
                        "default": 10
                    }
                },
                "required": ["account_id"]
            }
        },
        {
            "name": "cognee_store_interaction",
            "description": (
                "Store new account interaction in knowledge graph memory. "
                "Types: email, call, meeting, note, deal_update. "
                "Updates account context and triggers re-analysis."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Account ID"
                    },
                    "interaction_type": {
                        "type": "string",
                        "enum": ["email", "call", "meeting", "note", "deal_update"],
                        "description": "Type of interaction"
                    },
                    "data": {
                        "type": "object",
                        "description": "Interaction details",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Interaction date (ISO format)"
                            },
                            "summary": {
                                "type": "string",
                                "description": "Brief summary"
                            },
                            "details": {
                                "type": "string",
                                "description": "Full details"
                            },
                            "participants": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of participants"
                            },
                            "outcome": {
                                "type": "string",
                                "description": "Outcome/result"
                            }
                        },
                        "required": ["summary"]
                    }
                },
                "required": ["account_id", "interaction_type", "data"]
            }
        }
    ]
