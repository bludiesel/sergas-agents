#!/usr/bin/env python3
"""Test script to verify application authentication configuration.

This script verifies that:
1. Application loads both .env and .env.local
2. .env.local overrides take precedence
3. GLM-4.6 configuration is active for the application
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Simulate the application's environment loading
print("🔍 Testing Application Authentication Configuration\n")

# Load .env first (base configuration)
print("1️⃣ Loading .env (base configuration)...")
load_dotenv()
env_base_url = os.getenv('ANTHROPIC_BASE_URL')
env_model = os.getenv('CLAUDE_MODEL')
print(f"   ANTHROPIC_BASE_URL: {env_base_url or '(not set)'}")
print(f"   CLAUDE_MODEL: {env_model or '(not set)'}")

# Load .env.local (application overrides)
print("\n2️⃣ Loading .env.local (application overrides)...")
load_dotenv('.env.local', override=True)
local_base_url = os.getenv('ANTHROPIC_BASE_URL')
local_api_key = os.getenv('ANTHROPIC_API_KEY')
local_model = os.getenv('CLAUDE_MODEL')

print(f"   ANTHROPIC_BASE_URL: {local_base_url or '(not set)'}")
print(f"   ANTHROPIC_API_KEY: {local_api_key[:20] + '...' if local_api_key else '(not set)'}")
print(f"   CLAUDE_MODEL: {local_model or '(not set)'}")

# Verify configuration
print("\n" + "="*60)
print("📊 Configuration Verification")
print("="*60)

success = True

# Check if GLM-4.6 is configured
if local_base_url == "https://api.z.ai/api/anthropic":
    print("✅ ANTHROPIC_BASE_URL points to Z.ai")
else:
    print(f"❌ ANTHROPIC_BASE_URL expected Z.ai, got: {local_base_url}")
    success = False

if local_api_key and len(local_api_key) > 20:
    print("✅ ANTHROPIC_API_KEY is set")
else:
    print("❌ ANTHROPIC_API_KEY is not set or invalid")
    success = False

if local_model == "glm-4.6":
    print("✅ CLAUDE_MODEL is set to glm-4.6")
else:
    print(f"❌ CLAUDE_MODEL expected glm-4.6, got: {local_model}")
    success = False

# Summary
print("\n" + "="*60)
if success:
    print("✅ Application Configuration: CORRECT")
    print("\nYour application will use:")
    print("  - Provider: Z.ai")
    print("  - Model: GLM-4.6")
    print("  - Cost: ~$3/month")
    print("\nClaude Code will use:")
    print("  - Provider: Anthropic (Max subscription)")
    print("  - Model: Claude 3.5 Sonnet")
    print("  - Cost: Included in $200/month subscription")
else:
    print("❌ Application Configuration: NEEDS FIXING")
    print("\nRun: ./scripts/check_auth_config.sh for guidance")

print("="*60)

sys.exit(0 if success else 1)
