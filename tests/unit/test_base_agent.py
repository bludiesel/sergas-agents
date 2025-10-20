"""Comprehensive tests for BaseAgent class.

Test-Driven Development approach for Week 6 implementation.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any
import structlog

from src.agents.base_agent import BaseAgent
from src.models.config import AgentConfig


class MockAgent(BaseAgent):
    """Mock agent implementation for testing."""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock execute method."""
        return {"status": "success", "data": context}


@pytest.fixture
def agent_config():
    """Create test agent configuration."""
    return AgentConfig(
        name="test-agent",
        system_prompt="You are a test agent.",
        allowed_tools=["test_tool_1", "test_tool_2"],
        max_iterations=5,
        temperature=0.5,
    )


@pytest.fixture
def mock_claude_client():
    """Create mock Claude SDK client."""
    client = AsyncMock()
    client.query = AsyncMock(return_value=AsyncMock(__aiter__=lambda self: iter([
        {"type": "text", "content": "Test response"}
    ])))
    return client


@pytest.fixture
def mock_hooks():
    """Create mock hook functions."""
    return {
        "pre_tool": AsyncMock(),
        "post_tool": AsyncMock(),
        "on_session_start": AsyncMock(),
        "on_session_end": AsyncMock(),
    }


class TestBaseAgentInitialization:
    """Test BaseAgent initialization."""

    def test_init_with_minimal_config(self, agent_config):
        """Test agent initialization with minimal configuration."""
        agent = MockAgent(
            agent_id="test-001",
            system_prompt=agent_config.system_prompt,
            allowed_tools=agent_config.allowed_tools,
        )

        assert agent.agent_id == "test-001"
        assert agent.system_prompt == agent_config.system_prompt
        assert agent.allowed_tools == agent_config.allowed_tools
        assert agent.client is None  # Not initialized yet

    def test_init_with_full_config(self, agent_config, mock_hooks):
        """Test agent initialization with full configuration."""
        agent = MockAgent(
            agent_id="test-002",
            system_prompt=agent_config.system_prompt,
            allowed_tools=agent_config.allowed_tools,
            permission_mode="default",
            mcp_servers={"zoho": {"url": "http://localhost:8080"}},
            hooks=mock_hooks,
        )

        assert agent.agent_id == "test-002"
        assert agent.permission_mode == "default"
        assert "zoho" in agent.mcp_servers
        assert agent.hooks == mock_hooks

    def test_init_creates_logger(self, agent_config):
        """Test that initialization creates a structured logger."""
        agent = MockAgent(
            agent_id="test-003",
            system_prompt=agent_config.system_prompt,
            allowed_tools=agent_config.allowed_tools,
        )

        assert agent.logger is not None
        assert isinstance(agent.logger, structlog.BoundLogger)


class TestBaseAgentClientSetup:
    """Test Claude SDK client setup."""

    @patch('src.agents.base_agent.ClaudeSDKClient')
    def test_initialize_client_with_api_key(self, mock_sdk_class, agent_config):
        """Test client initialization with API key."""
        agent = MockAgent(
            agent_id="test-004",
            system_prompt=agent_config.system_prompt,
            allowed_tools=agent_config.allowed_tools,
        )

        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            agent._initialize_client()

        mock_sdk_class.assert_called_once()
        call_args = mock_sdk_class.call_args
        assert call_args[0][0].api_key == 'test-key'

    @patch('src.agents.base_agent.ClaudeSDKClient')
    def test_initialize_client_with_hooks(self, mock_sdk_class, agent_config, mock_hooks):
        """Test client initialization includes hooks."""
        agent = MockAgent(
            agent_id="test-005",
            system_prompt=agent_config.system_prompt,
            allowed_tools=agent_config.allowed_tools,
            hooks=mock_hooks,
        )

        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            agent._initialize_client()

        call_args = mock_sdk_class.call_args
        options = call_args[0][0]
        assert options.hooks == mock_hooks

    @patch('src.agents.base_agent.ClaudeSDKClient')
    def test_initialize_client_with_allowed_tools(self, mock_sdk_class, agent_config):
        """Test client initialization with allowed tools."""
        agent = MockAgent(
            agent_id="test-006",
            system_prompt=agent_config.system_prompt,
            allowed_tools=["tool_a", "tool_b"],
        )

        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            agent._initialize_client()

        call_args = mock_sdk_class.call_args
        options = call_args[0][0]
        assert options.allowed_tools == ["tool_a", "tool_b"]


class TestBaseAgentExecution:
    """Test agent execution flow."""

    @pytest.mark.asyncio
    async def test_execute_method_is_abstract(self):
        """Test that execute method must be implemented by subclasses."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseAgent(
                agent_id="test-007",
                system_prompt="Test",
                allowed_tools=[],
            )

    @pytest.mark.asyncio
    async def test_execute_with_context(self, agent_config):
        """Test execute method with context."""
        agent = MockAgent(
            agent_id="test-008",
            system_prompt=agent_config.system_prompt,
            allowed_tools=agent_config.allowed_tools,
        )

        context = {"account_id": "ACC-001", "action": "analyze"}
        result = await agent.execute(context)

        assert result["status"] == "success"
        assert result["data"] == context

    @pytest.mark.asyncio
    @patch('src.agents.base_agent.ClaudeSDKClient')
    async def test_query_streams_responses(self, mock_sdk_class, agent_config):
        """Test that query method streams responses."""
        # Setup mock to return async generator
        async def mock_stream():
            yield {"type": "text", "content": "Part 1"}
            yield {"type": "text", "content": "Part 2"}

        mock_client = AsyncMock()
        mock_client.query = Mock(return_value=mock_stream())
        mock_sdk_class.return_value = mock_client

        agent = MockAgent(
            agent_id="test-009",
            system_prompt=agent_config.system_prompt,
            allowed_tools=agent_config.allowed_tools,
        )

        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            agent._initialize_client()

        chunks = []
        async for chunk in agent.client.query("Test task"):
            chunks.append(chunk)

        assert len(chunks) == 2
        assert chunks[0]["content"] == "Part 1"
        assert chunks[1]["content"] == "Part 2"


class TestBaseAgentHooks:
    """Test hook integration."""

    @pytest.mark.asyncio
    @patch('src.agents.base_agent.ClaudeSDKClient')
    async def test_pre_tool_hook_called(self, mock_sdk_class, agent_config, mock_hooks):
        """Test that pre_tool hook is called before tool execution."""
        agent = MockAgent(
            agent_id="test-010",
            system_prompt=agent_config.system_prompt,
            allowed_tools=agent_config.allowed_tools,
            hooks=mock_hooks,
        )

        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            agent._initialize_client()

        # Verify hooks were passed to client
        call_args = mock_sdk_class.call_args
        options = call_args[0][0]
        assert options.hooks["pre_tool"] == mock_hooks["pre_tool"]

    @pytest.mark.asyncio
    async def test_session_lifecycle_hooks(self, agent_config, mock_hooks):
        """Test session start and end hooks."""
        agent = MockAgent(
            agent_id="test-011",
            system_prompt=agent_config.system_prompt,
            allowed_tools=agent_config.allowed_tools,
            hooks=mock_hooks,
        )

        # Simulate session start
        await agent.on_session_start()
        mock_hooks["on_session_start"].assert_called_once()

        # Simulate session end
        await agent.on_session_end()
        mock_hooks["on_session_end"].assert_called_once()


class TestBaseAgentErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    @patch('src.agents.base_agent.ClaudeSDKClient')
    async def test_handles_api_errors(self, mock_sdk_class, agent_config):
        """Test handling of API errors."""
        mock_client = AsyncMock()
        mock_client.query.side_effect = Exception("API Error")
        mock_sdk_class.return_value = mock_client

        agent = MockAgent(
            agent_id="test-012",
            system_prompt=agent_config.system_prompt,
            allowed_tools=agent_config.allowed_tools,
        )

        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            agent._initialize_client()

        with pytest.raises(Exception, match="API Error"):
            async for _ in agent.client.query("Test"):
                pass

    @pytest.mark.asyncio
    async def test_handles_missing_context(self, agent_config):
        """Test handling of missing context."""
        agent = MockAgent(
            agent_id="test-013",
            system_prompt=agent_config.system_prompt,
            allowed_tools=agent_config.allowed_tools,
        )

        # Should handle empty context gracefully
        result = await agent.execute({})
        assert result["status"] == "success"


class TestBaseAgentConfiguration:
    """Test configuration validation."""

    def test_rejects_empty_agent_id(self, agent_config):
        """Test that empty agent_id is rejected."""
        with pytest.raises(ValueError, match="agent_id cannot be empty"):
            MockAgent(
                agent_id="",
                system_prompt=agent_config.system_prompt,
                allowed_tools=agent_config.allowed_tools,
            )

    def test_rejects_empty_system_prompt(self, agent_config):
        """Test that empty system_prompt is rejected."""
        with pytest.raises(ValueError, match="system_prompt cannot be empty"):
            MockAgent(
                agent_id="test-014",
                system_prompt="",
                allowed_tools=agent_config.allowed_tools,
            )

    def test_accepts_empty_allowed_tools(self, agent_config):
        """Test that empty allowed_tools list is accepted."""
        agent = MockAgent(
            agent_id="test-015",
            system_prompt=agent_config.system_prompt,
            allowed_tools=[],
        )
        assert agent.allowed_tools == []

    def test_validates_permission_mode(self, agent_config):
        """Test validation of permission_mode."""
        valid_modes = ["default", "acceptEdits", "bypassPermissions", "plan"]

        for mode in valid_modes:
            agent = MockAgent(
                agent_id=f"test-{mode}",
                system_prompt=agent_config.system_prompt,
                allowed_tools=agent_config.allowed_tools,
                permission_mode=mode,
            )
            assert agent.permission_mode == mode

        # Invalid mode should raise error
        with pytest.raises(ValueError, match="Invalid permission_mode"):
            MockAgent(
                agent_id="test-invalid",
                system_prompt=agent_config.system_prompt,
                allowed_tools=agent_config.allowed_tools,
                permission_mode="invalid",
            )


class TestBaseAgentLogging:
    """Test logging functionality."""

    def test_log_initialization(self, agent_config):
        """Test that initialization is logged."""
        with patch('structlog.get_logger') as mock_logger:
            mock_bound_logger = Mock()
            mock_logger.return_value.bind.return_value = mock_bound_logger

            agent = MockAgent(
                agent_id="test-016",
                system_prompt=agent_config.system_prompt,
                allowed_tools=agent_config.allowed_tools,
            )

            # Verify logger was bound with agent_id
            mock_logger.return_value.bind.assert_called_with(agent_id="test-016")

    @pytest.mark.asyncio
    async def test_log_execution_start(self, agent_config):
        """Test that execution start is logged."""
        agent = MockAgent(
            agent_id="test-017",
            system_prompt=agent_config.system_prompt,
            allowed_tools=agent_config.allowed_tools,
        )

        with patch.object(agent.logger, 'info') as mock_log:
            await agent.execute({"test": "data"})
            # Verify execution was logged
            mock_log.assert_called()


class TestBaseAgentMCPServers:
    """Test MCP server configuration."""

    @patch('src.agents.base_agent.ClaudeSDKClient')
    def test_mcp_servers_passed_to_client(self, mock_sdk_class, agent_config):
        """Test that MCP servers are passed to Claude SDK client."""
        mcp_servers = {
            "zoho": {"url": "http://localhost:8080", "api_key": "test"},
            "cognee": {"url": "http://localhost:8081"},
        }

        agent = MockAgent(
            agent_id="test-018",
            system_prompt=agent_config.system_prompt,
            allowed_tools=agent_config.allowed_tools,
            mcp_servers=mcp_servers,
        )

        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            agent._initialize_client()

        call_args = mock_sdk_class.call_args
        options = call_args[0][0]
        assert options.mcp_servers == mcp_servers

    def test_default_empty_mcp_servers(self, agent_config):
        """Test that MCP servers default to empty dict."""
        agent = MockAgent(
            agent_id="test-019",
            system_prompt=agent_config.system_prompt,
            allowed_tools=agent_config.allowed_tools,
        )

        assert agent.mcp_servers == {}
