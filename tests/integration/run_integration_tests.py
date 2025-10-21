#!/usr/bin/env python3
"""
Integration Test Runner

This script provides a comprehensive runner for the integration tests,
including environment setup, test execution, and reporting.
"""

import os
import sys
import argparse
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def setup_environment():
    """Setup test environment"""
    print("🔧 Setting up test environment...")

    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)

    # Check if required directories exist
    required_dirs = [
        "tests/integration",
        "src",
        "src/agents",
        "src/monitoring",
        "src/workflow",
        "src/zoho"
    ]

    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            print(f"❌ Required directory missing: {dir_path}")
            return False

    # Check if Python modules can be imported
    try:
        import sys
        sys.path.insert(0, str(Path("src")))

        # Try importing core modules
        from agents.orchestrator import EnhancedOrchestratorAgent
        from monitoring.enhanced_monitoring import EnhancedMonitoringSystem
        from workflow.enhanced_engine import EnhancedWorkflowEngine

        print("✅ Core modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import required modules: {e}")
        return False

    return True


def check_dependencies():
    """Check if required dependencies are installed"""
    print("📦 Checking dependencies...")

    required_packages = [
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "psutil",
        "aiohttp",
        "pydantic"
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package} (missing)")

    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r tests/integration/requirements.txt")
        return False

    return True


def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")

    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "-r", "tests/integration/requirements.txt"
        ], check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def run_test_suite(
    test_file: str = "full_system_integration_test.py",
    markers: Optional[List[str]] = None,
    verbose: bool = True,
    coverage: bool = True,
    parallel: bool = False,
    max_workers: int = 4
) -> Dict[str, Any]:
    """Run the integration test suite"""

    print(f"🚀 Running integration tests: {test_file}")

    # Build pytest command
    cmd = [
        sys.executable, "-m", "pytest",
        f"tests/integration/{test_file}",
        "-v" if verbose else "-q",
        "--tb=short",
        "--asyncio-mode=auto"
    ]

    # Add markers if specified
    if markers:
        for marker in markers:
            cmd.extend(["-m", marker])

    # Add coverage if requested
    if coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=html:tests/integration/coverage_html",
            "--cov-report=xml:tests/integration/coverage.xml",
            "--cov-report=term-missing"
        ])

    # Add parallel execution if requested
    if parallel:
        cmd.extend(["-n", str(max_workers)])

    # Add JSON reporting
    cmd.extend([
        "--json-report",
        "--json-report-file=tests/integration/test_report.json"
    ])

    # Add HTML reporting
    cmd.extend([
        "--html=tests/integration/test_report.html",
        "--self-contained-html"
    ])

    print(f"Command: {' '.join(cmd)}")

    # Run tests
    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )

        execution_time = time.time() - start_time

        # Parse results
        test_results = {
            "success": result.returncode == 0,
            "execution_time": execution_time,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }

        # Try to load JSON report if available
        try:
            with open("tests/integration/test_report.json", "r") as f:
                json_report = json.load(f)
                test_results.update({
                    "summary": json_report.get("summary", {}),
                    "tests": json_report.get("tests", [])
                })
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        return test_results

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "execution_time": time.time() - start_time
        }


def generate_test_report(results: Dict[str, Any]) -> str:
    """Generate a comprehensive test report"""

    report_lines = [
        "=" * 80,
        "INTEGRATION TEST REPORT",
        "=" * 80,
        f"Timestamp: {datetime.now().isoformat()}",
        f"Execution Time: {results.get('execution_time', 0):.2f} seconds",
        f"Status: {'✅ PASSED' if results.get('success', False) else '❌ FAILED'}",
        ""
    ]

    # Add summary if available
    if "summary" in results:
        summary = results["summary"]
        report_lines.extend([
            "SUMMARY:",
            f"  Total Tests: {summary.get('total', 0)}",
            f"  Passed: {summary.get('passed', 0)}",
            f"  Failed: {summary.get('failed', 0)}",
            f"  Skipped: {summary.get('skipped', 0)}",
            f"  Success Rate: {summary.get('passed', 0) / max(summary.get('total', 1), 1) * 100:.1f}%",
            ""
        ])

    # Add performance metrics if available
    if "tests" in results:
        performance_tests = [t for t in results["tests"] if "performance" in t.get("nodeid", "").lower()]

        if performance_tests:
            report_lines.extend([
                "PERFORMANCE TESTS:",
                ""
            ])

            for test in performance_tests:
                test_name = Path(test.get("nodeid", "")).name
                duration = test.get("duration", 0)
                outcome = test.get("outcome", "unknown")

                status_icon = "✅" if outcome == "passed" else "❌"
                report_lines.append(f"  {status_icon} {test_name}: {duration:.3f}s")

            report_lines.append("")

    # Add failed tests if any
    if results.get("return_code", 0) != 0:
        report_lines.extend([
            "FAILED TESTS OUTPUT:",
            "-" * 40,
            results.get("stderr", ""),
            "-" * 40,
            ""
        ])

    # Add recommendations
    report_lines.extend([
        "RECOMMENDATIONS:",
    ])

    if results.get("success", False):
        report_lines.extend([
            "  ✅ All integration tests passed",
            "  ✅ System is ready for production deployment",
            "  📊 Review performance metrics for optimization opportunities"
        ])
    else:
        report_lines.extend([
            "  ❌ Some tests failed - review the output above",
            "  🔧 Fix failing tests before production deployment",
            "  📋 Check system configuration and dependencies"
        ])

    report_lines.extend([
        "",
        "=" * 80
    ])

    return "\n".join(report_lines)


def save_test_report(report: str, results: Dict[str, Any]):
    """Save test report to file"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"tests/integration/reports/integration_report_{timestamp}.txt"

    # Create reports directory if it doesn't exist
    Path("tests/integration/reports").mkdir(parents=True, exist_ok=True)

    with open(report_file, "w") as f:
        f.write(report)

    # Save JSON results
    json_file = f"tests/integration/reports/integration_results_{timestamp}.json"
    with open(json_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"📄 Report saved to: {report_file}")
    print(f"📊 Results saved to: {json_file}")


def run_quick_health_check():
    """Run a quick health check of the system"""

    print("🏥 Running quick health check...")

    health_checks = [
        ("Environment Setup", setup_environment),
        ("Dependencies", check_dependencies),
    ]

    all_passed = True

    for check_name, check_func in health_checks:
        print(f"\n  Checking {check_name}...")
        if check_func():
            print(f"  ✅ {check_name} - OK")
        else:
            print(f"  ❌ {check_name} - FAILED")
            all_passed = False

    return all_passed


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(
        description="Run integration tests for SERGAS Agents system"
    )

    parser.add_argument(
        "--test-file",
        default="full_system_integration_test.py",
        help="Test file to run (default: full_system_integration_test.py)"
    )

    parser.add_argument(
        "--markers",
        nargs="*",
        help="Pytest markers to run (e.g., integration performance)"
    )

    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Disable code coverage reporting"
    )

    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)"
    )

    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install dependencies before running tests"
    )

    parser.add_argument(
        "--health-check-only",
        action="store_true",
        help="Run only health check without tests"
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Run tests with minimal output"
    )

    args = parser.parse_args()

    print("🧪 SERGAS Agents Integration Test Runner")
    print("=" * 50)

    # Run health check
    if not run_quick_health_check():
        if args.install_deps:
            print("\n🔧 Attempting to install dependencies...")
            if not install_dependencies():
                print("❌ Failed to install dependencies")
                sys.exit(1)
            print("✅ Dependencies installed, rechecking...")
            if not run_quick_health_check():
                print("❌ Health check still failing")
                sys.exit(1)
        else:
            print("❌ Health check failed. Use --install-deps to install missing dependencies.")
            sys.exit(1)

    if args.health_check_only:
        print("✅ Health check completed successfully")
        return

    # Run tests
    results = run_test_suite(
        test_file=args.test_file,
        markers=args.markers,
        verbose=not args.quiet,
        coverage=not args.no_coverage,
        parallel=args.parallel,
        max_workers=args.workers
    )

    # Generate and save report
    report = generate_test_report(results)
    print("\n" + report)

    save_test_report(report, results)

    # Exit with appropriate code
    sys.exit(0 if results.get("success", False) else 1)


if __name__ == "__main__":
    main()