"""Workflow Engine - Executes account review workflows.

Responsibilities:
- Schedule review cycles (daily/weekly/on-demand)
- Coordinate parallel subagent execution
- Aggregate and compile results
- Priority queue management
- Error handling and recovery
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import structlog
from pydantic import BaseModel, Field

from src.orchestrator.config import OrchestratorConfig
from src.services.memory_service import MemoryService
from src.integrations.zoho.integration_manager import ZohoIntegrationManager
from src.resilience.circuit_breaker import CircuitBreaker
from src.resilience.exceptions import CircuitBreakerOpenError

logger = structlog.get_logger(__name__)


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class PriorityLevel(str, Enum):
    """Account priority levels."""
    CRITICAL = "critical"  # Risk score > 80
    HIGH = "high"          # Risk score 60-80
    MEDIUM = "medium"      # Risk score 40-60
    LOW = "low"            # Risk score < 40


class WorkflowExecution(BaseModel):
    """Workflow execution tracking."""
    execution_id: str
    owner_id: str
    account_ids: List[str]
    status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    results: Dict[str, Any] = Field(default_factory=dict)


class WorkflowEngine:
    """Workflow execution engine for account reviews.

    Coordinates:
    - Parallel subagent queries using Claude SDK query() API
    - Result aggregation into owner briefs
    - Priority-based processing
    - Error handling with circuit breaker

    Performance Targets (SPARC PRD):
    - Owner brief generation: <10 minutes
    - Account analysis: <30 seconds per account
    - Concurrent subagents: Up to 10 parallel

    Example:
        >>> engine = WorkflowEngine(config, memory_service, zoho_manager)
        >>> await engine.initialize()
        >>> briefs = await engine.execute_owner_reviews(
        ...     owners=owners,
        ...     cycle=ReviewCycle.DAILY
        ... )
    """

    def __init__(
        self,
        config: OrchestratorConfig,
        memory_service: MemoryService,
        zoho_manager: ZohoIntegrationManager,
    ) -> None:
        """Initialize workflow engine.

        Args:
            config: Orchestrator configuration
            memory_service: Memory coordination service
            zoho_manager: Zoho integration manager
        """
        self.config = config
        self.memory_service = memory_service
        self.zoho_manager = zoho_manager

        # Priority queue for high-risk accounts
        self.priority_queue: List[Dict[str, Any]] = []

        # Active executions
        self.executions: Dict[str, WorkflowExecution] = {}

        # Circuit breaker for workflow operations
        self.workflow_breaker = CircuitBreaker(
            name="workflow_execution",
            failure_threshold=5,
            recovery_timeout=60,
        )

        # Metrics
        self.metrics = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_duration_seconds": 0.0,
            "total_accounts_processed": 0,
            "average_accounts_per_minute": 0.0,
        }

        self.logger = logger.bind(component="workflow_engine")
        self.logger.info("workflow_engine_initialized")

    async def initialize(self) -> None:
        """Initialize workflow engine."""
        self.logger.info("workflow_engine_initializing")

        # Load any pending workflows
        await self._load_pending_workflows()

        self.logger.info("workflow_engine_initialized")

    async def shutdown(self) -> None:
        """Shutdown workflow engine."""
        self.logger.info("workflow_engine_shutting_down")

        # Wait for active workflows
        if self.executions:
            self.logger.info(
                "waiting_for_active_workflows",
                count=len(self.executions),
            )
            await asyncio.sleep(1)  # Grace period

        self.logger.info("workflow_engine_shutdown")

    async def execute_owner_reviews(
        self,
        owners: List[Any],  # OwnerAssignment
        cycle: Any,  # ReviewCycle
        session_id: str,
    ) -> List[Any]:  # List[OwnerBrief]
        """Execute reviews for multiple owners in parallel.

        Args:
            owners: List of owner assignments
            cycle: Review cycle type
            session_id: Session identifier

        Returns:
            List of generated owner briefs
        """
        self.logger.info(
            "executing_owner_reviews",
            owner_count=len(owners),
            cycle=cycle.value,
            session_id=session_id,
        )

        start_time = datetime.utcnow()

        # Create workflow executions
        executions = []
        for owner in owners:
            execution = WorkflowExecution(
                execution_id=f"{session_id}_{owner.owner_id}",
                owner_id=owner.owner_id,
                account_ids=owner.account_ids,
            )
            self.executions[execution.execution_id] = execution
            executions.append(execution)

        # Execute in parallel with concurrency limit
        semaphore = asyncio.Semaphore(self.config.max_concurrent_subagents)

        async def execute_with_limit(execution: WorkflowExecution) -> Any:
            async with semaphore:
                return await self._execute_owner_review(
                    owner=[o for o in owners if o.owner_id == execution.owner_id][0],
                    cycle=cycle,
                    execution=execution,
                )

        # Execute all reviews
        briefs = await asyncio.gather(
            *[execute_with_limit(exec) for exec in executions],
            return_exceptions=True,
        )

        # Filter successful results
        successful_briefs = [
            b for b in briefs
            if b is not None and not isinstance(b, Exception)
        ]

        # Update metrics
        duration = (datetime.utcnow() - start_time).total_seconds()
        self.metrics["total_workflows"] += len(owners)
        self.metrics["successful_workflows"] += len(successful_briefs)
        self.metrics["failed_workflows"] += len(owners) - len(successful_briefs)

        total_accounts = sum(len(o.account_ids) for o in owners)
        self.metrics["total_accounts_processed"] += total_accounts

        if duration > 0:
            accounts_per_minute = (total_accounts / duration) * 60
            self.metrics["average_accounts_per_minute"] = (
                (self.metrics["average_accounts_per_minute"] *
                 (self.metrics["total_workflows"] - len(owners)) +
                 accounts_per_minute * len(owners)) /
                self.metrics["total_workflows"]
            )

        self.logger.info(
            "owner_reviews_completed",
            successful=len(successful_briefs),
            failed=len(owners) - len(successful_briefs),
            duration_seconds=duration,
        )

        return successful_briefs

    async def _execute_owner_review(
        self,
        owner: Any,  # OwnerAssignment
        cycle: Any,  # ReviewCycle
        execution: WorkflowExecution,
    ) -> Any:  # OwnerBrief
        """Execute review for single owner.

        Workflow steps:
        1. Prioritize accounts by risk
        2. Spawn parallel subagents:
           - Data Scout: Fetch account updates
           - Memory Analyst: Retrieve historical context
           - Recommendation Author: Generate suggestions
        3. Aggregate results
        4. Compile owner brief

        Args:
            owner: Owner assignment
            cycle: Review cycle
            execution: Execution tracking

        Returns:
            Owner brief
        """
        execution.status = WorkflowStatus.RUNNING
        execution.started_at = datetime.utcnow()

        self.logger.info(
            "executing_owner_review",
            owner_id=owner.owner_id,
            account_count=len(owner.account_ids),
        )

        try:
            # Step 1: Prioritize accounts
            prioritized_accounts = await self._prioritize_accounts(
                owner.account_ids
            )

            # Step 2: Execute parallel subagent queries
            updates = []
            recommendations = []

            for account_id in prioritized_accounts:
                try:
                    # Query subagents in parallel
                    scout_task = self._query_data_scout(account_id)
                    analyst_task = self._query_memory_analyst(account_id)
                    author_task = self._query_recommendation_author(account_id)

                    scout_result, analyst_result, author_result = await asyncio.gather(
                        scout_task,
                        analyst_task,
                        author_task,
                        return_exceptions=True,
                    )

                    # Aggregate results
                    if not isinstance(scout_result, Exception):
                        updates.append(scout_result)

                    if not isinstance(author_result, Exception):
                        recommendations.extend(author_result.get("recommendations", []))

                except Exception as e:
                    self.logger.warning(
                        "account_review_failed",
                        account_id=account_id,
                        error=str(e),
                    )
                    continue

            # Step 3: Compile brief
            brief = await self._compile_owner_brief(
                owner=owner,
                cycle=cycle,
                updates=updates,
                recommendations=recommendations,
            )

            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.results = brief.dict()

            self.logger.info(
                "owner_review_completed",
                owner_id=owner.owner_id,
                accounts_reviewed=brief.accounts_reviewed,
                recommendations=len(recommendations),
            )

            return brief

        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()

            self.logger.error(
                "owner_review_failed",
                owner_id=owner.owner_id,
                error=str(e),
            )
            raise

    async def _prioritize_accounts(
        self,
        account_ids: List[str],
    ) -> List[str]:
        """Prioritize accounts by risk score.

        Args:
            account_ids: Account identifiers

        Returns:
            Sorted account IDs (highest risk first)
        """
        # Fetch risk scores from memory
        account_priorities = []

        for account_id in account_ids:
            try:
                # Get health analysis (includes risk score)
                health = await self.memory_service.cognee.analyze_account_health(
                    account_id
                )
                risk_score = health.get("risk_score", 0)

                account_priorities.append({
                    "account_id": account_id,
                    "risk_score": risk_score,
                })

            except Exception as e:
                self.logger.warning(
                    "risk_score_fetch_failed",
                    account_id=account_id,
                    error=str(e),
                )
                # Default to medium priority
                account_priorities.append({
                    "account_id": account_id,
                    "risk_score": 50,
                })

        # Sort by risk score descending
        account_priorities.sort(key=lambda x: x["risk_score"], reverse=True)

        return [a["account_id"] for a in account_priorities]

    async def _query_data_scout(
        self,
        account_id: str,
    ) -> Dict[str, Any]:
        """Query Data Scout subagent for account updates.

        Args:
            account_id: Account identifier

        Returns:
            Account update data
        """
        # Fetch current data from Zoho
        current_data = await self.zoho_manager.get_account(account_id)

        # Get last known state from memory
        context = await self.memory_service.cognee.get_account_context(account_id)
        last_snapshot = context.get("current_snapshot", {})

        # Detect changes
        changes = self._detect_changes(
            current=current_data,
            previous=last_snapshot.get("data", {}),
        )

        return {
            "account_id": account_id,
            "account_name": current_data.get("Account_Name", ""),
            "current_data": current_data,
            "changes": changes,
            "requires_attention": len(changes) > 0,
        }

    async def _query_memory_analyst(
        self,
        account_id: str,
    ) -> Dict[str, Any]:
        """Query Memory Analyst subagent for historical context.

        Args:
            account_id: Account identifier

        Returns:
            Historical context
        """
        # Get comprehensive account brief from memory service
        brief = await self.memory_service.get_account_brief(
            account_id=account_id,
            include_recommendations=False,
        )

        return {
            "account_id": account_id,
            "context": brief.get("historical_context", {}),
            "health_analysis": brief.get("health_analysis", {}),
            "timeline": brief.get("timeline", []),
        }

    async def _query_recommendation_author(
        self,
        account_id: str,
    ) -> Dict[str, Any]:
        """Query Recommendation Author subagent.

        Args:
            account_id: Account identifier

        Returns:
            Generated recommendations
        """
        # Get account brief with recommendations
        brief = await self.memory_service.get_account_brief(
            account_id=account_id,
            include_recommendations=True,
        )

        return {
            "account_id": account_id,
            "recommendations": brief.get("recommendations", []),
        }

    def _detect_changes(
        self,
        current: Dict[str, Any],
        previous: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Detect field-level changes.

        Args:
            current: Current account data
            previous: Previous account data

        Returns:
            Dictionary of changes
        """
        changes = {}

        # Critical fields to monitor
        critical_fields = [
            "Account_Name",
            "Owner",
            "Stage",
            "Status",
            "Last_Activity_Time",
            "Annual_Revenue",
        ]

        for field in critical_fields:
            current_value = current.get(field)
            previous_value = previous.get(field)

            if current_value != previous_value:
                changes[field] = {
                    "old": previous_value,
                    "new": current_value,
                }

        return changes

    async def _compile_owner_brief(
        self,
        owner: Any,  # OwnerAssignment
        cycle: Any,  # ReviewCycle
        updates: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
    ) -> Any:  # OwnerBrief
        """Compile owner brief from aggregated results.

        Args:
            owner: Owner assignment
            cycle: Review cycle
            updates: Account updates
            recommendations: Recommendations

        Returns:
            Owner brief
        """
        # Import here to avoid circular dependency
        from src.orchestrator.main_orchestrator import OwnerBrief, AccountUpdate

        # Calculate metrics
        accounts_with_changes = len([u for u in updates if u.get("requires_attention")])
        high_priority = [
            u["account_id"] for u in updates
            if u.get("risk_score", 0) > 70
        ]

        critical_recommendations = [
            r for r in recommendations
            if r.get("priority") == "critical" or r.get("priority") == "high"
        ]

        # Estimate review time (3 minutes per account with changes + 1 per stable)
        estimated_time = (accounts_with_changes * 3) + (len(updates) - accounts_with_changes)

        # Create AccountUpdate objects
        account_updates = []
        for update in updates:
            account_updates.append(AccountUpdate(
                account_id=update["account_id"],
                account_name=update.get("account_name", ""),
                owner_id=owner.owner_id,
                changes=update.get("changes", {}),
                risk_score=update.get("risk_score", 0),
                requires_attention=update.get("requires_attention", False),
            ))

        # Create brief
        brief = OwnerBrief(
            owner_id=owner.owner_id,
            owner_name=owner.owner_name,
            cycle=cycle,
            accounts_reviewed=len(updates),
            accounts_with_changes=accounts_with_changes,
            high_priority_accounts=high_priority,
            updates=account_updates,
            recommendations=recommendations,
            total_recommendations=len(recommendations),
            critical_recommendations=len(critical_recommendations),
            estimated_review_time_minutes=estimated_time,
        )

        return brief

    async def _load_pending_workflows(self) -> None:
        """Load any pending workflows from previous session."""
        # This would load from database
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get workflow engine status.

        Returns:
            Status information
        """
        return {
            "active_executions": len(self.executions),
            "priority_queue_size": len(self.priority_queue),
            "circuit_breaker": self.workflow_breaker.get_metrics(),
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get workflow metrics.

        Returns:
            Metrics dictionary
        """
        return {**self.metrics}
