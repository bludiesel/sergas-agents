# Complete Claude Flow MCP Tools Reference

Comprehensive catalog of ALL Claude Flow MCP tools organized by category.

## Table of Contents
1. [Swarm Management](#swarm-management)
2. [Agent Management](#agent-management)
3. [Task Orchestration](#task-orchestration)
4. [Memory Management](#memory-management)
5. [Neural & AI Features](#neural--ai-features)
6. [SPARC Methodology](#sparc-methodology)
7. [Workflow Automation](#workflow-automation)
8. [GitHub Integration](#github-integration)
9. [Performance & Monitoring](#performance--monitoring)
10. [Dynamic Agent Adaptation (DAA)](#dynamic-agent-adaptation-daa)
11. [System & Configuration](#system--configuration)
12. [Advanced Features](#advanced-features)

---

## Swarm Management

### swarm_init
Initialize a new swarm with specified topology.

**Parameters:**
- `topology` (required): "mesh" | "hierarchical" | "ring" | "star"
- `maxAgents` (optional, default: 8): Maximum number of agents (1-100)
- `strategy` (optional, default: "auto"): "balanced" | "specialized" | "adaptive"

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
- `swarmId` (optional): Specific swarm ID

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

---

## Agent Management

### agent_spawn
Create a specialized AI agent.

**Parameters:**
- `type` (required): Agent type (see Available Types below)
- `name` (optional): Custom agent name
- `swarmId` (optional): Swarm to join
- `capabilities` (optional): Array of capability strings

**Available Types:**
- `coordinator` - Task orchestration and team coordination
- `analyst` - Code review and quality assessment
- `optimizer` - Performance tuning and bottleneck identification
- `documenter` - Documentation generation
- `monitor` - System monitoring and alerting
- `specialist` - Domain-specific expert
- `architect` - System design and architecture
- `task-orchestrator` - Complex task management
- `code-analyzer` - Code analysis and metrics
- `perf-analyzer` - Performance analysis
- `researcher` - Information gathering and analysis
- `coder` - Implementation and code generation
- `tester` - Test creation and validation
- `reviewer` - Code review and security analysis

### agents_spawn_parallel
Spawn multiple agents in parallel (10-20x faster than sequential).

**Parameters:**
- `agents` (required): Array of agent configurations
  - Each: `{ type, name, capabilities, priority }`
- `maxConcurrency` (optional, default: 5): Max concurrent spawns
- `batchSize` (optional, default: 3): Agents per batch

**Example:**
```javascript
mcp__claude-flow__agents_spawn_parallel {
  agents: [
    { type: "coder", name: "Backend Dev", capabilities: ["python", "fastapi"] },
    { type: "coder", name: "Frontend Dev", capabilities: ["react", "typescript"] },
    { type: "tester", name: "QA Engineer", capabilities: ["pytest", "jest"] }
  ],
  maxConcurrency: 3
}
```

### agent_list
List all active agents in the swarm.

**Parameters:**
- `swarmId` (optional): Filter by swarm
- `filter` (optional, default: "all"): "all" | "active" | "idle" | "busy"

### agent_metrics
Get performance metrics for agents.

**Parameters:**
- `agentId` (optional): Specific agent (omit for all)
- `metric` (optional, default: "all"): "all" | "cpu" | "memory" | "tasks" | "performance"

---

## Task Orchestration

### task_orchestrate
Orchestrate complex task workflows across agents.

**Parameters:**
- `task` (required): Task description
- `strategy` (optional, default: "adaptive"): "parallel" | "sequential" | "adaptive" | "balanced"
- `priority` (optional, default: "medium"): "low" | "medium" | "high" | "critical"
- `maxAgents` (optional): Max agents to use (1-10)
- `dependencies` (optional): Task dependencies array

### task_status
Check execution status of running tasks.

**Parameters:**
- `taskId` (required): Task ID
- `detailed` (optional, default: false): Include detailed progress

### task_results
Retrieve results from completed tasks.

**Parameters:**
- `taskId` (required): Task ID
- `format` (optional, default: "summary"): "summary" | "detailed" | "raw"

---

## Memory Management

### memory_usage
Store/retrieve persistent memory with TTL and namespacing.

**Parameters:**
- `action` (required): "store" | "retrieve" | "list" | "delete" | "search"
- `key` (optional): Memory key
- `value` (optional): Value to store
- `namespace` (optional, default: "default"): Namespace
- `ttl` (optional): Time-to-live in seconds

### memory_search
Search memory with pattern matching.

**Parameters:**
- `pattern` (required): Search pattern (wildcards supported)
- `namespace` (optional): Namespace filter
- `limit` (optional, default: 10): Max results

### memory_persist
Enable cross-session memory persistence.

**Parameters:**
- `sessionId` (optional): Session identifier

### memory_namespace
Manage memory namespaces.

**Parameters:**
- `namespace` (required): Namespace name
- `action` (required): "create" | "delete" | "list"

### memory_backup
Create backup of memory stores.

**Parameters:**
- `path` (optional): Backup destination

### memory_restore
Restore memory from backup.

**Parameters:**
- `backupPath` (required): Backup file path

### memory_compress
Compress memory data for efficiency.

**Parameters:**
- `namespace` (optional): Specific namespace to compress

### memory_sync
Synchronize memory across instances.

**Parameters:**
- `target` (required): Target instance identifier

### memory_analytics
Analyze memory usage patterns.

**Parameters:**
- `timeframe` (optional): Analysis time range

---

## Neural & AI Features

### neural_status
Check neural network status.

**Parameters:**
- `modelId` (optional): Specific model

### neural_train
Train neural patterns with WASM SIMD acceleration.

**Parameters:**
- `pattern_type` (required): "coordination" | "optimization" | "prediction"
- `training_data` (required): JSON training data
- `epochs` (optional, default: 50): Training iterations (1-100)

### neural_patterns
Analyze cognitive patterns.

**Parameters:**
- `action` (required): "analyze" | "learn" | "predict"
- `operation` (optional): Operation type
- `metadata` (optional): Additional context

### neural_predict
Make AI predictions using trained models.

**Parameters:**
- `modelId` (required): Model identifier
- `input` (required): Input data

### neural_compress
Compress neural models for efficiency.

**Parameters:**
- `modelId` (required): Model to compress
- `ratio` (optional): Compression ratio

### neural_explain
Get AI explainability for predictions.

**Parameters:**
- `modelId` (required): Model identifier
- `prediction` (required): Prediction to explain

### model_load
Load pre-trained models.

**Parameters:**
- `modelPath` (required): Path to model file

### model_save
Save trained models.

**Parameters:**
- `modelId` (required): Model to save
- `path` (required): Save destination

### wasm_optimize
WASM SIMD optimization for neural operations.

**Parameters:**
- `operation` (optional): Specific operation to optimize

### inference_run
Run neural inference on data.

**Parameters:**
- `modelId` (required): Model identifier
- `data` (required): Input data array

### pattern_recognize
Advanced pattern recognition in data.

**Parameters:**
- `data` (required): Data array
- `patterns` (optional): Known patterns to match

### cognitive_analyze
Analyze cognitive behavior patterns.

**Parameters:**
- `behavior` (required): Behavior to analyze

### learning_adapt
Adaptive learning from experience.

**Parameters:**
- `experience` (required): Experience object

### ensemble_create
Create model ensembles for better predictions.

**Parameters:**
- `models` (required): Array of model IDs
- `strategy` (optional): Ensemble strategy

### transfer_learn
Transfer learning between domains.

**Parameters:**
- `sourceModel` (required): Source model
- `targetDomain` (required): Target domain

---

## SPARC Methodology

### sparc_mode
Run SPARC development methodology with swarm coordination.

**Parameters:**
- `mode` (required): Development mode
  - `"dev"` - Full development workflow
  - `"api"` - API-focused development
  - `"ui"` - UI/Frontend development
  - `"test"` - Test-driven development
  - `"refactor"` - Code refactoring workflow
- `task_description` (required): Task description
- `options` (optional): Configuration object
  - `use_swarm`: Enable swarm coordination
  - `topology`: Swarm topology to use
  - `enable_neural`: Enable neural learning
  - `max_agents`: Maximum agents
  - `priority`: Task priority

**Example:**
```javascript
mcp__claude-flow__sparc_mode {
  mode: "dev",
  task_description: "Build OAuth2 authentication system",
  options: {
    use_swarm: true,
    topology: "ring",
    enable_neural: true,
    max_agents: 5,
    priority: "high"
  }
}
```

**SPARC Phases:**
1. **Specification** - Requirements analysis
2. **Pseudocode** - Algorithm design
3. **Architecture** - System design
4. **Refinement** - TDD implementation
5. **Completion** - Integration and validation

---

## Workflow Automation

### workflow_create
Create custom reusable workflows.

**Parameters:**
- `name` (required): Workflow name
- `steps` (required): Array of workflow steps
- `triggers` (optional): Trigger conditions

### workflow_execute
Execute predefined workflows.

**Parameters:**
- `workflowId` (required): Workflow ID
- `params` (optional): Execution parameters

### workflow_export
Export workflow definitions.

**Parameters:**
- `workflowId` (required): Workflow to export
- `format` (optional): Export format

### workflow_template
Manage workflow templates.

**Parameters:**
- `action` (required): "create" | "update" | "delete" | "list"
- `template` (optional): Template object

### automation_setup
Setup automation rules.

**Parameters:**
- `rules` (required): Array of automation rules

### pipeline_create
Create CI/CD pipelines.

**Parameters:**
- `config` (required): Pipeline configuration

### scheduler_manage
Manage task scheduling.

**Parameters:**
- `action` (required): Scheduler action
- `schedule` (required): Schedule object

### trigger_setup
Setup event triggers.

**Parameters:**
- `events` (required): Array of events
- `actions` (required): Actions to trigger

### batch_process
Batch processing operations.

**Parameters:**
- `items` (required): Items to process
- `operation` (required): Operation to perform

### parallel_execute
Execute tasks in parallel.

**Parameters:**
- `tasks` (required): Array of tasks

---

## GitHub Integration

### github_repo_analyze
Analyze repository for code quality, performance, or security.

**Parameters:**
- `repo` (required): "owner/repository"
- `analysis_type` (optional): "code_quality" | "performance" | "security"

### github_pr_manage
Pull request management.

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
- `action` (required): "triage" | "assign" | "close"

### github_release_coord
Release coordination and management.

**Parameters:**
- `repo` (required): Repository
- `version` (required): Version string

### github_workflow_auto
Workflow automation for GitHub.

**Parameters:**
- `repo` (required): Repository
- `workflow` (required): Workflow object

### github_sync_coord
Multi-repo synchronization coordination.

**Parameters:**
- `repos` (required): Array of repositories

### github_metrics
Repository metrics and analytics.

**Parameters:**
- `repo` (required): Repository

---

## Performance & Monitoring

### performance_report
Generate performance reports with real-time metrics.

**Parameters:**
- `format` (optional, default: "summary"): "summary" | "detailed" | "json"
- `timeframe` (optional, default: "24h"): "24h" | "7d" | "30d"

### bottleneck_analyze
Identify performance bottlenecks.

**Parameters:**
- `component` (optional): Component to analyze
- `metrics` (optional): Metrics array

### benchmark_run
Execute performance benchmarks.

**Parameters:**
- `suite` (optional): Benchmark suite

### token_usage
Analyze token consumption.

**Parameters:**
- `operation` (optional): Specific operation
- `timeframe` (optional, default: "24h"): Time range

### metrics_collect
Collect system metrics.

**Parameters:**
- `components` (optional): Components to monitor

### trend_analysis
Analyze performance trends.

**Parameters:**
- `metric` (required): Metric to analyze
- `period` (optional): Analysis period

### cost_analysis
Cost and resource analysis.

**Parameters:**
- `timeframe` (optional): Analysis timeframe

### quality_assess
Quality assessment metrics.

**Parameters:**
- `target` (required): Assessment target
- `criteria` (optional): Quality criteria

### error_analysis
Error pattern analysis.

**Parameters:**
- `logs` (optional): Log data to analyze

### usage_stats
System usage statistics.

**Parameters:**
- `component` (optional): Specific component

### health_check
System health monitoring.

**Parameters:**
- `components` (optional): Components to check

---

## Dynamic Agent Adaptation (DAA)

### daa_agent_create
Create dynamic agents with learning capabilities.

**Parameters:**
- `agent_type` (required): Agent type
- `capabilities` (optional): Capabilities array
- `resources` (optional): Resource allocation

### daa_agent_adapt
Trigger agent adaptation based on feedback.

**Parameters:**
- `agentId` (required): Agent to adapt
- `performanceScore` (optional): Score 0-1
- `feedback` (optional): Feedback message
- `suggestions` (optional): Improvement suggestions

### daa_capability_match
Match capabilities to task requirements.

**Parameters:**
- `task_requirements` (required): Required capabilities
- `available_agents` (optional): Agent filter

### daa_resource_alloc
Dynamic resource allocation.

**Parameters:**
- `resources` (required): Resource object
- `agents` (optional): Agent array

### daa_lifecycle_manage
Agent lifecycle management.

**Parameters:**
- `agentId` (required): Agent ID
- `action` (required): "start" | "pause" | "stop" | "restart"

### daa_communication
Inter-agent communication.

**Parameters:**
- `from` (required): Source agent
- `to` (required): Target agent
- `message` (required): Message object

### daa_consensus
Consensus mechanisms for distributed decisions.

**Parameters:**
- `agents` (required): Participating agents
- `proposal` (required): Proposal object

### daa_fault_tolerance
Fault tolerance and recovery.

**Parameters:**
- `agentId` (required): Agent ID
- `strategy` (optional): Recovery strategy

### daa_optimization
Performance optimization for DAA.

**Parameters:**
- `target` (required): Optimization target
- `metrics` (optional): Metrics array

---

## System & Configuration

### topology_optimize
Auto-optimize swarm topology.

**Parameters:**
- `swarmId` (optional): Swarm to optimize

### load_balance
Distribute tasks efficiently.

**Parameters:**
- `swarmId` (optional): Swarm ID
- `tasks` (optional): Tasks to balance

### coordination_sync
Synchronize agent coordination.

**Parameters:**
- `swarmId` (optional): Swarm to sync

### cache_manage
Manage coordination cache.

**Parameters:**
- `action` (required): Cache action
- `key` (optional): Cache key

### state_snapshot
Create state snapshots.

**Parameters:**
- `name` (optional): Snapshot name

### context_restore
Restore execution context.

**Parameters:**
- `snapshotId` (required): Snapshot to restore

### terminal_execute
Execute terminal commands.

**Parameters:**
- `command` (required): Command to execute
- `args` (optional): Command arguments

### config_manage
Configuration management.

**Parameters:**
- `action` (required): Config action
- `config` (optional): Config object

### features_detect
Detect runtime features and capabilities.

**Parameters:**
- `component` (optional): Component to check

### security_scan
Security scanning and vulnerability detection.

**Parameters:**
- `target` (required): Scan target
- `depth` (optional): Scan depth

### backup_create
Create system backups.

**Parameters:**
- `components` (optional): Components to backup
- `destination` (optional): Backup destination

### restore_system
System restoration from backup.

**Parameters:**
- `backupId` (required): Backup to restore

### log_analysis
Log analysis and insights.

**Parameters:**
- `logFile` (required): Log file path
- `patterns` (optional): Patterns to search

### diagnostic_run
System diagnostics.

**Parameters:**
- `components` (optional): Components to diagnose

---

## Advanced Features

### query_control
Control running queries (pause, resume, terminate, change model).

**Parameters:**
- `action` (required): "pause" | "resume" | "terminate" | "change_model" | "change_permissions" | "execute_command"
- `queryId` (required): Query ID
- `model` (optional): New model (for change_model)
- `permissionMode` (optional): New permissions (for change_permissions)
- `command` (optional): Command (for execute_command)

**Example:**
```javascript
mcp__claude-flow__query_control {
  action: "change_model",
  queryId: "query-123",
  model: "claude-3-5-sonnet-20241022"
}
```

### query_list
List all active queries and their status.

**Parameters:**
- `includeHistory` (optional, default: false): Include completed queries

---

## Quick Reference: Common Workflows

### 1. Full-Stack Development with SPARC
```javascript
// Use SPARC mode for complete development workflow
mcp__claude-flow__sparc_mode {
  mode: "dev",
  task_description: "Build user authentication system",
  options: {
    use_swarm: true,
    topology: "ring",
    enable_neural: true
  }
}
```

### 2. Parallel Agent Spawning (10-20x faster)
```javascript
// Spawn multiple agents in parallel
mcp__claude-flow__agents_spawn_parallel {
  agents: [
    { type: "coder", name: "Backend", capabilities: ["python"] },
    { type: "coder", name: "Frontend", capabilities: ["react"] },
    { type: "tester", name: "QA", capabilities: ["pytest"] }
  ],
  maxConcurrency: 3
}
```

### 3. Memory-Persistent Workflow
```javascript
// Store decision
mcp__claude-flow__memory_usage {
  action: "store",
  namespace: "project/architecture",
  key: "database",
  value: "PostgreSQL",
  ttl: 2592000  // 30 days
}
```

### 4. Neural Pattern Learning
```javascript
// Train from successful execution
mcp__claude-flow__neural_train {
  pattern_type: "coordination",
  training_data: JSON.stringify({
    task: "API development",
    outcome: "success",
    metrics: { quality: 0.92 }
  }),
  epochs: 50
}
```

### 5. GitHub Integration
```javascript
// Automated code review
mcp__claude-flow__github_code_review {
  repo: "owner/repository",
  pr: 123
}
```

---

## Tool Categories Summary

| Category | Tool Count | Key Tools |
|----------|------------|-----------|
| Swarm Management | 5 | swarm_init, swarm_status, swarm_scale |
| Agent Management | 4 | agent_spawn, agents_spawn_parallel, agent_metrics |
| Task Orchestration | 3 | task_orchestrate, task_status, task_results |
| Memory Management | 9 | memory_usage, memory_search, memory_backup |
| Neural & AI | 14 | neural_train, neural_predict, model_load |
| SPARC Methodology | 1 | sparc_mode |
| Workflow Automation | 9 | workflow_create, automation_setup, parallel_execute |
| GitHub Integration | 7 | github_pr_manage, github_code_review |
| Performance & Monitoring | 10 | performance_report, bottleneck_analyze |
| DAA | 8 | daa_agent_create, daa_agent_adapt |
| System & Configuration | 14 | config_manage, security_scan, log_analysis |
| Advanced Features | 2 | query_control, query_list |

**Total: 86+ MCP Tools**
