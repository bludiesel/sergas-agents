# Claude Flow MCP Tools Reference

Complete reference for all Claude Flow MCP tools with parameters and examples.

## Swarm Management

### swarm_init
Initialize a new swarm with specified topology.

**Parameters:**
- `topology` (required): "mesh" | "hierarchical" | "ring" | "star"
- `maxAgents` (optional, default: 8): Maximum number of agents (1-100)
- `strategy` (optional, default: "auto"): Distribution strategy ("balanced" | "specialized" | "adaptive")

**Example:**
```javascript
mcp__claude-flow__swarm_init {
  topology: "hierarchical",
  maxAgents: 10,
  strategy: "balanced"
}
```

### swarm_status
Get current swarm status and health metrics.

**Parameters:**
- `swarmId` (optional): Specific swarm to check

**Returns:** Status, agent count, topology, health metrics

### swarm_monitor
Real-time swarm activity monitoring.

**Parameters:**
- `swarmId` (optional): Swarm to monitor
- `interval` (optional): Update interval in seconds

### swarm_scale
Auto-scale agent count based on workload.

**Parameters:**
- `swarmId` (required): Swarm to scale
- `targetSize` (required): Target number of agents

### swarm_destroy
Gracefully shutdown a swarm.

**Parameters:**
- `swarmId` (required): Swarm to destroy

## Agent Management

### agent_spawn
Create a specialized AI agent.

**Parameters:**
- `type` (required): "coordinator" | "analyst" | "optimizer" | "documenter" | "monitor" | "specialist" | "architect" | "researcher" | "coder" | "tester" | "reviewer"
- `name` (optional): Custom agent name
- `swarmId` (optional): Swarm to join
- `capabilities` (optional): Array of capability strings

**Example:**
```javascript
mcp__claude-flow__agent_spawn {
  type: "coder",
  name: "Backend Developer",
  capabilities: ["python", "fastapi", "postgresql"]
}
```

### agent_list
List all active agents in the swarm.

**Parameters:**
- `swarmId` (optional): Filter by swarm
- `filter` (optional, default: "all"): "all" | "active" | "idle" | "busy"

### agent_metrics
Get performance metrics for specific agents.

**Parameters:**
- `agentId` (optional): Specific agent (omit for all agents)
- `metric` (optional, default: "all"): "all" | "cpu" | "memory" | "tasks" | "performance"

## Task Orchestration

### task_orchestrate
Orchestrate complex task workflows across agents.

**Parameters:**
- `task` (required): Task description or instructions
- `strategy` (optional, default: "adaptive"): "parallel" | "sequential" | "adaptive" | "balanced"
- `priority` (optional, default: "medium"): "low" | "medium" | "high" | "critical"
- `maxAgents` (optional): Maximum agents to use (1-10)
- `dependencies` (optional): Array of task dependencies

**Example:**
```javascript
mcp__claude-flow__task_orchestrate {
  task: "Implement OAuth2 authentication with JWT tokens",
  strategy: "sequential",
  priority: "high",
  maxAgents: 3
}
```

### task_status
Check execution status of running tasks.

**Parameters:**
- `taskId` (required): Task ID to check
- `detailed` (optional, default: false): Include detailed progress

### task_results
Retrieve results from completed tasks.

**Parameters:**
- `taskId` (required): Task ID
- `format` (optional, default: "summary"): "summary" | "detailed" | "raw"

## Memory Management

### memory_usage
Store/retrieve persistent memory with TTL and namespacing.

**Parameters:**
- `action` (required): "store" | "retrieve" | "list" | "delete" | "search"
- `key` (optional): Memory key
- `value` (optional): Value to store (for "store" action)
- `namespace` (optional, default: "default"): Namespace for organization
- `ttl` (optional): Time-to-live in seconds

**Examples:**
```javascript
// Store
mcp__claude-flow__memory_usage {
  action: "store",
  namespace: "project/decisions",
  key: "auth_method",
  value: "OAuth2 with JWT",
  ttl: 604800
}

// Retrieve
mcp__claude-flow__memory_usage {
  action: "retrieve",
  namespace: "project/decisions",
  key: "auth_method"
}

// List all in namespace
mcp__claude-flow__memory_usage {
  action: "list",
  namespace: "project/decisions"
}
```

### memory_search
Search memory with pattern matching.

**Parameters:**
- `pattern` (required): Search pattern (supports wildcards)
- `namespace` (optional): Limit search to namespace
- `limit` (optional, default: 10): Maximum results

**Example:**
```javascript
mcp__claude-flow__memory_search {
  pattern: "auth*",
  namespace: "project/decisions",
  limit: 20
}
```

### memory_persist
Cross-session memory persistence.

**Parameters:**
- `sessionId` (optional): Session identifier

### memory_backup
Create backup of memory stores.

**Parameters:**
- `path` (optional): Backup destination path

### memory_restore
Restore memory from backup.

**Parameters:**
- `backupPath` (required): Path to backup file

## Neural Features

### neural_status
Check neural network status.

**Parameters:**
- `modelId` (optional): Specific model to check

### neural_train
Train neural patterns with WASM SIMD acceleration.

**Parameters:**
- `pattern_type` (required): "coordination" | "optimization" | "prediction"
- `training_data` (required): JSON string with training data
- `epochs` (optional, default: 50): Training iterations (1-100)

**Example:**
```javascript
mcp__claude-flow__neural_train {
  pattern_type: "coordination",
  training_data: JSON.stringify({
    task: "Multi-agent development",
    topology: "mesh",
    agents: 5,
    outcome: "success",
    metrics: { quality: 0.92, speed: 0.85 }
  }),
  epochs: 50
}
```

### neural_patterns
Analyze cognitive patterns.

**Parameters:**
- `action` (required): "analyze" | "learn" | "predict"
- `operation` (optional): Operation type for analysis
- `metadata` (optional): Additional context

### neural_predict
Make predictions using trained models.

**Parameters:**
- `modelId` (required): Model identifier
- `input` (required): Input data for prediction

## GitHub Integration

### github_repo_analyze
Analyze repository code quality, performance, or security.

**Parameters:**
- `repo` (required): Repository in "owner/name" format
- `analysis_type` (optional): "code_quality" | "performance" | "security"

### github_pr_manage
Manage pull requests.

**Parameters:**
- `repo` (required): Repository
- `pr_number` (optional): PR number
- `action` (required): "review" | "merge" | "close"

### github_code_review
Automated code review for PRs.

**Parameters:**
- `repo` (required): Repository
- `pr` (required): PR number

### github_issue_track
Issue tracking and triage.

**Parameters:**
- `repo` (required): Repository
- `action` (required): Action to perform

## Performance & Monitoring

### performance_report
Generate performance reports with real-time metrics.

**Parameters:**
- `format` (optional, default: "summary"): "summary" | "detailed" | "json"
- `timeframe` (optional, default: "24h"): "24h" | "7d" | "30d"

### bottleneck_analyze
Identify performance bottlenecks.

**Parameters:**
- `component` (optional): Specific component to analyze
- `metrics` (optional): Array of metrics to check

### benchmark_run
Execute performance benchmarks.

**Parameters:**
- `suite` (optional): Benchmark suite to run

### token_usage
Analyze token consumption.

**Parameters:**
- `operation` (optional): Specific operation
- `timeframe` (optional, default: "24h"): Time range

## Dynamic Agent Adaptation (DAA)

### daa_agent_create
Create dynamic agents with learning capabilities.

**Parameters:**
- `agent_type` (required): Type of dynamic agent
- `capabilities` (optional): Array of capabilities
- `resources` (optional): Resource allocation

### daa_agent_adapt
Trigger agent adaptation based on feedback.

**Parameters:**
- `agentId` (required): Agent to adapt
- `performanceScore` (optional): Score 0-1
- `feedback` (optional): Feedback message
- `suggestions` (optional): Array of improvements

### daa_capability_match
Match agent capabilities to task requirements.

**Parameters:**
- `task_requirements` (required): Array of required capabilities
- `available_agents` (optional): Filter to specific agents

## Workflow Automation

### workflow_create
Create custom reusable workflows.

**Parameters:**
- `name` (required): Workflow name
- `steps` (required): Array of workflow steps
- `triggers` (optional): Array of trigger conditions

### workflow_execute
Execute predefined workflows.

**Parameters:**
- `workflowId` (required): Workflow to execute
- `params` (optional): Execution parameters

### sparc_mode
Run SPARC development methodology.

**Parameters:**
- `mode` (required): "dev" | "api" | "ui" | "test" | "refactor"
- `task_description` (required): Task description
- `options` (optional): Configuration options

## Topology Optimization

### topology_optimize
Auto-optimize swarm topology based on performance.

**Parameters:**
- `swarmId` (optional): Swarm to optimize

### load_balance
Distribute tasks efficiently across agents.

**Parameters:**
- `swarmId` (optional): Swarm for load balancing
- `tasks` (optional): Array of tasks to balance

### coordination_sync
Synchronize agent coordination.

**Parameters:**
- `swarmId` (optional): Swarm to sync

## Common Patterns

### Pattern 1: Initialize → Spawn → Orchestrate
```javascript
// 1. Initialize swarm
mcp__claude-flow__swarm_init { topology: "mesh", maxAgents: 6 }

// 2. Spawn specialized agents
mcp__claude-flow__agent_spawn { type: "researcher", name: "Analyst" }
mcp__claude-flow__agent_spawn { type: "coder", name: "Developer" }
mcp__claude-flow__agent_spawn { type: "tester", name: "QA" }

// 3. Orchestrate work
mcp__claude-flow__task_orchestrate {
  task: "Build authentication system",
  strategy: "adaptive",
  priority: "high"
}
```

### Pattern 2: Memory-Persistent Workflow
```javascript
// Store decision
mcp__claude-flow__memory_usage {
  action: "store",
  namespace: "project/architecture",
  key: "database_choice",
  value: "PostgreSQL for reliability",
  ttl: 2592000  // 30 days
}

// Later session: retrieve
mcp__claude-flow__memory_usage {
  action: "retrieve",
  namespace: "project/architecture",
  key: "database_choice"
}
```

### Pattern 3: Learn from Success
```javascript
// After successful task completion
mcp__claude-flow__neural_train {
  pattern_type: "coordination",
  training_data: JSON.stringify({
    task: "API development",
    topology: "hierarchical",
    success_factors: ["clear delegation", "parallel execution"],
    outcome_quality: 0.94
  }),
  epochs: 50
}

// Use learning for future predictions
mcp__claude-flow__neural_patterns {
  action: "predict",
  operation: "similar_api_task"
}
```
