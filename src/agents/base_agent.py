"""Base agent class using Claude SDK Client."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from claude_agent_sdk import ClaudeSDKClient
import structlog

logger = structlog.get_logger()


class BaseAgent(ABC):
    """Base class for all agents in the system."""

    def __init__(
        self,
        name: str,
        system_prompt: str,
        allowed_tools: list[str],
        **kwargs: Any
    ) -> None:
        """Initialize base agent.

        Args:
            name: Agent identifier
            system_prompt: System prompt for the agent
            allowed_tools: List of allowed tool names
            **kwargs: Additional configuration
        """
        self.name = name
        self.system_prompt = system_prompt
        self.allowed_tools = allowed_tools
        self.client: Optional[ClaudeSDKClient] = None
        self.logger = logger.bind(agent=name)

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent task.

        Args:
            context: Execution context with input data

        Returns:
            Results dictionary
        """
        pass

    async def initialize(self) -> None:
        """Initialize agent resources."""
        self.logger.info("agent_initialized", name=self.name)
