#!/usr/bin/env python3
"""
Environment check script for Week 1 validation.
Run this before running the full test suite to verify basic setup.
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """Check Python version."""
    print("Checking Python version...")
    version = sys.version_info
    print(f"  Found: Python {version.major}.{version.minor}.{version.micro}")

    if version >= (3, 10):
        print("  ✅ Python 3.10+ requirement met")
        return True
    else:
        print(f"  ❌ Python 3.10+ required, found {version.major}.{version.minor}")
        return False


def check_dependencies():
    """Check if key dependencies can be imported."""
    print("\nChecking key dependencies...")

    dependencies = {
        'pydantic': 'Pydantic (Data validation)',
        'pytest': 'Pytest (Testing framework)',
        'fastapi': 'FastAPI (API framework)',
        'sqlalchemy': 'SQLAlchemy (Database ORM)',
        'redis': 'Redis (Caching)',
        'requests': 'Requests (HTTP client)',
        'aiohttp': 'aiohttp (Async HTTP)',
        'httpx': 'HTTPX (Modern HTTP client)',
        'structlog': 'Structlog (Logging)',
        'boto3': 'Boto3 (AWS SDK)',
    }

    results = {}
    for module, description in dependencies.items():
        try:
            __import__(module)
            print(f"  ✅ {description}")
            results[module] = True
        except ImportError:
            print(f"  ❌ {description} - NOT INSTALLED")
            results[module] = False

    return all(results.values())


def check_project_structure():
    """Check project directory structure."""
    print("\nChecking project structure...")

    project_root = Path(__file__).parent.parent
    required_dirs = [
        'src',
        'src/agents',
        'src/integrations',
        'src/models',
        'src/hooks',
        'src/utils',
        'tests',
        'tests/unit',
        'tests/integration',
        'docs',
        'config',
        'scripts'
    ]

    all_present = True
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.is_dir():
            print(f"  ✅ {dir_path}/")
        else:
            print(f"  ❌ {dir_path}/ - MISSING")
            all_present = False

    return all_present


def check_config_files():
    """Check configuration files."""
    print("\nChecking configuration files...")

    project_root = Path(__file__).parent.parent
    required_files = [
        'pyproject.toml',
        'requirements.txt',
        '.env.example',
        '.gitignore'
    ]

    all_present = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.is_file():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - MISSING")
            all_present = False

    return all_present


def check_git():
    """Check git repository."""
    print("\nChecking git repository...")

    project_root = Path(__file__).parent.parent
    git_dir = project_root / '.git'

    if git_dir.is_dir():
        print("  ✅ Git repository initialized")
        return True
    else:
        print("  ❌ Git repository not initialized")
        return False


def main():
    """Run all environment checks."""
    print("="*70)
    print("Week 1 Environment Validation")
    print("="*70)

    checks = {
        'Python Version': check_python_version(),
        'Dependencies': check_dependencies(),
        'Project Structure': check_project_structure(),
        'Configuration Files': check_config_files(),
        'Git Repository': check_git()
    }

    print("\n" + "="*70)
    print("Summary")
    print("="*70)

    for check_name, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name}: {status}")

    all_passed = all(checks.values())

    print("\n" + "="*70)
    if all_passed:
        print("✅ All checks passed! Environment ready for Week 1 tests.")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Run tests: python3 -m pytest tests/ -v")
        print("  3. Run validation: ./scripts/run_week1_validation.sh")
    else:
        print("❌ Some checks failed. Please address issues above.")
        print("\nRecommended actions:")
        if not checks['Python Version']:
            print("  - Install Python 3.10 or higher")
        if not checks['Dependencies']:
            print("  - Run: pip install -r requirements.txt")
        if not checks['Project Structure']:
            print("  - Create missing directories")
        if not checks['Configuration Files']:
            print("  - Create missing configuration files")
        if not checks['Git Repository']:
            print("  - Initialize: git init")

    print("="*70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
