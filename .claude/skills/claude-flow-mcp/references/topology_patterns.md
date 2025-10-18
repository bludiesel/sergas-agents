# Topology Selection Guide

Comprehensive guide for choosing the right swarm topology based on task characteristics.

## Topology Overview

Claude Flow supports four swarm topologies, each optimized for different coordination patterns:

| Topology | Best For | Agent Count | Communication Pattern |
|----------|----------|-------------|----------------------|
| Mesh | Collaborative problem-solving | 3-6 | Peer-to-peer, full connectivity |
| Hierarchical | Complex projects with delegation | 5-10 | Top-down with feedback loops |
| Star | Parallel independent tasks | 3-8 | Hub-and-spoke, centralized |
| Ring | Sequential pipeline workflows | 3-5 | Unidirectional handoffs |

## Mesh Topology

### Characteristics
- **Communication**: Every agent can communicate with every other agent
- **Coordination**: Distributed decision-making through consensus
- **Scalability**: Limited (overhead increases quadratically)
- **Fault Tolerance**: High (no single point of failure)

### Use Cases
- Code review with multiple reviewers discussing findings
- Architectural design requiring consensus
- Brainstorming sessions with idea cross-pollination
- Security audits with collaborative threat analysis

### Example Scenario: Multi-Reviewer Code Review
```javascript
mcp__claude-flow__swarm_init {
  topology: "mesh",
  maxAgents: 5,
  strategy: "balanced"
}

// Spawn reviewers with different specializations
agents: [
  { type: "reviewer", capabilities: ["security", "auth"] },
  { type: "reviewer", capabilities: ["performance", "optimization"] },
  { type: "reviewer", capabilities: ["maintainability", "clean_code"] },
  { type: "reviewer", capabilities: ["testing", "edge_cases"] },
  { type: "coordinator", capabilities: ["synthesis", "prioritization"] }
]
```

**Why Mesh**: Each reviewer needs to see others' findings to avoid duplication and build on insights. The coordinator synthesizes without being a bottleneck.

### Performance Characteristics
- **Setup Time**: Medium
- **Communication Overhead**: High (O(n²))
- **Decision Speed**: Slower (consensus required)
- **Quality**: High (multiple perspectives)

## Hierarchical Topology

### Characteristics
- **Communication**: Tree structure with coordinator at root
- **Coordination**: Central coordinator delegates to specialized workers
- **Scalability**: Good (overhead grows linearly)
- **Fault Tolerance**: Medium (coordinator is critical path)

### Use Cases
- Full-stack feature development
- Large codebase refactoring
- System design with multiple components
- Multi-module testing

### Example Scenario: Full-Stack Feature Development
```javascript
mcp__claude-flow__swarm_init {
  topology: "hierarchical",
  maxAgents: 8,
  strategy: "specialized"
}

// Hierarchy:
// Coordinator (level 0)
//   ├─ Backend Lead (level 1)
//   │   ├─ API Developer (level 2)
//   │   └─ Database Developer (level 2)
//   ├─ Frontend Lead (level 1)
//   │   ├─ UI Developer (level 2)
//   │   └─ State Manager (level 2)
//   └─ QA Lead (level 1)
//       ├─ Unit Tester (level 2)
//       └─ Integration Tester (level 2)
```

**Why Hierarchical**: Complex projects need clear delegation. Coordinator manages overall progress while leads coordinate their domains.

### Performance Characteristics
- **Setup Time**: Medium-High
- **Communication Overhead**: Low-Medium (O(n))
- **Decision Speed**: Fast (clear authority)
- **Quality**: High (specialized expertise)

## Star Topology

### Characteristics
- **Communication**: All agents connect to central hub only
- **Coordination**: Central orchestrator distributes work
- **Scalability**: Excellent (hub manages all coordination)
- **Fault Tolerance**: Low (hub is single point of failure)

### Use Cases
- Parallel data processing
- Independent feature development
- Batch operations (multiple similar tasks)
- Map-reduce style workflows

### Example Scenario: Multi-Module Test Suite
```javascript
mcp__claude-flow__swarm_init {
  topology: "star",
  maxAgents: 6,
  strategy: "balanced"
}

// Hub: Test Coordinator
// Spokes: Module testers (independent)
agents: [
  { type: "coordinator", name: "Test Hub" },
  { type: "tester", capabilities: ["auth_module"] },
  { type: "tester", capabilities: ["api_module"] },
  { type: "tester", capabilities: ["database_module"] },
  { type: "tester", capabilities: ["frontend_module"] },
  { type: "tester", capabilities: ["integration_module"] }
]
```

**Why Star**: Each module can be tested independently. The hub collects results and generates final report.

### Performance Characteristics
- **Setup Time**: Low
- **Communication Overhead**: Low (O(n))
- **Decision Speed**: Very Fast (no inter-agent communication)
- **Quality**: Good (if tasks are truly independent)

## Ring Topology

### Characteristics
- **Communication**: Unidirectional, agent i → agent i+1
- **Coordination**: Sequential handoffs with state accumulation
- **Scalability**: Good (linear complexity)
- **Fault Tolerance**: Low (breaks if any agent fails)

### Use Cases
- SPARC workflow (spec → pseudocode → architecture → refinement → completion)
- CI/CD pipeline (build → test → stage → deploy)
- Data processing pipeline (extract → transform → load)
- Document generation (research → draft → review → publish)

### Example Scenario: SPARC Development Workflow
```javascript
mcp__claude-flow__swarm_init {
  topology: "ring",
  maxAgents: 5,
  strategy: "specialized"
}

// Sequential flow:
// Specification → Pseudocode → Architecture → Refinement → Completion
agents: [
  { type: "analyst", name: "Spec Writer", position: 0 },
  { type: "architect", name: "Pseudocode Designer", position: 1 },
  { type: "architect", name: "System Architect", position: 2 },
  { type: "coder", name: "Implementation Engineer", position: 3 },
  { type: "reviewer", name: "Completion Validator", position: 4 }
]
```

**Why Ring**: Each phase builds on the previous. Specification informs pseudocode, which informs architecture, etc.

### Performance Characteristics
- **Setup Time**: Low-Medium
- **Communication Overhead**: Very Low (O(n))
- **Decision Speed**: Slow (sequential processing)
- **Quality**: Very High (each stage validates previous)

## Decision Matrix

### By Task Characteristics

| Task Characteristic | Recommended Topology |
|-------------------|---------------------|
| Tasks are independent | Star |
| Tasks require collaboration | Mesh |
| Tasks have clear hierarchy | Hierarchical |
| Tasks are sequential | Ring |
| Need fault tolerance | Mesh |
| Need maximum speed | Star |
| Need maximum quality | Ring or Mesh |
| Large team (7+ agents) | Hierarchical |
| Small team (3-5 agents) | Mesh or Ring |

### By Domain

| Domain | Topology | Rationale |
|--------|----------|-----------|
| Code Review | Mesh | Reviewers discuss findings |
| Full-Stack Dev | Hierarchical | Clear component ownership |
| Data Processing | Star | Parallel independent tasks |
| CI/CD Pipeline | Ring | Sequential validation stages |
| API Development | Hierarchical | Backend/Frontend separation |
| Testing Suite | Star | Independent test modules |
| Architecture Design | Mesh | Collaborative decision-making |
| Refactoring | Hierarchical | Coordinated changes |

### By Team Size

**3 Agents:**
- Mesh: Best collaboration
- Ring: For sequential workflows
- Star: For simple parallel tasks

**4-6 Agents:**
- Mesh: If highly collaborative
- Hierarchical: For moderate complexity
- Star: For parallel execution
- Ring: For pipeline workflows

**7+ Agents:**
- Hierarchical: Required for manageability
- Star: If tasks are independent
- Mesh: Avoid (too much overhead)

## Hybrid Patterns

For complex scenarios, consider hybrid approaches:

### Hierarchical-Mesh Hybrid
```
Coordinator (hierarchical root)
  ├─ Team A (mesh of 3 agents)
  └─ Team B (mesh of 3 agents)
```

Use for: Large projects with semi-independent teams that need internal collaboration.

### Star-Ring Hybrid
```
Orchestrator (star hub)
  ├─ Pipeline 1 (ring of 3 agents)
  ├─ Pipeline 2 (ring of 3 agents)
  └─ Pipeline 3 (ring of 3 agents)
```

Use for: Multiple parallel pipelines that need coordination.

## Performance Tuning

### Mesh Topology
- **Max agents**: 6 (overhead grows quadratically)
- **Communication**: Enable batching for efficiency
- **Strategy**: Use "adaptive" to prevent over-communication

### Hierarchical Topology
- **Depth**: Keep to 2-3 levels max
- **Span**: 3-5 agents per coordinator
- **Strategy**: Use "specialized" for clear roles

### Star Topology
- **Hub capacity**: Monitor for bottlenecks
- **Max agents**: 10-12 before hub saturation
- **Strategy**: Use "balanced" for even distribution

### Ring Topology
- **Pipeline length**: 3-5 stages optimal
- **Fault handling**: Implement checkpoints between stages
- **Strategy**: Use "sequential" explicitly

## Common Mistakes

### ❌ Using Mesh for 10+ agents
**Problem**: Quadratic communication overhead
**Solution**: Use Hierarchical with sub-teams

### ❌ Using Star for dependent tasks
**Problem**: Tasks wait for each other, hub becomes bottleneck
**Solution**: Use Ring for sequential dependencies

### ❌ Using Ring for parallel tasks
**Problem**: Unnecessary serialization, slow execution
**Solution**: Use Star for true parallelism

### ❌ Using Hierarchical without clear roles
**Problem**: Coordinator overhead without benefits
**Solution**: Use Mesh for flat collaboration

## Examples from Real Projects

### Example 1: Zoho CRM Account Analysis
**Requirement**: Analyze 100 accounts for health risks

**Topology**: Star
**Rationale**: Each account analyzed independently
```javascript
mcp__claude-flow__swarm_init { topology: "star", maxAgents: 8 }
// Hub orchestrates, 7 workers analyze accounts in parallel
```

### Example 2: Multi-Service API Development
**Requirement**: Build authentication, user management, and billing APIs

**Topology**: Hierarchical
**Rationale**: Services independent but need coordination
```javascript
mcp__claude-flow__swarm_init { topology: "hierarchical", maxAgents: 10 }
// Coordinator → 3 service leads → 2 developers each
```

### Example 3: Code Quality Audit
**Requirement**: Security, performance, and maintainability review

**Topology**: Mesh
**Rationale**: Reviewers need to discuss overlapping concerns
```javascript
mcp__claude-flow__swarm_init { topology: "mesh", maxAgents: 4 }
// 3 specialized reviewers + 1 synthesizer, full collaboration
```

### Example 4: Release Pipeline
**Requirement**: Build → Test → Stage → Deploy

**Topology**: Ring
**Rationale**: Clear sequential stages with validation
```javascript
mcp__claude-flow__swarm_init { topology: "ring", maxAgents: 4 }
// Each stage validates before handoff to next
```
