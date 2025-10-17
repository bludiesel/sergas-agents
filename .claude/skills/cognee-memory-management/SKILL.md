---
name: cognee-memory-management
description: Persistent memory and knowledge management using Cognee for AI agents. Use this skill when building agents that need long-term memory, historical context retrieval, knowledge graph storage, or cross-session state persistence. Essential for account managers, customer service agents, and any application requiring contextual awareness beyond a single conversation.
---

# Cognee Memory Management

## Overview

Cognee is a purpose-built memory layer that combines vector embeddings with knowledge graphs to provide AI agents with persistent, structured memory. This skill covers setup, data ingestion, retrieval, and best practices for integrating Cognee into multi-agent systems.

## When to Use This Skill

Use this skill when:
- Building agents that need to remember past interactions
- Storing and retrieving historical account context
- Implementing knowledge graphs for relationship tracking
- Aggregating insights across multiple data sources
- Providing agents with long-term situational awareness
- Creating audit trails of agent decisions and reasoning

## Core Capabilities

### 1. Graph-Enhanced Memory Storage
- Combines vector embeddings with knowledge graphs
- Stores data as graph-enriched chunks with entity relationships (subject-relation-object)
- Supports ontologies and reasoning layers
- Better recall than vanilla RAG (~90% vs ~60% success rate)

### 2. Workspace Isolation
- Multiple isolated workspaces per deployment
- Separate contexts for different accounts, teams, or use cases
- Fine-grained access control

### 3. Semantic Retrieval
- Natural language queries
- Entity relationship traversal
- Temporal reasoning (track changes over time)

## Installation and Setup

### Installation

```bash
# Install Cognee
pip install cognee

# Or use CLI
pip install cognify
```

### Configuration

```python
import cognee
import os

# Configure Cognee
cognee.config.set({
    "llm_provider": "anthropic",
    "llm_model": "claude-3-5-sonnet-20241022",
    "embedding_provider": "openai",
    "vector_db_provider": "lancedb",
    "graph_db_provider": "neo4j"  # Optional
})

# Set API keys
os.environ["ANTHROPIC_API_KEY"] = "your-api-key"
os.environ["OPENAI_API_KEY"] = "your-embedding-key"
```

### Initialize Workspace

```python
# Create or connect to workspace
await cognee.initialize_workspace("sergas_accounts")

# Set current workspace
await cognee.use_workspace("sergas_accounts")
```

## Core Workflows

### Data Ingestion

#### Ingesting Account Data

```python
import cognee
from pathlib import Path

# Ingest text content
account_history = """
Account: Acme Corporation
Owner: Jane Smith
Last Contact: 2024-10-15
Status: Active
Notes: Customer requested demo of new features.
Previous meeting discussed Q4 renewal.
"""

await cognee.add(account_history, dataset_name="account_histories")

# Ingest files
await cognee.add(Path("account_notes.txt"), dataset_name="account_notes")

# Ingest structured data
account_data = {
    "account_id": "12345",
    "account_name": "Acme Corp",
    "owner": "Jane Smith",
    "status": "Active",
    "last_contact": "2024-10-15",
    "notes": ["Demo requested", "Q4 renewal discussion"]
}

await cognee.add(account_data, dataset_name="structured_accounts")
```

#### Bulk Ingestion

```python
# Ingest multiple accounts
accounts = [
    {"account_id": "123", "name": "Acme", "owner": "Jane"},
    {"account_id": "456", "name": "TechCo", "owner": "John"},
    {"account_id": "789", "name": "Global Inc", "owner": "Alice"}
]

for account in accounts:
    await cognee.add(account, dataset_name="bulk_accounts")
```

### Cognification (Processing)

Transform raw data into searchable knowledge:

```python
# Process all added data
await cognee.cognify()

# Process specific dataset
await cognee.cognify(dataset_name="account_histories")

# Process with custom parameters
await cognee.cognify(
    dataset_name="accounts",
    chunk_size=1024,
    chunk_overlap=100
)
```

### Memory Retrieval

#### Simple Search

```python
# Search for relevant context
results = await cognee.search(
    "What was discussed in the last meeting with Acme Corp?"
)

for result in results:
    print(f"Context: {result.content}")
    print(f"Relevance: {result.score}")
```

#### Filtered Search

```python
# Search within specific account
results = await cognee.search(
    "What are the customer's main concerns?",
    filters={"account_id": "12345"}
)

# Temporal search
results = await cognee.search(
    "What changed in the last 30 days?",
    filters={"modified_after": "2024-09-15"}
)
```

#### Graph Queries

```python
# Query relationships
query = """
MATCH (account:Account)-[:OWNED_BY]->(owner:Owner)
WHERE account.name = 'Acme Corp'
RETURN account, owner
"""

results = await cognee.graph_query(query)
```

### Memory Updates

#### Incremental Updates

```python
# Add new information to existing account
new_notes = """
Account: Acme Corporation
Date: 2024-10-18
Update: Demo completed successfully.
Customer expressed interest in enterprise features.
"""

await cognee.add(new_notes, dataset_name="account_histories")
await cognee.cognify()
```

#### Deduplication

```python
# Configure deduplication threshold
cognee.config.set({
    "deduplication_threshold": 0.95  # 95% similarity threshold
})

await cognee.cognify(deduplicate=True)
```

## MCP Server Integration

Create a custom MCP server for Cognee integration with agents:

### MCP Server Implementation

```python
# scripts/cognee_mcp_server.py

from mcp import McpServer
import cognee

mcp = McpServer("cognee-memory")

@mcp.tool()
async def add_account_context(account_id: str, context: str):
    """Add context to account memory"""
    data = {
        "account_id": account_id,
        "context": context,
        "timestamp": datetime.now().isoformat()
    }
    await cognee.add(data, dataset_name="account_contexts")
    await cognee.cognify()
    return {"status": "success", "account_id": account_id}

@mcp.tool()
async def search_account_history(account_id: str, query: str):
    """Search historical context for specific account"""
    results = await cognee.search(
        query,
        filters={"account_id": account_id}
    )
    return [{"content": r.content, "score": r.score} for r in results]

@mcp.tool()
async def get_account_timeline(account_id: str):
    """Get chronological timeline of account events"""
    query = f"""
    MATCH (event:Event)-[:BELONGS_TO]->(account:Account)
    WHERE account.id = '{account_id}'
    RETURN event ORDER BY event.timestamp DESC
    """
    return await cognee.graph_query(query)

@mcp.tool()
async def get_related_entities(account_id: str, entity_type: str):
    """Get entities related to account (contacts, deals, etc.)"""
    query = f"""
    MATCH (account:Account)-[*1..2]-(entity:{entity_type})
    WHERE account.id = '{account_id}'
    RETURN DISTINCT entity
    """
    return await cognee.graph_query(query)

if __name__ == "__main__":
    mcp.run()
```

### Using MCP Tools in Agents

```python
from claude_agent_sdk import ClaudeSDKClient

# Configure agent with Cognee MCP server
client = ClaudeSDKClient(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    mcp_servers={
        "cognee": {
            "command": "python",
            "args": ["scripts/cognee_mcp_server.py"],
            "transport": "stdio"
        }
    },
    allowed_tools=[
        "add_account_context",
        "search_account_history",
        "get_account_timeline",
        "get_related_entities"
    ]
)

# Agent can now use memory tools
response = await client.query(
    "What were the key points from our last meeting with Acme Corp?",
    session_id="account_review_session"
)
```

## Agent Integration Patterns

### Memory Analyst Subagent

```python
# Define Memory Analyst subagent with Cognee access
memory_analyst_config = {
    "name": "Memory Analyst",
    "system_prompt": """
    You are a Memory Analyst agent. Your role is to:
    1. Query historical account context using Cognee
    2. Identify relevant past interactions and commitments
    3. Highlight patterns and trends over time
    4. Surface important context for current decisions

    Always cite sources with timestamps when referencing historical data.
    """,
    "allowed_tools": [
        "Read",
        "search_account_history",
        "get_account_timeline",
        "get_related_entities"
    ],
    "permission_mode": "default"
}
```

### Orchestrator with Memory Persistence

```python
from claude_agent_sdk import ClaudeSDKClient

async def run_account_review_with_memory(account_id: str):
    """Run account review with persistent memory"""

    client = ClaudeSDKClient(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        mcp_servers={"cognee": {...}}
    )

    # Retrieve historical context
    history = await cognee.search(
        f"All interactions and notes for account {account_id}",
        filters={"account_id": account_id}
    )

    # Run analysis with context
    prompt = f"""
    Account ID: {account_id}

    Historical Context:
    {history}

    Analyze this account's current status and recommend next actions.
    """

    response = await client.query(prompt)

    # Store analysis results back to memory
    await cognee.add({
        "account_id": account_id,
        "analysis_date": datetime.now().isoformat(),
        "analysis_results": response.content,
        "recommendations": response.recommendations
    })
    await cognee.cognify()

    return response
```

## Performance Optimization

### Indexing Strategy

```python
# Create indexes for frequently queried fields
await cognee.create_index(
    field="account_id",
    index_type="btree"
)

await cognee.create_index(
    field="timestamp",
    index_type="btree"
)
```

### Caching

```python
# Cache frequently accessed accounts
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_account_context_cached(account_id: str):
    return await cognee.search(
        f"Account {account_id} context",
        filters={"account_id": account_id}
    )
```

### Batch Processing

```python
# Process multiple accounts in parallel
import asyncio

async def process_accounts_batch(account_ids: list):
    tasks = [
        cognee.search(f"account {aid}", filters={"account_id": aid})
        for aid in account_ids
    ]
    return await asyncio.gather(*tasks)
```

## Best Practices

1. **Workspace Organization**
   - Use separate workspaces for different contexts (dev/staging/prod)
   - Isolate customer data by tenant or account segment

2. **Data Quality**
   - Validate and normalize data before ingestion
   - Include timestamps and source metadata
   - Implement deduplication strategies

3. **Incremental Updates**
   - Schedule periodic re-ingestion for changing data
   - Use append-only patterns for audit trails
   - Maintain version history for critical data

4. **Query Optimization**
   - Use filters to narrow search scope
   - Cache frequently accessed contexts
   - Implement pagination for large result sets

5. **Security**
   - Encrypt data at rest and in transit
   - Implement access controls at workspace level
   - Audit all memory access and modifications

## Resources

See `references/api_reference.md` for:
- Complete Cognee API documentation
- Graph query examples
- Performance tuning guidelines
- Advanced ontology configuration

See project root `super_account_manager_research.md` for:
- Cognee architecture details
- Integration with Zoho CRM
- Multi-agent memory patterns
