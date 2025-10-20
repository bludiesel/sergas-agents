#!/bin/bash
# CLI Demo Script - Week 8 Implementation
# Demonstrates all CLI features with example commands

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Sergas CLI Demo"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Activate virtual environment
source venv/bin/activate 2>/dev/null || source venv312/bin/activate 2>/dev/null || echo "Using system Python"

# 1. Show CLI version
echo "1️⃣  CLI Version:"
python -m src.cli.agent_cli --version
echo ""

# 2. Show help
echo "2️⃣  CLI Help:"
python -m src.cli.agent_cli --help
echo ""

# 3. Show analyze command help
echo "3️⃣  Analyze Command Help:"
python -m src.cli.agent_cli analyze --help
echo ""

# 4. Health check (optional - only if backend is running)
echo "4️⃣  Health Check (requires running backend):"
echo "   python -m src.cli.agent_cli health"
echo ""

# 5. Example analyze command (dry run - shows what would execute)
echo "5️⃣  Example Analyze Command (interactive):"
echo "   python -m src.cli.agent_cli analyze --account-id ACC-001"
echo ""

# 6. Example analyze with auto-approve
echo "6️⃣  Example Analyze with Auto-Approve:"
echo "   python -m src.cli.agent_cli analyze --account-id ACC-001 --auto-approve"
echo ""

# 7. Example verbose analysis
echo "7️⃣  Example Verbose Analysis:"
echo "   python -m src.cli.agent_cli analyze --account-id ACC-001 --verbose"
echo ""

# 8. Example custom API URL
echo "8️⃣  Example Custom API URL:"
echo "   python -m src.cli.agent_cli analyze --account-id ACC-001 --api-url https://api.production.com"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Demo Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To run a real analysis, ensure backend is running and execute:"
echo "  python -m src.cli.agent_cli analyze --account-id ACC-001"
echo ""
echo "For automation, use auto-approve:"
echo "  python -m src.cli.agent_cli analyze --account-id ACC-001 --auto-approve"
echo ""
