---
name: claude-flow-mcp
description: Master Claude Flow MCP tools for swarm orchestration, multi-agent coordination, and distributed task execution. Use this skill when coordinating multiple AI agents, implementing parallel workflows, managing swarm topologies (mesh, hierarchical, ring, star), orchestrating complex tasks across agent teams, or integrating neural patterns and memory management in distributed systems.
---

# Claude Flow MCP

## Overview

This skill provides comprehensive guidance for using Claude Flow MCP (Model Context Protocol) tools to orchestrate multi-agent swarms, coordinate distributed tasks, and leverage advanced features like neural pattern recognition, persistent memory, and GitHub integration.

Claude Flow MCP enables:
- Multi-agent swarm coordination with various topologies
- Parallel task orchestration across agent teams
- Neural pattern learning and cognitive analysis
- Cross-session memory persistence
- GitHub workflow automation
- Performance monitoring and optimization

## Workflow Decision Tree

Start here to determine the appropriate Claude Flow workflow:

```
What do you need to accomplish?
├─ Single complex task → Use task_orchestrate with adaptive strategy
├─ Multiple independent tasks → Initialize swarm, spawn agents, parallel execution
├─ Iterative development workflow → Use SPARC mode integration
├─ GitHub operations → Use github_* tools for repo/PR/issue management
├─ Learning from patterns → Use neural_train and neural_patterns
└─ Cross-session context → Use memory_usage with namespacing
```

## Core Workflow: Swarm Initialization and Task Orchestration

### 1. Initialize Swarm Topology

Choose the topology based on task characteristics:

**Mesh Topology** - Best for collaborative tasks requiring peer communication
```
Use when: Multiple agents need to share information and coordinate decisions
Example: Code review with discussion between multiple reviewers
Tool: mcp__claude-flow__swarm_init { topology: "mesh", maxAgents: 6 }
```

**Hierarchical Topology** - Best for tasks with clear delegation and reporting
```
Use when: Central coordination with specialized worker agents
Example: Full-stack development with coordinator and specialized developers
Tool: mcp__claude-flow__swarm_init { topology: "hierarchical", maxAgents: 8 }
```

**Star Topology** - Best for centralized coordination with independent execution
```
Use when: Central orchestrator distributes independent subtasks
Example: Parallel data processing tasks
Tool: mcp__claude-flow__swarm_init { topology: "star", maxAgents: 5 }
```

**Ring Topology** - Best for sequential processing with handoffs
```
Use when: Pipeline processing where each agent builds on previous work
Example: SPARC workflow (spec → pseudocode → architecture → refinement)
Tool: mcp__claude-flow__swarm_init { topology: "ring", maxAgents: 4 }
```

### 2. Spawn Specialized Agents

After initializing the swarm, spawn agents with specific capabilities:

```javascript
// Spawn agents based on task requirements
mcp__claude-flow__agent_spawn {
  type: "researcher",
  name: "Requirements Analyst",
  capabilities: ["requirements_analysis", "documentation_search"]
}

mcp__claude-flow__agent_spawn {
  type: "coder",
  name: "Backend Developer",
  capabilities: ["python", "fastapi", "database_design"]
}

mcp__claude-flow__agent_spawn {
  type: "tester",
  name: "QA Engineer",
  capabilities: ["pytest", "integration_testing", "performance_testing"]
}
```

**Available Agent Types:**
- `researcher` - Information gathering, analysis, documentation
- `coder` - Implementation, code generation
- `analyst` - Code review, quality assessment
- `optimizer` - Performance tuning, bottleneck identification
- `coordinator` - Task orchestration, team coordination
- `tester` - Test creation, validation
- `reviewer` - Code review, security analysis
- `architect` - System design, architecture decisions

### 3. Orchestrate Tasks

Use `task_orchestrate` to distribute work across the swarm:

```javascript
// Sequential execution - for dependent tasks
mcp__claude-flow__task_orchestrate {
  task: "Implement user authentication with OAuth2",
  strategy: "sequential",
  priority: "high"
}

// Parallel execution - for independent tasks
mcp__claude-flow__task_orchestrate {
  task: "Run comprehensive test suite across all modules",
  strategy: "parallel",
  priority: "medium"
}

// Adaptive execution - let system decide based on dependencies
mcp__claude-flow__task_orchestrate {
  task: "Refactor codebase for better performance",
  strategy: "adaptive",
  priority: "medium",
  maxAgents: 4
}
```

## Memory Management Workflows

### Store Cross-Session Context

Use memory_usage to maintain context across sessions:

```javascript
// Store important decisions
mcp__claude-flow__memory_usage {
  action: "store",
  namespace: "project/decisions",
  key: "auth_approach",
  value: JSON.stringify({
    decision: "OAuth2 with JWT tokens",
    rationale: "Better scalability, industry standard",
    timestamp: "2025-10-18"
  }),
  ttl: 604800  // 7 days in seconds
}

// Store agent findings
mcp__claude-flow__memory_usage {
  action: "store",
  namespace: "swarm/analysis",
  key: "performance_bottlenecks",
  value: "Database query optimization needed in user service"
}

// Retrieve context in future sessions
mcp__claude-flow__memory_usage {
  action: "retrieve",
  namespace: "project/decisions",
  key: "auth_approach"
}
```

### Search Memory Patterns

Find relevant context across namespaces:

```javascript
mcp__claude-flow__memory_search {
  pattern: "auth*",
  namespace: "project/decisions",
  limit: 10
}
```

## Neural Pattern Learning

### Train from Successful Patterns

After completing tasks successfully, train neural patterns:

```javascript
// Train on coordination patterns
mcp__claude-flow__neural_train {
  pattern_type: "coordination",
  training_data: JSON.stringify({
    task: "Multi-agent API development",
    topology: "hierarchical",
    agents: 6,
    outcome: "success",
    metrics: {
      completion_time: 3600,
      quality_score: 0.92
    }
  }),
  epochs: 50
}

// Train on optimization patterns
mcp__claude-flow__neural_train {
  pattern_type: "optimization",
  training_data: JSON.stringify({
    bottleneck: "database_queries",
    solution: "add_indexes_and_caching",
    improvement: 0.73
  })
}
```

### Analyze and Predict

Use trained patterns to inform decisions:

```javascript
// Analyze cognitive patterns
mcp__claude-flow__neural_patterns {
  action: "analyze",
  operation: "code_review",
  metadata: { language: "python", complexity: "high" }
}

// Make predictions based on learned patterns
mcp__claude-flow__neural_predict {
  modelId: "coordination_model",
  input: JSON.stringify({
    task_type: "full_stack_feature",
    team_size: 5,
    complexity: "medium"
  })
}
```

## GitHub Integration Workflows

### Repository Analysis

```javascript
mcp__claude-flow__github_repo_analyze {
  repo: "owner/repository",
  analysis_type: "code_quality"
}
```

### Pull Request Management

```javascript
// Automated code review
mcp__claude-flow__github_code_review {
  repo: "owner/repository",
  pr: 123
}

// PR management
mcp__claude-flow__github_pr_manage {
  repo: "owner/repository",
  pr_number: 123,
  action: "review"  // or "merge", "close"
}
```

### Issue Tracking

```javascript
mcp__claude-flow__github_issue_track {
  repo: "owner/repository",
  action: "triage"  // or "assign", "close"
}
```

## Monitoring and Performance

### Check Swarm Status

```javascript
// Get overall swarm health
mcp__claude-flow__swarm_status {
  swarmId: "swarm-abc123"
}

// List active agents
mcp__claude-flow__agent_list {
  swarmId: "swarm-abc123"
}

// Get agent performance metrics
mcp__claude-flow__agent_metrics {
  agentId: "agent-xyz789"
}
```

### Monitor Task Progress

```javascript
// Check task status
mcp__claude-flow__task_status {
  taskId: "task-123456"
}

// Retrieve completed task results
mcp__claude-flow__task_results {
  taskId: "task-123456",
  format: "detailed"
}
```

### Performance Analysis

```javascript
// Run benchmarks
mcp__claude-flow__benchmark_run {
  suite: "all"
}

// Analyze bottlenecks
mcp__claude-flow__bottleneck_analyze {
  component: "swarm_coordination",
  metrics: ["latency", "throughput", "agent_utilization"]
}

// Generate performance report
mcp__claude-flow__performance_report {
  format: "detailed",
  timeframe: "24h"
}
```

## Advanced Features

### Dynamic Agent Adaptation

```javascript
// Create dynamic agents with DAA
mcp__claude-flow__daa_agent_create {
  agent_type: "specialist",
  capabilities: ["zoho_crm", "account_analysis", "recommendation_engine"]
}

// Agent learns and adapts
mcp__claude-flow__daa_agent_adapt {
  agentId: "agent-123",
  performanceScore: 0.87,
  feedback: "Excellent account risk detection",
  suggestions: ["Improve response time", "Add more data sources"]
}
```

### Workflow Automation

```javascript
// Create reusable workflow
mcp__claude-flow__workflow_create {
  name: "zoho_account_health_check",
  steps: [
    { action: "fetch_account_data", agent: "zoho_specialist" },
    { action: "analyze_engagement", agent: "analyst" },
    { action: "detect_risks", agent: "risk_detector" },
    { action: "generate_recommendations", agent: "recommendation_engine" }
  ],
  triggers: ["daily_schedule", "manual_request"]
}

// Execute workflow
mcp__claude-flow__workflow_execute {
  workflowId: "workflow-zoho-health",
  params: { account_id: "12345" }
}
```

### SPARC Mode Integration

The **SPARC methodology** (Specification, Pseudocode, Architecture, Refinement, Completion) is a systematic approach to software development that integrates seamlessly with Claude Flow swarm coordination.

#### SPARC Development Modes

**Available Modes:**
- `"dev"` - Full development workflow (all SPARC phases)
- `"api"` - API-focused development
- `"ui"` - UI/Frontend development
- `"test"` - Test-driven development
- `"refactor"` - Code refactoring workflow

**Basic Usage:**
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

#### SPARC Phases Explained

**Phase 1: Specification**
- Requirements analysis and use case definition
- User story creation
- Acceptance criteria specification
- Agent: Requirements Analyst

**Phase 2: Pseudocode**
- Algorithm design and logic flow
- High-level implementation planning
- Data structure design
- Agent: Pseudocode Designer

**Phase 3: Architecture**
- System architecture and component design
- API contract definition
- Database schema design
- Integration patterns
- Agent: System Architect

**Phase 4: Refinement**
- Test-driven development (TDD)
- Implementation with continuous testing
- Code refinement and optimization
- Agent: Implementation Engineer

**Phase 5: Completion**
- Integration testing
- Documentation finalization
- Validation against requirements
- Deployment preparation
- Agent: Completion Validator

#### SPARC with Ring Topology

SPARC works best with **ring topology** for sequential handoffs:

```javascript
// Initialize ring topology for SPARC
mcp__claude-flow__swarm_init { topology: "ring", maxAgents: 5 }

// Spawn SPARC-specialized agents
mcp__claude-flow__agents_spawn_parallel {
  agents: [
    { type: "analyst", name: "Spec Writer", capabilities: ["requirements"] },
    { type: "architect", name: "Pseudocode Designer", capabilities: ["algorithms"] },
    { type: "architect", name: "System Architect", capabilities: ["architecture"] },
    { type: "coder", name: "Implementation Engineer", capabilities: ["tdd", "python"] },
    { type: "reviewer", name: "Completion Validator", capabilities: ["validation"] }
  ]
}

// Execute SPARC workflow
mcp__claude-flow__sparc_mode {
  mode: "dev",
  task_description: "Implement user authentication with JWT",
  options: {
    use_swarm: true,
    topology: "ring",
    enable_neural: true
  }
}
```

#### Memory Usage in SPARC

Store phase outputs for cross-phase reference:

```javascript
// After Specification phase
mcp__claude-flow__memory_usage {
  action: "store",
  namespace: "sparc/specification",
  key: "user_auth_requirements",
  value: JSON.stringify({
    features: ["JWT tokens", "OAuth2", "Password reset"],
    acceptance_criteria: [...],
    user_stories: [...]
  }),
  ttl: 604800  // 1 week
}

// Later phases retrieve the specification
mcp__claude-flow__memory_usage {
  action: "retrieve",
  namespace: "sparc/specification",
  key: "user_auth_requirements"
}
```

#### SPARC Workflow Templates

Pre-built SPARC workflow available in:
`assets/workflow_templates/sparc_pipeline.json`

Load and execute:
```javascript
const sparcWorkflow = require('./assets/workflow_templates/sparc_pipeline.json');
mcp__claude-flow__workflow_execute {
  workflowId: "sparc_pipeline",
  params: { task: "Build authentication system" }
}
```

## Best Practices

### 1. Topology Selection
- **Mesh**: Use for collaborative problem-solving (3-6 agents)
- **Hierarchical**: Use for complex projects with delegation (5-10 agents)
- **Star**: Use for parallel independent tasks (3-8 agents)
- **Ring**: Use for sequential workflows (3-5 agents)

### 2. Memory Organization
- Use clear namespace hierarchies: `project/category/subcategory`
- Set appropriate TTLs: short-term (1 hour), medium (7 days), long-term (30 days)
- Store decisions, patterns, and context - not raw data

### 3. Neural Training
- Train after successful task completion
- Include outcome metrics in training data
- Use pattern recognition for similar future tasks

### 4. Agent Spawning
- Spawn minimum viable agents initially
- Scale up based on task complexity
- Use specialized capabilities for focused roles

### 5. Task Orchestration
- Use "adaptive" strategy when unsure about dependencies
- Set appropriate priorities (critical > high > medium > low)
- Monitor task status for long-running operations

## Integration with Project

This skill integrates seamlessly with the Sergas Agents project:

### Zoho CRM Workflows
```javascript
// Spawn Zoho-specialized agents
mcp__claude-flow__agent_spawn {
  type: "specialist",
  name: "Zoho CRM Analyst",
  capabilities: ["zoho_api", "account_health", "risk_detection"]
}

// Orchestrate account analysis
mcp__claude-flow__task_orchestrate {
  task: "Analyze all at-risk accounts and generate recommendations",
  strategy: "parallel",
  priority: "high",
  maxAgents: 4
}
```

### Account Health Analysis
Combine with `account-analysis` and `zoho-crm-analysis` skills for comprehensive account management automation.

## Resources

### scripts/
Executable utilities for common operations:

- **`swarm_orchestrator.py`** - Helper script for complex swarm setups
  - `python swarm_orchestrator.py fullstack <feature_name>` - Create full-stack dev swarm
  - `python swarm_orchestrator.py parallel <task1> <task2> ...` - Parallel task processing

- **`memory_manager.py`** - Memory namespace management utilities
  - `python memory_manager.py store <key> <value> [namespace] [ttl]` - Store memory
  - `python memory_manager.py retrieve <key> [namespace]` - Retrieve memory
  - `python memory_manager.py search <pattern> [namespace]` - Search memory
  - `python memory_manager.py decision <name> <value> <rationale>` - Store decisions
  - `python memory_manager.py finding <agent> <finding> [severity]` - Store agent findings

### references/
Comprehensive documentation for reference:

- **`mcp_tools_complete.md`** - **COMPLETE catalog of 86+ MCP tools**
  - All swarm management tools
  - Agent spawning and coordination
  - Task orchestration
  - Memory management (9 tools)
  - Neural & AI features (14 tools)
  - **SPARC methodology integration**
  - Workflow automation (9 tools)
  - GitHub integration (7 tools)
  - Performance monitoring (10 tools)
  - DAA (Dynamic Agent Adaptation) tools
  - System configuration and diagnostics
  - Quick reference tables and examples

- **`topology_patterns.md`** - Topology selection guide
  - Decision matrices for topology selection
  - Performance characteristics
  - Use cases by domain and team size
  - Hybrid patterns
  - Common mistakes and solutions
  - Real-world examples

### assets/
Pre-built templates and configurations:

- **`workflow_templates/`** - Ready-to-use workflow configurations
  - `full_stack_development.json` - Hierarchical topology for full-stack features
  - `zoho_account_analysis.json` - Star topology for Zoho CRM analysis
  - `sparc_pipeline.json` - Ring topology for SPARC methodology

- **`agent_configs/`** - Sample agent configuration files
  - README with usage instructions
  - Templates for common agent roles

## Quick Start Examples

### 1. SPARC Development Workflow
```javascript
mcp__claude-flow__sparc_mode {
  mode: "dev",
  task_description: "Build user authentication system",
  options: { use_swarm: true, topology: "ring", enable_neural: true }
}
```

### 2. Parallel Agent Spawning (10-20x faster)
```javascript
mcp__claude-flow__agents_spawn_parallel {
  agents: [
    { type: "coder", name: "Backend", capabilities: ["python", "fastapi"] },
    { type: "coder", name: "Frontend", capabilities: ["react", "typescript"] },
    { type: "tester", name: "QA", capabilities: ["pytest", "jest"] }
  ]
}
```

### 3. Zoho CRM Account Analysis
```javascript
// Load pre-built workflow
const workflow = require('./assets/workflow_templates/zoho_account_analysis.json');
mcp__claude-flow__workflow_execute {
  workflowId: "zoho_account_analysis",
  params: { account_id: "12345" }
}
```

## Tool Reference

For the complete catalog of **86+ MCP tools** with parameters, examples, and use cases, see:
- `references/mcp_tools_complete.md`

**Key Tool Categories:**
- Swarm Management (5 tools)
- Agent Management (4 tools including parallel spawning)
- Task Orchestration (3 tools)
- Memory Management (9 tools)
- Neural & AI (14 tools)
- **SPARC Methodology (1 comprehensive tool)**
- Workflow Automation (9 tools)
- GitHub Integration (7 tools)
- Performance & Monitoring (10 tools)
- Dynamic Agent Adaptation (8 tools)
- System & Configuration (14 tools)
- Advanced Features (2 tools)
