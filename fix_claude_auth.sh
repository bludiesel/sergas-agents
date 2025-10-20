#!/bin/bash
# Run this EVERY TIME before using Claude Code
# This unsets the API keys that block your subscription

unset ANTHROPIC_API_KEY
unset ANTHROPIC_BASE_URL

echo "✅ Unset ANTHROPIC_API_KEY and ANTHROPIC_BASE_URL"
echo "Claude Code should now use your Max subscription"
echo ""
echo "Run Claude Code in THIS SAME TERMINAL SESSION"
