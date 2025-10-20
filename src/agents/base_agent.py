"""Base agent class using Claude Agent SDK.

Part of Week 6: Base Agent Infrastructure - Complete Implementation.
"""

import os
import structlog
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, AsyncGenerator
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

from src.hooks.audit_hooks import AuditHook
from src.hooks.permission_hooks import PermissionHook
from src.hooks.metrics_hooks import MetricsHook
from src.events.ag_ui_emitter import AGUIEventEmitter

logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    """Base class for all agents using Claude Agent SDK.

    Provides:
    - Claude SDK client initialization
    - Hook system integration (audit, permission, metrics)
    - Session management
    - Tool permission enforcement
    - Structured logging

    Example:
        class MyAgent(BaseAgent):
            async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
                # Your implementation
                pass
    """

    # Valid permission modes for Claude SDK
    VALID_PERMISSION_MODES = ["default", "acceptEdits", "bypassPermissions", "plan"]

    def __init__(
        self,
        agent_id: str,
        system_prompt: str,
        allowed_tools: list[str],
        permission_mode: str = "default",
        mcp_servers: Optional[Dict[str, Any]] = None,
        hooks: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize base agent.

        Args:
            agent_id: Unique identifier for this agent
            system_prompt: System prompt defining agent behavior
            allowed_tools: List of tool names this agent can use
            permission_mode: Permission enforcement mode
            mcp_servers: MCP server configurations
            hooks: Custom hooks (or defaults will be used)
            **kwargs: Additional configuration

        Raises:
            ValueError: If agent_id or system_prompt is empty, or permission_mode is invalid
        """
        # Validate inputs
        if not agent_id:
            raise ValueError("agent_id cannot be empty")
        if not system_prompt:
            raise ValueError("system_prompt cannot be empty")
        if permission_mode not in self.VALID_PERMISSION_MODES:
            raise ValueError(
                f"Invalid permission_mode: {permission_mode}. "
                f"Must be one of {self.VALID_PERMISSION_MODES}"
            )

        # Core properties
        self.agent_id = agent_id
        self.system_prompt = system_prompt
        self.allowed_tools = allowed_tools
        self.permission_mode = permission_mode
        self.mcp_servers = mcp_servers or {}

        # Setup structured logging
        self.logger = logger.bind(agent_id=agent_id)

        # Initialize hooks (use provided or create defaults)
        if hooks:
            self.hooks = hooks
        else:
            self.hooks = {
                "pre_tool": AuditHook().pre_tool,
                "post_tool": AuditHook().post_tool,
                "on_session_start": MetricsHook().on_session_start,
                "on_session_end": MetricsHook().on_session_end,
            }

        # Claude SDK client (initialized later)
        self.client: Optional[ClaudeSDKClient] = None

        # Session tracking
        self.session_id: Optional[str] = None

        self.logger.info(
            "agent_initialized",
            system_prompt_length=len(system_prompt),
            allowed_tools_count=len(allowed_tools),
            permission_mode=permission_mode,
        )

    def _initialize_client(self) -> None:
        """Initialize Claude SDK client with configuration.

        Called automatically when needed or can be called manually.
        Requires ANTHROPIC_API_KEY in environment.

        Raises:
            ValueError: If ANTHROPIC_API_KEY is not set
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable must be set"
            )

        # Configure Claude SDK options
        options = ClaudeAgentOptions(
            api_key=api_key,
            model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
            system_prompt=self.system_prompt,
            allowed_tools=self.allowed_tools,
            permission_mode=self.permission_mode,
            mcp_servers=self.mcp_servers,
            hooks=self.hooks,
        )

        # Initialize SDK client
        self.client = ClaudeSDKClient(options)

        self.logger.info(
            "claude_sdk_client_initialized",
            model=options.model,
            tools_count=len(self.allowed_tools),
            mcp_servers_count=len(self.mcp_servers),
        )

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent task.

        This method must be implemented by all subclasses.

        Args:
            context: Execution context with input data

        Returns:
            Results dictionary with agent output

        Example:
            async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
                account_id = context.get("account_id")
                # Process account
                return {"status": "success", "account_id": account_id}
        """
        pass

    async def execute_with_events(
        self,
        context: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute agent with AG UI Protocol event streaming.

        Subclasses SHOULD override this method to emit custom events.
        Default implementation wraps execute() and emits basic events.

        Args:
            context: Execution context with input data

        Yields:
            AG UI Protocol events (agent_started, agent_stream, agent_completed, etc.)
        """
        # Default implementation - subclasses override for custom streaming
        session_id = context.get("session_id", "default")
        emitter = AGUIEventEmitter(session_id=session_id)

        step = context.get("step", 0)
        task = context.get("task", f"Execute {self.agent_id}")

        try:
            # Emit agent started
            yield emitter.emit_agent_started(
                agent=self.agent_id,
                step=step,
                task=task
            )

            # Call existing execute() method
            result = await self.execute(context)

            # Emit result as streaming content
            yield emitter.emit_agent_stream(
                agent=self.agent_id,
                content=str(result),
                content_type="text"
            )

            # Emit agent completed
            yield emitter.emit_agent_completed(
                agent=self.agent_id,
                step=step,
                output=result
            )

        except Exception as e:
            self.logger.error("agent_execution_error", agent_id=self.agent_id, error=str(e))
            yield emitter.emit_agent_error(
                agent=self.agent_id,
                step=step,
                error_type=type(e).__name__,
                error_message=str(e)
            )

    async def query(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream responses from Claude SDK for a given task.

        Args:
            task: Task description for the agent
            context: Optional context for the task

        Yields:
            Response chunks from Claude SDK

        Example:
            async for chunk in agent.query("Analyze account ACC-001"):
                if chunk.get("type") == "text":
                    print(chunk.get("content"))
        """
        if not self.client:
            self._initialize_client()

        # Build full task with context
        full_context = context or {}
        full_context.update({
            "agent_id": self.agent_id,
            "session_id": self.session_id,
        })

        # Stream responses from Claude SDK
        async for chunk in self.client.query(task):
            yield chunk

    async def on_session_start(self) -> None:
        """Handle session start event.

        Calls session_start hook if available.
        """
        if "on_session_start" in self.hooks:
            context = {
                "agent_id": self.agent_id,
                "session_id": self.session_id,
            }
            await self.hooks["on_session_start"](context)

    async def on_session_end(self) -> None:
        """Handle session end event.

        Calls session_end hook if available.
        """
        if "on_session_end" in self.hooks:
            context = {
                "agent_id": self.agent_id,
                "session_id": self.session_id,
            }
            await self.hooks["on_session_end"](context)

    async def initialize(self) -> None:
        """Initialize agent resources and start session.

        Call this before using the agent to ensure proper setup.
        """
        # Initialize Claude SDK client if not already done
        if not self.client:
            self._initialize_client()

        # Generate session ID
        from datetime import datetime
        self.session_id = f"{self.agent_id}-{datetime.utcnow().isoformat()}"

        # Trigger session start hook
        await self.on_session_start()

        self.logger.info(
            "agent_session_started",
            session_id=self.session_id,
        )

    async def cleanup(self) -> None:
        """Cleanup agent resources and end session.

        Call this when done with the agent to ensure proper cleanup.
        """
        # Trigger session end hook
        await self.on_session_end()

        self.logger.info(
            "agent_session_ended",
            session_id=self.session_id,
        )

        # Clear session ID
        self.session_id = None

    def __repr__(self) -> str:
        """String representation of agent.

        Returns:
            Human-readable agent description
        """
        return (
            f"<{self.__class__.__name__} "
            f"agent_id={self.agent_id} "
            f"tools={len(self.allowed_tools)} "
            f"mode={self.permission_mode}>"
        )
