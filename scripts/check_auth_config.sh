#!/bin/bash
# Authentication Configuration Checker
# Prevents Claude Code subscription from being overridden by API keys

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "🔍 Checking authentication configuration..."
echo ""

WARNINGS=0

# Check if ANTHROPIC_API_KEY is set in environment
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}⚠️  WARNING: ANTHROPIC_API_KEY is set in your environment!${NC}"
    echo "   Claude Code will use this API key instead of your subscription."
    echo "   This means:"
    echo "   - Usage will be billed to API (pay-per-token)"
    echo "   - Your Max subscription quota will NOT be used"
    echo ""
    echo "   To use your Max subscription, unset this variable:"
    echo -e "   ${YELLOW}unset ANTHROPIC_API_KEY${NC}"
    echo ""
    WARNINGS=$((WARNINGS + 1))
fi

# Check if ANTHROPIC_BASE_URL is set
if [ -n "$ANTHROPIC_BASE_URL" ]; then
    echo -e "${RED}⚠️  WARNING: ANTHROPIC_BASE_URL is set!${NC}"
    echo "   Current value: $ANTHROPIC_BASE_URL"
    echo "   This routes requests to a custom endpoint."
    echo ""
    if [[ "$ANTHROPIC_BASE_URL" == *"z.ai"* ]]; then
        echo "   Detected: Z.ai endpoint (GLM-4.6)"
        echo "   Claude Code will use GLM-4.6 instead of Claude models."
    fi
    echo ""
    echo "   To use official Anthropic API, unset this variable:"
    echo -e "   ${YELLOW}unset ANTHROPIC_BASE_URL${NC}"
    echo ""
    WARNINGS=$((WARNINGS + 1))
fi

# Check .env file
if [ -f ".env" ]; then
    if grep -q "^ANTHROPIC_API_KEY=" .env 2>/dev/null; then
        echo -e "${RED}⚠️  WARNING: .env contains active ANTHROPIC_API_KEY!${NC}"
        echo "   This may override Claude Code's subscription authentication."
        echo ""
        echo "   Recommendations:"
        echo "   1. Comment out the line with # in .env"
        echo "   2. Move API keys to a separate .env.app file"
        echo "   3. Use .env.claude-code for Claude Code settings only"
        echo ""
        WARNINGS=$((WARNINGS + 1))
    fi

    if grep -q "^ANTHROPIC_BASE_URL=" .env 2>/dev/null; then
        echo -e "${RED}⚠️  WARNING: .env contains active ANTHROPIC_BASE_URL!${NC}"
        echo "   This will route Claude Code requests to a custom endpoint."
        echo ""
        echo "   To use your subscription, comment out this line in .env"
        echo ""
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# Check if .env.claude-code exists (recommended)
if [ ! -f ".env.claude-code" ]; then
    echo -e "${YELLOW}ℹ️  INFO: .env.claude-code not found${NC}"
    echo "   Recommendation: Create a separate config file for Claude Code"
    echo "   This prevents conflicts with application API keys."
    echo ""
    echo "   Create it with:"
    echo -e "   ${YELLOW}touch .env.claude-code${NC}"
    echo ""
fi

# Check for API keys in common shell profiles
for profile in ~/.bashrc ~/.zshrc ~/.bash_profile ~/.profile; do
    if [ -f "$profile" ] && grep -q "ANTHROPIC_API_KEY" "$profile" 2>/dev/null; then
        echo -e "${RED}⚠️  WARNING: ANTHROPIC_API_KEY found in $profile${NC}"
        echo "   This sets the API key globally for all terminal sessions!"
        echo "   Claude Code will NEVER use your subscription while this is set."
        echo ""
        echo "   Remove it from $profile to use subscription."
        echo ""
        WARNINGS=$((WARNINGS + 1))
    fi
done

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ Authentication configuration looks good!${NC}"
    echo "   Claude Code will use your Max subscription."
    echo ""
    echo "   Current mode: Subscription OAuth"
    echo "   Billing: Included in your $200/month Max plan"
    echo "   Rate limits: Max tier (20x higher than Pro)"
    exit 0
else
    echo -e "${RED}❌ Found $WARNINGS authentication issue(s)!${NC}"
    echo ""
    echo "   Current mode: API Key (or custom endpoint)"
    echo "   Billing: Pay-per-token API charges"
    echo ""
    echo "   Fix these issues to use your Max subscription."
    echo ""
    echo "   Quick fix (temporary):"
    echo -e "   ${YELLOW}unset ANTHROPIC_API_KEY ANTHROPIC_BASE_URL${NC}"
    echo ""
    echo "   Permanent fix:"
    echo "   1. Comment out ANTHROPIC_* variables in .env"
    echo "   2. Remove from shell profile files"
    echo "   3. Restart your terminal"
    echo ""
    exit 1
fi
