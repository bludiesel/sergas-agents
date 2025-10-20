#!/bin/bash
# Switch Claude Code to use GLM-4.6 via Z.ai

echo "🔄 Switching to GLM-4.6 via Z.ai..."

# Export environment variables for current session
export ANTHROPIC_AUTH_TOKEN="6845ef1767204ea98a67faaecb3afe08.fyZ4DweXVe3SvCXS"
export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"
export ANTHROPIC_DEFAULT_SONNET_MODEL="glm-4.6"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="glm-4.5-air"
export ANTHROPIC_DEFAULT_OPUS_MODEL="glm-4.6"

echo "✅ Environment variables set:"
echo "   ANTHROPIC_AUTH_TOKEN: ${ANTHROPIC_AUTH_TOKEN:0:20}..."
echo "   ANTHROPIC_BASE_URL: $ANTHROPIC_BASE_URL"
echo "   ANTHROPIC_DEFAULT_SONNET_MODEL: $ANTHROPIC_DEFAULT_SONNET_MODEL"
echo ""
echo "📝 Now start Claude Code in THIS SAME TERMINAL:"
echo "   cd $(pwd)"
echo "   claude"
echo ""
echo "💡 To make this permanent, add these exports to ~/.bashrc or ~/.zshrc"
