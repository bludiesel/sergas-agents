"""Main Orchestrator Agent - Week 5 SPARC Implementation.

Central coordination agent that:
- Schedules and triggers account review cycles
- Coordinates parallel subagent execution
- Aggregates outputs into owner briefs
- Manages approval workflow for CRM modifications
- Maintains audit trails and metrics

Architecture Alignment: docs/sparc/03_architecture.md lines 104-167
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import structlog
from pydantic import BaseModel, Field

from src.orchestrator.config import OrchestratorConfig
from src.orchestrator.workflow_engine import WorkflowEngine
from src.orchestrator.approval_gate import ApprovalGate, ApprovalStatus
from src.services.memory_service import MemoryService
from src.integrations.zoho.integration_manager import ZohoIntegrationManager
from src.resilience.circuit_breaker import CircuitBreaker
from src.resilience.exceptions import CircuitBreakerOpenError

logger = structlog.get_logger(__name__)


class ReviewCycle(str, Enum):
    """Review cycle frequencies."""
    DAILY = "daily"
    WEEKLY = "weekly"
    ON_DEMAND = "on_demand"


class OrchestratorStatus(str, Enum):
    """Orchestrator operational status."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class OwnerAssignment(BaseModel):
    """Account owner assignment."""
    owner_id: str
    owner_name: str
    owner_email: str
    account_ids: List[str]
    portfolio_size: int = Field(ge=0)
    priority_accounts: List[str] = Field(default_factory=list)


class AccountUpdate(BaseModel):
    """Account change detected."""
    account_id: str
    account_name: str
    owner_id: str
    changes: Dict[str, Any]
    risk_score: int = Field(ge=0, le=100)
    requires_attention: bool = False
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class OwnerBrief(BaseModel):
    """Daily/weekly brief for account owner."""
    owner_id: str
    owner_name: str
    cycle: ReviewCycle
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    # Account summaries
    accounts_reviewed: int = 0
    accounts_with_changes: int = 0
    high_priority_accounts: List[str] = Field(default_factory=list)

    # Updates and recommendations
    updates: List[AccountUpdate] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)

    # Metrics
    total_recommendations: int = 0
    critical_recommendations: int = 0
    estimated_review_time_minutes: int = 0

    # Status
    delivered: bool = False
    reviewed: bool = False
    reviewed_at: Optional[datetime] = None


class SubagentQuery(BaseModel):
    """Subagent query configuration."""
    agent_type: str  # data-scout, memory-analyst, recommendation-author
    prompt: str
    context: Dict[str, Any]
    timeout_seconds: int = 300  # 5 minutes default
    tools_allowed: List[str] = Field(default_factory=list)


class SubagentResult(BaseModel):
    """Result from subagent query."""
    agent_type: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    tokens_used: int = 0


class MainOrchestrator:
    """Main Orchestrator Agent for Sergas Account Manager.

    System Prompt (from SPARC Architecture):
    You are the Sergas Account Manager Orchestrator.
    Your role is to:
    1. Coordinate subagents to review account portfolios
    2. Compile actionable briefs for account owners
    3. Gate all CRM modifications through human approval
    4. Maintain audit trails of all recommendations and decisions

    Never modify CRM data without explicit user approval.
    Always provide data sources for recommendations.
    Prioritize high-risk accounts first.

    Features:
    - Scheduled reviews (daily/weekly/on-demand)
    - Parallel subagent coordination
    - Approval workflow integration
    - Session state persistence
    - Comprehensive audit logging

    Example:
        >>> config = OrchestratorConfig.from_env()
        >>> orchestrator = MainOrchestrator(
        ...     config=config,
        ...     memory_service=memory_service,
        ...     zoho_manager=zoho_manager
        ... )
        >>> await orchestrator.start()
        >>> brief = await orchestrator.execute_review_cycle(
        ...     cycle=ReviewCycle.DAILY
        ... )
    """

    def __init__(
        self,
        config: OrchestratorConfig,
        memory_service: MemoryService,
        zoho_manager: ZohoIntegrationManager,
        approval_gate: Optional[ApprovalGate] = None,
        workflow_engine: Optional[WorkflowEngine] = None,
    ) -> None:
        """Initialize Main Orchestrator.

        Args:
            config: Orchestrator configuration
            memory_service: Memory coordination service
            zoho_manager: Zoho integration manager
            approval_gate: Approval workflow handler (created if None)
            workflow_engine: Workflow execution engine (created if None)
        """
        self.config = config
        self.memory_service = memory_service
        self.zoho_manager = zoho_manager

        # Initialize workflow components
        self.approval_gate = approval_gate or ApprovalGate(config.approval_config)
        self.workflow_engine = workflow_engine or WorkflowEngine(
            config=config,
            memory_service=memory_service,
            zoho_manager=zoho_manager,
        )

        # Circuit breaker for subagent calls
        self.subagent_breaker = CircuitBreaker(
            name="subagent_orchestration",
            failure_threshold=config.circuit_breaker_threshold,
            recovery_timeout=config.circuit_breaker_timeout,
        )

        # State management
        self.status = OrchestratorStatus.IDLE
        self.current_session_id: Optional[str] = None
        self.session_state: Dict[str, Any] = {}

        # Metrics
        self.metrics = {
            "total_reviews": 0,
            "successful_reviews": 0,
            "failed_reviews": 0,
            "total_briefs_generated": 0,
            "total_approvals_requested": 0,
            "total_approvals_granted": 0,
            "average_review_duration_seconds": 0.0,
        }

        self.logger = logger.bind(component="main_orchestrator")
        self.logger.info(
            "orchestrator_initialized",
            config_loaded=True,
            max_concurrent_subagents=config.max_concurrent_subagents,
        )

    async def start(self) -> None:
        """Start orchestrator and initialize components."""
        self.logger.info("orchestrator_starting")

        try:
            # Initialize workflow engine
            await self.workflow_engine.initialize()

            # Load owner assignments
            await self._load_owner_assignments()

            # Start approval gate
            await self.approval_gate.start()

            self.status = OrchestratorStatus.IDLE
            self.logger.info("orchestrator_started", status=self.status.value)

        except Exception as e:
            self.status = OrchestratorStatus.ERROR
            self.logger.error("orchestrator_start_failed", error=str(e))
            raise

    async def stop(self) -> None:
        """Stop orchestrator and cleanup."""
        self.logger.info("orchestrator_stopping")

        try:
            # Stop workflow engine
            await self.workflow_engine.shutdown()

            # Stop approval gate
            await self.approval_gate.stop()

            # Export session state
            if self.current_session_id:
                await self._export_session_state()

            self.status = OrchestratorStatus.IDLE
            self.logger.info("orchestrator_stopped")

        except Exception as e:
            self.logger.error("orchestrator_stop_failed", error=str(e))
            raise

    async def execute_review_cycle(
        self,
        cycle: ReviewCycle,
        owner_ids: Optional[List[str]] = None,
    ) -> List[OwnerBrief]:
        """Execute full review cycle for account owners.

        Main workflow (from SPARC Architecture):
        1. Load account owner assignments
        2. For each owner, spawn parallel subagent queries:
           - Zoho Data Scout: Fetch account updates
           - Memory Analyst: Retrieve historical context
           - Recommendation Author: Generate action suggestions
        3. Compile results into structured owner brief
        4. Present to owner for approval
        5. Execute approved actions
        6. Store decisions in Cognee

        Args:
            cycle: Review cycle type
            owner_ids: Specific owners to review (None = all)

        Returns:
            List of generated owner briefs

        Raises:
            Exception: If review cycle fails
        """
        start_time = datetime.utcnow()
        session_id = f"review_{cycle.value}_{start_time.isoformat()}"
        self.current_session_id = session_id
        self.status = OrchestratorStatus.RUNNING

        self.logger.info(
            "review_cycle_started",
            cycle=cycle.value,
            session_id=session_id,
            owner_count=len(owner_ids) if owner_ids else "all",
        )

        try:
            # Load owner assignments
            owners = await self._get_owners_for_cycle(cycle, owner_ids)

            if not owners:
                self.logger.warning("no_owners_found", cycle=cycle.value)
                return []

            # Execute review for each owner in parallel (respecting max_concurrent)
            briefs = await self.workflow_engine.execute_owner_reviews(
                owners=owners,
                cycle=cycle,
                session_id=session_id,
            )

            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics["total_reviews"] += 1
            self.metrics["successful_reviews"] += 1
            self.metrics["total_briefs_generated"] += len(briefs)
            self.metrics["average_review_duration_seconds"] = (
                (self.metrics["average_review_duration_seconds"] *
                 (self.metrics["successful_reviews"] - 1) + duration) /
                self.metrics["successful_reviews"]
            )

            self.logger.info(
                "review_cycle_completed",
                cycle=cycle.value,
                session_id=session_id,
                briefs_generated=len(briefs),
                duration_seconds=duration,
            )

            return briefs

        except Exception as e:
            self.metrics["total_reviews"] += 1
            self.metrics["failed_reviews"] += 1

            self.logger.error(
                "review_cycle_failed",
                cycle=cycle.value,
                session_id=session_id,
                error=str(e),
            )
            raise

        finally:
            self.status = OrchestratorStatus.IDLE
            self.current_session_id = None

    async def execute_on_demand_review(
        self,
        account_ids: List[str],
        owner_id: Optional[str] = None,
    ) -> OwnerBrief:
        """Execute on-demand review for specific accounts.

        Args:
            account_ids: Account IDs to review
            owner_id: Owner ID (fetched if None)

        Returns:
            Owner brief with review results

        Raises:
            Exception: If review fails
        """
        self.logger.info(
            "on_demand_review_requested",
            account_count=len(account_ids),
            owner_id=owner_id,
        )

        # Fetch owner if not provided
        if not owner_id and account_ids:
            account_data = await self.zoho_manager.get_account(account_ids[0])
            owner_id = account_data.get("Owner", {}).get("id")

        if not owner_id:
            raise ValueError("Could not determine account owner")

        # Create owner assignment
        owner = OwnerAssignment(
            owner_id=owner_id,
            owner_name="",  # Will be fetched
            owner_email="",
            account_ids=account_ids,
            portfolio_size=len(account_ids),
        )

        # Execute review
        briefs = await self.workflow_engine.execute_owner_reviews(
            owners=[owner],
            cycle=ReviewCycle.ON_DEMAND,
            session_id=f"ondemand_{datetime.utcnow().isoformat()}",
        )

        return briefs[0] if briefs else None

    async def query_subagent(
        self,
        query: SubagentQuery,
    ) -> SubagentResult:
        """Query a subagent with circuit breaker protection.

        Args:
            query: Subagent query configuration

        Returns:
            Subagent result
        """
        start_time = datetime.utcnow()

        self.logger.info(
            "querying_subagent",
            agent_type=query.agent_type,
            timeout=query.timeout_seconds,
        )

        try:
            # Execute with circuit breaker
            result = await self.subagent_breaker.call(
                self._execute_subagent_query,
                query,
            )

            duration = (datetime.utcnow() - start_time).total_seconds()

            return SubagentResult(
                agent_type=query.agent_type,
                success=True,
                result=result,
                duration_seconds=duration,
            )

        except CircuitBreakerOpenError as e:
            self.logger.error(
                "subagent_circuit_open",
                agent_type=query.agent_type,
                error=str(e),
            )

            return SubagentResult(
                agent_type=query.agent_type,
                success=False,
                error=f"Circuit breaker open: {str(e)}",
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
            )

        except asyncio.TimeoutError:
            self.logger.error(
                "subagent_timeout",
                agent_type=query.agent_type,
                timeout=query.timeout_seconds,
            )

            return SubagentResult(
                agent_type=query.agent_type,
                success=False,
                error=f"Timeout after {query.timeout_seconds}s",
                duration_seconds=query.timeout_seconds,
            )

        except Exception as e:
            self.logger.error(
                "subagent_query_failed",
                agent_type=query.agent_type,
                error=str(e),
            )

            return SubagentResult(
                agent_type=query.agent_type,
                success=False,
                error=str(e),
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
            )

    async def _execute_subagent_query(
        self,
        query: SubagentQuery,
    ) -> Dict[str, Any]:
        """Execute subagent query (internal).

        This would integrate with Claude Agent SDK query() API
        when implementing actual subagent spawning.

        Args:
            query: Subagent query

        Returns:
            Query result
        """
        # Placeholder for Claude Agent SDK integration
        # In production, this would use:
        # result = await claude_agent_sdk.query(
        #     agent_type=query.agent_type,
        #     prompt=query.prompt,
        #     context=query.context,
        #     tools=query.tools_allowed,
        #     timeout=query.timeout_seconds
        # )

        # For now, simulate subagent execution
        await asyncio.sleep(0.1)  # Simulate processing

        return {
            "agent_type": query.agent_type,
            "status": "completed",
            "data": query.context,
        }

    async def request_approval(
        self,
        recommendation: Dict[str, Any],
        account_id: str,
        owner_id: str,
    ) -> ApprovalStatus:
        """Request approval for recommended action.

        Args:
            recommendation: Recommendation details
            account_id: Account identifier
            owner_id: Owner identifier

        Returns:
            Approval status
        """
        self.metrics["total_approvals_requested"] += 1

        approval_status = await self.approval_gate.request_approval(
            recommendation=recommendation,
            account_id=account_id,
            owner_id=owner_id,
        )

        if approval_status == ApprovalStatus.APPROVED:
            self.metrics["total_approvals_granted"] += 1

        return approval_status

    async def execute_approved_action(
        self,
        action: Dict[str, Any],
        account_id: str,
    ) -> bool:
        """Execute approved CRM action.

        Args:
            action: Action details
            account_id: Account identifier

        Returns:
            True if execution successful
        """
        self.logger.info(
            "executing_approved_action",
            action_type=action.get("type"),
            account_id=account_id,
        )

        try:
            action_type = action.get("type")

            if action_type == "create_task":
                await self.zoho_manager.create_task(
                    account_id=account_id,
                    task_data=action.get("data", {}),
                )
            elif action_type == "add_note":
                await self.zoho_manager.create_note(
                    account_id=account_id,
                    note_data=action.get("data", {}),
                )
            elif action_type == "update_account":
                await self.zoho_manager.update_account(
                    account_id=account_id,
                    data=action.get("data", {}),
                )
            else:
                self.logger.warning(
                    "unknown_action_type",
                    action_type=action_type,
                )
                return False

            # Store decision in Cognee
            await self.memory_service.record_agent_action(
                account_id=account_id,
                agent_name="main_orchestrator",
                action="execute_approved_action",
                result=action,
            )

            self.logger.info(
                "action_executed",
                action_type=action_type,
                account_id=account_id,
            )

            return True

        except Exception as e:
            self.logger.error(
                "action_execution_failed",
                action_type=action.get("type"),
                account_id=account_id,
                error=str(e),
            )
            return False

    async def _load_owner_assignments(self) -> None:
        """Load account owner assignments from config/database."""
        self.logger.info("loading_owner_assignments")

        # This would load from database or config
        # For now, we'll fetch from Zoho
        self.session_state["owner_assignments"] = []

    async def _get_owners_for_cycle(
        self,
        cycle: ReviewCycle,
        owner_ids: Optional[List[str]] = None,
    ) -> List[OwnerAssignment]:
        """Get owners to include in review cycle.

        Args:
            cycle: Review cycle type
            owner_ids: Specific owners (None = all)

        Returns:
            List of owner assignments
        """
        # Fetch from Zoho or cache
        all_owners = self.session_state.get("owner_assignments", [])

        if owner_ids:
            return [o for o in all_owners if o.owner_id in owner_ids]

        return all_owners

    async def _export_session_state(self) -> None:
        """Export session state and audit trail."""
        if not self.current_session_id:
            return

        self.logger.info(
            "exporting_session_state",
            session_id=self.current_session_id,
        )

        # Store session state in memory
        await self.memory_service.record_agent_action(
            account_id="system",
            agent_name="main_orchestrator",
            action="export_session_state",
            result={
                "session_id": self.current_session_id,
                "session_state": self.session_state,
                "metrics": self.metrics,
            },
        )

    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status and metrics.

        Returns:
            Status information
        """
        return {
            "status": self.status.value,
            "current_session": self.current_session_id,
            "metrics": self.metrics,
            "circuit_breaker": self.subagent_breaker.get_metrics(),
            "workflow_engine": self.workflow_engine.get_status(),
            "approval_gate": self.approval_gate.get_status(),
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics.

        Returns:
            Metrics dictionary
        """
        return {
            **self.metrics,
            "workflow_metrics": self.workflow_engine.get_metrics(),
            "approval_metrics": self.approval_gate.get_metrics(),
        }
