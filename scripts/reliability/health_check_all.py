#!/usr/bin/env python3
"""
Comprehensive health check script for all system components.

Usage:
    python scripts/reliability/health_check_all.py
    python scripts/reliability/health_check_all.py --verbose
    python scripts/reliability/health_check_all.py --json
"""

import asyncio
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.reliability.health_checks import (
    HealthCheckRegistry,
    ServiceHealthCheck,
    DatabaseHealthCheck,
    CacheHealthCheck,
    DependencyHealthCheck,
    HealthStatus,
)


async def create_health_checks(registry: HealthCheckRegistry, config: dict):
    """
    Create and register all health checks.

    Args:
        registry: Health check registry
        config: Configuration dictionary
    """
    # Database health check
    if config.get("database", {}).get("enabled", True):
        db_check = DatabaseHealthCheck(
            name="database_primary",
            connection_string=config.get("database", {}).get(
                "connection_string",
                "postgresql://user:pass@localhost/sergas"
            ),
            max_connections=20
        )
        registry.register(db_check)

    # Cache health check (Redis)
    if config.get("cache", {}).get("enabled", True):
        cache_check = CacheHealthCheck(
            name="redis_cache",
            redis_url=config.get("cache", {}).get(
                "redis_url",
                "redis://localhost:6379/0"
            )
        )
        registry.register(cache_check)

    # Service health checks
    services = config.get("services", {})
    for service_name, service_config in services.items():
        if service_config.get("enabled", True):
            service_check = ServiceHealthCheck(
                name=service_name,
                service_url=service_config.get("url")
            )
            registry.register(service_check)

    # External dependency checks
    dependencies = config.get("dependencies", {})
    for dep_name, dep_config in dependencies.items():
        if dep_config.get("enabled", True):
            dep_check = DependencyHealthCheck(
                name=dep_name,
                endpoint=dep_config.get("endpoint"),
                expected_status=dep_config.get("expected_status", 200),
                timeout=dep_config.get("timeout", 10.0)
            )
            registry.register(dep_check)


def print_results(summary: dict, verbose: bool = False):
    """
    Print health check results in human-readable format.

    Args:
        summary: Health check summary
        verbose: Include detailed information
    """
    # Color codes
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"

    # Overall status
    status = summary["status"]
    if status == "healthy":
        status_color = GREEN
        status_symbol = "✓"
    elif status == "degraded":
        status_color = YELLOW
        status_symbol = "⚠"
    else:
        status_color = RED
        status_symbol = "✗"

    print(f"\n{status_color}{'='*60}{RESET}")
    print(f"{status_color}{status_symbol} Overall System Health: {status.upper()}{RESET}")
    print(f"{status_color}{'='*60}{RESET}\n")

    # Statistics
    print(f"Total Checks: {summary['total_checks']}")
    print(f"{GREEN}✓ Healthy: {summary['healthy']}{RESET}")
    print(f"{YELLOW}⚠ Degraded: {summary['degraded']}{RESET}")
    print(f"{RED}✗ Unhealthy: {summary['unhealthy']}{RESET}")
    print(f"Timestamp: {summary['timestamp']}\n")

    # Individual check results
    if verbose:
        print(f"{'='*60}")
        print("Detailed Check Results:")
        print(f"{'='*60}\n")

        for check_name, check_result in summary["checks"].items():
            status = check_result["status"]

            if status == "healthy":
                color = GREEN
                symbol = "✓"
            elif status == "degraded":
                color = YELLOW
                symbol = "⚠"
            else:
                color = RED
                symbol = "✗"

            print(f"{color}{symbol} {check_name}{RESET}")
            print(f"  Status: {status}")
            print(f"  Response Time: {check_result['response_time_ms']:.2f}ms")

            if check_result.get("error"):
                print(f"  {RED}Error: {check_result['error']}{RESET}")

            if verbose and check_result.get("details"):
                print(f"  Details:")
                for key, value in check_result["details"].items():
                    print(f"    {key}: {value}")

            print()


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive health checks on all system components"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed information"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file"
    )

    args = parser.parse_args()

    # Load configuration
    config = {
        "database": {
            "enabled": True,
            "connection_string": "postgresql://sergas:password@localhost/sergas_db"
        },
        "cache": {
            "enabled": True,
            "redis_url": "redis://localhost:6379/0"
        },
        "services": {
            "api_server": {
                "enabled": True,
                "url": "http://localhost:8000"
            },
            "auth_service": {
                "enabled": True,
                "url": "http://localhost:8001"
            }
        },
        "dependencies": {
            "zoho_crm": {
                "enabled": True,
                "endpoint": "https://www.zohoapis.com/crm/v2/",
                "timeout": 10.0
            }
        }
    }

    if args.config and args.config.exists():
        with open(args.config) as f:
            config = json.load(f)

    # Create registry and add checks
    registry = HealthCheckRegistry()
    await create_health_checks(registry, config)

    # Run health checks
    print("Running health checks...")
    results = await registry.check_all()
    summary = registry.get_summary(results)

    # Output results
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print_results(summary, verbose=args.verbose)

    # Exit with appropriate code
    if summary["status"] == "healthy":
        sys.exit(0)
    elif summary["status"] == "degraded":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
