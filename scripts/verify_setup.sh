#!/bin/bash
# Verification script for dual authentication setup

echo "🔍 Verifying Dual Authentication Setup"
echo "========================================"
echo ""

# Check file existence
echo "1️⃣ Checking file structure..."
files_ok=true

if [ -f ".env" ]; then
    echo "   ✅ .env exists"
else
    echo "   ❌ .env missing"
    files_ok=false
fi

if [ -f ".env.local" ]; then
    echo "   ✅ .env.local exists"
else
    echo "   ❌ .env.local missing"
    files_ok=false
fi

if [ -f ".env.example" ]; then
    echo "   ✅ .env.example exists"
else
    echo "   ⚠️  .env.example missing (optional)"
fi

if [ -f "scripts/check_auth_config.sh" ]; then
    echo "   ✅ Validation script exists"
else
    echo "   ❌ scripts/check_auth_config.sh missing"
    files_ok=false
fi

echo ""

# Check .env is clean
echo "2️⃣ Checking .env configuration..."
if grep -q "^ANTHROPIC_API_KEY=" .env 2>/dev/null; then
    echo "   ❌ .env has active ANTHROPIC_API_KEY (blocks subscription)"
    echo "      Run: sed -i.bak '/^ANTHROPIC_API_KEY=/s/^/# /' .env"
else
    echo "   ✅ .env has no active ANTHROPIC_API_KEY"
fi

if grep -q "^ANTHROPIC_BASE_URL=" .env 2>/dev/null; then
    echo "   ❌ .env has active ANTHROPIC_BASE_URL (blocks subscription)"
    echo "      Run: sed -i.bak '/^ANTHROPIC_BASE_URL=/s/^/# /' .env"
else
    echo "   ✅ .env has no active ANTHROPIC_BASE_URL"
fi

echo ""

# Check .env.local has GLM-4.6
echo "3️⃣ Checking .env.local configuration..."
if [ -f ".env.local" ]; then
    if grep -q "^ANTHROPIC_BASE_URL=https://api.z.ai" .env.local; then
        echo "   ✅ .env.local has Z.ai base URL"
    else
        echo "   ⚠️  .env.local missing Z.ai base URL"
    fi
    
    if grep -q "^ANTHROPIC_API_KEY=" .env.local; then
        echo "   ✅ .env.local has API key"
    else
        echo "   ❌ .env.local missing API key"
    fi
    
    if grep -q "^CLAUDE_MODEL=glm-4.6" .env.local; then
        echo "   ✅ .env.local uses GLM-4.6"
    else
        echo "   ⚠️  .env.local not set to GLM-4.6"
    fi
else
    echo "   ❌ .env.local not found"
fi

echo ""

# Check src/main.py loads both files
echo "4️⃣ Checking application configuration..."
if [ -f "src/main.py" ]; then
    if grep -q "load_dotenv('.env.local', override=True)" src/main.py; then
        echo "   ✅ src/main.py loads .env.local with override"
    else
        echo "   ⚠️  src/main.py might not load .env.local correctly"
    fi
else
    echo "   ⚠️  src/main.py not found"
fi

echo ""

# Run validation script
echo "5️⃣ Running authentication validation..."
if [ -f "scripts/check_auth_config.sh" ]; then
    ./scripts/check_auth_config.sh
else
    echo "   ❌ Validation script not found"
fi

echo ""
echo "========================================"
echo "📋 Summary"
echo "========================================"
echo ""
echo "Expected Behavior:"
echo "  • Claude Code → Uses .env → No API keys → Max subscription ✅"
echo "  • Your App → Uses .env + .env.local → Has GLM-4.6 → Z.ai ($3/month) ✅"
echo ""
echo "Documentation:"
echo "  • /docs/SETUP_INSTRUCTIONS.md - Complete setup guide"
echo "  • /docs/FILE_SEPARATION_STRATEGY.md - File organization"
echo "  • /docs/AUTHENTICATION_GUIDE.md - Technical details"
echo "  • /docs/QUICK_AUTH_REFERENCE.md - Quick reference"
echo ""
