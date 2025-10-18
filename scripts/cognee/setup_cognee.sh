#!/bin/bash
# Cognee Setup Script
# Sets up Cognee knowledge graph for Sergas Super Account Manager

set -e  # Exit on error

echo "🚀 Setting up Cognee Knowledge Graph..."
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DOCKER_DIR="$PROJECT_ROOT/docker/cognee"

echo -e "${YELLOW}📁 Project root: $PROJECT_ROOT${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"

# Create necessary directories
echo ""
echo "📂 Creating data directories..."
mkdir -p "$DOCKER_DIR/cognee_data"
mkdir -p "$DOCKER_DIR/lancedb_data"
echo -e "${GREEN}✓ Directories created${NC}"

# Check for .env file
if [ ! -f "$DOCKER_DIR/.env" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  No .env file found. Copying from .env.example${NC}"
    cp "$DOCKER_DIR/.env.example" "$DOCKER_DIR/.env"
    echo -e "${YELLOW}⚠️  Please edit $DOCKER_DIR/.env with your configuration${NC}"
    echo -e "${YELLOW}   Then run this script again.${NC}"
    exit 0
fi

# Start Docker services
echo ""
echo "🐳 Starting Docker services..."
cd "$DOCKER_DIR"

# Check if using production profile
if [ "$1" == "production" ]; then
    echo -e "${YELLOW}Starting with production profile (includes Neo4j and Nginx)...${NC}"
    docker-compose --profile production up -d
else
    echo "Starting with development profile..."
    docker-compose up -d
fi

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check Cognee health
echo ""
echo "🔍 Checking Cognee service..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Cognee is healthy${NC}"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for Cognee... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ Cognee failed to start${NC}"
    echo "Check logs with: docker-compose logs cognee"
    exit 1
fi

# Check LanceDB health
echo ""
echo "🔍 Checking LanceDB service..."
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ LanceDB is healthy${NC}"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for LanceDB... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${YELLOW}⚠️  LanceDB health check failed (may not have health endpoint)${NC}"
fi

# Initialize Cognee workspace
echo ""
echo "🔧 Initializing Cognee workspace..."
cd "$PROJECT_ROOT"

# Check if Python venv exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies if needed
if ! python -c "import cognee" 2>/dev/null; then
    echo "Installing Cognee Python client..."
    pip install -q cognee>=0.3.0
fi

# Run initialization script
if [ -f "$SCRIPT_DIR/initialize_cognee.py" ]; then
    echo "Running Cognee initialization..."
    python "$SCRIPT_DIR/initialize_cognee.py"
else
    echo -e "${YELLOW}⚠️  Initialization script not found: $SCRIPT_DIR/initialize_cognee.py${NC}"
fi

# Summary
echo ""
echo "========================================"
echo -e "${GREEN}✅ Cognee Setup Complete!${NC}"
echo "========================================"
echo ""
echo "📊 Services Status:"
echo "  - Cognee API:    http://localhost:8000"
echo "  - LanceDB:       http://localhost:8001"
if [ "$1" == "production" ]; then
    echo "  - Neo4j Browser: http://localhost:7474"
    echo "  - Nginx:         http://localhost"
fi
echo ""
echo "📝 Next Steps:"
echo "  1. Ingest pilot accounts: ./scripts/cognee/ingest_pilot_accounts.sh"
echo "  2. Test Cognee client:    python -m pytest tests/unit/memory/"
echo "  3. View logs:            docker-compose -f docker/cognee/docker-compose.yml logs -f"
echo ""
echo "🛠️  Useful Commands:"
echo "  - Stop services:  docker-compose -f docker/cognee/docker-compose.yml down"
echo "  - Restart:        docker-compose -f docker/cognee/docker-compose.yml restart"
echo "  - View logs:      docker-compose -f docker/cognee/docker-compose.yml logs -f cognee"
echo ""
