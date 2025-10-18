#!/usr/bin/env python3
"""
Swarm Orchestrator Helper Script

Utility for complex swarm setups and orchestration patterns.
Simplifies common Claude Flow MCP operations.
"""

import json
import subprocess
import sys
from typing import Dict, List, Optional


class SwarmOrchestrator:
    """Helper class for Claude Flow swarm orchestration."""

    def __init__(self):
        self.mcp_prefix = "mcp__claude-flow__"

    def init_swarm(
        self,
        topology: str,
        max_agents: int = 8,
        strategy: str = "auto"
    ) -> Dict:
        """
        Initialize a swarm with specified configuration.

        Args:
            topology: "mesh" | "hierarchical" | "ring" | "star"
            max_agents: Maximum number of agents (1-100)
            strategy: Distribution strategy

        Returns:
            Swarm initialization result
        """
        cmd = [
            "npx", "claude-flow@alpha", "mcp", "call",
            f"{self.mcp_prefix}swarm_init",
            "--params", json.dumps({
                "topology": topology,
                "maxAgents": max_agents,
                "strategy": strategy
            })
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return self._parse_result(result)

    def spawn_agents(self, agents: List[Dict]) -> List[Dict]:
        """
        Spawn multiple agents in batch.

        Args:
            agents: List of agent configurations
                Each config: {"type": str, "name": str, "capabilities": List[str]}

        Returns:
            List of spawn results
        """
        results = []
        for agent in agents:
            cmd = [
                "npx", "claude-flow@alpha", "mcp", "call",
                f"{self.mcp_prefix}agent_spawn",
                "--params", json.dumps(agent)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            results.append(self._parse_result(result))

        return results

    def orchestrate_task(
        self,
        task: str,
        strategy: str = "adaptive",
        priority: str = "medium",
        max_agents: Optional[int] = None
    ) -> Dict:
        """
        Orchestrate a task across the swarm.

        Args:
            task: Task description
            strategy: "parallel" | "sequential" | "adaptive" | "balanced"
            priority: "low" | "medium" | "high" | "critical"
            max_agents: Optional max agents to use

        Returns:
            Task orchestration result
        """
        params = {
            "task": task,
            "strategy": strategy,
            "priority": priority
        }

        if max_agents:
            params["maxAgents"] = max_agents

        cmd = [
            "npx", "claude-flow@alpha", "mcp", "call",
            f"{self.mcp_prefix}task_orchestrate",
            "--params", json.dumps(params)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return self._parse_result(result)

    def get_swarm_status(self, swarm_id: Optional[str] = None) -> Dict:
        """Get current swarm status."""
        params = {}
        if swarm_id:
            params["swarmId"] = swarm_id

        cmd = [
            "npx", "claude-flow@alpha", "mcp", "call",
            f"{self.mcp_prefix}swarm_status",
            "--params", json.dumps(params)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return self._parse_result(result)

    def _parse_result(self, result: subprocess.CompletedProcess) -> Dict:
        """Parse subprocess result into dict."""
        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr,
                "stdout": result.stdout
            }

        try:
            # Try to parse JSON output
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {
                "success": True,
                "output": result.stdout
            }


def create_full_stack_swarm(feature_name: str) -> Dict:
    """
    Create a hierarchical swarm for full-stack development.

    Args:
        feature_name: Name of the feature to develop

    Returns:
        Swarm setup result
    """
    orchestrator = SwarmOrchestrator()

    # Initialize hierarchical swarm
    print(f"Initializing swarm for: {feature_name}")
    swarm_result = orchestrator.init_swarm("hierarchical", max_agents=8)
    print(f"Swarm initialized: {swarm_result}")

    # Define agent team
    agents = [
        {"type": "coordinator", "name": "Feature Lead"},
        {"type": "architect", "name": "System Architect"},
        {"type": "coder", "name": "Backend Developer", "capabilities": ["python", "fastapi"]},
        {"type": "coder", "name": "Frontend Developer", "capabilities": ["react", "typescript"]},
        {"type": "coder", "name": "Database Developer", "capabilities": ["postgresql", "sqlalchemy"]},
        {"type": "tester", "name": "QA Engineer"},
        {"type": "reviewer", "name": "Code Reviewer"}
    ]

    # Spawn agents
    print(f"Spawning {len(agents)} agents...")
    agent_results = orchestrator.spawn_agents(agents)
    print(f"Agents spawned: {len(agent_results)}")

    # Orchestrate the development task
    task = f"Implement {feature_name} with full-stack architecture, tests, and documentation"
    print(f"Orchestrating task: {task}")
    task_result = orchestrator.orchestrate_task(
        task=task,
        strategy="adaptive",
        priority="high",
        max_agents=7
    )

    return {
        "swarm": swarm_result,
        "agents": agent_results,
        "task": task_result
    }


def create_parallel_processing_swarm(tasks: List[str]) -> Dict:
    """
    Create a star topology swarm for parallel task processing.

    Args:
        tasks: List of independent tasks

    Returns:
        Swarm setup and task results
    """
    orchestrator = SwarmOrchestrator()

    # Initialize star swarm
    print(f"Initializing star swarm for {len(tasks)} tasks")
    swarm_result = orchestrator.init_swarm("star", max_agents=len(tasks) + 1)

    # Spawn coordinator and workers
    agents = [{"type": "coordinator", "name": "Task Hub"}]
    agents.extend([
        {"type": "specialist", "name": f"Worker {i+1}"}
        for i in range(len(tasks))
    ])

    print(f"Spawning {len(agents)} agents...")
    agent_results = orchestrator.spawn_agents(agents)

    # Orchestrate each task in parallel
    print("Orchestrating parallel tasks...")
    task_results = []
    for task in tasks:
        result = orchestrator.orchestrate_task(
            task=task,
            strategy="parallel",
            priority="medium"
        )
        task_results.append(result)

    return {
        "swarm": swarm_result,
        "agents": agent_results,
        "tasks": task_results
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python swarm_orchestrator.py fullstack <feature_name>")
        print("  python swarm_orchestrator.py parallel <task1> <task2> ...")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "fullstack":
        feature = sys.argv[2] if len(sys.argv) > 2 else "New Feature"
        result = create_full_stack_swarm(feature)
        print("\n=== Full-Stack Swarm Created ===")
        print(json.dumps(result, indent=2))

    elif mode == "parallel":
        tasks = sys.argv[2:]
        if not tasks:
            print("Error: No tasks provided")
            sys.exit(1)
        result = create_parallel_processing_swarm(tasks)
        print("\n=== Parallel Processing Swarm Created ===")
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown mode: {mode}")
        print("Available modes: fullstack, parallel")
        sys.exit(1)
