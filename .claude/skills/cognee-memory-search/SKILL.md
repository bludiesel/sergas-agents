---
name: cognee-memory-search
description: Advanced memory search and pattern recognition using Cognee for AI agents. Use when retrieving historical account context, searching for patterns across customer interactions, synthesizing knowledge from past decisions, or building contextual awareness for account management workflows.
license: MIT
---

# Cognee Memory Search - Intelligent Context Retrieval & Pattern Recognition

Comprehensive memory search and knowledge management skill using Cognee for building context-aware AI agents with long-term memory and pattern recognition capabilities.

## When to Use

- Retrieving historical account context and interactions
- Searching for patterns across multiple customer accounts
- Building contextual awareness for account management decisions
- Synthesizing knowledge from past interventions and outcomes
- Finding similar situations or precedents
- Tracking decision history and rationale
- Maintaining continuity across sessions and agents
- Learning from past successes and failures

## Core Capabilities

### Memory Operations

**Store**: Save structured information with metadata
**Retrieve**: Get specific memories by key or pattern
**Search**: Find relevant memories using semantic search
**Analyze**: Identify patterns and relationships
**Synthesize**: Combine multiple memories into insights

### Search Types

**Exact Match**: Find specific records by ID or key
**Semantic Search**: Find conceptually similar content
**Pattern Search**: Identify recurring patterns
**Temporal Search**: Filter by time ranges
**Metadata Search**: Filter by tags, categories, types

### Knowledge Synthesis

**Aggregation**: Combine related memories
**Pattern Recognition**: Identify trends and commonalities
**Relationship Mapping**: Connect related information
**Insight Generation**: Derive conclusions from history

## Memory Schema Design

### Account Memory Structure

```yaml
memory_namespace: accounts
memory_key: account/[account_id]/[category]

Categories:
- health_scores: Historical health score data
- interactions: Communication history
- decisions: Key decisions and rationale
- interventions: Action taken and outcomes
- patterns: Identified behavioral patterns
- opportunities: Growth and expansion opportunities
- risks: Risk assessments and mitigations
- stakeholders: Relationship map and changes
- success_metrics: KPIs and achievements
- learnings: Lessons learned and best practices
```

### Memory Record Format

```json
{
  "id": "unique_memory_id",
  "namespace": "accounts",
  "key": "account/12345/health_scores",
  "timestamp": "2025-10-18T10:30:00Z",
  "data": {
    "account_id": "12345",
    "account_name": "Acme Corp",
    "category": "health_scores",
    "content": {
      "score": 75,
      "trend": "declining",
      "dimensions": {
        "engagement": 68,
        "financial": 85,
        "relationship": 72,
        "risk": 15
      }
    }
  },
  "metadata": {
    "source": "zoho-crm-analysis",
    "analyst": "agent_001",
    "tags": ["health_score", "at_risk", "q4_2025"],
    "related_memories": ["account/12345/interventions"]
  },
  "ttl": 31536000
}
```

## Search Workflows

### Workflow 1: Historical Context Retrieval

**Use Case**: Before engaging with account, retrieve all relevant history.

**Process**:
```bash
# 1. Retrieve account overview
cognee memory retrieve "account/[id]/overview"

# 2. Get recent interactions
cognee memory search "account:[id] AND category:interactions AND timestamp:last_30_days"

# 3. Get health score history
cognee memory retrieve "account/[id]/health_scores" --limit 10 --sort "timestamp:desc"

# 4. Get open action items
cognee memory search "account:[id] AND category:decisions AND status:pending"

# 5. Get similar account patterns
cognee memory search "similar_accounts pattern:[pattern_type] industry:[industry]"
```

**Output**:
```markdown
# Account Context: [Company Name]

## Recent History
- Last interaction: [Date] - [Type] - [Summary]
- Health score: [Current] (Trend: [Trend])
- Open action items: [Count]

## Key Patterns
- [Pattern 1]
- [Pattern 2]

## Similar Accounts
- [Account 1]: [Similarity description]
- [Account 2]: [Similarity description]
```

### Workflow 2: Pattern Recognition

**Use Case**: Identify common patterns across at-risk accounts.

**Process**:
```bash
# 1. Search for all at-risk accounts
cognee memory search "category:health_scores AND risk_level:high"

# 2. Analyze common characteristics
cognee memory analyze --pattern "churn_indicators" --accounts "[id_list]"

# 3. Find successful interventions
cognee memory search "category:interventions AND outcome:successful AND risk_level:high"

# 4. Synthesize learnings
cognee memory synthesize --inputs "[memory_ids]" --output "intervention_playbook"
```

**Output**:
```markdown
# At-Risk Account Patterns

## Common Risk Indicators (Found in 80%+ of cases)
1. [Indicator 1]: Frequency [X]
2. [Indicator 2]: Frequency [Y]
3. [Indicator 3]: Frequency [Z]

## Successful Intervention Strategies
1. **[Strategy 1]**: Success rate [%], Avg time to recovery [days]
2. **[Strategy 2]**: Success rate [%], Avg time to recovery [days]

## Recommended Playbook
[Step-by-step intervention process based on patterns]
```

### Workflow 3: Decision History

**Use Case**: Review past decisions and outcomes for similar situations.

**Process**:
```bash
# 1. Search for similar decisions
cognee memory search "category:decisions AND situation:[description]"

# 2. Get outcomes of similar decisions
cognee memory retrieve "decision/[id]/outcome"

# 3. Analyze success factors
cognee memory analyze --pattern "decision_outcomes" --filter "successful:true"

# 4. Generate recommendation
cognee memory synthesize --context "[current_situation]" --precedents "[decision_ids]"
```

**Output**:
```markdown
# Similar Decisions & Outcomes

## Historical Context
Found [N] similar decisions in memory.

## Decision 1: [Description]
- **Situation**: [Context]
- **Decision**: [What was decided]
- **Outcome**: [Result]
- **Lessons**: [What was learned]

## Decision 2: [Description]
[...]

## Recommendation for Current Situation
Based on [N] precedents, recommend:
[Recommendation with rationale]
```

### Workflow 4: Knowledge Graph Building

**Use Case**: Map relationships between accounts, stakeholders, and interventions.

**Process**:
```bash
# 1. Build account relationship graph
cognee memory graph --root "account/[id]" --depth 2

# 2. Identify connected entities
cognee memory search "related_to:account/[id]"

# 3. Map stakeholder connections
cognee memory search "category:stakeholders AND account:[id]"

# 4. Trace influence paths
cognee memory analyze --pattern "influence_network" --account "[id]"
```

**Output**:
```markdown
# Account Relationship Map: [Company Name]

## Direct Connections
- Stakeholder: [Name] → Role: [Role] → Influence: [Level]
- Related Account: [Company] → Relationship: [Type]
- Partner: [Partner Name] → Type: [Partnership Type]

## Influence Network
[Visual or textual representation of influence paths]

## Key Insights
- [Insight 1 about relationships]
- [Insight 2 about influence]
```

## Advanced Search Techniques

### Semantic Search

**Purpose**: Find conceptually similar content even with different wording.

**Examples**:
```bash
# Find similar customer pain points
cognee memory search --semantic "customer struggling with adoption" --namespace "accounts"

# Find related success stories
cognee memory search --semantic "increased engagement after training" --limit 5

# Find similar risk scenarios
cognee memory search --semantic "threat of churn due to competitor" --category "risks"
```

### Temporal Patterns

**Purpose**: Analyze trends over time.

**Examples**:
```bash
# Get health score progression
cognee memory search "account:[id] category:health_scores" --sort "timestamp:asc"

# Find seasonal patterns
cognee memory analyze --pattern "seasonal_trends" --timeframe "last_2_years"

# Compare quarter-over-quarter
cognee memory compare --metric "engagement_score" --periods "Q3_2025,Q4_2025"
```

### Multi-dimensional Search

**Purpose**: Combine multiple search criteria.

**Examples**:
```bash
# Find high-value at-risk accounts in specific industry
cognee memory search "category:health_scores AND risk_level:high AND industry:technology AND arr:>100000"

# Find successful upsells after QBRs
cognee memory search "category:opportunities AND outcome:closed_won AND trigger:qbr"

# Find common objections in enterprise deals
cognee memory search "category:interactions AND company_size:enterprise AND type:objection"
```

## Memory Storage Best Practices

### Data Structure

✅ **Do**:
- Use consistent naming conventions for keys
- Include rich metadata (tags, categories, timestamps)
- Link related memories with references
- Store both structured data and contextual information
- Version important changes

❌ **Don't**:
- Store large binary data directly
- Use ambiguous or changing key names
- Omit timestamps or source information
- Mix unrelated data in single memory
- Store sensitive data without encryption

### Memory Organization

**Namespace Strategy**:
```
accounts/[id]/[category]/[subcategory]
agents/[agent_id]/[activity]
patterns/[type]/[identifier]
decisions/[context]/[timestamp]
learnings/[domain]/[concept]
```

**Example Keys**:
```
accounts/12345/health_scores/2025-Q4
accounts/12345/interactions/email/2025-10-18
accounts/12345/stakeholders/executive_sponsor
patterns/churn/communication_gap
decisions/renewal_strategy/2025-10-15
learnings/interventions/best_practices
```

### Metadata Standards

**Required Fields**:
- `timestamp`: When memory was created
- `source`: Where data came from
- `category`: Type of information
- `tags`: Searchable keywords

**Optional Fields**:
- `confidence`: Reliability score (0-1)
- `version`: For tracking changes
- `related_to`: Links to other memories
- `expires_at`: For time-sensitive data
- `priority`: Importance level

### TTL Strategy

**Time-to-Live Guidelines**:
```python
# Permanent (no TTL)
- Core account information
- Major decisions and rationale
- Success case studies
- Strategic patterns

# 1 year TTL
- Health scores and metrics
- Interaction logs
- Stakeholder information
- Opportunity tracking

# 3 months TTL
- Temporary notes
- Draft analyses
- Work-in-progress
- Ephemeral context

# 1 week TTL
- Session state
- Temporary cache
- Short-term reminders
```

## Integration with Other Skills

### With zoho-crm-analysis

**Store analysis results**:
```bash
# After running health score analysis
cognee memory store "account/[id]/health_scores/latest" --data "[analysis_result]"

# After risk detection
cognee memory store "account/[id]/risks/[timestamp]" --data "[risk_assessment]"
```

**Retrieve for comparison**:
```bash
# Get historical health scores for trend analysis
cognee memory search "account:[id] category:health_scores" --limit 12 --sort "timestamp:desc"

# Compare current risk with historical risks
cognee memory retrieve "account/[id]/risks" --timeframe "last_6_months"
```

### With account-executive-assistant

**Store communication outcomes**:
```bash
# After customer meeting
cognee memory store "account/[id]/interactions/meeting/[date]" --data "[meeting_summary]"

# After sending email
cognee memory store "account/[id]/interactions/email/[date]" --data "[email_outcome]"
```

**Retrieve for context**:
```bash
# Before customer call
cognee memory search "account:[id] category:interactions" --limit 5 --sort "timestamp:desc"

# Before renewal conversation
cognee memory search "account:[id] category:decisions AND type:renewal"
```

### With recommendation-engine

**Store recommendations and outcomes**:
```bash
# Store generated recommendations
cognee memory store "account/[id]/recommendations/[timestamp]" --data "[recommendations]"

# Store recommendation outcomes
cognee memory store "account/[id]/recommendations/[id]/outcome" --data "[result]"
```

**Learn from historical recommendations**:
```bash
# Find most effective recommendations
cognee memory search "category:recommendations AND outcome:successful" --analyze "effectiveness"

# Find recommendations that didn't work
cognee memory search "category:recommendations AND outcome:unsuccessful" --analyze "failure_patterns"
```

## Use Cases

### Use Case 1: Onboarding New Account Executive

**Scenario**: New AE taking over existing accounts.

**Process**:
1. Retrieve complete account history
2. Get relationship map and stakeholder info
3. Review past decisions and outcomes
4. Identify patterns and best practices
5. Generate briefing document

**Commands**:
```bash
# Get comprehensive account context
cognee memory retrieve "account/[id]/overview"
cognee memory search "account:[id]" --limit 50 --sort "timestamp:desc"

# Get stakeholder map
cognee memory search "account:[id] category:stakeholders"

# Get decision history
cognee memory search "account:[id] category:decisions"

# Synthesize briefing
cognee memory synthesize --account "[id]" --output "ae_briefing"
```

### Use Case 2: Quarterly Portfolio Review

**Scenario**: Analyzing entire account portfolio for trends.

**Process**:
1. Get health scores for all accounts
2. Identify at-risk accounts
3. Find common patterns
4. Prioritize interventions
5. Generate executive report

**Commands**:
```bash
# Get all current health scores
cognee memory search "category:health_scores AND timestamp:last_30_days"

# Find at-risk accounts
cognee memory search "category:health_scores AND risk_level:high"

# Analyze patterns
cognee memory analyze --pattern "portfolio_trends" --timeframe "Q4_2025"

# Generate report
cognee memory synthesize --context "portfolio_review_Q4" --output "executive_report"
```

### Use Case 3: Intervention Learning

**Scenario**: Building playbook from successful interventions.

**Process**:
1. Find all intervention records
2. Filter for successful outcomes
3. Identify common characteristics
4. Extract best practices
5. Create playbook

**Commands**:
```bash
# Get successful interventions
cognee memory search "category:interventions AND outcome:successful"

# Analyze patterns
cognee memory analyze --pattern "intervention_success_factors"

# Extract best practices
cognee memory synthesize --inputs "[intervention_ids]" --output "playbook"

# Store playbook
cognee memory store "learnings/interventions/playbook" --data "[playbook]"
```

### Use Case 4: Predictive Analysis

**Scenario**: Predicting account risks before they materialize.

**Process**:
1. Retrieve historical churn patterns
2. Get current account signals
3. Compare with historical patterns
4. Calculate risk probability
5. Generate early warnings

**Commands**:
```bash
# Get historical churn patterns
cognee memory search "category:patterns AND type:churn"

# Get current account signals
cognee memory search "account:[id] category:health_scores,interactions" --limit 30

# Compare and predict
cognee memory analyze --pattern "churn_prediction" --account "[id]"

# Store prediction
cognee memory store "account/[id]/predictions/churn_risk" --data "[prediction]"
```

## Memory Query Language

### Basic Syntax

```bash
# Simple search
cognee memory search "keyword"

# Category filter
cognee memory search "category:health_scores"

# Multiple filters
cognee memory search "category:interactions AND type:email AND status:sent"

# Date range
cognee memory search "timestamp:[2025-10-01 TO 2025-10-31]"

# Numeric comparison
cognee memory search "health_score:>70 AND arr:>=100000"
```

### Advanced Queries

```bash
# Nested conditions
cognee memory search "(category:risks OR category:issues) AND severity:high"

# Wildcard search
cognee memory search "account/12345/interactions/*"

# Regex patterns
cognee memory search "key:regex:account/\d+/health_scores/\d{4}-Q\d"

# Proximity search
cognee memory search "churn~5 risk" # Words within 5 positions

# Fuzzy search
cognee memory search "category:healt~" # Allows typos
```

### Aggregation Queries

```bash
# Count by category
cognee memory aggregate "count by category"

# Average health score
cognee memory aggregate "avg(health_score) by industry"

# Trend analysis
cognee memory aggregate "health_score over time by account"

# Group statistics
cognee memory aggregate "count by risk_level, avg(arr)"
```

## Performance Optimization

### Indexing Strategy

**Create Indexes for**:
- Frequently searched fields (account_id, category, timestamp)
- High-cardinality fields (health_score, arr, industry)
- Composite indexes for common query patterns

**Example**:
```python
# Create composite index for common query
cognee.create_index("accounts_health", fields=["account_id", "category", "timestamp"])

# Create text index for semantic search
cognee.create_index("interactions_text", fields=["content"], type="text")
```

### Caching Strategy

**Cache**:
- Frequently accessed account summaries
- Common query results
- Pattern analysis results
- Synthesized insights

**Example**:
```python
# Cache account summary with 1-hour TTL
cache_key = f"summary/account/{account_id}"
cognee.cache_set(cache_key, summary_data, ttl=3600)

# Check cache before expensive query
cached = cognee.cache_get(cache_key)
if not cached:
    result = cognee.memory.search(query)
    cognee.cache_set(cache_key, result, ttl=3600)
```

### Query Optimization

**Best Practices**:
- Use specific namespaces to limit search scope
- Apply filters before semantic search
- Use pagination for large result sets
- Limit returned fields when possible
- Batch related queries

**Example**:
```bash
# Optimized query
cognee memory search "category:health_scores" \
  --namespace "accounts" \
  --fields "account_id,score,timestamp" \
  --limit 100 \
  --page 1

# Instead of
cognee memory search "health" # Too broad, slow
```

## Troubleshooting

**No results found**:
→ Check namespace and category filters
→ Verify key naming conventions
→ Try semantic search instead of exact match
→ Check if memories expired (TTL)

**Too many results**:
→ Add more specific filters
→ Use date range constraints
→ Filter by metadata tags
→ Increase specificity of search terms

**Slow queries**:
→ Add indexes for frequently searched fields
→ Use pagination for large result sets
→ Narrow search scope with namespaces
→ Cache frequently accessed results

**Stale data**:
→ Check TTL settings
→ Verify update mechanisms
→ Implement data refresh workflows
→ Set appropriate expiration policies

## Best Practices Summary

### Memory Creation
✅ Use structured data with consistent schema
✅ Include rich metadata and tags
✅ Link related memories
✅ Set appropriate TTLs
✅ Version important changes

### Memory Retrieval
✅ Use specific namespaces and categories
✅ Apply filters before semantic search
✅ Cache frequently accessed data
✅ Paginate large result sets
✅ Index commonly queried fields

### Knowledge Synthesis
✅ Combine multiple memory sources
✅ Validate insights with current data
✅ Document synthesis rationale
✅ Store synthesized insights for reuse
✅ Iterate and improve over time

### Pattern Recognition
✅ Use sufficient historical data
✅ Validate patterns across accounts
✅ Account for context and nuance
✅ Update patterns with new learnings
✅ Document pattern effectiveness

## Related Skills

- **zoho-crm-integration**: Data source for memory storage
- **zoho-crm-analysis**: Generates insights to store in memory
- **account-analysis**: Uses memory for historical context
- **recommendation-engine**: Learns from stored recommendations
- **account-executive-assistant**: Retrieves context for communications

## Resources

- Cognee documentation and API reference
- Memory architecture patterns
- Knowledge graph design principles
- Semantic search best practices
- Pattern recognition methodologies
