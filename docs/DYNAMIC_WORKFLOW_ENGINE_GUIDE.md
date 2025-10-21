# Dynamic Workflow Engine Guide

## Overview

The Dynamic Workflow Engine is a production-ready, adaptive workflow orchestration system designed for intelligent multi-agent coordination. It provides comprehensive workflow management with parallel execution, dependency resolution, performance optimization, and real-time adaptation.

## Key Features

### 🚀 Core Capabilities
- **Adaptive Agent Coordination**: Intelligent routing and selection of agents based on capabilities and load
- **Parallel Execution**: Concurrent step execution with automatic dependency resolution
- **Dynamic Routing**: Real-time workflow adaptation based on system conditions and performance
- **Performance Monitoring**: Comprehensive metrics collection and analysis
- **Error Handling**: Robust error recovery and retry mechanisms
- **Intent Integration**: Seamless integration with the intent detection system

### 🎯 Execution Modes
1. **Sequential**: Traditional step-by-step execution
2. **Parallel**: Maximum concurrency with dependency management
3. **Adaptive**: Intelligent routing with real-time optimization
4. **Pipeline**: Data flow optimized processing

### 📊 Priority Levels
- **CRITICAL**: Highest priority, immediate execution
- **HIGH**: High priority, expedited processing
- **MEDIUM**: Standard priority, normal processing
- **LOW**: Low priority, background processing
- **BACKGROUND**: Lowest priority, resource-aware processing

## Architecture

### Core Components

#### 1. WorkflowStep
Individual workflow step with execution metadata:
```python
@dataclass
class WorkflowStep:
    step_id: str
    name: str
    agent_type: str
    agent_capability: AgentCapability
    dependencies: List[str]
    execution_mode: ExecutionMode
    timeout_seconds: int
    retry_count: int
    estimated_duration: float
    state: WorkflowState
    result: Optional[Dict[str, Any]]
```

#### 2. Workflow
Complete workflow definition with execution tracking:
```python
@dataclass
class Workflow:
    workflow_id: str
    name: str
    steps: List[WorkflowStep]
    priority: WorkflowPriority
    execution_mode: ExecutionMode
    state: WorkflowState
    context: Dict[str, Any]
    results: Dict[str, Any]
```

#### 3. DynamicWorkflowEngine
Main orchestration engine with adaptive capabilities:
```python
class DynamicWorkflowEngine:
    def __init__(self, max_concurrent_workflows: int, enable_adaptation: bool)
    async def create_workflow(self, name: str, steps: List[Dict]) -> Workflow
    async def execute_workflow(self, workflow: Workflow) -> AsyncGenerator[Dict, None]
    def register_agent(self, agent_id: str, capabilities: List[AgentCapability])
    async def cancel_workflow(self, workflow_id: str) -> bool
```

## Getting Started

### 1. Basic Setup

```python
from src.agents.dynamic_workflow_engine import (
    DynamicWorkflowEngine,
    WorkflowPriority,
    ExecutionMode,
    AgentCapability
)

# Initialize the workflow engine
engine = DynamicWorkflowEngine(
    max_concurrent_workflows=10,
    enable_adaptation=True,
    enable_monitoring=True
)
```

### 2. Register Agents

```python
# Register specialized agents
engine.register_agent(
    agent_id="zoho_scout",
    agent_type="ZohoDataScout",
    capabilities=[AgentCapability.DATA_FETCH],
    max_concurrent_tasks=3
)

engine.register_agent(
    agent_id="risk_analyzer",
    agent_type="RiskAnalyzer",
    capabilities=[AgentCapability.ANALYSIS, AgentCapability.VALIDATION],
    max_concurrent_tasks=2
)

engine.register_agent(
    agent_id="memory_analyst",
    agent_type="MemoryAnalyst",
    capabilities=[AgentCapability.MEMORY],
    max_concurrent_tasks=2
)
```

### 3. Create Workflow Steps

```python
steps = [
    {
        "step_id": "fetch_account_data",
        "name": "Fetch Account Data",
        "description": "Retrieve account information from Zoho CRM",
        "agent_type": "zoho_scout",
        "agent_capability": "data_fetch",
        "estimated_duration": 5.0,
        "timeout_seconds": 30,
        "retry_count": 3
    },
    {
        "step_id": "analyze_risk",
        "name": "Analyze Risk Factors",
        "description": "Perform comprehensive risk analysis",
        "agent_type": "risk_analyzer",
        "agent_capability": "analysis",
        "dependencies": ["fetch_account_data"],
        "estimated_duration": 3.0,
        "timeout_seconds": 30
    },
    {
        "step_id": "get_historical_context",
        "name": "Get Historical Context",
        "description": "Retrieve historical patterns and trends",
        "agent_type": "memory_analyst",
        "agent_capability": "memory",
        "dependencies": ["fetch_account_data"],
        "estimated_duration": 2.0,
        "timeout_seconds": 30
    },
    {
        "step_id": "generate_recommendations",
        "name": "Generate Recommendations",
        "description": "Create actionable recommendations",
        "agent_type": "recommender",
        "agent_capability": "recommendation",
        "dependencies": ["analyze_risk", "get_historical_context"],
        "estimated_duration": 4.0,
        "timeout_seconds": 30
    }
]
```

### 4. Create and Execute Workflow

```python
# Create workflow
workflow = await engine.create_workflow(
    name="Account Analysis Workflow",
    description="Complete account analysis with risk assessment",
    steps=steps,
    priority=WorkflowPriority.HIGH,
    execution_mode=ExecutionMode.ADAPTIVE,
    context={"account_id": "ACC-12345"}
)

# Execute workflow with event streaming
async for event in engine.execute_workflow(
    workflow,
    context={"account_id": "ACC-12345"},
    session_id="user_session_123"
):
    if event.get("event") == "workflow_started":
        print(f"🚀 Workflow started: {event['data']['name']}")

    elif event.get("event") == "agent_started":
        step_data = event['data']
        print(f"🔵 Starting step {step_data['step']}: {step_data['task']}")

    elif event.get("event") == "agent_stream":
        stream_data = event['data']
        print(f"📡 {stream_data.get('content', '')}")

    elif event.get("event") == "agent_completed":
        step_data = event['data']
        print(f"🟢 Completed step {step_data['step']}")

    elif event.get("event") == "agent_error":
        error_data = event['data']
        print(f"❌ Error in step {error_data['step']}: {error_data['error_message']}")

    elif event.get("event") == "workflow_completed":
        final_output = event['data']['final_output']
        print(f"🎉 Workflow completed!")
        print(f"   Success rate: {final_output.get('success_rate', 0):.1%}")
        print(f"   Execution time: {final_output.get('total_execution_time', 0):.2f}s")
        break
```

## Advanced Usage

### 1. Parallel Execution

```python
# Create workflow with parallel steps
parallel_steps = [
    {
        "step_id": "fetch_data_1",
        "name": "Fetch Data Source 1",
        "agent_type": "data_fetcher",
        "agent_capability": "data_fetch",
        "estimated_duration": 2.0
    },
    {
        "step_id": "fetch_data_2",
        "name": "Fetch Data Source 2",
        "agent_type": "data_fetcher",
        "agent_capability": "data_fetch",
        "estimated_duration": 2.0
    },
    {
        "step_id": "fetch_data_3",
        "name": "Fetch Data Source 3",
        "agent_type": "data_fetcher",
        "agent_capability": "data_fetch",
        "estimated_duration": 2.0
    },
    {
        "step_id": "aggregate_results",
        "name": "Aggregate Results",
        "agent_type": "aggregator",
        "agent_capability": "analysis",
        "dependencies": ["fetch_data_1", "fetch_data_2", "fetch_data_3"],
        "estimated_duration": 1.0
    }
]

# Create parallel workflow
parallel_workflow = await engine.create_workflow(
    name="Parallel Data Processing",
    steps=parallel_steps,
    execution_mode=ExecutionMode.PARALLEL,
    max_parallel_steps=5
)
```

### 2. Data Transformations

```python
# Steps with data transformations
transform_steps = [
    {
        "step_id": "fetch_raw_data",
        "name": "Fetch Raw Data",
        "agent_type": "data_fetcher",
        "agent_capability": "data_fetch",
        "data_transformations": [
            {
                "type": "filter",
                "criteria": {"status": {"equals": "active"}}
            }
        ]
    },
    {
        "step_id": "process_data",
        "name": "Process Data",
        "agent_type": "processor",
        "agent_capability": "transformation",
        "dependencies": ["fetch_raw_data"],
        "data_transformations": [
            {
                "type": "map",
                "mapping": {"records": "processed_records"}
            },
            {
                "type": "aggregate",
                "aggregate_type": "sum"
            }
        ]
    }
]
```

### 3. Custom Adaptation Rules

```python
def custom_adaptation_rule(workflow: Workflow, ready_steps: List[WorkflowStep]):
    """Custom adaptation rule for workflow optimization."""
    # Prioritize steps with critical path impact
    critical_path = workflow.get_critical_path()
    for step in ready_steps:
        if step in critical_path:
            step.priority_boost += 20

# Add custom adaptation rule
engine.add_adaptation_rule(custom_adaptation_rule)
```

### 4. Error Handling and Recovery

```python
# Steps with robust error handling
robust_steps = [
    {
        "step_id": "critical_step",
        "name": "Critical Step",
        "agent_type": "specialist",
        "agent_capability": "analysis",
        "timeout_seconds": 60,
        "retry_count": 5,
        "retry_delay": 2.0
    }
]

# Execute with error handling
try:
    async for event in engine.execute_workflow(workflow):
        if event.get("event") == "agent_error":
            error_data = event['data']
            print(f"Handling error: {error_data['error_message']}")
            # Implement custom error handling logic

except Exception as e:
    print(f"Workflow execution failed: {e}")
    # Implement recovery logic
```

## Agent Capabilities

### Supported Capabilities

```python
class AgentCapability(str, Enum):
    DATA_FETCH = "data_fetch"          # Retrieve data from external sources
    ANALYSIS = "analysis"              # Analyze and process data
    MEMORY = "memory"                  # Access historical data and patterns
    RECOMMENDATION = "recommendation"  # Generate recommendations
    COORDINATION = "coordination"      # Coordinate between agents
    VALIDATION = "validation"          # Validate data and results
    TRANSFORMATION = "transformation"  # Transform and format data
    NOTIFICATION = "notification"      # Send notifications
```

### Agent Registration

```python
# Register agent with multiple capabilities
engine.register_agent(
    agent_id="multi_specialist",
    agent_type="MultiSpecialist",
    capabilities=[
        AgentCapability.ANALYSIS,
        AgentCapability.VALIDATION,
        AgentCapability.RECOMMENDATION
    ],
    max_concurrent_tasks=3,
    config={
        "model": "advanced",
        "timeout": 300,
        "custom_settings": {"optimization": True}
    }
)
```

## Performance Monitoring

### Engine Metrics

```python
# Get real-time engine metrics
metrics = engine.get_engine_metrics()

print(f"Active workflows: {metrics['active_workflows']}")
print(f"Completed workflows: {metrics['completed_workflows']}")
print(f"Agent load distribution: {metrics['agent_load']}")
print(f"Resource usage: {metrics['resource_usage']}")

# Performance history
performance_history = metrics['performance_metrics']
print(f"Recent workload: {performance_history['workflow_count'][-10:]}")
```

### Workflow Status

```python
# Get workflow status
status = engine.get_workflow_status(workflow.workflow_id)

print(f"Workflow state: {status['state']}")
print(f"Progress: {status['progress']:.1%}")
print(f"Current step: {status['current_step']}")
print(f"Total execution time: {status['total_execution_time']:.2f}s")

# Step details
for step_info in status['steps']:
    print(f"Step {step_info['step_id']}: {step_info['state']}")
    if step_info['execution_time'] > 0:
        print(f"  Execution time: {step_info['execution_time']:.2f}s")
```

## Best Practices

### 1. Workflow Design

```python
# ✅ Good: Clear dependencies and realistic time estimates
well_designed_steps = [
    {
        "step_id": "fetch_data",
        "name": "Fetch Account Data",
        "agent_type": "zoho_scout",
        "agent_capability": "data_fetch",
        "estimated_duration": 5.0,  # Realistic estimate
        "timeout_seconds": 30,      # Reasonable timeout
        "retry_count": 3           # Appropriate retries
    },
    {
        "step_id": "analyze_data",
        "name": "Analyze Data",
        "agent_type": "analyzer",
        "agent_capability": "analysis",
        "dependencies": ["fetch_data"],  # Clear dependency
        "estimated_duration": 3.0
    }
]

# ❌ Avoid: Unclear dependencies or unrealistic estimates
poorly_designed_steps = [
    {
        "step_id": "vague_step",
        "name": "Do Something",
        "agent_type": "generic",
        "agent_capability": "analysis",
        "estimated_duration": 0.1,  # Too optimistic
        "timeout_seconds": 1,      # Too short
        "retry_count": 10          # Too many retries
    }
]
```

### 2. Agent Selection

```python
# ✅ Good: Specialized agents with clear capabilities
engine.register_agent(
    agent_id="zoho_specialist",
    agent_type="ZohoDataScout",
    capabilities=[AgentCapability.DATA_FETCH],
    max_concurrent_tasks=3,
    config={"api_endpoint": "zoho.api", "timeout": 30}
)

# ❌ Avoid: Generic agents with too many capabilities
engine.register_agent(
    agent_id="do_everything",
    agent_type="GenericAgent",
    capabilities=list(AgentCapability),  # Too broad
    max_concurrent_tasks=10  # Too high
)
```

### 3. Error Handling

```python
# ✅ Good: Comprehensive error handling with fallbacks
async def execute_with_fallback(workflow):
    try:
        async for event in engine.execute_workflow(workflow):
            if event.get("event") == "agent_error":
                # Log error but continue
                logger.warning(f"Step error: {event['data']['error_message']}")
                continue
            yield event
    except Exception as e:
        # Implement fallback strategy
        logger.error(f"Workflow failed: {e}")
        await execute_fallback_workflow(workflow.context)

# ❌ Avoid: Silent failures or no error handling
async def poor_execution(workflow):
    async for event in engine.execute_workflow(workflow):
        # No error handling
        yield event
```

### 4. Performance Optimization

```python
# ✅ Good: Use parallel execution where possible
parallel_workflow = await engine.create_workflow(
    name="Optimized Workflow",
    steps=independent_steps,
    execution_mode=ExecutionMode.PARALLEL,
    max_parallel_steps=5
)

# ✅ Good: Use adaptive mode for complex workflows
adaptive_workflow = await engine.create_workflow(
    name="Intelligent Workflow",
    steps=complex_steps,
    execution_mode=ExecutionMode.ADAPTIVE
)

# ❌ Avoid: Sequential execution when parallel is possible
sequential_workflow = await engine.create_workflow(
    name="Slow Workflow",
    steps=independent_steps,
    execution_mode=ExecutionMode.SEQUENTIAL  # Missed optimization opportunity
)
```

## Troubleshooting

### Common Issues

#### 1. Workflow Timeout
```python
# Problem: Steps timing out frequently
# Solution: Increase timeout or break into smaller steps
step_config = {
    "timeout_seconds": 120,  # Increase from 30 to 120
    "retry_count": 2,       # Reduce from 5 to 2
    "estimated_duration": 60.0  # More realistic estimate
}
```

#### 2. Agent Overload
```python
# Problem: Agents becoming overloaded
# Solution: Register more agents or reduce concurrent tasks
engine.register_agent(
    agent_id="additional_agent",
    agent_type="AdditionalAgent",
    capabilities=[AgentCapability.ANALYSIS],
    max_concurrent_tasks=5  # Add capacity
)

# Or reduce existing load
engine.register_agent(
    agent_id="existing_agent",
    agent_type="ExistingAgent",
    capabilities=[AgentCapability.ANALYSIS],
    max_concurrent_tasks=2  # Reduce from 5 to 2
)
```

#### 3. Memory Issues
```python
# Problem: Large data consumption
# Solution: Use data transformations to filter early
step_with_filtering = {
    "data_transformations": [
        {
            "type": "filter",
            "criteria": {"date": {"greater_than": "2024-01-01"}}
        }
    ]
}
```

#### 4. Dependency Resolution
```python
# Problem: Circular dependencies
# Solution: Redesign workflow to eliminate cycles
# Before: A -> B -> C -> A (invalid)
# After:  A -> D -> B -> C (valid)

corrected_steps = [
    {"step_id": "A", "dependencies": []},
    {"step_id": "D", "dependencies": ["A"]},
    {"step_id": "B", "dependencies": ["D"]},
    {"step_id": "C", "dependencies": ["B"]}
]
```

## Integration Examples

### 1. Integration with Intent Detection

```python
from src.agents.intent_detection import IntentDetectionEngine

# Initialize with intent engine
intent_engine = IntentDetectionEngine(confidence_threshold=0.7)
engine = DynamicWorkflowEngine(intent_engine=intent_engine)

# Create adaptive workflow based on intent
async def adaptive_workflow_creation(user_message: str):
    # Detect user intent
    intent = intent_engine.analyze_intent(user_message)

    # Create workflow based on intent
    if intent.primary_intent == "account_analysis":
        return await create_account_analysis_workflow(intent)
    elif intent.primary_intent == "general_conversation":
        return await create_conversation_workflow(intent)
    else:
        return await create_default_workflow()
```

### 2. Integration with Agent Registry

```python
# Dynamic agent registration based on capabilities
def register_agents_from_registry(agent_registry_config):
    for agent_config in agent_registry_config:
        capabilities = [
            AgentCapability(cap)
            for cap in agent_config["capabilities"]
        ]

        engine.register_agent(
            agent_id=agent_config["id"],
            agent_type=agent_config["type"],
            capabilities=capabilities,
            max_concurrent_tasks=agent_config.get("max_tasks", 3),
            config=agent_config.get("config", {})
        )
```

### 3. Integration with Monitoring Systems

```python
import asyncio
from datetime import datetime

async def monitoring_loop():
    """Continuous monitoring of workflow engine performance."""
    while True:
        # Get metrics
        metrics = engine.get_engine_metrics()

        # Alert on high load
        if metrics["active_workflows"] > 15:
            send_alert("High workflow load detected")

        # Alert on agent bottlenecks
        for agent_id, load in metrics["agent_load"].items():
            if load > 5:
                send_alert(f"Agent {agent_id} overloaded: {load} tasks")

        # Log performance
        log_metrics(metrics)

        await asyncio.sleep(60)  # Check every minute

# Start monitoring
asyncio.create_task(monitoring_loop())
```

## Migration Guide

### From Simple Orchestrator

If you're migrating from the basic orchestrator:

```python
# Old approach
orchestrator = OrchestratorAgent(session_id, zoho_scout, memory_analyst)
result = await orchestrator.execute({"account_id": "ACC-123"})

# New approach with DynamicWorkflowEngine
engine = DynamicWorkflowEngine()

# Register agents
engine.register_agent("zoho_scout", "ZohoDataScout", [AgentCapability.DATA_FETCH])
engine.register_agent("memory_analyst", "MemoryAnalyst", [AgentCapability.MEMORY])

# Create workflow
workflow = await engine.create_workflow(
    name="Account Analysis",
    steps=[
        {"step_id": "fetch", "name": "Fetch Data", "agent_type": "zoho_scout", "agent_capability": "data_fetch"},
        {"step_id": "analyze", "name": "Analyze", "agent_type": "memory_analyst", "agent_capability": "memory", "dependencies": ["fetch"]}
    ]
)

# Execute with enhanced features
async for event in engine.execute_workflow(workflow, context={"account_id": "ACC-123"}):
    handle_event(event)
```

## API Reference

### DynamicWorkflowEngine

#### Constructor
```python
DynamicWorkflowEngine(
    intent_engine: Optional[IntentDetectionEngine] = None,
    agent_registry: Optional[Dict[str, Any]] = None,
    max_concurrent_workflows: int = 10,
    default_timeout: int = 3600,
    enable_adaptation: bool = True,
    enable_monitoring: bool = True
)
```

#### Methods

##### create_workflow
```python
async def create_workflow(
    name: str,
    description: str,
    steps: List[Dict[str, Any]],
    priority: WorkflowPriority = WorkflowPriority.MEDIUM,
    context: Optional[Dict[str, Any]] = None
) -> Workflow
```

##### execute_workflow
```python
async def execute_workflow(
    workflow: Workflow,
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None
) -> AsyncGenerator[Dict[str, Any], None]
```

##### register_agent
```python
def register_agent(
    agent_id: str,
    agent_type: str,
    capabilities: List[AgentCapability],
    max_concurrent_tasks: int = 5,
    config: Optional[Dict[str, Any]] = None
) -> None
```

##### cancel_workflow
```python
async def cancel_workflow(workflow_id: str) -> bool
```

##### get_workflow_status
```python
def get_workflow_status(workflow_id: str) -> Optional[Dict[str, Any]]
```

##### get_engine_metrics
```python
def get_engine_metrics() -> Dict[str, Any]
```

## Conclusion

The Dynamic Workflow Engine provides a powerful, flexible foundation for building sophisticated multi-agent workflows. With its adaptive routing, parallel execution, and comprehensive monitoring capabilities, it enables the creation of intelligent, scalable automation systems.

Key takeaways:
1. **Start Simple**: Begin with basic sequential workflows and gradually add complexity
2. **Monitor Performance**: Use built-in metrics to optimize workflow execution
3. **Handle Errors Gracefully**: Implement robust error handling and recovery mechanisms
4. **Design for Scale**: Use parallel execution and adaptive routing for optimal performance
5. **Integrate Thoughtfully**: Leverage intent detection and agent registry for intelligent coordination

For more examples and advanced patterns, see the `/examples/workflow_engine_examples.py` file and the comprehensive test suite in `/tests/test_dynamic_workflow_engine.py`.