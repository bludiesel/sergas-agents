"""Dynamic Workflow Engine Usage Examples.

This file demonstrates how to use the DynamicWorkflowEngine for various
workflow scenarios including account analysis, parallel processing,
and adaptive execution.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List

from src.agents.dynamic_workflow_engine import (
    DynamicWorkflowEngine,
    WorkflowState,
    WorkflowPriority,
    ExecutionMode,
    AgentCapability,
    DependencyType
)
from src.agents.intent_detection import IntentDetectionEngine


async def example_sequential_workflow():
    """Example: Sequential workflow execution for account analysis."""

    # Initialize workflow engine
    engine = DynamicWorkflowEngine()

    # Register agents
    engine.register_agent(
        agent_id="zoho_scout",
        agent_type="ZohoDataScout",
        capabilities=[AgentCapability.DATA_FETCH],
        max_concurrent_tasks=3
    )

    engine.register_agent(
        agent_id="memory_analyst",
        agent_type="MemoryAnalyst",
        capabilities=[AgentCapability.MEMORY, AgentCapability.ANALYSIS],
        max_concurrent_tasks=2
    )

    engine.register_agent(
        agent_id="recommendation_author",
        agent_type="RecommendationAuthor",
        capabilities=[AgentCapability.RECOMMENDATION],
        max_concurrent_tasks=2
    )

    # Create workflow steps
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
            "step_id": "analyze_historical_context",
            "name": "Analyze Historical Context",
            "description": "Retrieve and analyze historical patterns",
            "agent_type": "memory_analyst",
            "agent_capability": "memory",
            "dependencies": ["fetch_account_data"],
            "estimated_duration": 3.0,
            "timeout_seconds": 30
        },
        {
            "step_id": "generate_recommendations",
            "name": "Generate Recommendations",
            "description": "Create actionable recommendations",
            "agent_type": "recommendation_author",
            "agent_capability": "recommendation",
            "dependencies": ["fetch_account_data", "analyze_historical_context"],
            "estimated_duration": 4.0,
            "timeout_seconds": 30
        }
    ]

    # Create workflow
    workflow = await engine.create_workflow(
        name="Account Analysis Workflow",
        description="Complete account analysis with recommendations",
        steps=steps,
        priority=WorkflowPriority.HIGH,
        context={"account_id": "ACC-12345"}
    )

    print("🚀 Starting Sequential Workflow Execution")
    print(f"Workflow ID: {workflow.workflow_id}")
    print(f"Steps: {len(workflow.steps)}")

    # Execute workflow
    try:
        async for event in engine.execute_workflow(
            workflow,
            context={"account_id": "ACC-12345"},
            session_id="demo_session_1"
        ):
            if event.get("event") == "workflow_started":
                print(f"✅ Workflow started: {event['data']['name']}")
            elif event.get("event") == "agent_started":
                step_data = event['data']
                print(f"🔵 Starting step {step_data['step']}: {step_data['task']}")
            elif event.get("event") == "agent_completed":
                step_data = event['data']
                print(f"🟢 Completed step {step_data['step']}")
            elif event.get("event") == "workflow_completed":
                final_output = event['data']['final_output']
                print(f"🎉 Workflow completed!")
                print(f"   Total execution time: {final_output.get('total_execution_time', 0):.2f}s")
                print(f"   Success rate: {final_output.get('success_rate', 0):.1%}")
                break
            elif event.get("event") == "agent_error":
                error_data = event['data']
                print(f"❌ Error in step {error_data['step']}: {error_data['error_message']}")

    except Exception as e:
        print(f"❌ Workflow execution failed: {str(e)}")


async def example_parallel_workflow():
    """Example: Parallel workflow execution for data processing."""

    # Initialize workflow engine
    engine = DynamicWorkflowEngine(max_concurrent_workflows=15)

    # Register agents for parallel processing
    engine.register_agent(
        agent_id="data_processor_1",
        agent_type="DataProcessor",
        capabilities=[AgentCapability.TRANSFORMATION],
        max_concurrent_tasks=5
    )

    engine.register_agent(
        agent_id="data_processor_2",
        agent_type="DataProcessor",
        capabilities=[AgentCapability.TRANSFORMATION],
        max_concurrent_tasks=5
    )

    engine.register_agent(
        agent_id="aggregator",
        agent_type="DataAggregator",
        capabilities=[AgentCapability.ANALYSIS],
        max_concurrent_tasks=2
    )

    # Create parallel workflow steps
    steps = [
        {
            "step_id": "fetch_data_source_1",
            "name": "Fetch Data Source 1",
            "description": "Retrieve data from first source",
            "agent_type": "data_processor_1",
            "agent_capability": "data_fetch",
            "estimated_duration": 2.0
        },
        {
            "step_id": "fetch_data_source_2",
            "name": "Fetch Data Source 2",
            "description": "Retrieve data from second source",
            "agent_type": "data_processor_2",
            "agent_capability": "data_fetch",
            "estimated_duration": 2.0
        },
        {
            "step_id": "fetch_data_source_3",
            "name": "Fetch Data Source 3",
            "description": "Retrieve data from third source",
            "agent_type": "data_processor_1",
            "agent_capability": "data_fetch",
            "estimated_duration": 2.0
        },
        {
            "step_id": "transform_data_1",
            "name": "Transform Data 1",
            "description": "Transform and clean first dataset",
            "agent_type": "data_processor_1",
            "agent_capability": "transformation",
            "dependencies": ["fetch_data_source_1"],
            "estimated_duration": 1.5
        },
        {
            "step_id": "transform_data_2",
            "name": "Transform Data 2",
            "description": "Transform and clean second dataset",
            "agent_type": "data_processor_2",
            "agent_capability": "transformation",
            "dependencies": ["fetch_data_source_2"],
            "estimated_duration": 1.5
        },
        {
            "step_id": "transform_data_3",
            "name": "Transform Data 3",
            "description": "Transform and clean third dataset",
            "agent_type": "data_processor_1",
            "agent_capability": "transformation",
            "dependencies": ["fetch_data_source_3"],
            "estimated_duration": 1.5
        },
        {
            "step_id": "aggregate_results",
            "name": "Aggregate Results",
            "description": "Combine and analyze all transformed data",
            "agent_type": "aggregator",
            "agent_capability": "analysis",
            "dependencies": ["transform_data_1", "transform_data_2", "transform_data_3"],
            "estimated_duration": 2.0
        }
    ]

    # Create workflow
    workflow = await engine.create_workflow(
        name="Parallel Data Processing",
        description="Process multiple data sources in parallel",
        steps=steps,
        priority=WorkflowPriority.MEDIUM,
        execution_mode=ExecutionMode.PARALLEL,
        context={"batch_id": "BATCH-001"}
    )

    print("\n🚀 Starting Parallel Workflow Execution")
    print(f"Workflow ID: {workflow.workflow_id}")
    print(f"Execution mode: {workflow.execution_mode.value}")

    # Execute workflow
    start_time = datetime.utcnow()

    try:
        async for event in engine.execute_workflow(
            workflow,
            context={"batch_id": "BATCH-001"},
            session_id="demo_session_2"
        ):
            if event.get("event") == "workflow_started":
                print(f"✅ Workflow started: {event['data']['name']}")
            elif event.get("event") == "agent_started":
                step_data = event['data']
                print(f"🔵 Starting: {step_data['task']} (Agent: {step_data['agent']})")
            elif event.get("event") == "agent_completed":
                step_data = event['data']
                print(f"🟢 Completed: {step_data['task']}")
            elif event.get("event") == "workflow_completed":
                end_time = datetime.utcnow()
                total_time = (end_time - start_time).total_seconds()
                final_output = event['data']['final_output']
                print(f"🎉 Parallel workflow completed!")
                print(f"   Total execution time: {total_time:.2f}s")
                print(f"   Steps completed: {len(final_output.get('steps', []))}")
                break

    except Exception as e:
        print(f"❌ Parallel workflow execution failed: {str(e)}")


async def example_adaptive_workflow():
    """Example: Adaptive workflow execution with intelligent routing."""

    # Initialize workflow engine with adaptation enabled
    engine = DynamicWorkflowEngine(
        max_concurrent_workflows=20,
        enable_adaptation=True,
        enable_monitoring=True
    )

    # Register diverse agents
    agents_config = [
        {
            "agent_id": "specialist_1",
            "agent_type": "AnalysisSpecialist",
            "capabilities": [AgentCapability.ANALYSIS, AgentCapability.VALIDATION],
            "max_concurrent_tasks": 3
        },
        {
            "agent_id": "specialist_2",
            "agent_type": "AnalysisSpecialist",
            "capabilities": [AgentCapability.ANALYSIS, AgentCapability.VALIDATION],
            "max_concurrent_tasks": 3
        },
        {
            "agent_id": "data_scout",
            "agent_type": "DataScout",
            "capabilities": [AgentCapability.DATA_FETCH],
            "max_concurrent_tasks": 5
        },
        {
            "agent_id": "memory_bank",
            "agent_type": "MemoryBank",
            "capabilities": [AgentCapability.MEMORY],
            "max_concurrent_tasks": 2
        },
        {
            "agent_id": "recommender",
            "agent_type": "Recommender",
            "capabilities": [AgentCapability.RECOMMENDATION],
            "max_concurrent_tasks": 2
        }
    ]

    for agent_config in agents_config:
        engine.register_agent(**agent_config)

    # Create adaptive workflow with multiple pathways
    steps = [
        {
            "step_id": "intelligent_intent_detection",
            "name": "Intelligent Intent Detection",
            "description": "Analyze user intent and determine execution path",
            "agent_type": "specialist_1",
            "agent_capability": "analysis",
            "estimated_duration": 1.0,
            "priority_boost": 20
        },
        {
            "step_id": "conditional_data_fetch",
            "name": "Conditional Data Fetch",
            "description": "Fetch data based on intent detection results",
            "agent_type": "data_scout",
            "agent_capability": "data_fetch",
            "dependencies": ["intelligent_intent_detection"],
            "estimated_duration": 2.0
        },
        {
            "step_id": "historical_analysis",
            "name": "Historical Analysis",
            "description": "Analyze historical patterns if needed",
            "agent_type": "memory_bank",
            "agent_capability": "memory",
            "dependencies": ["conditional_data_fetch"],
            "estimated_duration": 1.5
        },
        {
            "step_id": "parallel_validation",
            "name": "Parallel Validation",
            "description": "Validate findings using multiple specialists",
            "agent_type": "specialist_2",
            "agent_capability": "validation",
            "dependencies": ["conditional_data_fetch"],
            "estimated_duration": 1.0
        },
        {
            "step_id": "synthesis_and_recommendations",
            "name": "Synthesis and Recommendations",
            "description": "Synthesize results and generate recommendations",
            "agent_type": "recommender",
            "agent_capability": "recommendation",
            "dependencies": ["historical_analysis", "parallel_validation"],
            "estimated_duration": 2.0,
            "priority_boost": 10
        }
    ]

    # Create adaptive workflow
    workflow = await engine.create_workflow(
        name="Adaptive Intelligent Analysis",
        description="Workflow with intelligent routing and adaptation",
        steps=steps,
        priority=WorkflowPriority.HIGH,
        execution_mode=ExecutionMode.ADAPTIVE,
        context={"user_query": "Analyze account performance and risks", "adaptive_mode": True}
    )

    print("\n🚀 Starting Adaptive Workflow Execution")
    print(f"Workflow ID: {workflow.workflow_id}")
    print(f"Execution mode: {workflow.execution_mode.value}")
    print(f"Adaptation enabled: {engine.enable_adaptation}")

    # Execute workflow
    start_time = datetime.utcnow()

    try:
        async for event in engine.execute_workflow(
            workflow,
            context={"user_query": "Analyze account performance and risks"},
            session_id="demo_session_3"
        ):
            if event.get("event") == "workflow_started":
                print(f"✅ Adaptive workflow started: {event['data']['name']}")
            elif event.get("event") == "agent_started":
                step_data = event['data']
                print(f"🔵 Adaptive execution: {step_data['task']}")
            elif event.get("event") == "agent_stream":
                stream_data = event['data']
                print(f"📡 Stream: {stream_data.get('content', '')[:50]}...")
            elif event.get("event") == "agent_completed":
                step_data = event['data']
                print(f"🟢 Adaptive step completed: {step_data['task']}")
            elif event.get("event") == "workflow_completed":
                end_time = datetime.utcnow()
                total_time = (end_time - start_time).total_seconds()
                final_output = event['data']['final_output']
                print(f"🎉 Adaptive workflow completed!")
                print(f"   Total execution time: {total_time:.2f}s")
                print(f"   Success rate: {final_output.get('success_rate', 0):.1%}")
                break

    except Exception as e:
        print(f"❌ Adaptive workflow execution failed: {str(e)}")

    # Show engine metrics
    metrics = engine.get_engine_metrics()
    print(f"\n📊 Engine Performance Metrics:")
    print(f"   Active workflows: {metrics['active_workflows']}")
    print(f"   Completed workflows: {metrics['completed_workflows']}")
    print(f"   Agent load distribution: {metrics['agent_load']}")


async def example_complex_multi_account_workflow():
    """Example: Complex workflow processing multiple accounts with dependencies."""

    # Initialize workflow engine for multi-account processing
    engine = DynamicWorkflowEngine(
        max_concurrent_workflows=25,
        enable_adaptation=True,
        enable_monitoring=True
    )

    # Register specialized agents
    engine.register_agent(
        agent_id="account_fetcher",
        agent_type="ZohoDataScout",
        capabilities=[AgentCapability.DATA_FETCH],
        max_concurrent_tasks=8
    )

    engine.register_agent(
        agent_id="risk_analyzer",
        agent_type="RiskAnalyzer",
        capabilities=[AgentCapability.ANALYSIS, AgentCapability.VALIDATION],
        max_concurrent_tasks=5
    )

    engine.register_agent(
        agent_id="memory_analyst",
        agent_type="MemoryAnalyst",
        capabilities=[AgentCapability.MEMORY],
        max_concurrent_tasks=3
    )

    engine.register_agent(
        agent_id="recommender",
        agent_type="RecommendationAuthor",
        capabilities=[AgentCapability.RECOMMENDATION],
        max_concurrent_tasks=4
    )

    engine.register_agent(
        agent_id="coordinator",
        agent_type="WorkflowCoordinator",
        capabilities=[AgentCapability.COORDINATION],
        max_concurrent_tasks=2
    )

    # Define complex workflow steps
    accounts = ["ACC-001", "ACC-002", "ACC-003", "ACC-004", "ACC-005"]

    steps = [
        {
            "step_id": "coordinate_batch_analysis",
            "name": "Coordinate Batch Analysis",
            "description": "Initialize and coordinate multi-account analysis",
            "agent_type": "coordinator",
            "agent_capability": "coordination",
            "estimated_duration": 1.0,
            "priority_boost": 15
        }
    ]

    # Add account-specific steps
    for i, account_id in enumerate(accounts):
        steps.extend([
            {
                "step_id": f"fetch_account_{account_id}",
                "name": f"Fetch {account_id} Data",
                "description": f"Retrieve data for account {account_id}",
                "agent_type": "account_fetcher",
                "agent_capability": "data_fetch",
                "dependencies": ["coordinate_batch_analysis"],
                "estimated_duration": 2.0,
                "resource_requirements": {"account_id": account_id}
            },
            {
                "step_id": f"analyze_risk_{account_id}",
                "name": f"Analyze {account_id} Risk",
                "description": f"Perform risk analysis for account {account_id}",
                "agent_type": "risk_analyzer",
                "agent_capability": "analysis",
                "dependencies": [f"fetch_account_{account_id}"],
                "estimated_duration": 3.0,
                "resource_requirements": {"account_id": account_id}
            },
            {
                "step_id": f"get_memory_{account_id}",
                "name": f"Get {account_id} Memory",
                "description": f"Retrieve historical context for account {account_id}",
                "agent_type": "memory_analyst",
                "agent_capability": "memory",
                "dependencies": [f"fetch_account_{account_id}"],
                "estimated_duration": 1.5,
                "resource_requirements": {"account_id": account_id}
            }
        ])

    # Add final coordination steps
    steps.extend([
        {
            "step_id": "synthesize_all_results",
            "name": "Synthesize All Results",
            "description": "Combine and synthesize all account analyses",
            "agent_type": "coordinator",
            "agent_capability": "coordination",
            "dependencies": [
                f"analyze_risk_{acc_id}" for acc_id in accounts
            ],
            "estimated_duration": 2.0,
            "priority_boost": 10
        },
        {
            "step_id": "generate_batch_recommendations",
            "name": "Generate Batch Recommendations",
            "description": "Create comprehensive recommendations for all accounts",
            "agent_type": "recommender",
            "agent_capability": "recommendation",
            "dependencies": [
                "synthesize_all_results"
            ] + [
                f"get_memory_{acc_id}" for acc_id in accounts
            ],
            "estimated_duration": 3.0,
            "priority_boost": 15
        }
    ])

    # Create complex workflow
    workflow = await engine.create_workflow(
        name="Multi-Account Batch Analysis",
        description=f"Analyze {len(accounts)} accounts with complex dependencies",
        steps=steps,
        priority=WorkflowPriority.HIGH,
        execution_mode=ExecutionMode.ADAPTIVE,
        context={
            "accounts": accounts,
            "batch_id": f"BATCH-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "analysis_type": "comprehensive"
        }
    )

    print(f"\n🚀 Starting Complex Multi-Account Workflow")
    print(f"Workflow ID: {workflow.workflow_id}")
    print(f"Processing {len(accounts)} accounts")
    print(f"Total steps: {len(workflow.steps)}")

    # Execute complex workflow
    start_time = datetime.utcnow()
    step_count = 0

    try:
        async for event in engine.execute_workflow(
            workflow,
            context={"accounts": accounts, "comprehensive_analysis": True},
            session_id="demo_session_complex"
        ):
            if event.get("event") == "workflow_started":
                print(f"✅ Complex workflow started: {event['data']['name']}")
            elif event.get("event") == "agent_started":
                step_data = event['data']
                step_count += 1
                print(f"🔵 [{step_count}/{len(steps)}] {step_data['task']}")
            elif event.get("event") == "agent_completed":
                step_data = event['data']
                if "result" in step_data.get("output", {}):
                    result = step_data["output"]["result"]
                    if "execution_time" in result:
                        print(f"⏱️  Step completed in {result['execution_time']:.2f}s")
            elif event.get("event") == "workflow_completed":
                end_time = datetime.utcnow()
                total_time = (end_time - start_time).total_seconds()
                final_output = event['data']['final_output']
                print(f"\n🎉 Complex multi-account workflow completed!")
                print(f"   Total execution time: {total_time:.2f}s")
                print(f"   Steps executed: {step_count}/{len(steps)}")
                print(f"   Success rate: {final_output.get('success_rate', 0):.1%}")
                print(f"   Average time per step: {total_time/step_count:.2f}s")
                break

    except Exception as e:
        print(f"❌ Complex workflow execution failed: {str(e)}")

    # Show final engine metrics
    final_metrics = engine.get_engine_metrics()
    print(f"\n📊 Final Engine Metrics:")
    print(f"   Total workflows processed: {final_metrics['total_workflows']}")
    print(f"   Final agent load: {final_metrics['agent_load']}")
    print(f"   Peak resource usage: {max(final_metrics['performance_metrics'].get('total_agent_load', [0]))}")


async def main():
    """Run all workflow engine examples."""
    print("=" * 80)
    print("🎯 Dynamic Workflow Engine Examples")
    print("=" * 80)

    # Run all examples
    await example_sequential_workflow()
    await asyncio.sleep(1)  # Brief pause between examples

    await example_parallel_workflow()
    await asyncio.sleep(1)

    await example_adaptive_workflow()
    await asyncio.sleep(1)

    await example_complex_multi_account_workflow()

    print("\n" + "=" * 80)
    print("✅ All workflow engine examples completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())