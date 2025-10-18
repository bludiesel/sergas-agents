#!/usr/bin/env python3
"""
Memory Manager Utility

Helper script for Claude Flow memory namespace management and operations.
"""

import json
import subprocess
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


class MemoryManager:
    """Helper class for Claude Flow memory management."""

    def __init__(self):
        self.mcp_prefix = "mcp__claude-flow__"

    def store(
        self,
        key: str,
        value: Any,
        namespace: str = "default",
        ttl: Optional[int] = None
    ) -> Dict:
        """
        Store value in memory with optional TTL.

        Args:
            key: Memory key
            value: Value to store (will be JSON serialized if not string)
            namespace: Namespace for organization
            ttl: Time-to-live in seconds (None = no expiration)

        Returns:
            Storage result
        """
        # Convert value to string if needed
        if not isinstance(value, str):
            value = json.dumps(value)

        params = {
            "action": "store",
            "key": key,
            "value": value,
            "namespace": namespace
        }

        if ttl is not None:
            params["ttl"] = ttl

        return self._call_memory_tool(params)

    def retrieve(self, key: str, namespace: str = "default") -> Dict:
        """
        Retrieve value from memory.

        Args:
            key: Memory key
            namespace: Namespace to search

        Returns:
            Retrieved value
        """
        params = {
            "action": "retrieve",
            "key": key,
            "namespace": namespace
        }

        return self._call_memory_tool(params)

    def list_keys(self, namespace: str = "default") -> List[str]:
        """
        List all keys in a namespace.

        Args:
            namespace: Namespace to list

        Returns:
            List of keys
        """
        params = {
            "action": "list",
            "namespace": namespace
        }

        result = self._call_memory_tool(params)
        return result.get("keys", [])

    def delete(self, key: str, namespace: str = "default") -> Dict:
        """
        Delete a key from memory.

        Args:
            key: Key to delete
            namespace: Namespace

        Returns:
            Deletion result
        """
        params = {
            "action": "delete",
            "key": key,
            "namespace": namespace
        }

        return self._call_memory_tool(params)

    def search(
        self,
        pattern: str,
        namespace: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search memory with pattern matching.

        Args:
            pattern: Search pattern (supports wildcards)
            namespace: Optional namespace filter
            limit: Maximum results

        Returns:
            List of matching entries
        """
        cmd = [
            "npx", "claude-flow@alpha", "mcp", "call",
            f"{self.mcp_prefix}memory_search",
            "--params", json.dumps({
                "pattern": pattern,
                "namespace": namespace,
                "limit": limit
            })
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return self._parse_result(result)

    def backup(self, path: Optional[str] = None) -> Dict:
        """Create backup of memory stores."""
        params = {}
        if path:
            params["path"] = path

        cmd = [
            "npx", "claude-flow@alpha", "mcp", "call",
            f"{self.mcp_prefix}memory_backup",
            "--params", json.dumps(params)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return self._parse_result(result)

    def restore(self, backup_path: str) -> Dict:
        """Restore memory from backup."""
        cmd = [
            "npx", "claude-flow@alpha", "mcp", "call",
            f"{self.mcp_prefix}memory_restore",
            "--params", json.dumps({"backupPath": backup_path})
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return self._parse_result(result)

    def _call_memory_tool(self, params: Dict) -> Dict:
        """Call memory_usage MCP tool."""
        cmd = [
            "npx", "claude-flow@alpha", "mcp", "call",
            f"{self.mcp_prefix}memory_usage",
            "--params", json.dumps(params)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return self._parse_result(result)

    def _parse_result(self, result: subprocess.CompletedProcess) -> Dict:
        """Parse subprocess result."""
        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr
            }

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {
                "success": True,
                "output": result.stdout
            }


# Common TTL values (in seconds)
TTL_1_HOUR = 3600
TTL_1_DAY = 86400
TTL_1_WEEK = 604800
TTL_1_MONTH = 2592000


def store_decision(
    decision_name: str,
    decision_value: str,
    rationale: str,
    ttl: int = TTL_1_MONTH
) -> Dict:
    """
    Store a project decision with context.

    Args:
        decision_name: Name/key for the decision
        decision_value: The decision made
        rationale: Why this decision was made
        ttl: How long to keep (default: 30 days)
    """
    mm = MemoryManager()

    decision_data = {
        "decision": decision_value,
        "rationale": rationale,
        "timestamp": datetime.now().isoformat(),
        "expires": (datetime.now() + timedelta(seconds=ttl)).isoformat()
    }

    return mm.store(
        key=decision_name,
        value=decision_data,
        namespace="project/decisions",
        ttl=ttl
    )


def store_agent_finding(
    agent_name: str,
    finding: str,
    severity: str = "info",
    ttl: int = TTL_1_WEEK
) -> Dict:
    """
    Store an agent's finding or observation.

    Args:
        agent_name: Name of the agent
        finding: The finding or observation
        severity: "info" | "warning" | "error" | "critical"
        ttl: How long to keep (default: 7 days)
    """
    mm = MemoryManager()

    finding_data = {
        "agent": agent_name,
        "finding": finding,
        "severity": severity,
        "timestamp": datetime.now().isoformat()
    }

    key = f"{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    return mm.store(
        key=key,
        value=finding_data,
        namespace="swarm/findings",
        ttl=ttl
    )


def get_all_decisions() -> List[Dict]:
    """Retrieve all stored project decisions."""
    mm = MemoryManager()
    return mm.search(pattern="*", namespace="project/decisions", limit=100)


def get_recent_findings(limit: int = 20) -> List[Dict]:
    """Retrieve recent agent findings."""
    mm = MemoryManager()
    return mm.search(pattern="*", namespace="swarm/findings", limit=limit)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python memory_manager.py store <key> <value> [namespace] [ttl]")
        print("  python memory_manager.py retrieve <key> [namespace]")
        print("  python memory_manager.py list [namespace]")
        print("  python memory_manager.py search <pattern> [namespace] [limit]")
        print("  python memory_manager.py decision <name> <value> <rationale>")
        print("  python memory_manager.py finding <agent> <finding> [severity]")
        sys.exit(1)

    mm = MemoryManager()
    command = sys.argv[1]

    if command == "store":
        key = sys.argv[2]
        value = sys.argv[3]
        namespace = sys.argv[4] if len(sys.argv) > 4 else "default"
        ttl = int(sys.argv[5]) if len(sys.argv) > 5 else None
        result = mm.store(key, value, namespace, ttl)
        print(json.dumps(result, indent=2))

    elif command == "retrieve":
        key = sys.argv[2]
        namespace = sys.argv[3] if len(sys.argv) > 3 else "default"
        result = mm.retrieve(key, namespace)
        print(json.dumps(result, indent=2))

    elif command == "list":
        namespace = sys.argv[2] if len(sys.argv) > 2 else "default"
        keys = mm.list_keys(namespace)
        print(f"Keys in '{namespace}':")
        for key in keys:
            print(f"  - {key}")

    elif command == "search":
        pattern = sys.argv[2]
        namespace = sys.argv[3] if len(sys.argv) > 3 else None
        limit = int(sys.argv[4]) if len(sys.argv) > 4 else 10
        results = mm.search(pattern, namespace, limit)
        print(json.dumps(results, indent=2))

    elif command == "decision":
        name = sys.argv[2]
        value = sys.argv[3]
        rationale = sys.argv[4]
        result = store_decision(name, value, rationale)
        print(f"Decision stored: {name}")
        print(json.dumps(result, indent=2))

    elif command == "finding":
        agent = sys.argv[2]
        finding = sys.argv[3]
        severity = sys.argv[4] if len(sys.argv) > 4 else "info"
        result = store_agent_finding(agent, finding, severity)
        print(f"Finding stored from {agent}")
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
