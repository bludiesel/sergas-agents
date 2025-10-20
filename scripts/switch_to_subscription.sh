#!/bin/bash
# Switch Claude Code to use Max subscription

echo "🔄 Switching to Max Subscription..."

# Unset all ANTHROPIC variables
unset ANTHROPIC_AUTH_TOKEN
unset ANTHROPIC_API_KEY
unset ANTHROPIC_BASE_URL
unset ANTHROPIC_DEFAULT_SONNET_MODEL
unset ANTHROPIC_DEFAULT_HAIKU_MODEL
unset ANTHROPIC_DEFAULT_OPUS_MODEL

echo "✅ Cleared all ANTHROPIC environment variables"
echo ""
echo "📝 Now start Claude Code in THIS SAME TERMINAL:"
echo "   cd $(pwd)"
echo "   claude"
echo ""
echo "💰 Claude Code will use your Max subscription ($200/month)"
echo ""
echo "⚠️  Note: Your Python app will still use .env.local for GLM-4.6"
