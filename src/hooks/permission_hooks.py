"""Permission hook implementation for access control and validation.

Part of Week 6: Base Agent Infrastructure - Hook System.
"""

import structlog
from typing import Dict, Any, List, Optional

logger = structlog.get_logger(__name__)


class PermissionError(Exception):
    """Raised when permission check fails."""

    pass


class PermissionHook:
    """Permission enforcement and validation for agent actions."""

    def __init__(self):
        """Initialize permission hook."""
        self.logger = logger

    async def check_tool_permission(
        self, tool_name: str, tool_input: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """Check if tool execution is permitted.

        Args:
            tool_name: Name of the tool to check
            tool_input: Input parameters for the tool
            context: Execution context with allowed_tools, permission_mode, etc.

        Returns:
            True if permitted

        Raises:
            PermissionError: If tool is not allowed
        """
        permission_mode = context.get("permission_mode", "default")
        allowed_tools = context.get("allowed_tools", [])

        # Log permission check
        self.logger.info(
            "permission_check",
            tool_name=tool_name,
            permission_mode=permission_mode,
            agent_id=context.get("agent_id"),
        )

        # BypassPermissions mode: allow all
        if permission_mode == "bypassPermissions":
            self.logger.info(
                "permission_bypassed",
                tool_name=tool_name,
                reason="bypassPermissions mode enabled",
            )
            return True

        # Check if tool is in allowed list
        if tool_name not in allowed_tools:
            self.logger.warning(
                "permission_denied",
                tool_name=tool_name,
                allowed_tools=allowed_tools,
            )
            raise PermissionError(
                f"Tool '{tool_name}' not allowed. Allowed tools: {allowed_tools}"
            )

        # Validate tool input schema if provided
        tool_schemas = context.get("tool_schemas", {})
        if tool_name in tool_schemas:
            self._validate_tool_input(tool_name, tool_input, tool_schemas[tool_name])

        self.logger.info("permission_granted", tool_name=tool_name)
        return True

    async def check_mcp_server_access(
        self, server_name: str, context: Dict[str, Any]
    ) -> bool:
        """Check if MCP server access is permitted.

        Args:
            server_name: Name of MCP server
            context: Execution context

        Returns:
            True if permitted

        Raises:
            PermissionError: If access is denied
        """
        allowed_servers = context.get("allowed_mcp_servers", [])

        # Allow all if not specified
        if not allowed_servers:
            return True

        if server_name not in allowed_servers:
            self.logger.warning(
                "mcp_server_access_denied",
                server_name=server_name,
                allowed_servers=allowed_servers,
            )
            raise PermissionError(
                f"MCP server '{server_name}' not allowed. Allowed: {allowed_servers}"
            )

        return True

    async def check_write_operation(
        self, operation: str, resource: str, context: Dict[str, Any]
    ) -> bool:
        """Check if write operation is permitted.

        Args:
            operation: Type of write operation (create, update, delete)
            resource: Resource being modified
            context: Execution context

        Returns:
            True if permitted (may require approval)

        Raises:
            PermissionError: If operation is blocked
        """
        # Plan mode: block all writes
        if context.get("permission_mode") == "plan":
            self.logger.warning(
                "write_blocked_plan_mode",
                operation=operation,
                resource=resource,
            )
            raise PermissionError(
                f"Write operation '{operation}' blocked in plan mode"
            )

        # Check if approval is required for this resource
        requires_approval = context.get("requires_approval", True)

        if requires_approval:
            self.logger.info(
                "write_requires_approval",
                operation=operation,
                resource=resource,
            )
            # Return True but caller must handle approval workflow
            return True

        return True

    def _validate_tool_input(
        self, tool_name: str, tool_input: Dict[str, Any], schema: Dict[str, Any]
    ) -> None:
        """Validate tool input against schema.

        Args:
            tool_name: Tool name (for error messages)
            tool_input: Input to validate
            schema: JSON schema to validate against

        Raises:
            ValueError: If validation fails
        """
        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in tool_input:
                self.logger.error(
                    "validation_failed",
                    tool_name=tool_name,
                    missing_field=field,
                )
                raise ValueError(f"Missing required field: {field}")

        # Validate field types
        properties = schema.get("properties", {})
        for field, value in tool_input.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type:
                    actual_type = self._get_json_type(value)
                    if actual_type != expected_type:
                        self.logger.error(
                            "type_validation_failed",
                            tool_name=tool_name,
                            field=field,
                            expected=expected_type,
                            actual=actual_type,
                        )
                        raise ValueError(
                            f"Field '{field}' must be {expected_type}, got {actual_type}"
                        )

    @staticmethod
    def _get_json_type(value: Any) -> str:
        """Get JSON type name for Python value.

        Args:
            value: Python value

        Returns:
            JSON type name (string, number, boolean, array, object, null)
        """
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int) or isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return "unknown"


class PermissionManager:
    """Manage permission policies and rules."""

    def __init__(self):
        """Initialize permission manager."""
        self.policies: Dict[str, Dict[str, Any]] = {}

    def register_policy(
        self, policy_name: str, allowed_tools: List[str], config: Optional[Dict] = None
    ) -> None:
        """Register a permission policy.

        Args:
            policy_name: Policy identifier
            allowed_tools: List of allowed tools
            config: Additional configuration
        """
        self.policies[policy_name] = {
            "allowed_tools": allowed_tools,
            "config": config or {},
        }

    def get_policy(self, policy_name: str) -> Optional[Dict[str, Any]]:
        """Get permission policy by name.

        Args:
            policy_name: Policy identifier

        Returns:
            Policy configuration or None
        """
        return self.policies.get(policy_name)
