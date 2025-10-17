# Python 3.14 Claude Agent SDK Implementation Plan

## 1. Executive Summary

This document outlines the comprehensive implementation plan for building a multi-agent system using the Claude Agent SDK (Python) for the Sergas project. The system will orchestrate specialized agents for account management, recommendations, and audit trail processing with integration to Cognee knowledge graphs and Zoho CRM.

### Key Technologies
- **Runtime**: Python 3.14
- **Agent Framework**: `claude-agent-sdk` (Python)
- **Knowledge Graph**: Cognee
- **CRM Integration**: Zoho Books, Zoho Creator, Zoho CRM
- **Orchestration**: Claude Flow (MCP)
- **State Management**: SQLite (local), Redis (production)

## 2. Project Structure

```
sergas_agents/
├── src/
│   ├── agents/                      # Agent implementations
│   │   ├── __init__.py
│   │   ├── base_agent.py           # Base agent class with SDK client
│   │   ├── account_agent.py        # Account management agent
│   │   ├── recommendation_agent.py # Recommendation agent
│   │   ├── audit_agent.py          # Audit trail agent
│   │   └── coordinator_agent.py    # Multi-agent coordinator
│   │
│   ├── tools/                       # MCP tool implementations
│   │   ├── __init__.py
│   │   ├── zoho_tools.py           # Zoho API tools
│   │   ├── cognee_tools.py         # Cognee knowledge graph tools
│   │   ├── analysis_tools.py       # Data analysis tools
│   │   └── validation_tools.py     # Data validation tools
│   │
│   ├── models/                      # Data models
│   │   ├── __init__.py
│   │   ├── account.py              # Account data models
│   │   ├── recommendation.py       # Recommendation models
│   │   ├── audit.py                # Audit trail models
│   │   └── context.py              # Agent context models
│   │
│   ├── hooks/                       # SDK lifecycle hooks
│   │   ├── __init__.py
│   │   ├── audit_hooks.py          # Audit logging hooks
│   │   ├── permission_hooks.py     # Permission enforcement
│   │   └── metrics_hooks.py        # Performance metrics
│   │
│   ├── services/                    # External service clients
│   │   ├── __init__.py
│   │   ├── zoho_client.py          # Zoho API client
│   │   ├── cognee_client.py        # Cognee client wrapper
│   │   └── mcp_client.py           # MCP server client
│   │
│   ├── utils/                       # Utility functions
│   │   ├── __init__.py
│   │   ├── config.py               # Configuration management
│   │   ├── logging.py              # Logging configuration
│   │   ├── validation.py           # Data validation utilities
│   │   └── retry.py                # Retry logic with backoff
│   │
│   └── main.py                      # Application entry point
│
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── unit/                        # Unit tests
│   │   ├── test_agents.py
│   │   ├── test_tools.py
│   │   └── test_models.py
│   ├── integration/                 # Integration tests
│   │   ├── test_zoho_integration.py
│   │   ├── test_cognee_integration.py
│   │   └── test_agent_workflows.py
│   └── e2e/                         # End-to-end tests
│       └── test_full_workflows.py
│
├── config/                          # Configuration files
│   ├── settings.yaml               # Application settings
│   ├── agents.yaml                 # Agent configurations
│   └── tools.yaml                  # Tool permissions
│
├── scripts/                         # Utility scripts
│   ├── setup_env.py                # Environment setup
│   ├── seed_data.py                # Test data seeding
│   └── run_tests.sh                # Test runner
│
├── docs/                            # Documentation
│   ├── implementation_plan.md      # This file
│   ├── data_models.md              # Data model specifications
│   ├── api_contracts.md            # API contracts
│   └── deployment.md               # Deployment guide
│
├── .claude/                         # Claude Code configuration
│   ├── CLAUDE.md                   # Project instructions
│   └── agents/                     # Agent definitions
│       ├── account_agent.md
│       ├── recommendation_agent.md
│       └── audit_agent.md
│
├── .swarm/                          # Swarm coordination data
│   └── memory.db                   # Session memory
│
├── pyproject.toml                   # Project dependencies
├── requirements.txt                 # Pinned dependencies
├── requirements-dev.txt             # Development dependencies
├── .env.example                     # Environment variables template
├── .gitignore
└── README.md
```

## 3. Package Dependencies

### Core Dependencies (pyproject.toml)

```toml
[project]
name = "sergas-agents"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = [
    # Claude Agent SDK
    "claude-agent-sdk>=0.1.0",
    "anthropic>=0.30.0",

    # Knowledge Graph
    "cognee>=0.1.0",

    # Zoho Integrations
    "zoho-crm-python>=1.0.0",
    "zoho-books-python>=1.0.0",
    "requests>=2.31.0",

    # Data Processing
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "python-dotenv>=1.0.0",

    # Database & Caching
    "sqlalchemy>=2.0.0",
    "redis>=5.0.0",
    "aiosqlite>=0.20.0",

    # Async & Concurrency
    "asyncio>=3.4.3",
    "aiohttp>=3.9.0",
    "tenacity>=8.3.0",

    # Utilities
    "pyyaml>=6.0.1",
    "python-dateutil>=2.9.0",
    "rich>=13.7.0",

    # Monitoring & Logging
    "structlog>=24.1.0",
    "prometheus-client>=0.20.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "pytest-mock>=3.14.0",
    "black>=24.4.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
    "pre-commit>=3.7.0",
]
```

### requirements.txt (Pinned Versions)
Generated via: `pip freeze > requirements.txt`

### requirements-dev.txt
Development tools, linters, testing frameworks

## 4. Configuration Management

### 4.1 Environment Variables (.env)

```bash
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-xxx
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929

# Zoho API
ZOHO_CLIENT_ID=xxx
ZOHO_CLIENT_SECRET=xxx
ZOHO_REFRESH_TOKEN=xxx
ZOHO_ORGANIZATION_ID=xxx

# Cognee
COGNEE_API_KEY=xxx
COGNEE_ENDPOINT=https://api.cognee.ai

# Database
DATABASE_URL=sqlite:///./sergas_agents.db
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Agent Configuration
MAX_ITERATIONS=10
TIMEOUT_SECONDS=300
ENABLE_HOOKS=true
PERMISSION_MODE=default
```

### 4.2 Settings Management (src/utils/config.py)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class AnthropicSettings(BaseSettings):
    api_key: str
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 8192
    temperature: float = 0.7

class ZohoSettings(BaseSettings):
    client_id: str
    client_secret: str
    refresh_token: str
    organization_id: str
    base_url: str = "https://www.zohoapis.com"

class CogneeSettings(BaseSettings):
    api_key: str
    endpoint: str = "https://api.cognee.ai"

class AgentSettings(BaseSettings):
    max_iterations: int = 10
    timeout_seconds: int = 300
    enable_hooks: bool = True
    permission_mode: Literal["default", "acceptEdits", "bypassPermissions", "plan"] = "default"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
    )

    anthropic: AnthropicSettings
    zoho: ZohoSettings
    cognee: CogneeSettings
    agent: AgentSettings
    database_url: str
    redis_url: str
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"

# Global settings instance
settings = Settings()
```

### 4.3 Agent Configuration (config/agents.yaml)

```yaml
agents:
  account_agent:
    name: "Account Management Agent"
    system_prompt: |
      You are an expert account management agent responsible for analyzing
      customer accounts, identifying patterns, and maintaining data quality.
    allowed_tools:
      - read
      - write
      - grep
      - glob
      - zoho_query_accounts
      - cognee_search
      - validate_account_data
    permission_mode: "default"
    max_iterations: 10

  recommendation_agent:
    name: "Recommendation Engine Agent"
    system_prompt: |
      You are a recommendation specialist that analyzes account data and
      generates personalized recommendations using historical patterns.
    allowed_tools:
      - read
      - grep
      - cognee_query_graph
      - zoho_query_transactions
      - generate_recommendation
    permission_mode: "default"
    max_iterations: 8

  audit_agent:
    name: "Audit Trail Agent"
    system_prompt: |
      You are an audit specialist ensuring compliance and tracking all
      system changes with detailed logging and verification.
    allowed_tools:
      - read
      - write
      - audit_log_event
      - verify_compliance
    permission_mode: "default"
    max_iterations: 5
```

## 5. Agent Implementation Patterns

### 5.1 Base Agent Class (src/agents/base_agent.py)

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from typing import AsyncGenerator, Optional, Dict, Any, List
import structlog
from src.utils.config import settings
from src.hooks.audit_hooks import audit_hook
from src.hooks.permission_hooks import permission_hook
from src.hooks.metrics_hooks import metrics_hook

logger = structlog.get_logger()

class BaseAgent:
    """Base class for all agents using Claude SDK."""

    def __init__(
        self,
        agent_id: str,
        system_prompt: str,
        allowed_tools: List[str],
        mcp_servers: Optional[Dict[str, Any]] = None,
        permission_mode: str = "default",
    ):
        self.agent_id = agent_id
        self.logger = logger.bind(agent_id=agent_id)

        # Configure agent options
        self.options = ClaudeAgentOptions(
            api_key=settings.anthropic.api_key,
            model=settings.anthropic.model,
            system_prompt=system_prompt,
            allowed_tools=allowed_tools,
            permission_mode=permission_mode,
            mcp_servers=mcp_servers or {},
            hooks={
                "pre_tool": audit_hook.pre_tool,
                "post_tool": audit_hook.post_tool,
                "on_session_start": metrics_hook.on_session_start,
                "on_session_end": metrics_hook.on_session_end,
                "can_use_tool": permission_hook.can_use_tool,
            },
            max_iterations=settings.agent.max_iterations,
            timeout=settings.agent.timeout_seconds,
        )

        # Initialize SDK client
        self.client = ClaudeSDKClient(self.options)
        self.session_id: Optional[str] = None

    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Execute agent task with streaming responses."""
        self.logger.info("agent_execution_started", task=task)

        try:
            # Format prompt with context
            prompt = self._format_prompt(task, context)

            # Stream responses
            async for chunk in self.client.query(prompt):
                if chunk.get("type") == "text":
                    yield chunk.get("content", "")
                elif chunk.get("type") == "session_id":
                    self.session_id = chunk.get("session_id")

            self.logger.info("agent_execution_completed", session_id=self.session_id)

        except Exception as e:
            self.logger.error("agent_execution_failed", error=str(e))
            raise

    def _format_prompt(self, task: str, context: Optional[Dict[str, Any]]) -> str:
        """Format task prompt with context."""
        if not context:
            return task

        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
        return f"{task}\n\nContext:\n{context_str}"

    async def continue_session(self, additional_prompt: str) -> AsyncGenerator[str, None]:
        """Continue existing session with additional prompt."""
        if not self.session_id:
            raise ValueError("No active session to continue")

        async for chunk in self.client.query(
            additional_prompt,
            session_id=self.session_id,
        ):
            if chunk.get("type") == "text":
                yield chunk.get("content", "")

    async def close(self):
        """Clean up resources."""
        await self.client.close()
```

### 5.2 Specialized Agent Example (src/agents/account_agent.py)

```python
from src.agents.base_agent import BaseAgent
from src.tools.zoho_tools import zoho_mcp_server
from src.tools.cognee_tools import cognee_mcp_server
from typing import Dict, Any, List
import yaml

class AccountAgent(BaseAgent):
    """Agent specialized in account management and analysis."""

    def __init__(self):
        # Load configuration
        with open("config/agents.yaml") as f:
            config = yaml.safe_load(f)["agents"]["account_agent"]

        super().__init__(
            agent_id="account_agent",
            system_prompt=config["system_prompt"],
            allowed_tools=config["allowed_tools"],
            mcp_servers={
                "zoho": zoho_mcp_server,
                "cognee": cognee_mcp_server,
            },
            permission_mode=config["permission_mode"],
        )

    async def analyze_account(self, account_id: str) -> Dict[str, Any]:
        """Analyze specific account and return insights."""
        task = f"""
        Analyze account {account_id} and provide:
        1. Account status and health metrics
        2. Transaction patterns and anomalies
        3. Engagement history and trends
        4. Risk assessment
        5. Recommendations for account optimization

        Use Zoho API to fetch account data and Cognee to search for
        historical patterns and similar accounts.
        """

        results = []
        async for chunk in self.execute(task, {"account_id": account_id}):
            results.append(chunk)

        return {
            "account_id": account_id,
            "analysis": "".join(results),
            "session_id": self.session_id,
        }
```

## 6. Hook Implementation Strategies

### 6.1 Audit Hooks (src/hooks/audit_hooks.py)

```python
import structlog
from datetime import datetime
from typing import Dict, Any
from src.models.audit import AuditEvent
from src.services.database import get_db_session

logger = structlog.get_logger()

class AuditHook:
    """Comprehensive audit logging for all agent actions."""

    async def pre_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        context: Dict[str, Any],
    ) -> None:
        """Log tool execution before it runs."""
        logger.info(
            "tool_execution_started",
            tool_name=tool_name,
            tool_input=tool_input,
            agent_id=context.get("agent_id"),
            session_id=context.get("session_id"),
        )

        # Store audit event
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            event_type="tool_execution",
            agent_id=context.get("agent_id"),
            session_id=context.get("session_id"),
            tool_name=tool_name,
            tool_input=tool_input,
            status="started",
        )

        async with get_db_session() as session:
            session.add(event)
            await session.commit()

    async def post_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Any,
        context: Dict[str, Any],
        error: Optional[Exception] = None,
    ) -> None:
        """Log tool execution after completion."""
        status = "failed" if error else "completed"

        logger.info(
            "tool_execution_completed",
            tool_name=tool_name,
            status=status,
            error=str(error) if error else None,
        )

        # Update audit event
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            event_type="tool_execution",
            agent_id=context.get("agent_id"),
            session_id=context.get("session_id"),
            tool_name=tool_name,
            tool_output=tool_output if not error else None,
            error=str(error) if error else None,
            status=status,
        )

        async with get_db_session() as session:
            session.add(event)
            await session.commit()

audit_hook = AuditHook()
```

### 6.2 Permission Hooks (src/hooks/permission_hooks.py)

```python
import structlog
from typing import Dict, Any, List
import yaml

logger = structlog.get_logger()

class PermissionHook:
    """Enforce tool permissions and security policies."""

    def __init__(self):
        # Load tool permissions from config
        with open("config/tools.yaml") as f:
            self.permissions = yaml.safe_load(f)

    def can_use_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        context: Dict[str, Any],
    ) -> bool:
        """Determine if agent can use specific tool with given input."""
        agent_id = context.get("agent_id")

        # Check if agent has permission for this tool
        agent_permissions = self.permissions.get(agent_id, {})
        if tool_name not in agent_permissions.get("allowed_tools", []):
            logger.warning(
                "tool_permission_denied",
                agent_id=agent_id,
                tool_name=tool_name,
                reason="tool_not_allowed",
            )
            return False

        # Check tool-specific constraints
        constraints = agent_permissions.get("constraints", {}).get(tool_name, {})

        # Example: File path restrictions
        if tool_name in ["read", "write", "edit"]:
            file_path = tool_input.get("file_path", "")
            allowed_paths = constraints.get("allowed_paths", [])

            if allowed_paths and not any(
                file_path.startswith(path) for path in allowed_paths
            ):
                logger.warning(
                    "tool_permission_denied",
                    agent_id=agent_id,
                    tool_name=tool_name,
                    file_path=file_path,
                    reason="path_not_allowed",
                )
                return False

        # Example: Bash command restrictions
        if tool_name == "bash":
            command = tool_input.get("command", "")
            blocked_commands = constraints.get("blocked_commands", [])

            if any(cmd in command for cmd in blocked_commands):
                logger.warning(
                    "tool_permission_denied",
                    agent_id=agent_id,
                    tool_name=tool_name,
                    command=command,
                    reason="command_blocked",
                )
                return False

        logger.info(
            "tool_permission_granted",
            agent_id=agent_id,
            tool_name=tool_name,
        )
        return True

permission_hook = PermissionHook()
```

### 6.3 Metrics Hooks (src/hooks/metrics_hooks.py)

```python
import structlog
from datetime import datetime
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge
import time

logger = structlog.get_logger()

# Prometheus metrics
session_counter = Counter("agent_sessions_total", "Total agent sessions", ["agent_id"])
tool_counter = Counter("agent_tool_calls_total", "Total tool calls", ["agent_id", "tool_name"])
tool_duration = Histogram("agent_tool_duration_seconds", "Tool execution duration", ["tool_name"])
active_sessions = Gauge("agent_active_sessions", "Active agent sessions", ["agent_id"])

class MetricsHook:
    """Collect performance metrics for monitoring."""

    def __init__(self):
        self.session_start_times: Dict[str, float] = {}
        self.tool_start_times: Dict[str, float] = {}

    def on_session_start(self, context: Dict[str, Any]) -> None:
        """Track session start."""
        session_id = context.get("session_id")
        agent_id = context.get("agent_id")

        self.session_start_times[session_id] = time.time()

        session_counter.labels(agent_id=agent_id).inc()
        active_sessions.labels(agent_id=agent_id).inc()

        logger.info("session_started", session_id=session_id, agent_id=agent_id)

    def on_session_end(self, context: Dict[str, Any]) -> None:
        """Track session end and duration."""
        session_id = context.get("session_id")
        agent_id = context.get("agent_id")

        start_time = self.session_start_times.pop(session_id, None)
        if start_time:
            duration = time.time() - start_time
            logger.info(
                "session_ended",
                session_id=session_id,
                agent_id=agent_id,
                duration_seconds=duration,
            )

        active_sessions.labels(agent_id=agent_id).dec()

metrics_hook = MetricsHook()
```

## 7. Tool Registration and Permission Enforcement

### 7.1 Zoho Tools (src/tools/zoho_tools.py)

```python
from claude_agent_sdk import tool, create_sdk_mcp_server
from src.services.zoho_client import ZohoClient
from typing import Dict, Any, List
import structlog

logger = structlog.get_logger()
zoho_client = ZohoClient()

@tool
async def zoho_query_accounts(
    query: str,
    filters: Dict[str, Any] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Query Zoho CRM for account data.

    Args:
        query: Search query or account criteria
        filters: Additional filters (status, date range, etc.)
        limit: Maximum number of results

    Returns:
        List of account records
    """
    logger.info("zoho_query_accounts", query=query, filters=filters)

    try:
        results = await zoho_client.search_accounts(
            query=query,
            filters=filters,
            limit=limit,
        )
        return results
    except Exception as e:
        logger.error("zoho_query_failed", error=str(e))
        raise

@tool
async def zoho_update_account(
    account_id: str,
    updates: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update account record in Zoho CRM.

    Args:
        account_id: Zoho account ID
        updates: Fields to update

    Returns:
        Updated account record
    """
    logger.info("zoho_update_account", account_id=account_id, updates=updates)

    try:
        result = await zoho_client.update_account(account_id, updates)
        return result
    except Exception as e:
        logger.error("zoho_update_failed", error=str(e))
        raise

# Create MCP server for Zoho tools
zoho_mcp_server = create_sdk_mcp_server(
    name="zoho",
    tools=[zoho_query_accounts, zoho_update_account],
)
```

### 7.2 Tool Permissions Config (config/tools.yaml)

```yaml
# Tool permissions by agent
account_agent:
  allowed_tools:
    - read
    - write
    - grep
    - glob
    - zoho_query_accounts
    - zoho_update_account
    - cognee_search
    - validate_account_data
  constraints:
    read:
      allowed_paths:
        - /Users/mohammadabdelrahman/Projects/sergas_agents/data
        - /Users/mohammadabdelrahman/Projects/sergas_agents/config
    write:
      allowed_paths:
        - /Users/mohammadabdelrahman/Projects/sergas_agents/data/output
    bash:
      blocked_commands:
        - rm -rf
        - sudo
        - chmod
        - chown

recommendation_agent:
  allowed_tools:
    - read
    - grep
    - cognee_query_graph
    - zoho_query_transactions
    - generate_recommendation
  constraints:
    read:
      allowed_paths:
        - /Users/mohammadabdelrahman/Projects/sergas_agents/data

audit_agent:
  allowed_tools:
    - read
    - write
    - audit_log_event
    - verify_compliance
  constraints:
    write:
      allowed_paths:
        - /Users/mohammadabdelrahman/Projects/sergas_agents/logs
        - /Users/mohammadabdelrahman/Projects/sergas_agents/data/audit
```

## 8. Error Handling and Logging Framework

### 8.1 Logging Configuration (src/utils/logging.py)

```python
import structlog
import logging
import sys
from src.utils.config import settings

def configure_logging():
    """Configure structured logging for the application."""

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer() if settings.log_format == "json"
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )
```

### 8.2 Error Handling Utilities (src/utils/retry.py)

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import structlog
from typing import Callable, TypeVar, Any

logger = structlog.get_logger()
T = TypeVar("T")

def with_retry(
    max_attempts: int = 3,
    min_wait: int = 1,
    max_wait: int = 10,
    exceptions: tuple = (Exception,),
):
    """Decorator for retrying failed operations with exponential backoff."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(exceptions),
            reraise=True,
        )
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                logger.warning(
                    "operation_retry",
                    function=func.__name__,
                    error=str(e),
                    attempt=wrapper.retry.statistics.get("attempt_number", 0),
                )
                raise

        return wrapper
    return decorator
```

## 9. Testing Strategy

### 9.1 Unit Tests (tests/unit/test_agents.py)

```python
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.agents.account_agent import AccountAgent

@pytest.mark.asyncio
class TestAccountAgent:
    """Unit tests for AccountAgent."""

    async def test_agent_initialization(self):
        """Test agent initializes correctly."""
        agent = AccountAgent()
        assert agent.agent_id == "account_agent"
        assert agent.client is not None

    async def test_analyze_account_success(self):
        """Test successful account analysis."""
        agent = AccountAgent()

        # Mock the SDK client
        with patch.object(agent.client, "query") as mock_query:
            mock_query.return_value = AsyncMock([
                {"type": "text", "content": "Analysis result"},
                {"type": "session_id", "session_id": "test-session"},
            ])

            result = await agent.analyze_account("ACC-12345")

            assert result["account_id"] == "ACC-12345"
            assert "analysis" in result
            assert result["session_id"] == "test-session"

    async def test_analyze_account_error_handling(self):
        """Test error handling in account analysis."""
        agent = AccountAgent()

        with patch.object(agent.client, "query") as mock_query:
            mock_query.side_effect = Exception("API Error")

            with pytest.raises(Exception, match="API Error"):
                await agent.analyze_account("ACC-12345")
```

### 9.2 Integration Tests (tests/integration/test_zoho_integration.py)

```python
import pytest
from src.tools.zoho_tools import zoho_query_accounts, zoho_update_account
from src.services.zoho_client import ZohoClient

@pytest.mark.integration
@pytest.mark.asyncio
class TestZohoIntegration:
    """Integration tests for Zoho API."""

    @pytest.fixture
    async def zoho_client(self):
        """Create Zoho client for testing."""
        client = ZohoClient()
        yield client
        await client.close()

    async def test_query_accounts(self, zoho_client):
        """Test querying accounts from Zoho."""
        results = await zoho_query_accounts(
            query="status:active",
            limit=10,
        )

        assert isinstance(results, list)
        assert len(results) <= 10

    async def test_update_account(self, zoho_client):
        """Test updating account in Zoho."""
        # Use test account
        account_id = "TEST-ACCOUNT-ID"
        updates = {"notes": "Updated by test"}

        result = await zoho_update_account(account_id, updates)

        assert result["id"] == account_id
        assert result["notes"] == "Updated by test"
```

### 9.3 End-to-End Tests (tests/e2e/test_full_workflows.py)

```python
import pytest
from src.agents.account_agent import AccountAgent
from src.agents.recommendation_agent import RecommendationAgent
from src.agents.audit_agent import AuditAgent

@pytest.mark.e2e
@pytest.mark.asyncio
class TestFullWorkflows:
    """End-to-end workflow tests."""

    async def test_account_analysis_workflow(self):
        """Test complete account analysis workflow."""
        # Initialize agents
        account_agent = AccountAgent()
        recommendation_agent = RecommendationAgent()
        audit_agent = AuditAgent()

        try:
            # Step 1: Analyze account
            account_analysis = await account_agent.analyze_account("ACC-12345")
            assert account_analysis["account_id"] == "ACC-12345"

            # Step 2: Generate recommendations
            recommendations = await recommendation_agent.generate_recommendations(
                account_id="ACC-12345",
                analysis=account_analysis["analysis"],
            )
            assert len(recommendations) > 0

            # Step 3: Audit the workflow
            audit_result = await audit_agent.audit_workflow(
                workflow_id="account-analysis",
                steps=[account_analysis, recommendations],
            )
            assert audit_result["status"] == "completed"

        finally:
            await account_agent.close()
            await recommendation_agent.close()
            await audit_agent.close()
```

### 9.4 Test Configuration (pytest.ini)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests with external services
    e2e: End-to-end workflow tests
    slow: Tests that take longer than 5 seconds
addopts =
    -v
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
```

## 10. CI/CD Pipeline Requirements

### 10.1 GitHub Actions Workflow (.github/workflows/ci.yml)

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.14"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Cache dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Lint with ruff
        run: ruff check src tests

      - name: Type check with mypy
        run: mypy src

      - name: Run unit tests
        run: pytest tests/unit -v --cov=src --cov-report=xml

      - name: Run integration tests
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          ZOHO_CLIENT_ID: ${{ secrets.ZOHO_CLIENT_ID }}
          ZOHO_CLIENT_SECRET: ${{ secrets.ZOHO_CLIENT_SECRET }}
        run: pytest tests/integration -v

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run security scan
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

  deploy:
    needs: [test, security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t sergas-agents:${{ github.sha }} .

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push sergas-agents:${{ github.sha }}
```

### 10.2 Pre-commit Hooks (.pre-commit-config.yaml)

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 24.4.0
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

## 11. Development Workflow and Standards

### 11.1 Code Style Standards

- **Formatting**: Black (line length: 100)
- **Linting**: Ruff with strict settings
- **Type Checking**: MyPy with strict mode
- **Docstrings**: Google style
- **Import Ordering**: isort

### 11.2 Git Workflow

1. **Branch Strategy**: GitFlow
   - `main`: Production-ready code
   - `develop`: Integration branch
   - `feature/*`: New features
   - `bugfix/*`: Bug fixes
   - `hotfix/*`: Urgent production fixes

2. **Commit Messages**: Conventional Commits
   ```
   type(scope): subject

   body

   footer
   ```
   Types: feat, fix, docs, style, refactor, test, chore

3. **Pull Request Process**:
   - Create PR from feature branch to develop
   - Require 1 approval
   - Pass all CI checks
   - Squash and merge

### 11.3 Development Environment Setup

```bash
# Clone repository
git clone <repo-url>
cd sergas_agents

# Create virtual environment
python3.14 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run tests
pytest

# Start development server
python src/main.py
```

### 11.4 Documentation Standards

- **Code Documentation**: All public APIs must have docstrings
- **README**: Keep updated with setup and usage instructions
- **CHANGELOG**: Track all notable changes
- **API Documentation**: Auto-generate from docstrings using Sphinx
- **Architecture Diagrams**: Maintain in docs/ directory

## 12. Monitoring and Observability

### 12.1 Metrics Collection

- **Prometheus**: Expose metrics endpoint at `/metrics`
- **Key Metrics**:
  - Agent session count and duration
  - Tool call frequency and latency
  - Error rates by agent and tool
  - API request rates to external services
  - Memory and CPU usage

### 12.2 Logging Strategy

- **Structured Logging**: JSON format with structlog
- **Log Levels**:
  - DEBUG: Detailed debugging information
  - INFO: General informational messages
  - WARNING: Warning messages for potential issues
  - ERROR: Error messages for failures
  - CRITICAL: Critical issues requiring immediate attention

### 12.3 Alerting

- **Alert Channels**: Slack, PagerDuty, Email
- **Alert Conditions**:
  - Error rate > 5% over 5 minutes
  - API latency > 2 seconds
  - Agent session failures > 10% over 10 minutes
  - External service unavailable

## 13. Security Considerations

### 13.1 API Key Management

- Store in environment variables
- Use secret management service (AWS Secrets Manager, HashiCorp Vault)
- Rotate keys regularly
- Never commit to version control

### 13.2 Data Privacy

- Encrypt sensitive data at rest
- Use TLS for data in transit
- Implement data retention policies
- Comply with GDPR/CCPA requirements

### 13.3 Access Control

- Implement role-based access control (RBAC)
- Use principle of least privilege
- Audit all access attempts
- Enforce MFA for production access

## 14. Deployment Strategy

### 14.1 Environments

- **Development**: Local development with mock data
- **Staging**: Pre-production testing with sanitized data
- **Production**: Live environment with production data

### 14.2 Deployment Process

1. Merge to main branch
2. CI pipeline builds and tests
3. Docker image created and pushed
4. Deploy to staging
5. Run smoke tests
6. Deploy to production (blue-green deployment)
7. Monitor for issues
8. Rollback if necessary

### 14.3 Rollback Strategy

- Keep previous 5 versions
- Automated rollback on critical errors
- Manual rollback approval process
- Database migration rollback scripts

## 15. Next Steps and Timeline

### Phase 1: Foundation (Week 1-2)
- [ ] Setup project structure
- [ ] Configure dependencies and environment
- [ ] Implement base agent class
- [ ] Setup logging and error handling
- [ ] Create initial tests

### Phase 2: Core Agents (Week 3-4)
- [ ] Implement AccountAgent
- [ ] Implement RecommendationAgent
- [ ] Implement AuditAgent
- [ ] Create MCP tools for Zoho and Cognee
- [ ] Implement hooks framework

### Phase 3: Integration (Week 5-6)
- [ ] Integrate with Zoho APIs
- [ ] Integrate with Cognee
- [ ] Implement coordinator agent
- [ ] Create integration tests
- [ ] Setup CI/CD pipeline

### Phase 4: Testing & Refinement (Week 7-8)
- [ ] Comprehensive testing (unit, integration, e2e)
- [ ] Performance optimization
- [ ] Security audit
- [ ] Documentation completion
- [ ] User acceptance testing

### Phase 5: Deployment (Week 9-10)
- [ ] Staging deployment
- [ ] Production deployment
- [ ] Monitoring setup
- [ ] Training and handover
- [ ] Post-deployment support

## 16. Success Metrics

- **Reliability**: 99.9% uptime
- **Performance**: < 2s average response time
- **Accuracy**: > 95% recommendation accuracy
- **Coverage**: > 80% test coverage
- **Security**: Zero security incidents
- **User Satisfaction**: > 4.5/5 rating

## 17. Support and Maintenance

### 17.1 Support Channels

- GitHub Issues for bug reports
- Slack channel for internal support
- Email for external inquiries

### 17.2 Maintenance Schedule

- **Daily**: Automated monitoring and alerts
- **Weekly**: Review logs and metrics
- **Monthly**: Dependency updates and security patches
- **Quarterly**: Performance reviews and optimization

### 17.3 Escalation Path

1. Level 1: Development team (response time: 4 hours)
2. Level 2: Technical lead (response time: 2 hours)
3. Level 3: CTO/System architect (response time: 1 hour)
4. Critical: Immediate response for production outages

---

This implementation plan provides a comprehensive roadmap for building a robust, scalable, and maintainable multi-agent system using the Claude Agent SDK. All code examples follow Python 3.14 best practices and the Claude SDK's recommended patterns for production deployments.
