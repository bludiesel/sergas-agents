"""Dynamic Workflow Engine with Adaptive Agent Coordination.

Production-ready workflow management system for intelligent multi-agent orchestration
with adaptive routing, parallel execution, and performance optimization.

Features:
- Workflow state management with priority scheduling
- Dynamic agent coordination and routing
- Parallel execution with dependency resolution
- Performance monitoring and adaptation
- Integration with intent detection and agent registry
- Comprehensive error handling and recovery
- Real-time workflow orchestration
"""

import asyncio
import uuid
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import structlog

from src.agents.intent_detection import IntentDetectionEngine, IntentResult
from src.events.ag_ui_emitter import AGUIEventEmitter

logger = structlog.get_logger(__name__)


class WorkflowState(str, Enum):
    """Workflow execution states."""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class WorkflowPriority(str, Enum):
    """Workflow priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"


class ExecutionMode(str, Enum):
    """Workflow execution modes."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"
    PIPELINE = "pipeline"


class AgentCapability(str, Enum):
    """Standard agent capabilities for workflow routing."""
    DATA_FETCH = "data_fetch"
    ANALYSIS = "analysis"
    MEMORY = "memory"
    RECOMMENDATION = "recommendation"
    COORDINATION = "coordination"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"
    NOTIFICATION = "notification"


class DependencyType(str, Enum):
    """Types of step dependencies."""
    SEQUENTIAL = "sequential"  # Must complete before this step
    DATA = "data"  # Data dependency
    CONDITIONAL = "conditional"  # Conditional dependency
    RESOURCE = "resource"  # Resource availability dependency


@dataclass
class WorkflowStep:
    """Individual workflow step with execution metadata."""
    step_id: str
    name: str
    description: str
    agent_type: str
    agent_capability: AgentCapability
    required_capabilities: List[AgentCapability] = field(default_factory=list)

    # Execution configuration
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    timeout_seconds: int = 300
    retry_count: int = 3
    retry_delay: float = 1.0

    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    dependency_types: Dict[str, DependencyType] = field(default_factory=dict)

    # Data flow
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    data_transformations: List[Dict[str, Any]] = field(default_factory=list)

    # Performance and optimization
    estimated_duration: float = 0.0
    priority_boost: float = 0.0
    resource_requirements: Dict[str, Any] = field(default_factory=dict)

    # Execution tracking
    state: WorkflowState = WorkflowState.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: float = 0.0
    retry_attempts: int = 0

    # Results and errors
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate step configuration."""
        if not self.step_id:
            raise ValueError("step_id cannot be empty")
        if not self.name:
            raise ValueError("name cannot be empty")
        if not self.agent_type:
            raise ValueError("agent_type cannot be empty")

        # Validate dependency types match dependencies
        for dep_id in self.dependencies:
            if dep_id not in self.dependency_types:
                self.dependency_types[dep_id] = DependencyType.SEQUENTIAL

    def is_ready(self, completed_steps: Set[str]) -> bool:
        """Check if step is ready for execution based on dependencies.

        Args:
            completed_steps: Set of completed step IDs

        Returns:
            True if all dependencies satisfied
        """
        for dep_id in self.dependencies:
            if dep_id not in completed_steps:
                return False
        return True

    def can_run_in_parallel(self, other_step: 'WorkflowStep') -> bool:
        """Check if this step can run in parallel with another step.

        Args:
            other_step: Other workflow step to check against

        Returns:
            True if steps can run in parallel
        """
        # Check for direct dependencies
        if other_step.step_id in self.dependencies:
            return False
        if self.step_id in other_step.dependencies:
            return False

        # Check for resource conflicts
        if self.resource_requirements.get("exclusive", False) and \
           other_step.resource_requirements.get("exclusive", False):
            return False

        return True

    def estimate_completion_time(self) -> datetime:
        """Calculate estimated completion time.

        Returns:
            Estimated completion datetime
        """
        if self.start_time and self.execution_time > 0:
            return self.start_time + timedelta(seconds=self.execution_time)

        base_time = datetime.utcnow()
        return base_time + timedelta(seconds=self.estimated_duration)

    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary representation.

        Returns:
            Dictionary representation of step
        """
        return {
            "step_id": self.step_id,
            "name": self.name,
            "description": self.description,
            "agent_type": self.agent_type,
            "agent_capability": self.agent_capability.value,
            "state": self.state.value,
            "execution_time": self.execution_time,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "dependencies": self.dependencies,
            "retry_attempts": self.retry_attempts,
            "has_result": self.result is not None,
            "has_error": self.error is not None,
            "estimated_duration": self.estimated_duration,
            "priority_boost": self.priority_boost
        }


@dataclass
class Workflow:
    """Complete workflow definition with execution metadata."""
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]

    # Workflow configuration
    priority: WorkflowPriority = WorkflowPriority.MEDIUM
    execution_mode: ExecutionMode = ExecutionMode.ADAPTIVE
    timeout_seconds: int = 3600
    max_parallel_steps: int = 5
    auto_retry: bool = True
    save_intermediate_results: bool = True

    # Execution tracking
    state: WorkflowState = WorkflowState.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_step: Optional[str] = None

    # Results and metrics
    results: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    # Context and data flow
    context: Dict[str, Any] = field(default_factory=dict)
    shared_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate workflow configuration."""
        if not self.workflow_id:
            raise ValueError("workflow_id cannot be empty")
        if not self.name:
            raise ValueError("name cannot be empty")
        if not self.steps:
            raise ValueError("workflow must have at least one step")

        # Validate step dependencies
        step_ids = {step.step_id for step in self.steps}
        for step in self.steps:
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    raise ValueError(f"Step {step.step_id} depends on non-existent step {dep_id}")

    def get_step_by_id(self, step_id: str) -> Optional[WorkflowStep]:
        """Get workflow step by ID.

        Args:
            step_id: Step identifier

        Returns:
            WorkflowStep if found, None otherwise
        """
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def get_ready_steps(self) -> List[WorkflowStep]:
        """Get steps ready for execution.

        Returns:
            List of steps that can be executed now
        """
        completed_steps = {
            step.step_id for step in self.steps
            if step.state == WorkflowState.COMPLETED
        }

        ready_steps = []
        for step in self.steps:
            if step.state == WorkflowState.PENDING and step.is_ready(completed_steps):
                ready_steps.append(step)

        # Sort by priority and estimated duration
        ready_steps.sort(key=lambda s: (-s.priority_boost, s.estimated_duration))
        return ready_steps

    def get_execution_groups(self) -> List[List[WorkflowStep]]:
        """Group steps that can be executed in parallel.

        Returns:
            List of execution groups (each group can run in parallel)
        """
        if self.execution_mode == ExecutionMode.SEQUENTIAL:
            return [[step] for step in self.steps]

        groups = []
        remaining_steps = self.steps.copy()

        while remaining_steps:
            current_group = []
            completed_steps = set()

            # Add steps from previous groups to completed set
            for group in groups:
                for step in group:
                    completed_steps.add(step.step_id)

            # Find steps that can run in parallel
            for step in remaining_steps[:]:
                if step.state == WorkflowState.PENDING and step.is_ready(completed_steps):
                    can_add = True

                    # Check compatibility with current group
                    for group_step in current_group:
                        if not step.can_run_in_parallel(group_step):
                            can_add = False
                            break

                    if can_add:
                        current_group.append(step)
                        remaining_steps.remove(step)

            if current_group:
                groups.append(current_group)
            else:
                # No progress - add remaining steps sequentially
                for step in remaining_steps:
                    groups.append([step])
                break

        return groups

    def calculate_progress(self) -> float:
        """Calculate workflow completion percentage.

        Returns:
            Progress percentage (0.0 - 1.0)
        """
        if not self.steps:
            return 1.0

        total_steps = len(self.steps)
        completed_steps = sum(
            1 for step in self.steps
            if step.state == WorkflowState.COMPLETED
        )

        return completed_steps / total_steps

    def get_critical_path(self) -> List[WorkflowStep]:
        """Calculate critical path of workflow.

        Returns:
            List of steps on the critical path
        """
        # Build dependency graph
        graph = {step.step_id: step.dependencies for step in self.steps}

        # Calculate longest path using dynamic programming
        def longest_path(step_id: str, memo: Dict[str, Tuple[float, List[str]]]) -> Tuple[float, List[str]]:
            if step_id in memo:
                return memo[step_id]

            step = self.get_step_by_id(step_id)
            if not step:
                return 0.0, []

            max_duration = 0.0
            best_path = []

            for dep_id in step.dependencies:
                duration, path = longest_path(dep_id, memo)
                if duration > max_duration:
                    max_duration = duration
                    best_path = path

            total_duration = max_duration + step.estimated_duration
            memo[step_id] = (total_duration, best_path + [step_id])
            return memo[step_id]

        # Find longest path from any step
        memo = {}
        max_total_duration = 0.0
        critical_path_ids = []

        for step in self.steps:
            duration, path = longest_path(step.step_id, memo)
            if duration > max_total_duration:
                max_total_duration = duration
                critical_path_ids = path

        return [self.get_step_by_id(step_id) for step_id in critical_path_ids]

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary representation.

        Returns:
            Dictionary representation of workflow
        """
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority.value,
            "state": self.state.value,
            "execution_mode": self.execution_mode.value,
            "progress": self.calculate_progress(),
            "step_count": len(self.steps),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "current_step": self.current_step,
            "total_execution_time": self.metrics.get("total_execution_time", 0),
            "errors": self.errors,
            "steps": [step.to_dict() for step in self.steps]
        }


class DynamicWorkflowEngine:
    """Advanced workflow engine with adaptive agent coordination.

    Features:
    - Dynamic workflow routing and optimization
    - Parallel execution with dependency management
    - Real-time performance monitoring and adaptation
    - Intelligent agent selection and coordination
    - Comprehensive error handling and recovery
    - Integration with intent detection and agent registry
    """

    def __init__(
        self,
        intent_engine: Optional[IntentDetectionEngine] = None,
        agent_registry: Optional[Dict[str, Any]] = None,
        max_concurrent_workflows: int = 10,
        default_timeout: int = 3600,
        enable_adaptation: bool = True,
        enable_monitoring: bool = True
    ):
        """Initialize dynamic workflow engine.

        Args:
            intent_engine: Intent detection engine for intelligent routing
            agent_registry: Registry of available agents and capabilities
            max_concurrent_workflows: Maximum concurrent workflow executions
            default_timeout: Default workflow timeout in seconds
            enable_adaptation: Enable adaptive routing and optimization
            enable_monitoring: Enable performance monitoring
        """
        self.engine_id = f"workflow_engine_{uuid.uuid4().hex[:8]}"
        self.intent_engine = intent_engine or IntentDetectionEngine()
        self.agent_registry = agent_registry or {}

        # Configuration
        self.max_concurrent_workflows = max_concurrent_workflows
        self.default_timeout = default_timeout
        self.enable_adaptation = enable_adaptation
        self.enable_monitoring = enable_monitoring

        # Workflow tracking
        self.active_workflows: Dict[str, Workflow] = {}
        self.completed_workflows: Dict[str, Workflow] = {}
        self.workflow_queue: List[Tuple[WorkflowPriority, Workflow]] = []

        # Performance monitoring
        self.performance_metrics: Dict[str, Any] = defaultdict(list)
        self.adaptation_rules: List[Callable] = []
        self.resource_usage: Dict[str, Any] = defaultdict(int)

        # Agent coordination
        self.agent_load: Dict[str, int] = defaultdict(int)
        self.agent_capabilities: Dict[str, Set[AgentCapability]] = defaultdict(set)
        self.execution_history: List[Dict[str, Any]] = []

        # Event handling
        self.event_emitters: Dict[str, AGUIEventEmitter] = {}
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)

        # Logging
        self.logger = logger.bind(component="dynamic_workflow_engine", engine_id=self.engine_id)

        self.logger.info(
            "dynamic_workflow_engine_initialized",
            max_concurrent_workflows=max_concurrent_workflows,
            default_timeout=default_timeout,
            enable_adaptation=enable_adaptation,
            enable_monitoring=enable_monitoring,
            registered_agents=len(self.agent_registry)
        )

    async def create_workflow(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]],
        priority: WorkflowPriority = WorkflowPriority.MEDIUM,
        context: Optional[Dict[str, Any]] = None
    ) -> Workflow:
        """Create a new workflow from step definitions.

        Args:
            name: Workflow name
            description: Workflow description
            steps: List of step definitions
            priority: Workflow priority
            context: Initial workflow context

        Returns:
            Created workflow instance
        """
        workflow_id = f"workflow_{uuid.uuid4().hex[:8]}"

        # Convert step definitions to WorkflowStep objects
        workflow_steps = []
        for step_def in steps:
            step = WorkflowStep(
                step_id=step_def.get("step_id", f"step_{uuid.uuid4().hex[:8]}"),
                name=step_def["name"],
                description=step_def.get("description", ""),
                agent_type=step_def["agent_type"],
                agent_capability=AgentCapability(step_def.get("agent_capability", "analysis")),
                required_capabilities=[
                    AgentCapability(cap) for cap in step_def.get("required_capabilities", [])
                ],
                execution_mode=ExecutionMode(step_def.get("execution_mode", "sequential")),
                timeout_seconds=step_def.get("timeout_seconds", 300),
                retry_count=step_def.get("retry_count", 3),
                dependencies=step_def.get("dependencies", []),
                estimated_duration=step_def.get("estimated_duration", 60.0),
                priority_boost=step_def.get("priority_boost", 0.0),
                resource_requirements=step_def.get("resource_requirements", {})
            )
            workflow_steps.append(step)

        # Create workflow
        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            steps=workflow_steps,
            priority=priority,
            context=context or {}
        )

        self.logger.info(
            "workflow_created",
            workflow_id=workflow_id,
            name=name,
            step_count=len(workflow_steps),
            priority=priority.value
        )

        return workflow

    async def execute_workflow(
        self,
        workflow: Workflow,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute a workflow with event streaming.

        Args:
            workflow: Workflow to execute
            context: Additional execution context
            session_id: Session ID for event streaming

        Yields:
            Execution events and results
        """
        # Initialize workflow execution
        workflow.state = WorkflowState.INITIALIZING
        workflow.start_time = datetime.utcnow()
        workflow.context.update(context or {})

        # Setup event emitter
        emitter = AGUIEventEmitter(session_id=session_id or workflow.workflow_id)
        self.event_emitters[workflow.workflow_id] = emitter

        # Add to active workflows
        self.active_workflows[workflow.workflow_id] = workflow

        try:
            # Emit workflow started
            yield emitter.emit_workflow_started(workflow.workflow_id, workflow.name)

            self.logger.info(
                "workflow_execution_started",
                workflow_id=workflow.workflow_id,
                name=workflow.name,
                priority=workflow.priority.value,
                step_count=len(workflow.steps)
            )

            # Analyze workflow for optimization
            if self.enable_adaptation:
                await self._optimize_workflow(workflow)

            # Execute workflow based on mode
            if workflow.execution_mode == ExecutionMode.SEQUENTIAL:
                async for event in self._execute_sequential(workflow, emitter):
                    yield event
            elif workflow.execution_mode == ExecutionMode.PARALLEL:
                async for event in self._execute_parallel(workflow, emitter):
                    yield event
            elif workflow.execution_mode == ExecutionMode.ADAPTIVE:
                async for event in self._execute_adaptive(workflow, emitter):
                    yield event
            elif workflow.execution_mode == ExecutionMode.PIPELINE:
                async for event in self._execute_pipeline(workflow, emitter):
                    yield event
            else:
                raise ValueError(f"Unsupported execution mode: {workflow.execution_mode}")

            # Mark workflow as completed
            workflow.state = WorkflowState.COMPLETED
            workflow.end_time = datetime.utcnow()

            # Calculate final metrics
            total_time = (workflow.end_time - workflow.start_time).total_seconds()
            workflow.metrics["total_execution_time"] = total_time
            workflow.metrics["success_rate"] = sum(
                1 for step in workflow.steps
                if step.state == WorkflowState.COMPLETED
            ) / len(workflow.steps)

            # Move to completed workflows
            self.completed_workflows[workflow.workflow_id] = workflow
            del self.active_workflows[workflow.workflow_id]

            # Emit workflow completed
            yield emitter.emit_workflow_completed(
                workflow=workflow.workflow_id,
                account_id=workflow.context.get("account_id", "system"),
                final_output=workflow.to_dict()
            )

            self.logger.info(
                "workflow_execution_completed",
                workflow_id=workflow.workflow_id,
                total_time=total_time,
                success_rate=workflow.metrics["success_rate"]
            )

        except Exception as e:
            # Handle workflow execution error
            workflow.state = WorkflowState.FAILED
            workflow.end_time = datetime.utcnow()
            workflow.errors.append(str(e))

            self.logger.error(
                "workflow_execution_failed",
                workflow_id=workflow.workflow_id,
                error=str(e),
                stack_trace=traceback.format_exc()
            )

            # Emit workflow error
            yield emitter.emit_agent_error(
                agent="workflow_engine",
                step=0,
                error_type="workflow_execution_error",
                error_message=str(e),
                stack_trace=traceback.format_exc()
            )

            # Emit workflow completed with error
            yield emitter.emit_workflow_completed(
                workflow=workflow.workflow_id,
                account_id=workflow.context.get("account_id", "system"),
                final_output=workflow.to_dict()
            )

            raise

        finally:
            # Cleanup
            if workflow.workflow_id in self.event_emitters:
                del self.event_emitters[workflow.workflow_id]

    async def _execute_sequential(
        self,
        workflow: Workflow,
        emitter: AGUIEventEmitter
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute workflow steps sequentially.

        Args:
            workflow: Workflow to execute
            emitter: Event emitter for streaming

        Yields:
            Execution events
        """
        workflow.state = WorkflowState.RUNNING

        for step in workflow.steps:
            workflow.current_step = step.step_id

            # Emit step started
            yield emitter.emit_agent_started(
                agent=step.agent_type,
                step=workflow.steps.index(step) + 1,
                task=step.name
            )

            # Execute step
            try:
                step.state = WorkflowState.RUNNING
                step.start_time = datetime.utcnow()

                # Get agent and execute step
                result = await self._execute_step(step, workflow)

                step.state = WorkflowState.COMPLETED
                step.end_time = datetime.utcnow()
                step.execution_time = (step.end_time - step.start_time).total_seconds()
                step.result = result

                # Store result in workflow context
                workflow.results[step.step_id] = result

                # Emit step completed
                yield emitter.emit_agent_completed(
                    agent=step.agent_type,
                    step=workflow.steps.index(step) + 1,
                    output=result
                )

                self.logger.info(
                    "workflow_step_completed",
                    workflow_id=workflow.workflow_id,
                    step_id=step.step_id,
                    execution_time=step.execution_time
                )

            except Exception as e:
                step.state = WorkflowState.FAILED
                step.error = str(e)
                workflow.errors.append(f"Step {step.step_id} failed: {str(e)}")

                # Check if we should continue
                if step.retry_count > step.retry_attempts:
                    self.logger.error(
                        "workflow_step_failed",
                        workflow_id=workflow.workflow_id,
                        step_id=step.step_id,
                        error=str(e)
                    )

                    # Emit step error
                    yield emitter.emit_agent_error(
                        agent=step.agent_type,
                        step=workflow.steps.index(step) + 1,
                        error_type="step_execution_error",
                        error_message=str(e)
                    )

                    # Continue to next step based on workflow configuration
                    if not workflow.auto_retry:
                        raise

                # Retry logic
                step.retry_attempts += 1
                await asyncio.sleep(step.retry_delay * step.retry_attempts)

                # Retry step
                continue

    async def _execute_parallel(
        self,
        workflow: Workflow,
        emitter: AGUIEventEmitter
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute workflow steps in parallel where possible.

        Args:
            workflow: Workflow to execute
            emitter: Event emitter for streaming

        Yields:
            Execution events
        """
        workflow.state = WorkflowState.RUNNING

        # Get execution groups
        execution_groups = workflow.get_execution_groups()

        for group_idx, group in enumerate(execution_groups):
            # Limit parallel execution
            concurrent_steps = group[:workflow.max_parallel_steps]

            # Create tasks for concurrent execution
            tasks = []
            for step in concurrent_steps:
                task = asyncio.create_task(
                    self._execute_step_async(step, workflow, emitter, group_idx)
                )
                tasks.append(task)

            # Wait for all steps in group to complete
            await asyncio.gather(*tasks, return_exceptions=True)

            # Check if any step failed
            failed_steps = [
                step for step in concurrent_steps
                if step.state == WorkflowState.FAILED
            ]

            if failed_steps and not workflow.auto_retry:
                raise RuntimeError(f"Parallel execution group {group_idx} failed")

    async def _execute_adaptive(
        self,
        workflow: Workflow,
        emitter: AGUIEventEmitter
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute workflow with adaptive routing and optimization.

        Args:
            workflow: Workflow to execute
            emitter: Event emitter for streaming

        Yields:
            Execution events
        """
        workflow.state = WorkflowState.RUNNING

        # Adaptive execution with real-time optimization
        while True:
            # Get ready steps
            ready_steps = workflow.get_ready_steps()

            if not ready_steps:
                # Check if workflow is complete
                if all(step.state in [WorkflowState.COMPLETED, WorkflowState.FAILED] for step in workflow.steps):
                    break
                else:
                    # Wait for running steps to complete
                    await asyncio.sleep(0.1)
                    continue

            # Select optimal execution strategy
            if self.enable_adaptation:
                await self._adapt_execution_strategy(workflow, ready_steps)

            # Execute ready steps in parallel (with limits)
            concurrent_steps = ready_steps[:workflow.max_parallel_steps]

            # Execute steps concurrently
            tasks = []
            for step in concurrent_steps:
                task = asyncio.create_task(
                    self._execute_step_async(step, workflow, emitter, 0)
                )
                tasks.append(task)

            # Wait for completion
            await asyncio.gather(*tasks, return_exceptions=True)

            # Update performance metrics
            if self.enable_monitoring:
                await self._update_performance_metrics(workflow)

    async def _execute_pipeline(
        self,
        workflow: Workflow,
        emitter: AGUIEventEmitter
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute workflow as a data pipeline.

        Args:
            workflow: Workflow to execute
            emitter: Event emitter for streaming

        Yields:
            Execution events
        """
        workflow.state = WorkflowState.RUNNING

        # Pipeline execution with data flow optimization
        pipeline_data = {}

        for step in workflow.steps:
            workflow.current_step = step.step_id

            # Prepare input data
            step_input = {
                "pipeline_data": pipeline_data,
                "workflow_context": workflow.context,
                "step_context": step.data_transformations
            }

            # Execute step
            try:
                step.state = WorkflowState.RUNNING
                step.start_time = datetime.utcnow()

                result = await self._execute_step(step, workflow, step_input)

                step.state = WorkflowState.COMPLETED
                step.end_time = datetime.utcnow()
                step.execution_time = (step.end_time - step.start_time).total_seconds()
                step.result = result

                # Add to pipeline data
                pipeline_data[step.step_id] = result
                workflow.results[step.step_id] = result

                # Emit step completed
                yield emitter.emit_agent_completed(
                    agent=step.agent_type,
                    step=workflow.steps.index(step) + 1,
                    output=result
                )

            except Exception as e:
                step.state = WorkflowState.FAILED
                step.error = str(e)
                workflow.errors.append(f"Pipeline step {step.step_id} failed: {str(e)}")
                raise

    async def _execute_step_async(
        self,
        step: WorkflowStep,
        workflow: Workflow,
        emitter: AGUIEventEmitter,
        group_idx: int
    ) -> None:
        """Execute a single step asynchronously.

        Args:
            step: Step to execute
            workflow: Parent workflow
            emitter: Event emitter
            group_idx: Group index for parallel execution
        """
        try:
            step.state = WorkflowState.RUNNING
            step.start_time = datetime.utcnow()

            # Emit step started
            emitter.emit_agent_started(
                agent=step.agent_type,
                step=workflow.steps.index(step) + 1,
                task=step.name
            )

            # Execute step
            result = await self._execute_step(step, workflow)

            step.state = WorkflowState.COMPLETED
            step.end_time = datetime.utcnow()
            step.execution_time = (step.end_time - step.start_time).total_seconds()
            step.result = result

            # Store result
            workflow.results[step.step_id] = result

            # Emit step completed
            emitter.emit_agent_completed(
                agent=step.agent_type,
                step=workflow.steps.index(step) + 1,
                output=result
            )

        except Exception as e:
            step.state = WorkflowState.FAILED
            step.error = str(e)
            workflow.errors.append(f"Step {step.step_id} failed: {str(e)}")

            # Emit step error
            emitter.emit_agent_error(
                agent=step.agent_type,
                step=workflow.steps.index(step) + 1,
                error_type="step_execution_error",
                error_message=str(e)
            )

    async def _execute_step(
        self,
        step: WorkflowStep,
        workflow: Workflow,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a single workflow step.

        Args:
            step: Step to execute
            workflow: Parent workflow
            input_data: Additional input data

        Returns:
            Step execution result
        """
        # Prepare step context
        step_context = {
            "workflow_id": workflow.workflow_id,
            "step_id": step.step_id,
            "agent_type": step.agent_type,
            "agent_capability": step.agent_capability,
            "workflow_context": workflow.context,
            "shared_data": workflow.shared_data,
            "step_results": workflow.results,
            "dependencies": step.dependencies,
            "timeout": step.timeout_seconds
        }

        if input_data:
            step_context.update(input_data)

        # Select appropriate agent
        agent = await self._select_agent(step, workflow)

        if not agent:
            raise RuntimeError(f"No suitable agent found for step {step.step_id}")

        # Execute with agent
        try:
            # Update agent load
            self.agent_load[step.agent_type] += 1

            # Execute step logic (this would integrate with actual agents)
            result = await self._execute_with_agent(agent, step_context)

            # Apply data transformations
            if step.data_transformations:
                result = await self._apply_data_transformations(
                    result, step.data_transformations
                )

            # Update shared data
            if workflow.save_intermediate_results:
                workflow.shared_data[step.step_id] = result

            return result

        finally:
            # Update agent load
            self.agent_load[step.agent_type] -= 1

    async def _select_agent(
        self,
        step: WorkflowStep,
        workflow: Workflow
    ) -> Optional[Any]:
        """Select optimal agent for step execution.

        Args:
            step: Step requiring agent
            workflow: Parent workflow

        Returns:
            Selected agent instance
        """
        # Get available agents for required capability
        available_agents = []

        for agent_id, agent_info in self.agent_registry.items():
            if step.agent_capability in agent_info.get("capabilities", []):
                # Check agent load
                current_load = self.agent_load.get(agent_id, 0)
                max_load = agent_info.get("max_concurrent_tasks", 5)

                if current_load < max_load:
                    available_agents.append((agent_id, agent_info, current_load))

        if not available_agents:
            return None

        # Sort by load (prefer less loaded agents)
        available_agents.sort(key=lambda x: x[2])

        # Return the best agent
        agent_id, agent_info, _ = available_agents[0]

        # Create agent instance (this would integrate with actual agent system)
        return {
            "agent_id": agent_id,
            "agent_type": step.agent_type,
            "capability": step.agent_capability,
            "config": agent_info
        }

    async def _execute_with_agent(
        self,
        agent: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute step with selected agent.

        Args:
            agent: Agent configuration
            context: Execution context

        Returns:
            Execution result
        """
        # This would integrate with the actual agent execution system
        # For now, simulate execution with timing
        start_time = time.time()

        # Simulate agent processing based on capability
        capability = agent["capability"]

        if capability == AgentCapability.DATA_FETCH:
            await asyncio.sleep(0.5)  # Simulate data fetch
            result = {
                "status": "success",
                "data": {"records": [], "count": 0},
                "message": "Data fetch completed"
            }
        elif capability == AgentCapability.ANALYSIS:
            await asyncio.sleep(1.0)  # Simulate analysis
            result = {
                "status": "success",
                "analysis": {"insights": [], "confidence": 0.8},
                "message": "Analysis completed"
            }
        elif capability == AgentCapability.MEMORY:
            await asyncio.sleep(0.3)  # Simulate memory retrieval
            result = {
                "status": "success",
                "memory": {"context": [], "patterns": []},
                "message": "Memory retrieval completed"
            }
        elif capability == AgentCapability.RECOMMENDATION:
            await asyncio.sleep(0.8)  # Simulate recommendation generation
            result = {
                "status": "success",
                "recommendations": [],
                "confidence": 0.9,
                "message": "Recommendations generated"
            }
        else:
            await asyncio.sleep(0.5)  # Default processing
            result = {
                "status": "success",
                "output": f"Processed by {agent['agent_type']}",
                "message": "Step completed successfully"
            }

        execution_time = time.time() - start_time

        return {
            **result,
            "execution_time": execution_time,
            "agent_id": agent["agent_id"],
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _apply_data_transformations(
        self,
        data: Dict[str, Any],
        transformations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply data transformations to step result.

        Args:
            data: Original data
            transformations: List of transformation rules

        Returns:
            Transformed data
        """
        result = data.copy()

        for transform in transformations:
            transform_type = transform.get("type")

            if transform_type == "filter":
                # Filter data based on criteria
                criteria = transform.get("criteria", {})
                result = {k: v for k, v in result.items() if self._meets_criteria(v, criteria)}

            elif transform_type == "map":
                # Map data fields
                field_mapping = transform.get("mapping", {})
                result = {field_mapping.get(k, k): v for k, v in result.items()}

            elif transform_type == "aggregate":
                # Aggregate data
                aggregation_type = transform.get("aggregate_type", "sum")
                if aggregation_type == "sum" and isinstance(result.get("value"), (int, float)):
                    result["total"] = sum(result.get("values", [result["value"]]))

            elif transform_type == "format":
                # Format data
                format_type = transform.get("format_type", "json")
                if format_type == "string":
                    result["formatted"] = str(result)

        return result

    def _meets_criteria(self, value: Any, criteria: Dict[str, Any]) -> bool:
        """Check if value meets filter criteria.

        Args:
            value: Value to check
            criteria: Filter criteria

        Returns:
            True if value meets criteria
        """
        if not criteria:
            return True

        for field, condition in criteria.items():
            if isinstance(value, dict) and field in value:
                field_value = value[field]

                if isinstance(condition, dict):
                    if condition.get("equals") is not None:
                        if field_value != condition["equals"]:
                            return False
                    elif condition.get("greater_than") is not None:
                        if field_value <= condition["greater_than"]:
                            return False
                    elif condition.get("less_than") is not None:
                        if field_value >= condition["less_than"]:
                            return False
                else:
                    if field_value != condition:
                        return False

        return True

    async def _optimize_workflow(self, workflow: Workflow) -> None:
        """Optimize workflow execution based on historical data.

        Args:
            workflow: Workflow to optimize
        """
        # Get historical performance data
        similar_workflows = [
            w for w in self.execution_history[-100:]  # Last 100 executions
            if len(w.get("steps", [])) == len(workflow.steps)
        ]

        if similar_workflows:
            # Calculate average execution times
            avg_times = {}
            for step in workflow.steps:
                step_times = [
                    w.get("step_times", {}).get(step.step_id, step.estimated_duration)
                    for w in similar_workflows
                ]
                if step_times:
                    avg_times[step.step_id] = sum(step_times) / len(step_times)

            # Update step estimates
            for step in workflow.steps:
                if step.step_id in avg_times:
                    step.estimated_duration = avg_times[step.step_id]

            # Optimize execution order based on critical path
            critical_path = workflow.get_critical_path()
            for step in critical_path:
                step.priority_boost += 10

    async def _adapt_execution_strategy(
        self,
        workflow: Workflow,
        ready_steps: List[WorkflowStep]
    ) -> None:
        """Adapt execution strategy based on current conditions.

        Args:
            workflow: Current workflow
            ready_steps: Steps ready for execution
        """
        # Check system load
        total_load = sum(self.agent_load.values())

        if total_load > self.max_concurrent_workflows * 0.8:
            # High load - prioritize critical steps
            for step in ready_steps:
                if step.priority_boost < 5:
                    step.priority_boost += 5

        # Check for bottlenecks
        bottleneck_agents = [
            agent for agent, load in self.agent_load.items()
            if load > 3
        ]

        if bottleneck_agents:
            # Redirect load from bottleneck agents
            for step in ready_steps:
                if step.agent_type in bottleneck_agents:
                    # Try to find alternative agent
                    alternative_agents = [
                        agent for agent, info in self.agent_registry.items()
                        if step.agent_capability in info.get("capabilities", [])
                        and agent not in bottleneck_agents
                    ]

                    if alternative_agents:
                        step.agent_type = alternative_agents[0]

    async def _update_performance_metrics(self, workflow: Workflow) -> None:
        """Update performance metrics for monitoring.

        Args:
            workflow: Current workflow
        """
        current_time = datetime.utcnow()

        # Update workflow metrics
        workflow.metrics["last_updated"] = current_time.isoformat()
        workflow.metrics["agent_load"] = dict(self.agent_load)
        workflow.metrics["resource_usage"] = dict(self.resource_usage)

        # Update engine metrics
        self.performance_metrics["workflow_count"].append(len(self.active_workflows))
        self.performance_metrics["total_agent_load"].append(sum(self.agent_load.values()))
        self.performance_metrics["timestamp"].append(current_time)

        # Keep only last 1000 data points
        for key in self.performance_metrics:
            if len(self.performance_metrics[key]) > 1000:
                self.performance_metrics[key] = self.performance_metrics[key][-1000:]

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow status dictionary
        """
        workflow = self.active_workflows.get(workflow_id) or \
                  self.completed_workflows.get(workflow_id)

        if not workflow:
            return None

        return workflow.to_dict()

    def get_engine_metrics(self) -> Dict[str, Any]:
        """Get workflow engine performance metrics.

        Returns:
            Engine metrics dictionary
        """
        return {
            "engine_id": self.engine_id,
            "active_workflows": len(self.active_workflows),
            "completed_workflows": len(self.completed_workflows),
            "total_workflows": len(self.active_workflows) + len(self.completed_workflows),
            "agent_load": dict(self.agent_load),
            "resource_usage": dict(self.resource_usage),
            "performance_metrics": dict(self.performance_metrics),
            "registered_agents": len(self.agent_registry),
            "max_concurrent_workflows": self.max_concurrent_workflows,
            "enable_adaptation": self.enable_adaptation,
            "enable_monitoring": self.enable_monitoring
        }

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            True if workflow was cancelled
        """
        workflow = self.active_workflows.get(workflow_id)

        if not workflow:
            return False

        workflow.state = WorkflowState.CANCELLED
        workflow.end_time = datetime.utcnow()

        # Move to completed workflows
        self.completed_workflows[workflow_id] = workflow
        del self.active_workflows[workflow_id]

        self.logger.info(
            "workflow_cancelled",
            workflow_id=workflow_id,
            name=workflow.name
        )

        return True

    def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: List[AgentCapability],
        max_concurrent_tasks: int = 5,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register an agent with the workflow engine.

        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent
            capabilities: List of agent capabilities
            max_concurrent_tasks: Maximum concurrent tasks for agent
            config: Additional agent configuration
        """
        self.agent_registry[agent_id] = {
            "agent_type": agent_type,
            "capabilities": [cap.value for cap in capabilities],
            "max_concurrent_tasks": max_concurrent_tasks,
            "config": config or {}
        }

        self.agent_capabilities[agent_id] = set(capabilities)

        self.logger.info(
            "agent_registered",
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=[cap.value for cap in capabilities],
            max_concurrent_tasks=max_concurrent_tasks
        )

    def add_adaptation_rule(self, rule: Callable[[Workflow, List[WorkflowStep]], None]) -> None:
        """Add an adaptation rule for workflow optimization.

        Args:
            rule: Adaptation rule function
        """
        self.adaptation_rules.append(rule)

        self.logger.info(
            "adaptation_rule_added",
            rule_name=rule.__name__,
            total_rules=len(self.adaptation_rules)
        )

    def __repr__(self) -> str:
        """String representation of the workflow engine."""
        return (
            f"<DynamicWorkflowEngine "
            f"engine_id={self.engine_id} "
            f"active_workflows={len(self.active_workflows)} "
            f"registered_agents={len(self.agent_registry)} "
            f"adaptation_enabled={self.enable_adaptation}>"
        )