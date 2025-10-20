#!/usr/bin/env python3
"""Test script to validate FastAPI startup with CopilotKit integration.

This script tests:
1. FastAPI application creation
2. CopilotKit integration (optional if API key not configured)
3. Endpoint registration
4. Basic API functionality

Usage:
    python scripts/test_fastapi_startup.py
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient


def test_app_startup():
    """Test FastAPI application startup."""
    print("=" * 70)
    print("Testing FastAPI Application Startup")
    print("=" * 70)

    # Import the app
    try:
        from src.main import app
        print("✓ FastAPI app imported successfully")
    except Exception as e:
        print(f"✗ Failed to import app: {e}")
        return False

    # Create test client
    try:
        client = TestClient(app)
        print("✓ Test client created successfully")
    except Exception as e:
        print(f"✗ Failed to create test client: {e}")
        return False

    # Test root endpoint
    try:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Root endpoint working: {data['service']}")
        print(f"  Endpoints: {data.get('endpoints', {})}")
    except Exception as e:
        print(f"✗ Root endpoint failed: {e}")
        return False

    # Test health endpoint
    try:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Health endpoint working: {data['status']}")
    except Exception as e:
        print(f"✗ Health endpoint failed: {e}")
        return False

    # Check OpenAPI docs
    try:
        response = client.get("/docs")
        assert response.status_code == 200
        print("✓ OpenAPI docs accessible")
    except Exception as e:
        print(f"✗ OpenAPI docs failed: {e}")
        return False

    # Check if CopilotKit endpoint is registered
    try:
        from src.main import copilotkit_integration
        if copilotkit_integration:
            print("✓ CopilotKit SDK integration configured")
            print(f"  Agents registered: {list(copilotkit_integration.agents.keys())}")
        else:
            print("⚠ CopilotKit SDK not configured (optional)")
    except Exception as e:
        print(f"⚠ CopilotKit check failed: {e}")

    print("\n" + "=" * 70)
    print("All tests passed! ✓")
    print("=" * 70)
    return True


def test_routes():
    """Test route registration."""
    print("\n" + "=" * 70)
    print("Testing Route Registration")
    print("=" * 70)

    try:
        from src.main import app
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(f"{','.join(route.methods) if hasattr(route, 'methods') else 'N/A'} {route.path}")

        print(f"\nRegistered routes ({len(routes)}):")
        for route in sorted(routes):
            print(f"  {route}")

        # Check for key endpoints
        paths = [route.split()[-1] for route in routes]

        required_paths = ["/", "/health"]
        for path in required_paths:
            if path in paths:
                print(f"✓ Required endpoint found: {path}")
            else:
                print(f"✗ Missing required endpoint: {path}")
                return False

        # Check for CopilotKit endpoint
        if "/copilotkit" in paths:
            print("✓ CopilotKit SDK endpoint registered: /copilotkit")
        else:
            print("⚠ CopilotKit SDK endpoint not registered (may not be configured)")

        # Check for AG UI Protocol endpoint
        if "/api/copilotkit" in paths:
            print("✓ AG UI Protocol endpoint registered: /api/copilotkit")
        else:
            print("⚠ AG UI Protocol endpoint not found")

        return True

    except Exception as e:
        print(f"✗ Route testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║       Sergas Account Manager - FastAPI Startup Test               ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print("\n")

    # Run tests
    startup_ok = test_app_startup()
    routes_ok = test_routes()

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"App Startup: {'✓ PASS' if startup_ok else '✗ FAIL'}")
    print(f"Route Registration: {'✓ PASS' if routes_ok else '✗ FAIL'}")

    if startup_ok and routes_ok:
        print("\n✓ All validation tests passed!")
        print("\nNext steps:")
        print("  1. Install CopilotKit SDK: pip install copilotkit")
        print("  2. Configure ANTHROPIC_API_KEY in .env")
        print("  3. Start server: uvicorn src.main:app --reload")
        print("  4. Access docs: http://localhost:8000/docs")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Please review errors above.")
        sys.exit(1)
