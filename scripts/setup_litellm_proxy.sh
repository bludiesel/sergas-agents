#!/bin/bash
# Setup LiteLLM Proxy with Ollama for FREE Cognee Integration
# This allows Cognee to work with 100% free local models

set -e  # Exit on error

echo "========================================"
echo "LiteLLM + Ollama Setup for Cognee"
echo "========================================"
echo ""

# Check if we're in the project root
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Run this script from project root"
    exit 1
fi

# Activate virtual environment
echo "[1/6] Activating virtual environment..."
if [ -d "venv312" ]; then
    source venv312/bin/activate
    echo "✓ Using venv312"
elif [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Using venv"
else
    echo "❌ No virtual environment found. Create one first:"
    echo "   python3 -m venv venv312"
    exit 1
fi

# Install LiteLLM
echo ""
echo "[2/6] Installing LiteLLM proxy..."
pip install -q 'litellm[proxy]' redis
echo "✓ LiteLLM installed"

# Check for Ollama
echo ""
echo "[3/6] Checking Ollama installation..."
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama not found. Installing via Homebrew..."
    if command -v brew &> /dev/null; then
        brew install ollama
        echo "✓ Ollama installed"
    else
        echo "❌ Homebrew not found. Install Ollama manually:"
        echo "   Visit: https://ollama.ai/"
        exit 1
    fi
else
    echo "✓ Ollama already installed"
fi

# Pull Ollama models
echo ""
echo "[4/6] Pulling Ollama models (this may take a few minutes)..."
echo "   Pulling llama3.2 for LLM..."
ollama pull llama3.2
echo "✓ llama3.2 ready"

echo "   Pulling nomic-embed-text for embeddings..."
ollama pull nomic-embed-text
echo "✓ nomic-embed-text ready"

# Create LiteLLM config
echo ""
echo "[5/6] Creating LiteLLM configuration..."
mkdir -p config

cat > config/litellm_config.yaml <<'EOF'
# LiteLLM Proxy Configuration for Cognee
# Uses 100% free local Ollama models

model_list:
  # Primary LLM model
  - model_name: cognee-llm
    litellm_params:
      model: ollama/llama3.2
      api_base: http://localhost:11434
      temperature: 0.7
      max_tokens: 4096

  # Embedding model
  - model_name: cognee-embed
    litellm_params:
      model: ollama/nomic-embed-text
      api_base: http://localhost:11434

general_settings:
  master_key: sk-cognee-local-key  # Simple auth for local use

litellm_settings:
  drop_params: true  # Handle Ollama compatibility
  cache: true
  cache_params:
    type: local
    ttl: 3600  # 1 hour cache

# Optional: Add paid providers as fallback
# Uncomment and configure if you want hybrid setup
# - model_name: cognee-llm-fallback
#   litellm_params:
#     model: anthropic/claude-3-5-sonnet-20241022
#     api_key: sk-ant-...
#
# - model_name: cognee-llm-zai
#   litellm_params:
#     model: zhipuai/glm-4-plus
#     api_key: your-z-ai-api-key
#     api_base: https://api.z.ai/api/anthropic
EOF

echo "✓ Configuration created: config/litellm_config.yaml"

# Update .env.real
echo ""
echo "[6/6] Updating .env.real with LiteLLM configuration..."

# Check if LiteLLM config already exists in .env.real
if grep -q "LiteLLM Proxy Configuration" .env.real 2>/dev/null; then
    echo "✓ .env.real already has LiteLLM configuration"
else
    cat >> .env.real <<'EOF'

# ===================================
# LiteLLM Proxy Configuration (FREE)
# ===================================
# Uses local Ollama models via LiteLLM proxy
# Total cost: $0/month
# Start proxy: litellm --config config/litellm_config.yaml --port 8000

# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=cognee-llm
LLM_ENDPOINT=http://localhost:8000
LLM_API_KEY=sk-cognee-local-key

# Embedding Configuration
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=cognee-embed
EMBEDDING_ENDPOINT=http://localhost:8000
EMBEDDING_API_KEY=sk-cognee-local-key
EOF
    echo "✓ .env.real updated"
fi

# Create helper scripts
echo ""
echo "Creating helper scripts..."

# Start script
cat > scripts/start_litellm.sh <<'EOF'
#!/bin/bash
# Start LiteLLM proxy with Ollama backend

echo "Starting LiteLLM proxy..."
echo "Endpoint: http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

# Start Ollama in background if not running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama server..."
    ollama serve > /dev/null 2>&1 &
    sleep 2
fi

# Start LiteLLM proxy
litellm --config config/litellm_config.yaml --port 8000 --detailed_debug
EOF
chmod +x scripts/start_litellm.sh
echo "✓ Created scripts/start_litellm.sh"

# Test script
cat > scripts/test_litellm.sh <<'EOF'
#!/bin/bash
# Test LiteLLM proxy connectivity

echo "Testing LiteLLM proxy..."
echo ""

# Check if proxy is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ LiteLLM proxy is not running"
    echo "   Start it with: ./scripts/start_litellm.sh"
    exit 1
fi

echo "✓ LiteLLM proxy is running"

# Test model availability
echo ""
echo "Available models:"
curl -s http://localhost:8000/v1/models | jq -r '.data[].id' 2>/dev/null || echo "  (Install jq for formatted output)"

echo ""
echo "✓ LiteLLM proxy is ready!"
echo ""
echo "Next steps:"
echo "1. Copy config: cp .env.real .env"
echo "2. Test Cognee: python scripts/setup_real_cognee.py"
EOF
chmod +x scripts/test_litellm.sh
echo "✓ Created scripts/test_litellm.sh"

echo ""
echo "========================================"
echo "✅ Setup Complete!"
echo "========================================"
echo ""
echo "📋 What was installed:"
echo "   ✓ LiteLLM proxy"
echo "   ✓ Ollama + llama3.2 + nomic-embed-text"
echo "   ✓ Configuration files"
echo "   ✓ Helper scripts"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. Start the LiteLLM proxy (in a separate terminal):"
echo "   ./scripts/start_litellm.sh"
echo ""
echo "2. Test the proxy connection:"
echo "   ./scripts/test_litellm.sh"
echo ""
echo "3. Update your environment config:"
echo "   cp .env.real .env"
echo "   # Edit .env to use LiteLLM configuration"
echo ""
echo "4. Test Cognee with free local models:"
echo "   source venv312/bin/activate"
echo "   python scripts/setup_real_cognee.py"
echo ""
echo "💡 Benefits:"
echo "   • 100% FREE (no API costs)"
echo "   • No internet required for inference"
echo "   • Privacy (all data stays local)"
echo "   • Can add paid APIs as fallback later"
echo ""
echo "📖 Documentation:"
echo "   • Full guide: docs/PROXY_SOLUTIONS_FOR_COGNEE.md"
echo "   • Config file: config/litellm_config.yaml"
echo ""
