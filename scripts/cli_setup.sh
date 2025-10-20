#!/bin/bash
# Sergas CLI Setup Script
# Week 8 Implementation - CLI environment initialization

set -e  # Exit on error

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Sergas Account Manager CLI - Setup Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Detect shell
SHELL_NAME=$(basename "$SHELL")
echo "📋 Detected shell: $SHELL_NAME"
echo ""

# Check Python version
echo "🐍 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "   Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Python $PYTHON_VERSION detected"
echo ""

# Install CLI dependencies
echo "📦 Installing CLI dependencies..."
pip3 install -q click rich httpx 2>&1 | grep -v "already satisfied" || true
echo "✓ Dependencies installed:"
echo "  - click (command-line interface)"
echo "  - rich (terminal UI)"
echo "  - httpx (async HTTP client)"
echo ""

# Create CLI alias
echo "🔗 Creating CLI alias..."

ALIAS_CMD='alias sergas="python3 -m src.cli.agent_cli"'

# Determine config file based on shell
case "$SHELL_NAME" in
    bash)
        CONFIG_FILE="$HOME/.bashrc"
        ;;
    zsh)
        CONFIG_FILE="$HOME/.zshrc"
        ;;
    *)
        CONFIG_FILE="$HOME/.profile"
        ;;
esac

# Check if alias already exists
if grep -q "alias sergas=" "$CONFIG_FILE" 2>/dev/null; then
    echo "⚠ Alias already exists in $CONFIG_FILE"
else
    echo "$ALIAS_CMD" >> "$CONFIG_FILE"
    echo "✓ Alias added to $CONFIG_FILE"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✨ Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To start using the CLI:"
echo ""
echo "  1. Reload your shell configuration:"
echo "     source $CONFIG_FILE"
echo ""
echo "  2. Or open a new terminal window"
echo ""
echo "  3. Run the CLI:"
echo "     sergas --help"
echo ""
echo "Quick Start Examples:"
echo ""
echo "  # Check backend health"
echo "  sergas health"
echo ""
echo "  # Analyze account (interactive)"
echo "  sergas analyze --account-id ACC-001"
echo ""
echo "  # Analyze with auto-approval"
echo "  sergas analyze --account-id ACC-001 --auto-approve"
echo ""
echo "  # Verbose output for debugging"
echo "  sergas analyze --account-id ACC-001 --verbose"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 For more information, see: docs/guides/CLI_USAGE.md"
echo ""
