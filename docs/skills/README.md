# SERGAS Agents - Claude Skills Documentation

**Last Updated**: October 18, 2025
**Project**: SERGAS Agents - Super Account Manager
**Total Skills**: 9 (5 core + 4 newly added)

---

## Overview

This document provides comprehensive documentation for all Claude Skills implemented in the SERGAS Agents project. These skills extend Claude's capabilities with specialized knowledge, workflows, and tool integrations for account management, CRM operations, and AI agent orchestration.

## Quick Start

### Installing Skills

Skills are automatically loaded from `.claude/skills/` when using Claude Code or Claude Desktop in this project directory.

**Location**: `/Users/mohammadabdelrahman/Projects/sergas_agents/.claude/skills/`

### Triggering Skills

Skills activate automatically based on keywords in your prompts. Use the trigger keywords listed below to activate specific skills.

**Example**:
```
"Analyze the health score for this Zoho account"
→ Triggers: zoho-crm-analysis skill

"How do I build an MCP server for Salesforce?"
→ Triggers: mcp-builder skill

"Search my memory for similar at-risk accounts"
→ Triggers: cognee-memory-search skill
```

---

## Core Skills (Existing)

### 1. **account-analysis**

**Purpose**: Foundation for account health scoring and analysis

**When to Use**:
- Calculating account health scores
- Analyzing account metrics
- Identifying account trends
- Generating account reports

**Key Features**:
- Multi-dimensional health scoring
- Trend analysis
- Risk assessment
- Performance metrics

**Integration Points**:
- Feeds data to zoho-crm-analysis
- Provides metrics for recommendation-engine
- Stores results in cognee-memory

**Trigger Keywords**: account health, health score, account analysis, account metrics

---

### 2. **agent-orchestration**

**Purpose**: Multi-agent coordination using Claude Agent SDK

**When to Use**:
- Coordinating multiple AI agents
- Implementing subagent patterns
- Managing agent communication
- Setting up MCP integrations
- Building production-ready agentic systems

**Key Features**:
- Agent lifecycle management
- Communication protocols
- MCP server integration
- Hooks and approval workflows
- Error handling and recovery

**Integration Points**:
- Orchestrates all other skills
- Manages agent coordination
- Handles MCP tool routing

**Trigger Keywords**: agent orchestration, multi-agent, agent coordination, subagent, agent communication

---

### 3. **cognee-memory-management**

**Purpose**: Persistent memory and knowledge management for AI agents

**When to Use**:
- Building agents with long-term memory
- Storing historical context
- Cross-session state persistence
- Knowledge graph creation
- Contextual awareness

**Key Features**:
- Persistent memory storage
- Knowledge graph integration
- Context retrieval
- Pattern recognition
- Session management

**Integration Points**:
- Stores data from all analysis skills
- Provides context to recommendation-engine
- Enables historical pattern analysis

**Trigger Keywords**: cognee, memory management, persistent memory, knowledge graph, historical context

---

### 4. **recommendation-engine**

**Purpose**: Actionable recommendation generation for account management

**When to Use**:
- Generating next-best-actions
- Creating follow-up strategies
- Drafting customer communications
- Prioritizing tasks
- Decision support

**Key Features**:
- AI-powered recommendations
- Priority-based ranking
- Communication templates
- Action plan generation
- Context-aware suggestions

**Integration Points**:
- Uses data from zoho-crm-analysis
- Retrieves context from cognee-memory
- Feeds suggestions to account-executive-assistant

**Trigger Keywords**: recommendations, next-best-action, suggested actions, action plan, prioritization

---

### 5. **zoho-crm-integration**

**Purpose**: Zoho CRM data access and manipulation

**When to Use**:
- Accessing Zoho CRM data
- Creating/updating CRM records
- Searching contacts and accounts
- Managing deals and activities
- OAuth authentication

**Key Features**:
- Complete Zoho CRM API coverage
- OAuth 2.0 authentication
- CRUD operations
- Search and filtering
- Relationship management

**Integration Points**:
- Primary data source for all analysis
- Used by zoho-crm-analysis for health scoring
- Integrated with cognee-memory for storage

**Trigger Keywords**: zoho crm, crm integration, zoho api, crm data, zoho oauth

---

## New Skills (Anthropic Standards)

### 6. **skill-creator** ⭐ Meta-Skill

**Purpose**: Interactive guide for creating new Claude skills

**When to Use**:
- Creating custom skills for domain-specific workflows
- Building reusable automation patterns
- Packaging specialized knowledge
- Extending Claude's capabilities
- Updating existing skills

**Key Features**:
- Six-phase creation process
- Interactive question-driven approach
- Automated validation
- Template generation
- Best practices guidance
- Quality checklists

**Process Flow**:
1. **Understand**: Gather concrete examples
2. **Plan**: Identify reusable resources
3. **Initialize**: Generate skill template
4. **Write**: Create instructions and content
5. **Create Resources**: Build scripts, references, assets
6. **Test**: Validate and iterate

**Quality Standards**:
- Progressive disclosure (metadata → SKILL.md → resources)
- Imperative voice for instructions
- Under 5,000 words per SKILL.md
- Concrete examples included
- Proper file organization

**Integration Points**:
- Meta-skill that creates other skills
- Can generate skills for any domain
- Validates skill structure and quality

**Trigger Keywords**: create skill, new skill, skill creator, build skill, custom skill, skill template

**Examples**:
```
"I want to create a skill for analyzing customer sentiment"
"How do I build a custom skill for financial modeling?"
"Create a skill for automating weekly reports"
```

---

### 7. **mcp-builder** ⭐ Development Tool

**Purpose**: Guide for building high-quality MCP servers

**When to Use**:
- Building MCP integrations for external APIs
- Creating custom tool servers
- Wrapping existing APIs for LLM consumption
- Enhancing existing MCP servers
- Developing enterprise MCP integrations

**Key Features**:
- Four-phase development process
- Agent-centric design principles
- Python (FastMCP) and TypeScript SDK support
- Comprehensive code examples
- Testing and evaluation harness
- Security best practices

**Process Flow**:
1. **Research & Planning**: Deep API understanding, tool design
2. **Implementation**: Code MCP server with best practices
3. **Review & Refinement**: Quality and security checks
4. **Evaluation**: Comprehensive testing with 10+ scenarios

**Supported Languages**:
- Python (FastMCP framework)
- TypeScript (MCP SDK)

**Quality Checklists**:
- Functionality validation
- Code quality standards
- Security requirements
- Usability testing
- Performance optimization

**Integration Points**:
- Can enhance zoho-crm-integration MCP server
- Builds tools used by agent-orchestration
- Creates integrations for any external service

**Trigger Keywords**: mcp server, build mcp, mcp integration, model context protocol, create mcp, fastmcp

**Examples**:
```
"How do I build an MCP server for Salesforce?"
"Create an MCP integration for our internal API"
"Enhance the Zoho MCP server with bulk operations"
```

---

### 8. **zoho-crm-analysis** ⭐ Analysis Engine

**Purpose**: Advanced Zoho CRM analysis for account health and risk detection

**When to Use**:
- Analyzing account health and engagement
- Detecting at-risk customers
- Identifying growth opportunities
- Calculating health scores
- Tracking lifecycle stages
- Monitoring engagement metrics

**Key Features**:
- Comprehensive health scoring (0-100 scale)
- Multi-dimensional analysis (Engagement, Financial, Relationship, Risk)
- Pattern recognition across accounts
- Risk signal detection (critical and warning)
- Opportunity identification
- Actionable insight generation

**Health Score Components**:
- **Engagement (40%)**: Communication, response time, meetings, adoption
- **Financial (30%)**: Revenue trend, payment history, renewal status
- **Relationship (20%)**: Executive engagement, stakeholder breadth, champions
- **Risk (10%)**: Support tickets, churn signals, competitive activity

**Risk Detection**:
- Critical signals (immediate action)
- Warning signals (monitor closely)
- Opportunity signals (growth potential)

**Workflow Phases**:
1. Data collection from Zoho CRM
2. Health score calculation
3. Risk pattern detection
4. Engagement pattern analysis
5. Insight generation
6. Reporting and memory storage

**Integration Points**:
- Uses zoho-crm-integration for data
- Stores results in cognee-memory
- Feeds insights to recommendation-engine
- Provides context to account-executive-assistant

**Trigger Keywords**: account health, risk detection, zoho analysis, health score, at-risk account, engagement analysis, churn risk

**Examples**:
```
"Analyze the health of account 12345"
"Identify at-risk accounts in my portfolio"
"Calculate engagement patterns for Acme Corp"
"Detect churn risk signals for enterprise accounts"
```

---

### 9. **account-executive-assistant** ⭐ Communication & Workflow

**Purpose**: AI assistant for account executives with communication templates and workflows

**When to Use**:
- Drafting customer communications
- Planning account strategies
- Prioritizing tasks and follow-ups
- Creating executive business reviews
- Generating meeting agendas
- Building customer-facing documents
- Managing renewals and escalations

**Key Features**:
- 7 communication templates (emails, meetings, documents)
- Task prioritization framework
- Meeting frameworks (kickoff, QBR, renewal)
- Daily and weekly workflow guidance
- Strategic account planning tools

**Communication Templates**:
1. **Introduction & Onboarding**: Welcome new customers
2. **Quarterly Business Review**: Strategic account reviews
3. **Value Reinforcement**: Highlight achievements and ROI
4. **At-Risk Intervention**: Re-engage struggling accounts
5. **Renewal Discussion**: Proactive renewal planning
6. **Upsell/Cross-sell**: Growth opportunities
7. **Executive Escalation**: High-priority issue resolution

**Meeting Frameworks**:
- Kickoff meetings (60 min)
- Quarterly Business Reviews (60-90 min)
- Renewal conversations
- Executive escalations

**Task Prioritization**:
- Priority matrix (Impact × Urgency)
- Daily routine guidance
- Weekly planning structure

**Integration Points**:
- Uses zoho-crm-analysis for account context
- Retrieves history from cognee-memory
- Implements recommendations from recommendation-engine
- Updates zoho-crm-integration with activities

**Trigger Keywords**: account executive, customer communication, email template, meeting agenda, renewal, qbr, executive assistant, follow-up

**Examples**:
```
"Draft a renewal email for Acme Corp"
"Create a QBR agenda for enterprise account"
"Help me prioritize my tasks this week"
"Write an at-risk account intervention email"
```

---

### 10. **cognee-memory-search** ⭐ Knowledge Retrieval

**Purpose**: Advanced memory search and pattern recognition using Cognee

**When to Use**:
- Retrieving historical account context
- Searching for patterns across accounts
- Building contextual awareness
- Synthesizing knowledge from past decisions
- Finding similar situations
- Tracking decision history
- Maintaining cross-session continuity
- Learning from outcomes

**Key Features**:
- Five core operations (Store, Retrieve, Search, Analyze, Synthesize)
- Multiple search types (exact, semantic, pattern, temporal, metadata)
- Knowledge synthesis and aggregation
- Relationship mapping
- Pattern recognition

**Search Types**:
- **Exact Match**: Find specific records by ID/key
- **Semantic Search**: Conceptually similar content
- **Pattern Search**: Recurring patterns and trends
- **Temporal Search**: Time-based filtering
- **Metadata Search**: Tag and category filtering

**Memory Schema**:
```
accounts/[id]/[category]:
  - health_scores: Historical health data
  - interactions: Communication history
  - decisions: Key decisions and rationale
  - interventions: Actions and outcomes
  - patterns: Behavioral patterns
  - opportunities: Growth potential
  - risks: Risk assessments
  - stakeholders: Relationship maps
```

**Workflows**:
1. **Historical Context Retrieval**: Get complete account history
2. **Pattern Recognition**: Identify common trends
3. **Decision History**: Review similar past decisions
4. **Knowledge Graph Building**: Map relationships

**Advanced Techniques**:
- Semantic similarity search
- Temporal pattern analysis
- Multi-dimensional queries
- Aggregation and statistics

**Integration Points**:
- Stores data from zoho-crm-analysis
- Provides context to account-executive-assistant
- Enables recommendation-engine learning
- Supports all skills with historical context

**Trigger Keywords**: cognee search, memory search, search memory, historical context, find patterns, similar accounts, knowledge retrieval, search history

**Examples**:
```
"Search my memory for accounts with similar risk patterns"
"Find historical context for this account"
"What were similar decisions we made in the past?"
"Search for successful intervention strategies"
```

---

## Skill Comparison Matrix

| Skill | Category | Complexity | Input | Output | Integration Level |
|-------|----------|------------|-------|--------|------------------|
| account-analysis | Analysis | Medium | Account data | Health metrics | Foundation |
| agent-orchestration | Infrastructure | High | Agent config | Coordination | Framework |
| cognee-memory-management | Memory | Medium | Data objects | Stored memories | Cross-cutting |
| recommendation-engine | Decision Support | Medium | Analysis data | Action plans | Consumer |
| zoho-crm-integration | Data Access | Medium | CRM queries | CRM data | Data source |
| **skill-creator** | Meta-Skill | Low | Examples | New skill | Development |
| **mcp-builder** | Development | High | API docs | MCP server | Development |
| **zoho-crm-analysis** | Analysis | High | Account ID | Health report | Specialized |
| **account-executive-assistant** | Communication | Medium | Context | Templates | Specialized |
| **cognee-memory-search** | Retrieval | Medium | Search query | Memories | Specialized |

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User / Claude                         │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐    ┌──────────▼─────────┐
│ skill-creator  │    │  mcp-builder       │
│ (Meta)         │    │  (Development)     │
└────────────────┘    └────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼─────────────┐   ┌──────▼──────────────────┐
│ agent-orchestration │   │ cognee-memory-search    │
│ (Coordination)      │   │ (Knowledge Retrieval)   │
└──────┬──────────────┘   └─────────────────────────┘
       │                          ▲
       │                          │
┌──────▼────────────────────┐    │
│ zoho-crm-integration      │    │
│ (Data Source)             │────┘
└──────┬────────────────────┘
       │
       │  ┌────────────────────────────┐
       ├──► zoho-crm-analysis          │
       │  │ (Health & Risk)            │
       │  └────────┬───────────────────┘
       │           │
       │  ┌────────▼───────────────────┐
       ├──► recommendation-engine       │
       │  │ (Next Best Actions)        │
       │  └────────┬───────────────────┘
       │           │
       │  ┌────────▼───────────────────┐
       └──► account-executive-assistant│
          │ (Communication)            │
          └────────────────────────────┘
                   │
          ┌────────▼────────┐
          │ cognee-memory   │
          │ (Storage)       │
          └─────────────────┘
```

---

## Use Case Examples

### Use Case 1: Analyze At-Risk Account

**Workflow**:
1. **zoho-crm-integration** → Fetch account data
2. **zoho-crm-analysis** → Calculate health score, detect risks
3. **cognee-memory-search** → Find similar historical cases
4. **recommendation-engine** → Generate intervention plan
5. **account-executive-assistant** → Draft intervention email
6. **cognee-memory-management** → Store analysis results

**Prompt**:
```
"Account 12345 has decreased engagement. Analyze the risk and create an intervention plan."
```

---

### Use Case 2: Quarterly Portfolio Review

**Workflow**:
1. **zoho-crm-integration** → Get all account data
2. **zoho-crm-analysis** → Score all accounts
3. **cognee-memory-search** → Identify patterns across portfolio
4. **recommendation-engine** → Prioritize interventions
5. **account-executive-assistant** → Generate executive report

**Prompt**:
```
"Analyze my entire account portfolio and generate a Q4 executive review."
```

---

### Use Case 3: Renewal Planning

**Workflow**:
1. **cognee-memory-search** → Get account history
2. **zoho-crm-analysis** → Current health assessment
3. **recommendation-engine** → Renewal strategy
4. **account-executive-assistant** → Create renewal proposal and QBR deck

**Prompt**:
```
"Plan renewal strategy for Acme Corp (renews in 90 days)."
```

---

### Use Case 4: Build New Integration

**Workflow**:
1. **mcp-builder** → Guide MCP server creation
2. **skill-creator** → Create skill wrapper for MCP tools
3. **agent-orchestration** → Integrate into agent workflow

**Prompt**:
```
"Build an MCP integration for Salesforce and create a skill to use it."
```

---

## Best Practices

### Skill Combination

✅ **Do**:
- Combine skills for comprehensive workflows
- Use cognee-memory-search before analysis for context
- Store analysis results in cognee-memory for learning
- Chain skills logically (data → analysis → recommendations → actions)

❌ **Don't**:
- Use skills in isolation when integration provides value
- Skip memory storage (prevents learning)
- Ignore historical context
- Break logical workflow sequences

### Memory Management

✅ **Do**:
- Store analysis results for future reference
- Use consistent naming conventions
- Add rich metadata and tags
- Set appropriate TTLs
- Link related memories

❌ **Don't**:
- Store duplicate data
- Use ambiguous memory keys
- Skip timestamps
- Omit metadata
- Store sensitive data unencrypted

### Communication

✅ **Do**:
- Personalize all templates
- Lead with value and customer goals
- Use account-executive-assistant for consistency
- Include specific metrics and examples

❌ **Don't**:
- Send generic messages
- Focus only on features
- Skip personalization
- Overwhelm with information

---

## Performance Metrics

**Skill Quality Indicators**:
- **Accuracy**: Health score prediction accuracy >85%
- **Coverage**: Test coverage >80% for all skills
- **Response Time**: Analysis completion <10 seconds
- **Memory Efficiency**: TTL compliance >95%
- **Integration Success**: Cross-skill workflows complete >90%

**Business Impact Metrics**:
- Churn prevention rate improvement
- Upsell identification accuracy
- Time saved on account management tasks
- Account health improvement tracking
- ROI of interventions

---

## Troubleshooting

### Skills Not Triggering

**Problem**: Skill doesn't activate with prompt

**Solutions**:
1. Check skill is in `.claude/skills/` directory
2. Use clear trigger keywords from documentation
3. Verify SKILL.md has valid YAML frontmatter
4. Restart Claude Desktop/Code
5. Check description contains relevant keywords

---

### Integration Issues

**Problem**: Skills not working together properly

**Solutions**:
1. Verify all required skills are installed
2. Check MCP servers are configured (zoho-crm-integration)
3. Ensure cognee-memory is initialized
4. Review agent-orchestration configuration
5. Check for conflicting skill versions

---

### Memory Search Issues

**Problem**: cognee-memory-search returns no results

**Solutions**:
1. Verify data was stored with correct namespace/key
2. Check memory hasn't expired (TTL)
3. Use broader search terms
4. Try semantic search instead of exact match
5. Verify cognee service is running

---

## Development Roadmap

### Completed (Week 1-2)
- ✅ Core skills implementation
- ✅ Zoho CRM integration
- ✅ Basic agent orchestration
- ✅ Anthropic skill standards adoption

### In Progress (Week 3)
- 🔄 Enhanced MCP server features
- 🔄 Advanced pattern recognition
- 🔄 Automated testing framework

### Planned (Week 4+)
- ⏳ PDF and XLSX skills for reporting
- ⏳ Web app testing skill
- ⏳ Interactive dashboard skill
- ⏳ Advanced predictive analytics

---

## Resources

### Official Documentation
- **Claude Skills**: https://docs.anthropic.com/claude/docs/skills
- **Anthropic Skills Repo**: https://github.com/anthropics/skills
- **MCP Documentation**: https://modelcontextprotocol.io
- **Cognee Docs**: https://cognee.ai/docs

### Project Resources
- **Skills Directory**: `.claude/skills/`
- **Research Report**: `docs/research/anthropic_claude_skills_research_report.md`
- **Implementation Plan**: `docs/implementation_plan.md`
- **SPARC Plan**: `docs/SPARC_PLAN_SUMMARY.md`

### Community
- **Issues**: GitHub Issues for skill problems
- **Discussions**: Slack channel for skill development
- **Examples**: `examples/` directory for skill usage

---

## Contributing

### Creating New Skills

1. Use **skill-creator** skill for guidance
2. Follow Anthropic skill standards
3. Include comprehensive documentation
4. Add tests and examples
5. Submit for review

### Enhancing Existing Skills

1. Review current skill documentation
2. Identify enhancement opportunities
3. Maintain backward compatibility
4. Update documentation
5. Add tests for new features

---

## Conclusion

The SERGAS Agents skill ecosystem provides comprehensive capabilities for account management, CRM operations, and AI agent orchestration. With 9 skills covering analysis, communication, memory, development, and coordination, the system enables sophisticated workflows for customer success and account executive operations.

**Key Strengths**:
- Modular, composable architecture
- Anthropic best practices compliance
- Comprehensive integration
- Production-ready quality
- Extensible framework

**Next Steps**:
1. Activate skills in your workflows
2. Combine skills for complex scenarios
3. Create custom skills using skill-creator
4. Build MCP integrations with mcp-builder
5. Contribute improvements and new skills

---

**Last Updated**: October 18, 2025
**Version**: 1.0.0
**Maintained By**: SERGAS Agents Team
