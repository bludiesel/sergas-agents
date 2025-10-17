---
name: agent-orchestration
description: Multi-agent orchestration using Claude Agent SDK for complex workflows. Use this skill when coordinating multiple AI agents, implementing subagent patterns, managing agent communication and handoffs, configuring MCP integrations, setting up hooks and approval workflows, and building production-ready agentic systems. Essential for Claude Agent SDK development and multi-agent architecture.
---

# Agent Orchestration

## Overview

This skill provides comprehensive guidance for orchestrating multi-agent systems using the Claude Agent SDK (Python). It covers subagent design patterns, communication protocols, permission management, MCP integration, and production deployment patterns for complex agentic workflows.

## When to Use This Skill

Use this skill when:
- Building multi-agent systems with Claude Agent SDK
- Implementing orchestrator-worker patterns
- Coordinating specialized subagents for complex tasks
- Setting up MCP (Model Context Protocol) servers
- Implementing approval workflows and human-in-the-loop
- Managing agent permissions and security
- Deploying production-ready agentic systems

## Claude Agent SDK Fundamentals

### Installation

```bash
# Install Claude Agent SDK
pip install claude-agent-sdk

# Verify installation
python -c "from claude_agent_sdk import ClaudeSDKClient; print('SDK installed')"
```

### Basic Client Setup

```python
import os
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

# Initialize client
client = ClaudeSDKClient(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    system_prompt="You are a helpful AI assistant.",
    model="claude-3-5-sonnet-20241022",
    permission_mode="default"
)

# Simple query
response = await client.query("Analyze this data...")
print(response.content)
```

## Multi-Agent Patterns

### 1. Orchestrator-Worker Pattern

Main orchestrator coordinates specialized subagents:

```python
from claude_agent_sdk import ClaudeSDKClient
import asyncio

class AccountManagerOrchestrator:
    """
    Main orchestrator for Super Account Manager system

    Workflow:
    1. Receive account review request
    2. Delegate to specialized subagents
    3. Aggregate results
    4. Generate final recommendations
    5. Present for approval
    """

    def __init__(self):
        self.client = ClaudeSDKClient(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            system_prompt=self._get_orchestrator_prompt(),
            model="claude-3-5-sonnet-20241022",
            permission_mode="default"
        )

        # Initialize subagents
        self.data_scout = self._create_data_scout()
        self.memory_analyst = self._create_memory_analyst()
        self.recommendation_author = self._create_recommendation_author()

    def _get_orchestrator_prompt(self) -> str:
        return """
        You are the Super Account Manager Orchestrator.

        Your responsibilities:
        1. Coordinate specialized subagents (Data Scout, Memory Analyst, Recommendation Author)
        2. Aggregate insights from multiple sources
        3. Ensure comprehensive account analysis
        4. Present findings for human approval
        5. Log all operations for audit trail

        Always:
        - Delegate specialized tasks to appropriate subagents
        - Validate outputs before aggregation
        - Require approval for any CRM modifications
        - Maintain clear audit trail
        """

    async def review_account(self, account_id: str) -> dict:
        """
        Orchestrate full account review workflow
        """

        # Phase 1: Data gathering (parallel)
        crm_data_task = self.data_scout.gather_crm_data(account_id)
        memory_data_task = self.memory_analyst.retrieve_context(account_id)

        crm_data, memory_data = await asyncio.gather(
            crm_data_task,
            memory_data_task
        )

        # Phase 2: Analysis and recommendations
        recommendations = await self.recommendation_author.generate(
            account_id=account_id,
            crm_data=crm_data,
            historical_context=memory_data
        )

        # Phase 3: Aggregate and format
        review = {
            "account_id": account_id,
            "timestamp": datetime.now().isoformat(),
            "crm_summary": crm_data,
            "historical_insights": memory_data,
            "recommendations": recommendations,
            "requires_approval": True
        }

        return review

    def _create_data_scout(self):
        """Create Data Scout subagent"""
        return DataScoutAgent(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            mcp_servers=self._get_mcp_config()
        )

    def _create_memory_analyst(self):
        """Create Memory Analyst subagent"""
        return MemoryAnalystAgent(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            mcp_servers=self._get_mcp_config()
        )

    def _create_recommendation_author(self):
        """Create Recommendation Author subagent"""
        return RecommendationAuthorAgent(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            allowed_tools=["Write", "Read"]
        )

    def _get_mcp_config(self):
        """MCP server configuration"""
        return {
            "zoho-crm": {
                "command": "uvx",
                "args": ["--from", "zoho-crm-mcp", "zoho-mcp"],
                "transport": "stdio",
                "env": {
                    "ZOHO_CLIENT_ID": os.getenv("ZOHO_CLIENT_ID"),
                    "ZOHO_CLIENT_SECRET": os.getenv("ZOHO_CLIENT_SECRET"),
                    "ZOHO_ACCESS_TOKEN": os.getenv("ZOHO_ACCESS_TOKEN")
                }
            },
            "cognee-memory": {
                "command": "python",
                "args": ["scripts/cognee_mcp_server.py"],
                "transport": "stdio"
            }
        }
```

### 2. Specialized Subagents

#### Data Scout Agent

```python
class DataScoutAgent:
    """
    Specialized agent for gathering CRM data

    Responsibilities:
    - Query Zoho CRM via MCP tools
    - Detect account changes
    - Gather deal pipeline status
    - Collect activity history

    Permissions: Read-only
    """

    def __init__(self, api_key: str, mcp_servers: dict):
        self.client = ClaudeSDKClient(
            api_key=api_key,
            system_prompt=self._get_prompt(),
            model="claude-3-5-sonnet-20241022",
            mcp_servers=mcp_servers,
            allowed_tools=[
                "Read",
                "get_contact_by_email_tool",
                "get_deal_by_name_tool",
                "list_open_deals_tool",
                "get_user_info_tool"
            ],
            disallowed_tools=[
                "Write",
                "create_contact_tool",
                "update_contact_tool"
            ],
            permission_mode="default"
        )

    def _get_prompt(self) -> str:
        return """
        You are a Data Scout specializing in CRM data retrieval.

        Your tasks:
        1. Query Zoho CRM for account information
        2. Detect recent changes and updates
        3. Identify open deals and their status
        4. Gather recent activity history
        5. Collect contact and owner information

        Constraints:
        - READ-ONLY access (no modifications)
        - Return structured, validated data
        - Flag any data quality issues
        - Include timestamps and sources
        """

    async def gather_crm_data(self, account_id: str) -> dict:
        """Gather comprehensive CRM data for account"""

        prompt = f"""
        Gather comprehensive CRM data for account ID: {account_id}

        Required information:
        1. Account basic information (name, owner, status, industry)
        2. All contacts associated with account
        3. Open deals with stages and amounts
        4. Recent activities (last 90 days)
        5. Modified fields (last 30 days)

        Return structured JSON with all findings.
        Flag any missing or incomplete data.
        """

        response = await self.client.query(prompt)
        return response.content
```

#### Memory Analyst Agent

```python
class MemoryAnalystAgent:
    """
    Specialized agent for querying historical context

    Responsibilities:
    - Search Cognee for account history
    - Identify key past events
    - Surface prior commitments
    - Analyze engagement patterns

    Permissions: Read-only memory access
    """

    def __init__(self, api_key: str, mcp_servers: dict):
        self.client = ClaudeSDKClient(
            api_key=api_key,
            system_prompt=self._get_prompt(),
            model="claude-3-5-sonnet-20241022",
            mcp_servers=mcp_servers,
            allowed_tools=[
                "Read",
                "search_account_history",
                "get_account_timeline",
                "get_related_entities"
            ],
            permission_mode="default"
        )

    def _get_prompt(self) -> str:
        return """
        You are a Memory Analyst specializing in historical context retrieval.

        Your tasks:
        1. Query Cognee for account history
        2. Identify key past interactions
        3. Surface prior commitments and promises
        4. Analyze engagement patterns over time
        5. Highlight sentiment trends

        Output:
        - Timeline of significant events
        - Recurring themes and patterns
        - Prior commitments to track
        - Relationship evolution insights
        - Always cite sources with timestamps
        """

    async def retrieve_context(self, account_id: str) -> dict:
        """Retrieve and analyze historical context"""

        prompt = f"""
        Retrieve historical context for account ID: {account_id}

        Focus areas:
        1. Key meetings and their outcomes
        2. Commitments made (by us or customer)
        3. Pain points and challenges discussed
        4. Wins and successes
        5. Engagement pattern evolution

        Organize chronologically and thematically.
        Highlight items requiring follow-up.
        """

        response = await self.client.query(prompt)
        return response.content
```

#### Recommendation Author Agent

```python
class RecommendationAuthorAgent:
    """
    Specialized agent for generating recommendations

    Responsibilities:
    - Synthesize data from other agents
    - Generate actionable recommendations
    - Draft communication templates
    - Prioritize actions

    Permissions: Write access (with approval gates)
    """

    def __init__(self, api_key: str, allowed_tools: list):
        self.client = ClaudeSDKClient(
            api_key=api_key,
            system_prompt=self._get_prompt(),
            model="claude-3-5-sonnet-20241022",
            allowed_tools=allowed_tools,
            permission_mode="default",
            hooks={
                "pre_tool_use": self._approval_hook
            }
        )

    def _get_prompt(self) -> str:
        return """
        You are a Recommendation Author specializing in actionable guidance.

        Your tasks:
        1. Analyze account health and risks
        2. Generate specific, actionable recommendations
        3. Draft communication templates
        4. Prioritize by impact and urgency
        5. Provide clear rationale and success criteria

        Every recommendation must include:
        - Specific action to take
        - Clear rationale with data
        - Priority level
        - Estimated effort
        - Expected outcome
        - Success criteria
        - Draft communication (if applicable)
        """

    async def generate(
        self,
        account_id: str,
        crm_data: dict,
        historical_context: dict
    ) -> list:
        """Generate recommendations based on all available data"""

        prompt = f"""
        Generate actionable recommendations for account {account_id}

        CRM Data:
        {crm_data}

        Historical Context:
        {historical_context}

        Generate 3-5 prioritized recommendations.
        For high-priority items, draft communication templates.
        """

        response = await self.client.query(prompt)
        return response.content

    async def _approval_hook(self, tool_name: str, tool_input: dict):
        """Require approval for any CRM modifications"""
        if tool_name in ["create_contact_tool", "update_contact_tool", "Write"]:
            print(f"\n{'='*60}")
            print(f"APPROVAL REQUIRED")
            print(f"Tool: {tool_name}")
            print(f"Input: {tool_input}")
            print(f"{'='*60}")

            approval = input("Approve? (y/n): ")
            if approval.lower() != 'y':
                raise PermissionError(f"User rejected {tool_name}")
```

## MCP Integration

### Configuring MCP Servers

```python
mcp_config = {
    # Zoho CRM MCP
    "zoho-crm": {
        "command": "uvx",
        "args": ["--from", "zoho-crm-mcp", "zoho-mcp"],
        "transport": "stdio",
        "env": {
            "ZOHO_CLIENT_ID": os.getenv("ZOHO_CLIENT_ID"),
            "ZOHO_CLIENT_SECRET": os.getenv("ZOHO_CLIENT_SECRET"),
            "ZOHO_ACCESS_TOKEN": os.getenv("ZOHO_ACCESS_TOKEN"),
            "ZOHO_REFRESH_TOKEN": os.getenv("ZOHO_REFRESH_TOKEN")
        }
    },

    # Custom Cognee Memory MCP
    "cognee-memory": {
        "command": "python",
        "args": ["scripts/cognee_mcp_server.py"],
        "transport": "stdio"
    },

    # Remote MCP (production)
    "zoho-remote": {
        "command": "npx",
        "args": ["mcp-remote", "https://zoho-mcp2-900114980.zohomcp.com/..."],
        "transport": "sse"
    }
}

# Initialize client with MCP servers
client = ClaudeSDKClient(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    mcp_servers=mcp_config
)
```

### Custom MCP Tool Creation

```python
# scripts/custom_mcp_server.py

from mcp import McpServer
import asyncio

mcp = McpServer("custom-tools")

@mcp.tool()
async def calculate_account_health_score(
    engagement_score: float,
    financial_score: float,
    satisfaction_score: float
) -> dict:
    """Calculate composite account health score"""

    weights = {
        "engagement": 0.40,
        "financial": 0.30,
        "satisfaction": 0.30
    }

    overall = (
        engagement_score * weights["engagement"] +
        financial_score * weights["financial"] +
        satisfaction_score * weights["satisfaction"]
    )

    return {
        "overall_score": overall,
        "health_status": "healthy" if overall > 75 else "at_risk",
        "components": {
            "engagement": engagement_score,
            "financial": financial_score,
            "satisfaction": satisfaction_score
        }
    }

@mcp.tool()
async def detect_risk_signals(account_data: dict) -> list:
    """Detect account risk indicators"""

    risks = []

    if account_data.get("days_since_contact", 0) > 30:
        risks.append({
            "type": "engagement",
            "severity": "high",
            "message": "No contact in 30+ days"
        })

    if account_data.get("payment_status") == "overdue":
        risks.append({
            "type": "financial",
            "severity": "critical",
            "message": "Payment overdue"
        })

    return risks

if __name__ == "__main__":
    mcp.run()
```

## Permission Management

### Permission Modes

```python
# Default mode: prompt for each tool use
client = ClaudeSDKClient(
    api_key=api_key,
    permission_mode="default"
)

# Accept edits automatically
client = ClaudeSDKClient(
    api_key=api_key,
    permission_mode="acceptEdits"
)

# Bypass all permissions (use with caution)
client = ClaudeSDKClient(
    api_key=api_key,
    permission_mode="bypassPermissions"
)

# Plan mode: generate plan without execution
client = ClaudeSDKClient(
    api_key=api_key,
    permission_mode="plan"
)
```

### Fine-Grained Tool Control

```python
# Allowlist specific tools
client = ClaudeSDKClient(
    api_key=api_key,
    allowed_tools=[
        "Read",
        "get_contact_by_email_tool",
        "search_account_history"
    ]
)

# Denylist dangerous tools
client = ClaudeSDKClient(
    api_key=api_key,
    disallowed_tools=[
        "Bash",
        "Write",
        "delete_account_tool"
    ]
)

# Custom permission handler
def custom_permission_handler(tool_name: str, tool_input: dict) -> bool:
    """Custom logic for tool permission"""

    # Always allow read operations
    if tool_name in ["Read", "Grep", "Glob"]:
        return True

    # Require approval for write operations
    if tool_name in ["Write", "Edit"]:
        return get_human_approval(tool_name, tool_input)

    # Block dangerous operations
    if tool_name == "Bash":
        return False

    return True

client = ClaudeSDKClient(
    api_key=api_key,
    can_use_tool=custom_permission_handler
)
```

## Hooks and Lifecycle Management

### Implementing Hooks

```python
class AuditedClient:
    """Client with comprehensive audit hooks"""

    def __init__(self, api_key: str):
        self.audit_log = []

        self.client = ClaudeSDKClient(
            api_key=api_key,
            hooks={
                "pre_tool_use": self.pre_tool_hook,
                "post_tool_use": self.post_tool_hook,
                "prompt_submission": self.prompt_hook,
                "session_start": self.session_start_hook,
                "session_end": self.session_end_hook
            }
        )

    async def pre_tool_hook(self, tool_name: str, tool_input: dict):
        """Log before tool execution"""
        self.audit_log.append({
            "event": "pre_tool_use",
            "tool": tool_name,
            "input": tool_input,
            "timestamp": datetime.now().isoformat()
        })

        # Approval gate for mutations
        if tool_name in ["update_contact_tool", "create_deal_tool"]:
            if not await self.get_approval(tool_name, tool_input):
                raise PermissionError(f"Approval denied for {tool_name}")

    async def post_tool_hook(self, tool_name: str, tool_output: dict):
        """Log after tool execution"""
        self.audit_log.append({
            "event": "post_tool_use",
            "tool": tool_name,
            "output_size": len(str(tool_output)),
            "timestamp": datetime.now().isoformat()
        })

    async def prompt_hook(self, prompt: str):
        """Log user prompts"""
        self.audit_log.append({
            "event": "prompt_submission",
            "prompt_length": len(prompt),
            "timestamp": datetime.now().isoformat()
        })

    async def session_start_hook(self, session_id: str):
        """Initialize session"""
        self.audit_log.append({
            "event": "session_start",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })

    async def session_end_hook(self, session_id: str):
        """Finalize session and persist audit log"""
        self.audit_log.append({
            "event": "session_end",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })

        # Persist audit log
        await self.save_audit_log(session_id)

    async def get_approval(self, tool_name: str, tool_input: dict) -> bool:
        """Get human approval for operation"""
        print(f"\nApproval required for {tool_name}")
        print(f"Input: {tool_input}")
        response = input("Approve? (y/n): ")
        return response.lower() == 'y'

    async def save_audit_log(self, session_id: str):
        """Persist audit log"""
        log_file = f"logs/audit_{session_id}.json"
        with open(log_file, 'w') as f:
            json.dump(self.audit_log, f, indent=2)
```

## Production Deployment

### Environment Configuration

```python
# config/production.py

import os
from dataclasses import dataclass

@dataclass
class ProductionConfig:
    """Production configuration"""

    # API Keys
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY")
    zoho_client_id: str = os.getenv("ZOHO_CLIENT_ID")
    zoho_client_secret: str = os.getenv("ZOHO_CLIENT_SECRET")

    # Model Configuration
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4096
    temperature: float = 0.7

    # Security
    permission_mode: str = "default"
    require_approval_for_writes: bool = True
    audit_logging_enabled: bool = True

    # Performance
    timeout_seconds: int = 300
    max_retries: int = 3

    # MCP Servers
    mcp_servers: dict = None

    def __post_init__(self):
        """Validate configuration"""
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY required")

        if self.mcp_servers is None:
            self.mcp_servers = self._default_mcp_config()

    def _default_mcp_config(self) -> dict:
        """Default MCP server configuration"""
        return {
            "zoho-crm": {
                "command": "npx",
                "args": ["mcp-remote", os.getenv("ZOHO_MCP_ENDPOINT")],
                "transport": "sse"
            },
            "cognee-memory": {
                "command": "python",
                "args": ["scripts/cognee_mcp_server.py"],
                "transport": "stdio"
            }
        }
```

### Monitoring and Observability

```python
import logging
from prometheus_client import Counter, Histogram

# Metrics
tool_usage_counter = Counter(
    'agent_tool_usage_total',
    'Total tool invocations',
    ['agent', 'tool']
)

tool_latency_histogram = Histogram(
    'agent_tool_latency_seconds',
    'Tool execution latency',
    ['agent', 'tool']
)

class MonitoredOrchestrator(AccountManagerOrchestrator):
    """Orchestrator with monitoring"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    async def review_account(self, account_id: str) -> dict:
        """Monitored account review"""

        self.logger.info(f"Starting account review: {account_id}")

        start_time = time.time()

        try:
            result = await super().review_account(account_id)

            # Log success metrics
            duration = time.time() - start_time
            self.logger.info(
                f"Account review completed: {account_id}, "
                f"duration={duration:.2f}s"
            )

            return result

        except Exception as e:
            self.logger.error(
                f"Account review failed: {account_id}, "
                f"error={str(e)}"
            )
            raise
```

## Best Practices

1. **Least Privilege**
   - Grant minimal permissions per subagent
   - Use allowlists, not denylists
   - Require approval for mutations

2. **Separation of Concerns**
   - One subagent per responsibility
   - Clear communication protocols
   - Isolated context windows

3. **Audit Everything**
   - Log all tool uses
   - Record approval decisions
   - Track performance metrics

4. **Error Handling**
   - Implement retries with backoff
   - Graceful degradation
   - Comprehensive error logging

5. **Testing**
   - Unit test each subagent
   - Integration test workflows
   - Load test at scale

## Resources

See `references/api_reference.md` for:
- Complete Claude Agent SDK API
- Advanced configuration options
- Performance optimization guides

See `scripts/` for:
- Example orchestrator implementations
- MCP server templates
- Deployment utilities

See project root `claude_agent_sdk_guide.md` for:
- SDK implementation details
- Customization intake checklist
